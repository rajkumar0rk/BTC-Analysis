#!/usr/bin/env python3
"""Research-only BTCUSD 1H Supertrend + EMA20; fixed BTC point TP or completed Supertrend reversal."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

BASE=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/ema20_st_fixed_tp_sweep_1h")
QTY=0.001
START_USD=100.
FEE=.0005*1.18
SLIP=5.

def load():
    files=sorted(BASE.glob("20??-??.csv.gz"))
    if not files: raise RuntimeError("No BTCUSD one-minute source archive")
    a=[]
    for f in files:
        x=pd.read_csv(f,compression="gzip",usecols=["time","open","high","low","close","volume"])
        x["time"]=pd.to_datetime(x.time.astype("int64"),unit="s",utc=True)
        a.append(x.set_index("time"))
    m=pd.concat(a).sort_index()
    if m.index.has_duplicates or not m.index.to_series().diff().dropna().eq(pd.Timedelta(minutes=1)).all():
        raise RuntimeError("Source 1m archive has duplicate or missing timestamps")
    if m[["open","high","low","close"]].isna().any().any(): raise RuntimeError("Missing OHLC")
    if not ((m.low<=m[["open","close"]].min(axis=1)) & (m.high>=m[["open","close"]].max(axis=1))).all():
        raise RuntimeError("Invalid OHLC")
    count=m.close.resample("1h").count()
    if not count.eq(60).all(): raise RuntimeError("Incomplete hourly bar")
    h=m.resample("1h").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    return m,h,len(files)

def features(h):
    prev=h.close.shift()
    tr=pd.concat([h.high-h.low,(h.high-prev).abs(),(h.low-prev).abs()],axis=1).max(axis=1).to_numpy()
    n=len(h); atr=np.full(n,np.nan)
    if n<30: raise RuntimeError("Insufficient signal warmup")
    atr[9]=tr[:10].mean()
    for i in range(10,n): atr[i]=(9*atr[i-1]+tr[i])/10
    mid=(h.high.to_numpy()+h.low.to_numpy())/2.
    up=mid+3*atr; down=mid-3*atr
    u=np.full(n,np.nan); d=np.full(n,np.nan); side=np.zeros(n,dtype=np.int8)
    for i in range(9,n):
        if i==9:
            u[i]=up[i];d[i]=down[i];side[i]=-1
        else:
            u[i]=up[i] if up[i]<u[i-1] or h.close.iloc[i-1]>u[i-1] else u[i-1]
            d[i]=down[i] if down[i]>d[i-1] or h.close.iloc[i-1]<d[i-1] else d[i-1]
            side[i]=(1 if side[i-1]==-1 and h.close.iloc[i]>u[i-1] else
                     (-1 if side[i-1]==1 and h.close.iloc[i]<d[i-1] else side[i-1]))
    h=h.copy()
    h["ema"]=h.close.ewm(span=20,adjust=False).mean()
    h["atr"]=atr
    h["side"]=side
    h["supertrend_line"]=np.where(side==1,d,u)
    return h


def setups(h, mode):
    """Previous study's completed-hour touch/reclaim signals, minus ALL stop/R filters."""
    events = {}
    prev_side = 0
    seen_adverse = False
    cycle = 0
    flip_i = 0
    for i in range(20, len(h)):
        side = int(h.side.iloc[i])
        if side != prev_side:
            cycle += 1
            flip_i = i
            seen_adverse = False
            prev_side = side
        if side == 0 or i == flip_i:
            continue
        r = h.iloc[i]
        favorable = side * (r.close - r.ema) > 0
        adverse = side * (r.close - r.ema) < 0
        touch = (favorable and not seen_adverse and
                 (r.low <= r.ema if side == 1 else r.high >= r.ema))
        reclaim = favorable and seen_adverse
        kind = "reclaim" if reclaim else ("touch" if touch else None)
        if adverse:
            seen_adverse = True
        elif reclaim:
            seen_adverse = False
        if kind is None or (mode != "combined" and kind != mode):
            continue
        # Entry is only eligible in the NEXT hour after the completed 1H signal.
        events[i + 1] = dict(side=side, cycle=cycle, kind=kind,
                             trigger=float(r.high + .5 if side == 1 else r.low - .5),
                             signal=str(h.index[i]))
    return events


def replay(m, h, mode, tp_points):
    """Independent counterfactual: exact 200/500/1000 point TP OR confirmed 1H ST flip.
    
    No protective initial stop, no R exit, no trailing. One filled trade per ST cycle.
    Historical OHLC high/low does not reveal tick order; avoid same-entry-minute TP.
    """
    events = setups(h, mode)
    op = m.open.to_numpy(float)
    hi = m.high.to_numpy(float)
    lo = m.low.to_numpy(float)
    close = m.close.to_numpy(float)
    times = m.index
    hour_for_minute = np.searchsorted(h.index.asi8, times.asi8, side="right") - 1
    hside = h.side.to_numpy()
    trades = []
    used_cycles = set()
    pos = None
    pending = None
    last_hour = -1
    realized_cash = START_USD
    peak_closed_cash = START_USD
    worst_open_mark = START_USD
    largest_excursion_below_closed_peak = 0.

    def mark_equity(worst_price):
        exit_fill = worst_price - pos["side"] * SLIP
        gross = QTY * pos["side"] * (exit_fill - pos["entry"])
        fee = QTY * FEE * (pos["entry"] + exit_fill)
        return realized_cash + gross - fee

    def finish(j, mid, reason):
        nonlocal pos, realized_cash, peak_closed_cash
        side = pos["side"]
        exit_fill = float(mid) - side * SLIP
        gross = QTY * side * (exit_fill - pos["entry"])
        fees = QTY * FEE * (pos["entry"] + exit_fill)
        net = gross - fees
        trades.append(dict(
            mode=mode, target_points=tp_points, setup=pos["kind"],
            side="LONG" if side == 1 else "SHORT",
            signal_utc=pos["signal"],
            entry_utc=str(times[pos["entry_j"]]),
            exit_utc=str(times[j]),
            entry_price=round(pos["entry"], 2),
            target_price=round(pos["tp"], 2),
            exit_price=round(exit_fill, 2),
            hold_minutes=int(j - pos["entry_j"]),
            gross_usd=round(gross, 6),
            fees_usd=round(fees, 6),
            net_usd=round(net, 6),
            max_favorable_points=round(pos["max_favorable_points"], 2),
            max_adverse_points=round(pos["max_adverse_points"], 2),
            exit_reason=reason))
        realized_cash += net
        peak_closed_cash = max(peak_closed_cash, realized_cash)
        pos = None

    for j, hour in enumerate(hour_for_minute):
        if hour != last_hour:
            last_hour = hour
            pending = None
            # The prior completed hour's Supertrend is observable now, before TP
            # checks on the new minute. This is the same exit timing as baseline.
            if hour > 0 and pos is not None and int(hside[hour - 1]) != pos["side"]:
                finish(j, op[j], "supertrend_flip")
            if pos is None:
                ev = events.get(hour)
                if ev is not None and ev["cycle"] not in used_cycles:
                    pending = ev

        if pos is None and pending is not None:
            ev = pending
            side = ev["side"]
            trigger_hit = hi[j] >= ev["trigger"] if side == 1 else lo[j] <= ev["trigger"]
            if trigger_hit:
                entry_mid = (max(float(op[j]), ev["trigger"]) if side == 1
                             else min(float(op[j]), ev["trigger"]))
                entry_fill = entry_mid + side * SLIP
                pos = dict(side=side, kind=ev["kind"], cycle=ev["cycle"],
                           entry_j=j, entry=entry_fill,
                           tp=entry_fill + side * tp_points,
                           signal=ev["signal"], max_adverse_points=0.,
                           max_favorable_points=0.)
                used_cycles.add(ev["cycle"])
                pending = None

        if pos is None or j == pos["entry_j"]:
            continue

        # Observe favorable/adverse 1m OHLC range prior to determining a TP
        # inside the same bar; adverse mark is conservative without tick path.
        side = pos["side"]
        adverse_price = lo[j] if side == 1 else hi[j]
        favorable_price = hi[j] if side == 1 else lo[j]
        adverse_points = max(0., side * (pos["entry"] - adverse_price))
        favorable_points = max(0., side * (favorable_price - pos["entry"]))
        pos["max_adverse_points"] = max(pos["max_adverse_points"], adverse_points)
        pos["max_favorable_points"] = max(pos["max_favorable_points"], favorable_points)
        adverse_equity = mark_equity(adverse_price)
        worst_open_mark = min(worst_open_mark, adverse_equity)
        largest_excursion_below_closed_peak = max(
            largest_excursion_below_closed_peak, peak_closed_cash - adverse_equity)

        target_reached = hi[j] >= pos["tp"] if side == 1 else lo[j] <= pos["tp"]
        if target_reached:
            # Do not assume advantageous fill at a positive gap beyond target.
            finish(j, pos["tp"], "fixed_take_profit")

    open_trade = None
    if pos is not None:
        side = pos["side"]
        hypo_exit = float(close[-1]) - side * SLIP
        hypo_net = (QTY * side * (hypo_exit - pos["entry"])
                    - QTY * FEE * (pos["entry"] + hypo_exit))
        open_trade = dict(side="LONG" if side == 1 else "SHORT", setup=pos["kind"],
                          cycle=pos["cycle"], entry_utc=str(times[pos["entry_j"]]),
                          entry_price=pos["entry"], target_price=pos["tp"],
                          mark_price=float(close[-1]),
                          hypothetical_net_usd=round(hypo_net, 4),
                          note="Unrealized only; NOT exited by strategy")
    extra = dict(
        fixed_take_profit_points=tp_points,
        target_exits=int((pd.Series([r["exit_reason"] for r in trades]) == "fixed_take_profit").sum()),
        supertrend_reversal_exits=int((pd.Series([r["exit_reason"] for r in trades]) == "supertrend_flip").sum()),
        open_trade=open_trade,
        worst_open_mark_equity_usd=round(worst_open_mark, 4),
        max_excursion_below_previous_realized_peak_usd=round(
            largest_excursion_below_closed_peak, 4),
        note="1m OHLC replay with conservative entry-minute TP omission; no funding/liquidation/bid-ask model")
    return pd.DataFrame(trades), extra


def summarize(trades, extra):
    if trades.empty:
        return dict(closed_trades=0, realized_net_usd=0, ending_closed_equity_usd=START_USD, **extra)
    p = trades.net_usd.to_numpy(float)
    closed_eq = np.r_[START_USD, START_USD + np.cumsum(p)]
    peaks = np.maximum.accumulate(closed_eq)
    draw = peaks - closed_eq
    wins = p[p > 0].sum()
    losses = -p[p < 0].sum()
    return dict(
        closed_trades=len(trades),
        wins=int((p > 0).sum()),
        losses=int((p < 0).sum()),
        win_rate_pct=round(float((p > 0).mean() * 100), 3),
        gross_usd=round(float(trades.gross_usd.sum()), 4),
        fees_usd=round(float(trades.fees_usd.sum()), 4),
        realized_net_usd=round(float(p.sum()), 4),
        ending_closed_equity_usd=round(float(closed_eq[-1]), 4),
        profit_factor=round(float(wins / losses), 4) if losses else None,
        realized_max_drawdown_usd=round(float(draw.max()), 4),
        realized_max_drawdown_pct=round(float(np.max(100 * draw / peaks)), 3),
        winning_trades_gross_usd=round(float(wins), 4),
        losing_trades_gross_usd=round(float(losses), 4),
        avg_win_usd=round(float(p[p > 0].mean()), 4) if (p > 0).any() else None,
        avg_loss_usd=round(float(p[p < 0].mean()), 4) if (p < 0).any() else None,
        max_trade_adverse_points=round(float(trades.max_adverse_points.max()), 2),
        max_trade_favorable_points=round(float(trades.max_favorable_points.max()), 2),
        **extra)


def monthly(trades, first, last):
    all_months = pd.period_range(
        first.tz_convert("Asia/Kolkata").tz_localize(None).to_period("M"),
        last.tz_convert("Asia/Kolkata").tz_localize(None).to_period("M"))
    if not trades.empty:
        t = trades.copy()
        # Realized profit belongs to the EXIT month, not the entry month.
        t["month"] = (pd.to_datetime(t.exit_utc, utc=True)
                      .dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m"))
    else:
        t = pd.DataFrame()
    rows = []
    cash = START_USD
    for per in all_months:
        month = str(per)
        group = t[t.month == month] if not t.empty else t
        n = len(group)
        net = float(group.net_usd.sum()) if n else 0.
        rows.append(dict(month_ist=month, complete_month=month < "2026-11",
                         closed_trades=n,
                         winning_trades=int((group.net_usd > 0).sum()) if n else 0,
                         losing_trades=int((group.net_usd < 0).sum()) if n else 0,
                         gross_usd=round(float(group.gross_usd.sum()), 4) if n else 0.,
                         fees_usd=round(float(group.fees_usd.sum()), 4) if n else 0.,
                         net_usd=round(net, 4),
                         starting_closed_equity_usd=round(cash, 4),
                         net_return_pct=round(100 * net / cash, 3) if cash > 0 else None,
                         ending_closed_equity_usd=round(cash + net, 4)))
        cash += net
    return pd.DataFrame(rows)


def main():
    m, h, nfiles = load()
    h = features(h)
    OUT.mkdir(parents=True, exist_ok=True)
    quality = dict(
        source="Delta Exchange India BTCUSD perpetual 1m OHLCV",
        source_files=nfiles, minute_bars=len(m), hourly_bars=len(h),
        first_utc=str(m.index[0]), last_utc=str(m.index[-1]),
        validated_consecutive_minutes=True,
        qty_btc=QTY, initial_account_usd=START_USD,
        side_taker_fee_including_gst=FEE,
        slippage_btc_price_points_per_side=SLIP,
        entry_methods=["touch", "reclaim", "combined"],
        target_scenarios_points=[200, 500, 1000],
        fallback_exit="next minute open after confirmed completed 1H Supertrend reversal",
        max_one_fill_per_supertrend_cycle=True,
        protective_stop_enabled=False, trailing_enabled=False,
        caveats=[
            "WITHOUT a protective stop, a real margin position can liquidate before profit target or trend flip",
            "TP on entry minute is NOT assumed since OHLC does not reveal whether entry preceded high/low",
            "Profit target executed at exact level minus 5 price points exit slippage; no positive-gap improvement",
            "No funding, bid-ask spread/depth, exchange latency, liquidation or capital feasibility model",
            "No untouched out-of-sample holdout; 200/500/1000 came from past losing-trade MFE study",
            "November 2026 partial; months in IST booked by EXIT time",
            "No artificial close of still-open position at end of data"
        ])
    (OUT / "quality.json").write_text(json.dumps(quality, indent=2) + "\n")
    results = {}
    for mode in ["touch", "reclaim", "combined"]:
        for target in (200, 500, 1000):
            key = f"{mode}_tp{target}"
            trades, extra = replay(m, h, mode, target)
            trades.to_csv(OUT / f"{key}_trades.csv", index=False)
            month = monthly(trades, m.index[0], m.index[-1])
            month.to_csv(OUT / f"{key}_monthly_ist.csv", index=False)
            summary = summarize(trades, extra)
            summary["profitable_full_months"] = int(((month.net_usd > 0) & month.complete_month).sum())
            summary["total_full_months"] = int(month.complete_month.sum())
            results[key] = summary
            print(f"{key}: {json.dumps(summary)}", flush=True)
    (OUT / "summary.json").write_text(json.dumps(results, indent=2) + "\n")
    pd.DataFrame([
        dict(configuration=k,
             target_points=s.get("fixed_take_profit_points"),
             closed_trades=s.get("closed_trades"),
             winners=s.get("wins"), losers=s.get("losses"),
             win_pct=s.get("win_rate_pct"), net_usd=s.get("realized_net_usd"),
             ending_closed_equity_usd=s.get("ending_closed_equity_usd"),
             profit_factor=s.get("profit_factor"),
             max_realized_drawdown_pct=s.get("realized_max_drawdown_pct"),
             profitable_full_months=s.get("profitable_full_months"),
             target_exits=s.get("target_exits"),
             supertrend_flip_exits=s.get("supertrend_reversal_exits"),
             open_unrealized_net_usd=(s["open_trade"]["hypothetical_net_usd"]
                                     if s.get("open_trade") is not None else None))
        for k, s in results.items()
    ]).to_csv(OUT / "comparison.csv", index=False)

if __name__ == "__main__":
    main()
