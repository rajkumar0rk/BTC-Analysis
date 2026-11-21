# BTC four-layer evidence selector — native 1M exit-management follow-up

## Fixed mechanism and no-hindsight rule
This is a controlled **exit-only** ablation of the already positive 6M/12M past-only eligibility rules. Regime detection and eligibility / first 15M confirmation are unchanged; no retrospective exclusion of losing 2026 months. The same 2025–2026 archive has been repeatedly researched and is **not a pristine holdout**.

## Quality
~~~json
{
  "native_1m_bars": 992160,
  "data_partitions": 23,
  "original_15m_confirmed_candidate_signals": 513,
  "original_6m_eligibility_event_count": 85,
  "original_12m_eligibility_event_count": 80,
  "independent_original_6m_baseline_trade_level_parity": true,
  "independent_original_12m_baseline_trade_level_parity": true,
  "selected_12m_and_6m_gates_fixed_from_previous_study": true,
  "fixed_breakout_protect_trigger_R": 1.5,
  "fixed_stop_protection_offset_R": 0.15,
  "fixed_runner_trailing_atr": 1.8,
  "trailing_updates_only_effective_following_1m_bar": true,
  "stop_first_same_1m_bar": true,
  "one_position_global": true,
  "original_fee_gst_and_slippage_preserved": true,
  "original_month_selection_uses_original_exit_shadow_trades": true,
  "realized_funding_ledger_included": false,
  "historical_spread_included": false,
  "liquidation_and_exchange_contract_rounding_included": false,
  "external_unresearched_validation_available": false,
  "live_trading_approved": false
}
~~~

## After-cost 22-month account returns
| model            |   candidate_events |   exclusive_position_rejections |   entry_unavailable |   executed_trades |   trades_activated |   post_bar_stop_updates |   trades |   wins |   win_rate_pct |   profit_factor |   net_return_pct |   net_profit_usd |   ending_equity_usd |   max_trade_close_drawdown_pct |   fees_gst_usd |   slippage_usd |   profitable_months |   losing_months |   idle_months | passes_22_22   |
|:-----------------|-------------------:|--------------------------------:|--------------------:|------------------:|-------------------:|------------------------:|---------:|-------:|---------------:|----------------:|-----------------:|-----------------:|--------------------:|-------------------------------:|---------------:|---------------:|--------------------:|----------------:|--------------:|:---------------|
| past12_original  |                 80 |                              29 |                   0 |                51 |                  0 |                       0 |       51 |     21 |         41.176 |          1.5211 |           8.9446 |           894.46 |             10894.5 |                          4.857 |         313.71 |          36.19 |                   7 |               3 |            12 | False          |
| past12_protected |                 80 |                              29 |                   0 |                51 |                 23 |                      23 |       51 |     23 |         45.098 |          1.6135 |           9.207  |           920.7  |             10920.7 |                          4.864 |         311.42 |          35.93 |                   7 |               3 |            12 | False          |
| past12_runner    |                 80 |                              24 |                   0 |                56 |                 25 |                     254 |       56 |     27 |         48.214 |          1.2204 |           3.5734 |           357.34 |             10357.3 |                          5.215 |         331.62 |          37.93 |                   7 |               3 |            12 | False          |
| past6_original   |                 85 |                              30 |                   0 |                55 |                  0 |                       0 |       55 |     19 |         34.545 |          1.203  |           3.9621 |           396.21 |             10396.2 |                          4.857 |         325.3  |          36.28 |                   7 |               5 |            10 | False          |
| past6_protected  |                 85 |                              30 |                   0 |                55 |                 23 |                      23 |       55 |     22 |         40     |          1.2833 |           4.8154 |           481.54 |             10481.5 |                          4.864 |         324.72 |          36.22 |                   7 |               5 |            10 | False          |

## Annual net returns (training-only months count as idle)
| model            |   year |   months |   profitable |   losing |   no_trade |   compounded_net_return_pct |
|:-----------------|-------:|---------:|-------------:|---------:|-----------:|----------------------------:|
| past12_original  |   2025 |       12 |            0 |        0 |         12 |                      0      |
| past12_original  |   2026 |       10 |            7 |        3 |          0 |                      8.9446 |
| past12_protected |   2025 |       12 |            0 |        0 |         12 |                      0      |
| past12_protected |   2026 |       10 |            7 |        3 |          0 |                      9.207  |
| past12_runner    |   2025 |       12 |            0 |        0 |         12 |                      0      |
| past12_runner    |   2026 |       10 |            7 |        3 |          0 |                      3.5734 |
| past6_original   |   2025 |       12 |            0 |        2 |         10 |                     -3.3589 |
| past6_original   |   2026 |       10 |            7 |        3 |          0 |                      7.5755 |
| past6_protected  |   2025 |       12 |            0 |        2 |         10 |                     -2.7999 |
| past6_protected  |   2026 |       10 |            7 |        3 |          0 |                      7.8346 |

## Complete month-by-month after-cost % returns
| month_ist   |   past12_original |   past12_protected |   past12_runner |   past6_original |   past6_protected |
|:------------|------------------:|-------------------:|----------------:|-----------------:|------------------:|
| 2025-01     |             0     |              0     |           0     |            0     |             0     |
| 2025-02     |             0     |              0     |           0     |            0     |             0     |
| 2025-03     |             0     |              0     |           0     |            0     |             0     |
| 2025-04     |             0     |              0     |           0     |            0     |             0     |
| 2025-05     |             0     |              0     |           0     |            0     |             0     |
| 2025-06     |             0     |              0     |           0     |            0     |             0     |
| 2025-07     |             0     |              0     |           0     |            0     |             0     |
| 2025-08     |             0     |              0     |           0     |           -2.292 |            -2.292 |
| 2025-09     |             0     |              0     |           0     |            0     |             0     |
| 2025-10     |             0     |              0     |           0     |            0     |             0     |
| 2025-11     |             0     |              0     |           0     |            0     |             0     |
| 2025-12     |             0     |              0     |           0     |           -1.092 |            -0.52  |
| 2026-01     |             2.518 |              2.518 |           0.32  |            1.23  |             1.23  |
| 2026-02     |             4.224 |              4.224 |           3.892 |            4.224 |             4.224 |
| 2026-03     |             3.322 |              1.872 |           1.239 |            3.322 |             1.872 |
| 2026-04     |            -3.15  |             -3.15  |          -3.15  |           -3.15  |            -3.15  |
| 2026-05     |             1.326 |              1.052 |           1.093 |            1.326 |             1.052 |
| 2026-06     |             1.166 |              2.34  |           1.777 |            1.166 |             2.34  |
| 2026-07     |            -1.342 |             -1.15  |          -0.939 |           -1.342 |            -1.15  |
| 2026-08     |             1.686 |              1.686 |           0.419 |            1.686 |             1.686 |
| 2026-09     |             1.446 |              1.446 |           1.141 |            1.446 |             1.446 |
| 2026-10     |            -2.331 |             -1.766 |          -2.093 |           -2.331 |            -1.766 |

## Additional hypothetical execution cost sensitivity, roundtrip bps
These are *additional* bps applied on entry notional to existing taker fees+GST+5-price-point slip per leg, not observed exchange L1 spreads.
| model            |   extra_roundtrip_bps |   net_account_return_pct |   additional_spread_like_cost_usd |   profitable_months |   losing_months |   no_trade_months |
|:-----------------|----------------------:|-------------------------:|----------------------------------:|--------------------:|----------------:|------------------:|
| past12_original  |                     0 |                   8.9446 |                              0    |                   7 |               3 |                12 |
| past12_original  |                     2 |                   8.404  |                             53.15 |                   7 |               3 |                12 |
| past12_original  |                     5 |                   7.598  |                            132.38 |                   7 |               3 |                12 |
| past12_original  |                    10 |                   6.2676 |                            263.14 |                   7 |               3 |                12 |
| past12_protected |                     0 |                   9.207  |                              0    |                   7 |               3 |                12 |
| past12_protected |                     2 |                   8.6652 |                             52.78 |                   7 |               3 |                12 |
| past12_protected |                     5 |                   7.8573 |                            131.45 |                   7 |               3 |                12 |
| past12_protected |                    10 |                   6.524  |                            261.3  |                   7 |               3 |                12 |
| past12_runner    |                     0 |                   3.5734 |                              0    |                   7 |               3 |                12 |
| past12_runner    |                     2 |                   3.0097 |                             56.14 |                   7 |               3 |                12 |
| past12_runner    |                     5 |                   2.1697 |                            139.78 |                   7 |               3 |                12 |
| past12_runner    |                    10 |                   0.7846 |                            277.7  |                   6 |               4 |                12 |
| past6_original   |                     0 |                   3.9621 |                              0    |                   7 |               5 |                10 |
| past6_original   |                     2 |                   3.4016 |                             55.07 |                   7 |               5 |                10 |
| past6_original   |                     5 |                   2.5664 |                            137.12 |                   7 |               5 |                10 |
| past6_original   |                    10 |                   1.189  |                            272.42 |                   7 |               5 |                10 |
| past6_protected  |                     0 |                   4.8154 |                              0    |                   7 |               5 |                10 |
| past6_protected  |                     2 |                   4.2504 |                             54.99 |                   7 |               5 |                10 |
| past6_protected  |                     5 |                   3.4085 |                            136.93 |                   7 |               5 |                10 |
| past6_protected  |                    10 |                   2.0201 |                            272.04 |                   7 |               5 |                10 |

## Account contribution by original strategy / regime
| strategy            | state         |   trades |   wins |   net_usd |   net_R |   stop_update_trades | model            |
|:--------------------|:--------------|---------:|-------:|----------:|--------:|---------------------:|:-----------------|
| shock_breakout      | shock         |       29 |     11 |   210.52  |   4.425 |                    0 | past12_original  |
| structured_breakout | breakout_down |       22 |     10 |   683.945 |  13.134 |                    0 | past12_original  |
| shock_breakout      | shock         |       29 |     11 |   116.303 |   2.573 |                   11 | past12_protected |
| structured_breakout | breakout_down |       22 |     12 |   804.4   |  15.435 |                   12 | past12_protected |
| shock_breakout      | shock         |       33 |     15 |  -250.256 |  -4.665 |                   13 | past12_runner    |
| structured_breakout | breakout_down |       23 |     12 |   607.598 |  11.98  |                   12 | past12_runner    |
| shock_breakout      | shock         |       27 |      8 |  -151.954 |  -2.779 |                    0 | past6_original   |
| structured_breakout | breakout_down |       28 |     11 |   548.163 |  10.971 |                    0 | past6_original   |
| shock_breakout      | shock         |       27 |      8 |  -241.934 |  -4.631 |                    9 | past6_protected  |
| structured_breakout | breakout_down |       28 |     14 |   723.469 |  14.423 |                   14 | past6_protected  |

## Caveats and decision
Stops update only after each fully completed native 1M candle, and only affect subsequent minutes. If active stop and TP touch inside the same candle, stop wins. The original fixed target remains 3R for breakout protection; runner removes the breakout TP and trails at 1.8 ATR14 after 1.5R activation. Original stop and 36-hour timeout unchanged.
Historical monthly eligibility was trained on shadow trades made with the original 3R exits, NOT with the new exit variants. Thus even an improved exit model is a conditional ablation, not an internally re-trained standalone alpha system. Bid/ask, realized funding, liquidation and exchange contract rounding not reconstructed. Drawdown only at trade exits. Never promote a result to real-money trading without genuinely unseen forward testing and actual exchange-cost verification.
