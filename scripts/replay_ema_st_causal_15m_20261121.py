#!/usr/bin/env python3
"""Research-only 15-minute EMA20 + Supertrend causal backtest.

Signals AND risk/exit decisions use 15-minute OHLC only. No hidden 1-minute
sequence and no fictitious open-high-low-close intra-bar path.

Rules
-----
* Signal calculated from a *completed* 15m candle, filled at NEXT bar's open.
* Initial stop is available immediately on the entry bar.
* At each 15m bar, existing stop / estimated liquidation are checked first.
* If no stop/liq trigger, newly observed favorable extreme may adjust trailing
  stop only for NEXT 15m bar. Never activate & stop on the same bar.
* Supertrend flip from the previous fully closed candle exits at current open.
* If the open gaps beyond a stop, fill at open (not at the stop threshold).
* Stop touches use an idealized stop-price fill; cannot reproduce spread,
  market impact, tick-order, latency or historical liquidation fills.
* Liquidation is a traded-OHLC proxy, NOT exchange historical mark-price.
* 100x, $10 isolated initial margin, no auto margin increase, no scaling.
* Two fee hypotheses: standard taker and assumed 30-minute Scalper waiver;
  historical offer entitlement is unknown. 18% GST on modeled fees.
* Funding, spread, and intrabar adverse selection are not included.

Reuses the original validated 15m indicator and data-resampling implementation.
The original 1m-execution model is NOT changed by this script.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from replay_ema_st_15m_entries_1m_exits_20261121 import load

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis" / "ema_st_correct_15m_20261121"
OUT.mkdir(parents=True, exist_ok=True)

START_EQUITY = 100.0
MARGIN_PER_TRADE = 10.0
LEVERAGE = 100
MAINTENANCE = 0.0025
TAKER = 0.0005
GST = 0.18
LIQ_FEE = 0.0005
SCALPER_WINDOW = 30

RULES = {
    "model": "CAUSAL_15M_BAR_CLOSE_TRAILING",
    "signal_candle": "15m",
    "execution_candle": "15m",
    "entry": "next 15m open after completed 15m signal",
    "entry_filter": "same original EMA20+ST(10,3), ATR ratio >=1.0, volume ratio >=1.5",
    "initial_stop": "2x ATR14 on last closed 15m signal",
    "protective_order": "monitor 15m high/low with stop priority",
    "trailing": "BTC activation 150, distance 50; ETH equivalent scaled at entry/80000",
    "trailing_update": "at 15m close using high/low; effective from next 15m open only",
    "conflicts": "old stop/liq wins over new trail if both touched in one candle",
    "supertrend_exit": "next 15m open after last completed 15m ST flip",
    "same_bar_reentry": False,
    "account_start_usd": START_EQUITY,
    "fixed_margin_budget_usd": MARGIN_PER_TRADE,
    "max_leverage": LEVERAGE,
    "maintenance_proxy": MAINTENANCE,
    "maker_orders": False,
    "taker_fee_fraction": TAKER,
    "gst_fraction": GST,
    "liquidation_penalty_fraction": LIQ_FEE,
    "scalper_window_min": SCALPER_WINDOW,
    "historical_scalper_offer_verified": False,
    "historical_spread": "unavailable, omitted",
    "historical_funding": "available in archive, not applied in this replay",
    "historical_mark_price_liquidation": "not applied; traded price liquidation proxy",
    "caveat": "15m OHLC cannot prove the sequence or fill price inside a candle",
}


def half_up_to_tick(value: float, tick: float) -> float:
    return max(tick, math.floor(value / tick + 0.5) * tick)


def exit_decision(side, op, hi, lo, stop, liq, flip_exit):
    """Decide on existing stop or exchange-threshold proxy; no price path guessing.

    Returns (idealized_trade_price, reason) or (None, None).
    Protection is assumed active at the candle open, and gets priority over
    a same-candle trailing update. If an open gaps beyond barriers, the fill
    is at the observed open. If a flip is pending, its market exit is at open
    unless an existing barrier was already breached at the open.
    """
    if (side == 1 and op <= liq) or (side == -1 and op >= liq):
        return float(op), "liquidation"
    if (side == 1 and op <= stop) or (side == -1 and op >= stop):
        return float(op), "stop_gap"
    if flip_exit:
        return float(op), "supertrend_flip"
    # Protective threshold that would be touched first if price moves against
    # the trade continuously from an open above/below the barriers.
    barrier = max(stop, liq) if side == 1 else min(stop, liq)
    if (side == 1 and lo <= barrier) or (side == -1 and hi >= barrier):
        liq_first = (liq >= stop) if side == 1 else (liq <= stop)
        return float(barrier), "liquidation" if liq_first else "protective_stop"
    return None, None


def close_and_update_trailing(position, high, low):
    """Update trailing only after candle closes; it cannot affect this bar."""
    p = position
    side = p["side"]
    best = max(p["best"], high) if side == 1 else min(p["best"], low)
    if side * (best - p["entry"]) >= p["activation"]:
        p["active"] = True
    if p["active"]:
        p["best"] = best
        next_stop = best - side * p["distance"]
        p["stop"] = max(p["stop"], next_stop) if side == 1 else min(p["stop"], next_stop)


def simulate(asset, bars, offer, liquidation_fill, slippage):
    d = bars.reset_index()
    ts = pd.DatetimeIndex(d["dt"])
    op = d.open.to_numpy(dtype=float)
    hi = d.high.to_numpy(dtype=float)
    lo = d.low.to_numpy(dtype=float)
    cl = d.close.to_numpy(dtype=float)
    ema = d.ema.to_numpy(dtype=float)
    atr = d.atr14.to_numpy(dtype=float)
    direction = d.dir.to_numpy(dtype=int)
    ar = d.atr_ratio.to_numpy(dtype=float)
    vr = d.volume_ratio.to_numpy(dtype=float)

    tick = .5 if asset == "BTC" else .05
    lot = .001 if asset == "BTC" else .01
    equity = START_EQUITY
    peak = START_EQUITY
    max_dd = 0.
    position = None
    records = []
    signals = 0
    rejected_equity = 0
    rejected_lot = 0

    for j in range(37, len(d)):
        i = j - 1  # last *closed* 15m signal, never current j
        old_position = position is not None

        if old_position:
            p = position
            flip_exit = (
                (p["side"] == 1 and direction[i] == 1 and direction[i-1] == -1)
                or (p["side"] == -1 and direction[i] == -1 and direction[i-1] == 1)
            )
            xp, why = exit_decision(
                p["side"], op[j], hi[j], lo[j], p["stop"], p["liq"], flip_exit)
        else:
            xp = why = None

        # Entry signals are only actionable at this candle's OPEN.
        # Never use the current candle's high/low/close to decide entry.
        if not old_position and all(np.isfinite(v) for v in (ema[i], atr[i], ar[i], vr[i])):
            side = 0
            if ar[i] >= 1.0 and vr[i] >= 1.5:
                if direction[i] == direction[i-1] == -1 and lo[i] <= ema[i] and cl[i] > ema[i]:
                    side = 1
                elif direction[i] == direction[i-1] == 1 and hi[i] >= ema[i] and cl[i] < ema[i]:
                    side = -1

            if side:
                signals += 1
                ep = float(op[j]) + side*slippage
                n = math.floor(MARGIN_PER_TRADE * LEVERAGE / (ep * lot) + 1e-10)
                if n < 1:
                    rejected_lot += 1
                else:
                    qty = n * lot
                    im = ep * qty / LEVERAGE
                    fee_open = ep * qty * TAKER * (1.0 + GST)
                    if im + fee_open > equity + 1e-9:
                        rejected_equity += 1
                    else:
                        dist = half_up_to_tick(2*atr[i], tick)
                        liq = ((ep - im/qty)/(1-MAINTENANCE) if side == 1 else
                               (ep + im/qty)/(1+MAINTENANCE))
                        act = 150.0 if asset == "BTC" else half_up_to_tick(ep*150/80000, tick)
                        distance = 50.0 if asset == "BTC" else half_up_to_tick(ep*50/80000, tick)
                        position = {
                            "side": side, "entry": ep, "j": j,
                            "stop": ep - side*dist, "original_stop": ep-side*dist,
                            "liq": liq, "bankruptcy": ep-side*im/qty,
                            "qty": qty, "im": im,
                            "activation": act, "distance": distance,
                            "best": ep, "active": False,
                        }
                        # New protective stop is active immediately on the
                        # ENTRY candle; no entry and exit on same open unless gap.
                        p = position
                        xp, why = exit_decision(side, op[j], hi[j], lo[j],
                                                p["stop"], p["liq"], False)

        if position is not None and xp is not None:
            p = position
            ep, side, qty = p["entry"], p["side"], p["qty"]
            price = p["bankruptcy"] if why == "liquidation" and liquidation_fill == "bankruptcy" \
                else xp - side*(0 if why == "liquidation" else slippage)
            minutes = 15*(j-p["j"])
            gross = (price-ep)*side*qty
            entry_fee = ep*qty*TAKER
            scalper_waived = bool(offer and minutes <= SCALPER_WINDOW and why != "liquidation")
            close_fee = 0 if scalper_waived or why == "liquidation" else price*qty*TAKER
            penalty = price*qty*LIQ_FEE if why == "liquidation" else 0.
            gst = GST*(entry_fee + close_fee + penalty)
            # Isolated position loss cannot exceed its initial margin;
            # wallet still pays opening fee separately.
            pnl = (max(-p["im"], gross - penalty*(1+GST)) - entry_fee*(1+GST)
                   if why == "liquidation" else gross-entry_fee-close_fee-gst)
            before = equity
            equity = max(0., equity + pnl)
            realized = equity-before
            peak = max(peak, equity)
            max_dd = max(max_dd, 100*(1-equity/peak))
            records.append(dict(
                asset=asset,
                entry_utc=str(ts[p["j"]]),
                exit_candle_utc=str(ts[j]),
                side="long" if side == 1 else "short",
                entry=ep, exit=price, qty=qty, held_minutes=minutes,
                reason=why, initial_stop=p["original_stop"],
                liq_threshold=p["liq"],
                gross_usd=gross,
                net_usd=realized,
                opening_fee_usd=entry_fee,
                closing_fee_usd=close_fee,
                liquidation_fee_usd=penalty,
                gst_usd=gst,
                scalper_waiver_assumed=scalper_waived,
                equity_before=before, equity_after=equity))
            position = None

        # At the *end* of this completed 15m bar, if trade survives, use this
        # bar's high/low to recompute stop for the NEXT 15m open and later.
        if position is not None:
            close_and_update_trailing(position, float(hi[j]), float(lo[j]))

    trades = pd.DataFrame.from_records(records)
    if len(trades):
        trades["exit_month_ist"] = pd.to_datetime(trades.exit_candle_utc, utc=True) \
            .dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    bymonth = dict(tuple(trades.groupby("exit_month_ist"))) if len(trades) else {}
    monthly = []
    before = START_EQUITY
    final_period = str(ts[-1].tz_convert("Asia/Kolkata").to_period("M"))
    for item in pd.period_range("2025-01", final_period, freq="M"):
        month = str(item)
        group = bymonth.get(month)
        after = before if group is None else float(group.equity_after.iloc[-1])
        count = 0 if group is None else len(group)
        monthly.append(dict(
            month_ist=month, opening_balance_usd=round(before,4),
            net_profit_usd=round(after-before,4),
            monthly_return_pct=round((after/before - 1)*100,2) if before>0 else None,
            closing_balance_usd=round(after,4), trades=count,
            completed_month=month<"2026-11"))
        before = after
    mon = pd.DataFrame(monthly)
    done = mon[mon.completed_month]
    wins = trades.loc[trades.net_usd>0, "net_usd"].sum() if len(trades) else 0.
    losses = -trades.loc[trades.net_usd<0, "net_usd"].sum() if len(trades) else 0.
    stats = dict(
        asset=asset, starting_usd=START_EQUITY,
        ending_usd=round(equity,4),
        net_profit_usd=round(equity-START_EQUITY,4),
        trades=len(trades),
        win_rate_pct=round(100*(trades.net_usd>0).mean(),2) if len(trades) else None,
        net_profit_factor=round(wins/losses,4) if losses else None,
        estimated_liquidations=int((trades.reason=="liquidation").sum()) if len(trades) else 0,
        max_closed_equity_drawdown_pct=round(max_dd,2),
        completed_months=len(done),
        profitable_completed_months=int((done.net_profit_usd>0).sum()),
        losing_completed_months=int((done.net_profit_usd<0).sum()),
        flat_completed_months=int((done.net_profit_usd==0).sum()),
        signals_while_flat=signals,
        rejected_insufficient_equity=rejected_equity,
        rejected_below_one_contract=rejected_lot,
        offer_assumed=bool(offer),
        liquidation_fill=liquidation_fill,
        adverse_slippage_per_side_usd=slippage,
        total_entry_fee_usd=round(float(trades.opening_fee_usd.sum()),3) if len(trades) else 0.,
        total_exit_fee_usd=round(float(trades.closing_fee_usd.sum()),3) if len(trades) else 0.,
        total_liquidation_fee_usd=round(float(trades.liquidation_fee_usd.sum()),3) if len(trades) else 0.,
        total_gst_usd=round(float(trades.gst_usd.sum()),3) if len(trades) else 0.,
        open_position_end=position is not None,
        last_data_utc=str(ts[-1]),
    )
    return trades, mon, stats


def self_test():
    # A new trailing stop must never be triggered on its source candle.
    p = dict(side=1, stop=90., liq=85., entry=100.,
             active=False, best=100., activation=15., distance=5.)
    assert exit_decision(1, 100., 120., 91., 90., 85., False)[0] is None
    close_and_update_trailing(p, 120., 91.)
    assert p["stop"] == 115.
    assert exit_decision(1, 101., 125., 99., 115., 85., False) == (101., "stop_gap")
    # On same 15m bar, old stop is hit even if favorable high touches activation.
    assert exit_decision(1, 100., 130., 89., 90., 85., False) == (90., "protective_stop")
    # Stop takes priority over activation/high: no fabricated intrabar path.
    assert exit_decision(-1, 100., 111., 80., 110., 115., False) == (110., "protective_stop")
    # A flip signal cannot act at the previous candle's close.
    assert exit_decision(1, 100., 120., 91., 90., 85., True) == (100., "supertrend_flip")
    # Existing protection must win over a flip when open gaps below stop.
    assert exit_decision(1, 80., 100., 79., 90., 85., True) == (80., "liquidation")


def main():
    self_test()
    result = {"model": RULES, "datasets": {}, "scenarios": {}}
    for asset in ("BTC", "ETH"):
        _, f, m = load(asset)
        result["datasets"][asset] = {
            "source": m["source"], "history_minutes_resampled": sum(p["observed_candles"] for p in m["partitions"]),
            "execution_bars_15m": len(f), "last_15m_utc": str(f.index[-1]),
            "manifest_generated": m["generated_at_utc"],
        }
        for offer in (False, True):
            for liq_fill in ("threshold", "bankruptcy"):
                for slip in (0., .5 if asset == "BTC" else .05):
                    label = f'{asset.lower()}_{"offer" if offer else "nooffer"}_{liq_fill}_{"noslip" if not slip else "onetick"}'
                    trades, monthly, stats = simulate(asset, f, offer, liq_fill, slip)
                    trades.to_csv(OUT/f"{label}_trades.csv.gz", index=False, compression="gzip")
                    monthly.to_csv(OUT/f"{label}_monthly.csv", index=False)
                    result["scenarios"][label] = stats
                    print("SCENARIO", label, json.dumps(stats), flush=True)
    (OUT/"summary.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print("CAUSAL_15M_BACKTEST_COMPLETE", OUT, flush=True)


if __name__ == "__main__":
    main()
