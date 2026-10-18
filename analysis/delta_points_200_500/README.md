# Can BTCUSD futures deliver 200–500 points every day?

**Answer: no guaranteed daily capture.** This study distinguishes daily price RANGE from realizable trade P&L.
**BTC points are USD price units per BTC, not INR or USD account profit.**

## Dataset and validation
{
  "rows": 943200,
  "first": "2025-01-01 00:00:00+00:00",
  "last": "2026-10-17 23:59:00+00:00",
  "zero_volume": 1819
}

Discovery before 2026-07-01 UTC; holdout July 1–October 17, 2026.
One trade per NY calendar day per signal type, 120-minute maximum hold. For every trade, entry is at next real 1m open *after a fully completed trigger candle*.
If stop and target both touch in a 1m candle, STOP counts first (pessimistic). No fabricated price paths.
Fee assumption: futures MARKET taker 0.05% on entry and 0.05% on exit plus 18% GST on these fees; simulated slippage 5 BTC points per side. Maker/discount tiers and funding NOT modeled.
No guarantee next-minute open is executable at OHLCV price; backtest approximation only.

## Historical opportunity (high-low only, NOT a trade signal)

| period          | split     | weekday   |   days |   median_range_points |   days_range_ge200_pct |   days_range_ge500_pct |
|:----------------|:----------|:----------|-------:|----------------------:|-----------------------:|-----------------------:|
| NY_0930_to_1130 | discovery | True      |    390 |                1519   |                    100 |                  98.97 |
| NY_0930_to_1130 | holdout   | True      |     78 |                 979.5 |                    100 |                  97.44 |
| full_NY_day     | discovery | False     |    156 |                2046.2 |                    100 |                  98.72 |
| full_NY_day     | discovery | True      |    391 |                2888.5 |                    100 |                 100    |
| full_NY_day     | holdout   | False     |     31 |                1054   |                    100 |                  90.32 |
| full_NY_day     | holdout   | True      |     78 |                1850.2 |                    100 |                 100    |

A day's high minus low can be hundreds/thousands of points without providing a profitable known-entry trade.

## Holdout results, target/stop matrix

| strategy                         | split   |   target_points |   stop_points |   trades |   days_traded |   target_hit_pct |   profitable_after_fees_pct |   avg_gross_points |   avg_net_points |   median_net_points |   total_net_points |   max_drawdown_points |   max_loss_streak |
|:---------------------------------|:--------|----------------:|--------------:|---------:|--------------:|-----------------:|----------------------------:|-------------------:|-----------------:|--------------------:|-------------------:|----------------------:|------------------:|
| 15m_red_impulsegreen_green_short | holdout |             200 |           150 |       60 |            60 |            38.33 |                       40    |               6.57 |           -90.85 |             -164.23 |           -5450.77 |                5637.1 |                 7 |
| 15m_red_impulsegreen_green_short | holdout |             200 |           250 |       60 |            60 |            48.33 |                       50    |              16.44 |           -80.97 |               -5.74 |           -4857.92 |                5044.3 |                 6 |
| 15m_red_impulsegreen_green_short | holdout |             300 |           150 |       60 |            60 |            25    |                       30    |               3.68 |           -93.73 |             -235.38 |           -5623.87 |                6372.3 |                 7 |
| 15m_red_impulsegreen_green_short | holdout |             300 |           250 |       60 |            60 |            30    |                       35    |              -8.53 |          -105.96 |             -101.63 |           -6357.3  |                6954.6 |                 7 |
| 15m_red_impulsegreen_green_short | holdout |             500 |           150 |       60 |            60 |            16.67 |                       26.67 |              22.93 |           -74.47 |             -236.11 |           -4468.19 |                6214.2 |                 8 |
| 15m_red_impulsegreen_green_short | holdout |             500 |           250 |       60 |            60 |            18.33 |                       31.67 |              12.98 |           -84.43 |             -158.3  |           -5065.54 |                6660.4 |                 7 |
| NY_0930_big_5m_follow            | holdout |             200 |           150 |       39 |            39 |            38.46 |                       38.46 |             -15.38 |          -111.73 |             -235.36 |           -4357.54 |                4357.5 |                 8 |
| NY_0930_big_5m_follow            | holdout |             200 |           250 |       39 |            39 |            56.41 |                       56.41 |               3.85 |           -92.5  |               91.14 |           -3607.34 |                3724.1 |                 3 |
| NY_0930_big_5m_follow            | holdout |             300 |           150 |       39 |            39 |            25.64 |                       25.64 |             -34.62 |          -130.95 |             -236.38 |           -5106.92 |                5106.9 |                 8 |
| NY_0930_big_5m_follow            | holdout |             300 |           250 |       39 |            39 |            33.33 |                       33.33 |             -62.4  |          -158.72 |             -335.56 |           -6190.2  |                6190.2 |                 7 |
| NY_0930_big_5m_follow            | holdout |             500 |           150 |       39 |            39 |            10.26 |                       12.82 |             -71.86 |          -168.2  |             -237.52 |           -6559.69 |                6559.7 |                10 |
| NY_0930_big_5m_follow            | holdout |             500 |           250 |       39 |            39 |            12.82 |                       20.51 |            -101.69 |          -198.03 |             -336.74 |           -7723.23 |                7723.2 |                 8 |
| NY_0930_first_1m_direction       | holdout |             200 |           150 |       78 |            78 |            44.87 |                       44.87 |               7.05 |           -88.92 |             -233.15 |           -6936.07 |                7029.5 |                 7 |
| NY_0930_first_1m_direction       | holdout |             200 |           250 |       78 |            78 |            51.28 |                       51.28 |             -19.23 |          -115.2  |               88.18 |           -8985.39 |                9078.8 |                 7 |
| NY_0930_first_1m_direction       | holdout |             300 |           150 |       78 |            78 |            35.9  |                       35.9  |              12.67 |           -83.32 |             -234.53 |           -6498.99 |                6499   |                10 |
| NY_0930_first_1m_direction       | holdout |             300 |           250 |       78 |            78 |            41.03 |                       42.31 |             -17.03 |          -113    |             -333.88 |           -8814.32 |                8814.3 |                10 |
| NY_0930_first_1m_direction       | holdout |             500 |           150 |       78 |            78 |            28.21 |                       28.21 |              36.62 |           -59.36 |             -235.67 |           -4630.27 |                4630.3 |                11 |
| NY_0930_first_1m_direction       | holdout |             500 |           250 |       78 |            78 |            30.77 |                       33.33 |              -3.5  |           -99.47 |             -334.8  |           -7758.34 |                7758.3 |                11 |
| NY_0930_large_15m_fade           | holdout |             200 |           150 |       22 |            22 |            45.45 |                       45.45 |               9.09 |           -87.96 |             -234.5  |           -1935.13 |                2390.8 |                 6 |
| NY_0930_large_15m_fade           | holdout |             200 |           250 |       22 |            22 |            59.09 |                       59.09 |              15.91 |           -81.13 |               90    |           -1784.86 |                2240.5 |                 4 |
| NY_0930_large_15m_fade           | holdout |             300 |           150 |       22 |            22 |            36.36 |                       36.36 |              13.64 |           -83.4  |             -235.7  |           -1834.89 |                2790.7 |                 7 |
| NY_0930_large_15m_fade           | holdout |             300 |           250 |       22 |            22 |            45.45 |                       45.45 |              15.23 |           -81.8  |             -167.19 |           -1799.69 |                2755.5 |                 4 |
| NY_0930_large_15m_fade           | holdout |             500 |           150 |       22 |            22 |            27.27 |                       27.27 |              27.27 |           -69.78 |             -236.16 |           -1535.19 |                2677.5 |                 7 |
| NY_0930_large_15m_fade           | holdout |             500 |           250 |       22 |            22 |            36.36 |                       36.36 |              37.95 |           -59.1  |             -335.4  |           -1300.11 |                2322.4 |                 4 |
| US_trend_5m_12bar_break          | holdout |             200 |           150 |       75 |            75 |            40    |                       40    |              -8.83 |          -104.82 |             -234.44 |           -7861.43 |                7981.7 |                 5 |
| US_trend_5m_12bar_break          | holdout |             200 |           250 |       75 |            75 |            56    |                       56    |              12.01 |           -83.97 |               91.72 |           -6297.49 |                6417.8 |                 4 |
| US_trend_5m_12bar_break          | holdout |             300 |           150 |       75 |            75 |            37.33 |                       37.33 |              19.17 |           -76.81 |             -235.18 |           -5761.07 |                5981.3 |                 7 |
| US_trend_5m_12bar_break          | holdout |             300 |           250 |       75 |            75 |            46.67 |                       46.67 |              21.81 |           -74.16 |             -149.11 |           -5562.24 |                5782.4 |                 5 |
| US_trend_5m_12bar_break          | holdout |             500 |           150 |       75 |            75 |            24    |                       28    |              24.68 |           -71.32 |             -236.23 |           -5348.92 |                5769   |                 7 |
| US_trend_5m_12bar_break          | holdout |             500 |           250 |       75 |            75 |            29.33 |                       38.67 |              32.32 |           -63.67 |             -333.17 |           -4775.6  |                5258.6 |                 6 |

## Best numerical holdout row (NOT automatically a validated edge)

NY_0930_large_15m_fade TP500/SL250, n=22, target-hit=36.36%, net-profitable=36.36%, average net=-59.1 BTC points per trade.
This top row is **selected from the holdout** for descriptive reporting, not valid as future predictive evidence.

## Conclusions
- No setup here proves a daily consistent 200–500 point take-profit.
- Treat unexplained zero-volume candles and contract/symbol behavior as data-quality caveats.
- No simulated position sizing/leverage; 0.001 BTC exposure maps one BTC price point to approximately $0.001 P&L before fees.
- Before live execution: obtain actual bid/ask, funding, latency and incremental order book data, and run another untouched date-block validation.
