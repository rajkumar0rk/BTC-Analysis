#!/usr/bin/env python3
"""BTC Step21: causal month-to-date stop adjustment, every weekday full risk.

Tests 75 monthly-state SL caps separately on frozen Step20 B risk-balanced
and A higher-profit baselines, with identical Step11 entry, Step15
month-aware early exit, and one order on each of all 477 IST weekdays.
Selection on 2025 only. 2026 previously researched, not blind OOS.
"""
from pathlib import Path
from itertools import product
import json
import numpy as np
import pandas as pd

import research_btc_every_weekday_reset_step1 as base
import research_btc_daily_monthly_exit_step13 as step13
import research_btc_daily_monthly_two_regime_step15 as step15
import research_btc_daily_exit_invalidation_step7 as early
import audit_btc_daily_risk_crosscheck_step20 as step20

OUT=Path("analysis/btc_daily_mtd_stop_step21")
N=len(base.DAYS)
TRAIN=base.NTRAIN
MONTHS=np.asarray(base.MONTH_LABELS)
CAPS=(.12,.18,.22,.28,.35)
SCOPES=("fallback","event","both")
TRIGGERS=("mtd_nonpositive","mtd_below_minus025",
          "mtd_below_minus050","giveback_ge050","prior_two_losses")
FAMILIES={
    "B_risk_balanced":dict(
        source="B_with60_plus_counter5",strategy="B",
        risk_parts=("with60","counter5"),net=25.423847,
        monthly_wins=21,drawdown=2.617670),
    "A_high_profit":dict(
        source="A_tight60_only",strategy="A",
        risk_parts=("tight60",),net=25.973352,
        monthly_wins=21,drawdown=2.715507)
}
assert N==477 and TRAIN==260 and len(TRIGGERS)*len(SCOPES)*len(CAPS)*len(FAMILIES)==150

def triggered(kind,mtd,giveback,prior_losses):
    if kind=="mtd_nonpositive":return mtd<=0
    if kind=="mtd_below_minus025":return mtd<=-.0025
    if kind=="mtd_below_minus050":return mtd<=-.005
    if kind=="giveback_ge050":return giveback>=.005
    if kind=="prior_two_losses":return prior_losses>=2
    raise KeyError(kind)

def daily_rule_exit(is_fallback,mtd,peak,giveback,prior_days,params,policy_ids):
    egate,eexit,fgate,fexit=params
    current=(policy_ids["profit_close_at_0.1pct_after_20m"]
             if is_fallback and mtd<=.0025 else 0)
    if is_fallback:
        if fexit!="baseline" and step15.gate(
                fgate,mtd,peak,giveback,prior_days):
            current=policy_ids[fexit]
    else:
        if eexit!="baseline" and step15.gate(
                egate,mtd,peak,giveback,prior_days):
            current=policy_ids[eexit]
    return current

def build_raw(m,idx,side,cfg,policies):
    return early.replay_with_nextbar_exits(
       m.open.to_numpy(float),m.high.to_numpy(float),
       m.low.to_numpy(float),m.close.to_numpy(float),
       idx,side,cfg,policies,base.COST,base.SLIP)

def run_sequential(raw_base,raw_cap,mask,settings,strategy_params,policy_ids):
    # Scoring / intra-month conditions use the hypothetical offer, but
    # the EXACT SAME chosen path is then repriced under normal fees.
    which_cap=np.zeros(N,dtype=bool)
    policy=np.zeros(N,dtype=np.int16)
    prev_mtd=np.zeros(N)
    prev_giveback=np.zeros(N)
    prev_streak=np.zeros(N,dtype=np.int16)
    trigger_type,scope,cap=settings
    month=None
    equity=1.
    peak=1.
    losses=0
    prior_days=0
    for d in range(N):
        if MONTHS[d]!=month:
            month=MONTHS[d]
            equity=1.
            peak=1.
            losses=0
            prior_days=0
        mtd=equity-1.
        gb=peak-equity
        prev_mtd[d]=mtd
        prev_giveback[d]=gb
        prev_streak[d]=losses
        valid_scope=scope=="both" or (
          scope=="fallback" and mask[d]) or (
          scope=="event" and not mask[d])
        enabled=(trigger_type!="none" and valid_scope and
                 triggered(trigger_type,mtd,gb,losses))
        which_cap[d]=enabled
        index=daily_rule_exit(
          bool(mask[d]),mtd,peak,gb,prior_days,
          strategy_params,policy_ids)
        policy[d]=index
        # This day's realized return updates ONLY NEXT trading day.
        chosen_raw=raw_cap if enabled else raw_base
        today=float(chosen_raw[0][d,index,1])
        if not np.isfinite(today):
            raise AssertionError("Nonfinite daily account return")
        equity*=1.+today
        peak=max(peak,equity)
        losses=losses+1 if today<0. else 0
        prior_days+=1
    assert len(policy)==477 and len(which_cap)==477
    return which_cap,policy,prev_mtd,prev_giveback,prev_streak

def realized_path(raw_base,raw_cap,choice,exit_policy,mode_index):
    d=np.arange(N)
    return tuple(
        np.where(choice,
          raw_cap[k][d,exit_policy,mode_index] if k<2 else raw_cap[k][d,exit_policy],
          raw_base[k][d,exit_policy,mode_index] if k<2 else raw_base[k][d,exit_policy]
        ) for k in range(5)
    )

def full_ledger(path,chosen_cap,exit_policy,prev_mtd,prev_gb,streak,
                frozen_cfg,capped_cfg,mask,side,hour,model,mode):
    p,fees,gross,reason,hold=path
    actual_stop=np.where(chosen_cap,capped_cfg[:,1],frozen_cfg[:,1])
    original_stop=frozen_cfg[:,1]
    ledger=pd.DataFrame(dict(
      date_ist=base.IST_DAYS,year=np.asarray(base.DAYS.year),month_ist=MONTHS,
      hour_ist=hour,side=np.where(side==1,"LONG","SHORT"),
      entry_type=np.where(mask,"MANDATORY_21H_FALLBACK","VOLUME_SIGNAL"),
      prior_month_compounded_net_pct=prev_mtd*100,
      previous_month_peak_giveback_pct=prev_gb*100,
      prior_consecutive_loss_days=streak,
      stop_cap_rule_enabled=chosen_cap,
      base_stop_pct=original_stop,
      chosen_initial_stop_pct=actual_stop,
      stop_narrowed=actual_stop<original_stop-1e-12,
      previous_bar_exit_index=exit_policy,
      net_account_pct=p*100,gross_btc_points=gross,fee_gst_btc_points=fees,
      adverse_slippage_btc_points=base.SLIP*2,
      exit_reason=np.where(reason==1,"TAKE_PROFIT",
                    np.where(reason==2,"STOP",
                    np.where(reason==3,"TIMEOUT","NEXT_MINUTE_EARLY_CLOSE"))),
      minutes_held=hold,model=model,cost_model=mode
    ))
    if len(ledger)!=477 or ledger.date_ist.nunique()!=477 or (
          pd.to_datetime(ledger.date_ist).dt.dayofweek>=5).any():
        raise AssertionError("Missing weekday or traded on weekend")
    monthly=ledger.groupby("month_ist",sort=True).agg(
      trades=("date_ist","size"),
      winning_days=("net_account_pct",lambda x:int((x>0).sum())),
      losing_days=("net_account_pct",lambda x:int((x<0).sum())),
      net_compounded_pct=("net_account_pct",
          lambda x:float(100*(np.prod(1+x.to_numpy()/100)-1))),
      gross_btc_points=("gross_btc_points","sum"),
      fees_gst_btc_points=("fee_gst_btc_points","sum"),
      capped_days=("stop_narrowed","sum")
    ).reset_index()
    if len(monthly)!=22 or monthly.trades.sum()!=477:
        raise AssertionError("Missing monthly trade ledger")
    return ledger,monthly

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,side,hour,index,defaultcfg=step13.create_path()
    policies,names=early.build_exit_policies()
    ids={name:i for i,name in enumerate(names)}
    step13.check_parity(build_raw(m,index,side,defaultcfg,policies),ctx,fb)
    features=step20.prev.preentry_features(m,index,side)
    baselines={}
    raw_by_family={}
    cfg_by_family={}
    params_by_family={}
    for name,source in FAMILIES.items():
        cfg,applied,narrowed=step20.build_capped(
          defaultcfg,features,side,mask,source["risk_parts"])
        cfg_by_family[name]=cfg
        base_raw=build_raw(m,index,side,cfg,policies)
        raw_by_family[name]=base_raw
        params=step20.PARAMS[source["strategy"]]
        params_by_family[name]=params
        baseline_decision=run_sequential(
          base_raw,base_raw,mask,("none","both",.0),params,ids)
        base_path=realized_path(base_raw,base_raw,
                    baseline_decision[0],baseline_decision[1],1)
        z=step15.score(base_path)
        if z["win_months_all"]!=21 or abs(z["net_total_pct"]-source["net"])>.00011 or abs(z["max_closed_dd_pct"]-source["drawdown"])>.00011:
            raise AssertionError("Original Step20 family baseline changed "+name+" "+str(z))
        baselines[name]=z
    print("STEP21_BASELINES "+json.dumps(baselines,sort_keys=True),flush=True)
    rows=[]
    choices={}
    alt_cache={}
    for family,source in FAMILIES.items():
        raw=raw_by_family[family]
        cfg=cfg_by_family[family]
        params=params_by_family[family]
        baseline_choice=run_sequential(
          raw,raw,mask,("none","both",0.),params,ids)
        for mode_index,mode in enumerate(base.MODES):
            path=realized_path(raw,raw,baseline_choice[0],baseline_choice[1],mode_index)
            z=step15.score(path)
            z.update(family=family,trigger="none",scope="none",
                cap_pct=None,model=family+"__unchanged",
                cost_model=mode,cap_activated_days=0,actually_shrunk_stops=0)
            rows.append(z)
        choices[(family,"none","none",0.)]=baseline_choice
        for cap in CAPS:
            capped=cfg.copy()
            capped[:,1]=np.minimum(capped[:,1],cap)
            if np.any(capped[:,1]>cfg[:,1]+1e-12):
                raise AssertionError("Widening original stop")
            alt=build_raw(m,index,side,capped,policies)
            alt_cache[(family,cap)]=alt
            for kind,scope in product(TRIGGERS,SCOPES):
                choice=run_sequential(
                  raw,alt,mask,(kind,scope,cap),params,ids)
                choices[(family,kind,scope,cap)]=choice
                actually_shrunk=int(np.sum(choice[0]&(
                    capped[:,1]<cfg[:,1]-1e-12)))
                for mi,mode in enumerate(base.MODES):
                    path=realized_path(raw,alt,choice[0],choice[1],mi)
                    z=step15.score(path)
                    z.update(family=family,trigger=kind,scope=scope,
                        cap_pct=cap,model=family+"__"+kind+"__"+scope+"__"+str(cap),
                        cost_model=mode,
                        cap_activated_days=int(choice[0].sum()),
                        actually_shrunk_stops=actually_shrunk)
                    rows.append(z)
            print("STEP21_CAP_COMPLETED "+json.dumps(dict(
              family=family,cap=cap,
              scenarios_completed=int(sum(1 for k in choices if k[0]==family and k[1]!="none"))),flush=True)
    df=pd.DataFrame(rows)
    if len(df)!=304 or not df.trades.eq(477).all():
        raise AssertionError("Invalid preregistered scenario or weekday count")
    df.to_csv(OUT/"all_150_mtd_stop_policies_both_costs.csv",index=False)
    print("STEP21_GRID "+json.dumps(dict(
      two_baselines=2,alternative_policies=150,cost_variants=304,
      trades_each=477,eligible_months=22)),flush=True)
    offer=df[df.cost_model=="scalper_offer"]
    selected={}
    for fam in FAMILIES:
        original=baselines[fam]
        available=offer[(offer.family==fam)&(offer.trigger!="none")]
        eligible=available[
          (available.win_months_2025==12)&
          (available.return_2025_pct>=original["return_2025_pct"]-1e-6)&
          (available.profitable_days_2025>=original["profitable_days_2025"])&
          (available.max_dd_2025<=original["max_dd_2025"]+1.e-4)]
        if len(eligible):
            chosen=eligible.sort_values(
                ["win_months_2025","return_2025_pct",
                 "profitable_days_2025","max_dd_2025"],
                ascending=[False,False,False,True]).iloc[0].to_dict()
            rule=(chosen["trigger"],chosen["scope"],float(chosen["cap_pct"]))
        else:
            rule=("none","none",0.)
        dec=choices[(fam,*rule)]
        raw=raw_by_family[fam]
        cfg=cfg_by_family[fam]
        if rule[0]=="none":
            alt=raw
            chosen_cfg=cfg
        else:
            alt=alt_cache[(fam,rule[2])]
            chosen_cfg=cfg.copy()
            chosen_cfg[:,1]=np.minimum(chosen_cfg[:,1],rule[2])
        fee_reports={}
        for mi,mode in enumerate(base.MODES):
            path=realized_path(raw,alt,dec[0],dec[1],mi)
            ledger,months=full_ledger(
                path,*dec[:2],dec[2],dec[3],dec[4],
                cfg,chosen_cfg,mask,side,hour,
                fam+"__"+str(rule),mode)
            ledger.to_csv(OUT/(fam+"_"+mode+"_selected_477_trades.csv"),index=False)
            months.to_csv(OUT/(fam+"_"+mode+"_selected_22_months.csv"),index=False)
            z=step15.score(path)
            fee_reports[mode]=dict(
                after_fee=z,
                positive_months=int((months.net_compounded_pct>0).sum()),
                losing_months=months.loc[months.net_compounded_pct<=0,
                         ["month_ist","net_compounded_pct"]].to_dict("records"),
                change_from_original_net_pct=round(z["net_total_pct"]-
                    baselines[fam]["net_total_pct"],6) if mode=="scalper_offer" else None,
                cap_activated_days=int(np.sum(dec[0])),
                truly_narrowed_days=int(ledger.stop_narrowed.sum()))
        selected[fam]=dict(
            2025_eligible_models=int(len(eligible)) if False else len(eligible),
            frozen_2025_rule=dict(trigger=rule[0],scope=rule[1],
                                  max_stop_pct=rule[2] if rule[0]!="none" else None),
            same_policy_repriced_under_two_fee_models=fee_reports
        )
        print("STEP21_SELECTED_"+fam.upper()+" "+
            json.dumps(selected[fam],sort_keys=True),flush=True)
    # All 2025-2026 historical cherry-pick winners explicitly separate
    full22=offer[offer.win_months_all==22].sort_values(
      ["net_total_pct","max_closed_dd_pct"],ascending=[False,True])
    full22.to_csv(OUT/"hindsight_22_out_of_22_NOT_SELECTED.csv",index=False)
    report=dict(
        task="Monthly losing-period initial SL protections, always one 1x BTCUSD trade per IST weekday",
        full_weekdays_each=477,span_months=22,
        base_historical_models=baselines,
        candidate_count=150,cost_variants=304,
        strict_2025_selection=selected,
        full_history_22_22_hindsight_count=int(len(full22)),
        full_history_best_22_22_NOT_SELECTED=full22.iloc[0].to_dict() if len(full22) else None,
        eligible_live_deployment=False,
        costs="0.05% taker each side GST18%, 5 BTCUSD quote-point adverse slip per leg; alternative historical hypothetical prior-activated <=30m Scalper closing fee waiver",
        important_limitations=[
            "The 2025/2026 dataset and predecessor risk-based family selections were heavily optimized before Step21",
            "Any 22/22 result would be historical hindsight, not independent confirmation of monthly profitability",
            "Actual historical offer activation, real spread, order book, funding, latency, tick-level fill paths and liquidation not modeled",
            "One full-size weekday trade is not guaranteed to produce a positive month"])
    (OUT/"summary.json").write_text(json.dumps(report,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
      "# Step21 BTC monthly-consistency recovery with pre-trade month-equity risk",
      "",
      "One 1x BTCUSD full-notional trade each of 477 full IST weekdays. Exact original entry price/time/side and Step15 A/B early exit policy. Only initial stop can shrink if earlier finished trades this month indicate cumulative losses/peak giveback. Standard-fee outcomes replay SAME decisions as hypothetical Scalper fee regime.",
      "",
      "## Frozen original risk model benchmarks",json.dumps(baselines,indent=2),
      "",
      "## 2025-selected models applied unchanged to researched 2026",
      json.dumps(selected,indent=2),
      "",
      "## Hindsight-only 22/22 models counted (NOT recommended)",
      str(len(full22)),
      "",
      "## Retained B model 22-month returns",
      pd.read_csv(OUT/"B_risk_balanced_scalper_offer_selected_22_months.csv").to_markdown(index=False),
      "",
      "## Warnings",
      "Historical offer cannot be verified and standard taker costs made prior family models net negative; dates 2025-2026 already deeply researched and November 2026 only partial/research-exposed. Real independent forward testing required."
    ])+"\n")
    print("STEP21_COMPLETE "+json.dumps(dict(
       models=150,full22_retrospective=len(full22),
       selected={k:v["same_policy_repriced_under_two_fee_models"]["scalper_offer"]["after_fee"] for k,v in selected.items()}),
       sort_keys=True),flush=True)

if __name__=="__main__":
    main()
