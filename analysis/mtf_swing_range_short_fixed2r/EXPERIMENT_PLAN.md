# Stage 5 SHORT 1:2 reward:risk experiment (registered before results)

Only change to the previously completed SHORT 1:3 experiment:
- Stop-loss and take-profit pairs in BTC price points: **100 / 200**, **200 / 400**, **300 / 600**, **400 / 800**.
- Both values are measured relative to the actual modelled SHORT entry execution price (minute OPEN minus 5 price points for adverse SELL slippage).
- 120-minute max hold; conservative STOP-first for ambiguous OHLC; gap-through-stop filled worse; SHORT cover price includes +5 points adverse slippage.
- Keep the same finished 30m bearish trend definitions (bearish candle and lower-high/lower-low), all five 1m range/swing/rejection entry definitions, six UTC / weekday / NY / London / Singapore / IST session filters with daylight savings, same Delta BTCUSD 1m historic candles, same 0.05% per-side taker futures fee with 18% GST, and same funding-calendar exclusion.
- Same 2025 research / Jan-Jun 2026 chronological validation / Jul-Oct 17 2026 previously examined recheck periods. Not a pristine untouched holdout.
- All configurations and periods, including zero trades: 2 trends x 5 entry types x 6 session windows x 4 risk pairs x 3 periods = 720 rows. Save trade ledger, fee-vs-gross, drawdown, win rate, PF, audit.
- Cross-compare specifically 30m completed bearish candle, previous-24m range-low breakdown, NY 09:30–12:00, **400/800 vs prior 400/1200**, which was the promising 52-trade Jan-Jun case. Other variants remain diagnostic, not selected/tradeable based on recheck.
- No live fills, synchronized L1/L2 depth, liquidation modelling or live trading; conclusions explicitly provisional.
