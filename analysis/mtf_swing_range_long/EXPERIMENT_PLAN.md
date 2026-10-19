# Stage 5 — 30m confirmed uptrend + 1m swings/ranges, with versus without session/timezone filters

## Requested hypothesis
When the last **completed** 30-minute BTCUSD candle establishes a bullish regime, can long entries around confirmed **1-minute swing highs/lows and range highs/lows** generate positive *net* futures returns? Compare trading at any hour to timezone-local sessions without pretending session-filtered results are independent.

## Fixed methodology before results
- Venue: genuine Delta Exchange India **BTCUSD futures 1m** OHLCV history available in this repository. No invented L1/L2 or fills.
- 30m candle trend, two separate (predefined) definitions:
  1. bullish last completed 30m candle: close > open AND close > previous completed 30m close.
  2. HHHL structural uptrend: last two **fully completed** 30m candles are bullish in structure: newer high > prior high, newer low > prior low, newer close > prior close, newer close > newer open.
- 1m swing high/low: local 7-candle fractal pivot, with 3 candles to its left and **3 later completed candles to its right**. A pivot becomes usable *only after* the three confirming candles have closed. Carry latest confirmed pivot forward; do not use future pivots.
- Range high/low: highest high and lowest low of previous 5 or 24 **completed 1m** candles, excluding signal candle. Do not use current-minute high to define breakout level.
- Long entry setups evaluated on completed 1m candle: (a) 5m or 24m range-high break, (b) confirmed-swing-high break, (c) combined confirmed-swing-high + 24m range-high break, (d) 24m range-low sweep and close reclaim while near a confirmed swing low. Every entry is next available 1m OPEN, never signal close.
- For all setups, swing low and/or prior range low provide an executable structure stop. Long stop under the **nearest confirmed historical support** (range low or confirmed swing low) minus 5 BTC points; for a sweep/reclaim the stop is below signal-candle sweep wick/historical support. Reject setups with stop distance <60 or >500 points. This exclusion is predetermined.
- Two management rules: take profit 1.5R or 2R, structure stop, 120m maximum hold (exit at next available 1m OPEN when timed out), conservative stop-first if both stop and target touch within a minute. No overlapping positions within any one strategy; no artificial one-per-day cap.
- Cost: 0.05% taker fee EACH SIDE plus 18% GST on fees; 5 BTC-price-points adverse slippage on entry and exit; calculate gross and net BTC-price-point equivalents. No assumption that fills occur at historical best quotes; gaps through stop must worsen fill, not improve it. No funding cashflow modeled; prevent opening a trade whose full possible 120-minute lifetime crosses a hypothetical 00/08/16 UTC settlement.
- Time treatment:
  - ALL_UTC: every hour and every day, no timezone/session filter
  - WEEKDAYS_ALL: Monday-Friday UTC, no clock filter
  - NY_OPEN: weekdays 09:30–12:00 local America/New_York, automatic US DST
  - LONDON_OPEN: weekdays 08:00–11:00 local Europe/London, automatic UK DST
  - ASIA_SINGAPORE: weekdays 09:00–12:00 Asia/Singapore
  - INDIA_MORNING: weekdays 09:00–12:00 Asia/Kolkata
  Session membership is evaluated at **entry time**; stops/exits may continue outside the session.
- Results per strategy for chronological 2025 (research), Jan-Jun 2026 (chronological validation), Jul–Oct 17 2026 (previously investigated recheck **not untouched OOS**).
- Save all attempted strategy-period combinations, zero-trade configurations, cost-vs-gross contrasts, drawdown, profit factor, traded days, sample size, full trade ledger as compressed CSV, UTC entry/exit and NY-local session alignment.
- Never select a strategy based on Jul-Oct then call Jul-Oct untouched. All variants exploratory; repeated selection and 1m OHLC fills may overstate reliability.

## Interpretation
The words "uptrend" and "swing high/low" admit multiple definitions, so the definitions above are frozen and explicitly recorded rather than changing after seeing outcomes. This is a **LONG-only** BTC perpetual futures backtest; it is not market-neutral arbitrage and cannot guarantee profits.
