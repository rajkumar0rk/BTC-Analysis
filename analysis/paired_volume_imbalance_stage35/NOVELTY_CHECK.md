# Stage35 preregistration and novelty gate — BTC-first signed-volume absorption
Decision: PARTIAL OVERLAP — explicit differential from prior price-volume impact reversal; not yet proven.

## Economic mechanism
A market with near-zero 24-hour net price change but strongly asymmetric *signed traded volume* may reflect passive liquidity absorbing aggressive flow. Hypothesis: once price stops being pinned, direction follows the persistent aggressive-volume sign. This is not Stage32's extreme price displacement divided by traded dollar volume, Stage34's serial-return covariance, or Stage33's semivariance reversal. Closest earlier work: `analysis/paired_impact_reversal_stage32/`, `analysis/independent_stage25_hourly_trend/`, `analysis/institutional_discovery_stage7_time_volume/`. Historical candle direction times volume is a PROXY for aggressor flow, not actual buyer-initiated volume, and may fail.

## Frozen rules
Completed UTC 1-hour candles; evaluate only 00:00 UTC. Require 25 fully formed 1h bars. Compute 24-hour signed volume imbalance = sum(sign(hourly log return) * hourly volume) / sum(hourly volume). Require absolute 24-hour log price drift <= 0.006. Long if imbalance >= 0.35; short if <= -0.35. Enter next available minute open. Stop 1.5x median hourly true range (24h lookback, shifted one bar), take profit 1.5R, maximum 480 minutes; one position; 0.5% NAV risk capped at 3x gross leverage. Stop-first if intrabar order ambiguous. BTC fee 0.05% each side plus 18% GST, 5 BTC points adverse slippage per fill; ETH 0.02% per fill; stress 10 BTC points / ETH 0.035%. Funding, spread, historical impact and liquidation maintenance unverified, so do not claim live-ready results.

## Falsifier and selection
Use BTC 2025 as discovery only. Reject if BTC 2025 net expectancy <=0, insufficient trades, poor cost stress, destructive drawdown or concentration. Rules frozen before BTC 2026 and ETH replay. No tuning on 2026/ETH. Preserve all 22 IST months, including flat/negative months, and report account NAV marked at month end. January 2025 IST start gap and October 2026 missing UTC candles must be checked. No fabricated data.

## Execution state
Script committed; workflow trigger and actual run confirmation must be audited before any performance claim.
