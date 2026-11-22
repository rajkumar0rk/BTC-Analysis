#!/usr/bin/env python3
"""Research-only BTCUSD 1H Supertrend + EMA20; 1H green-confirmed EMA20 Touch, comparison with breakout entry and percent lock ladders."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

BASE=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/st_ema20_touch_next_green_1h")
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



def next_hour_confirmation_candidates(m, h, allow_short=False):
    """Confirm 1H Touch by the next completely CLOSED 1H candle COLOR.

    setups(h,"touch") produces events keyed at i+1, where i is the closed
    1H Touch signal index. Confirm at i+1 close, enter at i+2 open.
    No observable information from unfinished candle i+1 may be used.
    """
    events=setups(h,"touch")
    cycles=set()
    out=[]
    tally=dict(touch_signals=len(events),long_signals=0,short_signals=0,
               skipped_short=0,wrong_color_or_doji=0,
               supertrend_flipped=0,not_enough_future_data=0,
               already_filled_cycle=0,filled_long=0,filled_short=0)
    total=len(m)
    for hour, ev in sorted(events.items()):
        side=int(ev["side"])
        tally["long_signals" if side==1 else "short_signals"]+=1
        if side==-1 and not allow_short:
            tally["skipped_short"]+=1
            continue
        if ev["cycle"] in cycles:
            tally["already_filled_cycle"]+=1
            continue
        if hour>=len(h) or (hour+1)*60>=total:
            tally["not_enough_future_data"]+=1
            continue
        if int(h.side.iloc[hour]) != side:
            tally["supertrend_flipped"]+=1
            continue
        confirm=h.iloc[hour]
        bullish=confirm.close > confirm.open
        bearish=confirm.close < confirm.open
        if not (bullish if side==1 else bearish):
            tally["wrong_color_or_doji"]+=1
            continue
        j=(hour+1)*60
        assert j%60==0
        assert m.index[j] >= h.index[hour]+pd.Timedelta(hours=1)
        price=float(m.open.iloc[j])+side*SLIP
        out.append(dict(
            entry_j=j,entry=price,side=side,kind="touch",cycle=ev["cycle"],
            signal=ev["signal"]))
        cycles.add(ev["cycle"])
        tally["filled_long" if side==1 else "filled_short"]+=1
    assert len({e["cycle"] for e in out})==len(out)
    return out,tally


def smoke_confirmation():
    idx=pd.date_range("2025-01-01",periods=6,freq="h",tz="UTC")
    h=pd.DataFrame(dict(open=[100,100,101,100,99,99],
                        close=[101,102,99,99,100,100],
                        side=[1,1,1,-1,-1,1]),index=idx)
    minute_index=pd.date_range("2025-01-01",periods=6*60,freq="min",tz="UTC")
    m=pd.DataFrame(dict(open=np.full(6*60,100.0)),index=minute_index)
    # Separate confirmation helper *must* only fill after the next close.
    # With signal i=0, confirmation i+1 green, buy at i+2 OPEN.
    original=setups
    try:
        def fixture(h_, mode):
            assert mode=="touch"
            return {1:dict(side=1,cycle=1,kind="touch",signal=str(h_.index[0])),
                    2:dict(side=1,cycle=2,kind="touch",signal=str(h_.index[1])),
                    3:dict(side=-1,cycle=3,kind="touch",signal=str(h_.index[2])),
                    4:dict(side=1,cycle=4,kind="touch",signal=str(h_.index[3]))}
        globals()["setups"]=fixture
        result,tally=next_hour_confirmation_candidates(m,h,allow_short=True)
        assert len(result)==2,(result,tally)
        assert result[0]["entry_j"]==120 and result[0]["entry"]==105.,result
        assert result[1]["entry_j"]==240 and result[1]["side"]==-1,result
        assert tally["wrong_color_or_doji"]==1,(result,tally)
        assert tally["supertrend_flipped"]==1,(result,tally)
        only,tally2=next_hour_confirmation_candidates(m,h,allow_short=False)
        assert len(only)==1 and only[0]["side"]==1,only
    finally:
        globals()["setups"]=original


from bisect import bisect_right

# Exact selected percent-of-entry stop protection levels.
LADDERS = {
    "S01_0p14": (0.14,),
    "S02_0p50": (0.50,),
    "S03_0p75": (0.75,),
    "S04_1": (1.0,),
    "S05_2": (2.0,),
    "S06_5": (5.0,),
    "L01_0p5_1_2_5": (0.5, 1.0, 2.0, 5.0),
    "L02_1_2_5": (1.0, 2.0, 5.0),
    "L03_2_3_5": (2.0, 3.0, 5.0),
}

PATHS = ("open_high_low_close", "open_low_high_close")



def next_stop_on_segment(side, entry, start, finish, current_stop, ladder):
    """Advance along a continuous intraminute price segment.

    Raises protective stop IMMEDIATELY each time a favorable milestone is
    crossed. If segment moves adversely, exit upon crossing preexisting stop.
    The stop is not activated after the segment completes; it is active inside
    this segment and hence the SAME 1-minute candle.
    """
    stop = current_stop
    gained = []
    if side * (finish - start) > 0:
        for rung in ladder:
            target = entry + side * entry * (rung / 100.0)
            # A favorable segment crosses the level if it moves from below to
            # at/above it in favorable (side-adjusted) coordinates.
            if side * (start - target) < -1e-9 and side * (finish - target) >= -1e-9:
                proposed = float(target)
                if stop is None or side * (proposed - stop) > 1e-9:
                    stop = proposed
                    gained.append(rung)
        return float(finish), stop, gained, False
    if stop is not None:
        if side * (start - stop) < -1e-9:
            # Gap through a previously active stop (handled at bar open, but
            # retained as safety for segment boundaries).
            return float(start), stop, gained, True
        if side * (start - stop) >= -1e-9 and side * (finish - stop) <= 1e-9:
            return float(stop), stop, gained, True
    return float(finish), stop, gained, False


def bar_path(opened,highest,lowest,closed,path):
    if path == "open_high_low_close":
        return (float(opened),float(highest),float(lowest),float(closed))
    if path == "open_low_high_close":
        return (float(opened),float(lowest),float(highest),float(closed))
    raise ValueError(path)


def simulate_bar(nodes,side,entry,mid_entry,prev_stop,ladder,entry_bar):
    """Replay the exact hypothetical price path. Tracks post-entry segments.

    For entry_bar: do NOT credit any movement before the 1H signal-breakout
    fill, which can occur anywhere inside the bar depending on path.
    """
    stop = prev_stop
    active = not entry_bar
    total_rungs = []
    favorable = 0.
    adverse = 0.
    if active and stop is not None and side * (nodes[0] - stop) < -1e-9:
        return dict(exit_mid=float(nodes[0]),stop=stop,rungs=(),
                    favorable=0.,adverse=max(0.,side*(entry-nodes[0])))
    if entry_bar and side * (nodes[0] - mid_entry) >= -1e-9:
        active = True

    for left,right in zip(nodes,nodes[1:]):
        start=float(left)
        finish=float(right)
        if not active:
            # Only enter as the breakout threshold is crossed in the favorable
            # direction, and only if the path actually reaches mid_entry.
            if side*(finish-start)<=0:
                continue
            if side*(start-mid_entry)>1e-9:
                # Should not arise if entry bar was treated at opening gap.
                raise AssertionError("unexpected entry path beyond breakout")
            if side*(finish-mid_entry)<-1e-9:
                continue
            start=float(mid_entry)
            active=True

        reached,new_stop,rungs,hit=next_stop_on_segment(
            side,entry,start,finish,stop,ladder)
        if rungs:
            total_rungs.extend(rungs)
        stop=new_stop
        favorable=max(favorable,max(0.,side*(reached-entry)))
        adverse=max(adverse,max(0.,side*(entry-reached)))
        # If segment moved in favor of position but stopped at its *end*,
        # the precise threshold would be live for any subsequent reversal.
        if hit:
            return dict(exit_mid=reached,stop=stop,rungs=tuple(total_rungs),
                        favorable=favorable,adverse=adverse)
    if not active:
        raise AssertionError("entry candidate not fillable under chosen OHLC path")
    return dict(exit_mid=None,stop=stop,rungs=tuple(total_rungs),
                favorable=favorable,adverse=adverse)


def smoke_test():
    assert len(LADDERS)==9
    assert (2.0,3.0,5.0)==LADDERS["L03_2_3_5"]
    for values in LADDERS.values():
        assert all(a<b for a,b in zip(values,values[1:]))
    # A +1% LONG lock on BTC 80k is a stop at 80,800.
    r=simulate_bar((80000,81000,79900,80300),1,80000,80000,None,(1.0,),False)
    assert r["exit_mid"]==80800 and r["rungs"]==(1.0,),r
    r=simulate_bar((80000,79000,81000,80900),1,80000,80000,None,(1.0,),False)
    assert r["exit_mid"] is None and r["stop"]==80800,r
    smoke_confirmation()


def replay(m,h,entries,mode,ladder_id,path):
    ladder=LADDERS[ladder_id]
    op=m.open.to_numpy(float)
    hi=m.high.to_numpy(float)
    lo=m.low.to_numpy(float)
    close=m.close.to_numpy(float)
    times=m.index
    hside=h.side.to_numpy()
    total=len(op)
    n_hours=len(h)
    trades=[]
    cash=START_USD
    peak=START_USD
    worst_mark=START_USD
    open_trade=None
    for event in entries:
        side=int(event["side"])
        j0=int(event["entry_j"])
        entry=float(event["entry"])
        mid_entry=entry-side*SLIP
        stop=None
        crossed=set()
        peak_favorable=0.
        max_adverse=0.
        flip_hour=np.flatnonzero(hside[j0//60:] != side)
        flip_j=(int(j0//60+flip_hour[0])+1)*60 if len(flip_hour)>0 else total
        flip_j=min(flip_j,total)
        exit_j=None
        exit_mid=None
        reason=None
        for j in range(j0,flip_j):
            nodes=bar_path(op[j],hi[j],lo[j],close[j],path)
            event_bar=simulate_bar(nodes,side,entry,mid_entry,stop,ladder,j==j0)
            stop=event_bar["stop"]
            crossed.update(event_bar["rungs"])
            peak_favorable=max(peak_favorable,event_bar["favorable"])
            max_adverse=max(max_adverse,event_bar["adverse"])
            bad_price=entry-side*max_adverse
            bad_fill=bad_price-side*SLIP
            mark=cash+QTY*side*(bad_fill-entry)-QTY*FEE*(entry+bad_fill)
            worst_mark=min(worst_mark,mark)
            if event_bar["exit_mid"] is not None:
                exit_j=j
                exit_mid=event_bar["exit_mid"]
                reason="profit_lock"
                break
        if exit_j is None and flip_j<total:
            exit_j=flip_j
            exit_mid=float(op[flip_j])
            reason="supertrend_flip"
        if exit_j is None:
            unrealized_exit=float(close[-1])-side*SLIP
            unrealized=QTY*side*(unrealized_exit-entry)-QTY*FEE*(entry+unrealized_exit)
            open_trade=dict(entry_utc=str(times[j0]),
                side="LONG" if side==1 else "SHORT",
                entry_price=round(entry,2),
                last_lock=round(side*(stop-entry),2) if stop is not None else None,
                last_mid=float(close[-1]),
                hypothetical_net_usd=round(unrealized,5),
                note="Position still OPEN, not forced closed")
            continue
        exit_fill=float(exit_mid)-side*SLIP
        gross=QTY*side*(exit_fill-entry)
        fee=QTY*FEE*(entry+exit_fill)
        net=gross-fee
        trades.append(dict(
            mode=mode,ladder=ladder_id,path=path,
            side="LONG" if side==1 else "SHORT",setup=event["kind"],
            entry_utc=str(times[j0]),exit_utc=str(times[exit_j]),signal_utc=event["signal"],
            entry_price=round(entry,2),exit_price=round(exit_fill,2),
            stop_at_exit=round(stop,2) if stop is not None else None,
            total_rungs_crossed=len(crossed),high_rung=max(crossed) if crossed else None,
            max_favorable_points=round(peak_favorable,2),
            max_adverse_points=round(max_adverse,2),
            hold_minutes=exit_j-j0,
            gross_usd=round(gross,6),fees_usd=round(fee,6),net_usd=round(net,6),
            exit_reason=reason))
        cash+=net
        peak=max(peak,cash)

    t=pd.DataFrame(trades)
    counts=t.exit_reason.value_counts().to_dict() if len(t) else {}
    return t,dict(
        ladder=ladder_id,levels=list(ladder),intraminute_path=path,
        exit_counts={k:int(v) for k,v in counts.items()},
        open_trade=open_trade,
        worst_open_mark_equity_usd=round(worst_mark,4),
        note="Hypothetical continuous OHLC path; immediate on-cross stop modifications; no exchange tick/order/latency/liquidation model")



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
    original=entry_candidates(m,h,"touch")
    green_long,count_long=next_hour_confirmation_candidates(m,h,allow_short=False)
    green_both,count_both=next_hour_confirmation_candidates(m,h,allow_short=True)
    entries={
      "original_touch_both": original,
      "original_touch_long": [e for e in original if e["side"]==1],
      "next_1h_green_long": green_long,
      "next_1h_matching_color_both": green_both,
    }
    # Entries are unique by Supertrend cycle per candidate strategy.
    for label,evs in entries.items():
        assert len(set(e["cycle"] for e in evs))==len(evs),(label,len(evs))
        assert all(0<=e["entry_j"]<len(m) for e in evs)
    assert len(entries["original_touch_both"])==253, "Baseline entry parity changed; abort"
    quality=dict(
      source="Delta Exchange India BTCUSD perpetual 1m OHLCV",
      source_files=nfiles,minute_bars=len(m),hourly_bars=len(h),
      first_utc=str(m.index[0]),last_utc=str(m.index[-1]),
      strategy="1H ST(ATR10, multiplier3) + EMA20 TOUCH, then next 1H candle color confirmation",
      confirmation_long="next fully closed 1H candle GREEN (close > open), ST still GREEN",
      confirmation_short_auxiliary="next fully closed 1H candle RED (close < open), ST still RED",
      next_hour_entry="market at next hour OPEN AFTER 1H confirming candle CLOSE; no lookahead",
      original_baseline_entry="next 1H breakout of TOUCH candle high/low +/- 0.5, using 1m prices",
      confirmation_long_only_counts=count_long,
      confirmation_both_counts=count_both,
      candidate_counts={name:len(e) for name,e in entries.items()},
      percent_ladders={name:list(x) for name,x in LADDERS.items()},
      paths=list(PATHS),position_qty_btc=QTY,initial_cash_usd=START_USD,
      taker_fee_plus_gst_per_side=FEE,adverse_slippage_price_points_per_side=SLIP,
      risks=[
        "1m OHLC candle high/low sequencing unknown; separate two hypothetical intraminute paths",
        "Stop amendment and execution assumed immediate; real latency/slippage not known",
        "No initial protective stop; large reversal or liquidation possible before profit lock",
        "Funding, liquidation, spread, margin/mark price and orderbook depth unmodeled",
        "Nov 2026 partial, Jan2025-Oct2026 22 complete months, prior historical data previously inspected"]
    )
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    rows=[]
    full={}
    for mode,evs in entries.items():
        for ladder in LADDERS:
            for path in PATHS:
                key=f"{mode}_{ladder}_{path}"
                t,meta=replay(m,h,evs,mode,ladder,path)
                t.to_csv(OUT/f"{key}_trades.csv",index=False)
                mon=monthly(t,m.index[0],m.index[-1])
                mon.to_csv(OUT/f"{key}_monthly_ist.csv",index=False)
                summ=summarize(t,meta)
                first=LADDERS[ladder][0]
                months=int(((mon.net_usd>0)&mon.complete_month).sum())
                hit_first=int((t.max_favorable_points >= t.entry_price*(first/100.)-1e-8).sum()) if len(t) else 0
                full[key]=summ
                rows.append(dict(
                    scenario=key,entry_mode=mode,ladder=ladder,
                    percent_rungs="-".join(f"{x:.3f}" for x in LADDERS[ladder]),
                    path=path,
                    entry_candidates=len(evs),
                    closed_trades=summ.get("closed_trades",0),
                    wins=summ.get("wins",0),losses=summ.get("losses",0),
                    win_rate_pct=summ.get("win_rate_pct"),
                    gross_usd=summ.get("gross_usd"),fees_usd=summ.get("fees_usd"),
                    net_usd=summ.get("realized_net_usd"),
                    profit_factor=summ.get("profit_factor"),
                    realized_max_dd_pct=summ.get("realized_max_drawdown_pct"),
                    positive_months=months,
                    reached_first_level=hit_first,
                    profit_lock_exits=meta["exit_counts"].get("profit_lock",0),
                    supertrend_flip_exits=meta["exit_counts"].get("supertrend_flip",0),
                    unrealized_open_trade_usd=meta["open_trade"]["hypothetical_net_usd"] if meta["open_trade"] else None))
                print(key, json.dumps(dict(
                    n=len(t),net=summ.get("realized_net_usd"),
                    win=summ.get("win_rate_pct"),months=months,
                    stop=meta["exit_counts"].get("profit_lock",0),
                    flip=meta["exit_counts"].get("supertrend_flip",0))),flush=True)
    pd.DataFrame(rows).to_csv(OUT/"comparison.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(full,indent=2)+"\n")


if __name__=="__main__":
    main()
