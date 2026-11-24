#!/usr/bin/env python3
"""Research Reclaim V2 1H causal entry-filter combinations preserving locked monthly profit.

Uses the frozen 55 live-eligible *simulated* Reclaim V1 trade entries and their
previously audited exits. We ONLY skip entries based on completed H1 features.
Skipped entries never lead to replacement entries within same ST cycle.
Exact net P&L per selected trade including fees, GST, 5-point slippage is
unchanged. This is a deterministic selection-only replay, not new trades.

Strict acceptance on BOTH price-path models and Jan 2025..Oct 2026:
  - Candidate monthly USD >= locked monthly USD for EVERY month,
  - Positive months >=16 (V1 had 15),
  - Positive total profits in both calendar years.
Filter names must reference entry-time features only, NEVER outcome/month labels.
Caution: all conditions are selected in-sample; no untouched out-of-sample.
"""
from __future__ import annotations
import itertools
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_st_ema20_reclaim_loss_months_20261122 import gates,MONTHS

OUT=Path("analysis/reclaim_v2_causal_entry_filter_20261124")
SRC=Path("analysis/st_ema20_reclaim_loss_months_20261122")
PATHS=("open_high_low_close","open_low_high_close")
EXPECTED_NET={"open_high_low_close":20.037378,"open_low_high_close":20.261506}
EPS=1e-6

def build_gates(f):
    native=gates(f)
    allg=[(g["name"],np.asarray(g["mask"],bool)) for g in native]
    def add(name,mask):
        mask=np.asarray(mask,bool)
        if mask.any() and not mask.all():
            allg.append((name,mask))
    for col,values in {
       "volume_ratio":(1.3,1.5,1.75,2.,2.25,2.5,3.,3.5,4.,5.),
       "adx14":(15.,20.,25.,30.,35.,40.,45.),
       "dir_rsi14":(45.,48.,50.,52.,54.,55.,56.,58.,60.,62.,65.,70.),
       "ema_slope_pct":(-.15,-.1,-.05,0.,.05,.1,.15,.2,.25),
       "ema_gap_pct":(.05,.1,.15,.2,.25,.3,.4,.5,.6,.75,1.),
       "supertrend_gap_pct":(.5,.6,.75,1.,1.25,1.5,2.),
       "atr_pct":(.3,.5,.75,1.,1.25,1.5,2.),
       "atr_expansion":(.8,1.,1.2,1.5,2.),
       "hourly_range_atr":(.5,1.,1.5,2.,2.5),
       "supertrend_age_hours":(3,6,12,24,48,72)
    }.items():
        v=f[col].to_numpy(float)
        for thr in values:
            add(f"{col} <= {thr:g}",np.isfinite(v)&(v<=thr))
            add(f"{col} >= {thr:g}",np.isfinite(v)&(v>=thr))
    unique={}
    for name,mask in allg:
        n=sum((1<<i) for i,v in enumerate(mask) if v)
        if n not in unique:unique[n]=name
    return [(k,n) for n,k in unique.items()]

def data():
    f=pd.read_csv(SRC/"signal_entry_features.csv")
    t=pd.read_csv(SRC/"baseline_trade_feature_audit.csv")
    assert len(f)==62 and len(t)==124
    sel=(f.ema_gap_pct<=1.)&(f.ema_slope_pct>=-.2)&(f.supertrend_gap_pct>=.5)
    f=f[sel].reset_index(drop=True)
    assert len(f)==55,len(f)
    ID={x:i for i,x in enumerate(f.entry_id)}
    ix={x:i for i,x in enumerate(MONTHS)}
    mat={}
    for path in PATHS:
        rows=t[t.path==path]
        P=np.zeros((55,22),float)
        for r in rows.itertuples():
            if r.signal_entry_id not in ID:continue
            assert r.month_ist in ix,r
            P[ID[r.signal_entry_id],ix[r.month_ist]]=r.net_usd
        base=P.sum(axis=0)
        assert int((base>EPS).sum())==15,(path,base)
        assert int((base<-EPS).sum())==5,(path,base)
        assert int((abs(base)<=EPS).sum())==2,(path,base)
        assert abs(base.sum()-EXPECTED_NET[path])<1e-5,(path,base.sum())
        mat[path]=(P,base)
    return f,mat

def main():
    f,mats=data()
    gateset=build_gates(f)
    N=len(f);ALL=(1<<N)-1
    assert len(gateset)>110,len(gateset)
    gateset.append(("all",ALL))
    best={}
    seen=set()
    summary=dict(unique_masks=0,never_worse_any_month=0,win_improvers=0,
                 month_only_status_improvers=0,three_or_masks=0,three_plus_masks=0)
    def evalmask(mask,name,complexity):
        if mask in seen:return
        seen.add(mask)
        count=mask.bit_count()
        if count<25:return
        summary["unique_masks"]+=1
        keep=np.fromiter(((mask>>i)&1 for i in range(N)),dtype=bool,count=N)
        per=[];cash=True;status=True;never=True
        for path in PATHS:
            P,base=mats[path]
            v=P[keep].sum(axis=0)
            origpos=base>EPS
            if np.any(v[origpos]+EPS<base[origpos]):cash=False
            if np.any(v[origpos]<=EPS):status=False
            if np.any(v+EPS<base):never=False
            per.append(dict(path=path,positive=int((v>EPS).sum()),
               loss=int((v<-EPS).sum()),flat=int((abs(v)<=EPS).sum()),
               net=round(float(v.sum()),6),
               net2025=round(float(v[:12].sum()),6),
               net2026=round(float(v[12:].sum()),6),
               new_positive=";".join(MONTHS[i] for i in range(len(MONTHS))
                                     if base[i]<=EPS and v[i]>EPS)))
        if never:summary["never_worse_any_month"]+=1
        posmin=min(x["positive"] for x in per)
        if cash and status and posmin>=16: summary["month_only_status_improvers"]+=1
        if not (never and posmin>=16):return
        summary["win_improvers"]+=1
        row=dict(filter_name=name,complexity=complexity,selected_trades=count,
          profitable_months_worst=posmin,
          losing_months_worst=max(x["loss"] for x in per),
          flat_months_worst=max(x["flat"] for x in per),
          net_worst=min(x["net"] for x in per),
          net_best=max(x["net"] for x in per),
          net2025_worst=min(x["net2025"] for x in per),
          net2026_worst=min(x["net2026"] for x in per),
          promoted_months_both_paths=";".join(sorted(
              set(per[0]["new_positive"].split(";")) & set(per[1]["new_positive"].split(";")))),
          retained_mask_hex=hex(mask),
          no_month_worse=True)
        best[mask]=row
    evalmask(ALL,"locked_v1",0)
    for name,mask in gateset:
        if name!="all":evalmask(mask,name,1)
    for (a,mask_a),(b,mask_b) in itertools.combinations(gateset[:-1],2):
        evalmask(mask_a|mask_b,f"({a} OR {b})",2)
        evalmask(mask_a&mask_b,f"({a} AND {b})",2)
    print("Evaluated first-order and pair filters:",summary["unique_masks"],flush=True)
    # Exactly three entry-time OR conditions, preserving global causal policy.
    raw=gateset[:-1]
    for i in range(len(raw)):
        a,ma=raw[i]
        for j in range(i+1,len(raw)):
            b,mb=raw[j]
            together=ma|mb
            for k in range(j+1,len(raw)):
                c,mc=raw[k]
                union=together|mc
                if union not in seen:
                    evalmask(union,f"({a} OR {b} OR {c})",3)
                    summary["three_or_masks"]+=1
        if (i+1)%18==0:print("Three-gate OR search",i+1,"of",len(raw),flush=True)
    # Explore one more AND gate against promising simple OR configurations.
    winners=sorted(best.values(),key=lambda x:(
        -x["profitable_months_worst"],-x["net_worst"],x["complexity"]))
    for row in winners[:120]:
        parent=int(row["retained_mask_hex"],16)
        for condname,condmask in raw:
            mask=parent & condmask
            if mask in seen:continue
            evalmask(mask,f"({row['filter_name']} AND {condname})",row["complexity"]+1)
            summary["three_plus_masks"]+=1
    # Further pairs of top OR rules; still causal, historical candidate search.
    for a,b in itertools.combinations(winners[:60],2):
        mask=int(a["retained_mask_hex"],16)&int(b["retained_mask_hex"],16)
        if mask in seen:continue
        evalmask(mask,f"({a['filter_name']} AND {b['filter_name']})",
                 a["complexity"]+b["complexity"])
        summary["three_plus_masks"]+=1
    winners=sorted(best.values(),key=lambda x:(
        -x["profitable_months_worst"],-x["net_worst"],x["complexity"],-x["selected_trades"]))
    out=pd.DataFrame(winners)
    OUT.mkdir(parents=True,exist_ok=True)
    out.to_csv(OUT/"strict_no_month_worse_profitable_month_improvements.csv",index=False)
    out.head(40).to_csv(OUT/"top_40_month_win_improvements.csv",index=False)
    chosen=[dict(filter_name="locked_v1",mask=ALL)]
    for row in winners[:8]:
        chosen.append(dict(filter_name=row["filter_name"],
                           mask=int(row["retained_mask_hex"],16)))
    months=[]
    for z in chosen:
        keep=np.fromiter(((z["mask"]>>i)&1 for i in range(N)),bool,count=N)
        for path in PATHS:
            P,base=mats[path];v=P[keep].sum(axis=0)
            for i,mo in enumerate(MONTHS):
                months.append(dict(filter_name=z["filter_name"],path=path,
                  month_ist=mo,locked_v1_usd=round(float(base[i]),6),
                  candidate_usd=round(float(v[i]),6),
                  delta_usd=round(float(v[i]-base[i]),6),
                  candidate_status="PROFIT" if v[i]>EPS else "LOSS" if v[i]<-EPS else "FLAT"))
    pd.DataFrame(months).to_csv(OUT/"top_monthly_pnl_audit.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps({
       **summary,"primitive_1h_signal_gates":len(raw),
       "original_trades":55,
       "original_month_win":15,"original_month_loss":5,"original_month_flat":2,
       "original_net_usd_per_path":EXPECTED_NET,
       "initial_sl_pct":2,"profit_lock_ladder_pct":[2,3,5],
       "entry_frozen":"Base 1H Reclaim V1; skipped trade never replaced",
       "causality":"completed H1 entry features only",
       "source":"independently verified historical BTCUSD 1m trade ledger",
       "backtest_price_paths":PATHS,
       "bias":"In-sample multiple testing over 2025-26; 2026 not untouched holdout"
    },indent=2)+"\n")
    report=("# Reclaim V2: new profitable months using only causally filtered existing entries\n\n"
      "The 55 original Reclaim V1 entries are frozen, as are 2% initial SL, 2->3->5% profit protection, "
      "execution (1m), fees/GST, and 5 BTC-point modeled slippage per leg. "
      "Any candidate skips trade entries based ONLY on completed 1H signal indicator values. "
      "A skipped first fill in a Supertrend cycle does NOT permit reentry in that cycle.\n\n"
      "**Mandatory acceptance:** EVERY original month's USD net P&L MUST remain at least unchanged "
      "on both OHLC paths; winning-month count MUST increase over 15.\n\n"
      f"Unique trade subsets evaluated: {summary['unique_masks']}; exact candidates meeting constraints: "
      f"{len(out)}.\n\n"
      "## Best qualifying historical filters\n\n"
      +(out.head(35).to_markdown(index=False) if len(out) else "None found.\n")
      +"\n\n### Trade count and statistical caveats\n\n"
      "Only 55 original trades across 22 months. The OR filters may be highly tuned to this particular history; "
      "this is in-sample and not forward validation. The 2026 months are already used in earlier research. "
      "True order-book, funding, liquidation and stop amendment latency are not simulated.\n")
    (OUT/"RESEARCH_REPORT.md").write_text(report)
    print("SUCCESS causal filter grid",summary,"TOP",out.head(10).to_string(index=False),flush=True)

if __name__=="__main__":
    main()
