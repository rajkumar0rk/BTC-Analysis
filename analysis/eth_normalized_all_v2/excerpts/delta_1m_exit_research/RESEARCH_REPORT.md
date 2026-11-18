# Delta ETHUSD 1m: exit policy comparison

This is a real-1m OHLCV, execution-aware research **simulation**, not a guarantee of daily 200–500 points.
Source: actual Delta Exchange India ETHUSD 1m perpetual future; 5 one-minute entry types; 10 exit methods. Every exit on an entry uses the exact same entry timestamp.
Holdout: July 1 through October 17 2026; train before this date. Only first eligible entry per NY weekday per strategy (no trades required every day).
Entry price: next 1m open plus adverse $5 price points. Exit: stop/target touch or timed close, minus adverse $5 points.
Both stop and target in same 1m bar = stop (pessimistic). Trailing/BE decisions update only for next 1m bar.
Futures fee assumed 0.05% taker per side, plus GST 18% on fees, deducted from modeled fills. No bid/ask, funding, market impact, or guaranteed fills.
Price points are per 1 BTC exposure; multiply by contract exposure (e.g. 0.001 BTC) for approximate dollar P&L.

## Data quality
~~~json
{
  "months": 22,
  "bars": 963360,
  "start": "2025-01-01 00:00:00+00:00",
  "end": "2026-10-31 23:59:00+00:00",
  "zero_volume": 1887,
  "entry_events": 2287,
  "exit_simulations": 22870,
  "holdout_start": "2026-07-01",
  "taker_fee": 0.0005,
  "gst_on_fee": 0.18,
  "slippage_points_per_side": 5.0
}
~~~

## Discovery-selected exits, evaluated on holdout
| strategy            | exit                 |   n_discovery |   avg_net_discovery |   win_pct_discovery |   n_holdout |   avg_net_holdout |   win_pct_holdout |   net200_pct_holdout |   max_dd_holdout |
|:--------------------|:---------------------|--------------:|--------------------:|--------------------:|------------:|------------------:|------------------:|---------------------:|-----------------:|
| 1m_3bar_exhaustion  | time15_sl250         |           380 |              -61.16 |               36.05 |          85 |            -92.2  |             37.65 |                 8.24 |           7847.6 |
| 1m_3bar_exhaustion  | time30_sl250         |           380 |              -63.86 |               32.89 |          85 |            -73.95 |             35.29 |                20    |           6810.4 |
| NY_open_1m          | time30_sl250         |           390 |              -70.77 |               29.49 |          88 |           -112.48 |             34.09 |                11.36 |           9898.5 |
| 1m_60m_sweep_reject | time15_sl250         |           330 |              -81.37 |               34.55 |          75 |           -140.89 |             28    |                 8    |          10566.5 |
| NY_open_1m          | time60_sl250         |           390 |              -81.54 |               22.31 |          88 |           -123.72 |             22.73 |                14.77 |          11155.1 |
| 1m_30m_range_break  | tp500_sl250_trail150 |           386 |              -83.54 |               43.01 |          86 |           -121.48 |             36.05 |                 9.3  |          10798.6 |
| 1m_30m_range_break  | time30_sl250         |           386 |              -86.51 |               25.91 |          86 |            -86.85 |             25.58 |                13.95 |           9752.5 |
| 1m_60m_sweep_reject | tp500_sl250_be200    |           330 |              -87.54 |               25.45 |          75 |           -122.56 |             21.33 |                17.33 |           9414.7 |
| 1m_trend_impulse    | tp500_sl250_trail150 |           383 |              -99.64 |               41.78 |          84 |           -112.74 |             38.1  |                10.71 |           9805.2 |
| 1m_trend_impulse    | tp500_sl250_be200    |           383 |             -100.71 |               23.24 |          84 |            -94.55 |             25    |                22.62 |           8822.8 |

## Every exit in holdout
| strategy            | exit                 |   n |   win_pct |   avg_net |   net200_pct |   net500_pct |   max_dd |
|:--------------------|:---------------------|----:|----------:|----------:|-------------:|-------------:|---------:|
| 1m_30m_range_break  | atr4_2R              |  86 |     26.74 |   -123.69 |        24.42 |         9.3  |  11972.6 |
| 1m_30m_range_break  | ema20_exit_sl250     |  86 |     19.77 |    -68.58 |        11.63 |         6.98 |   7944.4 |
| 1m_30m_range_break  | time15_sl250         |  86 |     20.93 |    -84.9  |        10.47 |         4.65 |   8722.7 |
| 1m_30m_range_break  | time30_sl250         |  86 |     25.58 |    -86.85 |        13.95 |         8.14 |   9752.5 |
| 1m_30m_range_break  | time60_sl250         |  86 |     24.42 |    -84.53 |        18.6  |        10.47 |   9778.7 |
| 1m_30m_range_break  | tp200_sl150          |  86 |     36.05 |   -102.57 |         0    |         0    |   8963.4 |
| 1m_30m_range_break  | tp300_sl200          |  86 |     27.91 |   -136.73 |        27.91 |         0    |  12239.7 |
| 1m_30m_range_break  | tp500_sl250          |  86 |     29.07 |   -110.93 |        27.91 |         0    |  10510   |
| 1m_30m_range_break  | tp500_sl250_be200    |  86 |     22.09 |    -97.97 |        22.09 |         0    |   9574.5 |
| 1m_30m_range_break  | tp500_sl250_trail150 |  86 |     36.05 |   -121.48 |         9.3  |         0    |  10798.6 |
| 1m_3bar_exhaustion  | atr4_2R              |  85 |     40    |    -32.58 |        34.12 |         9.41 |   5770   |
| 1m_3bar_exhaustion  | ema20_exit_sl250     |  85 |     22.35 |   -101.5  |         1.18 |         1.18 |   8627.7 |
| 1m_3bar_exhaustion  | time15_sl250         |  85 |     37.65 |    -92.2  |         8.24 |         1.18 |   7847.6 |
| 1m_3bar_exhaustion  | time30_sl250         |  85 |     35.29 |    -73.95 |        20    |         7.06 |   6810.4 |
| 1m_3bar_exhaustion  | time60_sl250         |  85 |     40    |    -17.61 |        21.18 |        11.76 |   7414.2 |
| 1m_3bar_exhaustion  | tp200_sl150          |  85 |     36.47 |   -101.54 |         0    |         0    |   8630.7 |
| 1m_3bar_exhaustion  | tp300_sl200          |  85 |     38.82 |    -82.73 |        37.65 |         0    |   7868.6 |
| 1m_3bar_exhaustion  | tp500_sl250          |  85 |     41.18 |    -27.16 |        36.47 |         0    |   5910.5 |
| 1m_3bar_exhaustion  | tp500_sl250_be200    |  85 |     22.35 |    -84.96 |        21.18 |         0    |   7311.6 |
| 1m_3bar_exhaustion  | tp500_sl250_trail150 |  85 |     44.71 |    -89.59 |        10.59 |         0    |   7648.7 |
| 1m_60m_sweep_reject | atr4_2R              |  75 |     32    |   -134.41 |        22.67 |         8    |  10867.3 |
| 1m_60m_sweep_reject | ema20_exit_sl250     |  75 |     18.67 |   -123.07 |         1.33 |         0    |   9230.4 |
| 1m_60m_sweep_reject | time15_sl250         |  75 |     28    |   -140.89 |         8    |         1.33 |  10566.5 |
| 1m_60m_sweep_reject | time30_sl250         |  75 |     24    |   -143.86 |        12    |         2.67 |  10789.7 |
| 1m_60m_sweep_reject | time60_sl250         |  75 |     28    |   -145.08 |        16    |         4    |  11561.2 |
| 1m_60m_sweep_reject | tp200_sl150          |  75 |     36    |   -103.93 |         0    |         0    |   7795.1 |
| 1m_60m_sweep_reject | tp300_sl200          |  75 |     33.33 |   -112.91 |        32    |         0    |   8573.5 |
| 1m_60m_sweep_reject | tp500_sl250          |  75 |     29.33 |   -120.81 |        24    |         0    |  10380   |
| 1m_60m_sweep_reject | tp500_sl250_be200    |  75 |     21.33 |   -122.56 |        17.33 |         0    |   9414.7 |
| 1m_60m_sweep_reject | tp500_sl250_trail150 |  75 |     42.67 |   -130.32 |         5.33 |         0    |   9851.4 |
| 1m_trend_impulse    | atr4_2R              |  84 |     32.14 |    -81.64 |        32.14 |         9.52 |   7780.7 |
| 1m_trend_impulse    | ema20_exit_sl250     |  84 |     22.62 |     -2.36 |        13.1  |         8.33 |   4577.6 |
| 1m_trend_impulse    | time15_sl250         |  84 |     25    |    -47.21 |        15.48 |         5.95 |   6214.1 |
| 1m_trend_impulse    | time30_sl250         |  84 |     28.57 |    -58.01 |        17.86 |        10.71 |   7885.6 |
| 1m_trend_impulse    | time60_sl250         |  84 |     27.38 |    -31.03 |        19.05 |        10.71 |   5896.7 |
| 1m_trend_impulse    | tp200_sl150          |  84 |     34.52 |   -107.82 |         0    |         0    |   9199.2 |
| 1m_trend_impulse    | tp300_sl200          |  84 |     33.33 |   -111.98 |        33.33 |         0    |   9887.9 |
| 1m_trend_impulse    | tp500_sl250          |  84 |     33.33 |    -89.43 |        29.76 |         0    |   8392.8 |
| 1m_trend_impulse    | tp500_sl250_be200    |  84 |     25    |    -94.55 |        22.62 |         0    |   8822.8 |
| 1m_trend_impulse    | tp500_sl250_trail150 |  84 |     38.1  |   -112.74 |        10.71 |         0    |   9805.2 |
| NY_open_1m          | atr4_2R              |  88 |     28.41 |   -141.03 |        22.73 |         1.14 |  12791.5 |
| NY_open_1m          | ema20_exit_sl250     |  88 |     17.05 |    -96.96 |         7.95 |         3.41 |   8532.8 |
| NY_open_1m          | time15_sl250         |  88 |     32.95 |    -93.39 |        10.23 |         4.55 |   8357.7 |
| NY_open_1m          | time30_sl250         |  88 |     34.09 |   -112.48 |        11.36 |         2.27 |   9898.5 |
| NY_open_1m          | time60_sl250         |  88 |     22.73 |   -123.72 |        14.77 |         9.09 |  11155.1 |
| NY_open_1m          | tp200_sl150          |  88 |     46.59 |    -65.9  |         0    |         0    |   5920.3 |
| NY_open_1m          | tp300_sl200          |  88 |     38.64 |    -84.69 |        38.64 |         0    |   7674.5 |
| NY_open_1m          | tp500_sl250          |  88 |     29.55 |   -108.76 |        28.41 |         0    |   9992.7 |
| NY_open_1m          | tp500_sl250_be200    |  88 |     22.73 |    -80.99 |        22.73 |         0    |   7127.1 |
| NY_open_1m          | tp500_sl250_trail150 |  88 |     43.18 |    -79.13 |        17.05 |         0    |   7039.8 |

## Exit policies
- time15_sl250 / time30_sl250 / time60_sl250: time-based, $250 hard stop.
- tp200_sl150 / tp300_sl200 / tp500_sl250: fixed target/stop; 120m max.
- tp500_sl250_be200: move stop to +10 points after +200 favorable excursion; takes effect NEXT minute.
- tp500_sl250_trail150: start trailing best price minus 150 points after +200 favorable excursion; next minute.
- atr4_2R: past-only 60-minute 1m ATR; stop clipped 120–350, target 2x stop; maximum 120 minutes.
- ema20_exit_sl250: after 5m, close below/above 1m EMA20 triggers next-minute open exit; 250 stop, 60m max.

## Cautions
OHLCV has no actual bid/ask and cannot establish real executable stop prices. Zero-volume candles require separate feed QA.
Some variants have small samples and discovery bias; a positive holdout row is not by itself proof of sustained edge.
Trading every day is not required; do not optimize exit rules solely to achieve daily frequency.

See entries.csv, trades.csv, exit_comparison.csv, training_selected_exits_holdout.csv.
