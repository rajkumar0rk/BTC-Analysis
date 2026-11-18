# Delta India ETHUSD positioning and structure: institutional-style proxies

## Executive result
Price/OI/mark/funding history is **not** identity-tagged institutional order flow; OI increases cannot label long/short aggressors; OHLCV does not reveal liquidations.
The objective is to test if patterns with *positioning proxies* improve signal expectancy and entry quality relative to price-only breakout/sweep controls.

## Data & chronology
{
  "future_minutes": 963360,
  "mark_minutes": 963360,
  "oi_5m": 192672,
  "funding_hours": 16056,
  "monthly_partitions": {
    "futures": 22,
    "mark": 22,
    "oi": 22,
    "funding": 22
  },
  "first_utc": "2025-01-01 00:00:00+00:00",
  "last_utc": "2026-10-31 23:59:00+00:00",
  "zero_volume_futures_minutes": 1887,
  "features": {
    "oi30_pct_p01_p50_p99": [
      -13.61723,
      0.29456,
      10.93343
    ],
    "basis_bp_p01_p50_p99": [
      -2.8574,
      0.0843,
      3.071
    ],
    "funding_p01_p50_p99": [
      -0.01040584,
      0.01,
      0.01
    ],
    "non_null_funding_aligned": 192661,
    "positive_oi_readings": 192672
  },
  "signals": 36471,
  "replay_trades": 218826,
  "setups": 21,
  "eligible_entry_exit_pairs": 120,
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
| prevday_sweep_fade_oi_drop  | time4h_sl600    |            342 |           -47.15 |                 162 |                -34.29 |              129 |             -80.07 |                         -166.86 |
| prevday_sweep_fade_oi_drop  | time2h_sl400    |            342 |           -55.98 |                 162 |                -51.59 |              129 |             -44.46 |                         -110.36 |
| prevday_sweep_fade_oi_drop  | tp1500_sl650_8h |            342 |           -50.59 |                 162 |                -56.87 |              129 |             -43.76 |                         -169.92 |
| oi_drop_bear_trend          | time4h_sl600    |           1272 |           -66.07 |                 661 |                -46.16 |              434 |            -102.21 |                         -153.09 |
| oi_add_price_fall_breakdown | tp300_sl250_2h  |            127 |           -71.79 |                  51 |                -43.13 |               30 |            -194.52 |                         -278.22 |
| oi_drop_bull_trend          | time4h_sl600    |            837 |           -75.25 |                 376 |                -42.44 |              232 |             -84.21 |                         -188.16 |
| oi_add_bear_trend           | tp500_sl350_4h  |            361 |           -75.42 |                 172 |                -64.89 |               96 |            -148.76 |                         -211.29 |
| oi_drop_bull_trend          | tp1000_sl500_8h |            837 |           -76.96 |                 376 |                -53.15 |              232 |            -104.3  |                         -185.36 |
| low_basis_sweep_fade        | tp1000_sl500_8h |            171 |           -77.99 |                  83 |                -42.92 |               52 |            -112.43 |                         -225.66 |
| oi_drop_bull_trend          | tp1500_sl650_8h |            837 |           -61.12 |                 376 |                -78.69 |              232 |            -142.08 |                         -247.59 |
| oi_add_price_fall_breakdown | time4h_sl600    |            127 |           -73.43 |                  51 |                -78.8  |               30 |            -334.29 |                         -482.77 |
| oi_add_bear_trend           | time2h_sl400    |            361 |           -25.3  |                 172 |                -79.2  |               96 |            -112.99 |                         -187.97 |
| low_basis_sweep_fade        | time4h_sl600    |            171 |           -79.79 |                  83 |                -54    |               52 |             -33.27 |                         -179.2  |
| prevday_sweep_fade_oi_drop  | tp1000_sl500_8h |            342 |           -42.67 |                 162 |                -81.74 |              129 |             -60.04 |                         -162.88 |
| prevday_sweep_fade_oi_add   | tp300_sl250_2h  |            206 |           -83.36 |                  96 |                -77.73 |               67 |             -45.29 |                         -100.35 |

Pairs positive in BOTH training and validation, with sample requirements: **0**.

The holdout 95% lower values use calendar-day block bootstrap of trade returns and are exploratory, not multiple-testing adjusted.

## US/London/Asia session comparison for leading setup
| period     | session      |   n |   mean_net |   win_pct |
|:-----------|:-------------|----:|-----------:|----------:|
| holdout    | Asia_evening |  33 |     -37.33 |     45.45 |
| holdout    | London_preUS |  40 |    -270.25 |     27.5  |
| holdout    | NY_late      |  14 |     156    |     78.57 |
| holdout    | US_regular   |  42 |     -11.21 |     45.24 |
| train      | Asia_evening |  78 |       6.43 |     42.31 |
| train      | London_preUS |  80 |    -131.33 |     31.25 |
| train      | NY_late      |  35 |     125.82 |     40    |
| train      | US_regular   | 149 |     -70.62 |     32.89 |
| validation | Asia_evening |  31 |     -78.79 |     35.48 |
| validation | London_preUS |  43 |     -49.84 |     39.53 |
| validation | NY_late      |  21 |     120.37 |     52.38 |
| validation | US_regular   |  67 |     -52.19 |     47.76 |

## Interpretation / audit
- Regime names are market-behavior PROXIES. Rising OI + rising price does NOT establish institutional long accumulation; there is a long and a short in every derivatives contract.
- Descending OI with big moves may reflect de-risking, closing of either side, expiration/venue effects; not proof of liquidations.
- Positive historical mean is insufficient without fee stress, sample uncertainty and forward paper-trading on newer dates.
- Baseline 2h breakout and 2h sweep are retained as price-only controls.
- Avoid choosing a result only because it looks best in July-Oct: that is data snooping.

Outputs: quality.json, feature_observations.csv, candidate_signals.csv, all_exit_trades.csv, all_results.csv, preselected_holdout_results.csv, full_train_validation_rank.csv, session_results.csv.
