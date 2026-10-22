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
    exchange_id TEXT, side TEXT, qty REAL, avg_cost REAL, opened_at REAL,
    PRIMARY KEY (exchange_id, side));
CREATE TABLE IF NOT EXISTS pending (
    id INTEGER PRIMARY KEY, exchange_id TEXT, side TEXT, action TEXT, qty INTEGER, price REAL,
    fair REAL, reason TEXT, label TEXT, pos_before REAL, created REAL, expires REAL, response TEXT);
CREATE TABLE IF NOT EXISTS fills (
    id INTEGER PRIMARY KEY, ts REAL, exchange_id TEXT, label TEXT, side TEXT, action TEXT,
    qty REAL, price REAL, fair REAL, reason TEXT, realized REAL, mode TEXT);
CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, ts REAL, level TEXT, msg TEXT);
CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT);
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

    def holdings(self) -> list[Holding]:
        rows = self.db.execute("SELECT exchange_id, side, qty, avg_cost, opened_at FROM holdings WHERE qty > 0")
        return [Holding(*r) for r in rows]

    def holding(self, exchange_id: str, side: str) -> Holding | None:
        r = self.db.execute("SELECT exchange_id, side, qty, avg_cost, opened_at FROM holdings "
                            "WHERE exchange_id=? AND side=? AND qty > 0", (exchange_id, side)).fetchone()
        return Holding(*r) if r else None

    def cost_by_exchange(self) -> dict[str, float]:
        rows = self.db.execute("SELECT exchange_id, SUM(qty * avg_cost) FROM holdings GROUP BY exchange_id")
        return {e: c or 0.0 for e, c in rows}

    def record_fill(self, o: Order, qty: float, label: str, ts: float | None = None) -> float:
        """Apply a fill to holdings and log it; returns realised P&L (sells only)."""
        ts = ts or time.time()
        h = self.holding(o.exchange_id, o.side)
        realized = 0.0
        if o.action == "buy":
            if h:
                new_qty = h.qty + qty
                avg = (h.qty * h.avg_cost + qty * o.price) / new_qty
                self.db.execute("UPDATE holdings SET qty=?, avg_cost=? WHERE exchange_id=? AND side=?",
                                (new_qty, avg, o.exchange_id, o.side))
            else:
                self.db.execute("INSERT OR REPLACE INTO holdings VALUES (?, ?, ?, ?, ?)",
                                (o.exchange_id, o.side, qty, o.price, ts))
        else:
            if h:
                qty = min(qty, h.qty)
                realized = qty * (o.price - h.avg_cost)
                self.db.execute("UPDATE holdings SET qty=? WHERE exchange_id=? AND side=?",
                                (h.qty - qty, o.exchange_id, o.side))
        self.db.execute("INSERT INTO fills (ts, exchange_id, label, side, action, qty, price, fair, reason, "
                        "realized, mode) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (ts, o.exchange_id, label, o.side, o.action, qty, o.price, o.fair, o.reason,
                         realized, self.mode))
        self.db.commit()
        return realized

    # ---- pending live orders ----

    def add_pending(self, o: Order, label: str, pos_before: float, ttl: float, response: str,
                    now: float | None = None) -> None:
        now = now or time.time()
        self.db.execute("INSERT INTO pending (exchange_id, side, action, qty, price, fair, reason, label, "
                        "pos_before, created, expires, response) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (o.exchange_id, o.side, o.action, o.qty, o.price, o.fair, o.reason, label,
                         pos_before, now, now + ttl, response))
        self.db.commit()

    def pending_exchanges(self) -> set[str]:
        return {r[0] for r in self.db.execute("SELECT exchange_id FROM pending")}

    def reconcile(self, positions: dict[tuple[str, str], float], now: float, grace: float = 3.0) -> list[str]:
        """Settle expired pending orders against current exchange positions."""
        notes = []
        rows = self.db.execute("SELECT id, exchange_id, side, action, qty, price, fair, reason, label, "
                               "pos_before FROM pending WHERE expires + ? <= ?", (grace, now)).fetchall()
        for pid, eid, side, action, qty, price, fair, reason, label, before in rows:
            pos = positions.get((eid, side), 0.0)
            delta = pos - before if action == "buy" else before - pos
            filled = max(0.0, min(float(qty), delta))
            if filled > 0:
                self.record_fill(Order(eid, side, action, int(qty), price, fair, reason), filled, label, now)
            notes.append(f"{action} {side} {label}: filled {filled:g}/{qty}")
            self.db.execute("DELETE FROM pending WHERE id=?", (pid,))
        self.db.commit()
        return notes

    # ---- reporting ----

    def fills_since(self, ts: float) -> list[tuple]:
        return self.db.execute("SELECT ts, label, side, action, qty, price, fair, reason, realized FROM fills "
                               "WHERE ts >= ? ORDER BY ts", (ts,)).fetchall()

    def realized_since(self, ts: float) -> float:
        return self.db.execute("SELECT COALESCE(SUM(realized), 0) FROM fills WHERE ts >= ?", (ts,)).fetchone()[0]

    def events_since(self, ts: float, levels: tuple[str, ...] = ("ERROR", "ALERT")) -> list[tuple]:
        q = f"SELECT ts, level, msg FROM events WHERE ts >= ? AND level IN ({','.join('?' * len(levels))}) ORDER BY ts"
        return self.db.execute(q, (ts, *levels)).fetchall()
