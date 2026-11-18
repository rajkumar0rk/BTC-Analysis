# Stage14 — Finding monthly consistency from known-at-entry BTC market regime

## What was measured
Original Stage11 eight market-structure entry families and Stage13 two trend-pullback variants.
Each compared across 12 predeclared 4H/1H/previous-month regimes, 2R/3R
and 4h/8h maximum holds. Entries can occur at any time. Same structural stop.
1m conservative stop-first replay and standard fees/GST/slippage.

## Monthly consistency gate
>=9 active 2025 and >=8 active 2026; >=75% profitable active months each year; >=60/30/20 trades and net-positive 2025/H1/H2

Months with no trades are shown separately and cannot count as profitable.
2026 windows are research-exposed and NOT independent tests.

**Models passing the research gate: 0 / 28**

## 2025-selected leaders, and their actual 2026 behavior
| family   | regime   | target_R   | max_hold_min   | year2025_n   | profit_months_2025   | loss_months_2025   | net_2025   | year2026_n   | profit_months_2026   | loss_months_2026   | net_2026   |
|----------|----------|------------|----------------|--------------|----------------------|--------------------|------------|--------------|----------------------|--------------------|------------|

## Passing models
None passed the predeclared criteria.

## Monthly results for those 2025-selected leaders
No models with adequate 2025 history.

## Limitations
- Stage11 and Stage13 original entry criteria reused, no future information
- Previous-month regime values lag one calendar month, in Asia/Kolkata
- Higher-timeframe ADX and volume are from complete 4H/1H bars
- A no-trade month is not a winning month; sparse models excluded by sample gate
- Trade variants are standalone and overlap; never add net PnL across configurations
- All historical 2026 windows have already been used in research; no virgin holdout
- No bid/ask spread history, funding cashflows, order book impact, margin or liquidation
- 1m OHLC stop-first, gapped stops fill at worse open or stop; intraminute uncertainty
- Many tested conditions create multiple-testing/selection bias
- Net BTC price points, not risk-sized dollar account monthly return
- 2026-10-31 missing from source; 2026-11 through the 16th only
- Nothing establishes zero-loss months or future profitability

Scripts and full trade logs are saved. To establish forward profitability
freeze a single model and evaluate data acquired after this research.
