# MR-001 follow-up: repository data recovery and novelty review — 2026-11-21

## Actual verified repository data
The earlier audit's statement that genuine Delta BTC 1m data was unavailable is **incorrect for the repository**. Read-only GitHub connector inspection on this run confirmed `data/delta_india/BTCUSD/1m/` holds compressed monthly source files from 2025-01 through 2026-11, plus `manifest.json`. The manifest generated at 2026-11-20T10:17:52Z reports **44,640 / 44,640 BTCUSD 1m bars for October 2026**, sha256_gzip `118135c40c1ef97a325c85a6aace8ebe45de88cb723a4da624b4a4f5b31043e6`. It reports every UTC month 2025-01 through 2026-10 fully populated; historical earlier research reports describing missing 2026-10-31 UTC candles refer to an older snapshot. Do not claim actual full validation without independent data hash/integrity verification at runtime and IST month boundary handling.

- Source: `data/delta_india/BTCUSD/1m/manifest.json` on this isolated branch
- Collector: `scripts/sync_delta_btcusd_1m.py`
- Pipeline docs: `codex/DELTA_1M_DATA_PIPELINE.md`
- Existing reusable 1m stop-first engines: `scripts/research_failed_auction_stage24.py`, `scripts/research_wide_monthly_stage23.py` and related scripts (inspect before reuse)
- Existing Actions examples: `.github/workflows/research-failed-auction-stage24.yml`, `.github/workflows/research-wide-monthly-stage23.yml`

## Novelty decision for Freqtrade BbandRsi
**PARTIAL OVERLAP / NOT YET APPROVED FOR EXECUTION**. The published 1H source (typical-price BB20 2sigma, RSI14<30, long-only, 10% ROI, 25% stop, RSI14>70 exit) is close in economic mechanism to prior RSI2 oversold and Keltner mean-reversion research. Stage23's 5m mean-reversion/fade studies and the prior KeltnerBounceV1 study must be inspected at exact source-level before asserting novelty. Potential differential: published 1H joint BB typical-price stretch and RSI14 confirmation with original asymmetrical 10% target/25% stop, rather than RSI2/Keltner. That is not necessarily a new causal edge. Do NOT run a redundant threshold search solely because the parameters differ.

## Execution handoff
1. Inspect Stage23 original 5m fade source and KeltnerBounceV1 implementation and record equivalent versus truly different signals. Confirm exact Freqtrade ROI, stop and signal semantics from pinned upstream source.
2. If novelty gate passes as a distinct published baseline, implement 1H close signals on **completed** bars and 1m next-open entries with conservative intrabar stop/target, zero slippage but fees 0.05%/side plus 18% GST. Use the repository's real BTC minute partitions, verify hashes, no interpolation and no same-bar hindsight. Avoid claims of exact Freqtrade spot parity when adapting to perpetual futures.
3. Launch isolated GitHub Actions backtest, verify completed run AND artifact, retain full trades and monthly IST NAV. Keep original and improved versions distinct; funding unmodeled.
4. If novelty gate fails, record SKIP and choose a different published mean-reversion mechanism, e.g. statistically grounded rolling z-score with volatility regime and structural risk cap, not arbitrary parameter tuning.

**No new historical backtest was executed during this follow-up. No PF, PnL, monthly returns or profitability may be inferred.** No protected or other research branches changed.
