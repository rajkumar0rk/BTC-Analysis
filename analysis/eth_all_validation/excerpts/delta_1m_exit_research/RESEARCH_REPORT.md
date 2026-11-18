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
  "months": 23,
  "bars": 987840,
  "start": "2025-01-01 00:00:00+00:00",
  "end": "2026-11-17 23:59:00+00:00",
  "zero_volume": 1887,
  "entry_events": 2344,
  "exit_simulations": 23440,
  "holdout_start": "2026-07-01",
  "taker_fee": 0.0005,
  "gst_on_fee": 0.18,
  "slippage_points_per_side": 5.0
}
~~~

## Discovery-selected exits, evaluated on holdout
| strategy            | exit             |   n_discovery |   avg_net_discovery |   win_pct_discovery |   n_holdout |   avg_net_holdout |   win_pct_holdout |   net200_pct_holdout |   max_dd_holdout |
|:--------------------|:-----------------|--------------:|--------------------:|--------------------:|------------:|------------------:|------------------:|---------------------:|-----------------:|
| NY_open_1m          | atr4_2R          |           390 |              -10.08 |               35.13 |         100 |            -10.67 |             28    |                    0 |           1095.5 |
| NY_open_1m          | tp200_sl150      |           390 |              -10.32 |               35.13 |         100 |            -10.97 |             28    |                    0 |           1125.5 |
| 1m_30m_range_break  | tp200_sl150      |           386 |              -12.13 |               35.75 |          98 |            -10.53 |             25.51 |                    0 |           1175.4 |
| 1m_30m_range_break  | atr4_2R          |           386 |              -12.15 |               35.49 |          98 |            -10.56 |             25.51 |                    0 |           1178.5 |
| 1m_3bar_exhaustion  | time15_sl250     |           380 |              -12.95 |               20.26 |          97 |            -12.18 |              9.28 |                    0 |           1190   |
| 1m_trend_impulse    | tp200_sl150      |           383 |              -12.98 |               33.68 |          96 |            -11.09 |             27.08 |                    0 |           1137.7 |
| 1m_60m_sweep_reject | time15_sl250     |           330 |              -13.1  |               16.97 |          84 |            -15.28 |              7.14 |                    0 |           1287.6 |
| 1m_trend_impulse    | atr4_2R          |           383 |              -13.11 |               33.42 |          96 |            -11.09 |             27.08 |                    0 |           1137.7 |
| 1m_3bar_exhaustion  | time30_sl250     |           380 |              -13.15 |               25    |          97 |            -10.83 |             17.53 |                    0 |           1154   |
| 1m_60m_sweep_reject | ema20_exit_sl250 |           330 |              -13.53 |                5.15 |          84 |            -14.59 |              1.19 |                    0 |           1226   |

## Every exit in holdout
| strategy            | exit                 |   n |   win_pct |   avg_net |   net200_pct |   net500_pct |   max_dd |
|:--------------------|:---------------------|----:|----------:|----------:|-------------:|-------------:|---------:|
| 1m_30m_range_break  | atr4_2R              |  98 |     25.51 |    -10.56 |            0 |            0 |   1178.5 |
| 1m_30m_range_break  | ema20_exit_sl250     |  98 |     12.24 |    -11.13 |            0 |            0 |   1142.4 |
| 1m_30m_range_break  | time15_sl250         |  98 |     10.2  |    -12.08 |            0 |            0 |   1184.2 |
| 1m_30m_range_break  | time30_sl250         |  98 |     16.33 |    -11.59 |            0 |            0 |   1213.4 |
| 1m_30m_range_break  | time60_sl250         |  98 |     22.45 |    -11    |            0 |            0 |   1213   |
| 1m_30m_range_break  | tp200_sl150          |  98 |     25.51 |    -10.53 |            0 |            0 |   1175.4 |
| 1m_30m_range_break  | tp300_sl200          |  98 |     25.51 |    -10.53 |            0 |            0 |   1175.4 |
| 1m_30m_range_break  | tp500_sl250          |  98 |     25.51 |    -10.53 |            0 |            0 |   1175.4 |
| 1m_30m_range_break  | tp500_sl250_be200    |  98 |     25.51 |    -10.53 |            0 |            0 |   1175.4 |
| 1m_30m_range_break  | tp500_sl250_trail150 |  98 |     25.51 |    -10.53 |            0 |            0 |   1175.4 |
| 1m_3bar_exhaustion  | atr4_2R              |  97 |     32.99 |     -8.56 |            0 |            0 |   1044.2 |
| 1m_3bar_exhaustion  | ema20_exit_sl250     |  97 |      4.12 |    -10.6  |            0 |            0 |   1133.1 |
| 1m_3bar_exhaustion  | time15_sl250         |  97 |      9.28 |    -12.18 |            0 |            0 |   1190   |
| 1m_3bar_exhaustion  | time30_sl250         |  97 |     17.53 |    -10.83 |            0 |            0 |   1154   |
| 1m_3bar_exhaustion  | time60_sl250         |  97 |     29.9  |     -8.09 |            0 |            0 |    941.6 |
| 1m_3bar_exhaustion  | tp200_sl150          |  97 |     32.99 |     -9.18 |            0 |            0 |   1104.2 |
| 1m_3bar_exhaustion  | tp300_sl200          |  97 |     32.99 |     -8.54 |            0 |            0 |   1042.7 |
| 1m_3bar_exhaustion  | tp500_sl250          |  97 |     32.99 |     -8.54 |            0 |            0 |   1042.7 |
| 1m_3bar_exhaustion  | tp500_sl250_be200    |  97 |     32.99 |     -8.54 |            0 |            0 |   1042.7 |
| 1m_3bar_exhaustion  | tp500_sl250_trail150 |  97 |     32.99 |     -8.54 |            0 |            0 |   1042.7 |
| 1m_60m_sweep_reject | atr4_2R              |  84 |     23.81 |    -15.92 |            0 |            0 |   1390   |
| 1m_60m_sweep_reject | ema20_exit_sl250     |  84 |      1.19 |    -14.59 |            0 |            0 |   1226   |
| 1m_60m_sweep_reject | time15_sl250         |  84 |      7.14 |    -15.28 |            0 |            0 |   1287.6 |
| 1m_60m_sweep_reject | time30_sl250         |  84 |     14.29 |    -15.03 |            0 |            0 |   1299   |
| 1m_60m_sweep_reject | time60_sl250         |  84 |     21.43 |    -14.34 |            0 |            0 |   1254.9 |
| 1m_60m_sweep_reject | tp200_sl150          |  84 |     23.81 |    -15.84 |            0 |            0 |   1383.4 |
| 1m_60m_sweep_reject | tp300_sl200          |  84 |     23.81 |    -15.84 |            0 |            0 |   1383.4 |
| 1m_60m_sweep_reject | tp500_sl250          |  84 |     23.81 |    -15.84 |            0 |            0 |   1383.4 |
| 1m_60m_sweep_reject | tp500_sl250_be200    |  84 |     23.81 |    -15.84 |            0 |            0 |   1383.4 |
| 1m_60m_sweep_reject | tp500_sl250_trail150 |  84 |     23.81 |    -15.84 |            0 |            0 |   1383.4 |
| 1m_trend_impulse    | atr4_2R              |  96 |     27.08 |    -11.09 |            0 |            0 |   1137.7 |
| 1m_trend_impulse    | ema20_exit_sl250     |  96 |     14.58 |     -8.49 |            0 |            0 |    881.2 |
| 1m_trend_impulse    | time15_sl250         |  96 |     16.67 |    -10.83 |            0 |            0 |   1042.9 |
| 1m_trend_impulse    | time30_sl250         |  96 |     17.71 |    -10.28 |            0 |            0 |   1033.7 |
| 1m_trend_impulse    | time60_sl250         |  96 |     21.88 |    -10.18 |            0 |            0 |   1069   |
| 1m_trend_impulse    | tp200_sl150          |  96 |     27.08 |    -11.09 |            0 |            0 |   1137.7 |
| 1m_trend_impulse    | tp300_sl200          |  96 |     27.08 |    -11.09 |            0 |            0 |   1137.7 |
| 1m_trend_impulse    | tp500_sl250          |  96 |     27.08 |    -11.09 |            0 |            0 |   1137.7 |
| 1m_trend_impulse    | tp500_sl250_be200    |  96 |     27.08 |    -11.09 |            0 |            0 |   1137.7 |
| 1m_trend_impulse    | tp500_sl250_trail150 |  96 |     27.08 |    -11.09 |            0 |            0 |   1137.7 |
| NY_open_1m          | atr4_2R              | 100 |     28    |    -10.67 |            0 |            0 |   1095.5 |
| NY_open_1m          | ema20_exit_sl250     | 100 |      7    |    -13.01 |            0 |            0 |   1301   |
| NY_open_1m          | time15_sl250         | 100 |      8    |    -13.04 |            0 |            0 |   1303.7 |
| NY_open_1m          | time30_sl250         | 100 |      8    |    -11.47 |            0 |            0 |   1146.6 |
| NY_open_1m          | time60_sl250         | 100 |     17    |    -12.06 |            0 |            0 |   1207.9 |
| NY_open_1m          | tp200_sl150          | 100 |     28    |    -10.97 |            0 |            0 |   1125.5 |
| NY_open_1m          | tp300_sl200          | 100 |     28    |    -10.63 |            0 |            0 |   1092.3 |
| NY_open_1m          | tp500_sl250          | 100 |     28    |    -10.63 |            0 |            0 |   1092.3 |
| NY_open_1m          | tp500_sl250_be200    | 100 |     28    |    -10.63 |            0 |            0 |   1092.3 |
| NY_open_1m          | tp500_sl250_trail150 | 100 |     28    |    -10.63 |            0 |            0 |   1092.3 |

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
