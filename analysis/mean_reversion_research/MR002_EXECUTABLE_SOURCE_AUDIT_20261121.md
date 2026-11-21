# MR-002 — pinned executable-source audit (2026-11-21)

Status: SOURCE EXECUTION AUDIT COMPLETE; NOT BACKTESTED; novelty versus Stage19/23/24 still pending. No profit claim.

## Immutable third-party provenance
- Creator: George Vasilev (vaultik); repository https://github.com/vaultik/algo-trading-system
- Pinned original commit: `7f9bcd24d0e1cf7258699f4835ecd80dcb684a84` (2026-05-06). Executable: `src/wfo.py` at this commit, `src/loader.py` for indicator calculations.
- License: MIT, copyright 2026 George Vasilev, from repository LICENSE. Retain notice if adapting code.
- Original: Bybit cryptocurrency 5m, currently configured DOGE/LTC/RENDER/TON/SUI/CRV/AAVE/FET, **not BTC**. No publisher BTC performance claim.
- WFO: 5 windows, 2023-01 to 2026-06; fixed z=3, previous-bar RVOL >=2.5, stop buffers 0.5/1/1.5 SD, time stops 2/4/8/12h; leverage=3, commission=0.0004 each side; optimizer requires at least 5 train and 5 test trades. WFO sums test-window PnL percentages, not a single continuous account NAV.

## Source-faithful signal and actual control flow
- Rolling 24h VWAP and SD; `z=(close-VWAP)/SD`.
- At bar `i`, long signal when `z[i-1]<-3` and `z[i]>=-3`; short when `z[i-1]>3` and `z[i]<=3`. Signal also requires `RVOL[i-1]>=2.5`. Only flat position can signal.
- `pending_signal` enters at the NEXT 5m bar open; saved signal-bar VWAP/SD set fixed stop and targets.
- Long stop = saved VWAP - (3+buffer)*saved SD; TP1 = saved VWAP - saved SD; TP2 = saved VWAP. Short symmetric. Fallback target adjustment if entry gaps past target. Exit after 2/4/8/12h.
- Source implementation has a critical execution ambiguity: on an already-open position it checks TP1 **before** stop within the SAME 5m OHLC bar, books half the position as profit, then moves remaining stop to breakeven and may book the remaining stop even if the true intrabar path hit the original stop first. This is path-optimistic, not a reproducible fill sequence. Correct Delta 1m replay must conservatively check initial stop first when both stop and TP1 are touched within a 1m candle, and gap stops at worse open. Record original behavior separately as publisher baseline and conservative correction as sensitivity.
- Further source caveat: the newly entered position is not managed for stop/TP during the entry bar (the `if in_position == 0` branch enters, but the `elif in_position == 1/-1` branches cannot run until next iteration). A live position can be stopped on the entry bar. The Delta 1m execution must monitor from the actual entry minute.
- Source `calc_metrics` treats each partial fill as a separate compounded return, even though the two halves belong to one position. Its reported trade count, Sharpe, NAV and max DD are not account-level statistics. Source uses a simplified 2x round-trip fee per partial leg and does not implement actual per-order fees, GST, funding, spread, or liquidation.
- Signal RVOL uses the *previous* 5m bar, not signal bar. Do not silently change this. Verify `loader.py` formula for SD and RVOL before implementing a faithful candidate.

## Novelty and disproof gate
This is a 24h volume-weighted equilibrium crossback with prior-bar relative-volume exhaustion and partial target, distinct from plain BB/RSI fade but potentially overlapping existing Stage19/23/24 failed-auction/reversion implementations. Next inspect their executable entry predicates and novelty policy; mark NEW or SKIP with concrete code comparisons. If approved, implement source-faithful BTC 5m signals from completed candles with 1m next-open execution and stop-first replay. Preserve immutable baseline and corrected execution sensitivity, full sequential NAV and IST 22-month reporting. Zero slippage first; 0.05% taker fee per side plus 18% GST; funding unmodeled. Only if credible positive, freeze 2025 settings and recheck 2026/ETH plus slippage. Never infer results from the publisher.

## Execution evidence
No GitHub Actions run exists on this branch as of this audit, no BTC trade ledger or monthly results were produced. This source audit is not a historical backtest. Do not notify as profitable finding.
