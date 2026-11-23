# BTCUSD 15m ATR0.2 minimum volatility — position-scale drawdown research

80 variants tested in both 1m OHLC path orders. Historical sample Jan2025–Oct2026.
Exact 15m-only Supertrend(10,3)/EMA20 reclaim entry. New filter ATR10/close >=0.20% evaluated at completed signal bar.
3% SL, 9% TP, late protection activates at +8.25% and first lock at 0%; 5 losing exits per IST month halts new entries.
Tiered 1x post-loss sizing; uniform global size factors 55%–100%. No additional leverage.
Modeled 0.05% taker fee per side +18% GST, 0.02% adverse slippage per side; funding and live depth not modeled.
**All 22 months heavily selected / in-sample. Do not treat these as forward results.**
Verified control in every shard and both paths: 71 trades, +229.037% total return, 14.740% floating DD, 18/22 profitable months.

Strict improvement over +162.964%/14.74%/18 months: 30 variants.
Under 12% floating DD and >=162.964% return with >=18 months: 1.
Under 12% floating DD and >=151.787% return with >=18 months: 3.
Under 10% floating DD and >=151.787% return with >=18 months: 0.

## Best strictly lower DD preserving +162.964% and 18 positive months
| tier      |   uniform_scale |   worst_dd |   worst_path_profit |   winning_months |   trades |   return_2025 |   return_2026 | strict_better   | dd12_net162   | dd12_net151   | dd10_net151   |
|:----------|----------------:|-----------:|--------------------:|-----------------:|---------:|--------------:|--------------:|:----------------|:--------------|:--------------|:--------------|
| T65_30_10 |           0.8   |     11.879 |             163.492 |               18 |       71 |        43.892 |        83.118 | True            | True          | True          | False         |
| T65_20_10 |           0.8   |     12.21  |             165.66  |               18 |       71 |        44.71  |        83.581 | True            | False         | False         | False         |
| T65_30_10 |           0.825 |     12.24  |             171.026 |               18 |       71 |        45.383 |        86.422 | True            | False         | False         | False         |
| T65_20_10 |           0.825 |     12.572 |             173.327 |               18 |       71 |        46.236 |        86.908 | True            | False         | False         | False         |
| T65_30_10 |           0.85  |     12.599 |             178.741 |               18 |       71 |        46.881 |        89.774 | True            | False         | False         | False         |
| T65_20_10 |           0.85  |     12.932 |             181.182 |               18 |       71 |        47.77  |        90.284 | True            | False         | False         | False         |
| T65_30_10 |           0.875 |     12.958 |             186.642 |               18 |       71 |        48.384 |        93.175 | True            | False         | False         | False         |
| T75_10_10 |           0.8   |     13.049 |             167.738 |               18 |       71 |        45.255 |        84.323 | True            | False         | False         | False         |
| T85_20_10 |           0.8   |     13.104 |             165.442 |               18 |       71 |        44.162 |        84.128 | True            | False         | False         | False         |
| T65_20_10 |           0.875 |     13.291 |             189.228 |               18 |       71 |        49.31  |        93.71  | True            | False         | False         | False         |
| T65_30_10 |           0.9   |     13.316 |             194.73  |               18 |       71 |        49.894 |        96.626 | True            | False         | False         | False         |
| T75_10_10 |           0.825 |     13.433 |             175.522 |               18 |       71 |        46.8   |        87.685 | True            | False         | False         | False         |
| T85_20_10 |           0.825 |     13.49  |             173.072 |               18 |       71 |        45.657 |        87.477 | True            | False         | False         | False         |
| T85_10_10 |           0.8   |     13.494 |             167.603 |               18 |       71 |        44.97  |        84.592 | True            | False         | False         | False         |
| T65_20_10 |           0.9   |     13.648 |             197.468 |               18 |       71 |        50.857 |        97.185 | True            | False         | False         | False         |
| T65_30_10 |           0.925 |     13.673 |             203.011 |               18 |       71 |        51.41  |       100.126 | True            | False         | False         | False         |
| T75_10_10 |           0.85  |     13.816 |             183.497 |               18 |       71 |        48.353 |        91.096 | True            | False         | False         | False         |
| T85_20_10 |           0.85  |     13.874 |             180.886 |               18 |       71 |        47.157 |        90.875 | True            | False         | False         | False         |
| T85_10_10 |           0.825 |     13.89  |             175.366 |               18 |       71 |        46.499 |        87.964 | True            | False         | False         | False         |
| T65_20_10 |           0.925 |     14.005 |             205.907 |               18 |       71 |        52.411 |       100.711 | True            | False         | False         | False         |
| T65_30_10 |           0.95  |     14.029 |             211.486 |               18 |       71 |        52.932 |       103.676 | True            | False         | False         | False         |
| T75_10_10 |           0.875 |     14.197 |             191.668 |               18 |       71 |        49.913 |        94.558 | True            | False         | False         | False         |
| T85_20_10 |           0.875 |     14.258 |             188.886 |               18 |       71 |        48.663 |        94.323 | True            | False         | False         | False         |
| T85_10_10 |           0.85  |     14.284 |             183.318 |               18 |       71 |        48.034 |        91.387 | True            | False         | False         | False         |
| T65_20_10 |           0.95  |     14.36  |             214.547 |               18 |       71 |        53.972 |       104.289 | True            | False         | False         | False         |
| T65_30_10 |           0.975 |     14.385 |             220.16  |               18 |       71 |        54.46  |       107.278 | True            | False         | False         | False         |
| T75_10_10 |           0.9   |     14.576 |             200.037 |               18 |       71 |        51.48  |        98.071 | True            | False         | False         | False         |
| T85_20_10 |           0.9   |     14.639 |             197.077 |               18 |       71 |        50.174 |        97.822 | True            | False         | False         | False         |
| T85_10_10 |           0.875 |     14.677 |             191.463 |               18 |       71 |        49.576 |        94.859 | True            | False         | False         | False         |
| T65_20_10 |           0.975 |     14.714 |             223.392 |               18 |       71 |        55.539 |       107.917 | True            | False         | False         | False         |

## Candidates below 12% with >=162.964% net
| tier      |   uniform_scale |   worst_dd |   worst_path_profit |   winning_months |   trades |   return_2025 |   return_2026 | strict_better   | dd12_net162   | dd12_net151   | dd10_net151   |
|:----------|----------------:|-----------:|--------------------:|-----------------:|---------:|--------------:|--------------:|:----------------|:--------------|:--------------|:--------------|
| T65_30_10 |             0.8 |     11.879 |             163.492 |               18 |       71 |        43.892 |        83.118 | True            | True          | True          | False         |

## Candidates below 10% with >=151.787% net
None.

## All lowest-drawdown variants
| tier      |   uniform_scale |   worst_dd |   worst_path_profit |   winning_months |   trades |   return_2025 |   return_2026 | strict_better   | dd12_net162   | dd12_net151   | dd10_net151   |
|:----------|----------------:|-----------:|--------------------:|-----------------:|---------:|--------------:|--------------:|:----------------|:--------------|:--------------|:--------------|
| T65_30_10 |           0.55  |      8.249 |             97.4193 |               18 |       71 |        29.348 |        52.626 | False           | False         | False         | False         |
| T65_20_10 |           0.55  |      8.531 |             98.5252 |               18 |       71 |        29.848 |        52.891 | False           | False         | False         | False         |
| T65_30_10 |           0.6   |      8.973 |            109.362  |               18 |       71 |        32.202 |        58.366 | False           | False         | False         | False         |
| T75_10_10 |           0.55  |      9.132 |             99.6431 |               18 |       71 |        30.206 |        53.329 | False           | False         | False         | False         |
| T85_20_10 |           0.55  |      9.168 |             98.5352 |               18 |       71 |        29.564 |        53.233 | False           | False         | False         | False         |
| T65_20_10 |           0.6   |      9.276 |            110.644  |               18 |       71 |        32.76  |        58.665 | False           | False         | False         | False         |
| T85_10_10 |           0.55  |      9.45  |             99.639  |               18 |       71 |        30.06  |        53.498 | False           | False         | False         | False         |
| T65_30_10 |           0.65  |      9.704 |            121.916  |               18 |       71 |        35.083 |        64.281 | False           | False         | False         | False         |
| T75_10_10 |           0.6   |      9.927 |            111.926  |               18 |       71 |        33.154 |        59.158 | False           | False         | False         | False         |
| T85_20_10 |           0.6   |      9.967 |            110.627  |               18 |       71 |        32.431 |        59.046 | False           | False         | False         | False         |
| T65_20_10 |           0.65  |     10.017 |            123.391  |               18 |       71 |        35.703 |        64.618 | False           | False         | False         | False         |
| T85_10_10 |           0.6   |     10.271 |            111.906  |               18 |       71 |        32.985 |        59.346 | False           | False         | False         | False         |
| T65_30_10 |           0.7   |     10.432 |            135.105  |               18 |       71 |        37.993 |        70.375 | False           | False         | False         | False         |
| T75_10_10 |           0.65  |     10.716 |            124.85   |               18 |       71 |        36.134 |        65.168 | False           | False         | False         | False         |
| T65_20_10 |           0.7   |     10.753 |            136.791  |               18 |       71 |        38.676 |        70.752 | False           | False         | False         | False         |
| T85_20_10 |           0.65  |     10.76  |            123.339  |               18 |       71 |        35.326 |        65.038 | False           | False         | False         | False         |
| T65_30_10 |           0.725 |     10.795 |            141.946  |               18 |       71 |        39.457 |        73.491 | False           | False         | False         | False         |
| T85_10_10 |           0.65  |     11.086 |            124.81   |               18 |       71 |        35.939 |        65.376 | False           | False         | False         | False         |
| T65_20_10 |           0.725 |     11.119 |            143.745  |               18 |       71 |        40.173 |        73.888 | False           | False         | False         | False         |
| T65_30_10 |           0.75  |     11.157 |            148.955  |               18 |       71 |        40.929 |        76.653 | False           | False         | False         | False         |
| T65_20_10 |           0.75  |     11.484 |            150.872  |               18 |       71 |        41.678 |        77.071 | False           | False         | False         | False         |
| T75_10_10 |           0.7   |     11.5   |            138.442  |               18 |       71 |        39.144 |        71.363 | False           | False         | False         | False         |
| T65_30_10 |           0.775 |     11.519 |            156.136  |               18 |       71 |        42.407 |        79.862 | False           | False         | True          | False         |
| T85_20_10 |           0.7   |     11.547 |            136.695  |               18 |       71 |        38.246 |        71.213 | False           | False         | False         | False         |
| T65_20_10 |           0.775 |     11.848 |            158.176  |               18 |       71 |        43.191 |        80.302 | False           | False         | True          | False         |
| T65_30_10 |           0.8   |     11.879 |            163.492  |               18 |       71 |        43.892 |        83.118 | True            | True          | True          | False         |
| T75_10_10 |           0.725 |     11.889 |            145.497  |               18 |       71 |        40.661 |        74.531 | False           | False         | False         | False         |
| T85_10_10 |           0.7   |     11.894 |            138.376  |               18 |       71 |        38.922 |        71.591 | False           | False         | False         | False         |
| T85_20_10 |           0.725 |     11.938 |            143.623  |               18 |       71 |        39.716 |        74.37  | False           | False         | False         | False         |
| T65_20_10 |           0.8   |     12.21  |            165.66   |               18 |       71 |        44.71  |        83.581 | True            | False         | False         | False         |

## Interpretation
No variant uses more than the original 1x notional. Expected profit can fall in future unseen regimes; volatility signal filters and adaptive sizing may overfit this heavily researched sample.
