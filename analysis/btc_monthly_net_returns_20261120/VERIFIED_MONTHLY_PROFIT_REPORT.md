# BTC monthly net-profit improvement: controlled replay (20-Nov-2026)

## Verified completed backtests

- [Risk-matched BTC 1m initial ATR stop, channel and trailer study — run 44665895240](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44665895240): **SUCCESS**. Tested 20 configurations under 0, +2, +5, +10 basis points additional slippage EACH side. Original 198-trade 48h strategy reproduced **exactly**, monthly max NAV drift zero.
- [Frozen BTC/ETH 1m 48h breakout and capital-neutral mixing — run 44666242888](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44666242888): **SUCCESS**. Tested ETH unchanged with native 1m data and compared 75/25, 50/50, 25/75 BTC/ETH capital splits. See Actions artifact `btc-monthly-net-return-research-evidence` ID 14597593362.

## Verdict

**NO meaningful improvement in average NET monthly return was validated.** Do not claim that positive total return or more positive months is the same as increasing expected profit per month. These are model outputs, not exchange-verified fills or forward tests.

### BTC stop/channel search

All candidates use completed 1H close and completed 4H trend, the first next 1m open, ATR initial stop and completed 1H trailing stops, maximum 14 day hold, 0.5% initial account risk per trade and <=3x implied theoretical notional. Initial stop ATR 1x,1.25x,1.5x,1.75x,2x; trailing 1.5x,1.75x,2x; channels 12,24,36,48,72 hours; 20 preregistered variants.

| BTC strategy | 2025 after base costs | Jan–Oct 2026 after base costs | 22m total after base costs | Mean monthly | Profitable months | Losing months | 22m net +2bps/side |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Prior 48h breakout, stop2×ATR trail2×ATR** | +7.2669% | +9.0207% | **+16.9431%** | **+0.7475%** | 12 | 10 | **+12.7836%** |
| BTC 2025-only selected **72h**, stop2×ATR trail2×ATR | +6.1828% | +4.1036% | +10.5401% | +0.4917% | 11 | 11 | +7.3833% |

The BTC 2025-only selected 72h exit looked attractive on training downside-adjusted monthly-profit score under +2bps/side, but is **inferior to the 48h original over the 2026 chronological check and the full 22 months**. This result is a failure to improve monthly profit, not a promotion.

The 48h original +10bps/side actual modeled adverse fill stress becomes **−2.4349%** over 22 months, indicating significant execution-cost sensitivity.

### Frozen BTC-to-ETH robustness / complementary trading

No ETH tuning of the BTC-2025 selected 48h rule; ETH uses a native ETH 1m OHLC feed and the same trend, breakout, 2×ATR stop and trailing rule. Risk 0.5% NAV per trade, max theoretical implied notional 3×, exchange model fee 0.05% taker EACH leg +18% GST, plus adverse slip. BTC baseline slip 5 USD-price points/side; ETH baseline slip = **1bp ETH price/side**, an assumption, not historical L1 quote data.

| Frozen market/capital split | 2025 return | Jan–Oct 2026 return | 22m return | Mean monthly net | Positive / losing months | 22m net with extra +2bps/side |
|---|---:|---:|---:|---:|---|---:|
| **100% BTC** | +7.2669% | +9.0207% | **+16.9431%** | **+0.7475%** | 12 / 10 | **+12.7836%** |
| 100% ETH | +3.8776% | +5.5232% | +9.6149% | +0.4547% | 11 / 11 | +7.3906% |
| 75% BTC / 25% ETH | +6.4911% | +8.1715% | +15.1929% | +0.6743% | 11 / 11 | +11.5346% |
| 50% BTC / 50% ETH | +5.6669% | +7.3052% | +13.3860% | +0.6011% | 12 / 10 | +10.2177% |
| 25% BTC / 75% ETH | +4.7954% | +6.4223% | +11.5256% | +0.5279% | 11 / 11 | +8.8355% |

**The ETH mix DID NOT improve monthly account profitability or the profitable-month fraction.** The portfolio estimates combine monthly NAVs at fixed capital weights and do NOT simulate rebalancing fills or shared exchange margin/liquidations.

## Research/data caveats

- Both 2025 and 2026 histories were exposed in earlier research; **no pristine independent out-of-sample / live forward validation**. Parameter-search selection risks overfitting.
- Minute OHLC is not tick-level data: cannot verify actual spread, queue priority, maker availability, slippage, funding, and stop order fill sequencing. Original candle model checks stop-first.
- Known BTC/ETH 1m historical archive gaps, earliest 2025 IST and last Oct 2026 UTC day. Dates in results are observed month labels, not certified completely uninterrupted market tape.
- Exact Delta contract lots, quantity rounding, margin, liquidation, financing and spread/impact are NOT modeled. Fractional risk sizing and 3× theoretical leverage filter are simplified.
- ETH USD index point vs BTC index point slippage assumptions DIFFER in deliberately disclosed ways; these are not exchange-validated historical fill statistics.
- No live orders, no modification of production strategies, no main branch merge.

**Decision: retain the original 48h BTC breakout as research baseline only, reject this batch as substantive monthly-profit improvements.** To genuinely reach larger average net monthly returns at the SAME risk, a new economic signal with stronger net per-trade expectancy or better complementary timing is necessary; adding leverage alone amplifies losses/drawdown without creating an edge.
