# Percentage-based BTCUSD risk/target grid — predeclared

2026-11-22. User requests replacing fixed BTC points with % stop loss and take profit including 0.120%, 0.20%, 0.30%, 1%, 2%, and 5%.

## Experiment
- BTCUSD 15m Supertrend (Wilder ATR10, x3), Delta India archived 1m Jan2025–Oct2026 (22 full IST entry months).
- Two user-discussed LONG entries, neither lookahead: second 15m candle closes GREEN after (A) first bullish Supertrend line touch, or (B) bullish Supertrend flip; market buy at third 15m candle OPEN. One entry per bull cycle.
- **SL % of simulated fill**: 0.10, 0.12, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75, 1, 1.5, 2, 3, 5%, plus no fixed % SL (Supertrend closing stop only).
- **TP % of simulated fill**: 0.10, 0.12, 0.15, 0.20, 0.30, 0.40, 0.50, 0.75, 1, 1.5, 2, 3, 5%. Include 0.118% in target reach diagnostics (prior question).
- Full 15 × 13 × 2 × 42 = **16,380** candidate configurations. 42 existing causal volume/volatility combinations: 6 volume (off, >=1x, >=1.25x, >=1.5x, >=2x, <=0.8x) x 7 15m ATR regimes (off, >=0.10/0.20/0.30/0.40% plus ATR relative >=1.25 or <=0.8).
- **Always retain original 15m Supertrend close-under-support / flip closing stop**, exit at following 1m OPEN, whichever occurs earlier among this stop, % hard SL or TP.
- Starting in entry 1m, a percent hard SL and TP can both touch. Because OHLC order unknown, **stop wins on same 1m**, conservative. % levels from entry fill = 1m opening raw midpoint +5 BTC point adverse slippage, and exit midpoint further minus 5 points. Stop gaps fill at 1m opening (worse). Resting TP fills assumed exactly on threshold. Exact orderbook/spread unavailable.
- Delta India taker 0.05% each side +18% GST on fee. No funding, liquidation, margin model, actual spread or queue. Historical net 1-BTC-equivalent price points, NOT capital returns. Relative % is absolute BTC price fraction, NOT leverage-adjusted account profit.
- Report all configurations and 22-month per-config cohort splits; representative unfiltered and volume>=1 ATR>=0.2 tables for two entry methods, 2025 and 2026 separately, trade counts/win rates, positive months, profit factor, maximum sequential equity drawdown.
- Historical configuration selection is descriptive. All source dates already exposed to research; no untouched historical OOS. Small trade counts can overfit. Disclose this.
- Do not touch master or deploy live.
