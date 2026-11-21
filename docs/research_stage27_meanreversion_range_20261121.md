# Stage27 — Add independent Mean Reversion and Range Trading BTCUSD strategies

**Research implementation completed:** [Successful GitHub Actions run 44909807475](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44909807475). Source: \`scripts/research_stage27_meanreversion_range_20261121.py\`. Experimental strategy configuration: \`config/strategies/stage27_btc_mean_reversion_range_research.json\`.

## Exact separation

1. **Mean Reversion, 1H:** Long after an already completed 1H candle had closed below the lower 20×2 Bollinger band with RSI(2) <=15, then a new full 1H candle closes back above the lower band. 4H regime ADX<=25 and efficiency8<=.35. Next 1m open. Structural stop below most recent 1H low(s) minus .15×ATR, target frozen signal-time 1H SMA20, max 12 hours. **Selected LONG ONLY on 2025 data**, not optimized for 2026.
2. **Range Trading, 1H:** Prior 48 complete 1H candles define pre-existing support/resistance, channel width 2.5–15×1H ATR; a full 1H signal candle touches and rejects a known boundary and closes back inside with directional conviction. ADX(4H)<=30, efficiency8(4H)<=.45. Next 1m open. LONG at support, SHORT at resistance. Stop 1.5× ATR; target frozen range midpoint, max 12 hours.

Other studied causal variants: EMA20/ATR overextension mean reversion, Bollinger re-entry, range sweep vs touch, 24 vs 48 hours, three regime gates, both/long/short, structural vs ATR stops, fixed vs midpoint targets, 4/8/12 hour holds. Total 1,296 configurations, 432 mean-reversion and 864 range-trading.

## Source and execution

- Original Delta India BTCUSD Futures **989,280 continuous authentic 1-minute candles**, Jan 2025–Nov 18 2026; **22 complete months Jan 2025–Oct 2026** are evaluated.
- All signals based on completed 1H/4H candles; next 1m open for entry; initial stop wins a 1-minute simultaneous stop/target hit; one open trade per standalone sleeve.
- Costs already included: taker 0.05% both legs, GST 18% on fees, plus five BTC price points adverse slippage on each leg. A second replay has **additional adverse 5bps per side**.
- Risk sizing 0.5% of strategy equity per 1R, capped by 5× notional.
- Preselected using **2025 only**, Jan–Oct 2026 check. IMPORTANT: 2026 has been previously researched across this repository, not truly untouched/out-of-sample. Further historical optimization will exacerbate overfitting.
- No real funding, book bid/ask, contract rounding, liquidation or shared margin are modeled. Portfolio blends are synthetic weighted month-end returns.

## Selected standalone results

| Family | 2025 | Jan–Oct 2026 | Full 22 months | Positive/loss/flat months | Full 22 months with +5bps extra per side | Interpretation |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| Mean Reversion, 1H Bollinger re-entry LONG | +1.85% | **−1.79%** | +0.03% | 11 / 9 / 2 | **−4.44%** | **Reject from live portfolio**. Did not pass cost-stressed 2025 selection gate. |
| Range Trading, 1H prior 48-bar boundary touch/reject | +6.48% | **−1.10%** | +5.31% | 12 / 8 / 2 | +2.07% | **Forward watch only**. Historically positive overall, but Jan–Oct 2026 negative and does not improve anchor. |

Mean Reversion had 42 completed standalone backtest trades; Range Trading had 55. These returns are on per-strategy hypothetical sizing, **not 10× leverage returns**.

## Portfolio experiment

The reference was the published synthetic **90% Core / 10% 4H Donchian20** blend, preserving its internal 90:10 split. Added strategies take a fixed percentage of the entire account and proportionally dilute the reference 90/10 allocation.

| Allocation of total capital | Standard-cost 22m | Profitable months | Extra +5bps each side 22m | Profitable months under stress |
| --- | ---: | ---: | ---: | --- |
| **90% Core + 10% 4H Donchian** (unchanged) | **+18.79%** | **18/22** | **+10.21%** | **13/22** |
| 95% original 90/10 + 5% Mean Reversion | +17.78% | 18/22 | +9.44% | 11/22 |
| 95% original 90/10 + 5% Range Trading | +18.08% | 17/22 | +9.79% | 12/22 |
| 90% original 90/10 + 5% MR + 5% Range | +17.08% | 18/22 | +9.03% | 11/22 |

**2025-only portfolio selection under additional 5bps on all sleeves: leave both added strategies at zero allocation.** No positive portfolio improvement verified. This is not a failure to implement the two proposed strategy families; it is a meaningful negative result from honest after-cost research.

## Decision and next steps

- Two new **coded, configurable, backtestable** strategy families are installed in the isolated Stage27 research branch, with the exact frozen candidate settings recorded in a disabled BACKTEST_ONLY JSON manifest.
- Do not merge into trading engine or turn on live orders. Range Trading is potentially worth fresh forward paper monitoring; Mean Reversion needs fundamentally better entry/exit logic or has no current trading edge.
- The family-specific research scheduled tasks should not be confused with a validated four- or six-strategy live trading account.
- Future work should prioritize NEW market data outside the historical tuning interval and direct order-book / funding model validation, not retrospective optimization to manufacture 22/22 profitable months.

Full machine-readable files are in workflow artifact **btc-stage27-meanreversion-range-replay-results**: \`two_strategy_selected_results.csv\`, \`two_strategy_selected_monthly.csv\`, \`every_meanreversion_range_configuration.csv\`, \`portfolio_blend_comparison.csv\`, \`portfolio_blend_monthly.csv\`, and \`summary.json\`.
