#!/usr/bin/env python3
"""Research-only BTCUSD 1H Supertrend + EMA20; 1-5%+ percentage-of-entry profit lock scenarios with same-candle updates."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

BASE=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/st_ema20_large_percent_locks_1h")
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


from bisect import bisect_right

# Explicit percentages, e.g. 0.12 means 0.12% of the ENTRY price.
LADDERS = {
    "S01_only_0p14": (0.14,),
    "S02_only_0p50": (0.5,),
    "S03_only_0p75": (0.75,),
    "S04_only_1": (1.0,),
    "S05_only_1p5": (1.5,),
    "S06_only_2": (2.0,),
    "S07_only_3": (3.0,),
    "S08_only_4": (4.0,),
    "S09_only_5": (5.0,),
    "S10_only_7p5": (7.5,),
    "S11_only_10": (10.0,),
    "L01_0p14_1_2_5": (0.14, 1.0, 2.0, 5.0),
    "L02_0p2_1_2_5": (0.2, 1.0, 2.0, 5.0),
    "L03_0p5_1_2_5": (0.5, 1.0, 2.0, 5.0),
    "L04_0p75_1_2_5": (0.75, 1.0, 2.0, 5.0),
    "L05_1_2_5": (1.0, 2.0, 5.0),
    "L06_1_1p5_2_3_5": (1.0, 1.5, 2.0, 3.0, 5.0),
    "L07_1_2_3_4_5": (1.0, 2.0, 3.0, 4.0, 5.0),
    "L08_1_3_5": (1.0, 3.0, 5.0),
    "L09_1_2_4_8": (1.0, 2.0, 4.0, 8.0),
    "L10_2_3_5": (2.0, 3.0, 5.0),
    "L11_2_5_10": (2.0, 5.0, 10.0),
    "L12_0p5_1_1p5_2": (0.5, 1.0, 1.5, 2.0),
    "L13_0p14_0p5_1_2_5": (0.14, 0.5, 1.0, 2.0, 5.0),
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
    assert len(LADDERS)==24
    assert (1.0,2.0,5.0)==LADDERS["L05_1_2_5"]
    assert (0.14,1.0,2.0,5.0)==LADDERS["L01_0p14_1_2_5"]
    assert 5.0 in LADDERS["S09_only_5"]
    for levels in LADDERS.values():
        assert all(0 < r <= 10.0 for r in levels),levels
        assert all(a<b for a,b in zip(levels,levels[1:])),levels
    # LONG: entry 80,000 +1%=80,800; +2%=81,600; +5%=84,000.
    r=simulate_bar((80000,82000,79800,80500),1,80000,80000,None,
                   (1.0,2.0,5.0),False)
    assert r["exit_mid"] == 81600 and r["rungs"]==(1.0,2.0),r
    r=simulate_bar((80000,79900,82000,81900),1,80000,80000,None,
                   (1.0,2.0,5.0),False)
    assert r["exit_mid"] == 81600 and r["rungs"]==(1.0,2.0),r
    r=simulate_bar((80000,84050,84500,84400),1,80000,80000,None,
                   (1.0,2.0,5.0),False)
    assert r["exit_mid"] is None and r["stop"]==84000,r
    # SHORT +5%=price -5% immediately, stop can execute on same bar.
    r=simulate_bar((80000,75900,80100,79900),-1,80000,80000,None,
                   (1.0,2.0,5.0),False)
    assert r["exit_mid"]==76000 and r["rungs"]==(1.0,2.0,5.0),r
    # Enter inside entry minute; no profit rung before entry.
    r=simulate_bar((79900,81000,79000,80050),1,80000,79995,None,
                   (1.0,2.0,5.0),True)
    assert r["exit_mid"]==80800 and r["rungs"]==(1.0,),r
    # Entry-based % moves, NOT fixed BTC points.
    r=simulate_bar((100000,102100,99800,100100),1,100000,100000,None,
                   (1.0,2.0,5.0),False)
    assert r["exit_mid"]==102000 and r["rungs"]==(1.0,2.0),r
    # A stop active at prior bar is gap filled worse, not at target.
    r=simulate_bar((80100,81100,79900,80500),1,80000,80000,80800,
                   (1.0,2.0,5.0),False)
    assert r["exit_mid"]==80100,r


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
    entries={mode:entry_candidates(m,h,mode) for mode in ("touch","reclaim","combined")}
    quality=dict(
        source="Delta Exchange India BTCUSD perpetual 1m OHLCV",
        source_files=nfiles,minute_bars=len(m),hourly_bars=len(h),
        first_utc=str(m.index[0]),last_utc=str(m.index[-1]),
        validated_consecutive_minutes=True,
        ladder_values_in_percent={name:list(rungs) for name,rungs in LADDERS.items()},
        definition="0.12 is 0.12 percent of actual execution entry price (entry*0.0012)",
        paths=list(PATHS),
        entry_modes=list(entries),
        entry_count={name:len(evs) for name,evs in entries.items()},
        qty_btc=QTY,initial_cash_usd=START_USD,
        taker_fee_plus_GST_per_side=FEE,
        adverse_execution_slippage_btc_points_per_side=SLIP,
        min_no_slippage_taker_fee_break_even_pct=2*FEE*100,
        estimated_roundtrip_slippage_btc_points=2*SLIP,
        one_fill_per_ST_cycle=True,no_initial_SL=True,no_fixed_TP=True,
        instant_stop_update_same_1m_bar=True,
        entry_minute_modeling="Follow hypothetical OHLC path after breakout, immediately on-touch activate profit lock",
        ladder_after_last_rung="hold final rung; no invented extra percentage milestones",
        fallback_exit="next 1m open after completed opposite 1H Supertrend flip",
        caveats=[
            "OHLC 1m cannot resolve intraminute high/low sequence, two possible path models are replayed separately",
            "No exchange tick sequence, order amendment latency, margin, funding, mark/index price or liquidation model",
            "A 0.12 percent gross lock can be negative net after the fee, GST and slippage",
            "No pristine out-of-sample, parameters are exploratory, November 2026 partial",
            "Monthly realized cash PnL is booked by exit month in IST"]
    )
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    summaries={}
    rows=[]
    for mode,evs in entries.items():
        for ladder in LADDERS:
            for path in PATHS:
                key=f"{mode}_{ladder}_{path}"
                trades,meta=replay(m,h,evs,mode,ladder,path)
                trades.to_csv(OUT/f"{key}_trades.csv",index=False)
                month=monthly(trades,m.index[0],m.index[-1])
                month.to_csv(OUT/f"{key}_monthly_ist.csv",index=False)
                summ=summarize(trades,meta)
                summ["profitable_full_months"]=int(((month.net_usd>0)&month.complete_month).sum())
                summ["total_full_months"]=int(month.complete_month.sum())
                summaries[key]=summ
                first_pct=LADDERS[ladder][0]
                hit_first=int((trades.max_favorable_points >= trades.entry_price*(first_pct/100.)-1e-8).sum()) if len(trades) else 0
                hit_fee_only=int((trades.max_favorable_points >= trades.entry_price*(2*FEE)-1e-8).sum()) if len(trades) else 0
                hit_fee_plus_slip=int((trades.max_favorable_points >= trades.entry_price*(2*FEE)+2*SLIP-1e-8).sum()) if len(trades) else 0
                hit_1pct=int((trades.max_favorable_points >= trades.entry_price*.01-1e-8).sum()) if len(trades) else 0
                hit_2pct=int((trades.max_favorable_points >= trades.entry_price*.02-1e-8).sum()) if len(trades) else 0
                hit_5pct=int((trades.max_favorable_points >= trades.entry_price*.05-1e-8).sum()) if len(trades) else 0
                rows.append(dict(
                    scenario=key,entry_mode=mode,ladder=ladder,
                    percent_rungs="-".join(f"{x:.3f}" for x in LADDERS[ladder]),
                    first_pct=first_pct,
                    intraminute_path=path,
                    trades=summ.get("closed_trades",0),
                    wins=summ.get("wins",0),losses=summ.get("losses",0),
                    win_pct=summ.get("win_rate_pct"),
                    gross_usd=summ.get("gross_usd"),fees_usd=summ.get("fees_usd"),
                    net_usd=summ.get("realized_net_usd"),
                    profit_factor=summ.get("profit_factor"),
                    max_realized_drawdown_pct=summ.get("realized_max_drawdown_pct"),
                    profitable_full_months=summ["profitable_full_months"],
                    hit_first_rung=hit_first,
                    hit_0p118_fee_only=hit_fee_only,
                    hit_fee_plus_10pts=hit_fee_plus_slip,
                    hit_1pct_before_exit=hit_1pct,
                    hit_2pct_before_exit=hit_2pct,
                    hit_5pct_before_exit=hit_5pct,
                    profit_lock_exits=meta["exit_counts"].get("profit_lock",0),
                    ST_reversal_exits=meta["exit_counts"].get("supertrend_flip",0),
                    unrealized_open_trade_usd=meta["open_trade"]["hypothetical_net_usd"] if meta["open_trade"] else None))
                print(key,json.dumps(dict(net=summ.get("realized_net_usd"),
                    win_pct=summ.get("win_rate_pct"),
                    months=summ["profitable_full_months"],
                    hit_first_rung=hit_first,
                    exits=meta["exit_counts"])),flush=True)
    pd.DataFrame(rows).to_csv(OUT/"comparison.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(summaries,indent=2)+"\n")


if __name__=="__main__":
    main()
