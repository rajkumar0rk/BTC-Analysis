# MR002 corrected 22-month baseline — REJECT — 2026-11-21

**Actual completed run:** [GitHub Actions #44911975169](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44911975169) (SUCCESS), workflow job replay, code SHA `0932ae131853e7fb26c6c164870bc4ae5d50adea`. Historical artifact `mr002-btc-1m-zero-slippage-baseline`, artifact ID **14709852576**, includes **summary.json, trade_ledger.csv, monthly_ist_nav.csv, minute_nav.csv.gz**. Previous successful run #44901636602 had a minute-NAV fee-timing defect; subsequent run #44906433526 failed syntax before replay; this run corrects both.

## Source and baseline
Original third-party publisher: [vaultik/algo-trading-system](https://github.com/vaultik/algo-trading-system), immutable [source commit 7f9bcd24d0e1cf7258699f4835ecd80dcb684a84](https://github.com/vaultik/algo-trading-system/commit/7f9bcd24d0e1cf7258699f4835ecd80dcb684a84), MIT; original Bybit 5m. Source-derived BTC adaptation: 5m 288-bar rolling volume-weighted VWAP and volume-weighted dispersion, z-score crosses back inside ±3 with prior 5m relative volume >=2.5; next 1m open entry; partial exits and structural stop; maximum 240 one-minute bars; 1x NAV notional. Important: **source-derived adaptation, not byte-for-byte publisher engine**, due conservative stop-first 1m execution and 1x risk sizing; original publisher used 3x leverage and optimistic OHLC paths. No untrusted third-party code executed.

BTC data: Delta Exchange India authentic 1m archive; 990,720 observed candles, 0 missing UTC minutes in archive, 23 compressed partitions from Jan 2025 through Nov 2026. Tested calendar months Jan 2025–Oct 2026 in IST. Exact data-partition SHA256 hashes in run logs. Historical data timestamp semantics were inherited from archive loader. Signals from completed 5m candles, entry at next 1m open. Conservative stop-first intrabar ambiguity, stop gap fill at worse of stop/open. Fee 0.05% taker per executed side +18% GST = 0.059% per side; **zero assumed slippage**. Funding, L1 spread, market impact, margin and liquidation UNMODELED. No positive-only stress variations run.

## Corrected historical result
- **204 trades from 225 eligible signals; 81 winners / 123 losers; realized net profit factor 0.569654**.
- **Compounded net return −30.550327%** (initial NAV 1.0, final NAV 0.694496731988).
- **6 profitable / 16 losing / 0 flat IST months**.
- Maximum **minute-close** NAV drawdown **33.5514%** (not necessarily intraminute worst drawdown).
- 2025 net **−22.602585%**; 2026 Jan–Oct net **−10.268744%** (chronological recheck, not pristine holdout).
- Gross PnL **−0.1182936933** initial NAV; entry fees **−0.0936085753**; exit fees **−0.0936009994**; total fee/GST debit **−0.1872095747**; net **−0.3055032680** initial NAV.
- Ledger-to-NAV reconciliation: `1 + sum(trade_ledger.net_pnl) = 0.6944967319880869`, matching final NAV `0.6944967319880864` to floating precision. Worst IST month: **2025-03 −7.844892%**.

| IST month | Net month NAV % | Entries |
|---|---:|---:|
| 2025-01 | -5.083534 | 10 |
| 2025-02 | -4.180184 | 13 |
| 2025-03 | -7.844892 | 11 |
| 2025-04 | -3.989811 | 8 |
| 2025-05 | +0.737576 | 6 |
| 2025-06 | -0.444570 | 6 |
| 2025-07 | -2.506883 | 9 |
| 2025-08 | -2.386167 | 7 |
| 2025-09 | -1.140192 | 5 |
| 2025-10 | -0.812253 | 12 |
| 2025-11 | +1.189176 | 6 |
| 2025-12 | +1.563863 | 18 |
| 2026-01 | +1.064653 | 10 |
| 2026-02 | -1.042891 | 5 |
| 2026-03 | -4.560436 | 11 |
| 2026-04 | -1.074593 | 9 |
| 2026-05 | -2.097350 | 10 |
| 2026-06 | -1.914727 | 10 |
| 2026-07 | -3.020821 | 7 |
| 2026-08 | -0.594088 | 10 |
| 2026-09 | +0.359311 | 12 |
| 2026-10 | +2.285605 | 9 |

**Decision: REJECT MR002 source-derived baseline.** Losses persist before adverse execution slippage; both gross trading PnL and net PnL negative. No defensible reason to optimize endlessly or test 0.5/5 BTC-point adverse slippage on this losing mechanism. Next family-compatible research should use a DIFFERENT externally sourced, novel mean-reversion mechanism, and repeat the source novelty gate before implementation. Preserve this original baseline and all losing trades.

No changes to main/master, other families, VPS, automations, or real trading.
