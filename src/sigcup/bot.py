"""The trading loop: reference prices -> fair values -> exits, then entries -> reports."""
from __future__ import annotations

import json
import math
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .arb import Race, exit_bar, group_races, plan_buy, plan_repair, plan_sell, screen_buy, screen_sell
from .arb import BasketOrder
from .config import Settings
from .ledger import Ledger
from .notify import Notifier
from .pricing import Fair, RefLeg, fair_value, load_map
from .references import KalshiFeed, PolymarketFeed, RefQuote
from .sig_api import ApiError, Book, SigApi
from .strategy import Holding, Order, plan_entry, plan_exit, side_fair
from . import value as V
from .pricing import leg_quote

log = logging.getLogger(__name__)


@dataclass
class Health:
    started: float = field(default_factory=time.time)
    cycles: int = 0
    last_ok: float = 0.0
    consecutive_errors: int = 0
    last_error: str = ""
    ref_ok: dict[str, float] = field(default_factory=dict)
    ref_quotes: dict[str, int] = field(default_factory=dict)
    ref_errors: dict[str, int] = field(default_factory=dict)


@dataclass
class Opportunities:
    """What the market offered during this run, traded or not: the raw material for tuning."""
    best_edge: dict[str, float] = field(default_factory=dict)  # exchange -> best gap seen
    best_arb: dict[str, float] = field(default_factory=dict)   # race -> best Σ YES bids − 1
    top_depth: list[float] = field(default_factory=list)       # shares at the best level, per book read
    priced_cycles: int = 0
    # Beyond the two strategies: things worth a human look
    widest: dict[str, float] = field(default_factory=dict)     # exchange -> widest bid/ask spread seen
    empty: set[str] = field(default_factory=set)               # exchanges seen with no bid or no ask
    yes_basket: dict[str, float] = field(default_factory=dict) # two-party race -> best 1 − Σ YES asks
    disagree: dict[str, float] = field(default_factory=dict)   # exchange -> Kalshi vs Polymarket gap
    first: dict[str, tuple[float, float | None]] = field(default_factory=dict)  # eid -> (fair, Cup mid)
    last: dict[str, tuple[float, float | None]] = field(default_factory=dict)


def _utc_day(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def _midnight(ts: float) -> float:
    d = datetime.fromtimestamp(ts, timezone.utc)
    return d.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()


def _ago(now: float, ts: float) -> str:
    if not ts:
        return "never"
    s = int(now - ts)
    return f"{s}s ago" if s < 120 else f"{s // 60}m ago" if s < 7200 else f"{s // 3600}h ago"


class Bot:
    def __init__(self, s: Settings, api: SigApi, kalshi: KalshiFeed, poly: PolymarketFeed,
                 ledger: Ledger, notifier: Notifier, live: bool = False, clock=time.time):
        self.s, self.api, self.kalshi, self.poly = s, api, kalshi, poly
        self.ledger, self.notifier, self.live, self.clock = ledger, notifier, live, clock
        self.map: dict[str, list[RefLeg]] = load_map(s.map_path)
        self.labels = {eid: legs[0].label or eid for eid, legs in self.map.items()}
        self.quotes: dict[tuple[str, str], RefQuote] = {}
        self.fairs: dict[str, tuple[Fair | None, str]] = {}
        self.prices: dict[str, tuple[float | None, float | None]] = {}
        self.positions: dict[tuple[str, str], float] = {}
        self.health = Health(started=clock())
        self.scaled: dict[str, float] = {}
        self.ladder_anchor: dict[str, tuple[float, float, float]] = {}   # eid -> (placed, touch, fair)
        self.turnover: list[tuple[float, float]] = []                     # (when, SUSQies sold by the allocator)
        self.opps = Opportunities()
        self.races: list[Race] = []
        self.mode_note = "live" if live else "paper"
        self.orders_disabled = ""
        self.cash = s.bankroll
        self._last_races = 0.0
        self._last_ref = 0.0
        self._alerted: set[str] = set()

    # ---- inputs ----

    def refresh_refs(self) -> None:
        refs = {"kalshi": set(), "polymarket": set()}
        for legs in self.map.values():
            for leg in legs:
                refs[leg.source].update(leg.parts)
        for name, feed in (("kalshi", self.kalshi), ("polymarket", self.poly)):
            if not refs[name]:
                continue
            try:
                got = feed.quotes(sorted(refs[name]))
            except Exception as e:
                self.health.ref_errors[name] = self.health.ref_errors.get(name, 0) + 1
                log.warning("%s refresh failed: %s", name, e)
                continue
            self.quotes.update({(name, r): q for r, q in got.items()})
            self.health.ref_ok[name] = self.clock()
            self.health.ref_quotes[name] = len(got)
        self._last_ref = self.clock()

    def refresh_races(self) -> None:
        if not self.s.arb_enabled or self.clock() - self._last_races < self.s.races_refresh_minutes * 60:
            return
        self.races = group_races(self.api.markets())
        for r in self.races:
            for eid in r.exchange_ids:
                self.labels.setdefault(eid, r.label(eid))
        self._last_races = self.clock()
        log.info("arb: %d races with 2+ party markets", len(self.races))

    def resync_from_exchange(self) -> str:
        """Live start-up: rebuild the ledger from the exchange's positions. Even NO holdings across
        every leg of a race become arb baskets; anything else is a gap-trade holding."""
        now = self.clock()
        pos = {(p.exchange_id, p.side): p for p in self.api.positions() if p.qty >= 1 and not p.settled}
        # keep when each holding was opened, so hold-time exits survive the hourly restarts
        opened = {(h.exchange_id, h.side): h.opened_at for h in self.ledger.holdings(None)}
        since = lambda e, side: min(opened.get((e, side), now), now)
        rows, used = [], {}
        for r in self.races:
            legs = [pos.get((e, "no")) for e in r.exchange_ids]
            if all(legs):
                sets = min(p.qty for p in legs)
                for p in legs:
                    rows.append(("arb", p.exchange_id, "no", sets, p.avg_cost, since(p.exchange_id, "no")))
                    used[(p.exchange_id, "no")] = sets
        for key, p in pos.items():
            rest = p.qty - used.get(key, 0.0)
            if rest >= 1:
                rows.append(("conv", p.exchange_id, p.side, rest, p.avg_cost, since(p.exchange_id, p.side)))
        self.ledger.replace_holdings(rows)
        self.ledger.drop_resting()  # the last run's ladder bids were cancelled at its shutdown
        n_arb = len({r[1] for r in rows if r[0] == "arb"})
        note = f"resynced from exchange: {n_arb} arb legs, {sum(1 for r in rows if r[0] == 'conv')} other positions"
        self.ledger.event("INFO", note)
        log.info(note)
        return note

    def free_cash(self) -> float:
        """Uninvested SUSQies: the exchange's account value minus holdings (live), or the bankroll
        minus the cost of what the ledger holds (paper)."""
        if not self.live:
            return self.s.bankroll - sum(h.qty * h.avg_cost for h in self.ledger.holdings(None))
        p = self.api.pnl()
        p = p.get("data", p) if isinstance(p, dict) else {}
        return float(p.get("totalAccountValue", 0)) - float(p.get("totalHoldingsValue", 0))

    def compute_fairs(self) -> None:
        now = self.clock()
        s = self.s
        self.fairs = {eid: fair_value(legs, self.quotes, now, max_age=s.ref_max_age_seconds,
                                      max_spread=s.ref_max_spread, max_disagreement=s.ref_max_disagreement,
                                      min_sources=s.ref_min_sources)
                      for eid, legs in self.map.items()}
        raw = {eid: f.p for eid, (f, _) in self.fairs.items() if f}
        self.scaled = V.race_scaled(raw, [r.exchange_ids for r in self.races]) if s.race_scale else raw

    def fair(self, eid: str) -> float | None:
        return self.scaled.get(eid)

    # ---- risk ----

    def mark_to_market(self) -> float:
        total = 0.0
        for h in self.ledger.holdings(None):
            bid, ask = self.prices.get(h.exchange_id, (None, None))
            mark = bid if h.side == "yes" else (None if ask is None else 1 - ask)
            if mark is not None:
                total += h.qty * (mark - h.avg_cost)
        return total

    def daily_pnl(self) -> float:
        now = self.clock()
        day = _utc_day(now)
        mtm = self.mark_to_market()
        if self.ledger.get("day") != day:
            self.ledger.put("day", day)
            self.ledger.put("mtm_day_start", mtm)
        return self.ledger.realized_since(_midnight(now)) + mtm - float(self.ledger.get("mtm_day_start", "0"))

    def entries_blocked(self) -> str:
        if self.closing():
            return "trading closes soon"
        if self.orders_disabled:
            return self.orders_disabled
        if Path(self.s.kill_switch).exists():
            return f"kill switch file '{self.s.kill_switch}' present"
        pnl = self.daily_pnl()
        if pnl < -self.s.daily_loss_stop:
            return f"daily loss stop hit ({pnl:,.0f} today)"
        return ""

    # ---- one cycle ----

    def cycle(self) -> None:
        s = self.s
        now = self.clock()
        if now - self._last_ref >= (s.night_ref_refresh_seconds if self.night() else s.ref_refresh_seconds):
            self.refresh_refs()
        self.compute_fairs()
        self.refresh_races()

        if self.live:
            self.positions = {(p.exchange_id, p.side): p.qty for p in self.api.positions()}
            for note in self.ledger.reconcile(self.positions, now):
                self.ledger.event("INFO", note)
                log.info(note)

        self.cash = self.free_cash()
        ids = list(dict.fromkeys(list(self.map) + [e for r in self.races for e in r.exchange_ids]))
        self.prices = self.api.prices(ids) if ids else {}
        self.track_opportunities()
        books_left = s.max_books_per_cycle
        pending = self.ledger.pending_exchanges()

        # Exits first: they free capital and never add risk.
        for h in self.ledger.holdings():
            if h.exchange_id in pending or books_left <= 0:
                continue
            bid, ask = self.prices.get(h.exchange_id, (None, None))
            # hold_to_settlement: only the stop-loss can sell (exit band above 1 never triggers)
            kw = dict(exit_band=-1.0 if s.hold_to_settlement else s.exit_band, stop_loss=s.stop_loss,
                      max_hold_hours=0 if s.hold_to_settlement else s.max_hold_hours,
                      exit_slippage=s.exit_slippage)
            fair = self.fair(h.exchange_id)
            if plan_exit(h, fair, Book.top(h.exchange_id, bid, ask), now, **kw) is None:
                continue
            books_left -= 1
            o = plan_exit(h, fair, self.book(h.exchange_id), now, **kw)
            if o:
                self.execute(o)
                pending.add(o.exchange_id)

        self.allocate(pending)
        self.ladder(pending)

        blocked = self.entries_blocked()
        if blocked:
            self.alert_once(f"blocked:{blocked}", f"New entries paused: {blocked}")
        else:
            self._alerted = {a for a in self._alerted if not a.startswith("blocked:")}
        # Risk-free baskets get first call on the book budget; repairs/exits run even when blocked.
        books_left = self.arb(pending, books_left, bool(blocked))
        if not blocked:
            self.enter(pending, books_left)

        if not self.live:
            self.ledger.put("paper_cycles", int(self.ledger.get("paper_cycles", "0")) + 1)
        self.health.cycles += 1
        self.health.last_ok = self.clock()
        self.health.consecutive_errors = 0

    def book(self, eid: str) -> Book:
        b = self.api.book(eid)
        best = (b.asks[:1] or b.bids[:1])
        if best:
            self.opps.top_depth.append(best[0].qty)
        return b

    def track_opportunities(self) -> None:
        o = self.opps
        o.priced_cycles += 1
        for edge, eid, _ in self.gaps():
            if edge > o.best_edge.get(eid, -1.0):
                o.best_edge[eid] = edge
        for r in self.races:
            e = screen_buy(r, self.prices)
            if e is not None and e > o.best_arb.get(r.key, -1.0):
                o.best_arb[r.key] = e
            asks = [self.prices.get(x, (None, None))[1] for x in r.exchange_ids]
            if r.k == 2 and all(a is not None for a in asks):
                o.yes_basket[r.key] = max(o.yes_basket.get(r.key, -1.0), 1 - sum(asks))
        for eid, (bid, ask) in self.prices.items():
            if bid is None or ask is None:
                o.empty.add(eid)
            else:
                o.widest[eid] = max(o.widest.get(eid, 0.0), ask - bid)
            fair = self.fair(eid)
            if fair is not None:
                mid = None if bid is None or ask is None else (bid + ask) / 2
                o.first.setdefault(eid, (fair, mid))
                o.last[eid] = (fair, mid)
        for eid, (f, why) in self.fairs.items():
            if f is None and why.startswith("references disagree by "):
                d = float(why.rsplit(" ", 1)[1])
                o.disagree[eid] = max(o.disagree.get(eid, 0.0), d)

    def opportunity_lines(self) -> list[str]:
        s, o = self.s, self.opps
        edges = sorted(o.best_edge.values(), reverse=True)
        n_hit = sum(1 for e in edges if e >= s.min_edge)
        n_near = sum(1 for e in edges if s.min_edge / 2 <= e < s.min_edge)
        lines = [f"\nOpportunities this run ({o.priced_cycles} priced cycles):",
                 f"  price gaps: {n_hit} markets reached ≥{s.min_edge:g}, {n_near} more reached "
                 f"≥{s.min_edge / 2:g} (near misses), of {len(edges)} with a fair value"]
        best = sorted(o.best_edge.items(), key=lambda kv: -kv[1])[:3]
        if best:
            lines.append("  best gaps: " + ", ".join(f"{self.labels.get(e, e)[:30]} {v:+.3f}" for e, v in best))
        arbs = sorted(o.best_arb.items(), key=lambda kv: -kv[1])
        n_arb = sum(1 for _, v in arbs if v >= s.arb_min_profit)
        if arbs:
            lines.append(f"  arb: {n_arb} races reached ≥{s.arb_min_profit:g}; best: "
                         + ", ".join(f"{k[:25]} {v:+.3f}" for k, v in arbs[:3]))
        if o.top_depth:
            d = sorted(o.top_depth)
            lines.append(f"  depth at best price: median {d[len(d) // 2]:,.0f} shares, "
                         f"max {d[-1]:,.0f} ({len(d)} books read)")
        return lines + self.other_opportunity_lines()

    def other_opportunity_lines(self) -> list[str]:
        """Not traded by the bot; candidates for new strategies or manual trades."""
        o, name = self.opps, lambda e: self.labels.get(e, e)[:30]
        out = ["\nOther opportunities (not traded, for review):"]
        wide = sorted(((v, e) for e, v in o.widest.items() if v >= 0.08), reverse=True)
        if wide:
            out.append(f"  wide spreads ≥0.08 ({len(wide)} markets; resting quotes could earn the spread): "
                       + ", ".join(f"{name(e)} {v:.3f}" for v, e in wide[:4]))
        if o.empty:
            out.append(f"  one-sided/empty books: {len(o.empty)} markets (first quote sets the price): "
                       + ", ".join(name(e) for e in sorted(o.empty)[:4]))
        yb = sorted(((v, k) for k, v in o.yes_basket.items() if v > 0), reverse=True)
        if yb:
            out.append("  two-party races with Σ YES asks < 1 (pays 1 unless a third party wins): "
                       + ", ".join(f"{k[:25]} +{v:.3f}" for v, k in yb[:4]))
        moves = []
        for e, (f0, m0) in o.first.items():
            f1, m1 = o.last[e]
            if abs(f1 - f0) >= 0.03:
                follow = "" if m0 is None or m1 is None else f", Cup {m1 - m0:+.3f}"
                moves.append((abs(f1 - f0), f"{name(e)} ref {f1 - f0:+.3f}{follow}"))
        if moves:
            out.append("  reference moved ≥3 pts this run (news?): " + "; ".join(m for _, m in sorted(moves, reverse=True)[:4]))
        if o.disagree:
            out.append("  Kalshi vs Polymarket disagree (skipped; one is stale or mis-mapped): "
                       + ", ".join(f"{name(e)} {v:.3f}" for e, v in sorted(o.disagree.items(), key=lambda kv: -kv[1])[:4]))
        unmapped = [e for r in self.races for e in r.exchange_ids if e not in self.map]
        if unmapped:
            out.append(f"  {len(unmapped)} Cup markets have no Kalshi/Polymarket mapping (gap trades can't see them)")
        if len(out) == 1:
            out.append("  none")
        return out

    def gaps(self) -> list[tuple[float, str, str]]:
        """(edge, exchange_id, side) for every priced market, best first."""
        out = []
        for eid in self.map:
            fair = self.fair(eid)
            bid, ask = self.prices.get(eid, (None, None))
            if fair is None:
                continue
            if ask is not None:
                out.append((fair - ask, eid, "yes"))
            if bid is not None:
                out.append((bid - fair, eid, "no"))
        return sorted(out, reverse=True)

    def reserve(self) -> float:
        """Cash no new trade may touch: CASH_RESERVE, plus ELECTION_RESERVE until election night."""
        s = self.s
        if s.election_reserve and s.election_night_start:
            start = datetime.fromisoformat(s.election_night_start.replace("Z", "+00:00")).timestamp()
            if self.clock() < start:
                return s.cash_reserve + s.election_reserve
        return s.cash_reserve

    # ---- time windows ----

    def _ts(self, iso: str) -> float | None:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() if iso else None

    def night(self) -> bool:
        """Inside the election-night window: from ELECTION_NIGHT_START until trading closes."""
        s, now = self.s, self.clock()
        start, close = self._ts(s.election_night_start), self._ts(s.trading_close)
        return bool(s.night_enabled and start and now >= start and (close is None or now < close))

    def closing(self) -> bool:
        close = self._ts(self.s.trading_close)
        return close is not None and self.clock() >= close - self.s.close_buffer_minutes * 60

    # ---- exposure ----

    def exposure(self) -> tuple[dict[str, float], dict[str, float], dict[str, str]]:
        """(cost per race, cost per state, race of each exchange): gap-trade holdings and resting ladder bids
        (arb baskets are hedged, so they don't count against race or state caps)."""
        race_of = {e: self.labels.get(e, e).split(" [")[0] for e in set(self.map) | set(self.labels)}
        race_of.update({e: r.key for r in self.races for e in r.exchange_ids})
        race_cost: dict[str, float] = {}
        state_cost: dict[str, float] = {}
        items = [(h.exchange_id, h.qty * h.avg_cost) for h in self.ledger.holdings("conv")]
        items += [(r[1], r[3] * r[4]) for r in self.ledger.resting(self.clock())]
        for e, c in items:
            race = race_of.get(e, e)
            race_cost[race] = race_cost.get(race, 0.0) + c
            st = V.state_of(race)
            if st:
                state_cost[st] = state_cost.get(st, 0.0) + c
        return race_cost, state_cost, race_of

    def side_price(self, eid: str, side: str) -> float | None:
        """Best price to buy `side` now, from bulk prices."""
        bid, ask = self.prices.get(eid, (None, None))
        return ask if side == "yes" else (None if bid is None else round(1 - bid, 6))

    def ranked_gaps(self) -> list[tuple[float, float, str, str]]:
        """(return on cash, points, exchange, side) for every buy clearing MIN_EDGE and MIN_RETURN, best return
        first (grissou: every opportunity on one scale)."""
        s, out = self.s, []
        for pts, eid, side in self.gaps():
            px, f = self.side_price(eid, side), self.fair(eid)
            if px is None or f is None or pts < s.min_edge:
                continue
            ret = V.edge(side_fair(f, side), px)
            if ret >= s.min_return:
                out.append((ret, pts, eid, side))
        return sorted(out, reverse=True)

    def night_candidates(self) -> list[tuple[float, str, str, float]]:
        """Election night (Bowen26 rule): (return, exchange, side, reference bid) where every fresh reference bids
        the side at NIGHT_MIN_REF_BID+ and the Cup still asks NIGHT_MIN_GAP below that."""
        s, now, out = self.s, self.clock(), []
        if not self.night():
            return out
        max_age = 2 * s.night_ref_refresh_seconds + 15
        for eid, legs in self.map.items():
            qs = [leg_quote(leg, self.quotes, now) for leg in legs]
            if not qs or any(q is None or q.bid is None or q.ask is None or now - q.ts > max_age for q in qs):
                continue
            for side in ("yes", "no"):
                ref = min(q.bid if side == "yes" else 1 - q.ask for q in qs)
                px = self.side_price(eid, side)
                if ref >= s.night_min_ref_bid - 1e-9 and px is not None and px <= ref - s.night_min_gap + 1e-9:
                    out.append((V.edge(ref, px), eid, side, ref))
        return sorted(out, reverse=True)

    def enter(self, pending: set[str], books_left: int) -> None:
        s = self.s
        cost = self.ledger.cost_by_exchange()
        total = sum(cost.values())
        race_cost, state_cost, race_of = self.exposure()
        held = {(h.exchange_id, h.side) for h in self.ledger.holdings()}
        arb_held = {h.exchange_id for h in self.ledger.holdings("arb")}
        night = [(ret, eid, side, ref) for ret, eid, side, ref in self.night_candidates()]
        day = [(ret, eid, side, None) for ret, _, eid, side in self.ranked_gaps()]
        for ret, eid, side, ref in night + day:
            if books_left <= 0:
                break
            other = "no" if side == "yes" else "yes"
            if eid in pending or (eid, other) in held or eid in arb_held:
                continue
            race = race_of.get(eid, eid)
            st = V.state_of(race)
            race_cap = s.night_race_cost if ref is not None else s.max_race_cost
            room = min(s.max_order_cost, s.max_market_cost - cost.get(eid, 0.0),
                       min(s.max_total_cost, s.bankroll - s.cash_reserve) - total,
                       self.cash - self.reserve(),
                       (race_cap - race_cost.get(race, 0.0)) if race_cap else float("inf"),
                       (s.state_max_cost - state_cost.get(st, 0.0)) if s.state_max_cost and st else float("inf"))
            if ref is not None:  # called races: the per-market caps give way to the race cap
                room = min(s.night_race_cost - race_cost.get(race, 0.0), self.cash - self.reserve())
            if room <= 0:
                continue
            books_left -= 1
            if ref is not None:
                fy = ref if side == "yes" else 1 - ref
                o = plan_entry(eid, fy, self.book(eid), min_edge=s.night_min_gap, depth_fraction=1.0,
                               max_cost=room, kelly_fraction=1.0, bankroll=s.bankroll, only_side=side,
                               reason=f"election night: refs bid {ref:.3f}")
            else:
                o = plan_entry(eid, self.fair(eid), self.book(eid), min_edge=s.min_edge,
                               depth_fraction=s.depth_fraction, max_cost=room, kelly_fraction=s.kelly_fraction,
                               bankroll=s.bankroll, min_return=s.min_return, only_side=side,
                               reason=f"edge {ret:.1%} on cash")
            if o:
                self.execute(o)
                pending.add(eid)
                total += o.cost
                self.cash -= o.cost
                cost[eid] = cost.get(eid, 0.0) + o.cost
                race_cost[race] = race_cost.get(race, 0.0) + o.cost
                if st:
                    state_cost[st] = state_cost.get(st, 0.0) + o.cost

    # ---- harvest ladder (grissou ladder.py) ----

    def ladder_fills(self) -> None:
        """Credit fills of our resting ladder bids, matched by order id from the fills list."""
        if not self.ledger.resting():
            return
        seen = int(self.ledger.get("fill_seen", "0") or 0)
        fills = self.api.fills()
        for f in sorted(fills, key=lambda x: int(x.get("id", 0))):
            fid = int(f.get("id", 0))
            if fid <= seen:
                continue
            note = self.ledger.apply_resting_fill(str(f.get("orderId")), abs(float(f.get("quantity") or 0)),
                                                  float(f.get("price") or 0), self.clock())
            if note:
                self.ledger.event("TRADE", f"[live] {note}")
                log.info(note)
        if fills:
            self.ledger.put("fill_seen", max(seen, max(int(f.get("id", 0)) for f in fills)))

    def cancel_ladder(self, eid: str | None = None) -> None:
        for r in self.ledger.resting():
            if eid is None or r[1] == eid:
                try:
                    self.api.cancel(r[0])
                except ApiError as e:
                    log.info("cancel %s: %s", r[0], e)
                self.ledger.drop_resting(r[0])
                self.ladder_anchor.pop(r[1], None)

    def ladder(self, pending: set[str]) -> None:
        """Rest bids under favourites' touch (fair >= LADDER_FAVOURITE_P) at 0/2/4/6c below it, 8%+ edge on
        cash, inside LADDER_BUDGET; re-quote a market when its touch or fair moves more than 1c, or every
        LADDER_REQUOTE_SECONDS. Off on election night and near the close: resting bids on favourites are
        exactly what gets hit when a race turns."""
        s, now = self.s, self.clock()
        start = self._ts(s.election_night_start)
        if not (s.ladder_enabled and self.live) or self.closing() or (start and now >= start - 3600):
            if self.ledger.resting():
                self.cancel_ladder()
            return
        self.ladder_fills()
        for r in self.ledger.resting():
            if r[6] <= now:  # expired at the exchange
                self.ledger.drop_resting(r[0])
        race_cost, state_cost, race_of = self.exposure()
        held_other = {(h.exchange_id, "no" if h.side == "yes" else "yes") for h in self.ledger.holdings(None)}
        arb_held = {h.exchange_id for h in self.ledger.holdings("arb")}
        offsets = [float(x) for x in s.ladder_offsets.split(",") if x.strip()]
        wanted: list[V.Level] = []
        for eid in self.map:
            fy = self.fair(eid)
            bid, ask = self.prices.get(eid, (None, None))
            race = race_of.get(eid, eid)
            st = V.state_of(race)
            if fy is None or eid in pending or eid in arb_held:
                continue
            lvls = V.ladder_levels(eid, fy, Book.top(eid, bid, ask), favourite_p=s.ladder_favourite_p,
                                   offsets=offsets, min_edge=s.ladder_min_edge, level_cost=s.ladder_level_cost)
            room = min((s.max_race_cost - race_cost.get(race, 0.0)) if s.max_race_cost else float("inf"),
                       (s.state_max_cost - state_cost.get(st, 0.0)) if s.state_max_cost and st else float("inf"))
            # resting bids already in this race/state count in race_cost; a market's levels must fit what's left
            mine = sum(r[3] * r[4] for r in self.ledger.resting(now) if r[1] == eid)
            lvls = V.within_budget([l for l in lvls if (l.exchange_id, l.side) not in held_other], room + mine)
            wanted += [l for l in lvls if l.cost >= 100]   # no dust bids
        spendable = self.cash - self.reserve() + min(s.ladder_from_reserve, s.election_reserve)
        wanted = [l for l in V.within_budget(wanted, min(s.ladder_budget, max(0.0, spendable))) if l.cost >= 100]
        by_eid: dict[str, list[V.Level]] = {}
        for lv in wanted:
            by_eid.setdefault(lv.exchange_id, []).append(lv)
        resting = {}
        for r in self.ledger.resting():
            resting.setdefault(r[1], []).append(r)
        for eid in set(resting) | set(by_eid):
            fy, (bid, ask) = self.fair(eid), self.prices.get(eid, (None, None))
            want = by_eid.get(eid, [])
            side = want[0].side if want else None
            touch = None if side is None else V.side_touch(Book.top(eid, bid, ask), side)[0]
            a = self.ladder_anchor.get(eid)
            keep = (a is not None and want and now - a[0] < s.ladder_requote_seconds
                    and abs((touch or 0) - a[1]) <= 0.01 + 1e-9 and abs((fy or 0) - a[2]) <= 0.01 + 1e-9)
            if keep:
                continue
            if eid in resting:
                self.cancel_ladder(eid)
            for lv in want:
                label = self.labels.get(eid, eid)
                msg = f"ladder BUY {lv.side.upper()} {lv.qty} {label} @ {lv.price:.3f} (edge {lv.edge:.1%})"
                ttl = int(s.ladder_requote_seconds + 120)
                resp = self.send(msg, lambda lv=lv: self.api.place_order(eid, lv.side, "buy", lv.qty, lv.price, ttl))
                oid = resp and (resp.get("orderId") or (resp.get("data") or {}).get("orderId"))
                if oid:
                    self.ledger.add_resting(oid, lv, label, side_fair(fy, lv.side), now, ttl)
                    self.ledger.event("TRADE", f"[live] rest {msg}")
            if want:
                self.ladder_anchor[eid] = (now, touch or 0.0, fy or 0.0)
        for r in self.ledger.resting():
            pending.add(r[1])  # no immediate orders where we rest: fills there are matched by order id
        self.cash -= sum(r[3] * r[4] for r in self.ledger.resting())

    # ---- allocator (grissou value.py Allocator) ----

    def allocate(self, pending: set[str]) -> None:
        """Hourly (every 5 min on election night): if the best buy can't be funded, sell the holdings with the
        least edge left, never more than ALLOC_SELL_MARGIN below fair, when the buy beats them by
        ALLOC_MIN_GAIN (2 points on election night). The freed cash goes to the normal entry step."""
        s, now = self.s, self.clock()
        night = self.night()
        interval = 300 if night else s.alloc_interval_seconds
        if not s.alloc_enabled or self.closing() or now - float(self.ledger.get("alloc_last", "0")) < interval:
            return
        self.ledger.put("alloc_last", now)
        cands = [(ret, eid, side) for ret, eid, side, _ in self.night_candidates()]
        cands += [(ret, eid, side) for ret, _, eid, side in self.ranked_gaps()]
        if not cands:
            return
        best = max(c[0] for c in cands)
        spare = max(0.0, self.cash - self.reserve())
        need = min(s.alloc_max_turnover, s.max_order_cost * 3) - spare
        self.turnover = [(w, u) for w, u in self.turnover if w > now - 3600]
        left = s.alloc_max_turnover - sum(u for _, u in self.turnover)
        if need < 20 or left < 20:
            return
        pinned = {e for r in self.races if r.key in {x.strip() for x in s.alloc_pinned.split(",")}
                  for e in r.exchange_ids}
        busy = pending | {c[1] for c in cands}
        sellers = V.swap_sellers([h for h in self.ledger.holdings() if h.exchange_id not in busy],
                                 self.scaled, self.prices, max_keep_edge=s.alloc_max_keep_edge,
                                 sell_margin=s.alloc_sell_margin, pinned=pinned)
        min_gain = 0.02 if night else s.alloc_min_gain
        for sl, n in V.plan_swap_sales(sellers, best, need, left, min_gain):
            o = Order(sl.exchange_id, sl.side, "sell", n, sl.price, sl.fair,
                      f"swap: keep {sl.keep_edge:.1%} < buy {best:.1%}")
            self.execute(o)
            pending.add(sl.exchange_id)
            self.turnover.append((now, n * sl.price))

    def arb(self, pending: set[str], books_left: int, blocked: bool) -> int:
        """Short-term NO-basket trading: repair uneven baskets; sell baskets for a quick profit, when
        held too long, or to free cash; buy new baskets when a race's YES bids sum above
        1 + ARB_MIN_PROFIT, using only cash above ARB_CASH_FLOOR."""
        s, now = self.s, self.clock()
        if not s.arb_enabled:
            return books_left
        held = {h.exchange_id: h for h in self.ledger.holdings("arb")}
        conv_busy = {h.exchange_id for h in self.ledger.holdings("conv")}
        capital = sum(h.qty * h.avg_cost for h in held.values())
        # SUSQies to free by selling baskets: over the arb budget, or cash below the floor
        to_free = max(capital - s.arb_max_capital, s.arb_cash_floor - self.cash, 0.0) if s.arb_unwind_for_cash else 0.0

        def exit_value(r: Race) -> float:  # sale proceeds minus cost per set; best exits first
            v = screen_sell(r, self.prices)
            if v is None or not all(e in held for e in r.exchange_ids):
                return -9.0
            return v - sum(held[e].avg_cost for e in r.exchange_ids)
        races = sorted(self.races, key=lambda r: (not any(e in held for e in r.exchange_ids), -exit_value(r)))

        for race in races:
            ids = race.exchange_ids
            if any(e in pending for e in ids) or books_left < race.k:
                continue
            qtys = [held[e].qty if e in held else 0.0 for e in ids]
            key = f"unhedged:{race.key}"
            if max(qtys) - min(qtys) >= 1:
                since = float(self.ledger.get(key) or 0) or now
                self.ledger.put(key, since)
                unwind = now - since > s.arb_repair_minutes * 60
                books_left -= race.k
                books = {e: self.book(e) for e in ids}
                orders = plan_repair(race, held, books, slippage=s.arb_repair_slippage, unwind=unwind)
                if unwind:
                    self.alert_once(key, f"{race.key}: basket uneven for {s.arb_repair_minutes:g} min, "
                                         f"selling the excess legs")
                for o in orders:
                    self.execute(o, "arb")
                    pending.add(o.exchange_id)
                continue
            if self.ledger.get(key):
                self.ledger.put(key, "")
                self._alerted.discard(key)
            sets = int(min(qtys))
            if sets >= 1:
                cost = sum(held[e].avg_cost for e in ids)
                bar, max_sell, reason = exit_bar(race, cost, s.arb_min_profit, s.arb_exit_profit), sets, "arb take-profit"
                opened = min(held[e].opened_at for e in ids)
                if to_free > 0:
                    bar, reason = min(bar, cost - s.arb_unwind_max_loss), "arb unwind (free cash)"
                    max_sell = min(sets, math.ceil(to_free / max(cost, 0.01)))
                elif s.arb_max_hold_hours and now - opened > s.arb_max_hold_hours * 3600:
                    bar, reason = min(bar, cost - s.arb_unwind_max_loss), "arb timeout"
                top = screen_sell(race, self.prices)
                if top is not None and top >= bar:
                    books_left -= race.k
                    o = plan_sell(race, {e: self.book(e) for e in ids}, sets_held=max_sell, bar=bar,
                                  reason=reason)
                    if o:
                        self.execute_basket(o)
                        pending.update(ids)
                        freed = o.sets * cost
                        to_free, capital, self.cash = to_free - freed, capital - freed, self.cash + o.sets * o.per_set
                        continue
            if blocked or to_free > 0 or any(e in conv_busy for e in ids):
                continue
            edge = screen_buy(race, self.prices)
            # ARB_MAX_SETS caps the sets held per race, not per order (paper re-bought one book to 18k)
            budget = min(s.arb_max_capital - capital, self.cash - max(s.arb_cash_floor, self.reserve()))
            room = min(int(budget / max(race.k - 1, 1)), s.arb_max_sets - sets)
            if edge is None or edge < s.arb_min_profit or room < 1:
                continue
            books_left -= race.k
            o = plan_buy(race, {e: self.book(e) for e in ids}, min_profit=s.arb_min_profit,
                         max_sets=min(s.arb_max_sets, room), depth_fraction=s.arb_depth_fraction)
            if o:
                self.execute_basket(o)
                pending.update(ids)
                capital += o.sets * o.per_set
                self.cash -= o.sets * o.per_set
        return books_left

    def send(self, what: str, place):
        """Place an order; a rejection is logged instead of failing the whole cycle. A permission
        error (e.g. a key without the `trade` scope) stops all order sending and alerts once."""
        try:
            return place()
        except ApiError as e:
            self.ledger.event("ERROR", f"order rejected: {what}: {e}"[:500])
            log.error("order rejected: %s: %s", what, e)
            if e.status in (401, 403):
                self.orders_disabled = f"orders refused by the exchange ({e.code})"
                self.alert_once("orders_disabled", f"Bot can't place orders: {e}")
            return None

    def execute_basket(self, b: BasketOrder) -> None:
        legs = b.leg_orders()
        k = b.race.k
        what = (f"{b.action.upper()} NO basket {b.race.key} x{b.sets} @ {b.per_set:.3f}/set "
                + (f"(locks {k - 1 - b.per_set:+.3f}/set)" if b.action == "buy" else ""))
        if not self.live:
            for leg in legs:  # paper fills at the average price walked
                self.ledger.record_fill(Order(leg.exchange_id, "no", leg.action, leg.qty, leg.fair, leg.fair,
                                              leg.reason), leg.qty, self.labels.get(leg.exchange_id, ""),
                                        self.clock(), "arb")
            self.ledger.event("TRADE", f"[paper] {what}")
            log.info("[paper] %s", what)
            return
        ttl = self.s.order_ttl_seconds
        resp = self.send(what, lambda: self.api.place_multi_leg(
            [{"exchangeId": l.exchange_id, "side": "no", "action": l.action, "quantity": l.qty,
              "price": l.price} for l in legs], ttl))
        if resp is None:
            return
        for leg in legs:
            self.ledger.add_pending(leg, self.labels.get(leg.exchange_id, ""),
                                    self.positions.get((leg.exchange_id, "no"), 0.0), ttl,
                                    json.dumps(resp, default=str)[:2000], self.clock(), "arb")
        self.ledger.event("TRADE", f"[live] sent {what}")
        log.info("[live] sent %s", what)

    def execute(self, o: Order, strategy: str = "conv") -> None:
        label = self.labels.get(o.exchange_id, o.exchange_id)
        msg = (f"{o.action.upper()} {o.side.upper()} {o.qty} {label} @ {o.price:.3f} "
               f"(fair {o.fair:.3f}, {o.reason})")
        if not self.live:
            realized = self.ledger.record_fill(o, o.qty, label, self.clock(), strategy)
            self.ledger.event("TRADE", f"[paper] {msg}" + (f" realized {realized:+.0f}" if o.action == "sell" else ""))
            log.info("[paper] %s", msg)
            return
        before = self.positions.get((o.exchange_id, o.side), 0.0)
        ttl = self.s.order_ttl_seconds
        resp = self.send(msg, lambda: self.api.place_order(o.exchange_id, o.side, o.action, o.qty, o.price, ttl))
        if resp is None:
            return
        self.ledger.add_pending(o, label, before, ttl, json.dumps(resp, default=str)[:2000], self.clock(), strategy)
        self.ledger.event("TRADE", f"[live] sent {msg}")
        log.info("[live] sent %s", msg)

    # ---- reporting ----

    def alert_once(self, key: str, text: str) -> None:
        if key in self._alerted:
            return
        self._alerted.add(key)
        self.ledger.event("ALERT", text)
        self.notifier.send("⚠️ SIG Cup bot alert", text)

    def report(self) -> str:
        s, h, now = self.s, self.health, self.clock()
        since = now - s.report_interval_hours * 3600
        up = int(now - h.started)
        healthy = h.last_ok and now - h.last_ok < max(120, 6 * s.poll_seconds)
        lines = [
            f"Mode: {'LIVE' if self.live else 'PAPER'} ({self.mode_note}) | "
            f"{datetime.fromtimestamp(now, timezone.utc):%Y-%m-%d %H:%M} UTC",
            f"Health: {'OK' if healthy else 'DEGRADED'} | up {up // 3600}h{up % 3600 // 60:02d}m | "
            f"cycles {h.cycles} | last good cycle {_ago(now, h.last_ok)} | consecutive errors {h.consecutive_errors}",
            f"SIG API: reads {self.api.reads.used}/{self.api.reads.per_minute}/min, "
            f"writes {self.api.writes.used}/{self.api.writes.per_minute}/min, errors total {self.api.error_count}",
        ]
        if h.last_error:
            lines.append(f"Last error: {h.last_error[:200]}")
        for src in ("kalshi", "polymarket"):
            if src in h.ref_ok or src in h.ref_errors:
                lines.append(f"{src}: last ok {_ago(now, h.ref_ok.get(src, 0))}, "
                             f"{h.ref_quotes.get(src, 0)} quotes, {h.ref_errors.get(src, 0)} failures")
        priced = sum(1 for f, _ in self.fairs.values() if f)
        lines.append(f"Markets: {len(self.map)} mapped, {priced} with a fair value")
        blocked = self.entries_blocked()
        lines.append(f"Entries: {'PAUSED — ' + blocked if blocked else 'active'}")

        lines.append(f"Arb: {len(self.races)} races watched" if s.arb_enabled else "Arb: off")
        realized_window = self.ledger.realized_since(since)
        lines.append(f"Bot P&L: realized {realized_window:+,.0f} (last {s.report_interval_hours:g}h), "
                     f"{self.ledger.realized_since(_midnight(now)):+,.0f} today, "
                     f"{self.ledger.realized_since(0):+,.0f} all-time | open MTM {self.mark_to_market():+,.0f}")
        try:
            pnl = self.api.pnl()
            pnl = pnl.get("data", pnl) if isinstance(pnl, dict) else {}
            scalars = {k: v for k, v in pnl.items() if isinstance(v, (int, float, str)) and k != "period"}
            if scalars:
                lines.append("Account: " + ", ".join(f"{k}={v}" for k, v in list(scalars.items())[:8]))
        except Exception as e:
            lines.append(f"Account P&L unavailable: {e}")

        holdings = self.ledger.holdings()
        lines.append(f"\nOpen positions ({len(holdings)}):")
        for hd in holdings:
            bid, ask = self.prices.get(hd.exchange_id, (None, None))
            mark = bid if hd.side == "yes" else (None if ask is None else 1 - ask)
            fair = self.fair(hd.exchange_id)
            lines.append(f"  {self.labels.get(hd.exchange_id, hd.exchange_id)[:40]:40} {hd.side.upper():3} "
                         f"{hd.qty:>6.0f} @{hd.avg_cost:.3f} mark {_p(mark)} "
                         f"fair {_p(None if fair is None else side_fair(fair, hd.side))} "
                         f"held {_ago(now, hd.opened_at).replace(' ago', '')}")
        fills = self.ledger.fills_since(since)
        lines.append(f"\nTrades last {s.report_interval_hours:g}h ({len(fills)}):")
        for ts, strat, label, side, action, qty, price, fair, reason, realized in fills[-25:]:
            r = f" P&L {realized:+.0f}" if action == "sell" else ""
            lines.append(f"  {datetime.fromtimestamp(ts, timezone.utc):%H:%M} {strat} {action.upper()} {side.upper()} "
                         f"{qty:g} {label[:35]} @{price:.3f} ({reason}){r}")
        arb_held = {h.exchange_id: h for h in self.ledger.holdings("arb")}
        baskets = [r for r in self.races if any(e in arb_held for e in r.exchange_ids)]
        lines.append(f"\nArb baskets held ({len(baskets)}):")
        for r in baskets:
            q = [arb_held[e].qty if e in arb_held else 0 for e in r.exchange_ids]
            cost = sum(arb_held[e].avg_cost for e in r.exchange_ids if e in arb_held)
            now_val = screen_sell(r, self.prices)
            even = "" if max(q) - min(q) < 1 else f" UNEVEN {q}"
            lines.append(f"  {r.key[:40]:40} {min(q):>6.0f} sets cost {cost:.3f} pays ≥{r.k - 1} "
                         f"sell-now {_p(now_val)}{even}")
        near = sorted(((screen_buy(r, self.prices), r.key) for r in self.races
                       if screen_buy(r, self.prices) is not None), reverse=True)[:3]
        if near:
            lines.append("Closest arb races (Σ YES bids − 1; trades at ≥ "
                         f"{s.arb_min_profit:g}): " + ", ".join(f"{k} {e:+.3f}" for e, k in near))
        lines += self.value_lines()
        lines += self.opportunity_lines()
        lines.append("\nLargest gaps now (edge = fair − price to buy):")
        for edge, eid, side in self.gaps()[:5]:
            lines.append(f"  {self.labels.get(eid, eid)[:40]:40} buy {side.upper():3} edge {edge:+.3f}")
        alerts = self.ledger.events_since(since)
        if alerts:
            lines.append(f"\nAlerts/errors last {s.report_interval_hours:g}h ({len(alerts)}):")
            lines += [f"  {datetime.fromtimestamp(t, timezone.utc):%H:%M} {lvl} {m[:150]}" for t, lvl, m in alerts[-10:]]
        return "\n".join(lines)

    def value_lines(self) -> list[str]:
        """Ladder, allocator, election-night state, state exposure and the national-swing stress test."""
        s, now = self.s, self.clock()
        since = now - s.report_interval_hours * 3600
        out = ["\nValue book:"]
        rest = self.ledger.resting(now)
        lf = [f for f in self.ledger.fills_since(since) if f[8] == "ladder"]
        if s.ladder_enabled:
            out.append(f"  ladder: {len(rest)} bids resting ({sum(r[3] * r[4] for r in rest):,.0f} SUSQies) on "
                       f"{len({r[1] for r in rest})} markets; {len(lf)} fills last {s.report_interval_hours:g}h "
                       f"(expected gain {sum(f[5] * (f[7] - f[6]) for f in lf):+,.0f})")
        sw = [f for f in self.ledger.fills_since(since) if str(f[8]).startswith("swap")]
        if s.alloc_enabled:
            out.append(f"  allocator: {len(sw)} swap sales last {s.report_interval_hours:g}h "
                       f"({sum(f[5] * f[6] for f in sw):,.0f} SUSQies freed)")
        if s.night_enabled:
            out.append(f"  election night: {'ON' if self.night() else 'from ' + s.election_night_start}, "
                       f"{len(self.night_candidates())} called races where the Cup lags now")
        _, state_cost, _ = self.exposure()
        if state_cost:
            top = sorted(state_cost.items(), key=lambda kv: -kv[1])[:4]
            out.append("  biggest states: " + ", ".join(f"{k} {v:,.0f}" for k, v in top)
                       + (f" (cap {s.state_max_cost:,.0f})" if s.state_max_cost else ""))
        party = {e: p for r in self.races for e, p in r.legs}
        hs = [(party.get(h.exchange_id, ""), h.side, h.qty, self.fair(h.exchange_id))
              for h in self.ledger.holdings(None) if self.fair(h.exchange_id) is not None]
        if hs:
            r_up, d_up = V.swing_value_change(hs, s.swing_shock)
            ev = sum(q * side_fair(fy, sd) for _, sd, q, fy in hs)
            out.append(f"  holdings expected value at Kalshi odds {ev:,.0f}; national swing "
                       f"±{s.swing_shock * 100:.0f} pts: R wave {r_up:+,.0f}, D wave {d_up:+,.0f}")
        return out if len(out) > 1 else []

    def send_report(self) -> None:
        self.notifier.send("📊 SIG Cup bot report", self.report())
        self.ledger.put("last_report", self.clock())

    # ---- main loop ----

    def run(self, minutes: float = 0, report_file: str = "") -> None:
        """Loop until stopped, or for `minutes` (scheduled runs), then write the final report."""
        s = self.s
        deadline = self.clock() + minutes * 60 if minutes else None
        if deadline is None:
            self.notifier.send("🤖 SIG Cup bot started",
                               f"Mode {'LIVE' if self.live else 'PAPER'}, {len(self.map)} mapped markets, "
                               f"reports every {s.report_interval_hours:g}h, channels: {', '.join(self.notifier.channels) or 'log only'}")
        if not self.map:
            log.warning("market map %s has no enabled rows: nothing to trade", s.map_path)
        if self.live:
            self.refresh_races()
            self.resync_from_exchange()
        try:
            while deadline is None or self.clock() < deadline:
                try:
                    self.cycle()
                    delay = s.night_poll_seconds if self.night() else s.poll_seconds
                except Exception as e:
                    h = self.health
                    h.consecutive_errors += 1
                    h.last_error = f"{type(e).__name__}: {e}"
                    log.exception("cycle failed")
                    self.ledger.event("ERROR", h.last_error[:500])
                    if h.consecutive_errors == 5:
                        self.notifier.send("⚠️ SIG Cup bot failing", f"5 cycles in a row failed. Last: {h.last_error}")
                    delay = min(s.poll_seconds * 2 ** min(h.consecutive_errors, 5), 300)
                    if deadline is not None:
                        delay = max(0.0, min(delay, deadline - self.clock()))
                Path(s.db_path).with_name("heartbeat").write_text(str(int(self.clock())))
                if self.clock() - float(self.ledger.get("last_report", "0")) >= s.report_interval_hours * 3600:
                    try:
                        self.send_report()
                    except Exception:
                        log.exception("report failed")
                time.sleep(delay)
        except KeyboardInterrupt:
            pass
        finally:
            if self.live:
                try:
                    self.api.cancel_all()
                except Exception as e:
                    log.error("cancel-all on shutdown failed: %s", e)
            final = self.report()
            if report_file:
                Path(report_file).parent.mkdir(parents=True, exist_ok=True)
                Path(report_file).write_text(final + "\n")
            if deadline is None:
                self.notifier.send("🛑 SIG Cup bot stopped", final)


def _p(x: float | None) -> str:
    return "  -  " if x is None else f"{x:.3f}"
