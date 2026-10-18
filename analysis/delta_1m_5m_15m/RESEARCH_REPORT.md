# Delta Exchange India BTCUSD: 1m, 5m, 15m empirical institutional-style study

**Source**: public Delta India BTCUSD perpetual 1-minute OHLCV (NOT the original uploaded 5m source).
**Research horizon**: Jan 2025 - Oct 17 2026. Discovery: before 2026-07-01 UTC; holdout: July-Oct 17.
**Candle labeling**: API 1m time assumed bar start; converted UTC-start-aligned 5m/15m bars. Confirm with live chart before using clock rules.
**Institutional caution**: OHLCV does not identify institutional orders, stops, liquidations, order book or resting liquidity.
**Execution**: trade signal observed at close of 1/5/15-minute opening bar, enter next REAL 1m open, exit 30 minutes later.
Gross bp is direction-adjusted close-to-close-price return. Net 2bp is only an illustrative assumed round-trip fee/slippage, not validated executable P&L.

## Data quality

~~~json
{
  "source_months": 22,
  "source_candles": 943200,
  "missing_minutes": 0,
  "first_utc": "2025-01-01 00:00:00+00:00",
  "last_utc": "2026-10-17 23:59:00+00:00",
  "zero_volume": 1819,
  "bars_by_resolution": {
    "1": 943200,
    "5": 188640,
    "15": 62880
  },
  "train_last_utc": "2026-06-30",
  "holdout_start_utc": "2026-07-01"
}
~~~

## New York 09:30 opening event hypotheses

|   tf | setup                      | split     |   n |   win_pct |   net_win_pct |   mean_gross_bp |   median_gross_bp |   mean_net_bp |
|-----:|:---------------------------|:----------|----:|----------:|--------------:|----------------:|------------------:|--------------:|
|    1 | close_above_premarket_high | discovery |   5 |      0    |          0    |         -50.117 |           -57.113 |       -52.117 |
|    1 | close_above_premarket_high | holdout   |   1 |      0    |          0    |          -6.148 |            -6.148 |        -8.148 |
|    1 | close_below_premarket_low  | discovery |   6 |     33.33 |         33.33 |          -7.224 |           -42.914 |        -9.224 |
|    1 | close_below_premarket_low  | holdout   |   2 |    100    |        100    |          14.211 |            14.211 |        12.211 |
|    1 | lower_sweep_close_inside   | discovery |   4 |     75    |         75    |          14.13  |            18.272 |        12.13  |
|    1 | lower_sweep_close_inside   | holdout   |   2 |    100    |        100    |          23.539 |            23.539 |        21.539 |
|    1 | opening_direction          | discovery | 389 |     48.59 |         47.04 |           1.319 |            -2.778 |        -0.681 |
|    1 | opening_direction          | holdout   |  78 |     53.85 |         51.28 |           3.057 |             4.936 |         1.057 |
|    1 | upper_sweep_close_inside   | discovery |   6 |     83.33 |         83.33 |          45.899 |            34.397 |        43.899 |
|    1 | upper_sweep_close_inside   | holdout   |   1 |      0    |          0    |          -0.479 |            -0.479 |        -2.479 |
|    5 | close_above_premarket_high | discovery |  13 |     38.46 |         38.46 |         -18.634 |           -39.338 |       -20.634 |
|    5 | close_above_premarket_high | holdout   |   1 |    100    |        100    |          13.07  |            13.07  |        11.07  |
|    5 | close_below_premarket_low  | discovery |  19 |     52.63 |         52.63 |           6.431 |            13.251 |         4.431 |
|    5 | close_below_premarket_low  | holdout   |   4 |     50    |         50    |          -3.126 |             3.989 |        -5.126 |
|    5 | lower_sweep_close_inside   | discovery |  21 |     57.14 |         57.14 |          34.103 |            32.068 |        32.103 |
|    5 | lower_sweep_close_inside   | holdout   |   7 |     71.43 |         71.43 |           6.433 |            25.002 |         4.433 |
|    5 | opening_direction          | discovery | 390 |     54.1  |         52.82 |           4.17  |             6.3   |         2.17  |
|    5 | opening_direction          | holdout   |  78 |     47.44 |         44.87 |          -0.045 |            -6.688 |        -2.045 |
|    5 | second_opening_5m_confirms | discovery | 204 |     53.92 |         52.45 |           2.088 |             4.628 |         0.088 |
|    5 | second_opening_5m_confirms | holdout   |  39 |     41.03 |         35.9  |          -4.393 |            -9.594 |        -6.393 |
|    5 | upper_sweep_close_inside   | discovery |  17 |     41.18 |         41.18 |         -23.596 |           -30.423 |       -25.596 |
|    5 | upper_sweep_close_inside   | holdout   |   2 |    100    |        100    |          17.691 |            17.691 |        15.691 |
|   15 | close_above_premarket_high | discovery |  32 |     37.5  |         34.38 |          -4.351 |           -10.212 |        -6.351 |
|   15 | close_above_premarket_high | holdout   |   4 |     75    |         75    |          37.456 |            32.419 |        35.456 |
|   15 | close_below_premarket_low  | discovery |  42 |     35.71 |         35.71 |          -4.248 |           -12.527 |        -6.248 |
|   15 | close_below_premarket_low  | holdout   |   9 |     22.22 |         22.22 |         -24.605 |           -15.938 |       -26.605 |
|   15 | lower_sweep_close_inside   | discovery |  46 |     36.96 |         36.96 |         -11.324 |           -13.905 |       -13.324 |
|   15 | lower_sweep_close_inside   | holdout   |   9 |     88.89 |         88.89 |          20.283 |            29.168 |        18.283 |
|   15 | opening_direction          | discovery | 390 |     50    |         47.44 |          -0.371 |            -0.107 |        -2.371 |
|   15 | opening_direction          | holdout   |  78 |     44.87 |         42.31 |          -6.036 |            -6.269 |        -8.036 |
|   15 | upper_sweep_close_inside   | discovery |  40 |     47.5  |         47.5  |         -12.077 |            -3.287 |       -14.077 |
|   15 | upper_sweep_close_inside   | holdout   |   4 |     50    |         50    |          11.038 |            -0.309 |         9.038 |

## Clock-time volatility and red/green tendencies
See session_clock_events.csv, all_weekday_time_slots.csv. Range multiplier uses preceding 2h of completed same-timeframe bars.
New York clock time uses daylight saving; values refer to assumed candle OPEN times, unlike prior reports which sometimes used close-time labels.
Clock-time scan includes thousands of candidate cells: apparent extreme red/green rates are subject to severe multiple-testing bias.

## Automatically mined 2-3 candle-shape sequences
Patterns encode relative range, body, upper/lower wick and color; selected solely by DISCOVERY training, then evaluated on HOLDOUT.
Correlated/overlapping samples; no independent-trade inference. See new_candle_sequences.csv.

|   tf |   sequence_bars | pattern                             |   train_n | direction   |   train_win_pct |   train_mean_bp |   holdout_n |   holdout_win_pct |   holdout_mean_bp |
|-----:|----------------:|:------------------------------------|----------:|:------------|----------------:|----------------:|------------:|------------------:|------------------:|
|   15 |               3 | red|impulse_green|green             |       131 | SHORT       |           59.54 |            3.97 |          26 |             76.92 |              7.89 |
|   15 |               3 | green|impulse_red|red               |       120 | LONG        |           59.17 |            6.38 |          29 |             55.17 |              4.97 |
|   15 |               2 | impulse_red|red                     |       395 | LONG        |           59.75 |            5.97 |          89 |             57.3  |              4.23 |
|    5 |               3 | red|impulse_red|impulse_red         |       143 | LONG        |           58.04 |            3.55 |          25 |             44    |              3.52 |
|    5 |               3 | compression|compression|impulse_red |       170 | LONG        |           58.82 |            3.47 |          50 |             54    |              2.82 |
|    5 |               3 | red|impulse_green|impulse_green     |       100 | SHORT       |           60    |            3.93 |          26 |             53.85 |              2.28 |
|    1 |               3 | impulse_green|lower_wick|upper_wick |       309 | SHORT       |           58.25 |            5.03 |          85 |             52.94 |              1.98 |
|    5 |               3 | red|red|impulse_red                 |       557 | LONG        |           58.71 |            5.2  |         111 |             57.66 |              1.93 |
|    5 |               3 | upper_wick|impulse_green|green      |        90 | SHORT       |           60    |            8.03 |          24 |             58.33 |              1.68 |
|   15 |               3 | red|impulse_red|red                 |       123 | LONG        |           60.98 |            4.54 |          20 |             50    |              1.24 |
|    5 |               3 | impulse_red|impulse_green|green     |       120 | LONG        |           58.33 |            4.03 |          20 |             50    |              0.58 |
|    5 |               3 | lower_wick|red|impulse_red          |       129 | LONG        |           58.91 |            5.41 |          28 |             50    |              0.51 |

## Interpretation and next controls
A recurring volatility window is not a known BUY/SHORT edge. Bid/ask, funding, market order slippage, size constraints and stops remain unmodeled.
Do not deploy without a further untouched period, realistic bid/ask replay and date-blocked tests.
