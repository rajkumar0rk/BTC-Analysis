# Trend following — source verification, iteration 2 (2026-11-21)

Status: **SOURCE AUDIT COMPLETED; NOT YET AUTHORIZED FOR CODE REUSE OR HISTORICAL BACKTEST.** This is not a profitable-strategy result.

## Primary inspected source
- https://github.com/xy3293/crypto-strategy-backtest (README GitHub blob SHA `a6af08927c28badce1ed3be9f26a10ba6ce7afe3` retrieved 2026-11-21).
- README describes a 4h Binance USDT-margined futures simulator, with 15 strategies, four reportedly validated in the author's original research. The author says the recommended Sharpe-weighted portfolio is RSI/ATR + Keltner + SuperTrend, and parameter tuning failed out of sample. **Those are author statements, not our Delta BTC results.**
- `LICENSE` at repo root returned GitHub 404. Until licensing is established, do not copy source code into BTC-Analysis; publicly visible code is not automatically licensed for reuse. Exact strategy source commit HEAD remains unpinned. This blocks source-faithful code reproduction, not conceptual independent implementation where permitted.
- Relevant exact README rule descriptions:
  - `rsi_atr_trend_4h`: RSI(14) crosses above 70 and SMA100>SMA200 for long, below 30 and SMA100<SMA200 for short; exit adverse SMA regime or ATR stop (1.5 ATR).
  - `ema_ribbon_4h`: EMA9>EMA21>EMA55 for long, reverse for short; exit alignment break, ATR(14) stop 2 ATR, 14-day maximum.
  - `adx_trend_4h`: ADX14>25 and +DI>-DI for long, reverse short; exit ADX<20 or DI flip; 2 ATR stop, 14-day max.
  - `ichimoku_4h`: close above cloud and Tenkan>Kijun for long, mirror short; exit Tenkan/Kijun cross or reentry into cloud; 2 ATR stop, 14-day max. The source's shift semantics need code-level verification before testing.
- Original author claims Binance futures OHLCV + historical funding and mark candles, 0.05% taker fee, 0.05% adverse slippage each side, risk sizing at 1% equity and next-bar-open execution; Delta historical funding and mark data cannot be assumed equivalent.

## Mandatory novelty review
- Read `codex/STRATEGY_NOVELTY_GATE.md` and `codex/AGENTS.md` on main.
- Read prior `analysis/convex_trend_acceleration_20261119/RESEARCH_REPORT.md` at `research/convex-trend-acceleration-20261119`: 64 tested models, 0 qualifiers. Some models achieved PF 1.284 and 8.881% overall, with 13 positive / 10 negative months in a 23-month window. These are **prior** results, not new work.
- EMA ribbon, ADX and SuperTrend are economically overlapping previous trend filters. Their source presentation alone does not pass novelty.
- Candidate `ichimoku_4h` is a possible DIFFERENT structural trend-state model, but novelty versus Stage13 and Stage25 is not yet established. Decision: **UNDECIDED — DO NOT BACKTEST UNTIL GATE PASSES.**
- An alternative research direction is Hurst/efficiency trend persistence with Chandelier exit, but do not invent an undocumented rule or assert novelty without source and previous-study comparison.

## Next executable actions
1. Locate exact source SHA and repository license (or another clearly licensed independent implementation), inspect original code to confirm Ichimoku displacement is causal.
2. Inspect Stage13 and Stage25 scripts/reports for same structural Ichimoku/trend persistence signal; record `NEW` or `PARTIAL OVERLAP — approved differential` only with evidence.
3. Locate authentic Delta India 2025 BTCUSD 1m source and historical replay runner, verify timestamp gaps and checksums. If not present, treat data as blocker; do not substitute Binance prices.
4. Commit source-faithful baseline and workflow to this branch ONLY, run a real 2025 zero-slippage screen with 0.05% fee each side and 18% GST on fees, archive immutable trades and monthly NAV. Do not report backtest until a completed job/artifact exists.
5. Only after credible positive screen, freeze settings for 2026 BTC and ETH and test adverse slippage; funding remains unmodeled unless historical Delta events are sourced.

No new backtest, trade ledger, PF, or monthly NAV was produced in this iteration. No main branch or live account changes.
