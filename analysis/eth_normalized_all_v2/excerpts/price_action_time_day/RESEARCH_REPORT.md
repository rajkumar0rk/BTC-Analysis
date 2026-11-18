# BTC Futures: price-action strategies + time-of-day + weekday filters

## Data and design
Original Delta Exchange India ETHUSD perpetual 1m OHLCV, resampled to 5m only for completed-price-structure signals.
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
  "symbol": "ETHUSD perpetual",
  "source_month_files": 22,
  "native_1m_candles": 963360,
  "derived_5m_candles": 192672,
  "zero_volume_minutes": 1887,
  "signal_events": 20682,
  "exit_replays": 123930,
  "setup_count": 13,
  "eligible_rules": 1794,
  "two_period_positive_rules": 29,
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
| local_1h_break_accept  | LONDON_EARLY | SUN         | trail350_after500_8h |        51 |            87.58 |             26 |                 82.09 |          17 |              46.65 |             47.06 |  -99.5447 |
| local_1h_break_accept  | ASIA_EVENING | TUE         | trail350_after500_8h |        51 |            57.54 |             25 |                122.83 |          17 |             -36.92 |             58.82 |  -99.5827 |
| opening30_sweep_reject | US_OPEN      | ALL         | time4h_sl500         |       264 |            68.88 |            133 |                  1.32 |          84 |            -109.79 |             42.86 | -126.631  |
| local_1h_break_accept  | US_OPEN      | WEEKDAYS    | time4h_sl500         |       207 |            88.82 |             98 |                 33.13 |          68 |              34.13 |             38.24 | -140.291  |
| sweep_nextbar_confirm  | LONDON_EARLY | THU         | tp500_sl350_4h       |        51 |            15.47 |             26 |                  6.53 |          18 |               6.25 |             50    | -150.858  |
| sweep_nextbar_confirm  | NY_EVENING   | SUN         | trail350_after500_8h |        38 |            65.3  |             21 |                102.08 |          14 |             107.71 |             64.29 | -169.257  |
| overnight_accept       | ASIA_EVENING | WEEKENDS    | time2h_sl400         |        62 |           137.35 |             27 |                 34.44 |          19 |            -155.42 |             26.32 | -217.222  |
| sweep_nextbar_confirm  | NY_EVENING   | SUN         | tp1000_sl500_8h      |        38 |            17.01 |             21 |                124.83 |          14 |              -9.56 |             35.71 | -218.823  |
| local_1h_break_accept  | NY_EVENING   | MON         | trail350_after500_8h |        30 |            51.55 |             19 |                 34.55 |          12 |            -131.95 |             33.33 | -227.271  |
| overnight_accept       | ASIA_EVENING | WEEKENDS    | time4h_sl500         |        62 |           213.85 |             27 |                 16.42 |          19 |            -196.61 |             31.58 | -240.96   |
| local_1h_break_accept  | NY_EVENING   | MON         | time2h_sl400         |        30 |           115.39 |             19 |                 17.44 |          12 |            -164.04 |             25    | -243.288  |
| opening30_sweep_reject | US_OPEN      | SUN         | time4h_sl500         |        43 |            82.36 |             18 |                214.38 |          12 |             -93.42 |             50    | -244.221  |
| opening30_sweep_reject | US_OPEN      | TUE         | tp1000_sl500_8h      |        34 |            38.5  |             20 |                 31.93 |          12 |             105.23 |             66.67 | -252.305  |
| local_1h_break_accept  | US_OPEN      | FRI         | time2h_sl400         |        47 |           271.24 |             19 |                 80    |          16 |              85.7  |             31.25 | -252.942  |
| sweep_nextbar_confirm  | LONDON_EARLY | WED         | time4h_sl500         |        53 |            19.01 |             25 |                 33.7  |          18 |            -194.91 |             33.33 | -254.228  |
| opening30_sweep_reject | US_OPEN      | MON         | time2h_sl400         |        38 |            21.96 |             19 |                 34.55 |          12 |              60.76 |             50    | -256.107  |
| opening30_accept       | US_OPEN      | FRI         | tp1000_sl500_8h      |        47 |            32.33 |             22 |                 25.62 |          15 |            -391.52 |              6.67 | -259.299  |
| local_1h_break_accept  | US_OPEN      | FRI         | time4h_sl500         |        47 |           457.16 |             19 |                103.25 |          16 |              -9.02 |             25    | -265.413  |
| opening30_sweep_reject | US_OPEN      | SUN         | trail350_after500_8h |        43 |            41.69 |             18 |                  7.75 |          12 |              28.68 |             50    | -272.67   |
| local_2h_sweep_reject  | US_AFTERNOON | THU         | time4h_sl500         |        47 |             0.48 |             21 |                192.58 |          14 |            -175.55 |             35.71 | -289.406  |

## Strongest pre-holdout rules
| setup                  | session      | day_group   | exit                 |   n_train |   mean_net_train |   n_validation |   mean_net_validation |   n_holdout |   mean_net_holdout |   win_pct_holdout |     score |
|:-----------------------|:-------------|:------------|:---------------------|----------:|-----------------:|---------------:|----------------------:|------------:|-------------------:|------------------:|----------:|
| opening30_sweep_reject | US_AFTERNOON | SAT         | tp300_sl250_2h       |        41 |            -9.46 |             18 |                 -6.46 |           9 |             -14.41 |             44.44 |  -94.5127 |
| local_1h_break_accept  | LONDON_EARLY | SUN         | trail350_after500_8h |        51 |            87.58 |             26 |                 82.09 |          17 |              46.65 |             47.06 |  -99.5447 |
| local_1h_break_accept  | ASIA_EVENING | TUE         | trail350_after500_8h |        51 |            57.54 |             25 |                122.83 |          17 |             -36.92 |             58.82 |  -99.5827 |
| local_1h_break_accept  | ASIA_EVENING | ALL         | tp300_sl250_2h       |       356 |           -82.9  |            180 |                -76    |         123 |             -74.86 |             35.77 | -112.6    |
| local_1h_break_accept  | LONDON_EARLY | WEEKENDS    | tp500_sl350_4h       |       101 |           -28.45 |             52 |                -20.85 |          33 |             -32.04 |             33.33 | -113.483  |
| opening30_sweep_reject | US_OPEN      | WEEKENDS    | tp300_sl250_2h       |        82 |           -48.41 |             37 |                -37.25 |          24 |            -149.5  |             20.83 | -113.939  |
| local_1h_break_accept  | ASIA_EVENING | WEEKDAYS    | tp300_sl250_2h       |       253 |           -86.47 |            129 |                -77.61 |          88 |             -76.26 |             39.77 | -121.943  |
| prev_day_failed_break  | ASIA_EVENING | WEEKENDS    | tp300_sl250_2h       |        39 |           -17.62 |             20 |                 -5.18 |          16 |              29.59 |             68.75 | -122.233  |
| opening30_failed_break | US_AFTERNOON | SAT         | tp300_sl250_2h       |        37 |           -35.71 |             17 |                -16.52 |           9 |             -14.41 |             44.44 | -122.471  |
| prev_day_sweep_reject  | ASIA_EVENING | ALL         | tp300_sl250_2h       |       138 |           -78.53 |             66 |                -50.77 |          57 |              -4.71 |             59.65 | -124.134  |
| sweep_nextbar_confirm  | LONDON_EARLY | THU         | tp300_sl250_2h       |        51 |           -48.63 |             26 |                -10.61 |          18 |             -85.14 |             38.89 | -125.274  |
| prev_day_sweep_reject  | ASIA_EVENING | WEEKENDS    | tp300_sl250_2h       |        43 |           -27.18 |             23 |                -15.5  |          18 |              31.4  |             66.67 | -125.351  |
| overnight_accept       | ASIA_EVENING | ALL         | tp300_sl250_2h       |       154 |           -84.41 |             80 |                -63.88 |          47 |            -134.74 |             31.91 | -126.255  |
| opening30_sweep_reject | US_OPEN      | ALL         | time4h_sl500         |       264 |            68.88 |            133 |                  1.32 |          84 |            -109.79 |             42.86 | -126.631  |
| local_1h_break_accept  | LONDON_EARLY | ALL         | tp300_sl250_2h       |       352 |           -98.71 |            180 |                -87.44 |         120 |             -34.92 |             44.17 | -126.673  |
| local_1h_break_accept  | LONDON_EARLY | WEEKENDS    | tp300_sl250_2h       |       101 |           -76.82 |             52 |                -50.26 |          33 |             -35    |             39.39 | -127.205  |
| opening30_accept       | US_OPEN      | WEEKDAYS    | tp300_sl250_2h       |       222 |           -91.37 |            114 |                -42.07 |          78 |             -67.03 |             47.44 | -127.804  |
| local_1h_break_accept  | ASIA_EVENING | WEEKENDS    | trail350_after500_8h |       103 |           -22.1  |             51 |                 29.96 |          35 |             -57.28 |             37.14 | -127.901  |
| local_1h_break_accept  | ASIA_EVENING | ALL         | tp500_sl350_4h       |       356 |           -86.19 |            180 |                -61.6  |         123 |            -111.87 |             30.89 | -128.462  |
| opening30_sweep_reject | US_OPEN      | SAT         | tp300_sl250_2h       |        39 |           -42.19 |             19 |                -24.85 |          12 |            -155.27 |             16.67 | -128.932  |
| prev_day_failed_break  | ASIA_EVENING | ALL         | tp300_sl250_2h       |       124 |           -81.09 |             58 |                -49.71 |          51 |              -9.31 |             58.82 | -129.235  |
| opening30_sweep_reject | NY_EVENING   | ALL         | tp300_sl250_2h       |       166 |           -86.26 |             75 |                -74.48 |          48 |             -69.27 |             43.75 | -129.453  |
| opening30_sweep_reject | NY_EVENING   | WEEKENDS    | tp300_sl250_2h       |        62 |           -52.54 |             25 |                -33.29 |          18 |            -112.07 |             33.33 | -129.569  |
| local_1h_break_accept  | ASIA_EVENING | ALL         | trail350_after500_8h |       356 |           -36.61 |            180 |                -54.72 |         123 |             -94.45 |             43.09 | -130.393  |
| sweep_nextbar_confirm  | NY_EVENING   | WEEKDAYS    | tp300_sl250_2h       |       205 |           -93.79 |             94 |                -30.71 |          59 |             -81.75 |             37.29 | -130.561  |
| sweep_nextbar_confirm  | NY_EVENING   | ALL         | tp300_sl250_2h       |       283 |           -99.52 |            134 |                -47.02 |          87 |             -80.93 |             39.08 | -130.616  |
| overnight_accept       | ASIA_EVENING | ALL         | tp500_sl350_4h       |       154 |           -66.38 |             80 |                -41.07 |          47 |            -118.52 |             36.17 | -130.951  |
| local_1h_break_accept  | LONDON_EARLY | SUN         | tp500_sl350_4h       |        51 |            87.93 |             26 |                 -0.38 |          17 |              39.28 |             41.18 | -132.636  |
| opening30_sweep_reject | US_OPEN      | WEEKENDS    | tp500_sl350_4h       |        82 |           -47.31 |             37 |                  2.14 |          24 |            -110.37 |             37.5  | -134.12   |
| local_1h_break_accept  | ASIA_EVENING | ALL         | tp1000_sl500_8h      |       356 |           -50.21 |            180 |                -45.27 |         123 |            -133.34 |             32.52 | -134.985  |
| opening30_failed_break | NY_EVENING   | ALL         | tp300_sl250_2h       |       159 |           -83.16 |             75 |                -80.91 |          45 |             -76.34 |             42.22 | -135.365  |
| local_1h_break_accept  | LONDON_EARLY | ALL         | tp500_sl350_4h       |       352 |           -92.41 |            180 |                -64.75 |         120 |             -52.69 |             39.17 | -135.365  |
| local_1h_break_accept  | LONDON_EARLY | SUN         | tp300_sl250_2h       |        51 |           -32.38 |             26 |                -49.81 |          17 |              38.11 |             58.82 | -135.417  |
| compression_ignite     | ASIA_EVENING | ALL         | tp300_sl250_2h       |       221 |           -85.58 |            113 |                -91.06 |          78 |             -32.06 |             47.44 | -136.475  |
| local_1h_break_accept  | ASIA_EVENING | WEEKENDS    | tp300_sl250_2h       |       103 |           -74.12 |             51 |                -71.94 |          35 |             -71.34 |             25.71 | -136.725  |

## Interpretation
Look for agreement across all three chronological periods, sufficient sample sizes, and positive expectancy after costs; a high win rate alone is not an edge.
Repeated variants on the same date are correlated, and selected trade results do not prove institutional order flow.
Do NOT optimize using Jul-Oct data then label it out-of-sample; do not force daily trades.
This is research, not a live strategy or a promise of daily 200–500 points.

## Reproducibility
See scripts/research_price_action_time_day.py, price_action_signals.csv, all_exit_trades.csv, time_day_breakdown.csv and ranked_rules_preholdout.csv.
