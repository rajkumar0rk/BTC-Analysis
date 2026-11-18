# BTC ETH completed 4H standardized relative-return dispersion differential

**Partial-overlap exploratory research, not novel base strategy or forward validation.**
Same entry/exit/ATR/stop/target parameters for BTC and ETH. 24 models each; 2025-selected candidates cross-checked in both markets. Dispersion compares each market 4H log return divided by its lagged 20-bar volatility; leader vs laggard threshold 0.75.

## Top models by count of monthly PF >=1.5 AND monthly NET return >=5%

| market   | model                                                        |   profit_factor |   net_return_pct |   months_pf15_net5 |   months_pf15_net10 |   positive_months |   trades |   max_closed_trade_drawdown_pct |   full_2025_net_pct |   jan_oct_2026_ytd_pct | full_2025_gt500   |
|:---------|:-------------------------------------------------------------|----------------:|-----------------:|-------------------:|--------------------:|------------------:|---------:|--------------------------------:|--------------------:|-----------------------:|:------------------|
| ETHUSD   | 4h:engulfing_reversal__cross_relative_leader_z075__SL1.5_RR2 |         1.51936 |          7.76012 |                  0 |                   0 |                14 |       58 |                       -2.67007  |            6.46695  |               1.21462  | False             |
| ETHUSD   | 4h:engulfing_reversal__cross_relative_leader_z075__SL1.5_RR3 |         1.44823 |          6.88633 |                  0 |                   0 |                14 |       57 |                       -2.67007  |            5.89322  |               0.937838 | False             |
| BTCUSD   | 15min:trend_retest__cross_relative_leader_z075__SL1.5_RR3    |         2.07293 |          3.56677 |                  0 |                   0 |                 5 |       11 |                       -2.11832  |            0.561477 |               2.98852  | False             |
| ETHUSD   | 15min:trend_retest__cross_relative_leader_z075__SL1.5_RR3    |         2.4768  |          3.51065 |                  0 |                   0 |                 5 |        9 |                       -1.16837  |            4.08743  |              -0.554128 | False             |
| BTCUSD   | 15min:trend_retest__cross_relative_leader_z075__SL2.5_RR2    |         2.73135 |          3.36775 |                  0 |                   0 |                 6 |       11 |                       -0.618442 |            1.44112  |               1.89926  | False             |
| BTCUSD   | 15min:trend_retest__cross_relative_leader_z075__SL1.5_RR2    |         2.21681 |          3.32305 |                  0 |                   0 |                 6 |       11 |                       -2.11832  |           -0.428201 |               3.76738  | False             |
| BTCUSD   | 15min:trend_retest__cross_relative_leader_z075__SL2.5_RR3    |         2.16655 |          3.09376 |                  0 |                   0 |                 5 |       11 |                       -1.87339  |            0.924821 |               2.14906  | False             |
| ETHUSD   | 15min:trend_retest__cross_relative_leader_z075__SL1.5_RR2    |         2.72356 |          3.01625 |                  0 |                   0 |                 5 |        9 |                       -0.596253 |            3.59027  |              -0.554128 | False             |
| ETHUSD   | 15min:trend_retest__cross_relative_leader_z075__SL2.5_RR2    |         2.21542 |          2.05918 |                  0 |                   0 |                 5 |        9 |                       -0.572519 |            2.6057   |              -0.532635 | False             |
| ETHUSD   | 1h:failed_auction__cross_relative_laggard_z075__SL1.5_RR2    |         1.32499 |          1.62628 |                  0 |                   0 |                 5 |       18 |                       -1.6672   |            2.45491  |              -0.808782 | False             |
| ETHUSD   | 4h:engulfing_reversal__cross_relative_leader_z075__SL2.5_RR2 |         1.1238  |          1.42286 |                  0 |                   0 |                12 |       55 |                       -3.01533  |            1.8526   |              -0.421922 | False             |
| ETHUSD   | 15min:trend_retest__cross_relative_leader_z075__SL2.5_RR3    |         1.55225 |          1.21654 |                  0 |                   0 |                 4 |        9 |                       -1.09873  |            1.75854  |              -0.532635 | False             |

## Limitations

{
  "original_data_sha256_verified": true,
  "markets": [
    "BTCUSD",
    "ETHUSD"
  ],
  "families": [
    "4h:engulfing_reversal",
    "15min:trend_retest",
    "1h:failed_auction"
  ],
  "dispersion_modes": [
    "relative_leader_z075",
    "relative_laggard_z075"
  ],
  "models_per_market": 24,
  "2025_train_only_selection": true,
  "2026_not_pristine_oos": true,
  "fee_each_side": 0.0005,
  "GST_on_fee": 0.18,
  "BTC_slip_each_side_points": 5,
  "ETH_slip_each_side_fraction": 0.0002,
  "risk_per_stop": 0.005,
  "notional_leverage_cap": 3.0,
  "first_IST_month_missing": "Jan2025 first 5.5h absent",
  "omitted": [
    "funding",
    "verified spread",
    "market impact",
    "lot sizes",
    "liquidation/margin",
    "actual fills"
  ],
  "novelty": "Partial overlap: standardized cross-market 4H relative-return dispersion filter; prior family entries and exits reused",
  "monthly_equity": "exit-based, positions closed at month boundaries by replay"
}
