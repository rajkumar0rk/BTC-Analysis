#!/usr/bin/env python3
"""Stricter Reclaim risk test: no originally profitable OR losing month may worsen.

Replay the original fixed (2% initial stop, 2/3/5 profit-lock) trade ledger
under signal-time causal entry filters only. A candidate is accepted iff,
for EACH of the 22 months and EACH of the two hypothetical 1m price paths:
    candidate_month_net >= baseline_month_net - 1e-8
and
    number of negative months strictly falls in BOTH paths.
This is historical in-sample optimization, NOT a live-forward guarantee.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_st_ema20_reclaim_preserve_profitable_months_20261122 import (
    load,make_masks,score,MONTHS,PATHS,EPS,KEEP_MIN
)

OUT=Path("analysis/st_ema20_reclaim_no_month_worse_20261122")

def main():
    f,t,P,track=load()
    primitives,masks=make_masks(f,P,track)
    accepted=[]
    stable=[]
    for key,mask in masks:
        if int(mask.sum())<KEEP_MIN:continue
        candidate=score(key,mask,P,track)
        no_down=True
        worsened=[]
        for path in PATHS:
            old=track[path]["net"]
            new=P[path][mask].sum(axis=0)
            diff=new-old
            if np.any(diff< -EPS):
                no_down=False
                worsened.append((path,[MONTHS[i] for i in np.flatnonzero(diff< -EPS)]))
        if no_down:
            stable.append(candidate)
        if no_down and candidate["reduced_losing_months_min"]>0:
            accepted.append(candidate)
    df=pd.DataFrame(accepted)
    if len(df):
        df=df.sort_values(["reduced_losing_months_min","losing_months_worst",
                           "net_22_worst","complexity","selected_trades"],
                         ascending=[False,True,False,True,False])
    OUT.mkdir(parents=True,exist_ok=True)
    df.to_csv(OUT/"strict_all_months_nondecreasing.csv",index=False)
    pd.DataFrame(stable).to_csv(OUT/"all_nonworsening_filters.csv",index=False)
    chosen=[]
    for case in (df.head(20).itertuples() if len(df) else []):
        mask=next(m for key,m in masks if " AND ".join(key)==case.filter_name)
        for path in PATHS:
            a=P[path][mask].sum(axis=0);b=track[path]["net"]
            for i,mo in enumerate(MONTHS):
                chosen.append(dict(filter_name=case.filter_name,
                  path=path,month_ist=mo,original_net=round(float(b[i]),6),
                  new_net=round(float(a[i]),6),
                  original_status=("Profit" if b[i]>EPS else "Loss" if b[i]<-EPS else "Flat"),
                  new_status=("Profit" if a[i]>EPS else "Loss" if a[i]<-EPS else "Flat"),
                  changed_usd=round(float(a[i]-b[i]),6)))
    pd.DataFrame(chosen).to_csv(OUT/"top_20_monthly_audit.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps({
        "tested_unique_filter_masks":len(masks),
        "never_worse_any_month_both_paths":len(stable),
        "never_worse_any_month_and_fewer_loss_months_both_paths":len(df),
        "trade_signals":62,
        "conditions":"each complete month independent, both OHLC path assumptions, dollar-profit nondecrease and no new losing month",
        "initial_stop_pct":2,
        "profit_lock_ladder_pct":[2,3,5],
        "years":"2025 full, 2026 Jan-Oct",
        "warning":"Strong retrospective constraint overfits historical months; no unbiased holdout or real exchange execution"
    },indent=2)+"\n")
    report=(
        "# EMA20 Reclaim: reduce losing months with NO month made worse\n\n"
        "Every month of 2025 and Jan-Oct 2026 must have **at least as much net USD** "
        "as the baseline in BOTH simulated price paths. This preserves all profitable months "
        "AND prevents increasing the size of any remaining losing month.\n\n"
        f"Distinct causal filters evaluated: {len(masks)}; completely nonworsening: {len(stable)}; "
        f"nonworsening AND reducing losing-month counts: {len(df)}.\n\n"
        "## Valid historical improvements\n\n"
        +(df.head(20).to_markdown(index=False) if len(df) else
          "No candidate met all the strict conditions in this causal filter grid.\n")
        +"\n\nResults are historical in-sample selection. Past-month preservation is NOT "
        "a rule that can be guaranteed in future trading. Trading risk, liquidation, "
        "exchange stop delay, and funding remain outside this replay.\n")
    (OUT/"RESEARCH_REPORT.md").write_text(report)
    print("COMPLETED",len(masks),"nonworsening",len(stable),"improving",len(df),flush=True)
    if len(df):print(df.head(15).to_string(index=False),flush=True)

if __name__=="__main__":
    main()
