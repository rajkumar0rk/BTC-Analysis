# Step 28 — precommitted month-high-water guard × favorable-excursion trailing combinations

**Novelty gate: PARTIAL OVERLAP (stop/exit research), not a new entry signal.** Step26 precommitted general month-high-water initial stop cap; Step27 tested 324 closed-bar early exits and showed that the best 2025-selected exit variation did not improve 2026 or total net. Step28 instead changes ONLY the future trailing-stop activation/lock on **already triggered previous-completed-month drawdown days**, preserving the exact Step25 Ridge daily entries and Step26 extra risk cap. Earlier static exit/trailing experiments exist; this is a conditional combination, not a novel trading signal. Heavy 2025/2026 prior research means even a high backtest score is overfit-prone.

## Frozen controls and data
- BTCUSD Delta India complete 1m OHLCV Jan2025–Oct2026; 477 complete IST Mon–Fri dates exactly, 260 2025 and217 Jan–Oct2026. One full account-notional 1× BTCUSD futures trade EVERY weekday, no skipped/zero days, weekends, leverage adjustments, or additional orders.
- Step25 `ridge120_fallback__tight60_050_both_cap040__baseline__positive_mtd_no_extra_exit` original direction/time frozen (18/19/20 IST volume-triggered event else mandatory21h fallback), Ridge uses only prior complete fallback trade outcomes and 1m completed-bar features (last120, minimum40, confidence0.30). Event stop0.50%, lock+0.10% when previous completed favorable excursion reaches+0.25% (live NEXT minute); fallback initial SL0.50/0.75% RVOL-dependent, trailing activates+0.35% favorable and distance0.20%; max30m and TP3% gross, stop first within one-minute bar on collisions, gap-aware. Prior extra stop caps: fallback 60m trend alignment>=0.15% cap0.40%, fallback counter last5m>=0.05% cap0.25%, both types when preentry60m range<=0.50% cap0.40%. Never widen any stop. Original Step25 early monthly exits identical: prior MTD<=0 event adverse close−0.08% after10m next OPEN; fallback prior MTD<=+0.25% profit close +0.1% after20m next OPEN; no fallback extra exit on >=+1% MTD. All price/volume indicators from completed prior candles only.
- Step26 **2025-selected** control: when PREVIOUS WITHIN-MONTH REALIZED ACCOUNT equity had already peaked >=+1.0%, and its previous completed-trade equity declined >=0.75 percentage points from peak, cap current initial SL to0.20% on both event/fallback (retain tighter existing stop). **+28.332018% historical modeled net**, Jan2026 +0.779650%, profitable months 21/22 (2025 11/12, 2026 10/10), 285/477 winning weekdays, closed DD2.617670%, standard taker fee net −3.137181%. January2025 −1.047101% worst month. Freeze this as official prior 2025-selected strategy.
- Cost price: 5 BTCUSD adverse quote points each leg, taker0.05% entry+18% GST, hypothetical **previously activated** Delta regular Scalper Offer closing fee waiver for qualifying <=30-minute positions; normal taker scenario charges0.05% each side +GST18%. Real historical offer opt-in, bid/ask spreads, live fills/latency, funding, tick-order and margin/liquidation unverified. Same selected trades/exits repriced normal fee scenario, never separately reoptimized.

## EXACT 180 alternatives plus unchanged Step26 control
Monthly guard trigger (both prior PRE-COMPLETE trades peak and giveback, checked at entry from only earlier completed SAME IST month trades):
1. peak≥+1.00% from month start, giveback≥0.75 percentage points (original Step26).
2. peak≥+1.00%, giveback≥0.50pp.
3. peak≥+1.50%, giveback≥0.75pp.
When triggered, initial SL capped by min(original, one of **0.18%, 0.20%, 0.25%**) on current trade, no sizing change.

Also ONLY when triggered, set favorable-excursion stop parameters *before entering*, preserving stop-first 1m and next-bar activation:
EVENT lock modes:
- E0 original event activation+0.25% locks+0.10% at/after next minute;
- E1 event activation+0.20%, locks+0.10%;
- E2 event activation+0.15%, locks+0.05%;
- E3 event activation+0.30%, locks+0.15%.
FALLBACK trail modes:
- F0 original activation+0.35%, trail distance0.20%;
- F1 activation+0.25%, distance0.15%;
- F2 activation+0.25%, distance0.20%;
- F3 activation+0.35%, distance0.15%;
- F4 activation+0.45%, distance0.25%.
These settings apply only to guarded trades of their matching type and NEVER change the original 30m max, TP3%, early close signal, entry time, direction or position size. They may ratchet profits earlier or later and could cause poorer results—measure, do not assume improvement.

**3 triggers×3 SL caps×4 event lock×5 fallback trail =180 candidates** plus Step26 original control; **362 fee/scenario results**. The frozen original setting (1.0 peak, 0.75pp giveback, SL cap0.20, E0,F0) must reproduce Step26 exact per-trade PnL within tolerance; baseline original (no monthly guard) Step25 remains +28.134367% for context.

## Selection and honest audit
- Select using **2025 ONLY**: at least 11/12 profitable calendar months, 2025 net return≥Step26 +11.744153%, at least154 positive 2025 weekdays, 2025 max closed DD<=2.617670%+1e−4 percentage points. Rank qualifying by 2025 compounded net, 2025 win months, 2025 winners, lower DD; if none qualify retain original Step26.
- Then show Jan2026 and 2026 results from frozen settings, but this is NOT independent OOS because all historical data and prior family were heavily researched. Promotion criteria for the all-history profile: January2026 >+0.779650%, total net >+28.332018%, 21/22 positive months maintained including 2026 10/10 and max DD <=2.617670%, all477 full size. If only some improve, describe tradeoff, do not promote.
- Separately report maximum January2026 among variants maintaining net≥+28.332018%, DD<=2.617670%, 21/22 and 2026 10/10 as **retrospective diagnostic only**. Even if better, it is NOT a forward proven strategy. All 22-month tables for all alternatives and both fee models, complete477 daily report for original, 2025-selected and highest January hindsight, full net/DD and standard fee.
- Do not merge main, do not deploy live or guarantee future profit. A result selected from years examined repeatedly is selection-biased. Historical regular Scalper fee waiver is an assumption not confirmed.
