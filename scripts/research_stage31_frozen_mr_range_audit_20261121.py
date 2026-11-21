#!/usr/bin/env python3
"""Stage31 frozen replay and November-partial diagnostic.
Two hypotheses were selected AFTER examining 2026, so retrospective. They are post-hoc
historical discoveries, NOT 2025-selected candidates or forward validation.

Never place actual futures orders. Uses complete 1H/4H features and 1m
next-open fills; exact same 1m stop-first simulator as Stage27/30.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive
from research_stage28_new_reversion_range_20261121 import prepare_new_events
from research_stage30_causal_market_gates_20261121 import add_gate_features, gate_subset
from research_stage27_meanreversion_range_20261121 import replay_one

OUT=Path("analysis/stage31_frozen_mr_range_20261121")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
# Historical hindsight choice, frozen before this replay.
SPECS={
 "MEAN_REVERSION":{
   "pattern":"mr_bollinger_reentry","side":"long",
   "max4h_adx":45.,"max4h_eff":.70,
   "guard":"drift3_atr_le1p5", "stop_atr":3.,
   "exit":"to_mean", "maxhold":1920,
   "stage30_stress5_expected_net22":2.661547929669439},
 "RANGE_TRADING":{
   "pattern":"range_touch_48","side":"both",
   "max4h_adx":45.,"max4h_eff":.70,
   "guard":"range_mid50pct", "stop_atr":3.,
   "exit":"to_mean", "maxhold":1920,
   "stage30_stress5_expected_net22":8.26318615321322},
}
COSTS=(0,2,5,10)
REPORT_MONTHS=MONTHS+["2026-11"]

def stats(v):
    a=np.asarray(v,float)
    return dict(net_return_pct=float(100*(np.prod(1+a/100)-1)),
         positive_months=int((a>1e-8).sum()),
         losing_months=int((a< -1e-8).sum()),
         flat_months=int((abs(a)<=1e-8).sum()),
         worst_month_pct=float(a.min()))

def replay_family(f,all_events,label,config):
    O=f.open.to_numpy(float);H=f.high.to_numpy(float)
    L=f.low.to_numpy(float);C=f.close.to_numpy(float)
    T=f.time.to_numpy(np.int64)
    e=all_events[(all_events.pattern==config["pattern"])&
                 (all_events.h4_adx<=config["max4h_adx"])&
                 (all_events.h4_eff<=config["max4h_eff"])]
    if config["side"]=="long":e=e[e.side==1]
    if config["side"]=="short":e=e[e.side==-1]
    e=gate_subset(e,config["guard"])
    if not e.k.is_monotonic_increasing:
        e=e.sort_values("k",kind="stable")
    nav=np.ones((len(COSTS),len(REPORT_MONTHS)),float)
    count=np.zeros(len(REPORT_MONTHS),int)
    ledger=[];last=-1
    skip_tail=0
    for z in e.itertuples(index=False):
        k=int(z.k);hold=int(config["maxhold"])
        if k<=last:continue
        if k+hold>=len(O) or T[k+hold-1]-T[k]!=(hold-1)*60:
            skip_tail+=1
            continue
        side=int(z.side)
        risk=float(config["stop_atr"])*float(z.atr)
        if not (200<=risk<=3500):continue
        target=float(z.mean_target)
        reward=side*(target-float(O[k]))/risk
        if not (.6<=reward<=5.):continue
        results=[replay_one(O,H,L,C,k,side,risk,target,hold,extra)
                 for extra in COSTS]
        first=results[0]
        if any((r[0],r[2])!=(first[0],first[2]) for r in results):
            raise AssertionError("Cost changed exit candle/reason")
        last=int(first[0])
        month=pd.Timestamp(int(T[last]),unit="s",tz="UTC").tz_convert(
          "Asia/Kolkata").strftime("%Y-%m")
        if month not in REPORT_MONTHS:continue
        idx=REPORT_MONTHS.index(month)
        fraction=min(.005,5*risk/O[k])
        for cidx,cost in enumerate(COSTS):
            netR=results[cidx][1]
            if 1+fraction*netR<=0:raise AssertionError("Invalid size")
            nav[cidx,idx]*=1+fraction*netR
        count[idx]+=1
        ledger.append(dict(strategy=label,entry_utc=str(pd.to_datetime(
         T[k],unit="s",utc=True)),exit_utc=str(pd.to_datetime(
         T[last],unit="s",utc=True)),exit_month_ist=month,
         side="LONG" if side==1 else "SHORT",risk_points=risk,
         target_atr_risk_ratio=reward,entry_mid=float(O[k]),
         exit_reason=("STOP" if first[2]==0 else "TARGET" if first[2]==1 else "TIMEOUT"),
         **{f"net_R_extra_{cost}bps":float(results[j][1])
                    for j,cost in enumerate(COSTS)}))
    print("STAGE31_TRADE_AUDIT",json.dumps(dict(strategy=label,
         admissible_events=len(e),realized_trades=len(ledger),
         unclosed_tail_excluded=skip_tail,jan_oct_2026_trades=
         sum(x["exit_month_ist"].startswith("2026") and
         x["exit_month_ist"]!="2026-11" for x in ledger),
         partial_nov_2026_trades=int(count[-1]))))
    pd.DataFrame(ledger).to_csv(OUT/(label.lower()+"_trade_ledger.csv"),index=False)
    rows=[]
    for costidx,cost in enumerate(COSTS):
        for i,month in enumerate(REPORT_MONTHS):
            rows.append(dict(strategy=label,month_ist=month,
                 additional_adverse_bps_per_side=cost,
                 monthly_return_pct=float(100*(nav[costidx,i]-1)),
                 trade_count=int(count[i]),
                 partial_month=month=="2026-11"))
    return pd.DataFrame(rows)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,_,_,quality=read_archive()
    print("FROZEN_SOURCE",json.dumps(dict(
      candles=len(f),missing_minutes=quality["missing_minutes"],
      first=quality["first_utc"],last=quality["last_utc"])))
    events=add_gate_features(prepare_new_events(f),f)
    results=[replay_family(f,events,label,config)
            for label,config in SPECS.items()]
    monthly=pd.concat(results,ignore_index=True)
    monthly.to_csv(OUT/"strategy_22_months_and_partial_november.csv",index=False)
    summary={}
    for label,config in SPECS.items():
        v={}
        for cost in COSTS:
            m=monthly[(monthly.strategy==label)&
                  (monthly.additional_adverse_bps_per_side==cost)]
            v22=m[m.month_ist!="2026-11"].monthly_return_pct.to_numpy()
            if len(v22)!=22:raise AssertionError("22 month mismatch")
            tr=m[m.month_ist!="2026-11"].trade_count.sum()
            nov=m[m.month_ist=="2026-11"].iloc[0]
            v[str(cost)+"bps"]=dict(
                all22=stats(v22),train2025=stats(v22[:12]),
                researched2026=stats(v22[12:]),
                trades22=int(tr),
                november_partial_return_pct=float(nov.monthly_return_pct),
                november_partial_trades=int(nov.trade_count))
        observed=v["5bps"]["all22"]["net_return_pct"]
        if abs(observed-config["stage30_stress5_expected_net22"])>0.00002:
            raise AssertionError("Independent Stage30 parity failed for "+label+
               f" observed {observed}, expected {config['stage30_stress5_expected_net22']}")
        summary[label]=v
        print("FROZEN_VERIFIED",json.dumps(dict(name=label,results=v)))
    m=monthly[(monthly.additional_adverse_bps_per_side==5)&
              (monthly.month_ist!="2026-11")]
    pivot=m.pivot(index="month_ist",columns="strategy",values="monthly_return_pct")
    pivot=pivot.reindex(MONTHS)
    if pivot.isna().any().any():raise AssertionError("missing portfolio months")
    equal=.5*pivot.MEAN_REVERSION.to_numpy()+.5*pivot.RANGE_TRADING.to_numpy()
    summary["synthetic_50_50_stress5"]=dict(
       all22=stats(equal),train2025=stats(equal[:12]),
       researched2026=stats(equal[12:]))
    (OUT/"frozen_verification_summary.json").write_text(
        json.dumps(summary,indent=2)+"\n")
    print("STAGE31_FROZEN_AUDIT_SUCCESS",json.dumps(summary))
if __name__=="__main__":main()
