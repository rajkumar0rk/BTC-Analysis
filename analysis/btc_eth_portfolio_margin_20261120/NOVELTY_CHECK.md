# Novelty gate — BTC/ETH portfolio margin, futures-only test (2026-11-20)

**Purpose:** compare the SAME BTC/ETH EMA20+Supertrend single-position futures strategy under Isolated, hypothetical Cross, and a Delta Portfolio Margin risk-scenario simulator. This is NOT a new strategy or optimized signal search.

Closest prior:
- `scripts/replay_btc_ema_st_fixed_10_margin.py` (baseline isolated fixed <=$10 100x margin)
- `scripts/replay_btc_ema_st_preliq_one_point.py` (isolated + pre-liquidation stop)
- `scripts/replay_eth_ema_st_preliq_one_point.py` (ETH isolated preliq)
- `scripts/replay_btc_eth_cross_margin_100x.py` (hypothetical full-account Cross).

**Methodological change only:** This replay sets the initial margin by Delta's Portfolio Margin stress risk, not by the 100x Isolated leverage setting. For a BTC portfolio notional below $100K, the publicly documented price-shock span is 1%; compute 27 regular underlying up/down shock × IV scenarios plus 2 extremes weighted 1/3. For one linear future, there is no IV exposure; risk is 1% notional. Futures floor is 0.5% notional; initial required `max(risk_margin, floor)`. Maintenance is `0.8*max(risk_margin,floor) - unrealized_PnL`. Modeled liquidation when wallet cash falls below this maintenance amount; equivalently wallet cash + UPNL <= 80% of current shock-risk margin. **Real Delta may perform partial liquidation; this model assumes full close.**

ETH price-shock span at this size is *not independently sourced* from published BTC illustrative table. Accordingly 1% for ETH is a comparative assumption, and 2% and 3% stress scenarios are separate sensitivities, with position size reduced to keep **portfolio initial risk margin <=$10**. Do not misrepresent ETH 1% shock as a confirmed rule.

**Account and trade controls:** independent $100 accounts for BTC and ETH; $10 initial margin cap per trade; maximum $1,000 notional, one futures position at a time, no additional positions/options; only existing EMA20 + Supertrend entries, ATR/volume filters, original 2xATR stop, 150/50 BTC trailing / percentage-scaled ETH trailing, opposite ST flip. 15m OHLC synthetic path from verified minute archive. No entry guard, no historical mark/funding/spread/slippage.

**Crucial:** Portfolio Margin does not report per-position liquidation prices, so the prior $1-before-liquidation protective exit is **not implemented**. Original ATR/trailing stops remain. Do not pretend the latest Isolated preliq replay is execution-identical.

**Costs and liquidation:** use original hypothetical 30-minute Scalper Offer, 0.05% taker commission plus assumed GST 18%, or separate no-offer scenario. Portfolio forced-liquidation fee: 0.25% notional plus modeled GST. Historical enrollment in the offer is unverified. User should not deploy from this simulation.

**Reporting:** full history Jan 2025–Nov 2026 (last Nov incomplete); recent 10k 15m subset with separate $100 initial wallet, 1%, 2%, 3% shocked exposure, drawdowns both closed equity and synthetic intrabar equity, per-month net and monthly closed-equity DD. Single-asset only, so no hedge savings from other positions/options can be inferred.

Primary documentation:
- https://guides.delta.exchange/delta-exchange-india-user-guide/trading-guide/margin-explainer/portfolio-margin
- https://www.delta.exchange/support/solutions?articleId=80001199835
- https://guides.delta.exchange/delta-exchange-india-user-guide/trading-guide/margin-explainer

No main-branch modifications.
