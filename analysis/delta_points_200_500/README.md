# Can BTCUSD futures deliver 200–500 points every day?

**Answer: no guaranteed daily capture.** This study distinguishes daily price RANGE from realizable trade P&L.
**BTC points are USD price units per BTC, not INR or USD account profit.**

## Dataset and validation
{
  "rows": 997920,
  "first": "2025-01-01 00:00:00+00:00",
  "last": "2026-11-24 23:59:00+00:00",
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
| NY_0930_to_1130 | holdout   | True      |    105 |                1052.5 |                    100 |                  98.1  |
| full_NY_day     | discovery | False     |    156 |                2046.2 |                    100 |                  98.72 |
| full_NY_day     | discovery | True      |    391 |                2888.5 |                    100 |                 100    |
| full_NY_day     | holdout   | False     |     42 |                1293.8 |                    100 |                  92.86 |
| full_NY_day     | holdout   | True      |    105 |                2047   |                    100 |                 100    |

A day's high minus low can be hundreds/thousands of points without providing a profitable known-entry trade.

## Holdout results, target/stop matrix

| strategy                         | split   |   target_points |   stop_points |   trades |   days_traded |   target_hit_pct |   profitable_after_fees_pct |   avg_gross_points |   avg_net_points |   median_net_points |   total_net_points |   max_drawdown_points |   max_loss_streak |
|:---------------------------------|:--------|----------------:|--------------:|---------:|--------------:|-----------------:|----------------------------:|-------------------:|-----------------:|--------------------:|-------------------:|----------------------:|------------------:|
| 15m_red_impulsegreen_green_short | holdout |             200 |           150 |       74 |            74 |            35.14 |                       36.49 |              -6.93 |          -104.14 |             -234.05 |           -7706.03 |                7706   |                 7 |
| 15m_red_impulsegreen_green_short | holdout |             200 |           250 |       74 |            74 |            45.95 |                       47.3  |               3.47 |           -93.72 |              -41.19 |           -6935.58 |                7054.4 |                 6 |
| 15m_red_impulsegreen_green_short | holdout |             300 |           150 |       74 |            74 |            21.62 |                       27.03 |             -13.73 |          -110.94 |             -235.56 |           -8209.33 |                8571.2 |                 7 |
| 15m_red_impulsegreen_green_short | holdout |             300 |           250 |       74 |            74 |            28.38 |                       33.78 |             -19.89 |          -117.1  |             -119.48 |           -8665.09 |                9094.8 |                 7 |
| 15m_red_impulsegreen_green_short | holdout |             500 |           150 |       74 |            74 |            14.86 |                       24.32 |               4.58 |           -92.62 |             -236.5  |           -6853.53 |                8047.9 |                 8 |
| 15m_red_impulsegreen_green_short | holdout |             500 |           250 |       74 |            74 |            17.57 |                       31.08 |               0.87 |           -96.33 |             -206.27 |           -7128.19 |                8590.5 |                 7 |
| NY_0930_big_5m_follow            | holdout |             200 |           150 |       51 |            51 |            41.18 |                       41.18 |              -5.88 |          -102.44 |             -234.06 |           -5224.19 |                5534.4 |                 8 |
| NY_0930_big_5m_follow            | holdout |             200 |           250 |       51 |            51 |            58.82 |                       58.82 |              14.71 |           -81.84 |               92.54 |           -4173.98 |                5049.8 |                 3 |
| NY_0930_big_5m_follow            | holdout |             300 |           150 |       51 |            51 |            27.45 |                       27.45 |             -26.47 |          -123.02 |             -236.38 |           -6274.1  |                6634   |                11 |
| NY_0930_big_5m_follow            | holdout |             300 |           250 |       51 |            51 |            39.22 |                       39.22 |             -31.05 |          -127.59 |             -335.42 |           -6507.16 |                7966.1 |                10 |
| NY_0930_big_5m_follow            | holdout |             500 |           150 |       51 |            51 |            15.69 |                       17.65 |             -39.26 |          -135.83 |             -237.52 |           -6927.1  |                8086.8 |                16 |
| NY_0930_big_5m_follow            | holdout |             500 |           250 |       51 |            51 |            21.57 |                       27.45 |             -41.58 |          -138.13 |             -336.52 |           -7044.58 |                9505   |                11 |
| NY_0930_first_1m_direction       | holdout |             200 |           150 |      105 |           105 |            46.67 |                       46.67 |              13.33 |           -83.06 |             -232.82 |           -8721.17 |                8836.1 |                 7 |
| NY_0930_first_1m_direction       | holdout |             200 |           250 |      105 |           105 |            52.38 |                       52.38 |             -14.29 |          -110.67 |               88.96 |          -11620.6  |               11635.6 |                 7 |
| NY_0930_first_1m_direction       | holdout |             300 |           150 |      105 |           105 |            37.14 |                       37.14 |              17.98 |           -78.42 |             -234.98 |           -8233.82 |                8649   |                11 |
| NY_0930_first_1m_direction       | holdout |             300 |           250 |      105 |           105 |            41.9  |                       42.86 |             -14.08 |          -110.47 |             -334.05 |          -11599.2  |               11914.4 |                11 |
| NY_0930_first_1m_direction       | holdout |             500 |           150 |      105 |           105 |            28.57 |                       28.57 |              38.15 |           -58.24 |             -235.8  |           -6115.36 |                7308.5 |                12 |
| NY_0930_first_1m_direction       | holdout |             500 |           250 |      105 |           105 |            31.43 |                       33.33 |              -2.6  |           -98.99 |             -335.57 |          -10393.7  |               11386.9 |                12 |
| NY_0930_large_15m_fade           | holdout |             200 |           150 |       31 |            31 |            51.61 |                       51.61 |              30.65 |           -65.77 |               88.24 |           -2038.96 |                2390.8 |                 6 |
| NY_0930_large_15m_fade           | holdout |             200 |           250 |       31 |            31 |            64.52 |                       64.52 |              40.32 |           -56.09 |               93.39 |           -1738.79 |                2240.5 |                 4 |
| NY_0930_large_15m_fade           | holdout |             300 |           150 |       31 |            31 |            45.16 |                       45.16 |              53.23 |           -43.18 |             -234.58 |           -1338.61 |                2790.7 |                 7 |
| NY_0930_large_15m_fade           | holdout |             300 |           250 |       31 |            31 |            54.84 |                       54.84 |              62.42 |           -33.99 |              188.95 |           -1053.56 |                2755.5 |                 4 |
| NY_0930_large_15m_fade           | holdout |             500 |           150 |       31 |            31 |            29.03 |                       29.03 |              38.71 |           -57.71 |             -236.04 |           -1789.05 |                2677.5 |                 7 |
| NY_0930_large_15m_fade           | holdout |             500 |           250 |       31 |            31 |            38.71 |                       38.71 |              51.13 |           -45.3  |             -334.55 |           -1404.3  |                2322.4 |                 4 |
| US_trend_5m_12bar_break          | holdout |             200 |           150 |      102 |           102 |            39.22 |                       39.22 |             -11.89 |          -108.23 |             -234.95 |          -11039.7  |               11160   |                 8 |
| US_trend_5m_12bar_break          | holdout |             200 |           250 |      102 |           102 |            56.86 |                       56.86 |              13.25 |           -83.1  |               91.99 |           -8475.93 |                8596.2 |                 4 |
| US_trend_5m_12bar_break          | holdout |             300 |           150 |      102 |           102 |            34.31 |                       34.31 |               5.27 |           -91.07 |             -235.8  |           -9289.37 |                9509.6 |                13 |
| US_trend_5m_12bar_break          | holdout |             300 |           250 |      102 |           102 |            47.06 |                       47.06 |              23.12 |           -73.22 |             -112.97 |           -7468.46 |                7688.7 |                 7 |
| US_trend_5m_12bar_break          | holdout |             500 |           150 |      102 |           102 |            22.55 |                       25.49 |              10.3  |           -86.06 |             -236.58 |           -8777.63 |                9509.5 |                18 |
| US_trend_5m_12bar_break          | holdout |             500 |           250 |      102 |           102 |            29.41 |                       37.25 |              23.52 |           -72.84 |             -333.89 |           -7430.06 |                8575.2 |                 7 |

## Best numerical holdout row (NOT automatically a validated edge)

NY_0930_large_15m_fade TP300/SL250, n=31, target-hit=54.84%, net-profitable=54.84%, average net=-33.99 BTC points per trade.
This top row is **selected from the holdout** for descriptive reporting, not valid as future predictive evidence.

## Conclusions
- No setup here proves a daily consistent 200–500 point take-profit.
- Treat unexplained zero-volume candles and contract/symbol behavior as data-quality caveats.
- No simulated position sizing/leverage; 0.001 BTC exposure maps one BTC price point to approximately $0.001 P&L before fees.
- Before live execution: obtain actual bid/ask, funding, latency and incremental order book data, and run another untouched date-block validation.
