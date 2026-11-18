# Stage 7 — Every BTC 1-minute candle: time, weekday, volume and volatility

## Predeclared setup
- Dataset: Delta India ETHUSD authentic 1m futures, first Jan 2025 to latest archive.
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
| all_hours_days | baseline | 2025_train                  | LONG   |            30 |    524441 |                   0.018 |                  0.016 |                          0.016 |                          0.018 |                        0.014 |               0.0019 |                        86 |                            74 |
| all_hours_days | baseline | 2025_train                  | SHORT  |            30 |    524441 |                   0.033 |                  0.025 |                          0.033 |                          0.033 |                        0.025 |               0.0015 |                       174 |                           129 |
| all_hours_days | baseline | 2026_H1_validation          | LONG   |            30 |    260203 |                   0     |                  0     |                          0     |                          0     |                        0     |               0      |                         0 |                             0 |
| all_hours_days | baseline | 2026_H1_validation          | SHORT  |            30 |    260203 |                   0     |                  0     |                          0     |                          0     |                        0     |               0      |                         0 |                             0 |
| all_hours_days | baseline | 2026_H2_seen_recheck        | LONG   |            30 |    176950 |                   0.007 |                  0.004 |                          0.007 |                          0.007 |                        0.004 |               0      |                        13 |                             7 |
| all_hours_days | baseline | 2026_H2_seen_recheck        | SHORT  |            30 |    176950 |                   0     |                  0     |                          0     |                          0     |                        0     |               0      |                         0 |                             0 |
| all_hours_days | baseline | 2026_Nov_recent_exploratory | LONG   |            30 |     24421 |                   0     |                  0     |                          0     |                          0     |                        0     |               0      |                         0 |                             0 |
| all_hours_days | baseline | 2026_Nov_recent_exploratory | SHORT  |            30 |     24421 |                   0     |                  0     |                          0     |                          0     |                        0     |               0      |                         0 |                             0 |

## 2025 training: highest 200-before-100-stop event probabilities
| filter                    | kind               | period     | side   |   horizon_min |   signals |   gross_200_reached_pct |   net_200_possible_pct |   gross_200_before_100stop_pct |   gross_200_before_200stop_pct |   net_200_before_100stop_pct |   no_adverse_200_pct |   hits_200_before_100stop |   net_hits_200_before_100stop |
|:--------------------------|:-------------------|:-----------|:-------|--------------:|----------:|------------------------:|-----------------------:|-------------------------------:|-------------------------------:|-----------------------------:|---------------------:|--------------------------:|------------------------------:|
| Mon_IST_07h               | weekday_hour       | 2025_train | SHORT  |            30 |      3120 |                   1.218 |                  1.218 |                          1.186 |                          1.218 |                        1.186 |               0.0321 |                        37 |                            37 |
| Sat_IST_02h               | weekday_hour       | 2025_train | SHORT  |            30 |      3120 |                   1.122 |                  1.09  |                          1.122 |                          1.122 |                        1.09  |               0.0641 |                        35 |                            34 |
| Fri_IST_19h               | weekday_hour       | 2025_train | LONG   |            30 |      3120 |                   0.962 |                  0.865 |                          0.962 |                          0.962 |                        0.865 |               0.0321 |                        30 |                            27 |
| Mon_IST_11h               | weekday_hour       | 2025_train | SHORT  |            30 |      3120 |                   0.929 |                  0.865 |                          0.929 |                          0.929 |                        0.865 |               0.0641 |                        29 |                            27 |
| Thu_IST_19h               | weekday_hour       | 2025_train | SHORT  |            30 |      3120 |                   0.769 |                  0.673 |                          0.769 |                          0.769 |                        0.673 |               0      |                        24 |                            21 |
| Thu_IST_17h               | weekday_hour       | 2025_train | SHORT  |            30 |      3120 |                   0.769 |                  0.128 |                          0.769 |                          0.769 |                        0.128 |               0.0641 |                        24 |                             4 |
| Sun_IST_21h               | weekday_hour       | 2025_train | LONG   |            30 |      3120 |                   0.641 |                  0.641 |                          0.641 |                          0.641 |                        0.641 |               0.0321 |                        20 |                            20 |
| IST_00-03_volatility_2p0x | session_volatility | 2025_train | SHORT  |            30 |      4177 |                   0.575 |                  0.551 |                          0.575 |                          0.575 |                        0.551 |               0.0239 |                        24 |                            23 |
| Mon_IST_00h               | weekday_hour       | 2025_train | SHORT  |            30 |      3120 |                   0.513 |                  0     |                          0.513 |                          0.513 |                        0     |               0.0321 |                        16 |                             0 |
| Sat_volatility_2p0x       | day_volatility     | 2025_train | SHORT  |            30 |      4729 |                   0.508 |                  0.486 |                          0.508 |                          0.508 |                        0.486 |               0.0211 |                        24 |                            23 |
| IST_06-09_volatility_2p0x | session_volatility | 2025_train | SHORT  |            30 |      4464 |                   0.515 |                  0.515 |                          0.493 |                          0.515 |                        0.493 |               0.0224 |                        22 |                            22 |
| IST_00-03_volume_2p0x     | session_volume     | 2025_train | SHORT  |            30 |      3781 |                   0.45  |                  0.423 |                          0.45  |                          0.45  |                        0.423 |               0      |                        17 |                            16 |
| Sat_IST_03h               | weekday_hour       | 2025_train | LONG   |            30 |      3120 |                   0.449 |                  0.417 |                          0.449 |                          0.449 |                        0.417 |               0.0962 |                        14 |                            13 |
| Mon_volatility_2p0x       | day_volatility     | 2025_train | SHORT  |            30 |      6592 |                   0.394 |                  0.394 |                          0.379 |                          0.394 |                        0.379 |               0.0152 |                        25 |                            25 |

## Selected entries: net results by period (200 gross TP, 100 stop, 30min maximum)
| period                      |   tested |   positive |   zero_loss |   max_net |
|:----------------------------|---------:|-----------:|------------:|----------:|
| 2025_train                  |      126 |          0 |           0 |    -9.266 |
| 2026_H1_validation          |      126 |          0 |           0 |    -8.626 |
| 2026_H2_seen_recheck        |      126 |          0 |           0 |    -7.714 |
| 2026_Nov_recent_exploratory |      126 |          0 |           0 |    -3.848 |

## Highest net expectancy on each period: NEVER a forward recommendation

### 2025_train
| rule                | side   |   trades |   win_pct |   avg_net_pts |   profit_factor |   losses_or_flat |
|:--------------------|:-------|---------:|----------:|--------------:|----------------:|-----------------:|
| Thu_IST_19h         | SHORT  |      105 |     33.33 |        -9.266 |           0.389 |               70 |
| Sat_IST_02h         | SHORT  |      108 |     15.74 |        -9.319 |           0.453 |               91 |
| Mon_IST_11h         | SHORT  |      104 |     10.58 |       -11.313 |           0.149 |               93 |
| IST_03h             | LONG   |      735 |     13.88 |       -12.05  |           0.165 |              633 |
| Sun_IST_21h         | LONG   |      104 |     17.31 |       -12.161 |           0.141 |               86 |
| Mon_volatility_2p0x | SHORT  |      948 |     19.2  |       -12.249 |           0.225 |              766 |
| Thu_IST_17h         | SHORT  |      104 |      9.62 |       -12.38  |           0.065 |               94 |
| Mon_IST_07h         | LONG   |      108 |     20.37 |       -12.495 |           0.311 |               86 |
| Sat_IST_03h         | LONG   |      105 |     12.38 |       -12.507 |           0.21  |               92 |
| IST_07h             | LONG   |      732 |     14.48 |       -12.685 |           0.141 |              626 |
| IST_19h             | SHORT  |      736 |     22.96 |       -12.688 |           0.233 |              567 |
| IST_21h             | SHORT  |      733 |     18.28 |       -12.946 |           0.175 |              599 |

### 2026_H1_validation
| rule                  | side   |   trades |   win_pct |   avg_net_pts |   profit_factor |   losses_or_flat |
|:----------------------|:-------|---------:|----------:|--------------:|----------------:|-----------------:|
| Thu_IST_19h           | SHORT  |       52 |     17.31 |        -8.626 |           0.252 |               43 |
| Fri_IST_19h           | SHORT  |       52 |     15.38 |       -10.839 |           0.137 |               44 |
| IST_19h               | SHORT  |      362 |     11.33 |       -11.232 |           0.112 |              321 |
| Mon_IST_00h           | SHORT  |       50 |      6    |       -11.26  |           0.042 |               47 |
| Mon_IST_11h           | SHORT  |       52 |      9.62 |       -11.276 |           0.038 |               47 |
| Sat_IST_02h           | LONG   |       52 |      5.77 |       -11.304 |           0.017 |               49 |
| IST_00-03_volume_2p0x | LONG   |      325 |      6.46 |       -11.512 |           0.111 |              304 |
| Thu_IST_17h           | SHORT  |       52 |      3.85 |       -11.541 |           0.012 |               50 |
| IST_11h               | SHORT  |      362 |      6.63 |       -11.638 |           0.052 |              338 |
| IST_07h               | SHORT  |      362 |      5.8  |       -11.654 |           0.051 |              341 |
| weekday_Thu           | SHORT  |     1237 |      8.81 |       -11.714 |           0.077 |             1128 |
| IST_00h               | LONG   |      361 |      8.03 |       -11.796 |           0.113 |              332 |

### 2026_H2_seen_recheck
| rule                      | side   |   trades |   win_pct |   avg_net_pts |   profit_factor |   losses_or_flat |
|:--------------------------|:-------|---------:|----------:|--------------:|----------------:|-----------------:|
| Thu_IST_19h               | LONG   |       36 |     19.44 |        -7.714 |           0.171 |               29 |
| Sun_IST_21h               | LONG   |       34 |      8.82 |        -8.893 |           0.117 |               31 |
| Fri_IST_19h               | LONG   |       36 |     13.89 |       -10.012 |           0.304 |               31 |
| Thu_IST_17h               | LONG   |       36 |      5.56 |       -11.277 |           0.044 |               34 |
| IST_20h                   | LONG   |      246 |     12.2  |       -11.512 |           0.094 |              216 |
| Sat_IST_03h               | LONG   |       36 |      5.56 |       -11.577 |           0.063 |               34 |
| Mon_IST_07h               | SHORT  |       34 |      8.82 |       -11.653 |           0.055 |               31 |
| IST_07h                   | SHORT  |      246 |      6.5  |       -11.662 |           0.06  |              230 |
| IST_18h                   | SHORT  |      246 |      4.07 |       -11.718 |           0.05  |              236 |
| Sat_IST_02h               | LONG   |       36 |      2.78 |       -11.821 |           0.059 |               35 |
| IST_17h                   | LONG   |      246 |      3.25 |       -11.884 |           0.015 |              238 |
| IST_00-03_volatility_2p0x | LONG   |      273 |      4.76 |       -11.894 |           0.052 |              260 |

### 2026_Nov_recent_exploratory
| rule                            | side   |   trades |   win_pct |   avg_net_pts |   profit_factor |   losses_or_flat |
|:--------------------------------|:-------|---------:|----------:|--------------:|----------------:|-----------------:|
| IST_03h                         | SHORT  |       34 |      2.94 |        -9.059 |           0.215 |               33 |
| IST_19h                         | SHORT  |       34 |     11.76 |        -9.233 |           0.157 |               30 |
| Mon_volatility_2p0x             | SHORT  |       55 |     12.73 |        -9.725 |           0.231 |               48 |
| IST_07h                         | LONG   |       34 |     14.71 |        -9.815 |           0.194 |               29 |
| weekday_Thu                     | SHORT  |       96 |     11.46 |       -10.133 |           0.113 |               85 |
| weekday_Wed                     | LONG   |      106 |      6.6  |       -10.527 |           0.093 |               99 |
| high_volume_and_volatility_3p0x | SHORT  |       90 |     12.22 |       -10.743 |           0.152 |               79 |
| IST_18-21                       | SHORT  |      102 |     11.76 |       -10.782 |           0.151 |               90 |
| IST_06h                         | SHORT  |       34 |      8.82 |       -10.818 |           0.023 |               31 |
| Sat_volatility_2p0x             | SHORT  |       39 |      2.56 |       -10.938 |           0.02  |               38 |
| IST_00-03_volume_2p0x           | SHORT  |       34 |      2.94 |       -10.962 |           0.064 |               33 |
| IST_21h                         | SHORT  |       34 |     20.59 |       -10.992 |           0.165 |               27 |

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
