#!/usr/bin/env python3
"""Frozen chronological November audit of 2025-selected Step8 kNN fallback.

Every 15 full IST weekdays gets one trade. KNN fallback decisions use ONLY
previously closed fallback days. Step6 event-side learning uses ONLY previous
closed event days. Neither ever inspects current/future daily outcome to
decide the current entry. This November period was previously researched.
"""
from pathlib import Path
import json

import numpy as np
import pandas as pd

import research_btc_every_weekday_reset_step1 as base
import research_btc_daily_causal_regime_step5 as regime
import research_btc_daily_online_direction_step6 as online
import research_btc_daily_causal_neighbors_step8 as step8
import research_btc_every_weekday_exit_protection_step3 as protection
import audit_btc_daily_fallback_regime_november_2026 as nov

OUT=Path("analysis/btc_daily_causal_neighbors_step8/november_audit")
DAYS=nov.NDAYS
COUNT=15
assert len(DAYS)==COUNT

def feature_one(m,index,side,hour=21):
    """Exact Step8 fixed-scale vector, strictly prior to this 1m OPEN."""
    op=m.open.to_numpy(float)
    close=m.close.to_numpy(float)
    hi=m.high.to_numpy(float)
    lo=m.low.to_numpy(float)
    v=m.volume.to_numpy(float)
    i=int(index)
    pclose=float(close[i-1])
    r5=pclose/float(op[i-5])-1
    r15=pclose/float(op[i-15])-1
    r60=pclose/float(op[i-60])-1
    r240=pclose/float(op[i-240])-1
    ownvol=float(np.sum(v[i-5:i]))
    prev=v[i-105:i-5].reshape(20,5).sum(axis=1)
    rvol=ownvol/float(np.mean(prev)) if np.mean(prev)>0 else 1.
    up=float(np.max(hi[i-60:i]))
    bottom=float(np.min(lo[i-60:i]))
    span60=up-bottom
    pos=(pclose-bottom)/span60 if span60>0 else .5
    range60=span60/float(op[i])
    span15=float(np.max(hi[i-15:i])-np.min(lo[i-15:i]))
    oldspans=np.array([float(
        np.max(hi[i-15*(z+2):i-15*(z+1)])-
        np.min(lo[i-15*(z+2):i-15*(z+1)]))
        for z in range(6)
    ])
    oldmed=float(np.median(oldspans))
    ratio=span15/oldmed if oldmed>0 else 1.
    s=float(side)
    vct=np.array([
        s*r5/.0015,s*r15/.003,s*r60/.007,s*r240/.015,
        (rvol-1.)/1.2,s*(pos-.5)*2,range60/.01,
        (ratio-1.)/1.5,(hour-20.)/2.,
        1. if np.sign(r5)==np.sign(r60) else -1.
    ],dtype=float)
    return np.clip(vct,-3.,3.),rvol,r5,r60

def fixed_kNN_choice(hist_features,hist_payoffs,current):
    # Step8 exact: last 45 PREVIOUS fallback days, k36 nearest,
    # weighted WIN fraction; select only if exceeds baseline by >0.05.
    assert len(hist_features)==len(hist_payoffs)
    prior=np.asarray(hist_features[-45:],dtype=float)
    payoffs=np.asarray(hist_payoffs[-45:],dtype=float)
    if len(prior)<12:return 0,0
    dist=np.sqrt(np.sum((prior-current[None,:])**2,axis=1))
    near=np.argsort(dist,kind="mergesort")[:min(36,len(dist))]
    w=1./(.35+dist[near])
    w=w/np.sum(w)
    scores=np.sum((payoffs[near,:4]>0)*w[:,None],axis=0)
    arm=int(np.argmax(scores))
    if arm and scores[arm]>scores[0]+.05:
        return arm,len(near)
    return 0,len(near)

def analyze(x):
    eq=np.cumprod(1+x)
    pk=np.maximum.accumulate(np.r_[1.,eq])[1:]
    return dict(
        trades=int(len(x)),profitable_days=int(np.sum(x>0)),
        losing_days=int(np.sum(x<0)),
        winning_day_pct=round(float(100*np.mean(x>0)),3),
        net_account_return_pct=round(float(100*(eq[-1]-1)),6),
        max_closed_dd_pct=round(float(100*np.max(1-eq/pk)),6),
        worst_day_pct=round(float(100*np.min(x)),6))

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    historic=base.load()
    old,mask,evtvec,fallvec,ev_base,evhist,reference=step8.initial_dataset(historic)
    # All history arrays end in Oct 2026; they exclude November.
    event_past=list(old["event"][1][0][~mask,:])
    event_context=list(old["eventimpulse"][~mask])
    fallback_past_features=list(fallvec[mask])
    fallback_past_returns=list(old["fallback"][1,"E"][0][mask,:4])
    if len(event_past)!=260 or len(fallback_past_features)!=217:
        raise AssertionError("Historical source labels changed")

    m=nov.load_with_nov()
    starts,hours,base_sides,isfallback=nov.determine_entries(m,"follow5")
    if len(starts)!=15 or int(np.sum(~isfallback))!=9 or int(np.sum(isfallback))!=6:
        raise AssertionError("Incomplete November entry calendar")
    configs,ci=regime.build_cfg()
    o=m.open.to_numpy(float);hi=m.high.to_numpy(float);lo=m.low.to_numpy(float)
    # Precompute exact same eventual intrabar sequence for each direction.
    long=protection.run_exit_grid(o,hi,lo,starts,hours,
        np.ones(COUNT,dtype=np.int8),configs,base.COST,base.SLIP)
    short=protection.run_exit_grid(o,hi,lo,starts,hours,
        -np.ones(COUNT,dtype=np.int8),configs,base.COST,base.SLIP)
    outcome_by_sign={1:long,-1:short}

    def exact(d,side,recipe,fee_mode):
        r,c,g,w,t=outcome_by_sign[int(side)]
        i=ci[recipe]
        mi=base.MODES.index(fee_mode)
        return (float(r[d,i,mi]),float(c[d,i,mi]),float(g[d,i]),
                int(w[d,i]),int(t[d,i]))
    def sign(v):return 1 if v>=0 else -1

    event_choice=np.zeros(COUNT,dtype=np.int8)
    fallback_choice=np.zeros(COUNT,dtype=np.int8)
    comparable=np.zeros(COUNT,dtype=np.int16)
    thresholds=np.zeros(COUNT)
    pricesides=np.zeros((COUNT,4),dtype=np.int8)
    for d in range(COUNT):
        i=int(starts[d])
        f,rv,r5,r60=feature_one(m,i,
                 base_sides[d],int(hours[d]))
        thresholds[d]=rv
        if not isfallback[d]:
            impulse=abs(r5)>=.0015
            last=np.asarray(event_past[-30:],dtype=float)
            lastctx=np.asarray(event_context[-30:],dtype=bool)
            matches=last[lastctx==impulse]
            comparable[d]=len(matches)
            if len(matches)>=12:
                ave=np.mean(matches,axis=0)
                if ave[1]>ave[0]+.0003:
                    event_choice[d]=1
            # Save only AFTER choosing day d's event side, from the
            # same 1m price/fee assumptions, ready for future days.
            faded=float(exact(d,int(base_sides[d]),"lock050","scalper_offer")[0])
            followed=float(exact(d,-int(base_sides[d]),"lock050","scalper_offer")[0])
            event_past.append([faded,followed])
            event_context.append(bool(impulse))
        else:
            # All fallback variants refer to 21h. Decisions BEFORE entry.
            vec,rv,r5,r60=feature_one(m,i,sign(r5),21)
            thresholds[d]=rv
            fallback_choice[d],comparable[d]=fixed_kNN_choice(
                fallback_past_features,fallback_past_returns,vec)
            pricesides[d]=np.array([sign(r5),-sign(r5),sign(r60),-sign(r60)])
            recipe="trail075" if rv>=1.25 else "trail050"
            fallback_past_features.append(vec)
            # Full shadow outcomes become known only after this day.
            fallback_past_returns.append([
                exact(d,pricesides[d,a],recipe,"scalper_offer")[0]
                for a in range(4)
            ])
    # No future day information was referenced in these online choices.
    report=[];allrows=[]
    for version in ("STEP6_original","STEP8_kNN"):
        for fee_mode in base.MODES:
            daily_returns=[]
            for d,day in enumerate(DAYS):
                is_fall=bool(isfallback[d])
                if not is_fall:
                    sd=(-int(base_sides[d]) if event_choice[d] else int(base_sides[d]))
                    recipe="lock050"
                    name="FOLLOW5" if event_choice[d] else "FADE5"
                else:
                    arm=int(fallback_choice[d]) if version=="STEP8_kNN" else 0
                    sd=int(pricesides[d,arm])
                    recipe="trail075" if thresholds[d]>=1.25 else "trail050"
                    name=old.FALL_ARMS[arm]
                p,c,g,w,t=exact(d,sd,recipe,fee_mode)
                daily_returns.append(p)
                allrows.append(dict(
                    model=version,cost_model=fee_mode,
                    day_ist=day.strftime("%Y-%m-%d"),
                    event_or_fallback="FALLBACK" if is_fall else "EVENT",
                    hour_ist=int(hours[d]),side="LONG" if sd>0 else "SHORT",
                    chosen_arm=name,prior_comparable_cases=int(comparable[d]),
                    preentry_vol_ratio=round(float(thresholds[d]),5),
                    account_net_pct=round(100*p,6),
                    fee_gst_btc_points=round(c,4),
                    gross_points=round(g,4),
                    reason="TP" if w==1 else ("STOP" if w==2 else "TIMEOUT"),
                    hold_minutes=t))
            z=analyze(np.asarray(daily_returns,dtype=float))
            z.update(model=version,cost_model=fee_mode,
                 event_direction_follow_days=int(np.sum(event_choice!=0)),
                 fallback_kNN_nonbaseline_days=int(np.sum(
                      (fallback_choice!=0)&isfallback)) if version=="STEP8_kNN" else 0,
                 event_days=int(np.sum(~isfallback)),
                 mandatory_fallback_days=int(np.sum(isfallback)))
            report.append(z)
    summaries=pd.DataFrame(report)
    ledger=pd.DataFrame(allrows)
    if len(ledger)!=15*4 or not summaries.trades.eq(15).all():
        raise AssertionError("November daily coverage changed")
    ref=summaries[(summaries.model=="STEP6_original")&
       (summaries.cost_model=="scalper_offer")].iloc[0]
    if int(ref.profitable_days)!=10 or abs(float(ref.net_account_return_pct)-.019249)>.00011:
        raise AssertionError("Step6 November replay parity failure "+str(ref.to_dict()))
    summaries.to_csv(OUT/"step6_vs_step8_fixed_15days_two_cost_models.csv",index=False)
    ledger.to_csv(OUT/"all_15_november_btc_trade_replays.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(dict(
        date_window="2026-11-02 through 2026-11-20 full IST weekdays",
        sample_days=15,
        frozen_online_policy="Step8 extended10, last45 fallback days k36 neighbors, distance weighted win fraction, 0.05 win probability margin; event side original Step6 online_impulse5",
        model_selected_only_using_2025=True,
        November_was_previously_researched=True,
        results=report,
        caveats=[
            "Later 15-day period is not untouched: earlier steps already inspected it",
            "Historical offer activation and real fills not verified; no real orderbook, funding, latency or liquidation",
            "Small sample and prior research optimization forbid live-ready claims"]
    ),indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
        "# Step8 November audit: fixed policy, one BTC trade every weekday",
        "","Identical Step6 event-side online learner; Step8 changes fallback direction based on completed PRIOR fallback days only, with k36 nearest pre-entry volume/price features.",
        "","## Summary",
        summaries.to_markdown(index=False),
        "","## All 15 daily trades for both cost assumptions",
        ledger.to_markdown(index=False),
        "","## Caution",
        "November has previously been examined in past BTC research; this is not a pristine blind test, and 15 days is insufficient for a durable conclusion."
    ])+"\n")
    print("STEP8_NOVEMBER_FROZEN "+json.dumps(report,sort_keys=True),flush=True)
    print("STEP8_NOVEMBER_COMPLETE",flush=True)

if __name__=="__main__":
    run()
