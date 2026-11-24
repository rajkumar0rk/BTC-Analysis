#!/usr/bin/env python3
"""Step56: strict incremental improvement on cost-aware Step52.
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

OUT=Path("analysis/btc_step56_joint_recovery")
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
    gain=np.sum(np.minimum(mo[:,:NPRIMARY],.01)-np.minimum(floor[:,:NPRIMARY],.01))
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
        print("STEP56_BASELINE",mode,slip,pct,flush=True)
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
    cx=np.stack(list(contexts.values()))
    # Candidate order is specified before entry; all delayed direction
    # signals use completed data strictly before their own entry open.
    # The gate chooses the candidate before the delay, not after observing PnL.
    policies=np.array([(0,0.,0.,x) for x in (8,14,20,29,45,60)]+[(1,.06,4,14),(3,.12,6,29)])
    candidates=[];specs=[];ctags=[]
    for delay in (0,5,10,15,24,30):
        j=idx+delay
        directions={"ridge":ridge,"inverse_ridge":-ridge}
        for lb in (2,5,10,60):
            sign=np.where(c[j-1]>=c[j-1-lb],1,-1)
            directions["follow"+str(lb)]=sign;directions["fade"+str(lb)]=-sign
        for cap in (.15,.25,.40):
            recipe=cfg.copy();recipe[:,1]=np.minimum(recipe[:,1],cap)
            raw={}
            for sd in (-1,1):
                a=s.early.replay_with_nextbar_exits(o,h,l,c,j,np.full(n,sd,dtype=np.int8),recipe,policies,s.base.COST,5.)
                raw[sd]=a
            for direction,side in directions.items():
                elapsed=np.where(side[:,None]>0,raw[1][4],raw[-1][4])
                gross=np.where(side[:,None]>0,raw[1][2],raw[-1][2])
                for p in range(len(policies)):
                    results=[]
                    for mode,slip in SC:
                        risk.mode=mode;risk.slip=slip
                        results.append(scenario_path(risk,j,elapsed[:,p],side,gross[:,p]))
                    candidates.append(np.stack(results,axis=1))
                    specs.append(dict(delay=delay,direction=direction,cap=cap,policy=policies[p].tolist()))
                    ctags.append(np.column_stack((j,side,elapsed[:,p],gross[:,p])))
        print("STEP56_CANDIDATES",delay,len(candidates),flush=True)
    C=np.stack(candidates);del candidates
    waits=np.array((0,5,10,15))
    targets=np.array((-.005,0.,.0025,.005,.0075,.01,.015))
    stages=[];selected=np.full((n,len(SC)),-1,dtype=int)
    def report(path):
        net,dd,mark,mo=metrics(path,mi)
        return [dict(mode=mode,slip=slip,net_pct=100*net[k],closed_dd_pct=100*dd[k],mark_dd_pct=100*mark[k],
                     months_ge1=int((mo[:,k]>=.01).sum()),months_positive=int((mo[:,k]>0).sum()),worst_month_pct=100*mo[:,k].min(),monthly_pct=(100*mo[:,k]).tolist()) for k,(mode,slip) in enumerate(SC)]
    initial=report(base)
    for stage in range(1,5):
        net,dd,mark,mo=metrics(base,mi)
        best,key,qualified=search(base,C,cx,waits,targets,mi,day,mo,dd,mark,net)
        print("STEP56_SEARCH",stage,len(C)*len(cx)*len(waits)*len(targets)*2,qualified,flush=True)
        if best[0]<0:break
        i,j,w,t,p=best
        new,used=route(base,C[i],cx[j],waits[w],targets[t],p==1,mi,day)
        nr,nd,nm,nmo=metrics(new,mi)
        assert np.all(nmo>=mo-1e-9) and np.all(nd<=dd+1e-9) and np.all(nm<=mark+1e-9) and np.all(nr>=net-1e-9)
        selected[used]=i;base=new
        rule=dict(stage=stage,**specs[i],context=list(contexts)[j],wait=int(waits[w]),target=float(targets[t]),pace=bool(p),modified_trades=used.sum(0).tolist())
        stages.append(rule)
        print("STEP56_ACCEPTED",json.dumps(dict(rule=rule,results=report(base))),flush=True)
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
    print("STEP56_FINAL",json.dumps(result),flush=True)
if __name__=="__main__":main()
