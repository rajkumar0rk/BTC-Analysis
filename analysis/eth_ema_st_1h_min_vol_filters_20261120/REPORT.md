# ETHUSD 1h EMA/ST with minimum ATR and volume filters

Source: Delta Exchange India ETHUSD 1m data grouped into complete 1h bars.
Exactly the existing fixed 100/50 ETH trailing strategy, 1h entry and 1h monitoring.
Changed entry-filter master switch from Off to Both, with ATR(14) >= 1.0x average ATR over previous 20 bars and Volume >= 1.5x average of previous 20 bars.

## Results (one 0.01 ETH contract, fees and GST modeled)

| Trades | Net P&L USD | PF | Win rate | Positive months |
|---:|---:|---:|---:|---:|
| 207 | +7.1346 | 1.1185 | 35.749% | 10/22 |

## Monthly net profit (UTC)

| month_utc   |   trades |   net_wins |   net_losses |   gross_points |   net_points |   net_usd |   fees_usd |   gst_usd |   profit_factor |
|:------------|---------:|-----------:|-------------:|---------------:|-------------:|----------:|-----------:|----------:|----------------:|
| 2025-01     |       10 |          6 |            4 |         361.5  |     322.048  |    3.2205 |     0.3343 |    0.0602 |          2.2727 |
| 2025-02     |        4 |          1 |            3 |        -105.2  |    -117.784  |   -1.1778 |     0.1066 |    0.0192 |          0.3661 |
| 2025-03     |        9 |          2 |            7 |          12.95 |      -8.6755 |   -0.0868 |     0.1833 |    0.033  |          0.9729 |
| 2025-04     |       10 |          1 |            9 |        -185.4  |    -205.594  |   -2.0559 |     0.1711 |    0.0308 |          0.4732 |
| 2025-05     |        6 |          1 |            5 |        -117.45 |    -133.075  |   -1.3308 |     0.1324 |    0.0238 |          0.3876 |
| 2025-06     |       10 |          3 |            7 |         289.3  |     259.609  |    2.5961 |     0.2516 |    0.0453 |          2.0177 |
| 2025-07     |       12 |          6 |            6 |         102.75 |      57.0222 |    0.5702 |     0.3875 |    0.0698 |          1.1336 |
| 2025-08     |        8 |          6 |            2 |         799.4  |     758.35   |    7.5835 |     0.3479 |    0.0626 |          9.2812 |
| 2025-09     |       12 |          8 |            4 |         435.1  |     373.662  |    3.7366 |     0.5207 |    0.0937 |          2.2325 |
| 2025-10     |       12 |          6 |            6 |         273.75 |     214.756  |    2.1476 |     0.4999 |    0.09   |          1.4902 |
| 2025-11     |       12 |          4 |            8 |        -191.35 |    -235.608  |   -2.3561 |     0.3751 |    0.0675 |          0.5563 |
| 2025-12     |       12 |          3 |            9 |        -167.4  |    -210.581  |   -2.1058 |     0.3659 |    0.0659 |          0.5557 |
| 2026-01     |        9 |          3 |            6 |         -75.1  |    -107.722  |   -1.0772 |     0.2765 |    0.0498 |          0.6446 |
| 2026-02     |        8 |          4 |            4 |          23.15 |       4.3909 |    0.0439 |     0.159  |    0.0286 |          1.0241 |
| 2026-03     |        9 |          4 |            5 |         152.75 |     130.71   |    1.3071 |     0.1868 |    0.0336 |          1.6295 |
| 2026-04     |        9 |          3 |            6 |          19.45 |      -4.5777 |   -0.0458 |     0.2036 |    0.0367 |          0.9802 |
| 2026-05     |        5 |          4 |            1 |         176.5  |     163.619  |    1.6362 |     0.1092 |    0.0196 |          6.2292 |
| 2026-06     |        8 |          1 |            7 |        -132.9  |    -148.964  |   -1.4896 |     0.1361 |    0.0245 |          0.2494 |
| 2026-07     |       12 |          3 |            9 |         -11.15 |     -37.2054 |   -0.3721 |     0.2208 |    0.0397 |          0.8262 |
| 2026-08     |        8 |          4 |            4 |         244.55 |     225.166  |    2.2517 |     0.1643 |    0.0296 |          4.3664 |
| 2026-09     |       12 |          0 |           12 |        -410.2  |    -446.48   |   -4.4648 |     0.3075 |    0.0553 |          0      |
| 2026-10     |       10 |          1 |            9 |        -110.25 |    -139.603  |   -1.396  |     0.2488 |    0.0448 |          0.4431 |

## Limitations
- Identical original ETH 1h 100/50 backtest rules except BOTH minimum volume and ATR filters enabled for entry.
- Volume and ATR baselines use previous 20 fully closed hourly candles only; no look-ahead.
- 27-minute Scalper Offer window cannot be confirmed for intrabar exits from 1h OHLC; conservative model charges closing fee on all trades.
- Fee and GST are modeled, not confirmed exchange settlement; offer entitlement historically unverified.
- Historical 1h OHLC fills approximate TradingView and live market; no actual orderbook spread, funding, liquidation or margin.
- One 0.01 ETH contract, constant size; no leverage or account compounding.
- 22 complete UTC months January 2025 to October 2026.
