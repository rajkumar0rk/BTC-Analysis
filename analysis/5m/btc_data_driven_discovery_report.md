# BTC Futures: Data-first Candle Discovery

**Input:** `underlying_bars(1).csv` — 61,206 continuous 5-minute OHLCV records, 2025-12-31 11:35 UTC through 2026-08-01 00:00 UTC. The main findings use Jan 1–Jul 31. Timestamps were interpreted as UTC and converted using `America/New_York` (real daylight-saving transitions). **The file does not tell us whether the timestamp is a bar open or bar close.** Confirm that against the source exchange before implementing alerts.

## What was searched (NOT a predefined breakout-strategy test)
- Every five-minute time-of-day slot on all seven weekdays: 7 × 288 = **2,016** distinct combinations, with separate January–April discovery, May intermediate, and June–July later samples.
- For each slot, percentage of green/red bodies, range relative to the preceding 24 *complete* candles (2 hours), percentage exceeding twice that preceding median, volume relative to its preceding median, and subsequent 30-/60-minute behavior.
- All 48 anchored half-hour time slots for candle direction on weekdays.
- Data-fitted 7-cluster single-candle shape descriptions (body sign/location, wick composition, relative candle range and volume). Scanned repeated 2-, 3-, 4-, and 5-candle sequences of those clusters. Censored sparse combinations and used later-month samples to see whether candidate behaviors persist. The shape research remains exploratory; many combinations were searched.

## Discovery A — Sunday 18:05 New York timestamp: unusually large range
- **28 of 30** Sunday observations had a five-minute high-low range over **2×** the preceding 24-bar median (16/17 in Jan–Apr, 5/5 in May, 7/8 in Jun–Jul).
- All-period median range multiplier: **4.34×** the preceding 24 completed bars; median 5-minute range about **46.9 basis points**, median relative volume about **5.35×**.
- At the same timestamp on Saturday, **11 of 30** candles exceeded 2×. The Sunday-versus-Saturday contrast is substantial (exploratory Fisher exact p≈3.1e-6).
- Following the Sunday 18:05-labeled candle, **23/30** next-hour paths had a **≥0.5%** excursion above or below its close at least once; this does **not** indicate direction or realizable profit.
- Candle bodies were **red only 17/30**, so there is no useful bearish direction rule.
- Plausible external mechanism: Sunday evening reopening of conventional US futures markets. The CSV alone cannot establish causation or bar-label convention.

## Discovery B — Weekdays 09:35 New York timestamp: persistent high range
- **109 of 152** five-minute bars had a range over **2×** the prior 24-bar median (Jan–Apr 67/86, May 13/21, Jun–Jul 29/45).
- Median range ratio: **2.58×** across the 152 weekdays; **2.71×**, **2.21×**, **2.35×** across the three time splits.
- **140/152** 09:35-labeled bars had a larger normalized range than the adjacent 09:30-labeled bar; paired one-sided Wilcoxon test p≈3.3e-24 across Jan–Jul.
- Red bodies: 78/152 ≈51.3%; **volatility, not up/down direction**, is consistent.
- A range burst five minutes after the normal US cash-market opening is consistent with *close-stamped* five-minute candles, but cannot prove that stamping convention.

## Discovery C — Weekdays 17:00 New York timestamp: recurring quiet patch
- Median range **0.66×** the preceding 24-bar median across 152 weekday observations (Jan–Apr 0.66×, May 0.60×, Jun–Jul 0.68×).
- Only **2/152** five-minute ranges exceeded 2× the preceding median.
- Candle red bodies ~50.0%; this is low activity rather than a directional edge.

## Discovery D — Repeated 3-candle shape, automatically identified
- Unsupervised cluster 1 is made of comparatively **large, high-volume bearish candles** (median 5-minute range ~24.6 bp in training, high-volume relative to recent candles).
- When this cluster appears **three times consecutively**, the probability of a future 60-minute intra-hour excursion of at least 0.5% was: **66.6%** (317 occurrences, Jan–Apr), **61.2%** (67 in May), **54.6%** (163 in Jun–Jul), versus unconditioned same-period rates **42.9%**, **21.3%**, **36.9%**.
- Requiring at least 12 bars (60 minutes) between signal occurrences left **104** Jun–Jul observations with a **53.8%** ≥0.5% excursion rate versus ~36.7% of hourly-spaced unconditioned observations.
- Importantly, the subsequent **30-minute direction was NOT stable**: 60.9% up in Jan–Apr, 62.7% up in May, but 45.4% up in Jun–Jul. Thus it is NOT a verified BUY/SHORT signal. The size relationship may partly reflect preexisting high volatility, and should be examined by volatility regime.
- A superficially promising run of three smaller green-cluster bars pointed lower afterward in the raw sample; the effect attenuated when clustered signals were spaced one hour apart. Not promoted as a trustworthy prediction.

## Example user hypothesis — is the weekday 8:30 candle mostly red?
- For the raw **08:30 ET timestamp**: 44.2% red Jan–Apr, 33.3% May, 46.7% Jun–Jul; about 43.8% across all available weekday observations.
- For the raw **08:35 ET timestamp** (the bar possibly covering 08:30–08:35 if bar-close stamped): 58.1%, 42.9%, 57.8% red; approximately 56.2% overall, also not a robust bearish prediction.

## Interpreting these as possible alert times in India
- Sunday **18:05 ET** is Monday **04:35 IST** during New York standard time and Monday **03:35 IST** during daylight time.
- Weekday **09:35 ET** is **20:05 IST** during New York standard time and **19:05 IST** during daylight time.
- Be sure to define whether alerts refer to the candle *starting* or *ending* at these times. The analysis uses the raw CSV timestamp without shifting the market-data bars.

## Statistical cautions
- These patterns were **mined from 2,016 time/weekday cells and many candle sequences**, so the most extreme-looking groups can be inflated by selection and multiple testing. Each pattern needs untouched future data for confirmation. Sunday n=30 is still a modest sample, though effect size is large and repeated in later periods.
- 24/7 BTC futures, trading costs, slippage, funding, exchange differences and contract size must be incorporated before calling any timed occurrence tradable.
- The label `hit a 0.5% excursion` checks **future high/low** during the following hour, not the 60-minute closing return. Both sides may be touched, and this is not the same as a profitable order.
- All timestamps represent the uploaded series, not necessarily the live tradable venue. Do not assume a CME-specific cause without verifying the origin of the BTC futures data.

## Associated exported data
- `btc_full_weekday_clock_scan.csv`: all 2,016 weekday × 5-minute clock observations; each with three chronological splits.
- `btc_discovery_unsupervised_candle_sequences.csv`: sequence outcomes for 2–5 automatically clustered candle shapes, showing discovery, intermediate, and later sample results.
- `btc_discovery_30m_clock.csv`: half-hour candle direction by chronological split.
- `btc_empirical_top_findings.csv`: concise metric snapshot of the strongest recurring tendencies.