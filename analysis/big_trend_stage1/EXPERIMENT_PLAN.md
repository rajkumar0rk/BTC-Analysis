# Big-trend-only BTC research — preregistered before running

## User goal
Prefer fewer high-conviction intraday BTC opportunities capable of delivering large wins over frequent small scalp trades; zero-trade days are acceptable, but do NOT impose an arbitrary daily one-trade cap.

## Historical universe
Genuine Delta Exchange India BTCUSD 1m OHLCV history (`data/delta_india/BTCUSD/1m`), January 2025 through October 17, 2026. No executable bid/ask archive: all fills are approximations. Historical open-interest/funding series are available but are NOT used to assert executable fills or to fabricate settled payments.

## Preset structural candidate family, no post-result parameter tuning
- Directional bias from completed **1-hour** candles. Two alternatives: (1) three consecutive closes in direction plus last closed candle body in trend direction; (2) last two consecutive 1h higher-high/higher-low [LONG] or lower-high/lower-low [SHORT] with final body in direction. Never use the open 1h candle in a signal.
- On a fully completed **5-minute** bar, look for close beyond highest high / lowest low of **previous 12 or 24** completed 5m bars. Require the preceding completed 5m close to have been on the other side of the frozen level. Breakout candle should be directional with body >=50% of its high-low range.
- Compare (A) no further qualifier vs (B) **volatility compression and volume confirmation**: width of 6 completed preceding 5m bars < 0.75 × median preceding 72 same-length widths, and breakout volume >=1.2 × average 5m volume over 24 preceding completed bars.
- Compare entry modes: (A) immediately following closed 5m breakout, (B) first subsequent **completed** 5m retest within 3 bars: touches original breakout boundary (within 0.2 × breakout signal ATR14), then closes back outside it in trend direction. Enter at the next 5m open in both cases. Retests may have no trade; do not pretend the retest was known on breakout.
- Stops: frozen 5m ATR14 × 1.2 with bounds 180–450 BTC points; profitable exits (A) fixed 3R, (B) 5R with stop tightened to entry only **on bars after** reaching 2R and to +1.5R after reaching 3R. Four-hour hard exit (240m) if neither SL nor TP has completed. Conservative intrabar stop-first and gap-through-stop, adverse entry/exit slippage 5 BTC points per side.
- 0.05% futures taker fee per side plus 18% GST on fees, exactly matching previous BTC futures studies. Fee and P&L reported in BTC-price-point equivalents, not user dollars or option-premium P&L.
- For comparability skip new trades if a possible 240-minute holding period contains a 00/08/16 UTC potential funding event; do not assert funding cashflows. This creates a significant calendar exposure restriction. No positions overlap within the same strategy.
- Evaluate **both** LONG and SHORT; no direction chosen using future bars.
- Sessions: ALL_UTC (24/7), NY_OPEN 09:30–12:00 America/New_York weekdays with DST, LONDON_OPEN 08:00–11:00 Europe/London weekdays with DST, INDIA_MORNING 09:00–12:00 Asia/Kolkata weekdays. New entry restricted only; exits can occur outside the entry window.
- Periods: 2025 training, Jan-Jun 2026 chronological validation, Jul–Oct 17 2026 **previously seen** recheck. NOT a completely untouched holdout.
- All 2 sides × 2 trend definitions × 2 breakout lookbacks × 2 compression variants × 2 entry types × 2 exits × 4 sessions × 3 historical periods = 384 rows, including no-trade; complete gzipped 1m-simulated trade ledger, chart-free reproducible program, MFE/MAE, gross/net, drawdown, costs, per-day trade frequency, data-quality checks.
- Evaluate selection bias: duplicated/overlapping variants don't independently validate each other. Reject a strategy as established unless results stay positive and survive costs across periods. Pure 1m OHLCV cannot verify live L1 fills or edge.
