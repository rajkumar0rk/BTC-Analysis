# Novelty gate: Supertrend reversal ONLY exit (2026-11-22)

Decision: PARTIAL OVERLAP — user-requested differential, not new entry alpha.

Base branch: research/ema20-supertrend-1h-touch-reclaim-1m-20261122.
Closest older files: scripts/backtest_supertrend_ema20_1h.py; analysis/ema20_supertrend_1h_touch_reclaim_1m/NOVELTY_CHECK.md and all three reports.

Keep hourly EMA20 touch/reclaim, Supertrend (10,3), next-hour confirmed-candle breakout, one filled trade per Supertrend cycle, no overlapping positions, entry structure-distance filter, 0.001 BTC, $100 starting account, 0.05% taker + 18% GST and 5 points slippage per side.

Exit ONLY at next 1m open after completed 1H Supertrend reversal; no initial stop orders, no breakeven/profit lock, no trailing stop, and no fixed take profit. End-of-archive valuation is not an actual strategy exit.

Measure one-minute close mark-to-market drawdown and MAE/MFE. Monthly results are assigned to EXIT month (corrected versus baseline entry-month convention) and so are not strictly comparable by month. Delta India BTCUSD January 2025 through November 20 2026, no missing candles according to latest manifest but revalidate actual bytes.

This experiment differs in economically significant risk exposure from prior multi-exit system. This is NOT an untouched holdout. NO modeled liquidation or funding, do not recommend trading without independent risk controls.
