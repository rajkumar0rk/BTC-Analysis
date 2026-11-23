# M48 — momentum source and execution-parity gate (2026-11-24 IST)

Research-only. Read codex/AGENTS.md and codex/STRATEGY_NOVELTY_GATE.md. Latest momentum branch Actions listing: 11 prior runs, latest historical success 45141426585 (M14), not an M48 replay. No source executed.

## 1. TradersPost Momentum Strategy Template — source-defined acceleration mode
- Source: https://github.com/TradersPost/pinescript-agents/blob/ebc382f88b6103fcda2569fe666a38b00fe714c5/templates/strategies/momentum.pine ; creator TradersPost; Pine v6; blob SHA 51d06ca7272f626104f6d58790f5ff39463cce24. No license established for this file. No original market/timeframe, period, trade count, PF, return, DD or complete cost validation supplied.
- Original defaults: 10% equity, 0.1% commission/side; MACD(12,26,9) signal crossover; EMA50 price trend; ATR14 stop 2x and target 2R. Both long and short.
- Distinct *optional* source mode: ROC12 threshold-cross setting is actually a continuous level condition, long when ROC>0 and ROC>ROC[1], short when ROC<0 and ROC<ROC[1]; MACD threshold mode is likewise a continuous histogram slope condition. They are not crossover events. Repeated signals may repeatedly submit entry/exit orders; Pine pyramiding defaults and order replacement must be reproduced exactly.
- Causal adaptation: completed signal bar then next 1m open; source stop and target are anchored to signal close, not actual fill, so execution gap changes realized R. No intrabar path inference. License and prior-art novelty (M14 MACD, prior ROC score) NOT CLEARED. No replay.

## 2. femibol Aggressive Scalper — stock-specific source cannot trade BTC unchanged
- Source: https://github.com/femibol/tpstrategyv3/blob/eaf689901135bd86d3f35f369ada888205c838a1/tradingview/aggressive_scalper.pine ; Pine v6; blob SHA f76d63b3b73d2c0c4ebcc32131593abe6feb1587. No explicit license verified. Original 1–5m low-priced US equity runners, not BTC; reported period/trades/PF/return/DD not established.
- Default preset **As-seen (aggressive)** overrides input defaults: EMA9/21, volume >1.2x SMA20, ROC5 >=0.2%, VWAP filter OFF, up to 8 trades/day, 1.5 ATR stop, 3R target, 50% partial, 2.5 ATR runner trail, 120-bar maximum hold. 25% equity, $0.005/share per side, five-tick slippage, `process_orders_on_close=true`.
- **Decisive source-fidelity gate:** priceOK = close >= $1 AND close <= $100, applied to every entry. BTCUSD at prices above $100 cannot generate any trades. Removing this would be a DERIVED adaptation, not the original baseline. Furthermore trailing stop is activated by `high >= entryPx + riskR` but `cand = close - trailMult*atr` is used on the same signal bar: cannot presume intrabar path or trailing activation before a stop. Cross/pullback signals are not acceleration-only. Reject unchanged BTC replay; avoid fabricated zero-trade BTC profitability.

## 3. iamrichardD BTC Futures MACD — publisher lead, not yet cleared
- Repository https://github.com/iamrichardD/tradingview/tree/9d20d513dcc3348024f82a0ffac6b2d90f6891a2 ; author iamrichardD; Apache-2.0 at repository root. Public summary advertises BTC MACD long-only and 85.71% win rate, 21 trades, PF 2.687, 8/21/5 MACD, 1.8% stop and 2.7% target. This is PUBLISHER CLAIM, not Delta evidence; dates, cost model, DD, complete source-execution parity and source-specific commit/path remain unverified. README is a marketing summary, not a faithful order protocol. Needs source path and code review, novelty comparison to M14, and possible repaint/fill check before replay. No invented source settings or historical results.

## Decision and costs
- Screened 3 distinct sources; 0 approved new baseline executions, 0 variants, 0 workflows launched, 0 new historical P&L verified.
- Fee screen: 0.05% notional per side * 2 * 1.18 GST = 0.118% notional round-trip, before funding/spread/slippage.
- Next: inspect actual iamrichardD Pine source and license scope; if novel, commit pre-run novelty record and batch with another licensed, executable acceleration source. Replay on authentic Delta 1m with next-minute open, stop-first gaps, sequential NAV and monthly IST mark-to-market. October 2026 has known missing 1440 UTC minutes; never claim complete 22-month verification.
