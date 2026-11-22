# Preregistered 1H EMA20 first-touch filtered TP1R strategy — 2026-11-22

User's latest follow-up: "**1H**" after completed filtered 15M TP1R test; the only parameter changed is **signal timeframe from 15M to 1H**. All entry, filters, target and stop settings remain consistent.

## Exact fixed setup
- BTCUSD and ETHUSD futures independent tests, 1H Supertrend Wilder ATR(10) multiplier3 and 1H EMA20. 1-minute OHLC execution/monitoring.
- Wait for a **confirmed 1H Supertrend flip**; ignore the flip candle, then enter on the **first subsequent 1H candle** whose 1-minute price touches the **last completed 1H EMA20**. If the first touch fails a filter, reject that epoch; no second-chance second touch.
- Entry filters: **the previous fully CLOSED 1H candle's volume > 1.2 × SMA20(1H volume)** AND **the previous fully CLOSED 1H Wilder ATR(14) > SMA20(ATR14)**. Thus no use of in-progress or future 1H candle's volume or volatility.
- Long only in green ST direction, short only in red, one trade per ST cycle.
- At EMA-touch entry, snapshot last closed 1H Supertrend line. Reference `R = side * (executed entry - last completed ST line)`; invalid risk geometry suppresses the trade. Fixed TP = entry + direction × **1R**.
- **No hard stop at the line**, no fixed-price stop, no trailing. The ONLY routine stop-loss is *confirmed opposite 1H Supertrend flip* and execution at next hourly candle's first 1-minute opening price.
- Same source/fees as last study: Jan2025–Oct2026 (22 IST months), verified Delta India BTC+ETH 1m OHLC, $1,000 initial 1x modeled equity each, taker 0.05% per side and GST18%, adverse 0.02% slippage each side. Long/short both sides, no weekday filter, one position per asset/timeframe.
- Two hypothetical inside-minute paths, O→H→L→C and O→L→H→C, model uncertain entry minute ordering. These are not tick data nor bounds.
- Monthly mark-to-market, net return, trade win/loss, PF, max floating drawdown, exit reason breakdown, first touch rejection counts. No funding, margin/liquidation, spread/depth or latency model; already-researched 2026 is not untouched holdout.

Closest baseline: `analysis/st_firsttouch_15m_filtered_tp1r_20261122/`, 15M filtered TP1R. Also separate prior unfiltered 1H TP2R `analysis/st_firsttouch_ema20_tp2r_stflip_1h15m_20261122/`. This is a requested **timeframe differential**, not a parameter sweep. Novelty gate: PARTIAL OVERLAP approved.
