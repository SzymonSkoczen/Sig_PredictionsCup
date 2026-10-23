
## 2026-10-23T00:09Z run
⚠️ LIVE blocked: API key lacks 'trade' scope (403 INSUFFICIENT_SCOPES) · health DEGRADED · P&L run 0 / all-time n/a (paper only) · open MTM n/a
Trades: 0 live (57 paper NO-basket buys in first segment, run cut off by container restart ~23:55 UTC)
✅ Went well: preflight OK, 27 tests pass, paper arb found 117 multi-party races; best locked edges +0.010–0.020/set (AZ-01, Alabama Senate, Alaska Gov)
❌ Went wrong: live mode switched on but every order 403s; suggest-map hung 17+ min (killed), so market map is empty (gap trading off, arb only)
💡 Improve (needs your OK): none yet, too early to tell; paper arb repeats same baskets (AZ-01 x368 several times) so check whether it re-buys filled sets
🔎 Opportunities: map key races once suggest-map is fixed/faster to enable gap trading; no other data (no report produced)
🔧 Fixed: nothing (not a code bug). ACTION: regenerate the SIG API key with trade scope in the Cup settings and update SIG_API_KEY
