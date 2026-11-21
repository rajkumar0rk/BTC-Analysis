# Pre-registered differential: 3×ATR14 vs 2×ATR14, 1H second EMA20 touch
Date: 2026-11-21. Research only, not a deployment.

**Single change:** Replace 2×ATR(14) with 3×ATR(14), evaluated from last COMPLETED 1H candle as a causal ATR trailing distance for BTCUSD and ETHUSD. Apply both to initial protective ATR-based trailing level and subsequent trailing adjustments. All other inputs, code, evaluation period and assumptions held constant.

Entry: Supertrend(10,3) confirmed on completed 1H bars; ignore the flip candle, count first and second touches on distinct subsequent 1H candles, enter immediately on second touch at frozen last-closed-1H EMA20 (identified using 1m OHLC). Only one entry per Supertrend direction cycle, no reentry after trailing stop until confirmed opposite flip; one live position per asset, independent capital. No 1H volume or volatility filters.

Exit: No fixed TP. No separate fixed SL. 3×ATR14 initialized at entry as stop in trade direction and monotonic trailing thereafter. On each 1m bar, check previously active stop before updating from favorable 1m extremes. Updated stop only effective next minute, and no favorable first-entry-minute wick assumed. Gap fills at adverse 1m open; slippage 0.02% adversely on both sides. Stop can be hit on entry minute, using stop-first conservative ambiguous 1m rule.

Dataset original SHA-validated Delta India 1m BTC/ETH from 2025-01 UTC through 2026-10-31 18:29 UTC, 22 IST months (Jan 2025 misses first 330 min, November 2026 incomplete). $1000 independent initial equity, 1× evolving-equity notional, fee 0.05% per side plus GST 18%; no funding, order book, latency, real spread, actual exchange liquidation/margin. Output all trades, month-end marked-to-market, drawdown and consistency. Historical 2026 data previously researched; no pristine OOS.

## Prior comparable studies
- `analysis/ema20_second_touch_1h_atr_trail_20261121/`, `scripts/research_ema20_second_touch_1h_atr_trail.py`: exact same setup, 2×ATR14: BTC −55.30835%, ETH −66.21535%. Controlled baseline.
- `analysis/ema20_second_touch_1h_one_trade_per_st_20261121/`: same 1H entry lockout and TP-only exits (no stop), different economic rule.
- `analysis/ema20_second_touch_20261121/`: EMA second touch with multiple entries and conditional ATR/breakeven.

**Novelty: PARTIAL OVERLAP — approved differential**: Single user-specified 3×ATR change, no broad parameter sweep or positive-only reporting. The wider trail may change fill sequence, so trade counts may differ. This report must not imply live profitability.
