# Reset Step 1 — ONE REAL TRADE PER WEEKDAY; Daily-profit consistency baseline

**NOVELTY DECISION: PARTIAL OVERLAP — approved differential.** This is a strict daily-coverage test of already researched fixed-time strategies, not a novel alpha discovery.

## User objective
The user wants **one BTCUSD trade EVERY Monday–Friday IST** and as many **consistently profitable days** as realistically possible after costs. The previous +0.2% net profit example is **NOT a fixed take-profit or strategy-success threshold**. A zero-trade day violates this experiment. Every candidate must enter on every eligible weekday without seeing its future price path.

## Previous research
- scripts/research_one_trade_every_day_200.py and analysis/one_daily_trade_200_points/RESEARCH_REPORT.md: one trade on every New York calendar day including weekends, fixed 200 gross/net point TP, price-point SL and 1/3/8-hour holding. The new test is IST weekdays, all 24 hourly entry clocks, broad percentage stop × reward matrix and daily net returns.
- scripts/research_btc_daily_opportunity_step1.py on research/btc-daily-opportunity-map-step1: 477 weekdays; hindsight max opportunity, no stop-first live-possible trades.
- scripts/research_btc_daily_target_first_step2.py: +0.2% net fixed target, six IST clock times, narrow stop range.
- scripts/research_btc_daily_direction_step3.py and scripts/research_btc_daily_rr_grid_step4.py: may skip 291–425 weekdays; rare strategies are not one-trade-per-day strategies.
- scripts/research_every_candle_200.py and Stage7 research: every-minute point first-passage, not account-percent risk/reward and compulsory daily coverage.
- Stage19, Stage23–25 event-based setups can skip weekdays and have different entry logic.

## Pre-registered deterministic test
- Delta India BTCUSD 1-minute OHLCV, contiguous authentic data January 2025–October 2026. Full IST weekdays from 2025-01-02 through 2026-10-30: **477 days, 260 in 2025 and 217 in 2026**. Validate duplicates, nulls, gaps and bad OHLC.
- **Exactly one entry PER weekday PER independent model** at the opening price of each of the **24 fixed IST clock hours**. None can skip a day and none can enter on Saturday/Sunday.
- 10 causal deterministic direction rules: always-long/always-short; last 5m/15m/60m/240m price momentum FOLLOW and FADE. Last completed 1m close relative to open of earliest bar in lookback determines sign. On zero change assign LONG to preserve one trade/day and report tie incidence.
- Gross price stop **0.10%, 0.20%, 0.30%, 0.50%, 0.75%, 1.00%**; gross TP **0.75R, 1R, 1.5R, 2R, 3R, 4R** times the stop distance. No fixed +0.2% target.
- Maximum hold **30, 60, 120 minutes**, capped at last 1-minute OPEN at 23:59 IST so no cross-day or weekend positions. Stop-first on simultaneous 1m touches; pessimistic gap stop; TP at threshold; timeout at 1m open.
- 100% account notional, **1x without leverage**. Taker standard 0.05%/side plus GST 18% and 5 BTC quote points adverse slippage each side. Alternative regular Scalper Offer hypothetical: zero closing taker/GST only when closed within 30 minutes, assuming pre-activated. Historical eligibility not verified. No funding/real L2/liquidation.
- **51,840 variants** = 10 directions × 24 hours × 6 stops × 6 targets × 3 max holds × 2 fee models. Every variant executes exactly 477 trades.
- Daily results primary: number/percentage of profitable and losing weekdays, daily net account returns, worst day, max losing streak, 2025/2026 separately. Also compounded net account PnL, 22 monthly returns, 2025/2026 positive month counts, max closed DD, costs, profit factor.
- 2025-only selection: among configs with 2025 positive compounded net account profit, maximize positive 2025 weekdays, then 2025 return and lower DD. If none, report failure. Recheck unchanged 2026, which has been research-exposed and is NOT a clean blind holdout.
- Show hindsight best across all 22 months as NOT tradeable. Count variants with >=60%, >=70%, >=80% profitable weekdays in EACH year AND positive net returns in both years, but warn of strong multiple-testing bias.
- Publish all comparisons, 477 daily results and 22 monthly results of the 2025-selected model. Stop after Step 1; do not add new predictive filters until evaluation.

## Quality note
Current 2026-11-23 source manifest says October 2026 is complete, superseding stale repository gate text; runner must check continuous 1m candles. This period has already been studied, and no historical fit guarantees future daily profit.
