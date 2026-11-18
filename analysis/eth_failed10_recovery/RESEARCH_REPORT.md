# ETHUSD failed-script recovery audit

**PARTIAL_OR_BLOCKED**

Originally blocked scripts: **10**. Recovered and successfully rerun: **8**.
Still failed: **2**. Missing: **0**.

## Each script's status

| Script | Status | Part |
|:--|:--|:--|
| research_every_candle_200.py | success | calendar |
| research_july_drawdown_stage15.py | success | chain |
| research_monthly_fixed_weight_stage21.py | success | chain |
| research_monthly_portfolio_stage18.py | failed | chain |
| research_monthly_regime_switch_stage16.py | success | chain |
| research_stage12_monthly.py | success | chain |
| research_three_sleeve_stage20.py | success | chain |
| research_time_day_volume_200.py | success | calendar |
| research_trade_counts_stage22.py | failed | chain |
| research_wide_monthly_stage23.py | success | chain |

## Remaining failures

- research_monthly_portfolio_stage18.py: failed, axis
    self._validate_integer(key, axis)
  File "/opt/hostedtoolcache/Python/3.12.16/x64/lib/python3.12/site-packages/pandas/core/indexing.py", line 2365, in _validate_integer
    raise IndexError("single positional indexer is out-of-bounds")
IndexError: single positional indexer is out-of-bounds

- research_trade_counts_stage22.py: failed, ine 161, in main
    months,_,_=verify_ledger(trades)
               ^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/eth_fix10_lmf04me9/research_trade_counts_stage22.py", line 106, in verify_ledger
    raise AssertionError(f"Stage20 source PnL disagrees {m}")
AssertionError: Stage20 source PnL disagrees 2025-02


## Method

Each strategy still uses its original entry and exit source rules.
Only ETH market mapping, diagnostic sample coverage, required artifact paths,
and historical BTC-only fixed count expectations were adjusted.
Upstream stage ledgers are generated fresh from ETH, not copied from BTC.
No previous BTC data analysis or schedules modified.
The successful ETH raw native 205-model cross-family audit resides separately
on the source branch: analysis/eth_native_crossfamily_v2.
A process-complete audit does not imply any strategy achieves 22/22 months profitable.
NOV 2026 source is partial and excluded from every 22-month target.
