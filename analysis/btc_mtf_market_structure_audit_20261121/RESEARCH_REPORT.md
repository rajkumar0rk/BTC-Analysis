# BTC 1H+4H market-state detector: present-state vs future-direction audit

## Precisely what is fixed
A trend is a measurable CURRENT market structure, not a forecast that every future 1H/4H close will continue up/down. This detector waits for the last completed 4H candle, requires alignment with a finished 1H signal, and leaves uncertain regimes explicitly unconfirmed. It distinguishes confirmed trend, breakout, shock, transition, compression, range and mixed markets; it does NOT force future direction trades.

## Quality checks
~~~json
{
  "source": "Delta India BTCUSD native 1M SHA256 checked against manifest",
  "native_minute_bars": 992160,
  "native_partitions": 23,
  "full_hours": 16536,
  "complete_ist_months": 22,
  "eligible_1h_with_known_closed_4h": 15851,
  "initial_warmup_unclassified_hours": 199,
  "timestamp_no_gaps": true,
  "all_1h_complete_60m": true,
  "all_4h_complete_240m": true,
  "unfinished_4h_used": false,
  "source_history_prefix_replays": [
    {
      "prefix_exclusive_utc": "2025-05-17T00:00:00Z",
      "hours": 3264,
      "revised_state_labels": 0,
      "revised_validity_flags": 0
    },
    {
      "prefix_exclusive_utc": "2025-12-19T00:00:00Z",
      "hours": 8448,
      "revised_state_labels": 0,
      "revised_validity_flags": 0
    },
    {
      "prefix_exclusive_utc": "2026-08-17T00:00:00Z",
      "hours": 14232,
      "revised_state_labels": 0,
      "revised_validity_flags": 0
    }
  ],
  "unchanged_prefix_history": true,
  "mixed_uncertain_share_pct": 58.034,
  "one_hour_label_switch_pct": 24.246,
  "confirmed_hours": 1971,
  "backward24h_reference_available_hours": 1902,
  "confirmed_trend_matches_past24h_direction_pct": 98.843,
  "independent_structure_reference": "current completed close minus close 24h earlier / current 1H ATR; if |value|>1, compare direction. Backward-looking price structure only, NOT true market-state accuracy.",
  "active_1h_up_hours": 2449,
  "active_1h_down_hours": 2581,
  "active_4h_up_hours": 2680,
  "active_4h_down_hours": 3036,
  "opposing_hourly_and_4h_trends": 13,
  "external_regime_ground_truth_available": false,
  "reliable_future_direction_demonstrated": false,
  "strategy_pnl_backtest_performed": false,
  "all_months_profitable_target_proved": false
}
~~~

## State shares across all 22 complete IST months
| state                |   hours |   share_pct |
|:---------------------|--------:|------------:|
| shock                |    1024 |       6.46  |
| confirmed_trend_up   |     941 |       5.937 |
| confirmed_trend_down |    1030 |       6.498 |
| breakout_up          |     381 |       2.404 |
| breakout_down        |     356 |       2.246 |
| transition           |       8 |       0.05  |
| compression          |    1074 |       6.776 |
| range                |    1838 |      11.595 |
| mixed_uncertain      |    9199 |      58.034 |

## How quickly each state changes
| state                |   runs |   median_consecutive_hours |   mean_consecutive_hours |
|:---------------------|-------:|---------------------------:|-------------------------:|
| breakout_down        |    251 |                          1 |                    1.418 |
| breakout_up          |    301 |                          1 |                    1.266 |
| compression          |    291 |                          3 |                    3.691 |
| confirmed_trend_down |    248 |                          3 |                    4.153 |
| confirmed_trend_up   |    224 |                          2 |                    4.201 |
| mixed_uncertain      |   1485 |                          3 |                    6.195 |
| range                |    506 |                          2 |                    3.632 |
| shock                |    532 |                          1 |                    1.925 |
| transition           |      6 |                          1 |                    1.333 |

## Year-specific trend and future continuation diagnostic (NOT ground-truth state accuracy)
|   year | state                |   horizon_hours |   nonoverlap_starts |   future_up_pct |   future_down_pct |   mean_future_return_ATR |   same_direction_followthrough_pct |
|-------:|:---------------------|----------------:|--------------------:|----------------:|------------------:|-------------------------:|-----------------------------------:|
|   2025 | confirmed_trend_up   |               4 |                 115 |          45.217 |            54.783 |                   0.151  |                             45.217 |
|   2025 | confirmed_trend_down |               4 |                 125 |          60     |            40     |                   0.1936 |                             40     |
|   2025 | breakout_up          |               4 |                  61 |          34.426 |            65.574 |                  -0.348  |                             34.426 |
|   2025 | breakout_down        |               4 |                  51 |          47.059 |            52.941 |                  -0.45   |                             52.941 |
|   2025 | range                |               4 |                 276 |          52.536 |            47.464 |                   0.0232 |                            nan     |
|   2025 | mixed_uncertain      |               4 |                1236 |          50.324 |            49.676 |                  -0.0108 |                            nan     |
|   2025 | confirmed_trend_up   |              12 |                  34 |          55.882 |            44.118 |                   0.3568 |                             55.882 |
|   2025 | confirmed_trend_down |              12 |                  42 |          64.286 |            35.714 |                   0.5986 |                             35.714 |
|   2025 | breakout_up          |              12 |                  17 |          52.941 |            47.059 |                  -0.0076 |                             52.941 |
|   2025 | breakout_down        |              12 |                  12 |          41.667 |            58.333 |                  -0.4902 |                             58.333 |
|   2025 | range                |              12 |                  91 |          45.055 |            54.945 |                  -0.3468 |                            nan     |
|   2025 | mixed_uncertain      |              12 |                 416 |          51.683 |            48.317 |                   0.0052 |                            nan     |
|   2026 | confirmed_trend_up   |               4 |                 123 |          41.463 |            58.537 |                  -0.1124 |                             41.463 |
|   2026 | confirmed_trend_down |               4 |                 127 |          49.606 |            50.394 |                  -0.1954 |                             50.394 |
|   2026 | breakout_up          |               4 |                  39 |          51.282 |            48.718 |                   0.0212 |                             51.282 |
|   2026 | breakout_down        |               4 |                  29 |          51.724 |            48.276 |                   0.0259 |                             48.276 |
|   2026 | range                |               4 |                 201 |          46.269 |            53.731 |                  -0.0679 |                            nan     |
|   2026 | mixed_uncertain      |               4 |                1087 |          50.966 |            49.034 |                   0.0308 |                            nan     |
|   2026 | confirmed_trend_up   |              12 |                  41 |          46.341 |            53.659 |                  -0.3111 |                             46.341 |
|   2026 | confirmed_trend_down |              12 |                  41 |          51.22  |            48.78  |                  -0.4386 |                             48.78  |
|   2026 | breakout_up          |              12 |                  12 |          41.667 |            58.333 |                   0.9411 |                             41.667 |
|   2026 | breakout_down        |              12 |                  11 |          45.455 |            54.545 |                  -0.4794 |                             54.545 |
|   2026 | range                |              12 |                  64 |          50     |            50     |                  -0.2194 |                            nan     |
|   2026 | mixed_uncertain      |              12 |                 350 |          52.857 |            47.143 |                  -0.0044 |                            nan     |

## Separate classification from profitable execution
A 4H trend confirmation is available only after its 4H bar has closed; the last 1H bar may enter a countertrend retracement while the 4H trend persists. State alignment with a past 24H directional price reference is a retrospective observation, NOT knowledge of what the next 4H candle will do.
No strategy trade was backtested here. Matching current structure does not establish directional edge or 22/22 profitable months. The existing models' after-cost PnL and forecasting failures remain valid unless new independent evidence contradicts them.

## Missing live-readiness inputs
Unobserved true market regime labels; historical L1/L2 order book and actual spread; funding cash settlements; margin/liquidation/exchange fill feasibility. No live strategy deployment and no main-branch merge.
