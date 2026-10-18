# BTC Futures 5-Minute OHLCV: Repeated Patterns and Out-of-Sample Findings

**Source:** `underlying_bars(1).csv` (user-provided). **Period:** 2025-12-31 11:35 UTC to 2026-08-01 00:00 UTC. **Rows:** 61,206 continuous 5-minute bars.

## How tested

- Screened 44 mechanical candlestick, streak, range-breakout, sweep, EMA trend, and volume variants with features known at each signal candle close.
- Train: January–May 2026; chronological test: June–July 2026 (last UTC bar is August 1).
- Enter at **next 5-minute bar OPEN**. For a 30-minute directional outcome, compare that price to the close of the 6th subsequent bar; winner = favorable directional price move greater than zero.
- For primary findings, filter repeated signals to one accepted event every **at least seven 5-minute bars**, preventing overlapping 30-minute holdings within a pattern.
- Directional results are **before fees, funding, spread, market impact, and slippage**. Positive direction accuracy does not imply net trading profit.
- All prices are taken from source OHLCV; no implied fills from a real order book. In intrabar TP/SL tests, stop is conservatively assumed to trigger first if both thresholds are touched in one bar.

## Finding 1: Upside 24-candle breakout was more often followed by a 30-minute drop

**Rule:** Close of signal candle is strictly above highest high of the **previous 24 completed 5m candles** (past two hours). At the next bar open consider a hypothetical SHORT for 30 minutes. No other filter.

| Segment | Independent, spaced signals | Favorable SHORT outcome | Median signed move (bps) | Mean signed move (bps) |
|---|---:|---:|---:|---:|
| Jan–May 2026 train | 1,016 | 55.61% | +2.559 | +1.184 |
| Jun–Jul 2026 test | 404 | 60.64% | +4.231 | +1.378 |

**Monthly spaced 30-minute reversal hit rate:** Jan 57.53%, Feb 57.59%, Mar 57.45%, Apr 55.61%, May 50.00%, Jun 55.49%, Jul 64.86%. Calendar-day block bootstrap for June–July SHORT win percentage: **55.53%–65.63% (95% interval)**. For mean signed basis points: **-1.83 to +4.38** (includes zero).

**Retracement check:** In the test period, 62.13% of accepted upper breakout signals had at least one close back *below the prior 24-candle high* during the following 30 minutes; only 45.05% were back under that level at the final 30-minute close.

**Important limitation:** At 30 minutes, the result predicts direction somewhat better than chance but the expected raw movement is small. A separate, *one-position-at-a-time* test with a 1x ATR stop, 1.5x ATR target, and 12-bar max holding time averaged +1.867 bps in training (1,143 trades) and +1.862 bps in the test (461 trades). An **illustrative**, NOT exchange-specific, 2-bps round-trip cost turns these to -0.133 bps and -0.138 bps. The test is sensitive to execution assumptions and does not establish an investable strategy.

The reverse pattern, LONG after a downside break of the prior 24-candle low, failed out of sample: **55.47% train, 51.70% test** over the next 30 minutes (spaced events).

## Finding 2: Strong green impulse bars were often faded

**Pattern A, green 2x ATR bar:** Bullish 5m bar with full high-low range above 2x the pre-bar ATR(14) and candle body at least 65% of bar range. Next-bar open hypothetical SHORT, exit at close six bars later:

- Train: **54.32%** of 567 spaced signals; mean +1.35 bps.
- Test: **58.94%** of 246 spaced signals; mean +0.90 bps.

**Pattern B, strong green candle with volume spike:** Bullish candle body >=65% of range, range >1.8x pre-bar ATR(14), and current volume >2x previous 20-bar average. Hypothetical SHORT:

- Train: **55.00%** of 480 spaced signals; mean +1.65 bps.
- Test: **58.94%** of 207 spaced signals; mean +0.86 bps.

These patterns have weak average economic value and overlap conceptually with the upside breakout fade. They are research clues, **not verified net-profitable systems**.

## Finding 3: Volatility regime is more predictable than direction

Define the volatility-regime signal from information at each 5m close: ATR(14, Wilder-smoothed) **greater than 1.5x the median ATR over the *previous* 2,016 completed 5m bars (~7 days)**. Event: the absolute price change from next bar open to close 12 bars later (60 minutes) is **at least 50 basis points = 0.50%**. The direction is not predicted.

| Condition at signal | Jan–May probability | Jun–Jul probability | Test, hourly sampled |
|---|---:|---:|---:|
| All valid bars | 19.11% | 18.55% | 18.54% (n=1,462) |
| ATR >1.5x trailing 7-day median | 35.04% | 36.47% | 36.77% (n=291) |
| ATR <0.8x trailing 7-day median | 9.28% | 9.49% | 9.77% (n=430) |
| Weekday UTC 13:00–17:59 (IST 18:30–23:29) | 39.00% | 32.85% | 29.33% (n=225) |

In the June–July test, calendar-day block bootstrap difference for the high-ATR condition vs unconditional: **+17.63 percentage points**, 95% interval **+13.0 to +22.4 pp**. For low-ATR vs unconditional: **-9.01 pp**, 95% interval **-12.51 to -5.91 pp**. The fully overlapping bar-by-bar counts exaggerate independence; separate hour-sampled results corroborate direction of the effect.

**Practical interpretation:** If searching for large BTC moves, first filter for active/high-volatility periods. This may improve odds of a sizable move, but no *directional* advantage follows automatically.

## Finding 4: Intraday and weekend effects

- Full study: 5m average absolute close-to-close move peaked at 14:00–15:59 UTC (~19:30–21:29 IST); UTC 14 and 15 averaged 13.97 and 13.63 bps per 5m candle respectively.
- June–July: 14:00 and 15:00 UTC averaged 13.15 and 12.21 bps; quieter 10:00 UTC averaged 6.35 bps.
- June–July weekday mean 5m absolute close-to-close return **9.83 bps**, versus **5.92 bps on weekends**. These are volatility comparisons, not indicators of the next direction.

## Data cautions

- There are **no missing timestamps**, duplicates, NaN OHLCV fields or malformed OHLC highs/lows.
- **75 bars (0.12%)** have zero volume and perfectly flat OHLC values, often occurring in blocks. These could be no-trade periods or data-feed placeholders and merit verification before live-system use. Excluding signals within 24 bars of such candles had no material effect on the main upside-breakout result.
- The file does not contain order book bid/ask quotes, execution fills, commissions, funding, mark prices, instrument venue/contract metadata or leverage details. Historical OHLCV cannot validate exchange-specific net profit.
- Results end August 1, 2026 and do not cover later months. This is exploratory pattern discovery across 44 rules and several horizons; even withheld tests need independent, more recent forward validation.

## Suggested follow-up implementation

1. Display and log two independent detections in Strategy Lab: **24-bar high breakout (potential SHORT pullback warning)** and **ATR regime >1.5x rolling weekly median (large-move volatility alert)**.
2. Only alert, not auto-execute; decide direction separately, particularly in high-volatility periods.
3. Replay entries at next-bar open or bid/ask where available; test contract-specific fees/slippage/funding and fully overlapping exclusion, ATR stops, and risk budget.
4. Forward paper-test on August–October 2026 or newer data not used in the discovery before capital allocation.

See `btc_pattern_all_tests.csv` for full screened patterns: its row counts reflect **all pattern hits** (with overlapping forward windows), whereas key findings above use **spaced signals** and a separate trade simulator.