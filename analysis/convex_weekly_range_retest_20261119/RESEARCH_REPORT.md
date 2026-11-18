# Independent weekly-channel breakout retest asymmetry study

**Strict qualifiers: 0 / 64**

## Best 2025 returns (not recommendations)
| symbol   | model                                   |   signals |   trades |   wins |   losses |   win_rate |     pf |   win_loss_ratio |   max_winner_R |   winners_over_10R |   return_total_pct |   return_2025_pct |   return_2026_partial_pct |   max_drawdown_pct |   fees_usd |   funding_proxy_usd |
|:---------|:----------------------------------------|----------:|---------:|-------:|---------:|-----------:|-------:|-----------------:|---------------:|-------------------:|-------------------:|------------------:|--------------------------:|-------------------:|-----------:|--------------------:|
| ETHUSD   | channel168_wait6_tol0.5_stop2_trail72   |       121 |       61 |     14 |       47 |     0.2295 | 1.8222 |           6.1173 |         23.604 |                  3 |             22.307 |            10.681 |                    10.504 |             -7.83  |     22.114 |               5.012 |
| ETHUSD   | channel72_wait6_tol0.5_stop2_trail72    |       176 |       96 |     16 |       80 |     0.1667 | 1.1431 |           5.7153 |         25.263 |                  3 |              6.313 |             7.836 |                    -1.412 |            -15.932 |     34.742 |               4.996 |
| ETHUSD   | channel72_wait6_tol0.5_stop2_trail168   |       176 |       81 |     12 |       69 |     0.1481 | 1.6174 |           9.3003 |         24.531 |                  6 |             24.769 |             7.156 |                    16.437 |            -12.665 |     30.564 |               5.086 |
| ETHUSD   | channel168_wait6_tol0.5_stop3_trail72   |       121 |       57 |     17 |       40 |     0.2982 | 1.604  |           3.7741 |         15.736 |                  2 |             12.531 |             6.828 |                     5.339 |             -5.756 |     13.431 |               3.358 |
| ETHUSD   | channel168_wait6_tol0.5_stop3_trail168  |       121 |       51 |     12 |       39 |     0.2353 | 1.9721 |           6.4094 |         17.472 |                  4 |             21.008 |             5.715 |                    14.466 |             -6.509 |     12.436 |               3.842 |
| ETHUSD   | channel168_wait12_tol0.25_stop2_trail72 |       124 |       60 |     15 |       45 |     0.25   | 1.3353 |           4.0059 |         23.604 |                  1 |              8.242 |             5.523 |                     2.576 |             -8.848 |     19.941 |               2.462 |
| ETHUSD   | channel168_wait6_tol0.5_stop2_trail168  |       121 |       58 |     11 |       47 |     0.1897 | 2.1909 |           9.3611 |         26.208 |                  5 |             33.529 |             5.299 |                    26.81  |            -10.622 |     21.212 |               6.96  |
| ETHUSD   | channel168_wait6_tol0.25_stop2_trail72  |        99 |       53 |      9 |       44 |     0.1698 | 1.0993 |           5.3746 |         23.604 |                  1 |              2.382 |             4.991 |                    -2.486 |            -11.046 |     17.541 |               2.115 |
| ETHUSD   | channel168_wait12_tol0.5_stop2_trail72  |       136 |       66 |     16 |       50 |     0.2424 | 1.6056 |           5.0174 |         23.604 |                  2 |             16.629 |             4.971 |                    11.106 |             -9.325 |     22.489 |               3.432 |
| ETHUSD   | channel72_wait6_tol0.25_stop2_trail168  |       147 |       72 |      8 |       64 |     0.1111 | 1.1813 |           9.4505 |         25.001 |                  4 |              6.584 |             3.892 |                     2.59  |            -12.24  |     26.415 |               1.702 |
| ETHUSD   | channel72_wait6_tol0.25_stop2_trail72   |       147 |       84 |     11 |       73 |     0.131  | 0.7686 |           5.1006 |         25.734 |                  1 |             -8.997 |             3.162 |                   -11.786 |            -18.852 |     28.733 |               2.347 |
| ETHUSD   | channel168_wait12_tol0.5_stop3_trail72  |       136 |       61 |     18 |       43 |     0.2951 | 1.4001 |           3.3447 |         15.736 |                  2 |              8.624 |             3.035 |                     5.424 |             -6.372 |     13.743 |               2.741 |

## Data and model limitations
- Both markets use continuous Delta India one-minute data; signals on closed 1h bars
- One position, 0.5% initial equity risk, 10x notional leverage cap
- Taker fee 0.05% each side + 18% GST, 2bps slippage each execution
- Delta 1h funding rate proxy, missing settlement 1bp charged to position
- No intraminute path, spread, liquidation, or true portfolio margin simulation
- 2026 is partial, not a full-year 500% return test
- In-sample comparisons only; no untouched holdout or prospective validation
- Trail uses completed hourly range; gaps through stops use worse opening price
- Signal entered next hour open; stop checks at same minute are approximate
- Robustness tests only meaningful for passing candidates, none assumed
