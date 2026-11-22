# BTCUSD 15M Supertrend Line Touch vs Bullish Flip vs Flip + Breakout

New third variant: a bullish flip and next 15m GREEN candle with CLOSE
above flip candle HIGH; market enter at third 15m candle OPEN.
Same Supertrend(10,3) closing exit for all three; fixed % SL & TP
on 1m, conservative stop-first OHLC ties. No profit-lock experiment
in this three-way fixed risk/reward comparison. Original filters and
fee model: taker 0.05% each side + GST18 and 5 BTC pts slip per side.

## Same volume>=1 ATR>=0.20 filters, highest win count and rates
| entry_type               | metric            |   sl_pct |   tp_pct |   trades |   wins |   losses |   win_rate_pct |   net_pts |   profitable_months |   losing_months |   max_drawdown_pts |
|:-------------------------|:------------------|---------:|---------:|---------:|-------:|---------:|---------------:|----------:|--------------------:|----------------:|-------------------:|
| after_line_touch         | max_wins          |        1 |      0.2 |      108 |     73 |       35 |          67.59 | -11704    |                   6 |              16 |           12000.3  |
| after_line_touch         | max_winrate_min20 |        1 |      0.2 |      108 |     73 |       35 |          67.59 | -11704    |                   6 |              16 |           12000.3  |
| after_line_touch         | max_winrate_min50 |        1 |      0.2 |      108 |     73 |       35 |          67.59 | -11704    |                   6 |              16 |           12000.3  |
| after_line_touch         | max_net_min20     |        1 |      1.5 |      108 |     37 |       71 |          34.26 |   8822.33 |                  13 |               9 |            4312.12 |
| after_line_touch         | max_net_min50     |        1 |      1.5 |      108 |     37 |       71 |          34.26 |   8822.33 |                  13 |               9 |            4312.12 |
| after_bullish_flip       | max_wins          |        3 |      0.2 |      197 |    159 |       38 |          80.71 | -28883.5  |                   7 |              15 |           30485.8  |
| after_bullish_flip       | max_winrate_min20 |        3 |      0.2 |      197 |    159 |       38 |          80.71 | -28883.5  |                   7 |              15 |           30485.8  |
| after_bullish_flip       | max_winrate_min50 |        3 |      0.2 |      197 |    159 |       38 |          80.71 | -28883.5  |                   7 |              15 |           30485.8  |
| after_bullish_flip       | max_net_min20     |        3 |      1.5 |      197 |     78 |      119 |          39.59 | -16829.5  |                  10 |              12 |           23011.6  |
| after_bullish_flip       | max_net_min50     |        3 |      1.5 |      197 |     78 |      119 |          39.59 | -16829.5  |                  10 |              12 |           23011.6  |
| flip_plus_green_breakout | max_wins          |        3 |      0.2 |      132 |    108 |       24 |          81.82 | -19289    |                   8 |              14 |           20560.8  |
| flip_plus_green_breakout | max_winrate_min20 |        3 |      0.2 |      132 |    108 |       24 |          81.82 | -19289    |                   8 |              14 |           20560.8  |
| flip_plus_green_breakout | max_winrate_min50 |        3 |      0.2 |      132 |    108 |       24 |          81.82 | -19289    |                   8 |              14 |           20560.8  |
| flip_plus_green_breakout | max_net_min20     |        3 |      1.5 |      132 |     52 |       80 |          39.39 | -11063.7  |                  10 |              12 |           17013.9  |
| flip_plus_green_breakout | max_net_min50     |        3 |      1.5 |      132 |     52 |       80 |          39.39 | -11063.7  |                  10 |              12 |           17013.9  |

## Selected ratios, same filters
| entry_type               |   sl_pct |   tp_pct |   trades |   wins |   win_rate_pct |   net_pts |   profitable_months |   losing_months |
|:-------------------------|---------:|---------:|---------:|-------:|---------------:|----------:|--------------------:|----------------:|
| after_line_touch         |     0.5  |      1   |      108 |     41 |          37.96 |   2993.54 |                  12 |              10 |
| after_line_touch         |     0.5  |      1.5 |      108 |     34 |          31.48 |   6231.58 |                  11 |              11 |
| after_line_touch         |     0.75 |      1.5 |      108 |     36 |          33.33 |   7928.77 |                  12 |              10 |
| after_line_touch         |     1    |      1   |      108 |     45 |          41.67 |   5457.49 |                  12 |              10 |
| after_line_touch         |     1    |      2   |      108 |     31 |          28.7  |   3336.91 |                  11 |              11 |
| after_line_touch         |     1    |      3   |      108 |     29 |          26.85 |  -3266.72 |                   7 |              15 |
| after_line_touch         |     2    |      4   |      108 |     29 |          26.85 |  -2792.59 |                   7 |              15 |
| after_line_touch         |     3    |      6   |      108 |     29 |          26.85 |  -1436.59 |                   8 |              14 |
| after_bullish_flip       |     0.5  |      1   |      197 |     57 |          28.93 | -31508.8  |                   4 |              18 |
| after_bullish_flip       |     0.5  |      1.5 |      197 |     45 |          22.84 | -30835.5  |                   5 |              17 |
| after_bullish_flip       |     0.75 |      1.5 |      197 |     61 |          30.96 | -24901.5  |                   8 |              14 |
| after_bullish_flip       |     1    |      1   |      197 |     83 |          42.13 | -27747.2  |                   7 |              15 |
| after_bullish_flip       |     1    |      2   |      197 |     60 |          30.46 | -27229.4  |                   5 |              17 |
| after_bullish_flip       |     1    |      3   |      197 |     57 |          28.93 | -26173    |                   7 |              15 |
| after_bullish_flip       |     2    |      4   |      197 |     60 |          30.46 | -34536    |                   5 |              17 |
| after_bullish_flip       |     3    |      6   |      197 |     62 |          31.47 | -22848.3  |                   6 |              16 |
| flip_plus_green_breakout |     0.5  |      1   |      132 |     39 |          29.55 | -20228.5  |                   4 |              18 |
| flip_plus_green_breakout |     0.5  |      1.5 |      132 |     29 |          21.97 | -22972    |                   5 |              17 |
| flip_plus_green_breakout |     0.75 |      1.5 |      132 |     37 |          28.03 | -23052.8  |                   6 |              16 |
| flip_plus_green_breakout |     1    |      1   |      132 |     54 |          40.91 | -20064    |                   8 |              14 |
| flip_plus_green_breakout |     1    |      2   |      132 |     39 |          29.55 | -17654.4  |                   6 |              16 |
| flip_plus_green_breakout |     1    |      3   |      132 |     36 |          27.27 | -17292.4  |                   8 |              14 |
| flip_plus_green_breakout |     2    |      4   |      132 |     39 |          29.55 | -24501.4  |                   6 |              16 |
| flip_plus_green_breakout |     3    |      6   |      132 |     40 |          30.3  | -20291.1  |                   5 |              17 |

## Other filters and highest wins
| entry_type               | metric            |   sl_pct |   tp_pct |   trades |   wins |   losses |   win_rate_pct |   net_pts |   profitable_months |   losing_months |   max_drawdown_pts | scope               | vol_filter   | atr_filter     |
|:-------------------------|:------------------|---------:|---------:|---------:|-------:|---------:|---------------:|----------:|--------------------:|----------------:|-------------------:|:--------------------|:-------------|:---------------|
| after_line_touch         | max_wins          |     1    |     0.2  |      108 |     73 |       35 |          67.59 | -11704    |                   6 |              16 |           12000.3  | same_filters        | vol_ge_1p0   | atrpct_ge_0p20 |
| after_line_touch         | max_winrate_min20 |     1    |     0.2  |      108 |     73 |       35 |          67.59 | -11704    |                   6 |              16 |           12000.3  | same_filters        | vol_ge_1p0   | atrpct_ge_0p20 |
| after_line_touch         | max_winrate_min50 |     1    |     0.2  |      108 |     73 |       35 |          67.59 | -11704    |                   6 |              16 |           12000.3  | same_filters        | vol_ge_1p0   | atrpct_ge_0p20 |
| after_line_touch         | max_net_min20     |     1    |     1.5  |      108 |     37 |       71 |          34.26 |   8822.33 |                  13 |               9 |            4312.12 | same_filters        | vol_ge_1p0   | atrpct_ge_0p20 |
| after_line_touch         | max_net_min50     |     1    |     1.5  |      108 |     37 |       71 |          34.26 |   8822.33 |                  13 |               9 |            4312.12 | same_filters        | vol_ge_1p0   | atrpct_ge_0p20 |
| after_line_touch         | max_wins          |     0.75 |     0.2  |       34 |     29 |        5 |          85.29 |   -955.94 |                  10 |               4 |            2038.98 | atr_high_volume_off | vol_off      | atrpct_ge_0p40 |
| after_line_touch         | max_winrate_min20 |     0.75 |     0.2  |       34 |     29 |        5 |          85.29 |   -955.94 |                  10 |               4 |            2038.98 | atr_high_volume_off | vol_off      | atrpct_ge_0p40 |
| after_line_touch         | max_net_min20     |     0.15 |     0.9  |       34 |     11 |       23 |          32.35 |   2201.79 |                   7 |               7 |            1959.79 | atr_high_volume_off | vol_off      | atrpct_ge_0p40 |
| after_line_touch         | max_wins          |     1    |     0.2  |      220 |    142 |       78 |          64.55 | -24880.8  |                   2 |              20 |           25282.7  | all_filters         | vol_off      | atrpct_ge_0p10 |
| after_line_touch         | max_winrate_min20 |     0.75 |     0.2  |       34 |     29 |        5 |          85.29 |   -955.94 |                  10 |               4 |            2038.98 | all_filters         | vol_off      | atrpct_ge_0p40 |
| after_line_touch         | max_winrate_min50 |     1    |     0.2  |       69 |     51 |       18 |          73.91 |  -5181.63 |                   9 |              12 |            5327.73 | all_filters         | vol_ge_1p5   | atrpct_ge_0p20 |
| after_line_touch         | max_net_min20     |     1    |     1.5  |      108 |     37 |       71 |          34.26 |   8822.33 |                  13 |               9 |            4312.12 | all_filters         | vol_ge_1p0   | atrpct_ge_0p20 |
| after_line_touch         | max_net_min50     |     1    |     1.5  |      108 |     37 |       71 |          34.26 |   8822.33 |                  13 |               9 |            4312.12 | all_filters         | vol_ge_1p0   | atrpct_ge_0p20 |
| after_bullish_flip       | max_wins          |     3    |     0.2  |      197 |    159 |       38 |          80.71 | -28883.5  |                   7 |              15 |           30485.8  | same_filters        | vol_ge_1p0   | atrpct_ge_0p20 |
| after_bullish_flip       | max_winrate_min20 |     3    |     0.2  |      197 |    159 |       38 |          80.71 | -28883.5  |                   7 |              15 |           30485.8  | same_filters        | vol_ge_1p0   | atrpct_ge_0p20 |
| after_bullish_flip       | max_winrate_min50 |     3    |     0.2  |      197 |    159 |       38 |          80.71 | -28883.5  |                   7 |              15 |           30485.8  | same_filters        | vol_ge_1p0   | atrpct_ge_0p20 |
| after_bullish_flip       | max_net_min20     |     3    |     1.5  |      197 |     78 |      119 |          39.59 | -16829.5  |                  10 |              12 |           23011.6  | same_filters        | vol_ge_1p0   | atrpct_ge_0p20 |
| after_bullish_flip       | max_net_min50     |     3    |     1.5  |      197 |     78 |      119 |          39.59 | -16829.5  |                  10 |              12 |           23011.6  | same_filters        | vol_ge_1p0   | atrpct_ge_0p20 |
| after_bullish_flip       | max_wins          |     3    |     0.24 |       71 |     64 |        7 |          90.14 |  -4335.18 |                  11 |               6 |            4998.86 | atr_high_volume_off | vol_off      | atrpct_ge_0p40 |
| after_bullish_flip       | max_winrate_min20 |     3    |     0.24 |       71 |     64 |        7 |          90.14 |  -4335.18 |                  11 |               6 |            4998.86 | atr_high_volume_off | vol_off      | atrpct_ge_0p40 |
| after_bullish_flip       | max_winrate_min50 |     3    |     0.24 |       71 |     64 |        7 |          90.14 |  -4335.18 |                  11 |               6 |            4998.86 | atr_high_volume_off | vol_off      | atrpct_ge_0p40 |
| after_bullish_flip       | max_net_min20     |     3    |     6    |       71 |     28 |       43 |          39.44 |   9771.64 |                   7 |              10 |            8392.49 | atr_high_volume_off | vol_off      | atrpct_ge_0p40 |
| after_bullish_flip       | max_net_min50     |     3    |     6    |       71 |     28 |       43 |          39.44 |   9771.64 |                   7 |              10 |            8392.49 | atr_high_volume_off | vol_off      | atrpct_ge_0p40 |
| after_bullish_flip       | max_wins          |     3    |     0.2  |      343 |    268 |       75 |          78.13 | -43278.2  |                   4 |              18 |           43565.9  | all_filters         | vol_off      | atr_off        |
| after_bullish_flip       | max_winrate_min20 |     3    |     0.3  |       20 |     19 |        1 |          95    |    279.91 |                   9 |               1 |            2757.47 | all_filters         | vol_ge_2p0   | atrpct_ge_0p40 |
| after_bullish_flip       | max_winrate_min50 |     3    |     0.24 |       71 |     64 |        7 |          90.14 |  -4335.18 |                  11 |               6 |            4998.86 | all_filters         | vol_off      | atrpct_ge_0p40 |
| after_bullish_flip       | max_net_min20     |     3    |     6    |       41 |     17 |       24 |          41.46 |  14259.9  |                   8 |               7 |            7928.52 | all_filters         | vol_ge_1p25  | atrpct_ge_0p40 |
| after_bullish_flip       | max_net_min50     |     3    |     6    |       71 |     28 |       43 |          39.44 |   9771.64 |                   7 |              10 |            8392.49 | all_filters         | vol_off      | atrpct_ge_0p40 |
| flip_plus_green_breakout | max_wins          |     3    |     0.2  |      132 |    108 |       24 |          81.82 | -19289    |                   8 |              14 |           20560.8  | same_filters        | vol_ge_1p0   | atrpct_ge_0p20 |
| flip_plus_green_breakout | max_winrate_min20 |     3    |     0.2  |      132 |    108 |       24 |          81.82 | -19289    |                   8 |              14 |           20560.8  | same_filters        | vol_ge_1p0   | atrpct_ge_0p20 |
| flip_plus_green_breakout | max_winrate_min50 |     3    |     0.2  |      132 |    108 |       24 |          81.82 | -19289    |                   8 |              14 |           20560.8  | same_filters        | vol_ge_1p0   | atrpct_ge_0p20 |
| flip_plus_green_breakout | max_net_min20     |     3    |     1.5  |      132 |     52 |       80 |          39.39 | -11063.7  |                  10 |              12 |           17013.9  | same_filters        | vol_ge_1p0   | atrpct_ge_0p20 |
| flip_plus_green_breakout | max_net_min50     |     3    |     1.5  |      132 |     52 |       80 |          39.39 | -11063.7  |                  10 |              12 |           17013.9  | same_filters        | vol_ge_1p0   | atrpct_ge_0p20 |
| flip_plus_green_breakout | max_wins          |     3    |     0.24 |       48 |     43 |        5 |          89.58 |  -4624.47 |                  10 |               5 |            4939.44 | atr_high_volume_off | vol_off      | atrpct_ge_0p40 |
| flip_plus_green_breakout | max_winrate_min20 |     3    |     0.24 |       48 |     43 |        5 |          89.58 |  -4624.47 |                  10 |               5 |            4939.44 | atr_high_volume_off | vol_off      | atrpct_ge_0p40 |
| flip_plus_green_breakout | max_net_min20     |     3    |     6    |       48 |     18 |       30 |          37.5  |   6847.02 |                   6 |               9 |           12358.1  | atr_high_volume_off | vol_off      | atrpct_ge_0p40 |
| flip_plus_green_breakout | max_wins          |     3    |     0.2  |      236 |    185 |       51 |          78.39 | -31016.3  |                   4 |              18 |           31614    | all_filters         | vol_off      | atr_off        |
| flip_plus_green_breakout | max_winrate_min20 |     3    |     0.3  |       27 |     25 |        2 |          92.59 |   -887.87 |                  11 |               2 |            2808.84 | all_filters         | vol_ge_1p25  | atrpct_ge_0p40 |
| flip_plus_green_breakout | max_winrate_min50 |     3    |     0.2  |       63 |     56 |        7 |          88.89 |  -7163.96 |                  15 |               6 |            8388.99 | all_filters         | vol_ge_1p25  | atrpct_ge_0p30 |
| flip_plus_green_breakout | max_net_min20     |     3    |     6    |       40 |     14 |       26 |          35    |   8830.92 |                   9 |               8 |            5288.7  | all_filters         | vol_ge_1p25  | atrrel_ge_1p25 |
| flip_plus_green_breakout | max_net_min50     |     3    |     6    |       50 |     16 |       34 |          32    |   2794.17 |                   8 |              11 |            8880.67 | all_filters         | vol_ge_1p0   | atrrel_ge_1p25 |

## Limitations
No independent untouched future sample. In-sample optimized results.
No model for leverage, funding, bid/ask depth or liquidation.
1-BTC equivalent price points, not percent account returns.
