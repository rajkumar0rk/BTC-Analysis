#!/usr/bin/env python3
"""Step47: merge Step45 and Step46 recovery rules with joint monthly floor.
Historical optimization only. Fees: same as Step36; real funding and fills not modeled.
"""
from pathlib import Path
from itertools import product
import json
import numpy as np
import pandas as pd
import research_btc_one_percent_monthly_floor_step36 as s
OUT=Path("analysis/btc_monthly_floor_step47")
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,orig,hours,idx,cfg=s.step13.create_path()
    oldpol,names=s.early.build_exit_policies()
    ids={n:i for i,n in enumerate(names)}
    features,ridge=s.previous.all_features_and_sides(m,mask,idx,orig,cfg,oldpol)
    extra=[(0,0.,0.,float(h)) for h in (2,4,6,8,12,18,22,28)]
    extra_names=[f"new_timeout_{h}m" for h in (2,4,6,8,12,18,22,28)]
    for t in (2,4,6,12):
        for v in (.03,.06,.10,.16):
            extra.append((1,v,float(t),30.))
            extra_names.append(f"new_adverse_{v}_{t}")
        for v in (.06,.12,.25):
            extra.append((3,v,float(t),30.))
            extra_names.append(f"new_profit_{v}_{t}")
    policies=np.vstack((oldpol,np.array(extra)))
    labels=names+extra_names
    cache,_=s.previous.raw_cache(m,mask,idx,cfg,features,policies)
    fs=s.s31.filters(features,ridge);middle=fs["middle_half"]
    cl=m.close.to_numpy(float);hi=m.high.to_numpy(float);lo=m.low.to_numpy(float)
    width=np.asarray([(hi[i-60:i].max()-lo[i-60:i].min())/cl[i-1] for i in idx])
    locked=(.005,False,5,"event","fade5",None,None,fs["range60_high"],fs["none"])
    settings=[(False,15,"event","none","r5_aligned"),None,
              (True,10,"event","none","range60_low"),
              (False,10,"event","none","rvol175_low"),
              (False,5,"event","rvol175_high","r5_aligned")]
    def calc(k):
        o=[locked]
        if k is not None:
            pace,wait,scope,sidef,exitf=k
            o.append((.01,pace,wait,scope,"fade5",None,ids["hard_timeout_20m"],fs[sidef],fs[exitf]))
        return s.simulate(("fallback_month_cumulative_below025","invert_high_rvol",.20,"base"),
                         cache,mask,ridge,features,ids,middle,middle,.5,.75,
                         "last_two_negative",width>=.005,.25,None,o)
    shadows=[calc(k) for k in settings]
    offer=s.base.MODES.index("scalper_offer")
    std=s.base.MODES.index("standard")
    r=np.stack([x["pnl"][offer] for x in shadows],axis=1)
    n=len(r); assert n==477
    months,mi=np.unique(s.MONTHS,return_inverse=True)
    day=np.array([np.sum(mi[:i]==mi[i]) for i in range(n)])
    assert len(months)==22
    index=np.arange(n)
    def path(sel):return r[index,sel]
    def lag(z,l):return np.array([np.prod(1+z[max(0,i-l):i])-1 for i in index])
    def overlay(sel,which,cond,wait,threshold):
        out=sel.copy();mt=1.
        for i in index:
            if i and mi[i]!=mi[i-1]:mt=1.
            if cond[i] and day[i]>=wait and mt-1<threshold:out[i]=which
            mt*=1+r[i,out[i]]
        return out
    z=np.zeros(n,dtype=int)
    z=overlay(z,3,lag(r[:,0],1)>0,0,.005)
    z=overlay(z,2,(lag(r[:,0],10)<0)&(ridge>0),0,.005)
    z=overlay(z,2,ridge<0,16,.004)
    z=overlay(z,3,(lag(r[:,0],10)>0)&(ridge>0),0,.0075)
    z=overlay(z,4,(lag(path(z),5)>0)&(ridge<0),0,-.0025)
    baseline=path(z)
    def score(y):
        eq=np.cumprod(1+y); dd=np.max(1-eq/np.maximum.accumulate(np.r_[1,eq])[1:])
        mo=np.array([np.prod(1+y[mi==j])-1 for j in range(22)])
        return eq[-1]-1,dd,mo
    bn,bd,bm=score(baseline)
    assert abs(bn*100-36.612862)<.0002,(bn,bd,bm)
    assert abs(bd*100-2.506676)<.0002
    print("STEP43_PARITY",bn*100,bd*100,bm*100,flush=True)
    side=np.array([shadows[z[i]]["side"][i] for i in index])
    peak=np.array([shadows[z[i]]["highwater_guard"][i] for i in index])
    eid=np.array([shadows[z[i]]["policy"][i] for i in index])
    caps=[]
    for i in index:
        a=shadows[z[i]]
        cap=.20 if a["fallback_loss_trigger"][i] and middle[i] and 1+a["fallback_mtd"][i]<=.9925 else None
        if a["event_active"][i]:cap=.25
        caps.append(cap)
    original=np.array([cache[(int(side[i]),bool(peak[i]),caps[i])][0][i,eid[i],:] for i in index])
    assert np.allclose(original[:,offer],baseline,atol=1e-12,rtol=0)
    # Freeze Step44 first overlay; the gate uses its own completed realized returns.
    p44=labels.index("new_profit_0.06_4")
    mt=1.
    for i in index:
        if i and mi[i]!=mi[i-1]:mt=1.
        if fs["rvol175_high"][i] and day[i]>=15 and mt-1<.005:
            eid[i]=p44
            original[i]=cache[(int(side[i]),bool(peak[i]),caps[i])][0][i,eid[i],:]
        mt*=1+original[i,offer]
    baseline=original[:,offer].copy()
    bn,bd,bm=score(baseline)
    assert abs(bn*100-37.613286294736255)<.0002,(bn,bd,bm)
    assert abs(bd*100-2.5066755399884566)<.0002
    print("STEP46_STEP44_PARITY",bn*100,bd*100,bm*100,flush=True)
    # Reproduce Step46 independently before combining, including its original MTD gate.
    delayed10=s.previous.raw_cache(m,mask,idx+10,cfg,features,policies)[0]
    fade=np.where(features["r5"]==0,side,-np.sign(features["r5"])).astype(int)
    p46=original.copy();mt=1.
    for i in index:
        if i and mi[i]!=mi[i-1]:mt=1.
        if mask[i] and side[i]<0 and day[i]>=15 and mt-1<.0025:
            p46[i]=delayed10[(int(fade[i]),bool(peak[i]),caps[i])][0][i,eid[i],:]
        mt*=1+p46[i,offer]
    n46,d46,m46=score(p46[:,offer])
    assert abs(n46*100-38.60599952841175)<.0002
    print("STEP47_STEP46_PARITY",n46*100,d46*100,m46*100,flush=True)
    # Freeze Step45's fallback profit-close overlay on the Step44 path.
    p45=labels.index("profit_close_at_0.1pct_after_20m")
    mt=1.
    for i in index:
        if i and mi[i]!=mi[i-1]:mt=1.
        if mask[i] and mt-1<.01*min(day[i]/20,1):
            eid[i]=p45
            original[i]=cache[(int(side[i]),bool(peak[i]),caps[i])][0][i,eid[i],:]
        mt*=1+original[i,offer]
    baseline=original[:,offer].copy()
    bn,bd,bm=score(baseline)
    assert abs(bn*100-38.184662318874075)<.0002
    print("STEP47_STEP45_PARITY",bn*100,bd*100,bm*100,flush=True)
    # The acceptance floor is the better monthly return of either historical candidate.
    floor=np.maximum(bm,m46)
    min_net=max(bn,n46)
    max_dd=min(bd,d46)
    print("STEP47_JOINT_FLOOR",floor*100,flush=True)
    # Candidate per-day paths are actual newly evaluated OHLC fills, not ledger switching.
    candidates=[];params=[]
    # Delay is committed at original signal; all features and side selection
    # use data available at that signal, never prices inside the delay.
    choices={"keep":side,"invert":-side,
             "follow60":np.where(features["r60"]==0,side,np.sign(features["r60"])).astype(int),
             "fade5":np.where(features["r5"]==0,side,-np.sign(features["r5"])).astype(int)}
    exits=[-1,0,labels.index("hard_timeout_10m"),labels.index("hard_timeout_20m"),
           labels.index("new_profit_0.06_4"),labels.index("new_profit_0.12_6"),
           labels.index("new_adverse_0.06_4"),labels.index("new_timeout_8m")]
    for delay in (0,2,5,10):
        delayed=cache if delay==0 else delayed10 if delay==10 else s.previous.raw_cache(m,mask,idx+delay,cfg,features,policies)[0]
        for (direction,ss),cap,p in product(choices.items(),(None,.15,.25),exits):
            if delay==0 and direction=="keep" and cap is None and p==-1:continue
            arr=np.empty((n,len(s.base.MODES)))
            for i in index:
                c=caps[i] if cap is None else cap if caps[i] is None else min(caps[i],cap)
                arr[i]=delayed[(int(ss[i]),bool(peak[i]),c)][0][i,eid[i] if p==-1 else p,:]
            if np.allclose(arr[:,offer],baseline,atol=1e-12,rtol=0):continue
            candidates.append(arr)
            params.append((cap,f"delay{delay}m__{direction}__"+("original" if p==-1 else labels[p])))
        del delayed
    cand=np.array(candidates)
    contexts={"both":np.ones(n,bool),"event":~mask,"fallback":mask,"long":side>0,"short":side<0}
    for key in ("r5_aligned","r5_opposed","r60_aligned","r60_opposed","range60_high","range60_low","rvol175_high","rvol175_low"):
        contexts[key]=np.asarray(fs[key],bool)
    for key,l in (("last3loss",3),("last5loss",5),("last10loss",10)):
        contexts[key]=lag(baseline,l)<0
    contexts.update({"early_month":day<7,"late_month":day>=14,"event_long":(~mask)&(side>0),"event_short":(~mask)&(side<0),"fallback_long":mask&(side>0),"fallback_short":mask&(side<0)})
    models=list(product(range(len(cand)),list(contexts),(0,5,10,15),(.0025,.005,.0075,.01),("fixed","pace")))
    print("STEP47_CONFIGS",len(models),flush=True)
    records=[];best=None;bestkey=None;best45=None;best45key=None
    for start in range(0,len(models),4000):
        ps=models[start:start+4000]; nn=len(ps)
        jj=np.array([p[0] for p in ps]); cx=np.array([contexts[p[1]] for p in ps])
        wait=np.array([p[2] for p in ps]); target=np.array([p[3] for p in ps]); pace=np.array([p[4]=="pace" for p in ps])
        eq=np.ones(nn);peak_eq=np.ones(nn);dd=np.zeros(nn);mt=np.ones(nn);mo=np.empty((nn,22))
        used=np.zeros((nn,n),bool)
        for i in index:
            if i and mi[i]!=mi[i-1]:mo[:,mi[i-1]]=mt-1;mt.fill(1.)
            gate=cx[:,i]&(day[i]>=wait)&(mt-1<target*np.where(pace,min(day[i]/20,1),1))
            used[:,i]=gate
            y=np.where(gate,cand[jj,i,offer],baseline[i])
            eq*=1+y;mt*=1+y;peak_eq=np.maximum(peak_eq,eq);dd=np.maximum(dd,1-eq/peak_eq)
        mo[:,-1]=mt-1
        lower=(mo<floor-1e-10).sum(1); lower45=(mo<bm-1e-10).sum(1); cnt=(mo>=.01).sum(1); sf=np.maximum(.01-mo,0).sum(1)
        for j,p in enumerate(ps):
            row=dict(cap=params[p[0]][0],exit=params[p[0]][1],context=p[1],wait=p[2],target=p[3],gate=p[4],
                     net_pct=(eq[j]-1)*100,dd_pct=dd[j]*100,months_ge1=int(cnt[j]),positive=int((mo[j]>0).sum()),
                     lower=int(lower[j]),lower_vs45=int(lower45[j]),shortfall_pp=sf[j]*100,worst_month_pct=mo[j].min()*100,
                     **dict(zip(months,mo[j]*100)))
            records.append(row)
            key=(int(cnt[j]),-sf[j],mo[j].min(),eq[j])
            if lower45[j]==0 and dd[j]<=bd+1e-9 and eq[j]>=1+bn-1e-10 and (best45key is None or key>best45key):
                best45key=key;best45=(row,p,used[j].copy())
            if lower[j]==0 and dd[j]<=max_dd+1e-9 and eq[j]>=1+min_net-1e-10 and (bestkey is None or key>bestkey):
                bestkey=key;best=(row,p,used[j].copy())
    grid=pd.DataFrame(records);grid.to_csv(OUT/"all_candidates.csv",index=False)
    print("STEP47_STRICT",len(grid[(grid.lower==0)&(grid.dd_pct<=bd*100+1e-7)]),flush=True)
    joint=best is not None
    if best is None:best=best45
    if best:
        row,p,used=best
        row["joint_floor_pass"]=joint
        selected=np.where(used[:,None],cand[p[0]],original)
        daily=pd.DataFrame(dict(day_ist=s.base.IST_DAYS,month=s.MONTHS,baseline_pct=baseline*100,
                                net_pct=selected[:,offer]*100,standard_net_pct=selected[:,std]*100,overlay=used))
        daily.to_csv(OUT/"best_daily.csv",index=False)
        row["standard_fee_net_pct"]=float((np.prod(1+selected[:,std])-1)*100)
        row["trade_count"]=n;row["candidates"]=len(models)
        print("STEP47_BEST",json.dumps(row,default=str),flush=True)
        (OUT/"summary.json").write_text(json.dumps(row,indent=2,default=str))
    else:
        (OUT/"summary.json").write_text(json.dumps(dict(status="no strict improvement",candidates=len(models),baseline_net_pct=bn*100,baseline_dd_pct=bd*100,baseline_months=dict(zip(months,bm*100))),default=str))
if __name__=="__main__":main()
