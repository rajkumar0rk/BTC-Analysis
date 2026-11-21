# M04 — Source-faithful Fusion VWAP Momentum novelty decision (2026-11-21 14:17 IST)

## Original pinned source
- Pine: https://github.com/shahzaib-574/MarketCipherTrading/blob/main/vwap_momentum_strategy.pine (blob 8302401c7b4f855fbb0c114a283dd4e57c7aebf1)
- Companion Python: https://github.com/shahzaib-574/MarketCipherTrading/blob/main/backtest_vwap_momentum.py (blob 7d78e4e34dec86d8a6a56562a9a2f442bb797138)
- Copyright/license status remains unverified. Research the rules, do not redistribute third-party code without authorization.
- Author-published BTCUSDT 4h 2025 +16.27%, PF 2.13, 19 trades is NOT independently reproduced.

## Exact candidate
- 4h long-only; 100% equity per source, one position, 12 complete 4h-bar cooldown.
- 21/55/200 EMA; ROC(10)>0; RSI(14)>52; MACD(12,26,9) histogram positive and rising; +DI>-DI with ADX(14)>=14; close>EMA21; EMA21>EMA55; close>prior close: ALL 7 momentum-score tests must pass.
- Close>EMA200, EMA21>EMA55, close>EMA21; 4h VWAP positive slope >=0.01 ATR(14); close above VWAP, <=1.5 ATR extension; 4h range <=2.5 ATR; candle LOW<=VWAP+0.75 ATR and close>open and prior close.
- At completed signal 4h close submit market entry for next eligible 1m open, no intrabar signal peeking. Store signal-bar ATR for 2.6 ATR stop; use original Pine timing semantics for when stop becomes active and when position is considered opened. Exit when 4h close<VWAP-0.75 ATR or score<=1 or EMA21<EMA55; next 1m open. Original Pine's ta.vwap(hlc3) intraday session anchor and fallback must be validated against 4h UTC exchange sessions, not approximated by a generic moving VWAP.
- Baseline source Pine: 0.06% commission each side and 2 ticks slippage; separate user-requested Delta screen: 0.05% each side +18% GST on fees, 0 price-point slippage. Funding unavailable = UNMODELED. Original source risk/qty may not match Delta margin; account NAV and lot feasibility must be separate.

## Mandatory previous-work comparison
1. Stage25: https://github.com/rajkumar0rk/BTC-Analysis/blob/research/stage25-new-trend/analysis/independent_stage25_hourly_trend/RESEARCH_REPORT.md — 2,880 tested 1h momentum_accel/inside_bar/donchian configurations; optional 4h context, 1m stop-first, ATR stops and fixed/trailing exits. Its momentum_accel lookback-24, stop-2.5 ATR trail-3R returned -16.77% net in 2025 and -9.05% net in 2026 for the reported 3x model. Fusion VWAP uses a **7-condition simultaneous 4h impulse score, session VWAP pullback and score/VWAP invalidation exit**, rather than Stage25's 1h impulse and fixed/trailing R exits.
2. Stage13: https://github.com/rajkumar0rk/BTC-Analysis/blob/main/analysis/institutional_discovery_stage13_4h_1h_15m/RESEARCH_REPORT.md — 4h trend + 1h EMA pullback + 15m breakout with 2R/3R and time-based exit; negative after-cost outcomes. Fusion uses same-timeframe 4h VWAP/impulse score, no breakout confirmation, dynamic momentum exit; partially overlaps trend/pullback thesis.
3. Prior trend-following and VWAP strategies may still overlap; before executing, compare the underlying scripts, not only the summaries.

**Decision: PARTIAL OVERLAP — approved differential for a SINGLE SOURCE-FAITHFUL BASELINE ONLY**, conditional on script-level comparison confirming no equivalent 7-condition momentum-score/VWAP entry and exit has already been tested. Do not tune parameter grids or call this NEW just because it has a new name. If script-level inspection reveals equivalent causal signal and execution, change decision to SKIP.

## Data/implementation gate
Authentic Delta India BTCUSD 1m compressed archives at data/delta_india/BTCUSD/1m/ must be accessed and their byte checksums, minute continuity and UTC->IST monthly boundaries independently validated. Jan 2025 UTC start excludes first 5.5 IST hours; October 2026 completeness conflicts across manifest and old gate; never claim 22 full months without direct verification. No data bytes or executable historical workflow were available in this tool session; no backtest, ledger, PF, or account NAV was generated. The next task must obtain the actual data and executable environment, run original settings in BTC2025 with conservative stop/gap fills and fee/GST, save artifacts, then freeze before BTC2026/ETH. Never use 2026 to tune.
