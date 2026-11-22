# NOVELTY CHECK — EMA20 Touch volume and volatility entry filters (2026-11-22)

**Decision: PARTIAL OVERLAP — differential test specifically requested by user.** The existing entry/exit family is not novel; this experiment isolates **causal 1H volume and ATR-based volatility gating applied to previously validated EMA20 Touch entries** while keeping fixed exit replays unchanged. Previous comparison `research/st-ema20-large-percent-profit-locks-20261122:analysis/st_ema20_large_percent_locks_1h/comparison.csv` tested locks from 0.14% to 10%, none included a 1H signal-candle volume/volatility gate. Other prior research examined volume/volatility in different strategies: `analysis/institutional_discovery_stage7_time_volume/`; do not imply those results confirm these filter thresholds.

## Frozen baseline
- BTCUSD Delta Exchange India perpetual, 1-minute historical archive Jan 1 2025–Nov 20 2026.
- From `scripts/backtest_st_ema20_large_percent_locks.py`: Supertrend(10,3) 1H + EMA20 completed 1H **TOUCH** setup, entry 1m breakout above signal high+0.5 or below low-0.5 during next 1H, one filled trade per ST cycle; no lookahead.
- Preserve the **original first-fill per-cycle** entry when a filter rejects it: **SKIP that Supertrend cycle entirely**, rather than selecting a later trade. This guarantees controlled comparison of preexisting 253 candidates rather than changing entry-time behavior.
- Use **precomputed per-trade 1m replay ledger** from `analysis/st_ema20_large_percent_locks_1h`. Filtering a subset is valid because filtered trades do not interact and the engine enforced one entry per ST cycle, with exit no later than next completed ST flip. Verify trade ledgers match canonical unfiltered comparison totals.
- Keep original protective stop activation immediately on favorable price crossing each percent rung; exit on locked stop or opposite 1H ST flip; no initial stop/TP; both `O→H→L→C` and `O→L→H→C` hypothetical intraminute OHLC paths, 0.001 BTC, $100 illustrative balance, taker 0.05% each side plus 18% GST, 5 BTCUSD point slippage each side.
- Test locked profit ladders **0.14%**, **0.5%**, **0.75%**, **1%**, **2%**, **5%**, **1→2→5%**, **2→3→5%**. No optimization of the exit rung itself in this particular study.

## Features — all from completed 1H SIGNAL candle, never from entry or future 1m bars
- `volume_ratio`: signal hour total traded BTC volume / mean volume of previous 20 complete hours, i.e. `h.volume / h.volume.shift(1).rolling(20).mean()` (exclude current hour from denominator).
- `atr_pct`: 100×1H ATR10 (the existing 1H Wilder ATR from ST) / completed signal hour close; normalizes volatility to BTC price.
- `atr_expansion`: 1H ATR10 / average ATR10 of the *previous 20* completed hourly candles, excluding signal candle.
- All indicators calculated from timestamped price data up to and including signal hour close; filter decisions made before following-hour entry begins. Missing/zero/invalid indicator values **reject the entry**, not fill forward/fabricate.

## Prespecified filter grid
Volume-ratio min in {0, 0.5, 0.75, 1, 1.25, 1.5, 2}; volume max in {unlimited, 2.5}; ATR% min in {0, 0.35, 0.5, 0.75, 1, 1.25}; ATR% max in {unlimited, 1.25, 1.75, 2.5}; ATR expansion min in {0, 0.9, 1.1, 1.3}. Exclude impossible max below min. Compare no-filter, volume-only, volatility-only and both. For combined look at threshold stability, 2025 and 2026 separately, trade counts, profitable full months, max realized DD, and **worst of the two intraminute paths**; no outcome-based per-trade filter or manual removal of losing trades. Selection minimum 35 trades overall and ≥12 each year. Current 2026 historical data already inspected; cross-period validation is NOT fresh independent holdout. Publish all evaluated parameter combinations to CSV and original accepted/rejected trades for leading filters. No live strategy change.

## Required realism notes
Relative 1H volume and ATR% may not predict future movement, and historical price-volume may have data quality inconsistencies. Timeframe 1H, unit of volume source must be audited for zeros/missing. Fees use taker/taker normal rate. No funding, actual spread/stop-limit/latency, liquidation, margin, tick path. Selection across many combinations inflates overfitting risk; never claim 22/22 months unless measured. Do not merge into master.
