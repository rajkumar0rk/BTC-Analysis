#!/usr/bin/env python3
"""Step13: month-to-date risk-conditioned NEXT-minute early exits on frozen Step11.

Exactly 477 weekday trades, every candidate, no sizing or entry differences.
The 1-minute standard/Scalper OHLC exit engine is replayed once with the
exact Step11 chosen LONG/SHORT and original stop/lock/trailing. Trade exits
may switch after a losing month-to-date using previous daily P&L ONLY.
"""
from itertools import product
from pathlib import Path
import json

import numpy as np
import pandas as pd

import research_btc_every_weekday_reset_step1 as base
import research_btc_daily_causal_regime_step5 as regime
import research_btc_daily_online_structure_step11 as study
import research_btc_daily_exit_invalidation_step7 as closebar
import research_btc_daily_online_direction_step6 as online

OUT=Path("analysis/btc_daily_monthly_exit_step13")
N=len(base.DAYS)
TRAIN=base.NTRAIN
MONTHS=np.asarray(base.MONTH_LABELS)
TRIGGERS=(-.005,-.0025,0.,.0025)
SCOPES=("event","fallback","both")
POLICY_NAMES=(
    "profit_close_at_0.1pct_after_10m",
    "profit_close_at_0.15pct_after_10m",
    "profit_close_at_0.1pct_after_20m",
    "profit_close_at_0.15pct_after_20m",
    "profit_close_at_0.2pct_after_20m",
    "adverse_cut_0.08pct_after_5m",
    "adverse_cut_0.12pct_after_5m",
    "adverse_cut_0.08pct_after_10m",
    "stall_if_mfe_below_0.1pct_at_10m",
    "hard_timeout_20m",
    "hard_timeout_25m",
)
assert len(POLICY_NAMES)==11 and len(TRIGGERS)*len(SCOPES)*len(POLICY_NAMES)==132

def create_path():
    m=base.load()
    ctx=study.shadow(m)
    mask=ctx["mask"]
    fb,prior,_=study.choose_online(
        ctx["returns"]["scalper_offer"][0],mask,
        60,"all_6_arms","net","none")
    f=ctx["f"]
    be=ctx["base_event"]
    eside=np.where(be==0,f["event_signs"],-f["event_signs"])
    fbindex=ctx["fb_arms"][np.arange(N),fb]
    fside=f["fall_signs"][np.arange(N),fbindex]
    side=np.where(mask,fside,eside).astype(np.int8)
    hours=ctx["entry_hour"].astype(int)
    idx=base.prepare(m)[0][np.arange(N),hours]
    cfg,cfgid=regime.build_cfg()
    pids=np.empty(N,dtype=int)
    for d in range(N):
        pids[d]=(cfgid["trail075"] if f["features21"][d,21]["volume5"]>=1.25
                 else cfgid["trail050"]) if mask[d] else cfgid["lock050"]
    exitcfg=cfg[pids]
    if not (np.abs(side)==1).all() or int(np.sum(mask))!=217:
        raise AssertionError("Step11 frozen entry types/side changed")
    return m,ctx,mask,fb,side,hours,idx,exitcfg

def check_parity(raw,ctx,basefb):
    target={}
    for mi,mode in enumerate(base.MODES):
        src=ctx["returns"][mode]
        ref=tuple(x[np.arange(N),basefb] for x in src)
        # Every single Step11 day must match 1m prior-minute policy engine
        for j in range(5):
            compare=raw[j][:,0,mi] if j<2 else raw[j][:,0]
            if not np.allclose(compare,ref[j],rtol=0,atol=1e-13):
                raise AssertionError(f"Baseline drift mode={mode}, component={j}, maxabs={np.max(abs(compare-ref[j]))}")
        target[mode]=online.metrics(*ref)
    a=target["scalper_offer"];b=target["standard"]
    if a["profitable_days"]!=279 or abs(a["net_total_pct"]-22.141056)>.00011:
        raise AssertionError("Step11 model not reproduced")
    if abs(b["net_total_pct"]+7.812987)>.00011:
        raise AssertionError("Fee baseline not reproduced")
    return target

def monthly_metrics(returns):
    return np.array([100*(np.prod(1+returns[MONTHS==month])-1)
        for month in list(dict.fromkeys(MONTHS.tolist()))],dtype=float)

def simulate_policy(raw,mask,month_trigger,scope,rule_index):
    # Only 2025 and past days drive state for first 2026, then only prior
    # 2026 days are appended. No same-day future information.
    if scope not in SCOPES and scope!="none":raise KeyError(scope)
    selected=np.zeros(N,dtype=np.int8)
    mtd_before=np.zeros(N,dtype=np.float64)
    month=None
    equity=1.
    for d in range(N):
        if MONTHS[d]!=month:
            month=MONTHS[d]
            equity=1.
        mtd=equity-1.
        mtd_before[d]=mtd
        if mtd<=month_trigger and (scope=="both" or
           (scope=="fallback" and mask[d]) or
           (scope=="event" and not mask[d])):
            selected[d]=rule_index
        r=float(raw[0][d,selected[d],1]) # hypothetical Scalper Offer
        equity*=1.+r
    return selected,mtd_before

def evaluate(raw,choices,mode_idx):
    d=np.arange(N)
    return tuple(x[d,choices,mode_idx] if j<2 else x[d,choices]
                 for j,x in enumerate(raw))

def metrics(path):
    p,fees,gross,why,t=path
    z=online.metrics(p,fees,gross,why,t)
    z["early_rule_exits"]=int(np.sum(why==4))
    return z

def ledger(path,choices,mtd,mask,side,hour,mode,policy_label):
    p,fee,gross,why,hold=path
    d=pd.DataFrame(dict(
        date_ist=base.IST_DAYS,month_ist=MONTHS,
        year=np.asarray(base.DAYS.year),
        hour_ist=hour,
        direction=np.where(side>0,"LONG","SHORT"),
        entry_category=np.where(mask,"MANDATORY_FALLBACK","VOLUME_SIGNAL"),
        prior_MTD_compounded_pct=mtd*100,
        early_rule_enabled=choices!=0,
        early_rule_index=choices.astype(int),
        month_recovery_policy=policy_label,
        net_account_pct=p*100,
        gross_btc_points=gross,fee_gst_btc_points=fee,
        adverse_slippage_btc_points=2*base.SLIP,
        exit_reason=np.where(why==1,"TARGET",np.where(why==2,"STOP",
                      np.where(why==3,"TIMEOUT","PREVIOUS_BAR_EXIT"))),
        hold_minutes=hold.astype(int),
        cost_model=mode
    ))
    if len(d)!=477 or d.date_ist.nunique()!=477 or (pd.to_datetime(d.date_ist).dt.dayofweek>=5).any():
        raise AssertionError("Lost weekday trade")
    mon=d.groupby("month_ist",sort=True).agg(
        trade_days=("date_ist","size"),
        winning_days=("net_account_pct",lambda x:int(np.sum(x>0))),
        losing_days=("net_account_pct",lambda x:int(np.sum(x<0))),
        monthly_compounded_pct=("net_account_pct",lambda x:float(100*(np.prod(1+x.to_numpy()/100)-1))),
        gross_points=("gross_btc_points","sum"),
        fee_gst_points=("fee_gst_btc_points","sum"),
        special_exits=("early_rule_enabled","sum")
    ).reset_index()
    if len(mon)!=22 or mon.trade_days.sum()!=477:
        raise AssertionError("Month-by-month 477-day coverage failed")
    return d,mon

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,side,hours,idx,cfg=create_path()
    policy,policy_names=closebar.build_exit_policies()
    find={name:i for i,name in enumerate(policy_names)}
    for name in POLICY_NAMES:
        if name not in find:raise AssertionError(f"Prior tested 1m exit absent: {name}")
    raw=closebar.replay_with_nextbar_exits(
        m.open.to_numpy(float),m.high.to_numpy(float),
        m.low.to_numpy(float),m.close.to_numpy(float),
        idx,side,cfg,policy,base.COST,base.SLIP
    )
    baseline=check_parity(raw,ctx,fb)
    print("STEP13_BASELINE "+json.dumps(baseline,sort_keys=True),flush=True)

    scenarios=[("baseline",0.,"none",0)]
    for threshold,scope,name in product(TRIGGERS,SCOPES,POLICY_NAMES):
        scenarios.append(("conditional",threshold,scope,find[name]))
    assert len(scenarios)==133
    models=[];candidate={}
    for kind,threshold,scope,ridx in scenarios:
        choices,mtd=simulate_policy(raw,mask,threshold,scope,ridx)
        key=(kind,threshold,scope,ridx)
        candidate[key]=(choices,mtd)
        for i,mode in enumerate(base.MODES):
            path=evaluate(raw,choices,i)
            z=metrics(path)
            z.update(
                kind=kind,threshold_MTD_pct=threshold*100.,
                applicable_scope=scope,
                early_exit_rule=policy_names[ridx],
                rule_index=ridx,cost_model=mode,
                early_rule_activated_trades=int(np.sum(choices!=0)),
                changed_event_days=int(np.sum((choices!=0)&(~mask))),
                changed_fallback_days=int(np.sum((choices!=0)&mask))
            )
            models.append(z)
    df=pd.DataFrame(models)
    if len(df)!=266 or not df.trades.eq(477).all():
        raise AssertionError("Exit variation skipped weekday")
    df.to_csv(OUT/"all_132_monthly_early_exit_variants_two_fees.csv",index=False)
    print("STEP13_GRID "+json.dumps(dict(models=133,two_fee_scenarios=266,
        all_trades=477,year2025_days=260,year2026_days=217)),flush=True)
    offer=df[df.cost_model=="scalper_offer"].copy()
    qualifying=offer[
       (offer.win_months_2025>=10)&
       (offer.return_2025_pct>=8.5)&
       (offer.profitable_days_2025>=147)&
       (offer.max_dd_2025<=3.05)]
    if len(qualifying):
        selected=qualifying.sort_values(
            ["win_months_2025","return_2025_pct","profitable_days_2025","max_dd_2025"],
            ascending=[False,False,False,True]).iloc[0].to_dict()
    else:
        selected=offer[offer.kind=="baseline"].iloc[0].to_dict()
    key=(selected["kind"],round(float(selected["threshold_MTD_pct"])/100,9),
         selected["applicable_scope"],int(selected["rule_index"]))
    chosen,mtd=candidate[key]
    selected_details={}
    for i,mode in enumerate(base.MODES):
        path=evaluate(raw,chosen,i)
        daily,monthly=ledger(path,chosen,mtd,mask,side,hours,mode,
                             f"{key[0]}__{key[1]}__{key[2]}__{key[3]}")
        daily.to_csv(OUT/(mode+"_selected_477_daily.csv"),index=False)
        monthly.to_csv(OUT/(mode+"_selected_22_months.csv"),index=False)
        metrics_result=metrics(path)
        selected_details[mode]=dict(
            summary=metrics_result,
            winning_months=int((monthly.monthly_compounded_pct>0).sum()),
            negative_months=monthly.loc[monthly.monthly_compounded_pct<=0,
                ["month_ist","monthly_compounded_pct"]].to_dict("records"),
            change_vs_step11_net_pct=round(float(metrics_result["net_total_pct"]-baseline[mode]["net_total_pct"]),6),
            change_vs_step11_months=int(metrics_result["win_months_all"]-baseline[mode]["win_months_all"]),
            change_vs_step11_positive_days=int(metrics_result["profitable_days"]-baseline[mode]["profitable_days"]),
            change_vs_step11_dd_pct=round(float(metrics_result["max_closed_dd_pct"]-baseline[mode]["max_closed_dd_pct"]),6))
        print("STEP13_SELECTED_"+mode.upper()+" "+json.dumps(selected_details[mode],sort_keys=True),flush=True)
        print("STEP13_MONTHLY_"+mode.upper()+"\n"+monthly.to_string(index=False),flush=True)

    result=selected_details["scalper_offer"]["summary"]
    eligible_for_upgrade=(
        result["win_months_all"]>=18 and
        result["win_months_2026"]>=8 and
        result["net_total_pct"]>=22.141056 and
        result["max_closed_dd_pct"]<=3.008746
    )
    hindsight=offer.sort_values(["win_months_all","net_total_pct"],ascending=False).iloc[0].to_dict()
    pareto=int(((offer.win_months_all>=18)&
           (offer.net_total_pct>=22.141056)&
           (offer.max_closed_dd_pct<=3.008746)).sum())
    report=dict(
        task="Causal month-to-date exit protection with unchanged Step11 weekday positions",
        all_full_ist_weekdays_traded=True,
        total_weekday_trades_per_model=477,
        count_variants=133,two_fee_results=len(df),
        original_step11=baseline,
        precommitted_2025_train_qualifiers=int(len(qualifying)),
        frozen_policy_selected_using_2025_only=selected,
        chosen_results=selected_details,
        qualifies_for_promotion_even_in_research_exposed_2026=bool(eligible_for_upgrade),
        full_history_most_profitable_months_hindsight_NOT_SELECTED=hindsight,
        hindsight_variants_with_monthly_profit_dd_all_improved=pareto,
        economics="1x 100% daily notional, 0.05% taker per leg+18% GST; hypothetical preactivated Scalper Offer zero <=30m exit fee; 5 BTC quote price point adverse slippage per leg",
        limitations=[
          "2025/2026 already researched heavily; Jan-Oct2026 not independent out-of-sample",
          "133 candidates on top of prior iterations introduce selection bias",
          "No historical authentication of Scalper Offer opt-in, spreads, funding, market depth or execution latency",
          "No advance guarantee of winning calendar month with 1 nonzero trade every weekday"
        ])
    (OUT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
        "# Step13 BTC daily mandatory monthly-aware 1m early exit research",
        "",
        "Exactly 477 full Mon–Fri IST entries, 1x notional and frozen Step11 event/fallback directions. Only optional exit after a previously CLOSED 1-minute candle; all stop/target/trailing still active.",
        "",
        "## Verified per-day baseline parity with Step11",
        json.dumps(baseline,indent=2),
        "",
        "## 2025-selected candidate and Jan-Oct2026 historical check",
        json.dumps(selected,indent=2),
        "",
        "## After-cost results, including standard taker sensitivity",
        json.dumps(selected_details,indent=2),
        "",
        "## Full 22-month Scalper Offer account return",
        pd.read_csv(OUT/"scalper_offer_selected_22_months.csv").to_markdown(index=False),
        "",
        "## Hindsight-only best from ALL 22 months, NOT selected",
        json.dumps(hindsight,indent=2),
        "",
        "## Caveats",
        "Causal month-to-date means no future trade enters its earlier decision, but 2026 has repeatedly been researched already. Historical waiver status and bid-ask fills are not verified. No actual forward paper validation."
    ])+"\n")
    print("STEP13_COMPLETE "+json.dumps(report,sort_keys=True),flush=True)

if __name__=="__main__":
    run()
