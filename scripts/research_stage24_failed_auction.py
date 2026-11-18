#!/usr/bin/env python3
"""Causal hourly failed-auction reversal, next-minute fills, 22 IST months."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive,FEE,SLIPPAGE

OUT=Path("analysis/stage24_failed_auction")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,ss,se,q=read_archive()
    hourly=f[["open","high","low","close"]].resample("1h",closed="left",label="right").agg({"open":"first","high":"max","low":"min","close":"last"})
    hourly["n"]=f.close.resample("1h",closed="left",label="right").count()
    hourly["valid"]=hourly.n.rolling(15,min_periods=15).min().eq(60)
    upper=hourly.high.shift(2).rolling(12,min_periods=12).max()
    lower=hourly.low.shift(2).rolling(12,min_periods=12).min()
    atr=(hourly.high-hourly.low).rolling(14,min_periods=14).mean()
    sell=(hourly.close.shift(1)>upper)&(hourly.close<upper)&(hourly.close>lower)&(hourly.close<hourly.open)
    buy=(hourly.close.shift(1)<lower)&(hourly.close>lower)&(hourly.close<upper)&(hourly.close>hourly.open)
    ix=f.index.get_indexer(hourly.index)
    events=[]
    for j in range(len(hourly)):
        k=int(ix[j])
        if k<0 or not bool(hourly.valid.iat[j]) or k-ss[k]<900 or se[k]-k<720:continue
        side=1 if bool(buy.iat[j]) else -1 if bool(sell.iat[j]) else 0
        if side and np.isfinite(atr.iat[j]):events.append((k,side,float(atr.iat[j])))
    op=f.open.to_numpy(float);hi=f.high.to_numpy(float);lo=f.low.to_numpy(float);cl=f.close.to_numpy(float)
    t=f.time.to_numpy("int64")
    records=[]
    for mult in (1.5,2.5):
      for rr in (2.,3.):
       for hold in (360,720):
        busy=-1
        for k,side,vol in events:
          if k<=busy:continue
          risk=float(np.clip(mult*vol,150,1600))
          stop=op[k]-side*risk;target=op[k]+side*rr*risk
          for j in range(k,k+hold):
            if (lo[j]<=stop if side==1 else hi[j]>=stop):
              px=min(op[j],stop) if side==1 else max(op[j],stop);reason="stop";break
            if (hi[j]>=target if side==1 else lo[j]<=target):
              px=target;reason="target";break
          else:j=k+hold-1;px=cl[j];reason="timeout"
          busy=j
          entryfill=op[k]+side*SLIPPAGE;exitfill=px-side*SLIPPAGE
          net=side*(exitfill-entryfill)-FEE*(entryfill+exitfill)
          equity_return=min(.005,5*risk/op[k])*net/risk
          records.append(dict(mult=mult,rr=rr,hold=hold,entry_unix=int(t[k]),exit_unix=int(t[j]),side=side,net_pts=float(net),return_fraction=float(equity_return),reason=reason))
    trades=pd.DataFrame(records)
    if trades.empty:raise RuntimeError("No eligible trades")
    trades["month_ist"]=pd.to_datetime(trades.exit_unix,unit="s",utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    trades.to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    monthly=[]
    for key,g in trades.groupby(["mult","rr","hold"]):
      for month in MONTHS:
        part=g[g.month_ist==month]
        net=100*(np.prod(1+part.return_fraction.to_numpy())-1)
        monthly.append(dict(mult=key[0],rr=key[1],hold=key[2],month_ist=month,trades=len(part),wins=int((part.net_pts>0).sum()),losses=int((part.net_pts<0).sum()),net_return_pct=float(net)))
    table=pd.DataFrame(monthly)
    table.to_csv(OUT/"monthly.csv",index=False)
    ranking=[]
    for key,g in table.groupby(["mult","rr","hold"]):
      y=g[g.month_ist.str.startswith("2025")]
      ranking.append((int((y.net_return_pct>0).sum()),float(y.net_return_pct.min()),key))
    choice=sorted(ranking,reverse=True)[0][2]
    selected=table[(table.mult==choice[0])&(table.rr==choice[1])&(table.hold==choice[2])]
    selected.to_csv(OUT/"selected_monthly.csv",index=False)
    selected_trades=trades[(trades.mult==choice[0])&(trades.rr==choice[1])&(trades.hold==choice[2])].sort_values("exit_unix")
    eq=1.;peak=1.;dd=0.
    for v in selected_trades.return_fraction:
      eq*=1+v;peak=max(peak,eq);dd=max(dd,1-eq/peak)
    result=dict(selected_parameters=dict(mult=choice[0],rr=choice[1],hold=choice[2]),positive_months=int((selected.net_return_pct>0).sum()),required_months=22,trade_close_drawdown_pct=100*dd,selected_trade_count=len(selected_trades),source_missing_minutes=q["missing_minutes"],october_31_2026_source_gap_unresolved=True,november_excluded=True,limitations=["No funding or actual order-book spread/impact","October 31 missing: cannot certify October complete","2026 already research-exposed, not blind holdout","Intratrade drawdown may exceed trade-close drawdown","Assumes fractional sizing and 5x leverage, not validated exchange minimums"])
    (OUT/"result.json").write_text(json.dumps(result,indent=2)+"\n")
    print("STAGE24_RESULT",json.dumps(result))
    print(selected.to_string(index=False))
if __name__=="__main__":main()
