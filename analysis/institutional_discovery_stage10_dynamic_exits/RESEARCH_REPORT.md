# Stage 10 — Let high-volume exhaustion reversal profits run beyond 200 points

## What changed
Entry signal: **unchanged Stage 8 M_exhaustion_reversal**, on any 5-minute boundary.
Compare gross fixed exits (200/300/500/800/1200), 200 NET activation trailing
(100/200 points or prior-volatility distance), and step-up locks
(first +50 NET lock then +100 for each additional +200 close-confirmed NET rise).
Original 100/200 fixed initial stops, plus a prior 24x5m-range scaled initial stop.
Holds 30/60/120/240m; one trade at a time across LONG and SHORT per model.

## Main comparisons (fixed200 initial stop, 120 minute max hold, standard taker)
| period                      | model                        |   trades |   win_rate |   net_mean |   net_total |   profit_factor |   max_drawdown |   avg_duration_min |   share_mfe_500 |   share_mfe_800 |
|:----------------------------|:-----------------------------|---------:|-----------:|-----------:|------------:|----------------:|---------------:|-------------------:|----------------:|----------------:|
| 2025_train                  | fixed1200                    |      307 |      19.54 |    -143.81 |   -44150.1  |           0.405 |       44750.6  |              56.03 |           22.48 |           10.42 |
| 2025_train                  | fixed200                     |      311 |      48.23 |    -123.64 |   -38453.4  |           0.213 |       38538.9  |              24.91 |            0.32 |            0    |
| 2025_train                  | fixed300                     |      309 |      39.48 |    -116.68 |   -36054.6  |           0.365 |       36244.2  |              31.3  |            0.97 |            0    |
| 2025_train                  | fixed500                     |      309 |      27.83 |    -124.5  |   -38471.8  |           0.424 |       38959    |              42.06 |           22.65 |            0    |
| 2025_train                  | fixed800                     |      307 |      19.87 |    -148.96 |   -45731.9  |           0.381 |       45932.2  |              50.91 |           22.48 |           10.42 |
| 2025_train                  | step100_per_200_after_net200 |      308 |      33.77 |    -143.36 |   -44156    |           0.287 |       44312.1  |              43.5  |           16.88 |            3.9  |
| 2025_train                  | trail100_after_net200        |      309 |      33.98 |    -123.89 |   -38282.6  |           0.382 |       38525.2  |              37.24 |           13.59 |            1.62 |
| 2025_train                  | trail200_after_net200        |      309 |      33.98 |    -138.07 |   -42663.3  |           0.311 |       42819.4  |              40.39 |           17.8  |            2.27 |
| 2025_train                  | trail_vol_after_net200       |      309 |      32.04 |    -137.24 |   -42408.1  |           0.321 |       42585.6  |              39.15 |           16.5  |            2.27 |
| 2026_H1_validation          | fixed1200                    |      125 |      27.2  |    -105.67 |   -13208.2  |           0.453 |       13466.3  |              69.66 |           18.4  |            6.4  |
| 2026_H1_validation          | fixed200                     |      126 |      46.03 |    -101.71 |   -12815.5  |           0.312 |       12935.3  |              40.02 |            0    |            0    |
| 2026_H1_validation          | fixed300                     |      125 |      33.6  |    -115.26 |   -14407.6  |           0.357 |       14584    |              48.94 |            1.6  |            0    |
| 2026_H1_validation          | fixed500                     |      125 |      30.4  |     -93.59 |   -11698.5  |           0.491 |       11874.9  |              59.45 |           18.4  |            0    |
| 2026_H1_validation          | fixed800                     |      125 |      28    |    -103.38 |   -12922.5  |           0.459 |       13098.9  |              67.06 |           18.4  |            6.4  |
| 2026_H1_validation          | step100_per_200_after_net200 |      125 |      33.6  |    -104.73 |   -13091.3  |           0.416 |       13663.1  |              61.87 |           15.2  |            4    |
| 2026_H1_validation          | trail100_after_net200        |      125 |      33.6  |    -102.7  |   -12837.8  |           0.427 |       13014.1  |              51.5  |            9.6  |            1.6  |
| 2026_H1_validation          | trail200_after_net200        |      125 |      33.6  |    -116.05 |   -14506.6  |           0.353 |       14683    |              56.46 |           12.8  |            1.6  |
| 2026_H1_validation          | trail_vol_after_net200       |      125 |      33.6  |    -102.5  |   -12812.2  |           0.429 |       12988.6  |              52.5  |           11.2  |            2.4  |
| 2026_H2_seen_recheck        | fixed1200                    |      114 |      27.19 |     -81.09 |    -9244.62 |           0.513 |        9384.75 |              78.84 |           16.67 |            7.89 |
| 2026_H2_seen_recheck        | fixed200                     |      118 |      46.61 |     -77.62 |    -9159.05 |           0.367 |        9875.18 |              48.32 |            0    |            0    |
| 2026_H2_seen_recheck        | fixed300                     |      118 |      37.29 |     -79.81 |    -9417.12 |           0.455 |        9612.93 |              54.84 |            0    |            0    |
| 2026_H2_seen_recheck        | fixed500                     |      116 |      30.17 |     -79.21 |    -9188.28 |           0.502 |        9411.36 |              69.84 |           17.24 |            0    |
| 2026_H2_seen_recheck        | fixed800                     |      116 |      28.45 |     -67.87 |    -7872.37 |           0.579 |        8295.22 |              75.86 |           17.24 |            8.62 |
| 2026_H2_seen_recheck        | step100_per_200_after_net200 |      116 |      36.21 |     -37.93 |    -4399.58 |           0.749 |        4995.15 |              72.88 |           15.52 |            7.76 |
| 2026_H2_seen_recheck        | trail100_after_net200        |      117 |      35.9  |     -71.52 |    -8367.26 |           0.524 |        8426.94 |              61.68 |            9.4  |            2.56 |
| 2026_H2_seen_recheck        | trail200_after_net200        |      117 |      35.9  |     -54.22 |    -6343.55 |           0.639 |        6483.68 |              67.46 |           15.38 |            7.69 |
| 2026_H2_seen_recheck        | trail_vol_after_net200       |      117 |      35.9  |     -65.15 |    -7622.22 |           0.566 |        7681.9  |              63.81 |           13.68 |            4.27 |
| 2026_Nov_recent_exploratory | fixed1200                    |       10 |      20    |    -111.26 |    -1112.63 |           0.325 |        1240.98 |             106.2  |           10    |           10    |
| 2026_Nov_recent_exploratory | fixed200                     |       11 |      63.64 |     -21.52 |     -236.77 |           0.751 |         646.88 |              56.64 |            0    |            0    |
| 2026_Nov_recent_exploratory | fixed300                     |       10 |      20    |    -124.28 |    -1242.79 |           0.246 |        1242.79 |              86.5  |            0    |            0    |
| 2026_Nov_recent_exploratory | fixed500                     |       10 |      20    |    -111.71 |    -1117.13 |           0.322 |        1240.98 |              97.9  |           10    |            0    |
| 2026_Nov_recent_exploratory | fixed800                     |       10 |      20    |     -81.7  |     -816.96 |           0.504 |        1240.98 |              98    |           10    |           10    |
| 2026_Nov_recent_exploratory | step100_per_200_after_net200 |       10 |      20    |    -124.79 |    -1247.93 |           0.243 |        1311.51 |              93.1  |           10    |           10    |
| 2026_Nov_recent_exploratory | trail100_after_net200        |       10 |      20    |    -140.53 |    -1405.31 |           0.147 |        1405.31 |              87    |            0    |            0    |
| 2026_Nov_recent_exploratory | trail200_after_net200        |       10 |      20    |     -95.1  |     -951    |           0.423 |        1270.96 |              89.8  |           10    |           10    |
| 2026_Nov_recent_exploratory | trail_vol_after_net200       |       10 |      20    |    -140.72 |    -1407.16 |           0.146 |        1407.16 |              88.1  |            0    |            0    |

## Chronological consistency for every model
| model                        | stop              |   horizon |   n2025 |   net2025 |   n2026h1 |   net2026h1 |   n2026h2 |   net2026h2 | adequate_sample   | all_positive   |
|:-----------------------------|:------------------|----------:|--------:|----------:|----------:|------------:|----------:|------------:|:------------------|:---------------|
| fixed1200                    | fixed100          |        30 |     317 |   -137.8  |       131 |      -98.92 |       120 |      -68.1  | True              | False          |
| fixed1200                    | fixed100          |        60 |     316 |   -143.23 |       131 |      -97.24 |       119 |      -68.75 | True              | False          |
| fixed1200                    | fixed100          |       120 |     316 |   -140.25 |       130 |      -83.32 |       116 |      -86.72 | True              | False          |
| fixed1200                    | fixed100          |       240 |     316 |   -142.99 |       127 |      -86.65 |       115 |      -94.19 | True              | False          |
| fixed1200                    | fixed200          |        30 |     309 |   -127.09 |       128 |      -96.19 |       118 |      -71.18 | True              | False          |
| fixed1200                    | fixed200          |        60 |     307 |   -136.04 |       128 |      -99.46 |       117 |      -63.49 | True              | False          |
| fixed1200                    | fixed200          |       120 |     307 |   -143.81 |       125 |     -105.67 |       114 |      -81.09 | True              | False          |
| fixed1200                    | fixed200          |       240 |     304 |   -142.18 |       123 |     -117.95 |       112 |      -83    | True              | False          |
| fixed1200                    | volatility_scaled |        30 |     310 |   -126.96 |       130 |     -103.81 |       120 |      -73.23 | True              | False          |
| fixed1200                    | volatility_scaled |        60 |     309 |   -126.29 |       130 |     -110.12 |       119 |      -70.72 | True              | False          |
| fixed1200                    | volatility_scaled |       120 |     309 |   -136.87 |       129 |     -115.62 |       116 |      -92.16 | True              | False          |
| fixed1200                    | volatility_scaled |       240 |     308 |   -139.93 |       126 |     -120.79 |       115 |     -103.18 | True              | False          |
| fixed200                     | fixed100          |        30 |     319 |   -120.77 |       131 |      -97.38 |       121 |      -91.22 | True              | False          |
| fixed200                     | fixed100          |        60 |     319 |   -120.54 |       131 |      -94.39 |       121 |      -95.22 | True              | False          |
| fixed200                     | fixed100          |       120 |     319 |   -121.16 |       131 |      -94.83 |       120 |      -95.88 | True              | False          |
| fixed200                     | fixed100          |       240 |     319 |   -119.51 |       130 |      -96.54 |       120 |      -96.14 | True              | False          |
| fixed200                     | fixed200          |        30 |     312 |   -117.07 |       128 |      -88.22 |       119 |      -87.84 | True              | False          |
| fixed200                     | fixed200          |        60 |     311 |   -119.05 |       128 |      -90.78 |       119 |      -87.52 | True              | False          |
| fixed200                     | fixed200          |       120 |     311 |   -123.64 |       126 |     -101.71 |       118 |      -77.62 | True              | False          |
| fixed200                     | fixed200          |       240 |     311 |   -118.57 |       126 |     -108.74 |       117 |      -74.63 | True              | False          |
| fixed200                     | volatility_scaled |        30 |     313 |   -119.71 |       130 |      -95.76 |       121 |      -90.37 | True              | False          |
| fixed200                     | volatility_scaled |        60 |     313 |   -119.81 |       130 |      -96.68 |       121 |      -88.88 | True              | False          |
| fixed200                     | volatility_scaled |       120 |     313 |   -123.6  |       130 |     -103.06 |       120 |      -84.24 | True              | False          |
| fixed200                     | volatility_scaled |       240 |     313 |   -120.16 |       129 |     -105.79 |       120 |      -83.9  | True              | False          |
| fixed300                     | fixed100          |        30 |     318 |   -114.81 |       131 |      -98.49 |       121 |      -84.8  | True              | False          |
| fixed300                     | fixed100          |        60 |     318 |   -113.39 |       131 |      -98.54 |       121 |      -87.44 | True              | False          |
| fixed300                     | fixed100          |       120 |     318 |   -114.38 |       130 |      -94.27 |       120 |      -89.12 | True              | False          |
| fixed300                     | fixed100          |       240 |     318 |   -112.78 |       129 |      -95.18 |       120 |      -90.14 | True              | False          |
| fixed300                     | fixed200          |        30 |     310 |   -109.23 |       128 |      -93.07 |       119 |      -84.77 | True              | False          |
| fixed300                     | fixed200          |        60 |     309 |   -108.46 |       128 |     -103.63 |       119 |      -84.55 | True              | False          |
| fixed300                     | fixed200          |       120 |     309 |   -116.68 |       125 |     -115.26 |       118 |      -79.81 | True              | False          |
| fixed300                     | fixed200          |       240 |     308 |   -110.72 |       125 |     -121.36 |       117 |      -69.33 | True              | False          |
| fixed300                     | volatility_scaled |        30 |     311 |   -111.52 |       130 |     -100.65 |       121 |      -86.79 | True              | False          |
| fixed300                     | volatility_scaled |        60 |     311 |   -107.18 |       130 |     -110.81 |       121 |      -86.14 | True              | False          |
| fixed300                     | volatility_scaled |       120 |     311 |   -114.26 |       129 |     -118.33 |       120 |      -85.74 | True              | False          |
| fixed300                     | volatility_scaled |       240 |     311 |   -110.54 |       128 |     -120.86 |       120 |      -78.91 | True              | False          |
| fixed500                     | fixed100          |        30 |     318 |   -122.53 |       131 |      -93.92 |       120 |      -74.55 | True              | False          |
| fixed500                     | fixed100          |        60 |     318 |   -119.99 |       131 |      -88.93 |       120 |      -77.27 | True              | False          |
| fixed500                     | fixed100          |       120 |     318 |   -119.4  |       130 |      -72.39 |       118 |      -78.39 | True              | False          |
| fixed500                     | fixed100          |       240 |     318 |   -118.12 |       129 |      -67.61 |       118 |      -72.51 | True              | False          |
| fixed500                     | fixed200          |        30 |     310 |   -113.63 |       128 |      -87.75 |       118 |      -77.74 | True              | False          |
| fixed500                     | fixed200          |        60 |     309 |   -113.03 |       128 |      -91.98 |       118 |      -78.99 | True              | False          |
| fixed500                     | fixed200          |       120 |     309 |   -124.5  |       125 |      -93.59 |       116 |      -79.21 | True              | False          |
| fixed500                     | fixed200          |       240 |     307 |   -117.12 |       125 |      -84.31 |       115 |      -62.49 | True              | False          |
| fixed500                     | volatility_scaled |        30 |     311 |   -116.81 |       130 |      -93.87 |       120 |      -79.68 | True              | False          |
| fixed500                     | volatility_scaled |        60 |     311 |   -109.61 |       130 |      -97.66 |       120 |      -80.06 | True              | False          |
| fixed500                     | volatility_scaled |       120 |     311 |   -122.2  |       129 |      -96.53 |       118 |      -84.4  | True              | False          |
| fixed500                     | volatility_scaled |       240 |     310 |   -117.21 |       128 |      -86.42 |       118 |      -75.99 | True              | False          |
| fixed800                     | fixed100          |        30 |     317 |   -137.23 |       131 |      -97.52 |       120 |      -71.23 | True              | False          |
| fixed800                     | fixed100          |        60 |     316 |   -140.26 |       131 |      -93.43 |       120 |      -67.12 | True              | False          |
| fixed800                     | fixed100          |       120 |     316 |   -139.89 |       130 |      -83.47 |       118 |      -72.02 | True              | False          |
| fixed800                     | fixed100          |       240 |     316 |   -135.41 |       128 |      -81.93 |       117 |      -72.1  | True              | False          |
| fixed800                     | fixed200          |        30 |     309 |   -126.74 |       128 |      -92.59 |       118 |      -74.36 | True              | False          |
| fixed800                     | fixed200          |        60 |     307 |   -135.2  |       128 |      -93.99 |       118 |      -63.58 | True              | False          |
| fixed800                     | fixed200          |       120 |     307 |   -148.96 |       125 |     -103.38 |       116 |      -67.87 | True              | False          |
| fixed800                     | fixed200          |       240 |     304 |   -139.23 |       124 |     -107.18 |       114 |      -64.67 | True              | False          |
| fixed800                     | volatility_scaled |        30 |     310 |   -127.23 |       130 |     -100.27 |       120 |      -76.36 | True              | False          |
| fixed800                     | volatility_scaled |        60 |     309 |   -127.62 |       130 |     -104.73 |       120 |      -67.41 | True              | False          |
| fixed800                     | volatility_scaled |       120 |     309 |   -144.75 |       129 |     -113.34 |       118 |      -75.79 | True              | False          |
| fixed800                     | volatility_scaled |       240 |     308 |   -138.33 |       127 |     -109.71 |       117 |      -82.48 | True              | False          |
| step100_per_200_after_net200 | fixed100          |        30 |     318 |   -133.31 |       131 |      -98    |       120 |      -70.04 | True              | False          |
| step100_per_200_after_net200 | fixed100          |        60 |     317 |   -133.86 |       131 |      -96.63 |       119 |      -70.41 | True              | False          |
| step100_per_200_after_net200 | fixed100          |       120 |     317 |   -136.84 |       130 |      -89.87 |       118 |      -42.98 | True              | False          |
| step100_per_200_after_net200 | fixed100          |       240 |     317 |   -129.9  |       128 |      -88.16 |       118 |      -52.18 | True              | False          |
| step100_per_200_after_net200 | fixed200          |        30 |     310 |   -129.24 |       128 |      -91.19 |       118 |      -73.15 | True              | False          |
| step100_per_200_after_net200 | fixed200          |        60 |     308 |   -132.17 |       128 |      -93.76 |       117 |      -68.21 | True              | False          |
| step100_per_200_after_net200 | fixed200          |       120 |     308 |   -143.36 |       125 |     -104.73 |       116 |      -37.93 | True              | False          |
| step100_per_200_after_net200 | fixed200          |       240 |     305 |   -131.93 |       124 |     -111.06 |       115 |      -41.35 | True              | False          |
| step100_per_200_after_net200 | volatility_scaled |        30 |     311 |   -129.2  |       130 |      -99.8  |       120 |      -75.17 | True              | False          |
| step100_per_200_after_net200 | volatility_scaled |        60 |     310 |   -125.77 |       130 |     -101.7  |       119 |      -71.65 | True              | False          |
| step100_per_200_after_net200 | volatility_scaled |       120 |     310 |   -140.62 |       129 |     -105.52 |       118 |      -43.43 | True              | False          |
| step100_per_200_after_net200 | volatility_scaled |       240 |     309 |   -130.82 |       127 |     -109.73 |       118 |      -48.25 | True              | False          |
| trail100_after_net200        | fixed100          |        30 |     318 |   -122.17 |       131 |      -93.11 |       120 |      -73.96 | True              | False          |
| trail100_after_net200        | fixed100          |        60 |     318 |   -117.78 |       131 |      -92.84 |       120 |      -79.32 | True              | False          |
| trail100_after_net200        | fixed100          |       120 |     318 |   -118.79 |       130 |      -86.03 |       119 |      -74.38 | True              | False          |
| trail100_after_net200        | fixed100          |       240 |     318 |   -117.91 |       129 |      -86.83 |       119 |      -75.41 | True              | False          |
| trail100_after_net200        | fixed200          |        30 |     310 |   -117.71 |       128 |      -84.94 |       118 |      -77.14 | True              | False          |
| trail100_after_net200        | fixed200          |        60 |     309 |   -113.07 |       128 |      -92.02 |       118 |      -81.34 | True              | False          |
| trail100_after_net200        | fixed200          |       120 |     309 |   -123.89 |       125 |     -102.7  |       117 |      -71.52 | True              | False          |
| trail100_after_net200        | fixed200          |       240 |     307 |   -119.52 |       125 |     -107.27 |       116 |      -67.13 | True              | False          |
| trail100_after_net200        | volatility_scaled |        30 |     311 |   -118    |       130 |      -92.69 |       120 |      -79.09 | True              | False          |
| trail100_after_net200        | volatility_scaled |        60 |     311 |   -109.47 |       130 |      -99.46 |       120 |      -81.62 | True              | False          |
| trail100_after_net200        | volatility_scaled |       120 |     311 |   -119.03 |       129 |     -104.51 |       119 |      -76.77 | True              | False          |
| trail100_after_net200        | volatility_scaled |       240 |     310 |   -117.65 |       128 |     -105.82 |       119 |      -73.51 | True              | False          |
| trail200_after_net200        | fixed100          |        30 |     318 |   -130.31 |       131 |      -97.19 |       120 |      -71.7  | True              | False          |
| trail200_after_net200        | fixed100          |        60 |     318 |   -126.65 |       131 |      -98.02 |       120 |      -74.15 | True              | False          |
| trail200_after_net200        | fixed100          |       120 |     318 |   -130.66 |       130 |      -95.24 |       119 |      -63.53 | True              | False          |
| trail200_after_net200        | fixed100          |       240 |     318 |   -129.19 |       129 |      -96.83 |       119 |      -65.86 | True              | False          |
| trail200_after_net200        | fixed200          |        30 |     310 |   -127.79 |       128 |      -89.77 |       118 |      -74.84 | True              | False          |
| trail200_after_net200        | fixed200          |        60 |     309 |   -124.6  |       128 |      -99.14 |       118 |      -70.89 | True              | False          |
| trail200_after_net200        | fixed200          |       120 |     309 |   -138.07 |       125 |     -116.05 |       117 |      -54.22 | True              | False          |
| trail200_after_net200        | fixed200          |       240 |     307 |   -134.33 |       125 |     -122.31 |       116 |      -55.01 | True              | False          |
| trail200_after_net200        | volatility_scaled |        30 |     311 |   -126.98 |       130 |      -98.22 |       120 |      -76.83 | True              | False          |
| trail200_after_net200        | volatility_scaled |        60 |     311 |   -120.02 |       130 |     -106.82 |       120 |      -75.24 | True              | False          |
| trail200_after_net200        | volatility_scaled |       120 |     311 |   -133.57 |       129 |     -116.82 |       119 |      -62.85 | True              | False          |
| trail200_after_net200        | volatility_scaled |       240 |     310 |   -132.52 |       128 |     -119.72 |       119 |      -63.95 | True              | False          |
| trail_vol_after_net200       | fixed100          |        30 |     318 |   -130.32 |       131 |      -94.94 |       120 |      -72.95 | True              | False          |
| trail_vol_after_net200       | fixed100          |        60 |     318 |   -126.28 |       131 |      -94.22 |       120 |      -74.1  | True              | False          |
| trail_vol_after_net200       | fixed100          |       120 |     318 |   -128.07 |       130 |      -88.71 |       119 |      -72.32 | True              | False          |
| trail_vol_after_net200       | fixed100          |       240 |     318 |   -126.9  |       129 |      -89.53 |       119 |      -73.35 | True              | False          |
| trail_vol_after_net200       | fixed200          |        30 |     310 |   -128.19 |       128 |      -87.84 |       118 |      -76.11 | True              | False          |
| trail_vol_after_net200       | fixed200          |        60 |     309 |   -125.18 |       128 |      -89.14 |       118 |      -73.53 | True              | False          |
| trail_vol_after_net200       | fixed200          |       120 |     309 |   -137.24 |       125 |     -102.5  |       117 |      -65.15 | True              | False          |
| trail_vol_after_net200       | fixed200          |       240 |     307 |   -131.7  |       125 |     -107.07 |       116 |      -60.71 | True              | False          |
| trail_vol_after_net200       | volatility_scaled |        30 |     311 |   -127.94 |       130 |      -95.69 |       120 |      -78.08 | True              | False          |
| trail_vol_after_net200       | volatility_scaled |        60 |     311 |   -120.19 |       130 |      -96.72 |       120 |      -73.86 | True              | False          |
| trail_vol_after_net200       | volatility_scaled |       120 |     311 |   -132.04 |       129 |     -104.4  |       119 |      -70.1  | True              | False          |
| trail_vol_after_net200       | volatility_scaled |       240 |     310 |   -129.47 |       128 |     -105.71 |       119 |      -66.84 | True              | False          |

## Stable positive variants (>= 50 / 25 / 25 independent 2025 / H1 / H2 trades)
No consistently positive variant found.

## Caveats
- M exhaustion reversal entry reproduced EXACTLY from Stage8
- Entry at first minute OPEN after complete 5m reversal signal
- Both directions share at most one position at a time within a given model
- Fixed targets are gross price points; trailing activation is fee-aware net +200 at close
- Trailing updates use CLOSED minute only, next minute stop check
- Stop checked before target if both touched in same minute
- Gapped stops fill at worse of minute open or stop level
- Time exits at last minute close; no extrapolation outside real minute data
- Taker fees 0.05% per side plus GST 18%; 5 points adverse slippage per side
- Hypothetical waived closing fee only for <=30m; historical eligibility unverified
- No funding, mark price liquidation, bid/ask spread, impact or maker execution
- Positive historical cells subject to many-tests bias, previously seen 2026 is not an independent holdout
- No target/stop or profit lock can guarantee zero losing trades

## Reproduce
- scripts/research_dynamic_exit_stage10.py
- exit_comparison.csv — every period, exit, stop, horizon and fee model
- chronological_consistency.csv — stability audit
- trade_ledger.csv.gz — full raw evidence in GitHub Actions artifact
- quality.json — fee, fill and data limitations
