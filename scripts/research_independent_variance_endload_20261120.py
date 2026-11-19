#!/usr/bin/env python3
"""Pre-registered intrahour variance end-loading; BTC first, ETH frozen secondary."""
from pathlib import Path
import hashlib,json,math
import numpy as np
import pandas as pd
ROOT=Path("data/delta_india"); OUT=Path("analysis/independent_variance_endload_20261120");OUT.mkdir(parents=True,exist_ok=True)
FEE=.0005*1.18
def load(sym):
    fs=sorted((ROOT/sym/"1m").glob("20??-??.csv.gz"))
    if not fs:raise RuntimeError("MISSING_AUTHENTIC_1M_"+sym)
    hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in fs}
    p=[]
    for f in fs:
        x=pd.read_csv(f,compression="gzip",usecols=["time","open","high","low","close"])
        x["time"]=pd.to_datetime(x.time.astype("int64"),unit="s",utc=True);p.append(x)
    x=pd.concat(p,ignore_index=True).set_index("time").sort_index()
    if x.index.has_duplicates:raise RuntimeError("DUPLICATE_TIMESTAMPS")
    if (x.high<x[["open","low","close"]].max(axis=1)).any() or (x.low>x[["open","high","close"]].min(axis=1)).any():raise RuntimeError("BAD_OHLC")
    return x,hashes
def signals(x):
    # Group complete clock-hours; first minute's return uses its own open, never previous-hour close.
    h=x.index.floor("h"); pos=x.index.minute
    r=np.log(x.close.to_numpy()/np.r_[x.open.iloc[0],x.close.to_numpy()[:-1]])
    z=pd.DataFrame({"hour":h,"minute":pos,"rv":r*r,"close":x.close.to_numpy(),"open":x.open.to_numpy()},index=x.index)
    agg=z.groupby("hour").agg(count=("rv","size"),first=("open","first"),last=("close","last"))
    early=z[z.minute<45].groupby("hour").rv.sum()
    late=z[z.minute>=45].groupby("hour").rv.sum()
    startlate=z[z.minute==45].groupby("hour").open.first()
    agg["early"]=early;agg["late"]=late;agg["startlate"]=startlate
    agg=agg[(agg["count"]==60)&(agg.early>0)&(agg.late>4*agg.early)&((agg["last"]/agg.startlate-1).abs()>.003)]
    agg["side"]=np.sign(agg["last"]/agg.startlate-1).astype(int)
    # Signal only after hour complete. Position at next exact minute timestamp.
    return {t+pd.Timedelta(hours=1):int(s) for t,s in agg.side.items()}
def run(sym,reverse=False,stress=False):
    x,hashes=load(sym); sig=signals(x)
    ix=x.index; o=x.open.to_numpy(); hi=x.high.to_numpy();lo=x.low.to_numpy();cl=x.close.to_numpy()
    nav=10000.;peak=nav;dd=0.;pos=None;tr=[];equity=[];last_month=None
    sliprate=.0004 if stress else .0002
    missing=int(((ix[1:]-ix[:-1])!=pd.Timedelta(minutes=1)).sum())
    for i,t in enumerate(ix):
        # Never carry a position through missing price history without accounting.
        if i and t-ix[i-1]!=pd.Timedelta(minutes=1) and pos is not None:
            px=cl[i-1]-pos["side"]*max(5 if sym=="BTCUSD" else 0,cl[i-1]*sliprate)
            nav+=pos["side"]*pos["qty"]*(px-pos["entry"])-pos["qty"]*px*FEE
            tr.append(dict(entry_utc=str(pos["time"]),exit_utc=str(ix[i-1]),side=pos["side"],entry=pos["entry"],exit=px,qty=pos["qty"],net_pnl=nav-pos["nav_before"],net_R=(nav-pos["nav_before"])/pos["riskusd"],reason="gap_forced_exit"))
            pos=None
        if pos is not None:
            side=pos["side"]; stop=pos["stop"];exitpx=None;reason=None
            if (side==1 and lo[i]<=stop) or (side==-1 and hi[i]>=stop):
                exitpx=stop;reason="stop"
            elif i-pos["entry_i"]>=2880:
                exitpx=cl[i];reason="timeout"
            if exitpx is not None:
                exitpx-=side*max(5 if sym=="BTCUSD" else 0,exitpx*sliprate)
                nav+=side*pos["qty"]*(exitpx-pos["entry"])-pos["qty"]*exitpx*FEE
                tr.append(dict(entry_utc=str(pos["time"]),exit_utc=str(t),side=side,entry=pos["entry"],exit=exitpx,qty=pos["qty"],net_pnl=nav-pos["nav_before"],net_R=(nav-pos["nav_before"])/pos["riskusd"],reason=reason))
                pos=None
            else:
                # stop-first before updating trailing with this minute's favorable extreme
                favorable=hi[i] if side==1 else lo[i]
                pos["best"]=max(pos["best"],favorable) if side==1 else min(pos["best"],favorable)
                if side*(pos["best"]-pos["entry"])>=4*pos["riskpx"]:
                    newstop=pos["best"]-side*2*pos["riskpx"]
                    pos["stop"]=max(pos["stop"],newstop) if side==1 else min(pos["stop"],newstop)
        if pos is None and t in sig and i and t-ix[i-1]==pd.Timedelta(minutes=1):
            side=sig[t]*(-1 if reverse else 1)
            entry=o[i]+side*max(5 if sym=="BTCUSD" else 0,o[i]*sliprate)
            riskpx=.0065*entry
            qty=min(nav*.0025/riskpx,nav*2/entry)
            if qty>0 and nav>0:
                before=nav;nav-=qty*entry*FEE
                pos=dict(side=side,entry=entry,stop=entry-side*riskpx,best=entry,qty=qty,riskpx=riskpx,riskusd=qty*riskpx,time=t,entry_i=i,nav_before=before)
        mtm=nav if pos is None else nav+pos["side"]*pos["qty"]*(cl[i]-pos["entry"])-pos["qty"]*cl[i]*FEE
        peak=max(peak,mtm);dd=max(dd,1-mtm/peak) if peak>0 else 1
        month=t.tz_convert("Asia/Kolkata").strftime("%Y-%m")
        if month!=last_month:
            equity.append(dict(month=month,time_utc=str(t),nav=mtm,kind="start"));last_month=month
        # overwrite month-end snapshot, preserve actual final observed NAV
        if len(equity)>0 and equity[-1]["month"]==month:
            if equity[-1]["kind"]=="start":equity.append(dict(month=month,time_utc=str(t),nav=mtm,kind="end"))
            else:equity[-1].update(time_utc=str(t),nav=mtm)
    if pos is not None:
        px=cl[-1]-pos["side"]*max(5 if sym=="BTCUSD" else 0,cl[-1]*sliprate)
        nav+=pos["side"]*pos["qty"]*(px-pos["entry"])-pos["qty"]*px*FEE
        tr.append(dict(entry_utc=str(pos["time"]),exit_utc=str(ix[-1]),side=pos["side"],entry=pos["entry"],exit=px,qty=pos["qty"],net_pnl=nav-pos["nav_before"],net_R=(nav-pos["nav_before"])/pos["riskusd"],reason="dataset_end"))
    trades=pd.DataFrame(tr,columns=["entry_utc","exit_utc","side","entry","exit","qty","net_pnl","net_R","reason"])
    months=[]
    starts={}
    for row in equity:
        m=row["month"]
        if row["kind"]=="start":starts[m]=row["nav"]
        else:
            sub=trades[pd.to_datetime(trades.exit_utc,utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m").eq(m)] if len(trades) else trades
            win=sub[sub.net_pnl>0].net_pnl.sum();loss=-sub[sub.net_pnl<0].net_pnl.sum()
            months.append(dict(month=m,nav_start=starts.get(m),nav_end=row["nav"],return_pct=100*(row["nav"]/starts[m]-1) if starts.get(m) else None,pf=win/loss if loss>0 else ("Infinity" if win>0 else None),closed=len(sub),wins=int((sub.net_pnl>0).sum()),losses=int((sub.net_pnl<0).sum())))
    pnl=trades.net_pnl.to_numpy();wins=pnl[pnl>0];losses=pnl[pnl<0]
    result=dict(symbol=sym,reverse=reverse,stress=stress,source_sha256=hashes,missing_minute_transitions=missing,first=str(ix[0]),last=str(ix[-1]),closed=len(trades),nav_end=nav,max_mtm_drawdown=dd,pf=float(wins.sum()/-losses.sum()) if len(losses) else None,win_rate=float(len(wins)/len(pnl)) if len(pnl) else None,mean_win_loss=float(wins.mean()/-losses.mean()) if len(wins) and len(losses) else None,largest_R=float(trades.net_R.max()) if len(trades) else None,warning="Funding settlement unavailable; no L2 spread or fill confirmation; incomplete first/last IST months require caution")
    tag=sym+("_reverse" if reverse else "")+("_stress" if stress else "")
    trades.to_csv(OUT/(tag+"_trades.csv"),index=False)
    pd.DataFrame(months).to_csv(OUT/(tag+"_monthly.csv"),index=False)
    (OUT/(tag+"_quality.json")).write_text(json.dumps(result,indent=2))
    print(tag,json.dumps({k:v for k,v in result.items() if k!="source_sha256"}),flush=True)
if __name__=="__main__":
    for s in ("BTCUSD","ETHUSD"):
        for rev,stress in ((False,False),(True,False),(False,True)):run(s,rev,stress)
