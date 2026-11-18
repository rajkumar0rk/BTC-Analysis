# Stage28 novelty gate — relative price-impact shock fade

**Decision: PARTIAL OVERLAP — approved differential**, not an assertion of profitability.

## Predeclared causal rules

Using completed 15m Delta India BTCUSD futures candles, compute the bar's absolute log-return divided by (its reported exchange volume + 1), a rough OHLCV-based *price impact per reported volume* proxy. Compare it with the trailing 96 COMPLETED PRIOR 15m bars' median impact; also compare current bar volume with the trailing prior 96-bar median volume. If the latest completed bar's impact exceeds 3x or 5x the trailing median, and its volume is less than 0.75x prior median, fade the completed bar direction (long after down bar; short after up bar). This tests whether an unusually large move on unusually thin reported volume mean-reverts, rather than generic high volume, RSI, sweep, semivariance or variance-ratio effects. The volume units are exchange-reported and not verified to be BTC; the ratio is dimensionless only relative to its own trailing distribution. No actual order-book liquidity inference.

Enter next 1m OPEN, one open position, no stacking. Stop = 1.5x or 2.5x 15m ATR(14) calculated on completed bars; profit = 2x stop, maximum 240 minutes, stop-first when 1m touches both stop and target, flatten at IST month boundary. Risk 1% of account equity per trade with maximum notional 3x equity, initial $1000. Fees 0.05% per side plus 18% GST; 5 BTC points adverse slippage per side. Four configurations predeclared: impact multiples 3 and 5 crossed with ATR stop multiples 1.5 and 2.5. Select best using 2025 positive-month count and aggregate return only; audit fixed choice over 2026. Do not optimize by month or borrow old results.

## Closest experiments

- Stage7/9 `scripts/research_anytime_volume_volatility_patterns.py` and `scripts/research_adaptive_anytime_entries_stage9.py`: volatility and volume continuation/contrarian studies, but not price displacement **per reported volume** relative to lagged 96-bar impact median with a simultaneous low-volume constraint.
- Stage24 `research/stage24-monthly10` `analysis/institutional_discovery_stage24_structure_monthly10/RESEARCH_REPORT.md`: 15m structure breakouts, retests, squeeze; no impact ratio.
- Stage25 `research/stage25-new-trend` `analysis/independent_stage25_hourly_trend/RESEARCH_REPORT.md`: hourly momentum/inside-bar; no impact ratio.
- Stage26 `analysis/independent_stage26_semivariance/NOVELTY_CHECK.md`: signed squared-return imbalance over 32 bars; no volume normalization.
- Stage27 `research/independent-stage27-variance-ratio` `analysis/independent_stage27_variance_ratio/NOVELTY_CHECK.md`: 4-bar/1-bar variance ratio, serial dependence, not return-per-volume.
- Stage19/23: EMA, RSI, breakout, sweep, compression, volume; none specifically combines this normalized thin-volume price-impact shock threshold.

Generic reversal/volume premises overlap prior work, so the hypothesis is only **incrementally distinct**; report as partial overlap, never brand it a proven institutional edge.

## Data and validity

New branch from `research/oct31-raw-repair`; use genuine original Delta India BTCUSD 1m gzip archive, verify manifest SHA256 and minute continuity for Jan 2025–Oct 2026, including restored Oct31 2026. Source first minute 2025-01-01 00:00 UTC means Jan 2025 IST lacks its first 5.5 hours. November 2026 excluded. Source candles are not L1/L2 fills, funding settlements, actual bid/ask, liquidation prices or confirmed margin. No lookahead: trailing medians shift by 1 bar and signals become eligible only after latest 15m candle closes. January–December 2025 only used for parameter choice; Jan–Oct 2026 fixed retrospective recheck, not pristine out-of-sample due to earlier research exposure. Never combine earlier ledgers or overwrite earlier directories.
