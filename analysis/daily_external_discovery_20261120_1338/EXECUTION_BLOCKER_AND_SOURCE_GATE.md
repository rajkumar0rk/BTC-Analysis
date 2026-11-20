# Independent Daily-Profit — external discovery and execution gate (2026-11-20 13:38 IST)

Status: **NO NEW BACKTEST EXECUTED / NOT FOUND**. Previous path-efficiency experiment GitHub Actions run 44681216427, job 136104814197, completed successfully and was rejected on negative BTC net expectancy. This is not an open experiment.

## Actual discovery searches
- Public web: `site:github.com freqtrade strategy intraday time of day breakout opening range crypto python`
- Public web: `site:tradingview.com/script/ crypto intraday opening range strategy pine source`
- Read repository `codex/STRATEGY_NOVELTY_GATE.md` on isolated branch; existing intraday time and breakout/retest research in stages 6–9, 19, 24, 25.

## External sources screened
1. TradingView, Shivam_Mandrai, IU Opening range Breakout Strategy (2024-12-12): https://www.tradingview.com/script/JnOdejSN-IU-Opening-range-Breakout-Strategy/ . Described long: close crosses above opening range high; short: close crosses below opening range low; SL previous bar extreme; 2R target; max two trades/day; session end exit. TradingView open-source terms; direct source code unavailable from search result. **SKIP**: same core ORB mechanism as Stage24 breakout research; venue/session and fill specifics not fully verified. No code copied.
2. TradingView, martineye15, Opening Range Breakout ORB: https://www.tradingview.com/script/t2Uwp9FE-Opening-Range-Breakout-ORB-martineye15/ . Indicator, not trading strategy; breakout with optional retest, stop and target; **SKIP** Stage24 overlap and no executable order rules.
3. Freqtrade HourBasedStrategy by Masoud Azizi: https://github.com/freqtrade/freqtrade-strategies/blob/main/user_data/strategies/HourBasedStrategy.py . 1h clock window entries/exits plus ROI and stop; source requires hyperoptimization, default exit-hour bounds questionable. **SKIP** prior stage7 intraday time/day studies and source's selected SHIB returns not independently verified. License must be confirmed at exact commit before adapting.
4. TradingView Crypto Intraday Engine: https://in.tradingview.com/script/yQdPgJ6s-Crypto-Intraday-Engine/ . VWAP/UTC opening range/pivots indicator; **SKIP** non-executable description and overlap with VWAP/ORB/structure studies.

## Explicit execution gate
No externally sourced candidate passed novelty + reproducible execution-rule checks. Therefore a new backtest is **not** justified under `codex/STRATEGY_NOVELTY_GATE.md`. This iteration does **not** satisfy the requested new-experiment execution milestone. Do not pretend a zero-slippage screen occurred. Next: search a distinct mechanism with verified source commit/license and complete deterministic entry/exit; create dedicated branch, novelty file, runnable native BTC2025 zero-slippage + 0.05% each-side fee + 18% GST screen; only if positive, run 0.5 and 5 BTC-price-point adverse fill stress, then freeze and check BTC2026/ETH. Funding UNMODELED, spread and depth unavailable. Never alter other branches/main/live accounts.
