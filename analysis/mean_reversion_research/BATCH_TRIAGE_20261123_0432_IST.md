# Mean-reversion batch gate — 2026-11-23 04:32 IST

Status: source/novelty audit only; **zero new historical executions**. Existing MR003 Actions run 45036174691 is latest successful branch historical workflow (queried via branch Actions collection), rejected at 6550 trades / -99.92% NAV / PF 0.534. No new candidate may be reported profitable.

Mandatory prior-art gate: codex/STRATEGY_NOVELTY_GATE.md, Stage19 BB/RSI/sweep, MR002 rolling VWAP z-score, MR003 Keltner. Oct 2026 has 1440 missing UTC 1m bars; not a complete validated month.

## Source A — PatrickSebastine/mean-reversion-trading-bot
- https://github.com/PatrickSebastine/mean-reversion-trading-bot/blob/master/strategies.py ; pinned inspected blob 999ec765a5d52dc2ea862b7d53384afb0a4a1b49; risk.py blob d1aa86ba044b90d10d0ed914e64e5a9e77600865. Creator Patrick Sebastine, GitHub MIT metadata. Repository updated 2026-11-20.
- Original multi-exchange crypto 15m, BB20/2 and RSI14: BUY close <= lower BB and RSI<25; SELL close >= upper BB and RSI>75; strength scaled by band penetration. Separate risk class default 2% stop, 4% TP, 10% wallet cap, 3% daily loss threshold. Publisher describes 7-day OKX futures results in docs; exact return, trade count, PF, DD not independently recovered this iteration; do not invent.
- **SKIP — DUPLICATE CORE**: BB/RSI extreme fades already covered by Stage19, without a new economically distinct causal mechanism. Risk defaults and altered thresholds do not satisfy novelty. Signal uses current closed candle; next eligible 1m open needed, not source's instantaneous trading interpretation. Do not mix its momentum strategy into this family. No local Delta backtest.

## Source B — Ares-Infenus/rsi-backtesting-engine
- https://github.com/Ares-Infenus/rsi-backtesting-engine/blob/main/README.md ; inspected README blob 32a6ab49cf9dd43fdf24be64b00b02fffe1c637b. MIT metadata. Original BTC-USD daily 2020-01-01 through 2024-12-31, long-only RSI14<30 entry, RSI14>70 exit; next-bar open, 0.1% per-side commission, 0.05% adverse slippage, full capital per entry. No structural stop in documented baseline. Publisher metrics not recovered; do not imply profitable.
- **SKIP — PRIOR ART + UNBOUNDED LOSS EXPOSURE**: classic RSI mean-reversion overlaps Stage19 and source lacks structural stop. Appending a stop would be an adaptation rather than source-faithful baseline. README data cleaner supports bfill: if used, that risks future leakage; never silently fill historical missing minutes.

## Source C — zodboy/freqtrade-simple-mean-reversion
- https://github.com/zodboy/freqtrade-simple-mean-reversion ; public web index describes 1h long-only BB20/2 below lower band + RSI14<35, Freqtrade ROI ladder 5% -> 3% -> 1% -> -1%, -15% stop, purported MIT README. **GitHub connector repository GET returned 404** at screening, so immutable commit, executable source and actual license could not be verified. No publisher trade count/PF/return/DD recovered.
- **NOT REPRODUCIBLE** until repository is accessible and source pinned. Mechanism also overlaps Stage19 BB/RSI. No historical job.

## Next executable work
Search genuinely different low-turnover mean-reversion mechanisms (e.g. statistically defined liquidity sweep failure with session reset and objective stop, or paired spread reversion only with authentic synchronized data), verify source commit/license, compare actual Stage19 entry code, commit a NEW NOVELTY_CHECK in its own output directory, then reuse authenticated Delta BTC1m runner with 0.05%/side fees +18% GST, next-open fills, stop-first gaps and full NAV reconciliation. Source-fidelity modifications must be explicitly labeled. No protected branches, other families, VPS or trading changed.
