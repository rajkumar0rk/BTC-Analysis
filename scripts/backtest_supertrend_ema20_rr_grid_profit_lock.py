#!/usr/bin/env python3
"""Research-only BTCUSD 1H Supertrend + EMA20; 12 fixed-point SL:TP scenarios with causal profit protection."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

BASE=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/ema20_st_rr_grid_protected_1h")
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


RR_PAIRS = ((1,1),(1,2),(1,3),(1,4),(2,2),(2,4),(2,6),(2,8),(3,3),(3,6),(3,9),(3,12))
POINT_UNIT = 100.
PROFILES = {"none": (0.,0.), "early_75_lock50": (.75,.50), "late_90_lock75": (.90,.75)}


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


def bar_exit(side,opened,highest,lowest,stop,tp,entry_minute=False):
    """Conservative stop-first with stop gaps worsened and no TP positive gap credit."""
    stop_hit=lowest<=stop if side==1 else highest>=stop
    if stop_hit:
        if entry_minute:
            # Cannot establish intraminute chronology, conservatively register stop.
            mid=float(stop)
        else:
            mid=float(min(opened,stop) if side==1 else max(opened,stop))
        return mid,"stop"
    tp_hit=highest>=tp if side==1 else lowest<=tp
    if tp_hit and not entry_minute:
        return float(tp),"tp"
    return None,None


def smoke_test():
    assert bar_exit(1,110.,123.,101.,105.,120.)==(105.,"stop")
    assert bar_exit(-1,90.,101.,76.,95.,80.)==(95.,"stop")
    assert bar_exit(1,99.,123.,97.,105.,120.)==(99.,"stop")
    assert bar_exit(-1,102.,105.,79.,95.,80.)==(102.,"stop")
    assert bar_exit(1,110.,122.,106.,105.,120.)==(120.,"tp")
    assert bar_exit(-1,90.,94.,79.,95.,80.)==(80.,"tp")
    assert bar_exit(1,110.,122.,106.,105.,120.,entry_minute=True)==(None,None)
    assert bar_exit(1,110.,122.,104.,105.,120.,entry_minute=True)==(105.,"stop")


def replay(m,h,entries,mode,sl_points,tp_points,profile):
    """Simulate independent one-entry-per-cycle paths, exits at SL/TP/lock/ST flip."""
    activation,lock_fraction=PROFILES[profile]
    op=m.open.to_numpy(float);hi=m.high.to_numpy(float);lo=m.low.to_numpy(float)
    close=m.close.to_numpy(float);times=m.index
    hside=h.side.to_numpy()
    total=len(op);n_hours=len(h)
    trades=[];cash=START_USD;peak=START_USD
    worst_mark=START_USD;max_excursion=0.
    open_trade=None
    for ev in entries:
        side=ev["side"];j0=ev["entry_j"];entry=ev["entry"]
        entry_hour=j0//60
        initial_stop=entry-side*sl_points
        stop=initial_stop
        tp=entry+side*tp_points
        lock_active=False
        max_favorable=0.;max_adverse=0.
        # Locate start of the next hour where completed 1H ST differs from
        # the selected trade's original direction.
        flip_j=total
        for hour in range(entry_hour+1,n_hours):
            if int(hside[hour-1])!=side:
                flip_j=hour*60
                break
        exit_j=None;exit_mid=None;exit_reason=None
        # Historical sequence 1m by 1m. Stop on entry minute conservative.
        for j in range(j0,min(flip_j,total)):
            result,what=bar_exit(side,op[j],hi[j],lo[j],stop,tp,j==j0)
            if result is not None:
                exit_j=j;exit_mid=result
                exit_reason=("profit_lock" if lock_active else "initial_stop") if what=="stop" else "take_profit"
                break
            # Do not use entry-minute extrema to claim activation / MFE.
            if j==j0: continue
            favorable_px=hi[j] if side==1 else lo[j]
            adverse_px=lo[j] if side==1 else hi[j]
            favorable=max(0.,side*(favorable_px-entry))
            adverse=max(0.,side*(entry-adverse_px))
            max_favorable=max(max_favorable,favorable)
            max_adverse=max(max_adverse,adverse)
            # Unrealized marked equity at adverse extreme, with hypothetical close costs.
            hypo_exit=adverse_px-side*SLIP
            hypothetical=cash+QTY*side*(hypo_exit-entry)-QTY*FEE*(entry+hypo_exit)
            worst_mark=min(worst_mark,hypothetical)
            max_excursion=max(max_excursion,peak-hypothetical)
            # Profit lock is a strictly NEXT-minute stop change (never this bar).
            if profile!="none" and not lock_active and favorable>=activation*tp_points:
                new_stop=entry+side*(lock_fraction*tp_points)
                stop=max(stop,new_stop) if side==1 else min(stop,new_stop)
                lock_active=True

        if exit_j is None and flip_j<total:
            exit_j=flip_j;exit_mid=float(op[flip_j]);exit_reason="supertrend_flip"
        if exit_j is None:
            hypothetical_exit=float(close[-1])-side*SLIP
            unrealized=QTY*side*(hypothetical_exit-entry)-QTY*FEE*(entry+hypothetical_exit)
            open_trade=dict(
                entry_utc=str(times[j0]),side="LONG" if side==1 else "SHORT",
                signal_utc=ev["signal"],mark_price=float(close[-1]),
                entry_price=round(entry,2),initial_stop=round(initial_stop,2),
                target_price=round(tp,2),hypothetical_net_usd=round(unrealized,5),
                note="Unrealized position NOT forced closed at archive boundary")
            continue
        exit_fill=exit_mid-side*SLIP
        gross=QTY*side*(exit_fill-entry)
        fees=QTY*FEE*(entry+exit_fill)
        net=gross-fees
        trades.append(dict(
            mode=mode,rr=f"{int(sl_points/POINT_UNIT)}:{int(tp_points/POINT_UNIT)}",
            profile=profile,sl_points=sl_points,tp_points=tp_points,
            setup=ev["kind"],side="LONG" if side==1 else "SHORT",
            signal_utc=ev["signal"],
            entry_utc=str(times[j0]),exit_utc=str(times[exit_j]),
            entry_price=round(entry,2),initial_stop=round(initial_stop,2),
            final_stop=round(stop,2),target_price=round(tp,2),
            exit_price=round(exit_fill,2),
            hold_minutes=exit_j-j0,
            gross_usd=round(gross,6),fees_usd=round(fees,6),
            net_usd=round(net,6),exit_reason=exit_reason,
            max_favorable_points=round(max_favorable,2),
            max_adverse_points=round(max_adverse,2)))
        cash+=net;peak=max(peak,cash)
    df=pd.DataFrame(trades)
    reasons=df.exit_reason.value_counts().to_dict() if len(df) else {}
    return df,dict(
        sl_points=sl_points,tp_points=tp_points,
        risk_reward=f"{int(sl_points/POINT_UNIT)}:{int(tp_points/POINT_UNIT)}",
        protection_profile=profile,
        protection_activation_points=activation*tp_points if profile!="none" else None,
        protection_lock_points=lock_fraction*tp_points if profile!="none" else None,
        exit_counts={k:int(v) for k,v in reasons.items()},
        open_trade=open_trade,
        worst_open_mark_equity_usd=round(worst_mark,4),
        max_excursion_below_previous_realized_peak_usd=round(max_excursion,4),
        note="No funding, liquidation, mark price, bid/ask. Conservative entry-minute stop and stop-first intra-minute ambiguity")



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
    entries={mode:entry_candidates(m,h,mode) for mode in ("touch","reclaim","combined")}
    qual=dict(
        source="Delta Exchange India BTCUSD perpetual 1m OHLCV",
        source_files=nfiles,minute_bars=len(m),hourly_bars=len(h),
        first_utc=str(m.index[0]),last_utc=str(m.index[-1]),
        validated_consecutive_minutes=True,
        risk_reward_unit_btc_price_points=POINT_UNIT,
        risk_reward_pairs=[f"{a}:{b}" for a,b in RR_PAIRS],
        entry_modes=list(entries),
        candidate_trades_per_mode={k:len(v) for k,v in entries.items()},
        protection_profiles={k:list(v) for k,v in PROFILES.items()},
        initial_cash_usd=START_USD,quantity_btc=QTY,
        taker_fee_per_side_including_gst=FEE,
        adverse_slippage_btc_price_points_per_side=SLIP,
        max_one_filled_entry_per_supertrend_cycle=True,
        exit_rules=["fixed initial SL","fixed TP","optional next-minute profit lock","confirmed 1H ST reversal"],
        caveats=[
            "Initial fixed stop is newly reintroduced for this risk:reward sweep; earlier protected TP sweep had NO initial SL",
            "Entry-minute stop-first applies even when 1m bar's price path cannot show actual order of breakout and stop",
            "A next-minute activated lock does not protect the activating 1m price excursion",
            "No funding, mark price, bid/ask, liquidation or margin feasibility, exchange latency or order restrictions modeled",
            "Months previously research-exposed, no genuine untouched holdout; November 2026 is partial",
            "Monthly realized PnL booked by exit date in Asia/Kolkata"
        ])
    (OUT/"quality.json").write_text(json.dumps(qual,indent=2)+"\n")
    results={}
    rows=[]
    for mode in entries:
        for a,b in RR_PAIRS:
            sl=a*POINT_UNIT;tp=b*POINT_UNIT
            for profile in PROFILES:
                key=f"{mode}_{a}to{b}_{profile}"
                trades,meta=replay(m,h,entries[mode],mode,sl,tp,profile)
                trades.to_csv(OUT/f"{key}_trades.csv",index=False)
                monthly_table=monthly(trades,m.index[0],m.index[-1])
                monthly_table.to_csv(OUT/f"{key}_monthly_ist.csv",index=False)
                summ=summarize(trades,meta)
                summ["profitable_full_months"]=int(((monthly_table.net_usd>0)&monthly_table.complete_month).sum())
                summ["total_full_months"]=int(monthly_table.complete_month.sum())
                results[key]=summ
                rows.append(dict(
                    configuration=key,entry_mode=mode,rr=f"{a}:{b}",
                    sl_points=sl,tp_points=tp,protection=profile,
                    closed_trades=summ.get("closed_trades",0),
                    wins=summ.get("wins",0),losses=summ.get("losses",0),
                    win_rate_pct=summ.get("win_rate_pct"),
                    gross_usd=summ.get("gross_usd"),fees_usd=summ.get("fees_usd"),
                    net_usd=summ.get("realized_net_usd"),
                    pf=summ.get("profit_factor"),
                    max_realized_drawdown_pct=summ.get("realized_max_drawdown_pct"),
                    positive_full_months=summ["profitable_full_months"],
                    initial_stop_exits=meta["exit_counts"].get("initial_stop",0),
                    profit_lock_exits=meta["exit_counts"].get("profit_lock",0),
                    tp_exits=meta["exit_counts"].get("take_profit",0),
                    supertrend_flip_exits=meta["exit_counts"].get("supertrend_flip",0),
                    open_unrealized_net_usd=meta["open_trade"]["hypothetical_net_usd"] if meta["open_trade"] else None))
                print(f"{key}: net={summ.get('realized_net_usd')} win={summ.get('win_rate_pct')} "
                      f"months={summ['profitable_full_months']}/22",flush=True)
    pd.DataFrame(rows).to_csv(OUT/"comparison.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(results,indent=2)+"\n")


if __name__=="__main__":
    main()
