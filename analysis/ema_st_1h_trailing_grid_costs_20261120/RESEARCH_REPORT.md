# BTC and ETH EMA20+Supertrend trailing grid: costs included
1H signal, 1M OHLC stop monitoring; 22 months historical (2025-01 to 2026-10).
100/50 was regression-checked against the previous script.

| Asset | Activation/Distance | $100 wallet normal USD | $100 stressed USD | 22-month fixed-size stress USD | PF (fixed-size stress) | Positive months /22 |
|---|---|---:|---:|---:|---:|---:|
| BTC | 100/50 | -96.62 | -97.62 | -1,907.97 | 0.2748 | 0/22 |
| BTC | 150/50 | -96.42 | -97.35 | -1,677.71 | 0.4252 | 0/22 |
| BTC | 200/50 | -95.06 | -98.20 | -1,546.41 | 0.5285 | 1/22 |
| BTC | 200/100 | -90.83 | -91.90 | -1,647.54 | 0.4975 | 1/22 |
| BTC | 300/100 | -92.87 | -91.22 | -1,418.91 | 0.6292 | 2/22 |
| ETH | 100/50 | -92.05 | -92.30 | -2,214.00 | 0.3217 | 0/22 |
| ETH | 150/50 | -93.00 | -96.06 | -2,125.48 | 0.4507 | 0/22 |
| ETH | 200/50 | -91.16 | -94.26 | -2,009.75 | 0.556 | 1/22 |
| ETH | 200/100 | -91.36 | -94.03 | -2,293.13 | 0.4925 | 1/22 |
| ETH | 300/100 | -96.14 | -91.95 | -2,095.19 | 0.6143 | 2/22 |

## Caveats
- Real liquidation and funding payments require exchange mark-price and settlement records; historical FUNDING candles are OBSERVATIONS, not actual realized account funding debits.
- Stress assumes 0.01% unfavorable funding at each crossed 8-hour boundary; realized signed funding may differ.
- 1M historical candles still do not reveal exact tick movement or limit-order fills.
- Continuity mode is a research diagnostic to compare all 22 months, NOT the return obtainable with $100 starting cash.
- No backtest settings or bots were modified on the VPS.
- Scalper-offer simulation is hypothetical; not necessarily available over historical date range.
- Slippage stress includes 0.5 BTC and 0.05 ETH points per fill, not actual spread or modeled depth.
- Fees and GST follow assumed taker 0.05% each side, GST 18%.
