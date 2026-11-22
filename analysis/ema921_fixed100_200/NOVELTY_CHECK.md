# Pre-run novelty check: EMA9/21 1H+15M+5M — fixed SL100 / TP200

Date: 2026-11-22. Decision: **PARTIAL OVERLAP — approved differential (user-requested fixed-distance risk)**.

## Locked test specification before inspection
- Exact entry signals from `scripts/research_ema921_1h15m5m_rr.py`: only closed hourly and quarter-hour EMA9>EMA21 and close>EMA9 for long, reversed short. Fresh 5M EMA9/21 crossover triggers; next 1m open entry. No signal changes or parameter tuning.
- Original Delta India BTCUSD perpetual 1m OHLCV from `data/delta_india/BTCUSD/1m/`; chronological 2025-01 to 2026-10 IST complete months as available; November incomplete, excluded. 2026 research-exposed, not blind holdout.
- Fixed **100 BTC/USD price points stop** and **200 points take profit** calculated from the adverse-slippage-adjusted entry fill, each trade, both directions.
- Market entry assumes 5 USD adverse slippage; protective stop and take profit also 5 USD adverse slippage. Taker fee 0.05% on executed USD notional on entry and exit plus 18% GST on fee.
- Check every 1-minute OHLC candle for stop and target; if both touched within the same minute, favor stop conservatively; crossing the stop at the minute open means fill no better than that open.
- Never use intraminute future information for a signal; entry at candle open after the completed 5M trigger.
- One position at a time, compare weekdays IST for entries vs all days, no trade cap, no TP move, no trailing, **no time-based exit**. Exit and close position at an IST month boundary and before missing-data gaps so monthly equity can be compared (exception clearly identified).
- Return measure: compounded account return at 1× notional per trade with separate net fees/slip; no funding, leverage, liquidations, order book, actual bid/ask nor lot/min size modeled.

## Prior closest experiment comparison
1. `analysis/ema921_1h15m5m_rr/RESEARCH_REPORT.md` and `scripts/research_ema921_1h15m5m_rr.py` on `research/ema921-1h15m5m-rr-20261122`: identical 1H/15M/5M EMA signal, but swings define a **variable-size** stop with 2R and 3R targets, plus 24h timeout. This test examines the materially distinct, **always fixed** 100/200-dollar stop/target on the same signals, without timeout.
2. `scripts/research_mtf_swing_range_long_fixed2r.py`: fixed exits but a 30M structure and 1M breakout, not EMA9/21 alignment across three frames.
3. `research/stage25-new-trend` `analysis/independent_stage25_hourly_trend/RESEARCH_REPORT.md`: hourly momentum/inside bar/Donchian, not this EMA 5M crossover confirmation.

Do not describe this as an independent strategy discovery; this is a confirmatory exit execution test on already researched data. Report both losing and winning cases unfiltered and do not optimize settings afterward.
