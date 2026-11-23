# Combined historical replay artifact reconciliation — 2026-11-24 01:48 IST

Scope: existing research branch only. This is **artifact verification**, not a new distinct strategy backtest or source-faithful Dual Thrust reproduction.

- GitHub Actions run: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45246331426 ; run ID 45246331426, job 137943928136, commit 5030eb6da6057524df0b9f9bdd93b58cea5714a1, completed SUCCESS.
- Downloaded actual artifact ID 14853648610, 28 files. Historical workflow includes both the Wavelet replay and causal Dual Thrust adaptation.
- Dual Thrust artifact: 116 trade CSV rows; 56 positive / 60 negative; gross +152.70371941955395 USD; entry+exit fees and GST 199.9924370984369 USD; net -47.28871767888298 USD; $10,000 initial NAV -> 9952.711282321117 USD. Maximum per-trade arithmetic residual |gross-entry_fee-exit_fee-net| = 3.55e-15 USD.
- Monthly CSV: 23 observed IST month rows; 21 marked complete (10 positive, 11 negative), 2 marked partial. Maximum monthly NAV identity residual |last-first*(1+net_pct/100)| = 3.64e-12 USD. Final monthly NAV 9952.71128232112 USD agrees with trade ledger to <4e-12 USD.
- Caution: month-coverage labeling is runner-reported, not independently reconstructed from raw minute timestamps here. Historical source archive and full original coverage manifest should be checked before asserting that every calendar month has complete data. No funding, spread/L2 impact, liquidation or real margin modeled.
- Wavelet reference signal parity diagnostic: 29 reference and 29 local signals, zero mismatches. This is signal parity, not live execution parity.
- Decision: causal Dual Thrust adaptation rejected as net-negative after modeled fees; no new optimization on 2026. Combined job and artifact verification complete; no new distinct candidate baseline tested in this audit.
- Next: prioritize a new source-pinned, license-verified, genuinely nonduplicate boundary mechanism and run authentic 1m baseline with proper novelty gate; separately verify complete IST month coverage directly against archive timestamps.
