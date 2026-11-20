# ETHUSD 1-minute intrabar cross-check of 1-hour EMA/ST signals

| ETH trailing setup | Slippage case | Trades | Net USD / 0.01 ETH contract | PF | Positive months | Eligible exits |
|---|---|---:|---:|---:|---:|---:|
| fixed_100_50 | zero_slippage | 510 | -10.0240 | 0.9387 | 8/22 | 1 |
| fixed_100_50 | 0p5_point_each_side | 510 | -15.1240 | 0.9094 | 7/22 | 1 |
| pct_scaled | zero_slippage | 2084 | -31.3536 | 0.6134 | 3/22 | 1404 |
| pct_scaled | 0p5_point_each_side | 2084 | -52.1934 | 0.4042 | 3/22 | 1404 |

This is a 1-minute stop-monitoring sensitivity, **not** the exact 1-hour stop-monitoring screenshot. Offer assumed active, funding/spread omitted.
