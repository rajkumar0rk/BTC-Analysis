# Step 10 — causal market-structure directional override, with 477 daily trades

**Novelty gate: PARTIAL OVERLAP — approved differential**, pending independent validation. This is NOT a new claim that simple EMA/Donchian/trend signals are profitable: those were researched in institutional stages 7, 13, 19, 23, 24, 25, plus `scripts/research_btc_every_weekday_reset_step1.py`, `research_btc_daily_online_direction_step6.py`, and `research_btc_daily_causal_neighbors_step8.py`. The differential is a **conditional direction override on an already frozen all-weekday trading system with existing online selected directions, at identical entry times/exits**, never omitting a day. No prior experiment reported this exact overlay and its effects on the failing 2026 fallback component.

## Frozen benchmark and constraint
- Baseline Step 8: **477/477 IST Monday–Friday trades** 2025-01-02–2026-10-30, 2025-only selected. Exactly 277 winning days, **+21.423313%** modeled Scalper Offer net, 15/22 profitable months, 3.008746% max closed DD; **2026 unchanged from Step 6**, 130/217 positive days and +12.322236% return.
- Step 6 benchmark: 275/477, +17.7862% modeled net, 16/22 profitable months, 3.265838% max DD.
- Frozen entry times: first qualifying 18/19/20 IST prior-completed 5m volume >=1.5x prior20 5m mean, else forced 21:00. Exact Step 8 causal online event/fallback direction is the default.
- Exits UNCHANGED: event SL0.5%, gross TP3%, 30m max, lock +0.10% after +0.25% favorable; fallback SL0.5% or 0.75% depending on completed previous 5m volume ratio >=1.25, trail activation +0.35% and distance0.20%, TP3%, max30m; stop first within same 1m, protective updates next bar only; 1m OPEN fills and timeout.
- BTCUSD Delta India genuine 1m Jan2025–Oct2026, full 477 IST weekdays; zero skipped trades, 1× account notional and 100% tested exposure, Monday-Friday only.
- Hypothetical regular Scalper Offer previously activated, opening taker0.05% +18% GST; closing leg waived only for <=30m qualifying duration; also compute standard 0.05% taker both legs +GST. Adverse 5 BTC quote-price points slippage each side. No actual historical offer qualification, bid/ask spread/orderbook depth, funding, latency, margin or liquidation model.

## Frozen, non-exit-changing structural overrides
At each day's **already fixed** entry minute, compute ONLY previously completed 1m candles, never current/future:
- 5m,15m,60m,240m returns (last completed 1m CLOSE relative to preceding OPEN);
- 60m and 240m rolling high/low location; previous 120m Donchian high/low EXCLUDING the latest 5m;
- current last close relative to SMA20/SMA60 of last completed 1m CLOSES, and 20m vs 60m SMA trend; high/low vs the 09:00 IST session range; anchored 09:00 session VWAP based on already completed 1m volumes and HLC3;
- standard deviation over last60 completed 1m closes for z-score;
- 5m completed candle OHLC body sign and prior5m candle body sign for engulfing.
All features use only preentry data; nothing from current incomplete 1m bar or from later daily realized results.

Frozen 14 kinds × 2 intensity thresholds or regimes, with a hold-original/no-override default:
  1. 60m range edge FOLLOW (pos>=.8/.9=>LONG, <=.2/.1=>SHORT).
  2. 60m range edge FADE (pos>=.8/.9=>SHORT, <=.2/.1=>LONG).
  3. 240m range edge FOLLOW (same thresholds).
  4. 240m range edge FADE (same thresholds).
  5. 60m momentum FOLLOW if abs return >=0.20% /0.40%.
  6. 60m momentum FADE, same thresholds.
  7. 240m momentum FOLLOW if abs return >=0.35% /0.70%.
  8. 240m momentum FADE, same thresholds.
  9. Donchian 120m breakout FOLLOW if last-close is >upper prior 120m excluding most recent 5m / further by >=0.10%; short mirror.
  10. Donchian 120m breakout FADE, same thresholds.
  11. SMA20 vs SMA60 trend FOLLOW if relative gap >=0.03% /0.08%.
  12. SMA20 vs SMA60 trend FADE, same thresholds.
  13. 09:00-session VWAP deviation FOLLOW if |deviation|>=0.15%/0.30%.
  14. 09:00-session VWAP deviation FADE, same thresholds.
- Apply each structural rule ONLY to (a) volume-event trades, (b) forced fallback trades, or (c) both. If no threshold condition, retain Step8 original chosen direction. The rule may set either LONG or SHORT, with the same entry minute as original. **No abstention and no changes in exit.**
- Total **14×2×3 = 84 structural override scenarios** + no-override baseline, repriced under standard and hypothetical Scalper costs. No lookahead, any candidates have exactly 477 daily trades.

## Locked selection and audit
- Choose using **2025 only** (260 sessions): require 2025 net account return >=8.10265% (Step8 historical train), 2025 winning days >=147 (Step8) and max 2025 closed-trade DD <=3.00875% (Step8); from eligible rank by profitable days in 2025 then 2025 net return then lower DD. If NO variant improves these, retain original Step8. **Do not loosen constraints or select on 2026.**
- Print exact outcomes separately 2025 and 2026, 22 individual monthly returns, worst month/day, max drawdown and consecutive losing days. Compare to Step8 and Step6. Show count of changed direction days separately for years, event versus fallback, under each fee assumption.
- For every model, verify 477 entries/unique dates and no weekend trading. Baseline exact per-day parity required with Step8 under BOTH cost models before reporting. For 2026: reject if net, profitable days, drawdown or monthly consistency worsen, and do NOT tune 2026 after observing results. November was already researched, so is not a pristine unseen holdout. Full-period best-by-hindsight is diagnostic only.
- Important: 2025 and 2026 data have been repeatedly researched, and selection constraints themselves derive from the earlier Step8 results. This is only incremental historical research, not a statistically new strategy discovery or deployment approval.

## Provenance
Repo branch base: `research/btc-daily-causal-neighbors-step8`; new branch `research/btc-daily-structure-overlay-step10`. All modifications confined to new analysis/script/workflow files, never master.
