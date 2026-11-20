# Stage18/Stage20 — actual BTC 1-minute signal, target and trailing-exit improvement

**Status: RESEARCH-ONLY, NOT LIVE READY.** Completed TWO GitHub Actions backtest runs:
- [BTC 1-minute original-event replay and entry/TP/holding variants — run 44647079361](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44647079361)
- [Actual 1-minute progressive trailing/breakeven test — run 44647646879](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44647646879), SUCCESS. This run saves the original 1-minute trade exit ledgers and full monthly comparison artifacts.

## What was actually improved

We retrieved the authentic **Stage14 original candidate event states** from run 44118024590. Replayed Stage18/Stage20's primary Stage15 quiet-volume, previous-month ranging, 4H-filtered 1H/15M trade setups on the genuine BTCUSD **1-minute OHLC** archive using the unchanged original stop-first entry/exit engine. The original Stage15 target was **3R** and maximum hold **240 minutes**. Tested 2R, 4R, 5R, 480-minute holding, volatility/participation/risk filters, break-even stops after 2R and stepped profit-lock trailing. Kept the original structural stop, `weekly_minus_3R` entry gate, 1H volume ratio <=1.2 and 240-minute holding period for the **5R candidate**.

The result is a true new historical BTC entry/exit **primary-component** backtest. Stage18/Stage20 portfolio monthly figures combine this re-executed component with original Stage17 daily Donchian / Stage19 hourly momentum sleeve monthly NAV. This is **NOT yet a complete 1-minute, shared-margin three-sleeve execution replay**.

## Original vs BTC 5R

| Result | Original 3R / 240m | 5R / 240m |
|---|---:|---:|
| Stage18 BTC full 2025 account return | +4.7356% | +6.7313% |
| Stage18 BTC Jan–Oct 2026 return | +5.0832% | +4.9517% |
| Stage18 BTC compounded Jan2025–Oct2026 | +10.0596% | **+12.0163%** |
| Stage18 positive / losing / flat months | 15 / 4 / 3 | 15 / 4 / 3 |
| Stage20 BTC full 2025 account return | +3.4129% | +5.1873% |
| Stage20 BTC Jan–Oct 2026 return | +4.3056% | +4.1875% |
| Stage20 BTC compounded Jan2025–Oct2026 | +7.8655% | **+9.5921%** |
| Stage20 positive / losing / flat months | 18 / 3 / 1 | 18 / 3 / 1 |
| Stage15 core BTC PF of net R per closed trade | 1.9620 | **2.1507** |
| Stage15 core average net R per trade | +0.3843R | **+0.4596R** |
| Stage15 core completed trades (2025 + 2026 Jan–Oct) | 64 | 64 |
| Stage15 core 2025 training trades | 44 | 44 |

Baseline month-by-month comparison with preserved saved Stage18/Stage20 returns succeeded (max discrepancy <0.007 percentage points). Baseline is identical in strategy logic, with a 3× notional leverage size cap added.

### Extra-slippage sensitivity

The original source fills already charge the **modeled** taker fee 0.05% each side, GST 18% on fees, and 5 BTC price points adverse slippage **per side**.

| BTC 22-month model | Original 3R | 5R |
|---|---:|---:|
| Base modeled costs | +10.0596% Stage18; +7.8655% Stage20 | **+12.0163% Stage18; +9.5921% Stage20** |
| Additional +2 basis points adverse slippage EACH fill side | +7.6058% Stage18; +5.6961% Stage20 | **+9.5197% Stage18; +7.3882% Stage20** |
| Additional +5 basis points adverse slippage EACH fill side | +4.0278% Stage18; +2.5247% Stage20 | **+5.8791% Stage18; +4.1663% Stage20** |

The **2025-only risk-adjusted selection** of the first 12-variant experiment preferred **4R plus a low-4H-volatility filter**; that branch later disappointed in the already-researched 2026 period, indicating selection instability. A second, explicitly declared **trailing/large-winner comparison** used BTC 2025 with the additional 2bp/side slippage stress and selected **untrailed 5R** over the breakeven and profit-lock alternatives. However both test campaigns happened AFTER original 2026 history had previously been explored, so this is **NOT genuine pristine out-of-sample validation**. Do not retrospectively discard any failed selected model.

## Why the result is not a live trading recommendation

1. Stage18 and Stage20 multi-sleeve combined monthly results still mix a freshly executed Stage15 trade stream with **archived** Stage17/Stage19 monthly component equity. Their concurrent positions, rebalance fills, contract rounding, shared margin and liquidation constraints are **not** simulated in one native trade-execution engine.
2. The source beginning January 2025 IST is missing 330 minutes and source 2026-10-31 UTC is incomplete. Historical 22-month reporting is by month label; it is not certified complete unbroken 22-month data.
3. No true L1 bid/ask, market impact, actual historical funding cashflows, open-equity intraminute liquidation stress or exchange-compatible integer lot sizing. Monthly main-sleeve PnL is booked at trade exit, not exact month-end MTM of spanning trades.
4. **Native ETHUSD execution under the new 5R rule has NOT been completed.** Existing earlier ETH Stage18/20 studies were weak, but cannot be used as a 5R validation. Do not claim ETH success.
5. The 2025 training selection has been repeatedly exposed to earlier research; 2026 was also research-exposed and cannot be called an untouched holdout. Small sample 64 core trades across 22 month labels.

Decision: **EXPLORATORY 5R TRADING-RULE IMPROVEMENT** in modeled BTC account results; NOT a validated profitable or deployable strategy. Profit-protection trailing variants did not outperform the simple 5R take-profit in the BTC-2025 extra-cost selection. Further work should integrate all sleeves in genuine native 1m execution and verify funding, margin, lot sizes, ETH, and new forward paper data without retuning on already-seen 2026.

No changes to main or other research tasks, and no live trading.
