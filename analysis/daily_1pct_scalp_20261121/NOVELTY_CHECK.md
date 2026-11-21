# Pre-run novelty gate — BTC one-percent-per-day net account scalp (2026-11-21)

**Decision: PARTIAL OVERLAP — approved differential (new economically meaningful, net-account 1% daily goal).** Signal families are existing price-action ideas; do not claim novel alpha. The precise account target, leverage/risk model, one-entry-per-day selection and daily return audit have NOT been answered by prior fixed-price-point studies.

## Fixed predeclared rules — no optimization

Instrument: Delta India BTCUSD perpetual, **native** 1m OHLCV, 2025-01-01 to 2026-10-31 UTC; 2026-11 excluded as partial. Use UTC candle-open labels verified against repo convention, derive complete 15m/1h bars. All signals only after candle close; entry at the same instant as the NEXT 1m open, no future lookahead. Only **one entry per IST day** between **12:00 and 19:00 IST**, exclusive open position across directions. Stop/target from actual modeled **NET account return** with 2x exposure, $10k initial synthetic equity, taker fee 0.05% per side + 18% GST, adverse $5 BTC price-point per side. Target +1.00% account equity, protective stop -1.00% account equity. Compute exact target/stop BTC price levels from notional, fill spread/slip and fees; don't confuse 1% account return with a 1% BTC price move. In ambiguous same 1m OHLC, STOP takes priority. Stop gap worse than level. Time expiry 240 minutes, forced close before IST day rollover or archive break, no carrying to a second day's account earnings. No fixed profit/loss day manipulated through wins. Long and short allowed, seven days/week (crypto).

**Trend continuation setup:** On fully closed 1h candle: EMA20 > EMA50 (long) or reverse (short). 15m candle CLOSE strictly beyond previous 8 *completed* 15m highs/lows, 15m RSI14 >58 (long) or <42 (short), 15m volume >=1.25x average of preceding 20 *completed* 15m candles, close in upper/lower 25% of 15m range in breakout direction. Need preceding 55h closed bars and no data discontinuity.

**Liquidity sweep rejection setup:** 15m bar sweeps beneath previous 12 *completed* 15m lows (long) and closes back ABOVE previous 12-bar low, plus RSI14 <38 and a positive candle (close>open); reverse short sweeps previous 12 highs, closes back BELOW, RSI14 >62, close<open. 1h EMA20/50 spread <1% of price (range-sensitive), volume >= previous 20-bar mean; candles complete, no future levels.

**Combined first-valid option:** chronological first of either trend or sweep candidate for any IST day, with trade/day and account model unchanged; no hindsight pick of winning setup. Compare all three explicitly. If both at the same minute, favor trend (fixed rule).

All setups: once daily trade reaches +1% net, close and no more trades. Once stop hit, close and no second trade. On time exit, record actual net (whether partial profit or loss), don't invent 1% win. All exits based on 1m OHLC. No funding, quote-level spread, impact, maker fill, contract rounding or mark-price liquidation. 2x leverage is not permission for live deployment.

## Prior research comparison

- `analysis/one_daily_trade_200_points/RESEARCH_REPORT.md`: deterministic forced entry each NY day, fixed +200 BTC-price-point or net-200-point targets. New experiment uses **optional qualifying entries**, 1% **account** return after costs, 2x equity exposure, and a symmetric 1% net account loss budget.
- `analysis/price_action_time_day/RESEARCH_REPORT.md` and `analysis/selective_big_move_research/RESEARCH_REPORT.md`: opening range, sweep/rejection, breakout with fixed BTC point targets and timeouts. This experiment changes account-level target/risk framing, signal conjunctions, session and daily-gate logic.
- `analysis/institutional_discovery_stage6_every_candle_200/RESEARCH_REPORT.md`: one-minute breakout and volume with fixed points. This experiment uses **completed 15m and 1h context**, fee-aware **account** exit levels and daily zero-trade accounting.
- `analysis/institutional_discovery_stage19_monthly_10pct/RESEARCH_REPORT.md` and `analysis/institutional_discovery_stage24_structure_monthly10/RESEARCH_REPORT.md` (research branch): previously tested structural patterns with different timeframes/stops/targets. New test's incremental question is 1% actual net account winning-days, not whether renamed breakout rules are alpha.

## Audit

Show all IST dates, profitable/losing/zero-trade days, days hitting **exact fee-aware +1% target**, average net on trade days, 2025 and 2026 separately, months positive/negative, full compounded net account return, peak-to-trough CLOSED-TRADE drawdown, all fees and slippage dollars, profit factor. Include 0-trade days as failures for **daily profit** goal. Confirm UTC minute gap count directly against source (previous documentation about October gap conflicts with updated manifest; never fabricate bars). This project has already researched both 2025 and 2026; 2026 is chronological *seen-data recheck*, NOT a pristine OOS holdout.

**Rule:** No post hoc modification of thresholds to manufacture +1% days; publish negative results too.
