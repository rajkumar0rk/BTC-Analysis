#!/usr/bin/env python3
"""Coarse common parameter grid with chronological development blocks,
neighbor robustness and one frozen 2025-H2 evaluation. Prior research exposed
all these years; this is a retrospective split, not an untouched holdout.
"""
import json
from itertools import product
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit
from research_btc_clean_core_2024_2025 import load_files, select, report, ROOT, TZ
from research_btc_daily_exit_invalidation_step7 import replay_with_nextbar_exits
from step52_validation_engine import replay_one

OUT=Path("analysis/btc_robust_common_2024_2025")
DATA=Path("prior2024")
SC=[("historical",5),("historical",20),("standard",20),("conservative",5),("conservative",20),("offer30",5),("offer30",20),("offer30",50),("standard",100),("standard",200),("standard",5)]
FEE=.0005*1.18
HOLDS=(10,14,20,29,45,60,75)
POL=np.array([(0.,0.,0.,float(h)) for h in HOLDS])
DIRECTIONS=("follow5","fade5","follow15","fade15","follow60","fade60","follow240","fade240","trend_agreement","trend_pullback","range_fade","range_follow")

@njit
def pricing(starts,sides,holds,gross,o,mark_hi,mark_lo,fund_pre,fund_post,old,slips,modes):
    n=len(starts);k=len(slips)
    out=np.empty((n,k,3))
    for i in range(n):
        j=starts[i];e=j+holds[i];sd=sides[i]
        hi=mark_hi[j];lo=mark_lo[j]
        for x in range(j+1,e+1):
            hi=max(hi,mark_hi[x]);lo=min(lo,mark_lo[x])
        fu=fund_pre[e]-fund_pre[j]+fund_post[e+1]-fund_post[j]
        for a in range(k):
            en=o[j]+sd*slips[a];ex=o[j]+sd*gross[i]-sd*slips[a]
            mode=modes[a]
            waive=(mode==0 and holds[i]<(15 if old[j] else 30)) or (mode==1 and not old[j] and holds[i]<30) or (mode==2 and holds[i]<30)
            fee=FEE*(en+ex*(not waive))/en
            out[i,a,0]=(sd*(ex-en)/en)-fee-fu/en
            out[i,a,1]=sd*((lo if sd>0 else hi)-en)/en-2*FEE-fu/en
            out[i,a,2]=sd*((hi if sd>0 else lo)-en)/en-FEE
    return out

@njit
def stats(path,years,months):
    k=path.shape[1]
    eq=np.ones((2,k));peak=np.ones((2,k));mp=np.ones((2,k))
    dd=np.zeros((2,k));md=np.zeros((2,k));mo=np.ones((24,k));wins=np.zeros((2,k),np.int64)
    for i in range(len(path)):
        y=years[i];m=months[i]
        for j in range(k):
            r,a,f=path[i,j]
            mp[y,j]=max(mp[y,j],eq[y,j]*(1+f))
            md[y,j]=max(md[y,j],1-eq[y,j]*(1+a)/mp[y,j])
            eq[y,j]*=1+r;mo[m,j]*=1+r;wins[y,j]+=r>0
            peak[y,j]=max(peak[y,j],eq[y,j]);dd[y,j]=max(dd[y,j],1-eq[y,j]/peak[y,j])
            mp[y,j]=max(mp[y,j],eq[y,j]);md[y,j]=max(md[y,j],1-eq[y,j]/mp[y,j])
    return eq-1,dd,md,mo-1,wins

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m24=load_files(sorted(DATA.rglob("2024_data/*.csv.gz")))
    m25=load_files([ROOT/"1m"/(str(x)+".csv.gz") for x in pd.period_range("2025-01","2025-12",freq="M")])
    assert len(m24)>0 and len(m25)==525600,(len(m24),len(m25))
    m=pd.concat([m24,m25]).sort_index();assert not m.index.has_duplicates
    mark24=load_files(sorted(DATA.rglob("2024_aux/mark_*.csv.gz")))
    f24=load_files(sorted(DATA.rglob("2024_aux/funding_*.csv.gz")))
    root=ROOT/"institutional/history"
    mark25=load_files(sorted((root/"mark_1m").glob("*.csv.gz")))
    f25=load_files(sorted((root/"funding_1h").glob("*.csv.gz")))
    mark=pd.concat([mark24,mark25]).sort_index();assert not mark.index.has_duplicates
    funding=pd.concat([f24,f25]).sort_index();assert not funding.index.has_duplicates
    ix=m.index
    o,h,l,c,v=[m[x].to_numpy(float) for x in ("open","high","low","close","volume")]
    mm=mark.reindex(ix)
    mh=mm.high.to_numpy(float);ml=mm.low.to_numpy(float);mopen=mm.open.to_numpy(float)
    rate=funding.close.shift(1).reindex(ix,method="ffill").to_numpy(float)/100.
    before=ix<pd.Timestamp("2025-09-08T12:00Z")
    boundary=(ix.minute==0)&(ix.hour%8==0)
    old=ix<pd.Timestamp("2025-10-11",tz=TZ)
    # Missing values outside any tested position cannot create a cost credit.
    pre=np.where(before,np.abs(rate*mopen)/480.,0.)
    post=np.where((~before)&boundary,np.abs(rate*mopen),0.)
    days=[];grid=[];missing=[]
    for d in pd.date_range("2024-01-01","2025-12-31",freq="B",tz=TZ):
        a=(d+pd.Timedelta(hours=14)).tz_convert("UTC")
        b=(d+pd.Timedelta(hours=22,minutes=15)).tz_convert("UTC")
        ai,bi=ix.get_indexer([a,b])
        j=ix.get_indexer([(d+pd.Timedelta(hours=x)).tz_convert("UTC") for x in (18,19,20,21)])
        if ai<0 or bi<0 or bi-ai!=495 or np.any(j<0) or not np.array_equal(ix[ai:bi+1],pd.date_range(a,b,freq="min")):
            missing.append(str(d.date()));continue
        # Mark/funding from the earliest possible 18h entry to latest exit.
        q=slice(j[0],bi+1)
        if not (np.isfinite(mh[q]).all() and np.isfinite(ml[q]).all() and np.isfinite(mopen[q]).all() and np.isfinite(pre[q]).all() and np.isfinite(post[q]).all()):
            missing.append(str(d.date()));continue
        days.append(d);grid.append(j)
    days=pd.DatetimeIndex(days);grid=np.array(grid,np.int64);n=len(days)
    years=np.asarray(days.year-2024,dtype=np.int64)
    months=np.asarray(years*12+days.month-1,dtype=np.int64)
    expected=pd.date_range("2024-01-01","2025-12-31",freq="B",tz=TZ)
    counts=np.bincount(months,minlength=24)
    expcounts=np.bincount(np.asarray((expected.year-2024)*12+expected.month-1),minlength=24)
    complete=counts==expcounts
    assert n>450 and complete[12:].all(),(n,counts,expcounts)
    pre=np.r_[0.,np.cumsum(np.nan_to_num(pre,nan=0.))]
    post=np.r_[0.,np.cumsum(np.nan_to_num(post,nan=0.))]
    slips=np.array([s for _,s in SC],float)
    modecodes=np.array([{"historical":0,"conservative":1,"offer30":2,"standard":3}[k] for k,_ in SC])
    # Both years and all fees see exactly the same order descriptors.
    print("COMMON_COVERAGE",json.dumps(dict(trades=n,by_year=np.bincount(years).tolist(),month_counts=counts.tolist(),expected=expcounts.tolist(),missing=missing)),flush=True)
    # Predeclared grid: 4 times * 6 directions * 3 stops * 2 reward
    # ratios * 2 holds * 2 exit types = 576. No month/PNL in trading rules.
    hours=(18,19,20,21);looks=(15,60,240);fades=(False,True)
    stops=(.30,.60,.90);rewards=(2.,3.);holds=(30,60);types=("fixed","trailing")
    settings=list(product(hours,looks,fades,stops,rewards,holds,types))
    assert len(settings)==576
    dates=days.strftime("%Y-%m-%d").to_numpy()
    development=np.flatnonzero(dates<"2025-07-01")
    folds=[np.flatnonzero((dates[development]>=a)&(dates[development]<b)) for a,b in
           [("2024-01-01","2024-07-01"),("2024-07-01","2025-01-01"),("2025-01-01","2025-07-01")]]
    assert min(map(len,folds))>90
    test=np.flatnonzero(dates>="2025-07-01")
    def replay(setting,subset,verify=False):
        hour,look,fade,sl,rr,hold,kind=setting
        starts=grid[subset,hour-18]
        side=np.where(c[starts-1]>=o[starts-look],1,-1).astype(np.int8)
        if fade:side=-side
        recipe=np.array([0 if kind=="fixed" else 2,sl,sl*rr,hold,0 if kind=="fixed" else .35,0 if kind=="fixed" else .20,0.],float)
        policy=np.array([0.,0.,0.,float(hold)])
        raw=replay_with_nextbar_exits(o,h,l,c,starts,side,np.tile(recipe,(len(subset),1)),policy[None,:],FEE,5.)
        hh=raw[4][:,0];gg=raw[2][:,0]
        path=pricing(starts,side,hh,gg,o,mh,ml,pre,post,old,slips,modecodes)
        assert np.isfinite(path).all()
        if verify:
            for i,j in enumerate(starts):
                end,px,why,*_=replay_one(o,h,l,c,int(j),int(side[i]),recipe,policy)
                assert end-j==hh[i] and abs(side[i]*(px-o[j])-gg[i])<1e-7 and why==raw[3][i,0]
                if i:assert starts[i-1]+hh[i-1]<j
        return path,starts,side,hh,gg
    # Standard fees 5 and 20 points, plus historical 5. Cost-adjusted
    # daily log returns are comparable across unequal chronological folds.
    primary=(10,2,0)
    scores={};records={}
    for config in settings:
        path,*_=replay(config,development)
        block=[]
        for f in folds:
            p=path[f]
            net,dd,md,_,_=stats(p,np.zeros(len(f),np.int64),months[development[f]])
            log=np.log1p(p[:,primary,0]).mean(0)
            block.append(dict(net=(100*net[0,list(primary)]).tolist(),mark_dd=(100*md[0,list(primary)]).tolist(),mean_log=log.tolist()))
        floor=min(min(b["mean_log"]) for b in block)
        mean=float(np.mean([b["mean_log"] for b in block]))
        draw=max(max(b["mark_dd"]) for b in block)
        # Penalize drawdown above 2.5%; don't reward lucky return spikes.
        score=.65*floor+.35*mean-.000025*max(draw-2.506676,0.)
        passes=all(min(b["net"])>0 and max(b["mark_dd"])<=2.506676 for b in block)
        scores[config]=score
        records[config]=dict(blocks=block,score=score,development_pass=passes)
    def neighbors(cfg):
        out=[]
        # perturb one parameter at a time (including entry time and lookback)
        for dim,values in ((0,hours),(1,looks),(3,stops),(4,rewards),(5,holds)):
            i=values.index(cfg[dim])
            for d in (-1,1):
                if 0<=i+d<len(values):
                    a=list(cfg);a[dim]=values[i+d];out.append(tuple(a))
        return out
    ranking=[]
    for cfg in settings:
        ns=neighbors(cfg)
        q=float(np.quantile([scores[a] for a in ns],.25))
        nb_positive=float(np.mean([all(min(b["net"])>0 for b in records[a]["blocks"]) for a in ns]))
        stable=records[cfg]["development_pass"] and nb_positive>=.75 and q>0.
        robust=min(scores[cfg],q)
        ranking.append((stable,robust,scores[cfg],cfg,q,nb_positive))
    ranking.sort(reverse=True)
    stable,robust,score,winner,q,npos=ranking[0]
    def config_dict(cfg):return dict(zip(("hour_ist","lookback","fade","stop_pct","reward_risk","max_hold","exit"),cfg))
    selection=dict(config=config_dict(winner),development_pass=records[winner]["development_pass"],neighbor_stable=bool(stable),robust_score=robust,neighbor_lower_quartile=q,positive_neighbor_fraction=npos,development_blocks=records[winner]["blocks"],eligible_count=sum(x[0] for x in ranking))
    (OUT/"frozen_selection.json").write_text(json.dumps(selection,indent=2))
    print("ROBUST_FROZEN",json.dumps(selection),flush=True)
    # Only now evaluate 2025 H2: no search, replacement or parameter changes.
    path,starts,side,hh,gg=replay(winner,np.arange(n),verify=True)
    net,dd,md,mo,wins=stats(path,years,months)
    tn,td,tm,tmo,tw=stats(path[test],np.zeros(len(test),np.int64),months[test])
    test_months=np.unique(months[test])
    scenarios=[]
    for k,(mode,slip) in enumerate(SC):
        scenarios.append(dict(mode=mode,slip=slip,net_pct=(100*net[:,k]).tolist(),closed_dd_pct=(100*dd[:,k]).tolist(),mark_dd_pct=(100*md[:,k]).tolist(),wins=wins[:,k].tolist(),positive_complete_months=int((mo[complete,k]>0).sum()),ge1_complete_months=int((mo[complete,k]>=.01).sum()),monthly_pct=(100*mo[:,k]).tolist(),test_net_pct=100*tn[0,k],test_mark_dd_pct=100*tm[0,k],test_months_positive=int((tmo[test_months,k]>0).sum()),test_months_ge1=int((tmo[test_months,k]>=.01).sum())))
    passed=bool(stable and np.all(tmo[test_months,:10]>=.01) and np.all(tm[0,:10]<=.02506676))
    pd.DataFrame([dict(**config_dict(cfg),robust_score=r,neighbor_q=q,neighbor_positive=pos,development_pass=records[cfg]["development_pass"],stable=st) for st,r,score,cfg,q,pos in ranking]).to_csv(OUT/"development_grid.csv",index=False)
    pd.DataFrame(dict(date=days.astype(str),entry=ix[starts],exit=ix[starts+hh],side=side,gross_points=gg,net_historical5=100*path[:,0,0])).to_csv(OUT/"frozen_ledger.csv",index=False)
    result=dict(configurations=len(settings),days=n,by_year=np.bincount(years).tolist(),complete_months=int(complete.sum()),test_days=len(test),test_period="2025-07-01..2025-12-31",selection=selection,scenarios=scenarios,all_pass=passed,independent_replay=True,recovery_rules=0,prior_research_exposed=True)
    (OUT/"summary.json").write_text(json.dumps(result,indent=2))
    print("ROBUST_FINAL",json.dumps(result),flush=True)
if __name__=="__main__":main()
