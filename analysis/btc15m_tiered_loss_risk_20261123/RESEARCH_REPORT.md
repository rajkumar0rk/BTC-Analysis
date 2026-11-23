# BTCUSD 15M Reclaim — tiered loss-streak sizing

Tested 52 loss2/loss3/loss4 sizing schedules, both 1-minute OHLC paths, Jan 2025–Oct 2026.
Original 15M ST10/3 + EMA20 reclaim, one trade per cycle, 3% SL, 9% TP, +8.25% profit trigger/0% lock, five losses monthly pause; source baseline reconciled exactly.
Fees and 18% GST plus 0.02% slippage per side included; funding, live spread and actual execution NOT included.
All size multipliers <= 1, so no extra leverage. History is heavily in-sample (do not interpret selected configurations as out-of-sample performance).

Models with lower than 19.948% DD, >=151.787% return, and >=18 positive months: 36
Models beating both +172.101% profit and 16.662% drawdown: 6
Models with DD <12% preserving original return/months: 0; <10%: 0

## Strongest drawdown reduction preserving original net profit/month count
| size_mode   |   s2 |   s3 |   s4 |   worst_path_drawdown |   worst_path_return |   min_winning_months |   ntrades | vs_original   | vs_172_16   | target_12   | target_10   |
|:------------|-----:|-----:|-----:|----------------------:|--------------------:|---------------------:|----------:|:--------------|:------------|:------------|:------------|
| T65_30_10   | 0.65 |  0.3 |  0.1 |                14.74  |             162.964 |                   18 |        72 | True          | False       | False       | False       |
| T65_50_50   | 0.65 |  0.5 |  0.5 |                14.762 |             153.366 |                   18 |        72 | True          | False       | False       | False       |
| T65_40_40   | 0.65 |  0.4 |  0.4 |                14.945 |             157.141 |                   18 |        72 | True          | False       | False       | False       |
| T65_20_10   | 0.65 |  0.2 |  0.1 |                15.068 |             165.689 |                   18 |        72 | True          | False       | False       | False       |
| T65_30_30   | 0.65 |  0.3 |  0.3 |                15.136 |             160.907 |                   18 |        72 | True          | False       | False       | False       |
| T65_40_10   | 0.65 |  0.4 |  0.1 |                15.279 |             160.232 |                   18 |        72 | True          | False       | False       | False       |
| T75_50_50   | 0.75 |  0.5 |  0.5 |                15.307 |             158.746 |                   18 |        72 | True          | False       | False       | False       |
| T65_20_20   | 0.65 |  0.2 |  0.2 |                15.335 |             164.663 |                   18 |        72 | True          | False       | False       | False       |
| T75_40_40   | 0.75 |  0.4 |  0.4 |                15.489 |             162.601 |                   18 |        72 | True          | False       | False       | False       |
| T65_10_10   | 0.65 |  0.1 |  0.1 |                15.541 |             168.405 |                   18 |        72 | True          | False       | False       | False       |
| T75_30_10   | 0.75 |  0.3 |  0.1 |                15.557 |             168.548 |                   18 |        72 | True          | False       | False       | False       |
| T75_20_10   | 0.75 |  0.2 |  0.1 |                15.611 |             171.33  |                   18 |        72 | True          | False       | False       | False       |
| T75_30_30   | 0.75 |  0.3 |  0.3 |                15.679 |             166.447 |                   18 |        72 | True          | False       | False       | False       |
| T65_50_10   | 0.65 |  0.5 |  0.1 |                15.817 |             157.494 |                   18 |        72 | True          | False       | False       | False       |
| T85_50_50   | 0.85 |  0.5 |  0.5 |                15.85  |             164.107 |                   18 |        72 | True          | False       | False       | False       |
| T75_20_20   | 0.75 |  0.2 |  0.2 |                15.876 |             170.283 |                   18 |        72 | True          | False       | False       | False       |
| T85_40_40   | 0.85 |  0.4 |  0.4 |                16.031 |             168.041 |                   18 |        72 | True          | False       | False       | False       |
| T75_10_10   | 0.75 |  0.1 |  0.1 |                16.081 |             174.105 |                   18 |        72 | True          | True        | False       | False       |
| T75_40_10   | 0.75 |  0.4 |  0.1 |                16.091 |             165.758 |                   18 |        72 | True          | False       | False       | False       |
| T85_20_10   | 0.85 |  0.2 |  0.1 |                16.152 |             176.951 |                   18 |        72 | True          | True        | False       | False       |
| T85_30_30   | 0.85 |  0.3 |  0.3 |                16.22  |             171.967 |                   18 |        72 | True          | False       | False       | False       |
| T85_30_10   | 0.85 |  0.3 |  0.1 |                16.368 |             174.111 |                   18 |        72 | True          | True        | False       | False       |
| T95_50_50   | 0.95 |  0.5 |  0.5 |                16.392 |             169.443 |                   18 |        72 | True          | False       | False       | False       |
| T85_20_20   | 0.85 |  0.2 |  0.2 |                16.416 |             175.882 |                   18 |        72 | True          | True        | False       | False       |
| T95_40_40   | 0.95 |  0.4 |  0.4 |                16.572 |             173.457 |                   18 |        72 | True          | True        | False       | False       |
| T85_10_10   | 0.85 |  0.1 |  0.1 |                16.62  |             179.783 |                   18 |        72 | True          | True        | False       | False       |
| T75_50_10   | 0.75 |  0.5 |  0.1 |                16.623 |             162.962 |                   18 |        72 | True          | False       | False       | False       |
| T95_20_10   | 0.95 |  0.2 |  0.1 |                16.692 |             182.547 |                   18 |        72 | True          | False       | False       | False       |
| T95_30_30   | 0.95 |  0.3 |  0.3 |                16.759 |             177.463 |                   18 |        72 | True          | False       | False       | False       |
| T85_40_10   | 0.85 |  0.4 |  0.1 |                16.897 |             171.263 |                   18 |        72 | True          | False       | False       | False       |

## Strictly better than +172.101%/16.662%
| size_mode   |   s2 |   s3 |   s4 |   worst_path_drawdown |   worst_path_return |   min_winning_months |   ntrades | vs_original   | vs_172_16   | target_12   | target_10   |
|:------------|-----:|-----:|-----:|----------------------:|--------------------:|---------------------:|----------:|:--------------|:------------|:------------|:------------|
| T75_10_10   | 0.75 |  0.1 |  0.1 |                16.081 |             174.105 |                   18 |        72 | True          | True        | False       | False       |
| T85_20_10   | 0.85 |  0.2 |  0.1 |                16.152 |             176.951 |                   18 |        72 | True          | True        | False       | False       |
| T85_30_10   | 0.85 |  0.3 |  0.1 |                16.368 |             174.111 |                   18 |        72 | True          | True        | False       | False       |
| T85_20_20   | 0.85 |  0.2 |  0.2 |                16.416 |             175.882 |                   18 |        72 | True          | True        | False       | False       |
| T95_40_40   | 0.95 |  0.4 |  0.4 |                16.572 |             173.457 |                   18 |        72 | True          | True        | False       | False       |
| T85_10_10   | 0.85 |  0.1 |  0.1 |                16.62  |             179.783 |                   18 |        72 | True          | True        | False       | False       |

## Lowest drawdown regardless of profit preservation
| size_mode   |   s2 |   s3 |   s4 |   worst_path_drawdown |   worst_path_return |   min_winning_months |   ntrades | vs_original   | vs_172_16   | target_12   | target_10   |
|:------------|-----:|-----:|-----:|----------------------:|--------------------:|---------------------:|----------:|:--------------|:------------|:------------|:------------|
| T45_20_10   | 0.45 |  0.2 |  0.1 |                14.057 |             154.361 |                   17 |        72 | False         | False       | False       | False       |
| T45_30_10   | 0.45 |  0.3 |  0.1 |                14.057 |             151.752 |                   17 |        72 | False         | False       | False       | False       |
| T45_30_30   | 0.45 |  0.3 |  0.3 |                14.057 |             149.784 |                   17 |        72 | False         | False       | False       | False       |
| T45_40_10   | 0.45 |  0.4 |  0.1 |                14.057 |             149.137 |                   17 |        72 | False         | False       | False       | False       |
| T45_40_40   | 0.45 |  0.4 |  0.4 |                14.057 |             146.178 |                   17 |        72 | False         | False       | False       | False       |
| T55_30_10   | 0.55 |  0.3 |  0.1 |                14.071 |             157.364 |                   17 |        72 | False         | False       | False       | False       |
| T55_50_50   | 0.55 |  0.5 |  0.5 |                14.215 |             147.971 |                   17 |        72 | False         | False       | False       | False       |
| T45_20_20   | 0.45 |  0.2 |  0.2 |                14.246 |             153.379 |                   17 |        72 | False         | False       | False       | False       |
| T55_40_40   | 0.55 |  0.4 |  0.4 |                14.399 |             151.665 |                   17 |        72 | False         | False       | False       | False       |
| T45_10_10   | 0.45 |  0.1 |  0.1 |                14.455 |             156.962 |                   17 |        72 | False         | False       | False       | False       |
| T55_40_10   | 0.55 |  0.4 |  0.1 |                14.462 |             154.69  |                   17 |        72 | False         | False       | False       | False       |
| T55_20_10   | 0.55 |  0.2 |  0.1 |                14.523 |             160.031 |                   17 |        72 | False         | False       | False       | False       |
| T55_30_30   | 0.55 |  0.3 |  0.3 |                14.592 |             155.351 |                   17 |        72 | False         | False       | False       | False       |
| T65_30_10   | 0.65 |  0.3 |  0.1 |                14.74  |             162.964 |                   18 |        72 | True          | False       | False       | False       |
| T65_50_50   | 0.65 |  0.5 |  0.5 |                14.762 |             153.366 |                   18 |        72 | True          | False       | False       | False       |
| T55_20_20   | 0.55 |  0.2 |  0.2 |                14.791 |             159.027 |                   17 |        72 | False         | False       | False       | False       |
| T65_40_40   | 0.65 |  0.4 |  0.4 |                14.945 |             157.141 |                   18 |        72 | True          | False       | False       | False       |
| T55_10_10   | 0.55 |  0.1 |  0.1 |                14.999 |             162.69  |                   17 |        72 | False         | False       | False       | False       |
| T55_50_10   | 0.55 |  0.5 |  0.1 |                15.005 |             152.01  |                   17 |        72 | False         | False       | False       | False       |
| T65_20_10   | 0.65 |  0.2 |  0.1 |                15.068 |             165.689 |                   18 |        72 | True          | False       | False       | False       |

## Limitations
Floating peak-to-trough drawdown includes intratrade marks. Requires prospective validation, funding and real order execution stress test.
