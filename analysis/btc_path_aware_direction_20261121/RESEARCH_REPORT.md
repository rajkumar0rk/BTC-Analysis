# BTC event-conditioned direction meta-forecast and 1M trade replay

## Audit and hypothesis
Prior unconditional 4H UP/DOWN predictor was no better than chance in 2026; event-conditional future-close direction showed a 58.33% hit rate on accepted evaluation events but still lost 27.32% after costs. This study fixes the **target mismatch**: past-only monthly classifier predicts whether a confirmed event side would have produced positive net R under conservative 1M stop-first fills, including fee/GST/slippage. Each hypothetical label is released ONLY after the exit minute is finished, never before monthly training cutoff. This is a precommitted differential, not an optimized TP/SL search.

## Data integrity
~~~json
{
  "source": "Delta India BTCUSD futures, original SHA256 verified 1M candles",
  "native_minutes": 992160,
  "source_partitions": 23,
  "evaluated_complete_months": 16,
  "total_complete_ist_months": 22,
  "training_months": 6,
  "model_threshold": 0.5,
  "label_horizon": "native 1M stop-first event exit and net-after-fee R, released after exit minute",
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

## Path-aware profitable exit prediction, event signals sampled nonoverlapping each 4 UTC hours
| period     | model                         |   events |   actual_net_win_rate_pct |   model_accuracy_pct |   model_balanced_accuracy_pct |   direction_auc |   brier_score |   forecast_logloss |   acceptance_events |   acceptance_coverage_pct |   accepted_isolated_net_win_pct |
|:-----------|:------------------------------|---------:|--------------------------:|---------------------:|------------------------------:|----------------:|--------------:|-------------------:|--------------------:|--------------------------:|--------------------------------:|
| 2025H2     | boosted                       |      229 |                    34.934 |               62.445 |                        50.881 |          0.5503 |       0.23162 |            0.65682 |                  26 |                     11.35 |                          38.462 |
| 2025H2     | logistic                      |      229 |                    34.934 |               63.755 |                        50.44  |          0.5137 |       0.23222 |            0.65775 |                  13 |                      5.68 |                          38.462 |
| 2025H2     | trained_event_prior           |      229 |                    34.934 |               65.066 |                        50     |          0.4961 |       0.22811 |            0.64878 |                   0 |                      0    |                         nan     |
| 2025H2     | always_follow_confirmed_event |      229 |                    34.934 |               34.934 |                       nan     |        nan      |     nan       |          nan       |                 229 |                    100    |                          34.934 |
| 2026JanOct | boosted                       |      331 |                    34.441 |               63.746 |                        49.867 |          0.5247 |       0.22906 |            0.65014 |                  18 |                      5.44 |                          33.333 |
| 2026JanOct | logistic                      |      331 |                    34.441 |               64.653 |                        49.309 |          0.5227 |       0.22859 |            0.64945 |                   3 |                      0.91 |                           0     |
| 2026JanOct | trained_event_prior           |      331 |                    34.441 |               65.559 |                        50     |          0.5427 |       0.22644 |            0.64532 |                   0 |                      0    |                         nan     |
| 2026JanOct | always_follow_confirmed_event |      331 |                    34.441 |               34.441 |                       nan     |        nan      |     nan       |          nan       |                 331 |                    100    |                          34.441 |
| combined   | boosted                       |      560 |                    34.643 |               63.214 |                        50.299 |          0.5389 |       0.23011 |            0.65287 |                  44 |                      7.86 |                          36.364 |
| combined   | logistic                      |      560 |                    34.643 |               64.286 |                        49.786 |          0.5187 |       0.23008 |            0.65284 |                  16 |                      2.86 |                          31.25  |
| combined   | trained_event_prior           |      560 |                    34.643 |               65.357 |                        50     |          0.5276 |       0.22712 |            0.64674 |                   0 |                      0    |                         nan     |
| combined   | always_follow_confirmed_event |      560 |                    34.643 |               34.643 |                       nan     |        nan      |     nan       |          nan       |                 560 |                    100    |                          34.643 |

## Independently replayed account comparison (same 1M fills, global one position per account)
| model            |   events_candidate |   trades |   wins |   win_rate_pct |   profit_factor |   net_return_pct |   net_usd |   max_trade_close_drawdown_pct |   fees_gst_usd |   slippage_usd |   profitable_months |   losing_months |   idle_months | is_22_of_22   |
|:-----------------|-------------------:|---------:|-------:|---------------:|----------------:|-----------------:|----------:|-------------------------------:|---------------:|---------------:|--------------------:|----------------:|--------------:|:--------------|
| event_baseline   |               2304 |     1085 |    405 |          37.33 |          0.7628 |         -60.1432 |  -6014.32 |                         61.879 |        6823.61 |         663.9  |                   2 |              14 |             6 | False         |
| conditional_meta |               2304 |      140 |     50 |          35.71 |          0.5301 |         -20.5727 |  -2057.27 |                         20.573 |        1100.91 |         104.13 |                   5 |              11 |             6 | False         |

## Net returns for all 22 calendar months (including six first training idle)
| month_ist   |   conditional_meta |   event_baseline |
|:------------|-------------------:|-----------------:|
| 2025-01     |              0     |            0     |
| 2025-02     |              0     |            0     |
| 2025-03     |              0     |            0     |
| 2025-04     |              0     |            0     |
| 2025-05     |              0     |            0     |
| 2025-06     |              0     |            0     |
| 2025-07     |             -0.978 |           -3.415 |
| 2025-08     |             -4.369 |           -6.751 |
| 2025-09     |             -1.674 |          -11.665 |
| 2025-10     |             -0.974 |            0.196 |
| 2025-11     |             -0.724 |           -2.83  |
| 2025-12     |              2.065 |           -4.706 |
| 2026-01     |             -5.425 |            2.346 |
| 2026-02     |             -2.698 |           -4.719 |
| 2026-03     |              0.062 |           -4.835 |
| 2026-04     |             -3.296 |           -9.54  |
| 2026-05     |              0.588 |           -3.628 |
| 2026-06     |             -1.488 |           -6.292 |
| 2026-07     |              0.787 |           -5.974 |
| 2026-08     |             -1.84  |          -13.076 |
| 2026-09     |              0.039 |           -5.373 |
| 2026-10     |             -2.647 |           -7.907 |

## Important limitations
- Model observes only past hourly OHLCV indicators and the completed 1H setup, never the forward native 1M path or trade result. Training excludes events until their entire hypothetical exit is completed.
- Isolated-event net-win probability is NOT the same as single-account portfolio win rate; blocked overlapping entries change the executed sample. Both are independently reported.
- The all-event benchmark uses the same exclusive 1M execution and Jan-Jun 2025 initial idle period.
- Historical 2025-2026 research has been explored; chronological monthly validation is not pristine untouched external holdout.
- Excluded funding cash flows, real spreads/orderbook, liquidation, latency and contract rounding. Assumed taker .05% per side + GST 18%, $5 adverse price-point slip per leg.
- No live trading or guarantees. A failed model must not be promoted or described as reliable by selecting only its best-looking historical month.
