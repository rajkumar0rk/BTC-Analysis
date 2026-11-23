# BTCUSD 15m causal pre-entry filter and risk-size research

315 variants x 2 hypothetical intraminute paths. Jan2025–Oct2026 historical in-sample; NOT independent validation.
Fifteen-minute indicators only and completed-bar signals; 1-minute exits in the unchanged original simulator.
No Supertrend reversal exit, 3% SL, 9% TP, profit trigger 8.25%, BE lock, 5-loss month pause.
Fees +18% GST plus 0.02% per-side slippage included; funding and live spread/gaps NOT fully modeled.
Baseline revalidated for each shard/path: 72 trades, +162.964% return, 14.740% max floating DD, 18/22 positive months.

Strictly better than baseline profit and floating DD while retaining >=18 positive months: 0
At least old +151.787% profit & >=18 positive months, below 12% DD: 0; below 10% DD: 0.

## Pass strict objective
None.

## Smallest DD with >=151.787% profit and >=18 months
| tier      | filter      |   worst_dd |   min_profit |   min_winning_months |   min_trades |   max_filtered | pass_previous_profit   | beats_previous   | pass_original_profit   | target_12   | target_10   |
|:----------|:------------|-----------:|-------------:|---------------------:|-------------:|---------------:|:-----------------------|:-----------------|:-----------------------|:------------|:------------|
| T65_30_10 | ATRMIN_0p2  |     14.74  |      229.037 |                   18 |           71 |              6 | True                   | False            | True                   | False       | False       |
| T65_30_10 | ATRMIN_0p05 |     14.74  |      162.964 |                   18 |           72 |              0 | True                   | False            | True                   | False       | False       |
| T65_30_10 | BODY_0p1    |     14.74  |      162.964 |                   18 |           72 |              0 | True                   | False            | True                   | False       | False       |
| T65_30_10 | any         |     14.74  |      162.964 |                   18 |           72 |              0 | True                   | False            | True                   | False       | False       |
| T65_30_10 | VOLMAX_4p0  |     14.74  |      162.963 |                   18 |           72 |              1 | True                   | False            | True                   | False       | False       |
| T65_20_10 | ATRMIN_0p2  |     15.068 |      232.447 |                   18 |           71 |              6 | True                   | False            | True                   | False       | False       |
| T65_20_10 | ATRMIN_0p05 |     15.068 |      165.689 |                   18 |           72 |              0 | True                   | False            | True                   | False       | False       |
| T65_20_10 | BODY_0p1    |     15.068 |      165.689 |                   18 |           72 |              0 | True                   | False            | True                   | False       | False       |
| T65_20_10 | any         |     15.068 |      165.689 |                   18 |           72 |              0 | True                   | False            | True                   | False       | False       |
| T65_20_10 | VOLMAX_4p0  |     15.068 |      165.687 |                   18 |           72 |              1 | True                   | False            | True                   | False       | False       |
| T75_10_10 | ATRMIN_0p2  |     16.081 |      235.576 |                   18 |           71 |              6 | True                   | False            | True                   | False       | False       |
| T75_10_10 | ATRMIN_0p05 |     16.081 |      174.105 |                   18 |           72 |              0 | True                   | False            | True                   | False       | False       |
| T75_10_10 | BODY_0p1    |     16.081 |      174.105 |                   18 |           72 |              0 | True                   | False            | True                   | False       | False       |
| T75_10_10 | any         |     16.081 |      174.105 |                   18 |           72 |              0 | True                   | False            | True                   | False       | False       |
| T75_10_10 | VOLMAX_4p0  |     16.081 |      174.103 |                   18 |           72 |              1 | True                   | False            | True                   | False       | False       |
| T75_10_10 | ATRMAX_0p9  |     16.081 |      152.609 |                   18 |           70 |              2 | False                  | False            | True                   | False       | False       |
| T75_10_10 | ATRMAX_1p2  |     16.081 |      151.808 |                   18 |           71 |              1 | False                  | False            | True                   | False       | False       |
| T85_20_10 | ATRMIN_0p2  |     16.152 |      231.816 |                   18 |           71 |              6 | True                   | False            | True                   | False       | False       |
| T85_20_10 | ATRMIN_0p05 |     16.152 |      176.951 |                   18 |           72 |              0 | True                   | False            | True                   | False       | False       |
| T85_20_10 | BODY_0p1    |     16.152 |      176.951 |                   18 |           72 |              0 | True                   | False            | True                   | False       | False       |
| T85_20_10 | any         |     16.152 |      176.951 |                   18 |           72 |              0 | True                   | False            | True                   | False       | False       |
| T85_20_10 | ATRMAX_0p9  |     16.152 |      155.233 |                   18 |           70 |              2 | False                  | False            | True                   | False       | False       |
| T85_20_10 | ATRMAX_1p2  |     16.152 |      154.423 |                   18 |           71 |              1 | False                  | False            | True                   | False       | False       |
| T85_20_10 | VOLMAX_4p0  |     16.153 |      176.95  |                   18 |           72 |              1 | True                   | False            | True                   | False       | False       |
| T85_10_10 | ATRMIN_0p2  |     16.62  |      235.209 |                   18 |           71 |              6 | True                   | False            | True                   | False       | False       |
| T85_10_10 | ATRMIN_0p05 |     16.62  |      179.783 |                   18 |           72 |              0 | True                   | False            | True                   | False       | False       |
| T85_10_10 | BODY_0p1    |     16.62  |      179.783 |                   18 |           72 |              0 | True                   | False            | True                   | False       | False       |
| T85_10_10 | any         |     16.62  |      179.783 |                   18 |           72 |              0 | True                   | False            | True                   | False       | False       |
| T85_10_10 | VOLMAX_4p0  |     16.62  |      179.782 |                   18 |           72 |              1 | True                   | False            | True                   | False       | False       |
| T85_10_10 | ATRMAX_0p9  |     16.62  |      157.843 |                   18 |           70 |              2 | False                  | False            | True                   | False       | False       |

## Overall lowest DD irrespective of return
| tier      | filter        |   worst_dd |   min_profit |   min_winning_months |   min_trades |   max_filtered | pass_previous_profit   | beats_previous   | pass_original_profit   | target_12   | target_10   |
|:----------|:--------------|-----------:|-------------:|---------------------:|-------------:|---------------:|:-----------------------|:-----------------|:-----------------------|:------------|:------------|
| T65_20_10 | RSITREND_20   |     12.787 |      15.9971 |                    6 |           10 |            347 | False                  | False            | False                  | False       | False       |
| T65_30_10 | RSITREND_20   |     12.787 |      15.9971 |                    6 |           10 |            347 | False                  | False            | False                  | False       | False       |
| T75_10_10 | RSITREND_20   |     12.787 |      15.9971 |                    6 |           10 |            347 | False                  | False            | False                  | False       | False       |
| T85_10_10 | RSITREND_20   |     12.787 |      15.9971 |                    6 |           10 |            347 | False                  | False            | False                  | False       | False       |
| T85_20_10 | RSITREND_20   |     12.787 |      15.9971 |                    6 |           10 |            347 | False                  | False            | False                  | False       | False       |
| T65_20_10 | VOLMAX_2p0    |     14.133 |     177.871  |                   17 |           68 |              7 | False                  | False            | False                  | False       | False       |
| T75_10_10 | VOLMAX_2p0    |     14.143 |     193.486  |                   17 |           68 |              7 | False                  | False            | False                  | False       | False       |
| T65_20_10 | RANGE_MAX_2p0 |     14.199 |     158.887  |                   17 |           70 |              3 | False                  | False            | False                  | False       | False       |
| T65_20_10 | VOLMAX_3p0    |     14.199 |     158.887  |                   17 |           70 |              3 | False                  | False            | False                  | False       | False       |
| T75_10_10 | RANGE_MAX_2p0 |     14.483 |     172.56   |                   17 |           70 |              3 | False                  | False            | False                  | False       | False       |
| T75_10_10 | VOLMAX_3p0    |     14.483 |     172.56   |                   17 |           70 |              3 | False                  | False            | False                  | False       | False       |
| T65_30_10 | VOLMAX_2p0    |     14.674 |     172.65   |                   17 |           68 |              7 | False                  | False            | False                  | False       | False       |
| T85_10_10 | VOLMAX_2p0    |     14.694 |     204.004  |                   17 |           68 |              7 | False                  | False            | False                  | False       | False       |
| T65_30_10 | ATRMIN_0p2    |     14.74  |     229.037  |                   18 |           71 |              6 | True                   | False            | True                   | False       | False       |
| T65_30_10 | ATRMIN_0p05   |     14.74  |     162.964  |                   18 |           72 |              0 | True                   | False            | True                   | False       | False       |
| T65_30_10 | BODY_0p1      |     14.74  |     162.964  |                   18 |           72 |              0 | True                   | False            | True                   | False       | False       |
| T65_30_10 | any           |     14.74  |     162.964  |                   18 |           72 |              0 | True                   | False            | True                   | False       | False       |
| T65_30_10 | VOLMAX_4p0    |     14.74  |     162.963  |                   18 |           72 |              1 | True                   | False            | True                   | False       | False       |
| T65_30_10 | RANGE_MAX_2p0 |     14.74  |     154.022  |                   17 |           70 |              3 | False                  | False            | False                  | False       | False       |
| T65_30_10 | VOLMAX_3p0    |     14.74  |     154.022  |                   17 |           70 |              3 | False                  | False            | False                  | False       | False       |

## Cautions
Using the same history for model search can seriously overfit; prospective paper trading and no-lookahead forward testing are necessary.
Max DD is floating intratrade peak-to-trough in 1x notional, not closed-trade DD.
