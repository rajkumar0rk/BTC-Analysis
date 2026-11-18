# BTC ETH other-asset completed 4H confirmation differential

**Partial-overlap exploratory research, not novel base strategy or forward validation.**
Same entry/exit/ATR/stop/target parameters for BTC and ETH. 24 models each; 2025-selected candidates cross-checked in both markets.

## Top models by count of monthly PF >=1.5 AND monthly NET return >=5%

| market   | model                                                             |   profit_factor |   net_return_pct |   months_pf15_net5 |   months_pf15_net10 |   positive_months |   trades |   max_closed_trade_drawdown_pct |   full_2025_net_pct |   jan_oct_2026_ytd_pct | full_2025_gt500   |
|:---------|:------------------------------------------------------------------|----------------:|-----------------:|-------------------:|--------------------:|------------------:|---------:|--------------------------------:|--------------------:|-----------------------:|:------------------|
| BTCUSD   | 15min:trend_retest__cross_direction_agree__SL2.5_RR3              |         1.101   |          2.77351 |                  1 |                   0 |                10 |       74 |                       -5.97264  |             3.54541 |              -0.745468 | False             |
| ETHUSD   | 4h:engulfing_reversal__cross_direction_agree__SL1.5_RR3           |         1.21327 |         12.0482  |                  0 |                   0 |                13 |      190 |                       -6.49283  |            11.4197  |               0.56405  | False             |
| BTCUSD   | 15min:trend_retest__cross_direction_and_body_035atr__SL2.5_RR3    |         1.68898 |          9.41942 |                  0 |                   0 |                11 |       46 |                       -2.0657   |             5.10783 |               4.10206  | False             |
| ETHUSD   | 4h:engulfing_reversal__cross_direction_agree__SL2.5_RR3           |         1.28989 |          9.36839 |                  0 |                   0 |                13 |      161 |                       -4.1478   |             6.20159 |               2.98188  | False             |
| BTCUSD   | 15min:trend_retest__cross_direction_and_body_035atr__SL2.5_RR2    |         1.72655 |          8.91572 |                  0 |                   0 |                13 |       47 |                       -2.54901  |             5.22748 |               3.50502  | False             |
| ETHUSD   | 4h:engulfing_reversal__cross_direction_agree__SL2.5_RR2           |         1.25255 |          8.18791 |                  0 |                   0 |                15 |      167 |                       -4.14216  |             6.70144 |               1.39311  | False             |
| ETHUSD   | 4h:engulfing_reversal__cross_direction_and_body_035atr__SL2.5_RR3 |         1.24808 |          7.44958 |                  0 |                   0 |                11 |      143 |                       -6.67033  |             7.33463 |               0.107096 | False             |
| ETHUSD   | 4h:engulfing_reversal__cross_direction_agree__SL1.5_RR2           |         1.11398 |          6.47532 |                  0 |                   0 |                13 |      199 |                       -6.48841  |             7.65795 |              -1.09851  | False             |
| ETHUSD   | 4h:engulfing_reversal__cross_direction_and_body_035atr__SL1.5_RR3 |         1.12029 |          6.38892 |                  0 |                   0 |                12 |      172 |                       -8.95075  |             8.59153 |              -2.02834  | False             |
| ETHUSD   | 4h:engulfing_reversal__cross_direction_and_body_035atr__SL2.5_RR2 |         1.18507 |          5.59115 |                  0 |                   0 |                13 |      149 |                       -6.78504  |             7.83982 |              -2.0852   | False             |
| ETHUSD   | 1h:failed_auction__cross_direction_and_body_035atr__SL1.5_RR2     |        10.5552  |          5.27658 |                  0 |                   0 |                 7 |        8 |                       -0.534672 |             4.33471 |               0.902742 | False             |
| ETHUSD   | 1h:failed_auction__cross_direction_agree__SL1.5_RR2               |         2.21365 |          5.20361 |                  0 |                   0 |                 9 |       20 |                       -1.18109  |             5.03619 |               0.15939  | False             |

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
  "cross_modes": [
    "direction_agree",
    "direction_and_body_035atr"
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
  "novelty": "Partial overlap: cross-asset confirmation only; prior family entries and exits reused",
  "monthly_equity": "exit-based, positions closed at month boundaries by replay"
}
