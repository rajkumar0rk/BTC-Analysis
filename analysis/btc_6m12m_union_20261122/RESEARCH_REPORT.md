# Combined BTC four-layer 6M + 12M protected monthly results

## Correct definition of combined
UNION means ONE BTCUSD account, one active position, each shared eligible signal executed once, and equity/size/PnL recalculated sequentially on native 1M candles. It is NOT (6M return + 12M return), nor two independent accounts' returns averaged. For completeness INTERSECTION means trade only when both past-only 6M and past-only 12M filters agree. No historical best-month switching.

## Quality & provenance
~~~json
{
  "models": [
    "six_only",
    "twelve_only",
    "union_6m12m",
    "intersection_6m12m"
  ],
  "complete_IST_months": 22,
  "source": "Delta India BTCUSD SHA256 verified native 1M",
  "native_1m_candles": 992160,
  "source_partitions": 23,
  "confirmed_first_15m_events": 513,
  "six_month_eligible_unique_signals": 85,
  "twelve_month_eligible_unique_signals": 80,
  "common_signals_deduplicated": 70,
  "union_eligible_unique_signals": 95,
  "union_equals_set_sum_minus_intersection": true,
  "standalone_six_month_protected_trade_parity": true,
  "standalone_twelve_month_protected_trade_parity": true,
  "two_filters_enter_once_when_same_signal": true,
  "independent_single_combined_account": true,
  "one_position_globally_at_a_time": true,
  "original_fixed_15m_confirmation_and_next_1m_entry": true,
  "no_synthetic_signal_from_future_month_pnl": true,
  "same_protected_stop_exit_rules_for_all_variants": true,
  "native_1m_stop_first_and_next_bar_stop_updates": true,
  "fees_GST_slippage_accounted_as_original_assumptions": true,
  "actual_funding_cash_or_historical_orderbook_spread_present": false,
  "liquidation_or_contract_rounding_modelled": false,
  "external_untouched_prospective_holdout": false,
  "approved_for_live_trading": false
}
~~~

## Combined vs individual performance
| model              |   candidate_events |   exclusive_position_rejections |   entry_unavailable |   executed_trades |   trades_activated |   post_bar_stop_updates |   trades |   wins |   win_rate_pct |   profit_factor |   net_return_pct |   net_profit_usd |   ending_equity_usd |   max_trade_close_drawdown_pct |   fees_gst_usd |   slippage_usd |   profitable_months |   losing_months |   idle_months | passes_22_22   |
|:-------------------|-------------------:|--------------------------------:|--------------------:|------------------:|-------------------:|------------------------:|---------:|-------:|---------------:|----------------:|-----------------:|-----------------:|--------------------:|-------------------------------:|---------------:|---------------:|--------------------:|----------------:|--------------:|:---------------|
| six_only           |                 85 |                              30 |                   0 |                55 |                 23 |                      23 |       55 |     22 |         40     |          1.2833 |           4.8154 |           481.54 |             10481.5 |                          4.864 |         324.72 |          36.22 |                   7 |               5 |            10 | False          |
| twelve_only        |                 80 |                              29 |                   0 |                51 |                 23 |                      23 |       51 |     23 |         45.098 |          1.6135 |           9.207  |           920.7  |             10920.7 |                          4.864 |         311.42 |          35.93 |                   7 |               3 |            12 | False          |
| union_6m12m        |                 95 |                              34 |                   0 |                61 |                 25 |                      25 |       61 |     25 |         40.984 |          1.327  |           6.1494 |           614.94 |             10614.9 |                          4.864 |         359.89 |          39.73 |                   7 |               5 |            10 | False          |
| intersection_6m12m |                 70 |                              25 |                   0 |                45 |                 21 |                      21 |       45 |     20 |         44.444 |          1.596  |           7.8346 |           783.46 |             10783.5 |                          4.864 |         275.24 |          32.32 |                   7 |               3 |            12 | False          |

## All 22 IST months — individually compounded account return %
| month_ist   |   intersection_6m12m |   six_only |   twelve_only |   union_6m12m |
|:------------|---------------------:|-----------:|--------------:|--------------:|
| 2025-01     |                0     |      0     |         0     |         0     |
| 2025-02     |                0     |      0     |         0     |         0     |
| 2025-03     |                0     |      0     |         0     |         0     |
| 2025-04     |                0     |      0     |         0     |         0     |
| 2025-05     |                0     |      0     |         0     |         0     |
| 2025-06     |                0     |      0     |         0     |         0     |
| 2025-07     |                0     |      0     |         0     |         0     |
| 2025-08     |                0     |     -2.292 |         0     |        -2.292 |
| 2025-09     |                0     |      0     |         0     |         0     |
| 2025-10     |                0     |      0     |         0     |         0     |
| 2025-11     |                0     |      0     |         0     |         0     |
| 2025-12     |                0     |     -0.52  |         0     |        -0.52  |
| 2026-01     |                1.23  |      1.23  |         2.518 |         2.518 |
| 2026-02     |                4.224 |      4.224 |         4.224 |         4.224 |
| 2026-03     |                1.872 |      1.872 |         1.872 |         1.872 |
| 2026-04     |               -3.15  |     -3.15  |        -3.15  |        -3.15  |
| 2026-05     |                1.052 |      1.052 |         1.052 |         1.052 |
| 2026-06     |                2.34  |      2.34  |         2.34  |         2.34  |
| 2026-07     |               -1.15  |     -1.15  |        -1.15  |        -1.15  |
| 2026-08     |                1.686 |      1.686 |         1.686 |         1.686 |
| 2026-09     |                1.446 |      1.446 |         1.446 |         1.446 |
| 2026-10     |               -1.766 |     -1.766 |        -1.766 |        -1.766 |

## Yearly account performance
| model              |   year |   months |   trades |   profitable_months |   losing_months |   idle_months |   compounded_net_pct |
|:-------------------|-------:|---------:|---------:|--------------------:|----------------:|--------------:|---------------------:|
| six_only           |   2025 |       12 |       10 |                   0 |               2 |            10 |             -2.79986 |
| six_only           |   2026 |       10 |       45 |                   7 |               3 |             0 |              7.83457 |
| twelve_only        |   2025 |       12 |        0 |                   0 |               0 |            12 |              0       |
| twelve_only        |   2026 |       10 |       51 |                   7 |               3 |             0 |              9.20704 |
| union_6m12m        |   2025 |       12 |       10 |                   0 |               2 |            10 |             -2.79986 |
| union_6m12m        |   2026 |       10 |       51 |                   7 |               3 |             0 |              9.20704 |
| intersection_6m12m |   2025 |       12 |        0 |                   0 |               0 |            12 |              0       |
| intersection_6m12m |   2026 |       10 |       45 |                   7 |               3 |             0 |              7.83457 |

## Extra hypothetical spread-like round-trip cost stress
| model              |   extra_roundtrip_bps |   net_account_return_pct |   additional_spread_like_cost_usd |   profitable_months |   losing_months |   no_trade_months |
|:-------------------|----------------------:|-------------------------:|----------------------------------:|--------------------:|----------------:|------------------:|
| six_only           |                     0 |                   4.8154 |                              0    |                   7 |               5 |                10 |
| six_only           |                     2 |                   4.2504 |                             54.99 |                   7 |               5 |                10 |
| six_only           |                     5 |                   3.4085 |                            136.93 |                   7 |               5 |                10 |
| six_only           |                    10 |                   2.0201 |                            272.04 |                   7 |               5 |                10 |
| twelve_only        |                     0 |                   9.207  |                              0    |                   7 |               3 |                12 |
| twelve_only        |                     2 |                   8.6652 |                             52.78 |                   7 |               3 |                12 |
| twelve_only        |                     5 |                   7.8573 |                            131.45 |                   7 |               3 |                12 |
| twelve_only        |                    10 |                   6.524  |                            261.3  |                   7 |               3 |                12 |
| union_6m12m        |                     0 |                   6.1494 |                              0    |                   7 |               5 |                10 |
| union_6m12m        |                     2 |                   5.5187 |                             60.94 |                   7 |               5 |                10 |
| union_6m12m        |                     5 |                   4.5796 |                            151.69 |                   7 |               5 |                10 |
| union_6m12m        |                    10 |                   3.0326 |                            301.14 |                   7 |               5 |                10 |
| intersection_6m12m |                     0 |                   7.8346 |                              0    |                   7 |               3 |                12 |
| intersection_6m12m |                     2 |                   7.359  |                             46.65 |                   7 |               3 |                12 |
| intersection_6m12m |                     5 |                   6.6495 |                            116.24 |                   7 |               3 |                12 |
| intersection_6m12m |                    10 |                   5.4772 |                            231.22 |                   7 |               3 |                12 |

## By state contribution
| state         | strategy            |   executed |   positive_trades |   account_net_pnl_usd | model              |
|:--------------|:--------------------|-----------:|------------------:|----------------------:|:-------------------|
| breakout_down | structured_breakout |         28 |                14 |                723.47 | six_only           |
| shock         | shock_breakout      |         27 |                 8 |               -241.93 | six_only           |
| breakout_down | structured_breakout |         22 |                12 |                804.4  | twelve_only        |
| shock         | shock_breakout      |         29 |                11 |                116.3  | twelve_only        |
| breakout_down | structured_breakout |         28 |                14 |                731.09 | union_6m12m        |
| shock         | shock_breakout      |         33 |                11 |               -116.15 | union_6m12m        |
| breakout_down | structured_breakout |         22 |                12 |                796.56 | intersection_6m12m |
| shock         | shock_breakout      |         23 |                 8 |                -13.1  | intersection_6m12m |

## Limitations
This research has repeatedly examined Jan 2025–Oct 2026, so these figures are not an independent blind result. Real realized funding, historical L1 bid/ask, queue/slippage, liquidation and contract sizing are unavailable. Initial account $10,000, per-trade initial stop risk 0.5% of evolving equity capped 3x, modeled taker/GST+5 BTC point adverse slippage per side. Trade-close drawdown omits intratrade mark drawdown. The true live system remains BLOCKED. A zero-trade month fails the 22/22 monthly profitability objective.
