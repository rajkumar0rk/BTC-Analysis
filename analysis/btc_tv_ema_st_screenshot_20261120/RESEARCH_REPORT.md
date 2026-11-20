# BTCUSD EMA20 / Supertrend (15m) screenshot-parameter replay

Dataset: 963,360 authenticated Delta India 1-minute candle rows, 22 months.
Reference: saved Pine v6 BTCUSD EMA / ST | ATR & Volume Min Max + Net.

**Screenshot cost assumption:** Taker 0.05% opening, closing waived for <=100000 minutes, GST 18%, 0 funding, 0 slippage.
**Other scenario:** a 30-minute qualifying window; third scenario also includes $0.5 worse price on each side.

| Scenario | Trades | Net USD (1x0.001 BTC) | PF | Positive months /22 |
|---|---:|---:|---:|---:|
| screenshot_100000_min_offer_zero_slip | 4862 | +126.58 | 1.2694 | 0/22 |
| practical_30_min_offer_zero_slip | 4862 | +126.58 | 1.2694 | 0/22 |
| practical_30_min_offer_0p5point_adverse_each_side | 4862 | +121.71 | 1.2584 | 0/22 |

## Monthly screenshot (UTC, 1 TradingView contract)

| month_utc   |   trades |   net_wins |   net_losses |   gross_points |   net_points |   net_usd |   fees_usd |   gst_usd | profit_factor   |
|:------------|---------:|-----------:|-------------:|---------------:|-------------:|----------:|-----------:|----------:|:----------------|
| 2025-01     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2025-02     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2025-03     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2025-04     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2025-05     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2025-06     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2025-07     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2025-08     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2025-09     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2025-10     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2025-11     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2025-12     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2026-01     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2026-02     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2026-03     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2026-04     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2026-05     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2026-06     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2026-07     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2026-08     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2026-09     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |
| 2026-10     |        0 |          0 |            0 |              0 |            0 |         0 |          0 |         0 |                 |

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
