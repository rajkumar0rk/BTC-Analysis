# BTCUSD 15M — Remove Supertrend reversal exit, use fixed % SL

## Reproducibility and status

- Backtest calculation completed and passed all integrity assertions in [GitHub Actions run 45111222963](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45111222963). The GitHub job's final status is failure **only because its archive push was rejected by a concurrent research commit**; the actual calculation, artifact upload and parity assertions succeeded.
- All **204 distinct configurations**, each under both 1-minute OHLC path orderings: **408 simulations**, reconstructed and verified from the successful job's `RESULT` JSON log lines. Complete results: [summary.csv](summary.csv).
- Date window: January 2025 through October 2026 IST, BTCUSD futures, 15-minute Supertrend ATR(10) multiplier 3 + EMA20 entry signals. Historical 1-minute replay for exits. No 1-hour or volume entry filter.
- All models marked `NOFLIP` ignore Supertrend reversals as EXIT conditions. Supertrend still defines ENTRY signals and ST cycles. Trade exit is only through selected percent SL, profit-protection stop, 3R TP (when enabled), or sample-end close. At most one open position and one trade per ST cycle; later eligible entry signals while occupied are skipped.
- Fee model: taker 0.05% per side, 18% GST on fee, adverse slippage 0.02% per side; positions sized to evolving $1,000 starting equity at 1× notional. No funding, spread beyond explicit slippage, liquidation, depth, execution latency, or real exchange fill guarantees.
- The historical 22-month window has been heavily examined in earlier research: **these results are in-sample and do not constitute an out-of-sample edge.**

## Reclaim — promising models WITHOUT profit protection

| Initial percentage SL | Fixed 3R TP | Trades | Wins / losses | 22-month net return | Positive months | Max floating drawdown | Profit factor |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1.25% | 3.75% | 232 | 65 / 167 | −6.11% | 10/22 | 26.96% | 0.9751 |
| 1.50% | 4.50% | 198 | 60 / 138 | **+27.48%** | 13/22 | 20.19% | 1.0949 |
| 2.00% | 6.00% | 138 | 44 / 94 | **+52.39%** | 14/22 | 30.24% | 1.2297 |
| 3.00% | 9.00% | 75 | 27 / 48 | **+97.52%** | 16/22 | 20.86% | 1.5533 |

All these four rows are from the O-H-L-C path; the O-L-H-C path gave identical performance. Their exit counts include a single **forced end-of-dataset close** for each model; the remainder hit their SL or TP. No Supertrend reversals closed these trades.

### Annual results

| SL / TP | 2025 total return | Jan–Oct 2026 return | 2025 profitable months | 2026 profitable months |
|---|---:|---:|---:|---:|
| 1.50% / 4.50% | +19.85% | +6.36% | 7/12 | 6/10 |
| 2.00% / 6.00% | −10.82% | +70.87% | 6/12 | 8/10 |
| 3.00% / 9.00% | +4.33% | +89.32% | 8/12 | 8/10 |

At 3% SL / 9% TP, 26 trades reached TP, 48 reached SL, and 1 was closed for accounting at the end of the test. Fees plus GST accumulated $104.77; 1-minute adverse slippage is also included in the net result. Only 75 of 434 possible Reclaim signals opened positions; the rest were skipped while holding a position (359).

## What removing reversals and using profit protection changed

Controlled comparison holding **initial SL 1.25%, first protection trigger and lock both +0.15%, 3R TP**, and the same entry logic:

| Exit handling | Trades | Net after costs | Profitable months |
|---|---:|---:|---:|
| Supertrend flip exit ON, profit protection ON | 434 | −38.62% | 1/22 |
| Supertrend flip exit OFF, profit protection ON | 418 | −36.12% | 3/22 |
| Supertrend flip exit OFF, protection OFF, 3R TP (1.25% / 3.75%) | 232 | −6.11% | 10/22 |

**Simply removing reversal exits did not make the 1.25% protected strategy profitable.** The profitable models also use **larger stops, genuine 3R targets, and no early profit protection**, so multiple settings changed.

With a 3% SL, no flip exit but with immediate 0.15% protective lock, the best staircase model was still **−28.39%**, with 401 trades, 11/22 profitable months, 197 winners and 204 losers. The protection stop was used 388 times, the initial SL 13 times, and TP **zero** times. By contrast, at 3% SL, profit protection OFF and 9% TP ON yielded **+97.52%** on only 75 trades.

Turning fixed TP OFF as well (3% SL, protection OFF, flip OFF) yielded **−36.98%** with 21 trades. Thus the **large 3R fixed winners** are necessary for the positive historical results.

## Conclusions and caution

- The no-flip Reclaim results improved materially when positions were held to a **fixed 1.5%–3% percent SL or 3R target**, without early profit locking.
- These are *not* evidence the same profitability will repeat: 3% was selected from an already repeatedly inspected historical sample, exits assume simplified 1-minute OHLC and costs exclude funding and liquidation.
- Larger initial stops make losses larger per trade even when historical compounded returns improve. These results assume 1× notional and are not margin-adjusted or leverage-safe.
- Before considering live capital, validate on completely unseen future data, use exchange-specific fills/funding, and quantify fee and gap sensitivity. A controlled walk-forward test should retain predeclared parameters.

Full simulation JSON rows are published in `summary.csv` alongside this report. The GitHub Actions run includes downloadable full trade ledgers, monthly equity files and logs as its uploaded artifact.
