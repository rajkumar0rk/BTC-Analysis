# Corrected user intent: 1H first EMA20 touch, NO volume or volatility entry filter

2026-11-22 clarification from user: "i did not tell you to enablt Volume filter Volatility filter for 1h?" Confirmed: prior authorization to enable filters was **15M-only**, not 1H. Previous 1H +3×ATR profit figures were incorrectly presented as though matching the desired unfiltered 1H strategy.

## Exact corrected study (no tuning)
- BTCUSD and ETHUSD independently; 1H Supertrend(ATR10, multiplier3), EMA20, first 1H candle touch **after** a confirmed ST flip. Ignore flip candle. Entry on 1-minute EMA20 touch of EMA20 from last fully completed 1H bar; one trade per ST regime; both LONG and SHORT.
- **NO VOLUME ENTRY FILTER. NO VOLATILITY/ATR EXPANSION ENTRY FILTER.** ATR(14) is calculated **only for the trailing stop distance**, and doesn't gate entries. Avoid carrying 15M-only gating into 1H.
- **NO fixed TP**; compare 2×ATR(14) vs 3×ATR(14) trailing stops. ATR(14) = last completed 1H Wilder ATR14 and is FROZEN at entry for a fixed-distance trailing stop. Stop starts at entry ∓ multiplier×ATR14 and ratchets only favorably with 1-minute favorable extremes. On stop breach exit at stop (gap through at 1m OPEN, adverse slippage).
- Independently, confirmed opposite **1H Supertrend flip** exits at next hour first 1m OPEN. Whichever exit happens first. Do not exit at line touch alone, don't add any TP or hidden distance-to-ST-line entry filter; it is irrelevant once TP is removed.
- BTC/ETH Delta India Jan 2025–Oct 2026, 22 complete IST months, SHA256 checked 1m OHLC, no extra weekday filter; 0.05% taker each side+GST18% on fees, adverse 0.02% slippage each side; $1000 starting notional 1× evolving equity per instrument / multiplier.
- Synthetic within-minute O-H-L-C and O-L-H-C for EMA entry/stop sequence; not real ticks or rigorously proven bounds. No funding, spreads, real order-book execution, liquidation, margin, latency. Previously researched historic data, not untouched out-of-sample.
- Results: trade counts/win/loss, ATR stop/confirmed ST flip exits, PF, 22-month net, positive months, max floating DD, ledger and monthly MTM, compare directly against **filtered** 1H with separate labels.
- Novelty: **user correction**, approved differential from `analysis/st_firsttouch_1h_filtered_atrtrail2x3_20261122/`. Research branch only, no merge to master.
