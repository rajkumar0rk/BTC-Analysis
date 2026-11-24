# Frozen BTCUSD EMA20 Reclaim V6 — forward and execution validation protocol

Status: research candidate only; no production deployment, no order authority.

## Reproducibility and data boundary
- Frozen rules: commit ada8aae8dac5f8c971ac16e3f2f23c242f05232b (2026-11-24 05:05:22 UTC).
- Historical optimization/acceptance: Jan 2025–Oct 2026; all seven days; 0.001 BTC fixed quantity; $100 starting equity.
- November through 2026-11-22 23:59 UTC was inspected before the freeze and cannot be an untouched holdout.
- Start new forward evaluation at 2026-11-25 00:00 UTC. Only accept entries whose completed signal hour starts on or after this timestamp. Warmup from earlier history is allowed, but no carried historical trade.
- Record all signals, skipped opportunities, attempted fills, stop/target updates, fees, funding and mark prices. No rule or parameter edits while evaluating this version.
- Report every calendar month, including losing and zero-trade months. Partial month not accepted as a full-month pass.
- First review after at least 90 days and at least 30 closed trades; if insufficient trades continue observation, without retroactively changing the period. Neither threshold is proof of future profitability.

## Execution validation (no real orders authorized)
1. Read-only public data: timestamped trades, best bid/ask and order-book depth, mark, funding and feed reconnects. Compare timestamps to UTC clock.
2. Paper mode: replay bid/ask and actual arrival time; log exchange product filters, lot rounding and assumed order queue/latency. Reject stale feed, duplicate signals, missing candles; stops and targets must never be inferred from future candles.
3. Demo exchange order mode, only after explicit deployment authorization: use separate demo credentials and account; one open position; compare intended order to accepted order, fills, partial fills, cancel/replace, stop trigger and actual exchange position. Record reject/timeout/reconnect behavior and reconcile exchange ledger. No production keys or order submission in CI.
4. Funding: match actual authenticated wallet funding records to product, open-position snapshots and schedule; record exact timestamp, amount and settlement currency. Historical hypothetical trades have no actual wallet records.
5. Liquidation: use account margin mode, tier history, allocated margin, mark price, fees, funding and other positions. Present-day product parameters alone cannot certify historical exchange liquidation outcomes.
6. Production trading is a separate authorization and risk decision; no auto-enable.

## Evidence
- Historical independent V6 replay: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45330829397
- Frozen validation implementation: .github/workflows/reclaim-v6-independent-validation-20261124.yml
- Combined scenarios: .github/workflows/reclaim-v6-extended-validation-20261124.yml
- Historical funding schedule proxy: .github/workflows/reclaim-v6-historical-funding-20261124.yml

Do not label combined stress, settlement reconciliation, out-of-sample or live execution as passed until actual results support the claim.
