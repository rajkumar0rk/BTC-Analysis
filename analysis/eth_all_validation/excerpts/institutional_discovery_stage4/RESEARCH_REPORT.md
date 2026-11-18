# Stage 4 — Retracement/reclaim after high-volatility BTC hours

## Predeclared question
Does a genuine first-30m retracement plus subsequent *separate completed 5m* reclaim improve
execution against the Stage 3 immediate-entry price-only baselines?
This is an execution/selection investigation, not a claim of profitability.

## Event outcomes
| rule                  | period               |   events |   days |   retest_rate |   signed_30m_pts |   signed_60m_pts |
|:----------------------|:---------------------|---------:|-------:|--------------:|-----------------:|-----------------:|
| accepted_12h_breakout | 2025_train           |      277 |    187 |         34.3  |         3.81011  |        3.15794   |
| accepted_12h_breakout | 2026_H1_validation   |      127 |     87 |         26.77 |        -0.925591 |        0.547244  |
| accepted_12h_breakout | 2026_H2_seen_recheck |       90 |     63 |         51.11 |         2.31278  |        4.93278   |
| expansion_follow      | 2025_train           |     1032 |    298 |         34.69 |         0.437936 |        1.27083   |
| expansion_follow      | 2026_H1_validation   |      610 |    162 |         31.8  |        -0.297377 |        0.0829508 |
| expansion_follow      | 2026_H2_seen_recheck |      503 |    125 |         40.16 |         0.155467 |        0.873658  |
| rejected_12h_sweep    | 2025_train           |      130 |    107 |         37.69 |        -1.50385  |       -2.58846   |
| rejected_12h_sweep    | 2026_H1_validation   |       64 |     59 |         37.5  |        -0.519531 |        1.66953   |
| rejected_12h_sweep    | 2026_H2_seen_recheck |       42 |     37 |         33.33 |        -0.25     |        6.01429   |

## Executable replay, standard taker fees + GST + 5pt slippage per side
| rule                  | style               | fee_mode       | period               |   trades |   days |   mean_net_pts |   median_net_pts |   win_pct |   profit_factor |   max_drawdown_pts |   mean_gross_pts |   mean_cost_pts |   mean_mfe_pts |   mean_mae_pts |   mean_hold_min |   ci95_low |   ci95_high |
|:----------------------|:--------------------|:---------------|:---------------------|---------:|-------:|---------------:|-----------------:|----------:|----------------:|-------------------:|-----------------:|----------------:|---------------:|---------------:|----------------:|-----------:|------------:|
| accepted_12h_breakout | immediate_all       | standard_taker | 2025_train           |      277 |    187 |        -10.53  |          -14.895 |     28.16 |           0.447 |            2916.75 |             3.16 |           13.69 |          31.98 |          22.34 |           60    |     -14.93 |       -6.63 |
| accepted_12h_breakout | immediate_all       | standard_taker | 2026_H1_validation   |      127 |     87 |        -12.051 |          -14.775 |     23.62 |           0.268 |            1530.44 |             0.55 |           12.6  |          18.29 |          15.47 |           60    |     -15.98 |       -8.52 |
| accepted_12h_breakout | immediate_all       | standard_taker | 2026_H2_seen_recheck |       90 |     63 |         -7.719 |          -11.217 |     22.22 |           0.426 |             749.97 |             4.93 |           12.65 |          19.81 |          11.96 |           60    |     -13.16 |       -2.86 |
| accepted_12h_breakout | immediate_on_retest | standard_taker | 2025_train           |       95 |     80 |         -1.13  |           -6.14  |     38.95 |           0.904 |             317.93 |            12.54 |           13.67 |          45.04 |          19.41 |           60    |      -7.58 |        5.63 |
| accepted_12h_breakout | immediate_on_retest | standard_taker | 2026_H1_validation   |       34 |     29 |         -1.365 |           -3.483 |     41.18 |           0.811 |             116.62 |            11.17 |           12.54 |          27.06 |           9.52 |           60    |      -7.26 |        4.11 |
| accepted_12h_breakout | immediate_on_retest | standard_taker | 2026_H2_seen_recheck |       46 |     37 |         -3.43  |           -8.438 |     30.43 |           0.64  |             184.68 |             9.24 |           12.67 |          22.74 |           9.02 |           60    |      -9.97 |        4.23 |
| accepted_12h_breakout | retest_fixed        | standard_taker | 2025_train           |       94 |     80 |        -12.15  |          -12.967 |     31.91 |           0.397 |            1171.38 |             1.52 |           13.67 |          34.91 |          23.94 |           60    |     -19.5  |       -5.16 |
| accepted_12h_breakout | retest_fixed        | standard_taker | 2026_H1_validation   |       32 |     29 |         -5.27  |           -8.34  |     34.38 |           0.525 |             180.34 |             7.28 |           12.55 |          23.88 |          11.68 |           60    |     -13.28 |        1.45 |
| accepted_12h_breakout | retest_fixed        | standard_taker | 2026_H2_seen_recheck |       44 |     37 |        -13.134 |          -15.039 |     15.91 |           0.177 |             601.67 |            -0.47 |           12.66 |          14.13 |          13.95 |           60    |     -16.88 |       -9.25 |
| accepted_12h_breakout | retest_structure    | standard_taker | 2025_train           |        2 |      2 |         39.621 |           39.621 |     50    |           1.386 |             205.12 |            53.16 |           13.54 |         162.35 |         149    |           63    |     nan    |      nan    |
| expansion_follow      | immediate_all       | standard_taker | 2025_train           |     1032 |    298 |        -12.309 |          -14.748 |     24.71 |           0.353 |           12703.1  |             1.27 |           13.58 |          25.81 |          22.01 |           60    |     -14.15 |      -10.43 |
| expansion_follow      | immediate_all       | standard_taker | 2026_H1_validation   |      610 |    162 |        -12.576 |          -13.697 |     17.05 |           0.181 |            7671.28 |             0.08 |           12.66 |          15.27 |          13.26 |           60    |     -14    |      -11.16 |
| expansion_follow      | immediate_all       | standard_taker | 2026_H2_seen_recheck |      503 |    125 |        -11.759 |          -13.146 |     14.31 |           0.162 |            5914.78 |             0.87 |           12.63 |          12.77 |          10.54 |           60    |     -13.32 |      -10.45 |
| expansion_follow      | immediate_on_retest | standard_taker | 2025_train           |      358 |    193 |         -4.443 |           -9.695 |     32.12 |           0.661 |            2082.54 |             9.14 |           13.59 |          33.36 |          18.89 |           60    |      -7.92 |       -1.02 |
| expansion_follow      | immediate_on_retest | standard_taker | 2026_H1_validation   |      194 |    103 |         -6.908 |           -9.612 |     23.71 |           0.335 |            1381.38 |             5.83 |           12.73 |          20.2  |          10.58 |           60    |      -9.41 |       -4.51 |
| expansion_follow      | immediate_on_retest | standard_taker | 2026_H2_seen_recheck |      202 |     92 |         -9.046 |          -10.795 |     17.33 |           0.21  |            1827.28 |             3.59 |           12.64 |          14.87 |           8.79 |           60    |     -11.27 |       -6.73 |
| expansion_follow      | retest_fixed        | standard_taker | 2025_train           |      343 |    193 |        -10.685 |          -14.088 |     27.99 |           0.418 |            3851.15 |             2.89 |           13.58 |          28.52 |          21.75 |           59.99 |     -14.27 |       -6.86 |
| expansion_follow      | retest_fixed        | standard_taker | 2026_H1_validation   |      185 |    103 |        -11.803 |          -13.022 |     21.08 |           0.197 |            2203.43 |             0.92 |           12.73 |          16.95 |          13.07 |           60    |     -14.07 |       -9.04 |
| expansion_follow      | retest_fixed        | standard_taker | 2026_H2_seen_recheck |      192 |     92 |        -13.47  |          -13.925 |     12.5  |           0.106 |            2586.27 |            -0.84 |           12.63 |          11.58 |          11.54 |           60    |     -15.41 |      -11.92 |
| expansion_follow      | retest_structure    | standard_taker | 2025_train           |        4 |      4 |         25.396 |           11.171 |     75    |           1.495 |             205.12 |            39.08 |           13.69 |         106.95 |          97.67 |           91.5  |     nan    |      nan    |
| rejected_12h_sweep    | immediate_all       | standard_taker | 2025_train           |      130 |    107 |        -16.201 |          -11.941 |     23.08 |           0.179 |            2106.8  |            -2.59 |           13.61 |          21.11 |          25.56 |           60    |     -21.02 |      -12.08 |
| rejected_12h_sweep    | immediate_all       | standard_taker | 2026_H1_validation   |       64 |     59 |        -10.988 |          -13.822 |     20.31 |           0.237 |             717.46 |             1.67 |           12.66 |          15.6  |          14.21 |           60    |     -15.08 |       -6.22 |
| rejected_12h_sweep    | immediate_all       | standard_taker | 2026_H2_seen_recheck |       42 |     37 |         -6.636 |           -8.538 |     19.05 |           0.379 |             278.72 |             6.01 |           12.65 |          14.44 |           8.59 |           60    |     -12.74 |        2.28 |
| rejected_12h_sweep    | immediate_on_retest | standard_taker | 2025_train           |       49 |     46 |         -7.188 |           -5.82  |     36.73 |           0.375 |             364.84 |             6.52 |           13.7  |          27.92 |          19.66 |           60    |     -12.63 |       -1.33 |
| rejected_12h_sweep    | immediate_on_retest | standard_taker | 2026_H1_validation   |       24 |     24 |         -8.88  |          -10.276 |     20.83 |           0.259 |             227.35 |             3.96 |           12.84 |          18.58 |          14.05 |           60    |     -14.43 |       -2.14 |
| rejected_12h_sweep    | immediate_on_retest | standard_taker | 2026_H2_seen_recheck |       14 |     14 |         -6.219 |          -10.122 |     21.43 |           0.387 |              87.06 |             6.53 |           12.75 |          15.61 |           7.05 |           60    |     nan    |      nan    |
| rejected_12h_sweep    | retest_fixed        | standard_taker | 2025_train           |       49 |     46 |        -15.345 |           -8.885 |     28.57 |           0.153 |             751.89 |            -1.64 |           13.71 |          22.44 |          22.81 |           60    |     -23.31 |       -7.69 |
| rejected_12h_sweep    | retest_fixed        | standard_taker | 2026_H1_validation   |       24 |     24 |        -14.453 |          -14.592 |     20.83 |           0.103 |             346.87 |            -1.62 |           12.84 |          14.76 |          17.5  |           60    |     -20.69 |       -7.91 |
| rejected_12h_sweep    | retest_fixed        | standard_taker | 2026_H2_seen_recheck |       14 |     14 |         -8.726 |          -13.098 |     14.29 |           0.241 |             122.17 |             4.02 |           12.75 |          13.36 |           8.09 |           60    |     nan    |      nan    |

## Counterfactual Scalper Offer sensitivity (waive close fee only for <=30m exits)
| rule                  | style               | fee_mode               | period               |   trades |   days |   mean_net_pts |   median_net_pts |   win_pct |   profit_factor |   max_drawdown_pts |   mean_gross_pts |   mean_cost_pts |   mean_mfe_pts |   mean_mae_pts |   mean_hold_min |   ci95_low |   ci95_high |
|:----------------------|:--------------------|:-----------------------|:---------------------|---------:|-------:|---------------:|-----------------:|----------:|----------------:|-------------------:|-----------------:|----------------:|---------------:|---------------:|----------------:|-----------:|------------:|
| accepted_12h_breakout | immediate_all       | scalper_counterfactual | 2025_train           |      277 |    187 |        -10.53  |          -14.895 |     28.16 |           0.447 |            2916.75 |             3.16 |           13.69 |          31.98 |          22.34 |           60    |     -14.93 |       -6.63 |
| accepted_12h_breakout | immediate_all       | scalper_counterfactual | 2026_H1_validation   |      127 |     87 |        -12.051 |          -14.775 |     23.62 |           0.268 |            1530.44 |             0.55 |           12.6  |          18.29 |          15.47 |           60    |     -15.98 |       -8.52 |
| accepted_12h_breakout | immediate_all       | scalper_counterfactual | 2026_H2_seen_recheck |       90 |     63 |         -7.719 |          -11.217 |     22.22 |           0.426 |             749.97 |             4.93 |           12.65 |          19.81 |          11.96 |           60    |     -13.16 |       -2.86 |
| accepted_12h_breakout | immediate_on_retest | scalper_counterfactual | 2025_train           |       95 |     80 |         -1.13  |           -6.14  |     38.95 |           0.904 |             317.93 |            12.54 |           13.67 |          45.04 |          19.41 |           60    |      -7.58 |        5.63 |
| accepted_12h_breakout | immediate_on_retest | scalper_counterfactual | 2026_H1_validation   |       34 |     29 |         -1.365 |           -3.483 |     41.18 |           0.811 |             116.62 |            11.17 |           12.54 |          27.06 |           9.52 |           60    |      -7.26 |        4.11 |
| accepted_12h_breakout | immediate_on_retest | scalper_counterfactual | 2026_H2_seen_recheck |       46 |     37 |         -3.43  |           -8.438 |     30.43 |           0.64  |             184.68 |             9.24 |           12.67 |          22.74 |           9.02 |           60    |      -9.97 |        4.23 |
| accepted_12h_breakout | retest_fixed        | scalper_counterfactual | 2025_train           |       94 |     80 |        -12.15  |          -12.967 |     31.91 |           0.397 |            1171.38 |             1.52 |           13.67 |          34.91 |          23.94 |           60    |     -19.5  |       -5.16 |
| accepted_12h_breakout | retest_fixed        | scalper_counterfactual | 2026_H1_validation   |       32 |     29 |         -5.27  |           -8.34  |     34.38 |           0.525 |             180.34 |             7.28 |           12.55 |          23.88 |          11.68 |           60    |     -13.28 |        1.45 |
| accepted_12h_breakout | retest_fixed        | scalper_counterfactual | 2026_H2_seen_recheck |       44 |     37 |        -13.134 |          -15.039 |     15.91 |           0.177 |             601.67 |            -0.47 |           12.66 |          14.13 |          13.95 |           60    |     -16.88 |       -9.25 |
| accepted_12h_breakout | retest_structure    | scalper_counterfactual | 2025_train           |        2 |      2 |         40.632 |           40.632 |     50    |           1.396 |             205.12 |            53.16 |           12.53 |         162.35 |         149    |           63    |     nan    |      nan    |
| expansion_follow      | immediate_all       | scalper_counterfactual | 2025_train           |     1032 |    298 |        -12.309 |          -14.748 |     24.71 |           0.353 |           12703.1  |             1.27 |           13.58 |          25.81 |          22.01 |           60    |     -14.15 |      -10.43 |
| expansion_follow      | immediate_all       | scalper_counterfactual | 2026_H1_validation   |      610 |    162 |        -12.576 |          -13.697 |     17.05 |           0.181 |            7671.28 |             0.08 |           12.66 |          15.27 |          13.26 |           60    |     -14    |      -11.16 |
| expansion_follow      | immediate_all       | scalper_counterfactual | 2026_H2_seen_recheck |      503 |    125 |        -11.759 |          -13.146 |     14.31 |           0.162 |            5914.78 |             0.87 |           12.63 |          12.77 |          10.54 |           60    |     -13.32 |      -10.45 |
| expansion_follow      | immediate_on_retest | scalper_counterfactual | 2025_train           |      358 |    193 |         -4.443 |           -9.695 |     32.12 |           0.661 |            2082.54 |             9.14 |           13.59 |          33.36 |          18.89 |           60    |      -7.92 |       -1.02 |
| expansion_follow      | immediate_on_retest | scalper_counterfactual | 2026_H1_validation   |      194 |    103 |         -6.908 |           -9.612 |     23.71 |           0.335 |            1381.38 |             5.83 |           12.73 |          20.2  |          10.58 |           60    |      -9.41 |       -4.51 |
| expansion_follow      | immediate_on_retest | scalper_counterfactual | 2026_H2_seen_recheck |      202 |     92 |         -9.046 |          -10.795 |     17.33 |           0.21  |            1827.28 |             3.59 |           12.64 |          14.87 |           8.79 |           60    |     -11.27 |       -6.73 |
| expansion_follow      | retest_fixed        | scalper_counterfactual | 2025_train           |      343 |    193 |        -10.685 |          -14.088 |     27.99 |           0.418 |            3851.15 |             2.89 |           13.58 |          28.52 |          21.75 |           59.99 |     -14.27 |       -6.86 |
| expansion_follow      | retest_fixed        | scalper_counterfactual | 2026_H1_validation   |      185 |    103 |        -11.803 |          -13.022 |     21.08 |           0.197 |            2203.43 |             0.92 |           12.73 |          16.95 |          13.07 |           60    |     -14.07 |       -9.04 |
| expansion_follow      | retest_fixed        | scalper_counterfactual | 2026_H2_seen_recheck |      192 |     92 |        -13.47  |          -13.925 |     12.5  |           0.106 |            2586.27 |            -0.84 |           12.63 |          11.58 |          11.54 |           60    |     -15.41 |      -11.92 |
| expansion_follow      | retest_structure    | scalper_counterfactual | 2025_train           |        4 |      4 |         25.901 |           11.171 |     75    |           1.505 |             205.12 |            39.08 |           13.18 |         106.95 |          97.67 |           91.5  |     nan    |      nan    |
| rejected_12h_sweep    | immediate_all       | scalper_counterfactual | 2025_train           |      130 |    107 |        -16.201 |          -11.941 |     23.08 |           0.179 |            2106.8  |            -2.59 |           13.61 |          21.11 |          25.56 |           60    |     -21.02 |      -12.08 |
| rejected_12h_sweep    | immediate_all       | scalper_counterfactual | 2026_H1_validation   |       64 |     59 |        -10.988 |          -13.822 |     20.31 |           0.237 |             717.46 |             1.67 |           12.66 |          15.6  |          14.21 |           60    |     -15.08 |       -6.22 |
| rejected_12h_sweep    | immediate_all       | scalper_counterfactual | 2026_H2_seen_recheck |       42 |     37 |         -6.636 |           -8.538 |     19.05 |           0.379 |             278.72 |             6.01 |           12.65 |          14.44 |           8.59 |           60    |     -12.74 |        2.28 |
| rejected_12h_sweep    | immediate_on_retest | scalper_counterfactual | 2025_train           |       49 |     46 |         -7.188 |           -5.82  |     36.73 |           0.375 |             364.84 |             6.52 |           13.7  |          27.92 |          19.66 |           60    |     -12.63 |       -1.33 |
| rejected_12h_sweep    | immediate_on_retest | scalper_counterfactual | 2026_H1_validation   |       24 |     24 |         -8.88  |          -10.276 |     20.83 |           0.259 |             227.35 |             3.96 |           12.84 |          18.58 |          14.05 |           60    |     -14.43 |       -2.14 |
| rejected_12h_sweep    | immediate_on_retest | scalper_counterfactual | 2026_H2_seen_recheck |       14 |     14 |         -6.219 |          -10.122 |     21.43 |           0.387 |              87.06 |             6.53 |           12.75 |          15.61 |           7.05 |           60    |     nan    |      nan    |
| rejected_12h_sweep    | retest_fixed        | scalper_counterfactual | 2025_train           |       49 |     46 |        -15.345 |           -8.885 |     28.57 |           0.153 |             751.89 |            -1.64 |           13.71 |          22.44 |          22.81 |           60    |     -23.31 |       -7.69 |
| rejected_12h_sweep    | retest_fixed        | scalper_counterfactual | 2026_H1_validation   |       24 |     24 |        -14.453 |          -14.592 |     20.83 |           0.103 |             346.87 |            -1.62 |           12.84 |          14.76 |          17.5  |           60    |     -20.69 |       -7.91 |
| rejected_12h_sweep    | retest_fixed        | scalper_counterfactual | 2026_H2_seen_recheck |       14 |     14 |         -8.726 |          -13.098 |     14.29 |           0.241 |             122.17 |             4.02 |           12.75 |          13.36 |           8.09 |           60    |     nan    |      nan    |

## Incremental OI description (not a causally controlled study)
| rule                  | period               | oi_group   |   events |   retest_rate |   direction_60m_pts |
|:----------------------|:---------------------|:-----------|---------:|--------------:|--------------------:|
| accepted_12h_breakout | 2025_train           | falling    |      150 |      0.36     |           2.779     |
| accepted_12h_breakout | 2025_train           | middle     |      106 |      0.339623 |           2.48443   |
| accepted_12h_breakout | 2025_train           | rising     |       21 |      0.238095 |           9.26429   |
| accepted_12h_breakout | 2026_H1_validation   | falling    |       79 |      0.291139 |           2.89557   |
| accepted_12h_breakout | 2026_H1_validation   | middle     |       41 |      0.219512 |          -5.02195   |
| accepted_12h_breakout | 2026_H1_validation   | rising     |        7 |      0.285714 |           6.66429   |
| accepted_12h_breakout | 2026_H2_seen_recheck | falling    |       58 |      0.534483 |           7.32241   |
| accepted_12h_breakout | 2026_H2_seen_recheck | middle     |       28 |      0.464286 |           0.698214  |
| accepted_12h_breakout | 2026_H2_seen_recheck | rising     |        4 |      0.5      |          -0.075     |
| expansion_follow      | 2025_train           | falling    |      419 |      0.355609 |           0.990095  |
| expansion_follow      | 2025_train           | middle     |      515 |      0.333981 |           1.88922   |
| expansion_follow      | 2025_train           | rising     |       98 |      0.377551 |          -0.778571  |
| expansion_follow      | 2026_H1_validation   | falling    |      255 |      0.352941 |           2.20941   |
| expansion_follow      | 2026_H1_validation   | middle     |      304 |      0.302632 |          -1.68372   |
| expansion_follow      | 2026_H1_validation   | rising     |       51 |      0.235294 |          -0.0186275 |
| expansion_follow      | 2026_H2_seen_recheck | falling    |      199 |      0.437186 |           1.8902    |
| expansion_follow      | 2026_H2_seen_recheck | middle     |      248 |      0.407258 |           0.686089  |
| expansion_follow      | 2026_H2_seen_recheck | rising     |       56 |      0.25     |          -1.90804   |
| rejected_12h_sweep    | 2025_train           | falling    |       54 |      0.388889 |           3.55741   |
| rejected_12h_sweep    | 2025_train           | middle     |       67 |      0.373134 |          -8.05672   |
| rejected_12h_sweep    | 2025_train           | rising     |        9 |      0.333333 |           1.24444   |
| rejected_12h_sweep    | 2026_H1_validation   | falling    |       27 |      0.481481 |           2.86852   |
| rejected_12h_sweep    | 2026_H1_validation   | middle     |       33 |      0.30303  |           1.87879   |
| rejected_12h_sweep    | 2026_H1_validation   | rising     |        4 |      0.25     |          -8.15      |
| rejected_12h_sweep    | 2026_H2_seen_recheck | falling    |       19 |      0.263158 |           6.53158   |
| rejected_12h_sweep    | 2026_H2_seen_recheck | middle     |       20 |      0.3      |           4.405     |
| rejected_12h_sweep    | 2026_H2_seen_recheck | rising     |        3 |      1        |          13.4667    |

## Reproduction and caution
- Source: scripts/research_retest_reclaim_stage4.py; Stage 2 shared feature builder.
- immediate_all = first available hourly open, fixed TP 500 / SL 350 / 60m max.
- immediate_on_retest = same fixed execution, restricted to events that LATER met the retest condition; diagnostic only, NOT actionable ex ante.
- retest_fixed = 5m reclaim -> next 1m open; TP 500 / SL 350 / 60m max.
- retest_structure = same reclaim; already-observed swing stop, target 1.5R, 120m max.
- Only one position at a time within each independently measured style/rule.
- All 2026 data have been studied before. Do not call any of it an untouched holdout.
- Standard taker scenario is conservative relative to an eligible closing-fee offer; spread and impact unknown.
- Missing funding, quote-based costs and truly forward data prevent live-deployment claims.
- Retest eligibility is determined by future path; compare only executable retest entries as prospective strategies.

## Research verdict
No result is selected or optimized automatically. Examine the sign, sample sizes, and consistency
across the first two periods and the *previously seen* 2026 H2 recheck. Preserve negative runs.
Next genuinely independent test requires data collected AFTER the research freeze, with parameters locked.
