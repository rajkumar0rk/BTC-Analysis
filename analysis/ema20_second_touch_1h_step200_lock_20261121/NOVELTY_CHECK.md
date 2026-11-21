# Preregistered correction: BTC step-lock every +200 points, not a conventional trailing gap
Date 2026-11-21. Research-only.

## Precise user rule
BTC LONG at 80,000: until 80,200, NO stop. First arrival at 80,200 locks gross profit level at 80,200. If next traded price drops below it (e.g., 80,199), exit. If price rises uninterrupted to 80,400, **lock jumps to 80,400**. If price drops below it (e.g., 80,399), exit. Next steps at 80,600, 80,800, etc. Do NOT use peak-200 or peak-1 continuously. This is a **stepwise ratchet of the locked gross-profit level**, not a continuous trailing distance.

Short: entry 80,000; milestone levels 79,800, 79,600, etc.; exit when price crosses ABOVE most recently reached milestone. Lock never retreats. Strict *breach after milestone* required: at activation tick itself, do not exit simply because level equals current price.

Formula: let E=executed entry, S=200 BTC points, F=max favorable observed price excursion along a hypothetical path, n=floor((F+epsilon)/S). When n>=1, lock LONG=E+n*S and lock SHORT=E-n*S. On adverse retracement below locked level for LONG or above for SHORT, exit. For numerical example with discrete $1 BTC price increments, trigger at lock-1 for long and lock+1 for short; these are illustrative breach ticks, not verified exchange minimum tick. ETH uses a percentage-equivalent milestone and breach tick: S_ETH=200*ETH executed entry/last complete 1m BTC close, eps_ETH=1*ETH executed entry/that BTC close. Those distances are frozen at entry.

NO fixed TP, NO separate stop before first +200, NO ATR trailing, NO reversal exit, NO timed exit; one entry max per completed 1H Supertrend(10,3) direction cycle; EMA20 second distinct post-flip 1H candle wick touch based on previous fully completed 1H indicators; no 1H volume/vol filters. Entry and exits approximated from historical 1m OHLC, starting equity $1000 with 1x evolving notional, 0.05% taker fee per side and GST 18%, 0.02% adverse slippage per side, no funding/tick/actual margin/liquidation/book.

## Data limitation and method
Original SHA-verified Delta India BTC & ETH 1m OHLC Jan 2025–Oct 2026 (22 IST months). Cannot assert ordering, precision, real first breach fill, or realized profit of a 1-point strict breach without tick/quote/orderbook data. As exploratory sensitivity only, replay two hypothetical continuous within-1m paths O-H-L-C and O-L-H-C, letting milestone and breach transitions occur within the synthetic sequence. Neither is a reliable upper/lower bound because actual tick prices may oscillate. Use preceding BTC 1m close for ETH scaling to avoid leakage. Model mark-to-market floating and month-end equity; report insolvency if it occurs even if accounting later recovers. End-of-sample hypothetical forced close is NOT a strategy exit. These figures cannot support claims of real execution feasibility or a tick-level win rate.

## Prior comparisons
- `analysis/ema20_second_touch_1h_activation200_trail1_20261121/`: previous correction that moved stop continuously peak-1, WRONG; two hypothetical OHLC paths.
- `analysis/ema20_second_touch_1h_activation200_trail200_20261121/`: +200 activation then actual 200 price point gap, WRONG.
- `analysis/ema20_second_touch_1h_one_trade_per_st_20261121/`: fixed 200 point TP, no stop; not same.

Novelty gate: PARTIAL OVERLAP — APPROVED corrective step-lock variant. No hyperparameter search and 2026 is NOT pristine out-of-sample.
