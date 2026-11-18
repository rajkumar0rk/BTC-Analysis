# Stage 27 novelty gate — rolling Lo–MacKinlay-style variance-ratio regime

**Decision: PARTIAL OVERLAP — approved differential.**

## Deterministic new hypothesis

On completed 15-minute BTCUSD bars, calculate trailing 96-bar log-return variance ratio: sample variance of *overlapping 4-bar cumulative returns* divided by 4 times the sample variance of 1-bar returns, with both windows lagged one full completed bar. This statistic is a proxy for serial dependence, not a guarantee of tradable momentum. A high ratio (threshold 1.2 or 1.4) indicates persistence; a low ratio (0.8 or 0.6) indicates mean reversion. Determine side from sign of most recent *completed* 4-bar return: follow sign when high ratio, fade sign when low ratio. Enter next 1m open. One position only, flatten at IST month end. Initial stop = 2.5x 15m ATR(14); take-profit = 2x stop; timeout 240m; stop-first 1m execution; 1% current equity risk per trade capped at 3x notional. Evaluate 4 predeclared threshold/mode combinations: high 1.2, high 1.4, low 0.8, low 0.6. No future-bar features, no month selection. Include 0.05% taker each side, 18% GST on fees, 5 USD adverse slippage per side. No settled funding, bid/ask, impact, margin, liquidation or lot-size simulation.

## Closest existing and differentiation

- Stage26 `scripts/research_stage26_semivariance.py`, `analysis/independent_stage26_semivariance/NOVELTY_CHECK.md`: asymmetric *signed squared-return sums* and reversal of same-direction bar; Stage27 measures serial correlation of 4-bar returns relative to 1-bar variance, and follows/fades by variance-ratio regime.
- Stage25 `research/stage25-new-trend`, `analysis/independent_stage25_hourly_trend/RESEARCH_REPORT.md`: hourly trend/momentum/inside bar; Stage27 15m autocorrelation ratio.
- Stage24 `research/stage24-monthly10`, `analysis/institutional_discovery_stage24_structure_monthly10/RESEARCH_REPORT.md`: 15m breakout, retest, squeeze; Stage27 uses no breakout levels.
- Stages 7, 9, 19, 23: candle/volume/clock, supervised direction and 5m price patterns; none explicitly evaluates trailing multi-horizon variance ratio as the regime statistic. The generic trend/fade thesis overlaps; this is an incremental measurable difference, not a proven edge.

## Data and evaluation

Branch starts from `research/oct31-raw-repair` with original Delta India BTCUSD 1m data, including recovered 2026-10-31 UTC; check every source month against manifest SHA and exact minute continuity before testing. Use January–December 2025 only to choose a configuration, then report January–October 2026 without refitting. 2026 has been inspected in other research, so this is **not** pristine forward validation. January 2025 IST starts 5.5h before available UTC archive, so first IST month incomplete. Missing funding, spread, impact and liquidation remain limitations.

**Gate passed as PARTIAL OVERLAP with explicit variance-ratio differential.** Do not merge any previous strategy ledgers or results; isolated script and output folder only.
