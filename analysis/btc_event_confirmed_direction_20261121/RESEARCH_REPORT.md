# BTC event-conditioned direction meta-forecast and 1M trade replay

## Audit and hypothesis
The previous unconditional 4H direction predictor failed on 2026 (49.62% for boosted price-only). This test is NOT a re-run of unconditional UP/DOWN; instead a completed 1H breakout, failed sweep or displacement nominates a direction, and a past-only monthly classifier estimates P(4H follows that **event-side**). If the model is not confident, abstain. Model assumptions precommitted in NOVELTY_CHECK.md.

## Data integrity
~~~json
{
  "source": "Delta India BTCUSD futures, original SHA256 verified 1M candles",
  "native_minutes": 992160,
  "source_partitions": 23,
  "evaluated_complete_months": 16,
  "total_complete_ist_months": 22,
  "training_months": 6,
  "model_threshold": 0.6,
  "label_horizon": "event-side future completed 4H close direction, release t+5H",
  "event_family_order": [
    "24h_breakout",
    "24h_failed_sweep",
    "displacement"
  ],
  "all_models_fitted_before_evaluation_month": true,
  "next_1m_open_no_lookahead": true,
  "stops_first_on_1m_both_touch": true,
  "real_orderbook_spread_available": false,
  "realized_funding_included": false,
  "exchange_contract_margin_accurate": false,
  "blind_holdout_2026": false
}
~~~

## Direction forecasts after confirmed events, nonoverlap every 4 UTC hours
| period     | model                         |   events |   actual_continuation_rate_pct |   model_accuracy_pct |   model_balanced_accuracy_pct |   direction_auc |   brier_score |   forecast_logloss |   acceptance_events |   acceptance_coverage_pct |   accepted_continuation_hit_pct |
|:-----------|:------------------------------|---------:|-------------------------------:|---------------------:|------------------------------:|----------------:|--------------:|-------------------:|--------------------:|--------------------------:|--------------------------------:|
| 2025H2     | boosted                       |      229 |                         49.782 |               52.402 |                        52.422 |          0.5301 |       0.25457 |            0.70277 |                  36 |                     15.72 |                          55.556 |
| 2025H2     | logistic                      |      229 |                         49.782 |               49.345 |                        49.352 |          0.487  |       0.25976 |            0.71334 |                  30 |                     13.1  |                          40     |
| 2025H2     | trained_event_prior           |      229 |                         49.782 |               49.782 |                        50     |          0.5205 |       0.24996 |            0.69306 |                   0 |                      0    |                         nan     |
| 2025H2     | always_follow_confirmed_event |      229 |                         49.782 |               49.782 |                       nan     |        nan      |     nan       |          nan       |                 229 |                    100    |                          49.782 |
| 2026JanOct | boosted                       |      331 |                         52.266 |               52.87  |                        52.746 |          0.5438 |       0.25252 |            0.699   |                  48 |                     14.5  |                          60.417 |
| 2026JanOct | logistic                      |      331 |                         52.266 |               54.079 |                        54.039 |          0.5537 |       0.24843 |            0.69006 |                  22 |                      6.65 |                          54.545 |
| 2026JanOct | trained_event_prior           |      331 |                         52.266 |               50.453 |                        49.281 |          0.5296 |       0.24978 |            0.69271 |                   0 |                      0    |                         nan     |
| 2026JanOct | always_follow_confirmed_event |      331 |                         52.266 |               52.266 |                       nan     |        nan      |     nan       |          nan       |                 331 |                    100    |                          52.266 |
| combined   | boosted                       |      560 |                         51.25  |               52.679 |                        52.591 |          0.5371 |       0.25336 |            0.70054 |                  84 |                     15    |                          58.333 |
| combined   | logistic                      |      560 |                         51.25  |               52.143 |                        52.113 |          0.5223 |       0.25307 |            0.69958 |                  52 |                      9.29 |                          46.154 |
| combined   | trained_event_prior           |      560 |                         51.25  |               50.179 |                        49.285 |          0.5179 |       0.24985 |            0.69285 |                   0 |                      0    |                         nan     |
| combined   | always_follow_confirmed_event |      560 |                         51.25  |               51.25  |                       nan     |        nan      |     nan       |          nan       |                 560 |                    100    |                          51.25  |

## Independently replayed account comparison (same 1M fills, global one position per account)
| model            |   events_candidate |   trades |   wins |   win_rate_pct |   profit_factor |   net_return_pct |   net_usd |   max_trade_close_drawdown_pct |   fees_gst_usd |   slippage_usd |   profitable_months |   losing_months |   idle_months | is_22_of_22   |
|:-----------------|-------------------:|---------:|-------:|---------------:|----------------:|-----------------:|----------:|-------------------------------:|---------------:|---------------:|--------------------:|----------------:|--------------:|:--------------|
| event_baseline   |               2304 |     1085 |    405 |          37.33 |          0.7628 |         -60.1432 |  -6014.32 |                         61.879 |        6823.61 |         663.9  |                   2 |              14 |             6 | False         |
| conditional_meta |               2304 |      262 |     99 |          37.79 |          0.6587 |         -27.3152 |  -2731.52 |                         29.361 |        2220.25 |         215.99 |                   4 |              12 |             6 | False         |

## Net returns for all 22 calendar months (including six first training idle)
| month_ist   |   conditional_meta |   event_baseline |
|:------------|-------------------:|-----------------:|
| 2025-01     |              0     |            0     |
| 2025-02     |              0     |            0     |
| 2025-03     |              0     |            0     |
| 2025-04     |              0     |            0     |
| 2025-05     |              0     |            0     |
| 2025-06     |              0     |            0     |
| 2025-07     |             -0.161 |           -3.415 |
| 2025-08     |              1.769 |           -6.751 |
| 2025-09     |             -4.123 |          -11.665 |
| 2025-10     |             -2.144 |            0.196 |
| 2025-11     |             -7.028 |           -2.83  |
| 2025-12     |              1.4   |           -4.706 |
| 2026-01     |             -0.963 |            2.346 |
| 2026-02     |              0.453 |           -4.719 |
| 2026-03     |             -2.606 |           -4.835 |
| 2026-04     |             -6.175 |           -9.54  |
| 2026-05     |             -0.575 |           -3.628 |
| 2026-06     |             -2.497 |           -6.292 |
| 2026-07     |             -0.657 |           -5.974 |
| 2026-08     |             -2.265 |          -13.076 |
| 2026-09     |              0.114 |           -5.373 |
| 2026-10     |             -5.587 |           -7.907 |

## Important limitations
- Model observes only past hourly OHLCV indicators and the completed 1H setup, never the next 4H outcome or trade result.
- Normalized 4H event continuation hit percentage is NOT the same as win rate on stop-first trades; both are independently reported.
- The all-event benchmark uses the same exclusive 1M execution and Jan-Jun 2025 initial idle period.
- Historical 2025-2026 research has been explored; chronological monthly validation is not pristine untouched external holdout.
- Excluded funding cash flows, real spreads/orderbook, liquidation, latency and contract rounding. Assumed taker .05% per side + GST 18%, $5 adverse price-point slip per leg.
- No live trading or guarantees. A failed model must not be promoted or described as reliable by selecting only its best-looking historical month.
