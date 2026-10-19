# Stage 5 LONG, fixed 1:2 reward:risk — pre-registered experiment

User request: Test the LONG version of the same BTC 30m bullish regime and 1m confirmed swing/range setup using the shorter take-profit distance (1:2 instead of earlier LONG 1:3 and SHORT 1:2).

Frozen design, before seeing this experiment's results:

- Fixed BTCUSD price-point stop/target pairs: **(100/200), (200/400), (300/600), (400/800)**.
- SAME underlying Delta India BTCUSD 1m candles, from 2025-01-01 through 2026-10-17, and same 30m bullish_candle or hhhl_structure computed from the last *completed* 30-minute candle only. There is no RSI/EMA.
- SAME 1m long signals: prior 5m high breakout, prior 24m high breakout, confirmed swing-high breakout (3 left + 3 right closed candles), combined 24m/swing-high breakout, or 24m range-low sweep followed by bullish close and reclaim near confirmed swing low.
- Entry next 1m OPEN plus 5 points adverse buy slippage, stop below fill and target above fill. When both touched inside 1m, stop is conservatively assumed first. Gap beyond stop makes exit worse. Exit at 120-minute cap if neither touched. Closing adverse SELL slippage 5 points; both-side futures 0.05% taker with 18% GST. Model no real L1/L2 fills or funding cashflows; exclude possible 120-min funding settlement windows.
- SAME six session classifications: ALL_UTC (24/7), WEEKDAYS_ALL UTC, NY_OPEN 09:30–12:00 America/New_York, LONDON_OPEN 08:00–11:00 Europe/London, ASIA_SINGAPORE 09:00–12:00 and INDIA_MORNING 09:00–12:00 Asia/Kolkata. Observe local weekdays and real DST in NY and London. Sessions filter entry time only.
- Periods: 2025 training; 2026-01-01 through 2026-06-30 chronological validation; 2026-07-01 through 2026-10-17 previously examined recheck (NOT genuinely untouched independent OOS).
- 720 rows total = 2 regimes x 5 signals x 6 sessions x 4 exits x 3 periods. Save full trade ledger, complete rows including no-trade, gross/fee/net breakdown, win rate, PF and drawdown.
- Comparison with LONG 1:3 must use identical regimes, signals, costs, and session choices, especially HHHL + range5 breakout and NY opening. No retrospective change of entry logic to flatter an exit.
- This is a research simulation, not an executable edge or prediction that BTC will rise.
