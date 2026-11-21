# Independent big-winner source audit — 2026-11-21 09:54 IST

Scope: source discovery only; **NO new BTC backtest run**. Do not count published results as independently reproduced. Existing volume-absorption experiment run 44635317067 was negative and remains rejected. Latest repository-wide Actions runs checked; none identified as a newer big-winner experiment in first 100, but branch-specific exhaustive audit remains necessary.

## Sources

1. **sird, Bitcoin SuperTrend Strategy**, Roboquant listing https://roboquant.dev/t/c630aaf2-3d6c-480f-ae16-82478a385012 (version 1, 2026-11-17). CME Micro Bitcoin MBT, 5m, 2021-12–2026-10, reported 1321 trades, +230.8%, PF 1.32, DD 16.3%, win 37.2%. Published logic: SuperTrend(10,5) flip with rising/falling 200 SMA and 52-bar Kaufman efficiency >=0.05; protective SuperTrend stop and opposite flip exit; flat contracts 2. Publisher permits remix with attribution. Missing downloadable exact executable source, exact fills and fees. **BLOCKED for faithful reproduction**; also economically overlaps prior SuperTrend studies; do not represent as novel without novelty gate.
2. **MAKSAT-DEL, mtf-breakout-bot**, https://github.com/MAKSAT-DEL/mtf-breakout-bot . BTCUSDT 1h/4h/daily, ATR stops/trailing, ADX/volume; author reports 209 trades, 42.1% win, PF 1.46 over ~3.2 years. Need inspect main.py and licensing, commit SHA, causal signal timing before acceptance; live_bot.py must never execute. **INCONCLUSIVE**.
3. **pplonski, turtle-trading-python**, https://github.com/pplonski/turtle-trading-python . BTCUSDT crypto Turtle backtest, LICENSE present, code backtest.py. Requires pinned SHA and rule-level inspection. Turtle breakout mechanism likely overlaps earlier Donchian work; novelty gate before use. **INCONCLUSIVE**.
4. **JuRose99, turtle_strategy**, https://github.com/JuRose99/turtle_strategy . Author-reported 32 trades, PF 1.98, 31.2% win on CSI 300 ETF 2018–2026, long-only. Not BTC evidence and sample small. **LOW PRIORITY**.

## Next execution step
Read this branch's newest task-specific ledger and all its Actions runs, then inspect external repo source and license at pinned commit. Accept only complete causal rules; build native BTC2025 zero-slippage screening on genuine Delta 1m with two-sided 0.05% commission and 18% GST. Do not stress 0.5/5-point slippage unless positive expectancy passes. Funding unmodeled if missing. Preserve full 22 IST months, trade ledger, NAV and losses. No claim of profitable strategy. No other branches, automations or live accounts changed.
