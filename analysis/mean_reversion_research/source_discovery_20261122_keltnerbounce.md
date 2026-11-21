# Mean Reversion source discovery — 2026-11-22 — KeltnerBounceV1

Status: SOURCE RECOVERED; NOT APPROVED FOR BTC BACKTEST; NO NEW RUN. This is a source-audit checkpoint, not a strategy result or novelty approval.

Source: IvPalmer/Master-Trader, exact historical commit 912d9ff1cb0e638e52131950d2d82a56f2ad428e, path ft_userdata/user_data/strategies/KeltnerBounceV1.py, blob SHA 0bab8240cbe5cfb4c3ba949c96f8478bb231eb22.
URL: https://github.com/IvPalmer/Master-Trader/blob/912d9ff1cb0e638e52131950d2d82a56f2ad428e/ft_userdata/user_data/strategies/KeltnerBounceV1.py
Publisher report: https://github.com/IvPalmer/Master-Trader/blob/912d9ff1cb0e638e52131950d2d82a56f2ad428e/docs/keltner-bounce-v1-validation.md
License: UNKNOWN; LICENSE and LICENSE.md not found at this commit. Do not copy source into our repository absent license clarification; independently implement rules only if permitted and novelty approved.

Exact historical source rules: 1h spot long-only; 25-close SMA minus 2.5 times 25-period SMA of true range as lower channel; close crosses from at/below to above lower channel; current volume >1.75 times SMA20 volume; BTC/USDT 1h close > BTC/USDT SMA50; enter on next eligible completed-bar execution. Freqtrade minimal ROI: 0m 10%, 360m 7%, 720m 4%, 1440m 2%; stoploss -7%; trailing positive 3% activated at +5%; no exit signals; startup 200 candles. The later main version is DIFFERENT (-6% stop, 120h stale-bounce custom exit); do not mix versions. Protections cooldown 2 bars, global stoploss guard 2 stops in 72 bars, suspend 24 bars. Freqtrade stake and spot-wallet concurrency need explicit parity assessment.

Publisher claims: 18-pair backtest Jan 2023-Apr 2026, Lab 153 trades, +51.85%, PF 1.99, max DD 9%; Freqtrade 149 trades, +51.47%, PF 1.58, max DD 12.9%. Its validation report specifically WHITELISTS ADA ARB AVAX BCH BNB DOGE HBAR LINK LTC NEAR SUI TRX UNI XRP ZEC, BLACKLISTS ENA ETH SOL; BTC is not an included traded pair. Publisher results CANNOT be presented as BTC evidence; their strategy has explicit post-selection pair filtering and 4/6 profitable Freqtrade half-year windows.

Novelty gate: codex/STRATEGY_NOVELTY_GATE.md requires full Stage19/23/24 comparisons and a committed NOVELTY_CHECK.md before launch. Distinct hypothesis worth evaluating: channel CROSSBACK with current volume expansion and external BTC SMA gate versus MR002 VWAP z crossback with previous-bar volume; but previous Stage19/23 envelope/sweep studies remain to compare. BTC as both signal instrument and gate creates materially different economics. Do not approve based on names.

Critical replay issues: authentic Delta India BTCUSD 1m volume semantics and complete 1h aggregation; completed informative 1h BTC gate (avoid future leakage); exact ATR is simple moving average of true range, not Wilder ATR; next 1m open; stop-first same-minute ambiguous fills and gap-through stops; tiered ROI/trailing ordering; account NAV with 0.05% per-side fee plus 18% GST; zero first-screen slippage; missing UTC 2026-10-31 and first 5.5 IST hours of Jan 2025; funding unmodeled. 2026 already researched, not pristine holdout.

Decision: SOURCE CANDIDATE ONLY. No backtest launched; cannot claim profitable BTC edge. Next action: inspect Stage19/23/24 scripts and license/provenance, decide novelty and permissions, then implement and launch genuine historical replay only if approved. MR002 original negative baseline preserved unchanged.
