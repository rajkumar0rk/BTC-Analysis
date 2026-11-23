#!/usr/bin/env python3
"""Step6: online, prior-day-only BTC direction/clock choice with one weekday trade.

Event: first 18/19/20 IST RVOL >=1.5x. Choose fade/follow prior 5m.
Fallback: 21/22 IST, one of follow/fade previous 5m or previous 60m.
The online policy never consumes day >=d to choose arm for day d. Baseline B
and E side/exit implementations must reproduce exact prior 477-day results.
"""
from pathlib import Path
from itertools import product
import json

import numpy as np
import pandas as pd

import research_btc_every_weekday_reset_step1 as base
import research_btc_every_weekday_adaptive_step2 as adaptive
import research_btc_every_weekday_exit_protection_step3 as protection
import research_btc_daily_fallback_regime_step4 as previous
import research_btc_daily_causal_regime_step5 as regime

OUT=Path("analysis/btc_daily_online_direction_step6")
DAYS=base.DAYS
NUM_DAYS=len(DAYS)
MODES=base.MODES
EVENT_MODES=("fixed","online_global","online_volume2","online_impulse5")
FALLBACK_MODES=("fixed","online_global","online_align5_60","online_volume1p25")
WINDOWS=(30,60,120)
SCORES=("net","win","risk")
MARGINS=("none","conservative")
EXIT_PROFILES=("B","E")
FALL_ARMS=tuple(f"{hour}_{rule}" for hour in (21,22) for rule in
                ("follow5","fade5","follow60","fade60"))
EXPECTED=len(EVENT_MODES)*len(FALLBACK_MODES)*len(WINDOWS)*len(SCORES)*len(MARGINS)*len(EXIT_PROFILES)*len(MODES)
assert EXPECTED==1152 and NUM_DAYS==477

def retrieve(m):
    starts,_,_=base.prepare(m)
    features=adaptive.build_completed_candle_features(m,starts)
    hours,signs,fall=adaptive.choose_all_policy_entries(features)
    pol=adaptive.POLICIES.index(("vol5_fade","us_only","follow60"))
    event_hours=hours[pol].astype(int)
    event_signs=signs[pol].astype(int)
    isfallback=fall[pol].astype(bool)
    assert np.sum(isfallback)==217 and np.sum(~isfallback)==260
    cfg,cidx=regime.build_cfg()
    pre=previous.cache_entry_exits(m,starts,event_hours,event_signs,cfg)
    op=m.open.to_numpy(float);hi=m.high.to_numpy(float);lo=m.low.to_numpy(float)
    # Opposite hypothetical event side is replayed on same fixed first-trigger hour.
    event_opp=protection.run_exit_grid(op,hi,lo,
        starts[np.arange(NUM_DAYS),event_hours],event_hours,-event_signs,
        cfg,base.COST,base.SLIP)
    # Event candidate arms: 0=existing FADE5, 1=counterfactual FOLLOW5.
    event={}
    for mi in range(2):
        vals=[]
        for candidate in (pre["event"],event_opp):
            r,c,g,w,t=candidate
            ix=cidx["lock050"]
            vals.append((r[:,ix,mi],c[:,ix,mi],g[:,ix],w[:,ix],t[:,ix]))
        event[mi]=tuple(np.stack([v[k] for v in vals],axis=1) for k in range(5))

    f21=regime.features(m,starts)
    # Current event preentry data and fallback at 21:00 context are available
    # before selecting either a 21:00 or 22:00 fallback arm.
    eventvol=np.zeros(NUM_DAYS,dtype=bool)
    eventimpulse=np.zeros(NUM_DAYS,dtype=bool)
    align=np.zeros(NUM_DAYS,dtype=bool)
    highvol=np.zeros(NUM_DAYS,dtype=bool)
    fall_signs=np.zeros((NUM_DAYS,len(FALL_ARMS)),dtype=np.int8)
    arms_meta=[]
    for di in range(NUM_DAYS):
        h=event_hours[di]
        evt=features[(di,int(h))]
        eventvol[di]=evt["volume5_ratio"]>=2.0
        eventimpulse[di]=abs(evt["r5"])>=.0015
        cur21=f21[di,21]
        align[di]=regime.sign(cur21["ret"][5])==regime.sign(cur21["ret"][60])
        highvol[di]=cur21["volume5"]>=1.25
        for arm,lab in enumerate(FALL_ARMS):
            hh=int(lab[:2]);rule=lab[3:]
            f=f21[di,hh]
            ss=regime.sign(f["ret"][5 if rule.endswith("5") else 60])
            if rule.startswith("fade"):ss=-ss
            fall_signs[di,arm]=ss
    # Fallback price paths for both costs and B/E exit regimes.
    fallback={}
    for mi in range(2):
        for prof in EXIT_PROFILES:
            pvals=[[],[],[],[],[]]
            for di_arm,lab in enumerate(FALL_ARMS):
                hh=int(lab[:2])
                ix=np.arange(NUM_DAYS)
                side=fall_signs[:,di_arm]
                cands={}
                for s in (1,-1):
                    cands[s]=pre[f"fall_{hh}_{s}"]
                rp=[];ff=[];gg=[];ww=[];tt=[]
                for di in range(NUM_DAYS):
                    r,c,g,w,t=cands[int(side[di])]
                    key=("trail075" if (prof=="E" and
                         f21[di,hh]["volume5"]>=1.25) else "trail050")
                    param=cidx[key]
                    rp.append(r[di,param,mi])
                    ff.append(c[di,param,mi])
                    gg.append(g[di,param])
                    ww.append(w[di,param])
                    tt.append(t[di,param])
                for dst,chunk in zip(pvals,(rp,ff,gg,ww,tt)):
                    dst.append(chunk)
            fallback[mi,prof]=tuple(
                np.asarray(x,dtype=float if k in (0,1,2) else np.int16).T
                for k,x in enumerate(pvals)
            )
    return dict(event=event,fallback=fallback,event_hours=event_hours,
        event_signs=event_signs,fall_signs=fall_signs,
        isfallback=isfallback,features21=f21,
        eventvol=eventvol,eventimpulse=eventimpulse,
        align=align,highvol=highvol)

def calculate_scores(past,mode):
    if mode=="win":
        return np.mean(past>0,axis=0)
    if mode=="net":
        return np.mean(past,axis=0)
    if mode=="risk":
        downside=np.sqrt(np.mean(np.minimum(past,0)**2,axis=0))
        return np.mean(past,axis=0)-.30*downside
    raise KeyError(mode)

def prior_online_choices(returns,active,contexts,kind,lookback,score_kind,margin):
    """Returns prior-only arm choice; active labels and contexts for all days.

    Only active prior days are eligible for scores. For context-conditioned
    methods, the SAME context group must have >=12 prior observations among
    the last 'lookback' previous matching event/fallback days.
    """
    n,arms=returns.shape
    chosen=np.zeros(n,dtype=np.int8)
    sample_size=np.zeros(n,dtype=np.int16)
    nondefault=0
    assert active.shape==(n,) and contexts.shape==(n,)
    if kind=="fixed":
        return chosen,sample_size
    for d in range(n):
        if not active[d]:continue
        prior=np.flatnonzero(active[:d])[-lookback:]
        if kind!="online_global":
            prior=prior[contexts[prior]==contexts[d]]
        sample_size[d]=len(prior)
        if len(prior)<12:
            continue
        if int(np.max(prior))>=d:
            raise AssertionError("Future-day leak in online learner")
        samples=returns[prior,:]
        scores=calculate_scores(samples,score_kind)
        arm=int(np.argmax(scores))
        threshold=(.05 if score_kind=="win" else .0003) if margin=="conservative" else 0.
        if arm!=0 and scores[arm]>scores[0]+threshold:
            chosen[d]=arm
            nondefault+=1
    return chosen,sample_size

def pick_path(event,event_idx,fall,fall_idx,mask):
    d=np.arange(NUM_DAYS)
    path=np.where(mask,fall[0][d,fall_idx],event[0][d,event_idx])
    fees=np.where(mask,fall[1][d,fall_idx],event[1][d,event_idx])
    gross=np.where(mask,fall[2][d,fall_idx],event[2][d,event_idx])
    reason=np.where(mask,fall[3][d,fall_idx],event[3][d,event_idx])
    duration=np.where(mask,fall[4][d,fall_idx],event[4][d,event_idx])
    return path,fees,gross,reason,duration

def metrics(path,fees,gross,reason,duration):
    z=base.score(path,fees,gross,np.full(NUM_DAYS,2*base.SLIP),reason)
    z["max_dd_2025"]=adaptive.period_dd(path[:base.NTRAIN])
    z["max_dd_2026"]=adaptive.period_dd(path[base.NTRAIN:])
    z["worst_losing_streak"]=base.max_loss_run(path<0)
    z["mean_hold_min"]=round(float(np.mean(duration)),3)
    return z

def monthly_ledger(path,fees,gross,reason,duration,features,event_arm,fall_arm,
                   eventhist,fallhist,profile):
    mask=features["isfallback"]
    entry_hrs=np.where(mask,np.array([int(FALL_ARMS[int(i)][:2]) for i in fall_arm]),
                       features["event_hours"])
    entry_dir=np.where(mask,features["fall_signs"][np.arange(NUM_DAYS),fall_arm],
                       np.where(event_arm==0,features["event_signs"],-features["event_signs"]))
    entry_type=np.where(mask,"FORCED_FALLBACK","VOLUME_EVENT")
    chosen_label=np.where(mask,np.array(FALL_ARMS,dtype=str)[fall_arm],
                          np.where(event_arm==0,"fade5","follow5"))
    details=pd.DataFrame({
        "date_ist":base.IST_DAYS,"month_ist":base.MONTH_LABELS,
        "year":np.asarray(DAYS.year),"entry_hour_ist":entry_hrs,
        "direction":np.where(entry_dir>0,"LONG","SHORT"),
        "entry_type":entry_type,"online_choice":chosen_label,
        "prior_comparable_cases":np.where(mask,fallhist,eventhist),
        "exit_schedule":profile,"account_return_net_pct":path*100,
        "gross_btc_points":gross,"fee_gst_btc_points":fees,
        "slippage_btc_points":2*base.SLIP,
        "exit_reason":np.where(reason==1,"TAKE_PROFIT",np.where(reason==2,"STOP","TIMEOUT")),
        "hold_minutes":duration.astype(int)
    })
    if details.date_ist.nunique()!=NUM_DAYS or len(details)!=477:
        raise AssertionError("Lost mandatory daily trade coverage")
    months=details.groupby("month_ist",sort=True).agg(
        trades=("date_ist","size"),
        winning_days=("account_return_net_pct",lambda s:int(np.sum(s>0))),
        losing_days=("account_return_net_pct",lambda s:int(np.sum(s<0))),
        compounded_net_return_pct=("account_return_net_pct",
                        lambda s:float((np.prod(1+s.to_numpy()/100)-1)*100)),
        gross_points=("gross_btc_points","sum"),
        fee_gst_points=("fee_gst_btc_points","sum")
    ).reset_index()
    if len(months)!=22:raise AssertionError("Incomplete monthly coverage")
    return details,months

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=base.load()
    f=retrieve(m)
    evmask=~f["isfallback"]
    fbmask=f["isfallback"]
    assert int(evmask.sum())==260 and int(fbmask.sum())==217
    assert len(np.unique(base.IST_DAYS))==NUM_DAYS
    context_e={
        "fixed":np.zeros(NUM_DAYS,dtype=bool),
        "online_global":np.zeros(NUM_DAYS,dtype=bool),
        "online_volume2":f["eventvol"],
        "online_impulse5":f["eventimpulse"]
    }
    context_f={
        "fixed":np.zeros(NUM_DAYS,dtype=bool),
        "online_global":np.zeros(NUM_DAYS,dtype=bool),
        "online_align5_60":f["align"],
        "online_volume1p25":f["highvol"]
    }
    baseline={}
    for mode in MODES:
        mi=MODES.index(mode)
        er=f["event"][mi]
        for profile in EXIT_PROFILES:
            fl=f["fallback"][mi,profile]
            static_idx=np.zeros(NUM_DAYS,dtype=np.int8)
            p,c,g,w,t=pick_path(er,static_idx,fl,static_idx,fbmask)
            baseline[mode+"_"+profile]=metrics(p,c,g,w,t)
        if mode=="scalper_offer":
            a=baseline[mode+"_B"];b=baseline[mode+"_E"]
            if a["profitable_days"]!=271 or abs(a["net_total_pct"]-15.522477)>.00011:
                raise AssertionError("B parity failed "+str(a))
            if b["profitable_days"]!=273 or abs(b["net_total_pct"]-17.215989)>.00011:
                raise AssertionError("E parity failed "+str(b))
    print("STEP6_BASELINE_PARITY "+json.dumps(baseline,sort_keys=True),flush=True)
    # Precompute every prior-only choice; combine without changing entry count.
    eventchoices={};fallbackchoices={}
    for mi,mode in enumerate(MODES):
        er=f["event"][mi]
        for evmethod,w,score,margin in product(EVENT_MODES,WINDOWS,SCORES,MARGINS):
            key=(evmethod,w,score,margin,mi)
            eventchoices[key]=prior_online_choices(er[0],evmask,
                context_e[evmethod],evmethod,w,score,margin)
        for profile in EXIT_PROFILES:
            fl=f["fallback"][mi,profile]
            for fbmethod,w,score,margin in product(FALLBACK_MODES,WINDOWS,SCORES,MARGINS):
                key=(fbmethod,w,score,margin,profile,mi)
                fallbackchoices[key]=prior_online_choices(fl[0],fbmask,
                    context_f[fbmethod],fbmethod,w,score,margin)
    print("STEP6_CHOICES_COMPUTED "+json.dumps(dict(
        event_choice_tables=len(eventchoices),fallback_choice_tables=len(fallbackchoices),
        current_day_future_prices_never_used=True)),flush=True)
    rows=[]
    for evmethod,fbmethod,w,score,margin,profile,mode in product(
        EVENT_MODES,FALLBACK_MODES,WINDOWS,SCORES,MARGINS,EXIT_PROFILES,MODES
    ):
        mi=MODES.index(mode)
        e_idx,e_hist=eventchoices[evmethod,w,score,margin,mi]
        f_idx,f_hist=fallbackchoices[fbmethod,w,score,margin,profile,mi]
        er=f["event"][mi];fl=f["fallback"][mi,profile]
        p,c,g,reason,hold=pick_path(er,e_idx,fl,f_idx,fbmask)
        metric=metrics(p,c,g,reason,hold)
        metric.update(
            event_method=evmethod,fallback_method=fbmethod,lookback=w,
            scoring=score,preference=margin,exit_profile=profile,cost_model=mode,
            event_nondefault_choices=int(np.sum((e_idx!=0)&evmask)),
            fallback_nondefault_choices=int(np.sum((f_idx!=0)&fbmask)),
            event_default_due_insufficient_history=int(np.sum((e_hist<12)&evmask)) if evmethod!="fixed" else 0,
            fallback_default_due_insufficient_history=int(np.sum((f_hist<12)&fbmask)) if fbmethod!="fixed" else 0,
            entries_event=int(evmask.sum()),entries_fallback=int(fbmask.sum())
        )
        rows.append(metric)
    tab=pd.DataFrame(rows)
    if len(tab)!=EXPECTED or not tab.trades.eq(477).all():
        raise AssertionError("Wrong grid/forced weekday coverage")
    tab.to_csv(OUT/"all_1152_prior_day_learning_models.csv",index=False)
    print("STEP6_GRID "+json.dumps(dict(models=len(tab),mandatory_trades=int(tab.trades.min()),
        events=260,fallbacks=217)),flush=True)
    reported={}
    for mode in MODES:
        sub=tab[tab.cost_model==mode].copy()
        candidates=sub[(sub.return_2025_pct>0)&(sub.max_dd_2025<=8)]
        if len(candidates):
            sort=candidates.sort_values(
              ["profitable_days_2025","return_2025_pct","max_dd_2025"],
              ascending=[False,False,True])
        else:
            sort=sub.sort_values(["return_2025_pct","profitable_days_2025"],
                            ascending=[False,False])
        best=sort.iloc[0].to_dict()
        mi=MODES.index(mode)
        evmethod=best["event_method"];fbmethod=best["fallback_method"]
        w=int(best["lookback"]);score=best["scoring"];margin=best["preference"]
        profile=best["exit_profile"]
        e_idx,e_hist=eventchoices[evmethod,w,score,margin,mi]
        f_idx,f_hist=fallbackchoices[fbmethod,w,score,margin,profile,mi]
        p,c,g,reason,hold=pick_path(f["event"][mi],e_idx,
                                    f["fallback"][mi,profile],f_idx,fbmask)
        daily,monthly=monthly_ledger(p,c,g,reason,hold,f,e_idx,f_idx,e_hist,f_hist,profile)
        daily.to_csv(OUT/(mode+"_2025_selected_daily_477.csv"),index=False)
        monthly.to_csv(OUT/(mode+"_2025_selected_monthly_22.csv"),index=False)
        both=(sub.return_2025_pct>0)&(sub.return_2026_pct>0)
        b=baseline[mode+"_E"]
        strict=(sub.profitable_days>b["profitable_days"]) & (
            sub.net_total_pct>b["net_total_pct"]) & (
            sub.max_closed_dd_pct<=b["max_closed_dd_pct"])
        hindsight=sub.sort_values(["net_total_pct","profitable_days"],ascending=False).iloc[0].to_dict()
        reported[mode]={
            "selected_2025_only":best,
            "eligible_train_count":int(len(candidates)),
            "positive_both_years_models_hindsight":int(both.sum()),
            "pareto_improved_versus_E_hindsight":int(strict.sum()),
            "full_sample_best_profit_hindsight_NOT_SELECTED":hindsight,
            "selected_2025_winning_days":int(np.sum(p[:base.NTRAIN]>0)),
            "selected_2026_winning_days":int(np.sum(p[base.NTRAIN:]>0)),
            "selected_profitable_months":int(np.sum(monthly.compounded_net_return_pct>0)),
            "selected_worst_month_pct":round(float(monthly.compounded_net_return_pct.min()),5)
        }
        print("STEP6_SELECTED_"+mode.upper()+" "+json.dumps(reported[mode],sort_keys=True),flush=True)
        print("STEP6_MONTHLY_"+mode.upper()+"\n"+monthly.to_string(index=False),flush=True)
    (OUT/"summary.json").write_text(json.dumps({
        "purpose":"daily BTC 477-trade prior-day-only dynamic direction/clock",
        "models":len(tab),"days":len(DAYS),"events":260,"fallbacks":217,
        "train_dates":"2025-01-02 through 2025-12-31",
        "historical_check_dates":"2026-01-01 through 2026-10-30",
        "strict_future_leakage_check":True,
        "costs":"BTC 1x account exposure, 0.05% taker per leg+18% GST, 5 BTC price points adverse per leg; speculative activated regular Scalper Offer waives <=30min closing fee only",
        "exact_baselines":baseline,"results":reported,
        "caveats":[
            "2025 and 2026 are previously research-exposed; this is NOT genuine pristine OOS",
            "576 variants still cause selection bias, even with a prior-days-only online decision",
            "Multiple shadow trades each day are counterfactual outcomes obtained from completed prior OHLC bars; real orders not actually sent",
            "No funding, real orderbook spread, latency, historical scalper activation or tick-level sequencing",
            "Mandatory every-weekday entry does not guarantee a positive daily return"
        ]
    },indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
      "# Step 6 — one BTC trade each weekday, causal prior-days-only direction learning",
      "",f"Every model includes all {len(DAYS)} Monday–Friday IST trades, no skippable days.",
      "","## Verified B/E replay baselines",json.dumps(baseline,indent=2),
      "","## 2025-only selection; 2026 historical research-exposed check",json.dumps(reported,indent=2),
      "","## Scalper-selected 22-month breakdown","",
      pd.read_csv(OUT/"scalper_offer_2025_selected_monthly_22.csv").to_markdown(index=False),
      "","## Standard-selected 22-month breakdown","",
      pd.read_csv(OUT/"standard_2025_selected_monthly_22.csv").to_markdown(index=False),
      "","## Limitations",
      "Online prior-day selection prevents within-backtest decision lookahead but does not create unseen historical validation; costs assume historical opt-in. Forward paper-trading remains necessary."
    ])+"\n")
    print("STEP6_CAUSAL_ONLINE_COMPLETE",flush=True)

if __name__=="__main__":
    run()
