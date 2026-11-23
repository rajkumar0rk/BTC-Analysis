# BTCUSD 15M Reclaim SHORT-only — cost sensitivity

Fixed signal choices from prior 22-month experiment. This is sensitivity, not additional entry optimisation.
SHORT only; 15m ST(10,3), EMA20, reclaim within 4 completed 15m bars, 15m volume compared to previous 20 15m bars. One entry per ST regime.
1x notional, $1000 initial. 1m OHLC price paths only for exits. Opposite confirmed ST flip / 1R stop / 3R TP.
Jan 2025–Oct 2026 already used for selection: **not** a true out-of-sample test.

## Costs
Each cost case lists (fee including 18% GST per side, adverse slip per side).

{
  "base_taker05_slip02": [
    0.00059,
    0.0002
  ],
  "same_fee_slip04": [
    0.00059,
    0.0004
  ],
  "same_fee_slip06": [
    0.00059,
    0.0006
  ],
  "taker075_slip04": [
    0.0008849999999999999,
    0.0004
  ]
}

## Results (O-H-L-C assumed 1m path)

| config          | cost_case           |   trades |   wins |   win_rate_pct |   profit_factor |   net_return_pct |   profitable_months |   return_2025_pct |   return_2026_pct |   max_floating_drawdown_pct |
|:----------------|:--------------------|---------:|-------:|---------------:|----------------:|-----------------:|--------------------:|------------------:|------------------:|----------------------------:|
| volume120_SHORT | base_taker05_slip02 |       57 |     22 |         38.596 |          1.3049 |           7.0098 |                  11 |             3.077 |             3.816 |                       7.068 |
| volume150_SHORT | base_taker05_slip02 |       32 |     13 |         40.625 |          1.4354 |           5.7505 |                   8 |             3.478 |             2.196 |                       4.862 |
| volume120_SHORT | same_fee_slip04     |       57 |     22 |         38.596 |          1.1907 |           4.6013 |                  10 |             1.328 |             3.23  |                       8.574 |
| volume150_SHORT | same_fee_slip04     |       32 |     13 |         40.625 |          1.2772 |           3.8322 |                   8 |             1.971 |             1.825 |                       5.777 |
| volume120_SHORT | same_fee_slip06     |       57 |     21 |         36.842 |          1.0479 |           1.2175 |                   8 |            -1.393 |             2.648 |                      10.962 |
| volume150_SHORT | same_fee_slip06     |       32 |     13 |         40.625 |          1.2116 |           3.0809 |                   8 |             1.602 |             1.455 |                       6.046 |
| volume120_SHORT | taker075_slip04     |       57 |     22 |         38.596 |          1.0444 |           1.1467 |                   8 |            -0.389 |             1.542 |                       9.707 |
| volume150_SHORT | taker075_slip04     |       32 |     13 |         40.625 |          1.1276 |           1.894  |                   7 |             1.075 |             0.811 |                       6.391 |

No funding, tick-level bid/ask spread, depth, liquidation or latency modeled. Costs cannot validate performance on their own.
See summary.csv and monthly_mark_to_market.csv.
