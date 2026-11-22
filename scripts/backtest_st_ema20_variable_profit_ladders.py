#!/usr/bin/env python3
"""Research-only BTCUSD 1H Supertrend + EMA20; nonuniform user-specified profit lock ladders, no initial SL."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

BASE=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/st_ema20_variable_lock_ladders_1h")
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

LADDERS={
  "L01_double_100_200_400_800": (100,200,400,800),
  "L02_linear_100_200_300_400_500": (100,200,300,400,500),
  "L03_100_300_600_900": (100,300,600,900),
  "L04_100_400_800": (100,400,800),
  "L05_100_500_1000": (100,500,1000),
  "L06_100_200_500_1000": (100,200,500,1000),
  "L07_100_300_500_700_1000": (100,300,500,700,1000),
  "L08_100_200_400_600_1000": (100,200,400,600,1000),
  "L09_100_250_500_1000": (100,250,500,1000),
  "L10_100_400_800_1600": (100,400,800,1600),
  "L11_100_500_1000_2000": (100,500,1000,2000),
  "L12_100_300_600_1200_2400": (100,300,600,1200,2400),
  "L13_100_150_200_300_500_800": (100,150,200,300,500,800),
  "L14_100_200_300_500_800_1300": (100,200,300,500,800,1300),
}
INTERPRETATIONS=("behind","direct")


def extension(seed,limit=30000):
    """Extend finite examples so running profit locks can increase without cap."""
    levels=list(seed)
    assert levels[0]==100 and all(a<b for a,b in zip(levels,levels[1:]))
    doubling=all(levels[i]==2*levels[i-1] for i in range(1,len(levels)))
    last_step=levels[-1]-levels[-2]
    while levels[-1]<limit:
        levels.append(levels[-1]*2 if doubling else levels[-1]+last_step)
    return tuple(levels)


EXTENDED={key:extension(ladder) for key,ladder in LADDERS.items()}


def desired_lock(favorable,levels,variant):
    """Mapping from fully observed favorable 1M movement to locked points."""
    idx=bisect_right(levels,favorable+1e-8)-1
    if variant=="direct":
        return float(levels[idx]) if idx>=0 else None
    elif variant=="behind":
        return float(levels[idx-1]) if idx>=1 else None
    raise ValueError(variant)


def stop_exit(side,opened,high,low,stop):
    if stop is None:
        return None
    touched=low<=stop if side==1 else high>=stop
    if not touched:
        return None
    return float(min(opened,stop) if side==1 else max(opened,stop))


def smoke_test():
    L=EXTENDED["L01_double_100_200_400_800"]
    assert L[:6]==(100,200,400,800,1600,3200)
    assert desired_lock(99.9,L,"direct") is None
    assert desired_lock(100,L,"direct")==100.
    assert desired_lock(199.99,L,"direct")==100.
    assert desired_lock(200,L,"direct")==200.
    assert desired_lock(100,L,"behind") is None
    assert desired_lock(200,L,"behind")==100.
    assert desired_lock(400,L,"behind")==200.
    assert desired_lock(800,L,"behind")==400.
    assert desired_lock(1600,L,"behind")==800.
    assert desired_lock(999,EXTENDED["L02_linear_100_200_300_400_500"],"behind")==800.
    assert desired_lock(900,EXTENDED["L03_100_300_600_900"],"behind")==600.
    assert stop_exit(1,98.,130.,90.,105.)==98.
    assert stop_exit(-1,102.,110.,75.,95.)==102.
    assert stop_exit(1,110.,115.,106.,105.) is None


def replay(m,h,entries,mode,ladder_id,interpretation):
    levels=EXTENDED[ladder_id]
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
    max_excursion=0.
    open_trade=None
    for event in entries:
        side=event["side"]
        j0=event["entry_j"]
        entry=event["entry"]
        stop=None
        locked_points=0.
        favorable_high=0.
        max_adverse=0.
        upgrades=0
        peak_lock_index=-1
        exit_j=None
        exit_mid=None
        exit_reason=None
        flip_j=total
        for hour in range(j0//60+1,n_hours):
            if int(hside[hour-1])!=side:
                flip_j=hour*60
                break

        # Simulate each 1m candle sequentially: active stop FIRST, then the
        # completed candle can inform the next candle's higher stop.
        for j in range(j0,min(flip_j,total)):
            if j==j0:
                # Entry bar: unknown order of high/low vs breakout. No profit
                # lock or favorable movement assumed in this bar.
                continue

            price=stop_exit(side,op[j],hi[j],lo[j],stop)
            if price is not None:
                exit_j=j
                exit_mid=price
                exit_reason="profit_lock"
                break

            favorable_px=hi[j] if side==1 else lo[j]
            adverse_px=lo[j] if side==1 else hi[j]
            favorable=max(0.,side*(favorable_px-entry))
            adverse=max(0.,side*(entry-adverse_px))
            favorable_high=max(favorable_high,favorable)
            max_adverse=max(max_adverse,adverse)

            # 1m traded-price adverse mark, hypothetical fee & exit slippage.
            hypothetical_exit=adverse_px-side*SLIP
            marked=cash+QTY*side*(hypothetical_exit-entry)-QTY*FEE*(entry+hypothetical_exit)
            worst_mark=min(worst_mark,marked)
            max_excursion=max(max_excursion,peak-marked)

            lock=desired_lock(favorable_high,levels,interpretation)
            if lock is not None and lock>locked_points:
                # Next-minute activation; if price crossed lock within this
                # minute, next minute's open is used as a worse fill.
                locked_points=lock
                stop=entry+side*lock
                upgrades+=1
                peak_lock_index=bisect_right(levels,lock)-1

        if exit_j is None and flip_j<total:
            exit_j=flip_j
            exit_mid=float(op[flip_j])
            exit_reason="supertrend_flip"
        if exit_j is None:
            hypothetical_exit=float(close[-1])-side*SLIP
            hypothetical_net=QTY*side*(hypothetical_exit-entry)-QTY*FEE*(entry+hypothetical_exit)
            open_trade=dict(entry_utc=str(times[j0]),
                signal_utc=event["signal"],
                side="LONG" if side==1 else "SHORT",
                entry_price=round(entry,2),lock_points=locked_points,
                locked_stop_price=round(stop,2) if stop is not None else None,
                mark_price=float(close[-1]),hypothetical_net_usd=round(hypothetical_net,5),
                note="Not exited. Unrealized; market may liquidate earlier.")
            continue

        exit_fill=exit_mid-side*SLIP
        gross=QTY*side*(exit_fill-entry)
        fees=QTY*FEE*(entry+exit_fill)
        net=gross-fees
        trades.append(dict(
            mode=mode,ladder_id=ladder_id,interpretation=interpretation,
            setup=event["kind"],side="LONG" if side==1 else "SHORT",
            signal_utc=event["signal"],
            entry_utc=str(times[j0]),exit_utc=str(times[exit_j]),
            entry_price=round(entry,2),exit_price=round(exit_fill,2),
            lock_points=locked_points,stop_upgrades=upgrades,
            hold_minutes=exit_j-j0,
            gross_usd=round(gross,6),fees_usd=round(fees,6),
            net_usd=round(net,6),exit_reason=exit_reason,
            max_favorable_points=round(favorable_high,2),
            max_adverse_points=round(max_adverse,2)))
        cash+=net
        peak=max(peak,cash)

    frame=pd.DataFrame(trades)
    counts=frame.exit_reason.value_counts().to_dict() if len(frame) else {}
    return frame,dict(
        ladder_points=LADDERS[ladder_id],interpretation=interpretation,
        exit_counts={k:int(v) for k,v in counts.items()},
        open_trade=open_trade,
        worst_open_mark_equity_usd=round(worst_mark,4),
        max_excursion_below_previous_realized_peak_usd=round(max_excursion,4),
        note="1m next-candle lock activation, adverse gap-aware stop, no initial SL; liquidation not modeled")



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
        source="Delta Exchange India BTCUSD perpetual 1m price OHLCV",
        source_files=nfiles,minute_bars=len(m),hourly_bars=len(h),
        first_utc=str(m.index[0]),last_utc=str(m.index[-1]),
        validated_consecutive_minutes=True,
        quantity_btc=QTY,starting_cash_usd=START_USD,
        fee_per_side_plus_gst=FEE,slippage_btc_price_points_per_side=SLIP,
        ladders={k:list(v) for k,v in LADDERS.items()},
        extension_rule="after final rung: double if all listed rungs doubled; otherwise add last rung difference",
        interpretations={
            "behind":"When NEXT rung reached, activate protected stop at PREVIOUS rung; no lock until second rung",
            "direct":"When each rung reached, activate stop at THAT rung on following 1m candle"},
        entry_modes=list(entries),entry_counts={k:len(v) for k,v in entries.items()},
        one_filled_trade_per_supertrend_cycle=True,no_initial_sl=True,no_fixed_tp=True,
        fallback_exit="next 1m open after completed opposite 1H Supertrend flip",
        caveats=[
            "No initial stop: liquidation possible before lock activates",
            "No funding, mark prices, actual bid/ask spread, latency or exchange liquidation modeled",
            "Conservative causal execution: 1m stop updates only after completed bar, live next minute; gap fills can be worse",
            "No entry-minute favorable path claims; OHLC high/low ordering unknown",
            "Historic months previously inspected, so no untouched holdout",
            "November 2026 partial; monthly realized trade PnL allocated to IST exit date"])
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    summaries={}
    rows=[]
    for mode,events in entries.items():
        for ladder_id in LADDERS:
            for variant in INTERPRETATIONS:
                key=f"{mode}_{ladder_id}_{variant}"
                t,meta=replay(m,h,events,mode,ladder_id,variant)
                t.to_csv(OUT/f"{key}_trades.csv",index=False)
                mon=monthly(t,m.index[0],m.index[-1])
                mon.to_csv(OUT/f"{key}_monthly_ist.csv",index=False)
                summ=summarize(t,meta)
                summ["profitable_full_months"]=int(((mon.net_usd>0)&mon.complete_month).sum())
                summ["total_full_months"]=int(mon.complete_month.sum())
                summaries[key]=summ
                rows.append(dict(
                    configuration=key,entry_mode=mode,ladder_id=ladder_id,
                    ladder_levels="-".join(map(str,LADDERS[ladder_id])),
                    protection_variant=variant,
                    trades=summ.get("closed_trades",0),
                    wins=summ.get("wins",0),losses=summ.get("losses",0),
                    win_pct=summ.get("win_rate_pct"),
                    gross_usd=summ.get("gross_usd"),fees_usd=summ.get("fees_usd"),
                    net_usd=summ.get("realized_net_usd"),profit_factor=summ.get("profit_factor"),
                    max_realized_dd_pct=summ.get("realized_max_drawdown_pct"),
                    profitable_full_months=summ["profitable_full_months"],
                    lock_exits=meta["exit_counts"].get("profit_lock",0),
                    supertrend_flip_exits=meta["exit_counts"].get("supertrend_flip",0),
                    open_unrealized_usd=meta["open_trade"]["hypothetical_net_usd"] if meta["open_trade"] else None))
                print(key,json.dumps(dict(net=summ.get("realized_net_usd"),
                     win_pct=summ.get("win_rate_pct"),months=summ["profitable_full_months"],
                     exits=meta["exit_counts"])),flush=True)
    pd.DataFrame(rows).to_csv(OUT/"comparison.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(summaries,indent=2)+"\n")


if __name__=="__main__":
    main()
