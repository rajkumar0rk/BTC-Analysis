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
| 2025_train                  | fixed1200                    |      249 |      20.88 |    -114.14 |   -28421.2  |           0.526 |       30335    |              40.02 |           24.5  |           12.85 |
| 2025_train                  | fixed200                     |      253 |      47.83 |    -121.46 |   -30729    |           0.257 |       30977.4  |              15.04 |            2.37 |            0    |
| 2025_train                  | fixed300                     |      252 |      38.1  |    -121.88 |   -30714.9  |           0.368 |       31086.5  |              19.4  |            2.78 |            0    |
| 2025_train                  | fixed500                     |      252 |      28.57 |    -117.56 |   -29625.6  |           0.465 |       30601.6  |              27.31 |           24.21 |            0.79 |
| 2025_train                  | fixed800                     |      250 |      22.4  |    -126.07 |   -31517    |           0.468 |       32023.1  |              36.16 |           24.4  |           12.8  |
| 2025_train                  | step100_per_200_after_net200 |      252 |      31.75 |    -154.01 |   -38809.9  |           0.277 |       39114.5  |              28.6  |           17.06 |            3.97 |
| 2025_train                  | trail100_after_net200        |      252 |      31.75 |    -136.14 |   -34307.4  |           0.361 |       34960.4  |              22.84 |           13.89 |            1.59 |
| 2025_train                  | trail200_after_net200        |      252 |      31.35 |    -148.37 |   -37388.4  |           0.304 |       37742.3  |              25.35 |           17.06 |            2.78 |
| 2025_train                  | trail_vol_after_net200       |      251 |      26.29 |    -158.6  |   -39809.3  |           0.27  |       40217.7  |              24.94 |           16.73 |            3.98 |
| 2026_H1_validation          | fixed1200                    |      107 |      31.78 |     -49.36 |    -5281.95 |           0.714 |        5732.64 |              66.95 |           23.36 |           13.08 |
| 2026_H1_validation          | fixed200                     |      108 |      50.93 |     -68.66 |    -7415.46 |           0.456 |        7428.6  |              30.05 |            0.93 |            0    |
| 2026_H1_validation          | fixed300                     |      108 |      44.44 |     -52.29 |    -5647.46 |           0.632 |        5660.6  |              39.09 |            5.56 |            0    |
| 2026_H1_validation          | fixed500                     |      107 |      37.38 |     -42.7  |    -4568.79 |           0.734 |        4581.93 |              51.04 |           23.36 |            0    |
| 2026_H1_validation          | fixed800                     |      107 |      33.64 |     -33.03 |    -3534.31 |           0.804 |        4103.9  |              60.48 |           23.36 |           13.08 |
| 2026_H1_validation          | step100_per_200_after_net200 |      108 |      42.59 |     -64.77 |    -6995.54 |           0.561 |        7008.68 |              54.04 |           19.44 |            8.33 |
| 2026_H1_validation          | trail100_after_net200        |      108 |      42.59 |     -51.09 |    -5517.41 |           0.654 |        5530.55 |              43.64 |           12.04 |            3.7  |
| 2026_H1_validation          | trail200_after_net200        |      108 |      42.59 |     -51.25 |    -5535.22 |           0.653 |        5548.36 |              48.84 |           19.44 |            7.41 |
| 2026_H1_validation          | trail_vol_after_net200       |      108 |      42.59 |     -50.22 |    -5424.07 |           0.66  |        5437.21 |              46.74 |           19.44 |            6.48 |
| 2026_H2_seen_recheck        | fixed1200                    |      108 |      30.56 |     -89.51 |    -9667.35 |           0.489 |        9844.03 |              70.79 |           14.81 |            4.63 |
| 2026_H2_seen_recheck        | fixed200                     |      109 |      45.87 |     -89.75 |    -9782.45 |           0.347 |       10126.2  |              40.5  |            0    |            0    |
| 2026_H2_seen_recheck        | fixed300                     |      109 |      38.53 |     -89.23 |    -9726.07 |           0.426 |        9824.21 |              49.37 |            0.92 |            0    |
| 2026_H2_seen_recheck        | fixed500                     |      109 |      32.11 |     -95.39 |   -10398    |           0.442 |       10483.1  |              62.14 |           15.6  |            0.92 |
| 2026_H2_seen_recheck        | fixed800                     |      109 |      32.11 |     -84.11 |    -9168.44 |           0.508 |        9345.12 |              69.36 |           15.6  |            5.5  |
| 2026_H2_seen_recheck        | step100_per_200_after_net200 |      109 |      36.7  |     -80.56 |    -8780.63 |           0.499 |        9193.65 |              62.71 |           13.76 |            2.75 |
| 2026_H2_seen_recheck        | trail100_after_net200        |      109 |      36.7  |     -87.68 |    -9556.7  |           0.454 |        9636.24 |              53.14 |            9.17 |            1.83 |
| 2026_H2_seen_recheck        | trail200_after_net200        |      109 |      36.7  |    -103.99 |   -11335.2  |           0.353 |       11511.9  |              57.04 |           11.93 |            1.83 |
| 2026_H2_seen_recheck        | trail_vol_after_net200       |      109 |      35.78 |     -96.83 |   -10554.6  |           0.399 |       10657.2  |              53.91 |           10.09 |            1.83 |
| 2026_Nov_recent_exploratory | fixed1200                    |       12 |      16.67 |      27.08 |      324.91 |           1.17  |        1259.54 |              62.42 |           16.67 |           16.67 |
| 2026_Nov_recent_exploratory | fixed200                     |       12 |      33.33 |    -112.83 |    -1354    |           0.259 |        1599.36 |              36.75 |            0    |            0    |
| 2026_Nov_recent_exploratory | fixed300                     |       12 |      16.67 |    -122.83 |    -1474.02 |           0.231 |        1704.47 |              55.83 |            8.33 |            0    |
| 2026_Nov_recent_exploratory | fixed500                     |       12 |      16.67 |     -89.52 |    -1074.25 |           0.439 |        1504.58 |              60.58 |           16.67 |            0    |
| 2026_Nov_recent_exploratory | fixed800                     |       12 |      16.67 |     -39.55 |     -474.61 |           0.752 |        1259.54 |              60.75 |           16.67 |           16.67 |
| 2026_Nov_recent_exploratory | step100_per_200_after_net200 |       12 |      16.67 |     -33.5  |     -402    |           0.79  |        1259.54 |              66.25 |            8.33 |            8.33 |
| 2026_Nov_recent_exploratory | trail100_after_net200        |       12 |      16.67 |     -22.62 |     -271.45 |           0.858 |        1259.54 |              56.42 |            8.33 |            8.33 |
| 2026_Nov_recent_exploratory | trail200_after_net200        |       12 |      16.67 |     -39.28 |     -471.33 |           0.754 |        1259.54 |              56.83 |            8.33 |            8.33 |
| 2026_Nov_recent_exploratory | trail_vol_after_net200       |       12 |      16.67 |     -29.1  |     -349.16 |           0.818 |        1259.54 |              56.5  |            8.33 |            8.33 |

## Chronological consistency for every model
| model                        | stop              |   horizon |   n2025 |   net2025 |   n2026h1 |   net2026h1 |   n2026h2 |   net2026h2 | adequate_sample   | all_positive   |
|:-----------------------------|:------------------|----------:|--------:|----------:|----------:|------------:|----------:|------------:|:------------------|:---------------|
| fixed1200                    | fixed100          |        30 |     255 |   -106.24 |       108 |      -78.91 |       113 |      -85.17 | True              | False          |
| fixed1200                    | fixed100          |        60 |     254 |   -112.64 |       108 |      -81.25 |       113 |      -69.3  | True              | False          |
| fixed1200                    | fixed100          |       120 |     254 |   -109.65 |       108 |      -70.72 |       113 |      -76.15 | True              | False          |
| fixed1200                    | fixed100          |       240 |     253 |   -117.02 |       108 |      -55.96 |       109 |      -62.42 | True              | False          |
| fixed1200                    | fixed200          |        30 |     252 |   -109.56 |       107 |      -63.05 |       110 |      -85.6  | True              | False          |
| fixed1200                    | fixed200          |        60 |     251 |   -122.2  |       107 |      -54.5  |       110 |      -73.28 | True              | False          |
| fixed1200                    | fixed200          |       120 |     249 |   -114.14 |       107 |      -49.36 |       108 |      -89.51 | True              | False          |
| fixed1200                    | fixed200          |       240 |     247 |   -121.99 |       106 |      -28.3  |       105 |      -85.42 | True              | False          |
| fixed1200                    | volatility_scaled |        30 |     254 |   -108.01 |       107 |      -68.75 |       112 |      -76.65 | True              | False          |
| fixed1200                    | volatility_scaled |        60 |     253 |   -133.42 |       107 |      -63.09 |       112 |      -61.43 | True              | False          |
| fixed1200                    | volatility_scaled |       120 |     251 |   -140.61 |       107 |      -57.56 |       110 |      -73.84 | True              | False          |
| fixed1200                    | volatility_scaled |       240 |     249 |   -163.67 |       105 |      -41.76 |       107 |      -70.69 | True              | False          |
| fixed200                     | fixed100          |        30 |     256 |   -123.2  |       108 |      -66.91 |       113 |      -90.16 | True              | False          |
| fixed200                     | fixed100          |        60 |     256 |   -123.45 |       108 |      -65.25 |       113 |      -88.2  | True              | False          |
| fixed200                     | fixed100          |       120 |     256 |   -123.02 |       108 |      -67.26 |       113 |      -89.29 | True              | False          |
| fixed200                     | fixed100          |       240 |     256 |   -122.39 |       108 |      -67.84 |       113 |      -86.86 | True              | False          |
| fixed200                     | fixed200          |        30 |     253 |   -121.44 |       108 |      -68.8  |       110 |      -89.66 | True              | False          |
| fixed200                     | fixed200          |        60 |     253 |   -121.87 |       108 |      -65.44 |       110 |      -88.59 | True              | False          |
| fixed200                     | fixed200          |       120 |     253 |   -121.46 |       108 |      -68.66 |       109 |      -89.75 | True              | False          |
| fixed200                     | fixed200          |       240 |     253 |   -121.29 |       108 |      -67.1  |       109 |      -93.29 | True              | False          |
| fixed200                     | volatility_scaled |        30 |     255 |   -112.67 |       108 |      -72.69 |       112 |      -81.73 | True              | False          |
| fixed200                     | volatility_scaled |        60 |     255 |   -113.92 |       108 |      -75.12 |       112 |      -79.38 | True              | False          |
| fixed200                     | volatility_scaled |       120 |     255 |   -112.79 |       108 |      -76.09 |       111 |      -77.58 | True              | False          |
| fixed200                     | volatility_scaled |       240 |     255 |   -112.43 |       108 |      -78.44 |       111 |      -80.32 | True              | False          |
| fixed300                     | fixed100          |        30 |     256 |   -118.74 |       108 |      -66.83 |       113 |      -90.78 | True              | False          |
| fixed300                     | fixed100          |        60 |     256 |   -120.69 |       108 |      -62.26 |       113 |      -80.33 | True              | False          |
| fixed300                     | fixed100          |       120 |     256 |   -119.55 |       108 |      -57.38 |       113 |      -82.1  | True              | False          |
| fixed300                     | fixed100          |       240 |     256 |   -117.4  |       108 |      -59.82 |       113 |      -78.73 | True              | False          |
| fixed300                     | fixed200          |        30 |     253 |   -120    |       108 |      -58.17 |       110 |      -90.08 | True              | False          |
| fixed300                     | fixed200          |        60 |     253 |   -121.1  |       108 |      -53.5  |       110 |      -79.58 | True              | False          |
| fixed300                     | fixed200          |       120 |     252 |   -121.88 |       108 |      -52.29 |       109 |      -89.23 | True              | False          |
| fixed300                     | fixed200          |       240 |     252 |   -120.66 |       108 |      -53.76 |       109 |      -91.8  | True              | False          |
| fixed300                     | volatility_scaled |        30 |     255 |   -120.85 |       108 |      -64.96 |       112 |      -84.19 | True              | False          |
| fixed300                     | volatility_scaled |        60 |     255 |   -125.38 |       108 |      -63.97 |       112 |      -70.1  | True              | False          |
| fixed300                     | volatility_scaled |       120 |     254 |   -130.06 |       108 |      -57.59 |       111 |      -76.42 | True              | False          |
| fixed300                     | volatility_scaled |       240 |     254 |   -128.06 |       108 |      -63.3  |       111 |      -74.9  | True              | False          |
| fixed500                     | fixed100          |        30 |     256 |   -115.01 |       108 |      -69.28 |       113 |      -91.37 | True              | False          |
| fixed500                     | fixed100          |        60 |     256 |   -114.8  |       108 |      -68.75 |       113 |      -79.77 | True              | False          |
| fixed500                     | fixed100          |       120 |     256 |   -110.95 |       108 |      -65.98 |       113 |      -85.73 | True              | False          |
| fixed500                     | fixed100          |       240 |     256 |   -111.72 |       108 |      -58.92 |       112 |      -72.34 | True              | False          |
| fixed500                     | fixed200          |        30 |     253 |   -119.99 |       107 |      -48.49 |       110 |      -95.08 | True              | False          |
| fixed500                     | fixed200          |        60 |     253 |   -121.8  |       107 |      -40.93 |       110 |      -81.15 | True              | False          |
| fixed500                     | fixed200          |       120 |     252 |   -117.56 |       107 |      -42.7  |       109 |      -95.39 | True              | False          |
| fixed500                     | fixed200          |       240 |     252 |   -116.91 |       107 |      -33.49 |       108 |      -86.54 | True              | False          |
| fixed500                     | volatility_scaled |        30 |     255 |   -117.85 |       107 |      -54.66 |       112 |      -85.96 | True              | False          |
| fixed500                     | volatility_scaled |        60 |     255 |   -121.79 |       107 |      -50.55 |       112 |      -69.16 | True              | False          |
| fixed500                     | volatility_scaled |       120 |     254 |   -119.02 |       107 |      -47.14 |       111 |      -79.75 | True              | False          |
| fixed500                     | volatility_scaled |       240 |     254 |   -116.97 |       107 |      -41.03 |       110 |      -70.55 | True              | False          |
| fixed800                     | fixed100          |        30 |     255 |   -113.41 |       108 |      -68.79 |       113 |      -88.72 | True              | False          |
| fixed800                     | fixed100          |        60 |     254 |   -114.66 |       108 |      -56.05 |       113 |      -74.91 | True              | False          |
| fixed800                     | fixed100          |       120 |     254 |   -113.18 |       108 |      -48.04 |       113 |      -83.35 | True              | False          |
| fixed800                     | fixed100          |       240 |     254 |   -116.86 |       108 |      -27.79 |       109 |      -73.81 | True              | False          |
| fixed800                     | fixed200          |        30 |     252 |   -116.76 |       107 |      -53.24 |       110 |      -89.62 | True              | False          |
| fixed800                     | fixed200          |        60 |     251 |   -125.92 |       107 |      -30.97 |       110 |      -82.68 | True              | False          |
| fixed800                     | fixed200          |       120 |     250 |   -126.07 |       107 |      -33.03 |       109 |      -84.11 | True              | False          |
| fixed800                     | fixed200          |       240 |     249 |   -135.72 |       106 |      -11.37 |       106 |      -81.4  | True              | False          |
| fixed800                     | volatility_scaled |        30 |     254 |   -114.82 |       107 |      -58.95 |       112 |      -80.6  | True              | False          |
| fixed800                     | volatility_scaled |        60 |     253 |   -127.61 |       107 |      -40    |       112 |      -70.66 | True              | False          |
| fixed800                     | volatility_scaled |       120 |     252 |   -128.36 |       107 |      -36.6  |       111 |      -68.67 | True              | False          |
| fixed800                     | volatility_scaled |       240 |     251 |   -145.9  |       106 |      -16.4  |       108 |      -66.88 | True              | False          |
| step100_per_200_after_net200 | fixed100          |        30 |     256 |   -130.83 |       108 |      -74.25 |       113 |      -84.9  | True              | False          |
| step100_per_200_after_net200 | fixed100          |        60 |     256 |   -133.9  |       108 |      -74.73 |       113 |      -71.85 | True              | False          |
| step100_per_200_after_net200 | fixed100          |       120 |     256 |   -131.67 |       108 |      -64.96 |       113 |      -87.46 | True              | False          |
| step100_per_200_after_net200 | fixed100          |       240 |     256 |   -133.9  |       108 |      -41.87 |       109 |      -72.53 | True              | False          |
| step100_per_200_after_net200 | fixed200          |        30 |     253 |   -137.05 |       108 |      -65.05 |       110 |      -85.1  | True              | False          |
| step100_per_200_after_net200 | fixed200          |        60 |     253 |   -149.81 |       108 |      -66.7  |       110 |      -69.29 | True              | False          |
| step100_per_200_after_net200 | fixed200          |       120 |     252 |   -154.01 |       108 |      -64.77 |       109 |      -80.56 | True              | False          |
| step100_per_200_after_net200 | fixed200          |       240 |     252 |   -156.74 |       108 |      -40.11 |       106 |      -75.45 | True              | False          |
| step100_per_200_after_net200 | volatility_scaled |        30 |     255 |   -139.05 |       108 |      -71.83 |       112 |      -76.27 | True              | False          |
| step100_per_200_after_net200 | volatility_scaled |        60 |     255 |   -162.79 |       108 |      -76.91 |       112 |      -56.96 | True              | False          |
| step100_per_200_after_net200 | volatility_scaled |       120 |     254 |   -169.66 |       108 |      -69.71 |       111 |      -65.11 | True              | False          |
| step100_per_200_after_net200 | volatility_scaled |       240 |     254 |   -166.09 |       108 |      -49.41 |       108 |      -55.17 | True              | False          |
| trail100_after_net200        | fixed100          |        30 |     256 |   -118.65 |       108 |      -69.69 |       113 |      -89.49 | True              | False          |
| trail100_after_net200        | fixed100          |        60 |     256 |   -122.31 |       108 |      -61.52 |       113 |      -79.86 | True              | False          |
| trail100_after_net200        | fixed100          |       120 |     256 |   -122.76 |       108 |      -61.35 |       113 |      -81.81 | True              | False          |
| trail100_after_net200        | fixed100          |       240 |     256 |   -121.15 |       108 |      -57.27 |       112 |      -72.88 | True              | False          |
| trail100_after_net200        | fixed200          |        30 |     253 |   -128.27 |       108 |      -55.79 |       110 |      -88.11 | True              | False          |
| trail100_after_net200        | fixed200          |        60 |     253 |   -133.31 |       108 |      -45.17 |       110 |      -77.64 | True              | False          |
| trail100_after_net200        | fixed200          |       120 |     252 |   -136.14 |       108 |      -51.09 |       109 |      -87.68 | True              | False          |
| trail100_after_net200        | fixed200          |       240 |     252 |   -135.99 |       108 |      -45.71 |       108 |      -82.86 | True              | False          |
| trail100_after_net200        | volatility_scaled |        30 |     255 |   -133.09 |       108 |      -62.57 |       112 |      -78.18 | True              | False          |
| trail100_after_net200        | volatility_scaled |        60 |     255 |   -142.51 |       108 |      -55.38 |       112 |      -64.11 | True              | False          |
| trail100_after_net200        | volatility_scaled |       120 |     254 |   -147.99 |       108 |      -56.02 |       111 |      -71.04 | True              | False          |
| trail100_after_net200        | volatility_scaled |       240 |     254 |   -145.64 |       108 |      -55.22 |       110 |      -62.58 | True              | False          |
| trail200_after_net200        | fixed100          |        30 |     256 |   -124.3  |       108 |      -72.75 |       113 |      -92.15 | True              | False          |
| trail200_after_net200        | fixed100          |        60 |     256 |   -131.61 |       108 |      -68.72 |       113 |      -82.61 | True              | False          |
| trail200_after_net200        | fixed100          |       120 |     256 |   -130.71 |       108 |      -59.65 |       113 |      -94.23 | True              | False          |
| trail200_after_net200        | fixed100          |       240 |     256 |   -131.14 |       108 |      -44.54 |       111 |      -81.32 | True              | False          |
| trail200_after_net200        | fixed200          |        30 |     253 |   -134.87 |       108 |      -59.88 |       110 |      -92.66 | True              | False          |
| trail200_after_net200        | fixed200          |        60 |     253 |   -145.79 |       108 |      -52.97 |       110 |      -83.87 | True              | False          |
| trail200_after_net200        | fixed200          |       120 |     252 |   -148.37 |       108 |      -51.25 |       109 |     -103.99 | True              | False          |
| trail200_after_net200        | fixed200          |       240 |     252 |   -148.82 |       108 |      -35.94 |       107 |      -96.88 | True              | False          |
| trail200_after_net200        | volatility_scaled |        30 |     255 |   -140.43 |       108 |      -66.66 |       112 |      -83.54 | True              | False          |
| trail200_after_net200        | volatility_scaled |        60 |     255 |   -156.52 |       108 |      -63.17 |       112 |      -71.12 | True              | False          |
| trail200_after_net200        | volatility_scaled |       120 |     254 |   -160.28 |       108 |      -56.19 |       111 |      -87.96 | True              | False          |
| trail200_after_net200        | volatility_scaled |       240 |     254 |   -158.92 |       108 |      -44.52 |       109 |      -76.8  | True              | False          |
| trail_vol_after_net200       | fixed100          |        30 |     255 |   -134.61 |       108 |      -72.03 |       113 |      -90.78 | True              | False          |
| trail_vol_after_net200       | fixed100          |        60 |     255 |   -140.15 |       108 |      -63.81 |       113 |      -83.2  | True              | False          |
| trail_vol_after_net200       | fixed100          |       120 |     255 |   -140.34 |       108 |      -61.92 |       113 |      -87.26 | True              | False          |
| trail_vol_after_net200       | fixed100          |       240 |     255 |   -138.82 |       108 |      -59.65 |       112 |      -77.91 | True              | False          |
| trail_vol_after_net200       | fixed200          |        30 |     252 |   -140.25 |       108 |      -59.66 |       110 |      -92.09 | True              | False          |
| trail_vol_after_net200       | fixed200          |        60 |     252 |   -154.91 |       108 |      -47.59 |       110 |      -84.54 | True              | False          |
| trail_vol_after_net200       | fixed200          |       120 |     251 |   -158.6  |       108 |      -50.22 |       109 |      -96.83 | True              | False          |
| trail_vol_after_net200       | fixed200          |       240 |     251 |   -158.28 |       108 |      -48.18 |       108 |      -92.72 | True              | False          |
| trail_vol_after_net200       | volatility_scaled |        30 |     254 |   -141.16 |       108 |      -66.45 |       112 |      -83.35 | True              | False          |
| trail_vol_after_net200       | volatility_scaled |        60 |     254 |   -165.29 |       108 |      -57.8  |       112 |      -72.16 | True              | False          |
| trail_vol_after_net200       | volatility_scaled |       120 |     253 |   -171.99 |       108 |      -55.16 |       111 |      -81.32 | True              | False          |
| trail_vol_after_net200       | volatility_scaled |       240 |     253 |   -170.19 |       108 |      -57.69 |       110 |      -73.07 | True              | False          |

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
