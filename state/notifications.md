
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

## 2026-10-23T23:58Z run
LIVE · health OK (kalshi 429s x12, 0 errors) · P&L run +0 / all-time -838 · open MTM -316 (improved from -618)
Trades: 0 (no gap trades, no new baskets, no unwinds) · best: n/a · worst: n/a
✅ Went well: 432 cycles, 0 errors; no new realised loss for 3rd flat run; open MTM -618 -> -316; 192/192 priced.
❌ Went wrong: 0 entries despite 42 markets with gap >=0.04 (RI Senate R +0.117), likely cash-limited (holdings 74k of 99k); conv positions held 8-11h still unconverged (RI Gov 0.905 vs fair 0.996).
💡 Improve (needs your OK): conv positions converge slowly while gaps persist; too early to tell if fair value is stale vs Cup lagging; review MAX_HOLD_HOURS/EXIT_BAND only if still unconverged in the next runs.
🔎 Opportunities: Hawaii Gov YES basket Σasks<1 by 0.035, Maine Gov +0.030 (third-party risk); NO-arb RI Gov +0.060, Montana +0.050 (cash-limited); 45 markets unmapped. Hawaii/RI recur every run.
🔧 Fixed: nothing (no code bug).

## 2026-10-24T01:37Z run
LIVE · health OK (kalshi 429s x6, 0 SIG errors) · P&L run -360 / all-time -1,198 · open MTM -467
Trades: 432 fills (arb baskets ~108 buys/sells, 0 gap trades) · best: n/a · worst: Delaware Senate arb timeout unwinds (-14, -11, -9)
✅ Went well: 412 cycles, 0 errors, 192/192 priced; open MTM -618 -> -467; 10 conv positions kept.
❌ Went wrong: realized -360 from arb baskets bought then sold on "arb timeout" (69 losing exits, e.g. Delaware Senate -34 total); 10 conv positions held 10-13h, still unconverged (RI Gov 0.905 vs fair 0.996).
💡 Improve (needs your OK): arb baskets are churning (buy at +0.01-0.017/set, timeout-sold at a loss); consider raising ARB_MIN_PROFIT or lengthening the arb timeout. Conv gaps not closing after 13h: review MAX_HOLD_HOURS / fair-value staleness.
🔎 Opportunities: Hawaii Gov / RI recur every run (RI Gov +0.085 gap); 45 markets unmapped; Kalshi 429s limit refresh.
🔧 Fixed: nothing (no code bug).

## 2026-10-24T03:37Z run
LIVE · health OK (kalshi 429s x7, 0 SIG errors) · P&L run -1 / all-time -1,199 · open MTM -421
Trades: 6 fills (0 gap trades, 1 arb basket bought, 1 unwind) · best: n/a · worst: Alabama Senate timeout unwind (-1)
✅ Went well: 458 cycles, 0 errors, 192/192 priced; realised churn stopped (-360 -> -1); open MTM -467 -> -421.
❌ Went wrong: 0 gap entries despite 37 markets with gap >=0.04 (RI Senate R +0.117); 10 conv positions held 12-15h, still unconverged (RI Gov 0.900 vs fair 0.996).
💡 Improve (needs your OK): conv gaps not closing after 15h; consider MAX_HOLD_HOURS/EXIT_BAND or check fair-value staleness. Arb baskets need ~0.01/set but timeout-sell at ~0.975; ARB_MIN_PROFIT up if churn returns.
🔎 Opportunities: Hawaii Gov YES basket Σasks<1 by 0.040 (third-party risk), Maine Gov +0.025; NO-arb RI Gov +0.065, Montana +0.060 (cash-limited); 45 markets unmapped. Hawaii/RI recur every run.
🔧 Fixed: nothing (no code bug).

## 2026-10-24T05:37Z run
LIVE · health OK (kalshi 429s x2, 0 SIG errors) · P&L run -53 / all-time -1,251 · open MTM -404
Trades: 77 fills (0 gap trades, ~13 arb baskets bought, 25 timeout unwinds) · best: n/a · worst: CA Governor basket partial sell (1242/2000 R leg, repaired by re-buying 758 D, cost 0.997/set)
✅ Went well: 467 cycles, 0 errors, 192/192 priced; repair logic evened the uneven CA Gov basket; open MTM -421 -> -404.
❌ Went wrong: realized -53 from Alabama Senate arb timeout unwinds (cost 0.990 vs sell-now 0.970); 0 gap entries despite gaps (RI Senate R ~+0.12); 10 conv positions held 14-17h, unconverged (RI Gov 0.905 vs fair 0.996).
💡 Improve (needs your OK): arb baskets churn (bought +0.015/set, timeout-sold ~-0.02/set): consider longer arb timeout or higher ARB_MIN_PROFIT; conv gaps not closing after 17h: review MAX_HOLD_HOURS/EXIT_BAND or fair-value staleness.
🔎 Opportunities: RI Gov/Senate gaps ~+0.09-0.12 persist every run (cash-limited; needs freeing cash from stale arb baskets); Hawaii Gov YES basket and 45 unmapped markets recur.
🔧 Fixed: nothing (no code bug).

## 2026-10-24T07:40Z run
LIVE · health OK (kalshi 429s x1, 0 SIG errors) · P&L run +16 / all-time -1,236 · open MTM -385
Trades: 29 fills (0 gap trades, ~10 arb baskets bought, FL Gov take-profit unwinds +14) · best: FL Gov take-profit (+25 R leg) · worst: FL Gov D leg (-12)
✅ Went well: 459 cycles, 0 errors, 192/192 priced; realized +16 (first positive run in a while); open MTM -404 -> -385.
❌ Went wrong: 0 gap entries despite 41 markets with gap >=0.04 (RI Senate R +0.117); 10 conv positions held 16-19h, unconverged (RI Gov 0.905 vs fair 0.997).
💡 Improve (needs your OK): 63 near misses (>=0.02) and 41 gaps reached but no entries and no stop-outs -> cash is the limit (holdings 74k of 99k); consider smaller arb sizing or recycling stale baskets to fund gap trades; conv positions 19h old: review MAX_HOLD_HOURS/EXIT_BAND.
🔎 Opportunities: RI Gov/Senate gaps +0.09-0.12 persist every run (cash-limited); Hawaii Gov YES basket Σasks<1 by 0.040, Maine Gov +0.030 (third-party risk); 45 unmapped markets.
🔧 Fixed: nothing (no code bug).

## 2026-10-24T09:40Z run
LIVE · health OK (kalshi 0 failures, 0 SIG errors) · P&L run -6 / all-time -1,241 · open MTM -182
Trades: 37 fills (0 gap trades, ~10 arb baskets bought, Alaska Gov take-profit unwinds ~+10) · best: Alaska Gov take-profit (+6) · worst: n/a (no losing exits)
✅ Went well: 471 cycles, 0 errors, 192/192 priced; open MTM -385 -> -182; arb take-profits on Alaska Gov netted ~+10.
❌ Went wrong: 0 gap entries despite 42 markets with gap >=0.04 (RI Senate R +0.117); 10 conv positions held 18-21h, unconverged (RI Gov 0.905 vs fair 0.997).
💡 Improve (needs your OK): 56 near misses + 42 reached gaps, no entries and no stop-outs -> cash-limited (22 arb baskets tie up cash); consider smaller arb sizing/recycling baskets to fund gap trades; conv positions 21h old: review MAX_HOLD_HOURS/EXIT_BAND.
🔎 Opportunities: RI Gov/Senate gaps +0.09-0.12 recur every run (cash-limited); Hawaii Gov YES basket Σasks<1 by 0.045 (third-party risk), Maine Gov +0.025; 45 unmapped markets.
🔧 Fixed: nothing (no code bug).

## 2026-10-24T11:40Z run
LIVE · health OK (kalshi 429s x5, 0 SIG errors) · P&L run -99 / all-time -1,340 · open MTM -139
Trades: 118 fills (0 gap trades, ~20 arb baskets bought, FL-20 take-profits ~0, Alabama Sen timeout unwind) · best: FL-20 R leg +6 · worst: Alabama Senate timeout unwind (-33)
✅ Went well: 466 cycles, 0 errors, 192/192 priced; open MTM -182 -> -139; account value 98,928.
❌ Went wrong: realized -99, mostly Alabama Senate arb timeout unwind (2187 sets, cost 0.990 vs sell 0.97-0.94/0.035, -33); 0 gap entries despite 39 gaps >=0.04; 10 conv positions held 20-23h unconverged (RI Gov 0.895 vs fair 0.997).
💡 Improve (needs your OK): arb churn again (+0.01/set entries, timeout sells ~-0.02/set; 3 runs in a row) -> raise ARB_MIN_PROFIT or lengthen arb timeout; 95 gap/near-miss markets, no entries, no stop-outs, cash tied in 20 baskets -> smaller arb sizing; review MAX_HOLD_HOURS/EXIT_BAND (23h held).
🔎 Opportunities: RI Senate R +0.112 / D +0.098 / RI Gov +0.097 gaps recur every run (cash-limited); Hawaii Gov YES basket Σasks<1 by 0.050 (third-party risk), NH Sen +0.020, Maine Gov +0.020; 45 unmapped markets.
## 2026-10-24T13:40Z run
LIVE · health OK (kalshi 4 failures, 0 SIG errors) · P&L run -337 / all-time -1,579 · open MTM -52
Trades: ~251 fills (0 gap trades, ~25 arb baskets, many arb timeout unwinds) · best: n/a · worst: CO-08 basket timeout (-22), AZ-01 timeout (-17)
✅ Went well: 440 cycles, 0 errors, 192/192 priced; open MTM improved -182 -> -52.
❌ Went wrong: realized -337 this run (worst so far), mostly arb basket timeout unwinds (bought +0.010/set, sold below cost); 0 gap entries despite 28 gaps >=0.04; 10 conv positions held 22-25h, unconverged.
💡 Improve (needs your OK): arb timeouts lose money 3 runs in a row (cost 0.990 vs sell-now 0.975): raise ARB_MIN_PROFIT or lengthen arb hold; cash-limited gap trades (RI Senate R +0.111): recycle baskets; conv positions 25h old: review MAX_HOLD_HOURS/EXIT_BAND.
🔎 Opportunities: RI Gov/Senate gaps +0.09-0.11 recur every run; RI Gov NO-arb +0.060, Nebraska Sen +0.045; Hawaii Gov YES basket +0.040 (third-party risk); 45 unmapped markets.
🔧 Fixed: nothing (no code bug).

## 2026-10-24T15:40Z run
LIVE · health OK (kalshi 6 failures, 0 SIG errors) · P&L run +8 / all-time -1,571 · open MTM +20
Trades: 32 fills (0 gap trades, ~10 arb baskets bought, Alaska Sen take-profits ~+10) · best: Alaska Sen R leg +14 · worst: Alaska Sen D leg -7
✅ Went well: 449 cycles, 0 errors, 192/192 priced; realized +8 (vs -337 last run); open MTM -52 -> +20.
❌ Went wrong: 0 gap entries despite 29 gaps >=0.04 (RI Senate R +0.111); 10 conv positions held 24-27h, unconverged (RI Gov 0.905 vs fair 0.997).
💡 Improve (needs your OK): 29 reached + 69 near-miss gaps, no entries, no stop-outs, 72k of 99k tied up -> cash-limited; smaller arb sizing/recycling baskets; review MAX_HOLD_HOURS/EXIT_BAND (27h held).
🔎 Opportunities: RI Senate/Gov gaps +0.09-0.11 recur every run (cash-limited); Hawaii Gov YES basket Σasks<1 by 0.035 (third-party risk); 45 unmapped markets.

## 2026-10-24T17:40Z run
LIVE · health OK (kalshi 6 failures/429, 0 SIG errors) · P&L run -96 / all-time -1,666 · open MTM -46
Trades: ~115 fills (0 gap trades, ~15 arb baskets bought, arb timeout unwinds) · best: Delaware Sen R leg +3 · worst: Delaware Senate timeout (-24)
✅ Went well: 449 cycles, 0 errors, 192/192 priced; open MTM roughly flat (-46); 0 SIG API errors.
❌ Went wrong: realized -96, mostly Delaware Senate arb timeout (1494 sets, -24); 0 gap entries despite 32 gaps >=0.04; 10 conv positions held 26-29h unconverged (RI Gov 0.905 vs fair 0.997).
💡 Improve (needs your OK): arb timeout unwinds lose money 4 of last 5 runs (buy +0.010/set, sell below cost) -> raise ARB_MIN_PROFIT or lengthen arb hold; 32 reached + 60 near-miss gaps, none entered, 73k of 99k tied up -> smaller arb sizing; review MAX_HOLD_HOURS/EXIT_BAND (29h held).
🔎 Opportunities: RI Senate R +0.105 / D +0.097 / RI Gov +0.086 gaps recur every run (cash-limited); Hawaii Gov YES basket Σasks<1 by 0.035 (third-party risk); 45 unmapped markets.

## 2026-10-24T19:40Z run
LIVE · health OK (kalshi 12 failures/429, 0 SIG errors) · P&L run -29 / all-time -1,695 · open MTM +55
Trades: ~97 fills (0 gap trades, ~12 arb baskets bought, arb timeout unwinds) · best: n/a · worst: Iowa Senate timeout unwind (-5)
✅ Went well: 429 cycles, 0 errors, 192/192 priced; realized -29 (vs -96); open MTM -46 -> +55.
❌ Went wrong: 0 gap entries despite 33 gaps >=0.04 (RI Senate R +0.105); 10 conv positions held 28-31h unconverged (RI Gov 0.905 vs fair 0.997); 1 unfilled sell (NH-01 R 0/45).
💡 Improve (needs your OK): arb timeout unwinds keep losing small amounts (5 of 6 runs) -> raise ARB_MIN_PROFIT or lengthen arb hold; 33 reached + 65 near-miss gaps, none entered, ~73k tied up -> smaller arb sizing; review MAX_HOLD_HOURS/EXIT_BAND (31h held).
🔎 Opportunities: RI Senate/Gov gaps +0.09-0.105 recur every run (cash-limited); YES baskets Σasks<1: NH/ME/HI Governor +0.030 (third-party risk); 45 unmapped markets.

## 2026-10-24T21:40Z run
LIVE · health OK (kalshi 5 failures/429, 0 SIG errors) · P&L run +6 / all-time -1,689 · open MTM -196
Trades: 16 fills (0 gap trades, ~8 arb baskets bought, Kansas Senate take-profits ~+7) · best: Kansas Sen D leg +9 · worst: Kansas Sen R leg -6
✅ Went well: 453 cycles, 0 errors, 192/192 priced; realized +6 (vs -29); Kansas Senate arb take-profits netted ~+7.
❌ Went wrong: open MTM +55 -> -196; 0 gap entries despite 37 gaps >=0.04 (RI Senate R +0.111); 10 conv positions held 30-33h unconverged.
💡 Improve (needs your OK): arb timeouts lost money in most recent runs -> raise ARB_MIN_PROFIT or lengthen arb hold; 37 reached + 65 near-miss gaps, none entered, ~73k tied up -> smaller arb sizing; review MAX_HOLD_HOURS/EXIT_BAND (33h held).
🔎 Opportunities: RI Senate/Gov gaps +0.09-0.11 recur every run (cash-limited); RI Gov NO-arb +0.070, Montana Sen +0.045; 45 unmapped markets.

## 2026-10-24T23:40Z run
LIVE · health OK (kalshi 8 failures/429, 0 SIG errors) · P&L run -14 / all-time -1,703 · open MTM -22
Trades: ~33 fills (0 gap trades, ~10 arb baskets bought, NH-01 timeout unwinds) · best: n/a · worst: NH-01 R timeout (-7)
✅ Went well: 432 cycles, 0 errors, 192/192 priced; open MTM -196 -> -22; 0 SIG API errors.
❌ Went wrong: realized -14, NH-01 arb timeouts (-8 net); 0 gap entries despite 38 gaps >=0.04; 10 conv positions held 32-35h unconverged.
💡 Improve (needs your OK): arb timeouts lose small amounts in most runs -> raise ARB_MIN_PROFIT or lengthen arb hold; 38 reached + 60 near-miss gaps, none entered, ~73k tied up -> smaller arb sizing; review MAX_HOLD_HOURS/EXIT_BAND (35h held).
🔎 Opportunities: RI Senate R +0.105 / D +0.097 / RI Gov +0.086 gaps recur every run (cash-limited); Hawaii Gov YES basket Σasks<1 by 0.040 (third-party risk); 45 unmapped markets.

## 2026-10-25T01:40Z run
LIVE · health OK (kalshi 6 failures/429, 0 SIG errors) · P&L run -224 / all-time -1,927 · open MTM -110
Trades: 251 fills (0 gap trades, ~60 arb baskets, 10 timeout unwinds) · best: n/a · worst: arb timeout unwinds (-33, -19, -17 per leg)
✅ Went well: 445 cycles, 0 errors, 192/192 priced; 0 stuck orders; open MTM stayed small (-110).
❌ Went wrong: realized -224 (worst run today, vs -14), 35 losing exits, mostly arb timeouts; 0 gap entries despite 40 gaps >=0.04; 10 conv positions held 34-37h unconverged; 1 unfilled buy (Iowa Sen R 0/2).
💡 Improve (needs your OK): arb timeout unwinds are the main bleed (10 this run, ~-110 on the legs listed) with only +0.010/set locked -> raise ARB_MIN_PROFIT or lengthen arb hold; 40 reached + 63 near-miss gaps, none entered, ~73k tied up -> smaller arb sizing; review MAX_HOLD_HOURS/EXIT_BAND (37h held).
🔎 Opportunities: RI Senate R +0.105 / D +0.097 / RI Gov +0.086 gaps recur every run (cash-limited); Hawaii Gov YES basket Σasks<1 by 0.045 (third-party risk); 45 unmapped markets.

## 2026-10-25T03:40Z run
LIVE · health OK (kalshi 5 failures/429, 0 SIG errors) · P&L run -1 / all-time -1,928 · open MTM -55
Trades: 8 fills (0 gap trades, 3 arb baskets bought, Colorado Senate timeout unwind) · best: n/a · worst: Colorado Senate timeout (-1/leg)
✅ Went well: 447 cycles, 0 errors, 192/192 priced; realized -1 (vs -224 last run); open MTM -110 -> -55.
❌ Went wrong: 0 gap entries despite 38 gaps >=0.04 (RI Senate R +0.105); 10 conv positions held 36-39h unconverged (RI Gov 0.905 vs fair 0.997).
💡 Improve (needs your OK): ~73k tied up in 20 arb baskets, so gaps go unentered -> smaller arb sizing; review MAX_HOLD_HOURS/EXIT_BAND (39h held); arb timeouts only quiet this run - too early to tell on ARB_MIN_PROFIT.
🔎 Opportunities: RI Senate R +0.105 / D +0.097 / RI Gov +0.086 gaps recur every run (cash-limited); Hawaii Gov YES basket Σasks<1 by 0.050 (third-party risk); 45 unmapped markets.

## 2026-10-25T05:36Z run
LIVE · health OK (kalshi 5 failures/429, 0 SIG errors) · P&L run -16 / all-time -1,944 · open MTM +61
Trades: 27 fills (0 gap trades, ~12 arb baskets bought, Arizona Gov take-profit) · best: AZ Gov D leg +20 · worst: AZ Gov R leg -10
✅ Went well: 453 cycles, 0 errors, 192/192 priced; open MTM -55 -> +61; AZ Gov arb take-profit netted +10.
❌ Went wrong: realized -16 (vs -1); 0 gap entries despite 36 gaps >=0.04 (RI Senate R +0.105); 10 conv positions held 38-41h unconverged.
💡 Improve (needs your OK): ~73k tied up in 22 arb baskets at only +0.010/set, so gaps go unentered -> smaller arb sizing; review MAX_HOLD_HOURS/EXIT_BAND (41h held); too early to tell on ARB_MIN_PROFIT.
🔎 Opportunities: RI Senate R +0.105 / D +0.097 / RI Gov +0.086 gaps recur every run (cash-limited); Hawaii Gov YES basket Σasks<1 by 0.050 (third-party risk); 45 unmapped markets.

## 2026-10-25T07:36Z run
LIVE · health OK (6 SIG 503 "balance temporarily unavailable", server-side; kalshi 1 failure) · P&L run +2 / all-time -1,942 · open MTM +257
Trades: 48 fills (0 gap trades, ~10 arb baskets, ME-02 take-profits ~0, Delaware Sen timeout ~0) · best: ME-02 take-profits (+0) · worst: Delaware Sen timeout (-0)
✅ Went well: 469 cycles, realized +2 (vs -16), open MTM +61 -> +257; arb exits now flat instead of losing.
❌ Went wrong: 0 gap entries despite 34 gaps >=0.04 (RI Senate R +0.101); 10 conv positions held 40-43h unconverged; 6 transient SIG 503s (retried OK).
💡 Improve (needs your OK): ~73k tied up in 22 arb baskets at +0.010/set, so gaps go unentered -> smaller arb sizing; review MAX_HOLD_HOURS/EXIT_BAND (43h held); too early to tell on ARB_MIN_PROFIT.
🔎 Opportunities: RI Senate R +0.101 / D +0.097 / RI Gov +0.086 gaps recur every run (cash-limited); Hawaii Gov YES basket Σasks<1 by 0.040 (third-party risk); RI Gov arb Σ YES bids +0.070 and Montana Senate +0.055 near-miss; 45 unmapped markets.

## 2026-10-25T09:36Z run
LIVE · health OK (0 SIG errors, kalshi 5 failures/429) · P&L run -6 / all-time -1,948 · open MTM +333
Trades: 71 fills (0 gap trades, ~10 arb baskets, Oregon Gov take-profits ~0) · best: Oregon Gov take-profit (+0) · worst: Oregon Gov R leg (-1)
✅ Went well: 450 cycles, 0 SIG API errors, 192/192 priced; open MTM +257 -> +333.
❌ Went wrong: realized -6; 0 gap entries despite 32 gaps >=0.04 (RI Senate D +0.097); 10 conv positions held 42-45h unconverged.
💡 Improve (needs your OK): ~73k tied up in arb baskets at +0.010/set, so gaps go unentered -> smaller arb sizing; review MAX_HOLD_HOURS/EXIT_BAND (45h held); too early to tell on ARB_MIN_PROFIT.
🔎 Opportunities: RI Senate D +0.097 / R +0.090 / RI Gov +0.086 gaps recur every run (cash-limited); RI Gov arb +0.065, Montana Senate arb +0.050 near-miss; Hawaii Gov YES basket Σasks<1 by 0.035 (third-party risk); 45 unmapped markets.

## 2026-10-25T11:36Z run
LIVE · health OK (0 SIG errors, kalshi 6 failures/429) · P&L run -56 / all-time -2,004 · open MTM +304
Trades: ~106 fills (0 gap trades, ~20 arb baskets, AZ-01 timeout unwind -3) · best: arb take-profits (~0) · worst: AZ-01 R leg timeout (-3)
✅ Went well: 462 cycles, 0 errors, 192/192 priced; open MTM +333 -> +304 roughly flat; arb exits near-flat.
❌ Went wrong: realized -56 (vs -6 last run; all-time -1,948 -> -2,004); 0 gap entries despite 37 gaps >=0.04 (RI Senate D +0.097); 10 conv positions held 44-47h unconverged.
💡 Improve (needs your OK): ~73k tied up in arb baskets at +0.010/set, so gaps go unentered -> smaller arb sizing; review MAX_HOLD_HOURS/EXIT_BAND (47h held); arb timeout losses grew, ARB_MIN_PROFIT still too early to tell.
🔎 Opportunities: RI Senate D +0.097 / R +0.090 / RI Gov +0.086 gaps recur every run (cash-limited); RI Gov arb +0.060, Nebraska Senate arb +0.055 near-miss; Hawaii Gov YES basket Σasks<1 by 0.035 (third-party risk); 45 unmapped markets.

## 2026-10-25T13:36Z run
LIVE · health OK (0 SIG errors, kalshi 3 failures/429) · P&L run -231 / all-time -2,235 · open MTM +245
Trades: ~414 fills (0 gap trades, ~60 arb baskets/timeouts) · best: Oregon Gov D leg timeout +7 · worst: Idaho Gov R leg timeout -20, Oregon Gov R leg -14
✅ Went well: 439 cycles, 0 SIG errors, 192/192 priced; open MTM steady +245 (account unrealized +700).
❌ Went wrong: realized -231 (vs -56; all-time -2,004 -> -2,235), 59 losing arb-timeout exits; 0 gap entries despite 30 gaps >=0.04 (RI Senate D +0.097); 10 conv positions held 46-49h.
💡 Improve (needs your OK): arb baskets at +0.010/set are churned and timed out at a loss (losses 4 runs running: -16,+2,-6,-56,-231) -> raise ARB_MIN_PROFIT or shorten arb hold/ cut arb sizing; ~73k locked blocks RI gap trades.
🔎 Opportunities: RI Senate D +0.097 / R +0.090 / RI Gov +0.086 gaps recur every run (cash-limited); RI Gov arb +0.060, Nebraska Senate +0.045 near-miss; Hawaii Gov YES basket Σasks<1 by 0.035 (third-party risk); 45 unmapped markets.

## 2026-10-25T15:50Z run
(note: this run started 13:56Z on the pre-14:09Z config, i.e. ARB_MIN_PROFIT 0.01; the owner's 0.02 applies from the next run)
LIVE · health OK (0 SIG errors, kalshi 4 failures/429) · P&L run -34 / all-time -2,261 · open MTM +286
Trades: 242 fills (0 gap trades, ~25 arb baskets; Delaware Sen timeout unwinds -18) · best: arb baskets ~0 · worst: Delaware Sen R leg timeouts (-12)
✅ Went well: 451 cycles, 0 errors, 192/192 priced; open MTM +286; realized loss narrowed to -34 (vs -56 last run).
❌ Went wrong: 0 gap entries despite 31 gaps >=0.04 (RI Senate D +0.092); 10 conv positions held 48-51h unconverged; all-time -2,261 (-515 today).
💡 Improve (needs your OK): ~73k tied up in 27 arb baskets at +0.010/set starves gap trades -> smaller arb sizing; review MAX_HOLD_HOURS/EXIT_BAND (51h held); Delaware arb timeouts keep losing, ARB_MIN_PROFIT too early to tell.
🔎 Opportunities: RI Senate D +0.092 / RI Gov R +0.086 / RI Senate R +0.081 gaps recur every run (cash-limited); RI Gov arb +0.065, Montana/Nebraska Senate +0.040 near-miss; Hawaii Gov YES basket Σasks<1 by 0.035 (third-party risk); 45 unmapped markets.

## 2026-10-25T17:56Z run
LIVE · health OK (0 SIG errors, kalshi 13 failures/429) · P&L run -91 / all-time -2,352 · open MTM +158
Trades: 64 fills (0 gap trades, ~10 arb baskets at the new ≥0.02 threshold; timeout unwinds Nebraska Sen -13, Oklahoma Gov -15) · best: arb baskets ~0 · worst: Oklahoma Gov R leg timeout (-10)
✅ Went well: 421 cycles, 0 SIG errors, 192/192 priced; fills fell 242 -> 64 with ARB_MIN_PROFIT 0.02 (less churn); account unrealized +625.
❌ Went wrong: realized -91 (vs -34), all-time -2,352 (-606 today), from timeouts of older +0.010 baskets (Nebraska/Oklahoma); 0 gap entries despite 30 gaps >=0.04 (RI Senate D +0.097); 10 conv positions held 50-53h; open MTM +286 -> +158.
💡 Improve (needs your OK): ~72k still locked in 25 arb baskets (many 2000-set, cost 0.99) blocks RI gap trades -> cap arb sizing; review MAX_HOLD_HOURS/EXIT_BAND (53h held); ARB_MIN_PROFIT 0.02 only one run, too early to tell.
🔎 Opportunities: RI Senate D +0.097 / R +0.090 / RI Gov +0.086 gaps recur every run (cash-limited); RI Gov arb +0.060, Nebraska Sen +0.045 near-miss; Hawaii Gov YES basket Σasks<1 by 0.035 (third-party risk); 45 unmapped markets.
## 2026-10-25T19:40Z run
LIVE · health OK (0 SIG errors, kalshi 14 failures/429) · P&L run -35 / all-time -2,295 · open MTM +201
Trades: ~arb baskets only, 0 gap trades (ARB_MIN_PROFIT 0.02 now active, e.g. Oklahoma Sen @ +0.020/set) · best: n/a · worst: arb timeout unwinds
✅ Went well: 439 cycles, 0 SIG errors, 192/192 priced; arb entries now at +0.020/set.
❌ Went wrong: realized -35 (-550 today); 0 gap entries despite 29 gaps >=0.04 (RI Senate D +0.092); 10 conv positions held up to 55h; Kalshi 429s rose to 14.
💡 Improve (needs your OK): ~73k locked in arb baskets starves RI gap trades -> smaller arb sizing; review MAX_HOLD_HOURS/EXIT_BAND (55h held); too early to judge ARB_MIN_PROFIT 0.02 (1 run).
🔎 Opportunities: RI Senate D +0.092 / RI Gov R +0.086 / RI Senate R +0.081 gaps recur every run (cash-limited); RI Gov arb +0.060, Montana +0.055 near-miss; Hawaii Gov YES basket Σasks<1 by 0.035 (third-party risk); 45 unmapped markets.

## 2026-10-25T21:40Z run
LIVE · health OK (0 SIG errors, kalshi 3 failures/429) · P&L run +2 / all-time -2,293 · open MTM +249
Trades: 14 fills (0 gap trades, 1 new arb basket Tennessee Gov; 6 arb exits) · best: MT-01 take-profit +4 net · worst: MT-01 timeout -1 net
✅ Went well: 454 cycles, 0 SIG errors, 192/192 priced; realized flat (+2 vs -35 last run) as old +0.010 baskets clear; Kalshi failures fell 14 -> 3.
❌ Went wrong: 0 gap entries despite 32 gaps >=0.04 (RI Senate D +0.092); 10 conv positions held 54-57h unconverged; all-time -2,293 (-548 today).
💡 Improve (needs your OK): ~72k still locked in 20 arb baskets (many 2000-set) starves RI gap trades -> cap arb sizing; review MAX_HOLD_HOURS/EXIT_BAND (57h held). ARB_MIN_PROFIT 0.02 now looks better (14 fills vs 62) but 2 runs is too early to tell.
🔎 Opportunities: RI Senate D +0.092 / RI Gov R +0.086 / RI Senate R +0.081 gaps recur every run (cash-limited); RI Gov arb +0.060, Montana +0.050, Nebraska +0.045 near-miss; Hawaii Gov YES basket Σasks<1 by 0.030 (third-party risk); 45 unmapped markets.

## 2026-10-25T23:40Z run
LIVE · health OK (0 SIG errors, kalshi 13 failures/429) · P&L run -31 / all-time -2,324 · open MTM +308
Trades: 10 fills (0 gap trades, 1 new arb basket Delaware Sen; 4 arb timeout exits) · best: VA-05 D leg +10 · worst: SC Gov R leg / VA-05 R leg timeouts (-20 each)
✅ Went well: 429 cycles, 0 SIG errors, 192/192 priced; account unrealized +687; only 1 new arb entry (churn low at ARB_MIN_PROFIT 0.02).
❌ Went wrong: realized -31 (-579 today) from 2000-set arb timeouts (SC Gov, VA-05 ~-30 net); 0 gap entries despite 29 gaps >=0.04; 10 conv positions held 56-59h; Kalshi 429s 13.
💡 Improve (needs your OK): ~68k locked in 17 arb baskets (many 2000-set) starves RI gap trades -> cap arb sizing; review MAX_HOLD_HOURS/EXIT_BAND (59h held); arb timeouts on 2000-set baskets cost more than the +0.02 edge.
🔎 Opportunities: RI Senate D +0.092 / RI Gov R +0.086 / RI Senate R +0.080 gaps recur every run (cash-limited); RI Gov arb +0.065, Montana +0.050 near-miss; Hawaii Gov YES basket Σasks<1 by 0.030 (third-party risk); 45 unmapped markets.

## 2026-10-26T01:40Z run
LIVE · health OK (0 SIG errors, kalshi 6 failures/429) · P&L run -220 / all-time -2,544 · open MTM +540
Trades: 242 fills (0 gap trades, 0 new arb baskets; arb timeout unwinds only) · best: arb legs ~0 · worst: SC Senate R leg timeout (-13); realized -220 mostly from unwinding old baskets
✅ Went well: 461 cycles, 0 SIG errors, 192/192 priced; arb baskets held cut 17 -> 12 (locked cash freed, holdings 68k -> 54k); open MTM +540 (was +308).
❌ Went wrong: realized -220 (vs -31), all-time -2,544 (-220 today), from arb timeout unwinds of 2000-set baskets; 0 gap entries despite 26 gaps >=0.04 (RI Senate D +0.092); Tennessee Gov unwound in ~100 slices of 1-20 sets (thin depth).
💡 Improve (needs your OK): arb timeouts (MAX_HOLD) cost more than the +0.02 edge on large baskets -> cap arb size / shorten hold or require depth; cash now freed, so watch whether RI gap trades finally fire; review MAX_HOLD_HOURS/EXIT_BAND (61h held).
🔎 Opportunities: RI Senate D +0.092 / RI Gov R +0.086 / RI Senate R +0.080 gaps recur every run; RI Gov arb +0.060, Nebraska +0.050, Montana +0.045 near-miss; YES baskets Σasks<1: MN-05 +0.030, Hawaii Gov +0.030 (third-party risk); 45 unmapped markets.

## 2026-10-26T03:40Z run
LIVE · health OK (0 SIG errors, 0 consecutive errors) · P&L run -28 / all-time -2,573 · open MTM +678
Trades: 103 in last 2h (arb baskets only visible, mostly small Nebraska Sen churn/timeouts) · best: n/a · worst: arb timeouts ~-0 each
✅ Went well: 472 cycles, 0 SIG errors, 192/192 priced, 0 Kalshi failures; realized only -28 (vs -220 last run) as old 2000-set baskets cleared; open MTM +678 (was +540).
❌ Went wrong: all-time -2,573 (-248 today); RI Senate D/Gov R/Senate R gaps (+0.09) still held 63h unconverged; Nebraska Sen arb re-entered/timed out repeatedly in 50-set slices.
💡 Improve (needs your OK): review MAX_HOLD_HOURS/EXIT_BAND (63h held, RI fair 0.99 vs mark 0.89-0.90); cap arb size/churn on thin books (Nebraska) — 3 runs of timeout losses exceed +0.02 edge.
🔎 Opportunities: RI gaps +0.092/+0.086/+0.080 persist every run; RI Gov arb +0.060, Montana +0.050, Nebraska +0.045 near-miss; YES baskets Σasks<1: Hawaii Gov +0.030, Nebraska Gov +0.025 (third-party risk); 45 unmapped markets.

## 2026-10-26T05:40Z run
LIVE · health OK (0 SIG errors, kalshi 4 failures) · P&L run -27 / all-time -2,600 · open MTM +628
Trades: ~25 in 2h (0 gap trades, new arb baskets PA-10, Colorado Sen; Montana/Nebraska timeout re-churn; CA Gov, Alaska Gov take-profit) · best: CA Gov D take-profit +7 · worst: Montana Sen R timeout -14
✅ Went well: 469 cycles, 0 SIG errors, 192/192 priced; realized small (-27 vs -220 last run); CA Gov basket took profit.
❌ Went wrong: all-time -2,600 (-276 today); 0 gap entries despite 35 gaps >=0.04 (RI +0.087), RI/MS/HI positions held 63-65h unconverged; Nebraska/Montana baskets topped up then immediately timed out (opened_at keeps old time) ~-30 net.
💡 Improve (needs your OK): topping up an aged arb basket inherits its old opened_at so new sets are sold at timeout immediately - reset hold clock or skip re-entry on aged baskets; review MAX_HOLD_HOURS/EXIT_BAND (65h held, RI fair 0.99 vs mark 0.90).
🔎 Opportunities: RI Gov/Sen gaps +0.087/+0.086/+0.085 recur every run; RI Gov arb +0.060, Montana +0.040, Nebraska +0.035 near-miss; YES baskets Σasks<1: Hawaii Gov +0.045, Oklahoma Gov +0.025 (third-party risk); 45 unmapped markets.

## 2026-10-26T07:40Z run
LIVE · health OK (0 SIG errors, kalshi 2 failures) · P&L run -56 / all-time -2,629 · open MTM +532
Trades: 123 in last 2h (0 gap trades, arb baskets only: Delaware, Michigan, TX-15; Oklahoma timeout unwind) · best: Delaware take-profit ~0 · worst: Oklahoma Sen timeout -11 net
✅ Went well: 462 cycles, 0 SIG errors, 192/192 priced; account unrealized +790; 12 arb baskets held, all sell-now within ~0.01-0.02 of cost.
❌ Went wrong: realized -56 (-305 today), all-time -2,629; 0 gap entries despite 38 gaps >=0.04; 10 conv positions held 64-67h unconverged (RI Gov/Senate ~6-7k shares each).
💡 Improve (needs your OK): review MAX_HOLD_HOURS/EXIT_BAND — RI fair 0.985-0.997 vs mark 0.895-0.905 for 67h, capital is locked; arb timeouts on thin books (Oklahoma -11) still cost about the +0.02 edge; 4 runs of evidence.
🔎 Opportunities: RI Gov/Senate gaps +0.087/+0.086/+0.085 recur every run (already held, cash-limited); RI Gov arb +0.060, Montana +0.040, Alaska +0.035 near-miss; 45 unmapped markets.

## 2026-10-26T09:38Z run
LIVE · health OK (0 SIG errors, kalshi 2 failures) · P&L run +3 / all-time -2,626 · open MTM +433
Trades: 22 fills (0 gap trades, arb baskets only: NH-01, SC Sen, MN-02; Delaware/NC take-profits) · best: Delaware D take-profit +10 · worst: Delaware R leg -7
✅ Went well: 442 cycles, 0 SIG errors, 192/192 priced; realized +3 (best of last 6 runs, no timeout losses); account unrealized +731.
❌ Went wrong: all-time -2,626; 0 gap entries despite 35 gaps >=0.04; 10 positions held 66-69h unconverged (RI trio ~6.6-7k shares, fair 0.985-0.995 vs mark 0.895-0.905); NC Sen R sell 0/55 unfilled.
💡 Improve (needs your OK): review MAX_HOLD_HOURS/EXIT_BAND - RI gaps +0.085 unconverged ~69h, capital locked (5 runs of evidence); aged-basket top-ups inherit old opened_at (arb.py hold clock) - consider resetting it.
🔎 Opportunities: RI Gov/Senate gaps +0.087/+0.086/+0.085 recur every run; RI Gov arb +0.055, Montana +0.035, Nebraska +0.035 near-miss; YES baskets Σasks<1: MN-05 +0.025, Hawaii Gov +0.025 (third-party risk); 45 unmapped markets.

## 2026-10-26T11:36Z run
LIVE · health OK (0 SIG errors, kalshi 2 failures) · P&L run +4 / all-time -2,622 · open MTM +350
Trades: 22 fills (0 gap trades, arb baskets only: Delaware, Tennessee Gov, MN-01, WI-03, ME-02; VA-07/TX-15 take-profits) · best: VA-07 take-profit +5 · worst: VA-07 D leg -4
✅ Went well: 460 cycles, 0 SIG errors, 192/192 priced; realized +4 (2nd positive run in a row, no timeout losses); account unrealized +567.
❌ Went wrong: all-time -2,622; 0 gap entries despite 36 gaps >=0.04; 10 positions held 68-71h unconverged (RI trio ~6.6-7k shares, fair 0.985-0.995 vs mark 0.895-0.905).
💡 Improve (needs your OK): review MAX_HOLD_HOURS/EXIT_BAND - RI gaps +0.085 unconverged ~71h, capital locked (6 runs of evidence); aged-basket top-ups inherit old opened_at.
🔎 Opportunities: RI Gov/Senate gaps +0.086/+0.085/+0.084 recur every run; arb near-misses RI Gov +0.065, Nebraska +0.065, Montana +0.040; YES baskets Σasks<1: MN-05 +0.030, Hawaii Gov +0.030 (third-party risk); 45 unmapped markets.

## 2026-10-26T13:40Z run
LIVE · health OK (0 SIG errors, kalshi 3 failures) · P&L run +251 / all-time -2,371 · open MTM -354
Trades: 77 in last 2h (arb baskets mostly; conv timeouts incl. Hawaii Gov D +15; Vermont/NC arb timeouts) · best: Hawaii Gov D timeout +15 · worst: Vermont Gov R timeout -7
✅ Went well: 457 cycles, 0 SIG errors, 192/192 priced; realized +251 (best run today, old 66-71h conv positions finally cleared); all-time -2,622 → -2,371.
❌ Went wrong: open MTM fell +350 → -354 (RI Gov/Senate/Hawaii positions re-entered at ~0.90, marks 0.895-0.90); Vermont -7 and NC -6 arb timeouts; TN/VA/MS Senate still held 70h.
💡 Improve (needs your OK): conv timeouts realized the gains but fair 0.985 vs mark 0.90 gap never closed in 70h - review MAX_HOLD_HOURS/EXIT_BAND (7 runs of evidence); aged arb baskets inherit old opened_at.
🔎 Opportunities: RI Gov/Senate gaps +0.089/+0.086/+0.080 recur every run; arb near-misses RI Gov +0.070, Nebraska +0.045, Montana +0.040; YES baskets Σasks<1: Hawaii Gov +0.035, MN-05 +0.030 (third-party risk); 45 unmapped markets.

## 2026-10-26T15:40Z run
LIVE · health OK (1 transient truncated-JSON cycle error at 14:15, recovered; kalshi 3 failures) · P&L run -276 / all-time -2,648 · open MTM -234
Trades: 37 in last 2h (conv gap trades ~14 incl. 2 timeouts, arb baskets: US House, Oklahoma Sen, NH-01, VA-01) · best: NH-01 arb take-profit +5 · worst: Virginia Sen R timeout -92 / Tennessee Sen D timeout -83
✅ Went well: 455 cycles, 192/192 priced, 0 SIG errors; 16 arb baskets held, sell-now within ~0.01 of cost.
❌ Went wrong: realized -276 from two 70h conv timeouts (VA Sen -92, TN Sen -83 plus ~-100 other); all-time -2,648.
💡 Improve (needs your OK): review MAX_HOLD_HOURS/EXIT_BAND - conv gaps (fair ~0.96-0.98 vs mark ~0.90) not converging over 70h, timeouts realize losses (8 runs of evidence); aged-basket top-ups inherit old opened_at.
🔎 Opportunities: RI Senate/Gov gaps +0.086/+0.084 recur every run (held, cash-limited); arb near-misses Nebraska +0.045, RI Gov +0.060, Montana +0.040; YES baskets Σasks<1: Hawaii Gov +0.035 (third-party risk); 45 unmapped markets.

## 2026-10-26T18:07Z run
LIVE · health OK (0 cycle errors, 1 transient SSL timeout; kalshi 3 failures) · P&L run +0 / all-time -2,648 · open MTM -23
Trades: 4 fills (0 gap trades, 2 arb baskets: Texas Gov, Idaho Gov) · best: n/a · worst: n/a
✅ Went well: 452 cycles, 192/192 priced, 0 timeout losses; open MTM -234 → -23, account unrealized +54; 18 arb baskets held, sell-now within ~0.005 of cost.
❌ Went wrong: 0 gap entries despite 28 gaps ≥0.04 (cash-limited; ~52.7k locked in holdings); RI Senate pair (~6.6k sh) held 5h with gap +0.085 unconverged.
💡 Improve (needs your OK): review MAX_HOLD_HOURS/EXIT_BAND — gaps (fair ~0.985 vs mark ~0.90) persist for 70h and timeouts realized -92/-83 last run (9 runs of evidence); aged arb top-ups inherit old opened_at.
🔎 Opportunities: RI Gov/Senate gaps +0.089/+0.081 recur every run; arb near-misses Nebraska/Montana/RI Gov +0.045/+0.045/+0.045 (below 0.02 trade threshold only on fill cost); YES baskets Σasks<1: Hawaii Gov +0.035, MN-05 +0.030 (third-party risk); 45 unmapped markets.

## 2026-10-26T19:40Z run
LIVE · health OK (0 SIG errors, kalshi 3 failures) · P&L run -10 / all-time -2,658 · open MTM +27
Trades: 34 in last 2h (0 gap trades, arb baskets only: CO-04, California Gov, Kansas, MT-01, Oklahoma, Colorado; Texas Gov take-profits) · best: Texas Gov take-profits ~+1 each · worst: Michigan Sen timeout -3
✅ Went well: 459 cycles, 0 SIG errors, 192/192 priced; realized -10 vs -276 last run (no conv timeouts); open MTM -234 → +27; 19 arb baskets held, sell-now within ~0.01 of cost.
❌ Went wrong: all-time -2,658; 0 gap entries despite 28 gaps >=0.04; RI/MS/OK/ME positions held 7h+ unconverged (RI fair 0.985 vs mark 0.90).
💡 Improve (needs your OK): review MAX_HOLD_HOURS/EXIT_BAND - RI gaps +0.08 persist (9 runs of evidence), earlier timeouts realized losses (VA -92, TN -83).
🔎 Opportunities: RI Gov/Senate gaps +0.084/+0.081/+0.080 recur every run (held, cash-limited); arb near-misses Montana +0.050, Nebraska +0.045, RI Gov +0.040; YES baskets Σasks<1: Hawaii Gov +0.035 (third-party risk); 45 unmapped markets.

## 2026-10-26T22:58Z run
LIVE · health OK (1 transient SIG disconnect; kalshi 2 failures) · P&L run -12 / all-time -2,662 · open MTM -34
Trades: ~56 in 2h (0 gap trades, arb baskets: Alaska Sen, PA-10, Maine Sen, Michigan Sen…) · best: n/a · worst: n/a
✅ Went well: 267 cycles over final 60 min, 192/192 priced, 0 cycle errors after restart; open MTM only -34; account unrealized +135.
❌ Went wrong: first 100-min run died at 20:07 (readonly DB) because I merged git into state/ mid-run — process error, not code; ~1h50 of trading lost. 0 gap entries despite 31 gaps ≥0.04 (cash-limited, 12 positions ~10h unconverged).
💡 Improve (needs your OK): review MAX_HOLD_HOURS/EXIT_BAND — RI Senate ~6.6k sh held 10h, fair 0.985 vs mark 0.90 (10 runs of evidence).
🔎 Opportunities: RI Senate/Gov gaps +0.086/+0.089 recur every run; arb near-misses RI Gov +0.060, Nebraska +0.055, Montana +0.050; YES baskets Σasks<1: MN-05/Hawaii Gov +0.025 (third-party risk); 45 unmapped markets.

## 2026-10-26T23:40Z run
LIVE · health DEGRADED (container restarted 23:26, run cut at ~90/100 min; overlapped with a duplicate session's run, so the report file was clobbered) · P&L last 2h -9 / all-time -2,658 · open MTM -69
Trades: ~62 fills in 2h (0 gap trades; arb baskets: AZ-01, Colorado Sen churn, Maine Sen take-profit) · best: Maine Sen take-profit +1 · worst: Colorado Sen R timeout -4
✅ Went well: 0 SIG errors; 12 conv positions intact, open MTM -69; account unrealized +127.
❌ Went wrong: two sessions ran the bot at once (duplicate orders, 344 unfilled sell attempts, e.g. Tennessee Gov sell 0/218 repeating; MN-01/TN Gov baskets pending); Colorado Senate 1–39 share baskets bought then timed out repeatedly (~0 P&L churn).
💡 Improve (needs your OK): review MAX_HOLD_HOURS/EXIT_BAND — RI/MS/OK gaps (fair ~0.985 vs mark ~0.90) unconverged 11h (11 runs of evidence); consider a re-entry cooldown after an arb timeout (Colorado churn).
🔎 Opportunities: RI Senate/Gov gaps ~+0.085 recur every run; arb near-misses Nebraska/Montana/RI Gov; 45 unmapped markets.
🔧 Fixed: nothing in code.

## 2026-10-27T00:57Z run
LIVE · health DEGRADED (container restarted ~00:26, bot died after ~30 of 100 min; no fresh report written) · P&L run ~0 / all-time ≈-2,660 · open MTM n/a
Trades: ~15 order batches (0 gap trades; arb baskets e.g. Alaska Sen round-trip) · best: n/a · worst: n/a
✅ Went well: 0 SIG errors in the 30 min traded; conv positions intact.
❌ Went wrong: infra, not code — container restart killed the run; Kalshi 429s on every batch refresh.
💡 Improve (needs your OK): Kalshi 429s repeat each run — slower Kalshi polling would stabilise reference prices; MAX_HOLD_HOURS/EXIT_BAND review still open (RI gaps ~+0.085, 12 runs).
🔎 Opportunities: RI Senate/Gov gaps ~+0.085 recur (cash-limited); 45 unmapped markets.
🔧 Fixed: nothing in code.

## 2026-10-27T03:41Z run
LIVE · health OK (0 SIG errors; kalshi 14 failures, all 429s) · P&L run -7 / all-time -3,023 · open MTM -599
Trades: 46 in 2h (0 gap trades; arb baskets: Tennessee Gov, U.S. House; timeouts Oklahoma Sen, VA-01) · best: VA-01 leg +3 · worst: VA-01 R timeout -8
✅ Went well: full 100 min, 416 cycles, 0 SIG errors, 191/192 priced; realized only -7; 21 arb baskets held, sell-now within ~0.01-0.03 of cost.
❌ Went wrong: open MTM -69 → -599 and all-time -2,658 → -3,023 (12 conv positions marked down ~0.01-0.02, held 12-15h); 0 gap entries despite 45 gaps ≥0.04 (cash-limited).
💡 Improve (needs your OK): MAX_HOLD_HOURS/EXIT_BAND review (RI/MS/OK gaps ~+0.085 unconverged 15h, 13 runs of evidence); slower Kalshi polling (14 429s this run).
🔎 Opportunities: RI Gov/Senate gaps +0.09 recur every run; arb near-misses Montana +0.050, CO-04 +0.045, RI Gov +0.045; YES baskets Σasks<1: Hawaii Gov +0.045, Alaska Gov +0.035 (third-party risk); 45 unmapped markets.

## 2026-10-27T05:37Z run
LIVE · health OK (0 SIG errors; kalshi 12 failures, 429s) · P&L run +18 / all-time -3,005 · open MTM -91
Trades: 110 in 2h (0 gap trades; arb baskets CO-04, TX-15, California Gov, Idaho Gov take-profits) · best: California Gov Dem leg +5 · worst: California Gov Rep leg -3
✅ Went well: full 100 min, 434 cycles, 0 SIG errors, 191/192 priced; realized +18 vs -7 last run; open MTM -599 → -91.
❌ Went wrong: all-time -3,005; 12 conv positions (RI/MS/OK/ME/HI/TN/VA/WY) held 14-17h unconverged, fair 0.03-0.08 above mark; Kalshi 429s (12).
💡 Improve (needs your OK): MAX_HOLD_HOURS/EXIT_BAND review (RI Senate fair 0.986 vs mark 0.895 after 17h, 14 runs of evidence); slower Kalshi polling.
🔎 Opportunities: RI/MS gaps ~+0.08-0.09 recur every run (cash-limited); 45 unmapped markets; see report for Σasks<1 YES baskets (third-party risk).
## 2026-10-27T07:57Z run
LIVE · health OK (0 SIG errors, 439 cycles, kalshi 10 failures/429s) · P&L run +9 / all-time -3,014 · open MTM -174
Trades: 42 in 2h (0 gap trades; arb baskets: VA-01, Nebraska Gov, Iowa Sen ×3; take-profits NC Sen, SC Gov) · best: arb take-profits +1 · worst: none
✅ Went well: full 100 min, 0 errors; open MTM improved -599 → -174; realized +9.
❌ Went wrong: 12 conv positions still unconverged after 16-19h (RI Sen fair 0.986 vs mark 0.895); 0 gap entries despite 40 gaps ≥0.04 (cash-limited).
💡 Improve (needs your OK): MAX_HOLD_HOURS/EXIT_BAND review (14 runs of evidence on RI/MS gaps); slower Kalshi polling (429s).
🔎 Opportunities: RI Sen/Gov gaps +0.085 recur every run; arb near-misses RI Gov +0.055, Nebraska/Montana Sen +0.045; YES baskets Hawaii Gov +0.035, MN-05 +0.030 (third-party risk); 45 unmapped markets.

## 2026-10-27T09:39Z run
LIVE · health OK (1 SIG API error, 449 cycles, kalshi 5 failures) · P&L run +1 / all-time -3,013 · open MTM -219
Trades: 16 in 2h (0 gap trades; arb baskets: Oklahoma Sen, FL-16; take-profits Georgia Gov, VA-01, Nebraska Gov; MT-01 timeout) · best: Georgia Gov +9/-7 net +2 · worst: MT-01 R timeout -5
✅ Went well: full 100 min, 449 cycles, 191/192 priced; Kalshi failures down to 5 (from 10-14).
❌ Went wrong: 12 conv positions unconverged 18-21h (RI Sen fair 0.986 vs mark 0.895); 0 gap entries despite 35 gaps ≥0.04 (cash-limited); realized only +1.
💡 Improve (needs your OK): MAX_HOLD_HOURS/EXIT_BAND review (15 runs of evidence on RI/MS gaps).
🔎 Opportunities: RI Sen/Gov gaps +0.085 recur every run; arb near-misses RI Gov +0.050, Montana/Nebraska Sen +0.040; YES baskets Hawaii Gov +0.045, MN-05 +0.030 (third-party risk); 45 unmapped markets.

## 2026-10-27T11:40Z run
LIVE · health OK (0 SIG errors, 455 cycles, kalshi 5 failures/429s) · P&L run -35 / all-time -3,048 · open MTM -100
Trades: 60 fills in 2h (0 gap trades; arb baskets 29 orders: Nebraska Gov, MT-01, WI-03, Georgia Gov) · best: n/a · worst: Nebraska Sen Independent timeout -20
✅ Went well: full 100 min, 0 SIG API errors, 191/192 priced; open MTM -219 → -100; Kalshi failures stable at 5.
❌ Went wrong: 10 arb timeout exits cost ~-60 (PA-10 -8, Michigan Sen -7, AZ-01 -11, Nebraska Sen -25) vs +~25 from take-profits; 12 conv positions still unconverged 20-23h (RI Sen fair 0.986 vs mark 0.895).
💡 Improve (needs your OK): arb baskets held to timeout lose the ~0.02-0.03 spread; with ARB_MIN_PROFIT 0.02 vs sell-now 0.97-0.98, consider raising ARB_MIN_PROFIT or shortening hold; also MAX_HOLD_HOURS/EXIT_BAND review (16 runs of RI/MS gap evidence).
🔎 Opportunities: RI Sen/Gov gaps +0.085 recur every run (cash-limited); arb near-misses RI Gov +0.050, Montana Sen +0.045; YES baskets Hawaii Gov +0.045, MN-05 +0.030 (third-party risk); 45 unmapped markets.
🔧 Fixed: nothing (no bugs found; losses were rule-driven).

## 2026-10-27T13:40Z run
LIVE · health OK (0 SIG errors, 423 cycles, kalshi 4 failures/429s) · P&L run -1 / all-time -3,050 · open MTM -103
Trades: 55 fills / 26 orders (0 gap trades; arb baskets PA-07, Nebraska Gov, Idaho Gov, Vermont Gov, FL Gov; take-profits U.S. House, FL-16) · best: n/a · worst: Montana Sen Independent timeout -10
✅ Went well: full 100 min, 0 SIG errors, 191/192 priced; realized -1 vs -35 last run; open MTM flat at -103.
❌ Went wrong: 2 Montana Sen arb timeouts -15; 12 conv positions still unconverged 22-25h (RI Sen fair 0.986 vs mark 0.895); 0 gap entries despite 35 gaps ≥0.04 (cash-limited).
💡 Improve (needs your OK): MAX_HOLD_HOURS/EXIT_BAND review (17 runs of RI/MS gap evidence); arb timeouts lose the spread, consider ARB_MIN_PROFIT/hold review.
🔎 Opportunities: RI Sen/Gov gaps +0.09 recur every run; arb near-misses RI Gov +0.075, Montana Sen +0.040; YES baskets Hawaii Gov +0.035 (third-party risk); 45 unmapped markets.
🔧 Fixed: nothing (no bugs found).

## 2026-10-27T15:39Z run
LIVE · health OK (0 SIG errors, 434 cycles, kalshi 6 failures/429s) · P&L run +1 / all-time -3,049 · open MTM +54
Trades: 24 fills / 12 orders (0 gap trades; arb baskets PA-01, Georgia Gov; 6 take-profits Vermont/PA-07/Kansas/FL Gov) · best: PA-07 & Kansas Sen take-profits +3 · worst: Tennessee Gov timeout -5
✅ Went well: full 100 min, 0 SIG errors, 191/192 priced; open MTM -103 → +54; 6 arb take-profits ~net +6.
❌ Went wrong: 12 conv positions unconverged 24-27h (RI Sen fair 0.986 vs mark 0.90); 0 gap entries despite 24 gaps ≥0.04 (cash-limited); 1 arb timeout -5.
💡 Improve (needs your OK): MAX_HOLD_HOURS/EXIT_BAND review (18 runs of RI/MS gap evidence); arb timeouts lose the spread, consider ARB_MIN_PROFIT/hold review.
🔎 Opportunities: RI Gov/Sen gaps +0.08-0.10 recur every run; arb near-miss RI Gov +0.070, Montana/Nebraska Sen +0.030; YES baskets NH Sen/MN-05/Hawaii Gov +0.025 (third-party risk); 45 unmapped markets.
🔧 Fixed: nothing (no bugs found).

## 2026-10-27T17:38Z run
LIVE · health OK (0 SIG errors, 384 cycles, kalshi 5 failures/429s, 4 SIG read timeouts retried) · P&L run +10 / all-time -3,039 · open MTM -398
Trades: 24 fills / 20 orders (15 gap trades "conv" at 15:58-16:01 + 1 at 17:05; arb baskets Maine Sen, Florida Gov; take-profits Michigan Sen, Georgia Gov) · best: Michigan Sen take-profit +10 · worst: Michigan Sen R leg -3
✅ Went well: first gap entries in many runs (15 conv buys, edges 0.041-0.052, NY Gov, LA/GA/MA Sen, Hawaii Gov); realized +10; 0 SIG errors.
❌ Went wrong: open MTM +54 → -398 as new conv positions sit ~0.005-0.015 under cost (spread) and 12 older conv still unconverged 26-29h (RI Sen fair 0.986 vs mark 0.90).
💡 Improve (needs your OK): MAX_HOLD_HOURS/EXIT_BAND review (19 runs of RI/MS gap evidence); conv entries at the ask pay the spread immediately, check whether MIN_EDGE 0.04 leaves enough margin.
🔎 Opportunities: RI Gov/Sen gaps +0.08-0.095 recur every run; arb near-miss RI Gov +0.070, Maine/Montana Sen +0.035; YES basket Hawaii Gov +0.040 (third-party risk); 45 unmapped markets.
🔧 Fixed: nothing (no bugs found).

## 2026-10-27T19:46Z run
LIVE · health OK (2 SIG errors, 381 cycles, kalshi 9 failures/429s) · P&L run +0 / all-time -3,039 · open MTM -198
Trades: 0 fills (0 gap trades, 0 arb baskets) · best: n/a · worst: n/a
✅ Went well: full 100 min, 191/192 priced; open MTM improved -398 → -198 with no trading.
❌ Went wrong: 0 entries despite 22 gaps ≥0.04 and 13 arb races ≥0.02 (cash-limited); 12 older conv positions still unconverged 27-31h (RI Sen fair 0.986 vs mark 0.90).
💡 Improve (needs your OK): MAX_HOLD_HOURS/EXIT_BAND review (20 runs of RI/MS gap evidence); capital is tied in stuck conv positions, blocking new gap/arb entries.
🔎 Opportunities: RI Gov/Sen gaps +0.08 recur every run; arb near-miss RI Gov +0.070, Montana Sen +0.045; YES baskets Hawaii Gov +0.030 (third-party risk); 45 unmapped markets.
🔧 Fixed: nothing (no bugs found; pytest collection errors in this sandbox left untouched).

## 2026-10-27T21:36Z run
LIVE · health OK (2 SIG errors, 387 cycles, kalshi 8 failures/429s) · P&L run +0 / all-time -3,039 · open MTM -190
Trades: 1 fill (1 gap trade: Michigan Sen R NO, 1 share; 0 arb baskets) · best: n/a · worst: n/a
✅ Went well: full 100 min, 191/192 priced; 0 Traceback; MTM steady (-198 → -190) with nothing churned.
❌ Went wrong: only 1 fill despite 24 gaps ≥0.04 and 10 arb races ≥0.02 (cash-limited); 12 older conv positions unconverged 30-33h (RI Sen fair 0.986 vs mark 0.90).
💡 Improve (needs your OK): MAX_HOLD_HOURS/EXIT_BAND review (21 runs of RI/MS gap evidence); capital tied in stuck conv positions blocks new entries.
🔎 Opportunities: RI Gov/Sen gaps +0.08 recur every run; arb near-miss RI Gov +0.055, Montana Sen +0.045; YES baskets KY-04/Hawaii Gov +0.030 (third-party risk); 45 unmapped markets.
🔧 Fixed: nothing (no bugs found).

## 2026-10-27T23:00Z run
LIVE · health DEGRADED (container restarted twice, bot killed at ~40 min and ~20 min; no final report written) · P&L run n/a / all-time -3,039 (last report) · open MTM n/a
Trades: ~4 arb baskets in the partial runs (PA-01 and MT-01 sells; FL-13 and FL-16 NO buys, all filled fully) · best: n/a · worst: n/a
✅ Went well: all orders filled in full (4/4, 32/32, 35/35, 1/1); 0 tracebacks.
❌ Went wrong: sandbox restarts cut the run to ~60 of 100 trading minutes, so last_report.txt is stale (19:38 data); 429s from Kalshi again.
💡 Improve (needs your OK): MAX_HOLD_HOURS/EXIT_BAND review (conv positions stuck 27-31h); too early to tell on anything new.
🔎 Opportunities: RI Gov/Sen gaps and arb near-miss RI Gov recur every run (per last report); 45 unmapped markets.
🔧 Fixed: nothing (no bugs found; restarts were environmental).

## 2026-10-28T01:37Z run
LIVE · health OK (0 SIG errors, 399 cycles, kalshi 14 429s) · P&L run +5 / all-time -3,033 · open MTM -543
Trades: 8 fills (4 gap trades, 2 arb take-profit baskets: Maine Sen, Delaware Sen) · best: Maine/Delaware Sen arb sells +8 legs · worst: -5 legs on arb sells
✅ Went well: full 100 min, 0 tracebacks; 2 arb baskets closed for net +6; 191/192 priced.
❌ Went wrong: open MTM fell -190 → -543 (WA-03 Dem YES mark 0.83 vs 0.864 entry, ~-64; RI/NY marks drifting down); 12 conv positions still unconverged 34-37h.
💡 Improve (needs your OK): MAX_HOLD_HOURS/EXIT_BAND review (22 runs of RI/MS gap evidence); capital tied in stuck conv positions, 39 gaps ≥0.04 reached but only 4 filled.
🔎 Opportunities: RI Gov/Sen gaps +0.085-0.098 recur every run; arb near-miss RI Gov +0.055, Montana Sen +0.030; 45 unmapped markets.
🔧 Fixed: nothing (no bugs found).

## 2026-10-28T03:36Z run
LIVE · health OK (0 SIG errors, 396 cycles, kalshi 13 429s) · P&L run +3 / all-time -3,031 · open MTM -609
Trades: 21 fills (1 gap trade, 5 arb take-profit/entry rounds: Florida Gov x2, FL-13, Maine Sen, U.S. House) · best: Florida Gov arb sell +11 · worst: Florida Gov leg -6
✅ Went well: full 100 min, 0 tracebacks, 0 SIG errors; arb round-trips net +3 realized, all orders filled.
❌ Went wrong: open MTM -543 → -609 (RI Sen YES mark 0.88 vs 0.901 entry); 12 conv positions unconverged 36-39h; 41 gaps ≥0.04 but only 1 gap fill.
💡 Improve (needs your OK): MAX_HOLD_HOURS/EXIT_BAND review (23 runs of RI/MS gap evidence); capital tied in stuck conv positions starves new gap entries.
🔎 Opportunities: RI Gov/Sen gaps +0.085-0.098 recur every run; arb near-miss RI Gov +0.060, Montana/Nebraska Sen +0.030; YES baskets Hawaii Gov +0.030 (third-party risk); 45 unmapped markets.
🔧 Fixed: nothing (no bugs found).

## 2026-10-28T05:37Z run
LIVE · health OK (14 SIG read timeouts retried, 242 cycles, kalshi 11 429s) · P&L run +1 / all-time -3,029 · open MTM -711
Trades: 27 fills (1 gap trade, ~9 arb baskets/take-profit rounds) · best: Nebraska Gov arb take-profits (~+0 each) · worst: none realized
✅ Went well: full 100 min, 0 tracebacks, 0 stuck orders; realized +9 today, all arb orders filled.
❌ Went wrong: open MTM -609 → -711 (RI Sen YES mark 0.885 vs 0.901 entry); 39 gaps ≥0.04 reached but only 1 gap fill; 21 positions held up to 41h.
💡 Improve (needs your OK): MAX_HOLD_HOURS/EXIT_BAND review (24 runs of RI/MS gap evidence); stuck conv positions tie up capital and starve new gap entries.
🔎 Opportunities: RI Gov/Sen gaps +0.090-0.103 recur every run; arb near-miss RI Gov +0.055, Nebraska Sen +0.040, U.S. House +0.035; YES baskets MN-05 +0.030, Hawaii Gov +0.025 (risk: third-party win); 45 unmapped markets.
🔧 Fixed: nothing (no bugs found).

## 2026-10-28T07:37Z run
LIVE · health OK (283 cycles, 0 tracebacks, SIG read timeouts retried, kalshi 6 failures) · P&L run +0 / all-time -3,029 · open MTM -962
Trades: 0 fills (0 gap trades, 0 arb baskets) · best: n/a · worst: n/a
✅ Went well: full 100 min, 0 tracebacks, 0 stuck orders; 14 arb baskets held (cost ≤0.98, pays ≥1).
❌ Went wrong: open MTM -711 → -962 (RI Sen YES 0.880 vs 0.901 entry, ~-140); 21 positions held up to 43h, no fills; 54 gaps ≥0.04 reached, 0 filled.
💡 Improve (needs your OK): MAX_HOLD_HOURS/EXIT_BAND review (stuck conv positions starve new entries; 25 runs of evidence); gaps reached but nothing filled → depth/capital is the limit.
🔎 Opportunities: RI Gov/Sen gaps +0.090-0.100 recur every run; arb near-miss RI Gov +0.055, Nebraska Sen/U.S. House +0.035; YES baskets MN-05 +0.030, Hawaii Gov +0.025 (risk: third-party win); 45 unmapped.
🔧 Fixed: nothing (no bugs found).

## 2026-10-28T09:37Z run
LIVE · health OK (289 cycles, 0 tracebacks, kalshi 3 failures/429s, SIG read timeouts retried) · P&L run +3 / all-time -3,026 · open MTM -918
Trades: 13 fills (2 gap trades, ~4 arb rounds) · best: Alaska Sen arb take-profit +15/-12 legs · worst: WI-03 arb take-profit -7 leg
✅ Went well: full 100 min, 0 tracebacks, 0 stuck orders; realized +12 today, all orders filled; 2 new gap entries (FL Sen NO, TX-15 NO).
❌ Went wrong: open MTM -962 → -918 but still deep negative (RI Sen YES ~0.88 vs 0.901 entry); 23 positions, oldest held 45h; 52 gaps ≥0.04 reached, only 2 filled.
💡 Improve (needs your OK): MAX_HOLD_HOURS/EXIT_BAND review (26 runs of RI/MS gap evidence); capital tied in stuck conv positions starves new gap entries.
🔎 Opportunities: RI Gov/Sen gaps +0.090-0.105 recur every run; arb near-miss RI Gov +0.065, Montana/Nebraska Sen +0.030; YES baskets MN-05, Hawaii Gov +0.025 (risk: third-party win); 45 unmapped markets.
🔧 Fixed: nothing (no bugs found).

## 2026-10-28T11:37Z run
LIVE · health OK (243 cycles, 0 tracebacks, SIG read timeouts retried, kalshi 8 failures/429s) · P&L run +0 / all-time -3,026 · open MTM -689
Trades: 0 fills (0 gap trades, 0 arb baskets) · best: n/a · worst: n/a
✅ Went well: full 100 min, 0 tracebacks, 0 stuck orders; open MTM improved -918 → -689; 14 arb baskets held (cost ≤0.98).
❌ Went wrong: no fills for the run; 23 positions held up to 47h; 53 gaps ≥0.04 reached, 0 filled.
💡 Improve (needs your OK): MAX_HOLD_HOURS/EXIT_BAND review (27 runs of RI/MS gap evidence); gaps reached but nothing filled → capital tied in stuck conv positions is the limit.
🔎 Opportunities: RI Gov/Sen gaps +0.090-0.105 recur every run; arb near-miss RI Gov +0.070, Montana/Nebraska Sen +0.030; YES baskets Hawaii Gov +0.030, MN-05 +0.025 (risk: third-party win); 45 unmapped markets.
🔧 Fixed: nothing (no bugs found).

## 2026-10-28T13:39Z run
LIVE · health OK (390 cycles, 0 tracebacks, kalshi 6 failures/429s) · P&L run +3 / all-time -3,022 · open MTM -958
Trades: 22 fills (2 gap trades, ~7 arb rounds) · best: Maine Sen arb take-profit +3 · worst: WI-03 arb take-profit -7/+8 legs
✅ Went well: full 100 min, 0 tracebacks, SIG errors only 1; realized +16 today; new arb baskets Delaware/New Mexico/U.S. House (cost 0.978-0.980).
❌ Went wrong: open MTM -689 → -958 (RI Sen YES mark 0.865 vs 0.901 entry); 24 positions, oldest 49h; 54 gaps ≥0.04 reached, only 2 filled.
💡 Improve (needs your OK): MAX_HOLD_HOURS/EXIT_BAND review (28 runs of RI/MS gap evidence); capital tied in stuck conv positions starves new entries.
🔎 Opportunities: RI Sen/Gov gaps +0.09-0.116 recur every run; arb near-miss RI Gov +0.065; YES basket South Dakota Gov +0.065, Hawaii Gov +0.035 (risk: third-party win); 45 unmapped markets.
🔧 Fixed: nothing (no bugs found).
