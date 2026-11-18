# Stage 26 novelty check — signed realized semivariance exhaustion

**Decision: PARTIAL OVERLAP — approved differential.**

## Predeclared experiment
This tests **the imbalance of upside vs downside realized squared returns over the preceding 32 completed 15-minute bars**, not absolute range, trend EMA, price breakout, or simple 1m high-volume candle. A counter-direction trade is considered only when one semivariance side exceeds the other by a factor of 2 or 3, and the most recently completed 15-minute bar is in the same direction as the dominant semivariance. Enter opposite to that dominant side at the next 1m OPEN, not before the signal bar closes. Use stop distance 1.5 or 2.5 times the last completed 15m rolling mean true range (14 bars); fixed profit 2 times stop distance; maximum holding 240 minutes; stop-first on ambiguous 1m bar; only one position at a time; flatten at IST calendar month end.

Parameters: imbalance threshold {2,3}, stop ATR multiplier {1.5,2.5}; 4 variants. No 2026-based parameter tuning. Risk 1% equity per trade with 3x notional cap, modeled 0.05% per-side taker + 18% GST, 5 USD/BTC adverse slippage each side. Initial notional collateral model is approximate; lot size, funding, actual spread and impact not known.

## Closest existing research
- Stage 7 time/day/volume/volatility: uses range/volume and fixed TP/SL; does **not** test directional *squared-return semivariance imbalance* on completed 15m bars.
- Stage 9 adaptive direction: supervised closed-price/volume features and classifier, not this explicit variance asymmetry threshold and mean-reversion trigger.
- Stage 19/23 broad 5m: EMA, RSI2, sweep, compression, engulf, breakout, portfolio blends; no same semivariance trigger.
- Stage 24 (research/stage24-monthly10): 15m structure breakout/retest/squeeze; distinct entry cause.
- Stage 25 (research/stage25-new-trend): 1H trend, inside-bar breakout, momentum acceleration; distinct signal and side.
- Stage 2/3 OI/expansion: participation/positioning, not this price-only realized semivariance.
- Funding carry: different venue/hedge economics.

The general reversal premise overlaps earlier studies, so this is an incremental causal hypothesis, not a proven independent edge.

## Data and validation
Base: original Delta India BTCUSD 1m gzip partitions, Jan 2025–Oct 2026, **from research/oct31-raw-repair**. Verify every UTC minute and October 2026 SHA from manifest before execution. Signal uses 15m bars only after full completion. Evaluate 2025 as training/ranking, then fixed 2026 recheck. Historical 2026 was already seen in other projects; not a pristine out-of-sample test. IST month boundaries. November 2026 excluded. Initial IST January 2025 is missing the first 05:30 hours because the raw archive begins at UTC Jan 1; flag incomplete coverage rather than claiming perfect 22 months.

## Gate
Proceed with isolated test; do not reuse previous scripts' results or overwrite earlier research.
