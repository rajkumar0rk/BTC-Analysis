# Novelty gate — 1H BTCUSD EMA20 RECLAIM filtered by volume & volatility
Date 2026-11-22. **Decision: PARTIAL OVERLAP (user-directed)**. The signal filters and indicator formulas already studied for Touch, but Reclaim is a materially different completed-1H entry formation with different 227 entry candidates and materially different baseline P&L. Do not assert Touch results transfer to Reclaim. Same thresholds on Reclaim are an informative controlled cross-entry comparison, not a new indicator invention.

## Closest related experiments
- `research/st-ema20-touch-volume-volatility-grid-20261122:analysis/st_ema20_touch_volume_volatility_grid_1h/` — identical 1H volume/ATR filters on Touch only, 1,344 conditions x 8 exits x 2 paths. No Reclaim filter data.
- `research/st-ema20-large-percent-profit-locks-20261122:analysis/st_ema20_large_percent_locks_1h/` — same 1H Reclaim entry and independent OHLC-executed trades with UNFILTERED volume/volatility, 0.14–10% exit tests, two paths.
- `analysis/institutional_discovery_stage7_time_volume/` and related stages — prior volume/volatility research on other signals.
- `codex/STRATEGY_NOVELTY_GATE.md` inspected.

## Locked strategy and execution for comparison
BTCUSD perpetual, Delta India historical 1-minute OHLCV 2025-01-01–2026-11-20; Supertrend(10,3), EMA20 on completed 1H; **EMA20 RECLAIM** signal (after previous adverse close relative EMA, signal candle closes back in favorable direction). Following-hour 1m breakout through previous completed signal candle high+0.5 (long) or low-0.5 (short). One entry per ST cycle. Reject the original precomputed first candidate if filter fails and **do not substitute a later Reclaim entry in same cycle**. No changes to entry fill, profit locks or Supertrend-reversal fallback. Test 8 frozen percent lock configurations: 0.14%,0.5%,0.75%,1%,2%,5%,1→2→5%,2→3→5%. Locks immediately when touched on the hypothetical 1-minute path (both open-high-low-close and open-low-high-close). 0.001 BTC size, $100 illustrative equity, 0.05% taker fee x1.18 GST each side, 5 BTCUSD-point adverse slippage each side. No initial SL. Funding, margin, liquidations, tick chronology, stop amendment latency excluded.

## Filters and parameters frozen before evaluation
Use **signal hour** data only, known at completion prior to following-hour entry, computed with preceding bar histories:
- Volume relative to mean preceding 20 completed 1H candles: vol_min 0,0.5,0.75,1,1.25,1.5,2; vol_max unlimited or 2.5.
- 1H ATR(10) / last signal close in %: min 0,.35,.5,.75,1,1.25; max unlimited,1.25,1.75,2.5.
- ATR(10) expansion relative to mean prior 20 valid completed 1H ATRs: min 0,.9,1.1,1.3.
1,344 parameter combinations x 8 exit configs x 2 intraminute paths = 21,504 sensitivity results, with missing active feature rejected and missing inactive feature ignored. Compare volume-only, volatility-only, combined, unfiltered; preserve unfiltered reference 227 entries if all-off. Require ≥35 trades and ≥12 annual trades in both 2025/2026 Jan–Oct, rank by lower of two simulated path net results, report 2025 vs 2026, win rate, realized DD, 22 complete IST exit months.

### Explicit transfer tests from previous Touch study
Evaluate the prior Touch "balanced" filter **volume ratio ≤2.5 AND ATR% ≤1.25**, keeping the Reclaim 2→3→5% ladder; also Reclaim reference without filters. These transfer settings are predefined and avoid treating optimized Reclaim settings alone as trustworthy.

## Analysis limitations
This is extensive in-sample parameter mining on known history. Positive filtered backtests don't prove live performance. Regime splits are not pristine future holdout. 1m OHLC cannot reveal true stop/target sequence; paths are assumptions. Real stop fill latency, funding, liquidation, mark and spread risk absent. Do not merge master or deploy.
