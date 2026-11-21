# Pre-run novelty check: 15M second EMA20 touch with volume + volatility
Date: 2026-11-21

## Fixed experiment
BTCUSD and ETHUSD Delta India 1-minute futures candles Jan 2025–Oct 2026 (22 IST months). Same 15-minute EMA20 second distinct post-Supertrend-flip-bar touch immediate-entry as `scripts/research_ema20_second_touch_fixed_tpsl.py` and same 1m conservative SL-first exits. Fixed BTC +200 TP / -100 SL. ETH uses BTC-percent-equivalent TP/SL recomputed on entry from last completed 1-minute BTC close, frozen thereafter. Same 0.05% taker each side, GST 18%, adverse assumed slippage 0.02% per side, 1x model equity, no trailing or breakeven. Entry on touch without waiting for close.

**Volume filter:** at the time of the second touch, last fully completed 15M candle volume must be >=1.20 times the mean volume of the 20 preceding completed 15M candles (the current 15M volume is not known and is forbidden).

**Volatility filter:** last fully completed 15M ATR(14) Wilder must be >=1.00 times the mean ATR(14) of the 20 preceding complete 15M candles. No current candle high/low/ATR values are used.

Both filters evaluated only at the SECOND touch; ignored for first touch. No crossing of previously unrealized indicator values. If second touch rejected, count resets and the next two eligible touch-candles may form a new setup. (Pre-specified strategy implementation.)

Four independent variants per asset: baseline (both disabled), volume only, volatility only, both filters enabled. Each single-asset strategy independently exclusive positions. For comparisons show counts, TP/SL first hits, win rate, fees, net account return, PF, max realized drawdown, positive months. No leverage beyond 1x. Historical monthly breakdown retained for all variants.

## Prior research and difference
- `analysis/ema20_second_touch_fixed_tpsl_20261121/` and `scripts/research_ema20_second_touch_fixed_tpsl.py`: exact baseline entry/exits, no volume or volatility filter.
- `analysis/institutional_discovery_stage19_new_1h_patterns/` and `scripts/research_new_1h_patterns_stage19.py`: completed-candle EMA confirmation, some volatility contexts, not a second-touch counter with intrabar execution.
- `analysis/ethusd_native_atr_price_action/` and `scripts/research_eth_native_atr_price_action.py`: other EMA pullback with completed-candle signals, native ATR stops, not this hypothesis.
- Stage24 15m structure and Stage25 1H trend research on separate branches: related trend systems, but different signal, entry timing and stop mechanics.

Novelty decision: **PARTIAL OVERLAP — approved differential**. Tests whether two explicitly ex-ante market-quality gates rescue the weak 15M second-touch setup. This is a controlled differential from existing same-signal fixed-TP/SL experiment, not a new claimed entry family.

## Data/validation
SHA verify every 2025-01 to 2026-10 CSV partition, no missing minute interpolation; all 22 months including zero-trade months. First 330 minutes of January 2025 IST outside archived UTC data. 2026 already analyzed in multiple earlier research studies, **not an untouched statistical validation**. No new parameter sweep or performance target fitting. All outcomes, positive or negative, preserved. No tick sequencing/spread/funding/latency information, results purely 1m OHLC model.
