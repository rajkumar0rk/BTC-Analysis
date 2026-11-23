# Novelty check — Scalper Offer cost-model differential

**Decision:** PARTIAL OVERLAP — approved incremental execution-cost and 29-minute exit test, not a novel alpha hypothesis.

## Existing runs
- \`scripts/research_ema9_21_daily_quality_1m.py\`, GitHub Actions #45157193892: 343 weekday-only entries; standard taker fee on both legs.
- \`scripts/research_ema9_21_quality_upgrade.py\`, Actions #45158129266: 32 EMA9/21 1-minute entry/exit combinations; all after standard double-sided fee.
- \`scripts/research_ema9_21_htf_regime.py\`, Actions #45158528677: 12 1-hour/4-hour regime strategies with standard double-sided fees.
- Historical 5m EMA and 1m exit research in Stage23 and Stage4 already exists. No entry or feature optimization here.

## Differential hypothesis
Delta Exchange India's **regular Scalper Offer** charges 0% **closing** trading fee on BTCUSD Futures closed within 30 minutes, if the customer had opted in before placing the trade. For the historical counterfactual, reprice all trades with standard 0.05% taker **opening** fee plus 18% GST; if exit >30m after entry, the same standard 0.05% + GST applies on exit. Keep historical gross fills, positions, stop, TP, 5-point slippage per side, and 10% notional exposure identical.

The date of this offer's real-world availability and personal activation is not established for every 2025-26 trade, so applying today's 30m terms to the full archive is *hypothetical*, not historical realized performance. **Do not include Diwali fee-voucher cashback** or pretend that opening fees are waived.

## Pre-registered checks
1. Reprice old weekday 1m quality baseline (343 trades) using exact 1m entry/exit time columns.
2. Reprice every one of the 32 fixed quality variants, and every one of the 12 fixed higher-timeframe variants, with the same offers. Select using the 2025 results **only**, report all 2026 historical rechecks separately.
3. Additional 29-minute **hard exit** sensitivity (guaranteed before 30-minute deadline on 1-minute OHLC, if the next bar opens at 29 minutes) for just the 2025-selected member of each of the 32 and 12 variant groups; do not optimize that exit based on 2026.
4. Report 22-month full monthly account returns, totals, win/loss, profit factor, max closed-trade drawdown, qualifying trade count and total waived fees, fee savings. Non-eligible positions pay BOTH fees.
5. Data quality: 2025-01 to 2026-10 complete UTC archive per current 2026-11-22 1m manifest; original studies have full continuous data. Do not enter weekend IST, maximum one trade per IST weekday; stop-first 1-minute execution; no multiple entries/day or lookahead. Funding and real maker/taker fill status/real spread not modeled.
