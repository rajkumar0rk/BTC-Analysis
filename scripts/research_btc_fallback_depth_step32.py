#!/usr/bin/env python3
from pathlib import Path
from itertools import product
import json
import numpy as np
import pandas as pd
import research_btc_fallback_specific_loss_step30 as s30
import research_btc_fallback_selective_step31 as s31
from research_btc_fallback_specific_loss_step30 import base,step13,step15,early,previous,choose_fallback,fallback_is_losing,N,TRAIN,MONTHS
OUT=Path("analysis/btc_fallback_depth_step32")
DEPTHS=(.25,.35,.50,.60,.75,1.,1.25)
CAPS=(.15,.20,.25)
def simulate(setting,cache,mask,ridge_sides,info,ids,reverse_mask,cap_mask,reverse_depth,cap_depth):
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
        if fallback_trigger and reverse_mask[d] and fallback_equity<=1.-reverse_depth/100.:
            trade_side=choose_fallback(dir_name,trade_side,d,info)
        side[d]=trade_side
        if abs(trade_side)!=1:raise AssertionError("Zero position side")
        chosen_cap=(cap if fallback_trigger and cap_mask[d] and fallback_equity<=1.-cap_depth/100. else None)
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



def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,orig,hours,idx,cfg=step13.create_path()
    policies,names=early.build_exit_policies()
    ids={n:i for i,n in enumerate(names)}
    features,ridge=previous.all_features_and_sides(m,mask,idx,orig,cfg,policies)
    cache,_=previous.raw_cache(m,mask,idx,cfg,features,policies)
    filters=s31.filters(features,ridge)
    middle=filters["middle_half"]
    none=filters["none"]
    def calc(a,b,c,baseline=False):
        return simulate(("fallback_month_cumulative_below025","invert_high_rvol",c,"base"),cache,mask,ridge,features,ids,none if baseline else middle,none if baseline else middle,a,b)
    baseline=calc(.25,.25,.25,True)
    control=calc(.25,.25,.25)
    bo=baseline["out"]["scalper_offer"]
    co=control["out"]["scalper_offer"]
    assert abs(bo["performance"]["net_total_pct"]-28.574051)<.00011
    assert abs(co["performance"]["net_total_pct"]-29.548628)<.00011
    assert abs(co["january2025"]-.07536622603)<.00011
    assert abs(co["monthly"][19]+.5664794353)<.00011
    print("STEP32_CONTROL_PARITY",flush=True)
    rows=[];months=[];month_labels=list(dict.fromkeys(MONTHS.tolist()))
    for a,b,c in product(DEPTHS,DEPTHS,CAPS):
        r=calc(a,b,c)
        for fee in base.MODES:
            p=r["out"][fee]
            stats=p["performance"]
            assert stats["trades"]==477
            meta=dict(reverse_depth=a,cap_depth=b,cap=c,cost=fee)
            diff=p["monthly"]-baseline["out"][fee]["monthly"]
            rows.append(dict(**meta,jan2025=p["january2025"],aug2026=float(p["monthly"][19]),months_lower_than_baseline=int((diff< -1e-9).sum()),**stats))
            for month,ret in zip(month_labels,p["monthly"]):
                months.append(dict(**meta,month=month,net_pct=float(ret)))
    g=pd.DataFrame(rows);assert len(g)==294
    g.to_csv(OUT/"all_147_models_both_fees.csv",index=False)
    pd.DataFrame(months).to_csv(OUT/"all_monthly_returns.csv",index=False)
    o=g[g.cost=="scalper_offer"]
    strict=o[(o.win_months_2025==12)&(o.return_2025_pct>=11.982383)&(o.profitable_days_2025>=154)&(o.max_dd_2025<=2.617770)]
    full=o[o.win_months_all==22].sort_values("net_total_pct",ascending=False)
    guard=full[(full.net_total_pct>=28.574051)&(full.max_closed_dd_pct<=2.617770)]
    allguard=o[(o.win_months_all>=21)&(o.net_total_pct>=28.574051)&(o.max_closed_dd_pct<=2.617770)].sort_values(["win_months_all","jan2025","net_total_pct"],ascending=False)
    full.to_csv(OUT/"hindsight_22_months.csv",index=False)
    def key(r):return float(r.reverse_depth),float(r.cap_depth),float(r.cap)
    selected=key(strict.sort_values("return_2025_pct",ascending=False).iloc[0]) if len(strict) else None
    best=key(guard.iloc[0]) if len(guard) else key(full.iloc[0]) if len(full) else key(allguard.iloc[0]) if len(allguard) else (.25,.25,.25)
    s30.OUT=OUT
    reports={}
    for tag,k in (("baseline",None),("step31_control",(.25,.25,.25)),("selected_2025",selected),("hindsight_best",best)):
        r=baseline if k is None else calc(*k)
        p=s30.export(tag,("fallback_month_cumulative_below025","invert_high_rvol",None if k is None else k[2],"base"),r,ridge,hours,mask)
        for fee in base.MODES:
            fn=OUT/(tag+"_"+fee+"_477_daily.csv")
            df=pd.read_csv(fn);df["reverse_loss_depth_pct"]=None if k is None else k[0];df["stop_loss_depth_pct"]=None if k is None else k[1]
            df.to_csv(fn,index=False)
        reports[tag]=dict(settings=k,fees=p)
        print("STEP32_AUDIT "+json.dumps(dict(tag=tag,**reports[tag]),default=str),flush=True)
    summary=dict(models=147,all22=len(full),all22_with_net_dd_guard=len(guard),strict_2025=len(strict),no_lower_months_all22=int((full.months_lower_than_baseline==0).sum()),reports=reports)
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
    print("STEP32_COMPLETE "+json.dumps({k:v for k,v in summary.items() if k!="reports"}),flush=True)
if __name__=="__main__":main()
