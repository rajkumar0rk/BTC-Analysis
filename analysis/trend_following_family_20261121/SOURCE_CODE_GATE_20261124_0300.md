# Trend family source-code batch — 2026-11-24 03:00 IST

Scope: three public pinned source candidates, source-fidelity and novelty triage only. This is NOT an authentic historical backtest, a completed fix, or verified P&L. GitHub branch Actions query returned 30 runs; latest historical execution still run 45131335895 (completed SUCCESS, Kali-Uga, not a new result). Read codex/AGENTS.md, codex/STRATEGY_NOVELTY_GATE.md, family NOVELTY_CHECK.md and family ledger before screening.

## Candidate 1 — Amogh Athalekar, RSI/Stochastics/Chandelier
Pinned original: https://github.com/amoghathalekar/Stochastic-RSI-Trend-Following-Strategy/blob/4f4d2a40804829caba0577b7637c3665d6c0d6d6/RSI-Stochastics%20strategy%20NEW%20-%20github%20copy.py
Source market: ~50 NSE equities (Yahoo Finance adjusted daily OHLC), dynamically last 2520 days; NOT Delta BTC. License: no LICENSE in repository root at pinned snapshot; permission to reuse derivative code NOT established. No publisher BTC2025/2026 after-cost PF, trades, NAV or DD supplied.

Exact source: RSI Wilder-like length 250; stochastic of close within 20-bar high/low range. Flat -> LONG if RSI>=50, stochastic now >25 and previous <20; SHORT if RSI<50, stochastic now <75 and previous >80. Long exit if adjusted close below *previous* Chandelier long = rolling high(22) - 2*simple-average ATR(22); short exit if adjusted close above previous rolling low(22) + 2*ATR(22). State remains long/short otherwise; no position reversal while held. No explicit protective exchange stop, sizing or exchange costs.

Critical fidelity/causality: signal and exit use current daily close, but source computes daily return using the same candle's close/stop. A next-eligible-minute-open Delta implementation MUST separate signal close from execution. On exit source books prior Chandelier line regardless of whether candle ever traded through that level, and does not model gaps or OHLC intrabar path. This is optimistic/incorrect stop-fill accounting; source is not directly executable as an honest 1m stop-first backtest. The daily RSI250 also needs ~250 prior daily bars; Jan 2025 warmup may be unavailable. Formula differs from StochRSI (stochastic is price, not RSI). Existing StochRSI and ATR-trailing studies overlap components; incremental hypothesis is unusually slow RSI regime plus stochastic pullback with Chandelier exit. Decision: PARTIAL OVERLAP, novelty and source licensing not yet cleared for a new historical test. No code copied or executed.

## Candidate 2 — dooliepachachas Chandelier Long Exit
Pinned: https://github.com/dooliepachachas/Chandelier-Long-Exit/tree/4c67e76c0d15103e5b94ff9d9522452017c0ea45
README describes stop at highest price since entry minus NumATRs x ATR(ATRLength); initial stop entry-bar price minus NumATRs x ATR. No complete entry signal or size; source license not verified. Distinct from a rolling-window highest high, but is only an exit module. Decision: NOT A COMPLETE STRATEGY; do not fabricate entry and claim source-faithful replay.

## Candidate 3 — EarnForex PersistentAnti
Pinned: https://github.com/EarnForex/PersistentAnti/tree/8c7ef3f2d0e52d761c0e91726d5dc2b04e966095
README explicitly trades *against* detected trend persistence to anticipate reversal, original EUR/USD weekly MetaTrader EA, and warns of total loss. Published qualitative EUR/USD weekly claims are not BTC results. Source license exists but not audited here; full MQ4/MQ5 signal/size/exit not recovered. Decision: OUTSIDE EXCLUSIVE TREND-FOLLOWING FAMILY (countertrend/mean reversion). Refer only read-only to mean-reversion research; do not duplicate.

## Disproof and execution gate
The only potentially differential candidate is Amogh's slow-RSI/stochastic/Chandelier combination. Before any replay: compare Stage25 and prior trend-family stochastic/ATR implementations, establish license/reimplementation policy, pin exact source and original baseline, obtain >=250 prior daily warmup or explicitly disclose untestable early months, and precommit a new NOVELTY_CHECK.md. Reproduce original rules but replace impossible same-close fills with completed-day signals, next eligible 1m open, causal 1m stop-first/gap fills. Apply 0.05% notional fee each side plus 18% GST, zero assumed slippage initial screen, risk-matched sizing, sequential NAV and IST monthly MTM; funding UNMODELED. If no authentic minute runner can be launched, record blocker, never report fabricated P&L. BTC2026 is an exposed chronological recheck, not pristine holdout.

Counts: 3 source implementations screened, 0 approved new baseline, 0 historical runs launched/completed, 0 variants, 0 verified new P&L. No other-family or main writes, no deployment or orders.
