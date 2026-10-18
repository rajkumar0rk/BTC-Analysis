# Next analysis roadmap

1. Verify source identity, timezone and open/close timestamp labelling.
2. Audit 5m bars for flat volumes, gaps, corrections and corporate/exchange-specific anomalies.
3. Scan all 5m, 15m, 30m clock/day combinations, compare to baselines, and correct multiple comparisons.
4. Cluster 2–10 candle patterns using normalized body/wick/range/volume features, without preselecting candlestick names.
5. Evaluate continuation, reversal and move magnitude 5m through 240m later, with non-overlapping event windows.
6. Train Jan–May, validate June–July and seek new August–October 2026 data before accepting any signal.
7. Test fee/slippage/funding assumptions with conservative entry/exit rules, drawdown and tail-risk controls.
8. Preserve null findings, data versions, parameters, machine-readable outcomes and executable scripts for each experiment.
