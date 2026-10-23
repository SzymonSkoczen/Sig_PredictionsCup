
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

## 2026-10-23T09:40Z run
🚨 LIVE, 0 trades: every cycle failed (23 errors), 403 INSUFFICIENT_SCOPES, SIG_API_KEY lacks "trade" scope (4th run in a row). ACTION: regenerate the key with trade scope. Health DEGRADED · P&L run +0 / all-time +0 · open MTM +0 (account 100000)
Trades: 0 (gap 0, arb 0). No uneven basket, no convergence positions.
✅ Went well: reads fine, 117 races watched, no crashes.
❌ Went wrong: no order can be placed (scope); market map has 0 enabled rows so gap trading is off (237 unmapped).
💡 Improve: arb edge ≥0.01 in 42 races (Rhode Island Gov +0.075, Montana Sen +0.060, median depth 1,268 shares); verified market map would enable gap trades. Not applied.
🔎 Opportunities: NO-basket arb Rhode Island Gov +0.075, Montana Sen +0.060, Nebraska Sen +0.040; two-party YES<1: MN-05 +0.040, NH Sen +0.025, Mass Gov +0.020, Maine Gov +0.015 (third-party risk).
🔧 Fixed: nothing (key permission issue, not a code bug).

## 2026-10-23T11:37Z run
🚨 LIVE, trading works (key scope fixed) but LEDGER MISMATCH: account is fully invested (cost basis ~99,999 across 19 NO-basket positions) while the bot's ledger shows 0 trades/positions; ~975 "Insufficient funds" rejections as it kept re-buying. Health OK · run P&L +0 (unrecorded) · account value 99,450 (MTM -550)
Trades: ~170 arb baskets sent, all filled on the exchange, none recorded. Biggest: Arizona Gov x2000.
✅ Went well: scope/auth fixed, 387 cycles, Kalshi map 192 mapped, no crashes.
❌ Went wrong: Position parser read NO holdings (option YES, negative qty) as negative, so reconcile recorded 0 fills; buying power exhausted (arb ignored held sets).
💡 Improve: cap per-race arb sets by exchange positions, not ledger only; arb edges were thin (+0.01–0.03/set) vs 2000-set size — consider lower ARB sizing. Not applied.
🔎 Opportunities: gaps Rhode Island Sen R/D +0.12/+0.116, Mississippi Sen D +0.083 (not traded: funds gone); two-party YES<1: Maine Gov +0.03, MN-05 +0.03.
🔧 Fixed: nothing by me — the same Position-parsing bug was already fixed upstream (e220546) plus resync (80f9bca), which takes effect next run.

## 2026-10-23T13:37Z run
LIVE (trading works again, key scope fixed) · health OK (kalshi 429s x5, harmless) · P&L run -347 / all-time -347 · open MTM -1,769
Trades: 87 (gap/conv buys 9, arb unwinds ~78; 7 arb baskets + 7 conv positions held) · best: n/a (nothing closed in profit) · worst: arb unwinds, each -0..-8 (CA-22, Arizona Gov)
✅ Went well: 414 cycles, 0 errors, first live fills; 191/192 mapped markets priced; conv entries at edges 0.08-0.12 (RI Senate, RI Gov, Hawaii Gov).
❌ Went wrong: realized -347 came from arb baskets unwound "for free cash" at ~-0.02 each to fund conv buys; all 7 conv positions still under entry mark (-0.005..-0.01, none converged yet, held ~100m); cash is tight (holdings 89k of 99k).
💡 Improve (needs your OK): unwinding arb baskets at a loss to fund gap trades costs ~347 vs a theoretical +1-2% arb lock-in; consider not unwinding arbs for cash or raising the gap-trade edge floor. Too early to tell on convergence (first live run).
🔎 Opportunities: RI Senate/Gov gaps +0.13/+0.116 already traded; Hawaii Gov YES basket Σasks<1 by 0.06 (risk: third-party win); NO-arb RI Gov +0.085, Montana Sen +0.07 (cash-limited). 45 markets still unmapped.
🔧 Fixed: nothing (no code bug).

## 2026-10-23T15:37Z run
LIVE (container restart killed bot at ~53m; resumed 45m) · health OK (kalshi 429s, 1 API timeout) · P&L run -305 / all-time -652 · open MTM -1,390
Trades: 73 in 2h (conv buys ~10, arb unwinds ~60) · best: n/a · worst: Alaska Senate arb unwinds (-13, -4 each)
✅ Went well: 0 errors, 191/192 priced; 10 conv positions open at edges 0.07-0.13 (RI, MS, HI, VA, TN); several held 3h, marks flat/slightly down.
❌ Went wrong: realized -305 this window, again from arb baskets unwound "for free cash" at ~-0.02/set; conv positions not converged after 3h (e.g. Hawaii Gov mark 0.880 vs entry 0.898, -120).
💡 Improve (needs your OK): arb-unwind-for-cash cost ~650 all-time across 2 runs while no conv position has converged; consider disabling cash-funding unwinds or raising gap MIN_EDGE. Too early on convergence (2 live runs).
🔎 Opportunities: Hawaii Gov YES basket Σasks<1 by 0.06, MN-05 +0.035 (risk: third-party win); NO-arb RI Gov +0.085, Montana Sen +0.07 (cash-limited); 45 markets unmapped. Hawaii/RI repeat across runs.
🔧 Fixed: nothing (no code bug).

## 2026-10-23T17:37Z run
LIVE · health OK (kalshi 429s x7, 2 API errors) · P&L run -186 / all-time -838 · open MTM -810
Trades: 17 (conv buys 3, arb unwinds 14, 0 new baskets) · best: n/a · worst: Alaska Senate arb unwind -113 (8899 sets @ -0.013)
✅ Went well: 438 cycles, 0 errors/crashes; 10 conv positions held at edges 0.08-0.12; open MTM improved -1,390 → -810.
❌ Went wrong: realized -186 again from arb baskets unwound "for free cash" (Alaska Senate -113, -53); no conv position has converged after 5h (Hawaii Gov 0.885 vs entry 0.898).
💡 Improve (needs your OK): 3 runs, ~838 lost to cash-funding arb unwinds while 0 conv positions converged; consider disabling cash-funding unwinds or lowering conv size. Convergence still too early to judge.
🔎 Opportunities: Hawaii Gov YES basket Σasks<1 by 0.05, MN-05 +0.035 (third-party risk); NO-arb RI Gov +0.075, Montana +0.06 (cash-limited); 45 markets unmapped. Hawaii/RI recur every run.
🔧 Fixed: nothing (no code bug).

## 2026-10-23T19:37Z run
LIVE · health OK (1 cycle failed on a null API body, recovered; kalshi 429s) · P&L run +0 / all-time -838 · open MTM -449 (improved from -810)
Trades: 0 (no gap trades, no new baskets, no unwinds) · best: n/a · worst: n/a
✅ Went well: no arb unwinds, so no new realised loss (first flat run since going live); open MTM -810 -> -449; 421 cycles, 191/192 priced.
❌ Went wrong: 0 entries despite 50 markets with gap >=0.04 (RI Senate R +0.12), likely cash-limited (holdings 73.8k of 98.8k, 10 conv + 5 baskets); 19:13 AttributeError on a null positions response (one cycle lost).
💡 Improve (needs your OK): 7h-old conv positions have not converged (RI Gov 0.905 vs fair 0.995, Hawaii 0.900 vs 0.983); too early to tell if gaps close or the fair value is stale; check whether the Cup lags Kalshi by design before adding size.
🔎 Opportunities: Hawaii Gov YES basket Σasks<1 by 0.04, Maine Gov +0.035 (third-party risk); NO-arb RI Gov +0.07, Montana +0.055; SC Senate ref moved 3.5pts, Cup only 1.5 (news lag); 45 markets unmapped. Hawaii/RI recur every run.
🔧 Fixed: null body from positions/prices no longer crashes the cycle (+test, 38 pass).

## 2026-10-23T21:37Z run
LIVE · health OK (kalshi 429s, 2 API errors) · P&L run +0 / all-time -838 · open MTM -618
Trades: 0 (no gap trades, no baskets, no unwinds) · best: n/a · worst: n/a
✅ Went well: flat run, no new realised loss; 410 cycles, 192/192 priced, no crashes after the null-body fix.
❌ Went wrong: 0 entries despite 47 markets with gap >=0.04 (RI Senate R +0.117), likely cash-limited; open MTM -449 -> -618; 10 conv positions held 6-9h with no convergence.
💡 Improve (needs your OK): 9h-old conv positions not converging (RI Gov 0.905 vs fair 0.996, Hawaii 0.895 vs 0.983); fair values may be stale or Cup lags by design; consider lower conv size / MAX_HOLD_HOURS. Too early to be sure.
🔎 Opportunities: Hawaii Gov YES basket Σasks<1 by 0.035, Maine Gov +0.03, IA-02 +0.03 (third-party risk); NO-arb RI Gov +0.065, Montana +0.055 (cash-limited); 45 markets unmapped. Hawaii/RI recur every run.
🔧 Fixed: nothing (no code bug).
