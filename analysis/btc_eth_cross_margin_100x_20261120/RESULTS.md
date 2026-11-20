# Hypothetical Cross Margin BTC/ETH 100× — Results (2026-11-20)

**Important: this cross-margin model is NOT confirmed to be available on Delta India BTCUSD/ETHUSD.** Delta India public docs list the contracts as INR-settled, while cross-margin docs specify USDT-settled instruments. All results below are research simulations.

## Same strategy, changed margin only

- Wallet starts at $100 separately for BTC and ETH, fixed initial margin requirement <=$10 per trade, nominal leverage 100×, position notional <=$1000, one position at a time. Every remaining account dollar can support an adverse move (cross collateral). No shared BTC/ETH position risk is modeled; each asset has a separate independent $100 account.
- Same closed-15m EMA20+Supertrend entries, volume/ATR filters, 2xATR stop, original BTC 150/50 trailing and entry-relative ETH trail; optional $1 preliquidation exit.
- Assumes 0.25% maintenance on current position notional, no open other positions, zero historical funding, spread/slippage, no historical mark-price data, and a synthetic 15m OHLC price path. Cross liquidation is a **proxy**: wallet + unrealized price PnL falls below maintenance.
- Main fee case assumes an unverified historical 30-minute Delta Scalper Offer, taker 0.05% on entry, exit free when eligible, 18% modeled GST; otherwise exit taker 0.05%.
- Synthetic mark-to-market drawdown samples near-extreme-first 15m OHLC points **up to the modeled stop exit**; it is NOT historical exchange mark-price drawdown. Monthly DD is measured on closed realized wallet only.

## Full period, Jan 2025 — Nov 2026 (last November partial)

| Scenario | BTC ending | BTC net | BTC closed DD | BTC synthetic intrabar DD | BTC liquidation count | ETH ending | ETH net | ETH closed DD | ETH synthetic intrabar DD | ETH liquidation count |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Cross + one point preliq, assumed offer | $878.34 | +$778.34 | 9.64% | 10.45% | 0 | $1,940.45 | +$1,840.45 | 19.47% | 20.26% | 0 |
| Cross no preliq, assumed offer | $878.34 | +$778.34 | 9.64% | 10.45% | 0 | $1,940.45 | +$1,840.45 | 19.47% | 20.26% | 0 |
| Cross + one point preliq, NO offer | $513.54 | +$413.54 | 23.77% | 24.27% | 0 | $1,524.65 | +$1,424.65 | 22.20% | 23.30% | 0 |

With assumed offer and one point stop, BTC: 999 closed trades, PF 1.5545, 19 profitable/3 losing complete months. ETH: 1000 closed trades, PF 2.1520, 22 profitable/0 losing complete months. No completed month had a 100% account drawdown. These values are not live expectancy.

### Prior isolated 100× (one-point pre-liquidation simulation) — same $100 wallet, <=$10 initial margin

BTC: ending $928.50; DD 11.51%; zero model liquidations. ETH: ending $2,012.67; DD 16.98%; zero model liquidations. These isolated simulations have different potential account-level risk and were not modeled with live marks/slippage. Cross does **not** improve the modeled net P&L here despite reducing the possibility of liquidation from the original ATR-only isolated setup.

## Reproduction

Source: `scripts/replay_btc_eth_cross_margin_100x.py`

Action: `.github/workflows/replay-btc-eth-cross-100x.yml`

Primary full-history outputs:
- `summary.json`
- `btc_history_preliq_offer_threshold_monthly.csv`, `eth_history_preliq_offer_threshold_monthly.csv`
- Trade ledgers in corresponding compressed `_trades.csv.gz` files.
- No-offer and no-preliq scenario files are saved alongside.

Research caveat: One-dollar stops are **not guaranteed to execute** before liquidation, and cross can lose much more than the $10 initial margin. The hypothetical model is not a real cross-margin test at Delta Exchange India. Do not enable live cross trading from these results.
