# BTCUSD 1× +200/−100 — chronological ML first-touch probability

**Decision: NO_PROFITABLE_2025_CALIBRATION_GATE**

## Strict chronological protocol

- Train HistGradientBoostingClassifier on Jan–Jun 2025 ONLY, using completed 15m and completed prior 1h features. Both sides labelled separately from native 1m first touch.
- Select a predetermined probability threshold exclusively on Jul–Dec 2025 calibration, only if >=40 independent trades, >=4 positive months, net profit factor >1, positive compounded NAV and mean net point 95%-style lower bound >0.
- Apply fee-aware minimum break-even threshold +2.5 percentage points per entry, subject to strict threshold.
- 1× current net-account notional, $10,000 start; +200 BTC chart points / −100 raw chart points, 4h timeout or IST day close.
- Actual execution replay on 1-minute OHLC, stop wins target ambiguity. Taker fee 0.05% each side, GST 18%, adverse slip 5 points each side.
- 2026 H1 and H2 are chronological checks never seen by this model, but globally **historically researched** in this repository; no truly fresh OOS claims.
- Max one opened trade per IST day; zero-trade days count against daily income target.

## Fixed probability-gate comparison

| gate   | qualifies_on_2025_calibration   |   2025_CAL_entries |   2025_CAL_tp_first_pct |   2025_CAL_net_win_pct | 2025_CAL_mean_net_points   | 2025_CAL_mean_net_points_lower95   |   2025_CAL_net_account_return_pct |   2025_CAL_months_positive |   2026_H1_SEEN_entries |   2026_H1_SEEN_net_account_return_pct |   2026_H2_SEEN_entries |   2026_H2_SEEN_net_account_return_pct |
|:-------|:--------------------------------|-------------------:|------------------------:|-----------------------:|:---------------------------|:-----------------------------------|----------------------------------:|---------------------------:|-----------------------:|--------------------------------------:|-----------------------:|--------------------------------------:|
| p_0.55 | False                           |                  0 |                       0 |                      0 |                            |                                    |                                 0 |                          0 |                      0 |                                     0 |                      0 |                                     0 |
| p_0.60 | False                           |                  0 |                       0 |                      0 |                            |                                    |                                 0 |                          0 |                      0 |                                     0 |                      0 |                                     0 |
| p_0.65 | False                           |                  0 |                       0 |                      0 |                            |                                    |                                 0 |                          0 |                      0 |                                     0 |                      0 |                                     0 |
| p_0.70 | False                           |                  0 |                       0 |                      0 |                            |                                    |                                 0 |                          0 |                      0 |                                     0 |                      0 |                                     0 |
| p_0.75 | False                           |                  0 |                       0 |                      0 |                            |                                    |                                 0 |                          0 |                      0 |                                     0 |                      0 |                                     0 |
| p_0.80 | False                           |                  0 |                       0 |                      0 |                            |                                    |                                 0 |                          0 |                      0 |                                     0 |                      0 |                                     0 |
| p_0.85 | False                           |                  0 |                       0 |                      0 |                            |                                    |                                 0 |                          0 |                      0 |                                     0 |                      0 |                                     0 |

## Gate used in the diagnostic account replay

Approved gate: None

Exploratory unqualified gate, if no approval: p_0.55

## Period account audits

|   entries |   tp_count |   sl_count |   timeout_count |   net_wins |   net_losses |   positive_days |   negative_days |   no_trade_days |   net_win_pct |   tp_first_pct | mean_net_points   | std_net_points   | mean_net_points_lower95   | net_profit_factor   |   months_positive |   months_negative |   months_flat |   net_account_return_pct |   ending_nav |   drawdown_pct | period        |
|----------:|-----------:|-----------:|----------------:|-----------:|-------------:|----------------:|----------------:|----------------:|--------------:|---------------:|:------------------|:-----------------|:--------------------------|:--------------------|------------------:|------------------:|--------------:|-------------------------:|-------------:|---------------:|:--------------|
|         0 |          0 |          0 |               0 |          0 |            0 |               0 |               0 |             184 |             0 |              0 |                   |                  |                           |                     |                 0 |                 0 |             6 |                        0 |        10000 |              0 | 2025_CAL      |
|         0 |          0 |          0 |               0 |          0 |            0 |               0 |               0 |             181 |             0 |              0 |                   |                  |                           |                     |                 0 |                 0 |             6 |                        0 |        10000 |              0 | 2026_H1_SEEN  |
|         0 |          0 |          0 |               0 |          0 |            0 |               0 |               0 |             122 |             0 |              0 |                   |                  |                           |                     |                 0 |                 0 |             4 |                        0 |        10000 |              0 | 2026_H2_SEEN  |
|         0 |          0 |          0 |               0 |          0 |            0 |               0 |               0 |             303 |             0 |              0 |                   |                  |                           |                     |                 0 |                 0 |            10 |                        0 |        10000 |              0 | 2026_ALL_SEEN |

## Monthly account results for above diagnostic gate



## Source integrity

Source 1m rows: 961920

## Caveats

- Hourly trend inputs are ONLY completed hours, not forming hours
- Each 15m signal enters the next raw 1m OPEN, fully fee-adjusted net returns; stop first on same minute
- Model trained on two competing LONG/SHORT candidate outcomes from same timestamps; overlapping 4h labels imply correlation
- 1× NAV notional; one first passing trade per IST day, 4h timeout or flatten by midnight
- Economic probability threshold uses TP/SL and estimated fees at actual entry open plus 2.5 percentage point safety margin
- No funding, actual spread, orderbook, maker queue/partial fills, exchange rounding or price-mark liquidation
- Predictive classifier probabilities may be miscalibrated, especially in 2026
- Historical 2026 already researched in this repository; not a pristine holdout
- Jan1 2025 and Oct31 2026 IST are missing full-day coverage; no claim 22 fully complete months
- Zero profitable gate means no credible deployment candidate, not a reason to re-tune 2026 thresholds
- Gross 200 BTC price points differ from net account profitability
