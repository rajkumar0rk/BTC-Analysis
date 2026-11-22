# Mean Reversion batch triage — 2026-11-22 13:30 IST

Status: SOURCE TRIAGE ONLY; no new historical replay; no profitability claim.

## Verified recovery
- Branch-specific Actions GET /repos/rajkumar0rk/BTC-Analysis/actions/runs?branch=research/mean-reversion-bb-rsi-source-audit-20261121&per_page=30 returned three runs. Latest 44911975169: completed/success, SHA 0932ae131853e7fb26c6c164870bc4ae5d50adea, 2026-11-21T14:03:51Z. Earlier 44906433526 failed; 44901636602 succeeded.
- Prior MR002 artifact 14709852576 already independently verified in cross-session handoff: 204 trades, -30.5503268% NAV, 33.5514% max minute-close drawdown, six positive / sixteen negative IST months. Do not count it as new.
- Important duplicate discovery: vaultik/algo-trading-system at immutable commit 7f9bcd24d0e1cf7258699f4835ecd80dcb684a84 IS ALREADY MR002's source. Its rolling 5m VWAP z-score crossback / RVOL 2.5 / 3-sigma / 4-sigma stop / partial targets mechanism was already replayed. Decision DUPLICATE / REJECT; do not relaunch or relabel as MR004.

## Additional source screening
1. zevrichards/freqtrade-strategies MeanReversion.py and regime_filter.py: 4h BB20 lower band, RSI14<32, volume SMA20, ADX12..25, EMA200 proximity, RANGING regime, ROI ladder, -5% stop. Prior MR003_SOURCE_RECON_20261121_2131_IST.md contains recovered rules and original multi-pair publisher negative result. Core BB/RSI oversold is partial overlap with MR001 and Stage19/23; no distinct mechanism established. Upstream immutable commit and license unresolved. Decision SKIP until novel economic difference is demonstrated.
2. ojeology/mean-reversion-vwap-lab commit 5ae2853d729b6761d4be3c2ccb7602beb32665cf: session VWAP ±2SD + RSI + ATR candle confirmation, next-minute entry; publisher reports PF 2.01 in-sample on smaller coins, not BTC. Stop/target both hit same minute is target-first in inspected source, requiring conservative stop-first sensitivity. License unverified. Session-reset VWAP vs MR002 rolling VWAP is a potentially distinct anchor, but source permission, novelty and causal execution unresolved. Decision HOLD / NOT APPROVED.
3. GitHub code discovery queries for anchored VWAP, zscore and liquidity sweeps surfaced documentation or unrelated bot examples, not a verified licensed, source-faithful new baseline. Do not manufacture signals.

## Research economics and blockers
Taker research cost = 0.05% each side x 1.18 GST = 0.118% of round-trip notional, i.e. 11.8 bps before funding/spread. A short-horizon edge must exceed this just to break even. MR002 fails this criterion empirically.
No new branch run, code fix or historical artifact was produced this iteration. No newly tested strategies, no parameter variants, no new positive result.
Next actionable work: identify a license-cleared, source-defined DIFFERENT mean-reversion mechanism, compare exact Stage19/23/24 rules, commit pre-run novelty decision, implement source-faithful next-minute/stop-first replay in the existing genuine Delta BTC 1m runner, and verify a completed Actions run plus trade/monthly NAV artifacts. Do not repeat MR002 or claim the session VWAP lead is proven.
