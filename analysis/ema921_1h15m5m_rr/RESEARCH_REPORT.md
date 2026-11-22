# EMA9/21 1H + 15M + 5M — actual BTCUSD 1-minute replay

Pre-registered specifications: see NOVELTY_CHECK.md. All settings fixed before test.

## Four scenario results (fees, GST and adverse $5/side slippage included)
| case            |   trades |   wins |   losses |   win_rate_pct |   targets_hit |   stops_hit |   net_account_return_compounded_pct |   max_closed_trade_drawdown_pct |   positive_months_22 |   2025_account_return_pct |   2026_Jan_Oct_account_return_pct |
|:----------------|---------:|-------:|---------:|---------------:|--------------:|------------:|------------------------------------:|--------------------------------:|---------------------:|--------------------------:|----------------------------------:|
| weekdays_IST_2R |     1019 |    339 |      680 |          33.27 |           343 |         666 |                              -71.89 |                           72.60 |                    1 |                    -49.92 |                            -43.87 |
| weekdays_IST_3R |      970 |    240 |      730 |          24.74 |           239 |         718 |                              -71.82 |                           72.58 |                    1 |                    -51.64 |                            -41.72 |
| all_days_2R     |     1396 |    444 |      952 |          31.81 |           460 |         923 |                              -83.61 |                           83.83 |                    0 |                    -62.81 |                            -55.92 |
| all_days_3R     |     1312 |    318 |      994 |          24.24 |           321 |         973 |                              -82.46 |                           82.96 |                    1 |                    -62.39 |                            -53.35 |

## Net 1x account monthly returns by IST calendar month (%)
| month_ist   |   all_days_2R |   all_days_3R |   weekdays_IST_2R |   weekdays_IST_3R |
|:------------|--------------:|--------------:|------------------:|------------------:|
| 2025-01     |         -6.26 |         -5.81 |             -2.93 |             -2.79 |
| 2025-02     |         -6.99 |         -9.49 |             -5.79 |             -8.97 |
| 2025-03     |         -5.37 |         -1.09 |             -4.74 |             -0.28 |
| 2025-04     |         -7.16 |         -8.60 |             -6.80 |             -8.19 |
| 2025-05     |        -13.08 |         -9.54 |             -9.18 |             -5.84 |
| 2025-06     |         -4.66 |         -4.57 |             -2.02 |             -2.31 |
| 2025-07     |         -7.18 |         -9.46 |             -5.86 |             -7.99 |
| 2025-08     |         -6.80 |         -8.17 |             -4.45 |             -5.30 |
| 2025-09     |        -12.02 |        -12.42 |             -9.39 |             -9.56 |
| 2025-10     |        -12.22 |        -12.99 |             -9.94 |            -12.96 |
| 2025-11     |         -3.57 |          0.26 |              0.70 |              4.20 |
| 2025-12     |         -9.08 |        -11.01 |             -6.23 |             -9.21 |
| 2026-01     |        -10.25 |         -8.43 |             -7.16 |             -5.86 |
| 2026-02     |         -6.94 |         -3.97 |             -6.73 |             -1.98 |
| 2026-03     |        -11.66 |         -8.60 |             -7.49 |             -4.85 |
| 2026-04     |         -6.92 |         -9.36 |             -4.10 |             -7.17 |
| 2026-05     |         -9.12 |         -8.54 |             -6.92 |             -8.16 |
| 2026-06     |         -7.39 |         -2.49 |             -6.93 |             -1.45 |
| 2026-07     |         -9.13 |        -12.79 |             -5.70 |             -8.69 |
| 2026-08     |         -5.94 |         -5.25 |             -3.19 |             -2.74 |
| 2026-09     |         -4.81 |         -7.23 |             -2.62 |             -4.85 |
| 2026-10     |         -6.27 |         -6.35 |             -5.13 |             -6.51 |

## Data quality and limitations
- Source 1m rows: 992,160; span 2025-01-01 00:00:00+00:00 to 2026-11-20 23:59:00+00:00
- Historical missing-data gaps: []
- Months with incomplete IST source: [('2025-01', 330)]
- Candidate completed 5m aligned EMA crosses: {'complete_5m_bars': 198412, 'candidate_5m_crosses': 1643, 'long_candidates': 827, 'short_candidates': 816}
- Closed 1H and 15M confirmation; 5M signal known at bar close. Entry at next 1-minute open.
- Same-minute stop and TP: stop-first (conservative), not a known tick sequence.
- 1x fully notional account model, compounding at trade close; max drawdown sampled only at trade exit.
- 2025 and 2026 have previously been researched. 2026 is **seen recheck**, not blind out-of-sample.
- No funding, true bid/ask spread, slippage variability, margin, liquidation, or market depth model.
- Some months may be partial due source gaps. Missing candles were not reconstructed.

## Files
- trade_ledger.csv; monthly_results.csv; summary.csv; quality.json
