# External convex screening — 2026-11-20 12:42 IST

Status: BLOCKED / NO NEW BACKTEST EXECUTED. This is not a successful or profitable test.

## Prior state
Previous bipower-jump experiment was reported as completed in GitHub Actions run 44679516754, zero BTC closed trades and one ETH loss. No outstanding job from that experiment is known from prior audit. No new run is claimed.

## Public source discovery (actually accessed this iteration)
- https://github.com/EstebanSP23/crypto_systematic_research — public README, MIT license shown; Quattro Donchian 20-bar 4H breakout with rising daily EMA200, four-unit pyramid at +0.5N, 2 ATR trailing and 5% catastrophe stop. Author EstebanSP23. Published +1107% Jan 2022–May 2026 is third-party self-report, NOT independently validated on Delta. README explicitly assumes zero slippage and excludes funding. Exact source SHA, implementation-specific signal timing, fill details and full license attribution must be captured before reproducing.
- https://github.com/aurelien-gentile/turtle-strategy-backtest — author aurelien-gentile; hourly long-only Donchian breakout, opposite-channel exit, 2 ATR stop, 1% equity risk unit and optional pyramiding. Its README reports none of 343 configurations beating buy-and-hold mid-2023–early 2024. No LICENSE visible in root listing, so no source-code copying authorized without checking rights.
- Existing repository novelty gate: codex/STRATEGY_NOVELTY_GATE.md (main, blob 87215853264cfbfd928421152e752ce106a685a7), identifies numerous trend/breakout and 1H strategies. Quattro and Turtle are PARTIAL OVERLAP, not automatically NEW. Need exact source-to-prior rule comparison before launching.

## New cost-sequence contract
First genuine BTC 2025 screening: zero entry and exit slippage; taker 0.05% each side plus GST 18% on commissions; funding UNMODELED. No slippage stress unless a genuinely positive screening result. Then frozen BTC $0.5/side, $5/side, and optional bps stress. Preserve full 22-month IST ledger, original trades, NAV, gaps and risk accounting.

## Blocker and next action
No source-level exact Quattro implementation or commit SHA was verified in this iteration, and its apparent core thesis overlaps existing breakout tests. Launching a purported rule-for-rule test now would risk inventing missing execution rules or duplicating earlier research. NEXT: retrieve the third-party source module, exact commit/license and closest prior breakout scripts; determine whether Quattro's four-unit pyramid + daily regime gate creates a defensible differential. If approved, implement an isolated native Python reproduction, create a branch-scoped push workflow, verify run ID, audit zero-slippage BTC screen before any stress. Do not execute third-party scripts, touch main or trade live.

This ledger records a genuine reproducibility/novelty blocker, not a market-data failure or a profitable finding.
