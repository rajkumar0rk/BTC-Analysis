# Previous-day range & confirmed previous swing research — preregistered

User asked to research **previous-day range high/low** and **previous confirmed daily swing high/low** on Delta Exchange India BTCUSD futures, particularly whether these price-action levels offer a profitable intraday setup.

## Fixed definitions and chronology
- For UTC day D, **RH** = actual high of UTC day D-1 and **RL** = low of UTC day D-1; today's ongoing prices must not enter either level.
- **SH** = latest *confirmed* DAILY swing-high whose center day is strictly earlier than yesterday; **SL** = corresponding swing-low. A daily pivot has 2 neighboring daily candles on each side (5-day fractal) and is known only after both right-side days fully close. The last available confirmed pivot is forward-carried into D; if no prior pivot exists, no trade. Strict equality to 5-day rolling max/min is allowed for ties. This means an old swing high/low may persist many days.
- Base daily boundary is **00:00 UTC**, without guessing New York/India chart midnight; entry sessions, by contrast, use local DST-correct clocks. Alternate daily boundaries are future research, not mixed into this study.
- Test both **LONG and SHORT**, each with four causal signals:
  1. LONG: close above RH, SHORT: close below RL (previous-day range breakout).
  2. LONG: touch below RL and close back above RL on bullish candle; SHORT: sweep above RH and close back below RH on bearish candle (previous-day range sweep/rejection).
  3. LONG: close above confirmed SH, SHORT: close below confirmed SL (older confirmed daily swing breakout).
  4. LONG: sweep confirmed SL, then bullish close above it; SHORT: sweep confirmed SH, then bearish close below it (older swing rejection).
- Breakouts require the *previous completed entry-timeframe candle close* at/below (LONG) or at/above (SHORT) the level. Rejections require wick beyond level and completed close back inside it. No pending 5m/15m candle or future pivot information allowed.
- Evaluate entry signal on fully completed **1m, 5m or 15m** bar. Execution next entry-timeframe candle open (next underlying 1m OPEN). No forward price movement in indicators.
- Exits fixed BTC price-point offsets from modeled execution fill, user-familiar **(SL100,TP200), (SL200,TP400), (SL300,TP600), (SL400,TP800) [1:2]**, **(SL300,TP900), (SL400,TP1200) [1:3]**; hold maximum **120 or 240 minutes** (compare). Stop-first on intraminute OHLC ambiguity; adverse gap-through-stop at 1m open; 5 BTC-point adverse entry and exit slippage; 0.05% taker fee per side plus 18% GST. No margin/liquidation simulation or L1/queue depth.
- To avoid claiming missing funding cashflows, eliminate entries whose possible full 120/240m holding interval crosses a nominal 00,08,16 UTC settlement, consistent with earlier studies; this is conservative exclusion, not a funding model.
- Entry windows: ALL_UTC (24/7), NY_OPEN weekdays 09:30–12:00 New York local, LONDON_OPEN weekdays 08:00–11:00 UK local, INDIA_MORNING weekdays 09:00–12:00 India local; local DST correct. Entry only; positions can exit after window ends.
- Chronological periods: 2025 train, Jan–Jun 2026 validation, Jul–Oct 2026 previously inspected recheck (**not pristine holdout**). Configurations are tested without post-result tuning.
- Configuration-period results: 2 directions x 4 setups x 3 signal timeframes x 4 sessions x 6 exit pairs x 2 max-hold lengths x 3 periods = **3,456 rows**. Many configurations overlap; do not add cross-configuration trades or count positive correlated combinations as independent evidence. Store entry/exit ledger gzipped, ALL rows (including zero trades), fees/gross/net, PF/win, drawdown, trade frequency, skip counts, quality.
- Report selected **one-setup** results for validation vs other periods, at least 25 trades as indicative minimum; explicitly expose sparse-result cases and weak gross/net significance. Zero-trade days are allowed. No live trading.
