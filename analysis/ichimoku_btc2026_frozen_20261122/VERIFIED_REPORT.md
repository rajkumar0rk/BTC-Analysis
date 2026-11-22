# Frozen 4H Ichimoku BTCUSD — Jan–Oct 2026 historical replay

**COMPLETED VERIFIABLE BACKTEST:** [GitHub Actions run 44988188973](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44988188973), successful 2026-11-22. [Immutable run artifact](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44988188973/artifacts/14740423025) contains 34 trades, all 10 monthly IST NAV records and summary JSON. Full frozen source: [research script](https://github.com/rajkumar0rk/BTC-Analysis/blob/research/ichimoku-btc2026-frozen-replay-20261122/scripts/trend_family_ichimoku_frozen_btc2026.py).

## Verdict — fails profitability

| Statistic | BTC 2025 original verified screen | BTC Jan–Oct 2026 frozen screen |
|---|---:|---:|
| Net after modeled fees and GST | +1.699752% | **−3.483884%** |
| Profitable months | 6/12 | **3/10** |
| Losing months | 6/12 | **7/10** |
| Completed trades | 28 | **34** |
| Profit factor | 1.238745 | **0.679503** |
| Maximum intraminute-NAV drawdown as reported by replay | 4.2113% | **6.8336%** |
| Winning / losing closed trades | 9 / 19 | **8 / 26** |

2025 source: [run 44952126471](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44952126471). No optimization from 2026. No merged continuous-account NAV backtest across the 2025/2026 year boundary: 2026 was separately started with NAV=100, using Oct–Dec 2025 only as signal warmup.

## Actual 2026 IST monthly NAV results

| Month | Net month % | End NAV |
|---|---:|---:|
| 2026-01 | +0.299407 | 100.299407 |
| 2026-02 | +0.344227 | 100.644665 |
| 2026-03 | −0.751452 | 99.888369 |
| 2026-04 | −1.688933 | 98.201321 |
| 2026-05 | −0.039835 | 98.162202 |
| 2026-06 | +3.538934 | 101.636098 |
| 2026-07 | −2.765274 | 98.825581 |
| 2026-08 | −0.909233 | 97.927026 |
| 2026-09 | −0.740152 | 97.202218 |
| 2026-10 | −0.705850 | **96.516116** |

Total: **3 positive / 7 negative / zero flat**, compounded NAV from 100 to 96.516116; **−3.483884%**. Biggest winner month June +3.54%; worst July −2.77%.

## Strategy exactly frozen

- 4H Ichimoku Tenkan(9)/Kijun(26) crossover, completed close relative to the causally shifted 9/26/52/26 cloud, direction of close relative to 26 4H bars ago; simultaneous new signal and structural cloud rules.
- Enter at next 1-minute open upon 4H close, monitored with 1-minute stop with gap logic.
- Fixed 2×4H ATR(14) initial protective stop was an explicitly disclosed **research overlay** in both 2025 and 2026, so not a direct source-faithful publisher reproduction.
- Sizing nominal 0.5% initial-account NAV risk per entry, capped at 1× notional; equity changes recorded after exit, monthly marked to liquidatable mid-close with estimated exit fees.
- Fee assumption 0.05% notional per entry and exit side plus 18% GST; ZERO modeled slippage. No historical funding, order book spread/market impact, lot rounding, liquidation, or actual fill-depth data; figures are **not all-in live-ready**.
- BTCUSD historical one-minute archive, 2026 IST month boundaries validated and no source-minute gaps found in selected calendar range. SHA256 of pandas source candle-frame: `2e04f0e75a001013e533fc1c4253a9bc5dbc2a34cac637533973c8171012f131`.
- This is a **chronological research-exposed 2026 check**, not pristine out-of-sample validation. No post-2025 parameter optimization was performed.
- Strictly 2026 alone has 3/10 winning months; 2025 and 2026 individual year samples have 9/22 winning months together, but this simple count is NOT a separately executed continuous 22-month portfolio.

**Decision:** Reject current 4H Ichimoku as a BTC consistent-month-profit strategy. Do not paper over the losing 2026 months or claim 22/22, positive expectancy, or readiness to trade real money.

Code and results are on the isolated research branch only; no main change and no live order submission.
