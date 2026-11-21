# Iteration 11 — SignalFlow original configuration recovery (2026-11-21 IST)

Status: SOURCE CONFIG RECOVERED; NOT APPROVED FOR BTC BACKTEST; NO BTC TRADES EXECUTED.

## Immutable primary source
Creator: Bpmiller32; repository https://github.com/Bpmiller32/SignalFlow
Pinned commit: 48f999e98d450fab62495de9b3a148ec858e86f0
Original configuration: https://github.com/Bpmiller32/SignalFlow/blob/48f999e98d450fab62495de9b3a148ec858e86f0/server/strategies.json
Source blob SHA: cda7ab2062b98bfad0c12efce125744a630b6b0d
README: https://github.com/Bpmiller32/SignalFlow
License: not verified; do not copy source into research without checking.

## Exact recovered default parameters
Original assets: SPY, AAPL, MSFT, NVDA, GOOGL, META, GME (Alpaca US equities, NOT BTC).
Session NY 09:30–09:35 opening range; cutoff 11:30 NY; market close 16:00 NY; max 2 trades/day; no overnight holds.
Inverse mode ENABLED (fade of original directional setup).
Opening range minSize=0.10 maxSize=2.0 minStrength=3.0 maxPremarketGap=3.0 skipEarningsDays=true.
Breakout volumeMultiplier=1.2 minAbsoluteVolume=5000 maxFvgWindowMinutes=15.
FVG bodyPercent=40 minRangePercent=0.08 overlapTolerance=2.0 closePositionPercent=35 requireVolumeConfirmation=false.
Position sizing FIXED $1000 notional; accountRiskPercent=1 (not selected); minValue=100 maxValue=10000 adaptive=true weakSignalSizePercent=75.
Risk RR=2 stopLossBufferPercent=0.05 useAtrStops=false; ATR14 multiplier1.5 inactive for initial stop; trailing activated at 1R with ATR multiple1.5; partial exit 50% at 1R.
The README reports publisher paper results Jan 1–Apr 6 2026: 81 trades, 60.5% wins, +$88.74, PF1.74; Jun15–26: 18 trades, PF2.18; Mar6–Apr6: 35 trades, PF0.81. These are overlapping and publisher-only, with zero fees/slippage. No BTC result.

## Causal and novelty decision
Configuration is now recoverable but exact source onCandle/evaluatePosition, opening-range strength formula, FVG overlap semantics, stop ordering, and premarket/earnings inputs still need source verification. Default stock-specific dollar range, absolute share volume and earnings-day filter are not portable to BTC without altering the original hypothesis. NY daylight savings must be respected; 09:30 NY is 19:00 IST in winter and 19:00? Verify: 09:30 EST = 20:00 IST; 09:30 EDT = 19:00 IST. Do not hardcode one IST session time.
Closest prior art: Stage24 15m breakout/retest/squeeze; Stage25 hourly breakout; prior session failed-breakout research. Distinctness of breakout + subsequent FVG + inverse mode is UNRESOLVED. Decision: HOLD, not NEW. No parameter substitution or backtest permitted until source code, novelty, licensing and BTC transfer specification are verified.

## Execution blocker
GitHub connector can fetch individual known paths, but no candidate runner has been source-faithfully implemented. Archive validation already passed in workflow https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44902737237. The archive validation is NOT a strategy backtest. Next: recover exact TypeScript strategy source and novelty compare, then preregister a BTC adaptation with explicit economic differences, implement next-open 1m fills and execute fee+GST historical replay. Do not infer profits.
