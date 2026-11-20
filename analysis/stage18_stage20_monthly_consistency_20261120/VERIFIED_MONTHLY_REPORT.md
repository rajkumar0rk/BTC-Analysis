# Stage18 and Stage20: actual BTC 1m monthly-consistency improvements (research only)

Verified GitHub Actions: [native-entry and regime replay #44650521855](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44650521855) (success), [native daily swing ATR trailing replay #44651293914](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44651293914) (success). Branch `research/stage18-stage20-monthly-consistency-20261120-v1`; none of this merged to main or deployed to a live trading account.

## Decision

The original **5R** exit remains a strong baseline. A wider **entry eligibility** filter increased Stage18 profitable months from **15/22 to 17/22** and its modeled compounded BTC return from **+12.0163% to +12.9201%**, with the native Stage17 original 3xATR swing trailer. For Stage20, profitable months stayed **18/22**, while modeled net return increased from **+9.5803% to +10.3748%** on the fully rerun (native Stage17) basis.

A selected **2xATR daily swing trailing distance** improved Stage18 slightly further to **+12.9586%** while preserving 17/22 profitable months. Stage20's 2xATR option performed WORSE in the later period and returned +10.2463% vs +10.3748% using original 3xATR; therefore keep Stage20's unchanged 3xATR swing trailing baseline for this retrospective comparison.

### Actual changed trading rules

| Setting | Existing baseline | Exploratory improved Stage18 | Exploratory improved Stage20 |
|---|---|---|---|
| Stage15 4H ADX upper bound | 18 | **18, unchanged** | **18, unchanged** |
| Stage15 previous completed month directional efficiency maximum | 0.15 | **0.25** | **0.25** |
| Stage15 1H quiet-volume ratio | <=1.2 | <=1.2 unchanged | <=1.2 unchanged |
| Stage15 main take-profit | 5R | 5R unchanged | 5R unchanged |
| Stage15 trade max hold | 240min | 240min unchanged | 240min unchanged |
| Stage15 initial stop | Structural original | unchanged | unchanged |
| Stage17 daily swing ATR trailing | 3xATR original | **2xATR** | **3xATR unchanged** |
| Stage17 daily swing initial SL and 14-day time cap | 2xATR and 14days | unchanged | unchanged |
| Stage19 Stage20 auxiliary hourly sleeve | original monthly source | n/a | unchanged |

The wider efficiency filter was NOT the 2025-only selection winner; we identified it while reviewing the previously examined 2026 comparison. It therefore is an **exploratory, post-hoc research lead**, NOT independent out-of-sample validation. With the revised source replay, Stage20's original archived October 2026 Stage17 monthly value differs from native rerun by **−0.047895 percentage points**; this source drift is logged and not silently reconciled away.

## Full modeled BTC 22-month portfolio results

All percentages are account NAV *model outputs*, not BTC points or a claim of live return. Both components' entry/exit engines were replayed natively on BTC 1-minute OHLC; however portfolios combine separately traded component NAV streams by monthly allocation rather than shared-margin integrated execution.

| Metric | Stage18 baseline | Stage18 exploratory 2xATR | Stage20 baseline | Stage20 exploratory 3xATR |
|---|---:|---:|---:|---:|
| 2025 net return | +6.7313% | **+7.1370%** | +5.1873% | **+5.5665%** |
| 2026 Jan–Oct net return | +4.9517% | **+5.4338%** | +4.1763% | **+4.5547%** |
| 22m compounded net return | +12.0163% | **+12.9586%** | +9.5803% | **+10.3748%** |
| Profitable / losing / flat months | 15 / 4 / 3 | **17 / 4 / 1** | 18 / 3 / 1 | 18 / 3 / 1 |
| 22m net, +2bps additional modeled slippage each Stage15 order side | +9.5197% | **+10.2571%** | +7.3766% | **+7.9931%** |
| 22m net, +5bps additional modeled slippage each Stage15 order side | +5.8791% | **+6.3258%** | +4.1551% | **+4.5179%** |

**The core Stage15 recorded trades rose from 64 to 72**, bringing Stage18 positive months in March 2025 and July 2026, rather than obscuring losing months. Stage20 already had small positive returns in both months, so its profitable-month count stayed unchanged. In Stage18 no losses were removed or rewritten; it still loses Dec2025, Jan2026, Jun2026 and Sep2026 in this modeled ledger.

### Exact monthly BTC result: original vs exploratory improved

| Month IST | Stage18 5R baseline | Stage18 5R + wider regime + swing 2xATR | Stage20 5R baseline | Stage20 5R + wider regime |
|---|---:|---:|---:|---:|
| 2025-01 | 0.000% | 0.000% | 0.000% | 0.000% |
| 2025-02 | +1.000% | +1.000% | +0.607% | +0.607% |
| 2025-03 | 0.000% | +0.401% | +0.059% | +0.420% |
| 2025-04 | +1.603% | +1.603% | +1.657% | +1.657% |
| 2025-05 | +0.018% | +0.047% | +0.149% | +0.149% |
| 2025-06 | +1.318% | +1.294% | +0.982% | +0.982% |
| 2025-07 | +0.652% | +0.652% | +0.381% | +0.381% |
| 2025-08 | +0.562% | +0.562% | +0.415% | +0.415% |
| 2025-09 | +0.383% | +0.383% | +0.117% | +0.117% |
| 2025-10 | +1.343% | +1.343% | +1.230% | +1.230% |
| 2025-11 | +0.703% | +0.703% | +0.422% | +0.422% |
| 2025-12 | −1.020% | −1.045% | −0.926% | −0.926% |
| 2026-01 | −0.301% | −0.266% | −0.043% | −0.043% |
| 2026-02 | +3.381% | +3.343% | +2.871% | +2.871% |
| 2026-03 | +1.275% | +1.275% | +0.828% | +0.828% |
| 2026-04 | +0.243% | +0.243% | +0.207% | +0.207% |
| 2026-05 | +0.178% | +0.240% | +0.074% | +0.074% |
| 2026-06 | −0.208% | −0.213% | +0.032% | +0.032% |
| 2026-07 | 0.000% | +0.404% | +0.204% | +0.567% |
| 2026-08 | +0.424% | +0.424% | +0.415% | +0.415% |
| 2026-09 | −0.140% | −0.140% | −0.493% | −0.493% |
| 2026-10 | +0.046% | +0.046% | +0.042% | +0.042% |

## What was verified and what remains open

1. Actual BTC Stage15 entry and exit signals are re-executed on minute bars from original Stage14 event archive, including structural stop, 5R TP, original weekly -3R gate, 0.05% taker per side + 18% GST + assumed 5 BTC-point slippage per side. Added 0/2/5bp per-side slip tested on primary.
2. Original Stage17 Daily55 EMA50 and Daily20 no-filter trade entries and ATR trailing exits are independently **re-run on BTC 1-minute candles**; stage17 original Daily55 source matches within 0.00005%, Stage20's Daily20 differs in October 2026 by 0.047895% (audited). Stage17 includes estimated taker fees/GST and original slippage, not the extra core per-fill stress.
3. Stage20 10% Stage19 hourly sleeve is still from saved monthly results. **Full multi-sleeve order sequencing, month-rebalancing commissions, shared account margin, positions overlap, funding and liquidation are NOT modeled.**
4. Modeled account month-end drawdown understates possible intramonth equity drawdown; Stage15 PnL credited in exit month, whereas Stage17 positions are month-end marked. Data known incomplete early 2025 Jan IST and 2026 October 31. No actual quote-level spreads, realized funding, minimum lots, integer contract rounding or collateral requirements.
5. **BTC 2025 and BTC 2026 were previously inspected in multiple research studies. No untouched forward holdout. No ETH native rerun of widened and 2xATR rules.** Treat this research as a candidate for genuinely forward paper trading / independent new-data execution audit, not a live trading recommendation.

Source/run artifacts contain every tested variant, actual BTC core trades and daily-swing trades, and all monthly NAV CSVs. Keep originals immutable. Main branch and live accounts untouched.
