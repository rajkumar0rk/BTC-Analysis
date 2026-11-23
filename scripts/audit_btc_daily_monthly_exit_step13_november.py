#!/usr/bin/env python3
"""Frozen November audit of 2025-selected BTC month-positive Step13.

Exactly one BTC 1m-OPEN position Nov2-Nov20 2026, all 15 IST weekdays.
Online Step11 entry sides learnt strictly from completed PRIOR shadow days.
Step13 early-exit MTD is updated only after previous real model trades.
Never select thresholds/parameters on this November outcome.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

import research_btc_every_weekday_reset_step1 as base
import research_btc_daily_causal_regime_step5 as regime
import research_btc_every_weekday_exit_protection_step3 as protection
import research_btc_daily_exit_invalidation_step7 as bar_exit
import research_btc_daily_online_structure_step11 as study
import research_btc_daily_monthly_exit_step13 as monthtest
import research_btc_daily_structure_step10 as structural
import audit_btc_daily_fallback_regime_november_2026 as nov
import audit_btc_daily_online_structure_step11_november as novstep11

OUT=Path("analysis/btc_daily_monthly_exit_step13/november_audit")
NDAYS=len(nov.NDAYS)
assert NDAYS==15

def discover_entry_sides(m,idx,base_side,fall,volume_ratio):
    """Sequential, past-day-only Step11 event and structural fallback learning."""
    historical=study.shadow(base.load())
    oldmask=historical["mask"]
    oldf=historical["f"]
    offer_event=np.asarray(oldf["event"][1][0][~oldmask,:])
    event_context=np.asarray(oldf["eventimpulse"][~oldmask],dtype=bool)
    event_hist=[list(r) for r in offer_event]
    event_ctx=list(event_context)
    fallback_hist=[list(r) for r in historical["returns"]["scalper_offer"][0][oldmask]]
    if len(event_hist)!=260 or len(fallback_hist)!=217:
        raise AssertionError("Previous completed trading data unavailable")
    cfg,ci=regime.build_cfg()
    op=m.open.to_numpy(float)
    hi=m.high.to_numpy(float)
    lo=m.low.to_numpy(float)
    close=m.close.to_numpy(float)
    sim={}
    for side in (1,-1):
        sim[side]=protection.run_exit_grid(
           op,hi,lo,idx,np.zeros(NDAYS,dtype=np.int8),
           np.full(NDAYS,side,dtype=np.int8),cfg,base.COST,base.SLIP)
    def shadow_return(d,side,recipe):
        return float(sim[int(side)][0][d,ci[recipe],1])
    chosen_side=np.asarray(base_side,dtype=np.int8).copy()
    chosen_arm=np.zeros(NDAYS,dtype=np.int8)
    event_switch=np.zeros(NDAYS,dtype=bool)
    fall_prior_count=np.zeros(NDAYS,dtype=np.int16)
    for d,day in enumerate(nov.NDAYS):
        if not fall[d]:
            j=int(idx[d])
            r5=float(close[j-1]/op[j-5]-1.)
            impulse=abs(r5)>=.0015
            pre=np.asarray(event_hist[-30:],dtype=float)
            ctx=np.asarray(event_ctx[-30:],dtype=bool)
            similar=pre[ctx==impulse]
            if len(similar)>=12 and similar[:,1].mean()>similar[:,0].mean()+.0003:
                chosen_side[d]=-base_side[d]
                event_switch[d]=True
            # Update subsequent learner's counterfactual history ONLY AFTER
            # today's side is selected; these are fixed E-exit outcomes.
            event_hist.append([
               shadow_return(d,base_side[d],"lock050"),
               shadow_return(d,-base_side[d],"lock050")
            ])
            event_ctx.append(bool(impulse))
        else:
            pre=fallback_hist[-60:]
            fall_prior_count[d]=len(pre)
            if len(pre)>=15:
                scores=np.mean(np.asarray(pre,dtype=float),axis=0)
                arm=int(np.argmax(scores))
                if arm>0 and scores[arm]>scores[0]:
                    chosen_arm[d]=arm
            feature=novstep11.nov_structure(m,idx[d],day)
            choices=np.full(6,int(base_side[d]),dtype=np.int8)
            for a,(_,kind,level) in enumerate(study.ARMS):
                if not a:continue
                preferred=structural.desired_for(kind,level,feature)
                if preferred!=0:
                    choices[a]=preferred
            chosen_side[d]=choices[chosen_arm[d]]
            recip="trail075" if volume_ratio[d]>=1.25 else "trail050"
            fallback_hist.append([
                shadow_return(d,choices[a],recip) for a in range(6)
            ])
    return chosen_side,chosen_arm,event_switch,fall_prior_count


def report_metrics(p):
    eq=np.cumprod(1+p)
    peak=np.maximum.accumulate(np.r_[1.,eq])[1:]
    return dict(trades=len(p),profitable_days=int(np.sum(p>0)),
        losing_days=int(np.sum(p<0)),
        profitable_day_percentage=round(float(np.mean(p>0)*100),3),
        compounded_account_net_pct=round(float((eq[-1]-1)*100),6),
        max_closed_dd_pct=round(float(np.max(1-eq/peak)*100),6),
        worst_day_pct=round(float(np.min(p)*100),6))


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=nov.load_with_nov()
    idx,hh,base_sides,fall=nov.determine_entries(m,"follow5")
    if len(idx)!=15 or int(fall.sum())!=6 or int((~fall).sum())!=9:
        raise AssertionError("Nov weekday event/fallback counts differ")
    volume=m.volume.to_numpy(float)
    vol5=np.empty(NDAYS)
    for d,i in enumerate(idx):
        previous=volume[i-105:i-5].reshape(20,5).sum(axis=1)
        avg=float(np.mean(previous))
        vol5[d]=float(volume[i-5:i].sum()/avg) if avg>0 else 1.
    side,arm,event_switch,prior=discover_entry_sides(m,idx,base_sides,fall,vol5)
    # The old November Step11 audit found no deviations in actual side.
    if not np.array_equal(side,base_sides):
        raise AssertionError("Nov Step11 online learning side differs from already verified parity")
    cfg,ids=regime.build_cfg()
    day_cfg=np.asarray([
      cfg[ids["lock050"] if not fall[d] else (
          ids["trail075"] if vol5[d]>=1.25 else ids["trail050"])]
      for d in range(NDAYS)
    ],dtype=float)
    policies,policy_names=bar_exit.build_exit_policies()
    rule_index=policy_names.index("profit_close_at_0.1pct_after_20m")
    replay=bar_exit.replay_with_nextbar_exits(
        m.open.to_numpy(float),m.high.to_numpy(float),m.low.to_numpy(float),
        m.close.to_numpy(float),idx,side,day_cfg,policies,base.COST,base.SLIP)
    # Causal MTD check in the ACTUAL frozen offer-mode trading path.
    chosen=np.zeros(NDAYS,dtype=np.int8)
    mtd_before=np.zeros(NDAYS)
    equity=1.0
    for d in range(NDAYS):
        mtd=equity-1.
        mtd_before[d]=mtd
        if fall[d] and mtd<=.0025:
            chosen[d]=rule_index
        gain=float(replay[0][d,chosen[d],1])
        equity*=1.+gain
    rows=[];summaries=[]
    for model in ("Step11_baseline","Step13_selected"):
        order=np.zeros(NDAYS,dtype=np.int8) if model=="Step11_baseline" else chosen
        for mi,fee in enumerate(base.MODES):
            k=np.arange(NDAYS)
            p=replay[0][k,order,mi]
            fees=replay[1][k,order,mi]
            gross=replay[2][k,order]
            why=replay[3][k,order]
            hold=replay[4][k,order]
            met=report_metrics(p)
            met.update(model=model,fee_model=fee,
                volume_event_trades=int(np.sum(~fall)),
                forced_fallback_trades=int(np.sum(fall)),
                early_exit_policy_days=int(np.sum(order!=0)),
                early_exits_triggered=int(np.sum(why==4)),
                total_fees_gst_btc_points=round(float(np.sum(fees)),4))
            summaries.append(met)
            for d,day in enumerate(nov.NDAYS):
                rows.append(dict(
                    model=model,fee_model=fee,date_ist=day.strftime("%Y-%m-%d"),
                    entry_hour_ist=int(hh[d]),
                    direction="LONG" if side[d]>0 else "SHORT",
                    trade_type="FALLBACK" if fall[d] else "VOLUME_EVENT",
                    selected_step11_structural_arm=study.ARMS[int(arm[d])][0] if fall[d] else "EVENT",
                    prior_MTD_account_pct=round(float(mtd_before[d]*100),6) if model=="Step13_selected" else None,
                    early_rule_enabled=bool(order[d]!=0),
                    previous_event_side_switched=bool(event_switch[d]),
                    net_account_return_pct=round(float(p[d]*100),6),
                    gross_btc_points=round(float(gross[d]),5),
                    fee_gst_btc_points=round(float(fees[d]),5),
                    exit_kind=("NEXT_BAR_EARLY_EXIT" if why[d]==4 else
                               "STOP" if why[d]==2 else
                               "TARGET" if why[d]==1 else "TIMEOUT"),
                    holding_minutes=int(hold[d])
                ))
    s=pd.DataFrame(summaries);day=pd.DataFrame(rows)
    if len(s)!=4 or len(day)!=60 or not s.trades.eq(15).all():
        raise AssertionError("Not exactly one trade for each November weekday")
    b=s[(s.model=="Step11_baseline")&(s.fee_model=="scalper_offer")].iloc[0]
    if b.profitable_days!=10 or abs(b.compounded_account_net_pct-.019249)>.00011:
        raise AssertionError("Previously verified Step11 Nov 15-day baseline parity failed "+str(b.to_dict()))
    s.to_csv(OUT/"two_frozen_models_two_fee_scenarios.csv",index=False)
    day.to_csv(OUT/"every_november_weekday_trade_60_rows.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(dict(
      experiment="Later chronological check of 2025-selected 19/22 month-winning strategy",
      november_ist_full_weekdays=15,
      policy="Step13: only fallback 21h when previously completed month PnL<=+0.25%, after20m prior1m close gross>=+0.10% triggers next1m open exit",
      no_november_model_retuning=True,
      data_had_previous_research_exposure=True,
      results=summaries,
      limitations=[
        "November 2026 has already been used in other frozen audits, so NOT pristine independent out-of-sample",
        "15 days not enough to validate a trading edge, and current months are not guaranteed profitable",
        "Real historical scalper offer activation, spread, funding, market impact and actual fills not known"]
    ),indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
        "# Frozen Step13 November 2026 daily BTC audit",
        "",
        "Both variants enter exactly once on 15 full Nov2–20 IST weekdays; Step13 threshold and early exit were selected only from 2025, no tuning on November.",
        "",
        s.to_markdown(index=False),"",
        "## Every November trade, both fee schedules","",
        day.to_markdown(index=False),"",
        "## Caveats",
        "Already researched 15-day period, not truly blind holdout. Real exchange fill quality and historical Scalper Offer eligibility unknown."
    ])+"\n")
    print("STEP13_NOV_AUDIT "+json.dumps(summaries,sort_keys=True),flush=True)
    print("STEP13_NOV_COMPLETE",flush=True)

if __name__=="__main__":
    run()
