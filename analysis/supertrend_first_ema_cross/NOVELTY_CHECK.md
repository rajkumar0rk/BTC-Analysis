# Pre-run novelty check — Supertrend FIRST, EMA9/21 crossover SECOND

Date 2026-11-22. Decision: **NEW causal entry signal** (corrects the previous user-specified strategy, not mere parameter re-tuning).

## Exact frozen signal rules

For each independently tested time frame (5 minutes, 15 minutes, 1 hour):

- Compute Supertrend using Wilder ATR(10), multiplier 3.0, and exponential moving averages EMA9 and EMA21 from completely closed OHLCV candles. Warm up at least 100 complete candles.
- **LONG:** Supertrend bullish on the **previous** completed candle AND remains bullish on the **current** completed candle, AND EMA9 crosses **from <= EMA21 on the preceding completed candle to > EMA21 on the current completed candle**. Execute BUY at the very next true 1-minute OPEN.
- **SHORT:** Supertrend bearish on both the **previous** and **current** completed candles, AND EMA9 crosses **from >= EMA21 on the preceding completed candle to < EMA21 on the current completed candle**. Execute SELL at the next true 1-minute OPEN.
- No entry on a Supertrend flip alone, and **exclude simultaneous Supertrend switch plus EMA crossover** because Supertrend must have become favorable FIRST. Do not trigger simply because EMA9 is above/below EMA21. Do not enter twice without another fresh EMA crossover.
- Entry only after closed-timeframe signals; no current/incomplete higher timeframe candle data. Long/short, 7 days/week, one position per test case.

## Existing research compared / causal novelty

- Previous `analysis/supertrend_ema921/` on `research/supertrend-ema921-20261122` entered on ANY **fresh combined alignment**: Supertrend flipping into an already-aligned EMA condition could initiate a trade. This is **different**; the present entry requires a **fresh EMA crossover strictly after Supertrend is already favorable**.
- `analysis/supertrend_ema921_fixed_grid/` and `analysis/supertrend_ema921_rr_ratios/` tested parameter grids, but still used fresh alignment instead of a subsequent crossover. Their results must not be relabeled as results for this corrected strategy.
- `analysis/ema921_1h15m5m_rr/` and `analysis/ema921_fixed100_200/` used 1H & 15M EMA-only confirmation and 5M EMA crossover, NOT same-timeframe Supertrend-first entry. They do not establish the performance of the exact conjunction.
- `analysis/independent_stage25_hourly_trend/` on `research/stage25-new-trend` uses hourly breakout/inside-bar/momentum signals rather than this sequential indicator pattern.

## Fixed exits, costs and data: unchanged

- Research source: authentic Delta Exchange India BTCUSD futures candles `data/delta_india/BTCUSD/1m`, Jan 2025–Oct 2026 IST inclusive; 2025-January IST first 330 minutes unavailable. November excluded as incomplete.
- Backtest each independent 5M, 15M, and 1H signal on the entire source. Real 1-minute stop/target first touch, adverse stop-first handling for same-minute ambiguity, stop gaps at one-minute OPEN; take profit and stop distances measured from the *adverse-slip adjusted* entry fill. Do not use incomplete higher-timeframe highs/lows to infer hit order.
- Compare all previously requested 1:3 multiples (100/300,150/450,200/600,300/900,400/1200,500/1500,600/1800,800/2400,1000/3000) and 1:4 multiples (100/400,200/800,300/1200,400/1600,500/2000,600/2400,800/3200,1000/4000), plus reference 100/200, 200/2000 and 1000/2000 (20 unique pairs, **60 independent simulations**).
- One position at a time; new signals during a position ignored, no reentry until next fresh crossover. Flat all open trades at IST month boundary to evaluate monthly account returns. 1x compounded notional exposure.
- Per-side assumed taker fee 0.05% with GST 18% on fees, adverse $5 BTC-price-point slip per side. Include all modeled costs. No live bid/ask, order book, funding, liquidation, margin or market impact model.
- Output all 60 summary variants, 22 calendar IST monthly returns each, complete trade ledger, signal counts, source quality, drawdown and separate 2025 vs Jan–Oct 2026 outcomes. Record unsuccessful candidates; no fitting after outcomes.
- This is an exploratory historical screen; both 2025 and 2026 data have already been examined in past work, no untouched forward holdout. Positive outcomes could arise from multiple testing and do NOT demonstrate live edge.

## Initial unit tests to enforce the corrected order

- If both Supertrend and EMA crossover happen on the same completed candle, **do not signal**.
- If Supertrend becomes bullish when EMA9 is already above EMA21, **do not signal**.
- If Supertrend was bullish on the prior bar and remains bullish when EMA9 newly crosses above EMA21, **signal LONG**.
- Apply strictly symmetric SHORT logic.
- If EMA9 stays above EMA21 without a crossover, **do not signal**.

Analysis output namespace `analysis/supertrend_first_ema_cross/`; preserve all old reports on their research branches.
