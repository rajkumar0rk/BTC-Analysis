# Stage23 — Wider BTC monthly profit search including 5M orig/fade strategies

## Goal
Positive returns in every observed month of **both 2025 and 2026**,
after modeled Delta India taker fees, GST and slippage.

## Candidate sources
5585 original configurations,
4570 distinct return series, 703 selected
using ONLY 2025 training data for the real historical check.
Original Stage18 and Stage20 preserved unchanged.

## Important distinction
TRAIN2025 portfolios are fixed using 2025 alone and then tested
unchanged on 2026 (which has been exposed in prior research).
**HINDSIGHT_ALL23 and INVALID_full_hindsight_oracle are mathematical
upper bounds with future-month knowledge, NOT tradable strategies.**

## Configuration results
| name                                  |   train2025_winners |   seen2026_winners |   train2025_return_pct |   seen2026_return_pct |   minimum_fit_month_pct | historical_all_positive   |   selected_model_count |
|:--------------------------------------|--------------------:|-------------------:|-----------------------:|----------------------:|------------------------:|:--------------------------|-----------------------:|
| Train2025_35pct_anchor15pct_cap       |                  12 |                  2 |                3.86004 |              -7.26322 |                0.093319 | False                     |                      9 |
| Train2025_50pct_anchor10pct_cap       |                   4 |                  1 |                2.12547 |              -7.43018 |               -0.075621 | False                     |                     10 |
| Train2025_25pct_anchor15pct_cap       |                  12 |                  3 |                4.97273 |              -7.07403 |                0.194625 | False                     |                      9 |
| HINDSIGHT_ALL23_35pct_anchor15pct_cap |                   2 |                  2 |                0.36484 |              -1.83083 |               -0.29939  | False                     |                     13 |

## Historical full hindsight oracle (cannot be executed)
|   minimum_month_pct | all_months_positive   |   max_month_end_drawdown_pct |   prof2025 |   prof2026 |
|--------------------:|:----------------------|-----------------------------:|-----------:|-----------:|
|           -0.221297 | False                 |                       2.0662 |          4 |          2 |

## TRAIN ONLY leading configuration monthly table
| month_ist   |   modeled_return_pct | status   |   modeled_weighted_sleeve_trades |   unique_component_closed_trades |   selected_sleeves |
|:------------|---------------------:|:---------|---------------------------------:|---------------------------------:|-------------------:|
| 2025-01     |             0.093319 | Profit   |                            3.076 |                               39 |                  9 |
| 2025-02     |             0.66962  | Profit   |                            2.607 |                               32 |                  9 |
| 2025-03     |             0.350306 | Profit   |                            3.255 |                               42 |                  9 |
| 2025-04     |             0.093319 | Profit   |                            3.225 |                               40 |                  9 |
| 2025-05     |             0.093319 | Profit   |                            5.277 |                               62 |                  9 |
| 2025-06     |             0.093319 | Profit   |                            4.338 |                               56 |                  9 |
| 2025-07     |             1.4592   | Profit   |                            3.178 |                               39 |                  9 |
| 2025-08     |             0.50104  | Profit   |                            3.439 |                               44 |                  9 |
| 2025-09     |             0.093319 | Profit   |                            3.844 |                               46 |                  9 |
| 2025-10     |             0.093319 | Profit   |                            3.301 |                               42 |                  9 |
| 2025-11     |             0.169092 | Profit   |                            3.018 |                               40 |                  9 |
| 2025-12     |             0.093319 | Profit   |                            3.849 |                               50 |                  9 |
| 2026-01     |             0.0216   | Profit   |                            4.221 |                               56 |                  9 |
| 2026-02     |            -1.54798  | Loss     |                            3.678 |                               50 |                  9 |
| 2026-03     |            -0.943667 | Loss     |                            3.84  |                               49 |                  9 |
| 2026-04     |            -1.00871  | Loss     |                            4.047 |                               50 |                  9 |
| 2026-05     |            -0.347041 | Loss     |                            4.303 |                               55 |                  9 |
| 2026-06     |             0.292354 | Profit   |                            3.206 |                               39 |                  9 |
| 2026-07     |            -0.942879 | Loss     |                            3.168 |                               41 |                  9 |
| 2026-08     |            -0.428938 | Loss     |                            3.764 |                               42 |                  9 |
| 2026-09     |            -1.09914  | Loss     |                            4.545 |                               53 |                  9 |
| 2026-10     |            -1.17715  | Loss     |                            4.411 |                               54 |                  9 |
| 2026-11     |            -0.317235 | Loss     |                            2.08  |                               26 |                  9 |

## HINDSIGHT upper bound monthly returns (NOT an actual profitable pattern)
| month_ist   |   modeled_return_pct | status   |   modeled_weighted_sleeve_trades |   unique_component_closed_trades |   selected_sleeves |
|:------------|---------------------:|:---------|---------------------------------:|---------------------------------:|-------------------:|
| 2025-01     |            -0.16324  | Loss     |                            0.993 |                               27 |                 13 |
| 2025-02     |             0.434936 | Profit   |                            0.943 |                               27 |                 13 |
| 2025-03     |            -0.013383 | Loss     |                            1.278 |                               40 |                 13 |
| 2025-04     |             0.095511 | Profit   |                            1.268 |                               35 |                 13 |
| 2025-05     |             0.143183 | Profit   |                            1.539 |                               36 |                 13 |
| 2025-06     |            -0.221297 | Loss     |                            2.027 |                               46 |                 13 |
| 2025-07     |             1.25916  | Profit   |                            1.314 |                               31 |                 13 |
| 2025-08     |            -0.04092  | Loss     |                            0.898 |                               26 |                 13 |
| 2025-09     |            -0.221297 | Loss     |                            1.188 |                               30 |                 13 |
| 2025-10     |            -0.193135 | Loss     |                            1.258 |                               31 |                 13 |
| 2025-11     |            -0.221297 | Loss     |                            1.422 |                               40 |                 13 |
| 2025-12     |            -0.221297 | Loss     |                            1.052 |                               27 |                 13 |
| 2026-01     |             0.150175 | Profit   |                            1.896 |                               41 |                 13 |
| 2026-02     |            -0.109776 | Loss     |                            1.643 |                               43 |                 13 |
| 2026-03     |            -0.221297 | Loss     |                            1.509 |                               39 |                 13 |
| 2026-04     |            -0.221297 | Loss     |                            1.254 |                               32 |                 13 |
| 2026-05     |            -0.221297 | Loss     |                            1.57  |                               48 |                 13 |
| 2026-06     |             0.424652 | Profit   |                            1.689 |                               38 |                 13 |
| 2026-07     |            -0.221297 | Loss     |                            1.395 |                               41 |                 13 |
| 2026-08     |            -0.221297 | Loss     |                            1.421 |                               32 |                 13 |
| 2026-09     |            -0.221297 | Loss     |                            2.111 |                               47 |                 13 |
| 2026-10     |            -0.221297 | Loss     |                            2.641 |                               60 |                 13 |
| 2026-11     |            -0.102086 | Loss     |                            1.218 |                               27 |                 13 |

## Limitations
- The only test that uses 2026 in allocation fitting is clearly marked INVALID historical oracle
- Even 2025-only fit is likely overfit due to thousands of configurations
- All 2026 candle histories exposed by previous research; no pristine forward evaluation
- Original Stage18 and Stage20 are unchanged, only independent fixed-capital sleeves added
- Portfolio returns are fixed monthly weight averages of independently simulated strategies, not one integrated intraminute equity/margin engine
- No funding payments, actual spread, order book market impact, cross-venue hedge costs, monthly rebalancing fees, liquidation or contract lot granularity
- A positive historical NAV month does not imply guaranteed positive future months
- Some sources use exact fractional per-trade risk and max 5-10x exposure but actual exchange position feasibility unverified
- Trade counts in monthly output sum independent sleeves, which can overlap; not unique unified portfolio orders
- September 2026 is previously studied; no filter may select a strategy specifically because the month is September
- 2026-10-31 source day missing; November 2026 only through November 16
