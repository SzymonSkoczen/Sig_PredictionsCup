"""Client for the Predictions Cup exchange (The Super Market API, /api/v1).

Facts this relies on (from the public API docs at sig.thesuper.market/api/v1/docs):
- Bearer-token auth; 100 reads + 30 writes per minute per account, shared by all keys.
- Every order must carry `tournamentId`, otherwise it trades on the public book, not the Cup.
- Prices are on a 0.005 grid in [0.005, 0.995].
- Order books are YES-normalised: buying NO at n is selling YES at 1-n, so NO is bought
  against YES *bids* and sold against YES *asks*.
- Order POSTs take an idempotencyKey, which makes retrying ORDER_STATUS_UNKNOWN safe.
"""
from __future__ import annotations

import logging
import math
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterator

import httpx

log = logging.getLogger(__name__)

TICK = 0.005
MIN_PRICE = 0.005
MAX_PRICE = 0.995
RETRYABLE = {"RATE_LIMITED", "TX_CONFLICT", "SERVICE_UNAVAILABLE", "ORDER_STATUS_UNKNOWN",
             "REQUEST_IN_FLIGHT", "TRANSPORT_ERROR", "INTERNAL_ERROR"}


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(f"{status} {code}: {message}")
        self.status = status
        self.code = code


class RateLimiter:
    """Sliding 60 s window; acquire() blocks until a slot is free."""

    def __init__(self, per_minute: int, clock=time.monotonic, sleep=time.sleep):
        self.per_minute = per_minute
        self._clock, self._sleep = clock, sleep
        self._hits: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        while True:
            with self._lock:
                now = self._clock()
                while self._hits and now - self._hits[0] >= 60.0:
                    self._hits.popleft()
                if len(self._hits) < self.per_minute:
                    self._hits.append(now)
                    return
                wait = 60.0 - (now - self._hits[0]) + 0.01
            self._sleep(wait)

    @property
    def used(self) -> int:
        now = self._clock()
        return sum(1 for t in self._hits if now - t < 60.0)


def round_to_tick(price: float, action: str) -> float:
    """Snap onto the grid without worsening our price: buys round down, sells round up."""
    ticks = price / TICK
    ticks = math.floor(ticks + 1e-9) if action == "buy" else math.ceil(ticks - 1e-9)
    return round(min(MAX_PRICE, max(MIN_PRICE, ticks * TICK)), 3)


@dataclass(frozen=True)
class Level:
    price: float
    qty: float


@dataclass
class Book:
    """YES-normalised book. bids descending, asks ascending."""
    exchange_id: str
    bids: list[Level] = field(default_factory=list)
    asks: list[Level] = field(default_factory=list)

    def buy_levels(self, side: str) -> list[Level]:
        """Prices we can BUY `side` at, best first."""
        if side == "yes":
            return list(self.asks)
        return [Level(round(1 - l.price, 6), l.qty) for l in self.bids]

    def sell_levels(self, side: str) -> list[Level]:
        """Prices we can SELL `side` at, best first."""
        if side == "yes":
            return list(self.bids)
        return [Level(round(1 - l.price, 6), l.qty) for l in self.asks]

    @classmethod
    def from_api(cls, d: dict[str, Any]) -> "Book":
        d = d.get("data", d)
        lv = lambda xs: [Level(float(x["price"]), float(x["quantity"])) for x in xs or []]
        return cls(str(d.get("exchangeId", "")),
                   sorted(lv(d.get("bids")), key=lambda l: -l.price),
                   sorted(lv(d.get("asks")), key=lambda l: l.price))

    @classmethod
    def top(cls, exchange_id: str, bid: float | None, ask: float | None) -> "Book":
        """Top-of-book only, size unknown (taken as huge) — for screening, never for sizing."""
        big = 1e9
        return cls(exchange_id, [Level(bid, big)] if bid else [], [Level(ask, big)] if ask else [])


@dataclass
class Exchange:
    id: str
    option: str | None


@dataclass
class Market:
    id: str
    title: str
    status: str
    settlement_date: str | None
    exchanges: list[Exchange]

    @classmethod
    def from_api(cls, d: dict[str, Any]) -> "Market":
        return cls(str(d["id"]), d.get("title", ""), d.get("status", ""), d.get("settlementDate"),
                   [Exchange(str(e["id"]), e.get("option")) for e in d.get("exchanges") or []])


@dataclass
class Position:
    exchange_id: str
    market_id: str
    title: str
    side: str
    qty: float
    avg_cost: float
    unrealized_pnl: float

    @classmethod
    def from_api(cls, d: dict[str, Any]) -> "Position":
        lots = d.get("lots") or []
        side = (d.get("side") or (lots[0].get("side") if lots else None) or "yes").lower()
        return cls(str(d["exchangeId"]), str(d.get("marketId", "")), d.get("marketTitle", ""), side,
                   float(d.get("quantity", 0)), float(d.get("avgCost", 0)),
                   float(d.get("unrealizedPnl", 0)))


class SigApi:
    def __init__(self, api_key: str, base_url: str, tournament_slug: str,
                 read_budget: int = 70, write_budget: int = 20, timeout: float = 20.0,
                 max_retries: int = 4, transport: httpx.BaseTransport | None = None,
                 sleep: Callable[[float], None] = time.sleep):
        self._http = httpx.Client(base_url=base_url, timeout=timeout, transport=transport,
                                  headers={"Authorization": f"Bearer {api_key}",
                                           "Accept": "application/json"})
        self.slug = tournament_slug
        self.reads = RateLimiter(read_budget, sleep=sleep)
        self.writes = RateLimiter(write_budget, sleep=sleep)
        self.max_retries = max_retries
        self._sleep = sleep
        self._tournament_id: str | None = None
        self.error_count = 0

    # ---- transport ----

    def _request(self, method: str, path: str, params=None, json=None) -> Any:
        limiter = self.reads if method == "GET" else self.writes
        for attempt in range(self.max_retries + 1):
            limiter.acquire()
            try:
                r = self._http.request(method, path, params=params, json=json)
            except httpx.TransportError as e:
                err = ApiError(0, "TRANSPORT_ERROR", str(e))
            else:
                if r.status_code < 400:
                    return r.json() if r.content else None
                err = _parse_error(r)
            self.error_count += 1
            if err.code not in RETRYABLE and err.status < 500 or attempt == self.max_retries:
                raise err
            wait = min(2.0 ** attempt, 30.0)
            if err.code == "REQUEST_IN_FLIGHT":
                wait = 90.0  # the idempotency key holds a 90 s lease
            log.warning("%s %s failed (%s), retrying in %.0fs", method, path, err, wait)
            self._sleep(wait)
        raise AssertionError("unreachable")

    def get(self, path: str, **params: Any) -> Any:
        return self._request("GET", path, params={k: v for k, v in params.items() if v is not None})

    def post(self, path: str, body: dict[str, Any]) -> Any:
        return self._request("POST", path, json=body)

    def _paginate(self, path: str, **params: Any) -> Iterator[dict[str, Any]]:
        cursor = None
        while True:
            page = self.get(path, cursor=cursor, **params)
            yield from page.get("data", [])
            pag = page.get("pagination") or {}
            cursor = pag.get("nextCursor")
            if not pag.get("hasMore") or not cursor:
                return

    # ---- reads ----

    def tournaments(self) -> list[dict[str, Any]]:
        r = self.get("/tournaments")
        return r.get("data", r) if isinstance(r, dict) else r

    @property
    def tournament_id(self) -> str:
        if self._tournament_id is None:
            t = self.get(f"/tournaments/{self.slug}")
            t = t.get("data", t)
            self._tournament_id = str(t["id"])
        return self._tournament_id

    def account(self) -> dict[str, Any]:
        return self.get("/account")

    def markets(self, status: str | None = None) -> list[Market]:
        return [Market.from_api(m)
                for m in self._paginate(f"/tournaments/{self.slug}/markets", status=status, limit=100)]

    def prices(self, exchange_ids: list[str]) -> dict[str, tuple[float | None, float | None]]:
        """exchange_id -> (best YES bid, best YES ask); one read per 100 exchanges."""
        out: dict[str, tuple[float | None, float | None]] = {}
        for i in range(0, len(exchange_ids), 100):
            r = self.get("/exchanges/prices", ids=",".join(exchange_ids[i:i + 100]),
                         tournamentId=self.tournament_id)
            for p in r.get("data", []):
                eid = str(p.get("exchangeId") or p.get("id"))
                out[eid] = (_f(p.get("bestBid")), _f(p.get("bestAsk")))
        return out

    def book(self, exchange_id: str, depth: int = 10) -> Book:
        b = Book.from_api(self.get(f"/exchanges/{exchange_id}/orderbook", depth=depth,
                                   tournamentId=self.tournament_id))
        b.exchange_id = exchange_id
        return b

    def positions(self) -> list[Position]:
        r = self.get(f"/tournaments/{self.slug}/portfolio/positions")
        return [Position.from_api(p) for p in r.get("positions", r.get("data", []))]

    def pnl(self) -> dict[str, Any]:
        return self.get(f"/tournaments/{self.slug}/portfolio/pnl", period="all")

    # ---- writes ----

    def place_order(self, exchange_id: str, side: str, action: str, qty: int, price: float,
                    ttl_seconds: int = 15) -> dict[str, Any]:
        if side not in ("yes", "no") or action not in ("buy", "sell") or qty <= 0:
            raise ValueError(f"bad order {side}/{action}/{qty}")
        exp = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        body = {
            "idempotencyKey": str(uuid.uuid4()),
            "exchangeId": str(exchange_id),
            "side": side,
            "action": action,
            "quantity": int(qty),
            "price": round_to_tick(price, action),
            "tournamentId": self.tournament_id,
            "expirationDate": exp.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        }
        return self.post("/orders", body)

    def cancel_all(self) -> Any:
        return self.post("/orders/cancel-all", {"tournamentId": self.tournament_id})

    def close(self) -> None:
        self._http.close()


def _f(v: Any) -> float | None:
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _parse_error(r: httpx.Response) -> ApiError:
    try:
        e = r.json().get("error", {})
        return ApiError(r.status_code, e.get("code", "UNKNOWN"), e.get("message", ""))
    except ValueError:
        return ApiError(r.status_code, "UNKNOWN", r.text[:200])
