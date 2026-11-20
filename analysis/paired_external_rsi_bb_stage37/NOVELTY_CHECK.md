# Stage37 novelty decision — 2026-11-21 IST

Source: https://github.com/freqtrade/freqtrade-strategies/blob/6fce5f382bebb5d9ca7e0c2e9b8c676f6f4eb461/user_data/strategies/Strategy002.py
Author Gerald Lonlas; repository GPL-3.0. No third-party code copied.
Closest existing family: RSI/Bollinger mean reversion, including earlier Stage19 RSI2 and monthly regime work. **PARTIAL OVERLAP**.
Incremental falsifiable hypothesis: simultaneous hammer candlestick, stochastic oversold, RSI14 oversold and typical-price Bollinger breach, with SAR/Fisher exits and timed ROI, changes the trade distribution compared with generic RSI/BB entries.
Do not claim novelty merely because indicators are combined. Source-faithful 5m entry, exit and execution behavior must be validated before research screening.
Selection window BTC 2025 only; 2026 and ETH never used to choose parameters.
Missing historical order book prevents confirmation of limit fills. Conservative deterministic fill/cancel rules required and clearly labeled approximations. No historical funding => UNMODELED.
Decision: PROVISIONAL, source-faithful implementation preflight required. No backtest authorization until causal semantics and data coverage validated.
