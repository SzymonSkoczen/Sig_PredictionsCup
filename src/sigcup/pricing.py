"""Market map (SIG exchange -> reference legs) and fair value from the reference quotes."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .references import RefQuote, combine_sum

MAP_COLUMNS = ["sig_exchange_id", "label", "source", "ref", "invert", "weight", "enabled"]


@dataclass(frozen=True)
class RefLeg:
    exchange_id: str
    label: str
    source: str  # kalshi | polymarket
    ref: str     # see references.py; "+" sums several
    invert: bool
    weight: float

    @property
    def parts(self) -> list[str]:
        return [p.strip() for p in self.ref.split("+") if p.strip()]


def _truthy(v: str | None) -> bool:
    return (v or "").strip().lower() in ("1", "true", "yes", "y")


def load_map(path: str | Path) -> dict[str, list[RefLeg]]:
    """exchange_id -> its enabled reference legs. Rows with enabled=0 are suggestions only."""
    out: dict[str, list[RefLeg]] = {}
    p = Path(path)
    if not p.exists():
        return out
    with p.open(newline="") as f:
        for row in csv.DictReader(f):
            if not _truthy(row.get("enabled")) or not row.get("sig_exchange_id") or not row.get("ref"):
                continue
            source = row["source"].strip().lower()
            if source not in ("kalshi", "polymarket"):
                raise ValueError(f"{path}: unknown source {source!r}")
            leg = RefLeg(row["sig_exchange_id"].strip(), row.get("label", "").strip(), source,
                         row["ref"].strip(), _truthy(row.get("invert")), float(row.get("weight") or 1))
            out.setdefault(leg.exchange_id, []).append(leg)
    return out


def write_map(path: str | Path, rows: list[dict[str, str]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MAP_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def leg_quote(leg: RefLeg, quotes: dict[tuple[str, str], RefQuote], now: float) -> RefQuote | None:
    q = combine_sum(leg.source, leg.ref, [quotes.get((leg.source, p)) for p in leg.parts], now)
    if q is None:
        return None
    return q.inverted() if leg.invert else q


@dataclass(frozen=True)
class Fair:
    p: float                 # fair P(YES) for the SIG exchange
    n_sources: int
    disagreement: float      # max - min of the source mids
    detail: str


def fair_value(legs: list[RefLeg], quotes: dict[tuple[str, str], RefQuote], now: float, *,
               max_age: float, max_spread: float, max_disagreement: float,
               min_sources: int) -> tuple[Fair | None, str]:
    """Spread-weighted mean of usable reference mids, or (None, why not)."""
    usable: list[tuple[RefLeg, RefQuote]] = []
    why = []
    for leg in legs:
        q = leg_quote(leg, quotes, now)
        if q is None or q.mid is None:
            why.append(f"{leg.source}:no two-sided quote")
        elif now - q.ts > max_age:
            why.append(f"{leg.source}:stale")
        elif q.spread > max_spread:
            why.append(f"{leg.source}:spread {q.spread:.3f}")
        else:
            usable.append((leg, q))
    if len(usable) < min_sources:
        return None, "; ".join(why) or "no references"
    mids = [q.mid for _, q in usable]
    disagreement = max(mids) - min(mids)
    if disagreement > max_disagreement:
        return None, f"references disagree by {disagreement:.3f}"
    weights = [leg.weight / max(q.spread, 0.01) for leg, q in usable]
    p = sum(w * m for w, m in zip(weights, mids)) / sum(weights)
    detail = ", ".join(f"{leg.source} {q.bid:.3f}/{q.ask:.3f}" for leg, q in usable)
    return Fair(p, len(usable), disagreement, detail), ""
