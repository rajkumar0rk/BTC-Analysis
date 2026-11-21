# Novelty gate — 1H second-touch EMA20 with ATR-only trailing exit
2026-11-21. Research branch: research/ema20-second-touch-1h-atr-trail-20261121

## Pre-registered hypothesis, exact change
Keep user's most recent 1H entries: Supertrend(10,3) confirmed at completion of each 1H candle, ignore the flip candle; after a flip, count at most one EMA20 touch per DISTINCT subsequent 1H candle; when the SECOND eligible candle's 1m high-low touches the last COMPLETED hourly EMA20, enter immediately (no 1H candle-close confirmation), in Supertrend direction. One entry max per Supertrend direction epoch; mark the epoch as traded at entry so no reentry after a stop until a later confirmed reversal. Only one position per asset. No 1H volume or volatility gates; 15M filters are NOT transferred.

**Exit rule**: NO fixed take profit. NO separately imposed fixed percentage/point SL, breakeven, Supertrend reversal exit, or timeout. Use an ATR trailing stop ONLY:
- ATR(14) on fully COMPLETED 1H candle (same causal hourly indicator as original), multiplier 2.0. ATR distance recalculated at the last completed 1H bar as 2*ATR, never from incomplete 1H bar.
- At entry initialize the trailing stop to entry minus 2*ATR for long, entry plus 2*ATR for short. This is an initial protective stop **as part of ATR trailing**, not a separate fixed SL. (Without initial protection, a "trailing only" method is underspecified.)
- For LONG, after each full 1m candle whose prior active stop was not hit, best high is updated; next trailing stop=max(previous stop, best high-2*last-closed-hour ATR). SHORT similarly, stop=min(previous stop, best low+2*ATR). Stops never retreat; ATR changes can tighten or keep the stop, not loosen.
- On any 1-minute bar: test PREVIOUSLY ACTIVE stop first (long low<=stop, short high>=stop); fill at the worse of stop and that minute's opening price, plus 0.02% adverse exit slippage. Only if not stopped update best and stop effective for **NEXT 1-minute bar**. Entry-minute adverse stop event is counted conservatively; entry-minute favorable wick is NOT used to tighten the stop due unknown intra-minute event ordering.
- At end Oct 2026 mark open position for accounting and label explicit SAMPLE_END, not a planned exit. Trade can remain open across Supertrend flips (flip resets entry allowance but does NOT force exit).

Both BTCUSD and ETHUSD same 2×ATR on their respective hourly USD prices: no fixed point scaling for ETH (unlike earlier fixed TP200/SL100 studies). Delta Exchange India original SHA-checked contiguous 1-minute candles 2025-01 through 2026-10 (22 IST months). UTC data begins Jan 1, so 330 first minutes of January IST absent. 1× evolving account notional, $1,000 per asset initial, fees 0.05% taker each side plus GST on fees 18%, adverse slippage 0.02% per side. No actual spreads/funding/margin/liquidation/latency/LOB. Monthly mark-to-market equity includes open floating P&L; min wick equity and worst drawdown tracked. 2026 already historically explored and **not untouched test**. No tuning sweep; single locked 2×ATR choice.

## Closest previous studies and differential
1. scripts/research_ema20_second_touch_1h_one_trade_per_st.py and analysis/ema20_second_touch_1h_one_trade_per_st_20261121/: same entries and one-per-cycle, but TP-only 200 BTC point/equivalent ETH, no stop. Direct comparator.
2. scripts/research_ema20_second_touch_1h_no_sl.py and analysis/ema20_second_touch_1h_no_sl_20261121/: TP-only entry allows reentry within same Supertrend epoch.
3. scripts/research_ema20_second_touch.py and analysis/ema20_second_touch_20261121/: same EMA20 second touch with ATR stop and breakeven/2R trailing **without** one trade per Supertrend.
4. scripts/research_ema20_second_touch_fixed_tpsl.py: same entry with fixed 200/100 price exit.

**Novelty decision: PARTIAL OVERLAP — approved controlled exit differential.** Specifically removes fixed TP and implements always-active 2×ATR trail with explicit intraminute conservative execution and per-cycle lockout. Report all assets whether result good or bad.
