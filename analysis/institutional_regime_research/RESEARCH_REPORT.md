# Delta India BTCUSD positioning and structure: institutional-style proxies

## Executive result
Price/OI/mark/funding history is **not** identity-tagged institutional order flow; OI increases cannot label long/short aggressors; OHLCV does not reveal liquidations.
The objective is to test if patterns with *positioning proxies* improve signal expectancy and entry quality relative to price-only breakout/sweep controls.

## Data & chronology
{
  "future_minutes": 943200,
  "mark_minutes": 943200,
  "oi_5m": 188640,
  "funding_hours": 15720,
  "monthly_partitions": {
    "futures": 22,
    "mark": 22,
    "oi": 22,
    "funding": 22
  },
  "first_utc": "2025-01-01 00:00:00+00:00",
  "last_utc": "2026-10-17 23:59:00+00:00",
  "zero_volume_futures_minutes": 1819,
  "features": {
    "oi30_pct_p01_p50_p99": [
      -13.87585,
      0.26353,
      11.53915
    ],
    "basis_bp_p01_p50_p99": [
      -1.9771,
      0.0157,
      2.14
    ],
    "funding_p01_p50_p99": [
      -0.00753898,
      0.01,
      0.01
    ],
    "non_null_funding_aligned": 188629,
    "positive_oi_readings": 188640
  },
  "signals": 36029,
  "replay_trades": 216174,
  "setups": 21,
  "eligible_entry_exit_pairs": 126,
  "positive_both_early": 0,
  "candidates_selected_by_early_periods": 15
}

Native futures 1m plus mark 1m, OI 5m, funding 1h. Futures entry modeled at first available one-minute OPEN after completely closed five-minute signal bar.
Funding H-hour candle is used only AFTER hour H+1 begins, without same-hour lookahead. Mark basis uses previous complete 1-minute candle.
Signals use no future data; 2h cooldown independently per strategy. Independent setup rows may overlap; results are NOT an aggregated portfolio.
A funding OHLC candle is not a realized individual funding payment, and the study's trading cost does not include position funding.

## Fixed execution scenarios
+300/-250 max2h, +500/-350 max4h, +1000/-500 max8h, +1500/-650 max8h, time2h/-400, time4h/-600.
Taker 0.05% each side; 18% GST applied to fee; adverse 5 BTC-point slippage per side. No real L2 execution history, financing/funding cost, liquidation or account sizing.
Same-minute conflicting stop/target takes stop (conservative); no intraminute order inferred.
All outcomes are BTC PRICE POINTS per 1 BTC notional exposure, not account-dollar P&L.

## Preselected candidates versus chronological holdout
Select by greater of none: only train/validation minimum mean; never rank on holdout. Holdout periods have been examined in earlier unrelated studies, so NOT globally untouched.
| setup                       | exit_rule       |   trades_train |   mean_net_train |   trades_validation |   mean_net_validation |   trades_holdout |   mean_net_holdout |   holdout_day_bootstrap_lower95 |
|:----------------------------|:----------------|---------------:|-----------------:|--------------------:|----------------------:|-----------------:|-------------------:|--------------------------------:|
| oi_add_price_fall_breakdown | time4h_sl600    |            119 |           -26.88 |                  61 |                 -1.44 |               24 |            -308.71 |                         -423.74 |
| oi_add_price_fall_breakdown | tp1500_sl650_8h |            119 |           -66.08 |                  61 |                -21.55 |               24 |            -151.03 |                         -411.81 |
| low_basis_sweep_fade        | tp1500_sl650_8h |            212 |           -75.55 |                 103 |                -77.86 |               70 |             -88.35 |                         -258.98 |
| low_basis_sweep_fade        | time2h_sl400    |            212 |           -90.42 |                 103 |                -84.83 |               70 |            -102.06 |                         -176.41 |
| high_basis_sweep_fade       | time4h_sl600    |            182 |           -90.74 |                  82 |                -40.77 |               60 |            -236.7  |                         -334    |
| high_basis_sweep_fade       | time2h_sl400    |            182 |           -93.2  |                  82 |                -70.98 |               60 |            -216.13 |                         -282.55 |
| oi_add_price_fall_breakdown | tp1000_sl500_8h |            119 |           -97.25 |                  61 |                -86.53 |               24 |            -160.87 |                         -361.63 |
| low_basis_sweep_fade        | time4h_sl600    |            212 |          -100.58 |                 103 |                -29.29 |               70 |             -89.22 |                         -217.99 |
| oi_add_bear_trend           | time4h_sl600    |            356 |           -70.86 |                 170 |               -107.68 |              108 |            -149.68 |                         -232.97 |
| oi_add_bear_trend           | tp500_sl350_4h  |            356 |          -109.33 |                 170 |               -100.11 |              108 |            -115.31 |                         -182.16 |
| funding_crowded_long_fade   | tp300_sl250_2h  |           1155 |          -113.99 |                 473 |                -96.81 |              390 |             -99.54 |                         -122.82 |
| high_basis_sweep_fade       | tp1500_sl650_8h |            182 |          -115.74 |                  82 |                -88.32 |               60 |            -203.37 |                         -347.37 |
| oi_add_bear_trend           | tp300_sl250_2h  |            356 |          -116.18 |                 170 |                -72.05 |              108 |             -89.22 |                         -133.23 |
| funding_crowded_long_fade   | tp500_sl350_4h  |           1155 |          -116.31 |                 473 |                -58.89 |              390 |            -113.66 |                         -150.89 |
| high_basis_sweep_fade       | tp500_sl350_4h  |            182 |          -118.62 |                  82 |                  4.3  |               60 |            -213.52 |                         -286.68 |

Pairs positive in BOTH training and validation, with sample requirements: **0**.

The holdout 95% lower values use calendar-day block bootstrap of trade returns and are exploratory, not multiple-testing adjusted.

## US/London/Asia session comparison for leading setup
| period     | session      |   n |   mean_net |   win_pct |
|:-----------|:-------------|----:|-----------:|----------:|
| holdout    | Asia_evening |  10 |    -263.88 |     20    |
| holdout    | London_preUS |   7 |    -348.43 |     14.29 |
| holdout    | US_regular   |   7 |    -333.03 |      0    |
| train      | Asia_evening |  39 |      88.48 |     51.28 |
| train      | London_preUS |  32 |    -193.58 |     31.25 |
| train      | NY_late      |   4 |     191.18 |     50    |
| train      | US_regular   |  44 |     -27.72 |     38.64 |
| validation | Asia_evening |  17 |     -44.72 |     41.18 |
| validation | London_preUS |  21 |     223.48 |     42.86 |
| validation | US_regular   |  23 |    -174.82 |     34.78 |

## Interpretation / audit
- Regime names are market-behavior PROXIES. Rising OI + rising price does NOT establish institutional long accumulation; there is a long and a short in every derivatives contract.
- Descending OI with big moves may reflect de-risking, closing of either side, expiration/venue effects; not proof of liquidations.
- Positive historical mean is insufficient without fee stress, sample uncertainty and forward paper-trading on newer dates.
- Baseline 2h breakout and 2h sweep are retained as price-only controls.
- Avoid choosing a result only because it looks best in July-Oct: that is data snooping.

Outputs: quality.json, feature_observations.csv, candidate_signals.csv, all_exit_trades.csv, all_results.csv, preselected_holdout_results.csv, full_train_validation_rank.csv, session_results.csv.
