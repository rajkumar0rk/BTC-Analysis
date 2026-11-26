# BTC-Analysis — mandatory strategy novelty gate

Purpose: prevent duplicate BTCUSD futures strategy research and preserve compute budget.
**Do not execute a new backtest until this gate passes.**

## 1. Check existing work first

Search all of `scripts/research_*.py`, `analysis/**/RESEARCH_REPORT.md`,
`analysis/**/quality.json`, `codex/`, and relevant workflow files.
Do NOT search solely by a strategy's name: renamed or parameter-tweaked
strategies may reproduce the same research.

Inspect the proposed experiment's:
- Entry signal formation, side, candle closure and execution latency
- Timeframes, trend/volume/OI/funding filters and causal data sources
- Stop/target/trailing/timeout rules, trade concurrency, sizing and leverage
- Instrument, trading dates, fees, GST, slippage and funding assumptions
- Historical evaluation windows and account-level monthly metric

Record file paths of the closest matching previous experiments.

## 2. Existing research coverage (non-exhaustive)

| Experiment family | Evidence | Previously examined |
| --- | --- | --- |
| Intraday candle/time/volume/volatility | Stages 6, 7, 8, 9; `analysis/institutional_discovery_stage7_time_volume/` | 1m time, weekday, high-volume/volatility, direction/exit patterns |
| OI with price action | Stages 2, 3, 4; `analysis/institutional_discovery_stage2/`, `analysis/institutional_discovery_stage3/` | OI rising/falling, 12h breaks, sweeps, acceptance/rejection, hourly expansion |
| Funding/carry | `analysis/institutional_carry_stage1/` | funding proxy and market-neutral carry feasibility |
| 4H/1H/15M trend pullbacks | `analysis/institutional_discovery_stage13_4h_1h_15m/` | 4H trend, hourly pullback, 15m breakout |
| Monthly 5m price-action search | `analysis/institutional_discovery_stage19_monthly_10pct/` and Stage23 | breakout, sweep, RSI2, EMA pullback, compression, engulf, 1m stop-first exits |
| Other monthly models | Stages 14–23 | regime, risk, direction inversion, multiple sleeves and 2025-only portfolio fitting |
| 15m breakout / retest / squeeze | `analysis/institutional_discovery_stage24_structure_monthly10/` on `research/stage24-monthly10` | new 15m structure entries; 1m exits |
| 1H momentum, breakout, inside-bar | `analysis/independent_stage25_hourly_trend/` on `research/stage25-new-trend` | hourly momentum and trend variants, optional 4H context, 1m execution |

The Stage24 and Stage25 branches may not be in `main`. Inspect these
branches before proposing research that overlaps either stage.

## 3. Decision rules

- **DUPLICATE**: Same core causal signal and economically equivalent
  execution; parameter changes, renamed patterns and shifted thresholds
  do not make it new. **SKIP** and reference the original run.
- **PARTIAL OVERLAP**: A different component is proposed but the main
  thesis has been tested. Define the incremental hypothesis and why the
  existing reports cannot answer it; otherwise **SKIP**.
- **NEW**: A materially distinct, measurable, forward-observable signal
  or previously unavailable data source not covered by prior experiments.
  Only then create new code, results directory, and branch.

A proposed use of `funding + OI + volume` is NOT automatically novel:
all three have historical coverage in earlier projects, even if a
specific joint rule has not yet been tested. Verify the exact conjunction.

## 4. Required pre-run record

Before any new workflow execution, commit a `NOVELTY_CHECK.md` file
into its NEW output directory including:
- Proposed complete deterministic trade rules
- Closest older scripts and research reports, with paths/refs
- Exact economic difference from each closest strategy
- Data requirements and quality, especially missing 2026-10-31 UTC
- Validation split (2026 historical data has already been inspected)
- Decision: `NEW`, `PARTIAL OVERLAP — approved differential`, or `SKIP`

When decision is SKIP, do not run the backtest. Do not overwrite or
reuse existing result directories.

## 5. Evaluation after novelty passes

The research goal is at least 10% **NET ACCOUNT** return in every
COMPLETE IST calendar month, after correctly modeled exchange fees,
GST and slippage. Count no-trade and zero-profit months as failures;
November 2026 is incomplete. October 2026 has 1,440 missing UTC-minute
candles and cannot be claimed to be fully validated.

Show monthly PnL, total/win/loss trade counts, peak-to-trough
drawdown, estimated execution costs, excluded gaps, and separate
train/check periods. Avoid fitting to 2026 month labels, leverage
only to force return, or implying guaranteed future profits.

## Retired legacy experiments

See [RETIRED_STRATEGIES.md](RETIRED_STRATEGIES.md) and inspect the pinned pre-retirement commit before proposing equivalent rules. Removal from the current branch does not make previously tested ideas novel. Do not automatically recreate deleted workflows or result directories.

## Consolidated historical branch references (2026-11-26)

Consult `codex/RESEARCH_BRANCH_RETIREMENT_20261126.json` before new experiments. Inspect retired experiments at their exact recorded commit SHA, reachable from `archive/retired-research-20261126` after consolidation succeeds. Do not recreate retired refs to inspect them. Reuse the relevant retained workstream for iterative research. Retirement is not evidence of strategy failure.
