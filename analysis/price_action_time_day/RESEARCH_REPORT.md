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
  "source_month_files": 22,
  "native_1m_candles": 943200,
  "derived_5m_candles": 188640,
  "zero_volume_minutes": 1819,
  "signal_events": 21209,
  "exit_replays": 127152,
  "setup_count": 13,
  "eligible_rules": 1800,
  "two_period_positive_rules": 12,
  "two_period_lower_positive_rules": 0,
  "train": "2025",
  "validation": "2026-01 through 2026-06",
  "holdout": "2026-07-01 through 2026-10-17",
  "fees": "0.05% per side taker + 18% GST on fee; $5 slippage each side",
  "selection": "Training and validation only, never final holdout"
}
~~~

## Candidates selected without seeing holdout
| setup                  | session      | day_group   | exit            |   n_train |   mean_net_train |   n_validation |   mean_net_validation |   n_holdout |   mean_net_holdout |   win_pct_holdout |    score |
|:-----------------------|:-------------|:------------|:----------------|----------:|-----------------:|---------------:|----------------------:|------------:|-------------------:|------------------:|---------:|
| compression_ignite     | ASIA_EVENING | SAT         | time2h_sl400    |        31 |            43.07 |             16 |                 38.23 |          10 |            -163.36 |             10    | -183.745 |
| local_2h_sweep_reject  | US_AFTERNOON | TUE         | tp1000_sl500_8h |        48 |            53.63 |             21 |                 94.07 |          11 |             -99.64 |             36.36 | -184.307 |
| local_2h_sweep_reject  | NY_EVENING   | TUE         | time2h_sl400    |        32 |             9.29 |             19 |                 28.04 |          11 |             -57.26 |             36.36 | -185.762 |
| local_1h_break_accept  | LONDON_EARLY | FRI         | tp1000_sl500_8h |        52 |             9.33 |             26 |                 85.61 |          16 |             -21.85 |             37.5  | -197.626 |
| local_2h_sweep_reject  | US_AFTERNOON | TUE         | time4h_sl500    |        48 |           226.69 |             21 |                 83.36 |          11 |             -89.73 |             36.36 | -201.356 |
| overnight_accept       | ASIA_EVENING | WEEKENDS    | time4h_sl500    |        52 |            44.02 |             29 |                124.05 |          17 |            -165.07 |             29.41 | -201.573 |
| sweep_nextbar_confirm  | LONDON_EARLY | WED         | tp1000_sl500_8h |        52 |            20.27 |             24 |                 69.38 |          15 |            -129.66 |             33.33 | -224.345 |
| compression_ignite     | ASIA_EVENING | SAT         | time4h_sl500    |        31 |             7.1  |             16 |                 41.02 |          10 |            -168.45 |             20    | -233.792 |
| local_2h_sweep_reject  | LONDON_EARLY | THU         | tp1000_sl500_8h |        52 |             5.53 |             23 |                 26.26 |          16 |             153.85 |             50    | -271.739 |
| opening30_failed_break | NY_EVENING   | WEEKENDS    | time4h_sl500    |        62 |            27.42 |             29 |                 66.67 |          16 |            -107.91 |             43.75 | -272.463 |
| opening30_accept       | US_OPEN      | THU         | time4h_sl500    |        44 |            78.29 |             21 |                162.43 |          15 |               3.37 |             26.67 | -295.443 |
| local_1h_break_accept  | NY_EVENING   | SUN         | time4h_sl500    |        48 |            92.67 |             25 |                 11.86 |          14 |            -126.1  |             50    | -338.039 |

## Strongest pre-holdout rules
| setup                  | session      | day_group   | exit                 |   n_train |   mean_net_train |   n_validation |   mean_net_validation |   n_holdout |   mean_net_holdout |   win_pct_holdout |    score |
|:-----------------------|:-------------|:------------|:---------------------|----------:|-----------------:|---------------:|----------------------:|------------:|-------------------:|------------------:|---------:|
| opening30_failed_break | ASIA_EVENING | WEEKENDS    | tp300_sl250_2h       |        58 |           -59.68 |             27 |                -21.42 |          20 |            -143.75 |             30    | -119.182 |
| opening30_accept       | US_OPEN      | WEEKDAYS    | tp300_sl250_2h       |       231 |           -90.3  |            114 |                -46.42 |          72 |             -98.13 |             44.44 | -125.829 |
| compression_ignite     | ASIA_EVENING | ALL         | time4h_sl500         |       249 |           -45.44 |            131 |                -32.62 |          65 |             -44.54 |             30.77 | -129.27  |
| opening30_sweep_reject | ASIA_EVENING | WEEKENDS    | tp300_sl250_2h       |        59 |           -75.01 |             27 |                -21.42 |          20 |             -93.98 |             40    | -135.136 |
| opening30_accept       | US_OPEN      | ALL         | tp300_sl250_2h       |       325 |          -107.48 |            164 |                -85.82 |         100 |            -104.77 |             40    | -136.522 |
| compression_ignite     | ASIA_EVENING | ALL         | tp500_sl350_4h       |       249 |           -83.44 |            131 |                -76.75 |          65 |            -146.1  |             27.69 | -136.974 |
| local_2h_sweep_reject  | ASIA_EVENING | FRI         | tp300_sl250_2h       |        52 |           -68.68 |             26 |                  0.06 |          16 |            -137.44 |             18.75 | -140.7   |
| opening30_accept       | US_OPEN      | WEEKDAYS    | tp500_sl350_4h       |       231 |           -81.2  |            114 |                -64.25 |          72 |             -65.62 |             44.44 | -140.777 |
| compression_ignite     | ASIA_EVENING | ALL         | trail350_after500_8h |       249 |           -79.65 |            131 |                -62.22 |          65 |             -95.01 |             35.38 | -145.577 |
| compression_ignite     | ASIA_EVENING | ALL         | tp1000_sl500_8h      |       249 |           -68.59 |            131 |                -30.13 |          65 |             -91.99 |             30.77 | -146.542 |
| overnight_accept       | ASIA_EVENING | WEEKENDS    | tp300_sl250_2h       |        52 |           -77.48 |             29 |                -48.68 |          17 |            -128.83 |             29.41 | -149.021 |
| sweep_nextbar_confirm  | LONDON_EARLY | ALL         | tp1000_sl500_8h      |       355 |           -80.55 |            177 |                 23.95 |         106 |             -83.61 |             37.74 | -149.934 |
| compression_ignite     | ASIA_EVENING | ALL         | time2h_sl400         |       249 |           -58.34 |            131 |                -79.61 |          65 |            -101.66 |             24.62 | -150.388 |
| local_2h_sweep_reject  | LONDON_EARLY | WEEKDAYS    | tp300_sl250_2h       |       256 |          -118.78 |            126 |                -97.27 |          76 |            -119.36 |             35.53 | -150.555 |
| sweep_nextbar_confirm  | ASIA_EVENING | ALL         | tp300_sl250_2h       |       362 |          -124.86 |            179 |                -72.71 |         108 |             -95.66 |             32.41 | -150.724 |
| local_2h_sweep_reject  | US_OPEN      | ALL         | tp300_sl250_2h       |       276 |          -107.58 |            142 |               -108.56 |          82 |             -99.04 |             37.8  | -150.989 |
| compression_ignite     | ASIA_EVENING | SAT         | tp300_sl250_2h       |        31 |           -62.89 |             16 |                -48.48 |          10 |            -148.37 |             10    | -151.703 |
| compression_ignite     | ASIA_EVENING | WEEKDAYS    | tp500_sl350_4h       |       181 |           -90.36 |             97 |                -79.8  |          49 |            -150.99 |             28.57 | -152.201 |
| sweep_nextbar_confirm  | ASIA_EVENING | WEEKDAYS    | tp300_sl250_2h       |       258 |          -120.73 |            128 |                -81.09 |          78 |            -113.49 |             32.05 | -152.423 |
| opening30_failed_break | US_OPEN      | WEEKDAYS    | tp300_sl250_2h       |       154 |          -109.42 |             82 |                -82.62 |          52 |             -68.77 |             46.15 | -152.765 |
| sweep_nextbar_confirm  | ASIA_EVENING | FRI         | tp300_sl250_2h       |        52 |           -82.74 |             26 |                 34.31 |          16 |            -159.11 |             12.5  | -152.819 |
| opening30_failed_break | ASIA_EVENING | ALL         | tp300_sl250_2h       |       161 |          -113.66 |             83 |                -92.41 |          54 |            -133.27 |             29.63 | -152.894 |
| local_1h_break_accept  | LONDON_EARLY | ALL         | tp300_sl250_2h       |       356 |          -126.91 |            178 |               -100.41 |         107 |             -58.47 |             43.93 | -153.325 |
| local_2h_sweep_reject  | NY_EVENING   | WEEKDAYS    | tp300_sl250_2h       |       187 |          -117.04 |             92 |                -15.08 |          58 |             -81.65 |             37.93 | -154.463 |
| opening30_accept       | US_OPEN      | FRI         | tp300_sl250_2h       |        50 |           -66.65 |             19 |                -29.84 |          15 |            -126.21 |             40    | -154.484 |
| opening30_accept       | NY_EVENING   | WEEKENDS    | tp300_sl250_2h       |        61 |           -94.82 |             33 |                -59.26 |          17 |            -129.83 |             29.41 | -154.72  |
| local_1h_break_accept  | US_OPEN      | WEEKDAYS    | tp300_sl250_2h       |       229 |          -119.18 |            114 |                -94.47 |          66 |            -142.23 |             36.36 | -154.82  |
| local_2h_sweep_reject  | NY_EVENING   | ALL         | tp300_sl250_2h       |       269 |          -124.13 |            135 |                -22.7  |          79 |            -110.79 |             31.65 | -154.912 |
| opening30_accept       | US_OPEN      | WEEKDAYS    | time2h_sl400         |       231 |           -35.31 |            114 |                -41.1  |          72 |             -11.09 |             41.67 | -155.885 |
| sweep_nextbar_confirm  | LONDON_EARLY | ALL         | time4h_sl500         |       355 |           -97    |            177 |                  5.53 |         106 |            -133.55 |             32.08 | -155.982 |
| opening30_sweep_reject | US_OPEN      | WEEKDAYS    | tp300_sl250_2h       |       195 |          -111.92 |             95 |               -102.1  |          63 |             -51.94 |             50.79 | -156.916 |
| compression_ignite     | ASIA_EVENING | ALL         | tp300_sl250_2h       |       249 |          -125.28 |            131 |                -93.75 |          65 |            -112.32 |             26.15 | -157.084 |
| opening30_sweep_reject | US_OPEN      | ALL         | tp300_sl250_2h       |       274 |          -126    |            138 |                -97.78 |          87 |             -60.72 |             47.13 | -157.424 |
| local_1h_break_accept  | LONDON_EARLY | ALL         | time2h_sl400         |       356 |          -105.53 |            178 |               -107.35 |         107 |             -60.77 |             38.32 | -157.565 |
| local_2h_sweep_reject  | NY_EVENING   | WEEKDAYS    | time2h_sl400         |       187 |           -91.6  |             92 |                 14.71 |          58 |             -30.37 |             39.66 | -157.777 |

## Interpretation
Look for agreement across all three chronological periods, sufficient sample sizes, and positive expectancy after costs; a high win rate alone is not an edge.
Repeated variants on the same date are correlated, and selected trade results do not prove institutional order flow.
Do NOT optimize using Jul-Oct data then label it out-of-sample; do not force daily trades.
This is research, not a live strategy or a promise of daily 200–500 points.

## Reproducibility
See scripts/research_price_action_time_day.py, price_action_signals.csv, all_exit_trades.csv, time_day_breakdown.csv and ranked_rules_preholdout.csv.
