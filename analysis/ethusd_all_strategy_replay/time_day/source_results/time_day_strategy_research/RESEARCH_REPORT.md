# BTCUSD Futures: Time-based and day-of-week trading strategies

## What was tested
The real Delta India BTCUSD 1-minute candles, Jan 2025 through Oct 17 2026.
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
  "source": "Delta Exchange India BTCUSD perpetual native 1m",
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
  "positive_both_train_validation": 2486,
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
|         1 | THU         | 04:50           | clock_short |       480 |        52 |          821.226 |             26 |               855.653 |          20 |             53.171 |                50 |              314.265 |
|         2 | THU         | 04:35           | clock_short |       480 |        52 |          809.282 |             26 |               813.689 |          20 |             82.76  |                50 |              284.572 |
|         3 | THU         | 04:45           | clock_short |       480 |        52 |          793.04  |             26 |               815.389 |          20 |             65.415 |                50 |              283.511 |
|         4 | THU         | 04:40           | clock_short |       480 |        52 |          782.605 |             26 |               828.29  |          20 |             85.756 |                50 |              283.474 |
|         5 | THU         | 05:30           | clock_short |       480 |        52 |          862.481 |             26 |               870.034 |          20 |             -4.754 |                50 |              263.705 |
|         6 | THU         | 05:10           | clock_short |       480 |        52 |          817.999 |             26 |               825.93  |          20 |             78.855 |                50 |              262.217 |
|         7 | THU         | 05:05           | clock_short |       480 |        52 |          802.931 |             26 |               812.94  |          20 |             64.158 |                50 |              260.624 |
|         8 | THU         | 05:00           | clock_short |       480 |        52 |          786.613 |             26 |               868.018 |          20 |             75.009 |                55 |              258.812 |
|         9 | THU         | 05:20           | clock_short |       480 |        52 |          816.17  |             26 |               871.445 |          20 |              8.38  |                50 |              248.718 |
|        10 | THU         | 04:30           | clock_short |       480 |        52 |          760.537 |             26 |               772.446 |          20 |             72.563 |                50 |              245.337 |
|        11 | THU         | 04:20           | clock_short |       480 |        52 |          800.973 |             26 |               754.796 |          20 |              5.228 |                40 |              239.725 |
|        12 | THU         | 04:25           | clock_short |       480 |        52 |          767.114 |             26 |               732.025 |          20 |              9.931 |                45 |              236.044 |
|        13 | THU         | 04:55           | clock_short |       480 |        52 |          740.278 |             26 |               909.419 |          20 |             67.459 |                60 |              234.009 |
|        14 | THU         | 06:05           | clock_short |       480 |        52 |          885.109 |             26 |               805.425 |          20 |             95.196 |                50 |              233.302 |
|        15 | THU         | 05:25           | clock_short |       480 |        52 |          786.41  |             26 |               867.714 |          20 |             31.636 |                50 |              222.192 |
|        16 | THU         | 06:00           | clock_short |       480 |        52 |          839.218 |             26 |               812.297 |          20 |             38.651 |                45 |              221.989 |
|        17 | THU         | 05:35           | clock_short |       480 |        52 |          817.024 |             26 |               842.267 |          20 |            -30.467 |                45 |              217.383 |
|        18 | THU         | 05:15           | clock_short |       480 |        52 |          769.158 |             26 |               807.484 |          20 |             55.783 |                50 |              208.111 |
|        19 | THU         | 05:45           | clock_short |       480 |        52 |          799.437 |             26 |               809.377 |          20 |             -5.207 |                40 |              201.422 |
|        20 | THU         | 05:55           | clock_short |       480 |        52 |          851.02  |             26 |               801.622 |          20 |             43.055 |                45 |              186.243 |

## Protective stop retest of preselected rules (holdout only)
Below uses 500 BTC price point hard stop, time exit at chosen duration, no profit target. Exactly the same day/time/entry rules as above.
|   rule_id |   n |   avg_net |   median_net |   win_pct |
|----------:|----:|----------:|-------------:|----------:|
|         1 |  20 |    339.56 |      -337.58 |        45 |
|         2 |  20 |    316.68 |      -305.29 |        45 |
|         3 |  20 |    333.71 |      -338.27 |        45 |
|         4 |  20 |    316.38 |      -334.76 |        45 |
|         5 |  20 |    366.87 |        25.95 |        50 |
|         6 |  20 |    314.46 |      -342.45 |        45 |
|         7 |  20 |    335.68 |      -367.72 |        45 |
|         8 |  20 |    319.8  |      -310.28 |        45 |
|         9 |  20 |    293.5  |      -410.42 |        45 |
|        10 |  20 |    320.66 |      -289.82 |        45 |
|        11 |  20 |    277.45 |      -381.13 |        40 |
|        12 |  20 |    286.85 |      -304.52 |        45 |
|        13 |  20 |    325.09 |      -271.02 |        50 |
|        14 |  20 |    389.48 |      -107.73 |        50 |
|        15 |  20 |    318.7  |      -165.9  |        45 |
|        16 |  20 |    345.84 |      -136.36 |        45 |
|        17 |  20 |    367.5  |       -20.97 |        45 |
|        18 |  20 |    292.58 |      -416.02 |        45 |
|        19 |  20 |    316.62 |      -159.47 |        40 |
|        20 |  20 |    331.31 |      -168.66 |        45 |

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
