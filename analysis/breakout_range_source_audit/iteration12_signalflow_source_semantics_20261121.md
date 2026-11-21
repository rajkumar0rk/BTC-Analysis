# Iteration 12 — SignalFlow source semantics gate (2026-11-21 IST)

Status: SOURCE CODE INSPECTED; NOT APPROVED FOR BTC REPLAY. No historical strategy backtest executed.

Pinned primary source: https://github.com/Bpmiller32/SignalFlow/tree/48f999e98d450fab62495de9b3a148ec858e86f0 ; creator Bpmiller32. Examined server/src/strategies/orbHelpers.ts and server/src/strategyRunner.ts at this commit. Original configuration previously recorded in iteration11_signalflow_config_recovery_20261121.md. License still unverified; do not transplant source.

## Material causal findings

1. Opening range is first 5-minute NY 09:30 candle. Strength score is computed from opening-range size, close location, positive volume, body percentage and a base point. Its score is not a direct predictor; confirm handling of zero-range candles before porting.
2. Breakout detector tests candle HIGH above opening-range HIGH before testing LOW below opening-range LOW. Thus a candle sweeping BOTH boundaries is automatically classified ABOVE, not rejected as ambiguous. The breakout volume threshold is 1.2 times opening-range **average per-minute volume**, not 1.2 times equivalent-duration candle volume. These semantics must be preserved or explicitly labeled as a corrective adaptation.
3. Bullish three-candle FVG requires bullish candle2, body >=40% of its range, range >=0.08% of midpoint, close in top 35%, and candle3.low >= candle1.high*(1-0.02). Bearish mirror uses candle3.high <= candle1.low*(1+0.02). Critically, overlapTolerance=2.0 is **two percent of BTC price**, not 2% of gap width: this accepts substantial overlap and is not a strict non-overlapping FVG. Any strict FVG implementation is NOT source-faithful.
4. Source signal generation uses new Date() and currentPrice rather than an explicit next-minute historical execution timestamp. Runner polls latest 1-minute candle and passes signal to paper broker immediately; this is not an authenticated historical fill model. Runner trade records set fees: 0, so publisher PF cannot be treated as net Delta results.
5. Runner skips any further entry after tradeExecutedToday, even though config maxTradesPerDay=2: this is an execution/config discrepancy. The runner processes positions before new signals and marks symbol done after close.
6. NY 09:30 corresponds to 20:00 IST during EST and 19:00 IST during EDT. Any crypto transfer must use America/New_York IANA time and completed bars; not a fixed IST time.

## Novelty and portability decision

Closest prior art: Stage24 breakout/retest/squeeze and Stage24 failed auction, Stage25 hourly breakout, earlier session fakeout, as documented in codex/STRATEGY_NOVELTY_GATE.md. Three-candle FVG after an opening-range boundary sweep plus inverse-mode direction is a candidate differential, but source's 2% overlap tolerance substantially weakens its supposed FVG distinction. Stock-only earnings/premarket/share-volume and dollar range filters cannot be applied literally to BTC. Decision: PARTIAL OVERLAP — NOT APPROVED pending full onCandle/evaluatePosition inspection and a preregistered explicit BTC transfer; no backtest should claim source-faithful equivalence until resolved.

## Next executable step

Inspect remaining orbStrategy.ts state machine and broker fill/stop code, settle licensing and novel causal mechanism. If accepted, commit a separate NOVELTY_CHECK.md before a zero-slippage BTC2025 next-1m-open replay with both-side 0.05% fee + 18% GST, full ledger and month-end NAV. No slippage sensitivity until positive first screen. Funding unmodeled.
