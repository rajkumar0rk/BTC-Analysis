# M23 — ROC momentum execution-engine parity audit (2026-11-22 IST)

## Verified recovery
Read codex/AGENTS.md and codex/STRATEGY_NOVELTY_GATE.md. Branch Actions list returned nine runs, most recent c71c783 M14 correction completed success (45008927902, 45008927897); prior M16 independently reconciled 27 trades and 12 IST rows. No M14 repair pending.

## Immutable external source audit
Publisher k0nkupa, MIT license, commit d859028be5fd938257e5ac12b9900a8d3e74913f.
- Signal source: https://github.com/k0nkupa/paper-trading-bot-hyperliquid/blob/d859028be5fd938257e5ac12b9900a8d3e74913f/src/strategies/momentum.py ; ROC(14) above +2% plus close>SMA20 long, ROC(14) below -2% plus close<SMA20 short, persistent rather than crossover signals; nominal TP 3% and SL 1.5%.
- Actual backtest engine: https://github.com/k0nkupa/paper-trading-bot-hyperliquid/blob/d859028be5fd938257e5ac12b9900a8d3e74913f/src/backtest/engine.py ; blob ee5ec6fe316eab006edcf551aacca334919d3fd6.
- Broker: https://github.com/k0nkupa/paper-trading-bot-hyperliquid/blob/d859028be5fd938257e5ac12b9900a8d3e74913f/src/core/broker.py ; blob 36603d58459c0839c134967c7b5a74353832d133.

## Critical reproducibility findings from exact code
1. Engine appends the CURRENT candle to history, computes the signal using that candle's close, and submits a market order using the SAME candle close. This is optimistic same-bar execution; a Delta causal replication must execute no earlier than next eligible 1m open, which is a declared execution adaptation, not exact original engine parity.
2. Engine checks stop/TP only against candle.close, not candle.low/high. A bracket hit and reversal within a candle is invisible. It cannot be treated as a stop-first intraminute replay. It also checks exits before signal on that candle.
3. When opening a position it assigns stop_loss/take_profit from strategy.get_stop_loss/get_take_profit. Thus bracket percentages ARE applied by the engine, despite not appearing in generate_signal. M22's uncertainty about bracket wiring is resolved. The signal handler closes on Signal.CLOSE, but opposite LONG/SHORT signals while already positioned are ignored; opposite-signal exit is NOT automatically implemented in this engine. Need inspect strategy source for whether it emits CLOSE with an existing position before assuming opposite-signal exits.
4. BacktestEngine default fee_maker=.0005 and fee_taker=.001, distinct from the Delta research fee of .0005 per side plus 18% GST. Actual broker fee path needs explicit selection audit; no source-reported trade statistics validated.

## Cross-family novelty decision
Stage25 report https://github.com/rajkumar0rk/BTC-Analysis/blob/research/stage25-new-trend/analysis/independent_stage25_hourly_trend/RESEARCH_REPORT.md already tests hourly momentum_accel over 12/24 lookbacks, 1m stop-first execution, and fee/GST/slippage; 285-347 trades for prominent configs, negative 2025 net returns. Generic ROC14 threshold plus SMA20 is PARTIAL OVERLAP, not automatically new. Incremental hypothesis would have to demonstrate signal persistence / exact ROC threshold plus 3%/1.5% brackets is economically distinct from Stage25, and first confirm original strategy's position-aware CLOSE behavior and source timeframe. **Decision HOLD / NOT APPROVED FOR NEW BACKTEST** until incremental novelty and full signal exit parity are proven. Do not port the publisher's same-close fills or claim its results on BTC.

## Additional completed task: causal acceptance checklist
A source-faithful Delta adaptation must explicitly preserve completed-bar ROC/SMA calculation, next 1m open, one position at a time, high/low bracket evaluation with stop-first ambiguity, gap-adverse fills, no invented reverse exits, both fees+GST, full sequential NAV and IST monthly marks. First screen assumes zero slippage, funding unmodeled; no 2025/2026/ETH P&L verified. This audit is static code inspection, NOT a historical backtest.

Counts: one previously sourced candidate engine audited across three source files; one Stage25 read-only novelty comparison; zero new source-defined historical baselines, zero variants, zero launches. No other branch, main, VPS or live-trading writes.
