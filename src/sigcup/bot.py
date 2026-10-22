"""The trading loop: reference prices -> fair values -> exits, then entries -> reports."""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .config import Settings
from .ledger import Ledger
from .notify import Notifier
from .pricing import Fair, RefLeg, fair_value, load_map
from .references import KalshiFeed, PolymarketFeed, RefQuote
from .sig_api import Book, SigApi
from .strategy import Order, plan_entry, plan_exit, side_fair

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
        for h in self.ledger.holdings():
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

        if self.live:
            self.positions = {(p.exchange_id, p.side): p.qty for p in self.api.positions()}
            for note in self.ledger.reconcile(self.positions, now):
                self.ledger.event("INFO", note)
                log.info(note)

        ids = list(self.map)
        self.prices = self.api.prices(ids) if ids else {}
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
            o = plan_exit(h, fair, self.api.book(h.exchange_id), now, **kw)
            if o:
                self.execute(o)
                pending.add(o.exchange_id)

        blocked = self.entries_blocked()
        if blocked:
            self.alert_once(f"blocked:{blocked}", f"New entries paused: {blocked}")
        else:
            self._alerted = {a for a in self._alerted if not a.startswith("blocked:")}
            self.enter(pending, books_left)

        self.health.cycles += 1
        self.health.last_ok = self.clock()
        self.health.consecutive_errors = 0

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
        for edge, eid, side in self.gaps():
            if edge < s.min_edge or books_left <= 0:
                break
            other = "no" if side == "yes" else "yes"
            if eid in pending or (eid, other) in held:
                continue
            room = min(s.max_order_cost, s.max_market_cost - cost.get(eid, 0.0),
                       min(s.max_total_cost, s.bankroll - s.cash_reserve) - total)
            if room <= 0:
                continue
            books_left -= 1
            o = plan_entry(eid, self.fair(eid), self.api.book(eid), min_edge=s.min_edge,
                           depth_fraction=s.depth_fraction, max_cost=room,
                           kelly_fraction=s.kelly_fraction, bankroll=s.bankroll)
            if o:
                self.execute(o)
                pending.add(eid)
                total += o.cost
                cost[eid] = cost.get(eid, 0.0) + o.cost

    def execute(self, o: Order) -> None:
        label = self.labels.get(o.exchange_id, o.exchange_id)
        msg = (f"{o.action.upper()} {o.side.upper()} {o.qty} {label} @ {o.price:.3f} "
               f"(fair {o.fair:.3f}, {o.reason})")
        if not self.live:
            realized = self.ledger.record_fill(o, o.qty, label, self.clock())
            self.ledger.event("TRADE", f"[paper] {msg}" + (f" realized {realized:+.0f}" if o.action == "sell" else ""))
            log.info("[paper] %s", msg)
            return
        before = self.positions.get((o.exchange_id, o.side), 0.0)
        ttl = self.s.order_ttl_seconds
        resp = self.api.place_order(o.exchange_id, o.side, o.action, o.qty, o.price, ttl)
        self.ledger.add_pending(o, label, before, ttl, json.dumps(resp, default=str)[:2000], self.clock())
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
            f"Mode: {'LIVE' if self.live else 'PAPER'} | {datetime.fromtimestamp(now, timezone.utc):%Y-%m-%d %H:%M} UTC",
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
        for ts, label, side, action, qty, price, fair, reason, realized in fills[-20:]:
            r = f" P&L {realized:+.0f}" if action == "sell" else ""
            lines.append(f"  {datetime.fromtimestamp(ts, timezone.utc):%H:%M} {action.upper()} {side.upper()} "
                         f"{qty:g} {label[:35]} @{price:.3f} fair {fair:.3f} ({reason}){r}")
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

    def run(self) -> None:
        s = self.s
        self.notifier.send("🤖 SIG Cup bot started",
                           f"Mode {'LIVE' if self.live else 'PAPER'}, {len(self.map)} mapped markets, "
                           f"reports every {s.report_interval_hours:g}h, channels: {', '.join(self.notifier.channels) or 'log only'}")
        if not self.map:
            log.warning("market map %s has no enabled rows: nothing to trade", s.map_path)
        try:
            while True:
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
            self.notifier.send("🛑 SIG Cup bot stopped", self.report())


def _p(x: float | None) -> str:
    return "  -  " if x is None else f"{x:.3f}"
