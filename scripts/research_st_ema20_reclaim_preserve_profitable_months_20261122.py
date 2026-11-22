#!/usr/bin/env python3
"""Strict preserve-winners Reclaim research (not hindsight removal of known bad months).

OBJECTIVE: Filter out losing entries WITHOUT affecting ANY month profitable under
the frozen 2% initial SL / 2%-3%-5% profit-lock Reclaim baseline. Apply strict
constraints independently to two alternative historical 1m OHLC price paths:
 (A) preserve positive MONTH STATUS for each historically positive month,
 (B) stricter: preserve OR INCREASE its actual realized USD net profit.
Reduce original negative-month count with causal signal-hour filters only.

Uses the saved independently verified baseline 1m trade audit (62 entries/path)
and corresponding signal-hour indicator table. This is exact selection on a
frozen trade ledger: no re-entry, no changes to each selected trade's exit, and
no lookahead in deployed gate features. A skipped first fill does not trigger
an alternative entry within the same Supertrend cycle.
Research has substantial data snooping; 2026 is not pristine OOS.
"""
from __future__ import annotations
import itertools
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_st_ema20_reclaim_loss_months_20261122 import gates,MONTHS

SRC=Path("analysis/st_ema20_reclaim_loss_months_20261122")
OUT=Path("analysis/st_ema20_reclaim_preserve_profitable_months_20261122")
PATHS=("open_high_low_close","open_low_high_close")
BASELINE={
    "open_high_low_close":(14,8,13.522615),
    "open_low_high_close":(15,7,13.746743)
}
EPS=1e-8
KEEP_MIN=16

def load():
    f=pd.read_csv(SRC/"signal_entry_features.csv")
    assert len(f)==62 and f.entry_id.tolist()==list(range(62))
    t=pd.read_csv(SRC/"baseline_trade_feature_audit.csv")
    assert len(t)==124
    month_to_i={x:i for i,x in enumerate(MONTHS)}
    P={};track={}
    for path in PATHS:
        rows=t[t.path==path].sort_values("signal_entry_id").reset_index(drop=True)
        assert rows.signal_entry_id.tolist()==list(range(62)),path
        assert all(rows.signal_signal_utc.astype(str)==f.signal_utc.astype(str))
        mat=np.zeros((62,22),float)
        for x in rows.itertuples():
            mat[int(x.signal_entry_id),month_to_i[x.month_ist]]=float(x.net_usd)
        baseline=mat.sum(axis=0)
        positive=int((baseline>EPS).sum())
        negative=int((baseline< -EPS).sum())
        expected=BASELINE[path]
        assert (positive,negative)==expected[:2],(path,positive,negative)
        assert abs(baseline.sum()-expected[2])<.00001,(path,baseline.sum())
        P[path]=mat
        track[path]=dict(net=baseline,profit=baseline>EPS,losing=baseline< -EPS,
                         results=rows)
    return f,t,P,track

def make_masks(f,P,track):
    primitives=gates(f)
    masks={("all",):(np.ones(len(f),dtype=bool),{"all"})}
    prim_by_name={g["name"]:g for g in primitives}
    for g in primitives:
        masks[(g["name"],)]=(g["mask"],{g["category"]})
    # All two-family combinations (no month-name rules, no future P&L features).
    for a,b in itertools.combinations(primitives,2):
        if a["category"]==b["category"]:continue
        mask=a["mask"]&b["mask"]
        if mask.sum()>=KEEP_MIN:
            masks[(a["name"],b["name"])]=(mask,{a["category"],b["category"]})
    print("Raw unique-name singles and pairs:",len(masks),flush=True)
    # Triples seeded by strictly 2025 performance (avoid using 2026 for selection).
    pair_train=[]
    for key,(mask,families) in masks.items():
        if len(key)!=2 or mask.sum()<KEEP_MIN:continue
        keep=True
        reduce=[]
        net=[]
        for path in PATHS:
            v=P[path][mask,:12].sum(axis=0)
            b=track[path]["net"][:12]
            if np.any((b>EPS)&(v<=EPS)):
                keep=False;break
            reduce.append(int((b< -EPS).sum()-(v< -EPS).sum()))
            net.append(float(v.sum()))
        if keep:
            pair_train.append((min(reduce),min(net),key))
    pair_train.sort(key=lambda x:(x[0],x[1]),reverse=True)
    pairs=[x[2] for x in pair_train[:120]]
    for pair in pairs:
        basemask,families=masks[pair]
        for g in primitives:
            if g["category"] in families:continue
            mask=basemask&g["mask"]
            if mask.sum()<KEEP_MIN:continue
            key=tuple(sorted(pair+(g["name"],)))
            masks[key]=(mask,families|{g["category"]})
    print("Raw triplets and pairs:",len(masks),flush=True)
    unique={}
    for k,(m,cats) in masks.items():
        sig=np.packbits(m).tobytes()
        if sig not in unique or len(k)<len(unique[sig][0]):
            unique[sig]=(k,m)
    unique_list=list(unique.values())
    print("Distinct entry selection masks:",len(unique_list),flush=True)
    return primitives,unique_list

def score(key,mask,P,track):
    obj=dict(filter_name=" AND ".join(key),complexity=0 if key==("all",) else len(key),
             selected_trades=int(mask.sum()))
    aliveStatus=[];aliveDollars=[];alive25=[];alive26=[]
    reduction=[];red25=[];red26=[]
    for path in PATHS:
        month=P[path][mask].sum(axis=0)
        original=track[path]["net"]
        originalProf=track[path]["profit"]
        stat=not np.any(originalProf & (month<=EPS))
        cash=not np.any(originalProf & (month<original-EPS))
        st25=not np.any(originalProf[:12]&(month[:12]<=EPS))
        st26=not np.any(originalProf[12:]&(month[12:]<=EPS))
        baseLoss=track[path]["losing"]
        neg=month< -EPS
        obj[path+"_months_profit"]=int((month>EPS).sum())
        obj[path+"_months_loss"]=int(neg.sum())
        obj[path+"_months_flat"]=int((np.abs(month)<=EPS).sum())
        obj[path+"_net_2025"]=round(float(month[:12].sum()),6)
        obj[path+"_net_2026"]=round(float(month[12:].sum()),6)
        obj[path+"_net_22"]=round(float(month.sum()),6)
        obj[path+"_original_winners_preserved"]=int(np.count_nonzero(originalProf & (month>EPS)))
        obj[path+"_original_winners_count"]=int(np.count_nonzero(originalProf))
        obj[path+"_original_winners_dollars_preserved"]=int(np.count_nonzero(
            originalProf & (month>=original-EPS)))
        obj[path+"_removed_loss_months"]=int(np.count_nonzero(baseLoss)-np.count_nonzero(neg))
        aliveStatus.append(stat);aliveDollars.append(cash)
        alive25.append(st25);alive26.append(st26)
        reduction.append(int(baseLoss.sum()-neg.sum()))
        red25.append(int(baseLoss[:12].sum()-neg[:12].sum()))
        red26.append(int(baseLoss[12:].sum()-neg[12:].sum()))

    obj.update(all_prior_profitable_months_preserved=all(aliveStatus),
      all_prior_profitable_month_dollars_preserved=all(aliveDollars),
      original_2025_profit_months_preserved=all(alive25),
      original_2026_profit_months_preserved=all(alive26),
      reduced_losing_months_min=min(reduction),
      reduced_losing_months_max=max(reduction),
      reduced_losing_2025_min=min(red25),
      reduced_losing_2026_min=min(red26),
      profitable_months_min=min(obj[p+"_months_profit"] for p in PATHS),
      losing_months_worst=max(obj[p+"_months_loss"] for p in PATHS),
      flat_months_worst=max(obj[p+"_months_flat"] for p in PATHS),
      net_2025_worst=min(obj[p+"_net_2025"] for p in PATHS),
      net_2026_worst=min(obj[p+"_net_2026"] for p in PATHS),
      net_22_worst=min(obj[p+"_net_22"] for p in PATHS))
    obj["both_years_positive"]=obj["net_2025_worst"]>0 and obj["net_2026_worst"]>0
    return obj

def monthly_rows(winners,P,track):
    table=[]
    for z in winners.itertuples():
        key=z.filter_name
        # recover the mask from selection registry (injected by caller)
        mask=z._mask
        for path in PATHS:
            month=P[path][mask].sum(axis=0)
            b=track[path]["net"]
            for j,m in enumerate(MONTHS):
                table.append(dict(filter_name=key,path=path,month_ist=m,
                    baseline_net=round(float(b[j]),6),
                    baseline_status="profit" if b[j]>EPS else "loss" if b[j]<-EPS else "flat",
                    candidate_net=round(float(month[j]),6),
                    candidate_status="profit" if month[j]>EPS else "loss" if month[j]<-EPS else "flat",
                    delta=round(float(month[j]-b[j]),6),
                    original_profit_status_unchanged=(b[j]<=EPS or month[j]>EPS),
                    original_profit_amount_not_decreased=(b[j]<=EPS or month[j]>=b[j]-EPS)))
    return pd.DataFrame(table)

def main():
    f,t,P,track=load()
    primitives,masklist=make_masks(f,P,track)
    result=[]
    for key,mask in masklist:
        if mask.sum()<KEEP_MIN: continue
        row=score(key,mask,P,track)
        result.append(row)
    df=pd.DataFrame(result)
    baseline=df[df.filter_name=="all"].iloc[0]
    assert baseline.all_prior_profitable_months_preserved
    assert baseline.all_prior_profitable_month_dollars_preserved
    assert baseline.profitable_months_min==14 and baseline.losing_months_worst==8
    filtered=df[df.selected_trades>=KEEP_MIN]
    strict=filtered[(filtered.all_prior_profitable_months_preserved)&
       (filtered.both_years_positive)&(filtered.reduced_losing_months_min>0)]
    dollar=strict[strict.all_prior_profitable_month_dollars_preserved]
    keep2025=filtered[(filtered["original_2025_profit_months_preserved"])&
            (filtered.net_2025_worst>0)]
    strictRank=strict.sort_values(["reduced_losing_months_min","losing_months_worst",
                                  "net_22_worst","selected_trades","complexity"],
                                  ascending=[False,True,False,False,True])
    dollarRank=dollar.sort_values(["reduced_losing_months_min","losing_months_worst",
                                   "net_22_worst","selected_trades","complexity"],
                                   ascending=[False,True,False,False,True])
    # Training 2025 only, report 2026 NOT used to select.
    chronological=keep2025.sort_values(
       ["reduced_losing_2025_min","net_2025_worst","selected_trades","complexity"],
       ascending=[False,False,False,True]).head(40)
    relaxed=filtered[(filtered.all_prior_profitable_months_preserved)&
                       (filtered.both_years_positive)].sort_values(
       ["reduced_losing_months_min","net_22_worst"],ascending=False).head(40)
    OUT.mkdir(parents=True,exist_ok=True)
    df.to_csv(OUT/"all_causal_filters.csv",index=False)
    strictRank.head(80).to_csv(OUT/"top_strict_preserve_status.csv",index=False)
    dollarRank.head(80).to_csv(OUT/"top_strict_preserve_profit_dollars.csv",index=False)
    chronological.to_csv(OUT/"top_2025_only_2026_diagnostic.csv",index=False)
    relaxed.to_csv(OUT/"top_preserve_all_profitable_months.csv",index=False)
    known={"all"}
    known.update(strictRank.head(10).filter_name)
    known.update(dollarRank.head(10).filter_name)
    known.update(chronological.head(5).filter_name)
    masksByName={" AND ".join(k):mask for k,mask in masklist}
    audit=[]
    for name in sorted(known):
        if name not in masksByName:continue
        mask=masksByName[name]
        for path in PATHS:
            month=P[path][mask].sum(axis=0);b=track[path]["net"]
            for j,m in enumerate(MONTHS):
                audit.append(dict(filter_name=name,path=path,month_ist=m,
                  baseline_usd=round(float(b[j]),6),
                  baseline_status="profit" if b[j]>EPS else "loss" if b[j]<-EPS else "flat",
                  filtered_usd=round(float(month[j]),6),
                  filtered_status="profit" if month[j]>EPS else "loss" if month[j]<-EPS else "flat",
                  original_profitable_month_preserved=bool(b[j]<=EPS or month[j]>EPS),
                  profit_usd_not_decreased=bool(b[j]<=EPS or month[j]>=b[j]-EPS),
                  trade_count_selected=int(np.sum((P[path][mask,j]!=0.)))))
    pd.DataFrame(audit).to_csv(OUT/"selected_monthly_comparison.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps({
       "source":"Existing full 1m BTCUSD Reclaim baseline trade ledger, independently verified",
       "original_profit_months_by_path":{path:int(track[path]["profit"].sum()) for path in PATHS},
       "original_losing_months_by_path":{path:int(track[path]["losing"].sum()) for path in PATHS},
       "entries_considered":len(f),"candidate_causal_gates":len(primitives),
       "distinct_masks_evaluated":len(df),
       "strict_status_improvers":len(strict),
       "strict_status_and_dollar_improvers":len(dollar),
       "signal_filters":"only completed 1h hour data, no month-name rules",
       "baseline":"2% initial SL, 2-3-5% profit lock, volume >=1.25x",
       "month_window_IST":MONTHS,
       "limitations":["Search overfits 2025-26 data; 2026 not pristine unseen holdout",
          "Skipping entry never creates a later substitute within ST cycle",
          "Intra-minute paths assumed not tick reconstructed",
          "No exchange funding, liquidation, margin or amendment latency"]
    },indent=2)+"\n")
    report=(
      "# Reclaim: REDUCE losing months without harming existing profitable months\n\n"
      "**Hard rule:** each month historically profitable under the baseline must remain **strictly net positive**, "
      "individually for BOTH 1m price path models. A second harder rule preserves the USD profit AMOUNT "
      "of each originally profitable month. A profitable month CANNOT become flat.\n\n"
      "Baseline: 2% initial SL, 2%->3%->5% profit lock, 1H EMA20 Reclaim, "
      "volume ratio >=1.25x, 1m fills, 0.001 BTC, fees and modeled slippage.\n\n"
      f"Distinct causal filters tested: **{len(df)}**; status-preserving AND fewer losing months: "
      f"**{len(strict)}**; amount-preserving AND fewer losing months: **{len(dollar)}**.\n\n"
      "## Top strict: preserve profitable-month STATUS, reduce losing months in BOTH paths\n\n"
      +strictRank.head(20).to_markdown(index=False)+"\n\n"
      "## Stronger: do NOT reduce the net USD of ANY originally profitable month\n\n"
      +(dollarRank.head(20).to_markdown(index=False) if len(dollarRank) else "None found in tested filter grid.")
      +"\n\n## Select solely on 2025; 2026 diagnostic outcomes shown unchanged\n\n"
      +chronological.head(20).to_markdown(index=False)+"\n\n"
      "### Risk and bias\n\n"
      "The constraints themselves are assessed retrospectively on all 22 months, so qualifying "
      "candidates are **in-sample fits** and cannot guarantee preserving future profitable months. "
      "Chronological analysis is more informative, but 2026 was already used in earlier strategy searches. "
      "No guarantee of 22 positive months. No exchange tick sequence / stop latency / margin / liquidation / funding.\n")
    (OUT/"RESEARCH_REPORT.md").write_text(report)
    print("GRID COMPLETED",len(df),flush=True)
    print("STRICT STATUS IMPROVERS",len(strict),flush=True)
    print(strictRank.head(12).to_string(index=False),flush=True)
    print("STRICT DOLLAR IMPROVERS",len(dollar),flush=True)
    print(dollarRank.head(12).to_string(index=False),flush=True)
    print("2025 SELECTED",flush=True)
    print(chronological.head(8).to_string(index=False),flush=True)

if __name__=="__main__":
    main()
