# Reclaim V2 — independent complete 1m historical replay of the shortlisted monthly winners

Frozen Reclaim V1 exact entry and risk execution engine; skip-only pre-signal filters based on completed 1H candle properties. No replacement entry in a skipped Supertrend cycle.

### Candidate comparison across two intraminute path assumptions

| profile               |   trades |   profitable_months |   losing_months |   flat_months |   net_usd_min |   net_usd_max |   closed_equity_dd_pct_worst |
|:----------------------|---------:|--------------------:|----------------:|--------------:|--------------:|--------------:|-----------------------------:|
| OR_3_COND             |       47 |                  17 |               2 |             3 |       28.4256 |       28.6497 |                        2.967 |
| OR_AND_4_COND_NO_SIDE |       47 |                  17 |               2 |             3 |       25.6092 |       25.8334 |                        3.04  |
| OR_AND_4_COND         |       47 |                  17 |               2 |             3 |       25.2919 |       25.516  |                        3.021 |
| OR_AND_5_COND         |       45 |                  17 |               3 |             2 |       31.6997 |       31.9238 |                        2.828 |
| OR_2_COND             |       50 |                  16 |               4 |             2 |       25.9635 |       26.1876 |                        3.294 |
| LOCKED_V1             |       55 |                  15 |               5 |             2 |       20.0374 |       20.2615 |                        4.308 |

### Interpretation

- OR_3_COND achieves 17/22 but Oct 2025 net is only approximately $0.007, very fragile to extra costs.
- OR_AND_4_COND achieves 17/22, 2 losing, 3 flat months, with stronger Oct 2025 profit cushion than OR_3_COND.
- OR_AND_5_COND achieves 17/22, 3 losing, 2 flat months, higher historical net but more conditions.
- All original 15 profitable months preserved in USD, no month on either path made worse under the original cost model.

### Caveats

Search on repeated in-sample Jan 2025-Oct 2026 history is highly optimized; no guarantee of future monthly consistency. Price-path models assume continuous intraminute paths, not real tick sequencing. Existing leverage/liquidation and exchange amendment mechanics unmodeled. Stress sensitivity is only a trade-level P&L cost adjustment, not a re-executed orderbook simulator.
