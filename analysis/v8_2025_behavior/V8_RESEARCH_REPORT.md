# V8 — Reverse-engineering real BTC big moves (2025)

**Descriptive discovery and causal-entry opportunity labels; NOT a profit-tested strategy.**
Data: Delta India BTCUSD futures 1-minute candles, January–December 2025; evaluated March–December.

## A. What big trends actually occurred?

Trend legs are defined by a hindsight zigzag on 1m CLOSE with a 1,000-point reversal.
Legs are considered *confirmed* only after the opposite 1,000-point reversal.
The pivot start and end are retrospective labels, NOT knowable trade entry locations.

| Size threshold | Confirmed legs | Median hours to extreme | Biggest leg (pts) |
|---|---:|---:|---:|
| 2,000+ pts | 444 | 7.1 | 9424.5 |
| 5,000+ pts | 35 | 8.0 | 9424.5 |

## B. Could we enter BEFORE the move?

From each completed 1H close, evaluate both sides against the next 24/48h on 1M OHLC:
Reach +2,000 or +5,000 BTC points before −1,000; if same minute, loss first.
This is **not** realized trade P&L. Every hourly candidate, including failures, is counted.
Comparison split: March–August vs September–December 2025. Both are previously studied data.

### Mar-Aug_2025 — Weekdays IST only

| Completed-bar signal | Candidates | +2,000 first / 48h | +5,000 first / 48h |
|---|---:|---:|---:|
| baseline_all_hours | 6250 | 29.38% (1836) | 7.02% (439) |
| momentum6 | 2235 | 29.71% (664) | 6.76% (151) |
| day4h_alignment | 1330 | 25.04% (333) | 10.45% (139) |
| accepted_12h_breakout | 301 | 26.91% (81) | 5.65% (17) |
| range_volume_impulse | 314 | 28.98% (91) | 6.69% (21) |
| trend_and_breakout | 73 | 26.03% (19) | 8.22% (6) |
| trend_and_pullback | 86 | 22.09% (19) | 8.14% (7) |
| trend_and_impulse | 63 | 26.98% (17) | 7.94% (5) |

### Sep-Dec_2025 — Weekdays IST only

| Completed-bar signal | Candidates | +2,000 first / 48h | +5,000 first / 48h |
|---|---:|---:|---:|
| baseline_all_hours | 4130 | 31.16% (1287) | 8.45% (349) |
| momentum6 | 1506 | 30.08% (453) | 7.97% (120) |
| day4h_alignment | 815 | 32.64% (266) | 14.97% (122) |
| accepted_12h_breakout | 204 | 31.86% (65) | 7.84% (16) |
| range_volume_impulse | 235 | 31.91% (75) | 8.94% (21) |
| trend_and_breakout | 48 | 35.42% (17) | 12.5% (6) |
| trend_and_pullback | 42 | 38.1% (16) | 11.9% (5) |
| trend_and_impulse | 49 | 34.69% (17) | 12.24% (6) |

### All_Mar_Dec — Weekdays IST only

| Completed-bar signal | Candidates | +2,000 first / 48h | +5,000 first / 48h |
|---|---:|---:|---:|
| baseline_all_hours | 10380 | 30.09% (3123) | 7.59% (788) |
| momentum6 | 3741 | 29.86% (1117) | 7.24% (271) |
| day4h_alignment | 2145 | 27.93% (599) | 12.17% (261) |
| accepted_12h_breakout | 505 | 28.91% (146) | 6.53% (33) |
| range_volume_impulse | 549 | 30.24% (166) | 7.65% (42) |
| trend_and_breakout | 121 | 29.75% (36) | 9.92% (12) |
| trend_and_pullback | 128 | 27.34% (35) | 9.38% (12) |
| trend_and_impulse | 112 | 30.36% (34) | 9.82% (11) |

## C. Did our signal occur early in a real trend leg?

Within the first 25% of each retrospectively labelled leg (no future data in the signal itself).
| Causal condition | 2,000+ legs captured | 5,000+ legs captured |
|---|---:|---:|
| momentum6 | 144/444 (32.43%) | 15/35 (42.86%) |
| day4h_alignment | 75/444 (16.89%) | 4/35 (11.43%) |
| accepted_12h_breakout | 19/444 (4.28%) | 2/35 (5.71%) |
| range_volume_impulse | 64/444 (14.41%) | 9/35 (25.71%) |
| trend_and_breakout | 5/444 (1.13%) | 1/35 (2.86%) |
| trend_and_pullback | 13/444 (2.93%) | 2/35 (5.71%) |
| trend_and_impulse | 9/444 (2.03%) | 1/35 (2.86%) |

## D. Monthly confirmed 2,000+ / 5,000+ trend legs

| Month | ≥2,000 pts | ≥5,000 pts |
|---|---:|---:|
| 2025-03 | 73 | 4 |
| 2025-04 | 45 | 5 |
| 2025-05 | 36 | 1 |
| 2025-06 | 28 | 3 |
| 2025-07 | 37 | 1 |
| 2025-08 | 32 | 2 |
| 2025-09 | 26 | 2 |
| 2025-10 | 64 | 10 |
| 2025-11 | 63 | 4 |
| 2025-12 | 40 | 3 |

## Interpretation / limits
- Pivot catalogue is hindsight. The causal signal quality is evaluated separately from every eligible hour and BOTH sides.
- No trade is assumed to start at an ex-post pivot; a signal must exist before an outcome window.
- All 2025 is development/previously observed data, including the later-year consistency split.
- Stronger conditional success is not evidence of profitability without exclusive, real entry/exit replay after costs.
- No lookahead into 2026, funding, bid/ask, fills or liquidation modeled.
- Do not promote a condition to a trading strategy unless it beats the baseline and survives an execution backtest.

