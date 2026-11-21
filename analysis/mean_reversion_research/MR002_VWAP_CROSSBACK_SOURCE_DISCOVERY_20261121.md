# MR-002 source discovery — 2026-11-21 15:33 IST

Status: SOURCE DISCOVERY / NOVELTY REVIEW PENDING; **NO BACKTEST LAUNCHED**. This is not a profitability finding.

## Third-party executable source
- Creator: vaultik; https://github.com/vaultik/algo-trading-system
- Source: https://github.com/vaultik/algo-trading-system/blob/main/src/wfo.py and src/loader.py and src/paper_trading.py. Pin a commit SHA and confirm license before reproducing or copying.
- Original market: Bybit 5m cryptocurrencies, not Delta India BTCUSD. Current WFO COINS excludes BTC (DOGE, LTC, RENDER, TON, SUI, CRV, AAVE, FET). No BTC publisher result should be inferred.
- Source strategy: rolling 24-hour volume-weighted VWAP and rolling dispersion; Z=(Close-VWAP)/SD. A signal requires Z crossing *back inside* +/-3 standard deviations, with preceding-bar RVOL>=2.5; enter next 5m bar open. Symmetric long/short. Scale out 50% at VWAP +/-1 sigma toward center, move stop to breakeven; remainder targets VWAP. Structural stop at VWAP +/- (Z threshold+buffer)*SD, with buffers 0.5,1.0,1.5; 2/4/8/12-hour time stops. WFO uses 0.04% Bybit fee, leverage 3, time-window optimization and a minimum five training/test trades. Exact stop/target priority and volume definitions must be verified against executable source.
- This is economically distinct from simple RSI+BB fade: signal waits for *re-entry* after a volume-confirmed VWAP extreme and scales out to an estimated transaction-weighted fair value. However, earlier Stage19/23 sweep and reversal models might overlap; do not assert NEW before comparison.
- Risk: VWAP can move with price, violent trends can overwhelm 3sigma stops, stop and TP can collide in same minute; 5m-only published fills are not proof of 1m-realizable returns.
- Required next action: inspect source commit, license, complete WFO execution logic, compare Stage19/23 and Stage24 source implementations; create separate MR002/NOVELTY_CHECK.md with verdict. Only if NEW/approved differential, implement source-faithful BTC 5m signal, genuine Delta 1m execution, fee+GST zero-slippage first screen, full sequential NAV/22-month ledger and actual GitHub workflow artifact. Do not substitute published Bybit performance.
- Other discovered sources: https://github.com/9600dev/mmr/blob/master/strategies/vwap_reversion.py (VWAP+RSI potentially overlaps MR001); https://github.com/kayasolomon/anchored-vwap (indicator library, not full trading strategy); https://quantarenas.com/code/mr-06-z-score-mean-reversion/ (SPY daily z-score + volatility and MA filters, requires cross-market adaptation).

No existing branch or main mutated by this note except isolated MR branch. No live trading.
