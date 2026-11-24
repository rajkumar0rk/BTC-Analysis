#!/usr/bin/env python3
from pathlib import Path
from itertools import product
import json
import numpy as np
import pandas as pd
import research_btc_fallback_specific_loss_step30 as s30
import research_btc_fallback_selective_step31 as s31
from research_btc_event_low_month_step33 import gate
from research_btc_monthly_floor_step34 import adjust
from research_btc_fallback_specific_loss_step30 import base,step13,step15,early,previous,choose_fallback,fallback_is_losing,N,TRAIN,MONTHS
OUT=Path("analysis/btc_one_percent_monthly_floor_step36")
def simulate(setting,cache,mask,ridge_sides,info,ids,reverse_mask,cap_mask,reverse_depth,cap_depth,event_gate,event_filter,event_cap,event_exit,overlays):
    state,dir_name,cap,exit_name=setting
    pnl=np.empty((len(base.MODES),N),dtype=float)
    fee=np.empty((len(base.MODES),N),dtype=float)
    gross=np.empty(N)
    reason=np.empty(N,dtype=np.int8)
    hold=np.empty(N,dtype=np.int16)
    side=np.empty(N,dtype=np.int8)
    exit_policy=np.empty(N,dtype=np.int16)
    prior_mtd=np.zeros(N)
    prior_highwater=np.zeros(N)
    prior_month_giveback=np.zeros(N)
    prior_fallback_equity=np.zeros(N)
    prior_fallback_count=np.zeros(N,dtype=np.int16)
    prior_fallback_lost=np.zeros(N,dtype=np.int16)
    fallback_loss_trigger=np.zeros(N,dtype=bool)
    month_highwater_trigger=np.zeros(N,dtype=bool)
    month=None
    completed=0
    target_active=np.zeros(N,dtype=bool)
    event_history=[];event_equity=1.
    event_active=np.zeros(N,dtype=bool)
    equity=1.;peak=1.;fallback_equity=1.;fb_previous=[]
    for d in range(N):
        if MONTHS[d]!=month:
            month=MONTHS[d]
            equity=1.;peak=1.;fallback_equity=1.;fb_previous=[]
            event_history=[];event_equity=1.;completed=0
        mtd=equity-1.
        prior_mtd[d]=mtd
        prior_highwater[d]=peak-1.
        prior_month_giveback[d]=peak-equity
        prior_fallback_equity[d]=fallback_equity-1.
        prior_fallback_count[d]=len(fb_previous)
        prior_fallback_lost[d]=sum(v<0 for v in fb_previous)
        # Step28 high-water guard: independent of fallback regime.
        peakguard=(peak>=1.01 and peak-equity>=.0075)
        month_highwater_trigger[d]=peakguard
        # Trigger only if this day is the mandatory fallback entry.
        fallback_trigger=(bool(mask[d]) and
                          fallback_is_losing(state,fb_previous,
                                             fallback_equity))
        fallback_loss_trigger[d]=fallback_trigger
        trade_side=int(ridge_sides[d])
        if fallback_trigger and reverse_mask[d] and fallback_equity<=1.-reverse_depth/100.:
            trade_side=choose_fallback(dir_name,trade_side,d,info)
        side[d]=trade_side
        if abs(trade_side)!=1:raise AssertionError("Zero position side")
        chosen_cap=(cap if fallback_trigger and cap_mask[d] and fallback_equity<=1.-cap_depth/100. else None)
        eid=previous.entry_exit_id(
            bool(mask[d]),mtd,fallback_trigger,exit_name,ids)
        use_event=(not mask[d] and event_filter[d] and gate(event_gate,event_history,event_equity,mtd))
        event_active[d]=use_event
        if use_event:
            chosen_cap=event_cap
            if event_exit is not None: eid=event_exit
        for overlay in overlays:
            target,pace,wait,scope,direction,extra_cap,extra_exit,side_filter,exit_filter=overlay
            threshold=target*min(completed/20.,1.) if pace else target
            active=completed>=wait and mtd<threshold and (scope=='both' or (scope=='fallback')==bool(mask[d]))
            target_active[d]=target_active[d] or active
            if active:
                if trade_side==int(ridge_sides[d]) and side_filter[d]:
                    trade_side=adjust(direction,trade_side,d,info)
                side[d]=trade_side
                if extra_cap is not None:
                    chosen_cap=extra_cap if chosen_cap is None else min(chosen_cap,extra_cap)
                if extra_exit is not None and exit_filter[d]: eid=extra_exit
        exit_policy[d]=eid
        source=cache[(trade_side,peakguard,chosen_cap)]
        pnl[:,d]=source[0][d,eid,:]
        fee[:,d]=source[1][d,eid,:]
        gross[d]=source[2][d,eid]
        reason[d]=source[3][d,eid]
        hold[d]=source[4][d,eid]
        outcome=float(pnl[base.MODES.index("scalper_offer"),d])
        if not np.isfinite(outcome) or outcome<=-1.:
            raise AssertionError("Invalid realized return")
        equity*=1.+outcome
        completed+=1
        peak=max(peak,equity)
        if mask[d]:
            fb_previous.append(outcome)
            fallback_equity*=1.+outcome
        else:
            event_history.append(outcome)
            event_equity*=1.+outcome
    out={}
    for i,fee_mode in enumerate(base.MODES):
        path=(pnl[i],fee[i],gross,reason,hold)
        monthly=previous.step28.step26.month_numbers(path[0])
        stats=step15.score(path)
        if len(monthly)!=22 or stats["trades"]!=477 or stats["win_months_all"]!=int(np.sum(monthly>0)):
            raise AssertionError("Month count or missing 477 weekday trades")
        out[fee_mode]=dict(
            performance=stats,monthly=monthly,
            january2025=float(monthly[0]),
            january2026=float(monthly[12]))
    return dict(
        out=out,event_active=event_active,target_active=target_active,pnl=pnl,fee=fee,gross=gross,reason=reason,hold=hold,
        side=side,policy=exit_policy,
        mtd=prior_mtd,prior_peak=prior_highwater,
        giveback=prior_month_giveback,
        fallback_mtd=prior_fallback_equity,
        fallback_history_n=prior_fallback_count,
        fallback_history_losers=prior_fallback_lost,
        fallback_loss_trigger=fallback_loss_trigger,
        highwater_guard=month_highwater_trigger,
        sides_changed=int(np.sum((side!=ridge_sides)&mask))
    )







def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,orig,hours,idx,cfg=step13.create_path()
    policies,names=early.build_exit_policies()
    ids={n:i for i,n in enumerate(names)}
    features,ridge=previous.all_features_and_sides(m,mask,idx,orig,cfg,policies)
    cache,_=previous.raw_cache(m,mask,idx,cfg,features,policies)
    fs=s31.filters(features,ridge);middle=fs["middle_half"]
    cl=m.close.to_numpy(float);hi=m.high.to_numpy(float);lo=m.low.to_numpy(float)
    width=np.asarray([(hi[i-60:i].max()-lo[i-60:i].min())/cl[i-1] for i in idx])
    exfilters=("all","none","r5_aligned","r5_opposed","r60_aligned","r60_opposed","range60_high","range60_low","rvol175_high","rvol175_low")
    assert len(fs)==20 and all(x in fs for x in exfilters)
    locked=(.005,False,5,"event","fade5",None,None,fs["range60_high"],fs["none"])
    def calc(k=None):
        overlays=[locked]
        if k is not None:
            pace,wait,scope,sidef,exitf=k
            overlays.append((.01,pace,wait,scope,"fade5",None,ids["hard_timeout_20m"],fs[sidef],fs[exitf]))
        return simulate(("fallback_month_cumulative_below025","invert_high_rvol",.20,"base"),cache,mask,ridge,features,ids,middle,middle,.5,.75,"last_two_negative",width>=.005,.25,None,overlays)
    baseline=calc()
    bo=baseline["out"]["scalper_offer"];bm=bo["monthly"]
    assert abs(bo["performance"]["net_total_pct"]-33.509006)<.00011
    assert abs(bo["performance"]["max_closed_dd_pct"]-2.506676)<.00011
    assert bo["performance"]["win_months_all"]==22 and int((bm>=1).sum())==13
    assert abs(baseline["out"]["standard"]["performance"]["net_total_pct"]-.772972)<.00011
    print("STEP36_BASELINE_VERIFIED",flush=True)
    rows=[];months=[];configs={};month_labels=list(dict.fromkeys(MONTHS.tolist()))
    for j,k in enumerate(product((False,True),(5,10,15),("event","fallback","both"),fs,exfilters),1):
        configs[str(j)]=k
        r=calc(k)
        for fee in base.MODES:
            p=r["out"][fee];stats=p["performance"];v=p["monthly"]
            assert stats["trades"]==477
            diff=v-baseline["out"][fee]["monthly"]
            meta=dict(model=str(j),pace=k[0],wait=k[1],scope=k[2],direction_filter=k[3],timeout_filter=k[4],cost=fee)
            rows.append(dict(**meta,months_ge_one=int((v>=1).sum()),months_ge_half=int((v>=.5).sum()),min_month=float(v.min()),months_lower=int((diff< -1e-9).sum()),months_higher=int((diff>1e-9).sum()),shortfall=float(np.maximum(1-v,0).sum()),**stats))
            for month,value in zip(month_labels,v):months.append(dict(**meta,month=month,net_pct=float(value)))
        if j%900==0:print("STEP36_PROGRESS",j,flush=True)
    grid=pd.DataFrame(rows);assert len(grid)==7200
    grid.to_csv(OUT/"all_3600_models_both_fees.csv",index=False)
    pd.DataFrame(months).to_csv(OUT/"all_monthly_returns.csv",index=False)
    o=grid[grid.cost=="scalper_offer"]
    good=o[(o.win_months_all==22)&(o.net_total_pct>=33.509006-1e-6)&(o.max_closed_dd_pct<=2.506776)]
    strict=good[good.months_lower==0]
    order=["min_month","months_ge_one","net_total_pct"]
    strict=strict.sort_values(order,ascending=False);good=good.sort_values(order,ascending=False)
    all22=o[o.months_ge_one==22]
    strict.to_csv(OUT/"no_month_reduction.csv",index=False)
    good.to_csv(OUT/"all_positive_net_dd_guard.csv",index=False)
    all22.to_csv(OUT/"all_months_at_least_one.csv",index=False)
    s30.OUT=OUT;reports={}
    for tag,row in (("baseline",None),("best_strict",strict.iloc[0] if len(strict) else None),("best_guarded_floor",good.iloc[0] if len(good) else None),("best_guarded_count",good.sort_values(["months_ge_one","min_month","net_total_pct"],ascending=False).iloc[0] if len(good) else None),("best_unrestricted_floor",o.sort_values(order,ascending=False).iloc[0]),("best_unrestricted_count",o.sort_values(["months_ge_one","min_month","net_total_pct"],ascending=False).iloc[0])):
        k=None if row is None else configs[str(row.model)]
        r=calc(k)
        p=s30.export(tag,("fallback_month_cumulative_below025","invert_high_rvol",.20,"base"),r,ridge,hours,mask)
        for fee in base.MODES:
            fn=OUT/(tag+"_"+fee+"_477_daily.csv")
            df=pd.read_csv(fn);df["target_active"]=r["target_active"];df["target_overlay"]=str(k);df.to_csv(fn,index=False)
        v=r["out"]["scalper_offer"]["monthly"]
        reports[tag]=dict(settings=k,fees=p,monthly=dict(zip(month_labels,map(float,v))),changes={month:float(delta) for month,delta in zip(month_labels,v-bm) if abs(delta)>1e-9},at_least_one=int((v>=1).sum()),at_least_half=int((v>=.5).sum()))
        print("STEP36_AUDIT "+json.dumps(dict(tag=tag,**reports[tag]),default=str),flush=True)
    summary=dict(models=3600,all_months_one=len(all22),full_guard=len(good),no_month_reduction=len(strict),no_harm_floor_improved=int((strict.min_month>float(bm.min())+1e-9).sum()),no_harm_one_count_improved=int((strict.months_ge_one>13).sum()),reports=reports,warning="Retrospective full-history optimization; no independent validation.")
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
    print("STEP36_COMPLETE "+json.dumps({k:v for k,v in summary.items() if k!="reports"}),flush=True)
if __name__=="__main__":main()
