# EMA(9/21) 1H + 15M + 5M, 2R/3R — pre-run novelty decision

Date: 2026-11-22. Decision: **PARTIAL OVERLAP — approved differential** (explicit user-requested fixed configuration).

## Deterministic experiment (registered before seeing results)
- Delta Exchange India BTCUSD perpetual 1-minute OHLCV from `data/delta_india/BTCUSD/1m`.
- UTC close-labelled resamples from open-labelled 1m source (1H, 15M, 5M).
- At the COMPLETED 5-minute candle's close, long only when 1H EMA9 > EMA21 and 1H close > EMA9; 15M EMA9 > EMA21 and 15M close > EMA9; and 5M EMA9 crosses ABOVE EMA21 at that candle's close. Shorts reverse all comparisons.
- Trade enters at the immediately following 1m opening price, never on the signal candle.
- Stop at extreme of last three completed 5M bars (including signal) with $5 buffer; target at 2x or 3x the initial entry-to-stop BTC-dollar distance.
- Compare fixed 1:2 and 1:3 R:R, 7-day and weekdays IST entry masks (no post-hoc selection); one position at a time per case.
- At each minute, protective stop gets priority when both stop and target lie in that same 1m OHLC. Gaps through stops fill at the open; never assume the favorable intraminute path. No trailing or breakeven.
- Exit at stop, TP, 24h timeout, last 1-minute close before a dataset gap, or IST month boundary. The 24h maximum hold is an explicit conservative experiment rule, not an optimized threshold.
- Costs: 0.05% taker fee **per side**, 18% GST on fees, adverse 5 USD slip on each side. Funding, book spread, market impact, position sizing limits and liquidation are not modeled.
- Compute per-trade net USD per 1 BTC, compounded 1x account returns, win rate, max close-to-close equity drawdown, IST monthly results, invalid data/gap notes.
- Reference: full 2025 chronological results, then unchanged settings on already-researched 2026. **Neither period constitutes a genuinely blind holdout**; October 2026 missing-day and partial-month caveats must be reported. November 2026 excluded as incomplete.

## Closest prior work and why it is not equivalent
1. `scripts/research_trend_pullback_breakout_stage13.py`, `analysis/institutional_discovery_stage13_4h_1h_15m/`: 4H EMA20/EMA50 trend, 1H EMA20 pullback, and 15M breakout; not 1H/15M EMA9/EMA21 alignment with 5M EMA cross as trigger.
2. `scripts/research_mtf_swing_range_long_fixed2r.py`, `analysis/mtf_swing_range_long_fixed2r/`: 30M structure and 1M breakout, fixed 2R; differs in exact causal multi-timeframe EMA signal and 5M swing stop.
3. Branch `research/stage25-new-trend` — `scripts/research_independent_hourly_trend_stage25.py`, `analysis/independent_stage25_hourly_trend/`: 1H momentum/inside bar/Donchian with optional 4H filter; not simultaneous 1H/15M EMA9/21 alignment with 5M cross.
4. Main research stage19/monthly price action: prior EMA pullbacks and 1M stop-first exits exist; this is an incremental confirmatory **EMA cross/multi-timeframe** configuration, not a claim of a new trading concept.

This experiment answers the user's exact new causal rule comparison without sweeping hundreds of parameters. Preserve failures; do not label profitable based on unadjusted OHLC returns or treat fee-free results as executable.
