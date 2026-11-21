# Breakout & Range — fourth research iteration, 2026-11-21 IST

## Execution status
SOURCE AUDIT AND PRIOR-ART COMPARISON COMPLETED; NO NEW HISTORICAL BACKTEST EXECUTED. No BTC/ETH profitability result. No live changes.

## Verified repository policy and evidence
- Read main `codex/AGENTS.md`, `codex/STRATEGY_NOVELTY_GATE.md`, `codex/DATA_CONVENTIONS.md`, `codex/RESEARCH_CONTEXT.md`.
- Read `analysis/institutional_discovery_stage24_structure_monthly10/RESEARCH_REPORT.md` on `research/stage24-monthly10`: 1,920 tested configurations, none achieved >=10% net in every one of 22 IST months; closest mechanisms include 15m breakout, retest and squeeze with 1m stop-first.
- Read `analysis/independent_stage25_hourly_trend/RESEARCH_REPORT.md` on `research/stage25-new-trend`: 2,880 configurations, none met all-month target; includes hourly inside-bar/Donchian and 1m execution.
- Main's `codex/DATA_CONVENTIONS.md` describes only 61,206 original **5m** bars with unverified exchange and timestamps, approximately 2025-12-31 to 2026-08-01. This cannot be relabeled as authenticated Delta India BTC 1m data. Stage24/25 reports assert Delta India 1m data on their respective branches, but the actual minute archive manifest/hash and October missing-minute handling must be recovered before new execution. Novelty gate says October 2026 missing 1,440 UTC minutes.

## Newly discovered public executable research sources (NOT independently validated BTC results)
1. https://github.com/BatuhanGen/breakout-backtest-tool — author BatuhanGen, time-anchored range breakout with long/short and inverse modes; entry alternatives: immediate market, retest at boundary, and equilibrium at range midpoint; stop based on range or breakout bar; fixed R targets, break-even/trailing and selectable same-bar fill ordering. Useful **execution comparator**, not a validated BTC edge. Novelty: its ordinary range breakout/retest overlaps Stage24; midpoint equilibrium entry may be a differential execution hypothesis but cannot be approved without checking Stage19/23 and existing daily failed-breakout scripts.
2. https://github.com/sam-bateman/trading-orb — US equities 09:30–09:50 America/New_York opening range, entry 10:00–11:30 on volume-confirmed break, forced flat 15:50. Author claims 10 years of positive annual results, but these are not Delta BTC returns and require independent verification. Distinct equity-market opening auction mechanism does not directly transfer to 24/7 BTC; treat only as session anchoring/relative-volume hypothesis.
3. https://github.com/algotrade-education/Group09-BuyHighSellLow — 20m session opening range, 15m bars, 0.5x ATR breakout buffer, range viability 0.5–3 ATR, volume > 0.5x 20-bar mean, ADX >20, range-based stop, 3 ATR TP. Ordinary ORB/volatility filters overlap prior intraday research; do not run until novelty gate compares exact prior rules.
4. https://github.com/SC4RECOIN/simple-crypto-breakout-strategy — cryptocurrency previous-day-range breakout (Larry Williams-type), end-of-day exit. Author-reported ETH-PERP 2020 backtest: 113 trades, +304.713% strategy return versus +471.245% buy/hold, max DD -7.230% versus -61.446% benchmark; source-market/time/cost assumptions unverified. Standard prior-day breakout likely overlaps prior day-level studies, so no reproduction authorized yet.

## Candidate differential hypothesis for next iteration (NOT approved yet)
A *causally formed failed-breakout acceptance* event around a fixed New York session-anchored opening range, distinguishing a **failed excursion and confirmed return inside** from a generic breakout entry. Do not implement until full Stage19/23 and independent `research/daily-failed-breakout-20261119` code comparison proves the economic signal differs. If overlap, mark SKIP and select a new source. Source-faithful reproduction must use a published strategy with complete exact rules rather than inventing missing conditions.

## Blockers and exact next steps
1. Read the existing daily failed-breakout source and Stage19/23 signal code, decide DUPLICATE / PARTIAL / NEW. Do not mistake a renamed reversal for novelty.
2. Identify authenticated Delta BTCUSD 1m dataset path, coverage report, hash and time-label conventions from an existing completed workflow/branch; ensure actual runner access. Recover missing October 2026 1,440-minute UTC gap or mark incomplete month.
3. Select one source with fully specified executable entry/exit/risk rules, license and pinned commit. Commit required separate NOVELTY_CHECK.md with deterministic rules, data and baseline before starting workflow.
4. Launch actual BTC2025 zero-slippage 1m replay, next-open fills, stop-first ambiguous bars, 0.05% each side and 18% GST, funding unmodeled. Preserve full ledger and monthly NAV. Freeze selected rules before BTC2026 and ETH.

No claims of completed backtest, PF or profitable strategy. No protected branch, other schedule or live account touched.
