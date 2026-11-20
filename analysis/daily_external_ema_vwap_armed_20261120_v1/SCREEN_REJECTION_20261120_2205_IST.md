# BTC 2025 EMA/VWAP zero-slippage screen decision — 2026-11-20 22:05 IST

Task: Independent Daily-Profit Strategy Hunt. Isolated branch only.

Latest task-specific GitHub Actions run: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44735227357
Run 44735227357, job 136284807263, completed SUCCESS, source SHA cd5aa9d4b112d96f3fbb3696ba3b7f95764c8679. Job logs explicitly print the economic screening summary. Artifact ID 14628028243 (four BTC2025 files); raw artifact still requires separate binary reconciliation.

Original external source reported in job: xenoxavier/freqtrade-ema-vwap EmaVwapLong; source commit UNPINNED (provenance limitation). Cross-task EMA/VWAP novelty collision previously documented with research/btc-first-external-ema-vwap-stage36-20261120; other branch read-only.

Screen BTCUSD, IST 2025, zero modeled slippage BOTH sides, normal commissions and GST:
- 172 closed trades
- final closed NAV 0.9928803877925363 (starting 1.0; -0.71196122074637%)
- realized net PF 0.9352362277814735
- mean net trade -0.00004139309422944127 NAV units
- profitable 96 days, losing 135 days, flat 134 days, unavailable 0 (365 total)
- maximum daily NAV drawdown -0.020841829724546956
- commission 0.017027211884926986 NAV units, GST 0.003064898139286858, modeled slippage 0
- funding UNMODELED, spread UNMODELED; market impact, margin and rounding not independently evidenced.

Decision: REJECT at stage-1 screen due to negative after-commission-and-GST expectancy and PF below 1. No 0.5/5-point stress, BTC 2026 or ETH runs authorized for this failed screen. This is not a claim of fully after-cost executable loss; missing costs could worsen performance. Green CI means code ran, not profitable. The raw artifact and monthly NAV remain un-reconciled; no 22-month results claimed.

Next available candidate cycle: discover a materially distinct third-party executable economic strategy from public GitHub/TradingView/academic/Freqtrade, pin source commit/license/rules and check novelty before implementing a new BTC2025 zero-slippage screen on a NEW isolated branch. Do not retune this rejected mechanism, modify other tasks or main, or place live orders.
