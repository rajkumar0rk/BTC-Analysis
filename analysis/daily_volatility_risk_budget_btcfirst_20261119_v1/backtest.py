#!/usr/bin/env python3
"""Frozen BTC-first volatility regime study. One row per UTC calendar day."""
import hashlib,json
from pathlib import Path
import numpy as np,pandas as pd
OUT=Path("analysis/daily_volatility_risk_budget_btcfirst_20261119_v1")
OUT.mkdir(parents=True,exist_ok=True)
def load(sym):
 files=sorted((Path("data/delta_india")/sym/"1m").glob("20??-??.csv.gz"))
 if not files:raise RuntimeError("MISSING_ARCHIVE "+sym)
 parts=[]; hashes=[]
 for f in files:
  a=pd.read_csv(f,compression="gzip")
  if not {"time","open","high","low","close"}.issubset(a):raise RuntimeError("SCHEMA "+str(f))
  a=a[["time","open","high","low","close"]]
  a["time"]=pd.to_datetime(pd.to_numeric(a.time),unit="s",utc=True)
  parts.append(a);hashes.append({"path":str(f),"sha256":hashlib.sha256(f.read_bytes()).hexdigest(),"rows":len(a)})
 x=pd.concat(parts).sort_values("time").set_index("time")
 if x.index.has_duplicates or x.isna().any().any() or (x[["open","high","low","close"]]<=0).any().any() or (x.high<x[["open","close","low"]].max(axis=1)).any() or (x.low>x[["open","close","high"]].min(axis=1)).any():raise RuntimeError("INVALID_OHLC")
 return x,hashes
def execute(sym,cost):
 x,hashes=load(sym);rows=[];trades=[];nav=1.0;peak=1.0
 dates=pd.date_range("2025-01-01","2026-11-17",freq="D",tz="UTC")
 for d in dates:
  status="no_trade";reason="filter";gross=net=0.;direction=0;cv=np.nan;rvprev=np.nan;entry=np.nan;exitp=np.nan
  prior=pd.date_range(d-pd.Timedelta(days=7),d-pd.Timedelta(minutes=1),freq="min")
  future=pd.date_range(d+pd.Timedelta(minutes=1),d+pd.Timedelta(hours=4),freq="min")
  if not (len(x.loc[d-pd.Timedelta(days=7):d-pd.Timedelta(minutes=1)])==10080 and len(x.loc[d+pd.Timedelta(minutes=1):d+pd.Timedelta(hours=4)])==240):
   status="data_gap";reason="missing_window"
  else:
   p=x.loc[prior];f=x.loc[future]
   c=p.close.to_numpy().reshape(7,1440);o=p.open.to_numpy().reshape(7,1440)
   returns=np.diff(np.log(c),axis=1)
   rv=np.sqrt((returns**2).sum(axis=1))
   cv=float(rv.std()/rv.mean()) if rv.mean()>0 else np.inf
   rvprev=float(rv[-1])
   move=float(c[-1,-1]/o[-1,0]-1)
   if cv<=.4 and rv[-1]<=1.25*np.median(rv) and abs(move)>=.004:
    direction=1 if move>0 else -1
    entry=float(f.open.iloc[0]);stop=entry*(1-direction*.0045);target=entry*(1+direction*.007)
    exitp=float(f.open.iloc[-1]);reason="time"
    for t,b in f.iloc[:-1].iterrows():
     if (b.low<=stop if direction>0 else b.high>=stop):
      exitp=stop;reason="stop";break
     if (b.high>=target if direction>0 else b.low<=target):
      exitp=target;reason="target";break
    # 25% notional of initial equity; no leverage, noncompounded
    gross=nav*.25*direction*(exitp/entry-1);net=gross-nav*.25*cost;nav+=net
    status="profit" if net>0 else "loss"
    trades.append(dict(market=sym,date=str(d.date()),entry_utc=(d+pd.Timedelta(minutes=1)).isoformat(),direction=direction,entry=entry,exit=exitp,exit_reason=reason,cv=cv,previous_rv=rvprev,gross_pnl=gross,net_pnl=net,cost_roundtrip_pct=cost*100))
  peak=max(peak,nav)
  rows.append(dict(market=sym,date=str(d.date()),year=d.year,month=d.strftime("%Y-%m"),status=status,reason=reason,net_pnl=net,gross_pnl=gross,nav_end=nav,drawdown_pct=100*(peak-nav)/peak,direction=direction,cv=cv,previous_rv=rvprev))
 return pd.DataFrame(rows),pd.DataFrame(trades),hashes
def main():
 all_d=[];all_t=[];monthly=[];annual=[];provenance=[]
 for sym in ("BTCUSD","ETHUSD"):
  for cost,scenario in ((.00158,"base"),(.00238,"stress")):
   d,t,h=execute(sym,cost);d["scenario"]=scenario;t["scenario"]=scenario
   all_d.append(d);all_t.append(t)
   if scenario=="base":provenance.append({"market":sym,"files":h})
   for (year,month),g in d.groupby(["year","month"]):
    closed=t.loc[t.date.str[:7]==g.date.iloc[0][:7]] if not t.empty else pd.DataFrame()
    wins=closed.loc[closed.net_pnl>0,"net_pnl"].sum() if not closed.empty else 0;loss=-closed.loc[closed.net_pnl<0,"net_pnl"].sum() if not closed.empty else 0
    monthly.append(dict(market=sym,scenario=scenario,year=year,month=month,net_account_pct=100*(g.nav_end.iloc[-1]/(g.nav_end.iloc[0]-g.net_pnl.iloc[0])-1),pf=wins/loss if loss else ("Infinity" if wins else None),profit_days=int((g.status=="profit").sum()),loss_days=int((g.status=="loss").sum()),no_trade_days=int((g.status=="no_trade").sum()),data_gap_days=int((g.status=="data_gap").sum())))
   for year,g in d.groupby("year"):
    v=g.net_pnl.to_numpy();curve=g.nav_end.to_numpy();closed=t.loc[t.date.str[:4]==str(year)] if not t.empty else pd.DataFrame();wins=closed.loc[closed.net_pnl>0,"net_pnl"].sum() if not closed.empty else 0;loss=-closed.loc[closed.net_pnl<0,"net_pnl"].sum() if not closed.empty else 0
    annual.append(dict(market=sym,scenario=scenario,year=year,net_account_pct=100*(g.nav_end.iloc[-1]/(g.nav_end.iloc[0]-g.net_pnl.iloc[0])-1),pf=wins/loss if loss else ("Infinity" if wins else None),trades=int(g.status.isin(["profit","loss"]).sum()),profitable_days=int((g.status=="profit").sum()),losing_days=int((g.status=="loss").sum()),no_trade_days=int((g.status=="no_trade").sum()),data_gap_days=int((g.status=="data_gap").sum()),max_daily_equity_drawdown_pct=float(g.drawdown_pct.max()),mean_day_pct=v.mean(),median_day_pct=np.median(v),worst_day_pct=v.min()))
 pd.concat(all_d).to_csv(OUT/"daily.csv",index=False)
 pd.concat(all_t).to_csv(OUT/"trades.csv",index=False)
 pd.DataFrame(monthly).to_csv(OUT/"monthly.csv",index=False)
 pd.DataFrame(annual).to_csv(OUT/"annual.csv",index=False)
 (OUT/"provenance.json").write_text(json.dumps(provenance,indent=2))
 print("ANNUAL");print(pd.DataFrame(annual).to_string(index=False));print("MONTHLY");print(pd.DataFrame(monthly).to_string(index=False))
 print("INCONCLUSIVE executable validation: OHLC stop-first, no verified bid/ask, settled funding, lot/tick, gap fills or margin.")
if __name__=="__main__":main()
