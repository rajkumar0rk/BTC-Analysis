# Novelty check — volume and volatility conditioning of 15m Supertrend touch

Date: 2026-11-22. Decision: **PARTIAL OVERLAP — differential explicitly requested**.

## Exact earlier baseline
- `scripts/research_supertrend_15m_line_touch.py` and `analysis/supertrend_15m_touch_20261122/RESEARCH_REPORT.md` on `research/supertrend-15m-touch-20261122`.
- It simulated a 15m Supertrend(ATR10, 3) bullish flip, first subsequent touch at last completed 15m support level, one long per bullish cycle, 15m closing stop, and 0.2/0.4/0.5/0.6/1.0% price take-profits using 1m historical prices. The complete 22-month baseline was negative at every target.
- Other closest: `scripts/research_trend_pullback_breakout_stage13.py` (4H/1H/15M directional pullback, not ST limit touch), `analysis/institutional_discovery_stage24_structure_monthly10/RESEARCH_REPORT.md` on `research/stage24-monthly10` (15m retest, but different entry/stop).

## Incremental hypothesis (not a new core strategy)
Can *known-at-order-placement* 15m volume and ATR volatility regime conditioning improve fill selection and net results compared with the exact **unfiltered** baseline?

**Trading rules:** All original signal/entry/exit rules are unchanged. One long trade at most per bullish Supertrend cycle. A first touch that fails a filter is skipped and future support touches in the same bullish cycle remain eligible based on new, fully closed 15m bars. The volume/volatility filters are evaluated using the most recent **completed** 15m candle, never the still-building touch candle.

- Relative volume for the latest closed 15m candle = its volume / mean volume of the 20 **earlier** closed 15m candles. Compare: off, >=1.0, >=1.25, >=1.5, >=2.0, <=0.8.
- Volatility ATR14 on completed 15m candles, Wilder RMA. Compare: off; ATR14/close as a percentage >=0.10%, >=0.20%, >=0.30%, >=0.40%; ATR14 relative to mean of preceding 50 ATR14 values >=1.25 or <=0.8. Only past closed bars.
- Full cross-product of 6 volume conditions × 7 volatility conditions × 5 fixed TP targets = 210 combinations. No other filter, no weekday restriction, no short positions.
- One-limit-fill/gap-aware replay on Delta Exchange India BTCUSD 1m OHLCV; 15m stop at next 1m open; no same-entry-minute take-profit. Fees: 0.05%/side + 18% GST, 5 USD adverse slippage per side. All combinations compare against the unfiltered result and report 2025 only (training), 2026 H1 check, Jul–Oct previously observed, full 22 complete IST months; no untouched OOS remains.
- Include negative/null results and 0-trade month count, win rate, drawdown and minimum sample count for ranking. **This is an ablation of a known negative strategy, not a fresh independent strategy hypothesis.**

## Integrity gates
Validate 1m data continuity; compare the unfiltered optimized replay's trade count/wins/gross/net to the previously committed baseline before interpreting conditioned variants. If mismatch, fail loudly. Keep results and code on a separate research branch; never merge without user request. No automatic parameter optimization using 2026 as training; full-grid report retained. No leverage/margin/funding/order-book simulation: report BTC price-point-equivalent PnL, not actual account equity percentage.