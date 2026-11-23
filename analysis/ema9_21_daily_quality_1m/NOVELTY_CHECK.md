# Novelty check — 1m EMA9/21 quality pullback

Decision: **NEW — distinct 1-minute microtrend signal / incremental hypothesis**.

## Pre-registered setup
- Delta India BTCUSD 1m bar OHLCV, 2025-01-01 through 2026-10-31 UTC (22 UTC archive months).
- Long: 1m EMA9>21 with 21 up over three bars; completed 5m/15m EMA9>21; a prior 1-3 minute low touched EMA21; 1m close crosses above EMA9 on bullish bar; ADX14>=18; +DI>-DI; 1m volume>=1.1x SMA20, close above session VWAP.
- Short symmetrical. 1m EMA9/21 crossover is **not** required for entry.
- Entry next 1m open, at most one entry per IST day and one open position, all seven days.
- Stop: five-bar high/low +/-0.2 ATR14; only risk between 0.5x and 3x ATR, and 2.5R >=0.18% of signal close. Target 2.5R; stop-first if both touched in a minute; no forced timeout.
- 0.05% taker fee/side, +18% GST on fees, 5 quote-point adverse slippage/side; sensitivity at 0.5 points/side. 10% notional equity allocation with no leverage. Funding not modeled; show limitation.

## Closest previous studies
- `scripts/research_wide_monthly_stage23.py` / `analysis/institutional_discovery_stage23_broad_5m_monthly/RESEARCH_REPORT.md`: 5-minute monthly price-action, some EMA pullback. **Different** 1m EMA9/21 reclaim trigger, prior-HTF 5/15 trend, anchored VWAP/ADX/DI/volume combination and once-per-IST-day.
- `scripts/research_trend_pullback_breakout_stage13.py` / `analysis/institutional_discovery_stage13_4h_1h_15m/`: higher-timeframe 4h/1h/15m pullback breakout, not this one-minute rule.
- `scripts/research_one_trade_every_day_200.py` / `analysis/one_daily_trade_200_points/`: **forced** NY-day one-trade/200pt tests; this allows zero-trade days and IST-day lock.
- Stage24 branch uses 15m structural patterns; Stage25 hourly trend; neither matches this 1m conjunction.

## Quality / validation
Source `data/delta_india/BTCUSD/1m/manifest.json` declares all 22 months complete in the currently observed archive, including 2026-10 (older codex note says 2026-10-31 was missing). Runner must reject gaps rather than fill. Train 2025; recheck 2026 (**not pristine unseen holdout**, prior research exposed 2026). Separate results by each calendar month. This is research, not a validated strategy or a guarantee of daily profit.
