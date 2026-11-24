"""Independent single-order replay and frozen-fill cost sensitivity."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

def tag_cache(cache,starts):
    for (side,guard,cap),raw in list(cache.items()):
        pnl,fees,gross,reason,hold=raw
        n,p,_=pnl.shape
        extra=np.empty((n,p,8))
        extra[:,:,0]=np.asarray(starts)[:,None]
        extra[:,:,1]=side
        extra[:,:,2]=int(guard)
        extra[:,:,3]=-1 if cap is None else cap
        extra[:,:,4]=np.arange(p)[None,:]
        extra[:,:,5]=hold
        extra[:,:,6]=reason
        extra[:,:,7]=gross
        cache[(side,guard,cap)]=(np.concatenate((pnl,extra),axis=2),*raw[1:])
    return cache

from research_btc_daily_preentry_risk_step18 import preentry_features as original_preentry_features

def risk_features_prior_close(m,starts,sides):
    result=original_preentry_features(m,starts,sides)
    hi=m.high.to_numpy(float);lo=m.low.to_numpy(float);cl=m.close.to_numpy(float)
    result["range60"]=np.array([(hi[i-60:i].max()-lo[i-60:i].min())/cl[i-1] for i in starts])
    return result

def replay_one(o,h,l,c,start,side,recipe,policy):
    kind,sl,tp,_,act,value,step=recipe
    typ,threshold,after,limit=policy
    sl,tp,act,value,step,threshold=np.array([sl,tp,act,value,step,threshold])/100
    mid=float(o[start])
    # Work in directional return coordinates, independently of old simulator.
    stop=-sl; target=tp; max_favorable=0.
    initial_stop=mid*(1+side*stop)
    points=[]
    exit_idx=start+int(limit);exit_mid=float(o[exit_idx]);why=3
    simultaneous=False
    for j in range(start,start+int(limit)):
        adverse=side*((l[j] if side==1 else h[j])/mid-1)
        favorable=side*((h[j] if side==1 else l[j])/mid-1)
        open_move=side*(o[j]/mid-1)
        stop_hit=adverse<=stop+1e-14
        target_hit=favorable>=target-1e-14
        if stop_hit:
            points.append(min(open_move,stop));simultaneous=bool(target_hit)
            exit_idx=j;exit_mid=min(o[j],mid*(1+side*stop)) if side==1 else max(o[j],mid*(1+side*stop));why=2;break
        if target_hit:
            points.append(adverse)
            exit_idx=j;exit_mid=mid*(1+side*target);why=1;break
        points.append(adverse)
        max_favorable=max(max_favorable,favorable)
        if max_favorable>=act:
            if kind==1:stop=max(stop,value)
            elif kind==2:stop=max(stop,max_favorable-value)
            elif kind==3:stop=max(stop,value+int((max_favorable-act+1e-12)/step)*step)
        close_move=side*(c[j]/mid-1)
        if j-start+1>=after and ((typ==1 and close_move<=-threshold) or (typ==2 and max_favorable<threshold) or (typ==3 and close_move>=threshold)):
            exit_idx=j+1;exit_mid=float(o[exit_idx]);why=4;break
    return exit_idx,exit_mid,why,initial_stop,min([0.,*points]),simultaneous

def audit_fills(m,cfg,features,mask,policies,labels,selected,s,out,strict):
    o,h,l,c=[m[k].to_numpy(float) for k in ("open","high","low","close")]
    fee=float(s.base.COST); slip=float(s.base.SLIP)
    configs={}
    for side in (-1,1):
        cc,_=s.previous.step25.preentry_stop(cfg,features,mask,np.full(len(mask),side,dtype=np.int8),"tight60_050_both_cap040")
        configs[(side,False)]=cc
        configs[(side,True)]=s.previous.step28.change_trailing(cc,mask,.18,"E3_later_larger_lock","F3_normal_tight")
    rows=[]
    for i,row in enumerate(selected):
        start,side,guard,cap,pid,hold,reason,gross=row[2:]
        start,side,pid=int(start),int(side),int(pid)
        recipe=configs[(side,bool(guard))][i].copy()
        if cap>=0:recipe[1]=min(recipe[1],cap)
        end,outmid,why,sl,mae,both=replay_one(o,h,l,c,start,side,recipe,policies[pid])
        entry=o[start]+side*slip;exitfill=outmid-side*slip
        nstd=(side*(exitfill-entry)-fee*(entry+exitfill))/entry
        noffer=(side*(exitfill-entry)-fee*entry-(fee*exitfill if end-start>30 else 0))/entry
        assert why==int(reason) and end-start==int(hold),(i,why,reason,end-start,hold)
        assert abs(side*(outmid-o[start])-gross)<1e-7
        assert abs(nstd-row[0])<1e-11 and abs(noffer-row[1])<1e-11,(i,nstd,noffer,row[:2])
        rows.append(dict(day_ist=s.base.IST_DAYS[i],month=s.MONTHS[i],entry_utc=m.index[start],exit_utc=m.index[end],
                         direction=side,entry_mid=o[start],exit_mid=outmid,entry_fill=entry,exit_fill=exitfill,
                         initial_stop=sl,exit_policy=labels[pid],hold_min=end-start,reason=why,adverse_move=mae,
                         simultaneous_stop_tp=both,net_offer=noffer,net_standard=nstd))
    df=pd.DataFrame(rows)
    assert len(df)==477 and df.day_ist.nunique()==477
    assert pd.to_datetime(df.day_ist).dt.dayofweek.lt(5).all()
    assert (df.entry_utc<df.entry_utc.shift(-1)).iloc[:-1].all()
    assert (df.exit_utc<df.entry_utc.shift(-1)).iloc[:-1].all()
    assert df.hold_min.between(0,30).all()
    assert (df.entry_utc.dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m-%d")==df.day_ist).all()
    prefix="prior_close" if strict else "original"
    df.to_csv(out/(prefix+"_independent_trade_ledger.csv"),index=False)
    def metrics(y):
        equity=np.cumprod(1+np.asarray(y))
        monthly=pd.Series(np.asarray(y),index=df.month).groupby(level=0).apply(lambda z:100*(np.prod(1+z)-1))
        return dict(net_pct=float(100*(equity[-1]-1)),dd_pct=float(100*np.max(1-equity/np.maximum.accumulate(np.r_[1.,equity])[1:])),months_positive=int((monthly>0).sum()),months_ge1=int((monthly>=1).sum()),worst_month_pct=float(monthly.min()),monthly=monthly.to_dict())
    stress=[]
    # Date-aware conservative historical fee schedule: documented 30m upgrade
    # in October 2025. Earlier opt-in/eligibility is unknown, so no pre-upgrade waiver.
    upgrade=pd.Timestamp("2025-10-14",tz="Asia/Kolkata")
    is_after=df.entry_utc>=upgrade
    for slip_pts in (0,5,10,20,30,50,75,100,200):
        for mode in ("offer30","offer15","standard","historical_conservative","historical_15min_sensitivity"):
            a=df.entry_mid+df.direction*slip_pts;b=df.exit_mid-df.direction*slip_pts
            if mode=="offer30":waived=df.hold_min<30
            elif mode=="offer15":waived=df.hold_min<15
            elif mode=="historical_conservative":waived=is_after&(df.hold_min<30)
            elif mode=="historical_15min_sensitivity":waived=(is_after&(df.hold_min<30))|(~is_after&(df.hold_min<15))
            else:waived=np.zeros(len(df),bool)
            y=(df.direction*(b-a)-fee*a-fee*b*(~waived))/a
            stress.append(dict(slip_per_side=slip_pts,mode=mode,**metrics(y)))
    pd.DataFrame([{k:v for k,v in r.items() if k!="monthly"} for r in stress]).to_csv(out/(prefix+"_fixed_trade_cost_stress.csv"),index=False)
    # Hourly funding candles are observations, not independently proven settlements.
    funding_root=Path("data/delta_india/BTCUSD/institutional/history/funding_1h")
    fundfiles=sorted(funding_root.glob("*.csv.gz"))
    fsinfo={"files":len(fundfiles),"settlement_verified":False}
    if fundfiles:
        f=pd.concat([pd.read_csv(p) for p in fundfiles],ignore_index=True)
        fsinfo.update(columns=list(f.columns),rows=len(f),sample=f.head(2).to_dict("records"))
    # Conservative funding sensitivity: absolute funding charge of 0.01% or
    # 0.05% for every position crossing an illustrative 8-hour UTC boundary.
    crosses=[]
    for a,b in zip(df.entry_utc,df.exit_utc):
        tick=a.floor("8h")+pd.Timedelta(hours=8)
        crosses.append(a<tick<=b or a==a.floor("8h"))
    crosses=np.array(crosses,bool)
    funding=[]
    for rate in (.0001,.0005,.001):
        funding.append(dict(absolute_rate_pct=rate*100,crossing_trades=int(crosses.sum()),**metrics(df.net_offer-rate*crosses)))
    report=dict(strict_preentry=strict,trades=len(df),independent_fill_parity=True,weekday_unique=True,no_overlap=True,
        zero_minute_exits=int((df.hold_min==0).sum()),thirty_minute_exits=int((df.hold_min==30).sum()),simultaneous_hits=int(df.simultaneous_stop_tp.sum()),
        offer=metrics(df.net_offer),standard=metrics(df.net_standard),worst_intratrade_adverse_pct=float(-100*df.adverse_move.min()),
        funding_archive=fsinfo,funding_sensitivity=funding,stress=stress,
        limitations=["Frozen orders repriced, not feedback-aware strategy replay under stressed fees",
                     "OHLC cannot establish exact intraminute duration, spread, orderbook, latency or actual fill",
                     "Funding candles not proof of settled debits; no independent account settlement ledger",
                     "Historical offer activation and exact effective date not verified; date cutoff illustrative",
                     "One-times notional, no leverage liquidation model",
                     "All 22 months used for selection; no clean holdout"])
    (out/(prefix+"_audit.json")).write_text(json.dumps(report,indent=2,default=str))
    print("STEP52_AUDIT",json.dumps({k:v for k,v in report.items() if k not in ("stress","funding_sensitivity")},default=str),flush=True)
    for r in stress:
        if r["slip_per_side"] in (5,20,50,100,200):
            print("STEP52_COST_STRESS",json.dumps({k:v for k,v in r.items() if k!="monthly"}),flush=True)
    for r in funding:print("STEP52_FUNDING_SENSITIVITY",json.dumps({k:v for k,v in r.items() if k!="monthly"}),flush=True)
