#!/usr/bin/env python3
"""Joint 2024/2025 fixed-configuration optimization, no recovery rules.
All parameter combinations use the same calendar-independent rules for all days
and identical fills in every cost scenario. Both years are in-sample.
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

OUT=Path("analysis/btc_common_2024_2025")
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
    schedules=[]
    for a in range(4):
        schedules.append((f"fixed_{18+a}",grid[:,a]))
    rv=np.empty(grid.shape)
    for d in range(n):
        for z,j in enumerate(grid[d]):
            hist=v[j-105:j-5].reshape(20,5).sum(1).mean()
            rv[d,z]=v[j-5:j].sum()/hist if hist>0 else 0.
    for thresh in (1.25,1.5,1.75,2.,2.5):
        chosen=np.full(n,3)
        for a in (2,1,0):chosen=np.where(rv[:,a]>=thresh,a,chosen)
        schedules.append((f"first_rvol_{thresh:g}_else21",grid[np.arange(n),chosen]))
    recipes=[]
    for sl,rr in product((.10,.20,.30,.50,.75,1.0),(1.,2.,3.,5.)):
        tp=sl*rr
        recipes.append((f"fixed_{sl}_{rr}",[0,sl,tp,75,0,0,0]))
        for act,lock in ((.15,.075),(.25,.10),(.40,.20)):
            recipes.append((f"lock_{sl}_{rr}_{act}",[1,sl,tp,75,act,lock,0]))
        for act,dist in ((.25,.15),(.35,.20),(.50,.30)):
            recipes.append((f"trail_{sl}_{rr}_{act}",[2,sl,tp,75,act,dist,0]))
        recipes.append((f"step_{sl}_{rr}",[3,sl,tp,75,.30,.15,.20]))
    best={};rows=[];tested=0
    for name,starts in schedules:
        signs={}
        for look in (5,15,60,240):
            z=np.where(c[starts-1]>=o[starts-look],1,-1).astype(np.int8)
            signs[f"follow{look}"]=z;signs[f"fade{look}"]=-z
        signs["trend_agreement"]=np.where(signs["follow15"]==signs["follow60"],signs["follow60"],signs["follow240"])
        signs["trend_pullback"]=np.where(signs["follow5"]!=signs["follow60"],signs["follow60"],-signs["follow5"])
        loc=np.array([(c[j-1]-l[j-60:j].min())/max(h[j-60:j].max()-l[j-60:j].min(),1e-12) for j in starts])
        signs["range_fade"]=np.where(loc>=.5,-1,1).astype(np.int8)
        signs["range_follow"]=-signs["range_fade"]
        # Same original event/fallback direction relationship, no PnL routing.
        if name.startswith("first_"):
            signs["eventfade_fallbackfollow"]=np.where(starts==grid[:,3],signs["follow5"],signs["fade5"]).astype(np.int8)
            signs["eventfollow_fallbackfade"]=-signs["eventfade_fallbackfollow"]
        for label,rec in recipes:
            cfg=np.tile(np.asarray(rec,float),(n,1))
            raw={}
            for sd in (-1,1):
                raw[sd]=replay_with_nextbar_exits(o,h,l,c,starts,np.full(n,sd,np.int8),cfg,POL,FEE,5.)
            for direction,side in signs.items():
                for p,hold in enumerate(HOLDS):
                    hh=np.where(side>0,raw[1][4][:,p],raw[-1][4][:,p])
                    gg=np.where(side>0,raw[1][2][:,p],raw[-1][2][:,p])
                    path=pricing(starts,side,hh,gg,o,mh,ml,pre,post,old,slips,modecodes)
                    assert np.isfinite(path).all()
                    net,dd,md,mo,wins=stats(path,years,months)
                    # Never optimize different parameters by year or month.
                    # Standard 20pt and historical 5pt are primary comparisons;
                    # all 10 stress cases are mandatory for an all-pass claim.
                    pos=(mo[complete]>0).sum(0);ge=(mo[complete]>=.01).sum(0)
                    primary=net[:,:7];minannual=float(primary.min())
                    both=int(np.all(primary>0))
                    allpass=bool(np.all(mo[complete,:10]>=.01) and np.all(md[:,:10]<=.02506676))
                    # Joint objective favors positive returns in both years, then
                    # minimum positive-month coverage and worst annual return.
                    key=(int(allpass),both,int(pos[:7].min()),int(ge[:7].min()),minannual,-float(md[:,:7].max()))
                    monthlykey=(int(np.all(net[:,0]>0)),int(pos[0]),int(ge[0]),float(net[:,0].min()),-float(md[:,0].max()))
                    edgekey=(float(net[:,:7].min()),int(pos[:7].min()),-float(md[:,:7].max()))
                    fullkey=(float(net[:,:10].min()),int(pos[:10].min()),-float(md[:,:10].max()))
                    settings=dict(schedule=name,direction=direction,recipe=label,recipe_values=rec,max_hold=hold)
                    tested+=1
                    rows.append(dict(**settings,net24_historical5=100*net[0,0],net25_historical5=100*net[1,0],net24_standard20=100*net[0,2],net25_standard20=100*net[1,2],primary_worst_annual=100*minannual,primary_min_positive_months=int(pos[:7].min()),primary_min_ge1=int(ge[:7].min()),historical_positive_months=int(pos[0]),historical_ge1=int(ge[0]),historical_max_mark_dd=100*float(md[:,0].max()),all_pass=allpass))
                    for kind,rank in (("joint",key),("monthly",monthlykey),("gross_edge",edgekey),("severe",fullkey)):
                        if kind not in best or rank>best[kind][0]:
                            best[kind]=(rank,settings,starts.copy(),side.copy(),hh.copy(),gg.copy(),path.copy())
        print("COMMON_PROGRESS",name,tested,{k:v[1] for k,v in best.items()},flush=True)
    pd.DataFrame(rows).to_csv(OUT/"all_candidates.csv",index=False)
    results={}
    for kind,(_,settings,starts,side,hh,gg,path) in best.items():
        rec=np.array(settings["recipe_values"],float)
        policy=np.array([0.,0.,0.,float(settings["max_hold"])])
        for i,j in enumerate(starts):
            end,px,why,*_=replay_one(o,h,l,c,int(j),int(side[i]),rec,policy)
            assert end-j==hh[i] and abs(side[i]*(px-o[j])-gg[i])<1e-7,(kind,i)
            if i:assert starts[i-1]+hh[i-1]<j
        net,dd,md,mo,wins=stats(path,years,months)
        scenarios=[]
        for k,(mode,slip) in enumerate(SC):
            scenarios.append(dict(mode=mode,slip=slip,net_pct=(100*net[:,k]).tolist(),closed_dd_pct=(100*dd[:,k]).tolist(),mark_dd_pct=(100*md[:,k]).tolist(),wins=wins[:,k].tolist(),positive_complete_months=int((mo[complete,k]>0).sum()),ge1_complete_months=int((mo[complete,k]>=.01).sum()),monthly_pct=(100*mo[:,k]).tolist()))
        results[kind]=dict(config=settings,scenarios=scenarios,independent_replay=True)
        pd.DataFrame(dict(date=days.astype(str),entry=ix[starts],exit=ix[starts+hh],side=side,gross_points=gg,net_historical5=100*path[:,0,0])).to_csv(OUT/f"{kind}_ledger.csv",index=False)
    result=dict(configurations=tested,days=n,by_year=np.bincount(years).tolist(),month_counts=counts.tolist(),expected=expcounts.tolist(),complete_months=int(complete.sum()),recovery_rules=0,pnl_switches=0,optimization_period="both years in-sample",results=results)
    (OUT/"summary.json").write_text(json.dumps(result,indent=2))
    print("COMMON_FINAL",json.dumps(result),flush=True)
if __name__=="__main__":main()
