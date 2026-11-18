# ETHUSD Futures: Time-based and day-of-week trading strategies

## What was tested
The real Delta India ETHUSD 1-minute candles, Jan 2025 through Oct 17 2026.
Every five minutes in America/New_York, adjusted automatically for US daylight saving.
Day filters: each Monday–Sunday individually, all days, weekdays and weekends.
Entry variants: clock LONG, clock SHORT, prior completed 5m candle follow/fade, prior completed 15m candle follow/fade.
Holding durations: 15, 30, 60, 120, 240, 480 minutes. Signals are known at entry and never use future price information.
Each time-and-day rule has at most one signal in any New York calendar day. Weekend periods are included.
Fee model: both entries/exits taker 0.05% times 1.18 GST; slippage 5 BTC price points each side. No funding, spread/impact beyond modeled slippage, forced liquidation or position sizing.

## Chronological data separation and selection
TRAIN 2025, VALIDATION Jan-Jun 2026, holdout July 1–October 17 2026.
The HOLDOUT is NEVER used to pick a candidate or its stop/target. The many scans mean apparent positive results can be luck.
A positive finding must be robust to multiple comparisons, realistic protective stops, fee stress and new live-forward data before any capital deployment.
Every winning percentage is a historical outcome, NOT a daily guarantee.

## Data quality and multiple-tests warning
~~~json
{
  "source": "Delta Exchange India ETHUSD perpetual native 1m",
  "months": 23,
  "minute_candles": 987840,
  "utc_start": "2025-01-01 00:00:00+00:00",
  "utc_end": "2026-11-17 23:59:00+00:00",
  "zero_volume_candles": 1887,
  "evaluated_event_outcomes": 5503176,
  "periods": {
    "train": "2025",
    "validation": "Jan-Jun 2026",
    "holdout": "Jul-Oct 17 2026"
  },
  "eligible_rules": 80640,
  "positive_both_train_validation": 199,
  "strong_train_validation": 0,
  "final_candidates": 20,
  "tested_unique_rules": 80640,
  "selection": "Rank strictly on 2025 and Jan-Jun 2026. Holdout not used."
}
~~~

A conservative score is the WORSE 95%-style estimated lower mean bound in training and validation.
Normal-style standard errors use individual date events; they are NOT autocorrelation or volatility-regime adjusted. The stringent exploratory screen requires train z>3.5 and validation z>2.7 and is NOT a family-wise correction.

## Top rules selected exclusively on train+validation
|   rule_id | day_group   | ny_entry_time   | approach    |   minutes |   n_train |   mean_net_train |   n_validation |   mean_net_validation |   n_holdout |   mean_net_holdout |   win_pct_holdout |   conservative_score |
|----------:|:------------|:----------------|:------------|----------:|----------:|-----------------:|---------------:|----------------------:|------------:|-------------------:|------------------:|---------------------:|
|         1 | THU         | 04:50           | clock_short |       480 |        52 |           19.647 |             26 |                20.875 |          20 |             -7.747 |                40 |             1.56545  |
|         2 | THU         | 04:35           | clock_short |       480 |        52 |           19.221 |             26 |                19.378 |          20 |             -6.692 |                40 |             0.506428 |
|         3 | THU         | 04:45           | clock_short |       480 |        52 |           18.642 |             26 |                19.439 |          20 |             -7.31  |                45 |             0.468848 |
|         4 | THU         | 04:40           | clock_short |       480 |        52 |           18.269 |             26 |                19.899 |          20 |             -6.585 |                45 |             0.466722 |
|         5 | THU         | 05:30           | clock_short |       480 |        52 |           21.118 |             26 |                21.388 |          20 |             -9.813 |                35 |            -0.237602 |
|         6 | THU         | 05:10           | clock_short |       480 |        52 |           19.532 |             26 |                19.815 |          20 |             -6.831 |                35 |            -0.290722 |
|         7 | THU         | 05:05           | clock_short |       480 |        52 |           18.994 |             26 |                19.351 |          20 |             -7.355 |                40 |            -0.348235 |
|         8 | THU         | 05:00           | clock_short |       480 |        52 |           18.412 |             26 |                21.316 |          20 |             -6.968 |                40 |            -0.412829 |
|         9 | THU         | 05:20           | clock_short |       480 |        52 |           19.467 |             26 |                21.438 |          20 |             -9.344 |                35 |            -0.772072 |
|        10 | THU         | 04:30           | clock_short |       480 |        52 |           17.482 |             26 |                17.907 |          20 |             -7.055 |                45 |            -0.893418 |
|        11 | THU         | 04:20           | clock_short |       480 |        52 |           18.925 |             26 |                17.278 |          20 |             -9.457 |                35 |            -1.09274  |
|        12 | THU         | 04:25           | clock_short |       480 |        52 |           17.717 |             26 |                16.466 |          20 |             -9.289 |                35 |            -1.2244   |
|        13 | THU         | 04:55           | clock_short |       480 |        52 |           16.76  |             26 |                22.793 |          20 |             -7.237 |                40 |            -1.29686  |
|        14 | THU         | 06:05           | clock_short |       480 |        52 |           21.925 |             26 |                19.083 |          20 |             -6.248 |                35 |            -1.32264  |
|        15 | THU         | 05:25           | clock_short |       480 |        52 |           18.405 |             26 |                21.305 |          20 |             -8.515 |                35 |            -1.7187   |
|        16 | THU         | 06:00           | clock_short |       480 |        52 |           20.289 |             26 |                19.328 |          20 |             -8.265 |                40 |            -1.72624  |
|        17 | THU         | 05:35           | clock_short |       480 |        52 |           19.497 |             26 |                20.397 |          20 |            -10.73  |                35 |            -1.89047  |
|        18 | THU         | 05:15           | clock_short |       480 |        52 |           17.79  |             26 |                19.157 |          20 |             -7.654 |                40 |            -2.22059  |
|        19 | THU         | 05:45           | clock_short |       480 |        52 |           18.87  |             26 |                19.224 |          20 |             -9.829 |                35 |            -2.45963  |
|        20 | THU         | 05:55           | clock_short |       480 |        52 |           20.71  |             26 |                18.948 |          20 |             -8.108 |                35 |            -3.00045  |

## Protective stop retest of preselected rules (holdout only)
Below uses 500 BTC price point hard stop, time exit at chosen duration, no profit target. Exactly the same day/time/entry rules as above.
|   rule_id |   n |   avg_net |   median_net |   win_pct |
|----------:|----:|----------:|-------------:|----------:|
|         1 |  20 |     -7.75 |        -7.88 |        40 |
|         2 |  20 |     -6.69 |        -6.09 |        40 |
|         3 |  20 |     -7.31 |        -9.85 |        45 |
|         4 |  20 |     -6.58 |        -8.07 |        45 |
|         5 |  20 |     -9.81 |        -8.72 |        35 |
|         6 |  20 |     -6.83 |        -8.3  |        35 |
|         7 |  20 |     -7.36 |       -10.34 |        40 |
|         8 |  20 |     -6.97 |        -5.69 |        40 |
|         9 |  20 |     -9.34 |       -11.3  |        35 |
|        10 |  20 |     -7.06 |        -5.44 |        45 |
|        11 |  20 |     -9.46 |       -15.84 |        35 |
|        12 |  20 |     -9.29 |       -14.98 |        35 |
|        13 |  20 |     -7.24 |        -7.29 |        40 |
|        14 |  20 |     -6.25 |       -11.19 |        35 |
|        15 |  20 |     -8.51 |        -9.62 |        35 |
|        16 |  20 |     -8.26 |       -12.49 |        40 |
|        17 |  20 |    -10.73 |       -10.39 |        35 |
|        18 |  20 |     -7.65 |        -8.97 |        40 |
|        19 |  20 |     -9.83 |       -14.49 |        35 |
|        20 |  20 |     -8.11 |       -13.76 |        35 |

Other stops (250, 500, 800) and targets (none, 500, 1000) are reported in selected_rule_stop_target_summary.csv. Intraminute stop/target ambiguity is assigned to STOP first.
Do NOT choose the best result from these holdout stop variants and then claim a genuinely untouched test.

## Files
- all_time_day_rules.csv: every weekday/clock/entry/hold evaluated (including negative ones).
- eligible_ranked_by_preholdout.csv: ordered using only earlier data.
- hourly_weekday_baselines.csv: the honest full weekly clock context.
- preselected_candidates.csv: candidates selected before holdout.
- selected_rule_stop_trades.csv / selected_rule_stop_target_summary.csv: 1m path-aware protective-stop replay.

## Interpretation
Constant entry based on clock/day does not know market direction, and following/fading one 5m/15m candle remains a simplistic proxy.
These are exploratory strategies, not identification of institutional orders or actual resting liquidity.
A day may have a 500+ point high-low range yet have no profitable time entry.
Fixed time exits without stops are diagnostic only; evaluate path-aware protective stops before contemplating live orders.
