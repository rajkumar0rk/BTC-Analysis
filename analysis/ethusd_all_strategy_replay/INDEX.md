# ETHUSD historical rule-strategy replay

The original BTC algorithms are applied to authentic Delta India ETHUSD 1m history after a fixed January 1, 2025 BTC/ETH price-scale normalization. Model results are not live execution proofs.

| Suite | Engines attempted | Completed | Failed / skipped |
|---|---:|---:|---:|
| five_minute | 2 | 2 | 0 |
| high_frequency | 5 | 4 | 1 |
| other_systems | 6 | 2 | 4 |
| price_structures | 11 | 10 | 1 |
| time_day | 6 | 6 | 0 |

**Total: 24 of 30 engines completed in retained historical suites.**

Only January 2025–October 2026 is scored; November 2026 is excluded. See per-suite reports and failures.

The retired older suite remains recoverable from Git history. Mixed-suite reports retain original historical counts; future replay excludes retired engines.
