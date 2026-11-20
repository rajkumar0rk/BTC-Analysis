#!/usr/bin/env python3
"""Preregistered BTC-first extrema sequencing hypothesis; no parameter tuning."""
from pathlib import Path
import hashlib, json
import numpy as np
import pandas as pd
ROOT=Path("data/delta_india")
OUT=Path("analysis/independent_extrema_order_20261120")
OUT.mkdir(parents=True,exist_ok=True)
FEE=.0005*1.18
def load(symbol):
    fs=sorted((ROOT/symbol/"1m").glob("20??-??.csv.gz"))
    if not fs: raise RuntimeError("AUTHENTIC_DATA_UNAVAILABLE_"+symbol)
    hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in fs}
    parts=[]
    for f in fs:
        x=pd.read_csv(f,compression="gzip")
        if not {"time","open","high","low","close","volume"}.issubset(x.columns):
            raise RuntimeError("MISSING_REQUIRED_OHLCV_COLUMNS_"+str(f))
        x=x[["time","open","high","low","close","volume"]]
        x["time"]=pd.to_datetime(x.time.astype("int64"),unit="s",utc=True)
        parts.append(x)
    x=pd.concat(parts,ignore_index=True).set_index("time").sort_index()
    if x.index.has_duplicates: raise RuntimeError("DUPLICATE_BARS")
    if ((x.high<x[["open","close","low"]].max(axis=1))|(x.low>x[["open","close","high"]].min(axis=1))|(x.volume<0)).any():
        raise RuntimeError("BAD_OHLCV")
    return x,hashes
def signals(x):
    # Intrahour order of actual observed minute extrema, not unordered hourly OHLC.
    # First extreme must precede second by >=20 minutes. Signal at CLOSED hour only.
    h=x.index.floor("h")
    a=x.groupby(h).agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),n=("close","size"))
    minute_count=x.groupby(h).apply(lambda z:z.index.minute.nunique())
    a=a[(a.n==60)&(minute_count==60)]
    rng=a.high-a.low
    prior=rng.shift(1).rolling(168,min_periods=168).median()
    continuous=a.index.to_series().diff().eq(pd.Timedelta(hours=1)).rolling(168,min_periods=168).sum().eq(168)
    eligible=continuous&(rng>1.5*prior)&(rng/a.open>.002)
    out={}
    for t in a.index[eligible]:
        z=x.loc[t:t+pd.Timedelta(minutes=59)]
        low_time=z.low.idxmin();high_time=z.high.idxmax()
        if high_time-low_time>=pd.Timedelta(minutes=20) and (a.loc[t,"close"]-a.loc[t,"low"])/rng.loc[t]>=.8:
            out[t+pd.Timedelta(hours=1)]=1
        elif low_time-high_time>=pd.Timedelta(minutes=20) and (a.loc[t,"high"]-a.loc[t,"close"])/rng.loc[t]>=.8:
            out[t+pd.Timedelta(hours=1)]=-1
    return out
def run(symbol,reverse=False,stress=False):
    x,hashes=load(symbol)
    sig=signals(x)
    idx=x.index; o=x.open.to_numpy();hi=x.high.to_numpy();lo=x.low.to_numpy();cl=x.close.to_numpy()
    nav=10000.; peak=nav;maxdd=0.;pos=None;trades=[];navrows=[]
    sliprate=.0004 if stress else .0002
    gaps=int(((idx[1:]-idx[:-1])!=pd.Timedelta(minutes=1)).sum())
    def adverse(price,side):
        return price+side*max(5. if symbol=="BTCUSD" else 0.,price*sliprate)
    for i,t in enumerate(idx):
        contiguous=i>0 and t-idx[i-1]==pd.Timedelta(minutes=1)
        closed_this_bar=False
        if pos is not None:
            side=pos["side"]; reason=None
            if not contiguous:
                exitprice=adverse(o[i],-side);reason="gap_next_observed_open"
            elif (side==1 and lo[i]<=pos["stop"]) or (side==-1 and hi[i]>=pos["stop"]):
                # Stop-first, even if same minute could improve trailing.
                exitprice=adverse(min(pos["stop"],o[i]) if side==1 else max(pos["stop"],o[i]),-side);reason="stop_or_gap_through"
            elif (t-pos["entry_time"])>=pd.Timedelta(hours=48):
                exitprice=adverse(o[i],-side);reason="timeout_next_open"
            if reason:
                nav+=side*pos["qty"]*(exitprice-pos["entry"])-pos["qty"]*exitprice*FEE
                pnl=nav-pos["before"]
                trades.append(dict(entry_utc=str(pos["entry_time"]),exit_utc=str(t),side=side,entry=pos["entry"],exit=exitprice,qty=pos["qty"],risk_usd=pos["risk_usd"],net_pnl=pnl,net_R=pnl/pos["risk_usd"],reason=reason))
                pos=None
                closed_this_bar=True
            else:
                favorable=hi[i] if side==1 else lo[i]
                pos["best"]=max(pos["best"],favorable) if side==1 else min(pos["best"],favorable)
                if side*(pos["best"]-pos["entry"])>=4*pos["riskpx"]:
                    newstop=pos["best"]-side*2*pos["riskpx"]
                    pos["stop"]=max(pos["stop"],newstop) if side==1 else min(pos["stop"],newstop)
        # Never enter on a bar where we just closed another position.
        if pos is None and not closed_this_bar and contiguous and t in sig:
            side=sig[t]*(-1 if reverse else 1)
            entry=adverse(o[i],side);riskpx=.0065*entry
            qty=min(nav*.0025/riskpx,nav*2/entry)
            if qty>0 and nav>0:
                before=nav;nav-=qty*entry*FEE
                pos=dict(side=side,entry=entry,entry_time=t,qty=qty,riskpx=riskpx,risk_usd=qty*riskpx,stop=entry-side*riskpx,best=entry,before=before)
        mtm=nav if pos is None else nav+pos["side"]*pos["qty"]*(cl[i]-pos["entry"])-pos["qty"]*cl[i]*FEE
        peak=max(peak,mtm);maxdd=max(maxdd,1-mtm/peak)
        # Exact IST calendar month-end MTM from last observed minute.
        month=t.tz_convert("Asia/Kolkata").strftime("%Y-%m")
        if not navrows or navrows[-1]["month"]!=month:navrows.append(dict(month=month,first_observation=str(t),last_observation=str(t),nav_end=mtm))
        else:navrows[-1].update(last_observation=str(t),nav_end=mtm)
    if pos is not None:
        exitprice=adverse(cl[-1],-pos["side"])
        nav+=pos["side"]*pos["qty"]*(exitprice-pos["entry"])-pos["qty"]*exitprice*FEE
        pnl=nav-pos["before"]
        trades.append(dict(entry_utc=str(pos["entry_time"]),exit_utc=str(idx[-1]),side=pos["side"],entry=pos["entry"],exit=exitprice,qty=pos["qty"],risk_usd=pos["risk_usd"],net_pnl=pnl,net_R=pnl/pos["risk_usd"],reason="dataset_end"))
        navrows[-1]["nav_end"]=nav
    df=pd.DataFrame(trades,columns=["entry_utc","exit_utc","side","entry","exit","qty","risk_usd","net_pnl","net_R","reason"])
    months=[];prev_nav=10000.
    exit_month=pd.to_datetime(df.exit_utc,utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m") if len(df) else pd.Series([],dtype=str)
    for row in navrows:
        sub=df[exit_month==row["month"]] if len(df) else df
        wins=sub.loc[sub.net_pnl>0,"net_pnl"].sum();loss=-sub.loc[sub.net_pnl<0,"net_pnl"].sum()
        months.append(dict(month=row["month"],first_observation=row["first_observation"],last_observation=row["last_observation"],nav_start=prev_nav,nav_end=row["nav_end"],nav_return_pct=100*(row["nav_end"]/prev_nav-1),realized_pf=wins/loss if loss>0 else ("Infinity" if wins>0 else None),closed=len(sub),wins=int((sub.net_pnl>0).sum()),losses=int((sub.net_pnl<0).sum())))
        prev_nav=row["nav_end"]
    win=df[df.net_pnl>0];loss=df[df.net_pnl<0]
    quality=dict(symbol=symbol,reverse=reverse,stress=stress,source_hashes=hashes,first=str(idx[0]),last=str(idx[-1]),gaps=gaps,closed=len(df),net_return_pct=100*(nav/10000-1),max_mtm_dd=maxdd,win_rate=len(win)/len(df) if len(df) else None,pf=win.net_pnl.sum()/-loss.net_pnl.sum() if len(loss) else None,mean_win_loss=win.net_pnl.mean()/-loss.net_pnl.mean() if len(win) and len(loss) else None,largest_R=float(df.net_R.max()) if len(df) else None,without_biggest_winner_net_pnl=float(df.net_pnl.sum()-win.net_pnl.max()) if len(win) else float(df.net_pnl.sum()),funding="UNAVAILABLE_NOT_MODELED",spread="NO_HISTORICAL_L2",note="2025 partial start and 2026 October gap must be audited; 2026 research exposed")
    tag=symbol+("_reverse" if reverse else "")+("_stress" if stress else "")
    df.to_csv(OUT/(tag+"_trades.csv"),index=False)
    pd.DataFrame(months).to_csv(OUT/(tag+"_monthly.csv"),index=False)
    (OUT/(tag+"_quality.json")).write_text(json.dumps(quality,indent=2))
    print(tag,json.dumps({k:v for k,v in quality.items() if k!="source_hashes"}),flush=True)
if __name__=="__main__":
    for symbol in ("BTCUSD","ETHUSD"):
        for reverse,stress in ((False,False),(True,False),(False,True)):run(symbol,reverse,stress)
