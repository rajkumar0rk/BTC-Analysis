# MR-002 execution checkpoint — 2026-11-21 19:33 IST

**Source**: vaultik/algo-trading-system commit 7f9bcd24d0e1cf7258699f4835ecd80dcb684a84 (MIT); source-derived VWAP z-score crossback. Existing novelty gate approved in earlier branch history. No new candidate.

## Recovered successful historical baseline
- GitHub Actions [completed successful run 44901636602](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44901636602), SHA 58bf5a117a85ddee332034c4eaf009d8576c7bc2, artifact ID 14706465892, `mr002-btc-1m-zero-slippage-baseline`. Actual artifacts inspected: summary.json, trade_ledger.csv, monthly_ist_nav.csv, minute_nav.csv.gz.
- Original run used 990,720 authentic Delta India BTCUSD 1m candles 2025-01-01 to 2026-11-19 UTC (22 requested IST month marks through Oct 2026), no detected missing minutes; original archive has 23 UTC monthly partitions including November warmup/cutoff. Full data hashes are in subsequent run logs.
- 225 signals; 204 executed trades; 81 winning, 123 losing; realized net trade PF **0.56965**; 1x current NAV notional; 0 price-point slippage; fee+GST 0.059% of notional per executed side; funding UNMODELED; 1m stop-first assumption.
- Baseline model return **−30.5503%**, 6 positive / 16 negative months, zero flat; minute-close peak-to-trough DD 33.5514%; gross trading PnL −0.1182937 initial NAV; entry fees −0.0936086 and exit fees −0.0936010, net −0.3055033 initial NAV. Trade ledger sums reconcile to ending NAV 0.694496731988.
- 2025 compounded **−22.6482%**; 2026 Jan–Oct compounded **−10.2158%**; worst month March 2025 −7.8449%. Month-by-month full table is preserved in original run artifact.
- WARNING: This earlier successful version predates an entry-fee timing fix and should not be treated as final verified corrected minute NAV.

## Pending correction / actual launched rerun
- The subsequent workflow [run 44906433526](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44906433526) failed **before execution** with `IndentationError: unexpected indent` at line 130, caused by literal escaped newlines accidentally inserted in the Python file during a prior edit.
- This iteration fixed BOTH malformed escaped-newline regions without modifying signal/exit/fee parameters: [commit 0932ae1](https://github.com/rajkumar0rk/BTC-Analysis/commit/0932ae131853e7fb26c6c164870bc4ae5d50adea).
- The push launched [run 44911975169](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44911975169); **in progress** at checkpoint. Next iteration MUST inspect its completed job and artifact and reconcile corrected minute NAV before any new candidate or parameter variation.
- Initial economic finding is decisively adverse even at zero slippage, and should NOT proceed to positive-only slippage robustness unless corrected run materially changes the result.
- No changes to main/master, other families, automations, VPS, or live trading.
