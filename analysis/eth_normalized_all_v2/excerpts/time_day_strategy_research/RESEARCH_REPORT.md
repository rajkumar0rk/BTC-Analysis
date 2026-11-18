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
  "months": 22,
  "minute_candles": 963360,
  "utc_start": "2025-01-01 00:00:00+00:00",
  "utc_end": "2026-10-31 23:59:00+00:00",
  "zero_volume_candles": 1887,
  "evaluated_event_outcomes": 5366724,
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
|         1 | THU         | 04:50           | clock_short |       480 |        52 |          821.226 |             26 |               855.653 |          18 |           -229.532 |             44.44 |              314.265 |
|         2 | THU         | 04:35           | clock_short |       480 |        52 |          809.282 |             26 |               813.689 |          18 |           -198.601 |             44.44 |              284.572 |
|         3 | THU         | 04:45           | clock_short |       480 |        52 |          793.04  |             26 |               815.389 |          18 |           -223.801 |             44.44 |              283.511 |
|         4 | THU         | 04:40           | clock_short |       480 |        52 |          782.605 |             26 |               828.29  |          18 |           -204.391 |             44.44 |              283.474 |
|         5 | THU         | 05:30           | clock_short |       480 |        52 |          862.481 |             26 |               870.034 |          18 |           -297.229 |             44.44 |              263.705 |
|         6 | THU         | 05:10           | clock_short |       480 |        52 |          817.999 |             26 |               825.93  |          18 |           -207.15  |             44.44 |              262.217 |
|         7 | THU         | 05:05           | clock_short |       480 |        52 |          802.931 |             26 |               812.94  |          18 |           -232.75  |             44.44 |              260.624 |
|         8 | THU         | 05:00           | clock_short |       480 |        52 |          786.613 |             26 |               868.018 |          18 |           -211.646 |             50    |              258.812 |
|         9 | THU         | 05:20           | clock_short |       480 |        52 |          816.17  |             26 |               871.445 |          18 |           -285.368 |             44.44 |              248.718 |
|        10 | THU         | 04:30           | clock_short |       480 |        52 |          760.537 |             26 |               772.446 |          18 |           -210.714 |             44.44 |              245.337 |
|        11 | THU         | 04:20           | clock_short |       480 |        52 |          800.973 |             26 |               754.796 |          18 |           -279.769 |             33.33 |              239.725 |
|        12 | THU         | 04:25           | clock_short |       480 |        52 |          767.114 |             26 |               732.025 |          18 |           -274.935 |             38.89 |              236.044 |
|        13 | THU         | 04:55           | clock_short |       480 |        52 |          740.278 |             26 |               909.419 |          18 |           -210.222 |             55.56 |              234.009 |
|        14 | THU         | 06:05           | clock_short |       480 |        52 |          885.109 |             26 |               805.425 |          18 |           -212.129 |             44.44 |              233.302 |
|        15 | THU         | 05:25           | clock_short |       480 |        52 |          786.41  |             26 |               867.714 |          18 |           -271.441 |             44.44 |              222.192 |
|        16 | THU         | 06:00           | clock_short |       480 |        52 |          839.218 |             26 |               812.297 |          18 |           -252.128 |             38.89 |              221.989 |
|        17 | THU         | 05:35           | clock_short |       480 |        52 |          817.024 |             26 |               842.267 |          18 |           -333.902 |             38.89 |              217.383 |
|        18 | THU         | 05:15           | clock_short |       480 |        52 |          769.158 |             26 |               807.484 |          18 |           -217.899 |             44.44 |              208.111 |
|        19 | THU         | 05:45           | clock_short |       480 |        52 |          799.437 |             26 |               809.377 |          18 |           -305.137 |             33.33 |              201.422 |
|        20 | THU         | 05:55           | clock_short |       480 |        52 |          851.02  |             26 |               801.622 |          18 |           -248.56  |             38.89 |              186.243 |

## Protective stop retest of preselected rules (holdout only)
Below uses 500 BTC price point hard stop, time exit at chosen duration, no profit target. Exactly the same day/time/entry rules as above.
|   rule_id |   n |   avg_net |   median_net |   win_pct |
|----------:|----:|----------:|-------------:|----------:|
|         1 |  18 |     88.67 |      -568.82 |     38.89 |
|         2 |  18 |     61.32 |      -568.79 |     38.89 |
|         3 |  18 |     74.3  |      -568.82 |     38.89 |
|         4 |  18 |     51.86 |      -568.79 |     38.89 |
|         5 |  18 |    115.69 |      -167.3  |     44.44 |
|         6 |  18 |     54.64 |      -568.78 |     38.89 |
|         7 |  18 |     68.94 |      -568.82 |     38.89 |
|         8 |  18 |     60.35 |      -568.83 |     38.89 |
|         9 |  18 |     31.44 |      -568.83 |     38.89 |
|        10 |  18 |     64.94 |      -568.73 |     38.89 |
|        11 |  18 |     22.7  |      -568.13 |     33.33 |
|        12 |  18 |     32.75 |      -568.67 |     38.89 |
|        13 |  18 |     76.03 |      -568.83 |     44.44 |
|        14 |  18 |    114.86 |      -411.39 |     44.44 |
|        15 |  18 |     47.52 |      -371.94 |     38.89 |
|        16 |  18 |     89.2  |      -410.74 |     38.89 |
|        17 |  18 |    108.29 |      -145.58 |     38.89 |
|        18 |  18 |     45.21 |      -568.85 |     38.89 |
|        19 |  18 |     52.45 |      -344.9  |     33.33 |
|        20 |  18 |     71.73 |      -403    |     38.89 |

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
