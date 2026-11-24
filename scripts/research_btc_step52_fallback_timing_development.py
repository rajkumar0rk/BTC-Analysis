#!/usr/bin/env python3
"""Train only on 2024-2025, freeze one common configuration, validate 2026 once.
Previous research exposure means 2026 is retrospective, not pristine OOS.
No PnL/calendar routing, no selection using 2026.
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

OUT=Path("analysis/btc_step52_fallback_timing_development")
DATA=ROOT/"2024_verified_archive"
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

def dataset(validation=False):
    root=ROOT/"institutional/history"
    if validation:
        # Open 2026 trade/mark data only after the frozen selection is written.
        m=load_files([ROOT/"1m"/(str(x)+".csv.gz") for x in pd.period_range("2026-01","2026-10",freq="M")])
        mark=load_files([p for p in sorted((root/"mark_1m").glob("*.csv.gz")) if "2026-" in p.name])
        funding=load_files([p for p in sorted((root/"funding_1h").glob("*.csv.gz")) if "2026-" in p.name or "2025-12" in p.name])
        assert len(m)==437760,(len(m),m.index.min(),m.index.max())
        first,last="2026-01-01","2026-10-31"
    else:
        months24=pd.period_range("2024-02","2024-12",freq="M")
        manifest=json.loads((DATA/"manifest.json").read_text())
        for series in ("trade_1m","mark_1m","funding_1h"):
            for month in months24:
                rec=[x for x in manifest["months"] if x["series"]==series and x["month"]==str(month)]
                assert len(rec)==1 and rec[0]["missing"]==0,(series,str(month),rec)
        assert manifest["synthetic_rows"]==0
        m24=load_files([DATA/"trade_1m"/(str(x)+".csv.gz") for x in months24])
        expected24=pd.date_range("2024-02-01","2025-01-01",tz=TZ,freq="min",inclusive="left").tz_convert("UTC")
        assert len(m24)==len(expected24) and np.all(m24.index==expected24),(len(m24),len(expected24))
        assert np.isfinite(m24[["open","high","low","close","volume"]].to_numpy()).all()
        print("VERIFIED_2024_TRADE_CANDLES",len(m24),flush=True)
        m25=load_files([ROOT/"1m"/(str(x)+".csv.gz") for x in pd.period_range("2025-01","2025-12",freq="M")])
        assert len(m24)==482400 and len(m25)==525600,(len(m24),len(m25))
        m=pd.concat([m24,m25]).sort_index()
        mark24=load_files([DATA/"mark_1m"/(str(x)+".csv.gz") for x in months24])
        assert len(mark24)==len(expected24) and np.all(mark24.index==expected24)
        assert np.isfinite(mark24[["open","high","low","close"]].to_numpy()).all()
        f24=load_files([DATA/"funding_1h"/(str(x)+".csv.gz") for x in months24])
        assert ((f24.index[1:]-f24.index[:-1])==pd.Timedelta(hours=1)).all()
        assert np.isfinite(f24.close.to_numpy()).all()
        print("VERIFIED_2024_MARK_AND_FUNDING",len(mark24),len(f24),flush=True)
        mark25=load_files([p for p in sorted((root/"mark_1m").glob("*.csv.gz")) if "2025-" in p.name])
        f25=load_files([p for p in sorted((root/"funding_1h").glob("*.csv.gz")) if "2025-" in p.name])
        mark=pd.concat([mark24,mark25]).sort_index()
        funding=pd.concat([f24,f25]).sort_index()
        first,last="2024-02-01","2025-12-31"
    assert len(mark)>0 and len(funding)>0
    assert not m.index.has_duplicates and not mark.index.has_duplicates and not funding.index.has_duplicates
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
    for d in pd.date_range(first,last,freq="B",tz=TZ):
        a=(d+pd.Timedelta(hours=14)).tz_convert("UTC")
        b=(d+pd.Timedelta(hours=23,minutes=59)).tz_convert("UTC")
        ai,bi=ix.get_indexer([a,b])
        j=ix.get_indexer([(d+pd.Timedelta(hours=x)).tz_convert("UTC") for x in (18,19,20,21)])
        if ai<0 or bi<0 or bi-ai!=599 or np.any(j<0) or not np.array_equal(ix[ai:bi+1],pd.date_range(a,b,freq="min")):
            missing.append(str(d.date()));continue
        # Check actual trade, mark and funding coverage through 23:59 IST.
        assert np.isfinite(np.stack([o[ai:bi+1],h[ai:bi+1],l[ai:bi+1],c[ai:bi+1],v[ai:bi+1]])).all()
        q=slice(j[0],bi+1)
        if not (np.isfinite(mh[q]).all() and np.isfinite(ml[q]).all() and np.isfinite(mopen[q]).all() and np.isfinite(pre[q]).all() and np.isfinite(post[q]).all()):
            missing.append(str(d.date()));continue
        days.append(d);grid.append(j)
    days=pd.DatetimeIndex(days);grid=np.array(grid,np.int64);n=len(days)
    start_year=2026 if validation else 2024
    years=np.asarray(days.year-start_year,dtype=np.int64)
    months=np.asarray(years*12+days.month-1,dtype=np.int64)
    expected=pd.date_range(first,last,freq="B",tz=TZ)
    counts=np.bincount(months,minlength=24)
    expcounts=np.bincount(np.asarray((expected.year-start_year)*12+expected.month-1),minlength=24)
    complete=(counts==expcounts)&(expcounts>0)
    if validation:
        assert n>=210 and complete[:10].all(),(n,counts,expcounts)
    else:
        assert n==500 and not missing and complete[1:].all() and int(complete.sum())==23,(n,counts,expcounts,missing)
    pre=np.r_[0.,np.cumsum(np.nan_to_num(pre,nan=0.))]
    post=np.r_[0.,np.cumsum(np.nan_to_num(post,nan=0.))]
    slips=np.array([s for _,s in SC],float)
    modecodes=np.array([{"historical":0,"conservative":1,"offer30":2,"standard":3}[k] for k,_ in SC])
    # Both years and all fees see exactly the same order descriptors.
    print("ROBUST_COVERAGE",json.dumps(dict(validation=validation,trades=n,by_year=np.bincount(years).tolist(),month_counts=counts.tolist(),expected=expcounts.tolist(),missing=missing)),flush=True)
    return (m,ix,o,h,l,c,v,mh,ml,pre,post,old,slips,modecodes,days,grid,years,months,complete,counts,expcounts)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ix,o,h,l,c,v,mh,ml,pre,post,old,slips,modecodes,days,grid,years,months,complete,counts,expcounts=dataset()
    n=len(days)
    # Primary entries locked. After all three primary checks fail at 20:00,
    # test only a small common fallback timing and exit grid.
    signals=("fade5","range_reversion","follow240")
    offsets=(-45,-30,0)
    stops=(.75,1.0)
    holds=(60,120)
    types=("fixed","baseline_trailing","cost_lock")
    settings=list(product(signals,offsets,stops,holds,types))
    assert len(settings)==108
    baseline=("fade5",0,.75,60,"baseline_trailing")
    monthly_reference=("fade5",0,1.0,120,"fixed")
    dates=days.strftime("%Y-%m-%d").to_numpy()
    development=np.arange(n)
    folds=[np.flatnonzero((dates[development]>=a)&(dates[development]<b)) for a,b in
           [("2024-02-01","2024-07-01"),("2024-07-01","2025-01-01"),("2025-01-01","2025-07-01"),("2025-07-01","2026-01-01")]]
    assert min(map(len,folds))>90
    # All entries use completed bars. Earlier fallback entries are only
    # possible after the 20:00 primary decision has already failed.
    slot_cache={}
    def entry_features():
        key=id(grid)
        if key in slot_cache:return slot_cache[key]
        vol=np.zeros(grid.shape)
        for i in range(len(grid)):
            for z,j in enumerate(grid[i]):
                avg=v[j-105:j-5].reshape(20,5).sum(axis=1).mean()
                vol[i,z]=v[j-5:j].sum()/avg if avg>0 else 0.
        choice=np.full(len(grid),3,dtype=np.int64)
        for z in (2,1,0):choice=np.where(vol[:,z]>=1.25,z,choice)
        starts=grid[np.arange(len(grid)),choice]
        fade=-np.where(c[starts-1]>=o[starts-5],1,-1)
        slot_cache[key]=(starts,choice==3,fade)
        return slot_cache[key]
    def replay(setting,subset,verify=False):
        signal,offset,sl,hold,kind=setting
        starts0,fb,fade=entry_features()
        starts=starts0[subset].copy()
        fallback=fb[subset]
        starts[fallback]+=offset
        assert np.all(starts[fallback]>grid[subset,2][fallback])
        side=fade[subset].copy()
        j=starts[fallback]
        last=c[j-1]
        if signal=="fade5":
            side[fallback]=-np.where(last>=o[j-5],1,-1)
        elif signal=="follow240":
            side[fallback]=np.where(last>=o[j-240],1,-1)
        else:
            mid=np.array([(h[x-120:x].max()+l[x-120:x].min())/2 for x in j])
            side[fallback]=np.where(last<mid,1,-1)
        side=side.astype(np.int8)
        cfg=np.tile(np.array([1.,.75,2.25,60.,.25,.10,0.]),(len(subset),1))
        cfg[fallback]=np.array([0.,sl,sl*3,hold,0.,0.,0.])
        if kind=="baseline_trailing":
            cfg[fallback,0]=2;cfg[fallback,4]=.35;cfg[fallback,5]=.20
        elif kind=="cost_lock":
            # Fixed 0.20% gross lock exceeds the typical modeled
            # round-trip standard fee and 5pt slippage; no guarantee
            # under stress, gaps, funding or real execution.
            cfg[fallback,0]=1;cfg[fallback,4]=.40;cfg[fallback,5]=.20
        limits=np.where(fallback,hold,60)
        hh=np.empty(len(starts),np.int64);gg=np.empty(len(starts));why=np.empty(len(starts),np.int64)
        for limit in np.unique(limits):
            k=np.flatnonzero(limits==limit)
            policy=np.array([0.,0.,0.,float(limit)])
            raw=replay_with_nextbar_exits(o,h,l,c,starts[k],side[k],cfg[k],policy[None,:],FEE,5.)
            hh[k]=raw[4][:,0];gg[k]=raw[2][:,0];why[k]=raw[3][:,0]
        path=pricing(starts,side,hh,gg,o,mh,ml,pre,post,old,slips,modecodes)
        assert np.isfinite(path).all()
        if verify:
            for i,j in enumerate(starts):
                policy=np.array([0.,0.,0.,float(limits[i])])
                end,px,reason,*_=replay_one(o,h,l,c,int(j),int(side[i]),cfg[i],policy)
                assert end-j==hh[i] and abs(side[i]*(px-o[j])-gg[i])<1e-7 and reason==why[i]
                if i:assert starts[i-1]+hh[i-1]<j
        return path,starts,side,hh,gg
    # Standard fees 5 and 20 points, plus historical 5. Cost-adjusted
    # daily log returns are comparable across unequal chronological folds.
    primary=(10,2,0)
    basepath,*_=replay(baseline,development,verify=True)
    basenet,basedd,basemd,basemo,basewins=stats(basepath,years,months)
    print("HYBRID_BASELINE",json.dumps(dict(net_pct=(100*basenet[:,0]).tolist(),positive_months=int((basemo[complete,0]>0).sum()),mark_dd_pct=(100*basemd[:,0]).tolist())),flush=True)
    assert np.allclose(100*basenet[:,0],[-4.17339079797806,-11.965358903743784],atol=1e-6), "Round3 benchmark must reproduce before optimization"
    refpath,*_=replay(monthly_reference,development,verify=True)
    refnet,refdd,refmd,refmo,refwins=stats(refpath,years,months)
    assert np.allclose(100*refnet[:,0],[-1.0723854569066549,-11.913221845791622],atol=1e-6), "Round6 benchmark parity"
    print("ROUND6_REFERENCE",json.dumps(dict(net_pct=(100*refnet[:,0]).tolist(),positive_months=int((refmo[complete,0]>0).sum()),mark_dd_pct=(100*refmd[:,0]).tolist())),flush=True)
    scores={};records={}
    for config in settings:
        path,*_=replay(config,development)
        # Every candidate must keep original primary fills and PnL unchanged.
        event=~entry_features()[1]
        assert np.array_equal(path[event],basepath[event])
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
        net,dd,md,mo,wins=stats(path,years,months)
        annual_positive=bool(np.all(net[:,list(primary)]>0))
        monthly_gate=bool(np.all(mo[complete,:10]>=.01))
        draw_gate=bool(np.all(md[:,:10]<=.02506676))
        records[config]=dict(blocks=block,score=score,development_pass=passes,annual_positive=annual_positive,monthly_gate=monthly_gate,draw_gate=draw_gate,net_pct=(100*net[:,list(primary)]).tolist(),historical_net_pct=(100*net[:,0]).tolist(),positive_months=int((mo[complete,0]>0).sum()),ge1_months=int((mo[complete,0]>=.01).sum()),mark_dd_pct=(100*md[:,0]).tolist(),annual_nonregression=bool(np.all(net[:,0]>=refnet[:,0]-1e-12)),monthly_nonregression_count=int((mo[complete,0]>=refmo[complete,0]-1e-12).sum()))
    def neighbors(cfg):
        out=[]
        # perturb one parameter at a time (including entry time and lookback)
        for dim,values in ((1,offsets),(2,stops),(3,holds)):
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
        stable=records[cfg]["development_pass"] and nb_positive>=.75 and q>0. and records[cfg]["monthly_gate"] and records[cfg]["draw_gate"]
        robust=min(scores[cfg],q)
        ranking.append((stable,robust,scores[cfg],cfg,q,nb_positive))
    ranking.sort(reverse=True)
    # Report counts of candidates with positive both-year historical returns,
    # even when the standard-fee/robustness gates reject every candidate.
    historical_positive=sum(min(r["historical_net_pct"])>0 for r in records.values())
    stable,robust,score,winner,q,npos=ranking[0]
    def config_dict(cfg):
        return dict(zip(("fallback_direction","fallback_minutes_from_21_ist","fallback_stop_pct","fallback_max_hold","fallback_exit"),cfg))
    selection=dict(config=config_dict(winner),development_pass=records[winner]["development_pass"],neighbor_stable=bool(stable),robust_score=robust,neighbor_lower_quartile=q,positive_neighbor_fraction=npos,development_blocks=records[winner]["blocks"],eligible_count=sum(x[0] for x in ranking))
    (OUT/"frozen_selection.json").write_text(json.dumps(selection,indent=2))
    print("ROBUST_FROZEN",json.dumps(selection),flush=True)
    # Freeze training result, even when there are no qualified candidates.
    # An unqualified best candidate is diagnostic only, never accepted.
    trainpath,starts,side,hh,gg=replay(winner,np.arange(n),verify=True)
    net,dd,md,mo,wins=stats(trainpath,years,months)
    def attribution(path,starts,side,gg,years,grid,o):
        result={}
        for y in np.unique(years):
            result[str(int(y))]={}
            for name,mask in [("event",~entry_features()[1]),("fallback",entry_features()[1]),("long",side==1),("short",side==-1)]:
                k=(years==y)&mask
                gross=gg[k]/o[starts[k]]
                net=path[k,0,0]
                result[str(int(y))][name]=dict(trades=int(k.sum()),gross_mean_pct=float(100*gross.mean()) if len(gross) else None,net_mean_pct=float(100*net.mean()) if len(net) else None,net_compounded_pct=float(100*(np.prod(1+net)-1)),win_count=int((net>0).sum()))
        return result
    train_attribution=attribution(trainpath,starts,side,gg,years,grid,o)
    train_counts=np.bincount(years).tolist()
    train_complete=int(complete.sum())
    train_month_counts=counts.tolist()
    train_expected=expcounts.tolist()
    pd.DataFrame([dict(**config_dict(cfg),robust_score=r,neighbor_q=q,neighbor_positive=pos,development_pass=records[cfg]["development_pass"],stable=st,net_2024=records[cfg]["historical_net_pct"][0],net_2025=records[cfg]["historical_net_pct"][1],positive_months=records[cfg]["positive_months"],months_ge1=records[cfg]["ge1_months"]) for st,r,score,cfg,q,pos in ranking]).to_csv(OUT/"development_grid.csv",index=False)
    pd.DataFrame(dict(date=days.astype(str),entry=ix[starts],exit=ix[starts+hh],side=side,gross_points=gg,net_historical5=100*trainpath[:,0,0])).to_csv(OUT/"training_ledger.csv",index=False)
    # 2026 is never opened unless all predeclared development gates pass.
    diagnostics=dict(historical_both_year_positive_count=historical_positive,configurations=len(settings),train_by_year=train_counts,train_complete_months=train_complete,train_period="2024-02-01..2025-12-31",selection=selection,development_gate_count=sum(r["development_pass"] for r in records.values()),annual_positive_count=sum(r["annual_positive"] for r in records.values()),monthly_gate_count=sum(r["monthly_gate"] for r in records.values()),draw_gate_count=sum(r["draw_gate"] for r in records.values()),recovery_rules=0,independent_replay=True,train_attribution=train_attribution,train_scenarios=[dict(mode=mode,slip=slip,net_pct=(100*net[:,k]).tolist(),mark_dd_pct=(100*md[:,k]).tolist(),closed_dd_pct=(100*dd[:,k]).tolist(),wins=wins[:,k].tolist(),monthly_pct=(100*mo[:,k]).tolist(),positive_complete_months=int((mo[complete,k]>0).sum()),ge1_complete_months=int((mo[complete,k]>=.01).sum())) for k,(mode,slip) in enumerate(SC)])
    monthly_best=max(settings,key=lambda x:(records[x]["positive_months"],records[x]["ge1_months"],min(records[x]["historical_net_pct"])))
    annual_best=max(settings,key=lambda x:min(records[x]["historical_net_pct"]))
    diagnostics["monthly_best_diagnostic"]=dict(config=config_dict(monthly_best),**records[monthly_best])
    diagnostics["annual_best_diagnostic"]=dict(config=config_dict(annual_best),**records[annual_best])
    diagnostics["unchanged_primary"]=True
    diagnostics["round6_reference"]=dict(net_pct=(100*refnet[:,0]).tolist(),mark_dd_pct=(100*refmd[:,0]).tolist(),positive_months=int((refmo[complete,0]>0).sum()),months_ge1=int((refmo[complete,0]>=.01).sum()))
    diagnostics["baseline_net_pct"]=(100*basenet[:,0]).tolist()
    diagnostics["annual_nonregression_count"]=sum(r["annual_nonregression"] for r in records.values())
    diagnostics["monthly_nonregression_all_count"]=sum(r["monthly_nonregression_count"]==23 for r in records.values())
    diagnostics["monthly_improvement_without_annual_regression_count"]=sum(r["annual_nonregression"] and r["positive_months"]>10 for r in records.values())
    if not stable:
        diagnostics.update(validation_configurations=0,validation_status="NOT_RUN_DEVELOPMENT_FAILED",all_pass=False)
        (OUT/"summary.json").write_text(json.dumps(diagnostics,indent=2))
        print("EDGE_DEVELOPMENT_FINAL",json.dumps(diagnostics),flush=True)
        return
    # 2026 evaluation: no alternative candidate is evaluated.
    m,ix,o,h,l,c,v,mh,ml,pre,post,old,slips,modecodes,days,grid,years,months,complete,counts,expcounts=dataset(True)
    slot_cache.clear()
    testpath,starts,side,hh,gg=replay(winner,np.arange(len(days)),verify=True)
    validation_attribution=attribution(testpath,starts,side,gg,years,grid,o)
    tn,td,tm,tmo,tw=stats(testpath,years,months)
    scenarios=[]
    for k,(mode,slip) in enumerate(SC):
        scenarios.append(dict(mode=mode,slip=slip,train_net_pct=(100*net[:,k]).tolist(),train_closed_dd_pct=(100*dd[:,k]).tolist(),train_mark_dd_pct=(100*md[:,k]).tolist(),train_wins=wins[:,k].tolist(),train_monthly_pct=(100*mo[:,k]).tolist(),test_net_pct=100*tn[0,k],test_closed_dd_pct=100*td[0,k],test_mark_dd_pct=100*tm[0,k],test_wins=int(tw[0,k]),test_monthly_pct=(100*tmo[:10,k]).tolist(),test_months_positive=int((tmo[:10,k]>0).sum()),test_months_ge1=int((tmo[:10,k]>=.01).sum())))
    passed=bool(stable and np.all(tmo[:10,:10]>=.01) and np.all(tm[0,:10]<=.02506676))
    pd.DataFrame(dict(date=days.astype(str),entry=ix[starts],exit=ix[starts+hh],side=side,gross_points=gg,net_historical5=100*testpath[:,0,0])).to_csv(OUT/"validation_2026_ledger.csv",index=False)
    result=dict(configurations=len(settings),train_by_year=train_counts,train_complete_months=train_complete,train_month_counts=train_month_counts,train_expected=train_expected,test_days=len(days),test_period="2026-01-01..2026-10-31",selection=selection,scenarios=scenarios,all_pass=passed,independent_replay=True,recovery_rules=0,prior_research_exposed=True,validation_configurations=1,train_attribution=train_attribution,validation_attribution=validation_attribution)
    (OUT/"summary.json").write_text(json.dumps(result,indent=2))
    print("ROBUST_FINAL",json.dumps(result),flush=True)
if __name__=="__main__":main()
