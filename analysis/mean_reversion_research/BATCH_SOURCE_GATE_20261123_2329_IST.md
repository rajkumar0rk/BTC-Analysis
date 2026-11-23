# Mean-reversion source gate — 2026-11-23 23:29 IST

Scope: isolated read-only discovery and source eligibility. No historical job launched, no new BTC NAV or profit claims. Existing branch Actions GET returned eight runs, newest completed success 45036174691 (MR003, rejected); previous MR002 rejected, do not retest.

Instructions consulted: codex/AGENTS.md, codex/STRATEGY_NOVELTY_GATE.md, codex/FINDINGS_INDEX.md; latest prior gate BATCH_SOURCE_GATE_20261123_2232_IST.md.

## Three independent newly screened sources

1. **orangepineapple/mean_reversion_strategies** — https://github.com/orangepineapple/mean_reversion_strategies/tree/e6d64522861c4a0551c6d423d4b5e95955049922 ; commit e6d64522861c4a0551c6d423d4b5e95955049922. README describes Ernest Chan-inspired cointegration, pair spread, rolling hedge ratio, stationarity, Kalman and Backtrader examples. Economic mechanism: *relative-value two-asset stationary spread*, not single-asset RSI/Bollinger BTC reversion. Novelty: potentially NEW if both contemporaneous authentic Delta India BTC and ETH 1m data, synchronized gaps, hedge sizing, both-leg fees, liquidation and stop rules can be recovered. Current state **NOT REPRODUCIBLE AS BTC-ONLY**: source's demonstration pair is EWC/EWA equities, and BTC-only archive cannot faithfully reproduce pair strategy; original exact executable entry/exit, stop, source license, published period/PF/trades/return/DD not yet verified. Do not substitute synthetic ETH, or mislabel EWC/EWA performance as BTC. No execution approved.

2. **bryancwh/algo-trading-mean-reversion** — https://github.com/bryancwh/algo-trading-mean-reversion/tree/2dc604c65cdf4d0653bd395b2ad305f23ef3e83f ; commit 2dc604c65cdf4d0653bd395b2ad305f23ef3e83f. README identifies Bollinger Bands plus RSI on Alpha Vantage-selected equities. back_testing.py buys at signal bar close and sells at signal bar close, with no explicit protective stop, gap/stop-first handling, fees, GST, position-size NAV, or month-end MTM. Original period/trade count/PF/return/DD and license not verified. Novelty **DUPLICATE** of earlier BB/RSI mechanism; **SKIP**.

3. **jamesmawm/High-Frequency-Trading-Model-with-IB** — https://github.com/jamesmawm/High-Frequency-Trading-Model-with-IB/tree/8e96ade54a8e3eb94ead04827a846225ae122864 ; commit 8e96ade54a8e3eb94ead04827a846225ae122864. README version 3.0 describes IB high-frequency two-leg correlated-pair statistical arbitrage with beta/fair value, bootstrapped parameter fitting, short/long legs and tick orders. It explicitly warns earlier compatibility model may not work. This is cross-asset relative-value, not BTC-only price mean reversion. Novelty **PARTIAL / DATA BLOCKED**: cannot run source-faithful with only BTC one-leg archive; exact stop and trade execution rules, license and publisher performance not established. **HOLD**, no installation/trading scripts executed.

## Exact next executable gate

Recover source-complete *single-asset* bounded-risk mean-reversion model with license and pinned settings, compare Stage19/MR001–003 before NOVELTY_CHECK, then implement in reusable archived authentic BTC1m runner. First replay zero assumed slippage with 0.05% notional fee per side plus 18% GST (0.118% round-trip), stop-first gaps and next-open fills, sequential NAV, IST months. Verify completed Actions run and artifacts before claiming any new P&L. October 2026 has 1,440 missing UTC minutes. Funding remains unmodeled.

This session: 3 new public repositories screened; 0 eligible new baseline implementations; 0 new historical backtests; 0 variants; 0 new Actions launches; no code fix or profitability claim. This is source screening only, not the user's target of multiple completed studies.
