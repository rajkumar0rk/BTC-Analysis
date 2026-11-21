# EMA20 second-touch, intrabar 1m entry — novelty record

Date: 2026-11-21. Branch: research/ema20-second-touch-20261121.

## Proposed rules
For each BTCUSD and ETHUSD independently, 15m and 1h separately:
- Supertrend(10,3), ATR(14) Wilder, EMA(20) on complete HTF candles.
- Ignore the HTF candle in which Supertrend flipped; its current-direction count is not incremented.
- Count EMA20 touches in distinct later HTF bars, max one per bar; reset on every confirmed flip or after entry.
- 1-minute touch: range includes the **last completed HTF candle EMA20**; LONG only while last completed Supertrend is bullish and SHORT only while bearish. Trigger on second touch with no HTF candle-close confirmation. Fill market order near EMA with adverse slippage.
- One position at once per instrument and timeframe. SL = min(2 × ATR(14), 1% of entry price). At +1R move stop to breakeven; from +2R trail 1R behind favorable extreme. No fixed TP, no opposite-flip discretionary exit. 1m stop-first / adverse handling for simultaneous OHLC extremes.
- Taker 0.05% per side + GST 18%, adverse slippage 0.02% per side, one-times notional sizing; funding/spread/depth not directly observed. No spread-less or zero-cost profitability claim.
- Jan 2025–Oct 2026, chronological 2025 vs 2026 descriptive slices, 22 completed IST months; November incomplete excluded. Non-pristine 2026 due prior extensive research. Historical OHLC cannot prove exact touch-to-order sequencing.

## Closest prior research and economic difference
- scripts/research_eth_native_atr_price_action.py and analysis/ethusd_native_atr_price_action/RESEARCH_REPORT.md: conventional completed-candle EMA pullback confirmations; not second distinct intrabar touch following a Supertrend flip.
- scripts/research_new_1h_patterns_stage19.py and analysis/institutional_discovery_stage19_new_1h_patterns/RESEARCH_REPORT.md: 1h EMA20 pullback confirmation + 1m stop-first exits; different signal, entry timing, stop/trail semantics.
- scripts/research_trend_pullback_breakout_stage13.py and analysis/institutional_discovery_stage13_4h_1h_15m/RESEARCH_REPORT.md: multi-TF trend + pullback + breakout; no Supertrend epoch touch-count state.
- Research branches research/stage24-monthly10 and research/stage25-new-trend: 15m and 1h structural entries; differ from second EMA20 touch intrabar and independent Supertrend epochs.

## Novelty decision
**PARTIAL OVERLAP — approved differential**. A narrower follow-up to EMA pullback family; second eligible HTF touch in the same confirmed Supertrend regime and immediate frozen-EMA 1m entry are the meaningful changed causal components. Not a renamed existing complete-candle EMA pullback.

## Data/validation
Repo manifests show BTCUSD and ETHUSD authentic exchange 1m partitions for Jan 2025–Nov 2026. Source hashes/counts/contiguity must be verified at run. UTC 2025-01-01 start omits first 330 minutes of Jan 2025 IST. Latest BTC October partition reports 0 missing minutes (older novelty gate text refers to an earlier incomplete October snapshot). Month scoring uses IST, complete Jan 2025–Oct 2026; 2026 is already explored, not untouched holdout. No hyperparameter search for this requested exact-rule test.
