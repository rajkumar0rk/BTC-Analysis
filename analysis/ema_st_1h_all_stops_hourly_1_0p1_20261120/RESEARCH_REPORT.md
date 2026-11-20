# 1H-only ATR and trailing monitoring backtest (1 / 0.1)

**Entry and Supertrend reverse remain 1H.** Prior stop/trailing model is 1M; new is 1H OHLC. Fee assumptions and sizing unchanged.
**Historical period:** January 2025–October 2026 (22 complete months). Verified Delta India archive.

| Asset | Stop/trailing evaluation | Net USD | PF | Trades | Positive months |
|---|---|---:|---:|---:|---:|
| BTC | Previous 1M | -91.32 | 0.0885 | 108 | 0/22 |
| BTC | New 1H inferred | +4298.18 | 6.222 | 2405 | 22/22 |
| BTC | New 1H adverse_first | +2465.22 | 2.0216 | 2400 | 22/22 |
| BTC | New 1H favorable_first | +4433.96 | 6.7371 | 2406 | 22/22 |
| BTC | New 1H close_only | -97.77 | 0.4838 | 57 | 0/22 |
| ETH | Previous 1M | -90.80 | 0.3592 | 158 | 0/22 |
| ETH | New 1H inferred | +6773.09 | 5.1504 | 2421 | 22/22 |
| ETH | New 1H adverse_first | +3322.70 | 1.7426 | 2420 | 21/22 |
| ETH | New 1H favorable_first | +7385.07 | 6.1585 | 2423 | 22/22 |
| ETH | New 1H close_only | -96.75 | 0.8908 | 189 | 0/22 |

## Caveats
- This changes time resolution, not whether prices crossed a stop intrabar. No real 1H candle reveals high-vs-low chronology.
- An hourly inferred-path model may be dramatically optimistic versus the prior one-minute replay. Treat intrabar-path cases as sensitivity bounds, not confirmed fills.
- Close-only exits are filled at the 1H close optimistically and may be later than a broker fill; exchange liquidation can still happen intrabar.
- Underlying hourly OHLC cannot establish Delta mark-price liquidation, spreads, stop order latency or tick-size price fills.
- Conservative no-offer results use all fees; assumed 27-minute Scalper discount almost never qualifies on 1H bar-end times and does not prove eligibility.
- Synthetic 100x isolated margin/preliq proxy differs from actual shared Demo Portfolio Margin; entry fee is charged before trade close.
- BTC requested 0.1 trailing distance is below 0.5 assumed tick; modeled as 0.5. No strategy bots or live VPS orders were changed.
