# Step29 — GENERAL losing-month recovery: BTCUSD fallback direction × protective stop × early exit

**Novelty gate: PARTIAL OVERLAP, conditional factorial on a distinct prior equity STATE.** Existing Steps 21, 24, 26–28 test initial stop caps and exits, including monthly-state cuts. Step29 specifically integrates **conditional rescue of the current-month account when previous completed weekdays have left it negative** with a pre-entry fallback direction change and protective cap / early closed-bar exit, while preserving Step28's **independent** previous-month-peak trailing guard. No January-identity-specific override or future candle access. This is hypothesis research with pronounced historical selection bias.

## Correct month and exact frozen benchmark
- **January 2025, NOT January 2026**, is the sole losing month of latest Step28 frozen strategy: **−1.047101% compounded** on 22 IST weekdays. Event trades 14 positions/9 winners/approximately **+0.631713% sum daily returns**. Mandatory fallback trades 8 positions/3 winners/**−1.672284% sum**. Four fallback positions near −0.47% account return. Prior completed month account equity **never reached a positive peak in Jan2025**, so original Step28 high-water trailing guard never activates. In contrast Jan2026 is **+0.910871918%**, ALREADY profitable. Hence no targeting Jan2026.
- Step28 **2025-selected** original: one full 1× account-notional BTCUSD futures trade every 477 complete IST Mon–Fri dates Jan 2 2025–Oct30 2026, **21/22 profitable months, +28.574051% hypothetical after fees, 281 profitable weekdays, max closed drawdown2.617670%, 2025+11.982383%, Jan–Oct2026+14.816320%, Jan2025−1.047101%**, historical normal fees negative. 2025 11/12, 2026 10/10. Replay that baseline identically before any results accepted.
- Fixed underlying entry: event first prior completed 5m relative volume >=1.5×20 previous completed5m volume at 18/19/20 IST, else mandatory21 IST fallback; event original Step11 direction, fallback frozen Step22 Ridge last120 previously fully settled fallback shadow returns, min40, threshold0.30. Candidate **only changes fallback direction when previously settled month net-loss state triggers**, not events or entry time. One FULL notional order/day regardless of signal confidence, 1× exposure and no weekends. Never change size/skip.
- Step28 risk: event SL0.50% original TP3%, profit lock starts when favorable>=+0.25% and lock +0.10%; fallback stop0.50/0.75% depending prior5m volume, trailing activates +0.35% with distance0.20%, TP3%, max30min. Step20 original caps when fallback side aligned with completed prior60m move>=0.15% cap0.40%; fallback counter prior5m>=0.05% cap0.25%; Step25 both entry types prior60m range<=0.50% cap0.40%. All preentry features re-evaluated against any proposed new side. Step28 high-water guard checks prior completed MONTH account peak>=+1.0% and previous day-end equity giveback>=0.75 percentage points; when active cap SL0.18%, event lock activation+0.30% lock+0.15%; fallback trail activation+0.35% distance0.15%; unguarded baseline as above. This remains ON unchanged. Every stop may only tighten, never widen.
- Step25 frozen month-dependent extra early close: event if prior MTD account net<=0 and signed closed 1m price<=−0.08% after≥10m, exit next1m OPEN; fallback if prior MTD account<=+0.25% and 1m signed close>=+0.10% after≥20m, exit next OPEN; otherwise no extra. Step28 changed trailing activation only when peak guard active. Preserve stop-first if 1m stop/TP collision, gaps adverse, trailing/lock NEXT minute. No future data.
- Costs: full 1× account-notional 477 daily positions. Hypothetical previously opted-in Delta regular Scalper Offer with no exit fee for eligible positions <=30m; entry taker0.05%+GST18%; each leg 5 BTCUSD quote-point adverse slippage. ALSO standard taker fees each side0.05%+GST18%, SAME selected actions (no cost-dependent trading policy), funding/market depth/slippage fill quality and historic actual offer activation unavailable. Normal fees historically lose money. No live deploy or master merge.

## PREDEFINED exact 1200 alternatives plus original Step28 control
At each day's entry, compute losing-month state exclusively from **previously COMPLETED trades in same IST calendar month**, reset previous MTD=0 and loss streak=0 on the first weekday, and choose one of 4 conditions:
1. `mtd_nonpositive`: preceding completed month account return <= 0% (including first weekday).
2. `mtd_below_minus025`: preceding completed month account return <= −0.25%.
3. `mtd_below_minus050`: preceding completed month account return <= −0.50%.
4. `loss_streak2`: at least 2 immediately prior completed weekday trade losses in this same month.

If and only if condition triggers, **fallback trade direction policy** from five options:
1. `keep_ridge`: original frozen Ridge side.
2. `fade_last5m`: opposite signed previous completed 5m return if abs>=0.05%, else Ridge.
3. `follow_last60m`: sign of previous completed 60m return if abs>=0.15%, else Ridge.
4. `fade_last60m`: opposite previous completed 60m return if abs>=0.15%, else Ridge.
5. `invert_high_rvol`: invert original Ridge side only if latest completed5m RVOL >=1.25×.
The existing event direction is NEVER changed. Recompute all preentry SL caps using new actual side, not inherited stale Ridge side.

Apply one extra **initial stop cap** `min(known frozen stops, cap)` only on triggered trade and chosen scope `fallback_only` or `both`, with caps **0.15%, 0.20%, 0.25%, 0.30%, 0.35%** (5). The peak guard's .18 cap still wins when active and tighter. Otherwise original stops unchanged. Never use month identity to decide.

Apply one extra early-close policy **to triggered FALLBACK ONLY**, replacing current fallback previous-month-conditional early exit, never change event extra early exit, chosen from six:
1. `base`: original prior-month exit policy.
2. `profit010_after5`: prior completed1m signed CLOSE profit>=+0.10% after 5m, exit next 1m OPEN.
3. `profit010_after10`: same after10m.
4. `adverse008_after5`: prior CLOSE loss<=−0.08% after5m, exit next open.
5. `adverse008_after10`: same after10m.
6. `timeout20`: hard timeout at20m rather than30m, stops still first.
All use original numba first-stop conservative 1m replay.

**4 states ×5 fallback side choices ×5 SL caps ×2 scope choices ×6 early-close variants=1,200 alternatives**, plus exact frozen Step28 baseline, **2,402 after-cost scenario scores**, 477 full positions for each. This is a preregistered finite grid; no new grid values added after examining outcomes. Model-generated conditions are causal; outcome selection itself highly history-fitted.

## Selection and proof claims
- Strict 2025-only selection: only choose configurations which reach **12/12 strictly profitable months 2025** (corrected January2025 target), 2025 net compounded >= Step28 +11.982383%, >=154 positive 2025 weekdays, 2025 maximum closed DD<=baseline2.617670%+1e−4 pp. Rank eligible by number positive months (all12), 2025 net, winning days, lowest DD; if no model meets all, freeze Step28 unchanged. Never select by inspecting Jan2026 or full-period ranking.
- Freeze 2025-only winner and audit all 217 2026 weekdays. A successful complete-month profile would be **22/22**, >=+28.574051% full-period net, <=2.617670% DD, unchanged 477 full-size positions and Jan–Oct2026 all positive. Caution: Jan2025 is in-sample 2025 training and 2026 is ALREADY exposed in research; even "22/22" would not be unbiased predictive success.
- Report separately the best full-period model with 22/22 positive months if any as **HINDSIGHT ONLY NOT SELECTED** unless it independently passed 2025-only selection; also best January2025 diagnostic model regardless of other losses, with clear costs/return/DD. If all fail, explicitly report best near-candidate and tradeoffs without saying monthly problem fixed.
- All 1200×2 metrics, 22 monthly compounded returns for the selected + top hindsight models, 477 daily ledgers for exact baseline + selected + one hindsight, normal cost sensitivities, 2025 and2026 net/months/win-days and changed fallback-direction counts, risk cap activated count and early-exit changes. Audit exact original per-day baseline parity and January daily decomposition.
- Regular fee waiver/actual fills not audited, multiple-comparison and retrospectively tuned history substantial, no guarantee or live use.
