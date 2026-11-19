#!/usr/bin/env python3
"""BTC-first, predeclared OI absorption-to-release feasibility test. No parameter search."""
import json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path("data/delta_india")
OUT=Path("analysis/daily_oi_absorption_release_20261119_v1")
CAPITAL=1000.; NOTIONAL=1000.; COST=.00158; STRESS=.00238
def read(folder,cols):
    paths=sorted(folder.glob("20??-??.csv.gz"))
    if not paths: raise RuntimeError("No authentic files "+str(folder))
    parts=[]; provenance=[]
    for p in paths:
        x=pd.read_csv(p,compression="gzip")
        if not set(["time"]+cols).issubset(x.columns):raise RuntimeError("missing columns "+str(p))
        x=x[["time"]+cols].copy()
        x["time"]=pd.to_datetime(pd.to_numeric(x["time"]),unit="s",utc=True)
        parts.append(x.set_index("time"))
        provenance.append({"file":str(p),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"rows":len(x)})
    x=pd.concat(parts).sort_index()
    if x.index.has_duplicates:raise RuntimeError("duplicate timestamps")
    return x.astype(float),provenance
def simulate(symbol):
    root=ROOT/symbol
    px,prov=read(root/"1m",["open","high","low","close"])
    oi,oprov=read(root/"institutional/history/open_interest_5m",["close"])
    if not px.index.equals(pd.date_range(px.index[0],px.index[-1],freq="min")):raise RuntimeError("incomplete minute candles")
    b=px.resample("5min",label="left",closed="left").agg({"open":"first","high":"max","low":"min","close":"last"})
    # 5m timestamp t represents the interval [t,t+5min); all decisions are at t+5min.
    # To avoid assuming OI timestamp semantics, delay OI observation one additional 5m interval.
    b["oi"]=oi["close"].reindex(b.index).shift(1)
    b["oi_growth"]=b.oi/b.oi.shift(12)-1
    b["range60"]=b.high.shift(1).rolling(12).max()/b.low.shift(1).rolling(12).min()-1
    b["prev_hi"]=b.high.shift(1).rolling(12).max()
    b["prev_lo"]=b.low.shift(1).rolling(12).min()
    b["side"]=np.where((b.oi_growth>=.02)&(b.range60<=.008)&(b.close>b.prev_hi),1,
                 np.where((b.oi_growth>=.02)&(b.range60<=.008)&(b.close<b.prev_lo),-1,0))
    # Freeze BTC-chosen, dimensionless rules. ETH only independent secondary replay.
    ledger=[];days=pd.date_range(px.index[0].floor("D"),px.index[-1].floor("D"),freq="D")
    for day in days:
        sig=b.loc[(b.index>=day+pd.Timedelta(hours=1))&(b.index<day+pd.Timedelta(hours=21))&(b.side!=0)]
        if sig.empty:
            ledger.append(dict(symbol=symbol,day=str(day.date()),status="NO_TRADE",net_usd=0.,stress_net_usd=0.,fees_gst_usd=0.,slippage_usd=0.,funding_assumed_usd=0.))
            continue
        t=sig.index[0]; side=int(sig.iloc[0].side); entry_t=t+pd.Timedelta(minutes=5)
        if entry_t not in px.index or entry_t+pd.Timedelta(minutes=89) not in px.index:
            ledger.append(dict(symbol=symbol,day=str(day.date()),status="DATA_GAP",net_usd=0.,stress_net_usd=0.,fees_gst_usd=0.,slippage_usd=0.,funding_assumed_usd=0.))
            continue
        entry=float(px.at[entry_t,"open"]); exitp=float(px.at[entry_t+pd.Timedelta(minutes=89),"close"]);reason="TIME"
        stop=entry*(1-side*.0035); target=entry*(1+side*.007)
        for _,row in px.loc[entry_t:entry_t+pd.Timedelta(minutes=89)].iterrows():
            if (side==1 and row.low<=stop) or (side==-1 and row.high>=stop):
                exitp=stop;reason="STOP";break
            if (side==1 and row.high>=target) or (side==-1 and row.low<=target):
                exitp=target;reason="TARGET";break
        gross=NOTIONAL*side*(exitp/entry-1)
        ledger.append(dict(symbol=symbol,day=str(day.date()),status="PROFIT" if gross>NOTIONAL*COST else "LOSS",
           entry_utc=str(entry_t),side=side,exit_reason=reason,gross_usd=gross,
           net_usd=gross-NOTIONAL*COST,stress_net_usd=gross-NOTIONAL*STRESS,
           fees_gst_usd=NOTIONAL*.00118,slippage_usd=NOTIONAL*.0004,funding_assumed_usd=0.))
    return pd.DataFrame(ledger),{"symbol":symbol,"price":prov,"oi":oprov,"first":str(px.index[0]),"last":str(px.index[-1]),
      "oi_timestamp_semantics":"UNVERIFIED; delayed one 5-minute bar conservatively","execution":"OHLC open proxy, no actual bid/ask fills"}
def summary(g):
    v=g.net_usd.to_numpy();eq=np.r_[0,v.cumsum()];gain=v[v>0].sum();loss=-v[v<0].sum()
    streak=0;worst=0
    for z in v:
        streak=streak+1 if z<0 else 0;worst=max(worst,streak)
    return pd.Series({"calendar_days":len(g),"profitable_days":int((g.status=="PROFIT").sum()),"losing_days":int((g.status=="LOSS").sum()),
       "no_trade_days":int((g.status=="NO_TRADE").sum()),"data_gap_days":int((g.status=="DATA_GAP").sum()),
       "trades":int(g.status.isin(["PROFIT","LOSS"]).sum()),"net_usd":round(v.sum(),4),"return_pct":round(v.sum()/CAPITAL*100,4),
       "pf":round(gain/loss,4) if loss else None,"max_drawdown_pct":round((np.maximum.accumulate(eq)-eq).max()/CAPITAL*100,4),
       "worst_loss_streak":worst,"median_day_usd":round(float(np.median(v)),4),"mean_day_usd":round(float(v.mean()),4),
       "worst_day_usd":round(float(v.min()),4),"fees_gst_usd":round(g.fees_gst_usd.sum(),4),
       "slippage_usd":round(g.slippage_usd.sum(),4),"stress_net_usd":round(g.stress_net_usd.sum(),4)})
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    # BTC is always evaluated first; no ETH-dependent choice or tuning.
    btc,qb=simulate("BTCUSD")
    eth,qe=simulate("ETHUSD")
    d=pd.concat([btc,eth],ignore_index=True)
    d["year"]=d.day.str[:4];d["month"]=d.day.str[:7]
    d.to_csv(OUT/"daily.csv",index=False)
    annual=d.groupby(["symbol","year"],sort=False).apply(summary,include_groups=False).reset_index()
    monthly=d.groupby(["symbol","month"],sort=False).apply(summary,include_groups=False).reset_index()
    annual.to_csv(OUT/"annual.csv",index=False);monthly.to_csv(OUT/"monthly.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps([qb,qe],indent=2))
    verdict="REJECT" if (annual.loc[annual.symbol.eq("BTCUSD"),"net_usd"]<=0).any() else "INCONCLUSIVE_EXECUTION_UNVERIFIED"
    (OUT/"REPORT.md").write_text("# OI absorption-to-release, BTC-first fixed rules\n\nVerdict: "+verdict+
      "\n\n## Annual\n"+annual.to_markdown(index=False)+"\n\n## Monthly\n"+monthly.to_markdown(index=False)+
      "\n\n### Limitations\nOI timestamp semantics unverified (extra five-minute delay). No executable bid/ask, queue, lot/margin, or actual funding cashflows; zero funding is only an unverified assumption. Fees+GST 0.118% and slippage 0.040% per roundtrip, stressed total 0.238%. One position max/day, 0.35% stop, 0.70% TP, 90min expiry, stop-first OHLC. Not live-tradeable evidence. 2026 previously research-exposed.\n")
    print("VERDICT",verdict);print(annual.to_string(index=False));print("RESEARCH_COMPLETE")
if __name__=="__main__":main()
