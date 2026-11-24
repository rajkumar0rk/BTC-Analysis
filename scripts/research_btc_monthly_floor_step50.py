#!/usr/bin/env python3
"""Step50: merge Step48 and Step49, then chain monotone recovery overlays.
Historical optimization only. Fees: same as Step36; real funding and fills not modeled.
"""
from pathlib import Path
from itertools import product
import json
import numpy as np
import pandas as pd
import research_btc_one_percent_monthly_floor_step36 as s
OUT=Path("analysis/btc_monthly_floor_step50")
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
    # Exact Step47 parity: use the Step45-specific profit policy when applying its delayed entry.
    mt=1.
    for i in index:
        if i and mi[i]!=mi[i-1]:mt=1.
        if mask[i] and side[i]<0 and day[i]>=15 and mt-1<.0025:
            original[i]=delayed10[(int(fade[i]),bool(peak[i]),caps[i])][0][i,eid[i],:]
        mt*=1+original[i,offer]
    baseline=original[:,offer].copy()
    bn,bd,bm=score(baseline)
    assert abs(bn*100-39.181497338722046)<.0002,(bn,bd,bm)
    assert abs(bd*100-2.506675539988501)<.0002
    floor=bm.copy();max_dd=bd
    print("STEP50_STEP47_PARITY",bn*100,bd*100,bm*100,flush=True)
    # Replay the two frozen Step48 overlays and the alternate Step49 overlay.
    c15=s.previous.raw_cache(m,mask,idx+15,cfg,features,policies)[0]
    c5=s.previous.raw_cache(m,mask,idx+5,cfg,features,policies)[0]
    original47=original.copy()
    def add_rule(path,alternative,cond,wait,target,pace):
        out=path.copy();mt=1.
        for i in index:
            if i and mi[i]!=mi[i-1]:mt=1.
            if cond[i] and day[i]>=wait and mt-1<target*(min(day[i]/20,1) if pace else 1):
                out[i]=alternative[i]
            mt*=1+out[i,offer]
        return out
    a15=np.array([c15[(int(side[i]),bool(peak[i]),caps[i])][0][i,0,:] for i in index])
    stage2=add_rule(original47,a15,mask&fs["r5_opposed"],15,.005,False)
    assert abs(score(stage2[:,offer])[0]*100-39.9563927711833)<.0002
    a5=np.array([c5[(int(fade[i]),bool(peak[i]),caps[i])][0][i,0,:] for i in index])
    p48=add_rule(stage2,a5,(~mask)&fs["range60_low"],15,.005,True)
    n48,d48,m48=score(p48[:,offer])
    assert abs(n48*100-40.56492198244022)<.0002
    j=idx+15
    last5=cl[j-1]/cl[j-6]-1
    five=np.where(last5==0,side,np.sign(last5)).astype(int)
    a49first=np.array([c15[(int(-five[i]),bool(peak[i]),caps[i])][0][i,0,:] for i in index])
    p49first=add_rule(original47,a49first,mask&fs["r5_opposed"],15,.005,False)
    assert abs(score(p49first[:,offer])[0]*100-39.9563927711833)<.0002
    a49=np.array([c15[(int(-five[i]),bool(peak[i]),.15 if caps[i] is None else min(.15,caps[i]))][0][i,labels.index("hard_timeout_20m"),:] for i in index])
    p49=add_rule(p49first,a49,fs["rvol175_high"],15,.005,False)
    n49,d49,m49=score(p49[:,offer])
    assert abs(n49*100-40.701128784929395)<.0002
    print("STEP50_PARITY",n48*100,n49*100,flush=True)
    original=p48.copy()
    baseline=original[:,offer].copy()
    bn,bd,bm=score(baseline)
    floor=np.maximum(m48,m49);max_dd=min(d48,d49)
    # Candidate per-day paths are actual newly evaluated OHLC fills, not ledger switching.
    candidates=[a49,p49];params=[(.15,"frozen_step49_exit"),(None,"frozen_step49_path")]
    # Delay is committed at original signal; all features and side selection
    # use data available at that signal, never prices inside the delay.
    exits=[-1,0,labels.index("hard_timeout_10m"),labels.index("hard_timeout_20m"),
           labels.index("new_profit_0.06_4"),labels.index("new_profit_0.12_6"),
           labels.index("new_adverse_0.06_4"),labels.index("new_timeout_8m")]
    op=m.open.to_numpy(float)
    for delay in (1,2,3,5,8,10,12,15,18,20,25):
        j=idx+delay
        # Entry at open j; use only completed bars strictly before j.
        change=cl[j-1]/op[idx]-1
        last2=cl[j-1]/cl[j-3]-1
        last5=cl[j-1]/cl[j-6]-1
        up=np.where(change==0,side,np.sign(change)).astype(int)
        two=np.where(last2==0,side,np.sign(last2)).astype(int)
        five=np.where(last5==0,side,np.sign(last5)).astype(int)
        choices={"follow_delay":up,"fade_delay":-up,"follow_last2":two,"fade_last2":-two,
                 "follow_last5":five,"fade_last5":-five,
                 "flip_if_adverse_005":np.where(side*change<-.0005,-side,side),
                 "flip_if_adverse_010":np.where(side*change<-.001,-side,side)}
        delayed=delayed10 if delay==10 else s.previous.raw_cache(m,mask,j,cfg,features,policies)[0]
        for (direction,ss),cap,p in product(choices.items(),(None,.15,.25),exits):
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
    # All gates use pre-entry signals or previously completed shadow trades.
    for k in ("r240_aligned","r240_opposed","abs5_high","abs5_low","abs60_high","abs60_low","rvol125_high","rvol125_low","outer_quartile","middle_half"):
        contexts[k]=np.asarray(fs[k],bool)
    for k in ("r5_aligned","r5_opposed","range60_high","range60_low","rvol175_high","rvol175_low"):
        contexts["fallback_"+k]=mask&fs[k]
        contexts["event_"+k]=(~mask)&fs[k]
    contexts["fallback_short_late"]=mask&(side<0)&(day>=12)
    contexts["fallback_long_late"]=mask&(side>0)&(day>=12)
    initial=original.copy()
    results=[]
    tested=0
    for stage in range(1,5):
        baseline=original[:,offer].copy()
        bn,bd,bm=score(baseline)
        for l in (2,3,5,10):
            contexts["last"+str(l)+"loss"]=lag(baseline,l)<0
            contexts["last"+str(l)+"gain"]=lag(baseline,l)>0
        models=list(product(range(len(cand)),list(contexts),(0,5,10,15),(.0025,.005,.0075,.01),("fixed","pace")))
        best=None;bestkey=None
        qualified=0
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
            lower=(mo<bm-1e-10).sum(1)
            joint=(mo<floor-1e-10).sum(1)
            cnt=(mo>=.01).sum(1); sf=np.maximum(.01-mo,0).sum(1)
            deficit=np.maximum(floor-mo,0).sum(1)
            eligible=np.flatnonzero((lower==0)&(dd<=max_dd+1e-9)&(eq>1+bn+1e-9))
            qualified+=len(eligible)
            for j in eligible:
                p=ps[j]
                key=(-int(joint[j]),-deficit[j],int(cnt[j]),-sf[j],mo[j].min(),eq[j])
                if bestkey is None or key>bestkey:
                    bestkey=key
                    row=dict(stage=stage,cap=params[p[0]][0],exit=params[p[0]][1],context=p[1],
                             wait=p[2],target=p[3],gate=p[4],net_pct=(eq[j]-1)*100,dd_pct=dd[j]*100,
                             months_ge1=int(cnt[j]),positive=int((mo[j]>0).sum()),lower=int(lower[j]),
                             joint_lower=int(joint[j]),shortfall_pp=sf[j]*100,worst_month_pct=mo[j].min()*100,
                             **dict(zip(months,mo[j]*100)))
                    best=(row,p,used[j].copy())
        tested+=len(models)
        print("STEP50_STAGE_TESTED",stage,len(models),qualified,flush=True)
        if best is None:break
        row,p,used=best
        original=np.where(used[:,None],cand[p[0]],original)
        check=score(original[:,offer])
        assert abs(check[0]*100-row["net_pct"])<1e-8
        assert np.all(check[2]>=bm-1e-10)
        row["standard_fee_net_pct"]=float((np.prod(1+original[:,std])-1)*100)
        row["trade_count"]=n
        row["tested_cumulative"]=tested
        results.append(row)
        print("STEP50_STAGE_BEST",json.dumps(row,default=str),flush=True)
        pd.DataFrame(results).to_csv(OUT/"accepted_stages.csv",index=False)
        pd.DataFrame(dict(day_ist=s.base.IST_DAYS,month=s.MONTHS,baseline_pct=initial[:,offer]*100,
                           net_pct=original[:,offer]*100,standard_net_pct=original[:,std]*100)).to_csv(OUT/"best_daily.csv",index=False)
        (OUT/"summary.json").write_text(json.dumps(dict(tested=tested,stages=results),indent=2,default=str))
    print("STEP50_COMPLETE",json.dumps(dict(tested=tested,stages=results),default=str),flush=True)
if __name__=="__main__":main()
