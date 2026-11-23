# M47 — three pinned acceleration source gates (2026-11-24 IST)

Research-only; no execution or profitability claim. Read codex/AGENTS.md and codex/STRATEGY_NOVELTY_GATE.md. Canonical momentum Actions branch query returned 11 runs; latest historical success 45141426585 is old M14.

## A. Elder Impulse MACD, FMZ (ChaoZhang description; SudeepBisht Pine)

Source https://github.com/flatmoonsociety/fmzquant-strategies-english/blob/fb01bf197009a41eeb3f3caa463b3e199c0f355a/Macd-Blue-Red-Leverage-Strategy.md ; original https://www.fmz.com/strategy/435982 ; modified 2023-12-20. Publisher context Binance BTC_USDT futures daily signals, 1h base, 2022-12-13 to 2023-12-19. Numeric trade count, PF, return, DD and costs absent; license not verified.

Actual Pine: EMA13 slope and MACD(12,26) minus SMA9 histogram slope both rise => long, both fall => short, otherwise close_all. No stop, target, trailing or risk sizing implemented, despite prose claiming a slow-MA trailing stop. Optional higher-timeframe security requires repaint review; default same-timeframe. Publisher's close-bar orders require causal next-minute-open adaptation. Partial overlap with earlier MACD score/M14; distinct simultaneous histogram and EMA slope with neutral-flat state. Licensing and novelty gate NOT CLEARED; no replay.

## B. remiotore ImpulseMACDVolumeStrategy

Source https://github.com/remiotore/ccxt-freqtrade/blob/4586a4c30611106117494c6518bca1840047f818/strategies/ImpulseMACDVolumeStrategy.py . Freqtrade long-only 5m, startup 50, ROI 10%, stop -5%; market, performance period, trade count, PF, return, DD, costs and license not established.

Actual entry MACD line ABOVE signal, volume above rolling20 mean, RSI above 50; exit MACD below signal OR volume below mean, plus ROI/stop. Despite comment, no crossover test; histogram calculated but unused. Trend/volume level filter, not MACD acceleration. Reject as duplicate-like high-turnover participation. No replay.

## C. Waddah Attar Explosion, LazyBear/ShayanKM

Original pinned source https://github.com/edyatl/waddah-attar-explosion/tree/928f43180f72ab1f8537c9faf6c78cd4258969f7 ; TradingView https://www.tradingview.com/script/d9IjcYyS-Waddah-Attar-Explosion-V2-SHK/ ; inspected secondary rule record https://github.com/HCH725/alpha-strategy-research/blob/4fed0df7aa5b1a1a8c6fb7d4f26480204a19d0fd/waddah-attar-explosion-macd-bb-deadzone-two-sided-btcusdt-1d-2026-10-11.md .

Indicator computes one-bar MACD(20,40) difference times 150, Bollinger width(20,2), Wilder true-range deadzone(100) times 3.7. Publisher prose defines entry and exit visual conditions but no executable sizing/position state, stop or target. Secondary researcher expressly marks its position machine derived and uses same-bar-close fills, not acceptable for causal Delta execution. Original performance metrics absent. Not source-faithful executable; volatility breakout-family overlap requires cross-family novelty review. No replay.

## Counts and execution economics

3 source mechanisms screened; 0 newly eligible complete licensed protocols; 0 new distinct authentic Delta historical backtests; 0 variants; 0 workflow launches; 0 verified new P&L. Modeled round trip fee plus GST = 0.118% of notional before spread, funding and slippage. Authentic data was not accessed this turn. Next: source-complete licensed acceleration system, novelty decision, immutable source and BTC2025 replay with completed higher-timeframe bars, next eligible 1m open, stop-first fills, trade ledger and IST NAV reconciliation. No main/other-family/VPS/live changes.
