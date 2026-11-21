# Iteration 13 — SignalFlow position execution fidelity (2026-11-22 IST)

Status: SOURCE-FIDELITY FAILURE / NOT APPROVED FOR BTC HISTORICAL REPRODUCTION. No backtest was executed.

Primary immutable source: https://github.com/Bpmiller32/SignalFlow/tree/48f999e98d450fab62495de9b3a148ec858e86f0 (creator Bpmiller32). Examined `server/src/strategies/orbStrategy.ts` and `server/src/paperBroker.ts`. License not found in pinned tree; permission to redistribute source is not established.

## Newly verified causal execution defects

1. `evaluatePosition` computes a LONG trailing stop from **current candle.high** and then immediately tests **current candle.low** against that newly raised stop. SHORT does the inverse with current low and high. The high/low ordering within the minute is unknown; this is same-bar path hindsight, even though the source prioritizes stop before target. A legitimate historical replay must apply the prior active stop to the current minute first, and activate a newly computed trailing stop no sooner than the following minute, or use authentic tick order.
2. Partial profit is triggered by **candle.close**, filled at **that same close**, and the trailing stop can be activated in the very same candle using that candle's high/low. It is not a next-open fill. Any corrected replay is an explicitly labeled execution-corrected transfer, not exact original paper performance.
3. `paperBroker.openPosition` infers LONG/SHORT from `entryPrice < targetPrice`, rather than using signal direction. `onCandle` inverse mode swaps original target and stop; correctness requires both swapped levels to straddle entry in the intended direction. The broker's buy-side cash check and short-sale proceeds logic are equities-oriented and not Delta futures margin/NAV accounting.
4. `paperBroker.getAccountInfo` values positions at **entry price**, not current market price, and calculates equity as cash plus long-style position value regardless of short exposure. This cannot provide valid futures mark-to-market NAV or drawdown.
5. `checkStopAndTarget` is stop-first on OHLC but fills at the **stop price** even when the candle opens through the stop. Gap-aware adverse fills are required in an authentic replay.
6. Partial exits floor the quantity to integer shares. Delta BTC contract/lot precision differs; blindly copying integer share sizing may skip partial exits. No trading fees or GST are debited in paper broker.

## Decision

Do **not** treat published equity-paper PF as a transferable BTC edge. The novel FVG post-boundary confirmation still has overlap with Stage24, and the 2%-of-price overlap tolerance makes it a weakly defined gap. Reject source-faithful execution as an unbiased historical simulator; a corrected BTC transfer needs an independent novelty gate, explicit assumptions, and must not be labeled exact reproduction. The most defensible next step is to select a DIFFERENT published, licensed, fully specified breakout/range source with executable next-open semantics and run the zero-slippage, fee/GST BTC first screen. This study records negative source findings, not trading P&L.

No GitHub Actions strategy backtest was launched in this iteration. The previously completed archive integrity run is https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44902737237.
