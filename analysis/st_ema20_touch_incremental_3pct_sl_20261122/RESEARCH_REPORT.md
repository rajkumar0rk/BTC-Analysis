# EMA20 Touch: 3% initial stop plus incremental profit protection

BTCUSD 1H ST(10,3) first EMA20 Touch, volume ratio 1.25-2.5x; 1m stop updates.
Comparison includes exact 0.16% -> 0.30% -> 0.50% -> 1% -> 2% and 0.16% -> 0.50% -> 1% -> 2% ladders.
The stop starts at -3% from entry and moves to the highest reached positive lock.
The Supertrend flip remains a fallback exit; one fill per ST cycle.

## Side-by-side across two simulated price paths

| variant                   | initial_stop   | lock_levels_pct                   |   profitable_months_min |   profitable_months_max |   losing_months_max |   net_usd_min |   net_usd_max |   net_2025_min |   net_2025_max |   net_2026_min |   net_2026_max |   wins |   losses |   stops_triggered |   max_realized_dd_pct |
|:--------------------------|:---------------|:----------------------------------|------------------------:|------------------------:|--------------------:|--------------:|--------------:|---------------:|---------------:|---------------:|---------------:|-------:|---------:|------------------:|----------------------:|
| exact_0p16_0p30_0p50_1_2  | 3%             | 0.16% -> 0.3% -> 0.5% -> 1% -> 2% |                      21 |                      21 |                   0 |      2.92915  |      3.56408  |        2.23233 |        2.86815 |        0.69592 |        0.69682 |     50 |        0 |                 0 |                 0     |
| exact_0p16_0p50_1_2       | 3%             | 0.16% -> 0.5% -> 1% -> 2%         |                      21 |                      21 |                   0 |      2.27528  |      3.26879  |        1.66596 |        2.44697 |        0.60932 |        0.82183 |     50 |        0 |                 0 |                 0     |
| single_0p14               | 3%             | 0.14%                             |                      21 |                      21 |                   0 |      0.723046 |      0.725036 |        0.46296 |        0.46334 |        0.2597  |        0.26208 |     50 |        0 |                 0 |                 0     |
| increment_0p14_0p50_1_2_5 | 3%             | 0.14% -> 0.5% -> 1% -> 2% -> 5%   |                      21 |                      21 |                   0 |      1.42551  |      2.08574  |        1.16581 |        1.59866 |        0.2597  |        0.48708 |     50 |        0 |                 0 |                 0     |
| control_0p20_0p50_1_2_5   | 3%             | 0.2% -> 0.5% -> 1% -> 2% -> 5%    |                      20 |                      20 |                   1 |      2.05009  |      2.55877  |        0.13599 |        0.55979 |        1.4903  |        2.42278 |     49 |        1 |                 0 |                 2.685 |
| exact_0p20_0p50_1_2       | 3%             | 0.2% -> 0.5% -> 1% -> 2%          |                      20 |                      20 |                   1 |      2.05009  |      2.55877  |        0.13599 |        0.55979 |        1.4903  |        2.42278 |     49 |        1 |                 0 |                 2.685 |

## Yearly and path-level results

| variant                   | path                |   trades |   wins |   losses |   profitable_2025 |   profitable_2026 |   profitable_months |   losing_months |   flat_months |   net_2025 |   net_2026 |   total_net_usd |   stopped_trades |   max_realized_dd_pct |
|:--------------------------|:--------------------|---------:|-------:|---------:|------------------:|------------------:|--------------------:|----------------:|--------------:|-----------:|-----------:|----------------:|-----------------:|----------------------:|
| single_0p14               | open_high_low_close |       50 |     50 |        0 |                11 |                10 |                  21 |               0 |             1 |    0.46296 |    0.26208 |        0.725036 |                0 |                 0     |
| increment_0p14_0p50_1_2_5 | open_high_low_close |       50 |     50 |        0 |                11 |                10 |                  21 |               0 |             1 |    1.59866 |    0.48708 |        2.08574  |                0 |                 0     |
| exact_0p20_0p50_1_2       | open_high_low_close |       50 |     49 |        1 |                10 |                10 |                  20 |               1 |             1 |    0.55979 |    1.4903  |        2.05009  |                0 |                 2.674 |
| control_0p20_0p50_1_2_5   | open_high_low_close |       50 |     49 |        1 |                10 |                10 |                  20 |               1 |             1 |    0.55979 |    1.4903  |        2.05009  |                0 |                 2.674 |
| exact_0p16_0p30_0p50_1_2  | open_high_low_close |       50 |     50 |        0 |                11 |                10 |                  21 |               0 |             1 |    2.86815 |    0.69592 |        3.56408  |                0 |                 0     |
| exact_0p16_0p50_1_2       | open_high_low_close |       50 |     50 |        0 |                11 |                10 |                  21 |               0 |             1 |    2.44697 |    0.82183 |        3.26879  |                0 |                 0     |
| single_0p14               | open_low_high_close |       50 |     50 |        0 |                11 |                10 |                  21 |               0 |             1 |    0.46334 |    0.2597  |        0.723046 |                0 |                 0     |
| increment_0p14_0p50_1_2_5 | open_low_high_close |       50 |     50 |        0 |                11 |                10 |                  21 |               0 |             1 |    1.16581 |    0.2597  |        1.42551  |                0 |                 0     |
| exact_0p20_0p50_1_2       | open_low_high_close |       50 |     49 |        1 |                10 |                10 |                  20 |               1 |             1 |    0.13599 |    2.42278 |        2.55877  |                0 |                 2.685 |
| control_0p20_0p50_1_2_5   | open_low_high_close |       50 |     49 |        1 |                10 |                10 |                  20 |               1 |             1 |    0.13599 |    2.42278 |        2.55877  |                0 |                 2.685 |
| exact_0p16_0p30_0p50_1_2  | open_low_high_close |       50 |     50 |        0 |                11 |                10 |                  21 |               0 |             1 |    2.23233 |    0.69682 |        2.92915  |                0 |                 0     |
| exact_0p16_0p50_1_2       | open_low_high_close |       50 |     50 |        0 |                11 |                10 |                  21 |               0 |             1 |    1.66596 |    0.60932 |        2.27528  |                0 |                 0     |

Fees, GST and 5-point execution slippage each side included. No tick sequence, order latency, funding, margin or liquidation. The results are retrospective and are not live-trading proof.
