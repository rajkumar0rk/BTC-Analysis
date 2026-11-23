# Step 18 — Pre-entry volatility/volume-conditioned protective stops (mandatory 477 BTC weekday trades)

**Novelty gate classification: PARTIAL OVERLAP.** This is not a distinct indicator or claim of predictive reliability. Earlier Steps 1/3/7 tested SL/exit values; Step5 changed SL based on pre-entry RVOL; Step16 tested first-N-trading-day fixed stop caps (0 models reached 22/22 positive months); Step17 tested first-N-day direction rules (0 models reached 22/22). **New differential:** keep the exact frozen Step11 ENTRY and Step13/15 monthly EXIT, but tighten only the INITIAL stop when a **current pre-entry adverse market structure / volatility condition** is true. Unlike Step16, no first-weekday or January-specific condition. Normal/low volume, high volume, short-term range, trend alignment and 60m range edge are known at entry, with no future candle or realized PnL leakage.

## Frozen historical baselines
- Step13 official 2025-selected daily system: **477/477 full IST Monday–Friday dates (2025-01-02 through 2026-10-30), 19/22 profitable months, +23.261256% compounded modeled account return, 290 profitable days, 3.008746% max closed DD**.
- Step15 A is after-the-fact all-history selection: **20/22 positive months, +24.648136% compounded, 292 profitable days, DD2.715507%**, 2025 11/12, 2026 Jan–Oct 9/10. Negative months Jan2025 −1.450594%, May2026 −0.007785%; standard taker net −5.919472%.
- Step15 B, also HINDSIGHT not 2025-selected: **21/22 positive months, +22.480405% net, 293 profitable days, DD2.715507%**, 2025 11/12, 2026 Jan–Oct 10/10. Only negative Jan2025 −1.450594%; standard taker net −7.556393%.
- Step16 tightening first 3 weekdays to 0.25% improved Jan2025 but reduced B to 20/22 due to Aug2026. Step17 general first-N-day direction rules did not qualify. Do NOT do month-specific selection using knowledge of Jan2025/May2026/Aug2026 losses.

## Inputs, execution, fees, trade count—unchanged
- Delta India BTCUSD futures full historical authentic 1m OHLCV Jan2025–Oct2026. All exact 477 IST weekdays; one FULL 1× account-notional position on each, never skip/size down or add trades; no weekends.
- Timestamp = first completed 5m RVOL>=1.5× prior 20 5m bars at 18,19,20 IST else mandatory 21 IST; direction selected only from **prior completed days** using Step11 online learner (Step13/15 identical). Entry at 1m OPEN, 5 BTCUSD quote price points adverse slippage each leg.
- Original initial SL = event 0.50% of mid price; fallback 0.50% or0.75% depending previous complete 5m RVOL>=1.25×. Events lock +0.10% when past completed 1m favorable excursion>=+0.25%, live next candle. Fallback trailing activation +0.35%, trailing distance0.20%, valid next candle. Max30m hold, TP3% gross, pessimistic 1m stop first if TP/stop same bar, gap-aware stops. Step13 and Step15 A/B distinct month-to-date early exits remain EXACTLY frozen and update equity only from already completed past trading days.
- Fees: standard taker 0.05% on each leg+18% GST, hypothetical previously activated Delta regular Scalper offer waives qualifying closing fee <=30m, 5 BTC price point adverse slip each leg. Reprice EXACT same selected 1m fills and exits under standard taker; never optimize on standard fee results. No funding, depth, bid/ask L1 or latency available; actual historical offer activation unverified.

## Fixed parameter grid, predeclared BEFORE backtest
At every original entry minute, compute from STRICTLY prior fully completed 1m candles: prior5m dollar-independent return, prior60m and 240m return, last5m volume / mean prior 20 nonoverlapping 5m volumes, prior60m high-low range / price and position of last completed CLOSE in prior60m high-low. All use [entry_i−N, entry_i) only. Calculate fixed risk masks:

1. `low_rvol5`: completed 5m volume ratio <= **0.65** or **0.90**.
2. `high_rvol5`: ratio >= **1.25** or **1.75**.
3. `wide_range60`: previous completed 60m high-low range fraction >= **0.50%** or **0.90%**.
4. `tight_range60`: range fraction <= **0.30%** or **0.50%**.
5. `against60`: entry direction opposes prior60m price return by >= **0.15%** or **0.30%**.
6. `with60`: entry direction agrees with prior60m return by >= **0.15%** or **0.30%**.
7. `big_abs5`: |prior5m return| >= **0.10%** or **0.20%**.
8. `counter5`: entry direction opposes prior5m signed return by >= **0.05%** or **0.15%**.
9. `edge_against`: prior60m close location in upper **20%** or **10%** of range with entry SHORT, or in lower 20%/10% with entry LONG.

Apply risk-triggered stop cap to **fallback trades only** or **both event and fallback** (two scopes). Cap original initial SL to min(original SL, **0.15%, 0.20%, 0.25%, 0.30%, or 0.40%**) (five cap candidates). NEVER widen stop or change original trailing/TP/fixed time/early exit recipe.

**9 ×2 thresholds ×2 scopes ×5 stop caps =180 unique risk masks; across each of the frozen Step13, A and B baseline families = 540 historical tests plus 3 unchanged exact family baselines; both fee models =1086 reported rows.** Candidate must always have 477 trades, no skipped date and baseline parity to earlier reports.

## Frozen selection / recheck
- Within each family rank candidates from **2025 data ONLY**. For Step13, candidate must reach >=11 of the full 12 2025 months profitable, AND 2025 net >= original Step13 +9.587865%, 2025 positive weekdays >=157, and 2025 max closed DD <=3.00875%. For hindsight family A/B, require >=12/12 positive 2025 months, 2025 net no lower than family original (+10.073418% for A, +7.993545% for B), 2025 winning weekdays >=family (155 A, 154 B), DD no higher than original 2.71551%. Rank eligible by 2025 positive months, net profit, positive weekdays, lower DD. If no qualifier, return ORIGINAL family, not the best retrospective 2026 version.
- Apply that frozen candidate unchanged to Jan–Oct2026. This is a **research-exposed historical recheck**, not true independent OOS because many past iterations have examined 2026. For improvement require >=historical family baseline total positive months, >= baseline total net, <= baseline DD, and no degradation of 2026 monthly profitability. Report EXACT 22 monthly results, 2025/2026, 477-day ledger, worst day/month and standard-fee sensitivity.
- Separately count all-history **22/22 hindsight** variants (if any) but label them IN-SAMPLE, do not deploy/promote based on total period selection. No reoptimization after 2026. Nov2–20 2026 already researched and not a pristine test. A/B base selection also used 2026 hindsight.
- Extensive multiple comparison risk and unresolved real trading fee offer mean 22/22 backtested months, if any, could be random historical fit rather than future guarantee.

**No master merge or demo/live deployment.** Research-only branch.
