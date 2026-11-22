# Pre-run novelty check — EMA9/21 three-timeframe fixed exit grid (2026-11-22)

**Decision: PARTIAL OVERLAP — approved confirmatory exit differential (requested by user).**

## Incremental question
The identical historical 1H EMA(9/21) trend + 15M EMA(9/21) confirmation + 5M EMA(9/21) crossover generated losing results with (a) variable 3×5M swing stop with 2R/3R and (b) fixed **100 stop / 200 target**. The user's explicit question is whether a *larger stop* and/or *higher target multiple* can change that outcome under actual 1-minute stop-first execution, including **100/300** (1:3), **200/600** (2:6) and **200/800** (2:8).

## Distinct economics, no claim of signal novelty
- Entry signal remains **bit-for-bit the same** as `scripts/research_ema921_1h15m5m_rr.py` from branch `research/ema921-1h15m5m-rr-20261122`: completed 1H 9>21 and close above 9, completed 15M same, 5M 9 crossing 21 at candle close, or exact short inverse. Next 1m open only.
- Baseline 100/200 `analysis/ema921_fixed100_200/RESEARCH_REPORT.md` and `scripts/research_ema921_fixed100tp200.py` from `research/ema921-fixed100tp200-20261122`. This baseline is **not** retested as a new discovery; rerun is a reproducibility check and required to match historic trade counts exactly.
- Compare 26 fixed configurations, each independent and mutually exclusive within its own ledger, holding signals and fills constant:
  `(50,100),(50,150),(50,200),(75,150),(75,225),(100,150),(100,200),(100,300),(100,400),(100,500),(150,300),(150,450),(150,600),(200,300),(200,400),(200,600),(200,800),(250,500),(250,750),(250,1000),(300,600),(300,900),(300,1200),(400,800),(400,1200),(400,1600)` (SL points, TP points).
- Fixed stop and TP measured from entry **after** assumed $5 adverse entry slippage. Exit adds further $5 adverse slippage. Taker fee 0.05% of USD notional per side plus 18% GST on fees.
- One position at a time per scenario. 1m OHLC execution with stop-first if both barriers touch in the same minute; gaps through stop at 1m open, not artificially at stop. No time cap, no trailing, no EMA reversal exit. IST month boundary/data gap flatten ensures independent monthly accounting. Weekdays IST only vs all-days entry masks.
- Same Delta Exchange India BTCUSD 1m OHLCV archive; Jan 2025–Oct 2026 IST (22 months). 2025-01 IST starts 330 minutes late; Nov 2026 omitted. Fees/GST/slippage yes; funding/order book/true fill spread/liquidation not modeled.
- Compute win/loss, hit counts, gross/net P&L, per-month 1× account returns, max *closed-trade equity* drawdown, profit factor on net trade returns, fee totals, scenario split 2025 train vs Jan–Oct 2026 **already researched** recheck, and positive-month counts.
- Multiple-testing caveat: selecting the 'best' of 26+ variants using this history will be biased. No prospective or blind validation. Report losers and all tested parameters, do not optimize to 2026.
- Must verify baseline 100/200 exact trade counts: weekdays 1130 trades /359 net positive; all-days 1549/482. Fail if not.

## Comparison against research archive
- `codex/STRATEGY_NOVELTY_GATE.md`: not NEW as a signal, partial-overlap fixed exit **economic differential** is the only scoped research question.
- `analysis/ema921_fixed100_200/RESEARCH_REPORT.md`: prior fixed 100/200; no other fixed stop/target pair or 2026 sensitivity analysis here.
- `analysis/ema921_1h15m5m_rr/RESEARCH_REPORT.md`: variable stop + 2R/3R on the same entry rules; cannot answer fixed 200/800 or 100/300.
- `analysis/institutional_discovery_stage13_4h_1h_15m/RESEARCH_REPORT.md`: different 4H + 1H pullback + 15M breakout entry.
- `research/stage25-new-trend` hourly momentum/inside bar/Donchian: different entry.

This is an *exit sensitivity comparison*, not independent new alpha. Only empirical performance can justify choosing any configuration, with fresh-forward testing still required.
