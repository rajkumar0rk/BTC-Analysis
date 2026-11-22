# M13 novelty gate — MACD% + RSI extreme continuation (2026-11-22 IST)

## Source and exact baseline
Roshan7869, GPL-3.0 repository, commit `72a67c4db6b5585c3b576882c4ccbc2481832b95`, [archived Freqtrade source](https://github.com/Roshan7869/algotrading/blob/72a67c4db6b5585c3b576882c4ccbc2481832b95/user_data/strategies/_archived/hedge_momentum_macd_rsi_long.py). Original: 1h long-only, MACD line EMA12-EMA26 divided by close times 100 > 0.8, RSI14 >70, volume >0. Exit RSI14<50 OR MACD%<0. Freqtrade ROI target +30%, stoploss -10%, trailing stop offset +3% and positive distance 1%, custom_stoploss -0.5% if current profit >3%. Source returns 10x leverage and uses 50% tradable balance and up to 18 positions; these source assumptions are not a risk-matched single-BTC NAV simulation. Source has 100 startup candles; no published verified BTC PF, drawdown or trade count.

## Nearest prior art, read-only
`research/stage25-new-trend:scripts/research_independent_hourly_trend_stage25.py` tests hourly `momentum_accel`: bullish/bearish hourly directional regime, breakout beyond prior high/low, candle range >=1.35 ATR20, volume ratio >=1.1; 12/24 lookbacks and several 1m stop-first exits. `research/momentum-vwap-score-20261121:scripts/research_momentum_fusion_m08.py` tests 4h multi-indicator momentum/VWAP pullback with ATR stop. Stage25 tests acceleration via candle expansion and breakout, **not** a normalized MACD magnitude + RSI>70 joint extreme (per inspected script). Fusion has MACD among its score, but different 4h entry and exit economics. Thus **PARTIAL OVERLAP — differential provisionally approved** for a source-faithful first screen, subject to other research scripts' exhaustive check.

## Reproduction issues and disproof criteria
1. The source's custom stoploss returns -0.005 relative to current price when profit >3%, **not** an entry breakeven stop. Its documentation headline "Breakeven after +3%" is not executable specification. Freqtrade stop/trailing precedence and high/low candle processing must be pinned to an exact engine version before declaring faithful replay.
2. Its 1h indicators must use completed hourly bars; entry at next eligible 1m open. No lookahead, no same-bar signal fills, no optimistic 1m OHLC path. Gap and stop-first conservative priority.
3. Source long-only, no short half inferred; 10x and 18 concurrent positions are not imported into risk-matched BTC NAV. Preserve original defaults separately from Delta adaptation.
4. Fee+GST roundtrip at flat notional = 0.118% (0.05% * 1.18 * 2). For $10,000 notional, $11.80 before funding, spread or slippage. A high-turnover version must beat this hurdle per roundtrip.
5. Disprove if net expectancy <=0, PF<=1, or robustness collapses on chronological 2026 / ETH. Never optimize on exposed 2026. Funding unmodeled.

## Data, scope, status
Authentic Delta India BTCUSD 1m archive, BTC2025 first; IST Jan 2025 incomplete if archive begins 2025-01-01 UTC and lacks 2024 warmup. 2026-10 UTC has known missing 1440 candles; do not claim complete October. Data hashes must come from actual replay artifacts, not this document.

**STATUS: SOURCE PINNED; NOVELTY PARTIALLY APPROVED; HISTORICAL BACKTEST NOT EXECUTED.** Next: implement source-faithful Freqtrade trailing/stop precedence and original parameter baseline in a distinct runner, execute GitHub Actions to completed trade+monthly artifacts, then judge. This document alone does not establish a profitable candidate.
