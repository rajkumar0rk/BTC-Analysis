# M45 — MACD/RSI dependency parity gate (2026-11-23 IST)

Static source audit only; **no new Delta historical backtest**, no source code executed.

Source: https://github.com/burakkalpak95-prog/ki-trading-bot/blob/main/user_data/strategies/MomentumMacdRsi.py (blob 0f13b9744d35a7e4f66c03cde1c284a79493eec2). Supporting blobs: src/kitb/risk.py 61d8324450d242eebdc0b81928e82e333fad79ac; src/kitb/rule_learning.py 612509f3c808657b5e35c354a3e87569185ad0a9; src/kitb/indicators.py fd4a4a92021cea9dafd7b96f4ea45725b8b0499a. All original source paths at https://github.com/burakkalpak95-prog/ki-trading-bot/tree/main/src/kitb. Repository API currently reports license=null; no LICENSE file in recursive tree; do not presume redistribution permission. Commit pin still required before reproduction.

## Recovered complete indicator and callback semantics
- Spot LONG only, 1h, 520 startup candles. TA-Lib MACD(12,26,9), RSI(14). Entry when MACD crosses above signal, MACD > 0, 50 < RSI < 70, volume > 0. Exit when MACD crosses below signal OR RSI > 80, volume > 0. Market entry/exit, -6% hard stop, ROI 100.0 (effectively disabled).
- StyleAiMixin only filters entries when `kitb_style_ai` is configured **and** live/dry-run; normal historical backtests leave it inactive. Its custom_stoploss returns None without a tagged learned stop, so baseline -6% applies. Learned 2/4/6% stops and exploration are live-like deviations, not faithful historical baseline.
- RiskManagedMixin is **not inert** in backtests: custom_stake_amount caps by configured position fraction, per-trade risk/stop, aggregate exposure and proposed stake; rejects leverage >1. confirm_trade_entry enforces long-only, duplicate-position, open-position, daily realized loss, active kill switch and min stake; drawdown halt and market freshness/liquidity checks differ in backtest vs live. Risk limits come from config/risk.json and must be pinned. Thus reproducing only MACD/RSI indicator rules with arbitrary fixed stake would NOT reproduce original account NAV.
- Source risk state uses realized closed-trade equity, UTC daily P&L; our required IST monthly mark-to-market NAV is a separate reporting layer. Entry is next eligible 1m open after completed 1h signal; stop-first and gap handling must be preserved. No same-bar fill or forward information is permissible.

## Decision
**NOT YET ELIGIBLE** for source-faithful Delta replay: risk.json and any active kill-switch/config state need pinning; no explicit reuse license; novelty against M14 and older hourly MACD/RSI work remains partial overlap. This is MACD crossover with positive level, not histogram acceleration, and may not justify a distinct momentum study. Do not fabricate missing backtest period, trade count, PF, return, DD or costs; publisher metrics unverified. The minimum modeled round-trip fee+GST is 0.118% notional before slippage/funding.

Actions branch query on 2026-11-23: 11 previous runs; latest successful historical run 45141426585 is old M14, not M45. New sources examined: 1 prior pending source with 3 dependencies; new distinct historical baselines 0; variants 0; new launches 0; verified new profitability 0. No main/other family/VPS/live mutation.
