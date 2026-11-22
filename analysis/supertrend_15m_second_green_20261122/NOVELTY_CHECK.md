# Predeclared experiment — second GREEN 15m confirmation after bullish Supertrend

Date: 2026-11-22.

Historical source: Delta India BTCUSD perpetual 1m data Jan2025 through Oct2026 completed IST months, 15m complete aggregation.

## Why this test
User proposes entering on "second candle green" in bullish Supertrend context. Two distinct legitimate meanings require separation rather than conflation:
A. **Touch-next-green**: The original bullish Supertrend 15m support-touch bar is candle 1. Only if the immediately NEXT 15m candle is green (close > open) AND the bull Supertrend state remains confirmed after both bars, enter a LONG at the **OPEN of the third 15m candle** (first 1m open after second candle closes).
B. **Flip-next-green**: Candle 1 is the 15m bar at which Supertrend first flips bullish on close; if immediately subsequent candle 2 is green and ST remains bullish, enter LONG at candle 3 open. No line touch needed.
C. **Original touch**: Buy limit on first qualifying touch of last confirmed bullish support in each bullish ST cycle, as original baseline.

The distinction matters: cannot buy at the second candle's OPEN based on knowing it will close green. Green confirmation requires waiting to its close. For market entry at third candle OPEN, BOTH TP and SL may occur in first 1m candle: evaluate both, stop-first when simultaneous. For original resting limit touch, pessimistically check entry-minute adverse stop but exclude entry-minute favorable TP.

All cases long-only; one trade per ST bullish cycle. If first touch second candle not green or ST not bullish, SKIP that ST cycle, do not use a later touch; no hindsight choosing. Flip filter uses the last fully closed bullish-flip candle before 2nd bar; touch filters use last closed candle before the touch bar; both are causal.

## Comparisons
- Gross first-passage +100/+200/+500/+1000 before 15m Supertrend closing-stop (no hard SL) for all 3 entry variants and all 42 previously used volume/ATR filters.
- Hard 1m stops 100/200/300 BTCUSD pts with the exact 12 user-requested SL:TP settings: 1:1,1:2,1:3,1:4,2:2,2:4,2:6,2:8,3:3,3:6,3:9,3:12. Preserve original 15m closing-stop as secondary exit, next 1m open after completed bar.
- Profit protection: OFF (baseline), breakeven after +200, lock+200 after +500. Profit-lock can only work after activation (not beforehand). New arm+stop in same 1m: pessimistic high-then-low, flag ambiguity; hard stop/previously active stops take precedence. Standing fixed TP with target <= protection activation takes precedence over newly activated protective stop.
- All 42 existing volume-ATR filters: total 3×42×12×3 = 4,536 distinct backtest configurations, plus 504 first-passage grouped summaries. All filters use last complete bar.
- 0.05% taker per side, 18% GST on fees, 5 BTC price points slippage per side; funding, book depth, spread, liquidation, leverage omitted. P&L in hypothetical 1BTC-equivalent price points, NOT account dollars or return.
- 22 complete IST entry months Jan2025-Oct2026; November partial excluded. Monthly PnL attributed to entry month.
- Baseline parity for original touch +100=430, +200=299, +500=171, +1000=92; original touch 1:1 tp exits=325 across 782 entries.
- Screen results without chasing only best backtest: headline unfiltered comparison with per-trade net, profitable months, and quality. Rank 2025 reference separately, 2026 research-exposed follow-up separately; no untouched out-of-sample. Filtered cases are overlapping and cherry-picking risk is high.
- Do not deploy or merge; dedicated research branch.
