# 15M first EMA20 touch, volume+volatility gates ON, no TP, 2× / 3× ATR14 trailing

Corrected explicit user instruction 2026-11-23: **"Fixed take-profit OFF"**. Supersedes the previous 15M proposal that combined 1R / 2R fixed TP with ATR trailing. Do not present the earlier pending fixed-TP study as this request's results.

## Preregistered rules (no optimization)
- Assets BTCUSD, ETHUSD perpetual futures; 15M Supertrend (Wilder ATR10, factor3) and EMA20.
- After confirmed Supertrend flips, ignore the flip candle; FIRST subsequent 15M EMA20 touch triggers entry in Supertrend direction, recognized via 1-minute price movements using last closed 15M EMA. One attempt per ST direction cycle even if failed filters.
- **Volume filter ON**: prior completed 15M volume > 1.2×20-period SMA of completed 15M volume.
- **Volatility filter ON**: prior completed 15M Wilder ATR14 > 20-period SMA of completed Wilder ATR14.
- NO fixed take-profit or R-multiple target. Do not use ST-line distance as entry risk gate: that distance was relevant to removed TP.
- Compare 2×ATR14 or 3×ATR14 initial stop + trailing. ATR14 from last fully closed 15M candle, distance frozen at entry. LONG initial stop = executed entry−ATR_multiplier×ATR14; SHORT entry+distance. Trailing stop moves with favorable intraminute 1M price extremes, never moves backwards. Active immediately, no profit activation threshold.
- Opposite confirmed 15M Supertrend flip remains another exit at the first 1m candle OPEN of the next 15M bar, if the ATR trail has not already exited. Exit order is whichever occurs first.
- Two alternative hypothetical OHLC segment orders for each 1m candle: O-H-L-C and O-L-H-C. True intraminute tick order is unknown. Stops through gaps filled at 1m opening price; 0.02% adverse slippage both directions.
- Data Jan2025-Oct2026, 22 complete IST months, SHA-verified Delta India 1m BTC and ETH OHLC. Initial hypothetical equity $1000 per independent symbol/multiple/path, changing 1× notional. Taker fee 0.05% each side + 18% GST on fee. No funding, real spread, margin/liquidation, depth, latency or actual order replay. 2026 no longer untouched OOS.
- Output trades, wins, losses, PF, net return, profitable/losing months and monthly MTM, max floating drawdown, trailing vs Supertrend exits, data-quality and replay logs. Compare to former **15M fixed TP 1R / 2R without trailing** only with clear different exit labels, and to prior 1H variants only if useful.
- Partial overlap with earlier exploratory research; user specifically corrected exit semantics to **NO TAKE PROFIT**, so this is distinct.

Research branch only; do not merge master.
