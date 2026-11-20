# Hourly path-efficiency run verification — 2026-11-20 13:15 IST

Study branch: research/independent-path-efficiency-20261120-v1
Source/workflow SHA: 0934a86dc2d8d9426d00fa4d12d8351c3e01e898
Workflow: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44682789117
Run ID 44682789117; event push; status completed; conclusion success; created 2026-11-20T05:42:19Z; completed 05:42:57Z.
Job 136109919732 completed success, including Python replay and artifact upload.
Artifact 14605132432, path-efficiency-v1-ledgers, 10228 bytes, sha256:23cb42eabe3dde6a1c7702bf085af9ff61189d31f5819b0d68766c815767f581, expiry 2027-02-18.

AUDIT STATUS: INCONCLUSIVE / OUTPUT NOT YET INDEPENDENTLY READ.
GitHub connector exposes artifact metadata but not ZIP bytes; GitHub fetch rejects job logs endpoint (HTTP 400 disallowed endpoint), and container curl could not reach artifact endpoint (HTTP 000). Thus do not assert net PnL, PF, 22-month NAV or a research target. Preserve this same study until raw CSVs are read and reconciled. Exact next step: retrieve artifact via authenticated GitHub Actions API (GET /repos/rajkumar0rk/BTC-Analysis/actions/artifacts/14605132432/zip), or persist its reports on THIS branch using a dedicated workflow step; then inspect selected BTC-2025/2026 and ETH monthly rows, trades, drawdown and cost sensitivity.

CODE AUDIT FINDINGS: the original code uses BTC $5/side and ETH 0.02%/side, whereas the new highest-priority cost sequence requires ZERO slippage screening then BTC $0.5 and $5/side stress only on a screen PASS. Original code also does not model funding, actual spread, margin/liquidation, or lot rounding. Do not label its successful job as fully executable net. A revised staged run must preserve original baseline artifact and trade logic and change only explicitly preregistered cost model; do not select on 2026/ETH.

No live execution, main branch, or other schedules touched.
