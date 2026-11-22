#!/usr/bin/env python3
"""Historical 1H BTCUSD EMA20 Touch versus ST-flip entry comparisons; no live actions."""
import importlib.util
import json
from pathlib import Path
import numpy as np
import pandas as pd

REPLAY=Path("scripts/backtest_st_ema20_large_percent_locks.py")
TOUCH_BASE=Path("analysis/st_ema20_large_percent_locks_1h")
OUT=Path("analysis/st_ema20_touch_vs_flip_1h")
PATHS=("open_high_low_close","open_low_high_close")
LADDERS={
  "0.75%":"S03_only_0p75",
  "1-2-5%":"L05_1_2_5",
  "2-3-5%":"L10_2_3_5",
  "5%":"S09_only_5",
}
FILTERS={
  "unfiltered":(None,None,None,None),
  "touch_balanced":(None,2.5,None,1.25),
  "volume_0.5_to_2.5_ATR_max_1.25":(.5,2.5,None,1.25),
  "volume_min_1.25_ATR_max_1.75":(1.25,None,None,1.75),
}
MODES=("touch","flip_next_open","flip_breakout")


def import_replay():
    spec=importlib.util.spec_from_file_location("btc_1h_replay",REPLAY)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalized_features(h):
    h=h.copy()
    h["vol_ratio"]=h.volume/h.volume.shift(1).rolling(20,min_periods=20).mean().replace(0,np.nan)
    h["atr_pct"]=100.0*h.atr/h.close
    return h


def flip_entries(m,h,at_open):
    op=m.open.to_numpy(float)
    hi=m.high.to_numpy(float)
    lo=m.low.to_numpy(float)
    sides=h.side.to_numpy(int)
    out=[]
    for i in range(21,len(h)-1):
        side=int(sides[i])
        if not side or side==sides[i-1]:continue
        start=(i+1)*60
        if start>=len(op):continue
        signal=str(h.index[i])
        if at_open:
            entry_j=start
            fill_mid=float(op[start])
        else:
            trigger=float(h.high.iloc[i]+.5 if side==1 else h.low.iloc[i]-.5)
            entry_j=None
            fill_mid=None
            for j in range(start,min(start+60,len(op))):
                if (hi[j]>=trigger if side==1 else lo[j]<=trigger):
                    entry_j=j
                    fill_mid=(max(op[j],trigger) if side==1 else min(op[j],trigger))
                    break
            if entry_j is None:continue
        out.append(dict(
            entry_j=entry_j,entry=fill_mid+side*5.0,
            side=side,kind="flip_next_open" if at_open else "flip_breakout",
            cycle=i,signal=signal))
    assert len(set(v["cycle"] for v in out))==len(out),"Duplicate ST cycle"
    return out


def entry_filter(h,events,choice):
    config=FILTERS[choice]
    if choice=="unfiltered":return list(events)
    vmin,vmax,amin,amax=config
    r=[]
    for ev in events:
        ts=pd.Timestamp(ev["signal"])
        if ts not in h.index:raise AssertionError("1H signal not in history")
        bar=h.loc[ts]
        vol=float(bar.vol_ratio)
        atr=float(bar.atr_pct)
        if not np.isfinite(vol) or not np.isfinite(atr):continue
        if vmin is not None and vol<vmin:continue
        if vmax is not None and vol>vmax:continue
        if amin is not None and atr<amin:continue
        if amax is not None and atr>amax:continue
        r.append(ev)
    return r


def touch_ledger(h,ladder,path):
    file=TOUCH_BASE/f"touch_{ladder}_{path}_trades.csv"
    t=pd.read_csv(file)
    assert len(t)>0 and t.signal_utc.notna().all()
    return t


def touch_filter_ledger(h,t,choice):
    if choice=="unfiltered":return t.copy()
    choice_values=FILTERS[choice]
    signals=pd.to_datetime(t.signal_utc,utc=True)
    ref=h.reindex(pd.DatetimeIndex(signals))
    assert len(ref)==len(t)
    vols=ref.vol_ratio.to_numpy(float)
    atrs=ref.atr_pct.to_numpy(float)
    filt=np.isfinite(vols)&np.isfinite(atrs)
    vmin,vmax,amin,amax=choice_values
    if vmin is not None:filt &= vols>=vmin
    if vmax is not None:filt &= vols<=vmax
    if amin is not None:filt &= atrs>=amin
    if amax is not None:filt &= atrs<=amax
    return t.loc[filt].copy()


def calculate(t,mode,choice,ladder,path):
    net=t.net_usd.to_numpy(float)
    n=len(net)
    t=t.copy()
    if n:
        t["exit_ts"]=pd.to_datetime(t.exit_utc,utc=True)
        t=t.sort_values("exit_ts")
        net=t.net_usd.to_numpy(float)
        eq=np.r_[100.,100.+np.cumsum(net)]
        peaks=np.maximum.accumulate(eq)
        draw=np.max((peaks-eq)/np.maximum(peaks,1e-8)*100.)
        profits=net[net>0].sum()
        losses=-net[net<0].sum()
        pf=(profits/losses if losses else None)
        t["month"]=(t.exit_ts+pd.Timedelta(hours=5,minutes=30)).dt.tz_localize(None).dt.to_period("M").astype(str)
        bymonth=t.groupby("month").net_usd.agg(["sum","count"]).to_dict("index")
    else:
        draw=0.;pf=None;bymonth={}
    year_months=list(pd.period_range("2025-01","2026-10",freq="M").astype(str))
    all_months=year_months+["2026-11"]
    monthly=[]
    for mo in all_months:
        a=bymonth.get(mo,{"sum":0.,"count":0})
        monthly.append(dict(
            mode=mode,filter=choice,ladder=ladder,path=path,
            month=mo,complete_month=mo<="2026-10",
            trades=int(a["count"]),net_usd=round(float(a["sum"]),6)))
    full=[x for x in monthly if x["complete_month"]]
    winmonths=sum(x["net_usd"]>0 for x in full)
    return dict(mode=mode,filter=choice,ladder=ladder,path=path,
        trades=n,wins=int((net>0).sum()),losses=int((net<0).sum()),
        win_pct=round(100*(net>0).mean(),3) if n else 0.,
        net_usd=round(float(net.sum()),4),fees_usd=round(float(t.fees_usd.sum()),4),
        profit_factor=round(float(pf),4) if pf is not None else None,
        max_realized_dd_pct=round(float(draw),3),
        full_profitable_months=winmonths,
        year_2025_net=round(sum(x["net_usd"] for x in full if x["month"].startswith("2025")),4),
        year_2026_jan_oct_net=round(sum(x["net_usd"] for x in full if x["month"].startswith("2026")),4),
        lock_exits=int((t.exit_reason=="profit_lock").sum()),
        flip_exits=int((t.exit_reason=="supertrend_flip").sum())), monthly


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    e=import_replay()
    e.smoke_test()
    m,h,nfiles=e.load()
    h=normalized_features(e.features(h))
    touch_entries=e.entry_candidates(m,h,"touch")
    flip_open=flip_entries(m,h,True)
    flip_breakout=flip_entries(m,h,False)
    entries={"flip_next_open":flip_open,"flip_breakout":flip_breakout}
    assert len(touch_entries)==253, f"Original Touch entry candidates drift: {len(touch_entries)}"
    comparison=pd.read_csv(TOUCH_BASE/"comparison.csv")
    allsummary=[];allmonth=[]
    for mode in MODES:
        for label,ladder in LADDERS.items():
            for path in PATHS:
                if mode=="touch":
                    t0=touch_ledger(h,ladder,path)
                    ref=comparison.loc[
                        (comparison.entry_mode=="touch")&
                        (comparison.ladder==ladder)&
                        (comparison.intraminute_path==path)]
                    assert len(ref)==1 and abs(float(ref.net_usd.iloc[0])-t0.net_usd.sum())<.002
                else:
                    t0,_=e.replay(m,h,entries[mode],mode,ladder,path)
                    if not t0.empty:
                        t0.to_csv(OUT/f"{mode}_{ladder}_{path}_trades.csv",index=False)
                for f in FILTERS:
                    if mode=="touch":
                        t=touch_filter_ledger(h,t0,f)
                        # Strict fixed filter reproduces independently verified 212 Touch trades.
                        if f=="touch_balanced" and label=="1-2-5%":
                            assert len(t)==212,f"Touch filtered baseline drift: {len(t)}"
                            assert 10.81<=t.net_usd.sum()<=12.02
                    else:
                        allowed=entry_filter(h,entries[mode],f)
                        allowed_signals=set(ev["signal"] for ev in allowed)
                        t=t0.loc[t0.signal_utc.isin(allowed_signals)].copy()
                        assert t.signal_utc.nunique()==len(t),"Multiple trades per flip"
                    summ,months=calculate(t,mode,f,label,path)
                    allsummary.append(summ)
                    allmonth+=months
                    if f=="touch_balanced" and label=="1-2-5%" and mode=="touch":
                        print("Verified previously published Touch filtered baseline",summ,flush=True)
                print(f"{mode}/{label}/{path} completed",flush=True)
    r=pd.DataFrame(allsummary)
    mm=pd.DataFrame(allmonth)
    assert len(r)==len(MODES)*len(LADDERS)*len(PATHS)*len(FILTERS)
    assert len(mm)==len(r)*23
    r.to_csv(OUT/"comparison.csv",index=False)
    mm.to_csv(OUT/"monthly_ist.csv",index=False)
    cols=["mode","filter","ladder"]
    pair=r.groupby(cols).agg(
        min_trades=("trades","min"),
        worst_net=("net_usd","min"),
        best_net=("net_usd","max"),
        min_win_pct=("win_pct","min"),
        min_profit_months=("full_profitable_months","min"),
        max_profit_months=("full_profitable_months","max"),
        worst_2025=("year_2025_net","min"),
        worst_2026=("year_2026_jan_oct_net","min"),
        max_realized_dd_pct=("max_realized_dd_pct","max"),
        min_profit_factor=("profit_factor","min")).reset_index()
    pair.sort_values(["worst_net","min_profit_months"],ascending=[False,False]).to_csv(OUT/"paired_comparison.csv",index=False)
    note={
       "test_name":"1H ST EMA20 Touch vs ST flip next open and flip breakout",
       "source":"Delta Exchange India BTCUSD perpetual 1m OHLCV",
       "source_month_files":nfiles,
       "first_utc":str(m.index[0]),"last_utc":str(m.index[-1]),
       "touch_entry_candidates":len(touch_entries),
       "flip_next_open_candidates":len(flip_open),
       "flip_breakout_candidates":len(flip_breakout),
       "filter_levels":FILTERS,
       "exit_ladders":{name:list(e.LADDERS[id]) for name,id in LADDERS.items()},
       "fee_plus_gst_per_side":e.FEE,
       "adverse_slippage_points_per_side":e.SLIP,
       "qty_btc":e.QTY,
       "no_initial_stop":True,
       "theoretical_price_paths":PATHS,
       "complete_months":22,
       "known_limitations":["historical parameter selections were explored on known data",
                            "minute OHLC does not determine tick path",
                            "no live-order latency, funding, margin, liquidation or spreads beyond 5 point slippage each side",
                            "realized drawdown only; floating account drawdown excluded",
                            "Touch signal and Flip signal time differs by design",
                            "One candidate per ST cycle, rejected candidate never replaced by a later candidate"]}
    (OUT/"quality.json").write_text(json.dumps(note,indent=2)+"\n")
    print("RESULT_SUMMARY",pair.loc[(pair["filter"]=="touch_balanced") & (pair.ladder=="1-2-5%")].to_json(orient="records"),flush=True)
    print("ALL_GRID",len(r),"rows",flush=True)


if __name__=="__main__":
    main()
