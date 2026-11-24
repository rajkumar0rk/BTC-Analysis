#!/usr/bin/env python3
"""Fixed static sleeves: unchanged C05 partial TP plus one independent 1H Bollinger reentry.
Separate capital, no rebalancing, no cross-margin or order netting.
2024/25 selection; 2026 conditional, historically exposed. No funding.
"""
import os,sys,json,hashlib,bisect
from pathlib import Path
import pandas as pd
import numpy as np
import research_btc15m_c05_trend_maturity as core
OUT=Path("analysis/btc_c05_diversification_20261124")
WEIGHTS=(0.,.25,.5,.75,1.)
INITIAL=1000.
def mean_reversion(data,period,path,stress):
    df,_,_,_,_,_,months=data
    tm=df.time.to_numpy(np.int64)
    op,h,l,c=(df[k].to_numpy(float) for k in ("open","high","low","close"))
    # UTC-aligned full hours, last observed hour close. Orders next minute open.
    d=pd.DataFrame({"bucket":tm//3600,"h":h,"l":l,"c":c})
    g=d.groupby("bucket",sort=True).agg(h=("h","max"),l=("l","min"),c=("c","last"),n=("c","size"))
    g=g[g.n==60]
    assert np.all(np.diff(g.index.to_numpy())==1)
    mid=g.c.rolling(20,min_periods=20).mean()
    sd=g.c.rolling(20,min_periods=20).std(ddof=0)
    lo=mid-2*sd;hi=mid+2*sd
    prev=g.c.shift(1)
    longs=(prev<lo.shift(1))&(g.c>=lo)&(g.c<mid)
    shorts=(prev>hi.shift(1))&(g.c<=hi)&(g.c>mid)
    tr=pd.concat([g.h-g.l,(g.h-prev).abs(),(g.l-prev).abs()],axis=1).max(axis=1).to_numpy()
    atr=np.full(len(g),np.nan)
    atr[13]=np.mean(tr[:14])
    for j in range(14,len(g)):atr[j]=(13*atr[j-1]+tr[j])/14
    start=core.date("2024-02-03" if period=="2024" else period+"-01-01")
    ends=(g.index.to_numpy(np.int64)+1)*3600
    events={}
    for j in range(20,len(g)):
        if ends[j]<start.timestamp() or ends[j]>tm[-1]:continue
        i=int(np.searchsorted(tm,ends[j]))
        assert tm[i]==ends[j]
        events[i]=(int(longs.iloc[j])-int(shorts.iloc[j]),float(g.c.iloc[j]),float(mid.iloc[j]),float(atr[j]))
    monthends={}
    for mon in months:
        end=(pd.Period(mon)+1).start_time.tz_localize(core.TZ).tz_convert("UTC")-pd.Timedelta(minutes=1)
        i=int(np.searchsorted(tm,int(end.timestamp())))
        assert tm[i]==int(end.timestamp())
        monthends[i]=mon
    keys=sorted(set(events)|set(monthends))
    cash=INITIAL;pos=None;peak=INITIAL;dd=0.;ledger=[];monthly=[]
    fee=core.base.FEE;slip=core.base.SLIP*(3 if stress else 1)
    def mark(px):
        nonlocal peak,dd
        eq=cash
        if pos is not None:
            side,entry,qty,stop,entryfee,when=pos
            fill=px*(1-side*slip)
            eq+=side*qty*(fill-entry)-fee*qty*fill
        peak=max(peak,eq);dd=max(dd,100*(peak-eq)/peak)
        return eq
    def close(px,i,reason):
        nonlocal cash,pos
        side,entry,qty,stop,entryfee,when=pos
        mark(px)
        fill=px*(1-side*slip)
        gross=side*qty*(fill-entry);exitfee=fee*qty*fill
        cash+=gross-exitfee
        ledger.append(dict(entry_sec=when,exit_sec=int(tm[i]),direction=side,reason=reason,net=gross-entryfee-exitfee,fees=entryfee+exitfee))
        pos=None;mark(px)
    i=0
    while i<len(tm):
        if pos is None and i not in events and i not in monthends:
            k=bisect.bisect_left(keys,i)
            if k==len(keys):break
            i=keys[k]
        had=pos is not None
        raw=op[i]
        if pos is not None and pos[0]*(raw-pos[3])<=0:close(raw,i,"STOP_GAP")
        if i in events:
            signal,last,mean,a=events[i]
            if pos is not None and pos[0]*(last-mean)>=0:close(raw,i,"MEAN")
            # No same-minute reentry following a close.
            if not had and pos is None and signal!=0 and cash>0 and np.isfinite(a) and a>0:
                entry=raw*(1+signal*slip);stop=entry-signal*2*a
                if stop>0 and signal*(raw-stop)>0:
                    qty=cash/entry;entryfee=fee*qty*entry
                    cash-=entryfee;pos=(signal,entry,qty,stop,entryfee,int(tm[i]))
        mark(raw)
        for px in ((h[i],l[i],c[i]) if path=="O-H-L-C" else (l[i],h[i],c[i])):
            if pos is not None and pos[0]*(px-pos[3])<=0:close(pos[3],i,"STOP")
            mark(px)
        if i in monthends:monthly.append(dict(month_ist=monthends[i],equity_usd=mark(c[i])))
        i+=1
    if pos is not None:
        close(c[-1],len(tm)-1,"SAMPLE_END")
        monthly[-1]["equity_usd"]=cash
    assert len(monthly)==len(months)
    assert abs(sum(x["net"] for x in ledger)-(cash-INITIAL))<.02
    m=pd.DataFrame(monthly)
    return dict(net_return_pct=100*(cash/INITIAL-1),max_floating_drawdown_pct=dd,trades=len(ledger),fees_gst_usd=sum(x["fees"] for x in ledger)),m
def evaluate(period,path,stress,weights):
    data=core.prep(period)
    ns=core.engine()
    t,tm,_=core.replay(ns,data,period,0,core.config(0.,1.),100,path,stress)
    r,rm=mean_reversion(data,period,path,stress)
    assert tm.month_ist.tolist()==rm.month_ist.tolist()
    assert abs(float(tm.equity_usd.iloc[-1])/INITIAL-1-t["net_return_pct"]/100)<1e-5
    assert abs(float(rm.equity_usd.iloc[-1])/INITIAL-1-r["net_return_pct"]/100)<1e-9
    if period in ("2024","2025") and not stress and path=="O-H-L-C":
        assert abs(t["net_return_pct"]-{"2024":66.7746,"2025":51.2151}[period])<.015
    rows=[];monthly=[]
    for w in weights:
        # Static initial capital allocation. Independent NAVs scaled by weights;
        # no resetting capital monthly and no retrospective capital transfers.
        eq=(1-w)*tm.equity_usd.to_numpy(float)+w*rm.equity_usd.to_numpy(float)
        ret=100*(eq/np.r_[INITIAL,eq[:-1]]-1)
        assert np.all(eq>0)
        # Portfolio peak <= sum of sleeve peaks. At any time sleeve equity >=
        # (1-DD_sleeve)*its own peak, hence portfolio DD <= max active sleeve DD.
        # This is a conservative upper bound, NOT measured portfolio intraminute DD.
        bound=max(([t["max_floating_drawdown_pct"]] if w<1 else [])+([r["max_floating_drawdown_pct"]] if w>0 else []))
        half=pd.Series(ret).groupby([x[:4]+("H1" if int(x[5:])<=6 else "H2") for x in tm.month_ist])
        halfret=half.apply(lambda x:100*(np.prod(1+x/100)-1))
        rows.append(dict(period=period,path=path,stress=stress,mr_weight=w,net=100*(eq[-1]/INITIAL-1),profitable_months=int((ret>0).sum()),dd_bound=bound,trend_trades=t["trades"] if w<1 else 0,mr_trades=r["trades"] if w>0 else 0,worst_half=float(halfret.min()),trend_return=t["net_return_pct"],mr_return=r["net_return_pct"],trend_dd=t["max_floating_drawdown_pct"],mr_dd=r["max_floating_drawdown_pct"]))
        for k,mon in enumerate(tm.month_ist):
            monthly.append(dict(period=period,path=path,stress=stress,mr_weight=w,month_ist=mon,equity=eq[k],return_pct=ret[k]))
    return rows,monthly
def train():
    i=int(os.environ["SHARD_INDEX"]);path=core.base.PATHS[i//2];stress=bool(i%2)
    rows=[];monthly=[]
    for period in ("2024","2025"):
        a,b=evaluate(period,path,stress,WEIGHTS);rows+=a;monthly+=b
    p=OUT/f"shard_{i}";p.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(p/"training.csv",index=False)
    pd.DataFrame(monthly).to_csv(p/"monthly.csv",index=False)
def freeze():
    s=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"training.csv") for i in range(4)],ignore_index=True)
    m=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"monthly.csv") for i in range(4)],ignore_index=True)
    assert len(s)==40 and not s.duplicated(["period","path","stress","mr_weight"]).any()
    s.to_csv(OUT/"training.csv",index=False);m.to_csv(OUT/"monthly.csv",index=False)
    a=s.groupby("mr_weight").agg(worst_return=("net","min"),max_dd_bound=("dd_bound","max"),worst_half=("worst_half","min")).reset_index()
    counts=s.groupby(["mr_weight","period"]).profitable_months.min().unstack()
    a["months24"]=a.mr_weight.map(counts[2024]);a["months25"]=a.mr_weight.map(counts[2025])
    a["months"]=a.months24+a.months25
    # Fixed allocation neighborhood stability, chronological choice by 2024 only.
    y=s[s.period==2024].groupby("mr_weight").agg(net=("net","min"),dd=("dd_bound","max"))
    choice=float((y.net-.05*y.dd).loc[[.25,.5,.75]].idxmax())
    a["chronological_selected"]=a.mr_weight==choice
    aa=a.set_index("mr_weight")
    def stable(w):
        z=aa.loc[w];neighbors=[v for v in WEIGHTS if abs(v-w)==.25]
        return float(np.mean([aa.loc[v,"worst_return"]>=.8*z.worst_return and aa.loc[v,"months"]>=z.months-2 and aa.loc[v,"worst_half"]>0 for v in neighbors]))
    a["neighbor_stability"]=a.mr_weight.map(stable)
    a["eligible"]=a.mr_weight.isin([.25,.5,.75])&a.chronological_selected&(a.months24>=9)&(a.months25>=11)&(a.worst_return>=52.0497)&(a.max_dd_bound<=10.651)&(a.worst_half>0)&(a.neighbor_stability>=.5)
    a=a.sort_values(["eligible","worst_return"],ascending=False)
    a.to_csv(OUT/"training_ranked.csv",index=False)
    f=dict(passes_training_gate=bool(a.eligible.any()),selected_weight=choice,prior_2026_exposure=True,training_sha256=hashlib.sha256((OUT/"training.csv").read_bytes()).hexdigest())
    (OUT/"FROZEN.json").write_text(json.dumps(f,indent=2)+"\n")
def validate():
    f=json.loads((OUT/"FROZEN.json").read_text())
    assert hashlib.sha256((OUT/"training.csv").read_bytes()).hexdigest()==f["training_sha256"]
    if not f["passes_training_gate"]:
        (OUT/"REPORT.md").write_text("No allocation passed training gate; 2026 not replayed. Static sleeves, conservative drawdown bound, funding excluded.\n")
        return
    rows=[];monthly=[]
    for path in core.base.PATHS:
        for stress in (False,True):
            a,b=evaluate("2026",path,stress,[f["selected_weight"]]);rows+=a;monthly+=b
    pd.DataFrame(rows).to_csv(OUT/"validation.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"validation_monthly.csv",index=False)
    (OUT/"REPORT.md").write_text("Frozen allocation tested on historically exposed 2026 only. No tuning. Static sleeves, conservative drawdown bound, funding excluded.\n")
if __name__=="__main__":
    {"train":train,"freeze":freeze,"validate":validate}[sys.argv[1]]()
