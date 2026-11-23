# Novelty gate — EMA9/21 1m with higher-timeframe trend regime

Decision: **PARTIAL OVERLAP — approved incremental test**. Not repeating Stage25 (hourly entry strategy) or Stage13 (4h/1h/15m swing breakout), because 1m EMA9/21 is retained as execution trigger, with one-IST-weekday entry lock.

Closest prior experiments:
- scripts/research_ema9_21_quality_upgrade.py — 32 variants of 1m EMA9/21 + 5m/15m alignment, 5m ATR stop and bounded hold: all negative net after 0.05% taker fee/side + 18% GST and 5pt/side slip.
- scripts/research_trend_pullback_breakout_stage13.py — higher timeframe swing entry.
- analysis/independent_stage25_hourly_trend/ (research/stage25-new-trend branch) — hourly entry price-action, 1m execution.

**Fixed experiments**, chosen before observing results: two 1-minute signal families (EMA9/21 cross with completed 5m/15m trend; EMA-aligned 1m 15-bar breakout, 1.3x volume, 55% candle body), both with pre-existing thresholds. Three higher-timeframe filters applied on last completed bars: 1h EMA9>EMA21 & close>EMA9, 1h EMA9/21 + 4h EMA20/50, or 1h EMA9/21 + 1h ATR14 >= its trailing rolling 60 bar median. Mirror for shorts. Session 13:30–23:30 IST. Static stop 2.5× fully completed 5m ATR14; target 3× risk; hold limit 12h or 36h, stop-first minute-level pessimistic replay; one entry per IST weekday, no forced entry, no overlap. Exactly 2*3*2=12 fixed combinations. Full 2025 train rank, 2026 historical recheck, not untouched. 2025-01 to 2026-10 22 full UTC months, November raw tail exits permitted; no November entries. Same costs and 10% notional exposure, no leverage; no funding, spread or impact in model. 36h holdings can incur funding; do not claim fully cost-validated profitability.

Output every candidate and monthly results. Do not select on 2026; stop expanding if still negative.
