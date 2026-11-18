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
  "source_month_files": 23,
  "native_1m_candles": 987840,
  "derived_5m_candles": 197568,
  "zero_volume_minutes": 1887,
  "signal_events": 21152,
  "exit_replays": 126798,
  "setup_count": 13,
  "eligible_rules": 1818,
  "two_period_positive_rules": 2,
  "two_period_lower_positive_rules": 0,
  "train": "2025",
  "validation": "2026-01 through 2026-06",
  "holdout": "2026-07-01 through 2026-10-17",
  "fees": "0.05% per side taker + 18% GST on fee; $5 slippage each side",
  "selection": "Training and validation only, never final holdout"
}
~~~

## Candidates selected without seeing holdout
| setup            | session   | day_group   | exit                 |   n_train |   mean_net_train |   n_validation |   mean_net_validation |   n_holdout |   mean_net_holdout |   win_pct_holdout |    score |
|:-----------------|:----------|:------------|:---------------------|----------:|-----------------:|---------------:|----------------------:|------------:|-------------------:|------------------:|---------:|
| overnight_accept | US_OPEN   | TUE         | trail350_after500_8h |        35 |             9.37 |             18 |                  0.95 |          11 |             -20.24 |             18.18 | -26.0618 |
| overnight_accept | US_OPEN   | TUE         | tp1000_sl500_8h      |        35 |             9.37 |             18 |                  0.95 |          11 |             -20.24 |             18.18 | -26.0618 |

## Strongest pre-holdout rules
| setup                  | session      | day_group   | exit                 |   n_train |   mean_net_train |   n_validation |   mean_net_validation |   n_holdout |   mean_net_holdout |   win_pct_holdout |    score |
|:-----------------------|:-------------|:------------|:---------------------|----------:|-----------------:|---------------:|----------------------:|------------:|-------------------:|------------------:|---------:|
| local_2h_sweep_reject  | NY_EVENING   | FRI         | time2h_sl400         |        40 |            -3.06 |             17 |                 -8.61 |          16 |             -13.62 |              0    | -14.4211 |
| overnight_accept       | US_OPEN      | ALL         | tp1000_sl500_8h      |       212 |            -0.88 |            112 |                 -6.81 |          77 |              -8.5  |             27.27 | -14.4366 |
| overnight_accept       | US_OPEN      | ALL         | trail350_after500_8h |       212 |            -0.88 |            112 |                 -6.81 |          77 |              -8.5  |             27.27 | -14.4366 |
| prev_day_sweep_reject  | ASIA_EVENING | WEEKENDS    | time2h_sl400         |        43 |            -7.33 |             23 |                 -7.63 |          19 |              -5.76 |             36.84 | -14.9006 |
| prev_day_sweep_reject  | ASIA_EVENING | WEEKENDS    | tp300_sl250_2h       |        43 |            -7.33 |             23 |                 -7.63 |          19 |              -5.76 |             36.84 | -14.9006 |
| local_1h_break_accept  | US_OPEN      | ALL         | tp500_sl350_4h       |       276 |            -6.58 |            129 |                 -8    |         104 |             -10.57 |             29.81 | -15.0968 |
| local_1h_break_accept  | US_OPEN      | ALL         | time4h_sl500         |       276 |            -6.58 |            129 |                 -8    |         104 |             -10.57 |             29.81 | -15.0968 |
| opening30_accept       | US_AFTERNOON | ALL         | tp500_sl350_4h       |       261 |            -9.42 |            124 |                 -9.89 |          83 |              -9.59 |             22.89 | -15.2058 |
| opening30_accept       | US_AFTERNOON | ALL         | time4h_sl500         |       261 |            -9.42 |            124 |                 -9.89 |          83 |              -9.59 |             22.89 | -15.2058 |
| overnight_accept       | US_OPEN      | ALL         | time4h_sl500         |       212 |             0.09 |            112 |                 -8.29 |          77 |             -10.29 |             25.97 | -15.2444 |
| overnight_accept       | US_OPEN      | ALL         | tp500_sl350_4h       |       212 |             0.09 |            112 |                 -8.29 |          77 |             -10.29 |             25.97 | -15.2444 |
| local_1h_break_accept  | US_AFTERNOON | WEEKENDS    | tp300_sl250_2h       |        80 |            -7.23 |             42 |                 -9.67 |          33 |             -11.64 |              9.09 | -15.2766 |
| local_1h_break_accept  | US_AFTERNOON | WEEKENDS    | time2h_sl400         |        80 |            -7.23 |             42 |                 -9.67 |          33 |             -11.64 |              9.09 | -15.2766 |
| local_1h_break_accept  | ASIA_EVENING | WEEKENDS    | tp1000_sl500_8h      |       103 |            -2.76 |             51 |                 -6.6  |          40 |             -12.68 |             15    | -15.4594 |
| local_1h_break_accept  | ASIA_EVENING | WEEKENDS    | trail350_after500_8h |       103 |            -2.76 |             51 |                 -6.6  |          40 |             -12.68 |             15    | -15.4594 |
| local_1h_break_accept  | ASIA_EVENING | ALL         | time2h_sl400         |       356 |           -11.36 |            180 |                -12.55 |         140 |             -12.75 |             12.14 | -15.4616 |
| local_1h_break_accept  | ASIA_EVENING | ALL         | tp300_sl250_2h       |       356 |           -11.36 |            180 |                -12.55 |         140 |             -12.75 |             12.14 | -15.4616 |
| local_1h_break_accept  | ASIA_EVENING | ALL         | trail350_after500_8h |       356 |            -6.92 |            180 |                -10.04 |         140 |             -13.22 |             23.57 | -15.5038 |
| local_1h_break_accept  | ASIA_EVENING | ALL         | tp1000_sl500_8h      |       356 |            -6.92 |            180 |                -10.04 |         140 |             -13.22 |             23.57 | -15.5038 |
| local_1h_break_accept  | ASIA_EVENING | ALL         | time4h_sl500         |       356 |           -11.64 |            180 |                 -9.56 |         140 |             -14.92 |             14.29 | -15.5261 |
| local_1h_break_accept  | ASIA_EVENING | ALL         | tp500_sl350_4h       |       356 |           -11.64 |            180 |                 -9.56 |         140 |             -14.92 |             14.29 | -15.5261 |
| overnight_accept       | US_OPEN      | WEEKDAYS    | tp1000_sl500_8h      |       172 |            -0.63 |             92 |                 -6.86 |          56 |             -10.33 |             25    | -15.561  |
| overnight_accept       | US_OPEN      | WEEKDAYS    | trail350_after500_8h |       172 |            -0.63 |             92 |                 -6.86 |          56 |             -10.33 |             25    | -15.561  |
| sweep_nextbar_confirm  | NY_EVENING   | FRI         | trail350_after500_8h |        42 |            -2.11 |             19 |                 -4.43 |          14 |             -14.19 |              7.14 | -15.5925 |
| sweep_nextbar_confirm  | NY_EVENING   | FRI         | tp1000_sl500_8h      |        42 |            -2.11 |             19 |                 -4.43 |          14 |             -14.19 |              7.14 | -15.5925 |
| local_2h_sweep_reject  | NY_EVENING   | FRI         | trail350_after500_8h |        40 |            -2.36 |             17 |                 -5.68 |          16 |             -10.15 |             18.75 | -15.6295 |
| local_2h_sweep_reject  | NY_EVENING   | FRI         | tp1000_sl500_8h      |        40 |            -2.36 |             17 |                 -5.68 |          16 |             -10.15 |             18.75 | -15.6295 |
| local_1h_break_accept  | ASIA_EVENING | SAT         | tp1000_sl500_8h      |        52 |            -5.22 |             26 |                 -1.64 |          20 |              -7.32 |             15    | -15.6871 |
| local_1h_break_accept  | ASIA_EVENING | SAT         | trail350_after500_8h |        52 |            -5.22 |             26 |                 -1.64 |          20 |              -7.32 |             15    | -15.6871 |
| opening30_sweep_reject | ASIA_EVENING | ALL         | time2h_sl400         |       179 |           -12.35 |             81 |                -11.63 |          70 |             -13.03 |             11.43 | -16.1663 |
| opening30_sweep_reject | ASIA_EVENING | ALL         | tp300_sl250_2h       |       179 |           -12.35 |             81 |                -11.63 |          70 |             -13.03 |             11.43 | -16.1663 |
| overnight_sweep_reject | ASIA_EVENING | SAT         | time2h_sl400         |        34 |            -8.21 |             15 |                -10.58 |          11 |             -15.44 |              0    | -16.1765 |
| overnight_sweep_reject | ASIA_EVENING | SAT         | tp300_sl250_2h       |        34 |            -8.21 |             15 |                -10.58 |          11 |             -15.44 |              0    | -16.1765 |
| local_2h_sweep_reject  | LONDON_EARLY | ALL         | tp300_sl250_2h       |       347 |           -13.1  |            173 |                -11.84 |         136 |             -12.83 |              9.56 | -16.1797 |
| local_2h_sweep_reject  | LONDON_EARLY | ALL         | time2h_sl400         |       347 |           -13.1  |            173 |                -11.84 |         136 |             -12.83 |              9.56 | -16.1797 |

## Interpretation
Look for agreement across all three chronological periods, sufficient sample sizes, and positive expectancy after costs; a high win rate alone is not an edge.
Repeated variants on the same date are correlated, and selected trade results do not prove institutional order flow.
Do NOT optimize using Jul-Oct data then label it out-of-sample; do not force daily trades.
This is research, not a live strategy or a promise of daily 200–500 points.

## Reproducibility
See scripts/research_price_action_time_day.py, price_action_signals.csv, all_exit_trades.csv, time_day_breakdown.csv and ranked_rules_preholdout.csv.
