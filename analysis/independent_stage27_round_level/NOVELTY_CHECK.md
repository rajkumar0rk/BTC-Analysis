# Stage27 novelty gate — BTC round-number liquidity rejection

**Decision: PARTIAL OVERLAP — approved differential.** This is an independent, predeclared test of *fixed ex-ante psychological BTCUSD price grids*, rather than a rolling historical high/low, time-of-day pattern, EMA, OI, volume, 15m squeeze or realized semivariance.

## Deterministic signal and execution
On each **completed 15-minute candle**, define levels at integer multiples of USD 500 or USD 1000. Long when the previous completed 15m close is ABOVE the nearest lower grid level, the latest 15m low pierces that grid by at least USD 10, and the latest close recovers ABOVE that level, with candle low-to-level distance <= 0.8 times the **previously known** ATR(14). Short is exact reverse at the next higher grid. Use the next 1-minute open (plus 5 points adverse entry slippage), stop at 1.5 or 2.5 times last completed 15m ATR, target at 2x stop distance, max holding 240 minutes, stop-first if both stop/target touch same minute, one position, IST month-end flatten. Risk 1% account equity per trade, max notional 3x equity; no month-specific selection. The grid step (500/1000) and stop multiplier (1.5/2.5) produce four fixed variants. Choose using only 2025 positive-month count and sum of monthly net returns, then recheck unchanged in 2026.

## Closest prior experiments and differential
- `scripts/research_retest_reclaim_stage4.py` and `analysis/institutional_discovery_stage24_structure_monthly10/RESEARCH_REPORT.md` on `research/stage24-monthly10`: historical dynamic level sweeps, breaks, squeeze and retest; **not predetermined fixed absolute BTC price grid rejection**.
- `analysis/independent_stage25_hourly_trend/RESEARCH_REPORT.md` on `research/stage25-new-trend`: hourly inside bar, momentum, trend; not fixed-price psychological rejection.
- `analysis/independent_stage26_semivariance/NOVELTY_CHECK.md` on `research/independent-stage26-semivariance`: squared return imbalance; not grid-level pierce/reclaim.
- `scripts/research_price_action_time_day.py`, `scripts/research_wide_monthly_stage23.py`: session, candle, breakout, historical swing; not absolute $500/$1000 BTC grid.
- `scripts/analyze_institutional_regimes.py`: OI/funding/mark-based proxy; not grid test.
This is a different causal price reference, though general sweep-and-reclaim thesis overlaps earlier experiments. No earlier results are reused.

## Data and cost integrity
Use only original Delta India BTCUSD 1m OHLCV Jan 2025–Oct 2026 from verified `research/oct31-raw-repair` base. Verify gzip SHA256, all 963,360 original minutes, October 2026 complete. January 2025 IST first 5h30m is missing; full 22 IST-month observation therefore cannot be claimed. Model 0.05% taker per side + 18% GST, 5 BTC price points adverse slippage per side. Actual funding, spread, order-book impact, lot size, collateral/margin and liquidation cannot be validated from OHLCV and remain excluded. A fixed stop can gap. 2026 is chronologically rechecked but not pristine unseen forward data.

## Decision
Run an isolated new 4-variant backtest; archive full monthly equity ledger and negative findings. No live orders, no inference of guaranteed returns.
