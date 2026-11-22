# Supertrend EMA9/21 RR-ratio robustness extension — novelty gate

Date: 2026-11-22. Decision: **PARTIAL OVERLAP — approved differential robustness audit**.

## Why execute this follow-up?
The previous fixed TP/SL robustness grid on `research/supertrend-ema921-fixed-grid-20261122` has already tested 162 cases, including 100/300, 200/800, 500/1500, 500/2000 and 1000/3000. **Never rerun those pairs**. The user's newly requested 200/600 (2:6), as well as several untested proportional 1:3 and 1:4 settings, are absent. This is NOT a novel strategy or an independent edge discovery. It is a narrowly scoped *sensitivity interpolation/audit* requested by the user, with output clearly marked reused vs newly computed. No new data, signal, execution or economic regime is claimed.

## Frozen sample and deterministic configuration
- Exactly same original entries as `scripts/research_supertrend_ema921.py`: Delta India BTCUSD futures, Supertrend Wilder ATR(10) x 3 + EMA9/21 same-timeframe alignment, 5M/15M/1H independently, next available 1m OPEN after fully closed candle.
- Source: `data/delta_india/BTCUSD/1m`. Jan 2025–Oct 2026 IST. Jan 2025 missing 330 minutes at start; all other months complete. Reject any source minute gap. No fabricated bars.
- One open trade at a time. Only a fresh indicator conjunction transition can initiate entry. No indicator exit for fixed TP/SL. No arbitrary max trades/day. Entries allowed seven days.
- Fixed stop and target in BTCUSD PRICE POINTS **from adverse-slippage-adjusted entry fill**; actual 1-minute OHLC checks; if TP and SL both touched in same minute, favor SL; stop gaps at next open.
- Month-end position flatten for account monthly return. 1x compounded notional, 0.05% per-side taker fee + 18% GST, $5 adverse slippage each side. No actual spread/depth, maker model, funding, liquidation or margin.
- Test **1:3 multiples** (SL,TP): (100,300), (150,450), (200,600), (300,900), (400,1200), (500,1500), (600,1800), (800,2400), (1000,3000).
- Test **1:4 multiples**: (100,400), (200,800), (300,1200), (400,1600), (500,2000), (600,2400), (800,3200), (1000,4000).
- Reuse exact existing output for 5 previously tested pairs. Compute the 12 previously UNTESTED pairs on 5/15/60m (36 fresh configurations); publish a combined table of 51 configurations, marking origin of every row.
- Report trade count, wins/losses, win rate, profit factor, net PnL after all modeled costs, compounded 1x account return, trade-close maximum drawdown, monthly returns by IST, counts of winning/losing months, and trade ledgers for newly computed variants.
- All results use historical data already investigated: **no untouched out-of-sample validation**. Testing additional variations increases selection bias. Do not make deployment or reliability claims.

## Closest existing work
1. `analysis/supertrend_ema921_fixed_grid/` on `research/supertrend-ema921-fixed-grid-20261122`: identical signal and pricing model, 162 fixed-stop and target variants. Preserves existing rows; different additional ratio steps being audited only.
2. `analysis/supertrend_ema921/` on `research/supertrend-ema921-20261122`: fixed 100/200 and indicator exit on identical entries.
3. `analysis/ema921_fixed100_200/` on `research/ema921-fixed100tp200-20261122`: 1H/15M/5M EMA-only MTF signal, not the same-timeframe Supertrend/EMA signal.
4. `analysis/independent_stage25_hourly_trend/` on `research/stage25-new-trend`: different 1H signals (momentum/Donchian/inside bar) and exits.

No revision of previous results, no re-tuning of entries based on 2026, and no code merges into main.
