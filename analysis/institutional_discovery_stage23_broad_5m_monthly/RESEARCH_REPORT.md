# Stage23 — Wider BTC monthly profit search including 5M orig/fade strategies

## Goal
Positive returns in every observed month of **both 2025 and 2026**,
after modeled Delta India taker fees, GST and slippage.

## Candidate sources
5585 original configurations,
4472 distinct return series, 277 selected
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
| Train2025_35pct_anchor15pct_cap       |                   4 |                  4 |                0.5322  |               0.64441 |               -0.040725 | False                     |                      9 |
| Train2025_50pct_anchor10pct_cap       |                   6 |                  5 |                0.66599 |               1.00507 |               -0.110876 | False                     |                      9 |
| Train2025_25pct_anchor15pct_cap       |                   4 |                  4 |                0.93469 |               0.53017 |               -0.016678 | False                     |                     11 |
| HINDSIGHT_ALL23_35pct_anchor15pct_cap |                   5 |                  3 |                0.08218 |               1.28586 |               -0.168016 | False                     |                     12 |

## Historical full hindsight oracle (cannot be executed)
|   minimum_month_pct | all_months_positive   |   max_month_end_drawdown_pct |   prof2025 |   prof2026 |
|--------------------:|:----------------------|-----------------------------:|-----------:|-----------:|
|           -0.150203 | False                 |                       0.6547 |          6 |          4 |

## TRAIN ONLY leading configuration monthly table
| month_ist   |   modeled_return_pct | status   |   modeled_weighted_sleeve_trades |   unique_component_closed_trades |   selected_sleeves |
|:------------|---------------------:|:---------|---------------------------------:|---------------------------------:|-------------------:|
| 2025-01     |            -0.040725 | Loss     |                            0.883 |                               17 |                  9 |
| 2025-02     |             0.178572 | Profit   |                            1.821 |                               24 |                  9 |
| 2025-03     |            -0.040725 | Loss     |                            1.91  |                               33 |                  9 |
| 2025-04     |             0.507186 | Profit   |                            1.436 |                               35 |                  9 |
| 2025-05     |            -0.040725 | Loss     |                            2.357 |                               37 |                  9 |
| 2025-06     |             0.103181 | Profit   |                            3.172 |                               56 |                  9 |
| 2025-07     |            -0.040725 | Loss     |                            3.374 |                               48 |                  9 |
| 2025-08     |             0.055913 | Profit   |                            1.077 |                               32 |                  9 |
| 2025-09     |            -0.040725 | Loss     |                            2.784 |                               51 |                  9 |
| 2025-10     |            -0.040725 | Loss     |                            1.109 |                               34 |                  9 |
| 2025-11     |            -0.027412 | Loss     |                            2.694 |                               52 |                  9 |
| 2025-12     |            -0.040725 | Loss     |                            1.505 |                               20 |                  9 |
| 2026-01     |            -0.264431 | Loss     |                            1.517 |                               29 |                  9 |
| 2026-02     |             1.42937  | Profit   |                            2.436 |                               40 |                  9 |
| 2026-03     |             0.421064 | Profit   |                            1.454 |                               35 |                  9 |
| 2026-04     |            -0.114877 | Loss     |                            2.699 |                               41 |                  9 |
| 2026-05     |            -0.133595 | Loss     |                            1.695 |                               38 |                  9 |
| 2026-06     |            -0.259621 | Loss     |                            2.233 |                               51 |                  9 |
| 2026-07     |            -0.023476 | Loss     |                            2.803 |                               56 |                  9 |
| 2026-08     |             0.661803 | Profit   |                            1.999 |                               36 |                  9 |
| 2026-09     |            -0.901825 | Loss     |                            3.442 |                               53 |                  9 |
| 2026-10     |            -0.191261 | Loss     |                            1.788 |                               40 |                  9 |
| 2026-11     |             0.037505 | Profit   |                            0.347 |                               11 |                  9 |

## HINDSIGHT upper bound monthly returns (NOT an actual profitable pattern)
| month_ist   |   modeled_return_pct | status   |   modeled_weighted_sleeve_trades |   unique_component_closed_trades |   selected_sleeves |
|:------------|---------------------:|:---------|---------------------------------:|---------------------------------:|-------------------:|
| 2025-01     |            -0.083412 | Loss     |                            0.721 |                               13 |                 12 |
| 2025-02     |             0.138584 | Profit   |                            1.316 |                               23 |                 12 |
| 2025-03     |             0.115332 | Profit   |                            0.546 |                               14 |                 12 |
| 2025-04     |             0.570362 | Profit   |                            1.225 |                               27 |                 12 |
| 2025-05     |            -0.150203 | Loss     |                            1.414 |                               26 |                 12 |
| 2025-06     |            -0.150203 | Loss     |                            1.926 |                               39 |                 12 |
| 2025-07     |            -0.0184   | Loss     |                            2.761 |                               53 |                 12 |
| 2025-08     |            -0.150203 | Loss     |                            1.281 |                               31 |                 12 |
| 2025-09     |             0.049275 | Profit   |                            1.669 |                               39 |                 12 |
| 2025-10     |             0.020991 | Profit   |                            1.467 |                               35 |                 12 |
| 2025-11     |             0.042842 | Profit   |                            1.96  |                               40 |                 12 |
| 2025-12     |            -0.150203 | Loss     |                            1.941 |                               27 |                 12 |
| 2026-01     |            -0.150203 | Loss     |                            0.98  |                               21 |                 12 |
| 2026-02     |             1.16994  | Profit   |                            1.604 |                               29 |                 12 |
| 2026-03     |             0.649766 | Profit   |                            1.61  |                               32 |                 12 |
| 2026-04     |            -0.150203 | Loss     |                            1.478 |                               30 |                 12 |
| 2026-05     |            -0.118342 | Loss     |                            1.034 |                               25 |                 12 |
| 2026-06     |            -0.150203 | Loss     |                            1.836 |                               39 |                 12 |
| 2026-07     |            -0.150203 | Loss     |                            1.104 |                               30 |                 12 |
| 2026-08     |             0.39175  | Profit   |                            0.857 |                               22 |                 12 |
| 2026-09     |            -0.150203 | Loss     |                            0.966 |                               30 |                 12 |
| 2026-10     |            -0.050546 | Loss     |                            1.26  |                               27 |                 12 |
| 2026-11     |             0.107286 | Profit   |                            0.269 |                                7 |                 12 |

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
