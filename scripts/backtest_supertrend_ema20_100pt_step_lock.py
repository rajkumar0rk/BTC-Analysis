#!/usr/bin/env python3
"""Research-only BTCUSD 1H Supertrend + EMA20; 100-point stepped profit lock, no initial SL."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

BASE=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/st_ema20_step_lock_100_1h")
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


POINT_UNIT=100.

def entry_candidates(m,h,mode):
    """First fill of each ST cycle, using only the following hour after a signal.

    Entry selection independent of any exit, because ONLY one filled entry may
    occur in each cycle. Precompute once to avoid 108 full million-minute scans.
    """
    events = setups(h,mode)
    op=m.open.to_numpy(float);hi=m.high.to_numpy(float);lo=m.low.to_numpy(float)
    n=len(op);cycles=set();entries=[]
    assert n==len(h)*60, "complete aligned 1h/1m archive required"
    for hour, ev in sorted(events.items()):
        if hour >= len(h) or ev["cycle"] in cycles:continue
        start=hour*60;end=min(start+60,n);side=ev["side"]
        for j in range(start,end):
            crossed=hi[j]>=ev["trigger"] if side==1 else lo[j]<=ev["trigger"]
            if crossed:
                fill_mid=max(op[j],ev["trigger"]) if side==1 else min(op[j],ev["trigger"])
                entries.append(dict(
                    entry_j=j,entry=fill_mid+side*SLIP,
                    side=side,kind=ev["kind"],cycle=ev["cycle"],signal=ev["signal"]))
                cycles.add(ev["cycle"])
                break
    # Validate invariant that selected signals exist ONLY once per Supertrend cycle.
    assert len({e["cycle"] for e in entries})==len(entries)
    return entries


POINT_UNIT=100.
ACTIVATIONS=(150,200,300)
TP_MODES=(None,1000)


def next_lock_points(favorable_points,activation):
    """Only after a whole 1m candle; first lock +100, then ratchet each +100."""
    if favorable_points+1.e-8<activation:
        return None
    steps=1+int((favorable_points-activation+1.e-8)//100.)
    return 100.*steps


def stop_first_exit(side,opened,hi,lo,stop,tp):
    """Conservative stop priority on double-touch, adverse opening gaps at stop."""
    if stop is not None:
        touched=lo<=stop if side==1 else hi>=stop
        if touched:
            mid=min(opened,stop) if side==1 else max(opened,stop)
            return float(mid),"profit_lock"
    if tp is not None:
        hit=hi>=tp if side==1 else lo<=tp
        if hit:
            return float(tp),"fixed_take_profit"
    return None,None


def smoke_test():
    assert next_lock_points(149.99,150) is None
    assert next_lock_points(150.,150)==100.
    assert next_lock_points(249.99,150)==100.
    assert next_lock_points(250.,150)==200.
    assert next_lock_points(499.9,200)==300.
    assert next_lock_points(500.,200)==400.
    assert next_lock_points(300.,300)==100.
    assert next_lock_points(400.,300)==200.
    assert stop_first_exit(1,100.,130.,90.,105.,120.)==(100.,"profit_lock")
    assert stop_first_exit(-1,100.,110.,80.,95.,90.)==(100.,"profit_lock")
    assert stop_first_exit(1,110.,130.,106.,105.,120.)==(120.,"fixed_take_profit")
    assert stop_first_exit(-1,90.,94.,80.,95.,85.)==(85.,"fixed_take_profit")
    assert stop_first_exit(1,110.,112.,106.,105.,120.)==(None,None)


def replay(m,h,entries,mode,activation,target_cap):
    op=m.open.to_numpy(float);hi=m.high.to_numpy(float);lo=m.low.to_numpy(float);close=m.close.to_numpy(float)
    times=m.index;hside=h.side.to_numpy();total=len(op);n_hours=len(h)
    trades=[];cash=START_USD;peak=START_USD;worst_mark=START_USD;max_excursion=0.
    open_trade=None
    for ev in entries:
        side=ev["side"];j0=ev["entry_j"];entry=ev["entry"]
        tp=entry+side*target_cap if target_cap is not None else None
        stop=None;locked_points=0.;highest_profit=0.;max_adverse=0.;upgrades=0
        entry_hour=j0//60
        flip_j=total
        for hr in range(entry_hour+1,n_hours):
            if int(hside[hr-1])!=side:
                flip_j=hr*60
                break
        exit_j=None;exit_mid=None;exit_reason=None
        # At the start of the entry minute there is no profit stop. No same-bar
        # favorable lookahead. After entry, observe each minute after its
        # prior active stop is checked.
        for j in range(j0,min(flip_j,total)):
            if j>j0:
                mid,reason=stop_first_exit(side,op[j],hi[j],lo[j],stop,tp)
                if reason is not None:
                    exit_j=j;exit_mid=mid;exit_reason=reason;break
                favorable_px=hi[j] if side==1 else lo[j]
                adverse_px=lo[j] if side==1 else hi[j]
                favorable=max(0.,side*(favorable_px-entry))
                adverse=max(0.,side*(entry-adverse_px))
                highest_profit=max(highest_profit,favorable)
                max_adverse=max(max_adverse,adverse)
                hypo_exit=adverse_px-side*SLIP
                mark=cash+QTY*side*(hypo_exit-entry)-QTY*FEE*(entry+hypo_exit)
                worst_mark=min(worst_mark,mark)
                max_excursion=max(max_excursion,peak-mark)
                requested_lock=next_lock_points(highest_profit,activation)
                if requested_lock is not None and requested_lock>locked_points:
                    # The new stop becomes active for the FOLLOWING 1m candle.
                    # If current close has already reversed beyond it, next
                    # minute's opening price (not imagined lock fill) is used.
                    locked_points=requested_lock
                    stop=entry+side*locked_points
                    upgrades+=1
        if exit_j is None and flip_j<total:
            exit_j=flip_j;exit_mid=float(op[flip_j]);exit_reason="supertrend_flip"
        if exit_j is None:
            hypo_exit=float(close[-1])-side*SLIP
            hypo_net=QTY*side*(hypo_exit-entry)-QTY*FEE*(entry+hypo_exit)
            open_trade=dict(entry_utc=str(times[j0]),
                side="LONG" if side==1 else "SHORT",entry_price=round(entry,2),
                exit_stop=round(stop,2) if stop is not None else None,
                mark_price=float(close[-1]),hypothetical_net_usd=round(hypo_net,5),
                note="Still open: no forced exit")
            continue
        exit_fill=exit_mid-side*SLIP
        gross=QTY*side*(exit_fill-entry);fees=QTY*FEE*(entry+exit_fill);net=gross-fees
        trades.append(dict(mode=mode,activation_points=activation,
            fixed_tp_points=target_cap if target_cap is not None else "",
            setup=ev["kind"],side="LONG" if side==1 else "SHORT",
            signal_utc=ev["signal"],
            entry_utc=str(times[j0]),exit_utc=str(times[exit_j]),
            entry_price=round(entry,2),exit_price=round(exit_fill,2),
            locked_points=round(locked_points,2),
            stop_upgrades=upgrades,hold_minutes=exit_j-j0,
            gross_usd=round(gross,6),fees_usd=round(fees,6),
            net_usd=round(net,6),exit_reason=exit_reason,
            max_favorable_points=round(highest_profit,2),
            max_adverse_points=round(max_adverse,2)))
        cash+=net;peak=max(peak,cash)
    t=pd.DataFrame(trades)
    reasons=t.exit_reason.value_counts().to_dict() if len(t) else {}
    return t,dict(activation_points=activation,initial_locked_profit_points=100.,
        increment_trigger_points=100.,lock_increment_points=100.,
        fixed_tp_cap_points=target_cap,
        exit_counts={k:int(v) for k,v in reasons.items()},
        open_trade=open_trade,worst_open_mark_equity_usd=round(worst_mark,4),
        max_excursion_below_previous_realized_peak_usd=round(max_excursion,4),
        note="1m next-bar activation with stop-first and gap-aware lock exits, no initial SL, funding or liquidation model")



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
    m,h,source_files=load();h=features(h)
    OUT.mkdir(parents=True,exist_ok=True)
    entries={mode:entry_candidates(m,h,mode) for mode in ("touch","reclaim","combined")}
    quality=dict(source="Delta Exchange India BTCUSD perpetual 1m traded price OHLCV",
        source_files=source_files,minute_bars=len(m),hourly_bars=len(h),
        first_utc=str(m.index[0]),last_utc=str(m.index[-1]),
        validated_consecutive_minutes=True,
        entry_modes=list(entries),entry_counts={k:len(v) for k,v in entries.items()},
        activation_points=list(ACTIVATIONS),
        initial_lock_points=100,step_trigger_points=100,step_lock_points=100,
        target_cap_points=["uncapped",1000],
        one_filled_trade_per_supertrend_cycle=True,
        initial_stop_loss=False,
        exit_rules=["step-profit-lock 1m after completed trigger", "optional fixed TP 1000", "confirmed 1H ST reversal"],
        quantity_btc=QTY,starting_cash_usd=START_USD,
        fee_per_side_plus_gst=FEE,slippage_price_points_per_side=SLIP,
        caveats=["No initial stop: losses can exceed available margin or liquidate",
            "No funding, liquidation, mark price, depth or actual spread model",
            "Profit-lock updates only on next 1m candle; gap fills may be worse",
            "No same-entry-minute TP or profit protection",
            "Prior months researched, no untouched out-of-sample; November 2026 partial",
            "Monthly realized net PnL booked by IST exit month"])
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    summaries={};rows=[]
    for mode,evs in entries.items():
        for activation in ACTIVATIONS:
            for cap in TP_MODES:
                suffix="uncapped" if cap is None else "tp1000"
                key=f"{mode}_act{activation}_{suffix}"
                trades,more=replay(m,h,evs,mode,activation,cap)
                trades.to_csv(OUT/f"{key}_trades.csv",index=False)
                mon=monthly(trades,m.index[0],m.index[-1])
                mon.to_csv(OUT/f"{key}_monthly_ist.csv",index=False)
                s=summarize(trades,more)
                s["profitable_full_months"]=int(((mon.net_usd>0)&mon.complete_month).sum())
                s["total_full_months"]=int(mon.complete_month.sum())
                summaries[key]=s
                rows.append(dict(configuration=key,entry_mode=mode,
                    activation_points=activation,fixed_tp_cap=cap if cap is not None else "none",
                    closed_trades=s.get("closed_trades",0),
                    winners=s.get("wins",0),losers=s.get("losses",0),
                    win_rate_pct=s.get("win_rate_pct"),
                    gross_usd=s.get("gross_usd"),fees_usd=s.get("fees_usd"),
                    net_usd=s.get("realized_net_usd"),pf=s.get("profit_factor"),
                    realized_max_drawdown_pct=s.get("realized_max_drawdown_pct"),
                    profitable_full_months=s["profitable_full_months"],
                    lock_exits=more["exit_counts"].get("profit_lock",0),
                    tp_exits=more["exit_counts"].get("fixed_take_profit",0),
                    supertrend_exit_count=more["exit_counts"].get("supertrend_flip",0),
                    open_unrealized_net_usd=more["open_trade"]["hypothetical_net_usd"] if more["open_trade"] else None))
                print(key,json.dumps(dict(net=s.get("realized_net_usd"),
                    win_rate=s.get("win_rate_pct"),months=s["profitable_full_months"],
                    exit_reasons=more["exit_counts"])),flush=True)
    pd.DataFrame(rows).to_csv(OUT/"comparison.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(summaries,indent=2)+"\n")


if __name__=="__main__":
    main()
