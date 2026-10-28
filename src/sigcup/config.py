"""Settings from the environment, with a minimal .env loader (no extra dependency)."""
from __future__ import annotations

import os
from dataclasses import dataclass, fields
from pathlib import Path


def load_dotenv(path: str | Path = ".env") -> None:
    """Fill os.environ from KEY=VALUE lines; real environment variables win."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


@dataclass
class Settings:
    sig_api_key: str = ""
    sig_base_url: str = "https://www.thesuper.market/api/v1"
    sig_tournament_slug: str = ""
    read_budget: int = 70
    write_budget: int = 20

    mode: str = "paper"
    poll_seconds: float = 10.0
    kill_switch: str = "KILL"
    db_path: str = "data/sigcup.db"
    map_path: str = "data/market_map.csv"

    kalshi_base_url: str = "https://api.elections.kalshi.com/trade-api/v2"
    polymarket_gamma_url: str = "https://gamma-api.polymarket.com"
    polymarket_clob_url: str = "https://clob.polymarket.com"
    ref_refresh_seconds: float = 20.0
    ref_max_age_seconds: float = 120.0
    ref_max_spread: float = 0.06
    ref_max_disagreement: float = 0.05
    ref_min_sources: int = 1

    min_edge: float = 0.04
    kelly_fraction: float = 0.25
    bankroll: float = 100_000.0
    max_order_cost: float = 2_500.0
    max_market_cost: float = 6_000.0
    max_total_cost: float = 40_000.0
    cash_reserve: float = 10_000.0
    depth_fraction: float = 0.5
    order_ttl_seconds: int = 15
    max_books_per_cycle: int = 6
    # Cap on gap-trade cost per race (both party markets together); 0 = off
    max_race_cost: float = 0.0
    # Hold gap trades to settlement: no "converged" or time-limit exits (stop-loss still applies)
    hold_to_settlement: bool = False
    # Kept free until ELECTION_NIGHT_START (ISO 8601), then released for election-night trading
    election_reserve: float = 0.0
    election_night_start: str = ""

    # --- adapted from grissou/prediction-market-maker (see value.py) ---
    # Gap entries must also earn this much per unit of cash, (fair - price) / price; 0 = off
    min_return: float = 0.0
    # Scale each race's fair values to sum to 1 when they already sum to within 5% of it
    race_scale: bool = False
    # A state's total cost across all its markets, e.g. Rhode Island Senate + Governor + RI-01; 0 = off
    state_max_cost: float = 0.0
    # Harvest ladder: resting bids under favourites (fair >= LADDER_FAVOURITE_P) at these offsets below the bid
    ladder_enabled: bool = False
    ladder_favourite_p: float = 0.90
    ladder_offsets: str = "0,0.02,0.04,0.06"
    ladder_min_edge: float = 0.08
    ladder_level_cost: float = 3_000.0
    ladder_budget: float = 15_000.0
    ladder_requote_seconds: float = 900.0
    # The ladder may rest bids with this much of ELECTION_RESERVE (grissou carves its ladder out of its reserve);
    # all ladder bids are cancelled an hour before election night
    ladder_from_reserve: float = 0.0
    # Allocator: hourly, sell holdings with little edge left to fund buys with ALLOC_MIN_GAIN more
    alloc_enabled: bool = False
    alloc_interval_seconds: float = 3_600.0
    alloc_min_gain: float = 0.05
    alloc_max_keep_edge: float = 0.05
    alloc_sell_margin: float = 0.03
    alloc_max_turnover: float = 15_000.0
    alloc_pinned: str = "U.S. House,U.S. Senate"
    # Election night (Bowen26/election-bot rule): buy a side the references bid at NIGHT_MIN_REF_BID+ while the
    # Cup still asks NIGHT_MIN_GAP below that bid
    night_enabled: bool = False
    night_min_ref_bid: float = 0.95
    night_min_gap: float = 0.02
    night_race_cost: float = 8_000.0
    night_poll_seconds: float = 4.0
    night_ref_refresh_seconds: float = 5.0
    # Trading locks at this time (ISO 8601); new orders stop CLOSE_BUFFER_MINUTES before it
    trading_close: str = ""
    close_buffer_minutes: float = 10.0
    swing_shock: float = 0.15

    arb_enabled: bool = True
    arb_min_profit: float = 0.01
    arb_exit_profit: float = 0.005
    arb_max_sets: int = 2_000
    arb_max_capital: float = 40_000.0
    # Short-term arb: sell baskets held longer than this, and free cash for new trades by selling
    # baskets at up to ARB_UNWIND_MAX_LOSS per set below cost.
    arb_max_hold_hours: float = 12.0
    arb_unwind_max_loss: float = 0.015
    # Sell baskets at a loss to free cash for gap trades. Off: baskets are held to take-profit/timeout.
    arb_unwind_for_cash: bool = False
    # Arb buys only spend cash above this, and baskets are sold to get back to it: keeps money free
    # for gap trades and the next opportunity.
    arb_cash_floor: float = 25_000.0
    arb_depth_fraction: float = 0.5
    arb_repair_slippage: float = 0.02
    arb_repair_minutes: float = 10.0
    races_refresh_minutes: float = 30.0

    # Paper until this moment (ISO 8601 with offset), then live if the paper run was healthy
    live_from: str = ""
    paper_min_cycles: int = 30

    exit_band: float = 0.01
    stop_loss: float = 0.08
    max_hold_hours: float = 72.0
    exit_slippage: float = 0.02
    daily_loss_stop: float = 8_000.0

    report_interval_hours: float = 2.0
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    discord_webhook_url: str = ""
    slack_webhook_url: str = ""
    ntfy_topic: str = ""
    ntfy_server: str = "https://ntfy.sh"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_to: str = ""

    @classmethod
    def from_env(cls, dotenv: str | Path | None = ".env") -> "Settings":
        if dotenv:
            load_dotenv(dotenv)
        kwargs = {}
        for f in fields(cls):
            raw = os.environ.get(f.name.upper())
            if raw is None or raw == "":
                continue
            kind = type(f.default)
            if kind is bool:
                kwargs[f.name] = raw.strip().lower() in ("1", "true", "yes", "on")
            else:
                kwargs[f.name] = kind(raw) if kind is not str else raw
        return cls(**kwargs)

    @property
    def live(self) -> bool:
        return self.mode.lower() == "live"
