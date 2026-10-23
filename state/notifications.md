
## 2026-10-23T00:09Z run
⚠️ LIVE blocked: API key lacks 'trade' scope (403 INSUFFICIENT_SCOPES) · health DEGRADED · P&L run 0 / all-time n/a (paper only) · open MTM n/a
Trades: 0 live (57 paper NO-basket buys in first segment, run cut off by container restart ~23:55 UTC)
✅ Went well: preflight OK, 27 tests pass, paper arb found 117 multi-party races; best locked edges +0.010–0.020/set (AZ-01, Alabama Senate, Alaska Gov)
❌ Went wrong: live mode switched on but every order 403s; suggest-map hung 17+ min (killed), so market map is empty (gap trading off, arb only)
💡 Improve (needs your OK): none yet, too early to tell; paper arb repeats same baskets (AZ-01 x368 several times) so check whether it re-buys filled sets
🔎 Opportunities: map key races once suggest-map is fixed/faster to enable gap trading; no other data (no report produced)
🔧 Fixed: nothing (not a code bug). ACTION: regenerate the SIG API key with trade scope in the Cup settings and update SIG_API_KEY
📊 SIG Cup bot — PAPER, health OK (1h40m, 539 cycles, 0 errors) — 2026-10-23 01:37 UTC
Mode: PAPER (0/30 healthy paper cycles counted). P&L: realized +0 (window/all-time), open MTM -817.
Trades: 54 paper arb legs (9 NO baskets re-bought), largest 2000 sets. Baskets held: Alabama Sen 18000, Alaska Gov 16855, Alaska Sen 16009 sets. No uneven basket. Convergence positions: 0.
✅ Went well: no errors, API reads 15/70 per min, 117 races watched.
❌ Went wrong: market map empty (0 mapped), so gap trading never ran; "healthy paper cycles" stuck at 0/30, so live never unlocks. Paper arb re-bought the same static depth every cycle (18000 sets vs 2000 intended) — likely paper-only artefact, unverified.
💡 Improve: check why healthy-cycle counter stays 0 after 539 OK cycles; cap arb sets per race in paper; build a verified market map (suggest-map hung last time).
🔎 Opportunities: NO-basket arb up to +0.070 (Montana Sen, Rhode Island Gov), Nebraska Sen +0.045; two-party YES<1: MN-05 +0.050, Maine Gov +0.030, Mass Gov +0.025, NH Sen +0.020. 237 markets unmapped.
🔧 Fixed: nothing (no bugs changed).

## 2026-10-23T03:38Z run
⚠️ PAPER (live aborted: API key lacks 'trade' scope, 403 INSUFFICIENT_SCOPES on every live cycle) · health OK · P&L run +0 / all-time +0 · open MTM -491
Trades: 0 (gap trades 0, arb baskets 0; paper arb capped at held baskets)
✅ Went well: paper segment 541 cycles, 0 errors; 117 races watched; 3 baskets held (Alabama Sen 18000, Alaska Gov 16855, Alaska Sen 16009 sets), all even.
❌ Went wrong: live blocked by key scope (ACTION: regenerate SIG_API_KEY with trade scope); market map empty so gap trading is off (0 mapped).
💡 Improve (needs your OK): too early to tell on thresholds; arb edge ≥0.01 reached in 51 races but capital cap blocks new buys, consider ARB_MAX_CAPITAL once live works.
🔎 Opportunities: arb Rhode Island Gov +0.085, Montana Sen +0.080 (recurring); two-party YES<1: MN-05 +0.060, Maine Gov +0.025 (risk: third-party win). 237 unmapped markets.
🔧 Fixed: nothing (no code bug).

## 2026-10-23T05:36Z run
🚨 LIVE, 0 trades: every cycle failed (24 errors) — 403 INSUFFICIENT_SCOPES, SIG_API_KEY lacks "trade" scope. ACTION: regenerate the key with trade scope. Health DEGRADED · P&L run +0 / all-time +0 · open MTM +0 (account 100000, no holdings)
Trades: 0 (gap 0, arb baskets 0). No uneven basket, no convergence positions.
✅ Went well: reads fine, 117 races watched, no crashes; order shape reached the API (rejected only on scope).
❌ Went wrong: live cannot place any order (scope); market map has 0 enabled rows so gap trading is off (237 markets unmapped).
💡 Improve: once trading works, arb edge ≥0.01 appeared in 47 races (best Rhode Island Gov +0.085, Montana Sen +0.065, depth median 2,685 shares) — consider a verified market map to enable gap trades. Not applied.
🔎 Opportunities: NO-basket arb Rhode Island Gov +0.085, Montana Sen +0.065, Nebraska Sen +0.040; two-party YES<1: MN-05 +0.050, Maine Gov +0.025, NH Sen +0.020, Mass Gov +0.020 (risk: third-party win).
🔧 Fixed: nothing (scope error is a key/permission issue, not a code bug).

## 2026-10-23T07:36Z run
🚨 LIVE, 0 trades: every cycle failed (24 errors), 403 INSUFFICIENT_SCOPES, SIG_API_KEY lacks "trade" scope (3rd run in a row). ACTION: regenerate the key with trade scope. Health DEGRADED · P&L run +0 / all-time +0 · open MTM +0 (account 100000)
Trades: 0 (gap 0, arb 0). No uneven basket, no convergence positions.
✅ Went well: reads fine, 117 races watched, no crashes.
❌ Went wrong: no order can be placed (scope); market map has 0 enabled rows so gap trading is off (237 unmapped).
💡 Improve: arb edge ≥0.01 in 45 races (Rhode Island Gov +0.080, Montana Sen +0.060, median depth 2,687 shares); a verified market map would enable gap trades. Not applied.
🔎 Opportunities: NO-basket arb Rhode Island Gov +0.080, Montana Sen +0.060, Nebraska Sen +0.040; two-party YES<1: MN-05 +0.050, NH Sen +0.025, Maine Gov +0.020, Mass Gov +0.020 (third-party risk).
🔧 Fixed: nothing (key permission issue, not a code bug).
