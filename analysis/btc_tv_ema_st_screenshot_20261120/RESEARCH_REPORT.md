# BTCUSD EMA20 / Supertrend (15m) screenshot-parameter replay

Dataset: 963,360 authenticated Delta India 1-minute candle rows, 22 months.
Reference: saved Pine v6 BTCUSD EMA / ST | ATR & Volume Min Max + Net.

**Screenshot cost assumption:** Taker 0.05% opening, closing waived for <=100000 minutes, GST 18%, 0 funding, 0 slippage.
**Other scenario:** a 30-minute qualifying window; third scenario also includes $0.5 worse price on each side.

| Scenario | Trades | Net USD (1x0.001 BTC) | PF | Positive months /22 |
|---|---:|---:|---:|---:|
| screenshot_100000_min_offer_zero_slip | 4862 | +126.58 | 1.2694 | 19/22 |
| practical_30_min_offer_zero_slip | 4862 | +16.86 | 1.0321 | 12/22 |
| practical_30_min_offer_0p5point_adverse_each_side | 4862 | +11.99 | 1.0228 | 11/22 |

## Monthly screenshot (UTC, 1 TradingView contract)

| month_utc   |   trades |   net_wins |   net_losses |   gross_points |   net_points |   net_usd |   fees_usd |   gst_usd |   profit_factor |
|:------------|---------:|-----------:|-------------:|---------------:|-------------:|----------:|-----------:|----------:|----------------:|
| 2025-01     |      265 |        201 |           64 |        21084.5 |     5458.33  |    5.4583 |    13.2425 |    2.3837 |          1.1698 |
| 2025-02     |      212 |        165 |           47 |        18828   |     6870.79  |    6.8708 |    10.1332 |    1.824  |          1.3086 |
| 2025-03     |      241 |        202 |           39 |        29294   |    17222.6   |   17.2226 |    10.23   |    1.8414 |          1.6652 |
| 2025-04     |      241 |        201 |           40 |        28136   |    15909     |   15.909  |    10.3619 |    1.8651 |          1.7422 |
| 2025-05     |      243 |        186 |           57 |        16631.5 |     1819.12  |    1.8191 |    12.5529 |    2.2595 |          1.0728 |
| 2025-06     |      206 |        146 |           60 |         8503   |    -4344.06  |   -4.3441 |    10.8873 |    1.9597 |          0.8198 |
| 2025-07     |      230 |        155 |           75 |        13053.5 |    -2575.51  |   -2.5755 |    13.2449 |    2.3841 |          0.9078 |
| 2025-08     |      234 |        165 |           69 |        19406.5 |     3545.8   |    3.5458 |    13.4413 |    2.4194 |          1.1654 |
| 2025-09     |      223 |        145 |           78 |        11691.5 |    -3165.34  |   -3.1653 |    12.5905 |    2.2663 |          0.8575 |
| 2025-10     |      237 |        178 |           59 |        23202.5 |     7315.57  |    7.3156 |    13.4635 |    2.4234 |          1.2649 |
| 2025-11     |      246 |        200 |           46 |        29489   |    15456.2   |   15.4562 |    11.8922 |    2.1406 |          1.691  |
| 2025-12     |      211 |        166 |           45 |        17034   |     5936.66  |    5.9367 |     9.4045 |    1.6928 |          1.2834 |
| 2026-01     |      221 |        171 |           50 |        13068.5 |     1269.94  |    1.2699 |     9.9988 |    1.7998 |          1.0607 |
| 2026-02     |      199 |        172 |           27 |        29299   |    21131.9   |   21.1319 |     6.9213 |    1.2458 |          2.3345 |
| 2026-03     |      243 |        200 |           43 |        21154   |    11170.4   |   11.1704 |     8.4607 |    1.5229 |          1.52   |
| 2026-04     |      219 |        172 |           47 |        13085.5 |     3539.71  |    3.5397 |     8.0897 |    1.4561 |          1.1841 |
| 2026-05     |      201 |        159 |           42 |         9805.5 |      539.708 |    0.5397 |     7.8524 |    1.4134 |          1.0342 |
| 2026-06     |      207 |        164 |           43 |        10671.5 |     2949.8   |    2.9498 |     6.5438 |    1.1779 |          1.1399 |
| 2026-07     |      207 |        149 |           58 |         8191   |      397.426 |    0.3974 |     6.6047 |    1.1889 |          1.0221 |
| 2026-08     |      189 |        138 |           51 |        12679.5 |     4784.28  |    4.7843 |     6.6909 |    1.2044 |          1.3239 |
| 2026-09     |      198 |        159 |           39 |        14943.5 |     5552.59  |    5.5526 |     7.9584 |    1.4325 |          1.3759 |
| 2026-10     |      189 |        148 |           41 |        14957   |     5790.9   |    5.7909 |     7.7679 |    1.3982 |          1.3968 |

## Reproducibility / limitations

- Independent reconstruction of the saved Pine v6 logic; NOT a TradingView tester export.
- OHLC inferred path approximates native TradingView strategy.exit trail; same-bar execution, rounding, and fills can differ from TV.
- Original Pine calc_bars_count=10000 may restrict accessible history on some TradingView charts; 22-month full replay here uses all source bars.
- Exact screenshot's 100000-min qualifying window and all-history offer are assumptions, NOT verified Delta promotion terms.
- Entry and exit are TAKER per screenshot; exit fee waived only if offer eligible in model.
- No actual bid/ask spread, order-book impact, trading latency, realized slippage, or margin liquidation.
- Funding explicitly set to 0 from screenshot; this does not represent historical funding payments.
- One TradingView fixed contract=0.001 BTC; no leverage, margin, portfolio compounding or account sizing applied.
- Returns scored by UTC exit calendar month to provide 22 truly complete months Jan 2025-Oct 2026.
- Entry timestamp is signal candle close. Intrabar exits timestamped at bar close as conservative upper bound for fee-window eligibility.
- Uses assumed 0.5 BTCUSD price tick for rounded initial ATR stops.
