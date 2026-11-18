# Stage 15 — Preserve Stage 14; investigate July 2025 and pre-entry no-trade filters

## Exact original strategy retained
- Entry: S13_pullback_near_half_atr / previous_month_ranging_4h_adx18, 3R structural stop, 240-minute maximum hold
- Data: exact original Stage 14 Actions event and trade artifacts, verified against the original CSV
- **Reconciliation:** {"original_trades": 90, "largest_individual_net_difference_pts": 0.0, "months_reconciled": 23, "july_2025_net_pts": 2181.55, "july_2025_trades": 6}

## July 2025 original trade diagnosis
- Total trades: 6; winners: 4; losses/flat: 2
- Net price points after standard costs: 2181.55; net normalized R: 3.538
| segment   | value        |   trades |   net_pts |   net_R |   wins |   average_risk_pts |
|:----------|:-------------|---------:|----------:|--------:|-------:|-------------------:|
| side      | LONG         |        6 |   2181.55 |   3.538 |      4 |             737.06 |
| reason    | stop         |        1 |   -703.51 |  -1.151 |      0 |             611.24 |
| reason    | target       |        1 |   1405.06 |   2.81  |      1 |             500    |
| reason    | timeout      |        4 |   1480    |   1.879 |      3 |             827.78 |
| result    | loss_or_flat |        2 |   -996.28 |  -1.542 |      0 |             679.86 |
| result    | profit       |        4 |   3177.82 |   5.081 |      4 |             765.66 |

## Distinguishing 2025 July winners from losers (DESCRIPTIVE; not a predictive proof)
| feature            | outcome      |   trades |   median |     mean |
|:-------------------|:-------------|---------:|---------:|---------:|
| h4_adx             | loss_or_flat |        2 |  14.8858 |  14.8858 |
| h4_adx             | profit       |        4 |  16.7705 |  16.3676 |
| h4_eff8            | loss_or_flat |        2 |   0.4087 |   0.4087 |
| h4_eff8            | profit       |        4 |   0.5557 |   0.5343 |
| h4_atr_ratio       | loss_or_flat |        2 |   0.9642 |   0.9642 |
| h4_atr_ratio       | profit       |        4 |   0.8216 |   0.8301 |
| h1_vr              | loss_or_flat |        2 |   0.4768 |   0.4768 |
| h1_vr              | profit       |        4 |   0.9989 |   0.9577 |
| volume_ratio_5m    | loss_or_flat |        2 |   1.392  |   1.392  |
| volume_ratio_5m    | profit       |        4 |   1.0721 |   1.1366 |
| initial_risk_pts   | loss_or_flat |        2 | 679.859  | 679.859  |
| initial_risk_pts   | profit       |        4 | 770.431  | 765.659  |
| previous_month_eff | loss_or_flat |        2 |   0.0148 |   0.0148 |
| previous_month_eff | profit       |        4 |   0.0148 |   0.0148 |

## Entire-history comparisons (each scenario replays its own trades)
| filter                 | guard                          |   n2025 |   positive_months_2025 |   net_R_2025 |   n2026 |   positive_months_2026 |   net_R_2026 |   july_trades |   july_net_pts |   july_net_R |   max_drawdown_R |
|:-----------------------|:-------------------------------|--------:|-----------------------:|-------------:|--------:|-----------------------:|-------------:|--------------:|---------------:|-------------:|-----------------:|
| adx_le_15              | no_loss_gate                   |      23 |                      4 |       -6.25  |      18 |                      3 |       -0.972 |             2 |         701.55 |       1.6592 |           11.581 |
| breakout_volume_ge_1p2 | no_loss_gate                   |      27 |                      4 |       -1.751 |      38 |                      4 |       -4.071 |             4 |        1153.16 |       1.24   |           11.036 |
| risk_le_700            | no_loss_gate                   |      28 |                      2 |       -4.469 |      44 |                      4 |       -3.748 |             2 |         701.55 |       1.6592 |           13.999 |
| unchanged              | daily_minus_1R                 |      38 |                      3 |        1.31  |      45 |                      4 |       -4.907 |             6 |        2181.55 |       3.5384 |           11.56  |
| unchanged              | daily_minus_2R                 |      40 |                      2 |       -0.981 |      50 |                      4 |       -4.626 |             6 |        2181.55 |       3.5384 |           11.523 |
| unchanged              | daily_minus_2R_weekly_minus_3R |      40 |                      2 |       -0.981 |      48 |                      4 |       -6.801 |             6 |        2181.55 |       3.5384 |           13.698 |
| unchanged              | no_loss_gate                   |      40 |                      2 |       -0.981 |      50 |                      4 |       -4.626 |             6 |        2181.55 |       3.5384 |           11.523 |
| unchanged              | weekly_minus_3R                |      40 |                      2 |       -0.981 |      48 |                      4 |       -6.801 |             6 |        2181.55 |       3.5384 |           13.698 |

## Non-July 2025 ranking, then JULY and 2026 as already-known checks
| filter                 | guard                          |   n2025 |   positive_months_2025_except_july |   net_R_2025_except_july |   july_trades |   july_net_R |   n2026H1 |   net_R_2026H1 |   n2026H2 |   net_R_2026H2 |
|:-----------------------|:-------------------------------|--------:|-----------------------------------:|-------------------------:|--------------:|-------------:|----------:|---------------:|----------:|---------------:|
| 1h_volume_ratio_le_1p2 | daily_minus_1R                 |      32 |                                  2 |                   -1.373 |             5 |       3.4418 |        21 |          2.922 |        13 |         -9.284 |
| 4h_atr_ratio_le_1      | daily_minus_1R                 |      30 |                                  2 |                   -1.567 |             5 |       4.6894 |        22 |          3.097 |        12 |         -8.393 |
| unchanged              | daily_minus_1R                 |      38 |                                  2 |                   -2.229 |             6 |       3.5384 |        27 |          6.653 |        18 |        -11.56  |
| 4h_atr_ratio_le_1      | daily_minus_2R                 |      31 |                                  2 |                   -2.671 |             5 |       4.6894 |        23 |          3.34  |        15 |         -8.329 |
| 4h_atr_ratio_le_1      | daily_minus_2R_weekly_minus_3R |      31 |                                  2 |                   -2.671 |             5 |       4.6894 |        23 |          3.34  |        15 |         -8.329 |
| 4h_atr_ratio_le_1      | no_loss_gate                   |      31 |                                  2 |                   -2.671 |             5 |       4.6894 |        23 |          3.34  |        15 |         -8.329 |
| 4h_atr_ratio_le_1      | weekly_minus_3R                |      31 |                                  2 |                   -2.671 |             5 |       4.6894 |        23 |          3.34  |        15 |         -8.329 |
| 1h_volume_ratio_le_1p2 | daily_minus_2R                 |      34 |                                  1 |                   -3.664 |             5 |       3.4418 |        21 |          2.922 |        14 |        -10.484 |
| 1h_volume_ratio_le_1p2 | daily_minus_2R_weekly_minus_3R |      34 |                                  1 |                   -3.664 |             5 |       3.4418 |        21 |          2.922 |        14 |        -10.484 |
| 1h_volume_ratio_le_1p2 | no_loss_gate                   |      34 |                                  1 |                   -3.664 |             5 |       3.4418 |        21 |          2.922 |        14 |        -10.484 |
| 1h_volume_ratio_le_1p2 | weekly_minus_3R                |      34 |                                  1 |                   -3.664 |             5 |       3.4418 |        21 |          2.922 |        14 |        -10.484 |
| unchanged              | daily_minus_2R                 |      40 |                                  1 |                   -4.519 |             6 |       3.5384 |        28 |          6.897 |        22 |        -11.523 |

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
