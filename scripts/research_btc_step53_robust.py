#!/usr/bin/env python3
"""Step53: simple, fee-robust daily strategy family; no monthly PnL feedback.
All 22 months are research-exposed. Selection uses 2025; 2026 is a recheck,
NOT an untouched holdout. Never use month identity or future candles as signals.
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

OUT=Path("analysis/btc_step53_robust")
# Joint scenarios are identical rules and fill triggers, different cost assumptions.
SCENARIOS=[("historical",5),("conservative",5),("offer30",5),("historical",20),
           ("conservative",20),("standard",20),("offer30",50),("standard",50),
           ("standard",100),("standard",200)]
PRIMARY=np.arange(6)
@njit
def scores(y,mi):
    n,k=y.shape
    net=np.ones(k);peak=np.ones(k);dd=np.zeros(k);mo=np.ones((22,k))
    for i in range(n):
        for j in range(k):
            net[j]*=1+y[i,j];peak[j]=max(peak[j],net[j])
            dd[j]=max(dd[j],1-net[j]/peak[j]);mo[mi[i],j]*=1+y[i,j]
    return net-1,dd,mo-1

def metrics(y,mi):
    net,dd,mo=scores(y,mi)
    return dict(net_pct=100*net,dd_pct=100*dd,months_ge1=(mo>=.01).sum(0),
                positive_months=(mo>0).sum(0),worst_month_pct=100*mo.min(0),monthly_pct=100*mo)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m=base.load();o,h,l,c,v=[m[x].to_numpy(float) for x in ("open","high","low","close","volume")]
    starts=base.prepare(m)[0]
    n=len(starts);assert n==477
    mi=base.MONTH_IDX;train=base.NTRAIN
    risk=Risk(m,5,"historical",base.COST)
    # First known volume event 18/19/20 IST; fallback 21 IST. All inputs
    # are completed bars before the selected signal. Other daily clock
    # families are tested independently, not chosen using the day's outcome.
    hour=np.full(n,21,dtype=int)
    for d in range(n):
        for hh in (18,19,20):
            j=starts[d,hh];prior=v[j-105:j-5].reshape(20,5).sum(1).mean()
            if prior>0 and v[j-5:j].sum()/prior>=1.5:hour[d]=hh;break
    event=hour<21
    arms=[];ret=[];spec=[]
    clock={"event_or_21":starts[np.arange(n),hour]}
    for hh in (7,9,12,15,18,21):clock["hour_"+str(hh)]=starts[:,hh]
    holds=(8,14,20,29,45,60,90,120)
    policies=np.array([(0,0.,0.,float(x)) for x in holds])
    for clockname,initial in clock.items():
        for delay in (0,5,15):
            idx=initial+delay
            dirs={}
            for length in (5,15,60,240):
                sg=np.where(c[idx-1]>=o[idx-length],1,-1)
                dirs["follow"+str(length)]=sg;dirs["fade"+str(length)]=-sg
            # Structural breakout / location rule without future bars.
            pos=np.array([(c[j-1]-l[j-60:j].min())/max(h[j-60:j].max()-l[j-60:j].min(),1e-12) for j in idx])
            dirs["range_follow"]=np.where(pos>=.5,1,-1);dirs["range_fade"]=-dirs["range_follow"]
            for stop,tp,kind,activation,val in [
                (.20,.60,0,0,0),(.35,.70,0,0,0),(.50,1.0,0,0,0),
                (.75,1.5,0,0,0),(1.,2.,0,0,0),
                (.35,1.5,2,.25,.15),(.50,2.,2,.40,.25),(.75,2.5,2,.60,.35)]:
                cfg=np.tile([kind,stop,tp,120,activation,val,0.],(n,1))
                vals={}
                for sign in (-1,1):
                    raw=early.replay_with_nextbar_exits(o,h,l,c,idx,np.full(n,sign,dtype=np.int8),cfg,policies,base.COST,5.)
                    gross,elapsed=raw[2],raw[4]
                    starts2=np.broadcast_to(idx[:,None],elapsed.shape)
                    fund=risk.funding(starts2,elapsed,sign,o[idx][:,None],adverse=True)
                    result=[]
                    for mode,slip in SCENARIOS:
                        entry=o[idx][:,None]+sign*slip
                        exitfill=o[idx][:,None]+sign*gross-sign*slip
                        # Re-evaluate costs per candidate, strict boundary treatment.
                        if mode=="historical":
                            waived=elapsed<np.where((m.index[idx]<risk.upgrade)[:,None],15,30)
                        elif mode=="conservative":
                            waived=(m.index[idx]>=risk.upgrade)[:,None]&(elapsed<30)
                        elif mode=="offer30":waived=elapsed<30
                        else:waived=np.zeros_like(elapsed,bool)
                        y=(sign*(exitfill-entry)-base.COST*(entry+exitfill*(~waived)))/entry-fund*o[idx][:,None]/entry
                        result.append(y)
                    vals[sign]=np.stack(result,axis=2)
                for name,side in dirs.items():
                    a=np.where((side>0)[:,None,None],vals[1],vals[-1])
                    for pi,hold in enumerate(holds):
                        ret.append(a[:,pi,:].astype(np.float32))
                        spec.append((clockname,delay,name,stop,tp,kind,activation,val,hold))
                del vals
        print("STEP53_CLOCK",clockname,"arms",len(ret),flush=True)
    Y=np.stack(ret);del ret
    # Scores chosen solely on 2025, against all primary scenarios. No return
    # feedback is needed so real net-cost changes cannot alter future choices.
    def rank(y,mask):
        a=y[:,mask,:][:,:,PRIMARY]
        monthly=[]
        for month in range(12):
            ix=mi[mask]==month
            monthly.append(np.log1p(a[:,ix,:]).sum(1))
        mo=np.stack(monthly,axis=1)
        total=mo.sum(1)
        # Score worst-case monthly deficits, loss months and total net,
        # penalize excessive risk by preferring the smallest negative tail.
        return total.min(1)+.65*np.minimum(mo,0).sum(1).min(1)+.15*mo.min((1,2))
    trainmask=np.arange(n)<train
    rr=rank(Y,trainmask)
    # Include 80 leading universal policies and 100 leading policies per
    # known event/fallback branch. Only these predeclared pairs are combined.
    top=np.argsort(rr)[-80:][::-1]
    e=np.argsort(rank(Y,trainmask&event))[-100:][::-1]
    f=np.argsort(rank(Y,trainmask&~event))[-100:][::-1]
    candidates=[(int(i),int(i)) for i in top]
    candidates.extend((int(i),int(j)) for i in e for j in f)
    def path(pair):
        i,j=pair;return np.where(event[:,None],Y[i],Y[j])
    def train_key(y):
        r,d,mo=scores(y[:train],mi[:train])
        m=mo[:12,PRIMARY];r=r[PRIMARY];d=d[PRIMARY]
        return (float(np.min(r)-.8*np.max(d)+.6*np.minimum(m,0).sum(0).min()),float(m.min()))
    chosen=max(candidates,key=lambda p:train_key(path(p)))
    # Research-only oracle over the same pairs, explicitly NOT a validation.
    def robust_key(y):
        r,d,mo=scores(y,mi);r=r[PRIMARY];d=d[PRIMARY];mo=mo[:,PRIMARY]
        return (int((mo>=.01).sum(0).min()),float(np.min(r)-.8*np.max(d)+.6*np.minimum(mo,0).sum(0).min()),float(mo.min()))
    research=max(candidates,key=lambda p:robust_key(path(p)))
    def audit(pair,tag):
        predicted=path(pair).astype(float)
        selected=[];details=[]
        for d in range(n):
            p=pair[0] if event[d] else pair[1]
            cn,delay,name,stop,tp,kind,act,val,hold=spec[p];j=int(clock[cn][d]+delay)
            if name.startswith("range"):
                pos=(c[j-1]-l[j-60:j].min())/max(h[j-60:j].max()-l[j-60:j].min(),1e-12)
                sd=1 if pos>=.5 else -1
                if name.endswith("fade"):sd=-sd
            else:
                length=int("".join(x for x in name if x.isdigit()))
                sd=1 if c[j-1]>=o[j-length] else -1
                if name.startswith("fade"):sd=-sd
            cfg=[kind,stop,tp,120,act,val,0.]
            end,mid,why,sl,mae,both=replay_one(o,h,l,c,j,sd,cfg,[0.,0.,0.,hold])
            selected.append((j,end,sd,mid,why,sl,mae,both))
            assert m.index[j].tz_convert("Asia/Kolkata").date()==m.index[end].tz_convert("Asia/Kolkata").date()
            if d:assert selected[d-1][1]<j
        for k,(mode,slip) in enumerate(SCENARIOS):
            risk.mode=mode;risk.slip=slip
            eq=peak=1.;dd=0.;liquidations=0;actual=[]
            for j,end,sd,mid,why,sl,mae,both in selected:
                y,fee,fund=risk.prices(np.array([j]),np.array([[end-j]]),sd,np.array([[sd*(mid-o[j])]]))
                y=float(y[0,0]);actual.append(y)
                en=o[j]+sd*slip
                for a,b in zip(risk.mark_low[j:end+1],risk.mark_high[j:end+1]):
                    assert np.isfinite(a+b)
                    adv=a if sd==1 else b;fav=b if sd==1 else a
                    peak=max(peak,eq*(1+sd*(fav-en)/en-base.COST))
                    loweq=eq*(1+sd*(adv-en)/en-2*base.COST-fund[0,0])
                    dd=max(dd,1-loweq/peak)
                if 1+min(sd*(risk.mark_low[j:end+1].min()-en)/en,sd*(risk.mark_high[j:end+1].max()-en)/en)-2*base.COST-fund[0,0]<=.005:liquidations+=1
                eq*=1+y;peak=max(peak,eq);dd=max(dd,1-eq/peak)
            assert np.max(np.abs(np.array(actual)-predicted[:,k]))<2e-8
            z=metrics(np.array(actual)[:,None],mi)
            row=dict(mode=mode,slip=slip,net_pct=float(z["net_pct"][0]),closed_dd_pct=float(z["dd_pct"][0]),
                     mark_dd_pct=100*dd,months_ge1=int(z["months_ge1"][0]),positive_months=int(z["positive_months"][0]),
                     worst_month_pct=float(z["worst_month_pct"][0]),one_x_liquidation_proxy=liquidations,
                     monthly_pct=z["monthly_pct"][:,0].tolist())
            details.append(row)
            print("STEP53_SCENARIO",tag,json.dumps(row),flush=True)
        report=dict(tag=tag,arms=[spec[x] for x in pair],trade_count=n,independent_fill_parity=True,
                    scenario_results=details,all_primary_pass=all(x["months_ge1"]==22 and x["mark_dd_pct"]<=2.506676 for x in details[:6]),
                    research_exposed=True,actual_settlement_verified=False,demo_verified=False)
        (OUT/(tag+".json")).write_text(json.dumps(report,indent=2))
        print("STEP53_RESULT",json.dumps({k:v for k,v in report.items() if k!="scenario_results"}),flush=True)
    print("STEP53_SEARCH",len(spec),len(candidates),flush=True)
    audit(chosen,"2025_selected_2026_recheck")
    audit(research,"all_months_research")
if __name__=="__main__":main()
