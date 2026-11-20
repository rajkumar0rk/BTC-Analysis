# BTC 2025 KeltnerBounceV1 screening decision — 2026-11-20

Status: **REJECT / INSUFFICIENT TRADE SAMPLE**. This is a zero-slippage, commission-and-GST-only screen, not an executable after-all-cost profit claim.

Verified GitHub Actions run: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44710028523 (completed success); job 136199080130; workflow source SHA 14a52d33974b9aab90eb52d07a242f384152d540; original third-party source IvPalmer/Master-Trader KeltnerBounceV1 commit b8dc9a00a2bc77a50bc505cf0b9976c16c9d1771.
Original artifact: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44710028523/artifacts/14616876828 ; artifact SHA256 68d0d5beed1a043608061b4eaef05832847496f8015ec5ee916d3edbf9410b64. Artifact contains original BTC2025_trades.csv, BTC2025_daily_nav.csv, BTC2025_monthly.csv, BTC2025_summary.json.

Reported screen (2025 IST): 3 closed trades; closed NAV 1.0096697737249019 (+0.96698%); mean trade account NAV increment 0.003223257908300601; no losing closed trades, so PF is **Infinity with a 3-trade warning**, not N/A and not evidence of robustness. 6 profitable days, 1 losing day, 358 flat days; 0 unavailable days per the script's daily-close coverage indicator; daily NAV drawdown -0.1597%; commission 0.0003061809307722595 and GST 0.000055112567539006714 in NAV units; zero slippage. Funding, spread, impact, margin and contract rounding not validated. No stress test is warranted because only 3 trades occurred; no 2026/ETH validation and no claim of daily profitability.

Code audit caveats: hourly signal is based on a completed candle and entry at next hour; code contains 1m stop-first checking. The script's zero-slippage fills can be optimistic and the 'gap_forced' exit references prior close. Daily returns are marked at IST day end and do not establish complete minute-level coverage; the script's monthly compounded returns can be null when a daily return is missing. Three wins make the sample too small to establish net expectancy; do not optimize filters to manufacture more trades or run slippage stress. Preserve original artifact and reject this exact candidate. Next cycle: search public external sources first, novelty-check read-only repository, then launch a different reproducible BTC-2025 zero-slippage screen with fees and GST.

No other branches, automations, main, or live accounts changed.
