# Delta India ETHUSD positioning and structure: institutional-style proxies

## Executive result
Price/OI/mark/funding history is **not** identity-tagged institutional order flow; OI increases cannot label long/short aggressors; OHLCV does not reveal liquidations.
The objective is to test if patterns with *positioning proxies* improve signal expectancy and entry quality relative to price-only breakout/sweep controls.

## Data & chronology
{
  "future_minutes": 987840,
  "mark_minutes": 987840,
  "oi_5m": 197568,
  "funding_hours": 16464,
  "monthly_partitions": {
    "futures": 23,
    "mark": 23,
    "oi": 23,
    "funding": 23
  },
  "first_utc": "2025-01-01 00:00:00+00:00",
  "last_utc": "2026-11-17 23:59:00+00:00",
  "zero_volume_futures_minutes": 1887,
  "features": {
    "oi30_pct_p01_p50_p99": [
      -13.54776,
      0.29212,
      10.85416
    ],
    "basis_bp_p01_p50_p99": [
      -2.8326,
      0.0852,
      3.0423
    ],
    "funding_p01_p50_p99": [
      -0.01040584,
      0.01,
      0.01
    ],
    "non_null_funding_aligned": 197557,
    "positive_oi_readings": 197568
  },
  "signals": 37317,
  "replay_trades": 223902,
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
| oi_drop_bear_trend          | tp1500_sl650_8h |           1272 |           -10.81 |                 661 |                -10.84 |              497 |             -11.54 |                          -15.22 |
| oi_drop_bear_trend          | tp1000_sl500_8h |           1272 |           -10.76 |                 661 |                -10.84 |              497 |             -11.54 |                          -15.22 |
| benchmark_breakout_2h       | tp1500_sl650_8h |           2316 |           -10.53 |                1160 |                -11.41 |              878 |             -13.47 |                          -15.87 |
| benchmark_breakout_2h       | tp1000_sl500_8h |           2316 |           -10.54 |                1160 |                -11.41 |              878 |             -13.47 |                          -15.87 |
| oi_drop_bull_trend          | tp1000_sl500_8h |            837 |           -11.66 |                 376 |                 -8.96 |              257 |             -13.3  |                          -20.27 |
| oi_add_price_fall_breakdown | tp1000_sl500_8h |            127 |           -11.32 |                  51 |                -11.69 |               34 |             -23.24 |                          -32.39 |
| oi_add_price_fall_breakdown | tp1500_sl650_8h |            127 |           -11.32 |                  51 |                -11.69 |               34 |             -23.24 |                          -32.39 |
| oi_drop_down_squeeze_proxy  | tp500_sl350_4h  |            886 |           -11.75 |                 461 |                -10.96 |              354 |             -14.13 |                          -17.27 |
| oi_drop_bull_trend          | tp1500_sl650_8h |            837 |           -11.84 |                 376 |                 -8.96 |              257 |             -13.3  |                          -20.27 |
| prevday_sweep_fade_oi_drop  | time2h_sl400    |            342 |           -11.85 |                 162 |                -10.24 |              140 |             -12.01 |                          -15.1  |
| prevday_sweep_fade_oi_drop  | tp300_sl250_2h  |            342 |           -11.85 |                 162 |                -10.24 |              140 |             -12.01 |                          -15.1  |
| oi_drop_bull_trend          | time4h_sl600    |            837 |           -11.88 |                 376 |                -10.27 |              257 |             -11.95 |                          -16.29 |
| oi_drop_bull_trend          | tp500_sl350_4h  |            837 |           -11.89 |                 376 |                -10.27 |              257 |             -11.95 |                          -16.29 |
| oi_drop_bear_trend          | tp500_sl350_4h  |           1272 |           -10.65 |                 661 |                -12    |              497 |             -12.39 |                          -14.64 |
| oi_drop_bear_trend          | time4h_sl600    |           1272 |           -11.5  |                 661 |                -12    |              497 |             -12.39 |                          -14.64 |

Pairs positive in BOTH training and validation, with sample requirements: **0**.

The holdout 95% lower values use calendar-day block bootstrap of trade returns and are exploratory, not multiple-testing adjusted.

## US/London/Asia session comparison for leading setup
| period     | session      |   n |   mean_net |   win_pct |
|:-----------|:-------------|----:|-----------:|----------:|
| holdout    | Asia_evening | 126 |     -14.51 |     26.98 |
| holdout    | London_preUS | 150 |     -10.54 |     30    |
| holdout    | NY_late      |  73 |     -13.2  |     28.77 |
| holdout    | US_regular   | 148 |      -9.19 |     25    |
| train      | Asia_evening | 291 |     -10.31 |     37.46 |
| train      | London_preUS | 412 |     -12.97 |     40.29 |
| train      | NY_late      | 139 |     -13.86 |     31.65 |
| train      | US_regular   | 430 |      -8.09 |     35.58 |
| validation | Asia_evening | 161 |     -11.23 |     36.65 |
| validation | London_preUS | 212 |      -6.52 |     35.85 |
| validation | NY_late      |  76 |      -8.61 |     30.26 |
| validation | US_regular   | 212 |     -15.67 |     26.89 |

## Interpretation / audit
- Regime names are market-behavior PROXIES. Rising OI + rising price does NOT establish institutional long accumulation; there is a long and a short in every derivatives contract.
- Descending OI with big moves may reflect de-risking, closing of either side, expiration/venue effects; not proof of liquidations.
- Positive historical mean is insufficient without fee stress, sample uncertainty and forward paper-trading on newer dates.
- Baseline 2h breakout and 2h sweep are retained as price-only controls.
- Avoid choosing a result only because it looks best in July-Oct: that is data snooping.

Outputs: quality.json, feature_observations.csv, candidate_signals.csv, all_exit_trades.csv, all_results.csv, preselected_holdout_results.csv, full_train_validation_rank.csv, session_results.csv.
