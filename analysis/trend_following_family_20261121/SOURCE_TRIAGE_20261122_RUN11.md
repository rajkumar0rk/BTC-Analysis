# Trend-family source triage — 2026-11-22 run 11

Status: source/novelty screening ONLY; 0 newly completed historical strategy backtests, 0 variants. No source-faithful profitability claim.

## Recovery
- Branch `research/trend-following-family-20261121`, head `d5c667bdc11f542598cf3a6369f70470f1bf450f` before this research note.
- Canonical Actions branch listing `GET /repos/rajkumar0rk/BTC-Analysis/actions/runs?branch=research/trend-following-family-20261121&per_page=30`: 18 runs, newest 44952126471, status completed/success, head SHA d5c667b; no newer historical runs at inspection time. https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44952126471
- Existing TF-ICH-001 baseline unchanged: 28 trades, 1.2387 PF, +1.6998% net NAV, 6/12 profitable 2025 months; source-faithful status unresolved. No 2026/ETH verification.

## Candidate 1 — Freqtrade triple Supertrend (source recovered, skip pending novelty)
- Author: Juan Carlos Soriano (@juankysoriano); source https://github.com/freqtrade/freqtrade-strategies/blob/main/user_data/strategies/Supertrend.py ; repository GPL-3.0 (repository metadata inspected 2026-11-22). **Source commit not pinned: not an immutable reproduction baseline yet.**
- Source: 1h long-only; 3 buy Supertrend direction signals all up plus volume >0; exits 3 distinct sell Supertrend signals all down plus volume >0; configured buy multipliers 4,7,1 and periods 8,9,8; sell multipliers 1,3,6 and periods 16,18,18; 199 candle warmup. Hard stop -26.5%; time-dependent ROI 8.7%/5.8%/2.9%/0%; trailing 5% with 14.4% offset. Hyperopt parameters described as optimized from 2021-01-01 on 1h, but no source-reproduced BTC trade count, PF, net return, DD or fee assumptions verified.
- Caveat: Supertrend direction implementation delegates to `technical.indicators.supertrend`, not pinned; upstream warns validation concerns; indicator must be checked for forward lookahead. Port to Delta BTC futures would require a separate, explicitly adapted execution/cost model, not claim faithful identical Freqtrade spot fills.
- Novelty: overlaps existing 4h Supertrend and Stage25 trend experiments; triple confirmation may reduce whipsaw but needs source-level comparison before approving incremental hypothesis. **No backtest launched.**

## Candidate 2 — Freqtrade Heracles (source recovered, reject as trend-family baseline)
- Author: Masoud Azizi (@Mablue); source https://github.com/freqtrade/freqtrade-strategies/blob/main/user_data/strategies/Heracles.py ; repository GPL-3.0, source commit unpinned.
- Source: 4h long-only, Donchian channel percentile (window 10) divided by Keltner width (window 20/ATR 10), with shifted historical indicator values (15 and 9) and ratio between 0.16 and 0.75. Stop -25.6%, timed ROI tiers 59.8%/16.6%/11.5%/0%. Embedded publisher hyperopt snippet reports 25 trades, 18 wins/4 draws/3 losses and 48.88% total profit; period, exchange, fees, DD and PF not independently established. **Publisher numbers are not our results.**
- This is volatility/channel-relative signal, not a directional persistence/trend-following mechanism. **SKIP as outside this family's mandate; coordinate read-only with Breakout & Range if needed.** Shifted inputs alone do not establish a repainting issue, but full indicator code must be checked before reproduction.

## Candidate 3 — xy3293 Supertrend/EMA/ADX catalog (duplicate gate)
- Source https://github.com/xy3293/crypto-strategy-backtest ; source SHA/license unpinned. Earlier novelty ledger documents `supertrend_4h`, `ema_ribbon_4h`, `adx_trend_4h` as discovery leads. Standalone Supertrend flip rejected as economically duplicate; EMA alignment and directional ADX require Stage25 comparison. **NOT source-pinned/reproducible for this run; no test.**

## Next executable work
- Pin source commits and dependencies, compare Stage25 and Stage13 source logic, then approve only a materially distinct causal trend-persistence strategy.
- Implement in existing 1m historical runner with completed higher-timeframe signals, next-minute entry, stop-first/gap fills, two-sided 0.05% fees + 18% GST and zero first-screen slippage; execute real workflow and inspect full artifacts before claiming a result.
- No repository main/master, other-family branch, VPS or live trading changes.
