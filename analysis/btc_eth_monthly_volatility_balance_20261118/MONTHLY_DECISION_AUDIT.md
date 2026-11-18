# Monthly-first decision audit — 2026-11-18

**Status: Does not meet alert conditions A, B, or C.** This is an experimental, historically inspected candidate screen, not a trading recommendation.

## Experiment
- Applied one NEW fixed, pre-entry-causal gate to 52 previously studied strategy families: last fully completed 1H log-return standard deviation (24 observations) divided by prior 168-hour standard deviation, shifted one complete hour, must be between 0.8 and 1.2.
- Replayed 205 identical strategy/stop/target settings on each of native BTCUSD and ETHUSD 1-minute histories, 22 IST months January 2025–October 2026. No instrument-specific hindsight parameter tuning.
- Risk 0.5% equity per stop, 3x notional cap; modeled taker 0.05% each side plus GST 18%, BTC adverse 5 points per side, ETH adverse 0.02% of price per side.
- 2025-only candidate selection, 2026 historical comparison. Full 2025 annual return and Jan–Oct 2026 YTD are separate columns in the all-model summary.

## Best monthly-consistency candidate (ETH 4H engulfing, 1.5 ATR stop, 3R target)
- 2025 full-year compounded net return **+9.33%**; 2026 Jan–Oct YTD **+4.52%**; 22-month net **+14.28%**.
- Aggregate after-cost profit factor **1.588**, 96 trades (48 wins / 48 losses), 16/22 profitable months; 9/22 months with PF >=1.5, positive net return and >=3 trades.
- **Zero** months earned +5% net account return, zero months +10%, zero months +20%; strongest month +2.96% (July 2025); worst month -2.91% (May 2025).
- Trade-close max drawdown -3.42%; intratrade max drawdown may be worse.
- Identical BTC rules: 2025 -0.07%, 2026 Jan–Oct -3.24%, aggregate PF 0.901, 10/22 profitable months, 107 trades.
- No full-year 2025 model among 410 market-specific configurations earned more than +500% net.
- Monthly PF is often based on just 2–7 trades; no independent forward holdout and no material monthly gains. Therefore this candidate does **not** merit a user notification as a convincing high-monthly-return edge or even a robust 'worth checking' discovery.

## Files
- `paired_all_model_summary.csv`: all 410 market/model summaries with 2025 and 2026 YTD returns and PF.
- `yearly_2025_and_ytd_2026.csv`: explicit 2025 >500% flags.
- `paired_all_model_monthly.csv`: every monthly PF, net equity return, trades, wins, losses for every model.
- `monthly_milestones.csv`: monthly PF >=1.5 and positive, PF >=1.5 and >=+5%, +10%, +20% counts.
- `candidate_monthly_22.csv`, `candidate_trade_ledgers.csv`: 2025-selected candidate monthly results and original sequential trade PnL ledgers.
- `quality.json`: data, fee, selection, execution and omitted-cost limitations.

## Limitations
January 2025 IST has a missing first 5.5 hours; verify complete BTC Oct 31 data repair before asserting fully covered October. November 2026 excluded. Funding, verified bid/ask spreads, market impact, discrete lot constraints and forced liquidation not modeled. Previous 2026 research exposure prevents a pristine independent OOS claim. Trade-close drawdown underestimates intratrade risk. No live trading systems or existing stages modified.
