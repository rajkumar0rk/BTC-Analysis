# ETHUSD 1h 100x — $0.20 pre-liquidation stop comparison

Settings unchanged from baseline except adding a protective stop $0.20 before estimated liquidation, tick-aligned.

| Model | Net profit | Ending balance | PF | Trades | Modeled liquidations | Pre-liq exits | Profitable months |
|---|---:|---:|---:|---:|---:|---:|---:|
| Without preliq | +3826.86 | 3926.86 | 2.8541 | 1678 | 230 | - | 22/22 |
| With preliq + $0.20 | +3676.56 | 3776.56 | 2.7627 | 1682 | 0 | 235 | 22/22 |

## Monthly P&L: pre-liquidation enabled

| month_utc   |   starting_balance_usd |   net_profit_usd |   monthly_return_pct |   ending_balance_usd |   trades |   wins |   losses |   liquidations |
|:------------|-----------------------:|-----------------:|---------------------:|---------------------:|---------:|-------:|---------:|---------------:|
| 2025-01     |                100     |         149.148  |               149.15 |              249.148 |       74 |     56 |       18 |              0 |
| 2025-02     |                249.148 |         202.367  |                81.22 |              451.515 |       65 |     47 |       18 |              0 |
| 2025-03     |                451.515 |         186.516  |                41.31 |              638.03  |       83 |     57 |       26 |              0 |
| 2025-04     |                638.03  |          51.082  |                 8.01 |              689.112 |       75 |     49 |       26 |              0 |
| 2025-05     |                689.112 |         199.912  |                29.01 |              889.024 |       70 |     56 |       14 |              0 |
| 2025-06     |                889.024 |         114.12   |                12.84 |             1003.14  |       73 |     51 |       22 |              0 |
| 2025-07     |               1003.14  |         221.286  |                22.06 |             1224.43  |       72 |     55 |       17 |              0 |
| 2025-08     |               1224.43  |         315.87   |                25.8  |             1540.3   |       68 |     53 |       15 |              0 |
| 2025-09     |               1540.3   |         118.846  |                 7.72 |             1659.15  |       86 |     62 |       24 |              0 |
| 2025-10     |               1659.15  |         230.286  |                13.88 |             1889.43  |       86 |     65 |       21 |              0 |
| 2025-11     |               1889.43  |         211.757  |                11.21 |             2101.19  |       77 |     57 |       20 |              0 |
| 2025-12     |               2101.19  |         152.351  |                 7.25 |             2253.54  |       81 |     57 |       24 |              0 |
| 2026-01     |               2253.54  |         233.266  |                10.35 |             2486.81  |       75 |     60 |       15 |              0 |
| 2026-02     |               2486.81  |         268.204  |                10.79 |             2755.01  |       74 |     55 |       19 |              0 |
| 2026-03     |               2755.01  |         275.042  |                 9.98 |             3030.05  |       85 |     68 |       17 |              0 |
| 2026-04     |               3030.05  |         105.051  |                 3.47 |             3135.1   |       83 |     62 |       21 |              0 |
| 2026-05     |               3135.1   |         149.399  |                 4.77 |             3284.5   |       84 |     61 |       23 |              0 |
| 2026-06     |               3284.5   |         130.496  |                 3.97 |             3415     |       69 |     52 |       17 |              0 |
| 2026-07     |               3415     |         114.79   |                 3.36 |             3529.79  |       63 |     48 |       15 |              0 |
| 2026-08     |               3529.79  |          60.7414 |                 1.72 |             3590.53  |       83 |     53 |       30 |              0 |
| 2026-09     |               3590.53  |         140.701  |                 3.92 |             3731.23  |       86 |     60 |       26 |              0 |
| 2026-10     |               3731.23  |          45.3322 |                 1.21 |             3776.56  |       70 |     46 |       24 |              0 |

## Caveats

- Pre-liquidation stop is not an entry filter; it tightens the exit price to a modeled threshold.
- 1h OHLC replay assumes the protective stop fills at its level on a crossing; stop execution may slip or fail in real trading.
- Liquidation modeled from last-trade candle prices and an assumed 0.25% maintenance rate, not actual historical Delta mark-price liquidation.
- The $0.20 buffer is Delta-Algo-Demo's ETH demo setting. Whether it is adequate requires exchange-confirmed liquidation and order-book testing.
- At a bar opening beyond liquidation, the model records liquidation, not a pre-liquidation fill.
- Historical 27-minute scalper fee eligibility cannot be proven with 1h OHLC; replay conservatively charges exit taker fee on all trades.
- Funding, spread, slippage and latency are excluded, as in the original 100x backtest.
- Returns are simulated, not reliable forecasts; no account or margin-mode change was made.
