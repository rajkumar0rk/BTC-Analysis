# M03 — Source-code parity and archive-manifest audit (2026-11-21 13:15 IST)

Status: **REPLAY BLOCKED ON IMPLEMENTATION / NO COMPLETED BACKTEST**. This is a source and manifest audit, not evidence of returns.

## Directly verified sources
- Original Pine: https://github.com/shahzaib-574/MarketCipherTrading/blob/8302401c7b4f855fbb0c114a283dd4e57c7aebf1/vwap_momentum_strategy.pine
- Companion Python: https://github.com/shahzaib-574/MarketCipherTrading/blob/7d78e4e34dec86d8a6a56562a9a2f442bb797138/backtest_vwap_momentum.py
- Dataset manifest: `data/delta_india/BTCUSD/1m/manifest.json` on this branch.
- Novelty gate: `codex/STRATEGY_NOVELTY_GATE.md`.

## Important new data correction
The current manifest reports **2026-10 expected_minutes=44,640, observed_candles=44,640, missing_minutes=0**, contradicting the older gate and M02 report which mention 1,440 missing UTC October minutes. This is **manifest metadata only**: the gzip SHA256, monotonic 1m timestamps, duplicate bars, OHLC integrity, and real exchange provenance have NOT been independently verified. Do not carry forward the stale October gap claim without checking the current archive bytes. All Jan–Dec 2025 partitions report 0 missing minutes in the manifest. UTC partitions do not map exactly to IST calendar months; read adjacent partition edges.

## Concrete reproduction risks found in original code
1. Pine 4h VWAP `ta.vwap(hlc3)` is intraday/session anchored. Verify TradingView's session anchor and its timezone relative to companion Python's `anchored_daily_vwap`; do not silently substitute an arbitrary UTC daily reset.
2. Pine sets `entryAtr := atr` on the 4h signal bar, before next-bar execution. Companion Python `open_position` uses `ind["atr"][i]` at the fill bar index, which introduces lookahead when filling at that bar's open. Freeze signal-bar ATR for the protective stop.
3. Companion Python's cooldown `last_entry = i` uses the execution bar, whereas Pine `lastEntryBar := bar_index` uses the signal bar. For `cooldownBars=12`, reconcile the 1-bar difference.
4. Python tests `bars[i]["low"] <= stop` and fills at the stop price even if `bars[i]["open"] < stop`. A real long stop should fill at the worse opening price when the market gaps below the stop; use 1m stop-first/gap-aware execution and never infer 4h OHLC intrabar path.
5. Python `run_backtest` accrues entry commission by multiplying equity, and then in `close_position` calculates the trade return from equity **after** entry commission; the reported per-trade return excludes entry commission and its PF is based on percent returns rather than monetary net P&L. Implement explicit entry and exit fee/GST debits and net-cash trade PF, reconcile NAV.
6. Python `run_backtest` can overwrite pending exit decisions after an intrabar stop because it uses the current bar's signal regardless of the position state at close; guard order state carefully.
7. Pine `strategy.entry` is not gated by flat position and can reverse if both directions enabled. Baseline is LONG ONLY; preserve the published 4h mode and separate source defaults from Delta adaptation.

## Novelty gate and next execution
Decision **PENDING — partial overlap** with Stage25 1h momentum and Stage13 4h/1h/15m trend pullback. Exact old script/report comparison still required before approval. The incremental hypothesis is the *simultaneous seven-condition impulse score* (ROC10>0, RSI14>52, MACD histogram rising above zero, positive DMI+ADX14>=14, close>EMA21, EMA21>EMA55, close>previous close) combined with VWAP slope/pullback, 4h signal, 12-bar cooldown and 2.6 ATR stop. The source uses long-score >=7, EMA200 trend and a next-bar order. Merely adjusting EMA/ADX thresholds is not novel.

**Execution deliverable still missing:** approved novelty comparison, verified gzip hashes and complete UTC 1m chronology, exact source-faithful 4h-to-1m runner, actual BTC2025 workflow, trade ledger, IST NAV/monthly results and fee/GST reconciliation. No positive PF/returns or live-readiness is asserted. Funding unmodeled. Preserve other branches and real accounts.
