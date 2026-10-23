"""Risk-free NO baskets inside the Cup.

Each race is listed as one binary market per party ("Will the Democratic Party win the Texas
Senate?", "Will the Republican Party win the Texas Senate?"). At most one of a race's k markets
can resolve YES, so NO on every leg pays at least k-1 whoever wins (k if nobody listed wins).

  Buy:  NO on every leg costs sum(1 - YES bid). Locked profit per set = sum(YES bids) - 1.
  Sell: a held basket can be sold for sum(1 - YES ask). Sell when that beats holding to
        settlement (k-1) by ARB_MIN_PROFIT, or beats what the set cost by ARB_EXIT_PROFIT
        (smaller profit now, capital freed for the next basket).
  Repair: an atomic multi-leg order places every leg or none, but fills can still be uneven.
        Short legs are topped up at no worse than break-even + ARB_REPAIR_SLIPPAGE; if that
        can't be done within ARB_REPAIR_MINUTES the excess legs are sold instead.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .sig_api import Book, Level, Market
from .strategy import Holding, Order

TITLE = re.compile(r"^\s*Will the (.+?) Party win the (.+?)\??\s*$", re.I)


@dataclass(frozen=True)
class Race:
    key: str                          # e.g. "Texas Senate"
    legs: tuple[tuple[str, str], ...]  # (exchange_id, party), sorted by party

    @property
    def k(self) -> int:
        return len(self.legs)

    @property
    def exchange_ids(self) -> list[str]:
        return [e for e, _ in self.legs]

    def label(self, eid: str) -> str:
        party = dict(self.legs).get(eid, "?")
        return f"{self.key} [{party}]"


def group_races(markets: list[Market]) -> list[Race]:
    groups: dict[str, list[tuple[str, str]]] = {}
    for m in markets:
        if len(m.exchanges) != 1 or m.status.lower() not in ("", "open", "active"):
            continue
        t = TITLE.match(m.title)
        if not t:
            continue
        groups.setdefault(t.group(2).strip(), []).append((m.exchanges[0].id, t.group(1).strip()))
    out = []
    for key, legs in sorted(groups.items()):
        parties = [p.lower() for _, p in legs]
        if len(legs) >= 2 and len(set(parties)) == len(parties):
            out.append(Race(key, tuple(sorted(legs, key=lambda l: l[1]))))
    return out


@dataclass(frozen=True)
class BasketOrder:
    race: Race
    action: str                  # buy | sell (NO on every leg)
    sets: int
    limits: tuple[float, ...]    # worst NO price per leg (the order's limit)
    avg: tuple[float, ...]       # average NO price per leg over the levels walked
    reason: str

    @property
    def per_set(self) -> float:
        return sum(self.avg)

    def leg_orders(self) -> list[Order]:
        return [Order(eid, "no", self.action, self.sets, lim, avg, self.reason)
                for eid, lim, avg in zip(self.race.exchange_ids, self.limits, self.avg)]


def _walk(ladders: list[list[Level]], ok, max_sets: int,
          depth_fraction: float) -> tuple[int, tuple[float, ...], tuple[float, ...]] | None:
    """Take sets across every leg's ladder together while the marginal set is still `ok`."""
    ladders = [[Level(l.price, math.floor(l.qty * depth_fraction)) for l in lad] for lad in ladders]
    ladders = [[l for l in lad if l.qty >= 1] for lad in ladders]
    if not ladders or any(not lad for lad in ladders):
        return None
    idx = [0] * len(ladders)
    left = [lad[0].qty for lad in ladders]
    sets, totals, limits = 0, [0.0] * len(ladders), [0.0] * len(ladders)
    while sets < max_sets:
        prices = [lad[i].price for lad, i in zip(ladders, idx)]
        if not ok(prices):
            break
        take = int(min(min(left), max_sets - sets))
        if take <= 0:
            break
        sets += take
        for j, p in enumerate(prices):  # every leg is booked before any ladder can run out
            totals[j] += take * p
            limits[j] = p
            left[j] -= take
        exhausted = False
        for j in range(len(ladders)):
            if left[j] < 1:
                idx[j] += 1
                if idx[j] >= len(ladders[j]):
                    exhausted = True
                else:
                    left[j] = ladders[j][idx[j]].qty
        if exhausted:
            break
    if not sets:
        return None
    return sets, tuple(limits), tuple(t / sets for t in totals)


def screen_buy(race: Race, prices: dict[str, tuple[float | None, float | None]]) -> float | None:
    """Top-of-book profit per set for buying the NO basket, from bulk prices."""
    bids = [prices.get(e, (None, None))[0] for e in race.exchange_ids]
    return None if any(b is None for b in bids) else sum(bids) - 1


def screen_sell(race: Race, prices: dict[str, tuple[float | None, float | None]]) -> float | None:
    """Top-of-book proceeds per set for selling the NO basket."""
    asks = [prices.get(e, (None, None))[1] for e in race.exchange_ids]
    return None if any(a is None for a in asks) else sum(1 - a for a in asks)


def exit_bar(race: Race, cost_per_set: float, min_profit: float, exit_profit: float) -> float:
    return min(race.k - 1 + min_profit, cost_per_set + exit_profit)


def plan_buy(race: Race, books: dict[str, Book], *, min_profit: float, max_sets: int,
             depth_fraction: float) -> BasketOrder | None:
    payout = race.k - 1
    r = _walk([books[e].buy_levels("no") for e in race.exchange_ids],
              lambda ps: payout - sum(ps) >= min_profit - 1e-9, max_sets, depth_fraction)
    if not r:
        return None
    sets, limits, avg = r
    return BasketOrder(race, "buy", sets, limits, avg, f"arb +{payout - sum(avg):.3f}/set")


def plan_sell(race: Race, books: dict[str, Book], *, sets_held: int, bar: float) -> BasketOrder | None:
    r = _walk([books[e].sell_levels("no") for e in race.exchange_ids],
              lambda ps: sum(ps) >= bar - 1e-9, sets_held, 1.0)
    if not r:
        return None
    sets, limits, avg = r
    return BasketOrder(race, "sell", sets, limits, avg, "arb exit")


def plan_repair(race: Race, held: dict[str, Holding], books: dict[str, Book], *,
                slippage: float, unwind: bool) -> list[Order]:
    """Even out a basket. Normal: buy NO on short legs up to break-even + slippage.
    unwind=True (repair took too long): sell the excess on long legs instead."""
    qty = {e: (held[e].qty if e in held else 0.0) for e in race.exchange_ids}
    hi, lo = max(qty.values()), min(qty.values())
    out: list[Order] = []
    if unwind:
        for e in race.exchange_ids:
            excess = math.floor(qty[e] - lo)
            levels = books[e].sell_levels("no")
            if excess < 1 or not levels:
                continue
            floor_px, n, limit = levels[0].price - slippage, 0, None
            for l in levels:
                if l.price < floor_px - 1e-9 or n >= excess:
                    break
                n, limit = n + min(math.floor(l.qty), excess - n), l.price
            if n > 0:
                out.append(Order(e, "no", "sell", n, limit, levels[0].price, "arb unwind"))
        return out
    for e in race.exchange_ids:
        missing = math.floor(hi - qty[e])
        if missing < 1:
            continue
        others = sum(held[o].avg_cost for o in race.exchange_ids if o != e and o in held)
        cap = race.k - 1 + slippage - others
        n, limit = 0, None
        for l in books[e].buy_levels("no"):
            if l.price > cap + 1e-9 or n >= missing:
                break
            n, limit = n + min(math.floor(l.qty), missing - n), l.price
        if n > 0:
            out.append(Order(e, "no", "buy", n, limit, cap, "arb repair"))
    return out
