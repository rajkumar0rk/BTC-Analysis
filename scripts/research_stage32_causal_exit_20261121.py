#!/usr/bin/env python3
"""Stage32: pre-2026-checked advanced stop/TP/time-exit optimizer, BTCUSD.

A stricter follow-up to Stage31:
* The TWO 2025-only selected Stage30 signals, and TWO historically hindsight-
  selected Stage31 signals, are held separately. No signal parameters tuned.
* Every exit uses actual 1-minute candles, next open after completed 1H signal.
* Intraminute stop and target ties hit STOP first. Trailing updates based on
  current candle highs/lows take effect only the NEXT minute, ensuring causal
  executable stop management (no using candle's final low/high in past).
* 0.05%/leg taker plus 18% GST on trading fees; 5 BTC points/leg slip and an
  additional 5bps/leg adverse execution stress. Funding, exact contract size,
  bid/ask and shared cross-strategy margin are NOT modeled.
* Optimizes exits using 2025 ONLY, then reports Jan-Oct 2026, which is not a
  pristine untouched holdout because the entire history was studied before.
* November source remains partial; one-month return is NOT a complete result.
* No live orders / do not promote fitted candidates to real-money trading.
"""
from pathlib import Path
import itertools
import json
import numpy as np
import pandas as pd
from numba import njit
from research_every_candle_200 import read_archive,FEE,SLIPPAGE
from research_stage28_new_reversion_range_20261121 import prepare_new_events
from research_stage30_causal_market_gates_20261121 import add_gate_features,gate_subset

OUT=Path("analysis/stage32_mr_range_dynamic_exit_20261121")
MONTHS=pd.period_range("2025-01","2026-11",freq="M").astype(str).tolist()
MI={m:i for i,m in enumerate(MONTHS)}
TRAIN_END=12
TEST_END=22
# Frozen hypotheses: these signal conditions are not optimized in Stage32.
SOURCES={
 "MR_2025SELECTED":dict(pattern="mr_bollinger_reclaim_h1",regime=(32.,.5),
     direction=1,gate="channel_no_break",initial_stop_atr=3.,target_mode="3R",
     holding_minutes=1920,previous_stress5_22=2.988141284383805),
 "RANGE_2025SELECTED":dict(pattern="range_touch_48",regime=(25.,.35),
     direction=0,gate="none",initial_stop_atr=2.,target_mode="3R",
     holding_minutes=1920,previous_stress5_22=2.8493733802704035),
 "MR_POSTHOC":dict(pattern="mr_bollinger_reentry",regime=(45.,.7),
     direction=1,gate="drift3_atr_le1p5",initial_stop_atr=3.,target_mode="to_mean",
     holding_minutes=1920,previous_stress5_22=2.661547929669439),
 "RANGE_POSTHOC":dict(pattern="range_touch_48",regime=(45.,.7),
     direction=0,gate="range_mid50pct",initial_stop_atr=3.,target_mode="to_mean",
     holding_minutes=1920,previous_stress5_22=8.26318615321322),
}
STOPS=(2.,2.5,3.,3.5,4.)
TARGETS=("to_mean","1.5R","2R","3R","4R")
HOLDS=(480,960,1920,2880)
LOCKS=("none","breakeven_at_1R","lock_half_at_1p5R",
       "trail_1p5R_at_1R","trail_2R_at_1R")
# fixed exit and lock templates for all source families
EXTRA_BPS=(0.,5.)
EPS=1e-8

@njit(cache=True)
def replay_causal_exit(O,H,L,C,k,side,risk,target,hold,lock_mode):
    """Prices from 1m OHLC, but stop update is always effective NEXT minute.

    If any candle touches both the old stop and target, stop wins. We
    conservatively never grant an in-candle profit stop triggered by an
    in-candle high/low whose ordering is unknown.
    """
    entry=O[k]
    stop=entry-side*risk
    top=entry
    bottom=entry
    mid=C[k]
    reason=2
    jexit=k+hold-1
    for j in range(k,k+hold):
        stopped=(L[j]<=stop) if side==1 else (H[j]>=stop)
        target_hit=(H[j]>=target) if side==1 else (L[j]<=target)
        if stopped:
            mid=min(O[j],stop) if side==1 else max(O[j],stop)
            reason=0
            jexit=j
            break
        if target_hit:
            mid=target
            reason=1
            jexit=j
            break
        # No exit in this bar; use its realized favorable extrema to
        # update a live executable stop for the following 1-minute bar.
        if H[j]>top:top=H[j]
        if L[j]<bottom:bottom=L[j]
        favorable=(top-entry) if side==1 else (entry-bottom)
        candidate=stop
        if lock_mode==1 and favorable>=risk:
            candidate=entry
        elif lock_mode==2 and favorable>=1.5*risk:
            candidate=entry+side*.5*risk
        elif lock_mode==3 and favorable>=risk:
            candidate=(top-1.5*risk) if side==1 else (bottom+1.5*risk)
            candidate=max(candidate,entry) if side==1 else min(candidate,entry)
        elif lock_mode==4 and favorable>=risk:
            candidate=(top-2.*risk) if side==1 else (bottom+2.*risk)
            candidate=max(candidate,entry) if side==1 else min(candidate,entry)
        if side==1:
            if candidate>stop:stop=candidate
        else:
            if candidate<stop:stop=candidate
        mid=C[j]
    return jexit,mid,reason

def cost_net_r(entry,exit_price,side,risk,extra_bps):
    entry_fill=entry+side*(SLIPPAGE+extra_bps*entry/10000.)
    exit_fill=exit_price-side*(SLIPPAGE+extra_bps*exit_price/10000.)
    return (side*(exit_fill-entry_fill)-FEE*(entry_fill+exit_fill))/risk

def indicators_and_events(f):
    raw=add_gate_features(prepare_new_events(f),f)
    seen={}
    for group,setting in SOURCES.items():
        rows=raw[(raw.pattern==setting["pattern"])&
                (raw.h4_adx<=setting["regime"][0])&
                (raw.h4_eff<=setting["regime"][1])]
        if setting["direction"]!=0:rows=rows[rows.side==setting["direction"]]
        rows=gate_subset(rows,setting["gate"])
        if rows.empty:raise AssertionError("Missing signals for "+group)
        seen[group]=rows.sort_values("k",kind="stable").reset_index(drop=True)
    return seen

def month_nav_and_stats(v):
    a=np.asarray(v[:22],float)
    q=np.cumprod(1+a/100.)
    peak=np.maximum.accumulate(np.r_[1.,q])[1:]
    q25=np.cumprod(1+a[:12]/100.)
    peak25=np.maximum.accumulate(np.r_[1.,q25])[1:]
    qs=[100.*(np.prod(1+a[i:i+3]/100)-1) for i in (0,3,6,9)]
    return dict(total_pct=float(100*(q[-1]-1)),
       train2025_pct=float(100*(q25[-1]-1)),
       reviewed2026_pct=float(100*(np.prod(1+a[12:]/100.)-1)),
       win22=int((a>EPS).sum()),loss22=int((a<-EPS).sum()),
       flat22=int((abs(a)<=EPS).sum()),win2026=int((a[12:]>EPS).sum()),
       worst_month_pct=float(a.min()),
       train_maxdd_pct=float(100*np.max(1-q25/peak25)),
       worst_2025_quarter_pct=float(min(qs)),
       positive_2025_quarters=int(sum(x>EPS for x in qs)),
       first6_2025_pct=float(100*(np.prod(1+a[:6]/100)-1)),
       second6_2025_pct=float(100*(np.prod(1+a[6:12]/100)-1)),
       november_partial_pct=float(v[22]))
       
def backtest(f,events):
    O=f.open.to_numpy(float);H=f.high.to_numpy(float)
    L=f.low.to_numpy(float);C=f.close.to_numpy(float)
    TS=f.time.to_numpy(np.int64)
    results=[];selected_months=[];selected_ledgers={};selected_summary=[]
    for group,rows in events.items():
        src=SOURCES[group]
        ncases=0
        frozen=None
        all_runs=[]
        for stop_atr,mode,hold,lock in itertools.product(
            STOPS,TARGETS,HOLDS,LOCKS):
            variant=f"atr{stop_atr:g}_{mode}_{hold}min_{lock}"
            nav=np.ones((2,23),float)
            trades_per_month=np.zeros(23,np.int32)
            last=-1
            ledger=[]
            for z in rows.itertuples(index=False):
                k=int(z.k)
                if k<=last or k+hold>=len(O) or TS[k+hold-1]-TS[k]!=(hold-1)*60:
                    continue
                entry=O[k]
                side=int(z.side)
                risk=float(stop_atr*z.atr)
                if risk<200 or risk>3500:continue
                if mode=="to_mean":
                    target=float(z.mean_target)
                else:
                    target=entry+side*float(mode[:-1])*risk
                if not np.isfinite(target):continue
                reward=side*(target-entry)/risk
                if reward<.6 or reward>5.:continue
                j,exit_mid,reason=replay_causal_exit(O,H,L,C,k,side,risk,target,
                     hold,LOCKS.index(lock))
                last=int(j)
                month=pd.Timestamp(int(TS[j]),unit="s",tz="UTC").tz_convert(
                    "Asia/Kolkata").strftime("%Y-%m")
                if month not in MI:continue
                mi=MI[month]
                w=min(.005,5*risk/entry)
                r0=cost_net_r(entry,exit_mid,side,risk,EXTRA_BPS[0])
                r5=cost_net_r(entry,exit_mid,side,risk,EXTRA_BPS[1])
                if 1+w*min(r0,r5)<=0:raise AssertionError("Liquidation")
                nav[0,mi]*=(1+w*r0)
                nav[1,mi]*=(1+w*r5)
                trades_per_month[mi]+=1
                ledger.append(dict(cohort=group,model=variant,
                    entry_unix=int(TS[k]),exit_unix=int(TS[j]),
                    month_ist=month,side=side,reason=int(reason),
                    entry_price=float(entry),exit_mid=float(exit_mid),
                    risk_points=float(risk),R_to_target=float(reward),
                    R_net_base=float(r0),R_net_extra5bps=float(r5)))
            v0=(nav[0]-1.)*100.
            v5=(nav[1]-1.)*100.
            s0=month_nav_and_stats(v0)
            s5=month_nav_and_stats(v5)
            d=dict(cohort=group,variant=variant,stop_atr=stop_atr,target=mode,
              maxhold_minutes=hold,causal_lock_mode=lock,
              historical_signal_count=len(rows),
              trades22=int(trades_per_month[:22].sum()),
              train_trades=int(trades_per_month[:12].sum()),
              reviewed2026_trades=int(trades_per_month[12:22].sum()),
              nov_partial_trades=int(trades_per_month[22]),
              **{f"base_{key}":val for key,val in s0.items()},
              **{f"extra5_{key}":val for key,val in s5.items()})
            # 2025-only objective; require positive net after full extra 5bps
            # stress in BOTH halves of 2025 and minimum observations.
            d["train_eligible"]=bool(
                d["train_trades"]>=15 and s5["train2025_pct"]>0 and
                s5["first6_2025_pct"]>0 and s5["second6_2025_pct"]>0)
            d["train_score"]=(s5["train2025_pct"]-.6*s5["train_maxdd_pct"]+
                              .12*s5["positive_2025_quarters"]+
                              .06*min(s5["worst_2025_quarter_pct"],0))
            results.append(d)
            all_runs.append((d,v0,v5,ledger))
            if (stop_atr==src["initial_stop_atr"] and
                mode==src["target_mode"] and hold==src["holding_minutes"] and
                lock=="none"):
                frozen=d
                if abs(s5["total_pct"]-src["previous_stress5_22"])>1e-5:
                    raise AssertionError("Stage31 or Stage30 original parity failed: "+
                          group+" got "+str(s5["total_pct"])+" vs "+
                          str(src["previous_stress5_22"]))
                print("BASELINE_STAGE31_OR_STAGE30_PARITY",json.dumps(d))
            ncases+=1
        if frozen is None:raise AssertionError("No baseline replay "+group)
        candidates=[a for a in all_runs if a[0]["train_eligible"]]
        if not candidates:
            candidates=[a for a in all_runs if a[0]["train_trades"]>=15]
        if not candidates:raise AssertionError("No candidate with adequate trades")
        best=max(candidates,key=lambda a:(a[0]["train_score"],
                                            a[0]["train_trades"]))
        selected_months.append((group,"selected_2025",best[1],best[2]))
        selected_months.append((group,"frozen_prior",next(a for a in all_runs
             if a[0]["variant"]==frozen["variant"])[1],
               next(a for a in all_runs if a[0]["variant"]==frozen["variant"])[2]))
        selected_ledgers[group]=best[3]
        selected_summary.append(best[0])
        print("2025_ONLY_EXIT_SELECTION",json.dumps(best[0]))
        print("2025_ONLY_MINUS_FROZEN",json.dumps(dict(cohort=group,
          selected_train5=best[0]["extra5_train2025_pct"],
          frozen_train5=frozen["extra5_train2025_pct"],
          selected_reviewed2026=best[0]["extra5_reviewed2026_pct"],
          frozen_reviewed2026=frozen["extra5_reviewed2026_pct"])))
        print("FAMILY_COMPLETE",json.dumps(dict(group=group,cases=ncases,
           train_eligible=len([x for x in all_runs if x[0]["train_eligible"]]))))
    out=pd.DataFrame(results)
    out.to_csv(OUT/"full_exit_grid.csv",index=False)
    mrows=[]
    for group,label,v0,v5 in selected_months:
        for i,month in enumerate(MONTHS):
            mrows.append(dict(cohort=group,selection_type=label,
               month_ist=month,base_pct=float(v0[i]),extra5_pct=float(v5[i]),
               incomplete_november=bool(i==22)))
    pd.DataFrame(mrows).to_csv(OUT/"frozen_vs_2025selected_monthly.csv",index=False)
    for group,ledger in selected_ledgers.items():
        pd.DataFrame(ledger).to_csv(OUT/(group.lower()+"_selected_trade_ledger.csv"),index=False)
    summary=dict(
      variants_tested=len(results),
      families=out.groupby("cohort").size().to_dict(),
      selected_from_2025_only=[dict(
        cohort=d["cohort"],variant=d["variant"],
        trades22=d["trades22"],train_trades=d["train_trades"],
        return22_after5bps=d["extra5_total_pct"],
        train2025_after5bps=d["extra5_train2025_pct"],
        reviewed2026_after5bps=d["extra5_reviewed2026_pct"],
        winning_months=d["extra5_win22"],
        november_partial=d["extra5_november_partial_pct"]
      ) for d in selected_summary],
      sample_22_months="Jan 2025-Oct 2026",
      november_partial_through="Nov 18, 2026",
      historically_researched_2026_not_pristine_holdout=True,
      funding_spread_liquidation_shared_margin_unmodeled=True,
      no_live_orders=True)
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("STAGE32_1M_EXIT_OPTIMIZATION_COMPLETE",json.dumps(summary))
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,_,_,q=read_archive()
    print("STAGE32_BTC_SOURCE",json.dumps(dict(candles=len(f),
         missing_minutes=q["missing_minutes"],first=q["first_utc"],
         last=q["last_utc"])))
    e=indicators_and_events(f)
    backtest(f,e)
if __name__=="__main__":
    main()
