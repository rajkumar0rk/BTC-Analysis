# BTC multi-regime hardening: classifier uncertainty, strict selector and execution costs

## Why this audit
Prior causal 6-month selector made 221 trades and -24% net; the shock-only strategy had +3.35% but only 10/22 positive months. The question is whether a stronger past-only eligibility gate and intuitive mapping improve reliable month-to-month performance. This is a frozen NON-OPTIMIZED comparator audit, not a search for an ex-post winner.

## Verification
~~~json
{
  "source": "Delta India BTCUSD native 1M, SHA256 and timestamp audited",
  "native_minutes": 992160,
  "native_partitions": 23,
  "state_causal_prefix_invariance_verified": true,
  "all_models_on_identical_single_account_1M_engine": true,
  "legacy_selector_parity_verified": true,
  "shock_only_parity_verified": true,
  "calendar_months": 22,
  "predeclared_comparators": [
    "no_trade",
    "fixed_logic",
    "shock_only",
    "prior_selector",
    "strict_lower_bound"
  ],
  "historical_spread_realized_funding_liquidation_included": false,
  "historical_funding_is_rate_proxy_not_settlement": true,
  "is_externally_blind_holdout": false,
  "cost_stress_hypothetical_not_historical": true
}
~~~

Historical-prefix regime labels were invariant in three checks; the regime has only descriptive price-action semantics and no independent ground-truth label. 2025/26 data has been used in previous research, so not externally blind.

## Results: common 1M exclusive-position account, net after base fees/GST/slip
| model              |   trades |   wins |   losses |   positive_months |   negative_months |   idle_months |   positive_evaluation_months |   net_return_pct |   net_pnl_usd |   ending_equity_usd |   profit_factor |   max_trade_close_drawdown_pct |   total_fee_gst_usd |   total_slippage_usd | passes_22_profitable_months   |   candidate_signal_hours |   selected_signal_hours |   blocked_due_exclusive_position |   actually_executed_trades |
|:-------------------|---------:|-------:|---------:|------------------:|------------------:|--------------:|-----------------------------:|-----------------:|--------------:|--------------------:|----------------:|-------------------------------:|--------------------:|---------------------:|:------------------------------|-------------------------:|------------------------:|---------------------------------:|---------------------------:|
| no_trade           |        0 |      0 |        0 |                 0 |                 0 |            22 |                            0 |           0      |          0    |            10000    |        nan      |                          0     |                0    |                 0    | False                         |                     6418 |                       0 |                                0 |                          0 |
| fixed_logic        |      688 |    234 |      454 |                 8 |                14 |             0 |                            8 |         -34.8618 |      -3486.18 |             6513.82 |          0.8211 |                         36.995 |             3992.07 |               386.34 | False                         |                     6418 |                    1369 |                              681 |                        688 |
| shock_only         |      301 |    107 |      194 |                10 |                12 |             0 |                            8 |           3.3469 |        334.69 |            10334.7  |          1.0316 |                          9.177 |             1841.47 |               184.26 | False                         |                     6418 |                     390 |                               89 |                        301 |
| prior_selector     |      221 |     68 |      153 |                 2 |                12 |             8 |                            2 |         -24.0037 |      -2400.37 |             7599.63 |          0.6763 |                         24.635 |             1386.46 |               148.81 | False                         |                     6418 |                     401 |                              180 |                        221 |
| strict_lower_bound |        0 |      0 |        0 |                 0 |                 0 |            22 |                            0 |           0      |          0    |            10000    |        nan      |                          0     |                0    |                 0    | False                         |                     6418 |                       0 |                                0 |                          0 |

## Per-month net percentage, all 22 complete IST months including no-trade
| month_ist   |   fixed_logic |   no_trade |   prior_selector |   shock_only |   strict_lower_bound |
|:------------|--------------:|-----------:|-----------------:|-------------:|---------------------:|
| 2025-01     |        -1.796 |          0 |            0     |       -2.111 |                    0 |
| 2025-02     |        -4.223 |          0 |            0     |       -1.016 |                    0 |
| 2025-03     |        -0.701 |          0 |            0     |       -0.046 |                    0 |
| 2025-04     |        -4.693 |          0 |            0     |        0.172 |                    0 |
| 2025-05     |        -4.221 |          0 |            0     |        1.324 |                    0 |
| 2025-06     |        -5.201 |          0 |            0     |       -2.635 |                    0 |
| 2025-07     |        -5.465 |          0 |           -1.226 |       -3.33  |                    0 |
| 2025-08     |         1.557 |          0 |            0     |        0.183 |                    0 |
| 2025-09     |         0.607 |          0 |           -2.627 |        2.845 |                    0 |
| 2025-10     |         2.381 |          0 |           -0.052 |       10.103 |                    0 |
| 2025-11     |         2.14  |          0 |           -0.136 |        0.487 |                    0 |
| 2025-12     |        -8.473 |          0 |           -6.365 |       -5.797 |                    0 |
| 2026-01     |         1.448 |          0 |           -1.132 |        4.738 |                    0 |
| 2026-02     |         2.374 |          0 |            0.793 |        2.501 |                    0 |
| 2026-03     |        -0.179 |          0 |           -0.227 |       -0.227 |                    0 |
| 2026-04     |        -5.637 |          0 |            2.577 |       -0.682 |                    0 |
| 2026-05     |        -3.417 |          0 |           -3.624 |       -0.474 |                    0 |
| 2026-06     |         2.586 |          0 |           -2.543 |        1.642 |                    0 |
| 2026-07     |        -4.086 |          0 |           -2.037 |       -0.306 |                    0 |
| 2026-08     |         1.498 |          0 |           -8.723 |        0.589 |                    0 |
| 2026-09     |        -5.536 |          0 |           -1.296 |       -2.378 |                    0 |
| 2026-10     |        -2.194 |          0 |            0     |       -1.271 |                    0 |

## Historical regime persistence and NEXT 4H direction by year
Forward returns are used ONLY for diagnostics after the state is determined; nonoverlapping four-hour start times; Wilson confidence interval on future up frequency.
| regime        |   year |   classified_hours |   persistence_next1h_pct |   nonoverlap4h_samples |   next4h_up_pct |   next4h_up_wilson_low95 |   next4h_up_wilson_high95 |   same_direction_as_regime_pct |   mean_next4h_high_low_over_signal_ATR |
|:--------------|-------:|-------------------:|-------------------------:|-----------------------:|----------------:|-------------------------:|--------------------------:|-------------------------------:|---------------------------------------:|
| shock         |   2025 |                593 |                    53.12 |                    128 |           56.25 |                    47.6  |                     64.54 |                         nan    |                                  2.41  |
| shock         |   2026 |                440 |                    41.36 |                     97 |           49.48 |                    39.75 |                     59.26 |                         nan    |                                  2.876 |
| breakout_up   |   2025 |                128 |                    14.84 |                     32 |           28.12 |                    15.56 |                     45.37 |                          28.12 |                                  2.152 |
| breakout_up   |   2026 |                 89 |                    23.6  |                     20 |           45    |                    25.82 |                     65.79 |                          45    |                                  2.248 |
| breakout_down |   2025 |                134 |                    27.61 |                     40 |           55    |                    39.83 |                     69.29 |                          45    |                                  2.584 |
| breakout_down |   2026 |                125 |                    24.8  |                     22 |           59.09 |                    38.73 |                     76.74 |                          40.91 |                                  2.782 |
| trend_up      |   2025 |                860 |                    71.86 |                    214 |           45.79 |                    39.25 |                     52.49 |                          45.79 |                                  2.244 |
| trend_up      |   2026 |                806 |                    71.59 |                    201 |           47.26 |                    40.48 |                     54.15 |                          47.26 |                                  2.142 |
| trend_down    |   2025 |                932 |                    72.21 |                    227 |           60.35 |                    53.87 |                     66.49 |                          39.65 |                                  2.216 |
| trend_down    |   2026 |                849 |                    72.91 |                    209 |           51.2  |                    44.46 |                     57.89 |                          48.8  |                                  2.12  |
| compression   |   2025 |                623 |                    73.19 |                    152 |           48.03 |                    40.23 |                     55.92 |                         nan    |                                  2.108 |
| compression   |   2026 |                468 |                    72.22 |                    119 |           58.82 |                    49.84 |                     67.26 |                         nan    |                                  2.126 |
| range         |   2025 |               1350 |                    72.89 |                    352 |           51.7  |                    46.49 |                     56.88 |                         nan    |                                  2.152 |
| range         |   2026 |               1033 |                    73.48 |                    258 |           46.51 |                    40.52 |                     52.6  |                         nan    |                                  2.021 |
| mixed         |   2025 |               4055 |                    79.09 |                   1023 |           48.78 |                    45.73 |                     51.84 |                         nan    |                                  2.044 |
| mixed         |   2026 |               3480 |                    79.4  |                    897 |           50.39 |                    47.12 |                     53.65 |                         nan    |                                  2.089 |

## Hypothetical additional roundtrip execution cost stress
2/5/10 extra basis points on entry notional as a spread-like scenario, NOT reconstructed historical bid/ask. No change in model selection rules as cost increases.
| model              |   extra_roundtrip_bps |   net_return_pct |   ending_account_usd |   positive_months |   negative_months |   idle_months |   extra_cost_usd |
|:-------------------|----------------------:|-----------------:|---------------------:|------------------:|------------------:|--------------:|-----------------:|
| no_trade           |                     0 |           0      |             10000    |                 0 |                 0 |            22 |             0    |
| no_trade           |                     2 |           0      |             10000    |                 0 |                 0 |            22 |             0    |
| no_trade           |                     5 |           0      |             10000    |                 0 |                 0 |            22 |             0    |
| no_trade           |                    10 |           0      |             10000    |                 0 |                 0 |            22 |             0    |
| fixed_logic        |                     0 |         -34.8618 |              6513.82 |                 8 |                14 |             0 |             0    |
| fixed_logic        |                     2 |         -40.2242 |              5977.58 |                 7 |                15 |             0 |           650.15 |
| fixed_logic        |                     5 |         -47.453  |              5254.7  |                 6 |                16 |             0 |          1532.38 |
| fixed_logic        |                    10 |         -57.6141 |              4238.59 |                 4 |                18 |             0 |          2786.64 |
| shock_only         |                     0 |           3.3469 |             10334.7  |                10 |                12 |             0 |             0    |
| shock_only         |                     2 |           0.213  |             10021.3  |                10 |                12 |             0 |           307.15 |
| shock_only         |                     5 |          -4.3112 |              9568.88 |                 7 |                15 |             0 |           750.2  |
| shock_only         |                    10 |         -11.404  |              8859.6  |                 7 |                15 |             0 |          1443.86 |
| prior_selector     |                     0 |         -24.0037 |              7599.63 |                 2 |                12 |             8 |             0    |
| prior_selector     |                     2 |         -25.9794 |              7402.06 |                 2 |                12 |             8 |           231.9  |
| prior_selector     |                     5 |         -28.8475 |              7115.25 |                 2 |                12 |             8 |           568.97 |
| prior_selector     |                    10 |         -33.3842 |              6661.58 |                 1 |                13 |             8 |          1103.18 |
| strict_lower_bound |                     0 |           0      |             10000    |                 0 |                 0 |            22 |             0    |
| strict_lower_bound |                     2 |           0      |             10000    |                 0 |                 0 |            22 |             0    |
| strict_lower_bound |                     5 |           0      |             10000    |                 0 |                 0 |            22 |             0    |
| strict_lower_bound |                    10 |           0      |             10000    |                 0 |                 0 |            22 |             0    |

## Interpretation
- The classifier correctly obeys history-prefix causality but no quantified true-regime accuracy is possible without independent ground-truth labels.
- Past-only selector correctness does not ensure strategic edge. A no-trade decision is valid but fails the 22/22 positive-month target.
- Statistical lower confidence bounds assume iid trades and may overstate certainty given regime clustering; 2026 was previously researched.
- Stop-first per original 1M intrabar execution. Fees 0.05% per side plus 18% GST; assumed 5 BTC points adverse slippage on both legs.
- No historical L1 bid/ask depth, queue, actual fills, cash funding settlements, liquidation or contract rounding. Extra cost sensitivities are scenario tests only.
- Drawdown sampled on each trade close; intratrade equity may show larger risk.
- No regime switch or candidate is promoted for real-money trading from this audit alone.
