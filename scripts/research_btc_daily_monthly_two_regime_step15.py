#!/usr/bin/env python3
"""Step15. BTC monthly wins via causally independent event/fallback exit overlays.

Same 477 mandatory weekday entry times and LONG/SHORT directions as Step13.
No daily position sizing reduction, no weekday skips or additional trades.
Month equity state updated ONLY after current trade already finished.
Candidate selection uses 2025 ONLY; 2026 historical research-exposed.
"""
from pathlib import Path
from itertools import product
import json

import numpy as np
import pandas as pd

import research_btc_every_weekday_reset_step1 as base
import research_btc_daily_monthly_exit_step13 as step13
import research_btc_daily_exit_invalidation_step7 as bar
import research_btc_daily_online_direction_step6 as online

OUT=Path("analysis/btc_daily_two_regime_step15")
N=len(base.DAYS)
TRAIN=base.NTRAIN
MONTHS=np.asarray(base.MONTH_LABELS)
EVENT_GATES=("none","mtd_not_positive","peak_ge_plus1_and_giveback050","first_five_weekdays")
EVENT_EXITS=("baseline","adverse_cut_0.08pct_after_10m","profit_close_at_0.1pct_after_10m")
FALLBACK_GATES=("none","peak_ge_plus1_and_giveback050","mtd_at_least_plus1","peak_giveback_ge050")
FALLBACK_EXITS=("baseline","profit_close_at_0.1pct_after_10m","hard_timeout_20m")
assert len(EVENT_GATES)*len(EVENT_EXITS)*len(FALLBACK_GATES)*len(FALLBACK_EXITS)==144

def gate(name,mtd,peak,giveback,day):
    if name=="none":return False
    if name=="mtd_not_positive":return mtd<=0
    if name=="peak_ge_plus1_and_giveback050":return peak>=1.01 and giveback>=.005
    if name=="first_five_weekdays":return day<5
    if name=="mtd_at_least_plus1":return mtd>=.01
    if name=="peak_giveback_ge050":return giveback>=.005
    raise KeyError(name)

def replay_one(raw,mask,baseline_exit,params,ids):
    event_gate,event_exit,fallback_gate,fallback_exit=params
    chosen=np.zeros(N,dtype=np.int16)
    mtd_prior=np.zeros(N)
    peak_giveback=np.zeros(N)
    changed_ev=0
    changed_fb=0
    month=None
    equity=1.
    peak=1.
    prior_day=0
    for d in range(N):
        if MONTHS[d]!=month:
            month=MONTHS[d]
            equity=1.
            peak=1.
            prior_day=0
        mtd=equity-1
        giveback=peak-equity
        mtd_prior[d]=mtd
        peak_giveback[d]=giveback
        # Step13 immutable default. Only a triggered overlay may replace it.
        default=int(baseline_exit) if mask[d] and mtd<=.0025 else 0
        current=default
        if mask[d]:
            if fallback_exit!="baseline" and gate(
                    fallback_gate,mtd,peak,giveback,prior_day):
                current=ids[fallback_exit]
                if current!=default:changed_fb+=1
        else:
            if event_exit!="baseline" and gate(
                    event_gate,mtd,peak,giveback,prior_day):
                current=ids[event_exit]
                if current!=default:changed_ev+=1
        chosen[d]=current
        # Past-only selection: today's return affects NEXT trading date only.
        val=float(raw[0][d,current,1])
        equity*=1+val
        peak=max(peak,equity)
        prior_day+=1
    return chosen,mtd_prior,peak_giveback,changed_ev,changed_fb

def getout(raw,chosen,mi):
    d=np.arange(N)
    return tuple(x[d,chosen,mi] if k<2 else x[d,chosen]
                 for k,x in enumerate(raw))

def score(path):
    p,c,g,r,t=path
    z=online.metrics(p,c,g,r,t)
    z["exit_on_next_minute"]=int(np.sum(r==4))
    return z

def saved_ledger(path,chosen,mtd,giveback,idx,hour,side,mask,model):
    p,c,g,r,t=path
    df=pd.DataFrame(dict(
      day_ist=base.IST_DAYS,year=np.asarray(base.DAYS.year),month_ist=MONTHS,
      entry_hour_ist=hour,entry_direction=np.where(side>0,"LONG","SHORT"),
      entry_type=np.where(mask,"FALLBACK_21H","5M_VOLUME_EVENT"),
      previously_completed_month_account_net_pct=mtd*100,
      prior_month_peak_giveback_pct=giveback*100,
      chosen_1m_exit_policy_index=chosen,
      net_account_pct=p*100,gross_btc_points=g,fee_gst_btc_points=c,
      adverse_slippage_points=2*base.SLIP,
      outcome=np.where(r==1,"TP",np.where(r==2,"PROTECTIVE_STOP",
              np.where(r==3,"TIMEOUT","NEXT_MINUTE_EARLY_CLOSE"))),
      hold_minutes=t,fee_scenario=model))
    assert len(df)==477 and df.day_ist.nunique()==477 and \
           (pd.to_datetime(df.day_ist).dt.dayofweek<5).all()
    mon=df.groupby("month_ist",sort=True).agg(
      trade_days=("day_ist","size"),
      winning_days=("net_account_pct",lambda s:int(np.sum(s>0))),
      losing_days=("net_account_pct",lambda s:int(np.sum(s<0))),
      net_compounded_pct=("net_account_pct",
          lambda s:float(100*(np.prod(1+s.to_numpy()/100)-1))),
      gross_btc_points=("gross_btc_points","sum"),
      fees_gst_btc_points=("fee_gst_btc_points","sum")
    ).reset_index()
    assert len(mon)==22 and mon.trade_days.sum()==477
    return df,mon

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,side,hour,idx,cfg=step13.create_path()
    policies,names=bar.build_exit_policies()
    ids={name:i for i,name in enumerate(names)}
    for name in EVENT_EXITS+FALLBACK_EXITS:
        if name!="baseline" and name not in ids:
            raise AssertionError("Unrecognized frozen Step7 1m exit "+name)
    raw=bar.replay_with_nextbar_exits(
        m.open.to_numpy(float),m.high.to_numpy(float),m.low.to_numpy(float),
        m.close.to_numpy(float),idx,side,cfg,policies,base.COST,base.SLIP
    )
    _=step13.check_parity(raw,ctx,fb)
    base_index=ids["profit_close_at_0.1pct_after_20m"]
    fixed=("none","baseline","none","baseline")
    original=replay_one(raw,mask,base_index,fixed,ids)
    baseline={mode:score(getout(raw,original[0],mi)) for mi,mode in enumerate(base.MODES)}
    assert baseline["scalper_offer"]["win_months_all"]==19
    assert abs(baseline["scalper_offer"]["net_total_pct"]-23.261256)<.00011
    assert abs(baseline["standard"]["net_total_pct"]+6.967115)<.00011
    print("STEP15_BASELINE_VERIFIED "+json.dumps(baseline,sort_keys=True),flush=True)
    decisions={};rows=[]
    for params in product(EVENT_GATES,EVENT_EXITS,FALLBACK_GATES,FALLBACK_EXITS):
        result=replay_one(raw,mask,base_index,params,ids)
        decisions[params]=result
        for mi,mode in enumerate(base.MODES):
            path=getout(raw,result[0],mi)
            z=score(path)
            z.update(
                event_gate=params[0],event_exit=params[1],
                fallback_gate=params[2],fallback_exit=params[3],
                cost_model=mode,
                actual_event_exit_changes=result[3],
                actual_fallback_exit_changes=result[4],
                day_exit_choices_differ_from_step13=int(np.sum(result[0]!=original[0])),
                chosen_2025_exit_changes=int(np.sum(result[0][:TRAIN]!=original[0][:TRAIN])),
                chosen_2026_exit_changes=int(np.sum(result[0][TRAIN:]!=original[0][TRAIN:])))
            rows.append(z)
    frame=pd.DataFrame(rows)
    if len(frame)!=288 or not frame.trades.eq(477).all():
        raise AssertionError("Incomplete Step15 candidate/test calendar coverage")
    frame.to_csv(OUT/"all_144_two_leg_monthly_overlays_both_fee_models.csv",index=False)
    print("STEP15_GRID "+json.dumps(dict(models=144,cost_reprices=288,
        mandatory_weekday_trades=477,train_2025_days=260,check_2026_days=217)),flush=True)
    offer=frame[frame.cost_model=="scalper_offer"]
    qualified=offer[(offer.win_months_2025>=11)&
                    (offer.return_2025_pct>=9.5)&
                    (offer.profitable_days_2025>=157)&
                    (offer.max_dd_2025<=3.05)]
    if len(qualified):
        best=qualified.sort_values(
            ["win_months_2025","return_2025_pct","profitable_days_2025","max_dd_2025"],
            ascending=[False,False,False,True]).iloc[0].to_dict()
    else:
        best=offer[(offer.event_gate=="none")&(offer.event_exit=="baseline")&
                   (offer.fallback_gate=="none")&(offer.fallback_exit=="baseline")].iloc[0].to_dict()
    key=(best["event_gate"],best["event_exit"],best["fallback_gate"],best["fallback_exit"])
    selected=decisions[key]
    reports={}
    for mi,mode in enumerate(base.MODES):
        path=getout(raw,selected[0],mi)
        daily,monthly=saved_ledger(path,selected[0],selected[1],selected[2],
                            idx,hour,side,mask,mode)
        daily.to_csv(OUT/(mode+"_selected_477_daily.csv"),index=False)
        monthly.to_csv(OUT/(mode+"_selected_22_months.csv"),index=False)
        z=score(path)
        reports[mode]=dict(
          score=z,
          winning_months=int(np.sum(monthly.net_compounded_pct>0)),
          negative_months=monthly.loc[monthly.net_compounded_pct<=0,
                 ["month_ist","net_compounded_pct"]].to_dict("records"),
          delta_vs_step13_net_pct=round(z["net_total_pct"]-baseline[mode]["net_total_pct"],6),
          delta_vs_step13_profitable_months=z["win_months_all"]-baseline[mode]["win_months_all"],
          delta_vs_step13_win_days=z["profitable_days"]-baseline[mode]["profitable_days"],
          delta_vs_step13_max_dd=round(z["max_closed_dd_pct"]-baseline[mode]["max_closed_dd_pct"],6))
        print("STEP15_SELECTED_"+mode.upper()+" "+json.dumps(reports[mode],sort_keys=True),flush=True)
        print("STEP15_MONTHLY_"+mode.upper()+"\n"+monthly.to_string(index=False),flush=True)

    a=reports["scalper_offer"]["score"]
    qualifies=(a["win_months_all"]>=20 and a["win_months_2026"]>=9 and
        a["net_total_pct"]>=23.261256 and a["max_closed_dd_pct"]<=3.008746)
    hindsight=offer.sort_values(["win_months_all","net_total_pct"],ascending=False).iloc[0].to_dict()
    historical_20=offer[offer.win_months_all>=20]
    research=dict(
       purpose="BTC monthly positive-month frequency using two independently preentry month-equity exit overlays",
       all_477_ist_weekday_trades=True,
       notional_1x_full_each_trade=True,
       model_variants=144,fee_sensitivity_results=288,
       original_step13_after_cost=baseline,
       accepted_train_2025_eleven_month_candidates=int(len(qualified)),
       selected_2025_only=best,
       selected_results=reports,
       historically_promotable_on_research_exposed_2026=bool(qualifies),
       hindsight_20_plus_months_variants=int(len(historical_20)),
       hindsight_all_period_best_NOT_selected=hindsight,
       costs="5 BTC quote price point adverse each leg; 0.05% taker per side+18% GST; hypothetical preactivated regular Scalper Offer waives eligible <=30min close fee; 1x account exposure",
       limitations=[
          "Previously researched Jan2025-Oct2026 and November2026 dates; NO independent held-out validation",
          "144 more policies and many past searches cause serious overfit risk",
          "Historical actual Scalper Offer eligibility cannot be inferred from OHLCV",
          "No real bid/ask spreads, market depth, funding, latency, tick-based fill chronology",
          "One daily trade does not guarantee monthly profitability"])
    (OUT/"summary.json").write_text(json.dumps(research,indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
       "# Step15 — two causal monthly exit protections without dropping trades",
       "",
       "Every model has exactly 477 IST Mon-Fri entries, frozen sides and original 1m stop/TP. Actual exit only changes when previous completed month's-to-date equity conditions indicate. 2025-only model selection and 2026 research-exposed validation.",
       "",
       "## Original Step13 baseline",json.dumps(baseline,indent=2),
       "",
       "## Policy selected using 2025 only",json.dumps(best,indent=2),
       "",
       "## Complete historical performance with standard fee sensitivity",json.dumps(reports,indent=2),
       "",
       "## All 22 month returns",
       pd.read_csv(OUT/"scalper_offer_selected_22_months.csv").to_markdown(index=False),
       "",
       "## Full-sample hindsight-only best, not selected",
       json.dumps(hindsight,indent=2),
       "",
       "## Caveats",
       "The year 2026 has already been examined in many past tests and cannot validate this approach independently. Actual historical Scalper Offer participation, funding, spreads and fills unknown. No live profits verified."
    ])+"\n")
    print("STEP15_COMPLETE "+json.dumps(research,sort_keys=True),flush=True)

if __name__=="__main__":
    run()
