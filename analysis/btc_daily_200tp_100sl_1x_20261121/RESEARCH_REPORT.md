# BTCUSD 1× 15M pullback breakout — fixed 200-point TP, 100-point SL

## Exact methodology

- Native Delta India BTCUSD 1m OHLCV. Use last **closed 1H** EMA20 > EMA50 and 1H close > EMA20 for long; reverse for short.
- Prior four 15m completed candles must touch the 15m EMA20. Signal's **closed 15m** candle must break previous 15m high/low, close beyond its EMA20, and have confirming bullish/bearish body.
- Enter next 1m OPEN. First qualifying IST-day entry, at most one trade, 7 days/week. No other indicators or session filters.
- Target +200 BTC chart-price points, stop −100 BTC chart-price points from 1m raw entry OPEN; if both touched in one 1m bar, stop wins.
- Four-hour time exit or flat by IST midnight. 1× equity notional. $10,000 hypothetical initial account, notional re-sized on realized equity.
- Taker 0.05% per side + 18% GST on fees, $5 BTC-points adverse slippage per side. Funding, true spread/impact, contract-lot constraints missing.
- Full IST days 2025-01-02 through 2026-10-30. January 2025 and October 2026 incomplete archive-edge months. 2026 previously seen, not blind OOS.

## Summary

|                                        | 0                                                                            |
|:---------------------------------------|:-----------------------------------------------------------------------------|
| strategy                               | h1_ema20_50_m15_prior4_ema20_touch_previous_high_break_200tp_100sl_1x        |
| trades                                 | 659                                                                          |
| longs                                  | 332                                                                          |
| shorts                                 | 327                                                                          |
| tp_before_sl_count                     | 211                                                                          |
| sl_before_tp_count                     | 436                                                                          |
| time_or_day_exit_count                 | 12                                                                           |
| tp_first_pct_of_trades                 | 32.0182                                                                      |
| net_win_trades                         | 213                                                                          |
| net_loss_trades                        | 446                                                                          |
| net_trade_win_rate_pct                 | 32.3217                                                                      |
| days_in_sample                         | 667                                                                          |
| net_profitable_days                    | 213                                                                          |
| net_losing_days                        | 446                                                                          |
| no_trade_days                          | 8                                                                            |
| tp_days_pct_all_calendar               | 31.6342                                                                      |
| positive_months                        | 0                                                                            |
| negative_months                        | 22                                                                           |
| flat_months                            | 0                                                                            |
| capital_start_usd                      | 10000.0                                                                      |
| capital_end_usd                        | 4088.86                                                                      |
| full_period_compounded_net_account_pct | -59.11137                                                                    |
| mean_after_fee_BTC_price_points        | -116.8206                                                                    |
| mean_gross_BTC_price_points            | -1.7504                                                                      |
| total_gross_usd                        | -200.01                                                                      |
| total_fee_gst_usd                      | 5211.19                                                                      |
| total_slippage_usd                     | 499.95                                                                       |
| total_net_usd                          | -5911.14                                                                     |
| net_profit_factor                      | 0.1793                                                                       |
| trade_close_max_drawdown_pct           | 59.1114                                                                      |
| 2025_net_compounded_pct                | -35.88341                                                                    |
| 2026_JanOct_net_compounded_pct         | -36.22768                                                                    |
| research_warning                       | 2026 previously researched in BTC-Analysis; this is NOT an untouched holdout |
| conclusion_warning                     | A 200-point daily profit target is not a daily profit guarantee              |

## Monthly results (NET after modeled trading costs)

| month_ist   |   days |   entries |   tp_hit_first |   sl_hit_first |   time_or_day_exit |   winning_days |   losing_days |   no_trade_days |   compounded_net_account_pct |   sum_of_daily_net_usd | archive_boundary_incomplete   |
|:------------|-------:|----------:|---------------:|---------------:|-------------------:|---------------:|--------------:|----------------:|-----------------------------:|-----------------------:|:------------------------------|
| 2025-01     |     30 |        29 |             10 |             19 |                  0 |             10 |            19 |               1 |                     -3.54261 |              -354.261  | True                          |
| 2025-02     |     28 |        28 |              6 |             22 |                  0 |              6 |            22 |               0 |                     -4.55823 |              -439.675  | False                         |
| 2025-03     |     31 |        31 |              9 |             21 |                  1 |              9 |            22 |               0 |                     -4.25325 |              -391.557  | False                         |
| 2025-04     |     30 |        30 |             10 |             20 |                  0 |             10 |            20 |               0 |                     -3.90598 |              -344.293  | False                         |
| 2025-05     |     31 |        31 |              6 |             25 |                  0 |              6 |            25 |               0 |                     -5.09497 |              -431.555  | False                         |
| 2025-06     |     30 |        29 |              8 |             19 |                  2 |              8 |            21 |               1 |                     -3.99505 |              -321.148  | False                         |
| 2025-07     |     31 |        31 |             13 |             18 |                  0 |             13 |            18 |               0 |                     -3.17895 |              -245.335  | False                         |
| 2025-08     |     31 |        31 |             16 |             15 |                  0 |             16 |            15 |               0 |                     -2.39087 |              -178.65   | False                         |
| 2025-09     |     30 |        30 |             10 |             19 |                  1 |             10 |            20 |               0 |                     -3.57198 |              -260.523  | False                         |
| 2025-10     |     31 |        30 |             19 |             11 |                  0 |             19 |            11 |               1 |                     -1.39026 |               -97.7773 | False                         |
| 2025-11     |     30 |        30 |             11 |             19 |                  0 |             11 |            19 |               0 |                     -3.54963 |              -246.175  | False                         |
| 2025-12     |     31 |        30 |              9 |             21 |                  0 |              9 |            21 |               1 |                     -4.14694 |              -277.391  | False                         |
| 2026-01     |     31 |        30 |             11 |             16 |                  3 |             11 |            19 |               1 |                     -3.26539 |              -209.366  | False                         |
| 2026-02     |     28 |        28 |              8 |             20 |                  0 |              8 |            20 |               0 |                     -4.41697 |              -273.953  | False                         |
| 2026-03     |     31 |        31 |              7 |             24 |                  0 |              7 |            24 |               0 |                     -5.45125 |              -323.169  | False                         |
| 2026-04     |     30 |        30 |              8 |             22 |                  0 |              8 |            22 |               0 |                     -4.6521  |              -260.758  | False                         |
| 2026-05     |     31 |        30 |             11 |             18 |                  1 |             11 |            19 |               1 |                     -3.22028 |              -172.105  | False                         |
| 2026-06     |     30 |        30 |             10 |             20 |                  0 |             10 |            20 |               0 |                     -3.94685 |              -204.143  | False                         |
| 2026-07     |     31 |        30 |              8 |             22 |                  0 |              8 |            22 |               1 |                     -4.84204 |              -240.561  | False                         |
| 2026-08     |     31 |        31 |              5 |             24 |                  2 |              6 |            25 |               0 |                     -5.71722 |              -270.288  | False                         |
| 2026-09     |     30 |        29 |              6 |             22 |                  1 |              6 |            23 |               1 |                     -4.83266 |              -215.407  | False                         |
| 2026-10     |     30 |        30 |             10 |             19 |                  1 |             11 |            19 |               0 |                     -3.60795 |              -153.046  | True                          |

## Data integrity

Source: 961920 1m bars; 0 missing within sampled UTC span; last candle 2026-10-30 23:59:00+00:00

## Interpretation

- TP/SL levels are **raw chart points**, not net price points or account-return percentages. Even a +200 chart-point win earns fewer than +200 net BTC points after costs.
- Incomplete calendar boundary dates excluded; not a fully verified 22 complete-month history.
- Zero-trade days are included when measuring the goal of capturing 200 every day.
- No strategy threshold was adjusted after seeing results; potential live deployment still requires additional independent forward testing.
