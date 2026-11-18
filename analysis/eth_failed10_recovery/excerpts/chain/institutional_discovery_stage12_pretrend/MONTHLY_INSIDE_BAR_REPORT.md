# Stage 12 exact inside-bar 2R strategy: Monthly consistency audit

Pattern: 06_inside_bar_break; market state: aligned_trend_plus_5m_compression_break.
2R reward, 120-minute hold, original structurally derived stop. No change to entries.
Months assigned by entry timestamp in Asia/Kolkata.
Net points include modeled 0.05% taker fees per side, 18% GST and 5 points per-side slippage.

Profitable months: 8/23
Losing months: 13
Months without trades: 2
Net total points equivalent: -6849.42

| month_ist   |   trades |   winning_trades |   win_pct |   net_points | status    | coverage_note                         |
|:------------|---------:|-----------------:|----------:|-------------:|:----------|:--------------------------------------|
| 2025-01     |        4 |                3 |     75    |       843.9  | Profit    |                                       |
| 2025-02     |        3 |                3 |    100    |      3175.41 | Profit    |                                       |
| 2025-03     |        1 |                1 |    100    |       677.74 | Profit    |                                       |
| 2025-04     |        1 |                1 |    100    |       552.96 | Profit    |                                       |
| 2025-05     |        1 |                1 |    100    |       516.56 | Profit    |                                       |
| 2025-06     |        6 |                2 |     33.33 |     -1230.83 | Loss      |                                       |
| 2025-07     |        2 |                0 |      0    |     -1618.31 | Loss      |                                       |
| 2025-08     |        4 |                1 |     25    |     -2409.27 | Loss      |                                       |
| 2025-09     |        0 |                0 |      0    |         0    | No trades |                                       |
| 2025-10     |        2 |                0 |      0    |     -1330.52 | Loss      |                                       |
| 2025-11     |        5 |                0 |      0    |     -2606.12 | Loss      |                                       |
| 2025-12     |        3 |                0 |      0    |     -1142.7  | Loss      |                                       |
| 2026-01     |        2 |                0 |      0    |     -1434.19 | Loss      |                                       |
| 2026-02     |        7 |                3 |     42.86 |      -449.99 | Loss      |                                       |
| 2026-03     |        4 |                2 |     50    |      1496.85 | Profit    |                                       |
| 2026-04     |        3 |                2 |     66.67 |       479.58 | Profit    |                                       |
| 2026-05     |        2 |                0 |      0    |      -623.11 | Loss      |                                       |
| 2026-06     |        1 |                1 |    100    |       385.52 | Profit    |                                       |
| 2026-07     |        2 |                1 |     50    |      -128.28 | Loss      |                                       |
| 2026-08     |        0 |                0 |      0    |         0    | No trades |                                       |
| 2026-09     |        1 |                0 |      0    |      -326.32 | Loss      |                                       |
| 2026-10     |        1 |                0 |      0    |      -267.26 | Loss      | 2026-10-31 missing in source archive  |
| 2026-11     |        3 |                0 |      0    |     -1411.04 | Loss      | Partial: through 2026-11-16 23:59 UTC |

The trade counts and averages for the four Stage12 research periods were
reconciled against the original saved strategy summary and original Actions artifact.

Limitations:
- Modeled net BTC quote-price points, not dollar-account return
- Standard taker fees, GST and slippage included; funding and order-book impact not
- 2026-10-31 missing from source, 2026-11 partial
- This original historical dataset was previously researched; not an untouched forward test
- Entry month grouped in IST; no trades are not a profitable month
