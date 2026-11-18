# Stage 9 — Adaptive entry discovery from closed BTC candles

## Method
Any-time model with NO hour, weekday or session inputs. 33 completed-bar
price/volume/volatility features from 5m ETHUSD futures candles.
Train Jan-Sep 2025; select cutoff Oct-Dec 2025; report 2026
chronologically without adjusting decisions after seeing later results.
Classification goal: net +200 before -100 within 30m, stop-first.

## Prediction skill
| side   | period          |     n |   hit_rate |      auc |   average_precision |   mean_pred |   top_decile_label_rate |
|:-------|:----------------|------:|-----------:|---------:|--------------------:|------------:|------------------------:|
| LONG   | train           | 78282 |       0.01 |   0.9999 |              0.7411 |      0.0001 |                    0.14 |
| LONG   | select_2025Q4   | 26265 |       0.01 |   0.9519 |              0.0015 |      0.0001 |                    0.11 |
| LONG   | check_2026H1    | 51916 |       0    | nan      |            nan      |      0.0001 |                    0    |
| LONG   | recheck_2026H2  | 35304 |       0    |   0.9647 |              0.0008 |      0.0001 |                    0.02 |
| LONG   | november_recent |  4801 |       0    | nan      |            nan      |      0.0001 |                    0    |
| SHORT  | train           | 78282 |       0.02 |   0.9993 |              0.526  |      0.0002 |                    0.22 |
| SHORT  | select_2025Q4   | 26265 |       0.03 |   0.8405 |              0.0029 |      0.0002 |                    0.19 |
| SHORT  | check_2026H1    | 51916 |       0    | nan      |            nan      |      0.0002 |                    0    |
| SHORT  | recheck_2026H2  | 35304 |       0    | nan      |            nan      |      0.0002 |                    0    |
| SHORT  | november_recent |  4801 |       0    | nan      |            nan      |      0.0002 |                    0    |

## Chosen probability cutoff
| side   |   selected_threshold |   selection_trades | selection_net   |
|:-------|---------------------:|-------------------:|:----------------|
| LONG   |                  0.5 |                  0 |                 |
| SHORT  |                  0.5 |                  0 |                 |

## Independently replayed net trading outcomes
| side   | period          | cutoff_model      |   threshold | tp_model   |   trades |   mean_net_pts |   profit_factor |   wins |   losses |   win_pct |   sum_net_pts |   whatif_avg_pts |
|:-------|:----------------|:------------------|------------:|:-----------|---------:|---------------:|----------------:|-------:|---------:|----------:|--------------:|-----------------:|
| LONG   | train           | trained_threshold |     0.5     | gross200   |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| LONG   | train           | trained_threshold |     0.5     | net200     |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| LONG   | train           | baseline_top10pct |     6e-05   | gross200   |     2767 |         -13.53 |           0.144 |    388 |     2379 |     14.02 |     -37443    |           -11.82 |
| LONG   | train           | baseline_top10pct |     6e-05   | net200     |     2767 |         -13.52 |           0.145 |    388 |     2379 |     14.02 |     -37415.1  |           -11.81 |
| LONG   | select_2025Q4   | trained_threshold |     0.5     | gross200   |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| LONG   | select_2025Q4   | trained_threshold |     0.5     | net200     |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| LONG   | select_2025Q4   | baseline_top10pct |     6e-05   | gross200   |      922 |         -14.54 |           0.195 |    163 |      759 |     17.68 |     -13406    |           -12.5  |
| LONG   | select_2025Q4   | baseline_top10pct |     6e-05   | net200     |      922 |         -14.52 |           0.196 |    163 |      759 |     17.68 |     -13391.6  |           -12.49 |
| LONG   | check_2026H1    | trained_threshold |     0.5     | gross200   |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| LONG   | check_2026H1    | trained_threshold |     0.5     | net200     |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| LONG   | check_2026H1    | baseline_top10pct |     6e-05   | gross200   |     2098 |         -12.71 |           0.075 |    216 |     1882 |     10.3  |     -26661.1  |           -11.39 |
| LONG   | check_2026H1    | baseline_top10pct |     6e-05   | net200     |     2098 |         -12.71 |           0.075 |    216 |     1882 |     10.3  |     -26661.1  |           -11.39 |
| LONG   | recheck_2026H2  | trained_threshold |     0.5     | gross200   |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| LONG   | recheck_2026H2  | trained_threshold |     0.5     | net200     |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| LONG   | recheck_2026H2  | baseline_top10pct |     6e-05   | gross200   |     1447 |         -12.51 |           0.057 |     89 |     1358 |      6.15 |     -18099.5  |           -11.19 |
| LONG   | recheck_2026H2  | baseline_top10pct |     6e-05   | net200     |     1447 |         -12.52 |           0.056 |     89 |     1358 |      6.15 |     -18121.9  |           -11.21 |
| LONG   | november_recent | trained_threshold |     0.5     | gross200   |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| LONG   | november_recent | trained_threshold |     0.5     | net200     |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| LONG   | november_recent | baseline_top10pct |     6e-05   | gross200   |      189 |         -13.9  |           0.047 |     14 |      175 |      7.41 |      -2627.02 |           -12.67 |
| LONG   | november_recent | baseline_top10pct |     6e-05   | net200     |      189 |         -13.9  |           0.047 |     14 |      175 |      7.41 |      -2627.02 |           -12.67 |
| SHORT  | train           | trained_threshold |     0.5     | gross200   |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| SHORT  | train           | trained_threshold |     0.5     | net200     |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| SHORT  | train           | baseline_top10pct |     0.00043 | gross200   |     2809 |         -13.16 |           0.16  |    411 |     2398 |     14.63 |     -36978.9  |           -11.45 |
| SHORT  | train           | baseline_top10pct |     0.00043 | net200     |     2809 |         -13.14 |           0.161 |    411 |     2398 |     14.63 |     -36922.4  |           -11.43 |
| SHORT  | select_2025Q4   | trained_threshold |     0.5     | gross200   |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| SHORT  | select_2025Q4   | trained_threshold |     0.5     | net200     |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| SHORT  | select_2025Q4   | baseline_top10pct |     0.00043 | gross200   |      968 |         -13.46 |           0.232 |    181 |      787 |     18.7  |     -13033.9  |           -11.42 |
| SHORT  | select_2025Q4   | baseline_top10pct |     0.00043 | net200     |      968 |         -13.44 |           0.234 |    181 |      787 |     18.7  |     -13005.1  |           -11.39 |
| SHORT  | check_2026H1    | trained_threshold |     0.5     | gross200   |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| SHORT  | check_2026H1    | trained_threshold |     0.5     | net200     |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| SHORT  | check_2026H1    | baseline_top10pct |     0.00043 | gross200   |     1954 |         -12.46 |           0.091 |    198 |     1756 |     10.13 |     -24339.5  |           -11.15 |
| SHORT  | check_2026H1    | baseline_top10pct |     0.00043 | net200     |     1954 |         -12.46 |           0.091 |    198 |     1756 |     10.13 |     -24339.5  |           -11.15 |
| SHORT  | recheck_2026H2  | trained_threshold |     0.5     | gross200   |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| SHORT  | recheck_2026H2  | trained_threshold |     0.5     | net200     |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| SHORT  | recheck_2026H2  | baseline_top10pct |     0.00043 | gross200   |     1202 |         -12.88 |           0.048 |     65 |     1137 |      5.41 |     -15477.1  |           -11.55 |
| SHORT  | recheck_2026H2  | baseline_top10pct |     0.00043 | net200     |     1202 |         -12.88 |           0.048 |     65 |     1137 |      5.41 |     -15477.1  |           -11.55 |
| SHORT  | november_recent | trained_threshold |     0.5     | gross200   |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| SHORT  | november_recent | trained_threshold |     0.5     | net200     |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| SHORT  | november_recent | baseline_top10pct |     0.00043 | gross200   |      200 |         -10.84 |           0.135 |     22 |      178 |     11    |      -2168.45 |            -9.61 |
| SHORT  | november_recent | baseline_top10pct |     0.00043 | net200     |      200 |         -10.84 |           0.135 |     22 |      178 |     11    |      -2168.45 |            -9.61 |

## Exploratory feature importance by 2025 selection permutation
| side   | feature           |   AP_drop |
|:-------|:------------------|----------:|
| SHORT  | distance_h24      |   0.00109 |
| SHORT  | range_6           |   0.00062 |
| SHORT  | range_24          |   0.00057 |
| SHORT  | trend_24          |   0.0005  |
| SHORT  | close_location    |   0.0003  |
| SHORT  | trend_6           |   0.0003  |
| LONG   | range_6           |   0.00024 |
| SHORT  | volume_3          |   0.00021 |
| LONG   | prior_range_ratio |   0.00016 |
| SHORT  | candle_body_frac  |   0.00014 |
| LONG   | range_2           |   0.00014 |
| SHORT  | trend_3           |   0.00012 |
| LONG   | range_3           |   0.0001  |
| LONG   | prior_close_loc   |   7e-05   |
| LONG   | volume_3          |   7e-05   |
| LONG   | volume_2          |   6e-05   |
| SHORT  | range_12          |   6e-05   |
| SHORT  | distance_h12      |   3e-05   |
| LONG   | abs_ret_12        |   3e-05   |
| LONG   | range_12          |   2e-05   |

## Interpretation
- More frequent +200 gross excursions do NOT guarantee a positive net result.
- Any positive results with tiny independent trade counts are not validated.
- All trades have known-at-entry features; zero next-bar lookahead.
- 0.05% taker per side, GST 18%, adverse 5 pts per side included.
- Scalper offer sensitivity is separate, not assumed qualified.
- No 2026 result should be treated as an untouched holdout.
- 2026 periods are research-exposed, not independent virgin holdouts
- Target labels of 5m signals overlap and overstate effective sample size
- 1m OHLC stop-first; no historical spread, fills, impact or funding
- Threshold selection among nine alternatives creates selection bias
- Model probabilities can drift with changes in BTC price/volatility
- No guarantee of profitability or zero losses
