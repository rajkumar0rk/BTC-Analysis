# Preregistered incremental BTC/ETH 1H EMA second-touch experiment — 500-point TP, no trailing

Date: 2026-11-21

## Exact user change

Take existing 1H Supertrend(10,3) + EMA20 second-touch 1m replay, **one entry per Supertrend cycle**. Change favorable fixed take-profit from 200 BTCUSD price points to **500 BTCUSD price points**, no fixed stop-loss, **NO ATR trailing or other trailing**, no breakeven, no Supertrend flip exit, and no time exit. ETH target is BTC-equivalent fraction from the previous completed 1-minute BTCUSD close at its entry: `ETH target price distance = 500 * ETH entry / prior BTC 1m close`, frozen at entry. One independent position per asset, one entry per Supertrend direction epoch; never reenter until the confirmed direction flips, even if fixed TP was already reached. Ignore Supertrend flip bar for touch counting, count one touch per distinct later 1H candle. Immediate entry modeled at frozen last completed 1H EMA20 on a 1m OHLC crossing, not candle-close entry.

Use original `scripts/research_ema20_second_touch_1h_one_trade_per_st.py` unchanged apart from exact target-distance parameter and output paths/report labels. Retain 1-minute OHLC monitoring; no TP on entry minute because intra-minute price order unknown. At last minute of October 2026 data close any remaining open trade **FOR REPORTING ONLY**, labelled sample-end; show month-end MTM and maximum adverse floating drawdown. User did not request a regime-based exit. The fixed TP is the only normal exit.

Data and execution held identical: original validated Delta Exchange India BTCUSD/ETHUSD 1m 2025-01 UTC through 2026-10-31 18:29 UTC; 22 IST months Jan 2025–Oct 2026, first 330 minutes Jan IST unavailable due UTC start, no minute gaps. Assumed $1000 per asset independent starting equity, 1× evolving equity notional, fee 0.05% taker each side plus 18% GST, 0.02% adverse slippage per side; no true bid/ask, funding, margin liquidation, order book or latency. No prediction or guaranteed profitability.

## Novelty gate and baseline

Closest is `scripts/research_ema20_second_touch_1h_one_trade_per_st.py` with BTC 200 point TP and ETH % counterpart, **no SL or trail**, same one trade per Supertrend. Earlier 200 TP results: BTC +4.91815% with 57.6724% MTM max DD, ETH +18.41904% but **104.6488% MTM drawdown and negative account equity** (non-tradable in a real margin setting).
Other `scripts/research_ema20_second_touch_1h_atr_trail.py` (2x ATR14) and `scripts/research_ema20_second_touch_1h_atr3.py` (3x ATR14) use ATR trailing stops, now intentionally removed. `scripts/research_ema20_second_touch_fixed_tpsl.py` uses both 200/100 exits and repeated entries.

Decision **PARTIAL OVERLAP — approved targeted differential** to compare 500 TP vs 200 TP without misleading returns. No parameter sweep, no use of 2026 as pristine validation (examined repeatedly). Report positive and negative outcomes with mark-to-market, insolvency flags, forced end-of-sample positions.
