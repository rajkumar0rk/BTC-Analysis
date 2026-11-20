# External discovery and novelty gate — 2026-11-21 01:02 IST

Status: REJECT BEFORE BACKTEST (novelty / market-mechanism mismatch); no positive expectancy claim.

Search: public GitHub Freqtrade strategy repositories, including paulcpk/freqtrade-strategies-that-work and freqtrade/freqtrade-strategies. Public source accessed via GitHub connector, not copied from a profit screenshot.

Source: https://github.com/paulcpk/freqtrade-strategies-that-work/blob/main/RSIDirectionalWithTrend.py ; author Paul Csapak; repository MIT license; source retrieved on 2026-11-21. Source SHA should be pinned before any executable implementation; this discovery is NOT an accepted experiment.

Original rules: 1h candles; RSI(4), EMA(100). Spot long entry when RSI crosses above 15, candle LOW > EMA100 and volume > 0. Exit when RSI crosses above 85 OR candle LOW < EMA100. Source stoploss -10%, trailing_stop=True; minimal ROI is commented out, with remaining behavior depending on Freqtrade configuration/defaults. No original short-side entry. Published 2018-03 to 2020-03 multiasset results are self-reported and cannot validate Delta BTC futures 2025.

Economic rationale: oversold recovery in an established uptrend. Novelty assessment: overlaps existing RSI2/EMA trend-pullback research and has no independent intraday clock/microstructure mechanism; not a good use of a BTC native run. Translating to symmetric short futures would be a NEW strategy, not rule-for-rule source parity. REJECT from this task's new-candidate pool without a backtest; do not count it as a tested strategy.

Other reviewed pool: https://github.com/freqtrade/freqtrade-strategies (generic indicators/ROI/stop examples); https://github.com/yukai1625/freqtrade-strategy-portfolio (CTA Donchian/ATR breakout overlaps existing Donchian studies; license not established). No claims of performance from either.

Next: select genuinely distinct, transparent third-party code with precise rules and permitted reuse; pin SHA, check novelty and then implement 2025 BTC zero-slippage fee+GST screen with GitHub Actions. If screening passes, freeze and stress 0.5/5 USD point slippage per side. Funding remains UNMODELED. No live changes. No BTC backtest executed this iteration; this discovery-only update is NOT a completed experiment.
