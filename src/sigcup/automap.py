"""Exact SIG -> Kalshi mapping from the Cup's structured titles (`sigcup build-map`).

SIG:    "Will the Democratic Party win the Texas Senate?" / "... the PA-07 House race?" / "... the U.S. House?"
Kalshi: SENATETX-26-D, SENATEFLS-26-R (specials), GOVPARTYTX-26-D, HOUSEPA7-26-D / KXHOUSETX35-26-R,
        CONTROLH-2026-D.

A row is only written when exactly one open 2026 Kalshi event fits the race and it has a market whose
ticker ends in the party's letter. Ambiguous races (e.g. a regular and a special Senate race in one
state) are skipped. A final sanity check drops any pair whose prices differ by more than
`max_price_gap`, which would mean the markets aren't the same thing.
"""
from __future__ import annotations

import logging
import re
from typing import Any

log = logging.getLogger(__name__)

STATES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA", "Colorado": "CO",
    "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY",
}
TITLE = re.compile(r"^\s*Will the (.+?) Party win the (.+?)\??\s*$")


def race_series(target: str) -> list[str] | None:
    """Kalshi series that may hold this SIG race, or None if the race type is unknown."""
    if target == "U.S. House":
        return ["CONTROLH"]
    if target == "U.S. Senate":
        return ["CONTROLS"]
    h = re.fullmatch(r"([A-Z]{2})-(\d+|AL) House race", target)
    if h:
        st, d = h.group(1), h.group(2)
        n = "AL" if d == "AL" else str(int(d))
        return [f"HOUSE{st}{n}", f"KXHOUSE{st}{n}"]
    o = re.fullmatch(r"(.+) (Senate|Governor)", target)
    if o and o.group(1) in STATES:
        st = STATES[o.group(1)]
        return [f"SENATE{st}", f"SENATE{st}S"] if o.group(2) == "Senate" else [f"GOVPARTY{st}"]
    return None


def _is_2026(event: dict[str, Any]) -> bool:
    t = event.get("event_ticker", "")
    return t.endswith("-26") or t.endswith("-2026") or "2026" in (event.get("title") or "")


def build_rows(sig_markets: list[tuple[str, str]], kalshi_events, sig_prices, *,
               max_price_gap: float = 0.25) -> tuple[list[dict[str, str]], list[str]]:
    """sig_markets: [(exchange_id, title)]. kalshi_events(series) -> open events with nested markets.
    sig_prices: exchange_id -> (bid, ask). Returns (map rows, notes on what was skipped and why)."""
    rows, notes = [], []
    cache: dict[str, list[dict[str, Any]]] = {}
    for eid, title in sig_markets:
        t = TITLE.match(title)
        series = race_series(t.group(2)) if t else None
        if not series:
            notes.append(f"skip (unknown race type): {title}")
            continue
        letter = t.group(1).strip()[0].upper()
        found = []
        for s in series:
            if s not in cache:
                cache[s] = [e for e in kalshi_events(s) if _is_2026(e)]
            for e in cache[s]:
                for m in e.get("markets") or []:
                    if m.get("ticker", "").endswith(f"-{letter}") and m.get("status") in (None, "active", "open"):
                        found.append(m)
        if len(found) != 1:
            notes.append(f"skip ({'no' if not found else 'ambiguous'} Kalshi market): {title}")
            continue
        m = found[0]
        k_mid = _mid(_px(m, "bid"), _px(m, "ask"))
        s_mid = _mid(*sig_prices.get(eid, (None, None)))
        if k_mid is not None and s_mid is not None and abs(k_mid - s_mid) > max_price_gap:
            notes.append(f"skip (prices too far apart, Cup {s_mid:.2f} vs Kalshi {k_mid:.2f}): {title}")
            continue
        label = f"{t.group(2)} [{t.group(1)}]"
        rows.append({"sig_exchange_id": eid, "label": label, "source": "kalshi", "ref": m["ticker"],
                     "invert": "0", "weight": "1", "enabled": "1"})
    return rows, notes


def _px(m: dict[str, Any], side: str) -> float | None:
    v = m.get(f"yes_{side}_dollars")
    try:
        p = float(v) if v not in (None, "") else None
    except ValueError:
        p = None
    return p if p is not None and 0 < p < 1 else None


def _mid(bid: float | None, ask: float | None) -> float | None:
    return None if bid is None or ask is None else (bid + ask) / 2
