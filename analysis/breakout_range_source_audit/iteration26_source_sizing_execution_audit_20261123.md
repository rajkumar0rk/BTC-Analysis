# Iteration 11 — source execution fidelity audit (2026-11-23 IST)

Upstream pinned source: https://github.com/zty05070242/wavelet-2b/tree/5d879b3d04031952f41d2b4d4c4a3cce43f04150 (MIT). Reviewed `strategy_folder/wavelet_two_b.py`, `strategy_folder/two_b_rule.py`, `backtester.py`, and `position_sizer.py` at this commit.

## Reproducible differences and controls

* Upstream Backtester default is **2% of account balance at stop**, **20x maximum notional leverage**, whereas initial local BTC screening deliberately used **0.5% risk and 3x cap** for matched-risk conservative evaluation. The earlier +3.14% result is NOT a reproduction of upstream position sizing. Commit c04ad026 adds separately named source-sizing runs for BOTH TwoB and WaveletTwoB without changing the original matched-risk outputs. These remain unverified until authentic Actions artifacts complete.
* Upstream WaveletTwoB does not emit a custom stop_loss column; its backtester captures the **signal day's low for long** or **signal day's high for short**, then enters next daily open. Local replay uses the same prior UTC daily high/low and evaluates minute OHLC stop-first with gap-at-open handling. This is a stronger intraday fill model than daily OHLC but not order-book realistic.
* Upstream flips on next daily open and checks stops on the same entry day. Local replay does so at next 1m open, conditional on complete UTC daily bars.
* Upstream default `slippage_pct` is 0, but WaveletTwoB CLI example uses 0.0001. Local first screen is 0 adverse price slippage, with 0.05% fee per side plus 18% GST on fees; historical funding remains unmodeled. Source cost settings therefore must not be represented as identical.
* Upstream's published original market in the WaveletTwoB CLI example is `SI=F` daily commodity futures, NOT Delta India BTCUSD. BTC performance is an independent transfer test.

## Remaining parity risks

The source-parity diagnostic independently translated the same source rules and found 29/29 signals aligned, but this is not an external upstream-library invocation. Need independent event-level comparisons for signal, entry, stop, exit, position size and cost per trade, plus source-sizing results. The first UTC and final IST months are partial; do not count them as complete.

## Status

Commit c04ad026: historical replay launched as Actions run 45087386572. **PENDING COMPLETED JOB, LOGS AND ARTIFACT RECONCILIATION** at time of this audit. No new profitability or verified source-sizing result claimed.
