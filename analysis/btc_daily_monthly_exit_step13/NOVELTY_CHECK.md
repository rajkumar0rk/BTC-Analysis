# Step 13 — causal monthly recovery by PREVIOUS-bar exit, one trade each weekday

**Novelty classification: PARTIAL OVERLAP — approved incremental regime use**, not new early-profit/stop signals. There is no previously validated edge; do not imply one. This tests **conditioning a small fixed set of previously implemented next-minute exit policies on current-month accumulated returns only from earlier completed daily positions**.

## Closest prior evidence
- `scripts/research_btc_every_weekday_reset_step1.py`: 477 daily trades, static stops/targets and timeouts.
- `scripts/research_btc_every_weekday_exit_protection_step3.py`: 425 static/protected exits, 477 weekdays, profit-lock updated next 1m.
- `scripts/research_btc_daily_online_direction_step6.py`: causal previous-event outcomes.
- `scripts/research_btc_daily_exit_invalidation_step7.py`: **67** early exit policies; 2025-selected 316 winning days but total net +5.50%, 11/22 months, so rejected for erosion of returns. Late November early-exit variations reduced profit. Step13 does NOT reintroduce them as universally superior; tests only conditional usage after month-level losses.
- `scripts/research_btc_daily_online_structure_step11.py`: immutable current baseline, 477 weekday trades, **17/22 positive months (9/12 2025, 8/10 2026), +22.141056% modeled net, 279 winning days, 3.008746% maximum closed DD** with assumed Scalper Offer.
- `scripts/research_btc_daily_monthly_recovery_step12.py`: previous 120 month-to-date direction-switch variants had **NO model** reaching 10/12 positive 2025 months or 18/22 full period; chose unchanged Step11 baseline. New experiment freezes direction and probes a different component: exits.
- Other institutional stages 19, 23, 24, 25 include broad price action/exit work but do not audit conditional all-477-day month-to-date recovery of Step11 fixed entries.

## Immutable risk, selection and trade-count contract
- Exactly **one BTCUSD futures trade on all 477 full IST Monday–Friday dates Jan 2 2025–Oct 30 2026**. No weekend entries and no missed days. Fixed **1× account notional (100% equity exposure)**; no leverage adjustment, sizing games, zero-size trades, additional orders or trades/day. No extra fee-free trades.
- Preserve Step11 EXACT entry minute and side, selected causally before entry: earliest 18:00,19:00,20:00 IST hourly checkpoint meeting preentry completed 5m volume >=1.5× previous20 5m average, otherwise forced 21:00 IST trade. Event side = frozen Step8 past-only algorithm, fallback side = frozen Step11 past60-fallback-day 6-arm mean offer net, min15 historical data. No refitting or reranking entry direction.
- Baseline exits identical: EVENT SL0.5% gross, TP3% gross, max30m, lock+0.10% after +0.25% favorable completed 1m bar. FALLBACK SL0.5% or0.75% by completed 5m vol ratio>=1.25, TP3%, max30m, trail activation+0.35%, distance0.20%, stop updated only NEXT 1m candle; stop first if same 1m touches both target and stop; worse-than-stop fills on gap.
- Costs: 0.05% taker each side+18% GST, 5 BTCUSD price points adverse slippage each leg, and hypothetical preactivated regular Scalper Offer closing fee waived **only for <=30m holding**. Same chosen decisions repriced separately under standard taker both legs. Account net returns use 1x notional. Funding, real spreads, market impact and actual historical offer status not available.

## Frozen experimental conditional exits, no future data
- Before each current trade, compute month-to-date compounded **NET ACCOUNT return from PREVIOUS FINISHED actual trades only**, reset each calendar IST month. Do not include the current day's result or any future bar.
- Trigger monthly early exit mode only if month-to-date return before entry is <= **−0.50%, −0.25%, 0.00%, or +0.25%** (four fixed thresholds).
- Apply the chosen early exit mode to **event trades only**, **fallback trades only**, or **both** (three fixed scopes). Untriggered trades use the exact baseline Stop/TP/trailing.
- Select one of **11 nonbaseline fixed next-bar exit modes** from already validated Step7 1m stop-first replay:
  1. Early profit at NEXT 1m OPEN if completed 1m CLOSE at/after 10 minutes shows signed profit >=+0.10%;
  2. same +0.15% after 10m;
  3. +0.10% after 20m;
  4. +0.15% after 20m;
  5. +0.20% after 20m;
  6. after 5 completed minutes early exit if completed CLOSE signed <=−0.08%;
  7. same <=−0.12%;
  8. after 10 completed minutes signed close <=−0.08%;
  9. after 10 completed minutes if max favorable excursion since entry <0.10%;
  10. fixed timeout 20m;
  11. fixed timeout 25m.
- In all cases, mandatory initial stop, take profit and protective trailing operate exactly as Step11 and are checked first in the current 1m candle. If no prior stop/TP hit, the completed 1m close / favorable range may trigger additional exit **ONLY AT NEXT MINUTE OPEN**; never fill retroactively at same-bar high/low. When no condition is met hold max30m.
- Matrix **4 MTD thresholds ×3 scopes ×11 additional exits = 132**, plus unchanged Step11 baseline. Every one of 133 models always enters each weekday once, only its exit can differ. No optimizing entry side or leverage in this experiment.

## Evaluation, predetermined before computation
- Model selection uses **only 2025** monthly results (260 weekdays across 12 full IST months). To qualify as a monthly improvement require >=**10/12 profitable months**, 2025 net account return >=**+8.5%**, 2025 winning weekday count>=**147**, and 2025 max closed DD<=**3.05%**. Rank by 2025 profitable-month count, 2025 net return, 2025 positive weekdays and lower 2025 DD; otherwise retain **unchanged Step11**.
- After selecting solely from 2025, apply frozen policy to Jan–Oct 2026 (217 weekday trades, 10 complete months). 2026 is research-exposed by prior work and **not** an untouched holdout.
- Promotion criteria: at least **18/22 profitable months**, 2026 positive months>=8/10, total account modeled net>=Step11 **+22.141056%**, max closed DD<=Step11 **3.008746%**, no drop in 477 trades. Also report annual changes in winning days and net separately (even if all-metric criterion is met).
- Publish all 22 monthly returns, both annual PnL/DD, worst loss day/month, max losing streak, event/fallback split, 133 variant grid, full 477 daily selected and baseline ledgers, after-fee results and standard-fee sensitivity.
- Full 22-month best hindsight can be shown explicitly as *in-sample diagnostic only*, never substituted for the 2025-selected rule. The 2026 and November data were already examined; no forward/live validation. No optimizing the result post hoc to selectively erase 2025 June, December, January or 2026 January/May.

## Research caution
The user explicitly requires improving monthly wins without reducing trades, but such constraints do not guarantee existence of a profitable daily strategy; testing many variants increases overfitting. Delta offer history cannot be inferred from OHLC and without the waiver Step11's full-sample compounded return was −7.812987%. Do not deploy from the historical best.
