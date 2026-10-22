"""Real-money reference prices: Kalshi and Polymarket public market data (no account needed).

A reference "ref" string names what to price:
  kalshi      TICKER            e.g. KXSENATETX-26-R
              T1+T2             sum of mutually exclusive markets (two candidates of one party)
  polymarket  slug:Outcome      e.g. texas-senate-election-winner:Republican   (gamma market slug)
              token:<id>        a CLOB token id directly
              a+b               sum, as above
Each leg can be inverted in the market map (SIG YES == reference NO).
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable

import httpx

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RefQuote:
    source: str
    ref: str
    bid: float | None
    ask: float | None
    ts: float

    @property
    def mid(self) -> float | None:
        if self.bid is None or self.ask is None:
            return None
        return (self.bid + self.ask) / 2

    @property
    def spread(self) -> float | None:
        if self.bid is None or self.ask is None:
            return None
        return self.ask - self.bid

    def inverted(self) -> "RefQuote":
        return RefQuote(self.source, self.ref,
                        None if self.ask is None else round(1 - self.ask, 6),
                        None if self.bid is None else round(1 - self.bid, 6), self.ts)


def combine_sum(source: str, ref: str, parts: list[RefQuote | None], now: float) -> RefQuote | None:
    """Sum of mutually exclusive outcomes; a side is only known if every part has it."""
    if not parts or any(p is None for p in parts):
        return None
    bids = [p.bid for p in parts]
    asks = [p.ask for p in parts]
    return RefQuote(source, ref,
                    sum(bids) if all(b is not None for b in bids) else None,
                    min(1.0, sum(asks)) if all(a is not None for a in asks) else None,
                    min(p.ts for p in parts) if parts else now)


class _Http:
    def __init__(self, base_url: str, min_interval: float, transport=None, sleep=time.sleep):
        self._http = httpx.Client(base_url=base_url, timeout=20.0, transport=transport,
                                  headers={"Accept": "application/json", "User-Agent": "sigcup/0.1"})
        self._min_interval = min_interval
        self._last = 0.0
        self._sleep = sleep

    def request(self, method: str, path: str, **kw: Any) -> Any:
        for attempt in range(4):
            wait = self._min_interval - (time.monotonic() - self._last)
            if wait > 0:
                self._sleep(wait)
            self._last = time.monotonic()
            r = self._http.request(method, path, **kw)
            if r.status_code in (429, 502, 503) and attempt < 3:
                self._sleep(float(r.headers.get("Retry-After") or 2 * (attempt + 1)))
                continue
            r.raise_for_status()
            return r.json()


def _num(v: Any) -> float | None:
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


class KalshiFeed:
    source = "kalshi"

    def __init__(self, base_url: str, transport=None, sleep=time.sleep, clock: Callable[[], float] = time.time):
        self._http = _Http(base_url, 0.25, transport, sleep)
        self._clock = clock

    @staticmethod
    def _price(m: dict[str, Any], side: str) -> float | None:
        """Kalshi now sends `yes_bid_dollars` ("0.4500"); older payloads send cents (45)."""
        d = _num(m.get(f"yes_{side}_dollars"))
        if d is None:
            c = _num(m.get(f"yes_{side}"))
            d = None if c is None else c / 100
        # 0 bid / 100 ask means "no order on that side"
        if d is None or d <= 0 or d >= 1:
            return None
        return d

    def quotes(self, tickers: list[str]) -> dict[str, RefQuote]:
        now = self._clock()
        out: dict[str, RefQuote] = {}
        for i in range(0, len(tickers), 100):
            r = self._http.request("GET", "/markets", params={"tickers": ",".join(tickers[i:i + 100]),
                                                              "limit": 1000})
            for m in r.get("markets") or []:
                if m.get("status") not in (None, "active", "open"):
                    continue
                out[m["ticker"]] = RefQuote(self.source, m["ticker"], self._price(m, "bid"),
                                            self._price(m, "ask"), now)
        return out

    def open_election_markets(self, max_pages: int = 25) -> list[dict[str, Any]]:
        """Open events with nested markets, for `suggest-map` (one-off, slow is fine)."""
        out, cursor = [], None
        for _ in range(max_pages):
            r = self._http.request("GET", "/events", params={"status": "open", "with_nested_markets": "true",
                                                             "limit": 200, **({"cursor": cursor} if cursor else {})})
            for e in r.get("events") or []:
                for m in e.get("markets") or []:
                    out.append({"ticker": m.get("ticker"),
                                "title": f"{e.get('title', '')} — {m.get('yes_sub_title') or m.get('title', '')}"})
            cursor = r.get("cursor")
            if not cursor:
                break
        return out


class PolymarketFeed:
    source = "polymarket"

    def __init__(self, gamma_url: str, clob_url: str, transport=None, sleep=time.sleep,
                 clock: Callable[[], float] = time.time):
        self._gamma = _Http(gamma_url, 0.2, transport, sleep)
        self._clob = _Http(clob_url, 0.1, transport, sleep)
        self._clock = clock
        self._tokens: dict[str, str] = {}  # "slug:Outcome" -> token id

    def token_id(self, ref: str) -> str:
        if ref.startswith("token:"):
            return ref[len("token:"):]
        if ref not in self._tokens:
            slug, _, outcome = ref.partition(":")
            r = self._gamma.request("GET", "/markets", params={"slug": slug})
            markets = r if isinstance(r, list) else r.get("data", [])
            if not markets:
                raise KeyError(f"polymarket market not found: {slug}")
            m = markets[0]
            outcomes = _jsonish(m.get("outcomes"))
            tokens = _jsonish(m.get("clobTokenIds"))
            want = (outcome or "Yes").strip().lower()
            idx = next((i for i, o in enumerate(outcomes) if str(o).strip().lower() == want), None)
            if idx is None:
                raise KeyError(f"polymarket {slug}: outcome {outcome!r} not in {outcomes}")
            self._tokens[ref] = str(tokens[idx])
        return self._tokens[ref]

    @staticmethod
    def _quote_from_book(ref: str, book: dict[str, Any], now: float) -> RefQuote:
        bids = [float(x["price"]) for x in book.get("bids") or [] if float(x.get("size", 0)) > 0]
        asks = [float(x["price"]) for x in book.get("asks") or [] if float(x.get("size", 0)) > 0]
        return RefQuote("polymarket", ref, max(bids) if bids else None, min(asks) if asks else None, now)

    def quotes(self, refs: list[str]) -> dict[str, RefQuote]:
        now = self._clock()
        ids: dict[str, str] = {}
        for ref in refs:
            try:
                ids[ref] = self.token_id(ref)
            except (KeyError, httpx.HTTPError, IndexError) as e:
                log.warning("polymarket %s: %s", ref, e)
        out: dict[str, RefQuote] = {}
        by_token = {t: r for r, t in ids.items()}
        tokens = list(by_token)
        for i in range(0, len(tokens), 50):
            chunk = tokens[i:i + 50]
            try:
                books = self._clob.request("POST", "/books", json=[{"token_id": t} for t in chunk])
            except httpx.HTTPError:
                books = [self._clob.request("GET", "/book", params={"token_id": t}) for t in chunk]
            for b in books or []:
                ref = by_token.get(str(b.get("asset_id")))
                if ref:
                    out[ref] = self._quote_from_book(ref, b, now)
        return out

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        r = self._gamma.request("GET", "/public-search", params={"q": query, "limit_per_type": limit})
        out = []
        for e in r.get("events") or []:
            for m in e.get("markets") or []:
                if m.get("closed"):
                    continue
                for o in _jsonish(m.get("outcomes")):
                    out.append({"ref": f"{m.get('slug')}:{o}", "title": f"{m.get('question', '')} — {o}"})
        return out


def _jsonish(v: Any) -> list:
    """Gamma returns some lists as JSON-encoded strings."""
    if isinstance(v, str):
        try:
            return json.loads(v)
        except ValueError:
            return []
    return list(v or [])
