# BTC futures: empirical 30-minute candle discovery

## Scope, data and units

- Source: `underlying_bars(1).csv`, continuous 5-minute BTC futures OHLCV data from 2025-12-31 11:35 UTC through 2026-08-01 00:00 UTC (61,206 rows). No missing timestamps, duplicate timestamps or missing OHLCV values in the source.
- Aggregation: right-closed, right-labelled UTC 30-minute bins: `open = first`, `high = max`, `low = min`, `close = last`, `volume = sum` over exactly six consecutive 5-minute observations. There are **10,201** complete 30-minute bars in the entire source; **10,176** for the January 1–July 31 2026 UTC discovery window. The first bin in the export includes data from 2025-12-31; the discovery period begins January 1.
- Time-zone analysis: convert the UTC **aggregated close label** to `America/New_York` (actual EDT/EST daylight saving transitions). Use both weekday and exact local 30-minute time. Times could be off by one original 5-minute bar if the raw timestamp refers to the opening time rather than close; verify before any live use.
- Candle color: red if `close < open`, green if `close > open`, flat otherwise. **17** flat bars in the Jan–July window, **6** zero-range / zero-volume bars. The comparison counts treat flat as neither red nor green.
- Range multiplier = (current high−low)/open, divided by median of the same measure for the **prior four completed 30-minute bars** (previous two hours). Volume multiplier similarly uses the prior four completed 30-minute bars.
- Chronological descriptive checks: Jan–Apr / May / Jun–Jul. These are replication checks, **not an untouched final test**, because discoveries were ranked using all three periods. Dataset-mining and multiple comparisons still matter.

## Most repeatable volatility discoveries

| 30m candle close label, NY time | n | Median range multiplier | Median volume multiplier | Range >2× prior norm | Jan–Apr / May / Jun–Jul median range |
|---|---:|---:|---:|---:|---|
| **Sunday 18:30 ET** | 30 | **2.69×** | 2.51× | **20/30 = 66.7%** | 2.52× / 2.71× / 3.37× |
| **Weekdays 10:00 ET** | 152 | **2.16×** | 2.56× | **85/152 = 55.9%** | 2.31× / 1.75× / 1.97× |
| Weekdays 17:00 ET (quiet) | 152 | **0.75×** | 0.45× | 3/152 = 2.0% | 0.67× / 0.87× / 0.82× |

Sunday 18:30 ET spike above 2×: **10/17 Jan–Apr**, **4/5 May**, **6/8 Jun–Jul**. For Sunday 18:30, red candles occurred 18/30 times (60%) but fell to only 4/8 (50%) in Jun–Jul, so the observed edge is in range and volume **not in direction**. The strong size pattern overlaps the known Sunday evening US market period; no causal inference can be made from OHLCV alone.

The weekday 10:00 candle was red only 53.9%, despite the range and volume surge. It contains the 09:30–10:00 US morning interval *assuming source labels mark 5-minute closes*.

## A potentially useful timing predictor (independent of future candle color)

At **weekday 09:30 ET close label**, a next-hour absolute BTC closing-price move of at least **0.5%** occurred **75/152** times (**49.3%**); Jan–Apr 48/86 (**55.8%**), May 6/21 (**28.6%**), Jun–Jul 21/45 (**46.7%**). Across every 30-minute observation, the 60-minute-move baseline was **18.4%**; Jun–Jul baseline was **18.1%**. This predicts large *size*, not upward or downward direction. The 09:30 → 10:30 window includes the US market-opening period. Such market-time selection can still lose money due to direction, spread, fills, and fees.

At **Sunday 18:00 ET close label**, 18/30 (**60%**) of the subsequent 60-minute net BTC closes moved >=0.5% up or down: 11/17 Jan–Apr, 3/5 May and 4/8 Jun–Jul. This is another **candidate timing signal** ahead of the Sunday 18:30 spike; the Jun–Jul sample (8 Sundays) is small.

## The requested red/green color search

There are **336** day-of-week × 30-minute-clock combinations. Of them **12** had naive direction p-values below 0.05, but **none** passed Benjamini–Hochberg FDR 5% when tested against their own weekday background red rates. By comparison, 13 day/time slots had FDR-corrected elevated >2×-range frequencies. These are empirical, exploratory tests (time observations and volatility regimes are not perfectly independent).

| Candidate | Red / green frequency | Jan–Apr / May / Jun–Jul | Interpretation |
|---|---|---|---|
| Weekday 08:30 red | **52.6% red**, n=152 | 48.8% / 38.1% / 66.7% red | Not stable enough for a blanket 08:30 short |
| Thursday 10:30 red | **23/31 = 74.2% red** | 77.8% / 75.0% / 66.7% red | Uncorrected pattern, but FDR q=1.000; cannot establish edge |
| Saturday 17:00 green | **24/30 = 80.0% green** | 76.5% / 80.0% / 87.5% green | Exploratory, adjusted q=0.472; missing/flat candles negligible here |

## Automatically discovered candle shape sequences

No standard named candlestick-pattern detector was applied. Each 30-minute candle was characterized using signed body-to-range fraction, upper and lower wick proportions, log(range divided by earlier two-hour median), and log(volume divided by earlier two-hour median). A 7-cluster K-means model fit on Jan–Apr data classified all candles into seven empirical shape groups. See `btc_30m_discovered_shapes.csv` for shape meanings. Only sequences sufficiently frequent to analyze are reported; there are 49 two-candle shape combinations with at least 20 occurrences, 259 three-candle combinations with 20+ occurrences, and no four-candle combinations with at least 20 occurrences.

- **Shape 1 → Shape 1:** two consecutive unusually large, high-volume candles (no fixed color); n=286. The next 60-minute close differed by >=0.5% in 38.1% Jan–Apr (n=168), 18.4% May (n=38), 31.2% Jun–Jul (n=80), versus Jun–Jul baseline 18.1%. This is a plausible *volatility persistence* pattern; it does not establish a directional or incremental edge above a single large candle. Episodes may overlap.
- **Shape 4 → Shape 4:** two consecutive strongly green-bodied candles of near-typical size; n=215. Next 30-minute bar red in 60.9% Jan–Apr, 56.2% May, 54.4% Jun–Jul; the Jun–Jul lift over the overall red baseline was only ~3.6 percentage points, too small for a validated trading entry.

## Purely empirical color sequences (no named setups)

From all 1–5-bar sequences of red and green candles:

- **GGG → next candle red:** 54.4% over n=1185; 54.0% Jan–Apr, 55.6% May, 54.6% Jun–Jul.
- **RRR → next candle green:** 55.0% over n=1171; 56.1% Jan–Apr, 54.8% May, 53.2% Jun–Jul.

This is a **modest mean-reversion tendency** in the subsequent half-hour. It can easily be outweighed by exchange fees and the magnitude of losing trades. Conditional rates do not imply positive expectancy.

## Local-time reading guide

Assuming raw timestamps mark 5-minute **closes**, the aggregated 30m close-labelled `10:00 ET` bar is the `09:30–10:00 ET` candle (NY market opening half-hour), and `18:30 ET` Sunday is the `18:00–18:30 ET` half-hour. If raw stamps mark the open instead, the window is shifted five minutes. The file alone cannot prove the timestamp convention.

For **EDT** (spring/summer), New York 10:00 ET = **19:30 IST**, 09:30 ET = **19:00 IST**; Sunday 18:30 ET = **Monday 04:00 IST**, Sunday 18:00 ET = **Monday 03:30 IST**. During **EST** add one hour to the IST equivalents. New York daylight saving is explicitly accounted for in the groupings.

## Statistical and trading limitations

1. The strongest differences are range and volume time-of-day seasonality, not reliable direction. Candlestick color does not include entry/exit spreads, funding, fees, slippage or price gaps.
2. Among 336 clock/day combinations and numerous shape sequences, some apparent patterns occur by chance. Multiple testing was controlled for simple color and range-spike scan, not fully for all sequential-pattern research.
3. Aggregations rely on the full continuous feed; although timestamp gaps were absent, 6 zero-range/volume 30m bars and one-bar open-vs-prior-close discrepancies should be audited against exchange documentation.
4. Spaced-trade, realistic execution, more recent August–October 2026 data, and an untouched forward-testing period are essential before treating any finding as an actionable strategy.

## Reproducibility and downloadable data

- `btc_futures_30m_ohlcv.csv`: all 10,201 aggregated 30-minute OHLCV bars; filter Jan–July for discovery.
- `btc_30m_weekday_time_scan.csv`: all 336 weekday/time combinations with period splits, raw counts, red-rate p-values, and Benjamini–Hochberg q-values.
- `btc_30m_clock_summary.csv`: 48 clock-times pooled by weekdays/weekends/all and chronological periods.
- `btc_30m_color_sequences.csv`: all 62 possible non-flat 1–5-bar color histories and outcomes.
- `btc_30m_discovered_shapes.csv`: seven training-derived empirical candle-shape groups.
- `btc_30m_discovered_shape_sequences.csv`: observed shape histories with a minimum of 20 instances and future outcomes.
- `analyze_btc_30m.py`: full reproducible analysis, including exact time-zone, sampling, and clustering rules.