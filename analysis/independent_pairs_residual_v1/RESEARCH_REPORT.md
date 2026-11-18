# Independent ETH/BTC dollar-neutral residual reversion

Novelty: differential two-leg pair, not two standalone asset backtests. Historical, not live validation.

## 2025-selected candidate

| config                                 |   overall_pf |   total_return_pct |   return_2025_pct |   return_2026_jan_oct_pct | yearly_2025_above_500   | ytd_2026_above_500   |   positive_months |   strong5_months |   strong10_months |   trades |   wins |   losses |   max_closed_trade_dd_pct |
|:---------------------------------------|-------------:|-------------------:|------------------:|--------------------------:|:------------------------|:---------------------|------------------:|-----------------:|------------------:|---------:|-------:|---------:|--------------------------:|
| ratio_revert_L120_Z1.5_stop1.5_hold24h |            0 |           -620.495 |          -620.495 |                         0 | False                   | False                |                 0 |                0 |                 0 |        1 |      0 |        1 |                  -620.495 |

## Highest total returns (exploratory, hindsight)

| config                                 |   overall_pf |   total_return_pct |   return_2025_pct |   return_2026_jan_oct_pct | yearly_2025_above_500   | ytd_2026_above_500   |   positive_months |   strong5_months |   strong10_months |   trades |   wins |   losses |   max_closed_trade_dd_pct |
|:---------------------------------------|-------------:|-------------------:|------------------:|--------------------------:|:------------------------|:---------------------|------------------:|-----------------:|------------------:|---------:|-------:|---------:|--------------------------:|
| ratio_revert_L480_Z1.5_stop2_hold24h   |            0 |           -156.277 |          -156.277 |                         0 | False                   | False                |                 0 |                0 |                 0 |        1 |      0 |        1 |                  -156.277 |
| ratio_revert_L480_Z1.5_stop2_hold48h   |            0 |           -156.277 |          -156.277 |                         0 | False                   | False                |                 0 |                0 |                 0 |        1 |      0 |        1 |                  -156.277 |
| ratio_revert_L480_Z1.5_stop1.5_hold24h |            0 |           -208.369 |          -208.369 |                         0 | False                   | False                |                 0 |                0 |                 0 |        1 |      0 |        1 |                  -208.369 |
| ratio_revert_L480_Z1.5_stop1.5_hold48h |            0 |           -208.369 |          -208.369 |                         0 | False                   | False                |                 0 |                0 |                 0 |        1 |      0 |        1 |                  -208.369 |
| ratio_revert_L240_Z2.5_stop2_hold48h   |            0 |           -248.453 |          -248.453 |                         0 | False                   | False                |                 0 |                0 |                 0 |        1 |      0 |        1 |                  -248.453 |
| ratio_revert_L240_Z2.5_stop2_hold24h   |            0 |           -248.453 |          -248.453 |                         0 | False                   | False                |                 0 |                0 |                 0 |        1 |      0 |        1 |                  -248.453 |
| ratio_revert_L240_Z2_stop2_hold48h     |            0 |           -253.014 |          -253.014 |                         0 | False                   | False                |                 0 |                0 |                 0 |        1 |      0 |        1 |                  -253.014 |
| ratio_revert_L240_Z2_stop2_hold24h     |            0 |           -253.014 |          -253.014 |                         0 | False                   | False                |                 0 |                0 |                 0 |        1 |      0 |        1 |                  -253.014 |

## All 22 monthly results for 2025-selected configuration

| config                                 | month   |   monthly_pf |   net_return_pct |   net_usd |   trades |   wins |   losses |   equity_start_usd |   equity_end_usd |
|:---------------------------------------|:--------|-------------:|-----------------:|----------:|---------:|-------:|---------:|-------------------:|-----------------:|
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2025-01 |            0 |         -620.495 |  -6204.95 |        1 |      0 |        1 |            1000    |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2025-02 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2025-03 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2025-04 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2025-05 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2025-06 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2025-07 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2025-08 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2025-09 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2025-10 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2025-11 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2025-12 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2026-01 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2026-02 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2026-03 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2026-04 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2026-05 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2026-06 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2026-07 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2026-08 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2026-09 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |
| ratio_revert_L120_Z1.5_stop1.5_hold24h | 2026-10 |          nan |         -100     |      0    |        0 |      0 |        0 |           -5204.95 |         -5204.95 |

2025 full-year >500% and 2026 Jan-Oct YTD >500% shown separately. All monthly values are after modeled two-leg fees/GST/slippage, with incomplete execution-cost coverage.
