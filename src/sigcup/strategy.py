"""Convergence trading rules, kept free of I/O so they can be tested directly.

Entry: SIG sells a side cheaper than the reference fair value by at least MIN_EDGE
       -> buy it (YES when SIG is too low, NO when SIG is too high).
Exit:  SIG's bid for the held side comes back to within EXIT_BAND of fair -> sell ("converged");
       fair value drops STOP_LOSS below what we paid -> sell ("stop");
       held longer than MAX_HOLD_HOURS -> sell ("timeout").
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .sig_api import Book


@dataclass(frozen=True)
class Order:
    exchange_id: str
    side: str      # yes | no
    action: str    # buy | sell
    qty: int
    price: float   # limit price for `side`
    fair: float    # fair value of `side`
    reason: str

    @property
    def cost(self) -> float:
        return self.qty * self.price


@dataclass
class Holding:
    exchange_id: str
    side: str
    qty: float
    avg_cost: float
    opened_at: float


def side_fair(fair_yes: float, side: str) -> float:
    return fair_yes if side == "yes" else 1 - fair_yes


def kelly_cost(p: float, price: float, fraction: float, bankroll: float) -> float:
    """Fraction-Kelly stake for a binary contract bought at `price` with win chance `p`."""
    if price >= 1 or p <= price:
        return 0.0
    return fraction * (p - price) / (1 - price) * bankroll


def plan_entry(exchange_id: str, fair_yes: float, book: Book, *, min_edge: float,
               depth_fraction: float, max_cost: float, kelly_fraction: float,
               bankroll: float, min_return: float = 0.0, only_side: str | None = None,
               reason: str = "") -> Order | None:
    """Buy the side Kalshi says is cheap. A level is taken only while it clears min_edge (points) and
    min_return (gain per unit of cash, (f - price) / price)."""
    ok = lambda f, px: f - px >= min_edge - 1e-9 and (f - px) / max(px, 1e-9) >= min_return - 1e-9
    for side in ("yes", "no"):
        if only_side and side != only_side:
            continue
        f = side_fair(fair_yes, side)
        levels = book.buy_levels(side)
        if not levels or not ok(f, levels[0].price):
            continue
        budget = min(max_cost, kelly_cost(f, levels[0].price, kelly_fraction, bankroll))
        qty, cost, limit = 0, 0.0, None
        for lvl in levels:
            if not ok(f, lvl.price):
                break
            take = min(math.floor(lvl.qty * depth_fraction), math.floor((budget - cost) / lvl.price + 1e-9))
            if take <= 0:
                break
            qty, cost, limit = qty + take, cost + take * lvl.price, lvl.price
        if qty > 0:
            return Order(exchange_id, side, "buy", qty, limit, f, reason or f"edge {f - levels[0].price:.3f}")
    return None


def plan_exit(h: Holding, fair_yes: float | None, book: Book, now: float, *, exit_band: float,
              stop_loss: float, max_hold_hours: float, exit_slippage: float) -> Order | None:
    levels = book.sell_levels(h.side)
    if not levels or h.qty < 1:
        return None
    best = levels[0].price
    f = side_fair(fair_yes, h.side) if fair_yes is not None else None
    reason, floor = None, None
    if f is not None and best >= f - exit_band:
        reason, floor = "converged", f - exit_band
    elif f is not None and f <= h.avg_cost - stop_loss:
        reason, floor = "stop", best - exit_slippage
    elif max_hold_hours and now - h.opened_at > max_hold_hours * 3600:
        reason, floor = "timeout", best - exit_slippage
    if reason is None:
        return None
    qty, limit = 0, None
    for lvl in levels:
        if lvl.price < floor - 1e-9 or qty >= h.qty:
            break
        take = min(math.floor(lvl.qty), math.floor(h.qty) - qty)
        if take > 0:
            qty, limit = qty + take, lvl.price
    if qty <= 0:
        return None
    return Order(h.exchange_id, h.side, "sell", qty, limit, f if f is not None else best, reason)
