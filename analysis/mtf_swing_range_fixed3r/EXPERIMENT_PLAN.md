# Fixed-price 3R exit test: BTC 30m uptrend + 1m swings/ranges

Study design frozen before examining fixed-exit results.

## User-specified changes to step 4
- Fixed stop/target BTC price-point pairs: **SL 200 / TP 600**, **SL 100 / TP 300**, **SL 300 / TP 900**, **SL 400 / TP 1200**. Each is a 3:1 gross reward-to-risk target; results include fees/slippage.
- Every position closes no later than 120 minutes after entry. For an unfilled SL/TP use the next available 1m OPEN at minute 120; stop hit wins intraminute ties.
- Fixed stop/target levels are calculated from *entry execution fill* (next 1m open plus 5 BTC points of adverse entry slippage); exit slippage another 5 points; Delta India taker fee 0.05% per side with 18% GST; stop gap worsens fill. Funding cashflows not reconstructed; new entries touching a scheduled funding timestamp in their full possible 120m window are excluded.
- All other signal definitions identical to the existing Stage 5 script: completed 30m bullish candle or completed 30m HHHL regime; one-minute previous 5 or 24 candle range break, confirmed 7-bar swing high break, combined swing/range high breakout, and range-low sweep/reclaim.
- Trade next 1m OPEN only after confirmed 1m candle close; **no** future knowledge of the 30m current candle or swing pivots.
- Separate 6 session subsets evaluated: ALL_UTC, WEEKDAYS_ALL, NY_OPEN (09:30–12:00 America/New_York), LONDON_OPEN (08:00–11:00 Europe/London), ASIA_SINGAPORE (09:00–12:00), INDIA_MORNING (09:00–12:00 Asia/Kolkata). Exchange 1m bars remain UTC; US/UK daylight-saving rules applied.
- 2025 train; January–June 2026 validation; July–17 October 2026 previously inspected recheck (not globally untouched).
- All 720 strategy x exit x session x period combinations saved, including zero-trade rows. Trade ledger in gzipped CSV; net/gross mean points, win rate, PF, average fees, max sequential realized drawdown, durations and counts.
- Independent configurations reuse the same data and often the same underlying events; never aggregate P&L across them. Historical OHLC does not confirm real executable bid/ask fills.
