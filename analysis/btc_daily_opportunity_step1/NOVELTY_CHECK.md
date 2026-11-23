# Step 1 of 5 — BTCUSD daily opportunity map (pre-run novelty gate)

Decision: **PARTIAL OVERLAP — approved differential, diagnostic only**.

## Why this study, rather than another indicator backtest?
The user wants >=+0.2% **NET ACCOUNT** profit per IST weekday, not just a daily BTC high-low range above 1%. Before attempting trading signals, distinguish what the price path *made possible* (with perfect hindsight) from what could have been predicted and executed.

## Closest prior work
- scripts/research_every_candle_200.py, analysis/institutional_discovery_stage6_every_candle_200/: evaluates first passage to *fixed BTC price-point* targets at every minute, including stop rules; not a full daily high/low map for fixed hour-of-day anchors and dynamic percentage price/cost budgets.
- analysis/institutional_discovery_stage7_time_volume/RESEARCH_REPORT.md: exhaustive 1m 200-point probabilities by time/volume/volatility regime, not the user's 0.2% **net account** criterion with 1x notional and side-specific 30-minute offer costs.
- scripts/research_daily_200_500_points.py, analysis/delta_points_200_500/: fixed point targets, NY clock signals, selected entry patterns and stops, not a no-direction ex-post percent-opportunity study.
- scripts/research_one_trade_every_day_200.py, analysis/one_daily_trade_200_points/: mandatory daily NY trade with fixed-dollar targets, unlike this descriptive non-trading analysis.
- scripts/research_monthly_10pct_stage19.py and latest research/btc-compression-momentum-daily-2026 (5m compression / 15m context) test predictive models; they do **not** prove fixed-time percent opportunity is tradable.

## Pre-registered measurements — Step 1 ONLY
Data: authentic continuous data/delta_india/BTCUSD/1m/*.csv.gz from Jan 2025 through Oct 2026. Require gapless, unique, non-null 1m timestamps and OHLC validity. Exclude incomplete first IST day 2025-01-01 and partial/latest November. Analyze complete Monday–Friday IST days, 2025-01-02 to 2026-10-30; do not invent missing candles.

1. **Daily price movement** per full IST weekday: (max(high)-min(low))/open_at_00:00_IST, and open-close absolute return. Count days with daily range >=0.2%, 0.27%, 0.35%, 0.5%, 1%, 2%; report count, median, 10th/90th percentiles separately for 2025 and 2026.
2. **Predefined fixed entry times:** Every IST clock hour 00:00, 01:00, ..., 23:00 (never select after seeing day's price path). Hypothetical fill at the 1-minute open at that exact hour. Future high/low available **after** entry for each side LONG/SHORT, as ex-post maximum favorable excursion, no stop and no predicted direction. Three horizons: next 30 minutes (candle minutes 0 through 29), next 120 minutes (only if full window remains in day), and to day end. Inspect gross directional threshold hits at 0.27%, 0.35%, 0.5%, and report either-direction (oracle) and side-specific results. Count no-move days. Both-side opportunities are NOT a trading win rate.
3. **Dynamic side-specific +0.2% net account price budget** at 100% notional, 1x leverage, 5 USD/BTC adverse slippage per side, 0.05% taker fee each side +18% GST on each charged fee. For a price hit inside the first 30 minutes, also compute a *hypothetical regular Scalper Offer* variant that waives only the closing fee, assuming prior opt-in; for later time use both taker-side fees. Compute exact entry-price-dependent long and short threshold prices with fee on exit price for the standard case. Offer is not guaranteed historically, and a candle high/low touch does not guarantee executable limit fills.
4. For 120m/EOD, scalper_or_standard_possible means: either the 30m move can cover +0.2% after offer opening cost, or a **later** move can cover +0.2% after double-sided standard cost; do not assume waiver for holds exceeding 30m. On every clock window compute standard_possible, offer_path_possible, gross long/short MFE, gross threshold reach flags, never automatic profits.
5. Count total valid fixed-time examples by hour and by year. Report 2025 and 2026 **separately**, no data mining used to build a trading signal. Rank hours by 2025 *oracle* 30m/120m opportunity rate, show 2026 rate beside it without promoting a tradable strategy. Save per-day and per-hour rows, grouped summaries and research caveats. Calendar weekdays with no moves still count.
6. No position sizing leverage, stop-loss, entry direction model, funding, liquidation, real order book, volatility entry filter, or return claims: these belong to Steps 2–5. All numbers in this step are **descriptive/ex-post opportunity bounds**, not a valid profitable backtest.

The old repository novelty document warns Oct 2026 was missing 1,440 UTC minutes, but current 1m/manifest.json regenerated Nov 23, 2026 reports **zero missing minutes** for all 22 months. The runner explicitly verifies continuity. The data period was studied in previous experiments; 2026 is **not pristine holdout**.
