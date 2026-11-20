# Stage 18/20 BTC — trailing stop and trailing distance (actual 1-minute core trades)

**Verified run:** [44648534792](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44648534792) — GitHub Actions completed SUCCESS. Source commit `a51e1a6dd975365abd3486d0949e5b51a1f03759`. Job artifacts include `analysis/stage18_stage20_trailing_distance_20261120/all_trailing_stop_distance_results.csv`, `monthly_22mo_account_return_comparison.csv`, and `all_trailing_trade_ledgers.csv.gz`.

## Strategy-change experiment

Real archived Stage14 candidate entries replayed on Delta India historical BTC 1m OHLC, retaining Stage15 originally defined weekly -3R loss gate, 1H quiet-volume filter and initial structural stop. Tested **19** fixed-stop, immediate trailing-stop, trailing-distance and 5R/8R/10R profit-cap cases, with 240m/480m time caps. Trailing stops update only on fully **completed** 1m bars and apply on the next 1m; stop-first if competing TP/SL touched in same minute; gaps stop at worse available open.

At 2025 model-selection time with extra +2bps adverse slippage on EACH order side, best candidate for BOTH portfolios: `distance_800pt_after3R` — wait for +3 initial-risk units favorable movement, then trail the favorable-price peak by 800 **BTCUSD index price points**, keep original structural stop until tightened, maximum TP +10R, maximum holding 240m. This is a stop touched by actual 1m high/low, not a candle-close exit. Best 2025 doesn't imply best 2026.

**Crucial correction:** Training penalty is computed from **BTC 2025 monthly drawdown ONLY**; 2026 equity is excluded from any selection metric. Prior GitHub run 44648373802 is superseded by corrected run 44648534792.

## Original vs fixed TP vs 800-point trailing

Model returns are account NAV return estimates from a freshly replayed Stage15 main component blended with **archived** Stage17 and Stage19 monthly NAVs, NOT a fully native simultaneous-sleeve account execution.

| BTC historical 1-Jan-2025 through 31-Oct-2026 IST | Original 3R | Fixed 5R / no trailer | +3R activates 800pt trail; TP10R |
|---|---:|---:|---:|
| Stage18 return 2025 | +4.7356% | +6.7313% | **+7.5547%** |
| Stage18 return 2026 Jan–Oct | +5.0832% | **+4.9517%** | +3.9464% |
| Stage18 compounded 22mo | +10.0596% | **+12.0163%** | +11.7993% |
| Stage18 positive/negative/flat months | 15/4/3 | 15/4/3 | 15/4/3 |
| Stage20 return 2025 | +3.4129% | +5.1873% | **+5.9186%** |
| Stage20 return 2026 Jan–Oct | **+4.3056%** | +4.1875% | +3.2849% |
| Stage20 compounded 22mo | +7.8655% | **+9.5921%** | +9.3980% |
| Stage20 positive/negative/flat months | 18/3/1 | 18/3/1 | 18/3/1 |
| Stage15 original core trade PF, net R | 1.9620 | **2.1507** | 2.1304 |
| Core trades (complete Jan2025–Oct2026) | 64 | 64 | 64 |

Cost sensitivity: the original model includes 0.05% taker/side and GST 18% plus adverse 5 BTC points/side. Additional +2bp adverse order slippage EACH side: Stage18 fixed5R +9.5197%, 800-trailing +9.3079%; Stage20 fixed5R +7.3882%, 800-trailing +7.1983%. Additional +5bp: Stage18 fixed5R +5.8791%, 800-trailing +5.6749%; Stage20 fixed5R +4.1663%, 800-trailing +3.9826%.

## Decision

**A 3R-activated 800-BTC-point trailing distance is a promising 2025-only in-sample variant, but did NOT beat fixed 5R in the chronologically later, previously exposed 2026 or over 22 months. Do not promote it as a validated improvement.**

Immediate trailing stops and many narrower/fixed/R-based trailing distances were tested; none beat the 800pt variant on the predeclared BTC-2025 stressed selection score. Full case-by-case BTC 2025, BTC 2026, PF, 22-month months and costs are in workflow artifact CSV.

### Audit limits (still material)

- Only the Stage15 trading component is replayed on native 1m bars; Stage17 and Stage19 contributions use old monthly returns and do NOT have integrated simultaneous fills or rebalancing/margin.
- The 2025 training period and 2026 comparison have been repeatedly examined in other research: no pristine out-of-sample.
- Historical source contains known missing data in the earliest IST hours of Jan 2025 and missing UTC 31 Oct 2026.
- Core NAV is allocated to *trade exit month* and may differ from month-end mark to market for still-open trades; month-end portfolio drawdown omits intramonth peaks/troughs and potential liquidation.
- The native ETHUSD entry/exit improvement using these BTC-frozen trailing parameters has NOT been tested.
- No authenticated historical bid/ask quotes, funding history, margin, liquidations, contract rounding, dynamic maker/taker/Scalper Offer eligibility or tick-level order sequencing were replayed. Extra slippage is a stress assumption, not actual fill verification.
- Work stays on research branch, no main merge and no live execution.

To continue improving: prefer forward paper checks of frozen 5R and 800pt trailing side by side rather than more hindsight optimization; or build a full integrated 1m portfolio margin/execution engine to replace monthly blending.
