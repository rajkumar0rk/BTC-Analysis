# Stage31 final decision — 2026-11-20 IST

**REJECT — completed paired research, not profitable.**

Workflow https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44605726717 ; source SHA 04abbc3b362637ea02bf4fb256955f7d17ec6693 ; job 135848772488.

Job failed only at final commit-results step. Backtest and upload succeeded. Original evidence: GitHub Actions artifact 14569702420 (stage31-paired-ledgers), digest sha256:0487b149e55d5c593677fdd46c8847c165bbe3df5c7a6f7de0dd5e0ccb0bb7c1. Includes all_22_months.csv, summary.csv, original_trade_ledger.csv.gz, quality.json, RESEARCH_REPORT.md.

BTC base: 455 trades (132 wins, 323 losses), 5/22 profitable months, 17 losing, median month -1.3154%, worst -7.4942%, PF 0.79085, full-year 2025 -10.5495%, Jan-Oct 2026 YTD -25.4450%, compounded 22 months -33.3102%, max modeled drawdown 35.8111%. Only one >=5% month, zero >=10% or >=20%. Worse costs: 4/22 positive, -35.9460% compounded, 38.2360% drawdown.

ETH unchanged-rule secondary: 414 trades (126 wins, 288 losses), 7/22 positive, PF 0.92194, 2025 +2.8516%, 2026 Jan-Oct YTD -15.3852%, compounded -12.9723%, max modeled drawdown 22.1065%. Worse costs: 6/22 positive and -18.1202%. ETH not used for selection.

Independent artifact audit: four series of exactly 22 monthly rows; trade counts match original closed-trade ledger; each monthly starting NAV equals preceding ending NAV; recomputed after-cost overall PF and compounded NAV match summary. Source marks open trades at month-end using last available candle and estimated exit cost. Pre-entry completed-hour signal, next-minute execution; risk 0.5%/trade, max leverage 3x, 1.5 ATR stop, 3R target, 24h timeout.

Limitations: January 2025 first 5.5 IST hours absent; funding, historical spreads/impact, contract minima, maintenance liquidation and tick-level fills not validated. Drawdown estimate not a liquidation simulation.

Falsified BTC hypothesis: insufficient positive months and PF below one in 2025 and overall. Do not optimize this rejected mechanism on 2026 or ETH. Next iteration may test a distinct mechanism after novelty check. Keep original artifact immutable.

Operational issue: final commit-results step failed after artifact upload; no need to rerun rejected study for cosmetic green status. Future workflows should retain unconditional artifact upload and make branch commit optional/robust. No changes to main, other tasks or live trading.