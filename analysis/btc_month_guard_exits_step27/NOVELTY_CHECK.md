# Step 27 — BTC monthly peak-profit protection × closed-bar exit combinations

**Novelty gate: PARTIAL OVERLAP, research-only.** Step26 tested 108 combinations of previous completed monthly peak equity, giveback, and INITIAL STOP width. It found **+28.332018% historical net, +0.779650% January 2026, 21/22 positive months, 2.617670% closed max DD** using a 0.20% stop cap when previous month's within-month peak had reached +1.00% and the prior completed account equity fell 0.75 percentage points from that peak. This step tests whether changing only the **already-supported causal early-exit policy when that general high-water risk guard is active** can improve the 22-month after-fee net and January 2026 without sacrificing other months. Similar early exits were studied elsewhere: no new signal family and the same old data are in-sample/mined.

## Immutable history and controls
- BTCUSD futures 1m historical Delta India OHLCV Jan2025–Oct2026. Exactly one 1× full-account-notional entry per complete IST Mon–Fri **477 weekdays (260 in 2025, 217 Jan–Oct2026)**, no weekends, skips, zero positions, position-sizing fixes, extra positions, or leverage.
- Keep frozen Step25 `ridge120_fallback__tight60_050_both_cap040__baseline__positive_mtd_no_extra_exit`: causal Ridge trained on previous completed 120 fallback trade counterfactuals (min40, threshold0.30) controls only fallback LONG/SHORT; event 18/19/20 IST first prior5m RVOL>=1.5×mean20; otherwise mandatory 21h fallback. Every order fills on 1m OPEN. Entry/side unchanged in Step27.
- Original Step20/25 preentry initial SL caps retained: fallback 60m trend-alignment>=0.15% cap0.40%; fallback counter5m>=0.05% cap0.25%; either event/fallback prior60m range <=0.50% cap0.40%. Initial SL otherwise event0.50%; fallback 0.50%/0.75% by RVOL. TP3% gross, event lock+0.10% after +0.25% favorable (from next bar), fallback trail after+0.35% favorable with 0.20% distance from next bar,30m max. Conservative stop-first same-minute collision/gap-aware, prior 1m closed-bar early signal exits NEXT OPEN.
- Step25 monthly baseline event exit: if previous complete within-month net<=0, adverse close<=−0.08% after 10 completed minutes next OPEN; otherwise no extra. Fallback if previous MTD<=+0.25%, positive close>=+0.10% after20 minutes next OPEN, otherwise no extra. All monthly equity state updates only AFTER prior actual position fully closed, resets IST calendar month.
- Verified Step26 control: +28.332018% modeled net under assumed preactivated Scalper closing-fee waiver + entry taker/GST and 5 BTCUSD quote price-point adverse slip EACH leg, Jan2026 +0.779650%, **21/22 winning months**, 285/477 winning days, 2.617670% max closed DD; 2025+11.744153%, Jan–Oct2026+14.844504%, standard fees −3.137181%. Only losing month Jan2025 −1.047101%. Earlier Step25 full net+28.134367% and Jan2026+0.087465% for comparison.
- Both fees: standard0.05% taker on each side plus GST18% vs hypothetical preactivated regular <=30m Delta India Scalper closing fee waiver; adverse 5 BTCUSD price points per side. Reprice SAME trade side+stop+exit on both fees, optimizing ONLY assumed-offer 2025. Historical fee offer activation, orderbook fills, funding, spread, latency, liquidation and intraminute tick paths unverified.

## Freeze 324-factor model grid before looking
Use exactly the following **four** month-peak/giveback triggers, assessed from previously CLOSED same-month trades at entry (triggered only when both conditions hold):
- Peak≥+1.00% AND past peak-to-current giveback≥0.75 percentage points (Step26 control).
- Peak≥+1.00% AND giveback≥0.50pp.
- Peak≥+1.50% AND giveback≥0.75pp.
- Peak≥+0.50% AND giveback≥0.75pp.

Apply only additional initial protective stop `min(frozen initial stop, 0.15% or 0.20% or 0.25%)`, and only for chosen scope **event**, **fallback**, **both** (3×3=9 stop/scope variants). Never widen stops. If guard condition doesn't hold, both existing stop and existing early exit policy stay exactly unchanged.

While the SAME guard fires for that day, one of **9** closed-bar early-exit choices (already supported in exact original stop-first 1m engine):
1. `baseline` — original frozen Step25 early-exit selection; does not override.
2. `guard_profit010_after5` — +0.10% signed prior-1m CLOSE after ≥5 completed minutes, next OPEN exit.
3. `guard_profit010_after10` — same after≥10.
4. `guard_profit010_after15` — same after≥15.
5. `guard_profit015_after15` — +0.15% signed CLOSE after≥15.
6. `guard_profit015_after20` — +0.15% signed CLOSE after≥20.
7. `guard_adverse008_after5` — adverse signed prior CLOSE≤−0.08% after≥5.
8. `guard_adverse008_after10` — same after≥10.
9. `guard_hard_timeout20` — original stop/TP/trailer with at most20m hold.
The extra policy REPLACES the original early-exit condition only on guarded trade, not in unguarded periods. Every exit remains stop-first and next-bar causal.

**4 guard trigger pairs×3 caps×3 scopes×9 extra exit conditions =324 predeclared candidates**, plus the verified Step26 frozen baseline. Compare under both standard and assumed Scalper =**650 score rows**. No other thresholds, January exceptions, altered model direction, trading-hour shifts, or after-the-fact tuning.

## Qualification and reporting
- For each candidate independently, actual month-to-date equity and peak are sequentially computed using ONLY prior completed ACTUAL candidate trades under assumed Scalper pricing. At each actual entry, choose whether guard fires, initial cap and early-exit ID; then realize that day's trade; update equity for NEXT weekday. Normal fee same decisions, no hindsight switch.
- Exact Step26 baseline regression +28.332018%, Jan2026+0.779650%, DD2.617670%, 21/22 and 477 trades required. The grid's trigger +1.00%, giveback0.75pp, both, cap0.20%, `baseline` exit must reproduce SAME original Step26 daily returns and all metrics (even though the grid contains it).
- Select **2025 ONLY** with >=11/12 positive 2025 months, >= +11.744153% compounded 2025 net, >=154 2025 winning days, <=2.617670% 2025 closed DD+1e−4 pp. Rank 2025 net highest, then more winning months, more win days, lower DD; if none strictly improve 2025, keep Step26 unchanged.
- Apply frozen selected policy to Jan–Oct2026 (already heavily research-exposed, NOT fresh out-of-sample). Overall improvement requires Jan2026>+0.779650%, total net>+28.332018%, **21/22 or more positive months, Jan–Oct2026 10/10 positive months, max DD<=2.617670%, all477 trades**. Report if January alone improves but other months or total net worsen.
- Separately report strongest *retrospective January2026* rule among grid retaining 21/22, DD≤2.617670%, and net≥+28.332018%, if any, but label **HINDSIGHT ONLY / never promote due to 2026 selection**. A full-history 22/22 result selected after viewing 2026 must also be labeled hindsight only. Never claim independently validated edge.
- Outputs: full all 324 model grid with both fees, 22 compounded month outcomes for all, separate 477-trade ledgers and 22 monthly CSV for Step26, 2025-selected, and best retrospectively higher-Jan rule; 2025/2026 separate return, daily win counts, worst month/day, DD and standard fee sensitivity. Audit reproducible exact parity. No merges into main and no real trade deployment.

## Primary weakness
All 2025–2026 candles have been researched many times, including January 2026, and previous Stage25/26 baselines were retrospectively selected. Even a clean-looking 22/22 would likely overstate future reliability. Scalper offer entitlement and real fill costs unverified; normal taker costs have been unprofitable.
