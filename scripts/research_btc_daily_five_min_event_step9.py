#!/usr/bin/env python3
"""BTCUSD Step 9: causal 5m intraday event scanning; compulsory 477 weekdays.

No hindsight event selection: first qualifying completed 5m bar at any
predeclared checkpoint, else 21:00 IST fallback. Exactly one trade each
Mon–Fri. Step6 E exits unchanged (next-bar profit locks, 1m stop-first).
Compare 2025 selected, frozen 2026, after fees + GST + 5pt slip each leg.
"""
from pathlib import Path
from itertools import product
import json

import numpy as np
import pandas as pd

import research_btc_every_weekday_reset_step1 as base
import research_btc_every_weekday_exit_protection_step3 as protection
import research_btc_daily_causal_regime_step5 as regime
import research_btc_daily_online_direction_step6 as online

OUT=Path("analysis/btc_daily_five_min_event_step9")
DAYS=base.DAYS
N=len(DAYS)
TRAIN=base.NTRAIN
COSTS=base.MODES
WINDOWS={
   "17_to_21":(17*60,21*60),
   "18_to_21":(18*60,21*60),
   "19_to_21":(19*60,21*60),
   "18_to_20":(18*60,20*60),
}
VOLS=(1.25,1.5,2.0)
IMPULSES=(0.,.0005,.001,.002)
SIDES=("fade5","follow5","follow60","align5_15_else_fade")
FALLBACKS=("follow5","fade5")
ALL_5M_MINUTES=np.arange(17*60,21*60,5,dtype=np.int32)
EXPECTED=len(WINDOWS)*len(VOLS)*len(IMPULSES)*len(SIDES)*len(FALLBACKS)
assert EXPECTED==384 and N==477 and TRAIN==260
assert len(ALL_5M_MINUTES)==48

def past_information(m,index):
    """All event observations use ONLY [t−105,t) minutes, never [t,t+)."""
    opening=m.open.to_numpy(dtype=float)
    closing=m.close.to_numpy(dtype=float)
    vol=m.volume.to_numpy(dtype=float)
    csum=np.r_[0.,np.cumsum(vol)]
    i=index.astype(np.int64)
    r5=closing[i-1]/opening[i-5]-1
    r15=closing[i-1]/opening[i-15]-1
    r60=closing[i-1]/opening[i-60]-1
    v5=csum[i]-csum[i-5]
    historic20=(csum[i-5]-csum[i-105])/20.
    rvol=np.divide(v5,historic20,out=np.zeros_like(v5),where=historic20>0)
    for x in (r5,r15,r60,rvol):
        if not np.isfinite(x).all():
            raise AssertionError("Bad pre-entry indicator")
    return {"r5":r5,"r15":r15,"r60":r60,"rvol":rvol}

def sign(x):
    return np.where(x>=0,1,-1).astype(np.int8)

def choose_sides(policy,ind):
    s5=sign(ind["r5"]);s15=sign(ind["r15"]);s60=sign(ind["r60"])
    if policy=="fade5":return -s5
    if policy=="follow5":return s5
    if policy=="follow60":return s60
    if policy=="align5_15_else_fade":
        return np.where(s5==s15,s5,-s5).astype(np.int8)
    raise KeyError(policy)

def prepared_candidates(m):
    starts,_,_=base.prepare(m)
    minute0=starts[:,0].astype(np.int64)
    event_indexes=minute0[:,None]+ALL_5M_MINUTES[None,:]
    # The first event's 5m bar ends at the predeclared entry minute.
    info=past_information(m,event_indexes)
    fallback_index=starts[:,21].astype(np.int64)
    fb=past_information(m,fallback_index)
    return event_indexes,info,fallback_index,fb

def choose_entries(settings,events,info,fbidx,fback):
    window,volume,minimum,direction,fallback=settings
    start,end=WINDOWS[window]
    in_window=(ALL_5M_MINUTES>=start)&(ALL_5M_MINUTES<end)
    valid=(info["rvol"]>=volume)&(np.abs(info["r5"])>=minimum)&in_window[None,:]
    have=valid.any(axis=1)
    first=np.argmax(valid,axis=1)
    days=np.arange(N)
    index=np.where(have,events[days,first],fbidx).astype(np.int64)
    dirside=choose_sides(direction,info)[days,first]
    fbside=choose_sides(fallback,fback)
    side=np.where(have,dirside,fbside).astype(np.int8)
    hour=np.where(have,ALL_5M_MINUTES[first]//60,21).astype(np.int16)
    minute=np.where(have,ALL_5M_MINUTES[first]%60,0).astype(np.int16)
    if np.any(side==0) or len(index)!=477:
        raise AssertionError("Missing required trade")
    # Every chosen order occurs at a precommitted instant, no scan of future.
    if np.any(index!=np.where(have,events[days,first],fbidx)):
        raise AssertionError("Bad future scanning")
    return index,side,hour,minute,have

def strategy_outcomes(m,cfg,ids,index,side,has_event,fallback_info):
    # Exact original Step6 E stop/lock/trailing recipes, independently per
    # trade selected from ONLY pre-entry event type / fallback volume.
    true_exit=np.where(has_event,ids["lock050"],
                       np.where(fallback_info["rvol"]>=1.25,
                                ids["trail075"],ids["trail050"]))
    op=m.open.to_numpy(float);high=m.high.to_numpy(float);low=m.low.to_numpy(float)
    # All 3 types passed through previously validated 1m Numba replay.
    hr=np.zeros(N,dtype=np.int8)
    r,fee,gross,why,elapsed=protection.run_exit_grid(
        op,high,low,index,hr,side,cfg,base.COST,base.SLIP)
    day=np.arange(N)
    p=r[day,true_exit,:]
    costs=fee[day,true_exit,:]
    g=gross[day,true_exit]
    reason=why[day,true_exit]
    t=elapsed[day,true_exit]
    if p.shape!=(477,2) or not np.isfinite(p).all():
        raise AssertionError("Unexpected realized trade shape")
    return p,costs,g,reason,t

def statistics(p,costs,gross,why,elapsed):
    z=base.score(p,costs,gross,np.full(N,base.SLIP*2),why)
    z["max_dd_2025_pct"]=online.adaptive.period_dd(p[:TRAIN])
    z["max_dd_2026_pct"]=online.adaptive.period_dd(p[TRAIN:])
    z["longest_losing_streak"]=base.max_loss_run(p<0)
    z["average_minutes_in_trade"]=round(float(np.mean(elapsed)),3)
    return z

def write_daily(p,cost,gross,why,elapsed,index,side,hour,minute,has_event,mode):
    df=pd.DataFrame(dict(
        day_ist=base.IST_DAYS,year=np.asarray(DAYS.year),
        month_ist=base.MONTH_LABELS,
        entry_hour_ist=hour.astype(int),
        entry_minute_ist=minute.astype(int),
        entry_side=np.where(side>0,"LONG","SHORT"),
        entry_type=np.where(has_event,"COMPLETED_5M_VOLUME_EVENT","MANDATORY_21H_FALLBACK"),
        account_net_return_pct=p*100.,
        gross_btc_price_points=gross,
        fee_gst_btc_price_points=cost,
        adverse_slippage_price_points=2*base.SLIP,
        exit_reason=np.where(why==1,"TARGET",np.where(why==2,"PROTECTIVE_STOP","TIMEOUT")),
        duration_minutes=elapsed.astype(int),
        modeled_fee_schedule=mode
    ))
    if len(df)!=477 or df.day_ist.nunique()!=477:raise AssertionError("Lost a weekday")
    monthly=df.groupby("month_ist",sort=True).agg(
        trades=("day_ist","count"),
        winning_days=("account_net_return_pct",lambda x:int(np.sum(x>0))),
        losing_days=("account_net_return_pct",lambda x:int(np.sum(x<0))),
        compounded_net_return_pct=("account_net_return_pct",
                      lambda x:float((np.prod(1+x.to_numpy()/100)-1)*100)),
        fee_gst_points=("fee_gst_btc_price_points","sum"),
        gross_points=("gross_btc_price_points","sum")
    ).reset_index()
    if len(monthly)!=22:
        raise AssertionError("Missing month")
    return df,monthly

def verify_step6_baseline(m):
    f=online.retrieve(m)
    mask=f["isfallback"]
    event,prior=online.prior_online_choices(
        f["event"][1][0],~mask,f["eventimpulse"],
        "online_impulse5",30,"net","conservative")
    fixed=np.zeros(N,dtype=np.int8)
    references={}
    for mi,mode in enumerate(COSTS):
        outcomes=online.pick_path(f["event"][mi],event,
            f["fallback"][mi,"E"],fixed,mask)
        references[mode]=statistics(*outcomes)
    b=references["scalper_offer"]
    if b["profitable_days"]!=275 or abs(b["net_total_pct"]-17.7862)>.00011:
        raise AssertionError("Step6 comparison baseline unexpectedly changed")
    if abs(references["standard"]["net_total_pct"]+11.101745)>.00011:
        raise AssertionError("Step6 standard fees changed")
    return references

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=base.load()
    baseline=verify_step6_baseline(m)
    cfg,ids=regime.build_cfg()
    events,info,fbidx,fb=prepared_candidates(m)
    print("STEP9_VERIFIED_BASELINE "+json.dumps(baseline,sort_keys=True),flush=True)
    results=[]
    for win,rv,imp,sd,fbmode in product(
            WINDOWS,VOLS,IMPULSES,SIDES,FALLBACKS):
        params=(win,rv,imp,sd,fbmode)
        index,side,hr,minute,has_event=choose_entries(params,events,info,fbidx,fb)
        p,cost,g,why,t=strategy_outcomes(m,cfg,ids,index,side,has_event,fb)
        for mi,mode in enumerate(COSTS):
            z=statistics(p[:,mi],cost[:,mi],g,why,t)
            z.update(search_window=win,min_5m_rvol=rv,
                min_abs_5m_return_pct=imp*100.,event_direction=sd,
                forced_fallback_direction=fbmode,cost_model=mode,
                event_days=int(np.sum(has_event)),
                fallback_days=int(np.sum(~has_event)),
                mean_event_entry_hour_ist=round(float(np.mean(hr[has_event]+minute[has_event]/60)) if np.any(has_event) else 0.,3),
                scenario_id=f"{win}__rvol{rv:g}__imp{imp*100:g}pct__{sd}__fallback{fbmode}")
            results.append(z)
    df=pd.DataFrame(results)
    if len(df)!=2*EXPECTED or not df.trades.eq(477).all():
        raise AssertionError("Not every strategy placed exactly one trade per weekday")
    df.to_csv(OUT/"all_384_fivemin_scenarios_two_fee_models.csv",index=False)
    print("STEP9_GRID "+json.dumps(dict(
        unique_entry_scenarios=EXPECTED,two_cost_scenarios=len(df),
        exact_weekday_trades=int(df.trades.min()),date_count=N),sort_keys=True),flush=True)
    offer=df[df.cost_model=="scalper_offer"]
    eligible=offer[(offer.profitable_days_2025>=145)&
       (offer.return_2025_pct>=3.)&(offer.max_dd_2025_pct<=4.)]
    if len(eligible):
        rank=eligible.sort_values(
            ["profitable_days_2025","return_2025_pct","max_dd_2025_pct"],
            ascending=[False,False,True])
    else:
        rank=offer.sort_values(["return_2025_pct","profitable_days_2025"],
              ascending=[False,False])
    best=rank.iloc[0].to_dict()
    settings=(best["search_window"],float(best["min_5m_rvol"]),
         round(float(best["min_abs_5m_return_pct"])/100.,8),
         best["event_direction"],best["forced_fallback_direction"])
    idx,sd,hr,minute,has_event=choose_entries(settings,events,info,fbidx,fb)
    p,fee,g,why,elapsed=strategy_outcomes(m,cfg,ids,idx,sd,has_event,fb)
    selected={}
    for mi,mode in enumerate(COSTS):
        led,monthly=write_daily(p[:,mi],fee[:,mi],g,why,elapsed,idx,sd,hr,minute,has_event,mode)
        led.to_csv(OUT/(mode+"_selected_477_weekdays.csv"),index=False)
        monthly.to_csv(OUT/(mode+"_selected_22_months.csv"),index=False)
        z=statistics(p[:,mi],fee[:,mi],g,why,elapsed)
        selected[mode]=dict(result=z,
             winning_months=int(np.sum(monthly.compounded_net_return_pct>0)),
             worst_month_pct=round(float(monthly.compounded_net_return_pct.min()),5),
             changed_2025_win_days=z["profitable_days_2025"]-baseline[mode]["profitable_days_2025"],
             changed_2026_win_days=z["profitable_days_2026"]-baseline[mode]["profitable_days_2026"],
             changed_2025_net_pct=round(float(z["return_2025_pct"]-baseline[mode]["return_2025_pct"]),5),
             changed_2026_net_pct=round(float(z["return_2026_pct"]-baseline[mode]["return_2026_pct"]),5))
    historic=offer.sort_values(["net_total_pct","profitable_days"],ascending=False).iloc[0].to_dict()
    both=(offer.return_2025_pct>0)&(offer.return_2026_pct>0)
    dominate_step6=(offer.profitable_days>baseline["scalper_offer"]["profitable_days"])&(
        offer.net_total_pct>baseline["scalper_offer"]["net_total_pct"])&(
        offer.max_closed_dd_pct<=baseline["scalper_offer"]["max_closed_dd_pct"])
    summary=dict(
       purpose="Check every completed 5m event rather than 18h 19h 20h checkpoints; mandatory 21h fallback",
       full_notional_1x=True,
       exactly_477_weekday_trades=True,
       2025_train_only=True,
       research_exposed_2026_not_blind=True,
       configurations=EXPECTED,
       both_fee_scenarios=len(df),
       train_2025_eligible_count=int(len(eligible)),
       selected_2025_policy=best,
       selected_across_two_fee_models=selected,
       baseline_Step6_verified=baseline,
       baseline_Step8_selected_historical=dict(
           historical_winning_days=277,modeled_net_pct=21.423313,
           profitable_months=15,max_dd_pct=3.008746,
           limitation="improvement concentrated in 2025, none in 2026"),
       full_period_highest_net_hindsight_NOT_SELECTED=historic,
       full_period_both_years_profitable_models_hindsight=int(np.sum(both)),
       full_period_pareto_better_than_step6_hindsight=int(np.sum(dominate_step6)),
       fee_model="standard 0.05% BTC futures taker per leg plus GST18%, 5 BTC price points slippage per leg; optional hypothetical preactivated regular Scalper Offer zero closing fee <=30m",
       limitations=[
           "2026 previously researched, not pristine independent forward test",
           "384 variants and prior extensive trials cause selection overfitting",
           "Scalper Offer historical validity and fills not verified",
           "OHLC1m cannot determine intrabar order of stop/TP: assume stop first",
           "No funding, true bid/ask, market depth, latency or liquidation model"])
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
       "# BTCUSD Step9 — 5m cadence daily entry analysis",
       "",
       "Every model enters exactly once on every eligible IST weekday. The entry time is the first 5m volume/price event before a fixed deadline, else a 21:00 fallback. Exit policies are frozen Step6 E rules.",
       "",
       "## Original Step6 verified after-cost baseline",json.dumps(baseline,indent=2),
       "",
       "## Entry rule selected using 2025 only",json.dumps(best,indent=2),
       "",
       "## Performance of the unchanged rule in Jan-Oct 2026",json.dumps(selected,indent=2),
       "",
       "## Selected Scalper modeled 22 monthly results","",
       pd.read_csv(OUT/"scalper_offer_selected_22_months.csv").to_markdown(index=False),
       "",
       "## Historical caveats",
       "2026 already researched; choosing best 2025 and comparing to 2026 is not truly independent forward validation. The historical Scalper Offer status and true fills/latency aren't established; actual live profit may be materially lower."
    ])+"\n")
    print("STEP9_SELECTION "+json.dumps(dict(
        policy=best,measured=selected,hindsight=historic),sort_keys=True),flush=True)
    print("STEP9_COMPLETED",flush=True)

if __name__=="__main__":
    run()
