# Stage 15 — Preserve Stage 14; investigate July 2025 and pre-entry no-trade filters

## Exact original strategy retained
- Entry: S13_pullback_near_half_atr / previous_month_ranging_4h_adx18, 3R structural stop, 240-minute maximum hold
- Data: exact original Stage 14 Actions event and trade artifacts, verified against the original CSV
- **Reconciliation:** {"original_trades": 91, "largest_individual_net_difference_pts": 0.0, "months_reconciled": 23, "july_2025_net_pts": -2268.58, "july_2025_trades": 15}

## July 2025 original trade diagnosis
- Total trades: 15; winners: 5; losses/flat: 10
- Net price points after standard costs: -2268.59; net normalized R: -0.074
| segment   | value        |   trades |   net_pts |   net_R |   wins |   average_risk_pts |
|:----------|:-------------|---------:|----------:|--------:|-------:|-------------------:|
| side      | LONG         |       14 |  -2601.71 |  -0.66  |      4 |             616.52 |
| side      | SHORT        |        1 |    333.12 |   0.586 |      1 |             568.77 |
| reason    | stop         |        4 |  -2848.09 |  -5.211 |      0 |             562.08 |
| reason    | target       |        3 |   2715.01 |   7.695 |      3 |             349.31 |
| reason    | timeout      |        8 |  -2135.51 |  -2.558 |      2 |             737.97 |
| result    | loss_or_flat |       10 |  -5657.11 |  -9.016 |      0 |             706.81 |
| result    | profit       |        5 |   3388.53 |   8.942 |      5 |             426.37 |

## Distinguishing 2025 July winners from losers (DESCRIPTIVE; not a predictive proof)
| feature            | outcome      |   trades |   median |     mean |
|:-------------------|:-------------|---------:|---------:|---------:|
| h4_adx             | loss_or_flat |       10 |  12.5493 |  12.7944 |
| h4_adx             | profit       |        5 |  12.3258 |  13.2654 |
| h4_eff8            | loss_or_flat |       10 |   0.3561 |   0.3082 |
| h4_eff8            | profit       |        5 |   0.2787 |   0.2611 |
| h4_atr_ratio       | loss_or_flat |       10 |   0.9854 |   0.9162 |
| h4_atr_ratio       | profit       |        5 |   1.0466 |   0.9318 |
| h1_vr              | loss_or_flat |       10 |   0.7385 |   0.9643 |
| h1_vr              | profit       |        5 |   1.0928 |   1.1576 |
| volume_ratio_5m    | loss_or_flat |       10 |   1.5644 |   1.8943 |
| volume_ratio_5m    | profit       |        5 |   1.0367 |   1.0485 |
| initial_risk_pts   | loss_or_flat |       10 | 809.082  | 706.814  |
| initial_risk_pts   | profit       |        5 | 465.804  | 426.374  |
| previous_month_eff | loss_or_flat |       10 |   0.0309 |   0.0309 |
| previous_month_eff | profit       |        5 |   0.0309 |   0.0309 |

## Entire-history comparisons (each scenario replays its own trades)
| filter                 | guard                          |   n2025 |   positive_months_2025 |   net_R_2025 |   n2026 |   positive_months_2026 |   net_R_2026 |   july_trades |   july_net_pts |   july_net_R |   max_drawdown_R |
|:-----------------------|:-------------------------------|--------:|-----------------------:|-------------:|--------:|-----------------------:|-------------:|--------------:|---------------:|-------------:|-----------------:|
| adx_le_15              | no_loss_gate                   |      32 |                      4 |        8.36  |      14 |                      3 |        6.5   |            13 |       -2138.78 |      -0.086  |            7.532 |
| breakout_volume_ge_1p2 | no_loss_gate                   |      46 |                      5 |        7.492 |      20 |                      4 |        7.267 |            13 |       -3569.25 |      -4.4894 |            6.778 |
| risk_le_700            | no_loss_gate                   |      50 |                      6 |       12.934 |      23 |                      4 |        5.406 |            10 |         394.59 |       2.6591 |            6.284 |
| unchanged              | daily_minus_1R                 |      53 |                      5 |        7.67  |      26 |                      4 |        6.757 |            13 |       -1760.11 |      -1.2599 |            5.416 |
| unchanged              | daily_minus_2R                 |      62 |                      6 |       10.014 |      28 |                      4 |        8.026 |            15 |       -2268.58 |      -0.0741 |            6.655 |
| unchanged              | daily_minus_2R_weekly_minus_3R |      59 |                      7 |       13.305 |      28 |                      4 |        8.026 |            13 |        -926.95 |       2.5703 |            5.734 |
| unchanged              | no_loss_gate                   |      63 |                      6 |       12.401 |      28 |                      4 |        8.026 |            15 |       -2268.58 |      -0.0741 |            6.558 |
| unchanged              | weekly_minus_3R                |      59 |                      7 |       13.305 |      28 |                      4 |        8.026 |            13 |        -926.95 |       2.5703 |            5.734 |

## Non-July 2025 ranking, then JULY and 2026 as already-known checks
| filter                 | guard                          |   n2025 |   positive_months_2025_except_july |   net_R_2025_except_july |   july_trades |   july_net_R |   n2026H1 |   net_R_2026H1 |   n2026H2 |   net_R_2026H2 |
|:-----------------------|:-------------------------------|--------:|-----------------------------------:|-------------------------:|--------------:|-------------:|----------:|---------------:|----------:|---------------:|
| 1h_volume_ratio_le_1p2 | no_loss_gate                   |      47 |                                  7 |                   13.042 |            11 |      -0.633  |        20 |         12.495 |         0 |          0     |
| 1h_volume_ratio_le_1p2 | daily_minus_2R_weekly_minus_3R |      44 |                                  7 |                   11.301 |            10 |       0.7958 |        20 |         12.495 |         0 |          0     |
| 1h_volume_ratio_le_1p2 | weekly_minus_3R                |      44 |                                  7 |                   11.301 |            10 |       0.7958 |        20 |         12.495 |         0 |          0     |
| 1h_volume_ratio_le_1p2 | daily_minus_2R                 |      46 |                                  7 |                   10.655 |            11 |      -0.633  |        20 |         12.495 |         0 |          0     |
| 4h_atr_ratio_le_1      | no_loss_gate                   |      44 |                                  6 |                   12.888 |             8 |      -1.6546 |        16 |          0.784 |         1 |          0.096 |
| 4h_atr_ratio_le_1      | weekly_minus_3R                |      44 |                                  6 |                   12.888 |             8 |      -1.6546 |        16 |          0.784 |         1 |          0.096 |
| unchanged              | no_loss_gate                   |      63 |                                  6 |                   12.475 |            15 |      -0.0741 |        27 |          7.93  |         1 |          0.096 |
| 1h_volume_ratio_le_1p2 | daily_minus_1R                 |      42 |                                  6 |                   11.13  |            10 |      -3.0847 |        20 |         12.495 |         0 |          0     |
| unchanged              | daily_minus_2R_weekly_minus_3R |      59 |                                  6 |                   10.734 |            13 |       2.5703 |        27 |          7.93  |         1 |          0.096 |
| unchanged              | weekly_minus_3R                |      59 |                                  6 |                   10.734 |            13 |       2.5703 |        27 |          7.93  |         1 |          0.096 |
| unchanged              | daily_minus_2R                 |      62 |                                  6 |                   10.088 |            15 |      -0.0741 |        27 |          7.93  |         1 |          0.096 |
| breakout_volume_ge_1p5 | daily_minus_2R                 |      40 |                                  6 |                    5.518 |            11 |      -7.1256 |        15 |          6.486 |         0 |          0     |

## Gate result: 0/75 configurations
Requires >=9 active 2025 and >=8 active 2026 months, >=75% positive active months
in both years, >=60/30/20 independent trades and positive net R
in 2025/2026 H1/H2. All previously inspected periods; passing would still be exploratory.

## Limitations
- July 2025 is a known bad outcome; all July improvements are retrospective
- No filter uses calendar month label (including July) to trigger entries
- Daily/weekly safeguards use realized net R from *closed* trades only
- A daily/weekly cap prevents subsequent entries; cannot limit stop gap losses
- Each filtered scenario replays from all eligible signals, not from baseline winners
- Risk normalized R represents constant per-trade risk concept, not actual account PnL
- Prices are 1m OHLC, stop-first, slippage 5 points per side, standard taker fees and GST
- Source 1m has one missing day 2026-10-31, 2026-11 partial
- Funding, quote spread, market impact and liquidation not modeled
- All 2026 historical windows already exposed; no truly independent forward verification
- 15 filters times five safeguards creates multiple-testing risk
- Zero-trade months are not counted as profitable

## Files
- july_2025_original_trade_diagnostics.csv
- july_2025_breakdown.csv
- july_winner_loser_feature_comparison.csv
- protective_filter_comparison.csv and month_by_month.csv
- variant_trade_ledger.csv.gz as downloadable GitHub Actions artifact
- quality.json for reproduction and reconciliation
