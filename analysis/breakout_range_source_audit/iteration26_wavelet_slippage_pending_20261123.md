# Wavelet-2B adverse-fill sensitivity — execution handoff (2026-11-23)

- Existing source-pinned causal signal and source/matched risk baselines remain unmodified in their output filenames.
- Commit: dc97d30b235e2ecbbad9bd28b748222572be20a1.
- Source: https://github.com/zty05070242/wavelet-2b/tree/5d879b3d04031952f41d2b4d4c4a3cce43f04150 (MIT); prior-art gate: analysis/breakout_range_wavelet_daily/NOVELTY_CHECK.md.
- Distinct new strategy baselines: 0. Sensitivity variants: 4 (Wavelet-2B at 0.5 and 5 USD adverse price points per executed side, each at matched 0.5%/3x and source 2%/20x sizing).
- Entries pay adverse +points for longs and -points for shorts; exits pay adverse -points for longs and +points for shorts, including gap/stop exits. Both entry and exit fees remain 0.05% notional plus 18% GST. No spread/L2 or historical funding modeled.
- Authentic BTCUSD Delta India 1m archive loaded by existing hash-verifying runner; no synthetic candles. No ETH experiment yet.
- Actual Actions launched at commit: archive audit https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45098672897 ; historical replay https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45098672933 ; replay job 137444175376.
- Status at first check: IN_PROGRESS (checkout). NOT VERIFIED. No slippage P&L may be quoted until successful job logs, artifact extraction, four variant trade/monthly files, source baselines unchanged and NAV reconciliation are inspected.
- Next action: poll replay 45098672933 and archive audit 45098672897 to completion; fetch artifact, reconcile all six summary rows and monthly NAV; diagnose/rerun failures on this branch. If positive after costs, separately examine trade distribution and frozen ETH data availability.
