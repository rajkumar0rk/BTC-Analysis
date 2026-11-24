# BTCUSD ST Locked V1.0: separately optimize monthly wins by leg

Baseline verified against 22 per-leg months, 85 exclusive trades:
Line Touch 14/22 positive months +13,816.06 net points;
Bullish Flip 12/22 positive months +5,283.56 net points.
Combined +19,099.62 net points, 17/22 profitable months.
9 inactive/no-trade months for Flip are FLAT, not losses.

## Strict individually profitable-month and combined non-degradation
Condition: no reduction in the profit of any historically positive
month of that leg OR combined portfolio; no decrease in total
net profit of leg or combined. The other leg retains exact rules.
| variant              | changed      |   touch_monthly_wins |   flip_monthly_wins |   changed_leg_winning_months_gain |   touch_net |   flip_net |   combined_net |   changed_leg_profit_months_degraded |   combined_profit_months_degraded | passes_all_hard_constraints   |
|:---------------------|:-------------|---------------------:|--------------------:|----------------------------------:|------------:|-----------:|---------------:|-------------------------------------:|----------------------------------:|:------------------------------|
| baseline             | none         |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| SL_0.75_TP_1.5       | line_touch   |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| SL_0.75_lock_1.0_0.4 | line_touch   |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| SL_2.0_TP_0.5        | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| SL_2.5_TP_0.5        | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| SL_3.0_TP_0.5        | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.45_0.0        | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.45_0.025      | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.45_0.05       | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.45_0.075      | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.45_0.1        | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.45_0.15       | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.45_0.2        | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.45_0.25       | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.45_0.3        | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.5_0.0         | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.5_0.025       | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.5_0.05        | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.5_0.075       | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.5_0.1         | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.5_0.15        | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.5_0.2         | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.5_0.25        | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.5_0.3         | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.5_0.4         | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.6_0.0         | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.6_0.025       | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.6_0.05        | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.6_0.075       | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.6_0.1         | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.6_0.15        | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.6_0.2         | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.6_0.25        | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.6_0.3         | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |
| lock_0.6_0.4         | bullish_flip |                   14 |                  12 |                                 0 |     13816.1 |    5283.56 |        19099.6 |                                    0 |                                 0 | True                          |

## Extra winning months but with tradeoffs (NOT eligible to lock)
| variant   | changed   | touch_monthly_wins   | flip_monthly_wins   | changed_leg_winning_months_gain   | touch_net   | flip_net   | combined_net   | changed_leg_profit_months_degraded   | combined_profit_months_degraded   | passes_all_hard_constraints   |
|-----------|-----------|----------------------|---------------------|-----------------------------------|-------------|------------|----------------|--------------------------------------|-----------------------------------|-------------------------------|

## Research limitations
2025 and 2026 have already been used in model construction.
This is an in-sample exit-parameter sensitivity grid, NOT
independent OOS, and optimizing one historical loss can overfit.
Increments 0.01 BTC point from rounding permitted, no funding,
margin liquidation, depth or live order latency.
