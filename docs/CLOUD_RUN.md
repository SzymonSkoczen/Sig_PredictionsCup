# Scheduled cloud run (every 2 hours)

These are the instructions a scheduled Claude Code cloud session follows each time it fires.
Each run trades for about 100 minutes, saves the bot's state to git, and ends with a short
summary, which arrives as a push notification on the owner's phone. Nobody approves trades.

Branch: `claude/quirky-darwin-u0tfmx` (repo `szymonskoczen/sig_predictionscup`).

## Rules

- Never print, log, commit or echo `SIG_API_KEY`. It comes from the environment only.
- Only push to `claude/quirky-darwin-u0tfmx`.
- Don't change strategy settings or risk limits unless the owner asks. Bug fixes are allowed
  (see step 5).
- Keep the final message short. It is the phone notification.

## Steps

1. **Sync.** `git fetch origin claude/quirky-darwin-u0tfmx && git checkout claude/quirky-darwin-u0tfmx && git pull`.
   Then run `pip install -q -e '.[dev]'`. Use `--user` if pip needs it.

2. **Preflight.** Run these checks, and stop at the first one that fails:
   - `test -n "$SIG_API_KEY"`. If this fails, end with: "Bot not run: SIG_API_KEY is not set in
     the cloud environment."
   - `curl -sS -o /dev/null -w '%{http_code}' https://www.thesuper.market/api/v1/tournaments`, and
     the same for `https://api.elections.kalshi.com/trade-api/v2/markets?limit=1` and
     `https://clob.polymarket.com/`. If any of them fails to connect (proxy 403 / code 000), end with
     "Bot not run: network policy blocks <hosts>".
   - `sigcup --env state/cloud.env check`. On 401/403, end with "Bot not run: API key rejected
     (or tournament not joined / Terms not accepted)".

3. **Market map (only if `state/market_map.csv` does not exist).**
   - Run `sigcup --env state/cloud.env suggest-map --out state/suggested_map.csv`.
   - Read the suggestions and write `state/market_map.csv`, using the columns
     `sig_exchange_id,label,source,ref,invert,weight,enabled`.
   - Set `enabled=1` only on rows where you are confident the reference market resolves exactly like
     the SIG market: the same race, the same party or outcome, and the same election (2026 general).
     Set `invert=1` where SIG YES equals the reference's NO.
   - Leave doubtful matches out. A wrong mapping loses money; a missing one only misses trades.
   - Commit the map. The NO-basket arbitrage needs no map, so it trades even if the map is empty.

4. **Trade.** Start the bot in the background, with a 7,200,000 ms (2 h) timeout:
   `sigcup --env state/cloud.env run --live --minutes 100 --report-file state/last_report.txt > state/run.log 2>&1`.
   - The bot decides paper or live by itself. It runs in paper mode until `LIVE_FROM`, then switches
     to live only after at least 30 healthy paper cycles.
   - Don't poll. Wait to be re-invoked when it exits.

5. **If it crashed or every cycle errored** (look at `tail -50 state/run.log`):
   - If the cause is clearly a mismatch between the code and the real API (a renamed field, a
     different payload shape), make the smallest fix in `src/sigcup/`, add or adjust a test, run
     `pytest -q`, commit and push. Then restart step 4 with the remaining time, or with
     `--minutes 60` if more than 40 minutes are left.
   - Otherwise don't touch the code. Report the error.

6. **Save state.**
   - Run `git add state/ && git commit -m "bot state <UTC time>"`.
   - Then run `git pull --rebase origin claude/quirky-darwin-u0tfmx && git push -u origin claude/quirky-darwin-u0tfmx`.
   - If the push fails because of the network, retry up to 4 times with backoff.

7. **Final message, the notification.** Keep it to at most 8 lines, built from `state/last_report.txt`:
   - mode (PAPER or LIVE, and why);
   - health;
   - realized P&L for the window and all-time, plus open mark-to-market;
   - the number of trades, and the largest one;
   - arb baskets held, and any uneven basket;
   - open convergence positions;
   - any error or alert.

   Put anything that needs the owner's attention first.
