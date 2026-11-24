#!/usr/bin/env python3
"""Step52: frozen Step51 regression and finer causal recovery search.
Historical optimization only. Fees: same as Step36; real funding and fills not modeled.
"""
from pathlib import Path
from itertools import product, islice
import json
import numpy as np
import pandas as pd
import research_btc_one_percent_monthly_floor_step36 as s
OUT=Path("analysis/btc_step52_risk_validation")
import os
from step52_validation_engine import tag_cache, risk_features_prior_close
from step52_dynamic_risk_engine import Risk
def build_baseline(mode,slip):
    OUT.mkdir(parents=True,exist_ok=True)
    strict=True
    if strict:
        s.previous.step25.risk.preentry_features=risk_features_prior_close
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
    risk=Risk(m,float(slip),mode,float(s.base.COST))
    cache,_=s.previous.raw_cache(m,mask,idx,cfg,features,policies)
    cache=risk.reprice(cache,idx)
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
    # Tag every replay result with its order specification. Subsequent frozen
    # selectors carry the specification, not just the return, to the ledger.
    raw_cache=s.previous.raw_cache
    def tagged_raw(m,mask,starts,cfg,features,policies):
        c,stops=raw_cache(m,mask,starts,cfg,features,policies)
        return tag_cache(risk.reprice(c,starts),starts),stops
    cache=tag_cache(cache,idx)
    s.previous.raw_cache=tagged_raw
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
    if not strict: assert abs(bn*100-36.612862)<.0002,(bn,bd,bm)
    if not strict: assert abs(bd*100-2.506676)<.0002
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
    if not strict: assert abs(bn*100-37.613286294736255)<.0002,(bn,bd,bm)
    if not strict: assert abs(bd*100-2.5066755399884566)<.0002
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
    if not strict: assert abs(n46*100-38.60599952841175)<.0002
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
    if not strict: assert abs(bn*100-38.184662318874075)<.0002
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
    if not strict: assert abs(bn*100-39.181497338722046)<.0002,(bn,bd,bm)
    if not strict: assert abs(bd*100-2.506675539988501)<.0002
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
    if not strict: assert abs(score(stage2[:,offer])[0]*100-39.9563927711833)<.0002
    a5=np.array([c5[(int(fade[i]),bool(peak[i]),caps[i])][0][i,0,:] for i in index])
    p48=add_rule(stage2,a5,(~mask)&fs["range60_low"],15,.005,True)
    n48,d48,m48=score(p48[:,offer])
    if not strict: assert abs(n48*100-40.56492198244022)<.0002
    j=idx+15
    last5=cl[j-1]/cl[j-6]-1
    five=np.where(last5==0,side,np.sign(last5)).astype(int)
    a49first=np.array([c15[(int(-five[i]),bool(peak[i]),caps[i])][0][i,0,:] for i in index])
    p49first=add_rule(original47,a49first,mask&fs["r5_opposed"],15,.005,False)
    if not strict: assert abs(score(p49first[:,offer])[0]*100-39.9563927711833)<.0002
    a49=np.array([c15[(int(-five[i]),bool(peak[i]),.15 if caps[i] is None else min(.15,caps[i]))][0][i,labels.index("hard_timeout_20m"),:] for i in index])
    p49=add_rule(p49first,a49,fs["rvol175_high"],15,.005,False)
    n49,d49,m49=score(p49[:,offer])
    if not strict: assert abs(n49*100-40.701128784929395)<.0002
    print("STEP50_PARITY",n48*100,n49*100,flush=True)
    original=p48.copy()
    baseline=original[:,offer].copy()
    bn,bd,bm=score(baseline)
    floor=np.maximum(m48,m49);max_dd=min(d48,d49)
    # Reproduce all four Step50 accepted rules before testing anything new.
    p50=add_rule(p48,p49,fs["range60_high"],0,.0075,False)
    if not strict: assert abs(score(p50[:,offer])[0]*100-41.43473491902474)<.0002
    j=idx+10
    last2=cl[j-1]/cl[j-3]-1
    two=np.where(last2==0,side,np.sign(last2)).astype(int)
    a50b=np.array([delayed10[(int(two[i]),bool(peak[i]),caps[i])][0][i,eid[i],:] for i in index])
    p50=add_rule(p50,a50b,mask&(side<0),15,.0075,True)
    if not strict: assert abs(score(p50[:,offer])[0]*100-42.31541091520996)<.0002
    op=m.open.to_numpy(float)
    def delayed_fade(delay,policy):
        jj=idx+delay
        change=cl[jj-1]/op[idx]-1
        ss=-np.where(change==0,side,np.sign(change)).astype(int)
        cc=c15 if delay==15 else s.previous.raw_cache(m,mask,jj,cfg,features,policies)[0]
        return np.array([cc[(int(ss[i]),bool(peak[i]),caps[i])][0][i,policy,:] for i in index])
    a50c=delayed_fade(20,labels.index("new_profit_0.12_6"))
    p50=add_rule(p50,a50c,(~mask)&fs["rvol175_low"],10,.0025,True)
    if not strict: assert abs(score(p50[:,offer])[0]*100-44.483847889155534)<.0002
    a50d=delayed_fade(15,0)
    p50=add_rule(p50,a50d,fs["r5_aligned"],15,.0025,False)
    n50,d50,m50=score(p50[:,offer])
    if not strict: assert abs(n50*100-46.228217440403775)<.0002,(n50,d50,m50)
    if not strict: assert abs(d50*100-2.506675539988479)<.0002
    print("STEP51_STEP50_PARITY",n50*100,d50*100,m50*100,flush=True)
    original=p50.copy()
    baseline=original[:,offer].copy()
    floor=m50.copy();max_dd=d50
    # Reproduce all accepted Step51 overlays with the original pre-entry features.
    def candidate(delay,kind,policy,cap=None):
        j=idx+delay
        if kind=="fade_delay":
            assert delay>0
            ret=cl[j-1]/op[idx]-1
        elif kind.endswith("last2"):
            ret=cl[j-1]/cl[j-3]-1
        elif kind.endswith("last5"):
            ret=cl[j-1]/cl[j-6]-1
        elif kind.endswith("last10"):
            ret=cl[j-1]/cl[j-11]-1
        else:raise KeyError(kind)
        ss=np.where(ret==0,side,np.sign(ret)).astype(int)
        if kind.startswith("fade"):ss=-ss
        cc=cache if delay==0 else c5 if delay==5 else s.previous.raw_cache(m,mask,j,cfg,features,policies)[0]
        out=[]
        for i in index:
            c=caps[i] if cap is None else cap if caps[i] is None else min(cap,caps[i])
            out.append(cc[(int(ss[i]),bool(peak[i]),c)][0][i,eid[i] if policy<0 else policy,:])
        return np.array(out)
    a51a=candidate(5,"fade_last2",labels.index("new_timeout_12m"))
    p51=add_rule(p50,a51a,(~mask)&fs["range60_high"],15,.0075,True)
    if not strict: assert abs(score(p51[:,offer])[0]*100-47.36958914125171)<.0002
    a51b=candidate(20,"fade_delay",labels.index("hard_timeout_10m"))
    p51=add_rule(p51,a51b,mask&fs["rvol175_high"],15,.0125,False)
    if not strict: assert abs(score(p51[:,offer])[0]*100-48.03073934989817)<.0002
    a51c=candidate(0,"fade_last5",labels.index("new_timeout_8m"))
    p51=add_rule(p51,a51c,(~mask)&fs["range60_high"],15,.0075,False)
    if not strict: assert abs(score(p51[:,offer])[0]*100-50.62267871444348)<.0002
    a51d=candidate(0,"follow_last2",0)
    p51=add_rule(p51,a51d,mask&fs["rvol175_high"],0,.0025,False)
    n51,d51,m51=score(p51[:,offer])
    if not strict: assert abs(n51*100-51.364585916310965)<.0002,(n51,d51,m51)
    if not strict: assert abs(d51*100-2.5066755399884677)<.0002
    if not strict: assert np.sum(m51>=.01)==21
    print("STEP52_STEP51_PARITY",n51*100,d51*100,m51*100,flush=True)
    original=p51.copy()
    baseline=original[:,offer].copy()
    floor=m51.copy();max_dd=d51
    # Exact frozen Step52 selected rule, without any parameter search.
    a52=candidate(24,"fade_last10",labels.index("new_adverse_0.06_4"))
    p52=add_rule(p51,a52,(~mask)&(features["rvol5"]<2.0),10,0.,False)
    net,dd,mo=score(p52[:,offer])
    if not strict:
        assert abs(net*100-53.29360135227979)<.0002
        if not strict: assert abs(dd*100-2.506675539988479)<.0002
        assert int((mo>=.01).sum())==22
    print("FROZEN_STEP52",json.dumps(dict(strict_preentry=strict,net_pct=net*100,dd_pct=dd*100,months_ge1=int((mo>=.01).sum()),monthly=dict(zip(months,mo*100)))),flush=True)
    s.previous.raw_cache=raw_cache
    return p52,m,idx,cfg,mask,features,ridge,mi,day,risk,policies
