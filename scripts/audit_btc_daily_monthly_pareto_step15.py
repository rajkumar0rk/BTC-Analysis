#!/usr/bin/env python3
"""Frozen Step15 A/B retrospective monthly ledgers and later 15-day audit.

A/B were already noticed AFTER entire Jan2025-Oct2026 performance was seen,
so NOT independent 2025-selected policies. Explicitly label in-sample.
The November chronological check uses exactly the frozen side/exit conditions.
"""
from pathlib import Path
import json

import numpy as np
import pandas as pd

import research_btc_every_weekday_reset_step1 as base
import research_btc_daily_causal_regime_step5 as regime
import research_btc_every_weekday_exit_protection_step3 as protection
import research_btc_daily_exit_invalidation_step7 as bar
import research_btc_daily_monthly_exit_step13 as step13
import research_btc_daily_monthly_two_regime_step15 as experiment
import audit_btc_daily_fallback_regime_november_2026 as nov
import audit_btc_daily_monthly_exit_step13_november as nov13

OUT=Path("analysis/btc_daily_two_regime_step15/frozen_candidate_audit")
CASES={
    "Step13_original":("none","baseline","none","baseline"),
    "A_20_month_hindsight":(
        "mtd_not_positive","adverse_cut_0.08pct_after_10m",
        "peak_ge_plus1_and_giveback050","profit_close_at_0.1pct_after_10m"),
    "B_21_month_hindsight":(
        "mtd_not_positive","adverse_cut_0.08pct_after_10m",
        "mtd_at_least_plus1","profit_close_at_0.1pct_after_10m")
}
def metrics(p):
    p=np.asarray(p,dtype=float)
    q=np.cumprod(1+p)
    priorpeak=np.maximum.accumulate(np.r_[1.,q])[1:]
    return dict(trades=len(p),profitable_days=int(np.sum(p>0)),
        losing_days=int(np.sum(p<0)),
        net_compounded_account_pct=round(float(100*(q[-1]-1)),6),
        max_closed_drawdown_pct=round(float(100*np.max(1-q/priorpeak)),6),
        worst_day_pct=round(float(100*np.min(p)),6))

def nov_choice(raw,mask,params,ids):
    # Nov is a single month, so reset month-to-date equity to exactly 1.
    n=len(mask)
    decision=np.zeros(n,dtype=np.int16)
    before=np.zeros(n)
    giveback=np.zeros(n)
    equity=1.
    peak=1.
    for d in range(n):
        mtd=equity-1
        gb=peak-equity
        before[d]=mtd
        giveback[d]=gb
        baseline_index=ids["profit_close_at_0.1pct_after_20m"] if (
            mask[d] and mtd<=.0025) else 0
        chosen=baseline_index
        if mask[d]:
            if params[3]!="baseline" and experiment.gate(
               params[2],mtd,peak,gb,d):
                chosen=ids[params[3]]
        else:
            if params[1]!="baseline" and experiment.gate(
               params[0],mtd,peak,gb,d):
                chosen=ids[params[1]]
        decision[d]=chosen
        # "Offer" outcome determines selected exit for both fee comparisons.
        equity*=1+float(raw[0][d,chosen,1])
        peak=max(peak,equity)
    return decision,before,giveback

def historical_audit(names,ids):
    m,ctx,mask,fb,side,hour,idx,cfg=step13.create_path()
    raw=bar.replay_with_nextbar_exits(
        m.open.to_numpy(float),m.high.to_numpy(float),m.low.to_numpy(float),
        m.close.to_numpy(float),idx,side,cfg,names,base.COST,base.SLIP
    )
    step13.check_parity(raw,ctx,fb)
    output={}
    for label,params in CASES.items():
        choice,mtd,giveback,changed_e,changed_f=experiment.replay_one(
            raw,mask,ids["profit_close_at_0.1pct_after_20m"],params,ids)
        output[label]={}
        for mi,mode in enumerate(base.MODES):
            path=experiment.getout(raw,choice,mi)
            daily,monthly=experiment.saved_ledger(
                path,choice,mtd,giveback,idx,hour,side,mask,mode
            )
            daily.to_csv(OUT/(f"historical_{label}_{mode}_477_daily.csv"),index=False)
            monthly.to_csv(OUT/(f"historical_{label}_{mode}_22_months.csv"),index=False)
            z=experiment.score(path)
            output[label][mode]=dict(
                winning_months=int(np.sum(monthly.net_compounded_pct>0)),
                max_dd=z["max_closed_dd_pct"],
                net_pct=z["net_total_pct"],
                profitable_days=z["profitable_days"],
                years_2025_positive_months=z["win_months_2025"],
                year_2026_positive_months=z["win_months_2026"],
                year_2025_net=z["return_2025_pct"],
                year_2026_net=z["return_2026_pct"],
                changed_event_exit_days=changed_e,
                changed_fallback_exit_days=changed_f,
                losing_months=monthly.loc[monthly.net_compounded_pct<=0,
                      ["month_ist","net_compounded_pct"]].to_dict("records"))
    assert output["Step13_original"]["scalper_offer"]["winning_months"]==19
    assert output["A_20_month_hindsight"]["scalper_offer"]["winning_months"]==20
    assert output["B_21_month_hindsight"]["scalper_offer"]["winning_months"]==21
    if abs(output["A_20_month_hindsight"]["scalper_offer"]["net_pct"]-24.648136)>.00011:
        raise AssertionError("A historical replay unexpected")
    if abs(output["B_21_month_hindsight"]["scalper_offer"]["net_pct"]-22.480405)>.00011:
        raise AssertionError("B historical replay unexpected")
    print("STEP15_FROZEN_A_B_22MONTH "+json.dumps(output,sort_keys=True),flush=True)
    return output

def november_audit(policies,ids):
    m=nov.load_with_nov()
    idx,hours,base_side,mask=nov.determine_entries(m,"follow5")
    n=len(idx)
    if n!=15 or int(mask.sum())!=6:
        raise AssertionError("Not 15 complete IST weekdays")
    volumes=m.volume.to_numpy(float)
    ratio=np.zeros(n,dtype=float)
    for d,i in enumerate(idx):
        prev=volumes[i-105:i-5].reshape(20,5).sum(axis=1)
        avg=float(prev.mean())
        ratio[d]=float(volumes[i-5:i].sum()/avg) if avg>0 else 1.
    side,arms,events,prior=nov13.discover_entry_sides(m,idx,base_side,mask,ratio)
    if not np.array_equal(side,base_side):
        raise AssertionError("Previously verified Nov Step11 online sides drift")
    recipes,recipe_id=regime.build_cfg()
    cfg=np.asarray([
        recipes[recipe_id["lock050"] if not mask[d] else
                (recipe_id["trail075"] if ratio[d]>=1.25 else recipe_id["trail050"])]
        for d in range(n)],dtype=float)
    raw=bar.replay_with_nextbar_exits(
        m.open.to_numpy(float),m.high.to_numpy(float),m.low.to_numpy(float),
        m.close.to_numpy(float),idx,side,cfg,policies,base.COST,base.SLIP)
    )
    records=[]
    rows=[]
    for label,params in CASES.items():
        choice,mtd,gb=nov_choice(raw,mask,params,ids)
        d=np.arange(n)
        for mi,mode in enumerate(base.MODES):
            p=raw[0][d,choice,mi]
            c=raw[1][d,choice,mi]
            g=raw[2][d,choice]
            why=raw[3][d,choice]
            hold=raw[4][d,choice]
            stat=metrics(p)
            stat.update(model=label,cost_model=mode,
                fallback_days=int(np.sum(mask)),event_days=int(np.sum(~mask)),
                overlay_exit_days=int(np.sum(choice!=0)),
                triggered_early_exits=int(np.sum(why==4)),
                total_fee_gst_points=round(float(np.sum(c)),4))
            records.append(stat)
            for i,day in enumerate(nov.NDAYS):
                rows.append(dict(
                    model=label,cost_model=mode,date_ist=day.strftime("%Y-%m-%d"),
                    hour_ist=int(hours[i]),entry_type="FALLBACK" if mask[i] else "EVENT",
                    direction="LONG" if side[i]>0 else "SHORT",
                    prior_month_net_pct=round(float(100*mtd[i]),6),
                    prior_month_peak_giveback_pct=round(float(100*gb[i]),6),
                    active_exit=name_lookup[int(choice[i])],
                    net_account_pct=round(float(100*p[i]),6),
                    gross_btc_points=round(float(g[i]),5),
                    fees_gst_btc_points=round(float(c[i]),5),
                    exit_type="EARLY_NEXT_OPEN" if why[i]==4 else (
                        "STOP" if why[i]==2 else ("TP" if why[i]==1 else "TIMEOUT")),
                    holding_minutes=int(hold[i])))
    result=pd.DataFrame(records)
    ledger=pd.DataFrame(rows)
    assert len(result)==6 and result.trades.eq(15).all()
    assert len(ledger)==90
    baseline=result[(result.model=="Step13_original")&
             (result.cost_model=="scalper_offer")].iloc[0]
    if baseline.profitable_days!=10 or abs(baseline.net_compounded_account_pct+.47076)>.00011:
        raise AssertionError("Nov Step13 regression failure "+str(baseline.to_dict()))
    result.to_csv(OUT/"frozen_november_A_B_baseline_two_fees.csv",index=False)
    ledger.to_csv(OUT/"frozen_november_every_day_two_fees.csv",index=False)
    records=[dict(x) for x in records]
    print("STEP15_FROZEN_NOVEMBER "+json.dumps(records,sort_keys=True),flush=True)
    return records

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    policies,names=bar.build_exit_policies()
    global name_lookup
    name_lookup=names
    ids={name:i for i,name in enumerate(names)}
    history=historical_audit(policies,ids)
    novres=november_audit(policies,ids)
    report=dict(
       label="HINDSIGHT selected A/B monthly-positive candidate audit, NOT genuine independent validation",
       historical_2025_oct2026=history,
       chronological_15_november=novres,
       calendar="477/477 IST Monday-Friday full historic trades, then 15/15 later Nov2-20 2026 weekdays",
       model_selection="Official Step15 strict 2025-selected policy remained original Step13 19/22. Both A and B were identified retrospectively after 2026 results and must not be promoted as verified.",
       fee_model="1x notional, taker 0.05% per leg+GST18%, hypothetical preactivated Scalper Offer waived <=30min exit fee, adverse 5 BTC point slippage per leg",
       limitations=[
         "Extensive 2025–2026 reuse and previous November research; no statistically independent data",
         "Standard taker fee profitability poor, actual historical Scalper Offer not verified",
         "No real market fill/spreads/depth/latency, funding or liquidation simulation",
         "All strategies lose some calendar months and cannot guarantee a profitable weekday"]
    )
    (OUT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    a=pd.read_csv(OUT/"frozen_november_A_B_baseline_two_fees.csv")
    lines=["# BTCUSD 20/22 and 21/22 hindsight monthly candidates — frozen check","",
       "The candidate settings and limitations were committed BEFORE viewing November outcomes. They had already been seen in the full 22-month data and do not constitute independent strategy validation.",
       "",
       "## Full historical after-cost results",json.dumps(history,indent=2),
       "",
       "## Frozen 15 weekday November audit",a.to_markdown(index=False),
       "",
       "## 22-month net return by candidate"]
    for label in CASES:
        month=pd.read_csv(OUT/(f"historical_{label}_scalper_offer_22_months.csv"))
        lines.extend(["",f"### {label}",month.to_markdown(index=False)])
    lines.extend(["","## Limitations",*report["limitations"]])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("STEP15_FROZEN_AUDIT_COMPLETE",flush=True)

if __name__=="__main__":
    run()
