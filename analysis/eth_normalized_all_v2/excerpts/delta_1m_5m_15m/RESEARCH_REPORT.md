# Delta Exchange India ETHUSD: 1m, 5m, 15m empirical institutional-style study

**Source**: public Delta India ETHUSD perpetual 1-minute OHLCV (NOT the original uploaded 5m source).
**Research horizon**: Jan 2025 - Oct 17 2026. Discovery: before 2026-07-01 UTC; holdout: July-Oct 17.
**Candle labeling**: API 1m time assumed bar start; converted UTC-start-aligned 5m/15m bars. Confirm with live chart before using clock rules.
**Institutional caution**: OHLCV does not identify institutional orders, stops, liquidations, order book or resting liquidity.
**Execution**: trade signal observed at close of 1/5/15-minute opening bar, enter next REAL 1m open, exit 30 minutes later.
Gross bp is direction-adjusted close-to-close-price return. Net 2bp is only an illustrative assumed round-trip fee/slippage, not validated executable P&L.

## Data quality

~~~json
{
  "source_months": 22,
  "source_candles": 963360,
  "missing_minutes": 0,
  "first_utc": "2025-01-01 00:00:00+00:00",
  "last_utc": "2026-10-31 23:59:00+00:00",
  "zero_volume": 1887,
  "bars_by_resolution": {
    "1": 963360,
    "5": 192672,
    "15": 64224
  },
  "train_last_utc": "2026-06-30",
  "holdout_start_utc": "2026-07-01"
}
~~~

## New York 09:30 opening event hypotheses

|   tf | setup                      | split     |   n |   win_pct |   net_win_pct |   mean_gross_bp |   median_gross_bp |   mean_net_bp |
|-----:|:---------------------------|:----------|----:|----------:|--------------:|----------------:|------------------:|--------------:|
|    1 | close_above_premarket_high | discovery |   3 |      0    |          0    |         -82.004 |           -73.266 |       -84.004 |
|    1 | close_below_premarket_low  | discovery |   4 |     50    |         50    |         -29.845 |             5.177 |       -31.845 |
|    1 | lower_sweep_close_inside   | discovery |   5 |     40    |         40    |         -18.385 |            -9.892 |       -20.385 |
|    1 | lower_sweep_close_inside   | holdout   |   1 |      0    |          0    |         -36.939 |           -36.939 |       -38.939 |
|    1 | opening_direction          | discovery | 390 |     52.05 |         50.51 |           3.889 |             3.456 |         1.889 |
|    1 | opening_direction          | holdout   |  88 |     62.5  |         59.09 |           6.352 |             6.865 |         4.352 |
|    1 | upper_sweep_close_inside   | discovery |   5 |     60    |         60    |          30.073 |            23.252 |        28.073 |
|    1 | upper_sweep_close_inside   | holdout   |   1 |    100    |        100    |           3.538 |             3.538 |         1.538 |
|    5 | close_above_premarket_high | discovery |  12 |     41.67 |         41.67 |         -29.7   |           -24.282 |       -31.7   |
|    5 | close_above_premarket_high | holdout   |   1 |    100    |        100    |          13.186 |            13.186 |        11.186 |
|    5 | close_below_premarket_low  | discovery |  17 |     47.06 |         47.06 |           3.321 |            -4.354 |         1.321 |
|    5 | close_below_premarket_low  | holdout   |   3 |      0    |          0    |         -39.257 |           -17.511 |       -41.257 |
|    5 | lower_sweep_close_inside   | discovery |  14 |     35.71 |         21.43 |         -44.089 |           -37.3   |       -46.089 |
|    5 | lower_sweep_close_inside   | holdout   |   3 |     66.67 |         66.67 |           9.295 |            11.768 |         7.295 |
|    5 | opening_direction          | discovery | 389 |     53.47 |         51.93 |           1.728 |             5.969 |        -0.272 |
|    5 | opening_direction          | holdout   |  87 |     39.08 |         37.93 |          -2.469 |           -15.952 |        -4.469 |
|    5 | second_opening_5m_confirms | discovery | 208 |     49.04 |         47.12 |          -3.439 |            -1.575 |        -5.439 |
|    5 | second_opening_5m_confirms | holdout   |  44 |     29.55 |         29.55 |         -14.119 |           -22.353 |       -16.119 |
|    5 | upper_sweep_close_inside   | discovery |  17 |     52.94 |         47.06 |          11.025 |             0.697 |         9.025 |
|    5 | upper_sweep_close_inside   | holdout   |   2 |     50    |         50    |           1.955 |             1.955 |        -0.045 |
|   15 | close_above_premarket_high | discovery |  21 |     47.62 |         42.86 |           3.759 |           -15.31  |         1.759 |
|   15 | close_above_premarket_high | holdout   |   7 |     57.14 |         57.14 |          46.899 |            20.75  |        44.899 |
|   15 | close_below_premarket_low  | discovery |  31 |     48.39 |         41.94 |           3.501 |            -0.11  |         1.501 |
|   15 | close_below_premarket_low  | holdout   |   7 |     28.57 |         28.57 |         -38.456 |           -30.771 |       -40.456 |
|   15 | lower_sweep_close_inside   | discovery |  43 |     34.88 |         34.88 |         -29.194 |           -21.558 |       -31.194 |
|   15 | lower_sweep_close_inside   | holdout   |   9 |     66.67 |         55.56 |          12.377 |            19.21  |        10.377 |
|   15 | opening_direction          | discovery | 390 |     51.28 |         48.46 |           6.09  |             0.795 |         4.09  |
|   15 | opening_direction          | holdout   |  88 |     43.18 |         43.18 |          -7.631 |           -10.003 |        -9.631 |
|   15 | upper_sweep_close_inside   | discovery |  34 |     52.94 |         50    |           9.43  |             6.111 |         7.43  |
|   15 | upper_sweep_close_inside   | holdout   |   2 |    100    |        100    |          44.609 |            44.609 |        42.609 |

## Clock-time volatility and red/green tendencies
See session_clock_events.csv, all_weekday_time_slots.csv. Range multiplier uses preceding 2h of completed same-timeframe bars.
New York clock time uses daylight saving; values refer to assumed candle OPEN times, unlike prior reports which sometimes used close-time labels.
Clock-time scan includes thousands of candidate cells: apparent extreme red/green rates are subject to severe multiple-testing bias.

## Automatically mined 2-3 candle-shape sequences
Patterns encode relative range, body, upper/lower wick and color; selected solely by DISCOVERY training, then evaluated on HOLDOUT.
Correlated/overlapping samples; no independent-trade inference. See new_candle_sequences.csv.

|   tf |   sequence_bars | pattern                         |   train_n | direction   |   train_win_pct |   train_mean_bp |   holdout_n |   holdout_win_pct |   holdout_mean_bp |
|-----:|----------------:|:--------------------------------|----------:|:------------|----------------:|----------------:|------------:|------------------:|------------------:|
|   15 |               2 | lower_wick|impulse_red          |       114 | LONG        |           64.91 |           15.19 |          26 |             73.08 |             17.78 |
|    5 |               3 | lower_wick|green|impulse_green  |       102 | SHORT       |           66.67 |           12.28 |          28 |             71.43 |             16.27 |
|   15 |               2 | lower_wick|lower_wick           |       215 | LONG        |           58.6  |            6.63 |          62 |             54.84 |             12.74 |
|   15 |               3 | red|compression|lower_wick      |        97 | LONG        |           59.79 |            7.68 |          22 |             72.73 |             11.8  |
|   15 |               3 | red|lower_wick|lower_wick       |        86 | LONG        |           63.95 |           11.4  |          27 |             51.85 |              9.05 |
|    5 |               3 | impulse_green|impulse_red|green |        98 | SHORT       |           58.16 |            8.57 |          45 |             51.11 |              7.15 |
|    5 |               3 | upper_wick|upper_wick|green     |       153 | SHORT       |           58.17 |            9.77 |          44 |             59.09 |              5.77 |
|    5 |               3 | green|green|impulse_green       |       533 | SHORT       |           58.16 |            4.53 |         123 |             62.6  |              5.33 |
|    5 |               3 | green|impulse_green|lower_wick  |       120 | SHORT       |           60.83 |           13.31 |          33 |             60.61 |              5.33 |
|    5 |               3 | upper_wick|green|impulse_green  |       115 | SHORT       |           66.96 |           11.09 |          24 |             54.17 |              4.42 |
|    5 |               3 | lower_wick|impulse_red|red      |        98 | LONG        |           58.16 |           12.39 |          16 |             56.25 |              4.02 |
|    5 |               2 | green|impulse_green             |      1606 | SHORT       |           58.53 |            3.65 |         396 |             58.84 |              2.16 |

## Interpretation and next controls
A recurring volatility window is not a known BUY/SHORT edge. Bid/ask, funding, market order slippage, size constraints and stops remain unmodeled.
Do not deploy without a further untouched period, realistic bid/ask replay and date-blocked tests.
