# Novelty check — 1H failed order-block / breaker confirmation, fixed 3R

2026-11-21; user asked for a profitable BTC 1H candidate with over 30% wins, at least 3:1 gross target.

## Source / hypothesis
Tessera Trades published 'BTCUSDT 1h breaker block strategy' Nov 18 2026:
https://www.tesseratrades.co.uk/trading-strategies/btcusdt-1h-breaker-block-strategy
The author's reported 30.7% win and net profit factor 1.75 are for **5R**, in Binance-like BTCUSDT bars; full proprietary order block detector is not specified on the web page.
Our implementation is **an independent, explicit, testable proxy** using Delta India BTCUSD perpetual price action and **fixed 3R**, NOT an exact reproduction and NOT a guarantee that the original 5R works on Delta.

## Causal deterministic rules
1. Full 1H UTC bars from genuine Delta India 1m candles; hourly candle timestamp is its CLOSE boundary.
2. Each previously completed 1H bar has Wilder ATR14 of true range.
3. Create a **bullish order-block candidate** when a GREEN 1H displacement candle closes above the prior 12 complete 1H candle highs, has directional body >= 0.5 ATR14, and a bearish candle occurred in the last 3 finished hourly candles. Store the most recent prior bearish candle **body range** with creation timestamp. Bearish OB created symmetrically on a red displacement close below prior 12-hour low and a prior green candle. The body range, not wick, is the broken zone.
4. Failed bullish OB -> SHORT when on a later finished hourly candle: candle is red, previous hourly close >= bottom of stored OB body and current close < OB bottom - 0.1*current ATR14. Failed bearish OB -> LONG symmetrically with close > top + 0.1 ATR14. Each stored OB usable once and expires after 48 complete hourly bars. If multiple zones flip on one bar, choose newest. No same-bar creation/execution or future candles.
5. Signals restricted to candles whose opening hour UTC is 13,14,15,16 (London/New York overlap). The 1h completed signal close may be traded at the following minute OPEN.
6. Stop: for LONG signal bar LOW - 0.25 ATR14, for SHORT signal bar HIGH + 0.25 ATR14; fixed TP=3 x risk at the genuine next 1m OPEN, +$5 adverse entry and -$5 adverse exit. No trailing and no maximum hold.
7. Risk size: 1% start-of-trade equity risk at initial stop capped at 2x total notional; one position total; all stop/target checked every genuine minute, conservative stop first in same minute, gap-through stop worse-open fill. Funding proxy from completed Delta 1h rates at 00/08/16 UTC, not real settlement cashflow; 0.05% taker fees per side and 18% GST on fee, plus $5 slip each side.
8. Account starts $10k; IST month-end marked-to-market returns including open-position liquidating-cost estimate, record all trade events, win%, PF, positives, drawdown, year 2025 and Jan-Oct 2026 separately.

## Prior work reviewed / exact difference
- `analysis/independent_stage25_hourly_trend/RESEARCH_REPORT.md` (`research/stage25-new-trend`): hourly momentum/Donchian/inside bar, no creation and subsequent failed OB state.
- `analysis/institutional_discovery_stage19_new_1h_patterns/`: 1H price action / regime compression / EMA engulf 2R,3R, with 4h/8h hold; not a 48h independently stored order-block failure and 1m multi-day hold.
- `analysis/institutional_discovery_stage24_structure_monthly10/` (`research/stage24-monthly10`): 15m retest / squeeze / failed auction; different structural event and timeframe, but conceptually overlaps failed breakout.
- `analysis/daily_bollinger_30_3r/`, `analysis/hourly_bollinger_30_3r/`: BB close breakout, no block state.
- `codex/STRATEGY_NOVELTY_GATE.md`: read; concern for previous intraday failed breakout assessed.

## Decision
**PARTIAL OVERLAP — approved user-directed external breaker hypothesis** with materially different two-event OB lifetime and validation, fixed before result inspection. One pre-registered 3R configuration; no post hoc target/range tuning.

## Validation
Use data January 2025 to November 19 2026; November partial; 2026 already historically researched and is NOT pristine out-of-sample. Recheck gap quality from actual archive. Report failures too. Publisher numbers are **5R** and thus cannot be transferred to this **3R** strategy.
