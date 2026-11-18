# Stage 7 — Every BTC 1-minute candle: time, weekday, volume and volatility

## Predeclared setup
- Dataset: Delta India BTCUSD authentic 1m futures, first Jan 2025 to latest archive.
- Entry: next 1m open; only previous completed 5m candles used for high volume/range.
- Time zone: Asia/Kolkata, DST-free. Hour is the actual entry timestamp.
- High volume = last completed rolling 5m total volume / older 60-window mean
  above fixed 1.5x / 2x / 3x thresholds.
- High volatility = last completed rolling 5m high-low range / older 60-window
  median above fixed 1.5x / 2x / 3x thresholds.
- Test all 24 IST hours, 7 days, 3h blocks, and intersections.
- Missing minute history never filled; conditions crossing gaps removed.
- Ex-post +200 reaches cannot be treated as predictable entry signals.
- Uses standard 0.05% taker/side + 18% GST and adverse 5 points/side slippage;
  alternate Scalper Offer closing-fee waiver is a hypothetical eligible scenario.
- Same 1m stop and TP bar: stop FIRST; no independent tick path.
- Each independent rule/direction/stop/horizon permits only one concurrent position.

## All-candle 30-minute reference
| filter         | kind     | period                      | side   |   horizon_min |   signals |   gross_200_reached_pct |   net_200_possible_pct |   gross_200_before_100stop_pct |   gross_200_before_200stop_pct |   net_200_before_100stop_pct |   no_adverse_200_pct |   hits_200_before_100stop |   net_hits_200_before_100stop |
|:---------------|:---------|:----------------------------|:-------|--------------:|----------:|------------------------:|-----------------------:|-------------------------------:|-------------------------------:|-----------------------------:|---------------------:|--------------------------:|------------------------------:|
| all_hours_days | baseline | 2025_train                  | LONG   |            30 |    524441 |                  50.341 |                 33.439 |                         30.242 |                         40.783 |                       19.18  |               4.0384 |                    158599 |                        100588 |
| all_hours_days | baseline | 2025_train                  | SHORT  |            30 |    524441 |                  50.148 |                 33.831 |                         30.404 |                         41.048 |                       19.534 |               4.2891 |                    159452 |                        102445 |
| all_hours_days | baseline | 2026_H1_validation          | LONG   |            30 |    260203 |                  31.23  |                 19.987 |                         22.307 |                         27.819 |                       13.807 |               2.5307 |                     58043 |                         35926 |
| all_hours_days | baseline | 2026_H1_validation          | SHORT  |            30 |    260203 |                  32.8   |                 21.155 |                         23.907 |                         29.566 |                       14.993 |               2.5795 |                     62207 |                         39012 |
| all_hours_days | baseline | 2026_H2_seen_recheck        | LONG   |            30 |    176950 |                  24.469 |                 14.089 |                         19.252 |                         22.872 |                       10.986 |               2.0972 |                     34067 |                         19440 |
| all_hours_days | baseline | 2026_H2_seen_recheck        | SHORT  |            30 |    176950 |                  23.622 |                 13.526 |                         18.598 |                         22.023 |                       10.432 |               2.1492 |                     32910 |                         18460 |
| all_hours_days | baseline | 2026_Nov_recent_exploratory | LONG   |            30 |     24421 |                  29.131 |                 17.481 |                         20.929 |                         26.039 |                       12.162 |               2.3873 |                      5111 |                          2970 |
| all_hours_days | baseline | 2026_Nov_recent_exploratory | SHORT  |            30 |     24421 |                  32.239 |                 20.523 |                         24.544 |                         29.769 |                       15.089 |               2.7558 |                      5994 |                          3685 |

## 2025 training: highest 200-before-100-stop event probabilities
| filter      | kind         | period     | side   |   horizon_min |   signals |   gross_200_reached_pct |   net_200_possible_pct |   gross_200_before_100stop_pct |   gross_200_before_200stop_pct |   net_200_before_100stop_pct |   no_adverse_200_pct |   hits_200_before_100stop |   net_hits_200_before_100stop |
|:------------|:-------------|:-----------|:-------|--------------:|----------:|------------------------:|-----------------------:|-------------------------------:|-------------------------------:|-----------------------------:|---------------------:|--------------------------:|------------------------------:|
| Mon_IST_06h | weekday_hour | 2025_train | SHORT  |            30 |      3120 |                  66.891 |                 49.712 |                         38.878 |                         53.429 |                       27.436 |               6.6667 |                      1213 |                           856 |
| Tue_IST_07h | weekday_hour | 2025_train | SHORT  |            30 |      3120 |                  62.404 |                 45.096 |                         38.269 |                         52.5   |                       27.885 |               5.609  |                      1194 |                           870 |
| Wed_IST_23h | weekday_hour | 2025_train | LONG   |            30 |      3180 |                  64.717 |                 48.113 |                         37.358 |                         51.73  |                       27.358 |               3.8679 |                      1188 |                           870 |
| Fri_IST_03h | weekday_hour | 2025_train | LONG   |            30 |      3120 |                  59.391 |                 42.468 |                         36.859 |                         49.519 |                       25.096 |               6.891  |                      1150 |                           783 |
| Tue_IST_18h | weekday_hour | 2025_train | LONG   |            30 |      3120 |                  63.141 |                 43.974 |                         36.795 |                         50.321 |                       23.269 |               4.359  |                      1148 |                           726 |
| Thu_IST_07h | weekday_hour | 2025_train | LONG   |            30 |      3120 |                  58.942 |                 40.545 |                         36.699 |                         49.712 |                       24.327 |               5.3205 |                      1145 |                           759 |
| Thu_IST_20h | weekday_hour | 2025_train | SHORT  |            30 |      3120 |                  67.276 |                 56.122 |                         36.635 |                         50.737 |                       28.558 |               4.9359 |                      1143 |                           891 |
| Mon_IST_03h | weekday_hour | 2025_train | SHORT  |            30 |      3120 |                  58.077 |                 42.596 |                         36.538 |                         46.635 |                       25.513 |               8.141  |                      1140 |                           796 |
| Tue_IST_02h | weekday_hour | 2025_train | LONG   |            30 |      3120 |                  58.045 |                 39.904 |                         36.538 |                         47.885 |                       24.551 |               5.2244 |                      1140 |                           766 |
| Tue_IST_08h | weekday_hour | 2025_train | SHORT  |            30 |      3120 |                  58.269 |                 40.673 |                         36.314 |                         48.91  |                       24.679 |               5.3846 |                      1133 |                           770 |
| Wed_IST_05h | weekday_hour | 2025_train | SHORT  |            30 |      3120 |                  59.872 |                 38.558 |                         36.25  |                         49.487 |                       22.308 |               5.8974 |                      1131 |                           696 |
| Tue_IST_06h | weekday_hour | 2025_train | SHORT  |            30 |      3120 |                  62.917 |                 46.571 |                         36.09  |                         49.968 |                       26.891 |               6.6026 |                      1126 |                           839 |
| Tue_IST_19h | weekday_hour | 2025_train | SHORT  |            30 |      3120 |                  74.744 |                 62.885 |                         35.865 |                         51.282 |                       27.564 |               4.391  |                      1119 |                           860 |
| Mon_IST_19h | weekday_hour | 2025_train | SHORT  |            30 |      3120 |                  69.712 |                 56.955 |                         35.737 |                         50.609 |                       26.378 |               4.6154 |                      1115 |                           823 |

## Selected entries: net results by period (200 gross TP, 100 stop, 30min maximum)
| period                      |   tested |   positive |   zero_loss |   max_net |
|:----------------------------|---------:|-----------:|------------:|----------:|
| 2025_train                  |      136 |          0 |           0 |   -99.816 |
| 2026_H1_validation          |      136 |          0 |           0 |   -55.502 |
| 2026_H2_seen_recheck        |      136 |          0 |           0 |   -55.314 |
| 2026_Nov_recent_exploratory |      136 |          0 |           0 |    -1.65  |

## Highest net expectancy on each period: NEVER a forward recommendation

### 2025_train
| rule        | side   |   trades |   win_pct |   avg_net_pts |   profit_factor |   losses_or_flat |
|:------------|:-------|---------:|----------:|--------------:|----------------:|-----------------:|
| Fri_IST_03h | LONG   |      678 |     38.64 |       -99.816 |           0.238 |              416 |
| Tue_IST_08h | SHORT  |      671 |     37.56 |      -105.49  |           0.223 |              419 |
| Tue_IST_07h | SHORT  |      790 |     36.08 |      -105.721 |           0.22  |              505 |
| Mon_IST_21h | SHORT  |     1131 |     36.6  |      -106.495 |           0.222 |              717 |
| Mon_IST_06h | SHORT  |     1023 |     37.54 |      -106.656 |           0.219 |              639 |
| Tue_IST_02h | LONG   |      774 |     37.08 |      -107.352 |           0.217 |              487 |
| Mon_IST_03h | SHORT  |      831 |     35.74 |      -107.394 |           0.222 |              534 |
| Wed_IST_23h | LONG   |     1015 |     35.47 |      -108.624 |           0.213 |              655 |
| Tue_IST_06h | SHORT  |      873 |     35.17 |      -109.886 |           0.213 |              566 |
| Tue_IST_18h | LONG   |      719 |     36.72 |      -110.306 |           0.205 |              455 |
| IST_03h     | LONG   |     4745 |     35.26 |      -110.506 |           0.203 |             3072 |
| Wed_IST_05h | SHORT  |      577 |     35.36 |      -111.288 |           0.202 |              373 |

### 2026_H1_validation
| rule        | side   |   trades |   win_pct |   avg_net_pts |   profit_factor |   losses_or_flat |
|:------------|:-------|---------:|----------:|--------------:|----------------:|-----------------:|
| Tue_IST_07h | SHORT  |      190 |     41.58 |       -55.502 |           0.456 |              111 |
| Tue_IST_18h | SHORT  |      143 |     37.76 |       -62.016 |           0.406 |               89 |
| Thu_IST_07h | SHORT  |      197 |     37.56 |       -63.675 |           0.396 |              123 |
| Thu_IST_19h | SHORT  |      322 |     38.2  |       -65.912 |           0.403 |              199 |
| Mon_IST_19h | SHORT  |      324 |     38.27 |       -66.38  |           0.403 |              200 |
| Tue_IST_08h | SHORT  |      155 |     34.84 |       -70.056 |           0.349 |              101 |
| IST_18h     | SHORT  |     1145 |     34.32 |       -71.864 |           0.348 |              752 |
| Mon_IST_03h | LONG   |      256 |     35.94 |       -72.067 |           0.366 |              164 |
| Wed_IST_19h | SHORT  |      320 |     36.56 |       -74.198 |           0.363 |              203 |
| IST_07h     | SHORT  |     1268 |     34.38 |       -74.253 |           0.334 |              832 |
| IST_11h     | SHORT  |      979 |     32.28 |       -75.273 |           0.305 |              663 |
| IST_19h     | SHORT  |     1950 |     34.51 |       -76.275 |           0.343 |             1277 |

### 2026_H2_seen_recheck
| rule        | side   |   trades |   win_pct |   avg_net_pts |   profit_factor |   losses_or_flat |
|:------------|:-------|---------:|----------:|--------------:|----------------:|-----------------:|
| Tue_IST_02h | SHORT  |       80 |     36.25 |       -55.314 |           0.384 |               51 |
| Thu_IST_07h | SHORT  |      131 |     39.69 |       -58.134 |           0.422 |               79 |
| Thu_IST_19h | LONG   |      233 |     42.06 |       -58.136 |           0.448 |              135 |
| Wed_IST_19h | SHORT  |      241 |     40.66 |       -62.352 |           0.422 |              143 |
| Wed_IST_20h | LONG   |      185 |     38.92 |       -66.765 |           0.394 |              113 |
| Mon_IST_06h | SHORT  |      140 |     37.14 |       -68.834 |           0.372 |               88 |
| Wed_IST_05h | LONG   |       71 |     30.99 |       -70.425 |           0.314 |               49 |
| Fri_IST_03h | SHORT  |       93 |     34.41 |       -70.554 |           0.322 |               61 |
| Wed_IST_22h | SHORT  |      116 |     37.07 |       -72.695 |           0.345 |               73 |
| Wed_IST_23h | LONG   |      124 |     34.68 |       -75.567 |           0.339 |               81 |
| IST_09h     | LONG   |      479 |     28.81 |       -76.042 |           0.252 |              341 |
| IST_20h     | LONG   |     1068 |     35.02 |       -76.583 |           0.335 |              694 |

### 2026_Nov_recent_exploratory
| rule        | side   |   trades |   win_pct |   avg_net_pts |   profit_factor |   losses_or_flat |
|:------------|:-------|---------:|----------:|--------------:|----------------:|-----------------:|
| Mon_IST_03h | SHORT  |       35 |     45.71 |       -34.905 |           0.608 |               19 |
| Wed_IST_20h | LONG   |       49 |     48.98 |       -39.109 |           0.588 |               25 |
| Thu_IST_20h | SHORT  |       59 |     44.07 |       -51.037 |           0.499 |               33 |
| IST_03h     | SHORT  |      126 |     38.89 |       -60.981 |           0.412 |               77 |
| IST_05h     | SHORT  |      100 |     35    |       -60.984 |           0.391 |               65 |
| IST_09h     | SHORT  |       93 |     34.41 |       -61.162 |           0.387 |               61 |
| IST_22h     | SHORT  |      135 |     35.56 |       -62.98  |           0.398 |               87 |
| IST_12h     | SHORT  |       81 |     32.1  |       -63.165 |           0.361 |               55 |
| IST_07h     | LONG   |      119 |     35.29 |       -63.995 |           0.393 |               77 |
| IST_10h     | SHORT  |       83 |     32.53 |       -64.431 |           0.363 |               56 |
| IST_03-06   | SHORT  |      324 |     36.11 |       -65.205 |           0.38  |              207 |
| weekday_Wed | LONG   |      316 |     37.03 |       -65.285 |           0.382 |              199 |

## Readout and limitations
- Clock/day effects are observational. Large differences may be regime and sampling effects.
- Training ranks are selected from multiple thresholds. 2026 was previously studied;
  there is NO pristine out-of-sample evaluation.
- Overlapping +200 first-passage events are correlated and should NOT be summed as trades.
- A positive hit probability alone does not cover fees and stopped-out losses.
- Standard price range is not actual bid/ask quote depth, funding or market impact.
- No guarantee of a zero-loss trade, and no live deployment recommendation.

## Files
- all_time_day_volume_volatility_rates.csv — exhaustive group comparisons
- selected_filters_2025_only.csv — selection audit
- trade_summary.csv — full standard and Scalper Offer what-if net outcomes
- trade_ledger.csv.gz — independently simulated entries
- quality.json — data and research limitations
