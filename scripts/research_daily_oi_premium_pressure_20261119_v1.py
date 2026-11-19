#!/usr/bin/env python3
"""Pre-registered OI expansion + mark/last premium crowding: one fixed hypothesis, no grid."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path("data/delta_india")
OUT=Path("analysis/daily_oi_premium_pressure_20261119_v1")
COST=.00158
STRESS=.00198
NOTIONAL=1000.
def load(folder,cols):
    paths=sorted(folder.glob("20??-??.csv.gz"))
    if not paths: raise RuntimeError("Missing authentic source: "+str(folder))
    pieces=[]
    for p in paths:
        d=pd.read_csv(p,compression="gzip")
        if not set(cols+["time"]).issubset(d.columns):raise RuntimeError(f"columns missing {p}: {list(d.columns)}")
        d=d[["time"]+cols]
        d["time"]=pd.to_datetime(pd.to_numeric(d["time"]),unit="s",utc=True)
        pieces.append(d.set_index("time"))
    d=pd.concat(pieces).sort_index()
    if d.index.has_duplicates:raise RuntimeError("duplicate timestamps "+str(folder))
    return d.astype(float)
def calc(symbol):
    root=ROOT/symbol
    px=load(root/"1m",["open","high","low","close"])
    mark=load(root/"institutional/history/mark_1m",["close"])["close"]
    oi=load(root/"institutional/history/open_interest_5m",["close"])["close"]
    if not px.index.equals(mark.index):raise RuntimeError("mark and trade time mismatch")
    expected=pd.date_range(px.index[0],px.index[-1],freq="min")
    if len(px)!=len(expected) or not px.index.equals(expected):raise RuntimeError("1m gaps")
    if not oi.index.is_unique:raise RuntimeError("OI duplicate")
    # OI value and premium at t are only used after t closes; next 1m open is executable proxy.
    # Native OI is sampled each 5m; compare completed 5m snapshots 60m apart.
    oi_ch=oi/oi.shift(12)-1
    # completed 1m bar at t: mark/last premium. Price direction aligns with the crowded mark pressure.
    prem=(mark/px["close"]-1)
    records=[]
    days=pd.date_range(px.index[0].floor("D"),px.index[-1].floor("D"),freq="D")
    for day in days:
        start=day+pd.Timedelta(hours=1)
        end=day+pd.Timedelta(hours=22)
        candidates=oi_ch.loc[(oi_ch.index>=start)&(oi_ch.index<end)]
        entry_t=None;side=0
        for t,change in candidates.items():
            if not np.isfinite(change) or change<=.05:continue
            if t not in prem.index:continue
            pr=prem.loc[t]
            if not np.isfinite(pr) or abs(pr)<.0015:continue
            entry_t=t+pd.Timedelta(minutes=1)
            side=-1 if pr>0 else 1
            break
        if entry_t is None:
            records.append(dict(symbol=symbol,day=str(day.date()),status="NO_TRADE",net_usd=0,stress_net_usd=0,fee_gst_usd=0,slippage_usd=0))
            continue
        if entry_t not in px.index or entry_t+pd.Timedelta(minutes=59) not in px.index:
            records.append(dict(symbol=symbol,day=str(day.date()),status="DATA_GAP",net_usd=0,stress_net_usd=0,fee_gst_usd=0,slippage_usd=0))
            continue
        entry=float(px.loc[entry_t,"open"])
        exit_price=float(px.loc[entry_t+pd.Timedelta(minutes=59),"close"])
        exit_reason="TIME"
        for t,r in px.loc[entry_t:entry_t+pd.Timedelta(minutes=59)].iterrows():
            if side==1:
                stop=entry*.996;target=entry*1.006
                if r["low"]<=stop:exit_price=stop;exit_reason="STOP";break
                if r["high"]>=target:exit_price=target;exit_reason="TARGET";break
            else:
                stop=entry*1.004;target=entry*.994
                if r["high"]>=stop:exit_price=stop;exit_reason="STOP";break
                if r["low"]<=target:exit_price=target;exit_reason="TARGET";break
        gross=NOTIONAL*side*(exit_price/entry-1)
        net=gross-NOTIONAL*COST
        records.append(dict(symbol=symbol,day=str(day.date()),status="PROFIT" if net>0 else "LOSS",entry_utc=str(entry_t),direction=side,exit_reason=exit_reason,net_usd=net,stress_net_usd=gross-NOTIONAL*STRESS,fee_gst_usd=NOTIONAL*.00118,slippage_usd=NOTIONAL*.0004))
    return pd.DataFrame(records),dict(symbol=symbol,rows_1m=len(px),rows_mark=len(mark),rows_oi=len(oi),first=str(px.index[0]),last=str(px.index[-1]))
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    ledgers=[];quality=[]
    for symbol in ("BTCUSD","ETHUSD"):
        l,q=calc(symbol);ledgers.append(l);quality.append(q)
    d=pd.concat(ledgers,ignore_index=True)
    d["year"]=d.day.str[:4]
    d["month"]=d.day.str[:7]
    d.to_csv(OUT/"daily.csv",index=False)
    rows=[]
    for (s,y),g in d.groupby(["symbol","year"]):
        v=g.net_usd.to_numpy();eq=np.r_[0,np.cumsum(v)]
        gains=v[v>0].sum();loss=-v[v<0].sum()
        rows.append(dict(symbol=s,year=y,calendar_days=len(g),profit_days=int((g.status=="PROFIT").sum()),loss_days=int((g.status=="LOSS").sum()),no_trade_days=int((g.status=="NO_TRADE").sum()),data_gap_days=int((g.status=="DATA_GAP").sum()),net_usd=round(v.sum(),3),return_pct=round(v.sum()/NOTIONAL*100,3),pf=round(gains/loss,3) if loss else None,max_drawdown_pct=round((np.maximum.accumulate(eq)-eq).max()/NOTIONAL*100,3),median_day_usd=round(float(np.median(v)),4),mean_day_usd=round(float(np.mean(v)),4),worst_day_usd=round(float(v.min()),4),fees_gst_usd=round(g.fee_gst_usd.sum(),3),slippage_usd=round(g.slippage_usd.sum(),3),stress_net_usd=round(g.stress_net_usd.sum(),3)))
    annual=pd.DataFrame(rows);annual.to_csv(OUT/"annual.csv",index=False)
    monthly=d.groupby(["symbol","month"],as_index=False).agg(net_usd=("net_usd","sum"),profit_days=("status",lambda x:(x=="PROFIT").sum()),loss_days=("status",lambda x:(x=="LOSS").sum()),no_trade_days=("status",lambda x:(x=="NO_TRADE").sum()))
    monthly["return_pct"]=monthly.net_usd/NOTIONAL*100
    monthly.to_csv(OUT/"monthly.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2))
    (OUT/"REPORT.md").write_text("# OI expansion plus mark premium: pre-registered crowding fade\n\n"+annual.to_markdown(index=False)+"\n\n## Monthly\n"+monthly.to_markdown(index=False)+"\n\nNo fills or settled funding available. OI snapshot timestamps might be candle-open rather than candle-close; strategy is NOT executable without confirming timestamps, bid/ask, spread, minimum lots, margin, and actual funding settlements. 2026 is research-exposed, not a pristine holdout. Funding modeled zero over 60m, which is not verified. Trade open/mark OHLC are proxies; costs 0.158% roundtrip, stress 0.198%. One trade per UTC day, stop first.\n")
    print(annual.to_string(index=False))
    print("RESEARCH_COMPLETE")
if __name__=="__main__":main()
