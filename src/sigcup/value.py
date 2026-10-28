"""Value-book tools adapted from grissou/prediction-market-maker (MIT licence, (c) 2026 Adam Zerouali):
https://github.com/grissou/prediction-market-maker — the best-documented Cup bot (152nd of 1,782, +15% expected
at settlement on 25 Oct). Ported here in this bot's side terms (YES or NO bought, never "short"):

- edge per unit of cash: every buy, and every holding kept instead of sold, is scored as expected gain at the
  result divided by the cash it ties up, (fair - price) / price, so a 5c gap at 90c (5.6%) ranks below a 5c gap
  at 30c (16.7%);
- race-scaled fair value: a race's legs scaled to sum to 1 (only when they already nearly do);
- the harvest ladder: resting bids under the touch on favourites (fair >= 90%) at 0/2/4/6c, only at 8%+ edge,
  inside a cash budget; it buys the Cup's favourite-longshot tilt as a maker instead of paying the spread;
- the allocator's pairing: sell the holdings with the least edge left (never below fair - margin) to fund buys
  with at least `min_gain` more edge;
- the national-swing stress test (every Republican price up, every Democratic price down, and the reverse).
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .automap import STATES
from .sig_api import MAX_PRICE, MIN_PRICE, TICK, Book
from .strategy import side_fair

EPS = 1e-9


def edge(fair_side: float, price: float) -> float:
    """Expected gain at the result per unit of cash: buying a side at `price`, or keeping it rather than selling
    at `price` (grissou's edge_buy / edge_short / edge_keep_long / edge_keep_short in one formula)."""
    return (fair_side - price) / max(price, TICK)


def race_scaled(fairs: dict[str, float], races: list[list[str]], lo: float = 0.95, hi: float = 1.05) -> dict[str, float]:
    """Each race's fair values divided by their sum when every leg is priced and the sum is within [lo, hi]
    (reference vig and noise). A sum far from 1 usually means a contender the Cup does not list: left alone."""
    out = dict(fairs)
    for legs in races:
        ps = [fairs.get(e) for e in legs]
        if len(legs) > 1 and all(p is not None for p in ps) and lo <= sum(ps) <= hi:
            total = sum(ps)
            out.update({e: p / total for e, p in zip(legs, ps)})
    return out


def state_of(race_key: str) -> str | None:
    """'Rhode Island Senate' -> 'RI', 'PA-07 House race' -> 'PA', 'U.S. House' -> None."""
    m = re.match(r"^([A-Z]{2})-(\d+|AL) ", race_key)
    if m:
        return m.group(1)
    for name in sorted(STATES, key=len, reverse=True):  # "West Virginia" before "Virginia"
        if race_key.startswith(name + " "):
            return STATES[name]
    return None


# --------------------------------------------------------------------------- the harvest ladder

@dataclass(frozen=True)
class Level:
    exchange_id: str
    side: str
    price: float
    qty: int
    edge: float

    @property
    def cost(self) -> float:
        return self.qty * self.price


def side_touch(book: Book, side: str) -> tuple[float | None, float | None]:
    """(best bid, best ask) for buying/selling `side`, from the YES-normalised book."""
    bids, asks = book.sell_levels(side), book.buy_levels(side)
    return (bids[0].price if bids else None), (asks[0].price if asks else None)


def ladder_levels(eid: str, fair_yes: float, book: Book, *, favourite_p: float, offsets: list[float],
                  min_edge: float, level_cost: float) -> list[Level]:
    """Resting bids under the favourite side's touch at each offset, strictly below its ask (never crossing),
    each only at min_edge per unit of cash or better (grissou ladder.market_levels)."""
    for side in ("yes", "no"):
        f = side_fair(fair_yes, side)
        if f < favourite_p - EPS:
            continue
        bid, ask = side_touch(book, side)
        if bid is None:
            return []
        out, seen = [], set()
        for off in sorted(set(offsets)):
            px = round(bid - off, 3)
            if px < MIN_PRICE - EPS or px > MAX_PRICE + EPS or px in seen:
                continue
            if ask is not None and px >= ask - EPS:
                continue
            e = edge(f, px)
            qty = int(level_cost / px + EPS)
            if e >= min_edge - EPS and qty >= 1:
                out.append(Level(eid, side, px, qty, e))
                seen.add(px)
        return out
    return []


def within_budget(levels: list[Level], budget: float) -> list[Level]:
    """Best edge first until the budget is spent; the last level that fits only in part is trimmed."""
    out, left = [], budget
    for lv in sorted(levels, key=lambda l: (-l.edge, l.exchange_id, -l.price)):
        if lv.cost > left + EPS:
            qty = int(left / lv.price + EPS)
            if qty < 1:
                continue
            lv = Level(lv.exchange_id, lv.side, lv.price, qty, lv.edge)
        out.append(lv)
        left -= lv.cost
    return out


# --------------------------------------------------------------------------- the allocator

@dataclass
class Seller:
    exchange_id: str
    side: str
    qty: float
    price: float        # best bid for the held side: what a sale gets now
    keep_edge: float    # edge of keeping it rather than selling at `price`
    fair: float


def swap_sellers(holdings, fairs_yes, books_top, *, max_keep_edge: float, sell_margin: float,
                 pinned: set[str]) -> list[Seller]:
    """Holdings the allocator may sell, least edge left first: keep-edge <= max_keep_edge, and the sale no more
    than sell_margin below fair (grissou's value floor for swaps). books_top: eid -> (YES bid, YES ask)."""
    out = []
    for h in holdings:
        fy = fairs_yes.get(h.exchange_id)
        bid, ask = books_top.get(h.exchange_id, (None, None))
        if fy is None or h.exchange_id in pinned or h.qty < 1:
            continue
        px = bid if h.side == "yes" else (None if ask is None else round(1 - ask, 6))
        if px is None:
            continue
        f = side_fair(fy, h.side)
        k = edge(f, px)
        if k <= max_keep_edge + EPS and px >= f - sell_margin - EPS:
            out.append(Seller(h.exchange_id, h.side, h.qty, px, k, f))
    return sorted(out, key=lambda x: (x.keep_edge, x.exchange_id))


def plan_swap_sales(sellers: list[Seller], best_buy_edge: float, need: float, turnover_left: float,
                    min_gain: float) -> list[tuple[Seller, int]]:
    """(seller, shares) to sell, lowest edge first, raising at most `need` cash, only while the best buy beats
    the seller by min_gain (grissou plan_swaps, with the buy left to the normal entry step once cash lands)."""
    out, left = [], min(need, turnover_left)
    for sl in sellers:
        if left < 20 or best_buy_edge - sl.keep_edge < min_gain - EPS:
            break
        n = min(int(sl.qty), math.ceil(left / sl.price))
        if n >= 1:
            out.append((sl, n))
            left -= n * sl.price
    return out


# --------------------------------------------------------------------------- national swing

def swing_value_change(holdings: list[tuple[str, str, float, float]], shock: float) -> tuple[float, float]:
    """(Republican swing, Democratic swing): the change in expected value at the result if every Republican
    YES fair moves up by `shock` and every Democratic one down (and the reverse). holdings: (party, side, qty,
    fair_yes). Other parties are held fixed. A rough, correlated worst case (grissou risk.py SWING_SHOCK)."""
    def value(sign: int) -> float:
        total = 0.0
        for party, side, qty, fy in holdings:
            d = {"r": shock, "d": -shock}.get(party[:1].lower(), 0.0) * sign
            p = min(1.0, max(0.0, fy + d))
            total += qty * (side_fair(p, side) - side_fair(fy, side))
        return total
    return value(+1), value(-1)
