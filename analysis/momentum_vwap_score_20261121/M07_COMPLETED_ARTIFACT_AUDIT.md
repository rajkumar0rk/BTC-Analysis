# M07 — completed M05 artifact audit (2026-11-21)

Source: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44891458609 ; artifact 14702470583. Audit of completed historical replay, NOT a new replay. Immutable baseline preserved.

## BTC2025 realized trade reconciliation
- 525,600 Delta 1m bars; 86 4h entry signals; 24 actual round trips.
- Winners 8, losers 16; win rate 33.33%; realized PF 0.9394307568; net USD -172.9450357363 on USD 10,000 starting NAV, return -1.7294503574%.
- Mean duration 65.0049 hours; median 56 hours; 48 executed order sides.
- ATR stops: 2 trades, combined net -USD 874.047837; momentum exits: 22 trades, combined net +USD 701.102801. The two stops outweigh the profits from the other exits. Descriptive only: removing protective stops would be an unsafe and biased inference.
- Zero assumed slippage; 0.05% trading fee per side and 18% GST on fees. Funding, spread and L2 impact unmodeled.

## IST calendar audit: concrete bug
M05 monthly_nav.csv contains 13 month labels despite only 12 UTC months supplied. Last 2025-12-31 23:59 UTC candle is 2026-01-01 05:29 IST and creates a spurious 2026-01 zero-return row. The 2025-12 snapshot is at 2025-12-31 23:59 IST, not the 2025 UTC archive end. Complete 2025 IST calendar year requires 2024-12-31 18:30 UTC through 2025-12-31 18:29 UTC plus signal warmup; 2024 warmup was not loaded. Do not treat January 2025 as fully warmed or January 2026 as tested.

Original monthly artifact values: Jan -7.8624%; Feb -1.6850%; Mar -1.1469%; Apr +3.7694%; May +5.5199%; Jun -2.8010%; Jul +0.8859%; Aug -1.0520%; Sep +1.5806%; Oct +1.6864%; Nov 0%; Dec 0%; spurious Jan 2026 0%. Five positive and five negative months in Jan-Oct. Calendar endpoint/coverage caveats remain.

## Decision
REJECT original M05 as positive momentum edge. Do not remove ATR stops based on their negative contributions. Next runnable M08 must correct IST year boundaries, warmup, full NAV mark-to-market, and source Pine parity; only then consider a small pre-registered source-defensible variation or move to a distinct mechanism. No live trading, main branch, or other families changed.
