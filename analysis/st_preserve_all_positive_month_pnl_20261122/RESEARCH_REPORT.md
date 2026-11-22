# BTCUSD 15m: strict no-harm profitable-month optimization

User's exact requirement: reduce the five losing months without
reducing NET POINTS in ANY of the other 17 originally profitable
calendar months (all 22 actual IST exit months).
Gate decisions are causal at each entry; baseline months may NOT
be known in live trading, so this requirement is a BACKTEST
acceptance criterion only, not a deployable month forecaster.

Baseline=+1.0% arm/+0.4% stop-lock Line Touch, 3%/0.5% Flip.
Original baseline 85 selected trades, 17/22 months, +19,099.62
BTC-equivalent points reproduced and month-by-month asserted.

## Strictly non-degrading configurations
| model                           | touch_gate                | flip_gate               |   selected |   y2025_net |   y2026_net |   total_net |   y2025_positive |   y2026_positive |   total_positive |   total_negative |   baseline_winning_months_non_degraded |   losses_to_positive |   losses_to_nonloss |
|:--------------------------------|:--------------------------|:------------------------|-----------:|------------:|------------:|------------:|-----------------:|-----------------:|-----------------:|-----------------:|---------------------------------------:|---------------------:|--------------------:|
| baseline                        | off                       | off                     |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| flip_15m_above_ema20            | off                       | 15m_above_ema20         |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| flip_15m_above_ema50            | off                       | 15m_above_ema50         |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| flip_15m_ema20_rising           | off                       | 15m_ema20_rising        |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| flip_15m_rsi50                  | off                       | 15m_rsi50               |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| flip_15m_rsi55                  | off                       | 15m_rsi55               |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| touch_1h_above_ema20            | 1h_above_ema20            | off                     |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| touch_1h_ema20_rising           | 1h_ema20_rising           | off                     |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| both_1h_rsi50                   | 1h_rsi50                  | 1h_rsi50                |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| touch_1h_rsi50                  | 1h_rsi50                  | off                     |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| flip_1h_rsi50                   | off                       | 1h_rsi50                |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| flip_weekday                    | off                       | weekday                 |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| touch_bull_age_min4             | bull_age_min4             | off                     |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| flip_bull_age_max16             | off                       | bull_age_max16          |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| touch_1h_above_ema20_and_rising | 1h_above_ema20_and_rising | off                     |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| touch_1h_above_ema20_age4       | 1h_above_ema20_age4       | off                     |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| both_prior15m_atrpct_ge_0.2     | prior15m_atrpct_ge_0.2    | prior15m_atrpct_ge_0.2  |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| touch_prior15m_atrpct_ge_0.2    | prior15m_atrpct_ge_0.2    | off                     |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| flip_prior15m_atrpct_ge_0.2     | off                       | prior15m_atrpct_ge_0.2  |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |
| flip_prior15m_atrpct_le_0.75    | off                       | prior15m_atrpct_le_0.75 |         85 |     14553.4 |     4546.27 |     19099.6 |                9 |                8 |               17 |                5 |                                     17 |                    0 |                   0 |

## Near misses: degrade up to ONE positive month
| model   | touch_gate   | flip_gate   | selected   | y2025_net   | y2026_net   | total_net   | y2025_positive   | y2026_positive   | total_positive   | total_negative   | baseline_winning_months_non_degraded   | losses_to_positive   | losses_to_nonloss   |
|---------|--------------|-------------|------------|-------------|-------------|-------------|------------------|------------------|------------------|------------------|----------------------------------------|----------------------|---------------------|

## Strictly positive months kept intact
2025-01, 2025-02, 2025-03, 2025-04, 2025-05, 2025-07, 2025-09, 2025-10, 2025-11, 2026-01, 2026-02, 2026-04, 2026-05, 2026-06, 2026-07, 2026-08, 2026-09

## Baseline five losing months
2025-06: -293.78, 2025-08: -1596.71, 2025-12: -80.79, 2026-03: -1916.69, 2026-10: -817.32

## Research integrity
All periods already used in model development, including 2026.
This high-dimensional search is a multiple-testing hazard.
Past profitable months are NOT knowable ahead of time; NEVER
deploy a calendar lookup that disables trades by realized
historical loss-month identity. If strict condition fails, say so.
No independent forward paper test; no funding/liquidation.
All returns are BTC price points per 1 BTC-equivalent position.
