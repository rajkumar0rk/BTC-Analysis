# Second EMA20 touch + fixed TP/SL — pre-run novelty check

Date: 2026-11-21. Research-only branch: `research/ema20-second-touch-fixed-tpsl-20261121`

## Fixed hypothesis and scope
Compare the already defined *second EMA20 touch immediate entry* independently on 15m and 1h, BTCUSD and ETHUSD, using Delta Exchange India authentic 1m OHLCV January 2025–October 2026 (22 IST calendar months).

Entry: Supertrend(10,3) on completed HTF bars defines direction; ignore flip bar for touch counting, max one touch per distinct subsequently eligible HTF candle; second EMA20 touch in 1-minute underlying candle enters immediately at frozen EMA20 from last completed HTF bar, with adverse entry slippage. Reset touch count after entry/exit. Only one position simultaneously per asset/entry timeframe. No candle-strength or candle-close entry requirement.

**Changed economic rule**: fixed TP=200 BTC price points and SL=100 BTC price points. ETH does **not** reuse 200/100 ETH dollars: scale both on each entry using the contemporaneous ex-ante ETHUSD entry price divided by the **previous completed minute BTCUSD close**:

`ETH_TP_USD = 200 * ETH_entry_price / prior_1m_BTC_close`
`ETH_SL_USD = 100 * ETH_entry_price / prior_1m_BTC_close`

This makes target and stop approximately equal *percent* of BTC spot at that same point in market history, instead of imposing same absolute BTC price-point move on ETH. The two levels are frozen at entry and never recalculated. BTC 200/100 absolute point levels likewise frozen at entry.

Exit: stop-first if both levels seen within same 1m candle; favorable target cannot be credited on the initial entry minute because ordering against entry is unknown, though adverse stop crossing is counted; gaps through stop fill at adverse open, target limit at target. No trailing/breakeven; no time exit (sample-end mark to close only). **Assumed** 0.05% taker fee each side + 18% GST, 0.02% adverse entry and exit slippage each side, model 1× evolving equity ($1000 initial), no funding/spread/book-depth/liquidation model. Full one-minute trade ledger and monthly summaries, include no-trade months.

## Prior research and novelty decision
- `scripts/research_ema20_second_touch.py` and `analysis/ema20_second_touch_20261121/`: exact same causal entry signal, but *ATR initial stop, BE at 1R, trailing at 2R*. This fixed 2:1 200/100 exit is economically different.
- `scripts/research_eth_native_atr_price_action.py` and `analysis/ethusd_native_atr_price_action/`: completed candle EMA pullbacks and ATR-based ETH exits; not second touch intrabar and not dynamic ex-ante scaled BTC-equivalent fixed stop.
- `scripts/research_new_1h_patterns_stage19.py` and `analysis/institutional_discovery_stage19_new_1h_patterns/`: completed hourly EMA confirmation versus our distinct touch count.
- Other fixed point models in `scripts/research_daily_200_500_points.py`, `analysis/delta_1m_exit_research/`: different entry thesis.

**Decision: PARTIAL OVERLAP — approved differential**: isolates influence of fixed point 2:1 exit holding user-prescribed new EMA second-touch entry constant. One pre-registered TP/SL combination, no grid fitting.

## Data, validation, limitations
Read and hash-verify 22 contiguous 1-minute monthly partitions per asset; do not interpolate. UTC data begins Jan 1 2025, so first 330 minutes of Jan 2025 IST unavailable. Use previous minute BTC close, never future BTC for ETH sizing. 2026 previously researched; **not** an untouched holdout. 1-minute OHLC is not tick order flow; actual limit/stop execution may differ. November 2026 is incomplete and excluded. Results must be labelled simulated and not live-ready.
