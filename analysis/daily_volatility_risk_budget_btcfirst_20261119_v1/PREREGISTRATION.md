# Preregistered BTC-first study: volatility-of-volatility gated directional risk budget (2026-11-19)

## Status
HYPOTHESIS REGISTERED, NOT BACKTESTED, NOT VALIDATED. No profitability or fill claim. This is an isolated, independent research track. Do not merge to main.

## Mechanism and novelty
Market volatility forecasts and actual realized volatility differ; after a sudden rise in short-horizon volatility-of-volatility, fixed notional intraday exposure may incur larger tail losses and costs. Hypothesis: selectively allocating directional risk only when short-term volatility is stable and the previous completed session's direction is persistent can improve **calendar-day** net profitability, chiefly by avoiding unfavorable regimes. This is not another volume-pressure, OI, VWAP, wick, breakout, funding drift, or weekend-only hypothesis. The null is that selective exposure after costs has no positive edge versus no-trade and simple BTC buy-and-hold risk-matched benchmarks.

## BTC-only selection and frozen validation protocol
Only BTCUSD 2025 data may inform configuration. All definitions below are frozen a priori for the initial test, not tuned on ETH or 2026. BTCUSD Jan 1–Dec 31 2025 is discovery; BTCUSD Jan 1–Nov 17 2026 is a later historical robustness check (NOT pristine untouched OOS). ETHUSD 2025 and 2026 are independent secondary checks with identical percentages, periods, risk, and entry/exit logic. Do not change BTC configuration based on ETH outcomes. If BTC fails, reject; do not rescue using ETH.

## Exact initial causal rule
- Use UTC timestamps and completed 1-minute candles; UTC day boundaries, including weekends and zero-trade days. Require 7 complete preceding UTC calendar days of 1m bars. Any missing required bars => no trade, data-gap day.
- At 00:00 UTC each day, compute realized volatility for each of the preceding seven COMPLETE UTC days: square root of sum of squared log minute close returns, using only returns whose both closes belong to that day. Calculate the coefficient of variation (population SD / mean) across those seven daily RV values. Require CV <= 0.40, and previous day's RV <= 1.25 times the seven-day median RV. No signal if median=0 or missing.
- Direction is the sign of the preceding UTC day's close divided by its open minus one. Require absolute move >= 0.40%; go LONG if positive, SHORT if negative. Do not use current-day price information in signal.
- Enter at 00:01 UTC open of first available completed 1m bar ONLY when all prerequisites are met; otherwise no trade. One position maximum; one entry maximum per UTC day. Initial stop = 0.45% of entry adverse, take-profit = 0.70% favorable, exit at 04:00 UTC bar open if neither hit. On same 1m bar touching stop and target, count stop first. No forced fills during gaps: missing bars invalidate affected trades as INCONCLUSIVE unless explicit conservative gap-fill convention is justified.
- Position notional = min(25% initial equity, notional implied by 0.25% initial-equity risk at 0.45% stop). No leverage beyond 1x. No compounding for comparison, and independently show compounded scenario if desired. No averaging losers, no martingale.
- Cost base: 0.158% round-trip of notional inclusive of assumed fees, GST, spread/slippage. Stress 0.238%. These are assumptions requiring independent Delta India verification, not proof of execution. Include funding only from authentic settlement cashflows or mark funding UNKNOWN; report both provisional excluding funding and INCONCLUSIVE executable status. Verify tick/lot/minimum notional and actual bid/ask before any live recommendation.

## Required results
One row for every UTC day including profitable, losing, zero-trade and data-gap days; trade timestamp, signal inputs, OHLC touch evidence, entry/exit, gross and net PnL, costs, reason; yearly/monthly PF, net return, number of profitable/losing/no-trade days, profitable calendar-day fraction, median/mean daily return, worst day, losing streak, max drawdown, cost stress, frequency, 2025/2026 splits. Save exact source hashes, run ID, executable script, frozen settings, monthly.csv and daily.csv. Re-run on ETH unchanged only after BTC rule freeze. Use no ETH-specific thresholds.

## Decision gate
Do NOT report a discovery unless BTC 2025 and 2026 exhibit credible positive net expectancy after realistic costs, many observations, bounded losses and reasonable daily frequency, then ETH independently confirms transferability or its failure is disclosed. Require independently verifiable fills and funding before any claim of tradeability. No real orders.

## Execution blocker
This commit is only a preregistration. A full executable backtest and accessible verified minute data must be attached and run before reporting numeric outcomes. Previous isolated experiments reported zero trades or substantial negative returns; no profitable strategy has yet been verified.
