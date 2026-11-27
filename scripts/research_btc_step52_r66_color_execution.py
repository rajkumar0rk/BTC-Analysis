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

OUT=Path("analysis/btc_step52_r66_color_execution")
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
    mh=mm.high.to_numpy(float);ml=mm.low.to_numpy(float);mopen=mm.open.to_numpy(float);mclose=mm.close.to_numpy(float)
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
        if not (np.isfinite(mh[q]).all() and np.isfinite(ml[q]).all() and np.isfinite(mopen[q]).all() and np.isfinite(mclose[q]).all() and np.isfinite(pre[q]).all() and np.isfinite(post[q]).all()):
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
    return (m,ix,o,h,l,c,v,mh,ml,pre,post,old,slips,modecodes,days,grid,years,months,complete,counts,expcounts,mopen,mclose)

def frozen(validation):
    m,ix,o,h,l,c,v,mh,ml,pre,post,old,slips,modecodes,days,grid,years,months,complete,counts,expcounts,mopen,mclose=dataset(validation)
    anchors=grid[:,0]
    starts=[];sides=[];risks=[];ratios=[];atr14=[];confirmed_count=0;unanimous=0
    def efficiency(j):
        closes=c[np.arange(j-241,j,15)]
        travel=np.abs(np.diff(closes)).sum()
        return abs(closes[-1]-closes[0])/travel if travel>0 else 0.
    def trmean(j,look,normalize=False):
        hi=h[j-look:j].reshape(-1,5).max(axis=1)
        lo=l[j-look:j].reshape(-1,5).min(axis=1)
        prior=c[np.arange(j-look-1,j-1,5)]
        tr=np.maximum(hi-lo,np.maximum(abs(hi-prior),abs(lo-prior)))
        return float((tr/prior if normalize else tr).mean())
    for j in anchors:
        hi=h[j-210:j].reshape(14,15).max(axis=1)
        lo=l[j-210:j].reshape(14,15).min(axis=1)
        prior=c[np.arange(j-211,j-1,15)]
        tr=np.maximum(hi-lo,np.maximum(abs(hi-prior),abs(lo-prior))).mean()
        risk=float(np.clip(400*tr/c[j-1],.25,1.5))
        atr14.append(float(tr))
        side=-1 if c[j-1]>=o[j-60] else 1
        if efficiency(j)>=.4:side=-side
        confirmed=False
        z=j+60
        for d in range(5,61,5):
            t=j+d
            move=100*side*(c[t-1]-o[t-5])/c[j-1]
            pullback=100*side*(c[t-1]-c[j-1])/c[j-1]
            if pullback<=-.1*risk and move>0:
                z=t;confirmed=True;break
        if confirmed:
            confirmed_count+=1
            delta=c[z-1]-c[z-241]
            if delta*side<0 and 100*abs(delta)/c[z-1]/risk>=1.5:side=-side
            monthly=annual=side
        else:
            delta=c[z-1]-o[z-15]
            monthly=annual=side
            if delta!=0:
                direction=1 if delta>0 else -1
                if 100*abs(delta)/c[z-1]>=.25*risk:monthly=direction
                annual=direction if efficiency(z)>=.4 else -direction
        high=h[z-60:z].max();low=l[z-60:z].min()
        range_edge=abs(2*c[z-1]-high-low)/(high-low) if high>low else 0.
        prev=trmean(z-120,120)
        vol=trmean(z,120)/prev if prev>0 else 1.
        votes=[monthly,monthly if range_edge<.75 else annual,monthly if vol<1. else annual]
        unanimous+=int(abs(sum(votes))==3)
        side=1 if sum(votes)>0 else -1
        prev=trmean(z-60,60,True);recent=trmean(z,60,True)
        ratio=recent/prev if recent>0 and prev>0 else 1.
        starts.append(z);sides.append(side);risks.append(risk);ratios.append(ratio)
    st=np.asarray(starts,np.int64);sd=np.asarray(sides,np.int8)
    risk=np.asarray(risks);ratio=np.asarray(ratios)
    base_limits=300-(st-anchors)
    limits=base_limits.copy()
    hh=np.empty(len(st),np.int64);gg=np.empty(len(st));why=np.empty(len(st),np.int64)
    for i,j in enumerate(st):
        armed=False
        for d in range(5,int(base_limits[i]),5):
            move=100*sd[i]*(c[j+d-1]-o[j])/o[j]
            if armed and move<=0:
                limits[i]=d;break
            if move>=.75*risk[i]:armed=True
        offsets=np.arange(5,int(base_limits[i]),5)
        moves=100*sd[i]*(c[j+offsets-1]-o[j])/o[j]
        peak=np.r_[-np.inf,np.maximum.accumulate(moves)[:-1]]
        hits=offsets[(peak>=.75*risk[i])&(moves<=0)]
        assert limits[i]==(hits[0] if len(hits) else base_limits[i])
        recipe=np.array([1.,risk[i],4*risk[i],limits[i],np.clip(1.5*ratio[i],1.,2.5)*risk[i],np.clip(.5/ratio[i],.25,.75)*risk[i],0.])
        policy=np.array([0.,0.,0.,float(limits[i])])
        end,px,reason,*_=replay_one(o,h,l,c,int(j),int(sd[i]),recipe,policy)
        raw=replay_with_nextbar_exits(o,h,l,c,st[i:i+1],sd[i:i+1],recipe[None,:],policy[None,:],FEE,5.)
        hh[i]=end-j;gg[i]=sd[i]*(px-o[j]);why[i]=reason
        assert hh[i]==raw[4][0,0] and abs(gg[i]-raw[2][0,0])<1e-7 and why[i]==raw[3][0,0]
    assert np.all(st+hh<=anchors+300) and np.all(st[:-1]+hh[:-1]<st[1:])
    path=pricing(st,sd,hh,gg,o,mh,ml,pre,post,old,slips,modecodes)
    assert np.isfinite(path).all()
    net,dd,md,mo,wins=stats(path,years,months)
    if not validation:
        assert len(st)==500 and confirmed_count==231 and unanimous==373
        assert np.allclose(100*net[:,0],[51.76065459925845,35.91767186836403],atol=1e-6)
        expected=[15.405601510063915,.26444676095194186,1.4822547220863402,7.489050812039033,.3042205684700372,-.6737558080061601,5.928644073488765,8.942210394421446,2.6591430032943952,-2.516547080437903,4.498402029674731,2.483908171825977,5.78201545163064,.23833564082929026,7.6746716048238905,2.169274102667962,-5.553474780827639,3.0995572875232025,-2.725607124827578,-4.131379533351732,9.874921265842884,8.014526358095853,5.497499476948886]
        assert np.allclose(100*mo[complete,0],expected,atol=1e-6)
        assert np.allclose(100*md[:,0],[11.03355540786649,13.4422642670878],atol=1e-6)
        print("R43_FROZEN_DEVELOPMENT_PARITY",json.dumps(dict(trades=len(st),returns=(100*net[:,0]).tolist(),monthly=(100*mo[complete,0]).tolist(),confirmed=confirmed_count,unanimous=unanimous)),flush=True)
    assert not validation
    def metrics(p,idx):
        r=p[:,idx,0];net,dd,md,mo,wins=stats(p,years,months)
        return dict(net_pct=(100*net[:,idx]).tolist(),closed_dd_pct=float(100*dd[:,idx].max()),mark_dd_bound_pct=float(100*md[:,idx].max()),
            positive_months=int((mo[complete,idx]>0).sum()),ge1_months=int((mo[complete,idx]>=.01).sum()),
            worst_month_pct=float(100*mo[complete,idx].min()),win_rate_pct=float(100*(r>0).mean()),
            profit_factor=float(r[r>0].sum()/-r[r<0].sum()),trades=len(r),
            monthly_pct=(100*mo[complete,idx]).tolist())
    # Fixed R66 C07. Reset each month, reduce after realized +2%.
    # State is recomputed causally for each fee/slippage scenario.
    def size_r66(p):
        sized=p.copy();sizes=np.ones(p.shape[:2])
        for k in range(p.shape[1]):
            equity=1.;latched=False;prev=-1
            for i,mth in enumerate(months):
                if mth!=prev:equity=1.;latched=False;prev=mth
                latched=latched or equity>=1.02
                sizes[i,k]=.25 if latched else 1.
                sized[i,k]=p[i,k]*sizes[i,k]
                equity*=1+sized[i,k,0]
        eq=np.ones(p.shape[1]);active=np.zeros(p.shape[1],bool);prev=-1
        for i,mth in enumerate(months):
            if mth!=prev:eq[:]=1.;active[:]=False;prev=mth
            active|=eq>=1.02
            assert np.array_equal(sizes[i],np.where(active,.25,1.))
            eq*=1+p[i,:,0]*sizes[i]
        assert np.all(sizes>0)
        return sized,sizes
    def sized_metrics(p,sizes,k):
        return dict(**metrics(p,k),mean_exposure=float(sizes[:,k].mean()),reduced_trades=int((sizes[:,k]<1).sum()))
    results=[];ledgers=[]
    op,os=size_r66(path)
    assert np.allclose(sized_metrics(op,os,0)["net_pct"],[37.603080548222614,24.56457538790804],atol=1e-8)
    assert sized_metrics(op,os,0)["positive_months"]==20
    assert sized_metrics(op,os,0)["ge1_months"]==19
    assert abs(os[:,0].mean()-.5515)<1e-12
    results.append(dict(name="r66_adverse_first",historical5=sized_metrics(op,os,0),offer30_5=sized_metrics(op,os,5)))
    results.append(dict(name="original_adverse_first",historical5=metrics(path,0),offer30_5=metrics(path,5)))
    for name in ("color_original",):
        ends=[];fills=[];reasons=[];mark_extremes=[];slots=[]
        for i,j in enumerate(st):
            mid=o[j];side=int(sd[i])
            if name=="color_original":
                stop_distance=risk[i]*mid/100
                arm=np.clip(1.5*ratio[i],1.,2.5)*risk[i]*mid/100
                lock=np.clip(.5/ratio[i],.25,.75)*risk[i]*mid/100
                trail=False
            else:
                stop_distance=2*atr14[i]
                arm=150.;lock=50.;trail=True
            target=4*risk[i]*mid/100
            # Both streams receive their own candle-color sequence.
            # Pair the corresponding ordinal samples (not a claim of simultaneity).
            stop=-stop_distance;peak=0.;mae=0.;mfe=0.;reason="deadline"
            e=j+int(limits[i]);fill=o[e];slot=0
            done=False
            for k in range(j,e):
                trade=sequence(o[k],h[k],l[k],c[k])
                mark=sequence(mopen[k],mh[k],ml[k],mclose[k])
                for n,(tp,mp) in enumerate(zip(trade,mark)):
                    assert np.isfinite(tp) and np.isfinite(mp)
                    mark_move=side*(mp-mid)
                    trade_move=side*(tp-mid)
                    mae=min(mae,mark_move);mfe=max(mfe,mark_move)
                    if mark_move<=stop+1e-10:
                        e=k;fill=tp;slot=n;reason="stop";done=True;break
                    if trade_move>=target-1e-10:
                        e=k;fill=mid+side*target;slot=n;reason="target";done=True;break
                    peak=max(peak,mark_move)
                    if peak>=arm:
                        stop=max(stop,peak-lock if trail else lock)
                if done:break
            if not done:
                reason="fade" if limits[i]<base_limits[i] else "deadline"
                mark_move=side*(mopen[e]-mid)
                mae=min(mae,mark_move);mfe=max(mfe,mark_move)
            assert j<=e<=anchors[i]+300
            ends.append(e);fills.append(fill);reasons.append(reason);slots.append(slot);mark_extremes.append((mae,mfe))
        ends=np.asarray(ends);fills=np.asarray(fills);slots=np.asarray(slots)
        assert np.all(ends[:-1]<st[1:])
        gross=sd*(fills-o[st]);duration=ends-st
        allpaths=[]
        # Reprice fixed fills with historic and 30-minute offer policies.
        # A slot is a sequence position, NOT a measured timestamp.
        # For waiver, exits in minute 30 are conservatively charged.
        scenarios=[("historical",5),("offer30",5),("offer30",0),("standard",5),("offer30",20),("offer30",50)]
        ext=np.asarray(mark_extremes)
        for mode,slip in scenarios:
            en=o[st]+sd*slip;ex=fills-sd*slip
            waive=(duration<(np.where(old[st],15,30) if mode=="historical" else 30)) if mode!="standard" else np.zeros(len(st),bool)
            fu=pre[ends]-pre[st]+post[ends+1]-post[st]
            ret=(sd*(ex-en)-FEE*(en+ex*(~waive))-fu)/en
            adverse=(ext[:,0]-slip)/en-2*FEE-fu/en
            favorable=(ext[:,1]-slip)/en-FEE
            allpaths.append(np.stack((ret,adverse,favorable),axis=1))
        cp=np.stack(allpaths,axis=1)
        assert np.isfinite(cp).all()
        row=dict(name=name,historical5=metrics(cp,0),offer30_5=metrics(cp,1),offer30_0=metrics(cp,2),standard5=metrics(cp,3),offer30_20=metrics(cp,4),offer30_50=metrics(cp,5),
            exit_counts={x:reasons.count(x) for x in sorted(set(reasons))},changed_exits_vs_original=int(((ends!=st+hh)|(np.abs(gross-gg)>1e-7)).sum()))
        assert np.allclose(row["offer30_5"]["net_pct"],[43.723385088735924,25.941645041694784],atol=1e-8)
        results.append(row)
        sp,ss=size_r66(cp)
        result_sized=dict(name="r66_color",**{key:sized_metrics(sp,ss,k) for k,key in enumerate(("historical5","offer30_5","offer30_0","standard5","offer30_20","offer30_50"))})
        results.append(result_sized)
        ledgers.append(pd.DataFrame(dict(model="r66_color",date=days.astype(str),entry=ix[st],exit_minute=ix[ends],exit_sample=slots,direction=sd,entry_price=o[st],exit_price=fills,exit_reason=reasons,exposure=ss[:,1],net_offer30_5=100*sp[:,1,0])))
        ledgers.append(pd.DataFrame(dict(model=name,date=days.astype(str),entry=ix[st],exit_minute=ix[ends],exit_sample=slots,direction=sd,entry_price=o[st],exit_price=fills,exit_reason=reasons,net_offer30_5=100*cp[:,1,0])))
    result=dict(period="2024-02 through 2025-12",trades=len(st),candles=len(m),development_parity=True,entry_unchanged=True,mark_and_trade_ordinal_pairing=True,optimization=False,validation_2026=False,original_r66_parity=True,monthly_profit_trigger_pct=2.,reduced_exposure=.25,results=results,
        caveats=["OHLC color is a synthetic sequence, not tick-level reconstruction","Separate mark and trade candle paths are paired by ordinal sample","Stops fill at corresponding trade sample, targets at limit price","Funding is conservative proxy","Mark drawdown bound uses sampled extremes before exit, not actual tick sequence","2ATR uses original simple mean of 14 completed 15m true ranges at 18:00 anchor, without clipping","Original 4R target and original fade remain in both color variants"])
    (OUT/"summary.json").write_text(json.dumps(result,indent=2))
    pd.concat(ledgers,ignore_index=True).to_csv(OUT/"ledger.csv",index=False)
    print("R66_COLOR_FINAL",json.dumps(result),flush=True)
def sequence(o,h,l,c):
    if c>o or (c==o and o-l<=h-o):return (o,l,h,c)
    return (o,h,l,c)
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assert sequence(100,110,90,101)==(100,90,110,101)
    assert sequence(100,110,90,99)==(100,110,90,99)
    assert sequence(100,103,90,100)==(100,103,90,100)
    assert sequence(100,110,90,100)==(100,90,110,100)
    frozen(False)
if __name__=="__main__":main()
