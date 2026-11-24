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

OUT=Path("analysis/btc_step52_portfolio_development")
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
        a=(d+pd.Timedelta(hours=6)).tz_convert("UTC")
        b=(d+pd.Timedelta(hours=23,minutes=59)).tz_convert("UTC")
        ai,bi=ix.get_indexer([a,b])
        j=ix.get_indexer([(d+pd.Timedelta(hours=x)).tz_convert("UTC") for x in (18,19,20,21)])
        if ai<0 or bi<0 or bi-ai!=1079 or np.any(j<0) or not np.array_equal(ix[ai:bi+1],pd.date_range(a,b,freq="min")):
            missing.append(str(d.date()));continue
        # Check actual trade, mark and funding coverage through 23:59 IST.
        assert np.isfinite(np.stack([o[ai:bi+1],h[ai:bi+1],l[ai:bi+1],c[ai:bi+1],v[ai:bi+1]])).all()
        q=slice(ai+240,bi+1)
        if not (np.isfinite(mh[q]).all() and np.isfinite(ml[q]).all() and np.isfinite(mopen[q]).all() and np.isfinite(pre[q]).all() and np.isfinite(post[q]).all()):
            missing.append(str(d.date()));continue
        days.append(d);grid.append(j)
    print("EXPANDED_SESSION_COVERAGE",json.dumps(dict(missing=missing,eligible=len(days),warmup="06:00",entry="10:00-18:00",last_exit="23:59")),flush=True)
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
    # Freeze Round18 entry timing, risk and deadline routes.
    # Reassess confirmed directions only on strong contradictory trend.
    models=("impulse","pullback","volume")
    bases=("monthly","annual")
    trend_looks=(240,480)
    trend_thresholds={"displacement":(.5,1.,1.5),"efficiency":(.25,.4,.55)}
    settings=[("trend",base,model,look,threshold) for base,model,look in product(bases,trend_thresholds,trend_looks) for threshold in trend_thresholds[model]]
    settings += [("risk",base,4.,"anchor","baseline_lock") for base in bases]
    assert len(settings)==26
    r18_models={"monthly":("momentum",15,.25),"annual":("updated_efficiency",15,0.)}
    round12_reference=("reference",0,0.,"round12")
    round13_reference=("reference",0,0.,"round13")
    round15_reference=(4.,3.,300,"delayed_lock")
    round16_reference=(4.,3.,300,"fixed")
    round17_reference=("pullback",.1,60,"delayed_lock")
    deadline_cache={}
    old_primary=(.75,3.,60,"baseline_lock","fade5",60,1.)
    fixed_fallback=("efficiency",120,.55,-30,.75,120,"fixed")
    baseline=("fade5",60,.40,0,.75,60,"baseline_trailing")+old_primary
    monthly_reference=("fade5",60,.40,0,1.0,120,"fixed")+old_primary
    round7_reference=("range_reversion",60,.40,-30,.75,120,"fixed")+old_primary
    round8_reference=fixed_fallback+old_primary
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
    def reference_replay(setting,subset,verify=False):
        signal,look,threshold,offset,sl,hold,kind,psl,prr,phold,pkind,psignal,plook,pthreshold=setting
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
            revert=np.where(last<mid,1,-1)
            if signal=="range_reversion":
                side[fallback]=revert
            else:
                # Kaufman-style directional efficiency on completed 5m closes.
                # Includes prior close at the start of the lookback. A flat
                # price path has efficiency zero, not a synthetic move.
                efficiency=[];trend=[]
                for x in j:
                    closes=c[np.arange(x-look-1,x,5)]
                    move=closes[-1]-closes[0]
                    travel=np.abs(np.diff(closes)).sum()
                    efficiency.append(abs(move)/travel if travel>0 else 0.)
                    trend.append(1 if move>=0 else -1)
                efficiency=np.array(efficiency)
                assert np.isfinite(efficiency).all() and (efficiency>=0).all() and (efficiency<=1+1e-10).all()
                side[fallback]=np.where(efficiency>=threshold,np.array(trend),revert)
        if psignal!="fade5":
            for i in np.flatnonzero(~fallback):
                x=starts[i]
                impulse=c[x-1]-o[x-5]
                shock=1 if impulse>=0 else -1
                # Baseline 5m true range excludes the shock candle.
                hs=h[x-5-plook:x-5].reshape(-1,5).max(axis=1)
                ls=l[x-5-plook:x-5].reshape(-1,5).min(axis=1)
                prior=c[np.arange(x-6-plook,x-6,5)]
                tr=np.maximum(hs-ls,np.maximum(abs(hs-prior),abs(ls-prior))).mean()
                extended=tr>0 and abs(impulse)>=pthreshold*tr
                trend=1 if c[x-6]>=o[x-5-plook] else -1
                mid=(h[x-5-plook:x-5].max()+l[x-5-plook:x-5].min())/2
                revert=1 if c[x-1]<mid else -1
                if psignal=="extension":
                    side[i]=-shock if extended else revert
                elif psignal=="trend_conditioned":
                    side[i]=-shock if extended and shock==trend else trend
                elif psignal=="confirmed":
                    # Wait for the next completed five minutes; enter
                    # at its successor open, never the confirmation close.
                    midpoint=(o[x-5]+c[x-1])/2
                    reclaimed=shock*(c[x+4]-midpoint)<=0
                    side[i]=-shock if extended and reclaimed else trend
                    starts[i]=x+5
                else:
                    raise ValueError(psignal)
        side=side.astype(np.int8)
        cfg=np.tile(np.array([0.,psl,psl*prr,phold,0.,0.,0.]),(len(subset),1))
        if pkind=="baseline_lock":
            cfg[~fallback,0]=1;cfg[~fallback,4]=.25;cfg[~fallback,5]=.10
        elif pkind=="cost_lock":
            cfg[~fallback,0]=1;cfg[~fallback,4]=.40;cfg[~fallback,5]=.20
        elif pkind=="trailing":
            cfg[~fallback,0]=2;cfg[~fallback,4]=.40;cfg[~fallback,5]=.20
        cfg[fallback]=np.array([0.,sl,sl*3,hold,0.,0.,0.])
        if kind=="baseline_trailing":
            cfg[fallback,0]=2;cfg[fallback,4]=.35;cfg[fallback,5]=.20
        elif kind=="cost_lock":
            # Fixed 0.20% gross lock exceeds the typical modeled
            # round-trip standard fee and 5pt slippage; no guarantee
            # under stress, gaps, funding or real execution.
            cfg[fallback,0]=1;cfg[fallback,4]=.40;cfg[fallback,5]=.20
        limits=np.where(fallback,hold,phold)
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
    # Fixed entry time is chosen as a whole-strategy parameter, never
    # selected daily from future returns. All horizons end within the day.
    def direction_at(hour,look,signal,subset):
        starts=grid[subset,0]+(hour-18)*60
        assert (starts>=grid[subset,0]-480).all()
        side=np.where(c[starts-1]>=o[starts-look],1,-1).astype(np.int8)
        if signal=="reversal":side=-side
        return starts,side
    feature_cache={}
    def feature_values(feature,look):
        key=(id(grid),feature,look)
        if key in feature_cache:return feature_cache[key]
        starts,fade=direction_at(18,60,"reversal",np.arange(len(grid)))
        result=[]
        for j,rev in zip(starts,fade):
            k=j-look
            closes=c[np.arange(k-1,j,15)]
            moves=np.diff(closes)
            if feature=="efficiency":
                denom=np.abs(moves).sum()
                val=abs(closes[-1]-closes[0])/denom if denom>0 else 0.
            elif feature=="normalized_impulse":
                hi=h[k:j].reshape(-1,15).max(axis=1)
                lo=l[k:j].reshape(-1,15).min(axis=1)
                tr=np.maximum(hi-lo,np.maximum(abs(hi-closes[:-1]),abs(lo-closes[:-1]))).mean()
                val=abs(c[j-1]-o[j-60])/tr if tr>0 else 0.
            elif feature=="trend_alignment":
                val=float(np.mean(-rev*moves>0))
            else:
                raise ValueError(feature)
            result.append(val)
        result=np.asarray(result)
        assert np.isfinite(result).all()
        feature_cache[key]=result
        return result
    def replay(setting,subset,verify=False):
        update=None
        exit_setting=None
        trend_setting=None
        if len(setting)==5 and setting[0]=="trend":
            _,base,trend_model,trend_look,trend_threshold=setting
            update=r18_models[base]
            trend_setting=(trend_model,trend_look,trend_threshold)
            model,threshold,wait,kind=round17_reference
        elif len(setting)==5:
            _,base,mult,source,protect=setting
            update=r18_models[base]
            exit_setting=(mult,source,protect)
            model,threshold,wait,kind=round17_reference
        elif len(setting)==3:
            update=setting
            model,threshold,wait,kind=round17_reference
        else:
            model,threshold,wait,kind=setting
        anchors,fade=direction_at(18,60,"reversal",subset)
        starts=anchors.copy()
        side=fade.copy()
        if model!="reference":
            flip=feature_values("efficiency",240)[subset]>=.40
            side[flip]=-side[flip]
        risk=[]
        for j in anchors:
            k=j-210
            hi=h[k:j].reshape(14,15).max(axis=1)
            lo=l[k:j].reshape(14,15).min(axis=1)
            prior=c[np.arange(k-1,j-1,15)]
            tr=np.maximum(hi-lo,np.maximum(abs(hi-prior),abs(lo-prior))).mean()
            risk.append(np.clip(400*tr/c[j-1],.25,1.5))
        risk=np.asarray(risk)
        if kind=="round12":risk=np.ones(len(starts))
        assert np.isfinite(risk).all() and (risk>0).all()
        confirmed=np.zeros(len(starts),bool)
        if model in models:
            for i,(j,sd) in enumerate(zip(anchors,side)):
                starts[i]=j+wait
                ref=c[j-1]
                # All thresholds computed from pre-entry data. Pullback
                # requires an improved close and a directional rebound.
                for d in range(5,wait+1,5):
                    z=j+d
                    move=100*sd*(c[z-1]-o[z-5])/ref
                    improved=100*sd*(c[z-1]-ref)/ref
                    if model=="impulse":
                        ok=move>=threshold*risk[i]
                    elif model=="pullback":
                        ok=improved<=-threshold*risk[i] and move>0
                    else:
                        prev=v[z-65:z-5].reshape(12,5).sum(axis=1).mean()
                        ok=prev>0 and v[z-5:z].sum()>=threshold*prev and move>0
                    if ok:
                        starts[i]=z;confirmed[i]=True;break
        if model=="pullback" and threshold==.1 and wait==60 and kind=="delayed_lock":
            eligible=(starts==anchors+60)&~confirmed
            if update is None:
                deadline_cache["reference_mask"]=eligible.copy()
            else:
                method,look,strength=update
                for i in np.flatnonzero(eligible):
                    j=starts[i]
                    delta=c[j-1]-o[j-look]
                    normalized=100*abs(delta)/c[j-1]
                    if normalized<strength*risk[i] or delta==0:continue
                    direction=1 if delta>0 else -1
                    if method=="reversal":direction=-direction
                    elif method=="updated_efficiency":
                        closes=c[np.arange(j-241,j,15)]
                        denom=np.abs(np.diff(closes)).sum()
                        er=abs(closes[-1]-closes[0])/denom if denom>0 else 0.
                        if er<.40:direction=-direction
                    side[i]=direction
        # Confirmed pullback/rebound was evaluated without future data.
        # A strong contradictory broader trend can override direction at
        # that same entry open; the deadline route and all timings stay fixed.
        if trend_setting is not None:
            trend_model,look,cut=trend_setting
            for i in np.flatnonzero(confirmed):
                j=starts[i]
                delta=c[j-1]-c[j-look-1]
                if delta*side[i]>=0:continue
                if trend_model=="displacement":
                    strength=100*abs(delta)/c[j-1]/risk[i]
                else:
                    closes=c[np.arange(j-look-1,j,15)]
                    travel=np.abs(np.diff(closes)).sum()
                    strength=abs(delta)/travel if travel>0 else 0.
                if strength>=cut:side[i]=-side[i]
        # Only now may risk change; original signal and entry are immutable.
        if exit_setting is not None:
            mult,source,protect=exit_setting
            newrisk=[]
            for j in (anchors if source=="anchor" else starts):
                k=j-210
                hi=h[k:j].reshape(14,15).max(axis=1)
                lo=l[k:j].reshape(14,15).min(axis=1)
                prior=c[np.arange(k-1,j-1,15)]
                tr=np.maximum(hi-lo,np.maximum(abs(hi-prior),abs(lo-prior))).mean()
                newrisk.append(np.clip(100*mult*tr/c[j-1],.25,1.5))
            risk=np.asarray(newrisk)
        limits=300-(starts-anchors)
        assert np.all(limits>=240)
        cfg=np.zeros((len(starts),7))
        cfg[:,1]=risk;cfg[:,2]=risk*3;cfg[:,3]=limits
        if kind in ("round13","delayed_lock"):
            cfg[:,0]=1;cfg[:,4]=1.5*risk;cfg[:,5]=.5*risk
        if exit_setting is not None:
            if protect=="late_lock":
                cfg[:,0]=1;cfg[:,4]=2*risk;cfg[:,5]=.5*risk
            elif protect=="late_trail":
                cfg[:,0]=2;cfg[:,4]=2*risk;cfg[:,5]=risk
        hh=np.empty(len(starts),np.int64);gg=np.empty(len(starts));why=np.empty(len(starts),np.int64)
        for limit in np.unique(limits):
            ids=np.flatnonzero(limits==limit)
            policy=np.array([0.,0.,0.,float(limit)])
            raw=replay_with_nextbar_exits(o,h,l,c,starts[ids],side[ids],cfg[ids],policy[None,:],FEE,5.)
            hh[ids]=raw[4][:,0];gg[ids]=raw[2][:,0];why[ids]=raw[3][:,0]
        path=pricing(starts,side,hh,gg,o,mh,ml,pre,post,old,slips,modecodes)
        assert np.isfinite(path).all()
        assert (starts+hh<=anchors+300).all()
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
    basepath,*_=reference_replay(baseline,development,verify=True)
    basenet,basedd,basemd,basemo,basewins=stats(basepath,years,months)
    print("HYBRID_BASELINE",json.dumps(dict(net_pct=(100*basenet[:,0]).tolist(),positive_months=int((basemo[complete,0]>0).sum()),mark_dd_pct=(100*basemd[:,0]).tolist())),flush=True)
    assert np.allclose(100*basenet[:,0],[-4.17339079797806,-11.965358903743784],atol=1e-6), "Round3 benchmark must reproduce before optimization"
    refpath,*_=reference_replay(monthly_reference,development,verify=True)
    refnet,refdd,refmd,refmo,refwins=stats(refpath,years,months)
    assert np.allclose(100*refnet[:,0],[-1.0723854569066549,-11.913221845791622],atol=1e-6), "Round6 benchmark parity"
    print("ROUND6_REFERENCE",json.dumps(dict(net_pct=(100*refnet[:,0]).tolist(),positive_months=int((refmo[complete,0]>0).sum()),mark_dd_pct=(100*refmd[:,0]).tolist())),flush=True)
    r7path,*_=reference_replay(round7_reference,development,verify=True)
    r7net,r7dd,r7md,r7mo,r7wins=stats(r7path,years,months)
    assert np.allclose(100*r7net[:,0],[-15.747765120457935,4.172178435601581],atol=1e-6), "Round7 benchmark parity"
    print("ROUND7_REFERENCE",json.dumps(dict(net_pct=(100*r7net[:,0]).tolist(),positive_months=int((r7mo[complete,0]>0).sum()),mark_dd_pct=(100*r7md[:,0]).tolist())),flush=True)
    r8path,r8starts,r8side,*_=reference_replay(round8_reference,development,verify=True)
    r8net,r8dd,r8md,r8mo,r8wins=stats(r8path,years,months)
    assert np.allclose(100*r8net[:,0],[-11.682655337715431,2.3359734350629546],atol=1e-6), "Round8 benchmark parity"
    print("ROUND8_REFERENCE",json.dumps(dict(net_pct=(100*r8net[:,0]).tolist(),positive_months=int((r8mo[complete,0]>0).sum()),mark_dd_pct=(100*r8md[:,0]).tolist())),flush=True)
    r12path,r12starts,r12side,*_=replay(round12_reference,development,verify=True)
    r12net,r12dd,r12md,r12mo,r12wins=stats(r12path,years,months)
    assert np.allclose(100*r12net[:,0],[-15.039595885370115,-1.2665379268715693],atol=1e-6), "Round12 benchmark parity"
    print("ROUND12_REFERENCE",json.dumps(dict(net_pct=(100*r12net[:,0]).tolist(),positive_months=int((r12mo[complete,0]>0).sum()),months_ge1=int((r12mo[complete,0]>=.01).sum()),mark_dd_pct=(100*r12md[:,0]).tolist())),flush=True)
    r13path,r13starts,r13side,*_=replay(round13_reference,development,verify=True)
    r13net,r13dd,r13md,r13mo,r13wins=stats(r13path,years,months)
    assert np.allclose(100*r13net[:,0],[-15.651044549390425,2.0413279520694605],atol=1e-6), "Round13 benchmark parity"
    print("ROUND13_REFERENCE",json.dumps(dict(net_pct=(100*r13net[:,0]).tolist(),positive_months=int((r13mo[complete,0]>0).sum()),months_ge1=int((r13mo[complete,0]>=.01).sum()),mark_dd_pct=(100*r13md[:,0]).tolist())),flush=True)
    r15path,r15starts,r15side,*_=replay(round15_reference,development,verify=True)
    r15net,r15dd,r15md,r15mo,r15wins=stats(r15path,years,months)
    assert np.allclose(100*r15net[:,0],[6.083832372068287,10.414607298018929],atol=1e-6), "Round15 benchmark parity"
    print("ROUND15_REFERENCE",json.dumps(dict(net_pct=(100*r15net[:,0]).tolist(),positive_months=int((r15mo[complete,0]>0).sum()),months_ge1=int((r15mo[complete,0]>=.01).sum()),mark_dd_pct=(100*r15md[:,0]).tolist())),flush=True)
    r16path,r16starts,r16side,*_=replay(round16_reference,development,verify=True)
    r16net,r16dd,r16md,r16mo,r16wins=stats(r16path,years,months)
    assert np.allclose(100*r16net[:,0],[1.176531899989186,15.666520564367993],atol=1e-6), "Round16 benchmark parity"
    print("ROUND16_REFERENCE",json.dumps(dict(net_pct=(100*r16net[:,0]).tolist(),positive_months=int((r16mo[complete,0]>0).sum()),months_ge1=int((r16mo[complete,0]>=.01).sum()),mark_dd_pct=(100*r16md[:,0]).tolist())),flush=True)
    r17path,r17starts,r17side,*_=replay(round17_reference,development,verify=True)
    r17net,r17dd,r17md,r17mo,r17wins=stats(r17path,years,months)
    assert np.allclose(100*r17net[:,0],[7.830714041494513,24.859099890128423],atol=1e-6), "Round17 benchmark parity"
    eligible_deadline=deadline_cache["reference_mask"].copy()
    assert int((r17starts==r15starts+60).sum())==274
    assert eligible_deadline.sum()<=274
    def deadline_attribution(path):
        result={}
        for year in (0,1):
            for name,mask in (("confirmed",~eligible_deadline),("unconfirmed_deadline",eligible_deadline)):
                ix0=(years==year)&mask
                returns=path[ix0,0,0]
                result[str(year)+"_"+name]=dict(trades=int(ix0.sum()),mean_net_pct=float(100*returns.mean()),compounded_net_pct=float(100*(np.prod(1+returns)-1)),win_count=int((returns>0).sum()))
        return result
    r17attr=deadline_attribution(r17path)
    print("ROUND17_REFERENCE",json.dumps(dict(net_pct=(100*r17net[:,0]).tolist(),positive_months=int((r17mo[complete,0]>0).sum()),months_ge1=int((r17mo[complete,0]>=.01).sum()),mark_dd_pct=(100*r17md[:,0]).tolist(),deadline_entries=274,unconfirmed_deadline=int(eligible_deadline.sum()),attribution=r17attr)),flush=True)
    r18refs={}
    for base,expected in (("monthly",[10.036064854717175,22.07006401698162]),("annual",[15.041397633662811,29.77487489717634])):
        p,st,sd,*_=replay(r18_models[base],development,verify=True)
        net0,dd0,md0,mo0,w0=stats(p,years,months)
        assert np.allclose(100*net0[:,0],expected,atol=1e-6),("Round18 parity",base)
        p2,st2,sd2,*_=replay(("risk",base,4.,"anchor","baseline_lock"),development,verify=True)
        assert np.array_equal(p,p2) and np.array_equal(st,st2) and np.array_equal(sd,sd2)
        r18refs[base]=(p,st,sd,net0,md0,mo0)
        print("ROUND18_REFERENCE",json.dumps(dict(base=base,net_pct=(100*net0[:,0]).tolist(),mark_dd_pct=(100*md0[:,0]).tolist(),positive_months=int((mo0[complete,0]>0).sum()),months_ge1=int((mo0[complete,0]>=.01).sum()),worst_month_pct=float(100*mo0[complete,0].min()))),flush=True)
    # Fixed predeclared net allocations, no return-dependent switching.
    # Both signals have the same entry time and risk/exit parameters.
    # Agreement: full 1x. Disagreement: net signed exposure is 0.5x
    # for 75/25 allocations. Do NOT charge two fictional opposing legs.
    pairs={"R18":(r18_models["monthly"],r18_models["annual"]),
           "R20":(("trend","monthly","displacement",240,1.5),("trend","annual","displacement",240,1.5))}
    weights=(0.,.25,.75,1.)
    primary=(10,2,0)
    def leg_pair(name,subset,verify=True):
        left,right=pairs[name]
        p,st,sd,hh,gg=replay(left,subset,verify)
        q,st2,sd2,hh2,gg2=replay(right,subset,verify)
        assert np.array_equal(st,st2)
        agree=sd==sd2
        assert np.array_equal(p[agree],q[agree])
        assert np.array_equal(hh[agree],hh2[agree]) and np.array_equal(gg[agree],gg2[agree])
        return p,q,st,sd,sd2,hh,hh2,gg,gg2
    def netted(pair,w):
        p,q,st,sd,sd2,hh,hh2,gg,gg2=pair
        signed=w*sd+(1-w)*sd2
        size=np.abs(signed)
        direction=np.sign(signed).astype(np.int8)
        assert (size>0).all() and (size<=1).all()
        choose=direction==sd
        path=np.where(choose[:,None,None],p,q)*size[:,None,None]
        duration=np.where(choose,hh,hh2)
        gross=np.where(choose,gg,gg2)
        # Cost and funding are linear in notional; no fixed lot rounding
        # or market impact is assumed. 1x full exposure is not preserved
        # on disagreements, so these are separate research diagnostics.
        assert np.isfinite(path).all()
        return path,st,direction,duration,gross,size
    def summarize(path,yy,mm,mask):
        net,dd,md,mo,wins=stats(path,yy,mm)
        return dict(net_pct=(100*net[:,0]).tolist(),positive_months=int((mo[mask,0]>0).sum()),
            ge1_months=int((mo[mask,0]>=.01).sum()),mark_dd_pct=(100*md[:,0]).tolist(),
            worst_month_pct=float(100*mo[mask,0].min()),monthly_pct=(100*mo[:,0]).tolist(),
            primary_costs_pct=(100*net[:,list(primary)]).tolist(),
            all_scenarios=[dict(mode=mode,slip=slip,net_pct=(100*net[:,k]).tolist(),mark_dd_pct=(100*md[:,k]).tolist(),
                positive_months=int((mo[mask,k]>0).sum()),months_ge1=int((mo[mask,k]>=.01).sum())) for k,(mode,slip) in enumerate(SC)])
    rows=[]; paths={}; ledgers=[]
    for name in pairs:
        pair=leg_pair(name,development)
        for w in weights:
            path,st,sd,hh,gg,size=netted(pair,w)
            assert len(path)==500
            key=(name,w)
            paths[key]=path
            result=summarize(path,years,months,complete)
            if name=="R20" and w in (0.,1.):
                expected=[18.629525561710047,32.83441105649572] if w==0. else [13.468077030498371,24.947953709622794]
                assert np.allclose(result["net_pct"],expected,atol=1e-6), "Round20 parity"
            result.update(pair=name,monthly_weight=w,annual_weight=1-w,days=len(path),
                reduced_exposure_days=int((size<1).sum()),mean_exposure=float(size.mean()),
                disagreements=int((pair[3]!=pair[4]).sum()))
            blocks=[]
            for f in folds:
                n0,d0,m0,_,_=stats(path[f],np.zeros(len(f),np.int64),months[f])
                blocks.append(dict(net_pct=(100*n0[0,list(primary)]).tolist(),mark_dd_pct=(100*m0[0,list(primary)]).tolist()))
            result["blocks"]=blocks
            net,dd,md,mo,wins=stats(path,years,months)
            result["monthly_gate"]=bool(np.all(mo[complete,:10]>=.01))
            result["draw_gate"]=bool(np.all(md[:,:10]<=.02506676))
            result["strict_full_exposure"]=bool(np.all(size==1))
            result["annual_primary_pass"]=bool(np.all(net[:,list(primary)]>0))
            rows.append(result)
            ledgers.append(pd.DataFrame(dict(pair=name,monthly_weight=w,date=days.astype(str),entry=ix[st],
                exit=ix[st+hh],direction=sd,exposure=size,gross_points=gg,net_historical5=100*path[:,0,0])))
            print("PORTFOLIO_CANDIDATE",json.dumps(result),flush=True)
    # Keep a chronological comparison with no retuning of allocations.
    for row in rows:
        name=row["pair"];w=row["monthly_weight"]
        p=paths[(name,w)]
        a=paths[(name,1.)];b=paths[(name,0.)]
        _,_,_,pm,_=stats(p,years,months)
        _,_,_,am,_=stats(a,years,months)
        _,_,_,bm,_=stats(b,years,months)
        row["monthly_base_positive_preserved"]=int(((pm[complete,0]>0)&(am[complete,0]>0)).sum())
        row["annual_base_positive_preserved"]=int(((pm[complete,0]>0)&(bm[complete,0]>0)).sum())
        row["annual_nonregression_vs_monthly"]=bool(np.all(np.array(row["net_pct"])>=np.array(next(x["net_pct"] for x in rows if x["pair"]==name and x["monthly_weight"]==1.))-1e-9))
        row["all_blocks_primary_positive"]=all(min(x["net_pct"])>0 for x in row["blocks"])
        row["walk_forward_diagnostic_pass"]=all(min(x["net_pct"])>0 and max(x["mark_dd_pct"])<=2.506676 for x in row["blocks"][1:])
    # This round is an exposure-relaxation diagnostic, not a new full-1x
    # strategy or a reason to unlock validation. No 2026 data is opened.
    result=dict(configurations=len(rows),new_allocations=4,controls=4,development_days=500,
        complete_months=23,recovery_rules=0,independent_leg_replay=True,
        strict_full_exposure_required=True,netting_model="same-time net position, proportional costs, no lot rounding",
        selection_policy="predeclared fixed allocations; no monthly weight tuning",
        validation_status="NOT_RUN_DIAGNOSTIC_ONLY",all_pass=False,rows=rows)
    pd.concat(ledgers,ignore_index=True).to_csv(OUT/"portfolio_daily_ledger.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(result,indent=2))
    print("PORTFOLIO_FINAL",json.dumps(result),flush=True)
if __name__=="__main__":main()
