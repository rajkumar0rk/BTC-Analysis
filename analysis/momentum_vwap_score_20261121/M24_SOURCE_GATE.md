# M24 — independent momentum source screen (2026-11-23 IST)

## Recovery and controls
Read codex/AGENTS.md, codex/STRATEGY_NOVELTY_GATE.md and M23. GET Actions branch runs returned 9 runs, most recent M14 regression run 45008927897 completed SUCCESS at c71c783; no pending fix. No changes to main or other families.

## Candidate A — FMZ Momentum and Volume Bot: REJECT SOURCE EXIT PARITY
- Publisher: ChaoZhang; published modified 2023-12-19. Immutable GitHub source: https://github.com/fmzquant/strategies/blob/7853bb2bf262c4567ac238d3552d97f0e50cb801/基于动量交易策略Momentum-and-Volume-Trading-Strategy.md ; publisher https://www.fmz.com/strategy/435894 . License not established; do not copy implementation into project without permission/license verification.
- Published BTC_USDT Binance Futures daily-bar backtest specification: 2022-12-12 through 2023-12-18, basePeriod 1h. No independently validated PF, return, drawdown, trade count, or actual fees from source; all UNVERIFIED.
- Exact source signal: momentum=close-close[1], long on crossover above zero AND volume > 2 * SMA(volume,20), short on crossunder below zero AND same volume surge. Source defaults target input 0.8 and stop 0.5 labelled percent, but Pine strategy.exit(profit=close * 0.8/100, loss=close * 0.5/100) interprets profit/loss as TICKS, not percent or price! This creates instrument-tick-size-dependent distances and contradicts prose. Source prose also describes 0.8/0.5 times price, inconsistent with labels. Do not silently substitute percent brackets and call it source-faithful.
- Signal formed at daily bar close, orders default next chart-bar open, source exit values recomputed from current close each bar; stop/target placement parity would require original Pine engine and tick size. A correct Delta adaptation would use completed daily bar, next eligible 1m open, stop-first intraminute fills and explicit percentage-vs-tick model choice; that adaptation would NOT be original baseline.
- Novelty: price sign-cross plus volume spike overlaps earlier intraday volume/price stages 6–9; lacks demonstrated new acceleration mechanism. Decision SKIP. No backtest.

## Candidate B — Momentum-based ZigZag: NOT AN EXECUTABLE STRATEGY
- Publisher wrapper: ChaoZhang, original code attribution Peter_O, Pine v5 with MPL-2.0 header. Immutable source: https://github.com/fmzquant/strategies/blob/7853bb2bf262c4567ac238d3552d97f0e50cb801/Momentum-based-ZigZag.md . Example Binance BTC_USDT 10m, basePeriod 1m, 2022-05-09 to 2022-05-15 (only ~7 days).
- Code starts indicator(), uses QQE/MACD/MA directional turns and force flags to draw ZigZag labels; its GoLong/GoShort labels are not sufficient evidence of order sizing, actual fills or a complete executable portfolio exit protocol. Any invented bracket or holding period would be a new strategy, not reproduction. Reversal pivot labels also mix momentum and reversal, and the public claims of non-repainting need separate confirmation against plotted past pivots and bar-close timing. Decision NOT REPRODUCIBLE as published trading system; no historical backtest.

## Economic/causal checks
Delta research first-screen fee hurdle is 0.05% per side * 1.18 GST * 2 = 0.118% round trip before slippage, funding and spread. These are not publisher costs. No source P&L has been reproduced or inferred. Original tick-based exit mismatch and indicator-only second candidate make both unsuitable for faithful baseline runs; do not waste historical executor cycles.

## Session counts
Two source-defined candidates screened, zero approved distinct strategies, zero historical baselines, zero variants, zero launched workflows. Next action: search for license-clear, full-order, acceleration-focused momentum source with explicit non-repainting entry and exit, novelty-check against Stage25, then batch authentic BTC2025 replay. Existing M14 regression already verified, no repeat.
