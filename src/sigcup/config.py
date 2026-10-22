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
    max_total_cost: float = 60_000.0
    cash_reserve: float = 10_000.0
    depth_fraction: float = 0.5
    order_ttl_seconds: int = 15
    max_books_per_cycle: int = 6

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
            kwargs[f.name] = kind(raw) if kind is not str else raw
        return cls(**kwargs)

    @property
    def live(self) -> bool:
        return self.mode.lower() == "live"
