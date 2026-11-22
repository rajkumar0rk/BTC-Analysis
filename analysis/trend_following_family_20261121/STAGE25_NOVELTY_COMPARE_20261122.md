# Stage25 read-only novelty comparison — 2026-11-22

Source: https://github.com/rajkumar0rk/BTC-Analysis/blob/research/stage25-new-trend/analysis/independent_stage25_hourly_trend/RESEARCH_REPORT.md

Stage25 actually evaluated 2,880 account configurations using closed 1H signals, optional 4H confirmation, next-minute entries and 1m stop-first exits. It includes `momentum_accel`, `donchian_break` and `inside_bar_break` with fixed 3R and trailing 3R variants, ATR stops and holding limits. Zero configurations met the stated all-22-month 10%-net target; the 2025-selected inside-bar model lost 16.1344% in 2025 and 10.1067% in 2026. The report's 2026 check is research-exposed and October has a missing UTC day. These are **Stage25's historical results**, not new family backtests.

**Novelty decisions:**
- A plain 1H ATR-trailing momentum acceleration or 1H Donchian persistence model is **DUPLICATE/SKIP**, not a new experiment.
- Triple Supertrend 1H long-only with three *different* buy confirmations and three distinct exit confirmations plus ROI and time-offset trailing remains **PARTIAL OVERLAP**, not approved yet: Stage25 did not directly test this exact signal, but existing Supertrend work and Stage25 directional regime experiments cover closely related economics. Need inspect other Supertrend prior art and pin external indicator before approval.
- Hurst/efficiency-ratio *regime persistence* gate layered on a separately sourced trend system may be a distinct hypothesis, but is not source-defined yet; no rules should be invented merely to backtest.

No new historical execution or profit claim. Existing source pin: Freqtrade strategies commit `f3340ce11f5bdf62f598522e64d1f5638eaa13f5`. Preserve original source and 2025/2026 rejected Ichimoku result.
