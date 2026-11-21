#!/usr/bin/env python3
"""Can a *fixed* BTC portfolio have 22/22 positive months? Historical feasibility.

No next-month regime switching, month labels in a decision rule, or future trade
selection. Uses independent native 1m BTC core + Daily Donchian standalone
monthly sources, plus the Stage19 separately backtested 1H monthly source.

CRITICAL: This is a multiple-testing HISTORICAL UPPER BOUND, NOT a deployable
system or a genuine untouched holdout. Three components are merged by a
SYNTHETIC MONTHLY weighted NAV, not simultaneous margin-aware execution.
"""
from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd

OUT = Path("analysis/stage18_22positive_feasibility_20261121")
CORE = Path("/tmp/stage18-core/core_22_months.csv")
DON = Path("/tmp/stage18-donchian/donchian_monthly_mtm.csv")
H1 = Path("analysis/institutional_discovery_stage19_new_1h_patterns/monthly_results.csv")
MONTHS = pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
EPS=1e-9

def clean_frame(f,ret_col):
    x=f.reindex(columns=MONTHS)
    if x.shape[1]!=22 or x.isna().any().any() or not np.isfinite(x.to_numpy(dtype=float)).all():
        raise ValueError("Strategy return month coverage invalid")
    a=x.to_numpy(dtype=float)
    if np.min(a)<=-100:raise ValueError("Historical bankrupt sleeve")
    return x

def metrics(v):
    v=np.asarray(v,float)
    equity=np.cumprod(1+v/100)
    peak=np.maximum.accumulate(np.r_[1.,equity])[1:]
    return dict(positive_months=int((v>EPS).sum()),
                loss_months=int((v< -EPS).sum()),
                flat_months=int((abs(v)<=EPS).sum()),
                total_return_pct=float(100*(equity[-1]-1)),
                return_2025_pct=float(100*(np.prod(1+v[:12]/100)-1)),
                return_2026JanOct_pct=float(100*(np.prod(1+v[12:]/100)-1)),
                pos_2025=int((v[:12]>EPS).sum()),
                pos_2026=int((v[12:]>EPS).sum()),
                worst_month_pct=float(v.min()),
                max_monthend_drawdown_pct=float(100*np.max(1-equity/peak)))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    core=pd.read_csv(CORE)
    don=pd.read_csv(DON)
    h1=pd.read_csv(H1)
    C=clean_frame(core[core.extra_slippage_bps_side==0].pivot(index="model",columns="month_ist",values="return_pct"),"return_pct")
    D=clean_frame(don[don.extra_slippage_bps_side==0].pivot(index="model",columns="month_ist",values="return_pct"),"return_pct")
    H=clean_frame(h1.pivot(index="model",columns="month_ist",values="modeled_return_pct"),"modeled_return_pct")
    assert (len(C),len(D),len(H))==(59,54,140), (len(C),len(D),len(H))
    c=C.to_numpy(float);d=D.to_numpy(float);h=H.to_numpy(float)
    cname=C.index.tolist();dname=D.index.tolist();hname=H.index.tolist()
    ci=cname.index("core_maxrisk_700")
    di=dname.index("daily55_hold30")
    base=.7*c[ci]+.3*d[di]
    bm=metrics(base)
    if abs(bm["total_return_pct"]-14.438074)>.02 or (bm["positive_months"],bm["loss_months"],bm["flat_months"])!=(19,2,1):
        raise AssertionError(f"Stage18 70/30 baseline does not reconcile: {bm}")
    print("SOURCE_PARITY_70_30",json.dumps(bm))

    # Constant weights only; no portfolio allocations conditional on what month it is.
    best_two=[]
    for w in np.arange(.05,1.0,.05):
        x=w*c[:,None,:]+(1-w)*d[None,:,:]
        pos=(x>EPS).sum(axis=-1)
        score=(np.prod(1+x/100,axis=-1)-1)*100
        maximum=int(pos.max())
        i,j=np.argwhere(pos==maximum)[np.argmax(score[pos==maximum])]
        best_two.append((maximum,float(score[i,j]),float(w),cname[i],dname[j]))
    best_two.sort(reverse=True)
    print("BEST_2_SLEEVES_EXPOST",json.dumps(best_two[:3]))
    if best_two[0][0] > 19:
        raise AssertionError("Two-sleeve 2025-Jan no-trade proof invalid")

    # Screen only 1H families that have positive Jan25; other sleeves are 0
    # in that month, making 22 positive months mathematically impossible.
    h_idx=np.flatnonzero(h[:,0]>EPS)
    print("H1_2025_JAN_POSITIVE",len(h_idx),"of",len(H))

    # Predeclared grid, each weight multiple of 5%, all strictly positive.
    # Includes a broad allocation range and 46 Jan25-positive 1H models.
    weights=[]
    for ai in range(1,19):
        for bi in range(1,20-ai):
            hi=20-ai-bi
            if hi>=1: weights.append((ai/20,bi/20,hi/20))
    assert weights and all(abs(sum(w)-1)<1e-12 for w in weights)
    n_tests=0
    hit_count=0
    best_hindsight=None
    best_2025=None
    candidates_by_pos={}
    for k in h_idx:
        hk=h[k]
        for wc,wd,wh in weights:
            n_tests+=len(C)*len(D)
            # Cheap necessary conditions: both 2026-Jan and 2026-Oct >0.
            jan26=wc*c[:,None,12]+wd*d[None,:,12]+wh*hk[12]
            oct26=wc*c[:,None,21]+wd*d[None,:,21]+wh*hk[21]
            candidate=(jan26>EPS)&(oct26>EPS)
            if candidate.any():
                ii,jj=np.where(candidate)
                a=wc*c[ii]+wd*d[jj]+wh*hk
                positive=(a>EPS).sum(axis=1)
                top=int(positive.max())
                mask=(positive==top)
                ix_top=np.flatnonzero(mask)
                # Rank in the exploratory hindsight block by 22m positive
                # month count, then total return; never call it a validated model.
                equity=(np.prod(1+a[ix_top]/100,axis=1)-1)*100
                best_local=int(ix_top[np.argmax(equity)])
                record=dict(core=cname[ii[best_local]],donchian=dname[jj[best_local]],
                    hourly=hname[k],weights=dict(core=wc,donchian=wd,hourly=wh),
                    **metrics(a[best_local]))
                if (best_hindsight is None or
                    (record["positive_months"],record["total_return_pct"])>
                    (best_hindsight["positive_months"],best_hindsight["total_return_pct"])):
                    best_hindsight=record.copy()
                    best_hindsight["months"]=a[best_local].tolist()
                if top==22:
                    wins=np.flatnonzero(positive==22)
                    hit_count+=len(wins)
                    print("HISTORICAL_22_22_GRID_HIT",json.dumps(dict(
                        hourly=hname[k],core=cname[ii[wins[0]]],
                        donchian=dname[jj[wins[0]]],weight_core=wc,
                        weight_donchian=wd,weight_hourly=wh,
                        number_hits=len(wins))))
                candidates_by_pos[top]=candidates_by_pos.get(top,0)+int(mask.sum())

            # Choose using ONLY the 2025 training portion. Require positive
            # all 12 months if possible; rank by training return secondarily.
            first12=wc*c[:,None,:12]+wd*d[None,:,:12]+wh*hk[:12]
            positive_25=(first12>EPS).sum(axis=-1)
            maxpositive=int(positive_25.max())
            ix,jx=np.where(positive_25==maxpositive)
            trained=(np.prod(1+first12[ix,jx]/100,axis=1)-1)*100
            z=int(np.argmax(trained))
            aidx,bidx=int(ix[z]),int(jx[z])
            full=wc*c[aidx]+wd*d[bidx]+wh*hk
            record=dict(core=cname[aidx],donchian=dname[bidx],
                hourly=hname[k],weights=dict(core=wc,donchian=wd,hourly=wh),
                **metrics(full))
            selection=(record["pos_2025"],record["return_2025_pct"])
            if best_2025 is None or selection>(best_2025["pos_2025"],best_2025["return_2025_pct"]):
                best_2025=record.copy()
                best_2025["months"]=full.tolist()
    print("COMBINATIONS_SCORED",n_tests)
    print("HISTORICAL_MAX_MONTHLY_CONSISTENCY",json.dumps(dict(max_positive=best_hindsight["positive_months"],
          possible_22_22=bool(hit_count),count_22_22=hit_count,
          full_period_selection_is_lookahead=True)))
    for label, rec in (("BEST_HINDSIGHT_RESEARCH_ONLY",best_hindsight),
                       ("BEST_2025_SELECTION",best_2025)):
        out=rec.copy()
        arr=np.asarray(out.pop("months"),float)
        print(label,json.dumps(out))
        pd.DataFrame(dict(month_ist=MONTHS,monthly_pct=arr,
                     positive=arr>EPS)).to_csv(OUT/(label.lower()+"_monthly.csv"),index=False)
        (OUT/(label.lower()+".json")).write_text(json.dumps(out,indent=2)+"\n")
    summary={
        "core_variants":len(C),"donchian_variants":len(D),"hourly_variants":len(H),
        "third_sleeve_models_positive_in_Jan_2025":len(h_idx),
        "allocation_triplets":len(weights),"three_sleeve_combinations_considered":n_tests,
        "fixed_2_sleeves_max_positive_months":int(best_two[0][0]),
        "fixed_3_sleeves_max_positive_months":int(best_hindsight["positive_months"]),
        "count_22_positive_candidates":int(hit_count),
        "baseline_70_30":bm,"best_2025_only_selection":{k:v for k,v in best_2025.items() if k!="months"},
        "best_hindsight_choice":{k:v for k,v in best_hindsight.items() if k!="months"},
        "WARNING":"Historic 2026 was previously examined and any best-full-sample variant is lookahead selection",
        "DATA":"Independent standalone monthly BTC 1m results; Stage19 stored 1H monthly after-cost results, separate engine. Synthetic monthly blending only.",
        "COSTS":"Stage18 base fee 0.05% taker per side plus GST18%, 5BTC-point slip per side. Stage19 historical stored model has no comparable 2bp/5bp extra stress in this study.",
        "NOT_MODELED":"Funding, exact contract sizing, actual spread, live margin, integrated portfolios, concurrent execution, realistic mid-month rebalance",
        "NO_LIVE_ORDER_WRITE":True
    }
    (OUT/"feasibility_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("FEASIBILITY_STUDY_DONE",json.dumps(dict(max_positive=best_hindsight["positive_months"],hit_count=hit_count,output=str(OUT))))
if __name__=="__main__":main()
