# Supertrend + EMA9/21 fixed-stop/target grid — pre-run robustness check

Date 2026-11-22. **Decision: PARTIAL OVERLAP — approved differential, robustness/sensitivity audit ONLY**. Do not claim a new signal discovery.

## Context, novelty, and economic difference

- Existing `analysis/supertrend_ema921/` on `research/supertrend-ema921-20261122` tested **exact same entries** with 100 stop/200 TP and indicator exits. Existing 100/200 baseline was unprofitable across all timeframes. This check is **not a new strategy**; the user explicitly requested a systematic fixed-exit sensitivity grid for stability across stop/target values, to avoid presenting a single cherry-picked configuration.
- Existing `analysis/ema921_fixed100_200/` and `analysis/ema921_1h15m5m_rr/` use a *different EMA multi-timeframe signal*, without Supertrend, and therefore cannot answer this sensitivity question.
- `analysis/independent_stage25_hourly_trend/` (branch `research/stage25-new-trend`) uses hourly momentum/Donchian/inside-bar entry, not this Supertrend/EMA alignment.
- This parameter grid is a **partial-overlap robustness extension** to previously completed research, not a supposed new strategy justified by changing numbers. It is pre-registered as a single finite comparison and will preserve all unfavorable variants.

## Frozen full rules and test scope

1. Source: Delta Exchange India BTCUSD perpetual OHLCV at `data/delta_india/BTCUSD/1m/`, 2025-01 to 2026-10 IST; 2025-01 is missing first 330 IST minutes. Abort if source has other gaps.
2. Independent completed 5-minute, 15-minute, 1-hour signals from `scripts/research_supertrend_ema921.py` **unchanged**. Supertrend Wilder ATR(10) × 3; EMA9>EMA21 + Supertrend bullish LONG, inverse SHORT; fresh conjunction transition; enter next 1-minute OPEN; 100 full candles warmup. Both directions, 24×7.
3. Test all 3 × 6 × 9 = **162** runs with `SL = [100,200,300,500,800,1000]` BTCUSD price points and `TP = [100,200,300,500,800,1000,1500,2000,3000]` points. Stop/target measured from the adverse-slippage entry fill, no other exits except month/gap/end flatten.
4. Use 1-minute OHLC for first touch, assume stop first if both touched in the same minute; stop gaps fill at minute open. No intraminute path hindsight.
5. Single active position per simulation. Don't re-enter after stop/target until a **fresh** alignment transition. If an event occurs while busy, ignore it (no queue).
6. Flat at the IST calendar-month boundary for independently auditable month returns, charged on the last 1-minute close of month.
7. 1× notional compounding (no leverage), Delta taker fee 0.05% per side, GST 18% on fee, $5 adverse slippage **each side**. No funding, live spread, book impact, margin, liquidation, taxes other than GST.
8. Validation: the preexisting 100SL/200TP results **must match**, within tolerance, for each timeframe: 5M 6,922 trades and 31.39266% win; 15M 2,254 and 32.12067%; 1H 556 and 30.75540%. Otherwise **fail** the run.
9. All 22 monthly IST returns, positive-month counts, win/loss, profit factor, net 1× account return, after-cost net per BTC, and trade-close peak-to-trough drawdown reported. Select no post-hoc “best strategy” for deployment. Show max positive months, top return and worst-case month.
10. 2025 and 2026 previously used in many research tests; **none is blind out-of-sample**. The expanded parameter count raises multiple-testing and selection-bias risks. No claims of profitable live strategy or institutional validity.

New files in `analysis/supertrend_ema921_fixed_grid/`; no changes to previous research artifacts. Code runs in a separate research branch.
