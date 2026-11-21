# Stage26: Robust BTCUSD 4H Donchian + 1H EMA20 research

**Confirmed run:** [44908493237](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44908493237), success on Nov 21, 2026.

**Decision:** The **2025-only after-cost portfolio selector retained the existing 70/30**. Both new standalone variants are research improvements (especially under extra adverse execution cost); neither currently justifies replacing the portfolio. The user-facing goal of a reliable positive **22/22 months is NOT achieved**.

## Reproduction and validation

- 989,280 historical BTCUSD 1-minute candles across 23 monthly source files (January 2025 through partial November 2026); zero missing minutes in current archive.
- Results evaluated January 2025–October 2026, 22 IST calendar months.
- **1,008** parameter variants: 288 four-hour swing and 720 one-hour EMA20 pullback.
- Higher-timeframe entries use complete source bars and **next 1-minute open**. 1-minute stops win ties against same-bar targets.
- Baseline costs: Delta India-style BTC futures **0.05% taker each side, plus GST 18% on fees, plus 5 BTC points of slippage per side**. All variants also tested with **+5 bps extra adverse slippage per side**. Four-hour swing cost surcharge applied to the exact entry/exit/mark fills; one-hour modeled cost surcharge approximated from entry price on both sides.
- 4H swing extended simulator exactly reproduced original Stage17 monthly account NAV (max absolute equity delta **0.0**). 1H original selected Stage25 config reproduced **+7.6640%** and **−1.0343%** under +5bps stress.
- Strategy selection used **2025 only**, requiring positive base-return after 5bps stress and 20 (swing) / 30 (hourly) training trades. Preferred solutions were profitable in both halves of 2025.
- **2026 is historically researched already**, not a pristine out-of-sample holdout. 2026 observations must not be used to optimize subsequent historical configurations.

## Independent optimized strategies

| Item | Stage25 configuration | Stage26 configuration |
| --- | --- | --- |
| **4H Donchian** | Channel 24, EMA50, stop 2×ATR, trail 2.5×ATR, hold 14 days | **Channel 20, EMA50, stop 2.5×ATR, trail 2.5×ATR, hold 7 days** |
| Base 22-month net return | +9.1062% | **+11.9380%** |
| New config +5bps additional slippage | Not previously computed with correct MTM fees | **+9.5234%** |
| 2025 return +5bps | n/a | +4.2893% |
| 2026 Jan–Oct return +5bps | n/a | +5.0188% |
| 22-month positive/loss/flat | 9/13/0 previous | **10/12/0** |
| **1H EMA20 LONG** | 4H efficiency>=0.30, 5R target, 8h hold | **4H efficiency>=0.25, 4H ADX>=20, stop risk>=500 BTC points, 5R, 8h hold** |
| Base 22-month net return | +7.6640% | +6.1754% |
| Additional +5bps/side | **−1.0343%** | **+2.3654%** |
| 2025 return +5bps | +0.3394% | +2.2168% |
| 2026 Jan–Oct return +5bps | −1.3691% | +0.1454% |
| 22-month positive/loss/flat | 12/10/0 | **13/7/2** |

Neither strategy satisfies an all-positive monthly consistency goal. Do not combine allocations based on already known losing months.

## Simulated monthly blends, original Stage18 70/30 unchanged

Every portfolio uses **fixed monthly weights** for the entire period, not dynamic month labels or retrospectively toggled strategies. These remain *synthetic monthly NAV blends*, not joint live execution.

| Portfolio | Without extra cost | Positive months | All sleeves +5bps stress | Positive months under stress |
| --- | ---: | ---: | ---: | ---: |
| Existing 70% core / 30% Donchian | **+14.4381%** | 19 / 22 | +8.1028% | 16 / 22 |
| 95% original 70/30 + 5% new 1H | +14.027% | **20 / 22** | +7.824% | 17 / 22 |
| 90% original 70/30 + 10% new 1H | +13.615% | **20 / 22** | +7.544% | **18 / 22** |
| 90% original 70/30 + 5% new 4H + 5% new 1H | +13.946% | **20 / 22** | +7.936% | 17 / 22 |

**2025-only portfolio selection after 5bps extra execution costs:** Retain the original 70/30, as it has the best risk/drawdown-adjusted 2025 return of the fixed weights screened. Note: its +5bps future-return changes are not a complete account-level 10-strategy cost model.

## Caveats and decisions

- **Prioritize independent research** on 4H channel20 EMA50, stop2.5×ATR / trail2.5×ATR / 7-day max, and 1H EMA20 long with 500-point minimum risk, 4H efficiency>=.25 and ADX>=20. Both need a truly new forward monitoring interval and margin-aware simulation.
- **Reject 5M inverted compression**: Still negative after 720 Stage25 variants.
- The short-only 1H compression candidate is weak (+1.41% base across 22m and negative when stressed at +5bps) and not advanced.
- Do NOT deploy or modify live trading; preserve earlier research on separate branches.
- **Return, win-month and cost robustness are different goals:** 4H improved total return, 1H improved high-cost robustness, but neither improves the frozen 70/30 on both total return and monthly consistency.
- Real Delta margin, bid/ask depth, funding, tick/contract rounding, broker order routing and liquidation omitted.
- All research has already examined the 2025–2026 dates and may overfit. A new out-of-sample data collection and precommitted paper-test plan are essential before considering real funds.

## Code and artifacts

Replay with:

\`\`\`bash
PYTHONPATH=scripts python scripts/research_stage26_robust_swing_hourly_20261121.py
\`\`\`

GitHub artifact **btc-stage26-aftercost-swing-hourly-20261121** includes all 1,008 backtested configurations, paired baseline/+5bps monthly series, two standalone selection ledgers, portfolio comparisons and selection parameters.
