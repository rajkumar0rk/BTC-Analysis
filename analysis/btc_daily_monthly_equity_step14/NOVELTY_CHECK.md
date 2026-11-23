# Step 14 — causal month-to-date equity-state exit management with 477 daily BTC positions

**Novelty decision: PARTIAL OVERLAP, conditional experiment allowed.** This is not an independent trading strategy class. It explicitly extends only the 2025-selected Step13 monthly fallback profit closure by examining whether early loss cuts, drawdown-from-month-peak and prior same-month losing streak can improve losing months **without selecting using 2026 outcomes**. Step13 succeeded in improving 17/22 to 19/22 months, but the November follow-on check returned −0.471% vs +0.019% Step11, so it is not independently validated.

## Closest implementations
- `scripts/research_btc_every_weekday_reset_step1.py`: compulsory 477 full IST weekdays.
- `scripts/research_btc_every_weekday_exit_protection_step3.py`: existing 1m stop, trailing/profit locks next-bar valid.
- `scripts/research_btc_daily_exit_invalidation_step7.py`: 67 completed-bar next-open early exits, ordinary static early exit harmed expectancy and/or November.
- `scripts/research_btc_daily_online_structure_step11.py`: six frozen structural direction arms and prior60 fallback-day online selector, 279/477 winning trades, 17/22 positive months.
- `scripts/research_btc_daily_monthly_recovery_step12.py`: 120 month-to-date direction changes failed to improve months.
- `scripts/research_btc_daily_monthly_exit_step13.py`: 132 conditional monthly exits, 2025-selected rule delivered 19/22 profitable months, 477 weekday positions, +23.261256% hypothetical offer net, 290 win days, 3.008746% max closed DD, under 1x account notional. Exactly three negative months: Jan2025 −1.662335%, June2025 −0.275849%, Jan2026 −0.564834%. Step13 selected rule: on fallback 21h if PRIOR completed month PnL<=+0.25%, after 20 completed minutes close at NEXT 1m OPEN when last 1m CLOSE shows gross signed profit>=0.10%; unchanged stop/TP/trail otherwise.

## Fixed base trading rules
- Authentic BTCUSD futures 1m historical Delta India Jan2025–Oct2026; 477 distinct full IST Monday-Friday dates, 260 in 2025, 217 Jan–Oct2026. MUST trade exactly once EVERY such day. NO weekend entries, abstentions, reduced size, zero-size trades, extra trades, martingale or changed leverage. Exactly 1x account-notional/full exposure per trade.
- Entry timestamp and side identical to 2025-selected Step11: first eligible precompleted 5m volume ratio >=1.5x prior20 complete 5m at 18/19/20 IST, else 21:00 forced fallback. Event direction = Step8 frozen prior-day online signal; fallback = Step11 frozen previous60 settled fallback arms mean net, min15. No selecting based on future current trade.
- SL/TP/trailing baseline EXACT Step11: event mid SL0.5%, profit lock +0.10% activated +0.25% next 1m; fallback mid SL0.5% or0.75% per preentry completed5m relative volume>=1.25x, trail activates +0.35% with distance0.20%; gross TP3%, max hold30m, stop-first if same 1m candle hits TP+SL, stop move only from *completed* previous candle, time exit at 30m 1m OPEN. Step13 conditional fallback exit described above layered on baseline.
- Economics at every trade: standard0.05% taker/leg plus GST18%, hypothetical preactivated regular Scalper Offer closing-leg zero fee only when exit within <=30m; 5 BTCUSD quote-price points adverse slippage EACH leg; 1x account notional, no historical proof offer actually enabled, no actual orderbook, latency, funding, liquidation, tick-level order.

## Novel monthly equity-state overlay (predeclared)
Before each weekday's entry compute ONLY prior **actually chosen strategy positions'** realized account returns in the current IST calendar month. Reset equity=1 and peak=1 at month open. MTD = prior equity−1. Peak giveback = current-month previous peak equity−prior equity. Previous losing streak counts consecutive earlier *finished actual trades* in the month. Day index counts only earlier weekdays in the month. Current/future day's outcomes cannot modify current order.
- Ten mutually exclusive *per-model trigger definitions*: (a) MTD<=0%, (b) MTD<=−0.25%, (c) monthly peak giveback>=0.30 pp, (d) giveback>=0.60 pp, (e) prior month equity peak>=+1% AND giveback>=0.50pp, (f) prior 2 consecutive losing days, (g) prior 3 consecutive losing days, (h) first 5 trading weekdays of month, (i) after >=10 prior weekdays AND giveback>=0.50 pp, (j) MTD>=+1.0% (protect winning months). No other thresholds.
- On triggered day apply one *substitution* of the previously tested next-bar exit, to event trades only, fallback trades only, or both, replacing the Step13 chosen exit just on that day:
    - adverse cut at prev1m CLOSE <=−0.08% after 5 completed minutes;
    - adverse cut <=−0.12% after 5;
    - adverse cut <=−0.08% after 10;
    - adverse cut <=−0.20% after 10;
    - insufficient maximum favorable excursion <0.10% after 10 completed minutes;
    - profit CLOSE>=+0.10% after 10 completed minutes;
    - profit CLOSE>=+0.15% after 20 completed minutes;
    - hard timeout after 10 minutes;
    - hard timeout after 15 minutes;
    - hard timeout after 20 minutes.
- No exit decisions from current-bar HIGH/LOW, no same-bar early exit; triggering CLOSE results in exit at NEXT 1m OPEN after the normal SL/TP check. Existing Step13/Step11 guard remains in nontriggering sessions.
- Exact preregistered **10 triggers ×3 scopes ×10 alternate exits = 300 experiments + unchanged Step13 baseline**. Cost sensitivity reprices exact same selected trade/exit decisions under standard fees, not a separate model selected on standard fees.

## Selection / validation
- Primary selection using **only 2025 (Jan–Dec, 260 weekdays)**. Require >=11/12 profitable calendar months (otherwise baseline remains selected), compounded 2025 account return >=+9.5%, 2025 win days>=157, and <=3.05% 2025 closed drawdown. Among qualifiers maximize 2025 positive months, then 2025 compounded net return, winning weekday count, lower 2025 DD. If no 11/12 qualifying, retain Step13 as selected; do not weaken bounds after seeing 2026.
- Recheck unchanged selected policy in Jan–Oct 2026, previously heavily researched and NOT a pristine untouched holdout. To promote to next historical candidate require >=20/22 profitable calendar months, >=9/10 in 2026, compounded 22-month net>= +23.261256%, closed DD<=3.008746%, exactly 477 trades. Separately report changes in win days, worst month and year-by-year net. Label all-history maximum positive months HINDSIGHT ONLY, not selected; do not change models to target 2026 Jan after reading results.
- Publish exact Step13 replay baseline per-individual-trade equality for both fees, 301×2 grid with costs, full 477-day trade ledger, 22 calendar-month returns, breakdown 2025 vs2026, max drawdown, worst-month/day, fee/point slippage/exit reasons, number overlay triggers and actually changed exits.
- November 2–20 2026 has been repeatedly inspected in previous steps; if checking it later, it must remain a locked chronological diagnostic, not a pristine blind holdout. NO claim of live-readiness from this selection.

## Risks
Only 22 historical months; 301 more comparisons after many earlier stages creates multiple-testing false discoveries. A losing month might be unavoidable with one full-notional trade every weekday. Real Scalper Offer historical eligibility, market fills, bid/ask depth, funding and tick execution are unverified. Standard fees made Step13 lose ~6.97%.
