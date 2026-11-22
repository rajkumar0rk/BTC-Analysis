# Monthly BTCUSD results — green-after-touch, 1% SL / 1.5% TP

January 2025–October 2026, 22 completed IST entry months.
Volume >= 1x and ATR(14) >= 0.20% of 15m price; ST10x3.
Long entered on the THIRD 15m bar OPEN after first bullish
line-touch candle and next bullish GREEN confirmation candle.
Take profit +1.5% of simulated market fill, hard SL -1.0%,
secondary 15m Supertrend closing-stop, next 1m open,
1m high/low replay with hard-stop-first OHLC collision.
Estimated 0.05% taker each side, GST 18% on fees,
5 BTC points adverse slippage each side. No funding or liquidation.
1BTC-equivalent BTC price-point P&L (NOT account dollar profit).

## Primary configuration (by IST ENTRY month)
| month_ist   |   trades |   winning_trades |   losing_trades |   win_rate_pct |   net_pts |   cumulative_net_pts |   tp_exits |   hard_sl_exits |   st_close_exits |
|:------------|---------:|-----------------:|----------------:|---------------:|----------:|---------------------:|-----------:|----------------:|-----------------:|
| 2025-01     |        8 |                2 |               6 |          25    |    583.86 |               583.86 |          2 |               0 |                6 |
| 2025-02     |        7 |                2 |               5 |          28.57 |  -1050.69 |              -466.83 |          1 |               1 |                5 |
| 2025-03     |        6 |                3 |               3 |          50    |   2335.57 |              1868.74 |          3 |               0 |                3 |
| 2025-04     |        1 |                1 |               0 |         100    |   1278.82 |              3147.56 |          1 |               0 |                0 |
| 2025-05     |        5 |                2 |               3 |          40    |   1399.42 |              4546.98 |          2 |               0 |                3 |
| 2025-06     |        1 |                0 |               1 |           0    |   -293.78 |              4253.2  |          0 |               0 |                1 |
| 2025-07     |        6 |                2 |               4 |          33.33 |   1989.04 |              6242.23 |          2 |               0 |                4 |
| 2025-08     |        4 |                1 |               3 |          25    |  -1659.07 |              4583.16 |          0 |               0 |                4 |
| 2025-09     |        2 |                0 |               2 |           0    |   -883.83 |              3699.34 |          0 |               0 |                2 |
| 2025-10     |        4 |                3 |               1 |          75    |   4378.16 |              8077.49 |          3 |               0 |                1 |
| 2025-11     |        5 |                2 |               3 |          40    |    171.53 |              8249.03 |          2 |               1 |                2 |
| 2025-12     |        3 |                1 |               2 |          33.33 |    285.84 |              8534.87 |          1 |               0 |                2 |
| 2026-01     |        4 |                1 |               3 |          25    |   -345.42 |              8189.44 |          1 |               0 |                3 |
| 2026-02     |        7 |                2 |               5 |          28.57 |   -344.65 |              7844.8  |          2 |               1 |                4 |
| 2026-03     |        7 |                1 |               6 |          14.29 |  -1852.88 |              5991.92 |          1 |               1 |                5 |
| 2026-04     |        4 |                1 |               3 |          25    |     85.92 |              6077.84 |          1 |               0 |                3 |
| 2026-05     |        5 |                2 |               3 |          40    |   1024.99 |              7102.83 |          2 |               0 |                3 |
| 2026-06     |        4 |                2 |               2 |          50    |    934.71 |              8037.54 |          2 |               0 |                2 |
| 2026-07     |        7 |                1 |               6 |          14.29 |  -1828.13 |              6209.41 |          1 |               1 |                5 |
| 2026-08     |        5 |                3 |               2 |          60    |   1409.91 |              7619.32 |          2 |               0 |                3 |
| 2026-09     |       11 |                5 |               6 |          45.45 |   2020.33 |              9639.65 |          4 |               1 |                6 |
| 2026-10     |        2 |                0 |               2 |           0    |   -817.32 |              8822.33 |          0 |               0 |                2 |

## Reconciliation and alternative configurations
| scenario               |   trades |   winners |   winrate_pct |   positive_months |   losing_months |   total_net_pts |   net_pts_2025 |   net_pts_2026 | highest_month   |   highest_month_pts | worst_month   |   worst_month_pts |
|:-----------------------|---------:|----------:|--------------:|------------------:|----------------:|----------------:|---------------:|---------------:|:----------------|--------------------:|:--------------|------------------:|
| line_touch_sl1_tp1p5   |      108 |        37 |         34.26 |                13 |               9 |         8822.33 |        8534.87 |         287.46 | 2025-10         |             4378.16 | 2026-03       |          -1852.88 |
| line_touch_sl0p4_tp1p5 |      108 |        31 |         28.7  |                13 |               9 |         3740.01 |        2624.29 |        1115.72 | 2026-09         |             2487.2  | 2026-03       |          -2343.3  |
| bullish_flip_sl1_tp1p5 |      197 |        68 |         34.52 |                 9 |              13 |       -24633.7  |       -8823.11 |      -15810.6  | 2025-10         |             3747.8  | 2025-02       |          -8674.09 |

## Method and limitations
- Month attribution is by entry timestamp in Asia/Kolkata.
- Metrics are historical; 2025 and 2026 not fresh OOS.
- In same-minute TP/SL collision, SL is treated as first.
- Same-minute favorable target at market open may be counted;
  third candle open entry can happen before that 1m high.
- No exchange funding, bid/ask, order book or actual maker/taker fill uncertainty.
- P&L is raw 1BTC-equivalent price-point units, not capital return.
