# ETHUSD — final verification: 10/10 previously blocked scripts recovered

**Verified 18 November 2026.** This report only consolidates the execution
**status** of two independent ETHUSD repair attempts; **no historical PnL
from BTC or other research was copied, pooled or merged**.

## Source provenance

- Isolated recovery branch v3: `research/eth-failed10-recovery-v3`.
- Focused correction branch v4: `research/eth-failed10-recovery-v4`.
- Original market data: Delta Exchange India ETHUSD 1m history on `main`;
  complete UTC 2025-01 through 2026-10, checksum verified.
- Original BTC-point thresholds use a pre-declared *constant* 2025-01-01
  BTC/ETH index conversion (not literal 200 ETH points); original ATR,
  entry, exit and fees source rules remain otherwise unchanged.
- **November 2026 partial history is used only for original code's diagnostic
  fourth-split assertions, NEVER to score 22 complete months.**
- Main branch, BTC ledgers, live systems and scheduled automations unchanged.

## Recovered scripts and independently verified outcomes

| Script | Original blocker | Final | Evidence |
|:--|:--|:--|:--|
| `research_every_candle_200.py` | Missing November diagnostic observations | **PASS** | [v3 calendar](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44284939821) |
| `research_time_day_volume_200.py` | Missing November diagnostic observations | **PASS** | [v3 calendar](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44284939821) |
| `research_stage12_monthly.py` | Missing ledger argument and BTC-only frozen expected counts | **PASS** | [v3 chain](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44284939821) |
| `research_monthly_regime_switch_stage16.py` | Missing original ETH Stage14 artifact | **PASS** | [v3 chain](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44284939821) |
| `research_july_drawdown_stage15.py` | Missing original ETH Stage14 artifact | **PASS** | [v3 chain](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44284939821) |
| `research_monthly_portfolio_stage18.py` | Missing Stage15 ledger; **zero ETH 2025 candidates met original qualification**, previously caused `iloc[0]` crash | **PASS with an explicitly UNQUALIFIED 2025-only fallback for report generation** | [v4](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44285849063) |
| `research_three_sleeve_stage20.py` | Missing generated ETH Stage18 output | **PASS** | [v3 chain](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44284939821) |
| `research_monthly_fixed_weight_stage21.py` | Missing generated ETH Stage18 output | **PASS** | [v3 chain](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44284939821) |
| `research_wide_monthly_stage23.py` | Missing upstream ETH portfolio outputs | **PASS** | [v3 chain](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44284939821) |
| `research_trade_counts_stage22.py` | Required ETH stage ledgers, hardcoded BTC-only component counts and BTC's frozen Stage20 allocation | **PASS** | [v4](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44285849063) |

**Final: 10 of 10 previously failed scripts successfully executed.**

### Important GitHub run nuance

The earlier v3 workflow `44284939821` is **marked failed as a whole**
because its original Stage18/Stage22 chain step failed; the *other 8*
sub-scripts had genuinely passed. The v4 workflow `44285849063`
**finished successfully and specifically reran those 2** with the fixes.
**Do not mistakenly interpret the old v3 top-level status as a failure
of the final recovered set.**

### Audit details

- Stage18 original strict 2025 qualification: **0 candidates**; the ETH-only
  reporting fallback is explicitly marked `original_2025_gate_met=false`.
  That is **not** a deployable profitable portfolio.
- Stage22: **386 historical ETH component closes reconciled** against the
  ETH-selected Stage20 model and its actual auxiliary allocation.
- The two formerly failing diagnostic scripts ran to completion in the
  v3 calendar job. This is not evidence of any +10%-every-month edge.
- The separate ETH native-price family audit covers 52 representative
  families/205 accounts and previously verified 0 achieving the
  22/22 monthly-positive or 22/22 +10% condition.

**Process-success does not prove trading profitability.** Funding, real spread,
market impact, minimum lots, margin and liquidation remain partly unmodeled.
A constant January 2025 BTC/ETH price anchor differs from per-entry dynamic
BTC/ETH normalization; monthly strategy outputs should not be pooled across
these different normalization methods. January 2025 first 5.5 hours IST
are not covered because historical partitions start January 1 UTC.
