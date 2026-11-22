#!/usr/bin/env python3
"""Historical allocation retune for Stage18 21/22. Research only; NEVER places orders.

Inputs: independent BTC 1m core/Donchian monthly returns from completed Actions
run 44889747997 plus archived Stage19 1H monthly returns. This is a synthetic
monthly portfolio NAV BLEND, not integrated shared-margin trade execution.
Weights were chosen with already-seen 2026 data and are NOT forward validated.
Additional 2/5 bps slippage only stresses core and Donchian, not hourly sleeve.
"""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd

MONTHS = pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
CORE = "core_maxrisk_700"
DONCHIAN = "channel20_2atrtrail"
HOURLY = "ema20_pullback_confirm__4h_efficiency_ge30__3R__480min"
CASES = {
    "original_70_25_5": (0.70,0.25,0.05),
    "retuned_73p5_22p5_4": (0.735,0.225,0.04),
    "stress_count_72_23p5_4p5": (0.72,0.235,0.045),
}

def monthly(df, model, value, fee_col=None, fee=0):
    x = df[(df.model==model) & df.month_ist.isin(MONTHS)]
    if fee_col is not None: x = x[x[fee_col]==fee]
    if len(x)!=22 or x.month_ist.duplicated().any():
        raise ValueError(f"Missing or duplicated 22-month source {model}, {fee}")
    v=x.set_index("month_ist").reindex(MONTHS)[value].to_numpy(float)
    if not np.isfinite(v).all() or (v<=-100).any(): raise ValueError("Invalid return series")
    return v

def stats(v):
    e=100*np.r_[1,np.cumprod(1+v/100)]
    dd=100*np.max(1-e/np.maximum.accumulate(e))
    return dict(profitable_months=int((v>1e-9).sum()),
      losing_months=int((v<-1e-9).sum()),flat_months=int((abs(v)<=1e-9).sum()),
      compounded_return_pct=round(float(e[-1]-100),6),
      max_monthend_drawdown_pct=round(float(dd),6),
      worst_month_pct=round(float(v.min()),6),
      year2025_return_pct=round(float(e[12]-100),6),
      year2026_JanOct_return_pct=round(float((e[-1]/e[12]-1)*100),6),
      year2025_profitable_months=int((v[:12]>1e-9).sum()),
      year2026_profitable_months=int((v[12:]>1e-9).sum()),
      sep2026_return_pct=round(float(v[20]),6),
      oct2026_return_pct=round(float(v[21]),6))

def run(args):
    cdf=pd.read_csv(args.core); ddf=pd.read_csv(args.donchian); hdf=pd.read_csv(args.hourly)
    h=monthly(hdf,HOURLY,"modeled_return_pct")
    summary=[]; ledger=[]
    for cost in (0,2,5):
        c=monthly(cdf,CORE,"return_pct","extra_slippage_bps_side",cost)
        d=monthly(ddf,DONCHIAN,"return_pct","extra_slippage_bps_side",cost)
        for name,(wc,wd,wh) in CASES.items():
            if not np.isclose(wc+wd+wh,1):raise AssertionError("Weights do not sum to 1")
            v=wc*c+wd*d+wh*h
            summary.append(dict(name=name,additional_core_don_bps_per_side=cost,
              core_weight=wc,donchian_weight=wd,hourly_weight=wh,**stats(v)))
            ledger.extend(dict(name=name,additional_core_don_bps_per_side=cost,
              month_ist=m,core_pct=float(c[i]),donchian_pct=float(d[i]),
              hourly_pct=float(h[i]),portfolio_pct=float(v[i]),
              status=("Profit" if v[i]>1e-9 else "Loss" if v[i]<-1e-9 else "Flat"))
              for i,m in enumerate(MONTHS))
    a=pd.DataFrame(summary)
    original=a[(a.name=="original_70_25_5")&(a.additional_core_don_bps_per_side==0)].iloc[0]
    improved=a[(a.name=="retuned_73p5_22p5_4")&(a.additional_core_don_bps_per_side==0)].iloc[0]
    if abs(original.compounded_return_pct-13.569514)>0.0002 or original.profitable_months!=21:
        raise AssertionError("Historical 21/22 baseline did not reconcile")
    if not (improved.profitable_months==21 and improved.compounded_return_pct>original.compounded_return_pct
            and improved.max_monthend_drawdown_pct<original.max_monthend_drawdown_pct):
        raise AssertionError("Historical retune regression failed")
    args.output.mkdir(parents=True,exist_ok=True)
    a.to_csv(args.output/"scenario_summary.csv",index=False)
    pd.DataFrame(ledger).to_csv(args.output/"scenario_monthly.csv",index=False)
    (args.output/"limitations.json").write_text(json.dumps({
      "status":"IN-SAMPLE RETROSPECTIVE, NOT INDEPENDENTLY VALIDATED",
      "cost_stress":"Extra bps applied ONLY to CORE/DONCHIAN; H1 fixed at baseline",
      "shared_margin_simulation":False,"intraminute_drawdown":False,
      "funding_and_actual_quotes_and_rebalance_fills":False,
      "future_data_used_to_choose_weights":True,
      "no_live_orders":True
    },indent=2)+"\n")
    for line in summary:print("STAGE18_21_ALLOCATION_REPLAY",json.dumps(line))
    print("STAGE18_21_BASELINE_RECONCILED")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--core",type=Path,required=True)
    p.add_argument("--donchian",type=Path,required=True)
    p.add_argument("--hourly",type=Path,default=Path("analysis/institutional_discovery_stage19_new_1h_patterns/monthly_results.csv"))
    p.add_argument("--output",type=Path,default=Path("analysis/stage18_21_profit_robustness_20261122"))
    run(p.parse_args())
