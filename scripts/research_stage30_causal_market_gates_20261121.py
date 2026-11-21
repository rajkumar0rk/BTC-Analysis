#!/usr/bin/env python3
"""Stage30: causal 4H market-state gates for existing independent BTCUSD
Mean Reversion and Range Trading hypotheses.

Precommits templates and 4H causal gates; 2025-only train selection scores
worst quarterly performance and drawdown, then reports 2026 chronological
results. 2026 is ALREADY RESEARCH-EXPOSED, not virgin OOS. No real orders.
1-minute next-open entry, stop-first 1m execution and full 5bps/slippage stress.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive
from research_stage28_new_reversion_range_20261121 import prepare_new_events,tf,MONTHS,MONTH_INDEX
from research_stage27_meanreversion_range_20261121 import replay_one
OUT=Path("analysis/stage30_causal_regime_gate_20261121")
EPS=1e-8
# These templates use old 2025-training winners and related stop/TP robustness
# configurations. They are frozen BEFORE this stage's 2026 result computation.
TEMPLATES=[
 ("MR","mr_rsi2_recovery_h1","short","aligned","quiet","atr2","3R",1920),
 ("MR","mr_rsi2_recovery_h1","short","aligned","quiet","atr3","3R",1920),
 ("MR","mr_bollinger_reclaim_h1","long","any","loose","atr3","3R",1920),
 ("MR","mr_bollinger_reentry","long","any","loose","atr3","3R",1920),
 ("MR","mr_bollinger_reentry","long","any","trend","atr3","to_mean",1920),
 ("MR","mr_bollinger_reentry","long","any","loose","atr3","to_mean",960),
 ("MR","mr_bollinger_reclaim_h1","long","any","loose","atr3","3R",960),
 ("MR","mr_4h_bollinger_reentry","both","any","loose","atr3","to_mean",1920),
 ("RANGE","range_touch_48","both","any","quiet","atr2","3R",1920),
 ("RANGE","range_touch_48","both","any","quiet","atr3","1.2R",1920),
 ("RANGE","range_touch_48","long","any","loose","struct","3R",960),
 ("RANGE","range_touch_48","both","any","trend","atr3","to_mean",1920),
 ("RANGE","range_touch_48","long","any","loose","struct","to_mean",960),
 ("RANGE","range_touch_48","short","any","loose","atr2","2R",1920),
 ("RANGE","range_sweep_48","long","any","trend","atr3","to_mean",960),
 ("RANGE","range_4h_sweep_12","short","any","trend","struct","to_mean",1920)
]
REGIME={"strict":(18.,.25),"quiet":(25.,.35),"loose":(32.,.50),"trend":(45.,.70)}
# Not optimized against 2026. Each causal filter uses only completed 4H
# historical candles and may fail to distinguish actual trends in real time.
GATES=[
 "none",
 "chop_ge55",
 "chop_ge60",
 "channel_no_break",
 "atr_ratio_le1p2",
 "drift3_atr_le1p5",
 "ema50_distance_atr_le2p5",
 "channel_no_break_and_chop55",
 "channel_no_break_and_atr_ratio_le1p2",
 "chop_ge55_and_atr_ratio_le1p2",
 "range_mid50pct",
 "chop_ge55_and_drift_le1p5"
]

def h4_features(f):
    h4=tf(f,"4h",240,65)
    prior=h4.close.shift(1)
    tr=pd.concat((h4.high-h4.low,(h4.high-prior).abs(),
                  (h4.low-prior).abs()),axis=1).max(axis=1)
    rng=(h4.high.rolling(14,min_periods=14).max()-
         h4.low.rolling(14,min_periods=14).min())
    h4["chop"]=100*np.log10(tr.rolling(14,min_periods=14).sum()/
          rng.replace(0,np.nan))/np.log10(14.)
    h4["atr_ratio"]=h4.atr/(h4.atr.shift(1).rolling(
          20,min_periods=20).median().replace(0,np.nan))
    h4["drift3"]=abs(h4.close-h4.close.shift(3))/h4.atr.replace(0,np.nan)
    h4["distance50"]=abs(h4.close-h4.ema50)/h4.atr.replace(0,np.nan)
    hi20=h4.high.shift(1).rolling(20,min_periods=20).max()
    lo20=h4.low.shift(1).rolling(20,min_periods=20).min()
    h4["channel_no_break"]=(h4.close<=hi20)&(h4.close>=lo20)
    hi48=h4.high.shift(1).rolling(48,min_periods=48).max()
    lo48=h4.low.shift(1).rolling(48,min_periods=48).min()
    width=hi48-lo48
    h4["range_mid50pct"]=((h4.close>=lo48+.25*width)&
                          (h4.close<=lo48+.75*width))
    return h4

def add_gate_features(events,f):
    h4=h4_features(f)
    ts=f.index[events.k.to_numpy(int)]
    # At event's *next* minute after fully closed H1/H4 candle, a
    # completed H4 bar may be read only if its right-edge timestamp<=event.
    z=h4.reindex(pd.DatetimeIndex(ts),method="ffill")
    out=events.reset_index(drop=True).copy()
    if not np.array_equal(out.entry_unix.to_numpy(np.int64),
                          f.time.to_numpy(np.int64)[out.k.to_numpy(int)]):
        raise AssertionError("Event timestamps not indexed to 1m source")
    for col in ("chop","atr_ratio","drift3","distance50",
                "channel_no_break","range_mid50pct","complete"):
        out["gate_"+col]=z[col].to_numpy()
    # Check no 4H unfinished bar is possible.
    valid=np.asarray(out.gate_complete.fillna(False),bool)
    out=out[valid].copy()
    print("CAUSAL_GATE_EVENT_COUNT",json.dumps(
        {str(k):int(v) for k,v in out.groupby("family").size().items()}))
    return out

def gate_subset(e,g):
    v=pd.Series(True,index=e.index)
    if "chop_ge55" in g:v&=e.gate_chop>=55
    if "chop_ge60" in g:v&=e.gate_chop>=60
    if "channel_no_break" in g:v&=e.gate_channel_no_break
    if "atr_ratio_le1p2" in g:v&=e.gate_atr_ratio<=1.2
    if "drift3_atr_le1p5" in g or "drift_le1p5" in g:v&=e.gate_drift3<=1.5
    if "ema50_distance_atr_le2p5" in g:v&=e.gate_distance50<=2.5
    if "range_mid50pct" in g:v&=e.gate_range_mid50pct
    return e[v.fillna(False)]

def monthly_stats(v):
    v=np.asarray(v,float)
    nav=np.cumprod(1+v/100)
    peak=np.maximum.accumulate(np.r_[1,nav])[1:]
    quarters=[100*(np.prod(1+v[i:i+3]/100)-1) for i in (0,3,6,9)]
    return dict(net22=float(100*(nav[-1]-1)),
       train2025=float(100*(np.prod(1+v[:12]/100)-1)),
       researched2026=float(100*(np.prod(1+v[12:]/100)-1)),
       q1_2025=float(quarters[0]),q2_2025=float(quarters[1]),
       q3_2025=float(quarters[2]),q4_2025=float(quarters[3]),
       worst2025quarter=float(min(quarters)),
       pos2025quarters=int(sum(q>EPS for q in quarters)),
       train2025_std=float(v[:12].std()),
       first6_2025=float(100*(np.prod(1+v[:6]/100)-1)),
       last6_2025=float(100*(np.prod(1+v[6:12]/100)-1)),
       positive22=int((v>EPS).sum()),negative22=int((v<-EPS).sum()),
       flat22=int((abs(v)<=EPS).sum()),
       positive2026=int((v[12:]>EPS).sum()),
       worst_month=float(v.min()),
       max_monthend_dd=float(100*np.max(1-nav/peak)))

def run_family(e,f):
    op=f.open.to_numpy(float);hi=f.high.to_numpy(float)
    lo=f.low.to_numpy(float);cl=f.close.to_numpy(float)
    tt=f.time.to_numpy(np.int64)
    records=[];monthly=[];ledgers={}
    for fam,pat,side,trend,regime,stopmode,exitmode,hold in TEMPLATES:
        src=e[(e.family==fam)&(e.pattern==pat)]
        src=src[(src.h4_adx<=REGIME[regime][0])&
                (src.h4_eff<=REGIME[regime][1])]
        if side!="both":src=src[src.side==(1 if side=="long" else -1)]
        if trend=="aligned":src=src[src.h4_trend_agrees]
        if len(src)==0:
            print("TEMPLATE_EMPTY",pat,side,regime)
            continue
        for gate in GATES:
            sub=gate_subset(src,gate)
            model=f"{pat}__{regime}__{side}__{trend}__{stopmode}__{exitmode}__{hold}__gate_{gate}"
            capital=np.ones((2,22),float)
            tradecounts=np.zeros(22,np.int32)
            tr=[];last=-1
            for z in sub.itertuples(index=False):
                k=int(z.k)
                if k<=last or k+hold>=len(op) or tt[k+hold-1]-tt[k]!=(hold-1)*60:
                    continue
                side_1=int(z.side)
                risk=(side_1*(op[k]-z.structural_stop) if stopmode=="struct"
                      else (2 if stopmode=="atr2" else 3)*float(z.atr))
                if not (200<=risk<=3500):continue
                if exitmode=="to_mean":target=float(z.mean_target)
                else:target=op[k]+side_1*float(exitmode[:-1])*risk
                reward=side_1*(target-op[k])/risk
                if not (.6<=reward<=5.):continue
                j,net0,reason=replay_one(op,hi,lo,cl,k,side_1,risk,target,hold,0.)
                j5,net5,reason5=replay_one(op,hi,lo,cl,k,side_1,risk,target,hold,5.)
                if (j,reason)!=(j5,reason5):
                    raise AssertionError("Price path depends on modeled slip")
                last=int(j)
                m=pd.Timestamp(int(tt[j]),unit="s",tz="UTC").tz_convert(
                    "Asia/Kolkata").strftime("%Y-%m")
                if m not in MONTH_INDEX:continue
                idx=MONTH_INDEX[m];frac=min(.005,5*risk/op[k])
                if min(1+frac*net0,1+frac*net5)<=0:
                    raise AssertionError("Invalid overlevered replay")
                capital[0,idx]*=(1+frac*net0)
                capital[1,idx]*=(1+frac*net5)
                tradecounts[idx]+=1
                tr.append(dict(family=fam,model=model,entry_unix=int(tt[k]),
                   exit_unix=int(tt[j]),exit_month=m,side=side_1,
                   risk_pts=float(risk),entry_price=float(op[k]),
                   netR_base=float(net0),netR_stress5=float(net5),
                   exit_reason=int(reason),gate=gate))
            v0=100*(capital[0]-1);v5=100*(capital[1]-1)
            a=monthly_stats(v0);b=monthly_stats(v5)
            row=dict(family=fam,model=model,signal_pattern=pat,
               base_regime=regime,direction=side,trend_filter=trend,
               stopmode=stopmode,exitmode=exitmode,hold=hold,gate=gate,
               train_trades=int(tradecounts[:12].sum()),
               all_trades=int(tradecounts.sum()),
               **{"base_"+k:v for k,v in a.items()},
               **{"stress5_"+k:v for k,v in b.items()})
            row["qualifies_from_2025_only"]=bool(
               row["train_trades"]>=20 and b["train2025"]>0 and
               b["first6_2025"]>0 and b["last6_2025"]>0 and
               b["pos2025quarters"]>=3)
            # 2025-only stability score has NO 2026 metric.
            row["train_stability_score"]=(b["worst2025quarter"]+
                .20*b["train2025"]-.15*b["train2025_std"]-
                .3*max(0,-b["worst_month"]))
            records.append(row)
            for i,month in enumerate(MONTHS):
                monthly.append(dict(family=fam,model=model,month_ist=month,
                  base_month_pct=float(v0[i]),stress5_month_pct=float(v5[i]),
                  trade_count=int(tradecounts[i])))
            ledgers[model]=tr
    return pd.DataFrame(records),pd.DataFrame(monthly),ledgers

def select_and_report(d,m,ledgers):
    d.to_csv(OUT/"all_market_gates_2025train_and_2026.csv",index=False)
    m.to_csv(OUT/"every_market_gate_monthly.csv.gz",index=False,compression="gzip")
    winners=[];sel_months=[]
    for fam,g in d.groupby("family"):
        good=g[g.qualifies_from_2025_only]
        if good.empty:
            print("NO_TRAIN_ELIGIBLE_MODELS",fam)
            good=g[g.train_trades>=20]
        if good.empty:good=g
        w=good.sort_values(["train_stability_score","train_trades"],
                 ascending=False,kind="stable").iloc[0].to_dict()
        winners.append(w)
        print("STAGE30_2025_SELECTED",json.dumps(w,default=str))
        checked=g[(g.qualifies_from_2025_only)&(g.stress5_researched2026>0)]
        print("STAGE30_2025_ELIGIBLE_POSITIVE_IN_RESEARCHED_2026",json.dumps(
          dict(family=fam,train_eligible=len(g[g.qualifies_from_2025_only]),
          positive2026=len(checked))))
        ledger=pd.DataFrame(ledgers[w["model"]])
        ledger.to_csv(OUT/(fam.lower()+"_2025selected_trade_ledger.csv"),index=False)
        sel_months.append(m[(m.family==fam)&(m.model==w["model"])])
    pd.DataFrame(winners).to_csv(OUT/"selected_2025_only_results.csv",index=False)
    pd.concat(sel_months).to_csv(OUT/"selected_2025_only_monthly.csv",index=False)
    summary=dict(total_models=len(d),family_models=d.groupby("family").size().to_dict(),
       selected_2025=[dict(family=x["family"],model=x["model"],
       ntrades=x["all_trades"],train_trades=x["train_trades"],
       base22=x["base_net22"],stress5_22=x["stress5_net22"],
       stress5_2025=x["stress5_train2025"],
       stress5_researched2026=x["stress5_researched2026"],
       train_stability_score=x["train_stability_score"]) for x in winners],
       risks=["2026 was previously examined in this research project",
       "2025-only model selection penalizes weak quarters but remains multiple-testing",
       "Stop-first intraminute, next 1-minute entry only",
       "Fundings, live bid-ask, queue priority, and shared account margin unmodeled",
       "No live orders are placed, all strategies disabled in any executable platform"])
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
    print("STAGE30_COMPLETE",json.dumps(summary,default=str))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,_,_,q=read_archive()
    print("INPUT_1MIN_SOURCE",json.dumps(dict(minutes=len(f),missing=q["missing_minutes"])))
    e=prepare_new_events(f)
    e=add_gate_features(e,f)
    e.to_csv(OUT/"signals_with_causal_market_state.csv.gz",
             index=False,compression="gzip")
    d,m,ledgers=run_family(e,f)
    select_and_report(d,m,ledgers)
if __name__=="__main__":main()
