"""SQLite record of what the bot owns, its orders, fills and events.

The bot only ever sells what it bought itself (`holdings`), so manual trades you make on the
website are left alone. Live fills are confirmed by reconciling exchange positions after each
order expires: the position change on that exchange/side is attributed to the order (capped at
the order size). Avoid trading the bot's markets by hand while one of its orders is pending.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from .strategy import Holding, Order

SCHEMA = """
CREATE TABLE IF NOT EXISTS holdings (
    strategy TEXT, exchange_id TEXT, side TEXT, qty REAL, avg_cost REAL, opened_at REAL,
    PRIMARY KEY (strategy, exchange_id, side));
CREATE TABLE IF NOT EXISTS pending (
    id INTEGER PRIMARY KEY, strategy TEXT, exchange_id TEXT, side TEXT, action TEXT, qty INTEGER,
    price REAL, fair REAL, reason TEXT, label TEXT, pos_before REAL, created REAL, expires REAL,
    response TEXT);
CREATE TABLE IF NOT EXISTS fills (
    id INTEGER PRIMARY KEY, ts REAL, strategy TEXT, exchange_id TEXT, label TEXT, side TEXT,
    action TEXT, qty REAL, price REAL, fair REAL, reason TEXT, realized REAL, mode TEXT);
CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, ts REAL, level TEXT, msg TEXT);
CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS resting (
    order_id TEXT PRIMARY KEY, exchange_id TEXT, side TEXT, price REAL, qty REAL, placed REAL, expires REAL,
    label TEXT, fair REAL);
"""


class Ledger:
    def __init__(self, path: str | Path, mode: str = "paper"):
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.executescript(SCHEMA)
        self.mode = mode

    # ---- key/value ----

    def get(self, key: str, default: str | None = None) -> str | None:
        row = self.db.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def put(self, key: str, value: object) -> None:
        self.db.execute("INSERT OR REPLACE INTO kv VALUES (?, ?)", (key, str(value)))
        self.db.commit()

    def event(self, level: str, msg: str) -> None:
        self.db.execute("INSERT INTO events (ts, level, msg) VALUES (?, ?, ?)", (time.time(), level, msg))
        self.db.commit()

    # ---- holdings ----

    def holdings(self, strategy: str | None = "conv") -> list[Holding]:
        """Open holdings of one strategy ("conv" or "arb"), or of all with strategy=None."""
        q = "SELECT exchange_id, side, qty, avg_cost, opened_at FROM holdings WHERE qty > 0"
        rows = self.db.execute(q) if strategy is None else self.db.execute(q + " AND strategy=?", (strategy,))
        return [Holding(*r) for r in rows]

    def holding(self, exchange_id: str, side: str, strategy: str = "conv") -> Holding | None:
        r = self.db.execute("SELECT exchange_id, side, qty, avg_cost, opened_at FROM holdings "
                            "WHERE strategy=? AND exchange_id=? AND side=? AND qty > 0",
                            (strategy, exchange_id, side)).fetchone()
        return Holding(*r) if r else None

    def cost_by_exchange(self, strategy: str = "conv") -> dict[str, float]:
        rows = self.db.execute("SELECT exchange_id, SUM(qty * avg_cost) FROM holdings WHERE strategy=? "
                               "GROUP BY exchange_id", (strategy,))
        return {e: c or 0.0 for e, c in rows}

    def record_fill(self, o: Order, qty: float, label: str, ts: float | None = None,
                    strategy: str = "conv") -> float:
        """Apply a fill to holdings and log it; returns realised P&L (sells only)."""
        ts = ts or time.time()
        h = self.holding(o.exchange_id, o.side, strategy)
        realized = 0.0
        if o.action == "buy":
            if h:
                new_qty = h.qty + qty
                avg = (h.qty * h.avg_cost + qty * o.price) / new_qty
                self.db.execute("UPDATE holdings SET qty=?, avg_cost=? WHERE strategy=? AND exchange_id=? "
                                "AND side=?", (new_qty, avg, strategy, o.exchange_id, o.side))
            else:
                self.db.execute("INSERT OR REPLACE INTO holdings VALUES (?, ?, ?, ?, ?, ?)",
                                (strategy, o.exchange_id, o.side, qty, o.price, ts))
        else:
            if h:
                qty = min(qty, h.qty)
                realized = qty * (o.price - h.avg_cost)
                self.db.execute("UPDATE holdings SET qty=? WHERE strategy=? AND exchange_id=? AND side=?",
                                (h.qty - qty, strategy, o.exchange_id, o.side))
        self.db.execute("INSERT INTO fills (ts, strategy, exchange_id, label, side, action, qty, price, fair, "
                        "reason, realized, mode) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (ts, strategy, o.exchange_id, label, o.side, o.action, qty, o.price, o.fair, o.reason,
                         realized, self.mode))
        self.db.commit()
        return realized

    def replace_holdings(self, rows: list[tuple[str, str, str, float, float, float]]) -> None:
        """Overwrite all holdings with (strategy, exchange_id, side, qty, avg_cost, opened_at) and drop
        pending orders: used at live start-up so the exchange is the source of truth."""
        self.db.execute("DELETE FROM holdings")
        self.db.execute("DELETE FROM pending")
        self.db.executemany("INSERT INTO holdings VALUES (?, ?, ?, ?, ?, ?)", rows)
        self.db.commit()

    # ---- pending live orders ----

    def add_pending(self, o: Order, label: str, pos_before: float, ttl: float, response: str,
                    now: float | None = None, strategy: str = "conv") -> None:
        now = now or time.time()
        self.db.execute("INSERT INTO pending (strategy, exchange_id, side, action, qty, price, fair, reason, "
                        "label, pos_before, created, expires, response) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (strategy, o.exchange_id, o.side, o.action, o.qty, o.price, o.fair, o.reason, label,
                         pos_before, now, now + ttl, response))
        self.db.commit()

    def pending_exchanges(self) -> set[str]:
        return {r[0] for r in self.db.execute("SELECT exchange_id FROM pending")}

    def reconcile(self, positions: dict[tuple[str, str], float], now: float, grace: float = 3.0) -> list[str]:
        """Settle expired pending orders against current exchange positions."""
        notes = []
        rows = self.db.execute("SELECT id, strategy, exchange_id, side, action, qty, price, fair, reason, label, "
                               "pos_before FROM pending WHERE expires + ? <= ?", (grace, now)).fetchall()
        for pid, strategy, eid, side, action, qty, price, fair, reason, label, before in rows:
            pos = positions.get((eid, side), 0.0)
            delta = pos - before if action == "buy" else before - pos
            filled = max(0.0, min(float(qty), delta))
            if filled > 0:
                self.record_fill(Order(eid, side, action, int(qty), price, fair, reason), filled, label, now,
                                 strategy)
            notes.append(f"{action} {side} {label}: filled {filled:g}/{qty}")
            self.db.execute("DELETE FROM pending WHERE id=?", (pid,))
        self.db.commit()
        return notes

    # ---- resting (ladder) orders: fills are matched by order id, not by position changes ----

    def add_resting(self, order_id: str, lv, label: str, fair: float, now: float, ttl: float) -> None:
        self.db.execute("INSERT OR REPLACE INTO resting VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (str(order_id), lv.exchange_id, lv.side, lv.price, lv.qty, now, now + ttl, label, fair))
        self.db.commit()

    def resting(self, now: float | None = None) -> list[tuple]:
        """(order_id, exchange_id, side, price, qty, placed, expires, label, fair) still resting."""
        q = "SELECT * FROM resting WHERE qty >= 1"
        rows = self.db.execute(q + (" AND expires > ?" if now else ""), ((now,) if now else ())).fetchall()
        return rows

    def drop_resting(self, order_id: str | None = None) -> None:
        if order_id is None:
            self.db.execute("DELETE FROM resting")
        else:
            self.db.execute("DELETE FROM resting WHERE order_id=?", (str(order_id),))
        self.db.commit()

    def apply_resting_fill(self, order_id: str, qty: float, price: float, now: float) -> str | None:
        """Credit a fill of one of our resting buys to the value book; returns a note, or None if not ours."""
        r = self.db.execute("SELECT exchange_id, side, qty, label, fair FROM resting WHERE order_id=?",
                            (str(order_id),)).fetchone()
        if not r:
            return None
        eid, side, left, label, fair = r
        n = min(qty, left)
        if n <= 0:
            return None
        self.record_fill(Order(eid, side, "buy", int(n), price, fair, "ladder"), n, label, now, "conv")
        self.db.execute("UPDATE resting SET qty=? WHERE order_id=?", (left - n, str(order_id)))
        self.db.commit()
        return f"ladder fill: BUY {side.upper()} {n:g} {label} @ {price:.3f}"

    # ---- reporting ----

    def fills_since(self, ts: float) -> list[tuple]:
        return self.db.execute("SELECT ts, strategy, label, side, action, qty, price, fair, reason, realized "
                               "FROM fills WHERE ts >= ? ORDER BY ts", (ts,)).fetchall()

    def realized_since(self, ts: float) -> float:
        return self.db.execute("SELECT COALESCE(SUM(realized), 0) FROM fills WHERE ts >= ?", (ts,)).fetchone()[0]

    def events_since(self, ts: float, levels: tuple[str, ...] = ("ERROR", "ALERT")) -> list[tuple]:
        q = f"SELECT ts, level, msg FROM events WHERE ts >= ? AND level IN ({','.join('?' * len(levels))}) ORDER BY ts"
        return self.db.execute(q, (ts, *levels)).fetchall()
