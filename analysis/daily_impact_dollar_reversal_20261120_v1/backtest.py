#!/usr/bin/env python3
"""Preregistered thin-liquidity impact reversal; causal 1m OHLCV test."""
import hashlib,json
from pathlib import Path
import numpy as np,pandas as pd
OUT=Path("analysis/daily_impact_dollar_reversal_20261120_v1")
OUT.mkdir(parents=True,exist_ok=True)
START=pd.Timestamp("2025-01-01",tz="Asia/Kolkata").tz_convert("UTC")
END=pd.Timestamp("2026-11-01",tz="Asia/Kolkata").tz_convert("UTC")
def load(symbol):
    files=sorted((Path("data/delta_india")/symbol/"1m").glob("20??-??.csv.gz"))
    if not files:raise RuntimeError("MISSING_ARCHIVE "+symbol)
    chunks=[];meta=[]
    for f in files:
        a=pd.read_csv(f,compression="gzip")
        needed={"time","open","high","low","close","volume"}
        if not needed.issubset(a.columns):raise RuntimeError("MISSING_VOLUME_OR_OHLC "+str(f))
        meta.append(dict(file=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),rows=len(a)))
        chunks.append(a[list(sorted(needed))])
    x=pd.concat(chunks,ignore_index=True)
    x["time"]=pd.to_datetime(pd.to_numeric(x.time),unit="s",utc=True)
    x=x.sort_values("time").set_index("time")
    if x.index.has_duplicates or x.isna().any().any() or (x[["open","high","low","close"]]<=0).any().any() or (x.volume<0).any() or (x.high<x[["open","close","low"]].max(axis=1)).any() or (x.low>x[["open","close","high"]].min(axis=1)).any():raise RuntimeError("INVALID_SOURCE "+symbol)
    if x.volume.sum()<=0:raise RuntimeError("EMPTY_VOLUME "+symbol)
    return x,meta
def run(symbol,stress=False):
    x,meta=load(symbol)
    h=x.resample("1h").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    count=x.close.resample("1h").count()
    h["complete"]=count.eq(60)
    h["turnover"]=(x.close*x.volume).resample("1h").sum()
    h["ret"]=np.log(h.close/h.open)
    h["impact"]=h.ret.abs()/h.turnover.replace(0,np.nan)
    h["q95"]=h.impact.shift(1).rolling(168,min_periods=168).quantile(.95)
    h["medturn"]=h.turnover.shift(1).rolling(168,min_periods=168).median()
    # Rolling thresholds cannot cross missing/incomplete hours.
    h["history_ok"]=h.complete.shift(1).rolling(168,min_periods=168).sum().eq(168)
    signals=h.loc[h.complete & h.history_ok & (h.impact>h.q95)&(h.ret.abs()>=.003)&(h.turnover<h.medturn)]
    nav=1.0;last_exit=START;trades=[];events=[]
    for ts,s in signals.iterrows():
        entry_time=ts+pd.Timedelta(hours=1)
        if entry_time<START or entry_time>=END or entry_time<=last_exit:continue
        minutes=pd.date_range(entry_time,periods=180,freq="min")
        if minutes[-1]>=x.index.max() or not x.index.isin(minutes).sum()==180:
            events.append(dict(time=str(entry_time),status="DATA_GAP_OR_INCOMPLETE_EXIT_WINDOW"));continue
        f=x.loc[minutes]
        direction=-1 if s.ret>0 else 1
        slip=(5.0/float(f.open.iloc[0]) if symbol=="BTCUSD" else .0002)*(2 if stress else 1)
        entry=float(f.open.iloc[0])*(1+direction*slip)
        stop=entry*(1-direction*.006);target=entry*(1+direction*.01)
        exit_time=minutes[-1];raw_exit=float(f.close.iloc[-1]);reason="timeout"
        for t,b in f.iterrows():
            if (b.low<=stop if direction==1 else b.high>=stop):
                raw_exit=stop;exit_time=t;reason="stop_first";break
            if (b.high>=target if direction==1 else b.low<=target):
                raw_exit=target;exit_time=t;reason="target";break
        exit_fill=raw_exit*(1-direction*slip)
        gross=.1*direction*(exit_fill/entry-1)
        fee=.1*.0005*1.18*(1+exit_fill/entry)
        pnl=nav*(gross-fee)
        before=nav;nav+=pnl;last_exit=exit_time
        trades.append(dict(market=symbol,stress=stress,signal_utc=str(ts),entry_utc=str(entry_time),exit_utc=str(exit_time),direction=direction,entry_fill=entry,exit_fill=exit_fill,exit_reason=reason,nav_before=before,net_pnl=pnl,nav_after=nav,fee_nav=before*fee,slippage_fraction_per_side=slip))
    t=pd.DataFrame(trades)
    # End-of-day NAV is marked from any open trade using the latest minute close;
    # current implementation realizes trade PnL at exit and does NOT mark open positions.
    # Fail closed rather than report unmarked daily NAV.
    if len(t):t.to_csv(OUT/(symbol+("_stress" if stress else "")+"_trades.csv"),index=False)
    else:pd.DataFrame(columns=["entry_utc","exit_utc","net_pnl"]).to_csv(OUT/(symbol+("_stress" if stress else "")+"_trades.csv"),index=False)
    (OUT/(symbol+("_stress" if stress else "")+"_gaps.json")).write_text(json.dumps(events,indent=2))
    return dict(market=symbol,stress=stress,trades=len(t),net_nav_unmarked=nav,source=meta,signal_count=len(signals),data_gap_signals=len(events),status="INCONCLUSIVE_UNMARKED_DAILY_NAV_AND_FUNDING")
def main():
    out=[]
    for symbol in ["BTCUSD","ETHUSD"]:
        for stress in [False,True]:out.append(run(symbol,stress))
    (OUT/"summary.json").write_text(json.dumps(out,indent=2))
    print(json.dumps([{k:v for k,v in o.items() if k!="source"} for o in out],indent=2))
    print("INCONCLUSIVE: daily mark-to-market, funding, executable spread and lot/tick validation still required")
if __name__=="__main__":main()
