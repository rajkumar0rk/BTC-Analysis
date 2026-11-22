# Preregistered incremental experiment — Supertrend 15m touch + profit protection

Date: 2026-11-22. **Incremental ablation** on previously completed Supertrend(10,3) bullish-touch research (not a novel entry strategy).

Previous comparisons:
- `analysis/supertrend_15m_touch_20261122/RESEARCH_REPORT.md`: first bullish 15m support touch, one entry per bullish cycle, no volume/ATR conditioning, 15m close stop, percentage take-profit exits.
- `analysis/supertrend_15m_filter_grid_20261122/RESEARCH_REPORT.md`: 6 prior-closed-bar relative-volume bands × 7 prior-closed-bar ATR regimes; every fixed-percentage-TP combination net negative.
- `analysis/supertrend_15m_touch_500_1000_20261122/RESEARCH_REPORT.md`: unfiltered +500 BTC-point first-passage 171/782 and +1000 92/782; +200 299/782.

## Incremental hypothesis
Test whether *causal protective exits after favorable price movement* improve net BTC price-point results of bullish Supertrend touch entries when prices retrace before fixed take-profit or 15m closing stop.

## Fixed rules
- BTCUSD perpetual Delta India 1m archive aggregated to fully closed 15m; same Wilder Supertrend ATR10 ×3; bullish flip is **not an entry**; wait for the first subsequent support-line touch, 1 long max per bullish cycle.
- Volume conditions: OFF, >=1.0, >=1.25, >=1.5, >=2.0, <=0.8 times mean previous 20 complete 15m bars; volatility: OFF, ATR14/close >=0.1/0.2/0.3/0.4%, ATR14 relative >=1.25 or <=0.8. All filters use last fully closed 15m candle, never the unfinished touch bar. Filter-rejected touch does not consume cycle.
- TP: +200, +500, +1,000 *raw BTC points* from hypothetical limit-fill mid; the +200/500/1000 hit diagnostics all agree with prior first-passage counts when protection OFF.
- Protection: baseline OFF; BE arm +200 → lock 0; arm +200 → lock +100; arm +300 → lock +100; arm +500 → lock +200; step-lock (arm +200 → lock +100, each +200 more peak increases lock +200); trailing (arm +300/distance100), (arm +500/distance200), (arm +500/distance300), (arm +1,000/distance200). 10 modes total.
- Protective stop only tightens, never lowers. The original 15m-close below prior confirmed ST support (or bearish flip) still exits at next 1m open if neither protective nor TP exit occurred.
- Replay 1m highs/lows from minute **AFTER** fill, using highest high seen so far to arm/ratchet protection; choose protective stop over take-profit on an overlapping 1-minute candle, a pessimistic sequencing convention. When 1m opens below protective stop, fill at open rather than the unreachable stop price. All TP and stop fills use 5 adverse USD points slippage per side plus 0.05% taker fee each side + 18% GST; no funding, queue, spread, or liquidation.
- 42 filter conditions × 3 targets × 10 protection modes = **1,260 backtest variants**. No automatic cherry-picking. 22 complete IST months Jan 2025–Oct 2026, 2025 reference vs 2026 observed follow-up; previously exposed historical data are **not untouched OOS**.
- Save all summary results, temporal splits, monthly counts, and trade ledger. Rank only on 2025 with >=30 2025 entries and >=60 total entries. Separate hindsight best from 2025 selection. Exclude November 2026 partial.
- The inherent OHLC path ambiguity on an activation + protective-stop hit inside the same minute can affect results. Same-minute stop-over-target and newly-armed-stop assumption are pessimistic *conventions*, not tick-level truth. Flag ambiguous events and compare to unprotected benchmark.
- 1BTC-equivalent price points are not leveraged account profit. No forward/live validation.

No merge or deployment; findings research-only, no profitable claims without data.
