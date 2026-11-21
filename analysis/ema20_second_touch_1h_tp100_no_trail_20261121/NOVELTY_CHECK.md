# Pre-registered 1H one-trade-per-Supertrend EMA20 second-touch: TP100, no stop and no trailing

Date: 2026-11-21. Exact change requested: BTC take-profit **100 USD price points**, replacing earlier TP500 (and comparable TP200); ETH has independently scaled price target equal to **100 * ETH entry price / prior completed 1m BTC close**, frozen at entry. ETH does not use identical 100 USD points.

Keep every other rule fixed: Supertrend (10,3), last COMPLETED 1H EMA20, ignore Supertrend flip bar for touch counting, count touches in distinct subsequent 1H candles and enter immediately when the second candle's 1m OHLC crosses frozen EMA20. One trade per confirmed Supertrend direction cycle and one position at a time per asset; once entered, cannot enter again in the same epoch even after target until Supertrend flips. No 1H volume/volatility gates (15M-only filters remain separate).

Exit policy: TP-only, NO initial/fixed SL, NO ATR trailing, NO breakeven, NO Supertrend reversal exit, NO time exit. Only at final 2026-10-31 observation forcibly close a still-open position for accounting and clearly flag end-of-sample; such artificial exit is NOT a viable live exit. Favorable TP may be hit beginning one 1m candle AFTER entry, never on same minute, to avoid assumed intra-minute ordering. Conservative adverse slippage assumed 0.02% at both entry/exit; fees 0.05% taker each side plus 18% GST. 1× of evolving equity notional, starting $1,000 separate account/asset. Compare trade count, TP hit count, month-end mark-to-market, hypothetical insolvency and worst drawdown. Original 1m Delta India OHLC histories BTCUSD and ETHUSD Jan 2025–Oct 2026, 22 IST months, SHA verified, no missing later minutes (Jan 2025 first 330 IST minutes not in UTC-start archive). Actual spread/depth/funding/margin calls/forced liquidations not modeled.

## Novelty and closest baseline
- `analysis/ema20_second_touch_1h_tp500_no_trail_20261121/` (same entry, TP500, no SL or trailing, one per Supertrend) — direct source to change only target price.
- `analysis/ema20_second_touch_1h_one_trade_per_st_20261121/` (same entry, TP200, no SL or trailing, one per Supertrend) — second comparator.
- `analysis/ema20_second_touch_1h_atr3_20261121/` is ATR trail (now disabled). `analysis/ema20_second_touch_fixed_tpsl_20261121/` uses fixed SL and repeated trades; NOT same exit model.

**Gate decision: PARTIAL OVERLAP — approved targeted differential**. No parameter sweep or selected positive-only reporting. 2026 has been repeatedly studied and is not untouched out-of-sample. A high TP-exit hit rate without SL can mask enormous open losses, prolonged holding and liquidation.
