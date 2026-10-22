"""The trading loop: reference prices -> fair values -> exits, then entries -> reports."""
from __future__ import annotations

import json
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
from .sig_api import Book, SigApi
from .strategy import Holding, Order, plan_entry, plan_exit, side_fair

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
        self.opps = Opportunities()
        self.races: list[Race] = []
        self.mode_note = "live" if live else "paper"
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

    def compute_fairs(self) -> None:
        now = self.clock()
        s = self.s
        self.fairs = {eid: fair_value(legs, self.quotes, now, max_age=s.ref_max_age_seconds,
                                      max_spread=s.ref_max_spread, max_disagreement=s.ref_max_disagreement,
                                      min_sources=s.ref_min_sources)
                      for eid, legs in self.map.items()}

    def fair(self, eid: str) -> float | None:
        f = self.fairs.get(eid, (None, ""))[0]
        return f.p if f else None

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
        if now - self._last_ref >= s.ref_refresh_seconds:
            self.refresh_refs()
        self.compute_fairs()
        self.refresh_races()

        if self.live:
            self.positions = {(p.exchange_id, p.side): p.qty for p in self.api.positions()}
            for note in self.ledger.reconcile(self.positions, now):
                self.ledger.event("INFO", note)
                log.info(note)

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
            kw = dict(exit_band=s.exit_band, stop_loss=s.stop_loss, max_hold_hours=s.max_hold_hours,
                      exit_slippage=s.exit_slippage)
            fair = self.fair(h.exchange_id)
            if plan_exit(h, fair, Book.top(h.exchange_id, bid, ask), now, **kw) is None:
                continue
            books_left -= 1
            o = plan_exit(h, fair, self.book(h.exchange_id), now, **kw)
            if o:
                self.execute(o)
                pending.add(o.exchange_id)

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

    def enter(self, pending: set[str], books_left: int) -> None:
        s = self.s
        cost = self.ledger.cost_by_exchange()
        total = sum(cost.values())
        held = {(h.exchange_id, h.side) for h in self.ledger.holdings()}
        arb_held = {h.exchange_id for h in self.ledger.holdings("arb")}
        for edge, eid, side in self.gaps():
            if edge < s.min_edge or books_left <= 0:
                break
            other = "no" if side == "yes" else "yes"
            if eid in pending or (eid, other) in held or eid in arb_held:
                continue
            room = min(s.max_order_cost, s.max_market_cost - cost.get(eid, 0.0),
                       min(s.max_total_cost, s.bankroll - s.cash_reserve) - total)
            if room <= 0:
                continue
            books_left -= 1
            o = plan_entry(eid, self.fair(eid), self.book(eid), min_edge=s.min_edge,
                           depth_fraction=s.depth_fraction, max_cost=room,
                           kelly_fraction=s.kelly_fraction, bankroll=s.bankroll)
            if o:
                self.execute(o)
                pending.add(eid)
                total += o.cost
                cost[eid] = cost.get(eid, 0.0) + o.cost

    def arb(self, pending: set[str], books_left: int, blocked: bool) -> int:
        """Repair uneven baskets, sell baskets worth more now than at settlement or cost,
        and buy new NO baskets when a race's YES bids sum above 1 + ARB_MIN_PROFIT."""
        s, now = self.s, self.clock()
        if not s.arb_enabled:
            return books_left
        held = {h.exchange_id: h for h in self.ledger.holdings("arb")}
        conv_busy = {h.exchange_id for h in self.ledger.holdings("conv")}
        capital = sum(h.qty * h.avg_cost for h in held.values())
        for race in self.races:
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
                bar = exit_bar(race, sum(held[e].avg_cost for e in ids), s.arb_min_profit, s.arb_exit_profit)
                top = screen_sell(race, self.prices)
                if top is not None and top >= bar:
                    books_left -= race.k
                    o = plan_sell(race, {e: self.book(e) for e in ids}, sets_held=sets, bar=bar)
                    if o:
                        self.execute_basket(o)
                        pending.update(ids)
                        continue
            if blocked or any(e in conv_busy for e in ids):
                continue
            edge = screen_buy(race, self.prices)
            room = int((s.arb_max_capital - capital) / max(race.k - 1, 1))
            if edge is None or edge < s.arb_min_profit or room < 1:
                continue
            books_left -= race.k
            o = plan_buy(race, {e: self.book(e) for e in ids}, min_profit=s.arb_min_profit,
                         max_sets=min(s.arb_max_sets, room), depth_fraction=s.arb_depth_fraction)
            if o:
                self.execute_basket(o)
                pending.update(ids)
                capital += o.sets * o.per_set
        return books_left

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
        resp = self.api.place_multi_leg([{"exchangeId": l.exchange_id, "side": "no", "action": l.action,
                                          "quantity": l.qty, "price": l.price} for l in legs], ttl)
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
        resp = self.api.place_order(o.exchange_id, o.side, o.action, o.qty, o.price, ttl)
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
        lines += self.opportunity_lines()
        lines.append("\nLargest gaps now (edge = fair − price to buy):")
        for edge, eid, side in self.gaps()[:5]:
            lines.append(f"  {self.labels.get(eid, eid)[:40]:40} buy {side.upper():3} edge {edge:+.3f}")
        alerts = self.ledger.events_since(since)
        if alerts:
            lines.append(f"\nAlerts/errors last {s.report_interval_hours:g}h ({len(alerts)}):")
            lines += [f"  {datetime.fromtimestamp(t, timezone.utc):%H:%M} {lvl} {m[:150]}" for t, lvl, m in alerts[-10:]]
        return "\n".join(lines)

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
        try:
            while deadline is None or self.clock() < deadline:
                try:
                    self.cycle()
                    delay = s.poll_seconds
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
