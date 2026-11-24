#!/usr/bin/env python3
"""Step55: intraday confirmed signals with one mandatory weekday entry.
Selection on 2025; 2026 research-exposed recheck. All-period search is not
out-of-sample. No PnL-based gate, no future selection, fixed 1x notional.
Historical funding proxy and conservative mark-price path bounds.
"""
from pathlib import Path
from itertools import product
import json
import numpy as np
import pandas as pd
from numba import njit
import research_btc_every_weekday_reset_step1 as base
import research_btc_daily_exit_invalidation_step7 as early
from step52_dynamic_risk_engine import Risk
from step52_validation_engine import replay_one

OUT=Path("analysis/btc_step55_intraday")
SCENARIOS=[("historical",5),("conservative",5),("offer30",5),
           ("historical",20),("conservative",20),("standard",20),
           ("offer30",50),("standard",50),("standard",100),("standard",200)]
PRIMARY=(0,1,2,3,4,5)
@njit
def mark_extrema(low,high,starts,holds):
    n,p=holds.shape
    lo=np.empty((n,p));hi=np.empty((n,p))
    for d in range(n):
        for k in range(p):
            j=starts[d];a=low[j];b=high[j]
            # Include whole exit minute: conservative bound on adverse exposure.
            for t in range(j+1,j+holds[d,k]+1):
                a=min(a,low[t]);b=max(b,high[t])
            lo[d,k]=a;hi[d,k]=b
    return lo,hi

@njit
def measure(y,adverse,favorable,mi,cut):
    n,p,k=y.shape
    net=np.ones((p,k));peak=np.ones((p,k));dd=np.zeros((p,k))
    month=np.ones((22,p,k));markdd=np.zeros((p,k));markpeak=np.ones((p,k))
    for d in range(cut):
        for j in range(p):
            for q in range(k):
                markpeak[j,q]=max(markpeak[j,q],net[j,q]*(1+favorable[d,j,q]))
                markdd[j,q]=max(markdd[j,q],1-net[j,q]*(1+adverse[d,j,q])/markpeak[j,q])
                net[j,q]*=1+y[d,j,q]
                month[mi[d],j,q]*=1+y[d,j,q]
                peak[j,q]=max(peak[j,q],net[j,q])
                dd[j,q]=max(dd[j,q],1-net[j,q]/peak[j,q])
                markpeak[j,q]=max(markpeak[j,q],net[j,q])
                markdd[j,q]=max(markdd[j,q],1-net[j,q]/markpeak[j,q])
    return net-1,dd,markdd,month-1

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m=base.load()
    o,h,l,c,v=[m[x].to_numpy(float) for x in ("open","high","low","close","volume")]
    days=base.prepare(m)[0][:,0]
    n=len(days);assert n==477
    mi=base.MONTH_IDX;train=base.NTRAIN
    risk=Risk(m,5,"historical",base.COST)
    # 5-minute decision grid; every feature references a completed minute.
    clock=np.arange(7*60,21*60,5)
    ix=days[:,None]+clock[None,:]
    last=c[ix-1]
    ret={k:last/o[ix-k]-1 for k in (5,15,30,60,120,240)}
    close=pd.Series(c)
    ema={k:close.ewm(span=k,adjust=False).mean().to_numpy()[ix-1] for k in (20,60,120,240)}
    rollh=pd.Series(h);rolll=pd.Series(l)
    upper={k:rollh.rolling(k).max().to_numpy()[ix-6] for k in (30,60,120)}
    lower={k:rolll.rolling(k).min().to_numpy()[ix-6] for k in (30,60,120)}
    recent_low=rolll.rolling(5).min().to_numpy()[ix-1]
    recent_high=rollh.rolling(5).max().to_numpy()[ix-1]
    r60=(rollh.rolling(60).max().to_numpy()[ix-1]-rolll.rolling(60).min().to_numpy()[ix-1])/last
    cum=np.r_[0.,np.cumsum(v,dtype=float)]
    rv=(cum[ix]-cum[ix-5])/np.maximum((cum[ix-5]-cum[ix-105])/20.,1e-9)
    diff=close.diff()
    gain=diff.clip(lower=0).ewm(alpha=1/14,adjust=False).mean().to_numpy()[ix-1]
    loss=(-diff.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean().to_numpy()[ix-1]
    rsi=np.divide(gain,gain+loss,out=np.full_like(gain,.5),where=gain+loss>0)
    # Fallback observable at 21:00, not known or used before that time.
    fb=days+21*60
    fall={k:np.where(c[fb-1]>=o[fb-k],1,-1) for k in (5,60,240)}
    signals=[]
    for horizon,threshold in product((15,60,240),(.0015,.003,.006)):
        for vmin in (1.,1.5):
            long=(ret[horizon]>=threshold)&(ret[5]>0)&(rv>=vmin)
            short=(ret[horizon]<=-threshold)&(ret[5]<0)&(rv>=vmin)
            signals.append(("momentum",horizon,threshold,vmin,long,short))
    for horizon,vmin in product((30,60,120),(1.,1.5,2.)):
        long=(last>upper[horizon])&(rv>=vmin)
        short=(last<lower[horizon])&(rv>=vmin)
        signals.append(("breakout",horizon,0.,vmin,long,short))
    for fast,slow in ((20,60),(60,240)):
        for vmin in (0.,1.25):
            long=(ema[fast]>ema[slow])&(recent_low<=ema[fast])&(last>ema[fast])&(ret[5]>0)&(rv>=vmin)
            short=(ema[fast]<ema[slow])&(recent_high>=ema[fast])&(last<ema[fast])&(ret[5]<0)&(rv>=vmin)
            signals.append(("ema_pullback",fast,slow,vmin,long,short))
    for lim,range_min in product((.15,.25,.35),(.003,.006)):
        long=(rsi<=lim)&(ret[5]>0)&(r60>=range_min)
        short=(rsi>=1-lim)&(ret[5]<0)&(r60>=range_min)
        signals.append(("rsi_reversal",14,lim,range_min,long,short))
    holds=(8,14,20,29,45,60,90,120)
    policies=np.array([(0,0.,0.,float(x)) for x in holds])
    recipes=[(.12,.35,0,0.,0.),(.20,.50,0,0.,0.),(.30,.75,0,0.,0.),(.45,1.,0,0.,0.),
             (.60,1.5,0,0.,0.),(.25,1.5,2,.20,.12),(.35,2.,2,.30,.18),(.50,2.,2,.40,.25)]
    best_train=None;best_all=None;best_month=None;tested=0;qualified=0
    summaries=[]
    # To keep a full weekday trade, use fallback direction rules fixed
    # across all dates; do not skip poor days or relabel missing outcomes.
    def key(net,dd,months):
        return (int((months>=.01).sum(0).min()),
                float(np.min(net)-2*np.maximum(dd-.02506676,0).max()+np.minimum(months,0).sum(0).min()),
                float(months.min()))
    def conservative_key(net,dd,months):
        return (float(np.min(net)-3*np.maximum(dd-.02506676,0).max()+np.minimum(months,0).sum(0).min()),
                int((months>=.01).sum(0).min()),float(months.min()))
    for family,horizon,threshold,vmin,long,short in signals:
        for begin,end in ((7,21),(12,21),(16,21)):
            window=(clock>=begin*60)&(clock<end*60)
            valid=(long^short)&window[None,:]
            found=valid.any(1);first=np.argmax(valid,axis=1)
            jj=np.where(found,ix[np.arange(n),first],fb)
            primary=np.where(long[np.arange(n),first],1,-1)
            for fl,flip in product((60,240),(1,-1)):
                sd=np.where(found,primary,fall[fl]*flip).astype(np.int8)
                for stop,tp,kind,act,val in recipes:
                    cfg=np.tile([kind,stop,tp,120,act,val,0.],(n,1))
                    raw=early.replay_with_nextbar_exits(o,h,l,c,jj,sd,cfg,policies,base.COST,5.)
                    gross,elapsed=raw[2],raw[4]
                    lmark,hmark=mark_extrema(risk.mark_low,risk.mark_high,jj,elapsed)
                    assert np.isfinite(lmark).all() and np.isfinite(hmark).all()
                    sign=sd[:,None];mid=o[jj,None]
                    starts2=np.broadcast_to(jj[:,None],elapsed.shape)
                    fund=risk.funding(starts2,elapsed,sign,mid,adverse=True)
                    result=[];adverse=[];favorable=[]
                    for mode,slip in SCENARIOS:
                        entry=mid+sign*slip
                        exitfill=mid+sign*gross-sign*slip
                        if mode=="historical":
                            waived=elapsed<np.where((m.index[jj]<risk.upgrade)[:,None],15,30)
                        elif mode=="conservative":
                            waived=(m.index[jj]>=risk.upgrade)[:,None]&(elapsed<30)
                        elif mode=="offer30":waived=elapsed<30
                        else:waived=np.zeros_like(elapsed,bool)
                        f=fund*mid/entry
                        result.append((sign*(exitfill-entry)-base.COST*(entry+exitfill*(~waived)))/entry-f)
                        adverse.append(sign*(np.where(sign>0,lmark,hmark)-entry)/entry-2*base.COST-f)
                        favorable.append(sign*(np.where(sign>0,hmark,lmark)-entry)/entry-base.COST)
                    Y=np.stack(result,axis=2)
                    A=np.stack(adverse,axis=2);F=np.stack(favorable,axis=2)
                    rn,rd,rm,ro=measure(Y,A,F,mi,n)
                    tn,td,tm,to=measure(Y,A,F,mi,train)
                    for pi,hold in enumerate(holds):
                        tested+=1
                        spec=dict(family=family,horizon=horizon,threshold=threshold,volume_or_range=vmin,begin=begin,end=end,
                                  fallback_lookback=fl,fallback_sign=flip,stop_pct=stop,tp_pct=tp,exit_kind=kind,
                                  activation_pct=act,trail_pct=val,hold=hold,event_trades=int(found.sum()))
                        K=conservative_key(rn[pi,:6],rm[pi,:6],ro[:,pi,:6])
                        T=conservative_key(tn[pi,:6],tm[pi,:6],to[:12,pi,:6])
                        M=key(rn[pi,:6],rm[pi,:6],ro[:,pi,:6])
                        passes=bool(np.all(ro[:,pi,:6]>=.01)&np.all(rm[pi,:6]<=.02506676))
                        qualified+=int(passes)
                        if best_all is None or K>best_all[0]:
                            best_all=(K,spec,jj.copy(),sd.copy(),Y[:,pi,:].copy())
                        if best_train is None or T>best_train[0]:
                            best_train=(T,spec,jj.copy(),sd.copy(),Y[:,pi,:].copy())
                        if best_month is None or M>best_month[0]:
                            best_month=(M,spec,jj.copy(),sd.copy(),Y[:,pi,:].copy())
        print("STEP55_PROGRESS",family,horizon,threshold,vmin,tested,qualified,flush=True)
    def audit(item,tag):
        _,spec,jj,sd,predicted=item
        fills=[]
        for d,(j,side) in enumerate(zip(jj,sd)):
            cfg=[spec["exit_kind"],spec["stop_pct"],spec["tp_pct"],120,spec["activation_pct"],spec["trail_pct"],0.]
            end,mid,why,sl,mae,both=replay_one(o,h,l,c,int(j),int(side),cfg,[0.,0.,0.,spec["hold"]])
            if d:assert fills[-1][1]<j
            assert m.index[j].tz_convert("Asia/Kolkata").date()==m.index[end].tz_convert("Asia/Kolkata").date()
            fills.append((int(j),end,int(side),mid,why))
        rows=[]
        for q,(mode,slip) in enumerate(SCENARIOS):
            risk.mode=mode;risk.slip=slip
            y=[];a=[];f=[]
            for j,end,side,mid,why in fills:
                z,fee,fund=risk.prices(np.array([j]),np.array([[end-j]]),side,np.array([[side*(mid-o[j])]]))
                en=o[j]+side*slip;lo=risk.mark_low[j:end+1].min();hi=risk.mark_high[j:end+1].max()
                y.append(z[0,0])
                a.append(side*((lo if side>0 else hi)-en)/en-2*base.COST-fund[0,0])
                f.append(side*((hi if side>0 else lo)-en)/en-base.COST)
            assert np.max(np.abs(np.array(y)-predicted[:,q]))<1e-10
            net,dd,markdd,mo=measure(np.array(y)[:,None,None],np.array(a)[:,None,None],np.array(f)[:,None,None],mi,n)
            month=mo[:,0,0]
            row=dict(mode=mode,slip=slip,net_pct=float(net[0,0]*100),closed_dd_pct=float(dd[0,0]*100),
                     mark_dd_pct=float(markdd[0,0]*100),months_ge1=int((month>=.01).sum()),positive_months=int((month>0).sum()),
                     worst_month_pct=float(month.min()*100),one_x_liquidation_proxy=int((np.array(a)<=-.995).sum()),monthly_pct=(month*100).tolist())
            rows.append(row);print("STEP55_SCENARIO",tag,json.dumps(row),flush=True)
        report=dict(tag=tag,spec=spec,trades=n,independent_fill_parity=True,scenario_results=rows,
                    all_primary_pass=all(x["months_ge1"]==22 and x["mark_dd_pct"]<=2.506676 for x in rows[:6]),
                    all_severe_pass=all(x["months_ge1"]==22 and x["mark_dd_pct"]<=2.506676 for x in rows),
                    funding_proxy_only=True,research_exposed=True,demo_verified=False)
        (OUT/(tag+".json")).write_text(json.dumps(report,indent=2))
        pd.DataFrame([dict(day=base.IST_DAYS[d],entry=m.index[j],exit=m.index[e],side=side,entry_mid=o[j],exit_mid=mid,reason=why) for d,(j,e,side,mid,why) in enumerate(fills)]).to_csv(OUT/(tag+"_ledger.csv"),index=False)
        print("STEP55_RESULT",json.dumps({k:v for k,v in report.items() if k!="scenario_results"}),flush=True)
    print("STEP55_SEARCH",tested,qualified,flush=True)
    audit(best_train,"2025_selected")
    audit(best_all,"risk_ranked_research")
    audit(best_month,"month_ranked_research")
if __name__=="__main__":main()
