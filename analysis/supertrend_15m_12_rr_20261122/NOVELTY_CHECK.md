# Novelty / pre-registration — 12 fixed point-risk/reward tuples with protective stops

Date 2026-11-22. This is an **incremental experiment on known Supertrend touch entry** (not an independent new strategy).

## Known earlier tests
- research/supertrend-15m-touch-20261122: Supertrend Wilder ATR(10) ×3, buy limit on first support touch in bullish cycle, 15m close stop; 22 months, all original % TP variants net negative.
- research/supertrend-15m-filters-20261122: 42 volume/ATR regime entry selections; 200/500/1000 BTC-point target first-passage counts and PnL.
- research/supertrend-15m-profit-protection-20261122: ten profit-protection modes with fixed targets but **no hard initial point-based stop**; all 1,260 variants negative.

## User's exact 12 combinations
Interpreting ratio terms as **100-BTCUSD-point units**, since the request differentiates 1:1, 2:2, and 3:3. Thus the first number is the fixed hard stop distance in 100-point units and the second is target distance in 100-point units:
- 1:1=100 SL/100 TP; 1:2=100/200; 1:3=100/300; 1:4=100/400.
- 2:2=200/200; 2:4=200/400; 2:6=200/600; 2:8=200/800.
- 3:3=300/300; 3:6=300/600; 3:9=300/900; 3:12=300/1200.

## Execution fixed before analysis
- Entries: original bullish Supertrend touch setup, no entry on bullish flip, first qualifying touch per bullish cycle, 15m support from last fully closed candle. Retain original secondary stop on 15m close below prior ST line or bearish flip, fill next 1m open. Long only.
- A **fixed hard SL** from entry midpoint at entry−SL_points, monitored continuously using 1m lows, including the *entry minute* adverse wick when the touch-filled order is known to have occurred no later than the 1m low. A +TP from entry midpoint is evaluated only after the entry minute because no intra-minute order of entry vs 1m high is available. For same 1m post-entry bar touching hard SL and TP, assume hard SL first. Gapped stops exit at 1m open, if worse than limit.
- Profit protection modes reused exactly from prior study: off, breakeven after +200, lock +100 after +200, lock +100 after +300, lock +200 after +500, step up after +200 (lock +100, step +200), trail100 after +300, trail200 after +500, trail300 after +500, trail200 after +1000. Prior maximum favorable movement on *completed* 1m candles sets active protective stop at minute start; an activation+retracement within the same 1m is modeled pessimistically as high-then-low (flag ambiguous). Fixed hard stop takes precedence. A resting TP less than or equal to the protection trigger takes precedence over a *newly* activated protection.
- Compare 12 ratios × 42 previously selected volume/volatility conditions × 10 profit-protection modes = **5,040** configurations, with all full-series results retained. Same complete 22 IST months Jan2025-Oct2026. Filters computed only on last completed 15m candle.
- Taker 0.05% each side +18% GST, 5 BTCUSD points adverse slip per side. No funding, queue, book spread, leverage, margin or liquidation. Report gross/net 1-BTC-equivalent **price-point** PnL, not account returns.
- All 2025 and 2026 were previously studied; no untouched OOS. Rank descriptively by 2025 mean net per trade with >=30 2025 and >=60 total trades; test 2026 separately.
- Count by *IST entry month* for total and monthly PnL to retain trades crossing a month boundary. This changes months vs prior exit-month accounting; explicitly flag the difference. Don't combine overlapping filtered variants. Long-only; no shorts.
- Sanity-check unfiltered entry count 782 and no-protection target hits can never exceed earlier 200/500/1000 baseline first-passage counts for SL-limited variants.

Research branch only, no merge or deployment. No claims of live profit without independent forward validation.
