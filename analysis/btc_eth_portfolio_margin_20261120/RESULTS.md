# BTC and ETH: Portfolio Margin futures-only backtest

**Research date:** 2026-11-20 · **Period:** 2025-01-01 to BTC 2026-11-18 / ETH 2026-11-17 · November 2026 is partial.

This is a **single unhedged futures position** portfolio-risk model using Delta's documented futures stress method, **not** an authenticated replay of the live portfolio risk engine. It is not a historical hedged futures/options Portfolio Margin test; the repository lacks historical strike/expiry-specific option quotes, IV and mark prices.

## Setup and risk methodology
- Two independent $100 starting wallets (one BTC, one ETH). Same 15m EMA20+Supertrend entry logic and ATR/volume filters, 2×ATR stop, BTC 150-point activation / 50-point trailing, ETH pre-agreed entry-relative trail, Supertrend flip. Fixed position-size target <=$1,000 notional.
- **Limit initial portfolio risk margin to $10**, not literal user-selected 100x leverage. 1% price shock allows up to $1,000 notional; 2% allows $500, and 3% allows ~$333.33 (rounded to whole contracts). No other positions or offsets.
- For a single linear futures position, the documented 29 risk scenarios collapse to the worst adverse price-shock loss (IV stress has no direct futures price effect), with a **futures floor of 0.5% of notional**. Maintenance risk is 80% of the scenario margin minus unrealized cashflows. Model full forced close when wallet + PnL <= 80% of stress risk. In reality the engine may cancel orders or partly hedge/reduce positions.
- The **1% notional shock** is documented for *small BTC* portfolios; its application to ETH is **unverified**. ETH 2% and 3% shocks below are explicit sensitivity assumptions, **not actual exchange ETH parameter claims**.
- Portfolio Margin does **not** provide an individual position liquidation price. Therefore a stop $1 before per-position liquidation is **not implemented**. The ordinary 2×ATR/trailing/ST exits remain.
- Fees: hypothetical 30-minute Scalper Offer, taker fees on non-waived sides, assumed GST18%. No funding, slippage, spread, or actual exchange historical mark/stop execution latency. The historical Scalper Offer eligibility is unproven.
- **Mode availability:** Delta India guide lists USD-settled BTC/ETH futures and options as eligible for Portfolio Margin. Confirm the particular account and contract in the exchange UI, not from this model.

## Full-history results

| Price-shock and fee case | BTC net | BTC ending wallet | BTC closed DD | BTC intrabar DD | BTC liquidations | ETH net | ETH ending wallet | ETH closed DD | ETH intrabar DD | ETH liquidations |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1% shock + offer | +$778.34 | $878.34 | 9.64% | 10.45% | 0 | +$1840.45 | $1940.45 | 19.47% | 20.25% | 0 |
| 1% shock without offer | +$413.54 | $513.54 | 23.77% | 24.27% | 0 | +$1424.65 | $1524.65 | 22.20% | 23.30% | 0 |
| 2% shock + offer | +$374.66 | $474.66 | 8.09% | 8.78% | 0 | +$905.18 | $1005.18 | 12.55% | 13.07% | 0 |
| 3% shock + offer | +$236.01 | $336.01 | 6.24% | 6.56% | 0 | +$596.85 | $696.85 | 9.33% | 9.73% | 0 |

**Base 1%/assumed-offer:** BTC 999 closed trades, net PF 1.5545, 19 profitable / 3 losing completed months; ETH 1,000 closed trades, net PF 2.152, 22 profitable / 0 losing completed months. Zero *modeled* liquidations in both, NOT zero guaranteed live liquidations. The 1% Portfolio result is numerically identical to prior hypothetical Cross because the strategy stop exits occurred before either margin threshold in the synthetic price path.

## Monthly results — 1% shock and assumed offer

**DD** is the worst *closed-equity* decline **within each month**, whereas aggregate intrabar DD includes simulated unrealized excursions. November 2026 is partial.

| Month IST | BTC net | BTC monthly closed DD | ETH net | ETH monthly closed DD |
|---|---:|---:|---:|---:|
| 2025-01 | +$140.65 | 8.93% | +$78.47 | 19.47% |
| 2025-02 | +$8.89 | 7.31% | +$1.65 | 10.01% |
| 2025-03 | +$112.75 | 5.66% | +$159.54 | 8.64% |
| 2025-04 | +$69.19 | 3.84% | +$84.58 | 8.79% |
| 2025-05 | +$17.35 | 5.31% | +$70.13 | 3.35% |
| 2025-06 | +$23.66 | 4.46% | +$158.71 | 3.23% |
| 2025-07 | +$0.67 | 4.58% | +$57.11 | 2.83% |
| 2025-08 | +$12.19 | 3.64% | +$200.50 | 1.81% |
| 2025-09 | −$40.37 | 9.34% | +$27.22 | 4.20% |
| 2025-10 | +$35.81 | 3.93% | +$89.21 | 1.81% |
| 2025-11 | +$31.52 | 2.16% | +$109.06 | 1.59% |
| 2025-12 | +$109.91 | 2.70% | +$137.71 | 1.94% |
| 2026-01 | +$18.13 | 2.80% | +$111.68 | 1.20% |
| 2026-02 | +$87.28 | 6.04% | +$154.90 | 1.69% |
| 2026-03 | +$70.31 | 1.71% | +$101.17 | 1.48% |
| 2026-04 | +$0.34 | 3.67% | +$35.24 | 1.68% |
| 2026-05 | −$5.83 | 3.14% | +$34.54 | 0.89% |
| 2026-06 | +$36.94 | 2.83% | +$6.49 | 2.30% |
| 2026-07 | −$33.29 | 6.31% | +$42.99 | 1.78% |
| 2026-08 | +$21.06 | 1.34% | +$39.09 | 0.95% |
| 2026-09 | +$37.38 | 1.52% | +$98.52 | 1.39% |
| 2026-10 | +$13.36 | 3.09% | +$7.90 | 1.91% |
| 2026-11 (partial) | +$10.44 | 2.81% | +$34.01 | 1.21% |

## Comparison to previous modeled outcomes

| Mode | BTC net | BTC max closed DD | ETH net | ETH max closed DD |
|---|---:|---:|---:|---:|
| Isolated 100x **with previous $1 preliquidation stop** | +$828.50 | 11.51% | +$1,912.67 | 16.98% |
| Hypothetical Cross (initial $10 margin target) | +$778.34 | 9.64% | +$1,840.45 | 19.47% |
| Portfolio futures-only, **1% price span assumption** | +$778.34 | 9.64% | +$1,840.45 | 19.47% |

These modes have different liquidation treatment: Isolated uses an *estimated individual liquidation-price pre-stop*, while Portfolio has no such individual reference. Identical profit under Cross/Portfolio in this simulated unhedged setup is not proof of equal live risk.

## Files

- `scripts/replay_btc_eth_portfolio_margin.py`
- `analysis/btc_eth_portfolio_margin_20261120/summary.json` (all scenarios, including recent 10k-candle fresh-$100 samples)
- `analysis/btc_eth_portfolio_margin_20261120/{btc,eth}_history_shock1pct_offer_monthly.csv` and corresponding 2%/3%/no-offer scenario monthly CSVs
- `*_trades.csv.gz` (each trade ledger)
- `.github/workflows/replay-portfolio-btc-eth.yml`

Official published margin formulas: https://guides.delta.exchange/delta-exchange-india-user-guide/trading-guide/margin-explainer/portfolio-margin

**Not live-ready:** this research does not test actual historical futures mark prices, option contracts/hedges, exchange portfolio liquidation behavior, historical offer access, funding or fill slippage. Do not change the VPS exchange margin mode based solely on this simulation.
