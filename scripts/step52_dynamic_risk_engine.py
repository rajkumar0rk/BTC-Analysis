"""Feedback-aware recovery-overlay stress; mark/funding historical proxies.
No new parameter selection. Upstream trained arm/ridge models stay frozen.
Funding data are indicative hourly candles, not account settlement records.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import json

def archive(kind):
    root=Path("data/delta_india/BTCUSD/institutional/history")/kind
    files=sorted(root.glob("*.csv.gz"))
    if not files:raise FileNotFoundError(root)
    d=pd.concat([pd.read_csv(p) for p in files],ignore_index=True)
    d["time"]=pd.to_datetime(d.time.astype("int64"),unit="s",utc=True)
    d=d.set_index("time").sort_index()
    if d.index.has_duplicates:raise AssertionError("duplicate "+kind)
    return d

class Risk:
    def __init__(self,m,slip,mode,fee):
        self.m=m
        self.slip=slip;self.mode=mode;self.fee=fee
        self.o=m.open.to_numpy(float)
        self.f=archive("funding_1h")
        self.mark=archive("mark_1m").reindex(m.index)
        self.rate=self.f.close.shift(1).reindex(m.index,method="ffill").to_numpy(float)/100
        # 8-Sep-2025 17:30 IST = 12:00 UTC; subsequent UTC 00/08/16.
        self.change=pd.Timestamp("2025-09-08T12:00Z")
        self.upgrade=pd.Timestamp("2025-10-11T00:00:00+05:30")
        self.before=(m.index<self.change)
        self.boundary=(m.index.minute==0)&(m.index.hour%8==0)
        # Prior hourly observations approximate historical minute accrual; after
        # transition, use preceding hourly close at scheduled funding timestamp.
        self.mark_close=self.mark.close.to_numpy(float)
        self.mark_open=self.mark.open.to_numpy(float)
        self.mark_low=self.mark.low.to_numpy(float)
        self.mark_high=self.mark.high.to_numpy(float)
    def funding(self,starts,holds,side,entry,adverse=False):
        starts=np.broadcast_to(starts,holds.shape); ends=starts+holds
        out=np.zeros(holds.shape)
        # Position at exactly start/end settlement has unresolved sequencing;
        # charge adverse only at ambiguous boundaries.
        for offset in range(int(holds.max())+1):
            ii=starts+offset
            pre=self.before[ii]&(offset<holds)
            post=(~self.before[ii])&self.boundary[ii]&(offset<=holds)
            if not (pre|post).any():continue
            # Hourly rate quoted in percent per 8 hours; index unavailable:
            # contemporaneous mark is explicit proxy for index notional.
            rate=self.rate[ii];px=self.mark_open[ii]
            valid=pre|post
            if not np.isfinite(rate[valid]).all() or not np.isfinite(px[valid]).all():
                raise AssertionError("funding or mark missing at candidate settlement")
            payment=side*rate*px/entry*np.where(pre,1/480,1.)
            ambiguous=post&((offset==0)|(offset==holds))
            if adverse:payment=np.abs(payment)
            payment=np.where(ambiguous,np.maximum(payment,0),payment)
            out+=np.where(valid,payment,0)
        return out
    def prices(self,starts,holds,side,gross):
        mid=self.o[starts][:,None]
        entry=mid+side*self.slip
        exitfill=mid+side*gross-side*self.slip
        starts2=np.broadcast_to(starts[:,None],holds.shape)
        if self.mode=="historical":
            old=(self.m.index[starts]<self.upgrade)[:,None]
            waive=holds<np.where(old,15,30)
        elif self.mode=="conservative":
            waive=(self.m.index[starts]>=self.upgrade)[:,None]&(holds<30)
        elif self.mode=="offer30":waive=holds<30
        elif self.mode=="standard":waive=np.zeros_like(holds,bool)
        else:raise ValueError(self.mode)
        fee=self.fee*(entry+exitfill*(~waive))
        fund=self.funding(starts2,holds,side,entry,adverse=True)
        trade=side*(exitfill-entry)
        return (trade-fee)/entry-fund,fee,fund
    def reprice(self,cache,starts):
        for (side,guard,cap),raw in list(cache.items()):
            pnl,fee,gross,reason,hold=raw
            p,f,_=self.prices(starts,hold,side,gross)
            pnl=pnl.copy();fee=fee.copy()
            pnl[:,:,1]=p;fee[:,:,1]=f
            cache[(side,guard,cap)]=(pnl,fee,gross,reason,hold)
        return cache
    def final(self,selected,out,s):
        rows=[]
        equity=1.;peak=1.;dd=0.;worst=0.;liqs={str(x):0 for x in (1,10,20,50,100)}
        for d,row in enumerate(selected):
            start,side,guard,cap,pid,hold,reason,gross=row[2:]
            start,side,hold=int(start),int(side),int(hold)
            end=start+hold
            p,fee,fund=self.prices(np.array([start]),np.array([[hold]]),side,np.array([[gross]]))
            assert abs(p[0,0]-row[1])<1e-11
            entry=self.o[start]+side*self.slip
            marklo=self.mark_low[start:end+1];markhi=self.mark_high[start:end+1]
            assert np.isfinite(marklo).all() and np.isfinite(markhi).all(),("missing mark",d)
            for lo,hi in zip(marklo,markhi):
                favorable=hi if side==1 else lo
                adverse=lo if side==1 else hi
                maxmove=side*(favorable-entry)/entry
                minmove=side*(adverse-entry)/entry
                # Include whole exit minute: conservative bound, not exact intraminute path.
                peak=max(peak,equity*(1+maxmove-self.fee))
                loweq=equity*(1+minmove-self.fee-fund[0,0])
                dd=max(dd,1-loweq/peak)
                worst=min(worst,minmove)
            adverse=marklo.min() if side==1 else markhi.max()
            move=side*(adverse-entry)/entry
            # Hypothetical isolated 0.5% maintenance + fee reserve.
            # This is not the historical exchange liquidation engine.
            for lev in (1,10,20,50,100):
                if 1/lev+move-self.fee-fund[0,0]<=.005*adverse/entry+self.fee:
                    liqs[str(lev)]+=1
            equity*=1+row[1];peak=max(peak,equity);dd=max(dd,1-equity/peak)
            rows.append(dict(date=s.base.IST_DAYS[d],entry=self.m.index[start],exit=self.m.index[end],side=side,net_pct=row[1]*100,funding_cost_pct=fund[0,0]*100,mark_adverse_pct=move*100))
        df=pd.DataFrame(rows);df.to_csv(out/(self.mode+"_"+str(self.slip)+"_risk_ledger.csv"),index=False)
        eq=np.cumprod(1+selected[:,1])
        mo=pd.Series(selected[:,1],index=s.MONTHS).groupby(level=0).apply(lambda x:100*(np.prod(1+x)-1))
        report=dict(mode=self.mode,slip_per_side=self.slip,net_pct=float(100*(eq[-1]-1)),months_positive=int((mo>0).sum()),months_ge1=int((mo>=1).sum()),worst_month_pct=float(mo.min()),closed_dd_pct=float(100*np.max(1-eq/np.maximum.accumulate(np.r_[1.,eq])[1:])),conservative_mark_dd_pct=float(100*dd),worst_mark_adverse_pct=float(-100*worst),funding_cost_sum_pct=float(df.funding_cost_pct.sum()),funding_charged_trades=int((df.funding_cost_pct>0).sum()),hypothetical_liquidation_breaches=liqs,monthly=mo.to_dict(),trades=len(df),limitations=["Funding rates are hourly proxies; index notional unavailable, mark substituted; adverse-only funding","Earlier minute accrual estimated using prior hourly rate","Fee upgrade date uses public announcement as proxy for exact effective time","Recovery shadow and overlay decisions re-evaluated under scenario costs; upstream arm and ridge training frozen","Intraminute mark drawdown conservative including exit minute","Liquidation sensitivity 0.5% maintenance, not exact historical margin tiers"])
        (out/(self.mode+"_"+str(self.slip)+"_summary.json")).write_text(json.dumps(report,indent=2))
        print("STEP52_DYNAMIC",json.dumps(report),flush=True)
