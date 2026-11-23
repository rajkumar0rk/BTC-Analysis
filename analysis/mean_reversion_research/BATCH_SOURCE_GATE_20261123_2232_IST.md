# Mean reversion source gate — 2026-11-23 22:32 IST

Scope: isolated source research only; no historical replay launched or completed. Existing branch Actions list checked: 8 runs; newest completed success 45036174691 at commit 1656866d6234032a6d19d3a2bc1692807667efcd (MR003, previously rejected). No newer workflow result.

Read codex/AGENTS.md, codex/STRATEGY_NOVELTY_GATE.md and codex/FINDINGS_INDEX.md. The novelty gate requires an independent signal and a pre-run NOVELTY_CHECK before execution; October 2026 has 1440 missing UTC minutes.

## Newly screened pinned source A — FinCell session VWAP deviation
- Source: https://github.com/fincell-xaviers/vwap-intraday-strategy/blob/2b042aa189a4d7b40ce552e096653ea42721404f/main.py
- Creator: FinCell Quants, authors Vedanth Teckchandani and Shaun Joseph; source SHA 2b042aa189a4d7b40ce552e096653ea42721404f; license file absent from root; status UNKNOWN.
- Original market: RELIANCE.NS intraday hourly Yahoo data, or synthetic fallback. Synthetic fallback is automatic and silently changes data provenance; results are not authentic BTC or even guaranteed authentic RELIANCE.
- Signals: session VWAP from cumulative typical-price*volume / cumulative volume; 'VWAPStd' from cumulative [typical price * (typical price - current VWAP)^2] / cumulative volume (NOT conventional volume-weighted variance); long close below VWAP -1.5std; short above VWAP +1.5std; position shifted one bar; no explicit stop, target, timeout, sizing, or exchange fees. Position returns are shifted log close-to-close, not a trade/fill ledger. No trustworthy trade count/PF/return/DD published in inspected executable.
- Structural failure: zero downside cap, unconventional variance, synthetic fallback, no causal stop-first intrabar execution. Decision NOT ELIGIBLE for source-faithful bounded-risk replay. Adding a stop would be a separate derivative, not the original baseline. Mechanism partially overlaps session VWAP E14 previously screened; skip.

## Newly screened pinned source B — dorian68 regime Z-score
- Source: https://github.com/dorian68/TradingStrat_mean_reversion/blob/761226816fa7484966fe8fdf6b06b2638d6f7ebf/Cls_Strategy.py
- Backtester: https://github.com/dorian68/TradingStrat_mean_reversion/blob/761226816fa7484966fe8fdf6b06b2638d6f7ebf/backtest.py
- Creator: dorian68; SHA 761226816fa7484966fe8fdf6b06b2638d6f7ebf; license not established from root listing.
- Baseline Strategy: SMA14, long deviation below -0.2%, short above +0.2%, no regime restriction. V2: rolling zscore 30, entry 2.0, exit 0.7, EMA10/50 trend strength threshold 1%, RSI14 extremes 25/65, ATR14 0.1%-4% range, cooldown 4, max hold 144; **trend_follow defaults TRUE** and explicitly opens directional trend positions in high-trend regime. Those trades belong to momentum/trend family, not exclusive mean reversion.
- Backtester default next-bar open signal, 2bps fee each side and 1bps slippage each side, 2% stop/4% TP, 1% risk per trade, max 1x leverage. Inspected code evaluates stop/TP using high/low after opening; exact gap fill and same-minute collision logic still require audit before any reproduction. No verified original period/trade count/PF/return/DD from inspected code.
- Decision PARTIAL OVERLAP / HOLD: cannot label V2 as a pure mean-reversion baseline while trend_follow=True. A trend_follow=False derivative requires separate immutable settings and novelty comparison to previous z-score and Bollinger mechanisms; license unresolved.

## Existing research and fee gates
MR002: 204 trades, 6 positive / 16 negative months, -30.5503268% compound NAV, 33.5514% minute-close DD; completed run https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44911975169, artifact 14709852576.
MR003: 6550 trades, PF 0.534, -99.92% NAV; completed run https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45036174691.
Research assumed fees 0.05% notional per side and GST 18% on fees = 0.118% round trip before slippage/funding. No newly verified BTC P&L, trade ledger, or monthly NAV this session.

## Handoff
Do not retry MR002, MR003, simple RSI/BB, or rename an existing VWAP mechanism. Source-gate materially different licensed mechanisms with bounded stop, and write NOVELTY_CHECK before any new historical workflow. Reuse archived BTC1m runner, 2025-only selection, stop-first next-open and actual Actions artifact reconciliation. Do not claim October 2026 fully verified.