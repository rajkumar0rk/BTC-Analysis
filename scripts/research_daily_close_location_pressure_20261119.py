#!/usr/bin/env python3
"""Pre-registered BTC-first close-location volume-pressure feasibility study."""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
OUT=Path("analysis/daily_close_location_pressure_20261119")
OUT.mkdir(parents=True,exist_ok=True)
def load(symbol):
    files=sorted((Path("data/delta_india")/symbol/"1m").glob("20??-??.csv.gz"))
    if not files: raise RuntimeError("missing authentic 1m "+symbol)
    frames=[]; provenance=[]
    for p in files:
        h=hashlib.sha256(p.read_bytes()).hexdigest()
        z=pd.read_csv(p,compression="gzip")
        if not {"time","open","high","low","close","volume"}.issubset(z.columns):raise RuntimeError("missing fields "+str(p))
        z=z[["time","open","high","low","close","volume"]]
        z["time"]=pd.to_datetime(pd.to_numeric(z.time),unit="s",utc=True)
        frames.append(z)
        provenance.append(dict(file=str(p),sha256=h,rows=len(z)))
    x=pd.concat(frames,ignore_index=True).sort_values("time").set_index("time")
    if x.index.has_duplicates:raise RuntimeError("duplicate timestamps")
    if (x.high<x.low).any() or (x.volume<0).any() or x.isna().any().any():raise RuntimeError("bad OHLCV")
    return x,provenance
def run(symbol,cost):
    x,prov=load(symbol)
    x=x.tz_convert("Asia/Kolkata")
    daily=[]; trades=[]
    first=max(pd.Timestamp("2025-01-01",tz="Asia/Kolkata"),x.index.min().normalize())
    last=min(pd.Timestamp("2026-11-17",tz="Asia/Kolkata"),x.index.max().normalize())
    for day in pd.date_range(first,last,freq="D"):
        entry=day+pd.Timedelta(hours=9)
        prior=pd.date_range(entry-pd.Timedelta(minutes=60),periods=60,freq="min")
        future=pd.date_range(entry,periods=121,freq="min")
        status="no_trade";net=0.; gross=0.; direction=0;reason="below_threshold"
        if not prior.isin(x.index).all() or not future.isin(x.index).all():
            status="data_gap";reason="missing_complete_window"
        else:
            s=x.loc[prior]
            denom=s.high-s.low
            clv=np.where(denom.to_numpy()>0,(2*s.close-s.high-s.low).to_numpy()/np.maximum(denom.to_numpy(),1e-12),0.)
            volume=s.volume.to_numpy()
            pressure=float(np.dot(clv,volume)/max(volume.sum(),1e-12))
            direction=1 if pressure>=.65 else (-1 if pressure<=-.65 else 0)
            if direction:
                f=x.loc[future]
                price=float(f.open.iloc[0])
                stop=price*(1-direction*.005)
                target=price*(1+direction*.0075)
                exitprice=float(f.close.iloc[-1]);reason="time"
                for _,c in f.iloc[:120].iterrows():
                    stop_hit=(c.low<=stop if direction==1 else c.high>=stop)
                    tp_hit=(c.high>=target if direction==1 else c.low<=target)
                    if stop_hit:exitprice=stop;reason="stop";break
                    if tp_hit:exitprice=target;reason="target";break
                gross=direction*(exitprice/price-1)*.25*100
                net=gross-cost*.25*100
                status="profit" if net>0 else "loss"
                trades.append(dict(market=symbol,date=str(day.date()),direction=direction,pressure=pressure,gross_pct=gross,net_pct=net,exit_reason=reason))
        daily.append(dict(market=symbol,date=str(day.date()),year=day.year,month=str(day.strftime("%Y-%m")),status=status,net_pct=net,gross_pct=gross,direction=direction,reason=reason))
    return pd.DataFrame(daily),pd.DataFrame(trades),prov
def summarize(d,t,market,cost):
    result=[]
    for yr,g in d.groupby("year"):
        v=g.net_pct.to_numpy()
        tv=t[t.date.str[:4]==str(yr)] if len(t) else t
        pos=tv.net_pct[tv.net_pct>0].sum() if len(tv) else 0
        neg=-tv.net_pct[tv.net_pct<0].sum() if len(tv) else 0
        curve=np.r_[0,v.cumsum()]
        result.append(dict(market=market,cost_roundtrip_pct=cost*100,year=int(yr),days=len(g),profitable_days=int((g.status=="profit").sum()),losing_days=int((g.status=="loss").sum()),no_trade_days=int((g.status=="no_trade").sum()),data_gap_days=int((g.status=="data_gap").sum()),trades=len(tv),net_pct=float(v.sum()),mean_day_pct=float(v.mean()),median_day_pct=float(np.median(v)),worst_day_pct=float(v.min()),profit_factor=float(pos/neg) if neg else None,max_drawdown_pct=float((np.maximum.accumulate(curve)-curve).max())))
    return result
def main():
    ds=[];ts=[];sums=[];qualities=[]
    for sym in ["BTCUSD","ETHUSD"]:
        for cost in [.00158,.00238]:
            d,t,p=run(sym,cost)
            d["scenario"]="base" if cost==.00158 else "stress"
            t["scenario"]=d.scenario.iloc[0] if len(t) else ("base" if cost==.00158 else "stress")
            ds.append(d);ts.append(t);sums+=summarize(d,t,sym,cost)
            if cost==.00158:qualities+= [dict(market=sym,files=p)]
    daily=pd.concat(ds,ignore_index=True);trades=pd.concat(ts,ignore_index=True)
    daily.to_csv(OUT/"daily.csv",index=False);trades.to_csv(OUT/"trades.csv",index=False)
    pd.DataFrame(sums).to_csv(OUT/"summary.csv",index=False)
    m=daily.groupby(["market","scenario","month"],as_index=False).agg(net_pct=("net_pct","sum"),profit_days=("status",lambda s:(s=="profit").sum()),loss_days=("status",lambda s:(s=="loss").sum()),no_trade_days=("status",lambda s:(s=="no_trade").sum()),data_gap_days=("status",lambda s:(s=="data_gap").sum()))
    m.to_csv(OUT/"monthly.csv",index=False)
    (OUT/"provenance.json").write_text(json.dumps(qualities,indent=2))
    print("FROZEN_BTC_FIRST_SUMMARY");print(pd.DataFrame(sums).to_string(index=False))
    print("FROZEN_MONTHLY");print(m.to_string(index=False))
    print("CAUTION: OHLCV signed pressure proxy, no L1 execution, funding settlements or true maker fills; 2026 research exposed.")
if __name__=="__main__":main()
