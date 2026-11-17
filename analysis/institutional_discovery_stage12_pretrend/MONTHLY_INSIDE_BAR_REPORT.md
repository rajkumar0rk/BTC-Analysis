# Stage 12 exact inside-bar 2R strategy: Monthly consistency audit

Pattern: 06_inside_bar_break; market state: aligned_trend_plus_5m_compression_break.
2R reward, 120-minute hold, original structurally derived stop. No change to entries.
Months assigned by entry timestamp in Asia/Kolkata.
Net points include modeled 0.05% taker fees per side, 18% GST and 5 points per-side slippage.

Profitable months: 12/23
Losing months: 10
Months without trades: 1
Net total points equivalent: 5839.44

| month_ist   |   trades |   winning_trades |   win_pct |   net_points | status    | coverage_note                         |
|:------------|---------:|-----------------:|----------:|-------------:|:----------|:--------------------------------------|
| 2025-01     |        0 |                0 |      0    |         0    | No trades |                                       |
| 2025-02     |        3 |                1 |     33.33 |      -541.48 | Loss      |                                       |
| 2025-03     |        3 |                3 |    100    |      2285.67 | Profit    |                                       |
| 2025-04     |        2 |                2 |    100    |      1283.42 | Profit    |                                       |
| 2025-05     |        4 |                2 |     50    |       187.31 | Profit    |                                       |
| 2025-06     |        1 |                0 |      0    |        -8.16 | Loss      |                                       |
| 2025-07     |        1 |                1 |    100    |      1095.35 | Profit    |                                       |
| 2025-08     |        1 |                1 |    100    |       871.31 | Profit    |                                       |
| 2025-09     |        1 |                0 |      0    |      -478.42 | Loss      |                                       |
| 2025-10     |        1 |                1 |    100    |       834.46 | Profit    |                                       |
| 2025-11     |       10 |                4 |     40    |       930.14 | Profit    |                                       |
| 2025-12     |        7 |                2 |     28.57 |     -1162.53 | Loss      |                                       |
| 2026-01     |        6 |                3 |     50    |      -144.93 | Loss      |                                       |
| 2026-02     |        4 |                2 |     50    |       474.56 | Profit    |                                       |
| 2026-03     |        3 |                1 |     33.33 |      -134.15 | Loss      |                                       |
| 2026-04     |        4 |                2 |     50    |      -249.76 | Loss      |                                       |
| 2026-05     |        2 |                0 |      0    |      -366.08 | Loss      |                                       |
| 2026-06     |        3 |                1 |     33.33 |      -938.62 | Loss      |                                       |
| 2026-07     |        1 |                1 |    100    |       411.42 | Profit    |                                       |
| 2026-08     |        1 |                1 |    100    |       336.64 | Profit    |                                       |
| 2026-09     |        3 |                0 |      0    |      -985    | Loss      |                                       |
| 2026-10     |        2 |                2 |    100    |      1115.09 | Profit    | 2026-10-31 missing in source archive  |
| 2026-11     |        1 |                1 |    100    |      1023.18 | Profit    | Partial: through 2026-11-16 23:59 UTC |

The trade counts and averages for the four Stage12 research periods were
reconciled against the original saved strategy summary and original Actions artifact.

Limitations:
- Modeled net BTC quote-price points, not dollar-account return
- Standard taker fees, GST and slippage included; funding and order-book impact not
- 2026-10-31 missing from source, 2026-11 partial
- This original historical dataset was previously researched; not an untouched forward test
- Entry month grouped in IST; no trades are not a profitable month
