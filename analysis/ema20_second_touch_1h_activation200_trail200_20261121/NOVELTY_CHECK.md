# Preregistered 1H EMA20 second touch — activate trailing at +200, trail distance 200

Date 2026-11-21. User clarified prior "200 point with trailer points" meant **activation profit 200 BTC price points, THEN trailing distance 200**, NOT 200 TP + always-active 200 trailing. This is a distinct configuration.

## Entry unchanged
- BTCUSD and ETHUSD Delta India 1m backtest through Oct 2026, 22 months Jan 2025–Oct 2026 IST.
- 1H EMA20 and Supertrend(10,3) on completed 1H bars. Ignore Supertrend flip candle, count two distinct later 1H EMA20 touches, enter immediately when second candle's 1m OHLC touches last-closed 1H EMA20. One entry per Supertrend direction epoch, one position concurrently per asset; no 1H volume/volatility filters.
- 1x evolving $1000 initial equity separately for BTC/ETH, 0.05% taker fee each side plus GST 18%, adverse 0.02% slippage each side; data SHA verified with no missing minutes within Jan 2025 UTC–Oct 2026, first 330 IST minutes Jan not covered. No funding, actual bid/ask, liquidation, orderbook, latency, or tick sequence.

## Exit rules exactly
- NO fixed take-profit; +200 is **only** trailing activation threshold.
- Before favorable price moves by 200 BTC price points from entry: NO active trailing stop, NO separately specified fixed stop-loss, NO Supertrend reversal exit or timeout. A position may suffer unlimited or unbounded floating losses (especially shorts).
- At favorable excursion >= +200 BTC points, activate a 200 BTC point distance trailing stop. For LONG, trail = best observed favorable high - 200; SHORT, trail = best observed favorable low + 200. It never retreats. At first activation exactly +200, trail is at entry (gross breakeven, before costs). ETH activation and trail BOTH scaled to ETH price by `200 * ETH entry / prior completed 1m BTC close` and frozen per trade, not identical absolute ETH points.
- For any minute with an active prior stop: check if that stop is hit FIRST, exiting at worse of 1m open or previous stop plus adverse slippage. Only if not exited update best high/low and trailing level from completed 1m candle for the NEXT minute.
- Entry minute: don't credit favorable high/low for activation (intra-minute crossing order unknown); no stop before activation. Starting with later minute, if activation and newly computed trail are both spanned on SAME 1m candle, **pessimistic ambiguity treatment** = assume activation then retrace to new trailing stop, fill at that stop within that minute, rather than crediting a guaranteed winning continuation. Do not use this 1m bar OPEN for activation-minute gap filling because it predates the activation.
- If activation on a 1m candle but new stop not touched, lock trail for next minute. If already active and new highs/low span tighter new trail, tightened level becomes effective only next minute. This asymmetry is documented and both sequence assumptions are approximations without actual tick data.
- End of Oct-2026 leftover positions hypothetically force-closed for reporting only and included in marked net result, not a live exit.
- Track TP exits as **zero**, exits via activation trailing stop, never-activated positions at sample end, maximum intratrade adverse excursion, monthly MTM equity, min hypothetical equity, downside insolvency, duration, fees and drawdown.

## Novelty / most similar runs
- `analysis/ema20_second_touch_1h_tp200_trailing200_20261121/` is the **incorrectly interpreted** prior 200 TP and immediate 200 trailing; BTC -48.12%, ETH -47.22%.
- `analysis/ema20_second_touch_1h_one_trade_per_st_20261121/` is the 200 TP only, no trailing, no stop: BTC +4.92% (huge floating DD), ETH +18.42% (equity below zero).
- `analysis/ema20_second_touch_1h_atr3_20261121/` is trailing 3xATR with stop from entry, no fixed point activation.

Gate **PARTIAL OVERLAP — APPROVED distinct user-specified activation and distance**. No parameter optimization and no selective positive-only reporting; previously studied 2026 is not untouched out-of-sample.
