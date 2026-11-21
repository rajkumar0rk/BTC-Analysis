#!/usr/bin/env python3
"""Investigate inactive BTC core in Sep 2026 with native 1m fills.

Audit *all* Stage14 pre-entry setups and causal gates. Re-run not only
recorded executions, but every newly eligible raw signal when the monthly
efficiency threshold changes. Keep the separately verified 30-day Donchian
sleeve unchanged, with 70/30 synthetic monthly rebalance.

Important: Aug 2026 previous-month efficiency=0.254272... in September.
Relaxing gate to 0.26 is RETROSPECTIVE on already seen Sep data.
There are no 2025 >0.25 regime months to train threshold safely.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive
import research_stage18_core_standalone_20261121 as core
import research_stage18_stage20_signal_exit_improvement_20261120 as nav
from research_stage18_70_30_portfolio_20261121 import metrics,blend_monthly

OUT=Path("analysis/stage18_september_gap_diagnostic_20261121")
DON_MONTHLY=Path("/tmp/stage18-donchian/donchian_monthly_mtm.csv")
H1=Path("analysis/institutional_discovery_stage19_new_1h_patterns/monthly_results.csv")
MONTHS=list(nav.MONTHS)

CASES=[
 ("baseline_eff025",.25,18,1.2),
 ("eff0255",.255,18,1.2),
 ("eff026",.26,18,1.2),
 ("eff0275",.275,18,1.2),
 ("eff030",.30,18,1.2),
 ("eff035",.35,18,1.2),
 ("eff100",1.,18,1.2),
 ("eff026_adx15",.26,15,1.2),
 ("eff026_adx22",.26,22,1.2),
 ("eff026_adx25",.26,25,1.2),
 ("eff026_adx30",.26,30,1.2),
 ("eff026_vr15",.26,18,1.5),
]
def by_month_source(df,label):
    x=df.set_index("month_ist").reindex(MONTHS)
    if x.return_pct.isna().any():raise AssertionError("Missing "+label)
    return x.return_pct.to_numpy(float)

def trade_count(g,month):
    if g is None:return 0
    return int((g.exit_month_ist==month).sum())

def diag_raw_events(events):
    e=events[(events.family==core.s15.FAMILY)].copy()
    rows=[]
    for m in MONTHS:
        g=e[e.month_ist==m]
        eff=g.previous_month_eff<=.25
        adx=g.h4_adx<=18
        vol=g.h1_vr<=1.2
        risk=g.risk_pts.between(150,700)
        allpass=eff&adx&vol&risk
        rows.append(dict(
            month_ist=m,raw_s13_signals=len(g),
            previous_month_efficiency=float(g.previous_month_eff.dropna().iloc[0]) if g.previous_month_eff.notna().any() else None,
            efficiency_gate_le025=int(eff.sum()),
            adx_gate_le18=int(adx.sum()),
            volume_gate_le12=int(vol.sum()),
            structural_risk_150_to_700=int(risk.sum()),
            pass_adx_volume_risk_without_eff=int((adx&vol&risk).sum()),
            pass_all_four=int(allpass.sum())))
    return pd.DataFrame(rows)

def portfolio_months(core_month,don_month,base_weight=.7):
    return blend_monthly(core_month,don_month,base_weight)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,_,_,quality=read_archive()
    e=core.load_events(f)
    audit=diag_raw_events(e)
    audit.to_csv(OUT/"core_entry_gate_month_by_month.csv",index=False)
    sept=audit[audit.month_ist=="2026-09"].iloc[0].to_dict()
    print("SEPTEMBER_CAUSAL_GATES",json.dumps(sept,default=str))
    assert sept["raw_s13_signals"]==34
    assert sept["pass_all_four"]==0
    assert abs(sept["previous_month_efficiency"]-.2542720938760542)<1e-10
    train=audit[audit.month_ist.str.startswith("2025")]
    assert all((train.previous_month_efficiency.dropna()<=.25))
    print("NO_2025_TRAINING_EXAMPLES_OF_EFF_GT025",json.dumps(dict(
        months_with_efficiency_between_025_and_030=0,
        september_previous_month_efficiency=sept["previous_month_efficiency"])))

    dm=pd.read_csv(DON_MONTHLY)
    rows=[];monthly=[];first=None
    for name,eff,adx,vol in CASES:
        cfg=core.case(name,eff=eff,adx=adx,vol=vol,maxrisk=700,
                      reward=5,hold=240)
        g=core.run_case(f,e,cfg)
        if g is None:continue
        if name=="baseline_eff025":
            if len(g)!=63:raise AssertionError("Baseline core no longer 63 trades")
            first=g
        septtrades=g[g.exit_month_ist=="2026-09"]
        for bps in (0,2,5):
            rv=nav.replay_nav(g,bps)
            c=np.asarray([z["net_pct"] for z in rv["monthly"]],dtype=float)
            sub=dm[(dm.model=="daily55_hold30")&(dm.extra_slippage_bps_side==bps)]
            d=by_month_source(sub,"donchian")
            comb=portfolio_months(c,d)
            st=metrics(comb)
            trainstats=metrics(comb[:12])
            holdout=metrics(comb[12:])
            rs=dict(case=name,efficiency_max=eff,adx_max=adx,h1_volume_max=vol,
                 extra_bps_per_side=bps,core_trades=len(g),
                 core_september_trades=len(septtrades),
                 core_september_pct=float(c[MONTHS.index("2026-09")]),
                 donchian_september_pct=float(d[MONTHS.index("2026-09")]),
                 combined_september_pct=float(comb[MONTHS.index("2026-09")]),
                 core_total_return_pct=metrics(c)["total_return_pct"],
                 train_2025_return_pct=trainstats["total_return_pct"],
                 train_2025_profitable_months=trainstats["positive_months"],
                 exposed_2026_return_pct=holdout["total_return_pct"],**st)
            rows.append(rs)
            monthly.extend(dict(case=name,extra_bps_per_side=bps,month_ist=m,
                core_pct=float(x),donchian_pct=float(y),
                combined_pct=float(z)) for m,x,y,z in zip(MONTHS,c,d,comb))
            if bps==0 and name in ("baseline_eff025","eff026","eff026_adx22"):
                print("CORE_EFFICIENCY_CHECK",json.dumps(rs,default=str))
        if name in ("baseline_eff025","eff026","eff026_adx22"):
            septtrades.to_csv(OUT/f"{name}_september_trades.csv",index=False)
    if first is None:raise AssertionError("Missing immutable baseline")
    totals=pd.DataFrame(rows)
    totals.to_csv(OUT/"threshold_experiment_summaries.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"threshold_experiment_monthly.csv",index=False)
    early=totals[(totals.extra_bps_per_side==0)&
                 (totals.case.isin(["baseline_eff025","eff0255","eff026","eff0275","eff030","eff035","eff100"]))]
    if not np.allclose(early.train_2025_return_pct.to_numpy(),
                       early.train_2025_return_pct.iloc[0],rtol=0,atol=1e-8):
        raise AssertionError("2025 changed despite no 2025 eff > .25")
    # Independent 1H archive model, selected by 2025-only without using Sep26 outcome.
    h1=pd.read_csv(H1)
    saved=totals[(totals.case=="baseline_eff025")&(totals.extra_bps_per_side==0)].iloc[0]
    core_m=pd.DataFrame(monthly)
    main=core_m[(core_m.case=="baseline_eff025")&(core_m.extra_bps_per_side==0)].set_index("month_ist").reindex(MONTHS).combined_pct.to_numpy(float)
    h1models=[]
    for name,grp in h1.groupby("model"):
        group=grp.set_index("month_ist").reindex(MONTHS)
        hr=group.modeled_return_pct.to_numpy(float)
        if not np.isfinite(hr).all():continue
        training_trades=int(group.trades.iloc[:12].sum())
        if training_trades<25:continue
        for alloc in (.05,.10,.15):
            blended=(1-alloc)*main+alloc*hr
            m=metrics(blended)
            t=metrics(blended[:12])
            h1models.append(dict(model=name,allocation=alloc,
                train_2025_trades=training_trades,
                train_2025_return_pct=t["total_return_pct"],
                train_2025_positive=t["positive_months"],
                september_2026_hourly_pct=float(hr[20]),
                september_2026_combined_pct=float(blended[20]),
                **m))
    hm=pd.DataFrame(h1models)
    hm.to_csv(OUT/"archived_h1_independent_candidate_comparison.csv",index=False)
    selected=hm.sort_values(["train_2025_positive","train_2025_return_pct"],
                          ascending=False).iloc[0].to_dict()
    print("H1_SELECTED_ON_2025_ONLY",json.dumps(selected,default=str))
    (OUT/"research_quality.json").write_text(json.dumps(dict(
        source=quality,
        reason_sept_2026="previous-month 4H efficiency Aug2026 0.254272093876 > .25 gate",
        prior_month_efficiency_is_causal=True,
        phase="historical exploratory; september 2026 already examined",
        prior_month_filter_repair="Not validated: no 2025 examples above .25. Do not enable 0.26 on retrospective September outcome.",
        baseline_2025_gate_only_same=True,
        baseline=totals[(totals.case=="baseline_eff025")&(totals.extra_bps_per_side==0)].iloc[0].to_dict(),
        h1_selection=selected,
        limitations=[
           "Native 1m for Core replays; Stage17 Donchian also 1m from prior verified standalone run",
           "H1 archived historical model outputs are not yet reproduced with shared 1m live execution",
           "No new trade-level integrated shared margin backtest; synthetic monthly blend only",
           "Funding, actual spread, maintenance margin, spot-order limits, and tick fills excluded",
           "Choosing a threshold solely to unlock Sep2026 is hindsight and invalid forward evidence",
           "No 2025 examples of previous_month_efficiency in (.25,.30], so not trainable on 2025",
           "True forward out-of-sample testing needed before live trading",
        ],
    ),default=str,indent=2)+"\n")
    print("SEPTEMBER_GAP_AUDIT_DONE",json.dumps(dict(
        rows=len(totals),cases=len(CASES),h1_models=len(hm),
        output=str(OUT)),default=str))
if __name__=="__main__":main()
