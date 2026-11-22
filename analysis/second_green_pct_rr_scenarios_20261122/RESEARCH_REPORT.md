# BTCUSD original Supertrend exit: percentage risk/reward scenarios

Important: 1:2 = 1% BTC price hard stop / 2% BTC price take profit.
Not BTC points, and not 1% or 2% on leveraged account equity.
The original 15-minute Supertrend(10,3) closing exit remains ON.
These are fixed percentage R:R exits, NOT the separate profit-lock
experiment. There is no profit-trailing/step-up in this test.
15m second GREEN confirmation after bullish line touch vs flip.
Market fill third 15m open using 1m OHLC, 1m SL-first tie,
taker each way 0.05%, GST 18%, 5 BTC points slip each way.
22 completed IST entry months Jan2025-Oct2026.

Full factorial size 24024 (2 entries x 42 filters x
13 stop levels x 22 targets).
Explicit requested ratios: 36 x 2 entries x 42 filter pairs
= 3024 cases.

## Volume >=1.0x, ATR >=0.20%, after line touch
| risk_reward   | entry_type       |   sl_pct |   tp_pct |   trades |   wins |   win_rate_pct |   sl_exits |   tp_exits |   close_stop_exits |   net_pts |   net_pts_per_trade |   max_drawdown_pts |   profitable_months |   losing_months |
|:--------------|:-----------------|---------:|---------:|---------:|-------:|---------------:|-----------:|-----------:|-------------------:|----------:|--------------------:|-------------------:|--------------------:|----------------:|
| 0.1% : 0.2%   | after_line_touch |     0.1  |     0.2  |      108 |     39 |          36.11 |         69 |         39 |                  0 | -10680    |              -98.89 |           10687.1  |                   2 |              20 |
| 0.1% : 0.3%   | after_line_touch |     0.1  |     0.3  |      108 |     31 |          28.7  |         77 |         31 |                  0 |  -9885.68 |              -91.53 |           10182.4  |                   3 |              19 |
| 0.12% : 0.24% | after_line_touch |     0.12 |     0.24 |      108 |     37 |          34.26 |         69 |         37 |                  2 | -11035.9  |             -102.18 |           11139.5  |                   2 |              20 |
| 0.2% : 0.4%   | after_line_touch |     0.2  |     0.4  |      108 |     42 |          38.89 |         61 |         42 |                  5 |  -7370.18 |              -68.24 |            9259.95 |                   6 |              16 |
| 0.2% : 0.6%   | after_line_touch |     0.2  |     0.6  |      108 |     38 |          35.19 |         65 |         38 |                  5 |  -2754.95 |              -25.51 |            5472.31 |                   9 |              13 |
| 0.3% : 0.6%   | after_line_touch |     0.3  |     0.6  |      108 |     45 |          41.67 |         49 |         45 |                 14 |  -1723.39 |              -15.96 |            5849.47 |                   9 |              13 |
| 0.3% : 0.9%   | after_line_touch |     0.3  |     0.9  |      108 |     37 |          34.26 |         53 |         37 |                 18 |   2063.49 |               19.11 |            5598.84 |                  10 |              12 |
| 0.5% : 1%     | after_line_touch |     0.5  |     1    |      108 |     41 |          37.96 |         34 |         40 |                 34 |   2993.54 |               27.72 |            6799.38 |                  12 |              10 |
| 0.5% : 1.5%   | after_line_touch |     0.5  |     1.5  |      108 |     34 |          31.48 |         37 |         30 |                 41 |   6231.58 |               57.7  |            4212.93 |                  11 |              11 |
| 0.75% : 1.5%  | after_line_touch |     0.75 |     1.5  |      108 |     36 |          33.33 |         14 |         32 |                 62 |   7928.77 |               73.41 |            4505.01 |                  12 |              10 |
| 0.75% : 2.25% | after_line_touch |     0.75 |     2.25 |      108 |     30 |          27.78 |         16 |         16 |                 76 |     98.14 |                0.91 |            7781.26 |                   9 |              13 |
| 1% : 1%       | after_line_touch |     1    |     1    |      108 |     45 |          41.67 |          6 |         44 |                 58 |   5457.49 |               50.53 |            5451.62 |                  12 |              10 |
| 1% : 2%       | after_line_touch |     1    |     2    |      108 |     31 |          28.7  |          6 |         21 |                 81 |   3336.91 |               30.9  |            6920.79 |                  11 |              11 |
| 1% : 3%       | after_line_touch |     1    |     3    |      108 |     29 |          26.85 |          7 |          9 |                 92 |  -3266.72 |              -30.25 |           10125.8  |                   7 |              15 |
| 1% : 4%       | after_line_touch |     1    |     4    |      108 |     29 |          26.85 |          7 |          6 |                 95 |  -1067.25 |               -9.88 |            9208.38 |                   7 |              15 |
| 1% : 5%       | after_line_touch |     1    |     5    |      108 |     29 |          26.85 |          7 |          4 |                 97 |  -1091.62 |              -10.11 |           11590.9  |                   8 |              14 |
| 1% : 6%       | after_line_touch |     1    |     6    |      108 |     29 |          26.85 |          7 |          3 |                 98 |   -144.35 |               -1.34 |           10914.2  |                   8 |              14 |
| 1% : 8%       | after_line_touch |     1    |     8    |      108 |     29 |          26.85 |          7 |          1 |                100 |   -480.4  |               -4.45 |            9560.73 |                   8 |              14 |
| 2% : 2%       | after_line_touch |     2    |     2    |      108 |     31 |          28.7  |          1 |         21 |                 86 |   1850.71 |               17.14 |            7957.65 |                  11 |              11 |
| 2% : 3%       | after_line_touch |     2    |     3    |      108 |     29 |          26.85 |          1 |          9 |                 98 |  -4992.05 |              -46.22 |           11806.3  |                   7 |              15 |
| 2% : 4%       | after_line_touch |     2    |     4    |      108 |     29 |          26.85 |          1 |          6 |                101 |  -2792.59 |              -25.86 |           10888.9  |                   7 |              15 |
| 2% : 6%       | after_line_touch |     2    |     6    |      108 |     29 |          26.85 |          1 |          3 |                104 |  -1869.69 |              -17.31 |           12594.6  |                   8 |              14 |
| 2% : 8%       | after_line_touch |     2    |     8    |      108 |     29 |          26.85 |          1 |          1 |                106 |  -2205.74 |              -20.42 |           11241.2  |                   8 |              14 |
| 2% : 10%      | after_line_touch |     2    |    10    |      108 |     29 |          26.85 |          1 |          0 |                107 |  -2997.77 |              -27.76 |           12033.2  |                   8 |              14 |
| 2% : 12%      | after_line_touch |     2    |    12    |      108 |     29 |          26.85 |          1 |          0 |                107 |  -2997.77 |              -27.76 |           12033.2  |                   8 |              14 |
| 3% : 3%       | after_line_touch |     3    |     3    |      108 |     29 |          26.85 |          0 |          9 |                 99 |  -4558.96 |              -42.21 |           11373.2  |                   7 |              15 |
| 3% : 4%       | after_line_touch |     3    |     4    |      108 |     29 |          26.85 |          0 |          6 |                102 |  -2359.5  |              -21.85 |           10455.8  |                   7 |              15 |
| 3% : 6%       | after_line_touch |     3    |     6    |      108 |     29 |          26.85 |          0 |          3 |                105 |  -1436.59 |              -13.3  |           12161.5  |                   8 |              14 |
| 3% : 9%       | after_line_touch |     3    |     9    |      108 |     29 |          26.85 |          0 |          1 |                107 |  -1095.92 |              -10.15 |           10564    |                   8 |              14 |
| 3% : 12%      | after_line_touch |     3    |    12    |      108 |     29 |          26.85 |          0 |          0 |                108 |  -2564.68 |              -23.75 |           11600.1  |                   8 |              14 |
| 3% : 15%      | after_line_touch |     3    |    15    |      108 |     29 |          26.85 |          0 |          0 |                108 |  -2564.68 |              -23.75 |           11600.1  |                   8 |              14 |
| 4% : 8%       | after_line_touch |     4    |     8    |      108 |     29 |          26.85 |          0 |          1 |                107 |  -1772.64 |              -16.41 |           10808.1  |                   8 |              14 |
| 4% : 12%      | after_line_touch |     4    |    12    |      108 |     29 |          26.85 |          0 |          0 |                108 |  -2564.68 |              -23.75 |           11600.1  |                   8 |              14 |
| 5% : 5%       | after_line_touch |     5    |     5    |      108 |     29 |          26.85 |          0 |          4 |                104 |  -2383.86 |              -22.07 |           12838.3  |                   8 |              14 |
| 5% : 10%      | after_line_touch |     5    |    10    |      108 |     29 |          26.85 |          0 |          0 |                108 |  -2564.68 |              -23.75 |           11600.1  |                   8 |              14 |
| 5% : 15%      | after_line_touch |     5    |    15    |      108 |     29 |          26.85 |          0 |          0 |                108 |  -2564.68 |              -23.75 |           11600.1  |                   8 |              14 |

## Same filters, after bullish flip
| risk_reward   | entry_type         |   sl_pct |   tp_pct |   trades |   wins |   win_rate_pct |   sl_exits |   tp_exits |   close_stop_exits |   net_pts |   net_pts_per_trade |   max_drawdown_pts |   profitable_months |   losing_months |
|:--------------|:-------------------|---------:|---------:|---------:|-------:|---------------:|-----------:|-----------:|-------------------:|----------:|--------------------:|-------------------:|--------------------:|----------------:|
| 0.1% : 0.2%   | after_bullish_flip |     0.1  |     0.2  |      197 |     47 |          23.86 |        150 |         47 |                  0 |  -26481   |             -134.42 |            26481   |                   1 |              21 |
| 0.1% : 0.3%   | after_bullish_flip |     0.1  |     0.3  |      197 |     34 |          17.26 |        163 |         34 |                  0 |  -26829   |             -136.19 |            26829   |                   1 |              21 |
| 0.12% : 0.24% | after_bullish_flip |     0.12 |     0.24 |      197 |     47 |          23.86 |        150 |         47 |                  0 |  -26955.7 |             -136.83 |            26955.7 |                   1 |              21 |
| 0.2% : 0.4%   | after_bullish_flip |     0.2  |     0.4  |      197 |     45 |          22.84 |        151 |         45 |                  1 |  -31966.2 |             -162.26 |            31966.2 |                   0 |              22 |
| 0.2% : 0.6%   | after_bullish_flip |     0.2  |     0.6  |      197 |     37 |          18.78 |        159 |         37 |                  1 |  -29545.3 |             -149.98 |            29545.3 |                   3 |              19 |
| 0.3% : 0.6%   | after_bullish_flip |     0.3  |     0.6  |      197 |     53 |          26.9  |        142 |         53 |                  2 |  -30392.1 |             -154.27 |            30392.1 |                   3 |              19 |
| 0.3% : 0.9%   | after_bullish_flip |     0.3  |     0.9  |      197 |     41 |          20.81 |        153 |         41 |                  3 |  -27580.3 |             -140    |            27580.3 |                   2 |              20 |
| 0.5% : 1%     | after_bullish_flip |     0.5  |     1    |      197 |     57 |          28.93 |        129 |         55 |                 13 |  -31508.8 |             -159.94 |            31972   |                   4 |              18 |
| 0.5% : 1.5%   | after_bullish_flip |     0.5  |     1.5  |      197 |     45 |          22.84 |        134 |         39 |                 24 |  -30835.5 |             -156.53 |            33866.4 |                   5 |              17 |
| 0.75% : 1.5%  | after_bullish_flip |     0.75 |     1.5  |      197 |     61 |          30.96 |         98 |         53 |                 46 |  -24901.5 |             -126.4  |            28067.5 |                   8 |              14 |
| 0.75% : 2.25% | after_bullish_flip |     0.75 |     2.25 |      197 |     54 |          27.41 |         99 |         33 |                 65 |  -24708.4 |             -125.42 |            26575.4 |                   6 |              16 |
| 1% : 1%       | after_bullish_flip |     1    |     1    |      197 |     83 |          42.13 |         57 |         81 |                 59 |  -27747.2 |             -140.85 |            29040.3 |                   7 |              15 |
| 1% : 2%       | after_bullish_flip |     1    |     2    |      197 |     60 |          30.46 |         60 |         41 |                 96 |  -27229.4 |             -138.22 |            30864.4 |                   5 |              17 |
| 1% : 3%       | after_bullish_flip |     1    |     3    |      197 |     57 |          28.93 |         60 |         24 |                113 |  -26173   |             -132.86 |            30788.2 |                   7 |              15 |
| 1% : 4%       | after_bullish_flip |     1    |     4    |      197 |     56 |          28.43 |         60 |         11 |                126 |  -32499.3 |             -164.97 |            36988.8 |                   5 |              17 |
| 1% : 5%       | after_bullish_flip |     1    |     5    |      197 |     56 |          28.43 |         60 |          6 |                131 |  -33995.1 |             -172.56 |            39477.8 |                   7 |              15 |
| 1% : 6%       | after_bullish_flip |     1    |     6    |      197 |     56 |          28.43 |         60 |          5 |                132 |  -31894.2 |             -161.9  |            38370.1 |                   6 |              16 |
| 1% : 8%       | after_bullish_flip |     1    |     8    |      197 |     56 |          28.43 |         60 |          0 |                137 |  -38541.8 |             -195.64 |            43728.2 |                   6 |              16 |
| 2% : 2%       | after_bullish_flip |     2    |     2    |      197 |     65 |          32.99 |         11 |         45 |                141 |  -29841.7 |             -151.48 |            32789.3 |                   6 |              16 |
| 2% : 3%       | after_bullish_flip |     2    |     3    |      197 |     61 |          30.96 |         11 |         26 |                160 |  -30047.2 |             -152.52 |            33975.1 |                   6 |              16 |
| 2% : 4%       | after_bullish_flip |     2    |     4    |      197 |     60 |          30.46 |         11 |         13 |                173 |  -34536   |             -175.31 |            38338.1 |                   5 |              17 |
| 2% : 6%       | after_bullish_flip |     2    |     6    |      197 |     60 |          30.46 |         11 |          7 |                179 |  -30255.7 |             -153.58 |            38019.8 |                   4 |              18 |
| 2% : 8%       | after_bullish_flip |     2    |     8    |      197 |     60 |          30.46 |         11 |          0 |                186 |  -39393   |             -199.96 |            43891.9 |                   4 |              18 |
| 2% : 10%      | after_bullish_flip |     2    |    10    |      197 |     60 |          30.46 |         11 |          0 |                186 |  -39393   |             -199.96 |            43891.9 |                   4 |              18 |
| 2% : 12%      | after_bullish_flip |     2    |    12    |      197 |     60 |          30.46 |         11 |          0 |                186 |  -39393   |             -199.96 |            43891.9 |                   4 |              18 |
| 3% : 3%       | after_bullish_flip |     3    |     3    |      197 |     63 |          31.98 |          1 |         28 |                168 |  -24074.3 |             -122.2  |            28002.1 |                   8 |              14 |
| 3% : 4%       | after_bullish_flip |     3    |     4    |      197 |     62 |          31.47 |          1 |         15 |                181 |  -27102.5 |             -137.58 |            30904.7 |                   7 |              15 |
| 3% : 6%       | after_bullish_flip |     3    |     6    |      197 |     62 |          31.47 |          1 |          8 |                188 |  -22848.3 |             -115.98 |            30339   |                   6 |              16 |
| 3% : 9%       | after_bullish_flip |     3    |     9    |      197 |     62 |          31.47 |          1 |          0 |                196 |  -32579.4 |             -165.38 |            37078.3 |                   6 |              16 |
| 3% : 12%      | after_bullish_flip |     3    |    12    |      197 |     62 |          31.47 |          1 |          0 |                196 |  -32579.4 |             -165.38 |            37078.3 |                   6 |              16 |
| 3% : 15%      | after_bullish_flip |     3    |    15    |      197 |     62 |          31.47 |          1 |          0 |                196 |  -32579.4 |             -165.38 |            37078.3 |                   6 |              16 |
| 4% : 8%       | after_bullish_flip |     4    |     8    |      197 |     62 |          31.47 |          0 |          0 |                197 |  -33145.3 |             -168.25 |            37644.2 |                   6 |              16 |
| 4% : 12%      | after_bullish_flip |     4    |    12    |      197 |     62 |          31.47 |          0 |          0 |                197 |  -33145.3 |             -168.25 |            37644.2 |                   6 |              16 |
| 5% : 5%       | after_bullish_flip |     5    |     5    |      197 |     62 |          31.47 |          0 |         10 |                187 |  -25866.2 |             -131.3  |            30661.4 |                   7 |              15 |
| 5% : 10%      | after_bullish_flip |     5    |    10    |      197 |     62 |          31.47 |          0 |          0 |                197 |  -33145.3 |             -168.25 |            37644.2 |                   6 |              16 |
| 5% : 15%      | after_bullish_flip |     5    |    15    |      197 |     62 |          31.47 |          0 |          0 |                197 |  -33145.3 |             -168.25 |            37644.2 |                   6 |              16 |

## Top requested R:R combinations with >=60 trades (hindsight ranked)
| vol_filter   | atr_filter     | entry_type         |   sl_pct |   tp_pct |   trades |   wins |   win_rate_pct |   sl_exits |   tp_exits |   close_stop_exits |   net_pts |   net_pts_per_trade |   max_drawdown_pts |   profitable_months |   losing_months |
|:-------------|:---------------|:-------------------|---------:|---------:|---------:|-------:|---------------:|-----------:|-----------:|-------------------:|----------:|--------------------:|-------------------:|--------------------:|----------------:|
| vol_off      | atrpct_ge_0p40 | after_bullish_flip |     3    |      6   |       71 |     28 |          39.44 |          1 |          7 |                 63 |   9771.64 |              137.63 |            8392.49 |                   7 |              10 |
| vol_ge_1p0   | atrpct_ge_0p20 | after_line_touch   |     0.75 |      1.5 |      108 |     36 |          33.33 |         14 |         32 |                 62 |   7928.77 |               73.41 |            4505.01 |                  12 |              10 |
| vol_ge_1p0   | atrpct_ge_0p20 | after_line_touch   |     0.5  |      1.5 |      108 |     34 |          31.48 |         37 |         30 |                 41 |   6231.58 |               57.7  |            4212.93 |                  11 |              11 |
| vol_off      | atrpct_ge_0p40 | after_bullish_flip |     4    |      8   |       71 |     28 |          39.44 |          0 |          2 |                 69 |   6073.53 |               85.54 |            8392.49 |                   7 |              10 |
| vol_off      | atrpct_ge_0p40 | after_bullish_flip |     3    |      9   |       71 |     28 |          39.44 |          1 |          1 |                 69 |   5972.51 |               84.12 |            8392.49 |                   8 |               9 |
| vol_off      | atrpct_ge_0p40 | after_bullish_flip |     5    |      5   |       71 |     28 |          39.44 |          0 |          8 |                 63 |   5490.28 |               77.33 |            8392.49 |                   8 |               9 |
| vol_ge_1p0   | atrpct_ge_0p20 | after_line_touch   |     1    |      1   |      108 |     45 |          41.67 |          6 |         44 |                 58 |   5457.49 |               50.53 |            5451.62 |                  12 |              10 |
| vol_ge_1p25  | atrpct_ge_0p20 | after_line_touch   |     0.75 |      1.5 |       88 |     28 |          31.82 |         11 |         25 |                 52 |   5147.01 |               58.49 |            5061.47 |                  11 |              11 |
| vol_ge_1p25  | atrpct_ge_0p20 | after_line_touch   |     0.5  |      1.5 |       88 |     27 |          30.68 |         33 |         24 |                 31 |   4775.28 |               54.26 |            4371.74 |                  13 |               9 |
| vol_off      | atrpct_ge_0p40 | after_bullish_flip |     3    |     12   |       71 |     28 |          39.44 |          1 |          0 |                 70 |   4082.2  |               57.5  |            8392.49 |                   7 |              10 |
| vol_off      | atrpct_ge_0p40 | after_bullish_flip |     3    |     15   |       71 |     28 |          39.44 |          1 |          0 |                 70 |   4082.2  |               57.5  |            8392.49 |                   7 |              10 |
| vol_off      | atrpct_ge_0p40 | after_bullish_flip |     4    |     12   |       71 |     28 |          39.44 |          0 |          0 |                 71 |   3516.34 |               49.53 |            8392.49 |                   6 |              11 |
| vol_off      | atrpct_ge_0p40 | after_bullish_flip |     5    |     10   |       71 |     28 |          39.44 |          0 |          0 |                 71 |   3516.34 |               49.53 |            8392.49 |                   6 |              11 |
| vol_off      | atrpct_ge_0p40 | after_bullish_flip |     5    |     15   |       71 |     28 |          39.44 |          0 |          0 |                 71 |   3516.34 |               49.53 |            8392.49 |                   6 |              11 |
| vol_ge_1p25  | atrpct_ge_0p20 | after_line_touch   |     3    |      9   |       88 |     25 |          28.41 |          0 |          1 |                 87 |   3515.95 |               39.95 |            7358.84 |                  10 |              12 |
| vol_ge_1p0   | atrpct_ge_0p20 | after_line_touch   |     1    |      2   |      108 |     31 |          28.7  |          6 |         21 |                 81 |   3336.91 |               30.9  |            6920.79 |                  11 |              11 |
| vol_ge_1p0   | atrpct_ge_0p20 | after_line_touch   |     0.5  |      1   |      108 |     41 |          37.96 |         34 |         40 |                 34 |   2993.54 |               27.72 |            6799.38 |                  12 |              10 |
| vol_ge_1p25  | atrpct_ge_0p20 | after_line_touch   |     4    |      8   |       88 |     25 |          28.41 |          0 |          1 |                 87 |   2839.23 |               32.26 |            7358.84 |                  10 |              12 |
| vol_off      | atrpct_ge_0p40 | after_bullish_flip |     3    |      4   |       71 |     28 |          39.44 |          1 |         10 |                 60 |   2745.61 |               38.67 |            8392.49 |                   8 |               9 |
| vol_ge_1p25  | atrpct_ge_0p20 | after_line_touch   |     3    |      4   |       88 |     25 |          28.41 |          0 |          6 |                 82 |   2584.98 |               29.37 |            6183.62 |                   9 |              13 |
| vol_ge_1p25  | atrpct_ge_0p20 | after_line_touch   |     5    |      5   |       88 |     25 |          28.41 |          0 |          4 |                 84 |   2563.81 |               29.13 |            8089.59 |                  10 |              12 |
| vol_ge_1p25  | atrpct_ge_0p20 | after_line_touch   |     1    |      8   |       88 |     24 |          27.27 |          6 |          1 |                 81 |   2547.23 |               28.95 |            7783.66 |                   9 |              13 |
| vol_ge_1p0   | atrpct_ge_0p10 | after_line_touch   |     0.75 |      1.5 |      157 |     46 |          29.3  |         17 |         36 |                104 |   2447    |               15.59 |            7339.07 |                  10 |              12 |
| vol_ge_1p25  | atrpct_ge_0p20 | after_line_touch   |     2    |      8   |       88 |     25 |          28.41 |          1 |          1 |                 86 |   2406.13 |               27.34 |            7791.94 |                  10 |              12 |
| vol_ge_1p25  | atrpct_ge_0p20 | after_line_touch   |     1    |      4   |       88 |     24 |          27.27 |          6 |          6 |                 76 |   2292.98 |               26.06 |            6978.49 |                   8 |              14 |

## Critical model limits
- 15m Supertrend closing stop can exit before SL or TP.
- 1m OHLC ordering ambiguous, SL wins same minute.
- User-requested percentage SL/TP is not the same as percentage
  profit protection; previous independent percent-lock study remains.
- BTC price-point PnL normalized to 1-BTC equivalent, not actual equity.
- No margin, liquidation, dynamic spread, funding or fills queue.
- Multiple-hypothesis retrospective selection; no blind forward test.
