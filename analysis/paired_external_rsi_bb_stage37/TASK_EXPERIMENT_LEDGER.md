# Stage37 external discovery / execution handoff — 2026-11-20 IST

Status: SOURCE SCREENING PENDING — no backtest run or profitability claim.

Latest own completed study: Stage36 zero-slip EMA9/VWAP screen rejected; 324 trades, PF 0.920, NAV -8.41%, 9/22 positive months. Source branch research/btc-first-external-ema-vwap-stage36-20261120, run 44717249423, original artifact 14619623197. Do not retune Stage36.

Online search query: site:github.com/freqtrade/freqtrade-strategies strategy volatility Bollinger RSI breakout.

Candidate A: https://github.com/freqtrade/freqtrade-strategies/blob/main/user_data/strategies/Strategy002.py ; Gerald Lonlas attribution per code; original repository GPL-3.0 reported in external catalog, verify actual license and exact commit before adaptation. 5m long-only: RSI<30, stochastic slowK<20, close below lower Bollinger(20,2), TA-Lib hammer=100; exits SAR>close and Fisher RSI>0.3; ROI/stoploss must be read from original source, not invented. Economic rationale: multi-confirmation oversold bounce; risk: extremely sparse signals, lookahead and framework ROI semantics, futures versus spot differences.

Candidate B: https://github.com/zodboy/freqtrade-simple-mean-reversion ; MIT stated in README, 1h long-only Bollinger(20,2) close below lower band and RSI14<35, stop -15%, tiered ROI 5/3/1/-1%; no independent returns. Potential overlap with prior RSI/BB family; novelty gate required before testing.

Candidate C: https://github.com/freqtrade/freqtrade-strategies/issues/297 ; community proposal not verified executable: BB(11,1.8), RSI19<25, bullish confirmation within eight bars, ATR20 stop and target 3.2x, cooldown eight bars. License unknown; defer until exact executable implementation found.

Next mandatory action: read codex/STRATEGY_NOVELTY_GATE.md and original source at fixed commit, choose novel executable strategy; implement original rules without lookahead on genuine BTC 2025 1m/5m data, commission 0.05% per side + GST 18%, zero slippage. Create branch-scoped workflow and verify actual Actions run. Screen BTC2025 first, reject negative/too-small samples; freeze if positive and only then stress 0.5 and 5 USD per side and check 2026/ETH. Keep 22 IST months and original trade/NAV ledgers. Funding, spread, impact and contract rounding unmodeled. Never label screening executable net.

No main, other schedule or live account mutation.
