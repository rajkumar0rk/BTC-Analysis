# Novelty check — Supertrend ATR10×3 with EMA9/21

Pre-registered 2026-11-22 UTC. Decision: **NEW (incremental trend-confirmation mechanism, user-requested)**.

## Frozen hypothesis and protocol

- Authentic Delta Exchange India BTCUSD perpetual 1-minute OHLCV from `data/delta_india/BTCUSD/1m/` on main.
- Evaluate separately on 5-minute, 15-minute and 1-hour bars; use only fully completed bars, enter/exit at immediately following true 1-minute OPEN, no chart timeframe dependence.
- EMA9 and EMA21 use standard exponential smoothing. Supertrend uses Wilder ATR(10) and multiplier 3.0, with standard carried upper/lower bands; warm-up 100 full bars.
- Bull alignment = EMA9 > EMA21 AND bullish Supertrend; bear alignment = EMA9 < EMA21 AND bearish Supertrend. Entry occurs only on a transition into aligned state, in either direction.
- Compare **signal_exit**: exit immediately after completed bar loses combined alignment, reversals allowed; versus **SL100_TP200**: fixed 100-point stop and 200-point take-profit from slipped entry, 1-minute intrabar stop-first conservative tie resolution; no automatic re-entry after stop until next alignment transition.
- Only one position per experiment; no arbitrary cap, weekends included (BTC 24/7).
- At IST month end, flatten open trades using last observed 1m CLOSE and charge exit costs; this gives independent calendar month results. No intraminute stop path forecast.
- Default model: entry and exit $5 adverse slippage per BTC, Delta taker fee 0.05% per side plus 18% GST, zero funding because not sourced; compounded 1× notional account return, trade-close maximum drawdown. No margin, leverage, order-book impact, exchange funding or fill guarantee.
- Research span Jan 2025 to Oct 2026; November 2026 excluded as incomplete. Jan 2025 starts at 05:30 IST because source starts Jan 1 UTC, so IST January is incomplete. 2026 data has been previously researched and is **not** a blind holdout.
- Preserve all trade ledgers, summary, IST monthly results and explicit data quality; never claim a live-profit edge from an historical exploratory result.

## Similar prior work

- `analysis/ema921_1h15m5m_rr` on `research/ema921-1h15m5m-rr-20261122`: 1H+15M EMA trend filter with *5M EMA crossover* and 2R/3R stops. No Supertrend; new independent same-timeframe conjunction evaluated.
- `analysis/ema921_fixed100_200` on `research/ema921-fixed100tp200-20261122`: same multi-timeframe EMA signals, fixed 100/200 exit, no Supertrend; different causal entries.
- `analysis/independent_stage25_hourly_trend` on `research/stage25-new-trend`: 1H momentum, Donchian, inside bars (optional 4H filter), no EMA9/21-Supertrend alignment.
- `analysis/institutional_discovery_stage24_structure_monthly10` on `research/stage24-monthly10`: 15M squeeze/retest structure signals, not this trend-following conjunction.
- `scripts/research_trend_pullback_breakout_stage13.py`: 4H EMA20/50 context + 1H pullback + 15M breakout, unlike same-timeframe Supertrend + EMA.
- No indexed Supertrend implementation/result in main found at pre-run inspection.

Comparison includes a common fixed 100/200 exit from recent user requests, not a claim of novel exit. This is in-sample/exploratory research with known multiple-testing risk.
