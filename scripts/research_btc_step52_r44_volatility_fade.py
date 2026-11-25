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

OUT=Path("analysis/btc_step52_r44_volatility_fade")
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
    # Round20 entry pair, full 1x exposure. Choose one of two independently
    # replayed legs using completed market data only on disagreement days.
    primary=(10,2,0)
    def leg_pair(subset):
        p,st,sd,hh,gg=replay(("trend","monthly","displacement",240,1.5),subset,True)
        q,st2,sd2,hh2,gg2=replay(("trend","annual","displacement",240,1.5),subset,True)
        assert np.array_equal(st,st2)
        agree=sd==sd2
        assert np.array_equal(p[agree],q[agree])
        assert np.array_equal(hh[agree],hh2[agree]) and np.array_equal(gg[agree],gg2[agree])
        return p,q,st,sd,sd2,hh,hh2,gg,gg2
    # Trend versus range selection: predeclared, coarse parameters.
    # Each feature is dimensionless and uses only completed observations.
    looks=(60,120,240)
    cuts={"efficiency":(.25,.4,.55),"volatility":(.8,1.,1.25),"range":(.25,.5,.75)}
    settings=[(model,look,cut) for model,look in product(cuts,looks) for cut in cuts[model]]
    controls=[("monthly",0,0.),("annual",0,0.)]
    settings+=controls
    assert len(settings)==29
    def feature(j,model,look):
        if model=="efficiency":
            closes=c[np.arange(j-look-1,j,5)]
            travel=np.abs(np.diff(closes)).sum()
            return abs(closes[-1]-closes[0])/travel if travel>0 else 0.
        if model=="volatility":
            # Current 5m true-range mean versus preceding equal window.
            def trmean(end):
                hi=h[end-look:end].reshape(-1,5).max(axis=1)
                lo=l[end-look:end].reshape(-1,5).min(axis=1)
                prior=c[np.arange(end-look-1,end-1,5)]
                return np.maximum(hi-lo,np.maximum(abs(hi-prior),abs(lo-prior))).mean()
            prev=trmean(j-look)
            return trmean(j)/prev if prev>0 else 1.
        # Absolute distance from the range midpoint, normalized to half-range.
        hi=h[j-look:j].max();lo=l[j-look:j].min()
        return abs(2*c[j-1]-hi-lo)/(hi-lo) if hi>lo else 0.
    def choose(pair,cfg):
        p,q,st,sd,sd2,hh,hh2,gg,gg2=pair
        model,look,cut=cfg
        disagree=sd!=sd2
        use_monthly=np.ones(len(st),bool)
        if model=="annual":use_monthly[:]=False
        elif model!="monthly":
            for i in np.flatnonzero(disagree):
                # High directional efficiency, expansion, or range-edge
                # displacement favors the annual regime-adaptive signal.
                use_monthly[i]=feature(st[i],model,look)<cut
        path=np.where(use_monthly[:,None,None],p,q)
        direction=np.where(use_monthly,sd,sd2)
        duration=np.where(use_monthly,hh,hh2)
        gross=np.where(use_monthly,gg,gg2)
        assert np.array_equal(path[~disagree],p[~disagree])
        assert np.isfinite(path).all()
        return path,st,direction,duration,gross,use_monthly
    def summarize(path,yy,mm,mask):
        net,dd,md,mo,wins=stats(path,yy,mm)
        return dict(net_pct=(100*net[:,0]).tolist(),positive_months=int((mo[mask,0]>0).sum()),
            ge1_months=int((mo[mask,0]>=.01).sum()),mark_dd_pct=(100*md[:,0]).tolist(),
            worst_month_pct=float(100*mo[mask,0].min()),monthly_pct=(100*mo[:,0]).tolist(),
            primary_costs_pct=(100*net[:,list(primary)]).tolist(),
            all_scenarios=[dict(mode=mode,slip=slip,net_pct=(100*net[:,k]).tolist(),mark_dd_pct=(100*md[:,k]).tolist(),
                positive_months=int((mo[mask,k]>0).sum()),months_ge1=int((mo[mask,k]>=.01).sum())) for k,(mode,slip) in enumerate(SC)])
    # Retain 3 frozen entry families, including the 16-month R20 control.
    pair=leg_pair(development)
    assert int((pair[3]!=pair[4]).sum())==147
    bases={"R20_monthly":("monthly",0,0.),"R22_range":("range",60,.75),"R22_volatility":("volatility",120,1.)}
    expected={"R20_monthly":[13.468077030498371,24.947953709622794],
              "R22_range":[19.782826608220883,28.65859731084297],
              "R22_volatility":[27.22601760758696,31.354832509782614]}
    # Freeze all three R24 reported candidates, including their TP.
    holding={"R20_monthly":300,"R22_range":240,"R22_volatility":240}
    rewards={"R20_monthly":4.,"R22_range":3.,"R22_volatility":4.}
    lock_activation={"R20_monthly":1.5,"R22_range":1.,"R22_volatility":1.5}
    expected_frozen={"R20_monthly":[19.738356779379274,30.06195218041594],
        "R22_range":[17.763695675779488,13.503874856586751],
        "R22_volatility":[33.55893954236748,30.11187940798059]}
    # Freeze R36 and diagnose gross loss, costs, exit types and
    # pre-entry agreement across both years. Diagnostics never route orders.
    # R44: scale the R43 C01 activation using pre-entry true range expansion.
    # Keep zero R floor, original stop, target, direction and exposure; no future observations.
    looks=(60,120,240)
    cuts=(.5,1.)
    research_bases=("R32_consensus","R35_adaptive","R36_winner")
    original=("R36_winner","original",0,0.)
    c01=("R36_winner","fade",.75,0.)
    controls=[original,c01]
    settings=controls+[("R36_winner","adaptive",look,cut) for look,cut in product(looks,cuts)]
    assert len(settings)==8
    # Predeclared paired month-block bootstrap; exploratory only because
    # the reference families and development sample have prior exposure.
    rng=np.random.default_rng(20261124)
    month_ids=np.flatnonzero(complete)
    boot=rng.integers(0,len(month_ids),size=(20000,len(month_ids)))
    refs={};rows={};paths={};ledgers=[]
    for base,entry_cfg in bases.items():
        bp,st,sd,bh,bg,_=choose(pair,entry_cfg)
        ref=summarize(bp,years,months,complete)
        assert np.allclose(ref["net_pct"],expected[base],atol=1e-6),("reference parity",base)
        refs[base]=(bp,st,sd,bh,bg,ref)
        print("SESSION_REFERENCE",json.dumps(dict(base=base,**ref)),flush=True)
    # 18:00 anchor and initial risk are frozen across all exit experiments.
    anchors=grid[:,0]
    risk=[]
    for j in anchors:
        k=j-210
        hi=h[k:j].reshape(14,15).max(axis=1)
        lo=l[k:j].reshape(14,15).min(axis=1)
        prior=c[np.arange(k-1,j-1,15)]
        tr=np.maximum(hi-lo,np.maximum(abs(hi-prior),abs(lo-prior))).mean()
        risk.append(np.clip(400*tr/c[j-1],.25,1.5))
    risk=np.asarray(risk)
    # All source strategies share entry time. Freeze votes before
    # replay; later updates to refs must not affect the vote arrays.
    common_st=refs["R20_monthly"][1].copy()
    votes=np.stack([refs[k][2].copy() for k in bases])
    assert all(np.array_equal(refs[k][1],common_st) for k in bases)
    assert np.isin(votes,(-1,1)).all()
    vote_sets={0:votes.sum(axis=0)}
    unanimous=abs(vote_sets[0])==3
    assert int(unanimous.sum())==373
    print("HOLDING_DIAGNOSTIC",json.dumps(dict(unanimous=int(unanimous.sum()),split=int((~unanimous).sum()))),flush=True)
    # Ratio of mean 5m true range over recent window to the immediately
    # preceding equally long window; both wholly before actual entry.
    ratios={}
    for look in looks:
        rr=[]
        for j in common_st:
            k=j-2*look
            assert ix[j]-ix[k-1]==pd.Timedelta(minutes=2*look+1)
            hi=h[k:j].reshape(-1,5).max(axis=1)
            lo=l[k:j].reshape(-1,5).min(axis=1)
            prior=c[np.arange(k-1,j-1,5)]
            tr=np.maximum(hi-lo,np.maximum(abs(hi-prior),abs(lo-prior)))/prior
            n=look//5
            older=tr[:n].mean()
            recent=tr[n:].mean()
            rr.append(recent/older if older>0 and recent>0 else 1.)
        ratios[look]=np.asarray(rr)
        assert np.isfinite(ratios[look]).all() and (ratios[look]>0).all()
    def activation_multiple(base):
        if base in ("R35_adaptive","R36_winner"):return np.clip(1.5*ratios[60],1.,2.5)
        return np.full(len(common_st),lock_activation[base])
    def lock_multiple(base):
        if base=="R36_winner":return np.clip(.5/ratios[60],.25,.75)
        return np.full(len(common_st),.5)
    def stop_distance(mode,look,cut):return risk.copy()
    exit_diagnostics={}
    def fade_limit(st,sd,limits,mode,look,cut):
        result=limits.copy()
        trigger=.75*np.clip(ratios[look]**cut,.75,1.25) if mode=="adaptive" else np.full(len(st),look)
        floor=0. if mode=="adaptive" else cut
        for i,j in enumerate(st):
            offsets=np.arange(5,int(limits[i]),5,dtype=np.int64)
            moves=100*sd[i]*(c[j+offsets-1]-o[j])/o[j]
            if len(moves):
                prior_peak=np.r_[-np.inf,np.maximum.accumulate(moves)[:-1]]
                hit=offsets[(prior_peak>=trigger[i]*risk[i])&(moves<=floor*risk[i])]
                if len(hit):result[i]=hit[0]
            # Independent chronological scalar check: only prior completed closes arm.
            armed=False
            check=int(limits[i])
            for t in range(5,int(limits[i]),5):
                move=100*sd[i]*(c[j+t-1]-o[j])/o[j]
                if armed and move<=floor*risk[i]:
                    check=t;break
                if move>=trigger[i]*risk[i]:armed=True
            assert result[i]==check
        return result
    def exit_replay(cfg):
        base,mode,look,cut=cfg
        bp,st,sd,bh,bg,ref=refs[base]
        st=st.copy();sd=sd.copy()
        if base in research_bases:
            sd=np.sign(vote_sets[0]).astype(np.int8)
        limits=np.minimum(holding[base],300-(st-anchors))
        assert np.all(limits>0)
        original_limits=limits.copy()
        if mode in ("fade","adaptive"):limits=fade_limit(st,sd,limits,mode,look,cut)
        params=np.zeros((len(st),7))
        params[:,0]=1
        params[:,1]=stop_distance(mode,look,cut);params[:,2]=rewards[base]*risk;params[:,3]=limits
        params[:,4]=activation_multiple(base)*risk;params[:,5]=lock_multiple(base)*risk
        assert np.all(params[:,5]<params[:,4])
        hh=np.empty(len(st),np.int64);gg=np.empty(len(st));why=np.empty(len(st),np.int64)
        for limit0 in np.unique(limits):
            ids=np.flatnonzero(limits==limit0)
            policy=np.array([0.,0.,0.,float(limit0)])
            raw=replay_with_nextbar_exits(o,h,l,c,st[ids],sd[ids],params[ids],policy[None,:],FEE,5.)
            hh[ids]=raw[4][:,0];gg[ids]=raw[2][:,0];why[ids]=raw[3][:,0]
        p=pricing(st,sd,hh,gg,o,mh,ml,pre,post,old,slips,modecodes)
        assert np.isfinite(p).all() and np.all(st+hh<=anchors+300)
        for i,j in enumerate(st):
            policy=np.array([0.,0.,0.,float(limits[i])])
            end,px,reason,*_=replay_one(o,h,l,c,int(j),int(sd[i]),params[i],policy)
            assert end-j==hh[i] and abs(sd[i]*(px-o[j])-gg[i])<1e-7 and reason==why[i]
            if i:assert st[i-1]+hh[i-1]<j
        exit_diagnostics[cfg]=dict(initial_stop_exits=int(((why==2)&(gg<0)).sum()),early_fade_exits=int(((why==3)&(limits<original_limits)).sum()))
        return p,st,sd,hh,gg
    # Establish exact R24 reference parity before testing.
    for base in bases:
        p,st,sd,hh,gg=exit_replay((base,"original",0,0.))
        ref=summarize(p,years,months,complete)
        assert np.allclose(ref["net_pct"],expected_frozen[base],atol=1e-6),("frozen parity",base)
        refs[base]=(p,st,sd,hh,gg,ref)
        print("R24_REFERENCE",json.dumps(dict(base=base,holding=holding[base],**ref)),flush=True)
    base="R32_consensus"
    refs[base]=refs["R20_monthly"]
    holding[base]=holding["R20_monthly"]
    rewards[base]=rewards["R20_monthly"]
    lock_activation[base]=lock_activation["R20_monthly"]
    p,st,sd,hh,gg=exit_replay((base,"original",0,0.))
    ref=summarize(p,years,months,complete)
    assert np.allclose(ref["net_pct"],[44.97144485838418,32.064183121536736],atol=1e-6),("R32 parity",ref["net_pct"])
    assert ref["positive_months"]==17 and ref["ge1_months"]==15
    refs[base]=(p,st,sd,hh,gg,ref)
    print("LOCK_DISTANCE_REFERENCE",json.dumps(dict(base=base,**ref)),flush=True)
    base="R35_adaptive"
    refs[base]=refs["R32_consensus"]
    holding[base]=holding["R32_consensus"]
    rewards[base]=rewards["R32_consensus"]
    lock_activation[base]=lock_activation["R32_consensus"]
    p,st,sd,hh,gg=exit_replay((base,"original",0,0.))
    ref=summarize(p,years,months,complete)
    assert np.allclose(ref["net_pct"],[44.20116138678174,33.005156444119855],atol=1e-6),("R35 parity",ref["net_pct"])
    assert ref["positive_months"]==18 and ref["ge1_months"]==14
    refs[base]=(p,st,sd,hh,gg,ref)
    print("LOCK_DISTANCE_REFERENCE",json.dumps(dict(base=base,**ref)),flush=True)
    base="R36_winner"
    refs[base]=refs["R35_adaptive"]
    holding[base]=holding["R35_adaptive"]
    rewards[base]=rewards["R35_adaptive"]
    lock_activation[base]=lock_activation["R35_adaptive"]
    p,st,sd,hh,gg=exit_replay((base,"original",0,0.))
    ref=summarize(p,years,months,complete)
    assert np.allclose(ref["net_pct"],[46.25504686567101,34.83414460428196],atol=1e-6),("R36 parity",ref["net_pct"])
    assert ref["positive_months"]==18 and ref["ge1_months"]==14
    refs[base]=(p,st,sd,hh,gg,ref)
    # Classify exit using original independent replay, not inference
    # from realized PnL. Attribute costs and gross log contribution.
    reasons=[]
    favorable=[]
    adverse=[]
    for i,j in enumerate(st):
        limit=int(min(holding[base],300-(j-anchors[i])))
        recipe=np.array([1.,risk[i],4*risk[i],limit,activation_multiple(base)[i]*risk[i],lock_multiple(base)[i]*risk[i],0.])
        end,px,why,_,_,_=replay_one(o,h,l,c,int(j),int(sd[i]),recipe,np.array([0.,0.,0.,float(limit)]))
        assert end-j==hh[i] and abs(sd[i]*(px-o[j])-gg[i])<1e-7
        kind="target" if why==1 else ("timeout" if why==3 else ("initial_stop" if gg[i]<0 else "protected_stop"))
        reasons.append(kind)
        # End-minute extremes are excluded: ordering within exit candle unknown.
        hi=h[j:end].max() if end>j else o[j]
        lo=l[j:end].min() if end>j else o[j]
        favorable.append(max(0.,100*(hi-o[j] if sd[i]>0 else o[j]-lo)/o[j]/risk[i]))
        adverse.append(max(0.,100*(o[j]-lo if sd[i]>0 else hi-o[j])/o[j]/risk[i]))
    reasons=np.asarray(reasons)
    gross=gg/o[st]
    def loss_diag(mask):
        vals=p[mask,0,0];g=gross[mask];lose=vals<0
        return dict(trades=int(mask.sum()),loss_days=int(lose.sum()),gross_log_pct=float(100*np.log1p(g).sum()),
            net_log_pct=float(100*np.log1p(vals).sum()),cost_drag_log_pct=float(100*(np.log1p(g)-np.log1p(vals)).sum()),
            gross_positive_net_negative=int(((g>0)&lose).sum()),
            exit_groups={k:dict(trades=int((reasons[mask]==k).sum()),loss_days=int(((reasons[mask]==k)&lose).sum()),
                net_log_pct=float(100*np.log1p(vals[reasons[mask]==k]).sum())) for k in ("target","timeout","initial_stop","protected_stop")})
    diagnostic=dict(overall=loss_diag(np.ones(len(st),bool)),by_year={str(2024+y):loss_diag(years==y) for y in (0,1)},
        by_agreement={"unanimous":loss_diag(unanimous),"split":loss_diag(~unanimous)},
        by_month={str(int(m)):loss_diag(months==m) for m in month_ids})
    print("R36_LOSS_DIAGNOSTIC",json.dumps(diagnostic),flush=True)
    (OUT/"loss_diagnostic.json").write_text(json.dumps(diagnostic,indent=2))
    pd.DataFrame(dict(date=days.astype(str),entry=ix[st],exit=ix[st+hh],direction=sd,unanimous=unanimous,
        risk_pct=risk,vol_ratio60=ratios[60],exit_kind=reasons,gross_pct=100*gross,net_pct=100*p[:,0,0],
        favorable_R_pre_exit_minute=favorable,adverse_R_pre_exit_minute=adverse)).to_csv(OUT/"baseline_loss_ledger.csv",index=False)
    for cfg in settings:
        base,mode,look,cut=cfg
        bp,bst,bsd,bh,bg,ref=refs[base]
        p,st,sd,hh,gg=exit_replay(cfg)
        assert len(p)==500 and np.array_equal(st,bst) and np.array_equal(sd,bsd)
        if mode=="original":
            assert np.array_equal(st,bst) and np.array_equal(sd,bsd) and np.array_equal(p,bp) and np.array_equal(hh,bh) and np.array_equal(gg,bg)
        multiple=stop_distance(mode,look,cut)
        original_limits=np.minimum(holding[base],300-(st-anchors))
        cap=fade_limit(st,sd,original_limits,mode,look,cut) if mode in ("fade","adaptive") else original_limits
        same=cap==original_limits
        assert np.array_equal(p[same],bp[same]) and np.array_equal(hh[same],bh[same]) and np.array_equal(gg[same],bg[same])
        paths[cfg]=p
        row=summarize(p,years,months,complete)
        if cfg==c01:
            assert np.allclose(row["net_pct"],[51.76065459925845,35.91767186836403],atol=1e-6)
            assert row["positive_months"]==18 and row["ge1_months"]==15
            assert np.allclose(row["mark_dd_pct"],[11.03355540786649,13.4422642670878],atol=1e-6)
        net,dd,md,mo,wins=stats(p,years,months)
        bn,bd,bmd,bmo,bw=stats(bp,years,months)
        cn,cd,cmd,cmo,cw=stats(paths.get(c01,bp),years,months)
        row.update(config=list(cfg),days=len(p),exposure=1.,
            changed_exit_count=int(((st+hh!=bst+bh)|(gg!=bg)).sum()),
            stop_mean_pct=float(multiple.mean()),stop_narrower=int((multiple<risk).sum()),stop_wider=int((multiple>risk).sum()),
            **exit_diagnostics[cfg],
            c01_annual_nonregression=bool(np.all(net[:,list(primary)]>=cn[:,list(primary)]-1e-12)),
            c01_draw_nonregression=bool(np.max(md[:,0])<=np.max(cmd[:,0])+1e-12),
            c01_months_preserved=int(((mo[complete,0]>0)&(cmo[complete,0]>0)).sum()),
            flipped_directions=int((sd!=bsd).sum()),
            flipped_by_year=[int(((sd!=bsd)&(years==y)).sum()) for y in (0,1)],
            profitable_months_preserved=int(((mo[complete,0]>0)&(bmo[complete,0]>0)).sum()),
            monthly_nonregression_count=int((mo[complete,0]>=bmo[complete,0]-1e-12).sum()),
            annual_nonregression=bool(np.all(net[:,0]>=bn[:,0]-1e-12)),
            primary_cost_nonregression=bool(np.all(net[:,list(primary)]>=bn[:,list(primary)]-1e-12)),
            draw_nonregression=bool(np.max(md[:,0])<=np.max(bmd[:,0])+1e-12),
            monthly_gate=bool(np.all(mo[complete,:10]>=.01)),
            draw_gate=bool(np.all(md[:,:10]<=.02506676)),
            annual_primary_pass=bool(np.all(net[:,list(primary)]>0)))
        # Paired log-return improvement and dependence on top winners.
        delta=np.log1p(p[:,0,0])-np.log1p(bp[:,0,0])
        sums=np.asarray([delta[months==k].sum() for k in month_ids])
        boot_means=sums[boot].mean(axis=1)
        positive=delta[delta>1e-12]
        total_gain=float(positive.sum())
        top5=float(np.sort(positive)[-5:].sum())
        row["paired_improvement"]=dict(
            improved_days=int((delta>1e-12).sum()),
            worsened_days=int((delta< -1e-12).sum()),
            improved_months=int((sums>1e-12).sum()),
            total_log_gain_pct=float(100*delta.sum()),
            log_gain_excluding_top5_pct=float(100*(delta.sum()-top5)),
            top5_share_of_positive_gain=float(top5/total_gain) if total_gain>0 else 0.,
            bootstrap_lower_95_monthly_log_pct=float(100*np.quantile(boot_means,.05)),
            bootstrap_lower_bonferroni_monthly_log_pct=float(100*np.quantile(boot_means,.05/6)))
        blocks=[]
        for f in folds:
            n0,d0,m0,_,_=stats(p[f],np.zeros(len(f),np.int64),months[f])
            blocks.append(dict(net_pct=(100*n0[0,list(primary)]).tolist(),mark_dd_pct=(100*m0[0,list(primary)]).tolist(),
                mean_log=np.log1p(p[f][:,primary,0]).mean(0).tolist()))
        row["blocks"]=blocks
        row["all_blocks_primary_positive"]=all(min(b["net_pct"])>0 for b in blocks)
        rows[cfg]=row
        ledgers.append(pd.DataFrame(dict(base=base,mode=mode,look=look,cut=cut,date=days.astype(str),entry=ix[st],exit=ix[st+hh],
            direction=sd,exposure=1.,activation_R=activation_multiple(base),lock_R=lock_multiple(base),stop_pct=multiple,gross_points=gg,net_historical5=100*p[:,0,0])))
    def neighbors(cfg):
        if cfg in controls:return [x for x in settings if x[1]=="adaptive"]
        return [x for x in settings if x[1]=="adaptive" and x!=cfg and (x[2]==cfg[2] or x[3]==cfg[3])]
    def score(cfg,t):
        blocks=rows[cfg]["blocks"][:t]
        return .65*min(min(b["mean_log"]) for b in blocks)+.35*float(np.mean([b["mean_log"] for b in blocks]))-.000025*max(max(max(b["mark_dd_pct"]) for b in blocks)-2.506676,0.)
    def rank(cfg,t):
        q=float(np.quantile([score(x,t) for x in neighbors(cfg)],.25))
        return min(score(cfg,t),q),score(cfg,t),cfg
    walk=[]
    for t in range(1,4):
        cfg=max(settings,key=lambda x:rank(x,t))
        b=rows[cfg]["blocks"][t]
        walk.append(dict(block=t,selected=list(cfg),**b,passed=min(b["net_pct"])>0 and max(b["mark_dd_pct"])<=2.506676))
    walk_pass=all(w["passed"] for w in walk)
    for cfg,row in rows.items():
        row["neighbor_positive_fraction"]=float(np.mean([rows[x]["all_blocks_primary_positive"] for x in neighbors(cfg)]))
        row["robust_score"]=rank(cfg,4)[0]
        row["eligible"]=bool(cfg not in controls and walk_pass and row["c01_annual_nonregression"] and row["c01_draw_nonregression"] and row["annual_nonregression"] and row["primary_cost_nonregression"] and row["draw_nonregression"] and row["profitable_months_preserved"]==refs[cfg[0]][-1]["positive_months"] and row["positive_months"]>refs[cfg[0]][-1]["positive_months"] and row["all_blocks_primary_positive"] and row["monthly_gate"] and row["draw_gate"] and row["neighbor_positive_fraction"]>=.75 and row["robust_score"]>0 and row["paired_improvement"]["bootstrap_lower_bonferroni_monthly_log_pct"]>0 and row["paired_improvement"]["log_gain_excluding_top5_pct"]>0)
    def month_key(r):return (r["positive_months"],r["ge1_months"],min(r["net_pct"]))
    def target_key(r):return (r["ge1_months"],r["positive_months"],min(r["net_pct"]))
    def annual_key(r):return min(r["net_pct"])
    by_base={}
    for base in ("R36_winner",):
        rr=[r for cfg,r in rows.items() if cfg[0]==base]
        ref=refs[base][-1]
        q=[r for r in rr if r["annual_nonregression"]]
        by_base[base]=dict(reference=ref,monthly_best=max(rr,key=month_key),target_best=max(rr,key=target_key),
            annual_best=max(rr,key=annual_key),nonregression_best=max(q,key=month_key),
            improved_months_no_annual_regression=sum(r["positive_months"]>ref["positive_months"] for r in q),
            improved_targets_no_annual_regression=sum(r["ge1_months"]>ref["ge1_months"] for r in q),
            preserve_all_and_improve=sum(r["profitable_months_preserved"]==ref["positive_months"] and r["positive_months"]>ref["positive_months"] for r in q))
    eligible=[r for r in rows.values() if r["eligible"]]
    result=dict(configurations=len(settings),new_configurations=6,controls=2,development_days=500,complete_months=23,
        strict_full_exposure=True,recovery_rules=0,independent_replay=True,
        monthly_best=max(rows.values(),key=month_key),target_best=max(rows.values(),key=target_key),
        annual_best=max(rows.values(),key=annual_key),robust_best=rows[max(settings,key=lambda x:rank(x,4))],
        by_base=by_base,historical_both_year_positive_count=sum(min(r["net_pct"])>0 for r in rows.values()),
        annual_primary_pass_count=sum(r["annual_primary_pass"] for r in rows.values()),
        all_blocks_primary_positive_count=sum(r["all_blocks_primary_positive"] for r in rows.values()),
        walk_forward=walk,eligible_count=len(eligible),validation_status="NOT_RUN_DEVELOPMENT_FAILED" if not eligible else "PENDING_FROZEN_VALIDATION",all_pass=False)
    pd.concat(ledgers,ignore_index=True).to_csv(OUT/"consensus_risk_diagnostic_daily_ledger.csv",index=False)
    (OUT/"grid.json").write_text(json.dumps(list(rows.values()),indent=2))
    (OUT/"summary.json").write_text(json.dumps(result,indent=2))
    print("R44_GRID",json.dumps([{k:r[k] for k in ("config","net_pct","positive_months","ge1_months","mark_dd_pct","worst_month_pct","days","initial_stop_exits","early_fade_exits","annual_nonregression","primary_cost_nonregression","draw_nonregression","profitable_months_preserved","c01_annual_nonregression","c01_draw_nonregression","c01_months_preserved","neighbor_positive_fraction","eligible")} for r in rows.values()]),flush=True)
    print("R44_VOLATILITY_FADE_FINAL",json.dumps(result),flush=True)
if __name__=="__main__":main()
