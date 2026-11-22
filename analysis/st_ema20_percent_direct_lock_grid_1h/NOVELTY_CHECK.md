# NOVELTY CHECK — 1H BTCUSD Supertrend+EMA20 percentage-based immediate profit locks

Date: 2026-11-22. Decision: **PARTIAL OVERLAP — user-directed difference in percent-of-entry activation/lock instead of fixed BTC points**.

## Complete entry + position rules (frozen)
Reuse `research/st-ema20-immediate-five-lock-ladders-20261122:scripts/backtest_st_ema20_immediate_five_ladders.py` signal code **unchanged**:
- 1H ST(ATR10, 3) + EMA20, signal TOUCH / RECLAIM / COMBINED on a fully closed hour, enter first 1m breakout of signal candle HIGH+0.5 for LONG or LOW−0.5 for SHORT in following hour.
- One filled trade per Supertrend cycle. No competing positions. At completed opposite 1H ST flip, close at next 1m open.
- No initial stop-loss, fixed take-profit, timeout or extra entry filters.
- historical Delta India BTCUSD perpetual 1m OHLC, Jan 2025 through 2026-11-20 UTC; strict 1m continuity and full 1h groups validated.
- Quantity BTC = 0.001, starting illustrative account $100, fee taker 0.05% each side plus 18% GST = 0.059% each side, and 5 BTCUSD price-point adverse slippage per side. No funding/liquidation/mark-price/order-book/margin model.

## Incremental percentage exit rule
A listed value of **0.12** means **0.12%** of actual execution entry price (not 12%, not 0.12 BTC points). Immediately on favorable price reaching `entry*(1 + side*0.12/100)`, update stop to that same price; at 0.20%, stop is at +0.20% of entry, and so on. Short symmetric. NEVER delay until next candle or next milestone. Stop cannot decrease once activated, and after final listed level it remains at that level. No extrapolation. During first entry minute, process any movements only AFTER the entry event. Gap through live stop fills at worse open. Exit slippage is charged separately.

## Prespecified percentage ladders (not retrospectively selected)
- First-level-only: 0.12; 0.13; 0.14; 0.15; 0.18; 0.20; 0.25; 0.30
- 0.12→0.20→0.30; 0.12→0.15→0.20→0.25→0.30; 0.12→0.20→0.40→0.80; 0.12→0.30→0.60→0.90; 0.12→0.40→0.80; 0.12→0.50→1.00
- 0.13→0.20→0.30; 0.14→0.20→0.30; 0.15→0.20→0.30; 0.15→0.25→0.40; 0.15→0.30→0.60; 0.15→0.20→0.40→0.80
- 0.18→0.30→0.50; 0.20→0.30→0.40; 0.20→0.40→0.80; 0.20→0.50→1.00; 0.25→0.50→1.00; 0.30→0.60→0.90
26 choices × TOUCH/RECLAIM/COMBINED × two 1m price paths = **156 replays**. The 0.12% first rung is not necessarily net profitable after both fees and slippage: fee-only break-even is 0.118%, while the extra modeled 10 BTC points may push the realistic threshold nearer 0.13%.

## Intraminute assumptions and valid alternatives
Full 1m OHLC candles cannot identify ordering of H and L, so replay **both** `O→H→L→C` and `O→L→H→C` deterministic continuous paths separately. Rung activation and stop touch are applied immediately while traversing a hypothetical price segment (INCLUDING entry minute). Compare both, never claim actual tick truth, round-trip executable fill guarantees or true upper/lower tick-level bounds.

## Closest prior tests
- `research/st-ema20-immediate-five-lock-ladders-20261122:analysis/st_ema20_immediate_five_ladders_1h/`: exact 5 FIXED BTC POINT ladders and two 1m path orders, **not percentage adaptation with changing BTC price**.
- `research/st-ema20-variable-lock-ladders-20261122:analysis/st_ema20_variable_lock_ladders_1h/`: fixed price-point ladders with delayed next-bar stops, no entry-price-percent rungs.
- `research/st-ema20-rr-grid-profit-protected-20261122:analysis/ema20_st_rr_grid_protected_1h/`: fixed SL and R-based TP; no percentage activation.
- `research/st-ema20-reversal-only-20261122:analysis/ema20_st_reversal_only_1h/`: same entries and flip fallback with no profit locks, useful reference only.

## Controls + reporting
Run all 156, report net, after-fee win rate, profitable complete IST months (Jan 2025–Oct 2026; November partial), realized drawdown, stop/flip exits, hit counts for first listed rung, sum fees, and rank by net and month consistency. Record per-trade and monthly CSVs and machine-readable summary. Avoid evaluating only previously labeled winners. Historic data already inspected; no untouched holdout / forward validation. Additional platform risk: no stop update guarantees in live exchange, and no initial SL exposes losses/liquidation.
