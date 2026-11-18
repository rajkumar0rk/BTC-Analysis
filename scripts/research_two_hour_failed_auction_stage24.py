#!/usr/bin/env python3
"""Independent Stage24: failed 2-hour auction reversal; 22 complete IST months only."""
from pathlib import Path
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive,FEE,SLIPPAGE

OUT=Path("analysis/stage24_failed_auction")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,ss,se,quality=read_archive()
    h=f[["open","high","low","close","volume"]].resample("1h",label="right",closed="left").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    h["count"]=f.close.resample("1h",label="right",closed="left").count()
    h["complete"]=h["count"].rolling(30,min_periods=30).min().eq(60)
    prior_hi=h.high.shift(2).rolling(12,min_periods=12).max()
    prior_lo=h.low.shift(2).rolling(12,min_periods=12).min()
    tr=pd.concat([h.high-h.low,(h.high-h.close.shift()).abs(),(h.low-h.close.shift()).abs()],axis=1).max(axis=1)
    atr=tr.rolling(14,min_periods=14).mean()
    long=(h.close.shift()>0)&(h.close.shift()<prior_lo)&(h.close>prior_lo)&(h.close<prior_hi)&(h.close>h.open)
    short=(h.close.shift()>prior_hi)&(h.close<prior_hi)&(h.close>prior_lo)&(h.close<h.open)
    op=f.open.to_numpy(float);hi=f.high.to_numpy(float);lo=f.low.to_numpy(float);cl=f.close.to_numpy(float)
    unix=f.time.to_numpy(np.int64)
    indexes=f.index.get_indexer(h.index)
    signals=[]
    for j in np.flatnonzero(h.complete.to_numpy(bool)):
        k=int(indexes[j])
        if k<0 or k-ss[k]<1800 or se[k]-k<720 or not np.isfinite(atr.iat[j]):continue
        if bool(long.iat[j]):signals.append((k,1,float(atr.iat[j])))
        if bool(short.iat[j]):signals.append((k,-1,float(atr.iat[j])))
    signals.sort()
    ledgers=[];summary=[]
    for mult in (1.5,2.5):
      for reward in (2.,3.):
       for hold in (360,720):
        busy=-1
        for k,side,a in signals:
            if k<=busy:continue
            risk=float(np.clip(mult*a,150,1600))
            stop=op[k]-side*risk;target=op[k]+side*reward*risk
            reason="timeout";j=k+hold-1;px=cl[j]
            for q in range(k,k+hold):
                if (side==1 and lo[q]<=stop) or (side==-1 and hi[q]>=stop):
                    j=q;px=min(op[q],stop) if side==1 else max(op[q],stop);reason="stop";break
                if (side==1 and hi[q]>=target) or (side==-1 and lo[q]<=target):
                    j=q;px=target;reason="target";break
            busy=j
            fi=op[k]+side*SLIPPAGE;fo=px-side*SLIPPAGE
            net=side*(fo-fi)-FEE*(fi+fo)
            ret=min(.005,5*risk/op[k])*net/risk
            month=pd.Timestamp(int(unix[j]),unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m")
            if month not in MONTHS:continue
            ledgers.append(dict(atr_mult=mult,reward_R=reward,hold_min=hold,entry_unix=int(unix[k]),exit_unix=int(unix[j]),side=side,reason=reason,net_pts=net,trade_return=ret,month_ist=month))
    ledger=pd.DataFrame(ledgers)
    if ledger.empty:raise RuntimeError("No qualifying trades")
    ledger.to_csv(OUT/"all_trade_ledgers.csv.gz",index=False,compression="gzip")
    monthly=[]
    for (mult,reward,hold),g in ledger.groupby(["atr_mult","reward_R","hold_min"]):
        for month in MONTHS:
            p=g[g.month_ist==month]
            v=100*(np.prod(1+p.trade_return.to_numpy())-1)
            monthly.append(dict(atr_mult=mult,reward_R=reward,hold_min=hold,month_ist=month,trades=len(p),wins=int((p.net_pts>0).sum()),losses=int((p.net_pts<0).sum()),flat=int((p.net_pts==0).sum()),net_account_return_pct=v))
    m=pd.DataFrame(monthly)
    m.to_csv(OUT/"all_monthly.csv",index=False)
    ranks=m.groupby(["atr_mult","reward_R","hold_min"]).apply(lambda g:pd.Series(dict(positive_2025=int((g[g.month_ist.str.startswith("2025")].net_account_return_pct>0).sum()),positive_2026=int((g[g.month_ist.str.startswith("2026")].net_account_return_pct>0).sum()),worst_2025=float(g[g.month_ist.str.startswith("2025")].net_account_return_pct.min()))),include_groups=False).reset_index()
    ranks=ranks.sort_values(["positive_2025","worst_2025"],ascending=[False,False])
    ranks.to_csv(OUT/"ranked_2025_only.csv",index=False)
    pick=ranks.iloc[0]
    chosen=m[(m.atr_mult==pick.atr_mult)&(m.reward_R==pick.reward_R)&(m.hold_min==pick.hold_min)]
    chosen.to_csv(OUT/"selected_monthly.csv",index=False)
    win=int((chosen.net_account_return_pct>0).sum())
    report=["# Stage24 — 2-hour failed auction reversal","",f"22-month positives: {win}/22","",f"Original source missing minutes: {quality['missing_minutes']}; October 31 2026 must be audited before full-month validation.","","2025-only parameter ranking, previously exposed 2026 evaluation; NOT independent out-of-sample.","Costs: 0.05% taker per side, 18% GST, 5-point adverse slippage per side.","Missing: funding, order-book spread/impact, liquidation, lot sizing. Intratrade drawdown not calculated.","",chosen.to_markdown(index=False)]
    (OUT/"REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE24_RESULT",win,"/22", "TRADES",int(chosen.trades.sum()))
if __name__=="__main__":main()
