# Novelty check — EMA20 + Supertrend reversal-only exit (2026-11-22)

**Decision: PARTIAL OVERLAP — approved exit-rule differential explicitly requested by user.**

## Frozen entry signals

Reuse exactly the 1H Supertrend (ATR 10, multiplier 3) and EMA20 entry logic in `scripts/backtest_supertrend_ema20_1h.py` on branch `research/ema20-supertrend-1h-touch-reclaim-1m-20261122`:
- LONG only if Supertrend green, SHORT only if red;
- touch: pullback to EMA20, completed 1H close back to trend side and no completed adverse EMA close in the excursion;
- reclaim: a completed 1H EMA close against the Supertrend followed by a completed 1H EMA close back with trend;
- entry only on next hour 1m breakout of signal 1H high+0.5 LONG or low−0.5 SHORT; fill gap-aware plus 5 BTC price points slippage.
- Compare independent TOUCH, RECLAIM, and COMBINED runs. One filled trade per Supertrend cycle. Multiple simultaneous positions never allowed.

## Changed exit hypothesis

**Remove ALL protective/target exits:** NO initial stop, NO risk(1R), NO take-profit, NO breakeven, NO trailing stop, NO time limit. Only exit an open LONG when a completed 1H Supertrend reverses GREEN → RED, or open SHORT on RED → GREEN. Exit at the next 1m open with modeled slippage. Leave the last position open if archive ends, report its unrealized P&L separately.

Do NOT filter entries by hypothetical setup stop distance or ATR-risk thresholds. ATR remains needed solely for the 1H Supertrend calculation. No R-based measurements/activations.

## Closest historical evidence and distinction

- `scripts/backtest_supertrend_ema20_1h.py` and `analysis/ema20_supertrend_1h_touch_reclaim_1m/` on base branch: *same entry* but original initial structure stop, 1.5R cost protection, 2R swing trailing, ST-flip backup exit. This new experiment isolates the stop/removal effect.
- `research/btc-ema-st-screenshot-20261119:scripts/replay_btc_ema_st_screenshot.py`: other entry implementations and exit mechanisms.
- `research/btc-tv-ema-st-screenshot-20261120:scripts/backtest_tv_ema_st_screenshot_20261120.py`: TradingView-parity study, does not replace exact current side-by-side comparison.

## Execution, quality, validation

Source Delta Exchange India BTCUSD perpetual traded-price 1m gzip partitions, Jan 2025–Nov 20 2026. Revalidate all 1m timestamps and complete hourly groups in executable code; note older novelty gate's October gap caveat predates later repair and manifest. Model 0.001 BTC per trade, $100 starting indicative equity, 0.05% taker fee per side plus 18% GST (0.00059), 5 BTC price points slippage each side. No funding, liquidation, spread/depth, broker margin or forced-liquidation model. Without initial stop, open losses may exceed account capital. Account P&L must not be presented as achievable live at $100 if margin would fail.

Monthly P&L is booked in IST **exit** month, corrects prior entry-month reporting. Show 2025 exploration, Jan–Jun 2026 seen review, Jul–Oct 2026 seen recheck, Nov 2026 partial. No untouched holdout. Include 1m intra-trade MAE and intra-trade equity drawdown caveats, as well as forced-final open position mark and recorded trades. No performance claim until GitHub workflow actually succeeds.
