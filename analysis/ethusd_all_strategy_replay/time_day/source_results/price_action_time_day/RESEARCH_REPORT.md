# BTC Futures: price-action strategies + time-of-day + weekday filters

## Data and design
Original Delta Exchange India BTCUSD perpetual 1m OHLCV, resampled to 5m only for completed-price-structure signals.
Signals after 5m close; entry at following 1m OPEN. Levels are based on previously completed bars, previous calendar day, completed overnight or completed NY 09:30-10:00 opening range.
Entry families: previous day high/low acceptance, sweeps and failed breakouts; overnight range acceptance, sweeps and failed breakouts; NY opening 30m acceptance, sweeps and failed breakouts; recent 1h breakout, 2h sweep, 30m compression/ignition, and sweep-confirmation.
Time windows (America/New_York DST aware): ASIA_EVENING=19:00-03:00; LONDON_EARLY=03:00-09:30; US_OPEN=09:30-11:30; US_AFTERNOON=11:30-16:00; NY_EVENING=16:00-19:00.
Weekday subsets: all, weekdays/weekends, each Monday–Sunday. Only first setup occurrence per session per NY date (to reduce correlation).
Exit variations: +300/-250 in 2h; +500/-350 in 4h; +1000/-500 in 8h; time 2h / -400 stop; time 4h / -500 stop; trailing 350 only once price first moves +500, 8h cap.
All results are BTC **price points**, not account P&L. They include assumed round-trip taker fees and GST plus adverse $5 slippage per side. No funding, realized bid/ask or market impact.
Train=2025, validation=Jan-Jun 2026, final untouched holdout=Jul-Oct 17 2026. Candidate ranking uses ONLY train and validation.
The exploratory 1.96-standard-error lower bound is NOT multiple-testing adjusted; apparent winners still require later independent forward testing and realistic execution replay.

## Data quality
~~~json
{
  "exchange": "Delta Exchange India",
  "symbol": "BTCUSD perpetual",
  "source_month_files": 23,
  "native_1m_candles": 987840,
  "derived_5m_candles": 197568,
  "zero_volume_minutes": 1887,
  "signal_events": 21149,
  "exit_replays": 126780,
  "setup_count": 13,
  "eligible_rules": 1818,
  "two_period_positive_rules": 32,
  "two_period_lower_positive_rules": 0,
  "train": "2025",
  "validation": "2026-01 through 2026-06",
  "holdout": "2026-07-01 through 2026-10-17",
  "fees": "0.05% per side taker + 18% GST on fee; $5 slippage each side",
  "selection": "Training and validation only, never final holdout"
}
~~~

## Candidates selected without seeing holdout
| setup                  | session      | day_group   | exit                 |   n_train |   mean_net_train |   n_validation |   mean_net_validation |   n_holdout |   mean_net_holdout |   win_pct_holdout |     score |
|:-----------------------|:-------------|:------------|:---------------------|----------:|-----------------:|---------------:|----------------------:|------------:|-------------------:|------------------:|----------:|
| local_1h_break_accept  | LONDON_EARLY | SUN         | trail350_after500_8h |        51 |            87.58 |             26 |                 82.09 |          20 |              72.69 |             55    |  -99.5447 |
| local_1h_break_accept  | ASIA_EVENING | TUE         | trail350_after500_8h |        51 |            57.54 |             25 |                122.83 |          20 |              12.49 |             60    |  -99.5827 |
| opening30_sweep_reject | US_OPEN      | ALL         | time4h_sl500         |       264 |            68.88 |            133 |                  1.32 |          95 |             -99.36 |             42.11 | -126.631  |
| local_1h_break_accept  | US_OPEN      | WEEKDAYS    | time4h_sl500         |       207 |            88.82 |             98 |                 33.13 |          79 |              74.24 |             40.51 | -140.291  |
| sweep_nextbar_confirm  | LONDON_EARLY | THU         | tp500_sl350_4h       |        51 |            15.47 |             26 |                  6.53 |          20 |             -21.37 |             45    | -150.858  |
| sweep_nextbar_confirm  | NY_EVENING   | SUN         | trail350_after500_8h |        38 |            65.3  |             21 |                102.08 |          15 |              61.5  |             60    | -169.257  |
| overnight_accept       | ASIA_EVENING | WEEKENDS    | time2h_sl400         |        62 |           137.35 |             27 |                 34.44 |          22 |            -115.96 |             36.36 | -217.222  |
| sweep_nextbar_confirm  | NY_EVENING   | SUN         | tp1000_sl500_8h      |        38 |            17.01 |             21 |                124.83 |          15 |             -47.96 |             33.33 | -218.823  |
| local_1h_break_accept  | NY_EVENING   | MON         | trail350_after500_8h |        30 |            51.55 |             19 |                 34.55 |          12 |            -131.95 |             33.33 | -227.271  |
| compression_ignite     | ASIA_EVENING | WEEKENDS    | trail350_after500_8h |        56 |             2.94 |             24 |                  8.91 |          22 |             -46.11 |             45.45 | -234.225  |
| compression_ignite     | ASIA_EVENING | WEEKENDS    | tp1000_sl500_8h      |        56 |            78.35 |             24 |                  9.68 |          22 |             -35.81 |             36.36 | -236.587  |
| compression_ignite     | ASIA_EVENING | WEEKENDS    | time4h_sl500         |        56 |             6.01 |             24 |                  4.34 |          22 |             -51.54 |             45.45 | -240.903  |
| overnight_accept       | ASIA_EVENING | WEEKENDS    | time4h_sl500         |        62 |           213.85 |             27 |                 16.42 |          22 |            -130.02 |             36.36 | -240.96   |
| local_1h_break_accept  | NY_EVENING   | MON         | time2h_sl400         |        30 |           115.39 |             19 |                 17.44 |          12 |            -164.04 |             25    | -243.288  |
| opening30_sweep_reject | US_OPEN      | SUN         | time4h_sl500         |        43 |            82.36 |             18 |                214.38 |          14 |            -101.95 |             50    | -244.221  |
| opening30_sweep_reject | US_OPEN      | TUE         | tp1000_sl500_8h      |        34 |            38.5  |             20 |                 31.93 |          15 |              96.79 |             60    | -252.305  |
| local_1h_break_accept  | US_OPEN      | FRI         | time2h_sl400         |        47 |           271.24 |             19 |                 80    |          18 |              88.5  |             33.33 | -252.942  |
| sweep_nextbar_confirm  | LONDON_EARLY | WED         | time4h_sl500         |        53 |            19.01 |             25 |                 33.7  |          20 |            -169.93 |             35    | -254.228  |
| opening30_sweep_reject | US_OPEN      | MON         | time2h_sl400         |        38 |            21.96 |             19 |                 34.55 |          15 |              68.05 |             53.33 | -256.107  |
| opening30_accept       | US_OPEN      | FRI         | tp1000_sl500_8h      |        47 |            32.33 |             22 |                 25.62 |          17 |            -344.14 |             11.76 | -259.299  |

## Strongest pre-holdout rules
| setup                  | session      | day_group   | exit                 |   n_train |   mean_net_train |   n_validation |   mean_net_validation |   n_holdout |   mean_net_holdout |   win_pct_holdout |     score |
|:-----------------------|:-------------|:------------|:---------------------|----------:|-----------------:|---------------:|----------------------:|------------:|-------------------:|------------------:|----------:|
| opening30_sweep_reject | US_AFTERNOON | SAT         | tp300_sl250_2h       |        41 |            -9.46 |             18 |                 -6.46 |          11 |             -34.64 |             45.45 |  -94.5127 |
| local_1h_break_accept  | LONDON_EARLY | SUN         | trail350_after500_8h |        51 |            87.58 |             26 |                 82.09 |          20 |              72.69 |             55    |  -99.5447 |
| local_1h_break_accept  | ASIA_EVENING | TUE         | trail350_after500_8h |        51 |            57.54 |             25 |                122.83 |          20 |              12.49 |             60    |  -99.5827 |
| local_1h_break_accept  | ASIA_EVENING | ALL         | tp300_sl250_2h       |       356 |           -82.9  |            180 |                -76    |         140 |             -81.81 |             35.71 | -112.6    |
| local_1h_break_accept  | LONDON_EARLY | WEEKENDS    | tp500_sl350_4h       |       101 |           -28.45 |             52 |                -20.85 |          38 |             -38.72 |             34.21 | -113.483  |
| opening30_sweep_reject | US_OPEN      | WEEKENDS    | tp300_sl250_2h       |        82 |           -48.41 |             37 |                -37.25 |          26 |            -138.84 |             23.08 | -113.939  |
| local_1h_break_accept  | ASIA_EVENING | WEEKDAYS    | tp300_sl250_2h       |       253 |           -86.47 |            129 |                -77.61 |         100 |             -81.59 |             40    | -121.943  |
| prev_day_failed_break  | ASIA_EVENING | WEEKENDS    | tp300_sl250_2h       |        39 |           -17.62 |             20 |                 -5.18 |          17 |               8.13 |             64.71 | -122.233  |
| opening30_failed_break | US_AFTERNOON | SAT         | tp300_sl250_2h       |        37 |           -35.71 |             17 |                -16.52 |          11 |             -51.34 |             36.36 | -122.471  |
| prev_day_sweep_reject  | ASIA_EVENING | ALL         | tp300_sl250_2h       |       138 |           -78.53 |             66 |                -50.77 |          61 |             -17.14 |             57.38 | -124.134  |
| sweep_nextbar_confirm  | LONDON_EARLY | THU         | tp300_sl250_2h       |        51 |           -48.63 |             26 |                -10.61 |          20 |             -96.15 |             35    | -125.274  |
| prev_day_sweep_reject  | ASIA_EVENING | WEEKENDS    | tp300_sl250_2h       |        43 |           -27.18 |             23 |                -15.5  |          19 |              12.1  |             63.16 | -125.351  |
| overnight_accept       | ASIA_EVENING | ALL         | tp300_sl250_2h       |       154 |           -84.41 |             80 |                -63.88 |          54 |            -112.31 |             37.04 | -126.255  |
| opening30_sweep_reject | US_OPEN      | ALL         | time4h_sl500         |       264 |            68.88 |            133 |                  1.32 |          95 |             -99.36 |             42.11 | -126.631  |
| local_1h_break_accept  | LONDON_EARLY | ALL         | tp300_sl250_2h       |       352 |           -98.71 |            180 |                -87.44 |         136 |             -34.31 |             44.12 | -126.673  |
| local_1h_break_accept  | LONDON_EARLY | WEEKENDS    | tp300_sl250_2h       |       101 |           -76.82 |             52 |                -50.26 |          38 |             -51.02 |             36.84 | -127.205  |
| opening30_accept       | US_OPEN      | WEEKDAYS    | tp300_sl250_2h       |       222 |           -91.37 |            114 |                -42.07 |          90 |             -77.64 |             45.56 | -127.804  |
| local_1h_break_accept  | ASIA_EVENING | WEEKENDS    | trail350_after500_8h |       103 |           -22.1  |             51 |                 29.96 |          40 |             -77.88 |             35    | -127.901  |
| local_1h_break_accept  | ASIA_EVENING | ALL         | tp500_sl350_4h       |       356 |           -86.19 |            180 |                -61.6  |         140 |            -109.19 |             31.43 | -128.462  |
| opening30_sweep_reject | US_OPEN      | SAT         | tp300_sl250_2h       |        39 |           -42.19 |             19 |                -24.85 |          12 |            -155.27 |             16.67 | -128.932  |
| prev_day_failed_break  | ASIA_EVENING | ALL         | tp300_sl250_2h       |       124 |           -81.09 |             58 |                -49.71 |          54 |             -16.99 |             57.41 | -129.235  |
| opening30_sweep_reject | NY_EVENING   | ALL         | tp300_sl250_2h       |       166 |           -86.26 |             75 |                -74.48 |          56 |             -62.86 |             44.64 | -129.453  |
| opening30_sweep_reject | NY_EVENING   | WEEKENDS    | tp300_sl250_2h       |        62 |           -52.54 |             25 |                -33.29 |          21 |            -117.02 |             33.33 | -129.569  |
| local_1h_break_accept  | ASIA_EVENING | ALL         | trail350_after500_8h |       356 |           -36.61 |            180 |                -54.72 |         140 |             -93.87 |             42.14 | -130.393  |
| sweep_nextbar_confirm  | NY_EVENING   | WEEKDAYS    | tp300_sl250_2h       |       205 |           -93.79 |             94 |                -30.71 |          67 |             -70.74 |             40.3  | -130.561  |
| sweep_nextbar_confirm  | NY_EVENING   | ALL         | tp300_sl250_2h       |       283 |           -99.52 |            134 |                -47.02 |          98 |             -76.54 |             40.82 | -130.616  |
| overnight_accept       | ASIA_EVENING | ALL         | tp500_sl350_4h       |       154 |           -66.38 |             80 |                -41.07 |          54 |            -120.77 |             35.19 | -130.951  |
| local_1h_break_accept  | LONDON_EARLY | SUN         | tp500_sl350_4h       |        51 |            87.93 |             26 |                 -0.38 |          20 |              -1.19 |             40    | -132.636  |
| opening30_sweep_reject | US_OPEN      | WEEKENDS    | tp500_sl350_4h       |        82 |           -47.31 |             37 |                  2.14 |          26 |            -114.5  |             38.46 | -134.12   |
| local_1h_break_accept  | ASIA_EVENING | ALL         | tp1000_sl500_8h      |       356 |           -50.21 |            180 |                -45.27 |         140 |            -118.64 |             32.14 | -134.985  |
| opening30_failed_break | NY_EVENING   | ALL         | tp300_sl250_2h       |       159 |           -83.16 |             75 |                -80.91 |          53 |             -80.25 |             41.51 | -135.365  |
| local_1h_break_accept  | LONDON_EARLY | ALL         | tp500_sl350_4h       |       352 |           -92.41 |            180 |                -64.75 |         136 |             -44.93 |             40.44 | -135.365  |
| local_1h_break_accept  | LONDON_EARLY | SUN         | tp300_sl250_2h       |        51 |           -32.38 |             26 |                -49.81 |          20 |             -10.67 |             50    | -135.417  |
| local_1h_break_accept  | ASIA_EVENING | WEEKENDS    | tp300_sl250_2h       |       103 |           -74.12 |             51 |                -71.94 |          40 |             -82.38 |             25    | -136.725  |
| opening30_accept       | US_OPEN      | ALL         | tp300_sl250_2h       |       314 |          -108.33 |            160 |                -70.71 |         126 |             -55.85 |             46.83 | -138.537  |

## Interpretation
Look for agreement across all three chronological periods, sufficient sample sizes, and positive expectancy after costs; a high win rate alone is not an edge.
Repeated variants on the same date are correlated, and selected trade results do not prove institutional order flow.
Do NOT optimize using Jul-Oct data then label it out-of-sample; do not force daily trades.
This is research, not a live strategy or a promise of daily 200–500 points.

## Reproducibility
See scripts/research_price_action_time_day.py, price_action_signals.csv, all_exit_trades.csv, time_day_breakdown.csv and ranked_rules_preholdout.csv.
