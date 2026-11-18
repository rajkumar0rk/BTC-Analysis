# Stage27 — fixed BTC price-grid rejection

This is exploratory, not an executable live edge. Original data checksum verified.
October 2026 UTC 1m is fully repaired on the isolated research branch.
January 2025 IST lacks the first 5.5 hours; cannot assert fully observed 22 IST months.
Fees and GST included, 5 points adverse slippage each side; no funding, spread, market impact or lot granularity.
Sizing uses 1% equity stop-distance risk and 3x notional cap, not validated Delta margin.
2025-only model selection, 2026 already seen in prior research (not blind).

## All configurations

| key              |   train_positive |   recheck_positive |   train_ge10 |   recheck_ge10 |   train_total_pct |   worst_month_pct |   total_trades | all_22_positive   | all_22_ge10   |
|:-----------------|-----------------:|-------------------:|-------------:|---------------:|------------------:|------------------:|---------------:|:------------------|:--------------|
| grid1000_stop2.5 |                1 |                  0 |            0 |              0 |          -179.335 |          -36.7429 |           2402 | False             | False         |
| grid500_stop2.5  |                0 |                  0 |            0 |              0 |          -278.358 |          -39.5925 |           3498 | False             | False         |
| grid1000_stop1.5 |                0 |                  1 |            0 |              0 |          -424.518 |          -46.2892 |           2971 | False             | False         |
| grid500_stop1.5  |                0 |                  0 |            0 |              0 |          -611.614 |          -63.1319 |           4542 | False             | False         |

## Chosen 2025-only configuration
grid1000_stop2.5

## Monthly net account returns

| month_ist   |   return_pct |   start_equity |   end_equity |   trades |   wins |   losses |    net_usd |
|:------------|-------------:|---------------:|-------------:|---------:|-------:|---------:|-----------:|
| 2025-01     |    -18.5621  |      1000      |     814.379  |      134 |     54 |       80 | -185.621   |
| 2025-02     |     -3.74157 |       814.379  |     783.908  |      103 |     47 |       56 |  -30.4705  |
| 2025-03     |    -15.1103  |       783.908  |     665.457  |      138 |     58 |       80 | -118.451   |
| 2025-04     |    -16.1174  |       665.457  |     558.203  |      115 |     50 |       65 | -107.254   |
| 2025-05     |      1.65852 |       558.203  |     567.461  |      116 |     56 |       60 |    9.25792 |
| 2025-06     |    -11.2673  |       567.461  |     503.523  |       93 |     43 |       50 |  -63.9377  |
| 2025-07     |    -29.8273  |       503.523  |     353.336  |      116 |     37 |       79 | -150.187   |
| 2025-08     |     -9.15347 |       353.336  |     320.993  |      110 |     50 |       60 |  -32.3425  |
| 2025-09     |    -31.7212  |       320.993  |     219.17   |       93 |     25 |       68 | -101.823   |
| 2025-10     |    -23.2009  |       219.17   |     168.321  |      149 |     54 |       95 |  -50.8494  |
| 2025-11     |    -13.9007  |       168.321  |     144.923  |      147 |     63 |       84 |  -23.3978  |
| 2025-12     |     -8.39158 |       144.923  |     132.762  |      120 |     51 |       69 |  -12.1613  |
| 2026-01     |    -36.7429  |       132.762  |      83.9813 |      108 |     31 |       77 |  -48.7805  |
| 2026-02     |    -16.9679  |        83.9813 |      69.7314 |      136 |     56 |       80 |  -14.2498  |
| 2026-03     |    -11.0332  |        69.7314 |      62.0378 |      118 |     50 |       68 |   -7.69363 |
| 2026-04     |    -19.657   |        62.0378 |      49.843  |      100 |     38 |       62 |  -12.1948  |
| 2026-05     |    -25.8416  |        49.843  |      36.9628 |       82 |     26 |       56 |  -12.8802  |
| 2026-06     |     -7.31719 |        36.9628 |      34.2582 |       92 |     42 |       50 |   -2.70464 |
| 2026-07     |     -8.86154 |        34.2582 |      31.2224 |       71 |     29 |       42 |   -3.0358  |
| 2026-08     |    -19.1838  |        31.2224 |      25.2327 |       76 |     25 |       51 |   -5.98963 |
| 2026-09     |    -16.9115  |        25.2327 |      20.9655 |       94 |     36 |       58 |   -4.26724 |
| 2026-10     |     -6.23367 |        20.9655 |      19.6586 |       91 |     44 |       47 |   -1.30692 |

## Audit
{
  "source": "Delta Exchange India original BTCUSD 1m",
  "input_months": 22,
  "source_minutes": 963360,
  "october_2026_complete": true,
  "selected_using": "2025 only, ranking positive months then sum of monthly net returns",
  "chosen": "grid1000_stop2.5",
  "signal_family": "fixed_absolute_price_grid_rejection",
  "all_22_positive": false,
  "all_22_ge10": false,
  "total_trades": 2402,
  "wins": 965,
  "losses": 1437,
  "max_trade_close_drawdown_pct": -98.24150246234386,
  "fee_per_side_with_gst": 0.00059,
  "slippage_points_per_side": 5.0,
  "missing": [
    "funding",
    "actual bid/ask spread",
    "impact",
    "lot size/margin/liquidation"
  ],
  "first_IST_month_missing_hours": 5.5,
  "warning": "2026 history was seen in previous studies; not pristine forward validation"
}

No guarantee of future profits. Never place orders from this research.
