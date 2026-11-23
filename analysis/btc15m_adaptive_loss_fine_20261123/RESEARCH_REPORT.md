# BTCUSD 15M Reclaim — fine grid on after-loss position size

54 position-sizing variants x 2 ordered 1-minute OHLC paths, original execution code re-run and baseline checked against +151.787% / 19.948% / 18 months / 72 trades.
Entry, fees+GST, 0.02% per-side adverse slippage, 3% SL, 9% TP, +8.25% break-even protection, five-loss monthly pause unchanged.
Position size AFTER N monthly losing exits is set to 10%–95% of account equity; before then remains 100%. All variants <= 1x notional.
**The full 22 months have already been used repeatedly for parameter selection. This is in-sample sensitivity, not evidence of future profitability. Funding and actual execution effects excluded.**

Compared to old baseline 151.787%/19.948%, 31 of 54 meet higher/equal profit, >=18 positive months, lower DD.
Compared to initial improvement 172.101%/16.662%, 0 are additionally better.
With DD <12% and >=151.787% profit & >=18 positive months: 0; DD <10%: 0.

## Best variants preserving original profit and winning-month count
| size_mode   |   count |   low_size |   min_return_pct |   max_floating_dd_pct |   positive_months_min |   trades | beats_original   | beats_first_improvement   | target_12   | target_10   |
|:------------|--------:|-----------:|-----------------:|----------------------:|----------------------:|---------:|:-----------------|:--------------------------|:------------|:------------|
| L3_55       |       3 |       0.55 |          170.071 |                16.584 |                    18 |       72 | True             | False                     | False       | False       |
| L3_50       |       3 |       0.5  |          172.101 |                16.662 |                    18 |       72 | True             | False                     | False       | False       |
| L3_45       |       3 |       0.45 |          174.129 |                16.751 |                    18 |       72 | True             | False                     | False       | False       |
| L3_40       |       3 |       0.4  |          176.155 |                16.842 |                    18 |       72 | True             | False                     | False       | False       |
| L3_35       |       3 |       0.35 |          178.178 |                16.934 |                    18 |       72 | True             | False                     | False       | False       |
| L3_60       |       3 |       0.6  |          168.041 |                16.963 |                    18 |       72 | True             | False                     | False       | False       |
| L3_30       |       3 |       0.3  |          180.2   |                17.028 |                    18 |       72 | True             | False                     | False       | False       |
| L3_25       |       3 |       0.25 |          182.218 |                17.125 |                    18 |       72 | True             | False                     | False       | False       |
| L3_20       |       3 |       0.2  |          184.233 |                17.223 |                    18 |       72 | True             | False                     | False       | False       |
| L3_15       |       3 |       0.15 |          186.244 |                17.322 |                    18 |       72 | True             | False                     | False       | False       |
| L3_65       |       3 |       0.65 |          166.009 |                17.34  |                    18 |       72 | True             | False                     | False       | False       |
| L3_70       |       3 |       0.7  |          163.977 |                17.716 |                    18 |       72 | True             | False                     | False       | False       |
| L3_75       |       3 |       0.75 |          161.944 |                18.09  |                    18 |       72 | True             | False                     | False       | False       |
| L3_80       |       3 |       0.8  |          159.912 |                18.464 |                    18 |       72 | True             | False                     | False       | False       |
| L4_45       |       4 |       0.45 |          158.121 |                18.77  |                    18 |       72 | True             | False                     | False       | False       |
| L3_85       |       3 |       0.85 |          157.879 |                18.837 |                    18 |       72 | True             | False                     | False       | False       |
| L4_50       |       4 |       0.5  |          157.575 |                18.855 |                    18 |       72 | True             | False                     | False       | False       |
| L4_55       |       4 |       0.55 |          157.022 |                18.964 |                    18 |       72 | True             | False                     | False       | False       |
| L4_60       |       4 |       0.6  |          156.463 |                19.074 |                    18 |       72 | True             | False                     | False       | False       |
| L4_40       |       4 |       0.4  |          158.662 |                19.116 |                    18 |       72 | True             | False                     | False       | False       |
| L4_65       |       4 |       0.65 |          155.899 |                19.183 |                    18 |       72 | True             | False                     | False       | False       |
| L3_90       |       3 |       0.9  |          155.848 |                19.208 |                    18 |       72 | True             | False                     | False       | False       |
| L4_70       |       4 |       0.7  |          155.328 |                19.292 |                    18 |       72 | True             | False                     | False       | False       |
| L4_75       |       4 |       0.75 |          154.752 |                19.401 |                    18 |       72 | True             | False                     | False       | False       |
| L4_35       |       4 |       0.35 |          159.196 |                19.462 |                    18 |       72 | True             | False                     | False       | False       |
| L4_80       |       4 |       0.8  |          154.17  |                19.511 |                    18 |       72 | True             | False                     | False       | False       |
| L3_95       |       3 |       0.95 |          153.817 |                19.578 |                    18 |       72 | True             | False                     | False       | False       |
| L4_85       |       4 |       0.85 |          153.583 |                19.62  |                    18 |       72 | True             | False                     | False       | False       |
| L4_90       |       4 |       0.9  |          152.99  |                19.729 |                    18 |       72 | True             | False                     | False       | False       |
| L4_30       |       4 |       0.3  |          159.724 |                19.808 |                    18 |       72 | True             | False                     | False       | False       |

## Strict improvements over +172.101%/16.662%
None.

## All variants with smallest drawdown
| size_mode   |   count |   low_size |   min_return_pct |   max_floating_dd_pct |   positive_months_min |   trades | beats_original   | beats_first_improvement   | target_12   | target_10   |
|:------------|--------:|-----------:|-----------------:|----------------------:|----------------------:|---------:|:-----------------|:--------------------------|:------------|:------------|
| L2_15       |       2 |       0.15 |          138.082 |                14.016 |                    16 |       72 | False            | False                     | False       | False       |
| L2_20       |       2 |       0.2  |          139.237 |                14.023 |                    17 |       72 | False            | False                     | False       | False       |
| L2_25       |       2 |       0.25 |          140.349 |                14.03  |                    17 |       72 | False            | False                     | False       | False       |
| L2_30       |       2 |       0.3  |          141.42  |                14.037 |                    17 |       72 | False            | False                     | False       | False       |
| L2_35       |       2 |       0.35 |          142.447 |                14.043 |                    17 |       72 | False            | False                     | False       | False       |
| L2_40       |       2 |       0.4  |          143.431 |                14.05  |                    17 |       72 | False            | False                     | False       | False       |
| L2_45       |       2 |       0.45 |          144.372 |                14.057 |                    17 |       72 | False            | False                     | False       | False       |
| L2_50       |       2 |       0.5  |          145.268 |                14.064 |                    17 |       72 | False            | False                     | False       | False       |
| L2_55       |       2 |       0.55 |          146.121 |                14.133 |                    17 |       72 | False            | False                     | False       | False       |
| L2_10       |       2 |       0.1  |          136.885 |                14.212 |                    16 |       72 | False            | False                     | False       | False       |
| L2_60       |       2 |       0.6  |          146.93  |                14.795 |                    17 |       72 | False            | False                     | False       | False       |
| L2_65       |       2 |       0.65 |          147.694 |                15.453 |                    18 |       72 | False            | False                     | False       | False       |
| L2_70       |       2 |       0.7  |          148.413 |                16.107 |                    18 |       72 | False            | False                     | False       | False       |
| L3_55       |       3 |       0.55 |          170.071 |                16.584 |                    18 |       72 | True             | False                     | False       | False       |
| L3_50       |       3 |       0.5  |          172.101 |                16.662 |                    18 |       72 | True             | False                     | False       | False       |
| L3_45       |       3 |       0.45 |          174.129 |                16.751 |                    18 |       72 | True             | False                     | False       | False       |
| L2_75       |       2 |       0.75 |          149.088 |                16.757 |                    18 |       72 | False            | False                     | False       | False       |
| L3_40       |       3 |       0.4  |          176.155 |                16.842 |                    18 |       72 | True             | False                     | False       | False       |
| L3_35       |       3 |       0.35 |          178.178 |                16.934 |                    18 |       72 | True             | False                     | False       | False       |
| L3_60       |       3 |       0.6  |          168.041 |                16.963 |                    18 |       72 | True             | False                     | False       | False       |

## Study quality
Both O-H-L-C and O-L-H-C price paths must satisfy the metrics. Actual gaps, market depth, slippage and funding may alter results.
