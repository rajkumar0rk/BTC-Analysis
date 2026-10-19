# Stage 5 SHORT mirror — 30m downtrend, 1m swing/range breakdown, fixed 3R exits

This file pre-registers the SHORT counterpart of the completed Stage 5 LONG research. Preserve the LONG study untouched and compare equivalent setups and sessions.

## Directional reversal of the tested setup

- Bearish 30m regime from the **last fully completed** 30m bar, either:
  1. bearish_candle: close < open and close < preceding completed 30m close
  2. ll_lh_structure: newer 30m low < preceding low, newer high < preceding high, newer close < preceding close, newer close < its open
- The same 7-bar 1m swing detector: 3 left-hand and **3 subsequently completed** right-hand candles; confirmed pivots only.
- 1m SHORT setups: prior-5-candle low breakdown; prior-24-candle low breakdown; confirmed swing-low breakdown; combined swing-low and range-24 low breakdown; 24m range-high sweep and close rejection while close < open and near confirmed swing high (the exact bearish mirror of long range-low reclaim).
- Signal on completed 1m bar; SELL at following 1m OPEN minus 5 points assumed adverse slippage. No intrabar or incomplete-30m lookahead.
- Four user-specified fixed SL/TP BTC-point pairs: (100,300), (200,600), (300,900), (400,1200). Stop **ABOVE SHORT fill** by SL points and target **BELOW SHORT fill** by TP points; buy-to-cover incurs 5 points adverse slippage.
- Intrabar stop wins when target/stop both hit. If candle opens past stop, exit at adverse gap open. Max 120 minutes, otherwise buy-to-cover at minute-120 open.
- Futures taker fee 0.05% each side and GST 18% on fee, as in LONG research. No imaginary spread, queue, maker fills, or funding receipts. Exclude entries with possible settlement in the full 120m lifespan (same filter).
- Compare ALL_UTC, WEEKDAYS_ALL, NY_OPEN 09:30–12:00 America/New_York, LONDON_OPEN 08:00–11:00 Europe/London, ASIA_SINGAPORE 09:00–12:00, INDIA_MORNING 09:00–12:00. DST as relevant.
- Chronological periods: 2025 training; Jan–Jun 2026 validation; July–Oct 17 2026 known previously researched recheck (not independent holdout).
- Save all 2 regimes × 5 signals × 6 sessions × 4 exits × 3 periods = 720 rows, including zero trades; ledger gzipped, fee/gross/net returns, drawdowns, counts and best validation tables.
- Compare to historical LONG study only as descriptive diagnostics. Cross-variant rows are correlated, cannot be added together; no claim of profitable or executable system without replicable positive net evidence. No live orders.
