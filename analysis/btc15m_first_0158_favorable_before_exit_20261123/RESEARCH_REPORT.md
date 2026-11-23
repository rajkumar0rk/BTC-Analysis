# BTCUSD 15M: How many trades touched +0.158% FAVORABLE before exit?

**This counts favorable excursion under the ORIGINAL exit logic; it does not simulate exiting at +0.158%.**
BTCUSD only; all entry indicators 15m, trade execution and path ambiguity checked on archived 1m OHLC.
22 completed IST months Jan 2025–Oct 2026; trades include fee, 18% GST and 0.02% per-side slippage on original exits.
The 0.158% hurdle uses BTC underlying quote movement from raw 1m market open at entry (before adverse fill slip).
Exact cost break-even is computed using filled entry, both taker fees + GST and adverse exit slip.
For a stop/TP exit minute, only the movement BEFORE that original stop/TP event on the assumed OHLC path counts.
For a confirmed ST flip or stop gap at minute open, the remainder of that minute is not included.
Within-29-min counts earliest touching minute, not a guarantee of fill or fee promotion eligibility.

## Results (assumed O-H-L-C path)

| config         |   total_trades |   hit_0p158_before_exit |   hit_0p158_pct |   hit_0p158_under_30min |   hit_true_cost_breakeven |   hit_0p20_before_exit |   hit_0p25_before_exit |   original_positive_trades |   touched_threshold_but_originally_lost |   original_net_return_pct |
|:---------------|---------------:|------------------------:|----------------:|------------------------:|--------------------------:|-----------------------:|-----------------------:|---------------------------:|----------------------------------------:|--------------------------:|
| touch_close_2R |            809 |                     611 |           75.53 |                     374 |                       611 |                    574 |                    535 |                        252 |                                     359 |                  -66.4683 |
| touch_close_3R |            809 |                     611 |           75.53 |                     374 |                       611 |                    575 |                    536 |                        205 |                                     406 |                  -69.4444 |
| reclaim4_2R    |            434 |                     336 |           77.42 |                     201 |                       336 |                    309 |                    288 |                        130 |                                     206 |                  -49.743  |
| reclaim4_3R    |            434 |                     336 |           77.42 |                     201 |                       336 |                    310 |                    289 |                        115 |                                     221 |                  -44.5322 |
| reclaim8_3R    |            493 |                     376 |           76.27 |                     218 |                       376 |                    350 |                    329 |                        130 |                                     246 |                  -47.583  |
| combined4_2R   |           1243 |                     947 |           76.19 |                     575 |                       947 |                    883 |                    823 |                        382 |                                     565 |                  -83.1479 |
| combined4_3R   |           1243 |                     947 |           76.19 |                     575 |                       947 |                    885 |                    825 |                        320 |                                     627 |                  -83.0515 |
| combined8_3R   |           1302 |                     987 |           75.81 |                     592 |                       987 |                    925 |                    865 |                        335 |                                     652 |                  -83.9837 |

O-L-H-C path results and complete trade-level first-touch flags are in the sidecar CSVs.
Touching 0.158% does not imply the eventual trade was profitable; an unexecuted opportunity can reverse before exit.
No tick-level transaction data or funding, bid-ask spread, depth or liquidation.
