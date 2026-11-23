# Critical duplicate-source correction — 2026-11-23 15:28 IST

**Decision: SKIP vaultik as NEW candidate.** The 13:29 and 14:28 audits mistakenly treated vaultik rolling-VWAP/RVOL staged exits as a pending novel strategy. This exact publisher source was already frozen and historically executed as **MR002** on 2026-11-21/22. Do not implement or launch it again as a distinct strategy. This correction is append-only; preserve earlier audits and original results.

## Identity proof
- Prior `analysis/mean_reversion_research/MR002/NOVELTY_CHECK.md` explicitly identifies **vaultik** commit `7f9bcd24d0e1cf7258699f4835ecd80dcb684a84`, `src/wfo.py`, `src/loader.py`, 5m rolling typical-price volume-weighted VWAP and weighted standard deviation over 288 bars, Z crossing back inside ±3, prior-bar RVOL >=2.5, 50% TP1 at 1 SD, remaining VWAP TP2, stop buffer 1 SD and 4h timeout.
- Recent 13:29 audit identifies precisely the same source, commit, features, staged exits and 12-combination publisher grid. It is NOT a new candidate.
- Original executable: https://github.com/vaultik/algo-trading-system/blob/7f9bcd24d0e1cf7258699f4835ecd80dcb684a84/src/wfo.py (blob 1adc9d2e41ac9fb7f854dfa6a5ed145ee142d95e).
- Feature executable: https://github.com/vaultik/algo-trading-system/blob/7f9bcd24d0e1cf7258699f4835ecd80dcb684a84/src/loader.py (blob b967e2816355d5b5f2b99cfa8fac94bc253fdc0d). `Typical_Price=(High+Low+Close)/3`, `VWAP=sum(TP*Volume)/sum(Volume)`, `SD=sqrt(max(sum(TP²*Volume)/sum(Volume)-VWAP²,0))`, `RVOL=Volume/rolling_mean(Volume)`. For 5m bars, window 288; publisher uses min_periods=1 (BTC reproduction must disclose warmup choice).
- This means the purported 'missing preprocessing' is recovered, but the historical candidate is already rejected. Its publisher's optimistic TP-first, entry-bar blindness and stop-gap fills were previously identified and the MR002 corrected historical run is the relevant evidence, not a new baseline.

## Actual prior historical result, not publisher performance
MR002 Actions successful run https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44911975169 ; artifact 14709852576. Previous independently parsed 204 trades, 22 IST monthly NAV records, +6/-16 months, compound NAV **-30.5503268%**, max minute-close DD **33.5514%**. Monthly records do not imply complete minute coverage; October 2026 has documented 1,440 missing UTC bars. Account NAV reconciled in earlier audit. **Reject source mechanism as profitable at frozen baseline.** Do not relabel the same source as MR004 or optimize its 12 grid on 2026.

## Novelty and execution gate
Compared `codex/STRATEGY_NOVELTY_GATE.md`, `analysis/mean_reversion_research/MR002/NOVELTY_CHECK.md`, `analysis/mean_reversion_research/MR003/NOVELTY_CHECK.md`, and Stage19 report. MR003 is a different Keltner fade; it also failed (run 45036174691). The current branch's Actions runs collection has 8 entries and latest completed run MR003, not a newer vaultik replay.

## Session outcome
One **critical novelty correction** and recovered exact pinned indicator formulas; **0 new distinct backtests, 0 variants, 0 new workflow runs**. The repeated vaultik discovery is a research-process failure, not a new profitability opportunity. Next session must source a genuinely different bounded-risk mean-reversion candidate (e.g. distributional RSI standardized against its own history, conditional on novelty/license) and run actual Delta BTC 1m replay only after pre-run novelty clearance. Do not modify main/master, other family branches, schedules, VPS, or trading accounts.
