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
  "months": 22,
  "minute_candles": 943200,
  "utc_start": "2025-01-01 00:00:00+00:00",
  "utc_end": "2026-10-17 23:59:00+00:00",
  "zero_volume_candles": 1819,
  "evaluated_event_outcomes": 5262456,
  "periods": {
    "train": "2025",
    "validation": "Jan-Jun 2026",
    "holdout": "Jul-Oct 17 2026"
  },
  "eligible_rules": 80640,
  "positive_both_train_validation": 1277,
  "strong_train_validation": 0,
  "final_candidates": 20,
  "tested_unique_rules": 80640,
  "selection": "Rank strictly on 2025 and Jan-Jun 2026. Holdout not used."
}
~~~

A conservative score is the WORSE 95%-style estimated lower mean bound in training and validation.
Normal-style standard errors use individual date events; they are NOT autocorrelation or volatility-regime adjusted. The stringent exploratory screen requires train z>3.5 and validation z>2.7 and is NOT a family-wise correction.

## Top rules selected exclusively on train+validation
|   rule_id | day_group   | ny_entry_time   | approach      |   minutes |   n_train |   mean_net_train |   n_validation |   mean_net_validation |   n_holdout |   mean_net_holdout |   win_pct_holdout |   conservative_score |
|----------:|:------------|:----------------|:--------------|----------:|----------:|-----------------:|---------------:|----------------------:|------------:|-------------------:|------------------:|---------------------:|
|         1 | THU         | 23:10           | prior5_follow |       480 |        52 |          343.263 |             26 |               369.551 |          16 |           -324.166 |             50    |              28.1345 |
|         2 | THU         | 05:20           | clock_short   |       480 |        52 |          448.301 |             26 |               629.322 |          16 |           -425.866 |             31.25 |             -10.4034 |
|         3 | MON         | 18:25           | clock_short   |       480 |        52 |          336.532 |             26 |               252.214 |          15 |            -27.008 |             40    |             -16.7796 |
|         4 | THU         | 06:10           | clock_short   |       240 |        52 |          213.86  |             26 |               376.704 |          16 |           -160.949 |             37.5  |             -17.4193 |
|         5 | THU         | 06:15           | clock_short   |       240 |        52 |          207.638 |             26 |               410.505 |          16 |           -191.546 |             43.75 |             -17.5327 |
|         6 | THU         | 05:30           | clock_short   |       480 |        52 |          483.606 |             26 |               613.493 |          16 |           -420.337 |             25    |             -24.1428 |
|         7 | MON         | 18:20           | clock_short   |       480 |        52 |          296.221 |             26 |               260.158 |          15 |             14.71  |             40    |             -27.7372 |
|         8 | THU         | 06:05           | clock_short   |       480 |        52 |          464.167 |             26 |               563.113 |          16 |           -354.646 |             31.25 |             -30.6806 |
|         9 | MON         | 08:45           | prior15_fade  |       240 |        51 |          386.735 |             26 |               382.515 |          15 |            -58.539 |             46.67 |             -33.7279 |
|        10 | THU         | 05:25           | clock_short   |       480 |        52 |          436.654 |             26 |               613.771 |          16 |           -399.41  |             31.25 |             -33.7764 |
|        11 | WED         | 17:25           | prior5_fade   |       480 |        53 |          272.407 |             24 |               486.03  |          15 |             69.296 |             53.33 |             -35.3387 |
|        12 | THU         | 04:50           | clock_short   |       480 |        52 |          384.243 |             26 |               572.981 |          16 |           -417.789 |             37.5  |             -41.7334 |
|        13 | THU         | 05:10           | clock_short   |       480 |        52 |          394.655 |             26 |               579.814 |          16 |           -372.701 |             37.5  |             -45.1884 |
|        14 | THU         | 04:40           | clock_short   |       480 |        52 |          370.13  |             26 |               546.852 |          16 |           -347.225 |             37.5  |             -45.3123 |
|        15 | THU         | 05:15           | clock_short   |       480 |        52 |          395.039 |             26 |               572.558 |          16 |           -384.59  |             31.25 |             -45.3454 |
|        16 | TUE         | 15:45           | prior15_fade  |       240 |        51 |          182.158 |             26 |               290.847 |          15 |            -21.005 |             46.67 |             -47.0261 |
|        17 | MON         | 18:50           | clock_short   |       480 |        52 |          318.824 |             26 |               228.44  |          15 |           -109.502 |             40    |             -47.5373 |
|        18 | MON         | 18:45           | clock_short   |       480 |        52 |          358.006 |             26 |               216.606 |          15 |           -129.42  |             40    |             -47.6015 |
|        19 | MON         | 17:50           | clock_short   |       480 |        52 |          304.05  |             26 |               255.26  |          15 |              4.115 |             46.67 |             -50.3802 |
|        20 | MON         | 18:55           | clock_short   |       480 |        52 |          331.696 |             26 |               219.734 |          15 |           -112.984 |             46.67 |             -50.671  |

## Protective stop retest of preselected rules (holdout only)
Below uses 500 BTC price point hard stop, time exit at chosen duration, no profit target. Exactly the same day/time/entry rules as above.
|   rule_id |   n |   avg_net |   median_net |   win_pct |
|----------:|----:|----------:|-------------:|----------:|
|         1 |  16 |   -180.34 |      -486.02 |     43.75 |
|         2 |  16 |   -108.93 |      -586.1  |     31.25 |
|         3 |  15 |    111.97 |      -105.37 |     40    |
|         4 |  16 |   -134.15 |      -335.76 |     37.5  |
|         5 |  16 |   -103.12 |      -144.71 |     43.75 |
|         6 |  16 |    -86.64 |      -466.2  |     25    |
|         7 |  15 |    130.58 |       -57.83 |     40    |
|         8 |  16 |   -115.82 |      -586.2  |     31.25 |
|         9 |  15 |   -148.85 |      -585.91 |     26.67 |
|        10 |  16 |    -85.13 |      -583.82 |     31.25 |
|        11 |  15 |    -72.98 |       -45.42 |     46.67 |
|        12 |  16 |   -107.61 |      -586.08 |     37.5  |
|        13 |  16 |   -104.14 |      -586.07 |     37.5  |
|        14 |  16 |   -122.19 |      -586.13 |     37.5  |
|        15 |  16 |    -93.89 |      -583.78 |     31.25 |
|        16 |  15 |    -63.38 |       -25.88 |     46.67 |
|        17 |  15 |    -70.38 |      -505.74 |     33.33 |
|        18 |  15 |    -71.89 |      -524.72 |     33.33 |
|        19 |  15 |    115.01 |       -57.35 |     46.67 |
|        20 |  15 |    -82.57 |      -568.29 |     40    |

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
