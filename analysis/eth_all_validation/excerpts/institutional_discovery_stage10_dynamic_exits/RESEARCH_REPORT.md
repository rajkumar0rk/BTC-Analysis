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
| 2025_train                  | fixed1200                    |      240 |      27.5  |     -11.25 |    -2698.83 |           0.386 |        2803.18 |             119.64 |               0 |               0 |
| 2025_train                  | fixed200                     |      240 |      27.5  |     -11.25 |    -2698.83 |           0.386 |        2803.18 |             119.64 |               0 |               0 |
| 2025_train                  | fixed300                     |      240 |      27.5  |     -11.25 |    -2698.83 |           0.386 |        2803.18 |             119.64 |               0 |               0 |
| 2025_train                  | fixed500                     |      240 |      27.5  |     -11.25 |    -2698.83 |           0.386 |        2803.18 |             119.64 |               0 |               0 |
| 2025_train                  | fixed800                     |      240 |      27.5  |     -11.25 |    -2698.83 |           0.386 |        2803.18 |             119.64 |               0 |               0 |
| 2025_train                  | step100_per_200_after_net200 |      240 |      27.5  |     -11.25 |    -2698.83 |           0.386 |        2803.18 |             119.64 |               0 |               0 |
| 2025_train                  | trail100_after_net200        |      240 |      27.5  |     -11.25 |    -2698.83 |           0.386 |        2803.18 |             119.64 |               0 |               0 |
| 2025_train                  | trail200_after_net200        |      240 |      27.5  |     -11.25 |    -2698.83 |           0.386 |        2803.18 |             119.64 |               0 |               0 |
| 2025_train                  | trail_vol_after_net200       |      240 |      27.5  |     -11.25 |    -2698.83 |           0.386 |        2803.18 |             119.64 |               0 |               0 |
| 2026_H1_validation          | fixed1200                    |       98 |      21.43 |     -12.02 |    -1178.16 |           0.186 |        1178.16 |             120    |               0 |               0 |
| 2026_H1_validation          | fixed200                     |       98 |      21.43 |     -12.02 |    -1178.16 |           0.186 |        1178.16 |             120    |               0 |               0 |
| 2026_H1_validation          | fixed300                     |       98 |      21.43 |     -12.02 |    -1178.16 |           0.186 |        1178.16 |             120    |               0 |               0 |
| 2026_H1_validation          | fixed500                     |       98 |      21.43 |     -12.02 |    -1178.16 |           0.186 |        1178.16 |             120    |               0 |               0 |
| 2026_H1_validation          | fixed800                     |       98 |      21.43 |     -12.02 |    -1178.16 |           0.186 |        1178.16 |             120    |               0 |               0 |
| 2026_H1_validation          | step100_per_200_after_net200 |       98 |      21.43 |     -12.02 |    -1178.16 |           0.186 |        1178.16 |             120    |               0 |               0 |
| 2026_H1_validation          | trail100_after_net200        |       98 |      21.43 |     -12.02 |    -1178.16 |           0.186 |        1178.16 |             120    |               0 |               0 |
| 2026_H1_validation          | trail200_after_net200        |       98 |      21.43 |     -12.02 |    -1178.16 |           0.186 |        1178.16 |             120    |               0 |               0 |
| 2026_H1_validation          | trail_vol_after_net200       |       98 |      21.43 |     -12.02 |    -1178.16 |           0.186 |        1178.16 |             120    |               0 |               0 |
| 2026_H2_seen_recheck        | fixed1200                    |       99 |      18.18 |     -13.06 |    -1293.22 |           0.124 |        1293.22 |             120    |               0 |               0 |
| 2026_H2_seen_recheck        | fixed200                     |       99 |      18.18 |     -13.06 |    -1293.22 |           0.124 |        1293.22 |             120    |               0 |               0 |
| 2026_H2_seen_recheck        | fixed300                     |       99 |      18.18 |     -13.06 |    -1293.22 |           0.124 |        1293.22 |             120    |               0 |               0 |
| 2026_H2_seen_recheck        | fixed500                     |       99 |      18.18 |     -13.06 |    -1293.22 |           0.124 |        1293.22 |             120    |               0 |               0 |
| 2026_H2_seen_recheck        | fixed800                     |       99 |      18.18 |     -13.06 |    -1293.22 |           0.124 |        1293.22 |             120    |               0 |               0 |
| 2026_H2_seen_recheck        | step100_per_200_after_net200 |       99 |      18.18 |     -13.06 |    -1293.22 |           0.124 |        1293.22 |             120    |               0 |               0 |
| 2026_H2_seen_recheck        | trail100_after_net200        |       99 |      18.18 |     -13.06 |    -1293.22 |           0.124 |        1293.22 |             120    |               0 |               0 |
| 2026_H2_seen_recheck        | trail200_after_net200        |       99 |      18.18 |     -13.06 |    -1293.22 |           0.124 |        1293.22 |             120    |               0 |               0 |
| 2026_H2_seen_recheck        | trail_vol_after_net200       |       99 |      18.18 |     -13.06 |    -1293.22 |           0.124 |        1293.22 |             120    |               0 |               0 |
| 2026_Nov_recent_exploratory | fixed1200                    |       12 |      16.67 |      -7.97 |      -95.64 |           0.459 |         136.02 |             120    |               0 |               0 |
| 2026_Nov_recent_exploratory | fixed200                     |       12 |      16.67 |      -7.97 |      -95.64 |           0.459 |         136.02 |             120    |               0 |               0 |
| 2026_Nov_recent_exploratory | fixed300                     |       12 |      16.67 |      -7.97 |      -95.64 |           0.459 |         136.02 |             120    |               0 |               0 |
| 2026_Nov_recent_exploratory | fixed500                     |       12 |      16.67 |      -7.97 |      -95.64 |           0.459 |         136.02 |             120    |               0 |               0 |
| 2026_Nov_recent_exploratory | fixed800                     |       12 |      16.67 |      -7.97 |      -95.64 |           0.459 |         136.02 |             120    |               0 |               0 |
| 2026_Nov_recent_exploratory | step100_per_200_after_net200 |       12 |      16.67 |      -7.97 |      -95.64 |           0.459 |         136.02 |             120    |               0 |               0 |
| 2026_Nov_recent_exploratory | trail100_after_net200        |       12 |      16.67 |      -7.97 |      -95.64 |           0.459 |         136.02 |             120    |               0 |               0 |
| 2026_Nov_recent_exploratory | trail200_after_net200        |       12 |      16.67 |      -7.97 |      -95.64 |           0.459 |         136.02 |             120    |               0 |               0 |
| 2026_Nov_recent_exploratory | trail_vol_after_net200       |       12 |      16.67 |      -7.97 |      -95.64 |           0.459 |         136.02 |             120    |               0 |               0 |

## Chronological consistency for every model
| model                        | stop              |   horizon |   n2025 |   net2025 |   n2026h1 |   net2026h1 |   n2026h2 |   net2026h2 | adequate_sample   | all_positive   |
|:-----------------------------|:------------------|----------:|--------:|----------:|----------:|------------:|----------:|------------:|:------------------|:---------------|
| fixed1200                    | fixed100          |        30 |     244 |    -14.23 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| fixed1200                    | fixed100          |        60 |     242 |    -15.58 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| fixed1200                    | fixed100          |       120 |     240 |    -11.85 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| fixed1200                    | fixed100          |       240 |     230 |    -11.8  |        93 |      -11.24 |        95 |      -13.61 | True              | False          |
| fixed1200                    | fixed200          |        30 |     244 |    -14.19 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| fixed1200                    | fixed200          |        60 |     242 |    -14.54 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| fixed1200                    | fixed200          |       120 |     240 |    -11.25 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| fixed1200                    | fixed200          |       240 |     229 |    -12.69 |        93 |      -11.43 |        95 |      -14.18 | True              | False          |
| fixed1200                    | volatility_scaled |        30 |     244 |    -14.44 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| fixed1200                    | volatility_scaled |        60 |     242 |    -15.74 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| fixed1200                    | volatility_scaled |       120 |     240 |    -12.21 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| fixed1200                    | volatility_scaled |       240 |     230 |    -13.04 |        93 |      -11.43 |        95 |      -14.13 | True              | False          |
| fixed200                     | fixed100          |        30 |     244 |    -14.23 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| fixed200                     | fixed100          |        60 |     242 |    -15.58 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| fixed200                     | fixed100          |       120 |     240 |    -11.85 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| fixed200                     | fixed100          |       240 |     230 |    -11.8  |        93 |      -11.24 |        95 |      -13.61 | True              | False          |
| fixed200                     | fixed200          |        30 |     244 |    -14.19 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| fixed200                     | fixed200          |        60 |     242 |    -14.54 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| fixed200                     | fixed200          |       120 |     240 |    -11.25 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| fixed200                     | fixed200          |       240 |     229 |    -12.69 |        93 |      -11.43 |        95 |      -14.18 | True              | False          |
| fixed200                     | volatility_scaled |        30 |     244 |    -14.44 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| fixed200                     | volatility_scaled |        60 |     242 |    -15.74 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| fixed200                     | volatility_scaled |       120 |     240 |    -12.21 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| fixed200                     | volatility_scaled |       240 |     230 |    -13.04 |        93 |      -11.43 |        95 |      -14.13 | True              | False          |
| fixed300                     | fixed100          |        30 |     244 |    -14.23 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| fixed300                     | fixed100          |        60 |     242 |    -15.58 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| fixed300                     | fixed100          |       120 |     240 |    -11.85 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| fixed300                     | fixed100          |       240 |     230 |    -11.8  |        93 |      -11.24 |        95 |      -13.61 | True              | False          |
| fixed300                     | fixed200          |        30 |     244 |    -14.19 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| fixed300                     | fixed200          |        60 |     242 |    -14.54 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| fixed300                     | fixed200          |       120 |     240 |    -11.25 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| fixed300                     | fixed200          |       240 |     229 |    -12.69 |        93 |      -11.43 |        95 |      -14.18 | True              | False          |
| fixed300                     | volatility_scaled |        30 |     244 |    -14.44 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| fixed300                     | volatility_scaled |        60 |     242 |    -15.74 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| fixed300                     | volatility_scaled |       120 |     240 |    -12.21 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| fixed300                     | volatility_scaled |       240 |     230 |    -13.04 |        93 |      -11.43 |        95 |      -14.13 | True              | False          |
| fixed500                     | fixed100          |        30 |     244 |    -14.23 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| fixed500                     | fixed100          |        60 |     242 |    -15.58 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| fixed500                     | fixed100          |       120 |     240 |    -11.85 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| fixed500                     | fixed100          |       240 |     230 |    -11.8  |        93 |      -11.24 |        95 |      -13.61 | True              | False          |
| fixed500                     | fixed200          |        30 |     244 |    -14.19 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| fixed500                     | fixed200          |        60 |     242 |    -14.54 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| fixed500                     | fixed200          |       120 |     240 |    -11.25 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| fixed500                     | fixed200          |       240 |     229 |    -12.69 |        93 |      -11.43 |        95 |      -14.18 | True              | False          |
| fixed500                     | volatility_scaled |        30 |     244 |    -14.44 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| fixed500                     | volatility_scaled |        60 |     242 |    -15.74 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| fixed500                     | volatility_scaled |       120 |     240 |    -12.21 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| fixed500                     | volatility_scaled |       240 |     230 |    -13.04 |        93 |      -11.43 |        95 |      -14.13 | True              | False          |
| fixed800                     | fixed100          |        30 |     244 |    -14.23 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| fixed800                     | fixed100          |        60 |     242 |    -15.58 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| fixed800                     | fixed100          |       120 |     240 |    -11.85 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| fixed800                     | fixed100          |       240 |     230 |    -11.8  |        93 |      -11.24 |        95 |      -13.61 | True              | False          |
| fixed800                     | fixed200          |        30 |     244 |    -14.19 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| fixed800                     | fixed200          |        60 |     242 |    -14.54 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| fixed800                     | fixed200          |       120 |     240 |    -11.25 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| fixed800                     | fixed200          |       240 |     229 |    -12.69 |        93 |      -11.43 |        95 |      -14.18 | True              | False          |
| fixed800                     | volatility_scaled |        30 |     244 |    -14.44 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| fixed800                     | volatility_scaled |        60 |     242 |    -15.74 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| fixed800                     | volatility_scaled |       120 |     240 |    -12.21 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| fixed800                     | volatility_scaled |       240 |     230 |    -13.04 |        93 |      -11.43 |        95 |      -14.13 | True              | False          |
| step100_per_200_after_net200 | fixed100          |        30 |     244 |    -14.23 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| step100_per_200_after_net200 | fixed100          |        60 |     242 |    -15.58 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| step100_per_200_after_net200 | fixed100          |       120 |     240 |    -11.85 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| step100_per_200_after_net200 | fixed100          |       240 |     230 |    -11.8  |        93 |      -11.24 |        95 |      -13.61 | True              | False          |
| step100_per_200_after_net200 | fixed200          |        30 |     244 |    -14.19 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| step100_per_200_after_net200 | fixed200          |        60 |     242 |    -14.54 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| step100_per_200_after_net200 | fixed200          |       120 |     240 |    -11.25 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| step100_per_200_after_net200 | fixed200          |       240 |     229 |    -12.69 |        93 |      -11.43 |        95 |      -14.18 | True              | False          |
| step100_per_200_after_net200 | volatility_scaled |        30 |     244 |    -14.44 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| step100_per_200_after_net200 | volatility_scaled |        60 |     242 |    -15.74 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| step100_per_200_after_net200 | volatility_scaled |       120 |     240 |    -12.21 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| step100_per_200_after_net200 | volatility_scaled |       240 |     230 |    -13.04 |        93 |      -11.43 |        95 |      -14.13 | True              | False          |
| trail100_after_net200        | fixed100          |        30 |     244 |    -14.23 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| trail100_after_net200        | fixed100          |        60 |     242 |    -15.58 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| trail100_after_net200        | fixed100          |       120 |     240 |    -11.85 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| trail100_after_net200        | fixed100          |       240 |     230 |    -11.8  |        93 |      -11.24 |        95 |      -13.61 | True              | False          |
| trail100_after_net200        | fixed200          |        30 |     244 |    -14.19 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| trail100_after_net200        | fixed200          |        60 |     242 |    -14.54 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| trail100_after_net200        | fixed200          |       120 |     240 |    -11.25 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| trail100_after_net200        | fixed200          |       240 |     229 |    -12.69 |        93 |      -11.43 |        95 |      -14.18 | True              | False          |
| trail100_after_net200        | volatility_scaled |        30 |     244 |    -14.44 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| trail100_after_net200        | volatility_scaled |        60 |     242 |    -15.74 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| trail100_after_net200        | volatility_scaled |       120 |     240 |    -12.21 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| trail100_after_net200        | volatility_scaled |       240 |     230 |    -13.04 |        93 |      -11.43 |        95 |      -14.13 | True              | False          |
| trail200_after_net200        | fixed100          |        30 |     244 |    -14.23 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| trail200_after_net200        | fixed100          |        60 |     242 |    -15.58 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| trail200_after_net200        | fixed100          |       120 |     240 |    -11.85 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| trail200_after_net200        | fixed100          |       240 |     230 |    -11.8  |        93 |      -11.24 |        95 |      -13.61 | True              | False          |
| trail200_after_net200        | fixed200          |        30 |     244 |    -14.19 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| trail200_after_net200        | fixed200          |        60 |     242 |    -14.54 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| trail200_after_net200        | fixed200          |       120 |     240 |    -11.25 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| trail200_after_net200        | fixed200          |       240 |     229 |    -12.69 |        93 |      -11.43 |        95 |      -14.18 | True              | False          |
| trail200_after_net200        | volatility_scaled |        30 |     244 |    -14.44 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| trail200_after_net200        | volatility_scaled |        60 |     242 |    -15.74 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| trail200_after_net200        | volatility_scaled |       120 |     240 |    -12.21 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| trail200_after_net200        | volatility_scaled |       240 |     230 |    -13.04 |        93 |      -11.43 |        95 |      -14.13 | True              | False          |
| trail_vol_after_net200       | fixed100          |        30 |     244 |    -14.23 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| trail_vol_after_net200       | fixed100          |        60 |     242 |    -15.58 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| trail_vol_after_net200       | fixed100          |       120 |     240 |    -11.85 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| trail_vol_after_net200       | fixed100          |       240 |     230 |    -11.8  |        93 |      -11.24 |        95 |      -13.61 | True              | False          |
| trail_vol_after_net200       | fixed200          |        30 |     244 |    -14.19 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| trail_vol_after_net200       | fixed200          |        60 |     242 |    -14.54 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| trail_vol_after_net200       | fixed200          |       120 |     240 |    -11.25 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| trail_vol_after_net200       | fixed200          |       240 |     229 |    -12.69 |        93 |      -11.43 |        95 |      -14.18 | True              | False          |
| trail_vol_after_net200       | volatility_scaled |        30 |     244 |    -14.44 |       100 |      -11.71 |       106 |      -12.34 | True              | False          |
| trail_vol_after_net200       | volatility_scaled |        60 |     242 |    -15.74 |       100 |      -12.02 |       105 |      -11.3  | True              | False          |
| trail_vol_after_net200       | volatility_scaled |       120 |     240 |    -12.21 |        98 |      -12.02 |        99 |      -13.06 | True              | False          |
| trail_vol_after_net200       | volatility_scaled |       240 |     230 |    -13.04 |        93 |      -11.43 |        95 |      -14.13 | True              | False          |

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
