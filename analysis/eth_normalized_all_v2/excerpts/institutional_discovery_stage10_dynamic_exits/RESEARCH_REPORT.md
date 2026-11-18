# Stage 10 — Let high-volume exhaustion reversal profits run beyond 200 points

## What changed
Entry signal: **unchanged Stage 8 M_exhaustion_reversal**, on any 5-minute boundary.
Compare gross fixed exits (200/300/500/800/1200), 200 NET activation trailing
(100/200 points or prior-volatility distance), and step-up locks
(first +50 NET lock then +100 for each additional +200 close-confirmed NET rise).
Original 100/200 fixed initial stops, plus a prior 24x5m-range scaled initial stop.
Holds 30/60/120/240m; one trade at a time across LONG and SHORT per model.

## Main comparisons (fixed200 initial stop, 120 minute max hold, standard taker)
| period               | model                        |   trades |   win_rate |   net_mean |   net_total |   profit_factor |   max_drawdown |   avg_duration_min |   share_mfe_500 |   share_mfe_800 |
|:---------------------|:-----------------------------|---------:|-----------:|-----------:|------------:|----------------:|---------------:|-------------------:|----------------:|----------------:|
| 2025_train           | fixed1200                    |      250 |      21.2  |    -112.87 |   -28217.9  |           0.529 |       30131.7  |              40.34 |           24.4  |           12.8  |
| 2025_train           | fixed200                     |      254 |      48.03 |    -120.56 |   -30622.9  |           0.259 |       30871.3  |              15.11 |            2.36 |            0    |
| 2025_train           | fixed300                     |      253 |      38.34 |    -120.59 |   -30508.8  |           0.373 |       30880.3  |              19.45 |            2.77 |            0    |
| 2025_train           | fixed500                     |      253 |      28.85 |    -116.29 |   -29422.3  |           0.468 |       30398.3  |              27.68 |           24.11 |            0.79 |
| 2025_train           | fixed800                     |      251 |      22.71 |    -124.76 |   -31313.7  |           0.471 |       31819.8  |              36.5  |           24.3  |           12.75 |
| 2025_train           | step100_per_200_after_net200 |      253 |      32.02 |    -153.2  |   -38759.8  |           0.278 |       39064.4  |              28.69 |           17    |            3.95 |
| 2025_train           | trail100_after_net200        |      253 |      32.02 |    -134.93 |   -34136.7  |           0.364 |       34789.8  |              22.91 |           13.83 |            1.58 |
| 2025_train           | trail200_after_net200        |      253 |      31.62 |    -147.5  |   -37317.8  |           0.305 |       37671.7  |              25.43 |           17    |            2.77 |
| 2025_train           | trail_vol_after_net200       |      252 |      26.59 |    -157.39 |   -39663.1  |           0.272 |       40071.5  |              25.01 |           16.67 |            3.97 |
| 2026_H1_validation   | fixed1200                    |      107 |      31.78 |     -49.36 |    -5281.95 |           0.714 |        5732.64 |              66.95 |           23.36 |           13.08 |
| 2026_H1_validation   | fixed200                     |      108 |      50.93 |     -68.66 |    -7415.46 |           0.456 |        7428.6  |              30.05 |            0.93 |            0    |
| 2026_H1_validation   | fixed300                     |      108 |      44.44 |     -52.29 |    -5647.46 |           0.632 |        5660.6  |              39.09 |            5.56 |            0    |
| 2026_H1_validation   | fixed500                     |      107 |      37.38 |     -42.7  |    -4568.79 |           0.734 |        4581.93 |              51.04 |           23.36 |            0    |
| 2026_H1_validation   | fixed800                     |      107 |      33.64 |     -33.03 |    -3534.31 |           0.804 |        4103.9  |              60.48 |           23.36 |           13.08 |
| 2026_H1_validation   | step100_per_200_after_net200 |      108 |      42.59 |     -64.77 |    -6995.54 |           0.561 |        7008.68 |              54.04 |           19.44 |            8.33 |
| 2026_H1_validation   | trail100_after_net200        |      108 |      42.59 |     -51.09 |    -5517.41 |           0.654 |        5530.55 |              43.64 |           12.04 |            3.7  |
| 2026_H1_validation   | trail200_after_net200        |      108 |      42.59 |     -51.25 |    -5535.22 |           0.653 |        5548.36 |              48.84 |           19.44 |            7.41 |
| 2026_H1_validation   | trail_vol_after_net200       |      108 |      42.59 |     -50.22 |    -5424.07 |           0.66  |        5437.21 |              46.74 |           19.44 |            6.48 |
| 2026_H2_seen_recheck | fixed1200                    |      108 |      29.63 |     -92.32 |    -9971.05 |           0.481 |       10147.7  |              69.79 |           14.81 |            4.63 |
| 2026_H2_seen_recheck | fixed200                     |      109 |      44.95 |     -92.53 |   -10086.1  |           0.339 |       10429.9  |              39.51 |            0    |            0    |
| 2026_H2_seen_recheck | fixed300                     |      109 |      37.61 |     -92.02 |   -10029.8  |           0.418 |       10127.9  |              48.38 |            0.92 |            0    |
| 2026_H2_seen_recheck | fixed500                     |      109 |      31.19 |     -98.18 |   -10701.6  |           0.435 |       10786.8  |              61.15 |           15.6  |            0.92 |
| 2026_H2_seen_recheck | fixed800                     |      109 |      31.19 |     -86.9  |    -9472.14 |           0.5   |        9648.82 |              68.37 |           15.6  |            5.5  |
| 2026_H2_seen_recheck | step100_per_200_after_net200 |      109 |      35.78 |     -83.34 |    -9084.33 |           0.49  |        9497.35 |              61.72 |           13.76 |            2.75 |
| 2026_H2_seen_recheck | trail100_after_net200        |      109 |      35.78 |     -90.46 |    -9860.4  |           0.446 |        9939.94 |              52.15 |            9.17 |            1.83 |
| 2026_H2_seen_recheck | trail200_after_net200        |      109 |      35.78 |    -106.78 |   -11638.9  |           0.347 |       11815.6  |              56.05 |           11.93 |            1.83 |
| 2026_H2_seen_recheck | trail_vol_after_net200       |      109 |      34.86 |     -99.62 |   -10858.3  |           0.391 |       10960.9  |              52.91 |           10.09 |            1.83 |

## Chronological consistency for every model
| model                        | stop              |   horizon |   n2025 |   net2025 |   n2026h1 |   net2026h1 |   n2026h2 |   net2026h2 | adequate_sample   | all_positive   |
|:-----------------------------|:------------------|----------:|--------:|----------:|----------:|------------:|----------:|------------:|:------------------|:---------------|
| fixed1200                    | fixed100          |        30 |     256 |   -105.92 |       108 |      -78.91 |       113 |      -85.18 | True              | False          |
| fixed1200                    | fixed100          |        60 |     255 |   -111.65 |       108 |      -81.25 |       113 |      -69.31 | True              | False          |
| fixed1200                    | fixed100          |       120 |     255 |   -108.42 |       108 |      -70.72 |       113 |      -76.16 | True              | False          |
| fixed1200                    | fixed100          |       240 |     253 |   -111.89 |       108 |      -55.96 |       109 |      -62.44 | True              | False          |
| fixed1200                    | fixed200          |        30 |     253 |   -109.23 |       107 |      -63.05 |       110 |      -87.61 | True              | False          |
| fixed1200                    | fixed200          |        60 |     252 |   -121.15 |       107 |      -54.5  |       110 |      -75.47 | True              | False          |
| fixed1200                    | fixed200          |       120 |     250 |   -112.87 |       107 |      -49.36 |       108 |      -92.32 | True              | False          |
| fixed1200                    | fixed200          |       240 |     247 |   -121.99 |       106 |      -28.3  |       105 |      -85.43 | True              | False          |
| fixed1200                    | volatility_scaled |        30 |     255 |   -107.68 |       107 |      -68.75 |       112 |      -78.22 | True              | False          |
| fixed1200                    | volatility_scaled |        60 |     254 |   -132.34 |       107 |      -63.09 |       112 |      -63.17 | True              | False          |
| fixed1200                    | volatility_scaled |       120 |     252 |   -139.25 |       107 |      -57.56 |       110 |      -76.18 | True              | False          |
| fixed1200                    | volatility_scaled |       240 |     249 |   -163.67 |       105 |      -41.76 |       107 |      -70.75 | True              | False          |
| fixed200                     | fixed100          |        30 |     257 |   -122.82 |       108 |      -66.91 |       113 |      -90.18 | True              | False          |
| fixed200                     | fixed100          |        60 |     257 |   -122.56 |       108 |      -65.25 |       113 |      -88.21 | True              | False          |
| fixed200                     | fixed100          |       120 |     257 |   -122.13 |       108 |      -67.26 |       113 |      -89.3  | True              | False          |
| fixed200                     | fixed100          |       240 |     257 |   -121.5  |       108 |      -67.84 |       113 |      -86.87 | True              | False          |
| fixed200                     | fixed200          |        30 |     254 |   -121.06 |       108 |      -68.8  |       110 |      -91.67 | True              | False          |
| fixed200                     | fixed200          |        60 |     254 |   -120.97 |       108 |      -65.44 |       110 |      -90.78 | True              | False          |
| fixed200                     | fixed200          |       120 |     254 |   -120.56 |       108 |      -68.66 |       109 |      -92.53 | True              | False          |
| fixed200                     | fixed200          |       240 |     254 |   -120.39 |       108 |      -67.1  |       109 |      -93.3  | True              | False          |
| fixed200                     | volatility_scaled |        30 |     256 |   -112.33 |       108 |      -72.69 |       112 |      -83.3  | True              | False          |
| fixed200                     | volatility_scaled |        60 |     256 |   -113.06 |       108 |      -75.12 |       112 |      -81.12 | True              | False          |
| fixed200                     | volatility_scaled |       120 |     256 |   -111.94 |       108 |      -76.09 |       111 |      -79.91 | True              | False          |
| fixed200                     | volatility_scaled |       240 |     256 |   -111.57 |       108 |      -78.44 |       111 |      -80.37 | True              | False          |
| fixed300                     | fixed100          |        30 |     257 |   -118.38 |       108 |      -66.83 |       113 |      -90.8  | True              | False          |
| fixed300                     | fixed100          |        60 |     257 |   -119.42 |       108 |      -62.26 |       113 |      -80.35 | True              | False          |
| fixed300                     | fixed100          |       120 |     257 |   -118.28 |       108 |      -57.38 |       113 |      -82.11 | True              | False          |
| fixed300                     | fixed100          |       240 |     257 |   -116.14 |       108 |      -59.82 |       113 |      -78.74 | True              | False          |
| fixed300                     | fixed200          |        30 |     254 |   -119.63 |       108 |      -58.17 |       110 |      -92.09 | True              | False          |
| fixed300                     | fixed200          |        60 |     254 |   -119.81 |       108 |      -53.5  |       110 |      -81.77 | True              | False          |
| fixed300                     | fixed200          |       120 |     253 |   -120.59 |       108 |      -52.29 |       109 |      -92.02 | True              | False          |
| fixed300                     | fixed200          |       240 |     253 |   -119.37 |       108 |      -53.76 |       109 |      -91.81 | True              | False          |
| fixed300                     | volatility_scaled |        30 |     256 |   -120.48 |       108 |      -64.96 |       112 |      -85.76 | True              | False          |
| fixed300                     | volatility_scaled |        60 |     256 |   -124.08 |       108 |      -63.97 |       112 |      -71.84 | True              | False          |
| fixed300                     | volatility_scaled |       120 |     255 |   -128.74 |       108 |      -57.59 |       111 |      -78.75 | True              | False          |
| fixed300                     | volatility_scaled |       240 |     255 |   -126.75 |       108 |      -63.3  |       111 |      -74.95 | True              | False          |
| fixed500                     | fixed100          |        30 |     257 |   -114.66 |       108 |      -69.28 |       113 |      -91.38 | True              | False          |
| fixed500                     | fixed100          |        60 |     257 |   -113.8  |       108 |      -68.75 |       113 |      -79.78 | True              | False          |
| fixed500                     | fixed100          |       120 |     257 |   -109.73 |       108 |      -65.98 |       113 |      -85.74 | True              | False          |
| fixed500                     | fixed100          |       240 |     257 |   -109.7  |       108 |      -58.92 |       112 |      -72.35 | True              | False          |
| fixed500                     | fixed200          |        30 |     254 |   -119.62 |       107 |      -48.49 |       110 |      -97.09 | True              | False          |
| fixed500                     | fixed200          |        60 |     254 |   -120.76 |       107 |      -40.93 |       110 |      -83.34 | True              | False          |
| fixed500                     | fixed200          |       120 |     253 |   -116.29 |       107 |      -42.7  |       109 |      -98.18 | True              | False          |
| fixed500                     | fixed200          |       240 |     253 |   -114.85 |       107 |      -33.49 |       108 |      -86.55 | True              | False          |
| fixed500                     | volatility_scaled |        30 |     256 |   -117.49 |       107 |      -54.66 |       112 |      -87.53 | True              | False          |
| fixed500                     | volatility_scaled |        60 |     256 |   -120.76 |       107 |      -50.55 |       112 |      -70.9  | True              | False          |
| fixed500                     | volatility_scaled |       120 |     255 |   -117.76 |       107 |      -47.14 |       111 |      -82.07 | True              | False          |
| fixed500                     | volatility_scaled |       240 |     255 |   -114.92 |       107 |      -41.03 |       110 |      -70.61 | True              | False          |
| fixed800                     | fixed100          |        30 |     256 |   -113.07 |       108 |      -68.79 |       113 |      -88.73 | True              | False          |
| fixed800                     | fixed100          |        60 |     255 |   -113.66 |       108 |      -56.05 |       113 |      -74.92 | True              | False          |
| fixed800                     | fixed100          |       120 |     255 |   -111.94 |       108 |      -48.04 |       113 |      -83.36 | True              | False          |
| fixed800                     | fixed100          |       240 |     255 |   -113.63 |       108 |      -27.79 |       109 |      -73.82 | True              | False          |
| fixed800                     | fixed200          |        30 |     253 |   -116.4  |       107 |      -53.24 |       110 |      -91.63 | True              | False          |
| fixed800                     | fixed200          |        60 |     252 |   -124.86 |       107 |      -30.97 |       110 |      -84.86 | True              | False          |
| fixed800                     | fixed200          |       120 |     251 |   -124.76 |       107 |      -33.03 |       109 |      -86.9  | True              | False          |
| fixed800                     | fixed200          |       240 |     249 |   -135.72 |       106 |      -11.37 |       106 |      -81.41 | True              | False          |
| fixed800                     | volatility_scaled |        30 |     255 |   -114.47 |       107 |      -58.95 |       112 |      -82.17 | True              | False          |
| fixed800                     | volatility_scaled |        60 |     254 |   -126.55 |       107 |      -40    |       112 |      -72.4  | True              | False          |
| fixed800                     | volatility_scaled |       120 |     253 |   -127.05 |       107 |      -36.6  |       111 |      -71    | True              | False          |
| fixed800                     | volatility_scaled |       240 |     251 |   -145.9  |       106 |      -16.4  |       108 |      -66.93 | True              | False          |
| step100_per_200_after_net200 | fixed100          |        30 |     257 |   -130.42 |       108 |      -74.25 |       113 |      -84.91 | True              | False          |
| step100_per_200_after_net200 | fixed100          |        60 |     257 |   -133.18 |       108 |      -74.73 |       113 |      -71.86 | True              | False          |
| step100_per_200_after_net200 | fixed100          |       120 |     257 |   -130.96 |       108 |      -64.96 |       113 |      -87.47 | True              | False          |
| step100_per_200_after_net200 | fixed100          |       240 |     257 |   -133.18 |       108 |      -41.87 |       109 |      -72.55 | True              | False          |
| step100_per_200_after_net200 | fixed200          |        30 |     254 |   -136.61 |       108 |      -65.05 |       110 |      -87.11 | True              | False          |
| step100_per_200_after_net200 | fixed200          |        60 |     254 |   -149.03 |       108 |      -66.7  |       110 |      -71.48 | True              | False          |
| step100_per_200_after_net200 | fixed200          |       120 |     253 |   -153.2  |       108 |      -64.77 |       109 |      -83.34 | True              | False          |
| step100_per_200_after_net200 | fixed200          |       240 |     253 |   -155.92 |       108 |      -40.11 |       106 |      -75.46 | True              | False          |
| step100_per_200_after_net200 | volatility_scaled |        30 |     256 |   -138.61 |       108 |      -71.83 |       112 |      -77.83 | True              | False          |
| step100_per_200_after_net200 | volatility_scaled |        60 |     256 |   -161.96 |       108 |      -76.91 |       112 |      -58.71 | True              | False          |
| step100_per_200_after_net200 | volatility_scaled |       120 |     255 |   -168.8  |       108 |      -69.71 |       111 |      -67.44 | True              | False          |
| step100_per_200_after_net200 | volatility_scaled |       240 |     255 |   -165.24 |       108 |      -49.41 |       108 |      -55.22 | True              | False          |
| trail100_after_net200        | fixed100          |        30 |     257 |   -118.28 |       108 |      -69.69 |       113 |      -89.5  | True              | False          |
| trail100_after_net200        | fixed100          |        60 |     257 |   -121.17 |       108 |      -61.52 |       113 |      -79.87 | True              | False          |
| trail100_after_net200        | fixed100          |       120 |     257 |   -121.62 |       108 |      -61.35 |       113 |      -81.82 | True              | False          |
| trail100_after_net200        | fixed100          |       240 |     257 |   -120.02 |       108 |      -57.27 |       112 |      -72.9  | True              | False          |
| trail100_after_net200        | fixed200          |        30 |     254 |   -127.87 |       108 |      -55.79 |       110 |      -90.12 | True              | False          |
| trail100_after_net200        | fixed200          |        60 |     254 |   -132.11 |       108 |      -45.17 |       110 |      -79.83 | True              | False          |
| trail100_after_net200        | fixed200          |       120 |     253 |   -134.93 |       108 |      -51.09 |       109 |      -90.46 | True              | False          |
| trail100_after_net200        | fixed200          |       240 |     253 |   -134.78 |       108 |      -45.71 |       108 |      -82.87 | True              | False          |
| trail100_after_net200        | volatility_scaled |        30 |     256 |   -132.67 |       108 |      -62.57 |       112 |      -79.74 | True              | False          |
| trail100_after_net200        | volatility_scaled |        60 |     256 |   -141.28 |       108 |      -55.38 |       112 |      -65.85 | True              | False          |
| trail100_after_net200        | volatility_scaled |       120 |     255 |   -146.74 |       108 |      -56.02 |       111 |      -73.37 | True              | False          |
| trail100_after_net200        | volatility_scaled |       240 |     255 |   -144.4  |       108 |      -55.22 |       110 |      -62.63 | True              | False          |
| trail200_after_net200        | fixed100          |        30 |     257 |   -123.91 |       108 |      -72.75 |       113 |      -92.16 | True              | False          |
| trail200_after_net200        | fixed100          |        60 |     257 |   -130.82 |       108 |      -68.72 |       113 |      -82.63 | True              | False          |
| trail200_after_net200        | fixed100          |       120 |     257 |   -129.92 |       108 |      -59.65 |       113 |      -94.24 | True              | False          |
| trail200_after_net200        | fixed100          |       240 |     257 |   -130.36 |       108 |      -44.54 |       111 |      -81.33 | True              | False          |
| trail200_after_net200        | fixed200          |        30 |     254 |   -134.44 |       108 |      -59.88 |       110 |      -94.67 | True              | False          |
| trail200_after_net200        | fixed200          |        60 |     254 |   -144.94 |       108 |      -52.97 |       110 |      -86.06 | True              | False          |
| trail200_after_net200        | fixed200          |       120 |     253 |   -147.5  |       108 |      -51.25 |       109 |     -106.78 | True              | False          |
| trail200_after_net200        | fixed200          |       240 |     253 |   -147.96 |       108 |      -35.94 |       107 |      -96.89 | True              | False          |
| trail200_after_net200        | volatility_scaled |        30 |     256 |   -139.98 |       108 |      -66.66 |       112 |      -85.1  | True              | False          |
| trail200_after_net200        | volatility_scaled |        60 |     256 |   -155.63 |       108 |      -63.17 |       112 |      -72.86 | True              | False          |
| trail200_after_net200        | volatility_scaled |       120 |     255 |   -159.37 |       108 |      -56.19 |       111 |      -90.29 | True              | False          |
| trail200_after_net200        | volatility_scaled |       240 |     255 |   -158.02 |       108 |      -44.52 |       109 |      -76.85 | True              | False          |
| trail_vol_after_net200       | fixed100          |        30 |     256 |   -134.18 |       108 |      -72.03 |       113 |      -90.79 | True              | False          |
| trail_vol_after_net200       | fixed100          |        60 |     256 |   -139.03 |       108 |      -63.81 |       113 |      -83.21 | True              | False          |
| trail_vol_after_net200       | fixed100          |       120 |     256 |   -139.22 |       108 |      -61.92 |       113 |      -87.27 | True              | False          |
| trail_vol_after_net200       | fixed100          |       240 |     256 |   -137.7  |       108 |      -59.65 |       112 |      -77.92 | True              | False          |
| trail_vol_after_net200       | fixed200          |        30 |     253 |   -139.8  |       108 |      -59.66 |       110 |      -94.1  | True              | False          |
| trail_vol_after_net200       | fixed200          |        60 |     253 |   -153.72 |       108 |      -47.59 |       110 |      -86.73 | True              | False          |
| trail_vol_after_net200       | fixed200          |       120 |     252 |   -157.39 |       108 |      -50.22 |       109 |      -99.62 | True              | False          |
| trail_vol_after_net200       | fixed200          |       240 |     252 |   -157.07 |       108 |      -48.18 |       108 |      -92.73 | True              | False          |
| trail_vol_after_net200       | volatility_scaled |        30 |     255 |   -140.71 |       108 |      -66.45 |       112 |      -84.92 | True              | False          |
| trail_vol_after_net200       | volatility_scaled |        60 |     255 |   -164.07 |       108 |      -57.8  |       112 |      -73.9  | True              | False          |
| trail_vol_after_net200       | volatility_scaled |       120 |     254 |   -170.74 |       108 |      -55.16 |       111 |      -83.64 | True              | False          |
| trail_vol_after_net200       | volatility_scaled |       240 |     254 |   -168.94 |       108 |      -57.69 |       110 |      -73.12 | True              | False          |

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
