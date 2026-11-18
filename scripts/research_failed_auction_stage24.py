#!/usr/bin/env python3
"""Independent Stage24: two-hour failed-auction reversal; 22 completed IST months.
Research only. No historical future labels used in signals. One position at a time.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive,FEE,SLIPPAGE

OUT=Path("analysis/stage24_failed_auction")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,ss,se,q=read_archive()
    h=f[["open","high","low","close","volume"]].resample("1h",closed="left",label="right").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    h["count"]=f.close.resample("1h",closed="left",label="right").count()
    h["valid"]=h["count"].rolling(15,min_periods=15).min().eq(60)
    prev_hi=h.high.shift(2).rolling(12,min_periods=12).max()
    prev_lo=h.low.shift(2).rolling(12,min_periods=12).min()
    tr=pd.concat([h.high-h.low,(h.high-h.close.shift()).abs(),(h.low-h.close.shift()).abs()],axis=1).max(axis=1)
    atr=tr.rolling(14,min_periods=14).mean()
    short=(h.close.shift(1)>prev_hi)&(h.close<prev_hi)&(h.close>prev_lo)&(h.close<h.open)
    long=(h.close.shift(1)<prev_lo)&(h.close>prev_lo)&(h.close<prev_hi)&(h.close>h.open)
    idx=f.index.get_indexer(h.index)
    events=[]
    for j in range(15,len(h)):
        k=int(idx[j])
        if k<0 or not bool(h.valid.iat[j]) or not np.isfinite(atr.iat[j]):continue
        if k-ss[k]<900 or se[k]-k<720:continue
        for side,ok in ((1,long.iat[j]),(-1,short.iat[j])):
            if bool(ok):events.append((k,side,float(atr.iat[j])))
    events.sort()
    op=f.open.to_numpy(float);hi=f.high.to_numpy(float);lo=f.low.to_numpy(float)
    cl=f.close.to_numpy(float);ts=f.time.to_numpy(np.int64)
    ledger=[];monthly=[];ranks=[]
    for multiple in (1.5,2.5):
        for reward in (2.,3.):
            for hold in (360,720):
                busy=-1;rows=[]
                for k,side,a in events:
                    if k<=busy:continue
                    risk=float(np.clip(multiple*a,150.,1600.))
                    entry=op[k];stop=entry-side*risk;target=entry+side*reward*risk
                    for j in range(k,k+hold):
                        stophit=(lo[j]<=stop if side==1 else hi[j]>=stop)
                        tphit=(hi[j]>=target if side==1 else lo[j]<=target)
                        if stophit:
                            exitpx=min(op[j],stop) if side==1 else max(op[j],stop)
                            reason="stop";break
                        if tphit:
                            exitpx=target;reason="target";break
                    else:
                        j=k+hold-1;exitpx=cl[j];reason="timeout"
                    busy=j
                    fillin=entry+side*SLIPPAGE;fillout=exitpx-side*SLIPPAGE
                    netpts=side*(fillout-fillin)-FEE*(fillin+fillout)
                    ret=min(.005,5*risk/entry)*netpts/risk
                    month=pd.to_datetime(int(ts[j]),unit="s",utc=True).tz_convert("Asia/Kolkata").strftime("%Y-%m")
                    if month not in MONTHS:continue
                    rows.append(dict(atr_mult=multiple,reward_R=reward,hold_min=hold,
                        entry_unix=int(ts[k]),exit_unix=int(ts[j]),month_ist=month,
                        direction="LONG" if side==1 else "SHORT",reason=reason,
                        net_points=round(float(netpts),6),return_fraction=float(ret)))
                ledger.extend(rows)
                eq=1.;peak=1.;dd=0.;returns=[]
                for month in MONTHS:
                    trades=[x for x in rows if x["month_ist"]==month]
                    trades.sort(key=lambda x:x["exit_unix"])
                    start=eq
                    for t in trades:
                        eq*=1+t["return_fraction"]
                        peak=max(peak,eq);dd=max(dd,1-eq/peak)
                    net=(eq/start-1)*100
                    returns.append(net)
                    monthly.append(dict(atr_mult=multiple,reward_R=reward,hold_min=hold,
                        month_ist=month,trades=len(trades),
                        winning_trades=sum(t["net_points"]>0 for t in trades),
                        losing_trades=sum(t["net_points"]<0 for t in trades),
                        flat_trades=sum(t["net_points"]==0 for t in trades),
                        net_account_return_pct=round(net,6)))
                ranks.append(dict(atr_mult=multiple,reward_R=reward,hold_min=hold,
                    positive_2025=sum(x>1e-9 for x in returns[:12]),
                    positive_2026=sum(x>1e-9 for x in returns[12:]),
                    min_2025_pct=min(returns[:12]),max_drawdown_pct=100*dd,
                    total_trades=len(rows)))
    pd.DataFrame(ledger).to_csv(OUT/"ledger.csv.gz",index=False,compression="gzip")
    pd.DataFrame(monthly).to_csv(OUT/"all_monthly.csv",index=False)
    ranking=pd.DataFrame(ranks).sort_values(["positive_2025","min_2025_pct"],
        ascending=[False,False],kind="stable")
    ranking.to_csv(OUT/"ranking.csv",index=False)
    best=ranking.iloc[0]
    selected=pd.DataFrame(monthly)
    for col in ("atr_mult","reward_R","hold_min"):selected=selected[selected[col]==best[col]]
    selected.to_csv(OUT/"selected_monthly.csv",index=False)
    verdict={"selected_2025_only":best.to_dict(),
        "positive_months":int((selected.net_account_return_pct>0).sum()),
        "required_months":22,"all_positive":bool((selected.net_account_return_pct>0).all()),
        "source_missing_minutes":q["missing_minutes"],
        "october_31_complete":False,
        "costs":"0.05% taker per side, 18% GST, 5 points adverse slippage per side",
        "limits":["October 31 2026 source candles need verification before any 22/22 claim",
            "2026 previously studied, not pristine out-of-sample",
            "Funding, actual spreads, impact, liquidation and lot-size feasibility not modeled",
            "One position at a time; stop-first 1m OHLC ambiguity; 0.5% risk, 5x leverage cap",
            "No-trade month is not profitable; intratrade drawdown may exceed trade-close drawdown"]}
    (OUT/"verdict.json").write_text(json.dumps(verdict,indent=2,default=str)+"\n")
    (OUT/"README.md").write_text("# Stage24 — failed-auction hourly reversal\n\n"+
        "After hour A closes beyond prior 12h extreme, hour B closes back inside; "+
        "enter against breakout at next minute open. Fixed 2025-only selection; "+
        "replay 2026 unchanged. November 2026 excluded.\n\n"+
        selected.to_markdown(index=False)+"\n\n"+json.dumps(verdict,indent=2,default=str)+"\n")
    print("STAGE24_VERDICT",json.dumps(verdict,default=str))
if __name__=="__main__":main()
