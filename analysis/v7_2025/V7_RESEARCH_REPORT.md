# V7 — 2025 BTC structural trend research

**Research only: event labels, not realized trades. No 2026 data used.**

Signal: completed 1H close beyond 12 preceding completed 1H bars, closing in the outer 25% of candle range.
Confirmation: two successive fully completed 4H higher-high/higher-low (LONG), or lower-high/lower-low (SHORT) candles.
Variant: breakout body >= 0.4 x completed 1H ATR14.
Outcome: next hourly OPEN reference; +1,000 favorable points before -500 adverse, within 24/48 hours. If both levels hit in one hour, count adverse first.
Last 48 hours of December are censored because reading January 2026 is forbidden.

## Detection by cohort

| Cohort | 24h signals | 24h hits | 24h % | 48h signals | 48h hits | 48h % |
|---|---:|---:|---:|---:|---:|---:|
| breakout_acceptance_all | 643 | 190 | 29.55 | 643 | 198 | 30.79 |
| breakout_and_4h_structure | 170 | 52 | 30.59 | 170 | 56 | 32.94 |
| breakout_structure_and_body | 151 | 47 | 31.13 | 151 | 50 | 33.11 |

## Monthly 24h detection

| Month | Acceptance hits / signals | 4H structure hits / signals | 4H + body hits / signals |
|---|---:|---:|---:|
| 2025-03 | 21/69 (30.43%) | 10/25 (40.0%) | 9/23 (39.13%) |
| 2025-04 | 12/57 (21.05%) | 3/17 (17.65%) | 3/15 (20.0%) |
| 2025-05 | 14/65 (21.54%) | 4/22 (18.18%) | 4/20 (20.0%) |
| 2025-06 | 19/69 (27.54%) | 4/16 (25.0%) | 4/13 (30.77%) |
| 2025-07 | 24/68 (35.29%) | 6/23 (26.09%) | 5/21 (23.81%) |
| 2025-08 | 18/73 (24.66%) | 4/15 (26.67%) | 3/11 (27.27%) |
| 2025-09 | 22/70 (31.43%) | 10/15 (66.67%) | 8/13 (61.54%) |
| 2025-10 | 24/63 (38.1%) | 4/15 (26.67%) | 4/14 (28.57%) |
| 2025-11 | 22/69 (31.88%) | 5/15 (33.33%) | 5/14 (35.71%) |
| 2025-12 | 14/40 (35.0%) | 2/7 (28.57%) | 2/7 (28.57%) |

## Limitations
- Signals can overlap; event-hit rate is not a real strategy win rate.
- No fee, slippage, funding, account sizing, portfolio overlap, or exchange fill modeling.
- 1H intrabar stop/target ambiguity scored adverse-first.
- Must build and backtest executable rules before any profitability conclusion.

