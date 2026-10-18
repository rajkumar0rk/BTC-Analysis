# Delta BTCUSD 1m: exit policy comparison

This is a real-1m OHLCV, execution-aware research **simulation**, not a guarantee of daily 200–500 points.
Source: actual Delta Exchange India BTCUSD 1m perpetual future; 5 one-minute entry types; 10 exit methods. Every exit on an entry uses the exact same entry timestamp.
Holdout: July 1 through October 17 2026; train before this date. Only first eligible entry per NY weekday per strategy (no trades required every day).
Entry price: next 1m open plus adverse $5 price points. Exit: stop/target touch or timed close, minus adverse $5 points.
Both stop and target in same 1m bar = stop (pessimistic). Trailing/BE decisions update only for next 1m bar.
Futures fee assumed 0.05% taker per side, plus GST 18% on fees, deducted from modeled fills. No bid/ask, funding, market impact, or guaranteed fills.
Price points are per 1 BTC exposure; multiply by contract exposure (e.g. 0.001 BTC) for approximate dollar P&L.

## Data quality
~~~json
{
  "months": 22,
  "bars": 943200,
  "start": "2025-01-01 00:00:00+00:00",
  "end": "2026-10-17 23:59:00+00:00",
  "zero_volume": 1819,
  "entry_events": 2243,
  "exit_simulations": 22430,
  "holdout_start": "2026-07-01",
  "taker_fee": 0.0005,
  "gst_on_fee": 0.18,
  "slippage_points_per_side": 5.0
}
~~~

## Discovery-selected exits, evaluated on holdout
| strategy            | exit                 |   n_discovery |   avg_net_discovery |   win_pct_discovery |   n_holdout |   avg_net_holdout |   win_pct_holdout |   net200_pct_holdout |   max_dd_holdout |
|:--------------------|:---------------------|--------------:|--------------------:|--------------------:|------------:|------------------:|------------------:|---------------------:|-----------------:|
| 1m_3bar_exhaustion  | ema20_exit_sl250     |           379 |              -87.58 |               24.27 |          75 |           -100.35 |             17.33 |                 4    |           7526.3 |
| 1m_3bar_exhaustion  | atr4_2R              |           379 |              -95.49 |               35.09 |          75 |           -113.37 |             29.33 |                21.33 |          10410.8 |
| 1m_trend_impulse    | tp500_sl250_trail150 |           383 |             -105.5  |               39.69 |          77 |           -116.29 |             40.26 |                11.69 |           9247.1 |
| 1m_trend_impulse    | tp500_sl250_be200    |           383 |             -107.02 |               23.24 |          77 |           -113.52 |             22.08 |                22.08 |           9166.2 |
| 1m_60m_sweep_reject | time15_sl250         |           327 |             -109.99 |               30.58 |          72 |            -84.34 |             37.5  |                 9.72 |           6200.7 |
| 1m_60m_sweep_reject | ema20_exit_sl250     |           327 |             -110.21 |               22.63 |          72 |            -85.19 |             22.22 |                 8.33 |           6425.2 |
| 1m_30m_range_break  | tp500_sl250_trail150 |           386 |             -117.89 |               35.49 |          77 |           -117.85 |             37.66 |                14.29 |           9301.5 |
| NY_open_1m          | time30_sl250         |           389 |             -120.93 |               26.74 |          78 |           -123.63 |             35.9  |                10.26 |           9643.5 |
| 1m_30m_range_break  | tp200_sl150          |           386 |             -121.44 |               40.41 |          77 |           -109.1  |             37.66 |                 0    |           8526   |
| NY_open_1m          | tp500_sl250_be200    |           389 |             -129.15 |               22.11 |          78 |            -99.53 |             23.08 |                21.79 |           7763   |

## Every exit in holdout
| strategy            | exit                 |   n |   win_pct |   avg_net |   net200_pct |   net500_pct |   max_dd |
|:--------------------|:---------------------|----:|----------:|----------:|-------------:|-------------:|---------:|
| 1m_30m_range_break  | atr4_2R              |  77 |     20.78 |   -165.78 |        16.88 |         5.19 |  13189.1 |
| 1m_30m_range_break  | ema20_exit_sl250     |  77 |     20.78 |    -86.05 |         7.79 |         5.19 |   7341.7 |
| 1m_30m_range_break  | time15_sl250         |  77 |     24.68 |    -97.26 |        10.39 |         2.6  |   7788.8 |
| 1m_30m_range_break  | time30_sl250         |  77 |     24.68 |   -134.58 |        10.39 |         3.9  |  10949.2 |
| 1m_30m_range_break  | time60_sl250         |  77 |     28.57 |    -93.32 |        20.78 |        11.69 |   7747.5 |
| 1m_30m_range_break  | tp200_sl150          |  77 |     37.66 |   -109.1  |         0    |         0    |   8526   |
| 1m_30m_range_break  | tp300_sl200          |  77 |     38.96 |    -93.39 |        28.57 |         0    |   7416.1 |
| 1m_30m_range_break  | tp500_sl250          |  77 |     29.87 |   -119.71 |        28.57 |         0    |   9642.9 |
| 1m_30m_range_break  | tp500_sl250_be200    |  77 |     22.08 |   -120.18 |        20.78 |         0    |   9678.9 |
| 1m_30m_range_break  | tp500_sl250_trail150 |  77 |     37.66 |   -117.85 |        14.29 |         0    |   9301.5 |
| 1m_3bar_exhaustion  | atr4_2R              |  75 |     29.33 |   -113.37 |        21.33 |         4    |  10410.8 |
| 1m_3bar_exhaustion  | ema20_exit_sl250     |  75 |     17.33 |   -100.35 |         4    |         1.33 |   7526.3 |
| 1m_3bar_exhaustion  | time15_sl250         |  75 |     34.67 |    -59.8  |        20    |         4    |   5747.7 |
| 1m_3bar_exhaustion  | time30_sl250         |  75 |     28    |   -115.82 |        18.67 |         5.33 |   9672.7 |
| 1m_3bar_exhaustion  | time60_sl250         |  75 |     25.33 |   -128.31 |        13.33 |         8    |  10170.1 |
| 1m_3bar_exhaustion  | tp200_sl150          |  75 |     42.67 |    -91.61 |         0    |         0    |   7222.4 |
| 1m_3bar_exhaustion  | tp300_sl200          |  75 |     37.33 |   -100.62 |        30.67 |         0    |   8750.8 |
| 1m_3bar_exhaustion  | tp500_sl250          |  75 |     26.67 |   -136.95 |        24    |         0    |  11166.5 |
| 1m_3bar_exhaustion  | tp500_sl250_be200    |  75 |     21.33 |    -96.89 |        21.33 |         0    |   7941   |
| 1m_3bar_exhaustion  | tp500_sl250_trail150 |  75 |     38.67 |    -97.91 |        12    |         0    |   8026.8 |
| 1m_60m_sweep_reject | atr4_2R              |  72 |     33.33 |    -92.32 |        25    |         6.94 |   7037.3 |
| 1m_60m_sweep_reject | ema20_exit_sl250     |  72 |     22.22 |    -85.19 |         8.33 |         1.39 |   6425.2 |
| 1m_60m_sweep_reject | time15_sl250         |  72 |     37.5  |    -84.34 |         9.72 |         2.78 |   6200.7 |
| 1m_60m_sweep_reject | time30_sl250         |  72 |     36.11 |    -81.62 |        20.83 |         1.39 |   6985.3 |
| 1m_60m_sweep_reject | time60_sl250         |  72 |     25    |   -106.71 |        20.83 |         6.94 |   8187.6 |
| 1m_60m_sweep_reject | tp200_sl150          |  72 |     40.28 |    -96.54 |         0    |         0    |   7049.2 |
| 1m_60m_sweep_reject | tp300_sl200          |  72 |     41.67 |    -83.64 |        26.39 |         0    |   6306   |
| 1m_60m_sweep_reject | tp500_sl250          |  72 |     33.33 |    -99.54 |        27.78 |         0    |   7663   |
| 1m_60m_sweep_reject | tp500_sl250_be200    |  72 |     25    |   -106.36 |        20.83 |         0    |   8153.9 |
| 1m_60m_sweep_reject | tp500_sl250_trail150 |  72 |     38.89 |   -110.98 |        11.11 |         0    |   8187.2 |
| 1m_trend_impulse    | atr4_2R              |  77 |     28.57 |   -121.87 |        23.38 |         2.6  |   9807.8 |
| 1m_trend_impulse    | ema20_exit_sl250     |  77 |     18.18 |    -95.09 |         6.49 |         5.19 |   8037.8 |
| 1m_trend_impulse    | time15_sl250         |  77 |     25.97 |   -115.08 |        10.39 |         2.6  |   9160.5 |
| 1m_trend_impulse    | time30_sl250         |  77 |     28.57 |   -120.39 |        10.39 |         5.19 |   9952.6 |
| 1m_trend_impulse    | time60_sl250         |  77 |     27.27 |    -96.8  |        18.18 |         9.09 |   8015.5 |
| 1m_trend_impulse    | tp200_sl150          |  77 |     38.96 |   -104.73 |         0    |         0    |   8189.8 |
| 1m_trend_impulse    | tp300_sl200          |  77 |     40.26 |    -87.08 |        29.87 |         0    |   7152.2 |
| 1m_trend_impulse    | tp500_sl250          |  77 |     28.57 |   -123.22 |        28.57 |         0    |   9912.8 |
| 1m_trend_impulse    | tp500_sl250_be200    |  77 |     22.08 |   -113.52 |        22.08 |         0    |   9166.2 |
| 1m_trend_impulse    | tp500_sl250_trail150 |  77 |     40.26 |   -116.29 |        11.69 |         0    |   9247.1 |
| NY_open_1m          | atr4_2R              |  78 |     28.21 |   -139.71 |        15.38 |         2.56 |  10897   |
| NY_open_1m          | ema20_exit_sl250     |  78 |     17.95 |    -95.36 |         6.41 |         1.28 |   7438.4 |
| NY_open_1m          | time15_sl250         |  78 |     28.21 |   -118.87 |        10.26 |         3.85 |   9271.6 |
| NY_open_1m          | time30_sl250         |  78 |     35.9  |   -123.63 |        10.26 |         1.28 |   9643.5 |
| NY_open_1m          | time60_sl250         |  78 |     23.08 |   -108.7  |        19.23 |         7.69 |   8478.6 |
| NY_open_1m          | tp200_sl150          |  78 |     44.87 |    -83.92 |         0    |         0    |   6644.5 |
| NY_open_1m          | tp300_sl200          |  78 |     37.18 |   -103.38 |        30.77 |         0    |   8063.6 |
| NY_open_1m          | tp500_sl250          |  78 |     33.33 |    -99.69 |        29.49 |         0    |   7775.6 |
| NY_open_1m          | tp500_sl250_be200    |  78 |     23.08 |    -99.53 |        21.79 |         0    |   7763   |
| NY_open_1m          | tp500_sl250_trail150 |  78 |     41.03 |    -89.13 |        15.38 |         0    |   6984.8 |

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
