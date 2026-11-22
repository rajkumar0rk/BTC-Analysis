# Mean-reversion batch source audit — 2026-11-22 17:26 IST

Scope: independent mean-reversion family only. Existing completed MR002 #44911975169 / artifact 14709852576 is rejected (-30.5503268% NAV, 204 trades); not retested.

## Candidate 1: DebugDatta/Keltner-Channel-Indicator
Source: https://github.com/DebugDatta/Keltner-Channel-Indicator/tree/d60838ad20b675bd930c82179f3facdb5006b09b
Creator DebugDatta; commit d60838ad20b675bd930c82179f3facdb5006b09b; GitHub license metadata MIT. Source files strategy.py and backtester.py inspected read-only.

Exact entry from strategy.py mean_reversion_signals: long when previous close > previous KC lower AND current close < current KC lower; short when previous close < previous KC upper AND current close > current KC upper. Exit long on crossing upward through KC middle, short on crossing downward through middle. No regime filter in this pure mode. BTParams defaults next_open, 1% risk, ATR stop multiple 2, no TP, 1x max leverage, fee 1 bp and slip 2 bp each side. Original market and reporting sample are not independently established; no publisher PF/return/trades/DD accepted.

Critical source-engine defects in backtester.py: (1) entry execution is next open, but stop/TP check tests CURRENT candle high/low and then exits at NEXT open regardless of the stop price, so gap/stop behavior is not correctly simulated; (2) when trailing enabled, trailing_high updates from the full bar high before testing its low, creating unknowable intrabar ordering; (3) entry_px for BOTH long and short is next_open*(1-cost), and exit_px also next_open*(1-cost), so short-side costs are directionally wrong; (4) cash/equity uses cash+pos*close while cash already contains starting capital, and closes only add price-change P&L; this double counts short/long open exposure and does not represent account NAV; (5) qty is floor(shares), which is incompatible with fractional BTC contracts; (6) risk-based size is not capped by max_leverage when ATR is narrow. Consequently source publisher backtest metrics, if any, cannot be trusted as a Delta futures replay.

Novelty: Keltner channel fade differs from earlier altcoin KeltnerBounceV1 crossback + volume/BTC regime gate, and from MR002 VWAP-z crossback. However, compare Stage23 5m fade and other Keltner research before approval. Status: PARTIAL OVERLAP, NOT APPROVED; source-faithful SIGNALS are recoverable but source execution engine is unusable for causal BTC reproduction. A separate BTC 1m stop-first adaptation with original signal/stop defaults must be labeled as such, after NOVELTY_CHECK and actual workflow.

## Candidate 2: zodboy/freqtrade-simple-mean-reversion
https://github.com/zodboy/freqtrade-simple-mean-reversion
Publisher describes MIT, 1h long-only Bollinger(20,2) + RSI(14)<35, ROI table and -15% stop. Equivalent BB/RSI thesis to MR001/Strategy002; SKIP duplicate. No new historical replay.

## Candidate 3: PatrickSebastine/mean-reversion-trading-bot
https://github.com/PatrickSebastine/mean-reversion-trading-bot
Publisher describes MIT, Bollinger lower+RSI<25 long / upper+RSI>75 short, risk engine. Equivalent BB/RSI family already audited; SKIP duplicate. Momentum subsystem excluded from this family.

## Execution / honest handoff
Branch Actions list returned latest completed historical run #44911975169, SHA 0932ae131853e7fb26c6c164870bc4ae5d50adea, successful; no later completed replay. This iteration: three source candidates screened (one distinct conditional, two duplicates); zero new baseline backtests, zero variants, zero verified P&L, zero code fixes. No untrusted source executed, no main or other family changes.

Next executable action: inspect KC indicator defaults and closest Stage23 fade; if novelty approved, commit immutable source and NOVELTY_CHECK, adapt signal-only logic to existing authentic Delta 1m archived runner with 0.05% fee each side + GST 18%, zero slippage, stop-first/gap-through 1m fills, minute NAV and monthly IST reconciliation. Trigger branch workflow and verify run/jobs/artifacts before reporting any strategy outcome. Funding remains unmodeled.