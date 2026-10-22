# Sig_PredictionsCup — convergence bot

An automated trader for the **Susquehanna Predictions Cup** (midterm elections, Oct 1 → Nov 4 2026).
It runs on the Cup's official API (The Super Market, `https://www.thesuper.market/api/v1`,
docs at <https://sig.thesuper.market/api/v1/docs>).

```
Kalshi + Polymarket quotes ──► fair value per SIG market ──► SIG cheap/rich by ≥ MIN_EDGE? ──► buy
                                                         └─► SIG back near fair? ──► sell
                                    every 2 h ──► health / P&L / trades report to your phone
```

## The strategy, and what it is (and isn't)

This is **convergence trading, not riskless arbitrage**. SUSQies can only be traded on the Cup.
You can't hedge on Kalshi or Polymarket, so no trade is locked in. The bot treats the real-money
markets as the best estimate of the true probability:

1. **Fair value.** For each SIG exchange you map, the bot takes the mid of each reference market
   (Kalshi, Polymarket, or both). It weights each mid by 1/spread. It skips a reference that is
   stale (older than `REF_MAX_AGE_SECONDS`) or wide (spread over `REF_MAX_SPREAD`). It skips the
   whole market when the references disagree by more than `REF_MAX_DISAGREEMENT`.
2. **Entry.** When SIG's ask is at least `MIN_EDGE` below fair, the bot buys YES. When SIG's bid is
   at least `MIN_EDGE` above fair, it buys NO. It walks the book only while every level still clears
   the edge, and takes `DEPTH_FRACTION` of each level. Size is the smallest of fraction-Kelly on
   `BANKROLL`, `MAX_ORDER_COST`, `MAX_MARKET_COST` and `MAX_TOTAL_COST`. Orders expire after
   `ORDER_TTL_SECONDS`, so they act like immediate-or-cancel orders.
3. **Exit.** The bot sells when:
   - SIG's bid for the held side comes back within `EXIT_BAND` of fair (**converged**: take the profit);
   - fair value falls `STOP_LOSS` below the entry price (**stop**: the news moved against us); or
   - the position has been held longer than `MAX_HOLD_HOURS` (**timeout**).
4. **Safety.**
   - Paper mode is the default. Live trading needs both `MODE=live` and `run --live`.
   - The kill-switch file (`sigcup kill`) pauses new entries, and exits keep running.
   - After losing `DAILY_LOSS_STOP` in a day, new entries pause until the next UTC day.
   - Each order has an idempotency key, so a retry can never place it twice.
   - The bot stays inside a rate budget below the account limit of 100 reads and 30 writes per minute.
   - On shutdown it cancels all its open orders.
   - The bot only sells positions **it** bought (tracked in `data/sigcup.db`). Your manual trades are left alone.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env            # then fill it in (see below)
pytest                          # 19 offline tests
```

On the Predictions Cup site:
- **My Profile → API Keys**: create a key with the `read` and `trade` scopes, and put it in `SIG_API_KEY`.
- Confirm your email, register for the tournament and accept the current Terms. Until then, every API
  call returns 403.

```bash
sigcup check                    # key works? lists tournaments -> put the slug in SIG_TOURNAMENT_SLUG
sigcup markets                  # every SIG exchange -> data/sig_markets.csv
sigcup suggest-map              # fuzzy matches to Kalshi/Polymarket -> data/suggested_map.csv
```

### The market map (the most important step)

`data/market_map.csv` tells the bot which reference market prices each SIG exchange. One row per
reference, and an exchange can have several rows:

| column | meaning |
|---|---|
| `sig_exchange_id` | from `data/sig_markets.csv` |
| `label` | a readable name, used in reports |
| `source` | `kalshi` or `polymarket` |
| `ref` | Kalshi ticker, or Polymarket `market-slug:Outcome` (or `token:<id>`). Join with `+` to sum mutually exclusive outcomes, e.g. two candidates from the same party. |
| `invert` | `1` if SIG YES equals the reference's NO (e.g. "Democrats win House" vs a "Republicans win House" market) |
| `weight` | relative trust in the source (default 1) |
| `enabled` | only `1` rows are traded |

`suggest-map` writes every suggestion with `enabled=0`. **Check each row by hand.** Make sure it is
the same race, the same outcome and the same resolution rules, and check whether it needs `invert`.
A wrong mapping is the single biggest way to lose money with this bot.
See `data/market_map.example.csv` for the format. The tickers in it are placeholders.

### Notifications (the 2-hourly report)

Fill in at least one channel in `.env`:

- **Telegram**: talk to @BotFather to get a token, then message your bot and read `chat_id`
  from `https://api.telegram.org/bot<TOKEN>/getUpdates`.
- **Discord** or **Slack**: an incoming-webhook URL.
- **ntfy**: the easiest option. Install the ntfy app and subscribe to an unguessable topic name.
- **Email**: any SMTP account. For Gmail, use an app password.

Every `REPORT_INTERVAL_HOURS` (default 2) you get a report with:
- health: uptime, last good cycle, API usage and errors, freshness of the Kalshi and Polymarket feeds;
- whether entries are active or paused;
- bot P&L: realized for the window, today and all-time, plus the open mark-to-market;
- the account P&L from the exchange;
- open positions, with entry price, current mark and fair value;
- every trade in the window;
- the five largest current gaps;
- any errors and alerts.

You also get immediate alerts on start and stop, after 5 failed cycles in a row, when the kill switch
is used, and when the daily loss stop is hit.
`sigcup report` prints the report now, and `sigcup report --send` sends it.

## Running

```bash
sigcup scan                     # one-off table: SIG vs fair vs edge. Never trades.
sigcup run                      # paper trading: simulated fills, real prices
# after a few days of sensible paper results:
MODE=live in .env, then: sigcup run --live
sigcup kill / sigcup resume     # pause / resume new entries without stopping the bot
```

It has to run **24/7 on a machine that stays on**. A laptop that sleeps will miss trades and reports.
Good options:
- a small VPS, such as Hetzner, DigitalOcean or AWS Lightsail at about $5/month, or a free Oracle
  Cloud VM. Run it with the systemd unit in `deploy/sigcup.service`, which restarts it if it crashes.
- Docker:
  `docker build -t sigcup . && docker run -d --restart=always --env-file .env -v $PWD/data:/app/data sigcup run`.
  The container health check fails if the bot's heartbeat is more than 10 minutes old.

## Tuning notes

- `MIN_EDGE` 0.04 is deliberately wide. Reference mids are noisy, and the Cup's books are thin.
  Lower it only after paper results show that small gaps really do converge.
- SIG prices for heavily traded races usually track Kalshi closely. The edges tend to be in
  less-watched races and right after news, before Cup traders react. Keep `POLL_SECONDS` low and the
  map wide.
- The Cup ends on **Nov 4**, around settlement. A position still open at settlement pays 1 or 0. The
  timeout and stop exits limit how long you're exposed. Decide before election night whether you want
  to be flat or carry positions.
- Live fills are confirmed by reconciling exchange positions after each order expires. Don't trade
  the bot's mapped markets by hand while one of its orders is pending (about 15 s), or the fill can be
  misattributed.

## Limits I couldn't verify

This was built without network access to the Cup, Kalshi or Polymarket. Request and response
shapes come from the public API docs and from community clients, and are covered by tests against
mocked responses. The first time you run `sigcup check` and `sigcup scan`, watch the output.
If a field name differs (for example in the prices or positions payloads), the fix is a one-line
change in `src/sigcup/sig_api.py`.
