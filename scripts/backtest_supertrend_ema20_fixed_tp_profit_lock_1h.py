#!/usr/bin/env python3
"""Research-only BTCUSD 1H Supertrend + EMA20; fixed TP with profit lock or completed Supertrend reversal."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

BASE=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/ema20_st_fixed_tp_protection_1h")
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


PROFILES = {
    # activation fraction of target, then locked fraction of target.
    "early_75_lock50": (0.75, 0.50),
    "late_90_lock75": (0.90, 0.75),
}
TARGETS = (200, 500, 1000)


def check_exit(side, opened, highest, lowest, fixed_target, active_lock):
    """Return (mid_fill, exit_reason) or (None, None).

    Stop-first path convention when both a protective lock and fixed target
    are inside the minute range. Worse opening-price gaps for protective stops.
    Target never receives favorable price improvement from positive gaps.
    """
    if active_lock is not None:
        hit_lock = lowest <= active_lock if side == 1 else highest >= active_lock
        if hit_lock:
            mid = min(opened, active_lock) if side == 1 else max(opened, active_lock)
            return float(mid), "profit_lock"
    hit_tp = highest >= fixed_target if side == 1 else lowest <= fixed_target
    if hit_tp:
        return float(fixed_target), "fixed_take_profit"
    return None, None


def replay(m, h, mode, tp_points, profile_name):
    """1M execution of fixed TP, post-activation profit lock and 1H ST flip."""
    activation_frac, lock_frac = PROFILES[profile_name]
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
            mode=mode, profile=profile_name, target_points=tp_points,
            setup=pos["kind"],
            side="LONG" if side == 1 else "SHORT",
            signal_utc=pos["signal"],
            entry_utc=str(times[pos["entry_j"]]),
            exit_utc=str(times[j]),
            entry_price=round(pos["entry"], 2),
            target_price=round(pos["tp"], 2),
            locked_stop_price=round(pos["lock"], 2) if pos["lock"] is not None else None,
            exit_price=round(exit_fill, 2),
            hold_minutes=int(j-pos["entry_j"]),
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
            # Only the LAST completed hourly ST signal is known at new hour open.
            if hour > 0 and pos is not None and int(hside[hour-1]) != pos["side"]:
                finish(j, op[j], "supertrend_flip")
            if pos is None:
                ev = events.get(hour)
                if ev is not None and ev["cycle"] not in used_cycles:
                    pending = ev

        if pos is None and pending is not None:
            ev = pending
            side = ev["side"]
            hit_entry = hi[j] >= ev["trigger"] if side == 1 else lo[j] <= ev["trigger"]
            if hit_entry:
                entry_mid = max(float(op[j]), ev["trigger"]) if side == 1 else min(float(op[j]), ev["trigger"])
                entry_fill = entry_mid + side * SLIP
                pos = dict(
                    side=side, kind=ev["kind"], cycle=ev["cycle"],
                    entry_j=j, entry=entry_fill,
                    tp=entry_fill+side*tp_points,
                    lock=None, signal=ev["signal"],
                    max_adverse_points=0., max_favorable_points=0.)
                used_cycles.add(ev["cycle"])
                pending = None

        if pos is None or j == pos["entry_j"]:
            continue

        side = pos["side"]

        # The active stop was set only at END OF EARLIER complete minute.
        # If both TP and lock hit during same 1M bar, stop wins conservatively.
        exit_mid, reason = check_exit(side, op[j], hi[j], lo[j], pos["tp"], pos["lock"])

        adverse_price = lo[j] if side == 1 else hi[j]
        favorable_price = hi[j] if side == 1 else lo[j]
        adverse_points = max(0., side * (pos["entry"]-adverse_price))
        favorable_points = max(0., side * (favorable_price-pos["entry"]))
        pos["max_adverse_points"] = max(pos["max_adverse_points"], adverse_points)
        pos["max_favorable_points"] = max(pos["max_favorable_points"], favorable_points)

        adverse_equity = mark_equity(adverse_price)
        worst_open_mark = min(worst_open_mark, adverse_equity)
        largest_excursion_below_closed_peak = max(
            largest_excursion_below_closed_peak, peak_closed_cash-adverse_equity)

        if reason is not None:
            finish(j, exit_mid, reason)
            continue

        # Only NOW, after observing the complete minute with no exit,
        # activate protection for the next minute. No same-minute hindsight.
        if pos["lock"] is None and favorable_points >= activation_frac * tp_points:
            pos["lock"] = pos["entry"] + side * (lock_frac * tp_points)

    open_trade = None
    if pos is not None:
        side = pos["side"]
        hypo_exit = float(close[-1]) - side * SLIP
        hypo_net = (QTY * side * (hypo_exit - pos["entry"])
                    - QTY * FEE * (pos["entry"] + hypo_exit))
        open_trade = dict(
            side="LONG" if side == 1 else "SHORT", setup=pos["kind"],
            entry_utc=str(times[pos["entry_j"]]), entry_price=pos["entry"],
            target_price=pos["tp"], lock=pos["lock"],
            mark_price=float(close[-1]),
            hypothetical_net_usd=round(hypo_net, 4),
            note="Not closed by either TP, profit protection or ST; unrealized only")

    exits=pd.Series([r["exit_reason"] for r in trades],dtype="object")
    extra = dict(
        fixed_take_profit_points=tp_points, protection_profile=profile_name,
        protection_activation_points=activation_frac*tp_points,
        locked_profit_points=lock_frac*tp_points,
        target_exits=int((exits=="fixed_take_profit").sum()),
        protection_exits=int((exits=="profit_lock").sum()),
        supertrend_reversal_exits=int((exits=="supertrend_flip").sum()),
        open_trade=open_trade,
        worst_open_mark_equity_usd=round(worst_open_mark, 4),
        max_excursion_below_previous_realized_peak_usd=round(
            largest_excursion_below_closed_peak, 4),
        note="No initial SL, no funding/liquidation model; fee-inclusive profit can be negative at a small protective lock")
    return pd.DataFrame(trades), extra


def smoke_test():
    # Long and short, stop-first collision, adverse gap, and TP-only cases.
    assert check_exit(1, 98., 125., 98., 120., 105.) == (98., "profit_lock")
    assert check_exit(-1, 102., 102., 76., 80., 95.) == (102., "profit_lock")
    assert check_exit(1, 108., 120., 102., 120., 105.) == (105., "profit_lock")
    assert check_exit(-1, 92., 96., 80., 80., 95.) == (95., "profit_lock")
    assert check_exit(1, 110., 130., 109., 120., None) == (120., "fixed_take_profit")
    assert check_exit(-1, 90., 91., 76., 80., None) == (80., "fixed_take_profit")
    assert check_exit(1, 110., 115., 106., 120., 105.) == (None, None)


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
    smoke_test()
    m,h,nfiles=load()
    h=features(h)
    OUT.mkdir(parents=True,exist_ok=True)
    quality=dict(
        source="Delta Exchange India BTCUSD perpetual 1m OHLCV",
        source_files=nfiles, minute_bars=len(m), hourly_bars=len(h),
        first_utc=str(m.index[0]), last_utc=str(m.index[-1]),
        validated_consecutive_minutes=True,
        qty_btc=QTY, initial_account_usd=START_USD,
        side_taker_fee_including_gst=FEE,
        slippage_btc_price_points_per_side=SLIP,
        entry_modes=["touch","reclaim","combined"],
        targets_points=TARGETS,
        protection_profiles={k:dict(activation_fraction=v[0],lock_fraction=v[1]) for k,v in PROFILES.items()},
        exit_rules=["fixed TP","active profit lock","completed 1H Supertrend reversal"],
        max_one_fill_per_supertrend_cycle=True,
        no_initial_stop=True, no_R_based_exits=True,
        caveats=[
            "Without initial SL there may be a large unrealized loss or liquidation before protection activates",
            "Exchange fee+GST can exceed small locked points and lead to net losing lock exits",
            "Profit lock live only after completed earlier 1m bar; bar with both TP/lock uses stop-first ambiguity",
            "No execution at entry bar's hypothetical favorable extreme",
            "No funding, mark price, bid-ask/depth, liquidation, latency or actual margin feasibility model",
            "No untouched out-of-sample months; previously studied 200/500/1000 points are not an unbiased discovery",
            "Month booked in IST on exit, November 2026 partial",
            "Open position at end of archive is unrealized only"
        ])
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    results={}
    for mode in ["touch","reclaim","combined"]:
        for target in TARGETS:
            for profile in PROFILES:
                key=f"{mode}_tp{target}_{profile}"
                trades,extra=replay(m,h,mode,target,profile)
                trades.to_csv(OUT/f"{key}_trades.csv",index=False)
                month=monthly(trades,m.index[0],m.index[-1])
                month.to_csv(OUT/f"{key}_monthly_ist.csv",index=False)
                summary=summarize(trades,extra)
                summary["profitable_full_months"]=int(((month.net_usd>0)&month.complete_month).sum())
                summary["total_full_months"]=int(month.complete_month.sum())
                results[key]=summary
                print(key,json.dumps(summary),flush=True)
    (OUT/"summary.json").write_text(json.dumps(results,indent=2)+"\n")
    pd.DataFrame([
        dict(configuration=k,mode=k.split("_tp")[0],
             target_points=s["fixed_take_profit_points"],
             profile=s["protection_profile"],
             activation_points=s["protection_activation_points"],
             lock_points=s["locked_profit_points"],
             trades=s["closed_trades"],wins=s["wins"],losses=s["losses"],
             win_rate_pct=s["win_rate_pct"],gross_usd=s["gross_usd"],
             fees_usd=s["fees_usd"],net_usd=s["realized_net_usd"],
             profit_factor=s["profit_factor"],
             max_drawdown_pct=s["realized_max_drawdown_pct"],
             profitable_full_months=s["profitable_full_months"],
             target_exits=s["target_exits"],
             protection_exits=s["protection_exits"],
             supertrend_reversal_exits=s["supertrend_reversal_exits"],
             open_unrealized_net_usd=s["open_trade"]["hypothetical_net_usd"] if s["open_trade"] else None)
        for k,s in results.items()
    ]).to_csv(OUT/"comparison.csv",index=False)

if __name__ == "__main__":
    main()
