# Completed three-strategy monthly portfolio screen — 2026-11-21

**Research finding: the combination does NOT achieve 22/22 profitable months.**

## Source artifacts (archived completed actions)

- Stage18 and Stage20 optimized monthly returns: [run 44652343750](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44652343750) artifact `btc-guard-free-stages18-20-complete`; read `all_months.csv`, variant `5R_broader_eff25_no_gate`, `stress_bps_side=0`.
- 48H Donchian monthly returns: [run 44681039768](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44681039768) artifact `btc-slippage-05-vs-5-22month-research`; read `all_22_months_and_rejected_signals.csv`, variant `unmodified`, adverse 5 BTC price points each side, `slippage_bps_side=0`.
- Matched 22 IST months, 2025-01 through 2026-10; previously simulated 0.05% taker fee each leg, 18% GST on these fees, adverse 5 BTC price points each leg; funding, bid/ask order book, margin, and liquidation NOT included.

## Result

Each month a predeclared **50% Stage18 / 20% Stage20 / 30% 48H Donchian** capital weighting was applied to the three already-after-cost monthly returns and compounded into one hypothetical month-end NAV.

| Capital allocations | Positive / 22 months | Losing | Flat | Compounded 22m net | Worst month |
|:--|--:|--:|--:|--:|--:|
| Stage18 alone | 18 | 3 | 1 | +13.8790% | −0.3012% |
| Stage20 alone | 18 | 3 | 1 | +11.2282% | −0.4928% |
| 48H Donchian alone | 12 | 10 | 0 | +16.9431% | −2.0034% |
| **50 / 20 / 30 combined** | **15** | **7** | **0** | **+14.4307%** | **−0.6706%** |
| 60 / 10 / 30 combined | 15 | 7 | 0 | +14.7015% | −0.6353% |
| 70 / 10 / 20 combined | 16 | 6 | 0 | +14.3549% | −0.4819% |
| 50 / 30 / 20 combined | 16 | 6 | 0 | +13.8164% | −0.5525% |
| 2025-only selected 90 / 5 / 5 | 17 | 5 | 0 | +13.9377% | −0.2342% |
| 83 / 5 / 12, **hindsight-only NOT VALIDATED** | 19 | 3 | 0 | +14.2001% | −0.3416% |

The 50/20/30 case has +7.5217% compounded model return for 2025 and +6.4257% during Jan–Oct 2026. Seven losing months: Jan, Sep, Dec 2025; Apr, Jul, Sep, Oct 2026. Approximate drawdown computed from monthly portfolio NAV only: 1.1311%, **not actual peak-to-trough intramonth drawdown**.

**22/22 is impossible for every constant nonnegative capital allocation among these three archived monthly histories**: September 2026 was negative for all three: Stage18 −0.1399%, Stage20 −0.4928%, 48H Donchian −1.6736%.

An additional grid search using only 2025 data, requiring at least 5% capital in each sleeve, chose 90% Stage18 / 5% Stage20 / 5% Donchian, which subsequently recorded only 6/10 profitable months in Jan–Oct 2026 (17/22 overall). The highest 19/22 result shown in this report uses hindsight over all 22 months: **NOT independently validated**.

## Limitations — do not call this a fully integrated 1m backtest

This run blends the **original separately executed 1-minute strategy studies' monthly results**; it does NOT perform synchronized 1-minute order fills, account equity, shared collateral, funding, position-level exposure or liquidation. Stage18 and Stage20 SHARE much of their core signal; positive weights to both represent overlapping economic risk and must not be misrepresented as independent trades. Their core returns are principally booked at exit month, while 48H Donchian is marked to market monthly, introducing month-boundary discrepancies. Rebalancing itself incurs no modeled costs. All 22 months have been historically researched; there is no pristine validation set.

**Verdict: reject this blended three-strategy portfolio as a 22/22 monthly-profit solution.** It worsens monthly consistency relative to Stage18 alone. For any live suitability decision, conduct a synchronized 1-minute shared-account backtest with deduplicated core strategy exposure and historically authentic fees, funding, margin and slippage. NO live trading, main branch, or unrelated schedules modified.

## Reproduce

Download the two Actions artifacts linked above, then:

```bash
python scripts/research_three_strategy_monthly_portfolio_20261121.py \
 --stage-artifact stage18-20-guardfree.zip \
 --donchian-artifact btc-48h-22month.zip \
 --out analysis/btc_three_strategy_portfolio_20261121
```

The script verifies 22 aligned months, produces the portfolio comparison and every monthly NAV return, and performs only 2025-based optimization before the 2026 recheck.
