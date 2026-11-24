#!/usr/bin/env python3
"""Step31: separate preentry market filter for fallback reversal vs stop cap."""
from itertools import product
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_btc_fallback_specific_loss_step30 as s30
from research_btc_fallback_specific_loss_step30 import base,step13,step15,early,previous,choose_fallback,fallback_is_losing,N,TRAIN,MONTHS
OUT=Path("analysis/btc_fallback_selective_step31")
def simulate(setting,cache,mask,ridge_sides,info,ids,reverse_mask,cap_mask):
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
    equity=1.;peak=1.;fallback_equity=1.;fb_previous=[]
    for d in range(N):
        if MONTHS[d]!=month:
            month=MONTHS[d]
            equity=1.;peak=1.;fallback_equity=1.;fb_previous=[]
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
        if fallback_trigger and reverse_mask[d]:
            trade_side=choose_fallback(dir_name,trade_side,d,info)
        side[d]=trade_side
        if abs(trade_side)!=1:raise AssertionError("Zero position side")
        chosen_cap=(cap if fallback_trigger and cap_mask[d] else None)
        eid=previous.entry_exit_id(
            bool(mask[d]),mtd,fallback_trigger,exit_name,ids)
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
        peak=max(peak,equity)
        if mask[d]:
            fb_previous.append(outcome)
            fallback_equity*=1.+outcome
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
        out=out,pnl=pnl,fee=fee,gross=gross,reason=reason,hold=hold,
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


def filters(f,side):
    out={"all":np.ones(N,dtype=bool),"none":np.zeros(N,dtype=bool)}
    for name in ("r5","r60","r240"):
        out[name+"_aligned"]=side*f[name]>=0
        out[name+"_opposed"]=side*f[name]<0
    for name,key,limit in (
        ("abs5","r5",.001),("abs60","r60",.003),
        ("range60","range60",.005),("rvol125","rvol5",1.25),
        ("rvol175","rvol5",1.75)):
        val=np.abs(f[key])
        out[name+"_high"]=val>=limit
        out[name+"_low"]=val<limit
    out["outer_quartile"]=(f["loc60"]<=.25)|(f["loc60"]>=.75)
    out["middle_half"]=~out["outer_quartile"]
    assert len(out)==20
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,orig,hours,idx,cfg=step13.create_path()
    policies,names=early.build_exit_policies()
    ids={n:i for i,n in enumerate(names)}
    features,ridge=previous.all_features_and_sides(m,mask,idx,orig,cfg,policies)
    cache,_=previous.raw_cache(m,mask,idx,cfg,features,policies)
    fs=filters(features,ridge)
    def calc(reverse,stop,cap):
        return simulate(("fallback_month_cumulative_below025","invert_high_rvol",cap,"base"),cache,mask,ridge,features,ids,fs[reverse],fs[stop])
    b=calc("none","none",.2)
    rec=calc("all","all",.2)
    bo=b["out"]["scalper_offer"]
    ro=rec["out"]["scalper_offer"]
    assert abs(bo["performance"]["net_total_pct"]-28.574051)<.00011
    assert abs(bo["january2025"]+1.04710143575)<.00011
    assert abs(ro["performance"]["net_total_pct"]-25.987617)<.00011
    assert abs(ro["january2025"]-.03422097933)<.00011
    print("STEP31_CONTROLS_VERIFIED",flush=True)
    rows=[]
    months=[]
    month_labels=list(dict.fromkeys(MONTHS.tolist()))
    for j,(rev,stop,cap) in enumerate(product(fs,fs,(.15,.20,.25)),1):
        result=calc(rev,stop,cap)
        for fee in base.MODES:
            p=result["out"][fee]
            stats=p["performance"]
            assert stats["trades"]==477
            meta=dict(reverse_filter=rev,stop_filter=stop,cap=cap,cost=fee)
            rows.append(dict(**meta,jan2025=p["january2025"],jan2026=p["january2026"],**stats))
            for month,value in zip(month_labels,p["monthly"]):
                months.append(dict(**meta,month=month,net_pct=float(value)))
        if j%300==0:print("STEP31_PROGRESS",j,flush=True)
    grid=pd.DataFrame(rows)
    assert len(grid)==2400
    grid.to_csv(OUT/"all_1200_models_both_fees.csv",index=False)
    pd.DataFrame(months).to_csv(OUT/"all_monthly_results.csv",index=False)
    offer=grid[grid.cost=="scalper_offer"]
    strict=offer[(offer.win_months_2025==12)&(offer.return_2025_pct>=11.982383)&(offer.profitable_days_2025>=154)&(offer.max_dd_2025<=2.617770)]
    all22=offer[offer.win_months_all==22].sort_values("net_total_pct",ascending=False)
    guarded=offer[(offer.win_months_all>=21)&(offer.net_total_pct>=28.574051)&(offer.max_closed_dd_pct<=2.617770)].sort_values(["jan2025","net_total_pct"],ascending=False)
    january=offer[offer.jan2025>0].sort_values(["win_months_all","net_total_pct"],ascending=False)
    all22.to_csv(OUT/"hindsight_22_months.csv",index=False)
    guarded.to_csv(OUT/"hindsight_net_dd_guard.csv",index=False)
    january.to_csv(OUT/"hindsight_january_positive.csv",index=False)
    def key(row):return (row.reverse_filter,row.stop_filter,float(row.cap))
    selected=key(strict.sort_values("return_2025_pct",ascending=False).iloc[0]) if len(strict) else ("none","none",.2)
    diag=key(all22.iloc[0]) if len(all22) else key(january.iloc[0]) if len(january) else key(guarded.iloc[0])
    best=key(guarded.iloc[0]) if len(guarded) else selected
    reports={}
    for tag,k in (("baseline",("none","none",.2)),("recovery_control",("all","all",.2)),("selected",selected),("hindsight_jan_positive_or_22",diag),("hindsight_guarded",best)):
        res=calc(*k)
        # export original 477-day audit with additional masks explicitly named
        report=s30.export(tag,("fallback_month_cumulative_below025","invert_high_rvol",k[2],"base"),res,ridge,hours,mask)
        for fee in base.MODES:
            path=OUT/(tag+"_"+fee+"_477_daily.csv")
            # s30.export uses its module OUT (set below)
            daily=pd.read_csv(path)
            daily["reverse_market_filter"]=k[0]
            daily["stop_market_filter"]=k[1]
            daily["reverse_market_filter_pass"]=fs[k[0]]
            daily["stop_market_filter_pass"]=fs[k[1]]
            daily.to_csv(path,index=False)
        reports[tag]=dict(settings=k,fees=report)
        print("STEP31_AUDIT "+json.dumps({"tag":tag,**reports[tag]},default=str),flush=True)
    summary=dict(models=1200,january_positive=len(january),positive_22_months=len(all22),strict_2025=len(strict),reports=reports,warning="Both historical years heavily researched; closing fee waiver hypothetical; no live validation.")
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
    print("STEP31_COMPLETE "+json.dumps({k:v for k,v in summary.items() if k!="reports"}),flush=True)

if __name__=="__main__":
    s30.OUT=OUT
    main()
