# Scheduled cloud run (every 2 hours)

These are the instructions a scheduled Claude Code cloud session follows each time it fires.
Each run trades for about 100 minutes, saves the bot's state to git, and ends with a short
summary, which arrives as a push notification on the owner's phone. Nobody approves trades.

Branch: `claude/quirky-darwin-u0tfmx` (repo `szymonskoczen/sig_predictionscup`).

## Rules

- Never print, log, commit or echo `SIG_API_KEY`. It comes from the environment only.
- Only push to `claude/quirky-darwin-u0tfmx`.
- Fix bugs automatically, but **never change the strategy**. Leave these alone unless the owner
  asks in a message:
  - entry and exit thresholds, sizing, Kelly, risk caps, stop-loss and timeout values;
  - `ARB_*` and `LIVE_FROM`;
  - anything in `state/cloud.env`, and the defaults in `src/sigcup/config.py`;
  - the trading rules in `strategy.py` and `arb.py`, meaning when to buy or sell and how much.

  Strategy ideas go in the notification as a "Suggestion:" line.
- What counts as a bug: a crash or exception; an API request that's rejected or has the wrong
  shape (bad field name, wrong units, missing `tournamentId`); a ledger that disagrees with the
  exchange; pending orders that never reconcile; a basket left uneven because repair/unwind logic
  misbehaves; or a report that is wrong. A trade that lost money while the code did what the rules
  say is **not** a bug.
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

3. **Review the previous run and fix bugs.** Spend at most 15 minutes on this step.
   - Read `sigcup --env state/cloud.env review --hours 3`, `state/last_report.txt` and
     `state/last_issues.log`, where present.
   - For each bug (see Rules), find the root cause in `src/sigcup/` and make the smallest fix.
     Add a test that would have caught it.
   - Run `pytest -q`. If it isn't fully green, revert your change with `git checkout -- src tests`
     and report the bug instead.
   - Commit each fix separately (`fix: <what> (seen in run <UTC time>)`) and push it before trading.
   - If a market-map row is clearly wrong (the reference prices a different race or outcome), set
     it to `enabled=0`. Removing a bad mapping is a fix. Adding new rows is not.
   - Nothing to fix → move on. Don't refactor or tidy.

4. **Market map (only if `state/market_map.csv` does not exist).**
   - Run `sigcup --env state/cloud.env suggest-map --out state/suggested_map.csv`.
   - Read the suggestions and write `state/market_map.csv`, using the columns
     `sig_exchange_id,label,source,ref,invert,weight,enabled`.
   - Set `enabled=1` only on rows where you are confident the reference market resolves exactly like
     the SIG market: the same race, the same party or outcome, and the same election (2026 general).
     Set `invert=1` where SIG YES equals the reference's NO.
   - Leave doubtful matches out. A wrong mapping loses money; a missing one only misses trades.
   - Commit the map. The NO-basket arbitrage needs no map, so it trades even if the map is empty.

5. **Trade.** Start the bot in the background, with a 7,200,000 ms (2 h) timeout:
   `sigcup --env state/cloud.env run --live --minutes 100 --report-file state/last_report.txt > state/run.log 2>&1`.
   - The bot decides paper or live by itself. It runs in paper mode until `LIVE_FROM`, then switches
     to live only after at least 30 healthy paper cycles.
   - Don't poll. Wait to be re-invoked when it exits.

6. **If it crashed or every cycle errored** (look at `tail -50 state/run.log`):
   - If the cause is clearly a mismatch between the code and the real API (a renamed field, a
     different payload shape), make the smallest fix in `src/sigcup/`, add or adjust a test, run
     `pytest -q`, commit and push. Then restart step 5 with the remaining time, or with
     `--minutes 60` if more than 40 minutes are left. Use the same rules as step 3.
   - Otherwise don't touch the code. Report the error.

7. **Save state.**
   - Keep the useful part of the log for the next run's review:
     `grep -E -A8 "WARNING|ERROR|Traceback" state/run.log | tail -400 > state/last_issues.log || true`.
   - Run `git add state/ && git commit -m "bot state <UTC time>"`.
   - Then run `git pull --rebase origin claude/quirky-darwin-u0tfmx && git push -u origin claude/quirky-darwin-u0tfmx`.
   - If the push fails because of the network, retry up to 4 times with backoff.

8. **Final message, the notification.** Keep it to at most 8 lines, built from `state/last_report.txt`:
   - mode (PAPER or LIVE, and why);
   - health;
   - realized P&L for the window and all-time, plus open mark-to-market;
   - the number of trades, and the largest one;
   - arb baskets held, and any uneven basket;
   - open convergence positions;
   - any error or alert;
   - `Fixed: ...` naming each bug fixed this run (one line), if any;
   - `Suggestion: ...` with a strategy idea backed by the review numbers, if any (never applied
     automatically).

   Put anything that needs the owner's attention first.
