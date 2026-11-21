# Incremental research: +200 activation, 1-point retracement from best price — 1H EMA second touch
Prepared 2026-11-21, prior to backtest. RESEARCH ONLY: 1-minute OHLC can NEVER verify the first $1 retracement tick order.

## Correct user-defined exit
Example: long entry BTC $80,000. When raw traded market price reaches $80,200, trailing is ARMED, and active trailing exit threshold is immediately $80,199 (peak minus **1** raw BTC price point). If the high advances to $80,400, trailing exit threshold becomes $80,399; first tick crossing threshold exits. Shorts reverse: entry $80,000; activation at $79,800; initial exit threshold $79,801; if down to $79,600 threshold advances to $79,601. **There is NO fixed TP and NO stop before +200 activation, NO extra SL, no ATR exit, no opposite-Supertrend exit or timeout**. Trail distance is exactly 1 BTC price point, NOT 200.

ETH both distances use an ex-ante percentage ratio frozen at entry: activation distance = `200 * ETHentry / preceding completed 1m BTC close`; trail distance = `1 * ETHentry / preceding completed 1m BTC close`. Do not accidentally use ETH 200/1 absolute points.

Entry remains the second distinct 1H-candle EMA20 touch in confirmed Supertrend(10,3) direction; exclude flip candle; enter when 1m path FIRST crosses last completed 1H EMA20 during second touch candle, not on 1H close. Only one entry per Supertrend direction cycle and one concurrent trade per asset; no 1H volume or volatility filters.

## Data-resolving caveat & two path hypotheses
Full Jan 2025–Oct 2026 historical 1m BTC and ETH OHLC data are present, hash verified but NOT tick-by-tick prices. A 1-point retracement could happen numerous times inside a 1m bar. Cannot prove tick ordering, exact level execution, exchange tick size, latency/slippage, or liquidity from 1m bars. Refuse false claim of an accurate tick-level backtest.

To provide honest exploratory results, replay TWO plausible *synthetic* within-1m paths, for each asset separately:
- O→H→L→C
- O→L→H→C

Allow activation and 1-point stop triggering within same 1m candle according to the ordered sequence. Stop moves monotonically behind each path's favorable extreme; order is represented as linear segments. On stop gap fill at worst of opening/stop, with adverse slippage; do not claim either scenario is confirmed historical order, and neither scenario is a rigorous performance bound because actual ticks can oscillate far more.

The synthetic path model changes entry timing as well: if EMA is touched on second distinct 1H candle, the first ordered segment crossing the last completed 1H EMA enters. No entry minute blind spot. Use $1,000 initial capital and 1x current realized equity notional per asset; 0.05% taker per side plus 18% GST, and 0.02% adverse slippage. Only force sample-end exit to account for an open position. Month-end marked-to-market PnL, max adverse exposure, insolvent-equity flags, fees. Funding, actual liquidation, bid/ask, and slippage path missing; do not interpret modeled positive returns as live executable.

## Novelty decision
Closest baselines:
1. `analysis/ema20_second_touch_1h_activation200_trail200_20261121/` (initial user misunderstanding) +200 activation, 200 BTC-point trailing (BTC +1.92%, ETH +14.95% but simulated ETH equity below zero).
2. `analysis/ema20_second_touch_1h_tp200_trailing200_20261121/`: fixed 200 TP plus immediately active 200-point trailing; NOT the user's rule.
3. `analysis/ema20_second_touch_1h_one_trade_per_st_20261121/`: 200-point TP only.

**Gate: PARTIAL OVERLAP — approved exact correction**; evaluate 1-point retracement specifically. Critical new price path uncertainty requires two hypothetical paths and transparent caveat. 2026 history already mined; no pristine OOS.
