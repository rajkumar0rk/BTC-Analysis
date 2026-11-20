# BTCUSD EMA20 / Supertrend (1h) screenshot-parameter replay

Dataset: 963,360 authenticated Delta India 1-minute candle rows, 22 months.
Reference: saved Pine v6 BTCUSD EMA / ST | ATR & Volume Min Max + Net.

**Screenshot cost assumption:** Taker 0.05% opening, closing waived for <=27 minutes, GST 18%, 0 funding, 0 slippage.
**Other scenario:** a 100000-minute hypothetical qualifying window; third scenario applies $0.5 adverse price slippage on both sides with the 27-minute offer.

| Scenario | Trades | Net USD (1x0.001 BTC) | PF | Positive months /22 |
|---|---:|---:|---:|---:|
| screenshot_27_min_offer_zero_slip | 1462 | +134.56 | 1.7498 | 20/22 |
| unlimited_100000_min_offer_zero_slip | 1462 | +212.03 | 2.3031 | 22/22 |
| screenshot_27_min_offer_0p5point_adverse_each_side | 1462 | +133.10 | 1.7398 | 20/22 |

## Monthly screenshot (UTC, 1 TradingView contract)

| month_utc   |   trades |   net_wins |   net_losses |   gross_points |   net_points |   net_usd |   fees_usd |   gst_usd |   profit_factor |
|:------------|---------:|-----------:|-------------:|---------------:|-------------:|----------:|-----------:|----------:|----------------:|
| 2025-01     |       59 |         40 |           19 |         9808.5 |     2775.97  |    2.776  |     5.9598 |    1.0728 |          1.2099 |
| 2025-02     |       66 |         49 |           17 |        17609   |    10156.5   |   10.1565 |     6.3156 |    1.1368 |          2.9298 |
| 2025-03     |       70 |         55 |           15 |        18135.5 |    11141.1   |   11.1411 |     5.9275 |    1.0669 |          2.0753 |
| 2025-04     |       66 |         46 |           20 |         9471   |     2718.43  |    2.7184 |     5.7225 |    1.0301 |          1.2758 |
| 2025-05     |       71 |         49 |           22 |        13048.5 |     4397.65  |    4.3976 |     7.3312 |    1.3196 |          1.3228 |
| 2025-06     |       72 |         50 |           22 |        18404   |     9434.76  |    9.4348 |     7.601  |    1.3682 |          2.7491 |
| 2025-07     |       73 |         47 |           26 |        19444   |     9527.99  |    9.528  |     8.4034 |    1.5126 |          2.1213 |
| 2025-08     |       72 |         43 |           29 |        19210.5 |     9465.51  |    9.4655 |     8.2585 |    1.4865 |          1.9022 |
| 2025-09     |       68 |         37 |           31 |         9376.5 |      338.601 |    0.3386 |     7.6592 |    1.3787 |          1.0391 |
| 2025-10     |       70 |         46 |           24 |        17362   |     7958.27  |    7.9583 |     7.9693 |    1.4345 |          1.9359 |
| 2025-11     |       83 |         65 |           18 |        27632   |    18208.6   |   18.2086 |     7.9859 |    1.4375 |          3.3082 |
| 2025-12     |       57 |         33 |           24 |         7397   |     1383.41  |    1.3834 |     5.0963 |    0.9173 |          1.1396 |
| 2026-01     |       69 |         52 |           17 |        14700   |     7274.88  |    7.2749 |     6.2925 |    1.1326 |          1.9867 |
| 2026-02     |       62 |         53 |            9 |        18751.5 |    13724.3   |   13.7243 |     4.2603 |    0.7669 |          4.461  |
| 2026-03     |       64 |         45 |           19 |        10859.5 |     5599.21  |    5.5992 |     4.4579 |    0.8024 |          1.6467 |
| 2026-04     |       63 |         49 |           14 |         8929.5 |     3434.03  |    3.434  |     4.6572 |    0.8383 |          1.4336 |
| 2026-05     |       59 |         35 |           24 |         4243   |    -1183.83  |   -1.1838 |     4.599  |    0.8278 |          0.8418 |
| 2026-06     |       69 |         62 |            7 |        14961.5 |     9810.39  |    9.8104 |     4.3653 |    0.7858 |          2.9057 |
| 2026-07     |       57 |         38 |           19 |         5260.5 |      982.741 |    0.9827 |     3.6252 |    0.6525 |          1.1412 |
| 2026-08     |       64 |         41 |           23 |         2605   |    -2587.13  |   -2.5871 |     4.4001 |    0.792  |          0.7502 |
| 2026-09     |       61 |         50 |           11 |        12792.5 |     6990.41  |    6.9904 |     4.917  |    0.8851 |          2.6995 |
| 2026-10     |       67 |         49 |           18 |         9512.5 |     3008.77  |    3.0088 |     5.5116 |    0.9921 |          1.5172 |

## Reproducibility / limitations

- Independent reconstruction of the saved Pine v6 logic; NOT a TradingView tester export.
- OHLC inferred path approximates native TradingView strategy.exit trail; same-bar execution, rounding, and fills can differ from TV.
- Pine calc_bars_count=10000 may restrict accessible history on some TradingView charts; a separate recent 10000-bar window is included alongside full 22-month replay.
- Exact screenshot's 27-min qualifying window and all-history offer are assumptions, NOT verified Delta promotion terms.
- Entry and exit are TAKER per screenshot; exit fee waived only if offer eligible in model.
- No actual bid/ask spread, order-book impact, trading latency, realized slippage, or margin liquidation.
- Funding explicitly set to 0 from screenshot; this does not represent historical funding payments.
- One TradingView fixed contract=0.001 BTC; no leverage, margin, portfolio compounding or account sizing applied.
- Returns scored by UTC exit calendar month to provide 22 truly complete months Jan 2025-Oct 2026.
- Entry timestamp is signal candle close. Intrabar exits timestamped at bar close as conservative upper bound for fee-window eligibility.
- Uses assumed 0.5 BTCUSD price tick for rounded initial ATR stops.
