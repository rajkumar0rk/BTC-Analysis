#!/usr/bin/env python3
"""Step59: frozen Step58 parity; complementary recovery pairs.
Identical added rule across scenarios, own prior-day state per scenario.
No month identity gates. No regressions in ANY scenario/month or mark DD.
Historical optimization only; no real settlement or demo evidence.
"""
from pathlib import Path
from itertools import product
import json
import numpy as np
import pandas as pd
from numba import njit
from step56_baseline import build_baseline
from step52_dynamic_risk_engine import Risk
from step52_validation_engine import replay_one
import research_btc_one_percent_monthly_floor_step36 as s

OUT=Path("analysis/btc_step59_paired_recovery")
SC=[("historical",5),("historical",20),("standard",20),("conservative",5),
    ("conservative",20),("offer30",5),("offer30",20),("offer30",50),
    ("standard",100),("standard",200)]
NPRIMARY=7

@njit
def metrics(path,mi):
    n,k,_=path.shape
    eq=np.ones(k);peak=np.ones(k);dd=np.zeros(k)
    mp=np.ones(k);md=np.zeros(k);mo=np.ones((22,k))
    for i in range(n):
        for j in range(k):
            r,a,f=path[i,j]
            mp[j]=max(mp[j],eq[j]*(1+f))
            md[j]=max(md[j],1-eq[j]*(1+a)/mp[j])
            eq[j]*=1+r;mo[mi[i],j]*=1+r
            peak[j]=max(peak[j],eq[j]);dd[j]=max(dd[j],1-eq[j]/peak[j])
            mp[j]=max(mp[j],eq[j]);md[j]=max(md[j],1-eq[j]/mp[j])
    return eq-1,dd,md,mo-1

@njit
def route(base,alt,cond,wait,threshold,pace,mi,day):
    n,k,_=base.shape
    out=base.copy();used=np.zeros((n,k),np.bool_)
    mt=np.ones(k)
    for i in range(n):
        if i and mi[i]!=mi[i-1]:mt[:]=1.
        if cond[i] and day[i]>=wait:
            t=threshold
            if pace:t*=min(day[i]/20.,1.)
            for j in range(k):
                if mt[j]-1<t:
                    out[i,j]=alt[i,j];used[i,j]=True
        for j in range(k):mt[j]*=1+out[i,j,0]
    return out,used

@njit
def evaluate(base,alt,cond,wait,threshold,pace,mi,day,floor,ddfloor,markfloor,netfloor):
    n,k,_=base.shape
    nets=np.empty(k);mdds=np.empty(k);dds=np.empty(k)
    mo=np.empty((22,k))
    # Screen primary historical first, then reject immediately when any
    # scenario/month falls below baseline, or any drawdown bound is breached.
    for j in range(k):
        eq=peak=mp=mt=1.;dd=md=0.
        for i in range(n):
            if i and mi[i]!=mi[i-1]:
                v=mt-1
                if v<floor[mi[i-1],j]-1e-9:return False,0.,0,0.
                mo[mi[i-1],j]=v;mt=1.
            t=threshold
            if pace:t*=min(day[i]/20.,1.)
            r,a,f=base[i,j]
            if cond[i] and day[i]>=wait and mt-1<t:
                r,a,f=alt[i,j]
            mp=max(mp,eq*(1+f))
            md=max(md,1-eq*(1+a)/mp)
            eq*=1+r;mt*=1+r
            peak=max(peak,eq);dd=max(dd,1-eq/peak)
            mp=max(mp,eq);md=max(md,1-eq/mp)
            if dd>ddfloor[j]+1e-9 or md>markfloor[j]+1e-9:return False,0.,0,0.
        if mt-1<floor[21,j]-1e-9:return False,0.,0,0.
        mo[21,j]=mt-1;nets[j]=eq-1;mdds[j]=md;dds[j]=dd
        if nets[j]<netfloor[j]-1e-9:return False,0.,0,0.
    improvement=np.sum(nets[:NPRIMARY]-netfloor[:NPRIMARY])
    if improvement<1e-8:return False,0.,0,0.
    # Every scenario improves or holds; prioritize deficits across all
    # primary scenarios and reduced drawdown over aggregate net return.
    gain=0.
    for j in range(NPRIMARY):
        # Reward recovery of negative and sub-1% months, especially the
        # historical-fee scenario. Reward reductions of excess mark DD.
        weight=2. if j==0 else 1.
        gain+=weight*(3.*(np.min(mo[:,j])-np.min(floor[:,j]))
            +2.*np.sum(np.minimum(mo[:,j],0.)-np.minimum(floor[:,j],0.))
            +np.sum(np.minimum(mo[:,j],.01)-np.minimum(floor[:,j],.01))
            +2.*(max(markfloor[j]-.02506676,0.)-max(mdds[j]-.02506676,0.)))
    cnt=np.sum(mo[:,:NPRIMARY]>=.01)
    return True,gain,cnt,improvement+np.sum(markfloor[:NPRIMARY]-mdds[:NPRIMARY])

@njit
def search(base,candidates,contexts,waits,targets,mi,day,floor,dd,mark,net):
    best=(-1,-1,-1,-1,-1);bestkey=(-1.,-1,-1.)
    qualified=0
    for i in range(len(candidates)):
        for j in range(len(contexts)):
            for w in range(len(waits)):
                for t in range(len(targets)):
                    for p in range(2):
                        ok,g,cnt,q=evaluate(base,candidates[i],contexts[j],waits[w],targets[t],p==1,mi,day,floor,dd,mark,net)
                        if ok:
                            qualified+=1
                            if (g,cnt,q)>bestkey:
                                bestkey=(g,cnt,q);best=(i,j,w,t,p)
    return best,bestkey,qualified

@njit
def paired_search(paths,C,cx,rules,mi,day,floor,dd,mark,net):
    best=(-1,-1);bestkey=(-1.,-1,-1.);qualified=0
    for a in range(len(paths)):
        for b in range(len(rules)):
            if a==b+1:continue
            i,j,w,t,p=rules[b]
            ok,g,cnt,q=evaluate(paths[a],C[int(i)],cx[int(j)],int(w),t,p==1.,mi,day,floor,dd,mark,net)
            if ok:
                qualified+=1
                if (g,cnt,q)>bestkey:
                    bestkey=(g,cnt,q);best=(a-1,b)
    return best,bestkey,qualified

def extrema(risk,starts,holds,side,entry,fund):
    a=[];f=[]
    for j,h,sd,en,fu in zip(starts,holds,side,entry,fund):
        lo=risk.mark_low[j:j+h+1].min();hi=risk.mark_high[j:j+h+1].max()
        if not np.isfinite(lo+hi):raise AssertionError("missing mark")
        a.append(sd*((lo if sd>0 else hi)-en)/en-2*risk.fee-fu)
        f.append(sd*((hi if sd>0 else lo)-en)/en-risk.fee)
    return np.array(a),np.array(f)

def scenario_path(risk,starts,holds,side,gross):
    # Repricing per side with vectorized funding and mark bounds.
    out=np.empty((len(starts),3))
    for sd in (-1,1):
        ix=np.flatnonzero(side==sd)
        if not len(ix):continue
        p,fee,fu=risk.prices(starts[ix],holds[ix,None],sd,gross[ix,None])
        a,f=extrema(risk,starts[ix],holds[ix],side[ix],risk.o[starts[ix]]+sd*risk.slip,fu[:,0])
        out[ix]=np.column_stack((p[:,0],a,f))
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    basepaths=[];basetags=[]
    expected=[3.6686964174388104,-15.16440927152919,-28.81506711200579,-3.931685292099929,-19.59221859891709,9.835459713487582,-9.518785775676298,-38.14402037433338]
    for k,(mode,slip) in enumerate(SC):
        tags,m,idx,cfg,mask,features,ridge,mi,day,risk,pol=build_baseline(mode,slip)
        starts=tags[:,2].astype(int);sd=tags[:,3].astype(int);holds=tags[:,7].astype(int);gross=tags[:,9]
        path=scenario_path(risk,starts,holds,sd,gross)
        assert np.max(abs(path[:,0]-tags[:,1]))<1e-11
        pct=100*(np.prod(1+path[:,0])-1)
        if k<len(expected):assert abs(pct-expected[k])<1e-7,(k,pct,expected[k])
        basepaths.append(path);basetags.append(tags)
        print("STEP59_BASELINE",mode,slip,pct,flush=True)
        del risk
    base=np.stack(basepaths,axis=1);baseline=base.copy();tags=np.stack(basetags,axis=1)
    n=len(idx);assert n==477
    risk=Risk(m,5,"historical",s.base.COST)
    o,h,l,c=[m[x].to_numpy(float) for x in ("open","high","low","close")]
    fs=s.s31.filters(features,ridge)
    contexts={"both":np.ones(n,bool),"event":~mask,"fallback":mask,"long_ridge":ridge>0,"short_ridge":ridge<0}
    for name in ("r5_aligned","r5_opposed","r60_aligned","r60_opposed","range60_high","range60_low","rvol175_high","rvol175_low","rvol125_high","rvol125_low","outer_quartile","middle_half"):
        a=np.asarray(fs[name],bool)
        contexts[name]=a;contexts["event_"+name]=(~mask)&a;contexts["fallback_"+name]=mask&a
    # Additional pre-entry context, never calendar month identity.
    r10=c[idx-1]/c[idx-11]-1
    r30=c[idx-1]/c[idx-31]-1
    r120=c[idx-1]/c[idx-121]-1
    for name,z in (("r10",r10),("r30",r30),("r120",r120)):
        for direction,a in (("positive",z>0),("negative",z<0)):
            contexts[name+"_"+direction]=a
            contexts["event_"+name+"_"+direction]=(~mask)&a
            contexts["fallback_"+name+"_"+direction]=mask&a
    # Additional causal regimes: prior completed 4h/day momentum, relative
    # local price position, and agreement between fast and slow direction.
    # No month identifiers, future values, or daily outcome-based masks.
    r240=c[idx-1]/c[idx-241]-1
    r1440=c[idx-1]/c[idx-1441]-1
    loc=np.array([(c[j-1]-l[j-60:j].min())/max(h[j-60:j].max()-l[j-60:j].min(),1e-12) for j in idx])
    extra_contexts={
        "r240_positive":r240>0,"r240_negative":r240<0,
        "r1440_positive":r1440>0,"r1440_negative":r1440<0,
        "fast_slow_agree":r10*r240>0,"fast_slow_oppose":r10*r240<0,
        "range_bottom":loc<.25,"range_top":loc>.75,
        "ridge_vs_day_agree":ridge*r1440>0,"ridge_vs_day_oppose":ridge*r1440<0,
        "low_rvol_wide_range":fs["rvol125_low"]&fs["range60_high"],
        "high_rvol_narrow_range":fs["rvol175_high"]&fs["range60_low"]}
    for name,a in extra_contexts.items():
        contexts[name]=a
        contexts["event_"+name]=(~mask)&a
        contexts["fallback_"+name]=mask&a
    cx=np.stack(list(contexts.values()))
    # Candidate order is specified before entry; all delayed direction
    # signals use completed data strictly before their own entry open.
    # The gate chooses the candidate before the delay, not after observing PnL.
    policies=np.array([(0,0.,0.,x) for x in (5,8,12,14,20,24,29,45,60,90)]+[(1,.06,4,14),(3,.12,6,29),(1,.04,2,14),(1,.10,6,29),(3,.08,4,14),(3,.20,8,29)])
    candidates=[];specs=[];ctags=[]
    for delay in (0,3,5,10,15,20,24,30,40):
        j=idx+delay
        directions={"ridge":ridge,"inverse_ridge":-ridge}
        for lb in (2,5,10,60):
            sign=np.where(c[j-1]>=c[j-1-lb],1,-1)
            directions["follow"+str(lb)]=sign;directions["fade"+str(lb)]=-sign
        for cap in (.10,.15,.25,.40):
            recipe=cfg.copy();recipe[:,1]=np.minimum(recipe[:,1],cap)
            raw={}
            for sd in (-1,1):
                a=s.early.replay_with_nextbar_exits(o,h,l,c,j,np.full(n,sd,dtype=np.int8),recipe,policies,s.base.COST,5.)
                raw[sd]=a
            # Reuse both independently simulated directions across every
            # direction rule; only direction selection varies.
            priced={}
            for sd in (-1,1):
                elapsed0=raw[sd][4];gross0=raw[sd][2]
                cube=np.empty((n,len(policies),len(SC),3))
                for p in range(len(policies)):
                    for k,(mode,slip) in enumerate(SC):
                        risk.mode=mode;risk.slip=slip
                        cube[:,p,k]=scenario_path(risk,j,elapsed0[:,p],np.full(n,sd),gross0[:,p])
                priced[sd]=cube
            for direction,side in directions.items():
                elapsed=np.where(side[:,None]>0,raw[1][4],raw[-1][4])
                gross=np.where(side[:,None]>0,raw[1][2],raw[-1][2])
                for p in range(len(policies)):
                    candidates.append(np.where((side>0)[:,None,None],priced[1][:,p],priced[-1][:,p]))
                    specs.append(dict(delay=delay,direction=direction,cap=cap,policy=policies[p].tolist()))
                    ctags.append(np.column_stack((j,side,elapsed[:,p],gross[:,p])))
        print("STEP59_CANDIDATES",delay,len(candidates),flush=True)
    # Novel exit recipes. Retain the exact frozen arms above; new recipes
    # change only the predeclared stop/target/trailing behavior, not fee logic.
    fixed_recipes=[
      ("fixed_tight",0,.20,.60,0.,0.,0.),
      ("fixed_wide",0,.40,1.20,0.,0.,0.),
      ("lock_early",1,.25,1.20,.20,.10,0.),
      ("trail_medium",2,.35,1.50,.35,.20,0.),
      ("step_lock",3,.35,2.00,.30,.15,.20)]
    newpol=np.array([(0,0.,0.,h) for h in (14,29,60,90)]+[(1,.08,4,29),(2,.08,6,29),(3,.20,4,29)])
    def new_recipe(d,name):
        vals=next(z[1:] for z in fixed_recipes if z[0]==name)
        k,sl,tp,a,v,step=vals
        return np.array([k,sl,tp,90,a,v,step],float)
    for delay in (0,10,20,30):
        j=idx+delay
        dirs={"ridge":ridge,"inverse_ridge":-ridge}
        for lb in (5,30,120):
            sign=np.where(c[j-1]>=c[j-1-lb],1,-1)
            dirs["follow"+str(lb)]=sign;dirs["fade"+str(lb)]=-sign
        for recipe_name,*_ in fixed_recipes:
            recipe=np.tile(new_recipe(0,recipe_name),(n,1))
            raw={};priced={}
            for sd in (-1,1):
                raw[sd]=s.early.replay_with_nextbar_exits(o,h,l,c,j,np.full(n,sd,dtype=np.int8),recipe,newpol,s.base.COST,5.)
                cube=np.empty((n,len(newpol),len(SC),3))
                for p in range(len(newpol)):
                    for k,(mode,slip) in enumerate(SC):
                        risk.mode=mode;risk.slip=slip
                        cube[:,p,k]=scenario_path(risk,j,raw[sd][4][:,p],np.full(n,sd),raw[sd][2][:,p])
                priced[sd]=cube
            for direction,side in dirs.items():
                elapsed=np.where(side[:,None]>0,raw[1][4],raw[-1][4])
                gross=np.where(side[:,None]>0,raw[1][2],raw[-1][2])
                for p in range(len(newpol)):
                    candidates.append(np.where((side>0)[:,None,None],priced[1][:,p],priced[-1][:,p]))
                    specs.append(dict(delay=delay,direction=direction,recipe=recipe_name,policy=newpol[p].tolist()))
                    ctags.append(np.column_stack((j,side,elapsed[:,p],gross[:,p])))
        print("STEP59_NEW_RECIPES",delay,len(candidates),flush=True)
    C=np.stack(candidates);del candidates
    waits=np.array((0,5,10,15,17,19))
    targets=np.array((-.01,-.005,-.0025,0.,.0025,.005,.0075,.01,.015))
    stages=[];selected=np.full((n,len(SC)),-1,dtype=int)
    def report(path):
        net,dd,mark,mo=metrics(path,mi)
        return [dict(mode=mode,slip=slip,net_pct=100*net[k],closed_dd_pct=100*dd[k],mark_dd_pct=100*mark[k],
                     months_ge1=int((mo[:,k]>=.01).sum()),months_positive=int((mo[:,k]>0).sum()),worst_month_pct=100*mo[:,k].min(),monthly_pct=(100*mo[:,k]).tolist()) for k,(mode,slip) in enumerate(SC)]
    # Freeze every Step56 accepted rule before new research. Exact parity
    # prevents selecting a worse baseline or relabeling an earlier result.
    locked=[
        (10,"follow10",.4,[0,0,0,29],"fallback_range60_low",15,.01,True),
        (10,"fade60",.4,[0,0,0,20],"fallback_rvol125_high",15,.01,False),
        (15,"follow5",.15,[0,0,0,60],"event_r5_aligned",10,.0025,False),
        (0,"inverse_ridge",.4,[3,.12,6,29],"fallback_rvol175_high",15,.015,False),
        (5,"fade2",.4,[0,0,0,45],"event_r5_aligned",17,.015,False),
        (5,"follow10",.4,[0,0,0,90],"fallback_r5_opposed",17,.01,True),
        (10,"follow10",.4,[3,.20,8,29],"fallback_range60_low",17,.01,True),
        (3,"inverse_ridge",.1,[0,0,0,14],"fallback_rvol175_high",15,.015,False)]
    for delay,direction,cap,policy,context,wait,target,pace in locked:
        i=specs.index(dict(delay=delay,direction=direction,cap=cap,policy=policy))
        base,used=route(base,C[i],contexts[context],wait,target,pace,mi,day)
        selected[used]=i
    locked58=[
        (dict(delay=40,direction="fade5",cap=.1,policy=[3,.12,6,29]),"event_middle_half",19,.0075,False),
        (dict(delay=20,direction="follow5",recipe="fixed_wide",policy=[0,0,0,60]),"event_r5_aligned",17,.0025,False),
        (dict(delay=3,direction="fade2",cap=.1,policy=[0,0,0,14]),"fallback_r120_negative",19,-.005,False),
        (dict(delay=0,direction="ridge",cap=.1,policy=[0,0,0,29]),"fallback_range_top",19,.01,False),
        (dict(delay=0,direction="inverse_ridge",recipe="fixed_tight",policy=[0,0,0,90]),"fallback_r5_opposed",19,.015,False),
        (dict(delay=10,direction="ridge",cap=.1,policy=[0,0,0,90]),"event_r5_aligned",19,.015,False)]
    for spec,context,wait,target,pace in locked58:
        i=specs.index(spec)
        base,used=route(base,C[i],contexts[context],wait,target,pace,mi,day)
        selected[used]=i
    expected56=np.array([16.355236975114295,-2.328301365824048,-17.598038143097806,10.370777207019156,-7.259995158640098,21.785902706237703,1.5261918806554364,-27.76854322702945,-66.92241071751619,-89.082001786998])
    nn,dd0,md0,mo0=metrics(base,mi)
    assert np.max(abs(nn*100-expected56))<1e-7,(nn*100,expected56)
    assert abs(md0[0]*100-4.189014947052449)<1e-7
    initial=report(base)
    print("STEP59_FROZEN_STEP58",json.dumps(initial),flush=True)
    # Fast approximate shortlist uses baseline prior-month-state gates.
    # A gate in the real evaluation is ALWAYS recomputed sequentially.
    # Approximation is a search heuristic only; not an execution result.
    def shortlist(path):
        net,dd,mark,mo=metrics(path,mi)
        mt=np.ones((n,len(SC)));state=np.ones(len(SC))
        for d in range(n):
            if d and mi[d]!=mi[d-1]:state[:]=1.
            mt[d]=state-1;state*=1+path[d,:,0]
        # Use different scenario rankings and prefer deficits over gains
        # in already healthy months. Retain diverse near-miss candidates.
        gate_specs=list(product(range(len(cx)),(0,5,10,15,17,19),(-.01,-.005,0.,.005,.01,.015),(False,True)))
        scenario_ids=(0,2,5,7)
        delta=[]
        for k in scenario_ids:
            delta.append((np.log1p(C[:,:,k,0])-np.log1p(path[:,k,0])[None,:]).astype(np.float32))
        weight=(1.+2.*np.maximum(.01-mo[:,0],0)/.03+2.*(mo[:,0]<0))[mi].astype(np.float32)
        gate_ids=set()
        for start in range(0,len(gate_specs),96):
            block=gate_specs[start:start+96]
            score=np.zeros((len(C),len(block)),np.float32)
            for kk,k in enumerate(scenario_ids):
                gates=np.stack([cx[j]&(day>=w)&(mt[:,k]<t*(np.minimum(day/20.,1.) if p else 1.)) for j,w,t,p in block]).astype(np.float32)
                q=delta[kk]@(gates*weight[None,:]).T
                score+=q/len(scenario_ids)
                if k==0:
                    top=np.argpartition(q,-2,axis=0)[-2:]
                    for bi in range(len(block)):
                        if not gates[bi].any():continue
                        for i in top[:,bi]:gate_ids.add((int(i),*block[bi]))
            top=np.argpartition(score,-3,axis=0)[-3:]
            for bi in range(len(block)):
                for i in top[:,bi]:
                    if score[i,bi]>0:gate_ids.add((int(i),*block[bi]))
        rules=sorted(gate_ids)
        print("STEP59_PREFILTER",len(gate_specs)*len(C),len(rules),flush=True)
        vals=[];diffs=[];risk_improvements=[]
        for i,j,w,t,p in rules:
            z,used=route(path,C[i],cx[j],w,t,p,mi,day)
            r,d,m,monthly=metrics(z,mi)
            diff=monthly-mo
            deficits=(np.minimum(monthly[:,:NPRIMARY],.01)-np.minimum(mo[:,:NPRIMARY],.01))
            loss_gain=(np.minimum(monthly[:,:NPRIMARY],0.)-np.minimum(mo[:,:NPRIMARY],0.))
            regress=np.minimum(diff,0.)
            risk_gain=np.sum(mark[:NPRIMARY]-m[:NPRIMARY])
            risk_loss=np.maximum(m-mark,0.).sum()+np.maximum(d-dd,0.).sum()
            val=deficits.sum()+2*loss_gain.sum()+risk_gain-3*abs(regress).sum()-3*risk_loss
            vals.append(val);diffs.append(diff[:,0]);risk_improvements.append(risk_gain-3*risk_loss)
        if not rules:return []
        vals=np.asarray(vals);diffs=np.asarray(diffs);risk_improvements=np.asarray(risk_improvements)
        keep=set(np.argsort(vals)[-256:].tolist())
        keep.update(np.argsort(risk_improvements)[-64:].tolist())
        for month in range(22):
            if mo[month,0]<.01:
                # Include complementary policies that help different
                # deficits, even if not individually acceptable.
                v=diffs[:,month]-.2*np.maximum(-diffs,0.).sum(1)
                keep.update(np.argsort(v)[-20:].tolist())
        return [rules[i] for i in sorted(keep)]
    for stage in range(1,7):
        net,dd,mark,mo=metrics(base,mi)
        rules=shortlist(base)
        if not rules:break
        # Reconstruct the first rule exactly; screen every ordered pair
        # against the SAME pre-stage floor, not a weakened intermediate.
        # A temporary regression is permitted only within the search,
        # never in an accepted final pair.
        paths=[base]
        for i,j,w,t,p in rules:
            z,used=route(base,C[i],cx[j],w,t,p,mi,day)
            paths.append(z)
        rr=np.asarray(rules,dtype=float)
        best,key,qualified=paired_search(np.stack(paths),C,cx,rr,mi,day,mo,dd,mark,net)
        print("STEP59_SEARCH",stage,(len(rules)+1)*len(rules),qualified,flush=True)
        if best[1]<0:break
        old=base.copy()
        pair=[]
        for a in best:
            if a<0:continue
            i,j,w,t,p=rules[a]
            base,used=route(base,C[i],cx[j],w,t,p,mi,day)
            selected[used]=i
            pair.append(dict(**specs[i],context=list(contexts)[j],wait=w,target=t,pace=p,modified_trades=used.sum(0).tolist()))
        nr,nd,nm,nmo=metrics(base,mi)
        assert np.all(nmo>=mo-1e-9) and np.all(nd<=dd+1e-9) and np.all(nm<=mark+1e-9) and np.all(nr>=net-1e-9)
        record=dict(stage=stage,rules=pair)
        stages.append(record)
        print("STEP59_ACCEPTED",json.dumps(dict(rule=record,results=report(base))),flush=True)
        if np.all(nmo>=.01) and np.all(nm<=.02506676):break
    # Independently reconstruct every newly selected trade from OHLC,
    # compare original Step52 descriptors for unchanged trades.
    fills=[]
    for k,(mode,slip) in enumerate(SC):
        risk.mode=mode;risk.slip=slip
        for d in range(n):
            arm=selected[d,k]
            if arm<0:
                start,sd,guard,cap,pid,hold,why,gross=tags[d,k,2:]
                start,sd,hold=int(start),int(sd),int(hold)
                end=start+hold;mid=o[start]+sd*gross
                # Base fills previously independently reconstructed in Step52;
                # replay selected stressed configuration again here.
                recipe,_=s.previous.step25.preentry_stop(cfg,features,mask,np.full(n,sd,dtype=np.int8),"tight60_050_both_cap040")
                if bool(guard):recipe=s.previous.step28.change_trailing(recipe,mask,.18,"E3_later_larger_lock","F3_normal_tight")
                recipe=recipe[d].copy()
                if cap>=0:recipe[1]=min(recipe[1],cap)
                e,x,reason,_,_,_=replay_one(o,h,l,c,start,sd,recipe,pol[int(pid)])
                assert e==end and abs(x-mid)<1e-7 and reason==int(why)
            else:
                start,sd,hold,gross=ctags[arm][d];start,sd,hold=int(start),int(sd),int(hold)
                if "recipe" in specs[arm]:
                    recipe=new_recipe(d,specs[arm]["recipe"])
                else:
                    recipe=cfg[d].copy();recipe[1]=min(recipe[1],specs[arm]["cap"])
                end,mid,why,_,_,_=replay_one(o,h,l,c,start,sd,recipe,specs[arm]["policy"])
                assert end-start==hold and abs(sd*(mid-o[start])-gross)<1e-7
            z=scenario_path(risk,np.array([start]),np.array([hold]),np.array([sd]),np.array([sd*(mid-o[start])]))
            assert np.max(abs(z[0]-base[d,k]))<1e-10
            if d:assert prev_end<start
            prev_end=end
            assert m.index[start].tz_convert("Asia/Kolkata").strftime("%Y-%m-%d")==s.base.IST_DAYS[d]
            fills.append(dict(mode=mode,slip=slip,day=s.base.IST_DAYS[d],entry=m.index[start],exit=m.index[end],side=sd,entry_mid=o[start],exit_mid=mid,net_pct=100*z[0,0],candidate=int(arm)))
    result=dict(accepted=stages,baseline=initial,final=report(base),trades=n,independent_execution_parity=True,
                all_primary_pass=all(x["months_ge1"]==22 and x["mark_dd_pct"]<=2.506676 for x in report(base)[:NPRIMARY]),
                all_severe_pass=all(x["months_ge1"]==22 and x["mark_dd_pct"]<=2.506676 for x in report(base)),
                research_exposed=True,settlement_verified=False,demo_verified=False)
    pd.DataFrame(fills).to_csv(OUT/"ledger.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(result,indent=2))
    print("STEP59_FINAL",json.dumps(result),flush=True)
if __name__=="__main__":main()
