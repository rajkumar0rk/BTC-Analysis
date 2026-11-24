#!/usr/bin/env python3
from pathlib import Path
from itertools import product
import json
import numpy as np
import pandas as pd
import research_btc_fallback_specific_loss_step30 as s30
import research_btc_fallback_selective_step31 as s31
from research_btc_fallback_specific_loss_step30 import base,step13,step15,early,previous,choose_fallback,fallback_is_losing,N,TRAIN,MONTHS
OUT=Path("analysis/btc_event_low_month_step33")
GATES=("last_negative","last_loss025","last_two_negative","last_two_sum025","event_mtd025","event_mtd050","total_mtd025")
CAPS=(None,.15,.20,.25,.30,.35)
EXITS=("base","adverse_cut_0.08pct_after_5m","adverse_cut_0.08pct_after_10m","profit_close_at_0.1pct_after_10m","profit_close_at_0.15pct_after_20m","hard_timeout_20m")
def gate(rule,hist,eq,mtd):
    n=len(hist)
    if rule=="off":return False
    if rule=="total_mtd025":return mtd<=.0025
    if n==0:return False
    if rule=="last_negative":return hist[-1]<0
    if rule=="last_loss025":return hist[-1]<=-.0025
    if rule=="last_two_negative":return n>=2 and max(hist[-2:])<0
    if rule=="last_two_sum025":return n>=2 and sum(hist[-2:])<=-.0025
    if rule=="event_mtd025":return eq<=.9975
    if rule=="event_mtd050":return eq<=.995
    raise KeyError(rule)
def simulate(setting,cache,mask,ridge_sides,info,ids,reverse_mask,cap_mask,reverse_depth,cap_depth,event_gate,event_filter,event_cap,event_exit):
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
    event_history=[];event_equity=1.
    event_active=np.zeros(N,dtype=bool)
    equity=1.;peak=1.;fallback_equity=1.;fb_previous=[]
    for d in range(N):
        if MONTHS[d]!=month:
            month=MONTHS[d]
            equity=1.;peak=1.;fallback_equity=1.;fb_previous=[]
            event_history=[];event_equity=1.
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
        out=out,event_active=event_active,pnl=pnl,fee=fee,gross=gross,reason=reason,hold=hold,
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
    middle=s31.filters(features,ridge)["middle_half"]
    cl=m.close.to_numpy(float);hi=m.high.to_numpy(float);lo=m.low.to_numpy(float)
    width=np.asarray([(hi[i-60:i].max()-lo[i-60:i].min())/cl[i-1] for i in idx])
    filters={"all":np.ones(N,dtype=bool),"counter60":ridge*features["r60"]<0,"high_rvol":features["rvol5"]>=1.25,"wide_range":width>=.005}
    def calc(g,f,c,e):
        return simulate(("fallback_month_cumulative_below025","invert_high_rvol",.20,"base"),cache,mask,ridge,features,ids,middle,middle,.5,.75,g,filters[f],c,None if e=="base" else ids[e])
    baseline=calc("off","all",None,"base")
    bo=baseline["out"]["scalper_offer"];base_month=bo["monthly"]
    assert abs(bo["performance"]["net_total_pct"]-30.490263)<.00011 and bo["performance"]["win_months_all"]==22
    assert abs(bo["performance"]["max_closed_dd_pct"]-2.617670)<.00011
    assert abs(baseline["out"]["standard"]["performance"]["net_total_pct"]+1.507253)<.00011
    print("STEP33_BASELINE_VERIFIED",flush=True)
    rows=[];months=[];month_labels=list(dict.fromkeys(MONTHS.tolist()));configs={}
    for j,k in enumerate(product(GATES,filters,CAPS,EXITS),1):
        g,f,c,e=k;name=str(j);configs[name]=k
        r=calc(*k)
        for fee in base.MODES:
            p=r["out"][fee];stats=p["performance"]
            assert stats["trades"]==477
            diff=p["monthly"]-baseline["out"][fee]["monthly"]
            meta=dict(model=name,gate=g,market_filter=f,cap=c,early_exit=e,cost=fee)
            rows.append(dict(**meta,minimum_month=float(p["monthly"].min()),months_lower=int((diff< -1e-9).sum()),months_higher=int((diff>1e-9).sum()),activated_days=int(r["event_active"].sum()),**stats))
            for month,value in zip(month_labels,p["monthly"]):
                months.append(dict(**meta,month=month,net_pct=float(value)))
        if j%252==0: print("STEP33_PROGRESS",j,flush=True)
    grid=pd.DataFrame(rows);assert len(grid)==2016
    grid.to_csv(OUT/"all_1008_models_both_fees.csv",index=False)
    pd.DataFrame(months).to_csv(OUT/"all_monthly_returns.csv",index=False)
    o=grid[grid.cost=="scalper_offer"]
    admiss=o[(o.win_months_all==22)&(o.net_total_pct>=30.490263-1e-6)&(o.max_closed_dd_pct<=2.617770)]
    improving=admiss[admiss.minimum_month>float(base_month.min())+1e-9]
    pareto=improving[improving.months_lower==0].sort_values(["minimum_month","net_total_pct"],ascending=False)
    no_harm=admiss[(admiss.months_lower==0)&(admiss.months_higher>0)].sort_values(["minimum_month","net_total_pct"],ascending=False)
    alt=improving.sort_values(["minimum_month","net_total_pct"],ascending=False)
    no_harm.to_csv(OUT/"historical_no_month_reduction.csv",index=False)
    alt.to_csv(OUT/"historical_min_month_improved.csv",index=False)
    s30.OUT=OUT
    reports={}
    for tag,row in (("baseline",None),("best_no_harm",no_harm.iloc[0] if len(no_harm) else None),("best_minimum",alt.iloc[0] if len(alt) else None)):
        k=("off","all",None,"base") if row is None else configs[str(row.model)]
        r=calc(*k)
        p=s30.export(tag,("fallback_month_cumulative_below025","invert_high_rvol",.20,"base"),r,ridge,hours,mask)
        for fee in base.MODES:
            fn=OUT/(tag+"_"+fee+"_477_daily.csv")
            df=pd.read_csv(fn);df["event_overlay_active"]=r["event_active"];df["event_gate"]=k[0];df["event_filter"]=k[1];df["event_cap"]=k[2];df["event_exit"]=k[3];df.to_csv(fn,index=False)
        vals=r["out"]["scalper_offer"]["monthly"]
        reports[tag]=dict(settings=k,fees=p,monthly=dict(zip(month_labels,map(float,vals))),changes={month:float(delta) for month,delta in zip(month_labels,vals-base_month) if abs(delta)>1e-9})
        print("STEP33_AUDIT "+json.dumps(dict(tag=tag,**reports[tag]),default=str),flush=True)
    summary=dict(models=1008,full_guard=len(admiss),improving_minimum=len(improving),no_harm_minimum_improved=len(pareto),no_harm_any_improvement=len(no_harm),reports=reports,warning="Full-history retrospective selection, not validated, hypothetical fee waiver.")
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
    print("STEP33_COMPLETE "+json.dumps({k:v for k,v in summary.items() if k!="reports"}),flush=True)
if __name__=="__main__":main()
