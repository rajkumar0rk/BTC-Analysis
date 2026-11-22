# Mean-reversion batch source triage — 2026-11-22 19:28 IST

Scope: research only; no new Delta historical replay, no verified new P&L. Existing MR002 remains rejected (run 44911975169, artifact 14709852576).

## Candidate A — MRCVEngineer/CRSI (source-code integrity rejection)
Source: https://github.com/MRCVEngineer/CRSI/blob/master/src/strategy.py ; README https://github.com/MRCVEngineer/CRSI ; publisher states MIT, 4h BTC/ETH, 1758 BTC trades, PF 1.23, +193.5% BTC, 16.2% BTC DD (publisher claims only; unverified).
Rule: CRSI=(RSI3+streak RSI2+100-return percentile rank)/3; LONG CRSI<30 and close>SMA200; SHORT CRSI>70 and close<SMA200; exit CRSI crossing 50 or 15 bars. Source has no explicit protective stop. 
Critical reproducibility defects in executable source: SMA200 is backfilled with .bfill(), injecting future information into the warmup period; signals are evaluated on current candle close and trades filled at that same close; the RSI helper uses ewm(span=period) rather than Wilder's smoothing; no fees/GST or intraminute gap stop in this source routine. Do not transfer reported performance to Delta BTC. To study CRSI in future requires explicit corrected causal adaptation and structural stop, separately labeled; mechanism overlaps prior RSI extremes. Decision: NOT APPROVED; no backtest.

## Candidate B — genia503/mean-reversion-backtester
Source: https://github.com/genia503/mean-reversion-backtester ; source describes 15m 3up/4up and bigbull fade shorts, 2025-03-19 through 2026-03-19 on seven altcoins, 11,660 aggregate simulated trades and 2,160 parameter sweeps. Its thesis is post-streak exhaustion, not an equilibrium band. Existing Stage19/Stage24 sweep/price-action reversal mechanisms are near prior art; no licensed, BTC-specific, frozen single configuration and no complete stop-first baseline confirmed here. Decision: PRIOR ART / SOURCE BASELINE NOT APPROVED; no replay.

## Candidate C — pairscan/ratio-mean-reversion
Source: https://github.com/pairscan/ratio-mean-reversion ; MIT stated. Mechanism is two-asset log-ratio stationary spread, Hurst/ADF/range tests, rolling P5/P95 walk-forward entry/exit. Requires synchronized two-leg prices and trades, while this lane mandates single BTCUSD futures source-faithful OHLCV reproduction. README explicitly notes execution costs not modeled and synthetic examples. Decision: NOT REPRODUCIBLE AS SINGLE-BTC BASELINE; no replay.

## Reproducibility and economics
Source-faithful single-BTC baseline eligibility: none this batch. Original MR002 has 204 trades, -30.5503268% compound NAV, 33.5514% minute-close DD, +6/-16 months; do not count its re-audit as new testing. New distinct completed historical backtests: 0; new parameter variants: 0; newly screened sources: 3; Actions runs launched: 0. Fee assumption for future first screens remains 0.05% notional per side plus 18% GST = 11.8 bps round trip before funding/spread/slippage. 2026-10-31 UTC missing in existing archive, cannot call October complete. Next action: select a licensed, source-pinned, nonduplicate BTC-native structurally stopped reversion rule, record novelty and immutable baseline, then run archived Delta BTC 1m replay with next-minute fills and stop-first execution. Do not create artificial stop rules while claiming source fidelity.
