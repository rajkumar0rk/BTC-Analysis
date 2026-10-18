# BTC Futures — data-first 15-minute candle discovery

## Data and method
- Original input: `underlying_bars(1).csv`, 61,206 continuous 5-minute OHLCV observations, December 31, 2025 to August 1, 2026 UTC.
- Aggregated to **20,402 complete 15-minute candles** (three consecutive 5-minute candles each), including the original partial December 31 UTC span and the August 1 00:00 UTC bar. The 15-minute research subset uses **20,352 15-minute bars** between January 1 and July 31 UTC, inclusive.
- UTC timestamps converted to New York local clock via `America/New_York` (DST aware).
- 15-minute OHLCV formed as first open, max high, min low, last close, sum volume.
- The original file does **not** state whether timestamps refer to candle OPEN or CLOSE; aggregations retain the raw convention and **label each resulting 15-minute group at the right-hand boundary**. If raw timestamps are close times, `09:45` is the bar running approximately 09:30–09:45 ET. If raw timestamps are opening times, align carefully to the source exchange before applying in TradingView.
- Relative candle range = (high−low)/open in basis points, divided by the median range of the eight immediately preceding completed 15-minute candles (2 hours); volume ratio similarly. **Only prior bars** are used for normalization.
- Searched **all 672 combinations** of 7 days of the week × 96 quarter-hour time slots; also pooled 96 slots across weekdays and weekends, separately.
- Tracked direction, range, relative volume, next-15/30/60/120-minute close-to-close changes, and chronological stability (Jan–Apr discovery, May intermediate, Jun–Jul later validation).
- Automatically clustered candle geometry into seven candle-shape types using Jan–Apr *only*; searched every observed 2-, 3-, and 4-candle shape sequence (longer shape sequences too sparse for reliable inference), plus every preceding 1–3 candle red/green sequence.

## Key discovery 1 — Weekday 09:45 ET 15-minute candle: consistent volatility spike
- **104/152 = 68.4%** of weekday 09:45-stamped candles have a range >2 times the previous two-hour median; median range multiplier **2.33×**; median high-low **69.70 basis points (0.6970%)**; median relative volume **2.83×**.
- Median normalized range in Jan–Apr **2.65×**, May **2.19×**, Jun–Jul **2.06×**. Exceeded 2× in Jan–Apr 65/86, May 13/21, and Jun–Jul 26/45.
- 09:45 had a larger normalized range than 09:30 on **135/152 weekdays** (paired by date); median of the pairwise 09:45/09:30 normalized-range ratios **1.84**.
- Direction **not consistent**: 81/152 (53.3%) candles red overall, red rates Jan–Apr 46/86, May 16/21, Jun–Jul 19/45.
- At the 09:45 close, the following hour had an absolute *close-to-close* change >=0.5% on 50.0% of weekdays; this is an observation, not a guaranteed tradable move.
- As a possible interpretation only, this window includes the US equity-market opening if stamps are bar closes. Do not treat that as established causation.

## Key discovery 2 — Sunday 18:15 ET 15-minute candle: weekly expansion
- **26/30 = 86.7%** exceeded 2× prior-two-hour median; **3.25×** median normalized range; **3.27×** median normalized volume; median high–low **70.29 bp (0.7029%)**.
- Jan–Apr **15/17 >2×** (range multiplier 3.06×), May **5/5** (2.88×), Jun–Jul **6/8** (3.88×).
- Same slot on Saturday: only **5/30 >2×**, median multiplier **1.29×**. Exploratory Fisher exact p ≈3.5e−8; multiple-testing and source-feed concerns remain.
- Red 15/30, green 15/30: **no directional prediction**.
- If timestamps are close-stamped, this 15m bar contains the 18:05 ET 5-minute spike found previously.

## Key discovery 3 — Weekday 17:00 ET quiet patch
- **2/152 = 1.3%** of these candles exceeded 2× previous two-hour range; median range **0.68×**, volume **0.47×**, red **74/152 = 48.7%**.
- Jan–Apr 0.65×, May 0.69×, Jun–Jul 0.75×; persists as a low-activity period, not a directional short/long setup.

## Sample question — does 08:30 ET turn red?
- Weekday 08:30-labeled 15m bar: **81/152 red = 53.3%**; Jan–Apr 43/86, May 9/21, Jun–Jul 29/45.
- Weekday 08:45-labeled 15m bar: **81/152 red = 53.3%**; Jan–Apr 46/86, May 8/21, Jun–Jul 27/45.
- Weekday 09:30-labeled 15m bar: **91/152 red = 59.9%**; Jan–Apr 45/86, May 16/21, Jun–Jul 30/45. This is exploratory only; tested over many times and red rates vary between periods.
- These do not support a consistently bearish 08:30 open-time strategy.

## Candidate fixed weekday/direction observations — NOT proven edges
- The strongest full-sample weekday/time red bias is Thursday **22:30 ET**: 25/31 red = **80.6%**; Jan–Apr 12/17, May 5/5, Jun–Jul 8/9. An exact two-sided 50/50 test yields p≈0.000878 *for this one selected slot*, but after conservative correction for **672 scanned weekday/time cells**, adjusted p≈0.59. **It does not survive the multiple-comparison test.** The median next-15m price change is only about −4.44 bp; the next hour's median change was **positive**, not further down.
- Friday **19:45 ET**: 23/31 green = 74.2%, split Jan–Apr 12/17, May 4/5, Jun–Jul 7/9. Also only a hypothesis after selection from 672.
- Of 672 individual 50/50 direction tests, 25 passed nominal p<0.05 and **zero** passed conservative Bonferroni p<0.05. A clock time being historically red does not prove the following candle or an eventual short is profitable.

## Automatically observed candle-shape sequences
Seven single-candle shape clusters learned from Jan–Apr candle body/wick shape, normalized range and normalized volume. Cluster descriptions (typical medians):
- **Cluster 3**: strong bullish body (about 70% of range), normal size/volume.
- **Cluster 6**: strong bearish body (about 71% of range), normal size/volume.
- **Cluster 0**: small-range candle with conspicuous lower wick (about 50% of range), lower-than-usual volume.
- **Cluster 1**: unusually large high-volume candle (median range 2.37× and volume 2.96× baseline); often mixed direction, generally weak wick dominance.
- **Cluster 2**: upper-wick dominated candle (median upper wick 53% of range).
- Other clusters 4 and 5 represent lower-wick and upper-wick shapes at differing normal/small sizes. Full descriptions exported.

**Candidate shape sequence A: 3→0→0** (a large-body green candle, then two small lower-wick candles): the *next* 15-minute CLOSE is lower in **95/156 = 60.9%** of occurrences, with chronological down rates **57/92 (62.0%)**, **10/17 (58.8%)**, **28/47 (59.6%)**. Median next-15m move **−2.0 bp (−0.02%)**; **June–July mean is positive +0.62 bp**, so the edge may be economically nonexistent and was selected from many shape sequences.

**Candidate shape sequence B: 3→6** (a strong green-body candle followed by a strong red-body candle): *next* 15-minute price close is higher in **55.9%** of 640 occurrences (next-15m down 44.1%). Jan–Apr 56.4% up in 369 examples; May 55.7% up in 88; Jun–Jul 55.2% up in 183. Median next-15m rise **+1.9 bp (0.019%)**, too small to imply profitability after fees/spread. June–July average next-15m price change is **negative** despite the higher positive-rate.

**Candidate shape sequence C: 1→1→2** (two large, high-volume candles, followed by an upper-wick candle): the absolute **next-60-minute closing change** was ≥0.5% in **22/77 (28.6%)** Jan–Apr, **7/25 (28.0%)** May, and **12/38 (31.6%)** Jun–Jul, versus period baselines **21.4%**, **9.4%**, **18.7%**. The direction varied across periods. The effect may be mostly an already-high-volatility regime: in Jun–Jul, all Cluster-1 candles already had 25.6% probability of a ≥0.5% move.

No examined directional candle sequence is established as tradeable after multiple-testing, signal overlap, realistic fills or futures expenses. Candidate samples are small and chosen from hundreds of tested sequences. A new untouched dataset is needed before committing money.

## Time conversion (assuming right-hand timestamps correspond to close)
New York clock times follow DST; corresponding India Standard Times:
- Weekday 09:45 ET -> **19:15 IST** in US daylight-saving time, **20:15 IST** in US standard time.
- Sunday 18:15 ET -> **Monday 03:45 IST** during US daylight-saving time, **Monday 04:45 IST** during standard time.
- Weekday 17:00 ET -> **next-day 02:30 IST** during daylight-saving time, **next-day 03:30 IST** in standard time.

## Limitations and next steps
- The original CSV has 20 aggregated 15m bars with zero summed volume, a source-feed data-quality concern. None of the claimed results assumes zero-volume candles are valid tradeable quotes.
- Findings depend on the venue and its source-feed conventions. Raw OHLCV cannot tell whether volume comes from exchange futures, spot index, CFD or consolidated sources, or if timestamps mark starts/closes. Verify source before live trading.
- Red/green results are tested on exact historical candle *bodies* and do not imply what the next candle will do or permit an entry at its opening after observing its closing body.
- The original file ends August 1, 2026 UTC. Test August–October 2026 or later separately before acting.
- Because scanning many clock slots and hundreds of sequences leads to false discoveries, all mined trading tendencies are exploratory. No result is a trading recommendation or post-cost backtest.

## Files
- `btc_futures_15m_ohlcv.csv`: aggregated historical 15m OHLCV, UTC labels.
- `btc_15m_weekday_time_scan.csv`: all 672 weekday × 15-minute clock slots with rates, relative range, relative volume and chronological splits.
- `btc_15m_clock_summary.csv`: 96 pooled weekday / weekend / all-day clock slots with chronological splits.
- `btc_15m_empirical_color_sequences.csv`: every red/green 1–3 candle sequence with following price direction.
- `btc_15m_discovered_candle_shapes.csv`: seven data-learned single-candle shape types.
- `btc_15m_discovered_shape_sequences.csv`: all sufficiently observed 2–4 shape sequences with train/validation/test behaviors.
- `analyze_btc_15m.py`: reproducible analysis source.