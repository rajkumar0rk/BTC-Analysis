# Novelty check — large-percent 1H ST/EMA20 direct-profit locks (BTCUSD)
**2026-11-22 — PARTIAL OVERLAP, approved differential**. User requests testing larger **1%, 2%, 5%** profit protections after small +0.14% lock produced $3.45 cumulative net across 237 profit-stop exits in the 253-trade baseline. Earlier work tested percentages ≤1%, but **has not tested 2%, 5%, 10% levels or ladders including these** with instant same-bar updates.

## Frozen common causal rules
Copy signal, OHLC replay and fee functions from `research/st-ema20-percent-direct-lock-grid-20261122:scripts/backtest_st_ema20_percent_direct_profit_locks.py` without modification. BTCUSD perpetual Delta Exchange India one-minute OHLC (2025-01-01 to 2026-11-20), 1H Supertrend (ATR 10, 3) + EMA20 Touch, Reclaim and Combined. Signal after completed hour, fill on breakout signal HIGH+0.5 LONG / LOW−0.5 SHORT during next hour, one fill per Supertrend cycle. No initial SL, fixed TP, or timeout, Supertrend flip exits at following 1m open; same-candle direct lock at exact **price percentage of entry** and no invented rungs after the last given percent. Long/short symmetric; backtest two plausible intraminute paths O→H→L→C and O→L→H→C. Fee: 0.05% taker × 1.18 GST each side; 5 BTC price points adverse slippage per side, quantity 0.001 BTC, illustrative starting capital $100. No funding, margin, liquidation, mark, spread, tick path or order amendment latency simulation.

## Prespecified grid, no selection/revision based on 2026 monthly results
- S01: 0.14%
- S02: 0.5%
- S03: 0.75%
- S04: 1%
- S05: 1.5%
- S06: 2%
- S07: 3%
- S08: 4%
- S09: 5%
- S10: 7.5%
- S11: 10%
- L01: 0.14 → 1 → 2 → 5%
- L02: 0.2 → 1 → 2 → 5%
- L03: 0.5 → 1 → 2 → 5%
- L04: 0.75 → 1 → 2 → 5%
- L05: 1 → 2 → 5%
- L06: 1 → 1.5 → 2 → 3 → 5%
- L07: 1 → 2 → 3 → 4 → 5%
- L08: 1 → 3 → 5%
- L09: 1 → 2 → 4 → 8%
- L10: 2 → 3 → 5%
- L11: 2 → 5 → 10%
- L12: 0.5 → 1 → 1.5 → 2%
- L13: 0.14 → 0.5 → 1 → 2 → 5%

Total **24 ladders × 3 entry modes × 2 intraminute paths = 144 scenarios**. Single percentage means once the threshold is reached stop locks at that percent until exit or fallback flip. Multiple thresholds: advance stop to most recently reached percent immediately on same assumed price path, *including the entry minute*. Remain fixed at last rung if price moves beyond that. For every scenario report net USD / gross / total fees, win/loss, win rate, first threshold hits, counts reaching **1%, 2%, 5%** before final exit, stop vs flip exits, max realized drawdown, full-month profitability (22 months), monthly and per-trade output.

## Closest comparisons
- `research/st-ema20-percent-direct-lock-grid-20261122:analysis/st_ema20_percent_direct_lock_grid_1h/comparison.csv`, 26 ladders, first level ≤0.30% and terminal rung ≤1%.
- `research/st-ema20-immediate-five-lock-ladders-20261122:analysis/st_ema20_immediate_five_ladders_1h/comparison.csv`, fixed BTC points not percent.
- `research/st-ema20-reversal-only-20261122:analysis/ema20_st_reversal_only_1h/touch_trades.csv`, baseline no-lock MFE and Supertrend-only exits useful as a comparison for target reach if no early stop.

## Validation, caveats, and economic interpretation
1m OHLC cannot observe the true order of intraminute high and low. Two continuous hypothetical paths are modeled, **neither guarantees a fill at the stop or gives tick-realistic bounds**. Profit locks activated at the touched price, with zero delay assumption and 5 BTC points slippage per side. Exact 1%,2%,5% first-passage counts can vary if an earlier lock exited the trade; report each configuration separately. The original baseline produced 237 stop gains totaling only +$3.45; larger targets could raise each payoff but allow more catastrophic no-lock reversals. Prior months already optimized; no pristine out-of-sample. November 2026 partial, no live deployment and zero claim of profitability.
