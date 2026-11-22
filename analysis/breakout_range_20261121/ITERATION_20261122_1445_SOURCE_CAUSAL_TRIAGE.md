# Breakout & Range — 2026-11-22 14:45 IST source/causality triage (append-only)

Branch-only research; no trading or historical P&L claim. Latest branch Actions run 44902737237 completed SUCCESS but is archive validation, not a strategy replay. Previous failed run 44902725486. Existing Stage24 and Stage25 novelty gate reviewed. Source URLs are immutable at publication only when a commit SHA is pinned; these are leads pending source pinning.

## Newly examined mechanisms

1. **holmar18/volatility-contraction-bot** https://github.com/holmar18/volatility-contraction-bot — README states MIT, version 1.0.0, June 18 2024; intraday cTrader stock VCP detection, breakout within 3 bars, volume >80% of current-day average. **SKIP as baseline**: contraction-breakout overlaps Stage24 squeeze; additionally, if the average is computed from the entire current day, it is lookahead. Only elapsed bars can be used, which changes original semantics. No independently verifiable reported BTC trade/PF/DD/fees.
2. **Bpmiller32/SignalFlow** https://github.com/Bpmiller32/SignalFlow — opening 5-minute range, >=1.2x volume, then three-bar FVG confirmation, additional breakout-quality and position filters, partial at 1R and ATR ratchet. **NOT REPRODUCIBLE/NOT APPROVED** until complete code/config commit and license are verified. Potential incremental FVG confirmation relative to Stage24 retest, but must inspect exact prior Stage24 rules and full 20-filter config before claiming NEW. Equities opening-session logic does not automatically transfer to 24/7 BTC.
3. **Bobksl/VCP-Strategy** https://github.com/Bobksl/VCP-Strategy — ATR-threshold directional-change pivot confirmation; contraction low stop and min(5R,next resistance) target; publisher describes 2020–24 CRSP equities and example CAGR 0.36, Sharpe 1.85, DD -0.13, win rate .75. **NOT APPROVED**: no verified source license, precise algorithm/config, and historical data mapping; pivot timestamp must be *confirmation bar*, never extreme bar. Potential distinct online pivot mechanism but overlaps Stage24 compression until differential established. Publisher figures are NOT BTC findings.
4. **dibind-stack/orb-trading-bot** https://github.com/dibind-stack/orb-trading-bot — README MIT; configurable opening range, breakout buffer, range-height R stops/targets, fractional sizing, simulated broker. **SKIP DUPLICATE** of session ORB and range-breakout work; its demo simulated fills and gains are not historical evidence.

## Causal research outcome

- Strongest new hypothesis to examine next: **online directional-change confirmed pivot contraction** from Bobksl, *only* after source license, full rules and Stage24 differential verified. It is not an approved strategy yet.
- Key source-fidelity hazard discovered: **current-day average volume** and **extreme-bar pivot dating** can inject future information. Reject implementations that access either before observation time; do not silently change published rules and claim reproduction.
- Authentic archive is available on GitHub Actions (prior integrity artifact 14706214242); no local archive access is required for a correctly configured push-triggered historical workflow. The archive validator verifies 23 partitions but does not execute positions or compute NAV.
- First screen cost remains 0.05% per side fee + 18% GST = 0.059% per side; 0.118% of round-trip notional before slippage/funding, ignoring price movement.
- This iteration: four source screens; **0 approved new baselines, 0 actual historical backtests, 0 variants, 0 proven profitable candidates**. No source snapshot, trade ledger or monthly NAV artifact exists for these leads; do not treat the audit as a completed test.

## Next executable action

Recover a complete MIT/other permissible implementation of the online directional-change VCP; pin source commit, compare to Stage24 signal and exits; if genuinely NEW, commit NOVELTY_CHECK and causal 1m runner plus push-triggered workflow to this isolated branch; monitor the exact new Actions run to completed trade/monthly artifacts before marking verified. Otherwise reject and switch to a different source-defined mechanism.
