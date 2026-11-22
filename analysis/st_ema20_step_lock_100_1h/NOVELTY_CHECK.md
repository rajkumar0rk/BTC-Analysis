# BTCUSD EMA20/Supertrend: 100-point stepped profit-lock — novelty gate

Date: 2026-11-22. Decision: **PARTIAL OVERLAP — user-requested non-R stepped profit lock**, rather than another fixed target or initial structure stop.

## Fixed entry rules
- Reuse unchanged 1H Supertrend (ATR10, multiplier3), EMA20, touch/reclaim/combined entry definitions, and 1m following-hour breakout trigger from `research/st-ema20-rr-grid-profit-protected-20261122:scripts/backtest_supertrend_ema20_rr_grid_profit_lock.py`.
- One completed 1H signal then one 1m breakout fill per Supertrend cycle; no overlapping trades or repeat entries.
- Model fixed 0.001 BTC futures quantity, $100 illustrative cash, taker 0.05%/side + GST 18% (0.00059), 5 BTCUSD price points adverse slippage on each side.

## Changed exit hypothesis
User asks to "100 point as lock profit protection and then we increase that". Implement a **stepwise ratcheting profit stop** that first locks +100 BTC price points from actual fill after sufficient favorable movement, then raises lock by another 100 for every additional 100 favorable points of the running 1m high (LONG) or low (SHORT).

Three independently tested activation profiles (rather than guessing a single ambiguous trigger): favorable excursion >= +150, >= +200, >= +300 to first lock +100; then for each additional complete +100 favorable move beyond activation, increment locked profit +100. Example activation 200: favorable +200 -> lock +100; +300 -> lock +200; +400 -> lock +300. Stop only moves in profitable direction.

**Causality:** 1m bar high/low may trigger new lock only after that 1m bar completes. The *existing* lock is checked first in the next 1m bar. A lock cannot trigger and exit from the same 1m candle's extreme retroactively; check no high/low of entry candle for a same-minute lock, and no guaranteed fill after a gap below/above lock. No initial stop and no R-based exits.

Two independent target options: (a) **uncapped** with only step-lock stop or confirmed 1H Supertrend reversal exit, and (b) cap profit at **+1000 BTC points** before the next step, else lock or ST flip. For a TP/active-lock double-touch in same 1m candle choose lock first (conservative). On a completed 1H ST flip, exit at next 1m open before candle's lock/TP checks, mirroring baseline.

18 scenarios: 3 entries (touch/reclaim/combined) × 3 activation points × 2 target caps. Historical 1m delta data Jan 2025 to 2026-11-20, revalidate complete archive. Report fee-adjusted PnL, gross, PF, wins, drawdown, monthly IST exit-month results, exit reasons, individual trades, optional open position unrealized only. **No liquidation, funding, real orderbook, spread, delays, margin or real-world stop-fill certainty**. Particularly without initial SL, adverse moves may liquidate before profit lock activates.

## Closest previous evidence
- `research/st-ema20-tp-profit-protection-20261122:analysis/ema20_st_fixed_tp_protection_1h`: +200/500/1000 fixed target and fixed post-activation non-ratcheting lock 50%/75% of TP; different stop update dynamics.
- `research/st-ema20-rr-grid-profit-protected-20261122:analysis/ema20_st_rr_grid_protected_1h`: 12 fixed-point initial SL:TP ratios; never executes this no-initial-stop 100-point stepped lock.
- `research/st-ema20-reversal-only-20261122:analysis/ema20_st_reversal_only_1h`: no stop/TP, fallback only Supertrend reversal.
- `research/ema20-supertrend-1h-touch-reclaim-1m-20261122:scripts/backtest_supertrend_ema20_1h.py`: 1.5R one-off breakeven and 2R swing stop, not 100-point stepping.

Months were previously researched, thresholds are exploratory not validated out-of-sample. Nov 2026 partial. No guarantee of monthly or live profitability.
