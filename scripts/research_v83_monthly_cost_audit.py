#!/usr/bin/env python3
"""V83: monthly consistency and cost sensitivity of frozen strategies; no cost-based promotion."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import research_v82_execution as v
import research_v82_mean_reversion as mr
import research_v79_trend_pullback as pb
import research_v81_structural_pullback as st
import research_v78_broader_breakout as broad

OUT=Path("analysis/v83_monthly_cost_audit");OUT.mkdir(parents=True,exist_ok=True)
# Cost scenarios are economic assumptions, not tunable strategy parameters.
# Preserve the original reserve, position sizing, fees, slippage and funding.
BASE=next(s for s in v.SC if s[0]=="base")
STRESS=next(s for s in v.SC if s[0]=="combined")
SCENARIOS=[(("cash_"+str(cost),cost,*BASE[2:]),0) for cost in (0,50,100,200)]+[(STRESS,1)]
PROFILES=(("V69_no_cap",240,20,1.25),("V78_15bar",240,15,1.25),("V78_10bar",240,10,1.25),("V78_no_expansion",240,20,None),("V75_2h",120,20,1.25),("V75_1h",60,20,1.25),("V79_pullback",60,20,1.25),("V81_structural",15,20,1.25),("V82_mean",15,20,1.25))

def train():
    m,ctx=v.load("train")
    ctx["channels"]={n:v.channel_series(m,n) for n in (10,20)}
    rows=[];monthly=[]
    for name,tf,n,threshold in PROFILES:
        ctx["atr"]={tf:v.atr_series(m,tf)}
        ev,ctx["exit_context"]=broad.setup(m,tf,n,threshold)
        ctx["mean_target"]=np.full(len(m),np.nan)
        hold=60*tf;hours=12*tf//60
        cfg=dict(mr.CFG,timeframe=tf,lookback=n,hold_minutes=hold,early_hours=hours)
        if name=="V79_pullback":ev=pb.pullback_events(m)
        if name=="V81_structural":ev=st.structural_events(m)
        if name=="V82_mean":
            ev,ctx["mean_target"]=mr.mean_reversion_events(m,tf)
            hold=20*tf
            cfg=dict(mr.CFG,timeframe=tf,hold_minutes=hold,early_hours=0,early_kind="none",exit_kind="fixed_atr",mean_mode=True)
        for fold,a,b in v.FOLDS+[("continuous","2024-02-01","2026-01-01")]:
            p=v.period(m,ctx,ev,a,b)
            for sc,mode in SCENARIOS:
                r=v.run(ctx,p,cfg,50,sc,mode,audit=True)
                ledger=r.pop("ledger");ex=ledger[ledger[:,0]==3];pnl=ex[:,9]
                assert (ex[1:,1]>ex[:-1,2]).all()
                assert abs(float(pnl.sum())-r["net_usd"])<1e-6
                gp=float(ex[:,12].sum());fee=float(ex[:,13].sum());fund=float(ex[:,14].sum());extra=float(ex[:,15].sum())
                if r["liquidations"]==0 and r["ending_equity"]>0:assert abs(gp-fee+fund-extra-r["net_usd"])<1e-6
                win=np.sort(pnl[pnl>0])[::-1];loss=float(-pnl[pnl<0].sum())
                r.update(gross_price_usd=gp,fee_usd=fee,funding_usd=fund,extra_cost_usd=extra,profit_factor=float(win.sum())/loss if loss else None,net_ex_top5_usd=float(pnl.sum()-win[:5].sum()),net_ex_top3_usd=float(pnl.sum()-win[:3].sum()),expectancy_usd=float(pnl.mean()) if len(pnl) else 0.,busy_signals=int((ledger[:,0]==1).sum()),invalid_target_signals=int((ledger[:,0]==4).sum()),other_unexecuted=int((ledger[:,0]==0).sum()))
                assert r["signal_count"]==r["trades"]+r["rejected"]+r["busy_signals"]+r["invalid_target_signals"]+r["other_unexecuted"]
                us=r.pop("monthly_usd");re=r.pop("monthly_returns");r.pop("monthly_points")
                if fold=="continuous":
                    r.update(year2024_usd=float(us[:11].sum()),year2025_usd=float(us[11:].sum()),positive_2024=int((re[:11]>0).sum()),positive_2025=int((re[11:]>0).sum()),negative_months=int((re<0).sum()),zero_pnl_months=int((re==0).sum()),worst_month_pct=float(re.min()),median_month_pct=float(np.median(re)))
                    monthly.extend(dict(profile=name,scenario=sc[0],month=str(pd.Period("2024-02",freq="M")+i),net_usd=u,return_pct=q) for i,u,q in zip(range(len(us)),us,re))
                rows.append(dict(profile=name,tf_minutes=tf,fold=fold,leverage=50,scenario=sc[0],additional_cost_points=sc[1],**r))
        print("V83_PROFILE_DONE",name,flush=True)
    df=pd.DataFrame(rows)
    df.to_csv(OUT/"training_folds.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"training_monthly.csv",index=False)
    full=df[df.fold=="continuous"]
    expected=[("V69_no_cap",49.277536827321114,42.020963450250946,68,17),("V78_15bar",41.40026333443549,39.02993777764482,81,16),("V78_10bar",29.942377351397283,30.534205062767086,78,12),("V78_no_expansion",38.794573321357745,36.063615050493524,74,16),("V75_2h",-26.614425306296212,-27.621767813045025,106,8),("V75_1h",-47.21962250984401,-46.9883795196677,190,5),("V79_pullback",-35.05455893435783,-40.10947943532746,195,10),("V81_structural",-74.10813846646157,-75.09208360122591,209,0),("V82_mean",-77.43532322387733,-77.32357633756925,160,0)]
    for name,net,stress,trades,months in expected:
        x=full[(full.profile==name)&(full.scenario=="cash_200")].iloc[0]
        y=full[(full.profile==name)&(full.scenario=="combined")].iloc[0]
        assert abs(x.net_usd-net)<1e-6,(name,x.net_usd,net)
        assert abs(y.net_usd-stress)<1e-6,(name,y.net_usd,stress)
        assert x.trades==trades and x.positive_months==months
    ranking=[]
    for _,x in full.iterrows():
        f=df[(df.profile==x.profile)&(df.scenario==x.scenario)&(df.fold!="continuous")]
        incumbent=full[(full.profile=="V69_no_cap")&(full.scenario==x.scenario)].iloc[0]
        ranking.append(dict(profile=x.profile,scenario=x.scenario,additional_cost_points=x.additional_cost_points,trades=x.trades,wins=x.wins,net_usd=x.net_usd,profit_factor=x.profit_factor,positive_months=x.positive_months,months_ge_1pct=x.months_ge_1pct,positive_2024=x.positive_2024,positive_2025=x.positive_2025,negative_months=x.negative_months,zero_pnl_months=x.zero_pnl_months,worst_month_pct=x.worst_month_pct,median_month_pct=x.median_month_pct,year2024_usd=x.year2024_usd,year2025_usd=x.year2025_usd,closed_dd_pct=x.closed_dd_pct,mark_dd_upper_pct=x.mark_dd_upper_pct,profitable_folds=int((f.net_usd>0).sum()),liquidations_all=int(f.liquidations.sum()+x.liquidations),gross_price_usd=x.gross_price_usd,fee_usd=x.fee_usd,funding_usd=x.funding_usd,extra_cost_usd=x.extra_cost_usd,expectancy_usd=x.expectancy_usd,net_ex_top5_usd=x.net_ex_top5_usd,signals=x.signal_count,risk_rejected=x.risk_rejected,budget_rejected=x.budget_rejected,margin_rejected=x.margin_rejected,busy_signals=x.busy_signals,invalid_target_signals=x.invalid_target_signals,other_unexecuted=x.other_unexecuted,monthly_improvement_same_cost=int(x.positive_months-incumbent.positive_months),frequency_target_met=bool(x.trades>=300),monthly_target_met=bool(x.positive_months==23),min_monthly_target_met=bool(x.months_ge_1pct==23),diagnostic_only=True,training_pass=False))
    rank=pd.DataFrame(ranking)
    rank.to_csv(OUT/"training_ranking.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps(dict(training_period="2024-02 to 2025-12",validation_2026_run=False,new_strategy_configurations=0,frozen_profiles=len(PROFILES),baseline_parity_all_profiles=True,nominal_leverage=50,additional_cost_points=[0,50,100,200],combined_stress_retained=True,fee_gst_funding_and_slippage_retained=True,risk_and_reserve_unchanged=True,monthly_targets=[23,23],minimum_monthly_return_pct=1.,minimum_trades=300,diagnostic_only=True,actual_cost_calibration_pending=True,holdout_previously_examined=True,selection_bias_possible=True),indent=2))
    print(rank[["profile","scenario","trades","positive_months","months_ge_1pct","net_usd","closed_dd_pct","profitable_folds"]].to_string(index=False),flush=True)

if __name__=="__main__":train()
