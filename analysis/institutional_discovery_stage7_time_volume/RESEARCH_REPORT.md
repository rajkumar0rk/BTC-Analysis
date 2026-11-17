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
| all_hours_days | baseline | 2025_train                  | LONG   |            30 |    524456 |                  37.517 |                 19.679 |                         25.907 |                         32.816 |                       12.923 |               3.5595 |                    135872 |                         67773 |
| all_hours_days | baseline | 2025_train                  | SHORT  |            30 |    524456 |                  37.506 |                 20.018 |                         25.975 |                         33.042 |                       13.103 |               3.6777 |                    136230 |                         68718 |
| all_hours_days | baseline | 2026_H1_validation          | LONG   |            30 |    260198 |                  28.394 |                 16.083 |                         20.928 |                         25.738 |                       11.285 |               2.349  |                     54455 |                         29363 |
| all_hours_days | baseline | 2026_H1_validation          | SHORT  |            30 |    260198 |                  29.8   |                 16.983 |                         22.446 |                         27.304 |                       12.387 |               2.4274 |                     58404 |                         32231 |
| all_hours_days | baseline | 2026_H2_seen_recheck        | LONG   |            30 |    175510 |                  19.968 |                  9.954 |                         16.119 |                         18.839 |                        7.818 |               1.8705 |                     28290 |                         13721 |
| all_hours_days | baseline | 2026_H2_seen_recheck        | SHORT  |            30 |    175510 |                  19.46  |                  9.417 |                         15.842 |                         18.427 |                        7.512 |               1.9076 |                     27804 |                         13184 |
| all_hours_days | baseline | 2026_Nov_recent_exploratory | LONG   |            30 |     22901 |                  27.435 |                 14.702 |                         20.06  |                         24.628 |                       10.353 |               2.3449 |                      4594 |                          2371 |
| all_hours_days | baseline | 2026_Nov_recent_exploratory | SHORT  |            30 |     22901 |                  31.518 |                 18.296 |                         24.252 |                         29.379 |                       13.545 |               2.7248 |                      5554 |                          3102 |

## 2025 training: highest 200-before-100-stop event probabilities
| filter      | kind         | period     | side   |   horizon_min |   signals |   gross_200_reached_pct |   net_200_possible_pct |   gross_200_before_100stop_pct |   gross_200_before_200stop_pct |   net_200_before_100stop_pct |   no_adverse_200_pct |   hits_200_before_100stop |   net_hits_200_before_100stop |
|:------------|:-------------|:-----------|:-------|--------------:|----------:|------------------------:|-----------------------:|-------------------------------:|-------------------------------:|-----------------------------:|---------------------:|--------------------------:|------------------------------:|
| Tue_IST_07h | weekday_hour | 2025_train | SHORT  |            30 |      3120 |                  53.59  |                 31.763 |                         38.75  |                         47.372 |                       23.173 |               5.9295 |                      1209 |                           723 |
| Tue_IST_19h | weekday_hour | 2025_train | SHORT  |            30 |      3120 |                  68.013 |                 50.385 |                         37.788 |                         51.891 |                       26.186 |               4.7756 |                      1179 |                           817 |
| Thu_IST_20h | weekday_hour | 2025_train | SHORT  |            30 |      3089 |                  62.48  |                 44.901 |                         36.42  |                         49.919 |                       25.316 |               4.7912 |                      1125 |                           782 |
| Wed_IST_22h | weekday_hour | 2025_train | LONG   |            30 |      3180 |                  55.472 |                 33.679 |                         36.321 |                         48.648 |                       22.17  |               4.0881 |                      1155 |                           705 |
| Mon_IST_07h | weekday_hour | 2025_train | LONG   |            30 |      3120 |                  53.686 |                 32.724 |                         36.218 |                         46.731 |                       22.244 |               4.8397 |                      1130 |                           694 |
| Wed_IST_21h | weekday_hour | 2025_train | SHORT  |            30 |      3180 |                  57.013 |                 35.314 |                         35.881 |                         49.497 |                       21.95  |               3.6164 |                      1141 |                           698 |
| Fri_IST_22h | weekday_hour | 2025_train | SHORT  |            30 |      3120 |                  58.141 |                 39.647 |                         35.833 |                         47.756 |                       23.942 |               4.5833 |                      1118 |                           747 |
| Thu_IST_01h | weekday_hour | 2025_train | LONG   |            30 |      3180 |                  56.101 |                 36.038 |                         35.755 |                         47.987 |                       23.145 |               5.5975 |                      1137 |                           736 |
| Mon_IST_06h | weekday_hour | 2025_train | SHORT  |            30 |      3120 |                  55.737 |                 35.673 |                         35.705 |                         47.051 |                       22.628 |               5.5449 |                      1114 |                           706 |
| Tue_IST_06h | weekday_hour | 2025_train | SHORT  |            30 |      3120 |                  51.603 |                 30.705 |                         35.609 |                         45.577 |                       19.904 |               5.8974 |                      1111 |                           621 |
| Tue_IST_22h | weekday_hour | 2025_train | LONG   |            30 |      3120 |                  55.481 |                 33.494 |                         35.417 |                         47.276 |                       21.891 |               4.0385 |                      1105 |                           683 |
| Wed_IST_19h | weekday_hour | 2025_train | LONG   |            30 |      3180 |                  63.396 |                 43.679 |                         35.377 |                         49.151 |                       22.107 |               4.4969 |                      1125 |                           703 |
| Wed_IST_01h | weekday_hour | 2025_train | SHORT  |            30 |      3102 |                  52.353 |                 32.27  |                         35.139 |                         45.487 |                       21.019 |               5.706  |                      1090 |                           652 |
| Mon_IST_20h | weekday_hour | 2025_train | SHORT  |            30 |      3120 |                  62.596 |                 44.006 |                         35.096 |                         48.013 |                       23.654 |               4.2308 |                      1095 |                           738 |

## Selected entries: net results by period (200 gross TP, 100 stop, 30min maximum)
| period                      |   tested |   positive |   zero_loss |   max_net |
|:----------------------------|---------:|-----------:|------------:|----------:|
| 2025_train                  |      134 |          0 |           0 |  -107.734 |
| 2026_H1_validation          |      134 |          0 |           0 |   -68.979 |
| 2026_H2_seen_recheck        |      134 |          0 |           0 |   -67.256 |
| 2026_Nov_recent_exploratory |      134 |          2 |           0 |    21.17  |

## Highest net expectancy on each period: NEVER a forward recommendation

### 2025_train
| rule        | side   |   trades |   win_pct |   avg_net_pts |   profit_factor |   losses_or_flat |
|:------------|:-------|---------:|----------:|--------------:|----------------:|-----------------:|
| Thu_IST_01h | LONG   |      613 |     38.99 |      -107.734 |           0.207 |              374 |
| Tue_IST_07h | SHORT  |      531 |     36.16 |      -114.06  |           0.183 |              339 |
| Mon_IST_06h | SHORT  |      695 |     35.97 |      -117.352 |           0.183 |              445 |
| Wed_IST_22h | LONG   |      624 |     36.22 |      -117.491 |           0.184 |              398 |
| Tue_IST_19h | SHORT  |      962 |     37.01 |      -117.876 |           0.18  |              606 |
| IST_03h     | LONG   |     3061 |     34.2  |      -118.063 |           0.168 |             2014 |
| Mon_IST_07h | LONG   |      623 |     35.63 |      -118.901 |           0.177 |              401 |
| Thu_IST_19h | SHORT  |      904 |     37.06 |      -119     |           0.178 |              569 |
| Tue_IST_06h | SHORT  |      631 |     35.5  |      -119.616 |           0.175 |              407 |
| Fri_IST_22h | SHORT  |      727 |     35.9  |      -119.684 |           0.176 |              466 |
| Wed_IST_21h | SHORT  |      756 |     35.19 |      -121.33  |           0.174 |              490 |
| Mon_IST_20h | SHORT  |     1067 |     34.58 |      -121.433 |           0.175 |              698 |

### 2026_H1_validation
| rule        | side   |   trades |   win_pct |   avg_net_pts |   profit_factor |   losses_or_flat |
|:------------|:-------|---------:|----------:|--------------:|----------------:|-----------------:|
| Tue_IST_07h | SHORT  |      165 |     40    |       -68.979 |           0.368 |               99 |
| Thu_IST_19h | SHORT  |      299 |     37.46 |       -80.093 |           0.329 |              187 |
| Tue_IST_06h | LONG   |      158 |     35.44 |       -81.801 |           0.301 |              102 |
| IST_18h     | SHORT  |     1055 |     33.84 |       -83.071 |           0.291 |              698 |
| Tue_IST_22h | SHORT  |      248 |     37.5  |       -83.614 |           0.306 |              155 |
| Thu_IST_20h | SHORT  |      430 |     36.74 |       -86.782 |           0.303 |              272 |
| Tue_IST_20h | SHORT  |      427 |     36.53 |       -87.49  |           0.297 |              271 |
| IST_07h     | SHORT  |     1119 |     31.72 |       -87.654 |           0.264 |              764 |
| IST_10h     | SHORT  |      860 |     29.65 |       -88.547 |           0.235 |              605 |
| IST_11h     | SHORT  |      869 |     29.11 |       -88.764 |           0.232 |              616 |
| Mon_IST_20h | LONG   |      387 |     35.92 |       -89.085 |           0.287 |              248 |
| weekday_Tue | SHORT  |     3645 |     33.36 |       -89.11  |           0.267 |             2429 |

### 2026_H2_seen_recheck
| rule        | side   |   trades |   win_pct |   avg_net_pts |   profit_factor |   losses_or_flat |
|:------------|:-------|---------:|----------:|--------------:|----------------:|-----------------:|
| Thu_IST_19h | LONG   |      203 |     43.35 |       -67.256 |           0.389 |              115 |
| Tue_IST_20h | LONG   |      120 |     40    |       -76.763 |           0.334 |               72 |
| Mon_IST_20h | LONG   |      155 |     39.35 |       -77.175 |           0.337 |               94 |
| Wed_IST_19h | SHORT  |      213 |     39.91 |       -78.557 |           0.334 |              128 |
| Wed_IST_22h | SHORT  |       84 |     36.9  |       -78.77  |           0.296 |               53 |
| IST_18h     | SHORT  |      648 |     33.8  |       -85.172 |           0.269 |              429 |
| Thu_IST_01h | LONG   |       78 |     32.05 |       -85.323 |           0.238 |               53 |
| IST_20h     | LONG   |      892 |     35.31 |       -85.522 |           0.286 |              577 |
| Mon_IST_07h | SHORT  |       96 |     34.38 |       -87.218 |           0.263 |               63 |
| Fri_IST_22h | SHORT  |       99 |     33.33 |       -87.487 |           0.253 |               66 |
| IST_03h     | SHORT  |      501 |     28.14 |       -87.722 |           0.213 |              360 |
| Tue_IST_19h | LONG   |      194 |     37.11 |       -88.197 |           0.294 |              122 |

### 2026_Nov_recent_exploratory
| rule        | side   |   trades |   win_pct |   avg_net_pts |   profit_factor |   losses_or_flat |
|:------------|:-------|---------:|----------:|--------------:|----------------:|-----------------:|
| Thu_IST_20h | SHORT  |       53 |     54.72 |       -35.136 |           0.609 |               24 |
| IST_19h     | SHORT  |      107 |     39.25 |       -66.358 |           0.376 |               65 |
| Fri_IST_20h | SHORT  |       45 |     42.22 |       -69.364 |           0.388 |               26 |
| IST_08h     | SHORT  |      106 |     38.68 |       -69.391 |           0.363 |               65 |
| IST_10h     | SHORT  |       79 |     35.44 |       -72.136 |           0.331 |               51 |
| Mon_IST_20h | SHORT  |       50 |     40    |       -73.27  |           0.369 |               30 |
| IST_20h     | SHORT  |      252 |     39.68 |       -74.191 |           0.357 |              152 |
| IST_18-21   | SHORT  |      420 |     38.57 |       -75.127 |           0.344 |              258 |
| weekday_Thu | SHORT  |      287 |     37.63 |       -76.015 |           0.32  |              179 |
| weekday_Sat | SHORT  |      230 |     31.74 |       -76.44  |           0.298 |              157 |
| IST_06-09   | SHORT  |      321 |     36.14 |       -76.493 |           0.327 |              205 |
| IST_06h     | SHORT  |      105 |     34.29 |       -77.324 |           0.315 |               69 |

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
