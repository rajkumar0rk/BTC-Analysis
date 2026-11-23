#!/usr/bin/env python3
"""Step 7 — Next-minute causal invalidation and early-exit experiments.

Every single candidate takes the exact SAME 477 daily BTCUSD entries from
Step6's 2025-selected prior-days-only trading direction. Only exits differ.
Baseline parity with Step6 required before producing any improvement claim.

Never use the current 1m HIGH/LOW to fill an exit in that SAME bar that it
triggers; abort at NEXT minute OPEN after closed prior 1m bar.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit

import research_btc_every_weekday_reset_step1 as base
import research_btc_every_weekday_adaptive_step2 as adaptive
import research_btc_daily_causal_regime_step5 as regime
import research_btc_daily_online_direction_step6 as online

OUT=Path("analysis/btc_daily_exit_invalidation_step7")
DAYS=base.DAYS
N=len(DAYS)
MODES=base.MODES
NTRAIN=base.NTRAIN

# Exit control:
# kind=0 none, kind=1 adverse close invalidation, kind=2 insufficient
# favorable excursion, kind=3 immediate early profit at NEXT minute OPEN.
# Fields: kind, threshold in gross entry-mid price %, after_minute, timeout_minute.
def build_exit_policies():
    values=[(0,0.,0.,30.)]
    ids=["baseline_30min"]
    for hold in (10,15,20,25):
        values.append((0,0.,0.,float(hold)))
        ids.append(f"hard_timeout_{hold}m")
    for after in (3,5,8,10,15,20):
        for cut in (.04,.08,.12,.20,.30):
            values.append((1,float(cut),float(after),30.))
            ids.append(f"adverse_cut_{cut:g}pct_after_{after}m")
    for after in (5,10,15,20):
        for mfe in (.05,.10,.15,.20):
            values.append((2,float(mfe),float(after),30.))
            ids.append(f"stall_if_mfe_below_{mfe:g}pct_at_{after}m")
    for after in (5,10,15,20):
        for take in (.10,.15,.20,.30):
            values.append((3,float(take),float(after),30.))
            ids.append(f"profit_close_at_{take:g}pct_after_{after}m")
    assert len(values)==len(set(ids))==67
    return np.asarray(values,dtype=np.float64),ids


@njit(cache=True)
def replay_with_nextbar_exits(open1,high1,low1,close1,starts,sides,
                              baserecipe,policies,fee,slip):
    # baserecipe per day [kind,SLpct,TPpct,hold,activationpct,valuepct,step].
    nd=len(starts);npoli=len(policies)
    profit=np.empty((nd,npoli,2),dtype=np.float64)
    fees=np.empty((nd,npoli,2),dtype=np.float64)
    gross=np.empty((nd,npoli),dtype=np.float64)
    reason=np.empty((nd,npoli),dtype=np.int8)
    elapsed=np.empty((nd,npoli),dtype=np.int16)
    for d in range(nd):
        start=int(starts[d])
        sd=float(sides[d])
        mid=open1[start]
        entry=mid+sd*slip
        feeopen=fee*entry
        ekind=int(baserecipe[d,0])
        sl=baserecipe[d,1]*.01
        tp=baserecipe[d,2]*.01
        act=baserecipe[d,4]*.01
        val=baserecipe[d,5]*.01
        step=baserecipe[d,6]*.01
        hardstop=mid*(1.-sd*sl)
        takeprofit=mid*(1.+sd*tp)
        for pidx in range(npoli):
            exit_type=int(policies[pidx,0])
            threshold=policies[pidx,1]*.01
            after=int(policies[pidx,2])
            maxhold=int(policies[pidx,3])
            stop=hardstop
            bestmove=0.
            exitj=start+maxhold
            midout=open1[exitj]
            why=3 # timeout
            for t in range(maxhold):
                j=start+t
                hitstop=(low1[j]<=stop) if sd>0 else (high1[j]>=stop)
                hittp=(high1[j]>=takeprofit) if sd>0 else (low1[j]<=takeprofit)
                # Pessimistic minute path for simultaneous TP + stop.
                if hitstop:
                    midout=min(open1[j],stop) if sd>0 else max(open1[j],stop)
                    exitj=j;why=2;break
                if hittp:
                    midout=takeprofit
                    exitj=j;why=1;break
                # Only end-of-minute favorable excursion is known for
                # stop ratcheting; new stop becomes LIVE FROM j+1.
                fav=(high1[j]-mid)/mid if sd>0 else (mid-low1[j])/mid
                if fav>bestmove:bestmove=fav
                if ekind==1:
                    if bestmove>=act:
                        proposed=mid*(1.+sd*val)
                        if sd>0 and proposed>stop:stop=proposed
                        if sd<0 and proposed<stop:stop=proposed
                elif ekind==2:
                    if bestmove>=act:
                        proposed=mid*(1.+sd*(bestmove-val))
                        if sd>0 and proposed>stop:stop=proposed
                        if sd<0 and proposed<stop:stop=proposed
                elif ekind==3:
                    if bestmove>=act:
                        nsteps=int((bestmove-act+1.e-12)/step)
                        proposed=mid*(1.+sd*(val+nsteps*step))
                        if sd>0 and proposed>stop:stop=proposed
                        if sd<0 and proposed<stop:stop=proposed
                # Invalidation determined at candle CLOSE, filled at
                # NEXT minute OPEN (j+1), never at j CLOSE or its HIGH/LOW.
                if (t+1)>=after and exit_type>0:
                    signedclose=sd*(close1[j]-mid)/mid
                    shouldcut=False
                    if exit_type==1:
                        shouldcut=signedclose <= -threshold
                    elif exit_type==2:
                        shouldcut=bestmove < threshold
                    elif exit_type==3:
                        shouldcut=signedclose >= threshold
                    if shouldcut:
                        exitj=j+1
                        midout=open1[exitj]
                        why=4 # prior-bar exit
                        break
            fillout=midout-sd*slip
            minheld=exitj-start
            standard=feeopen+fee*fillout
            offer=feeopen+(0. if minheld<=30 else fee*fillout)
            g=sd*(midout-mid)
            trade=sd*(fillout-entry)
            profit[d,pidx,0]=(trade-standard)/entry
            profit[d,pidx,1]=(trade-offer)/entry
            fees[d,pidx,0]=standard
            fees[d,pidx,1]=offer
            gross[d,pidx]=g
            reason[d,pidx]=why
            elapsed[d,pidx]=minheld
    return profit,fees,gross,reason,elapsed


def load_entries(m):
    f=online.retrieve(m)
    fallback=f["isfallback"]
    assert int(fallback.sum())==217 and int((~fallback).sum())==260
    eventidx,eventhist=online.prior_online_choices(f["event"][1][0],
        ~fallback,f["eventimpulse"],"online_impulse5",30,"net","conservative")
    fallbackidx=np.zeros(N,dtype=np.int8)
    # Our exact Step6 2025-selected event/fallback side and time.
    eventside=np.where(eventidx==0,f["event_signs"],-f["event_signs"])
    fs=f["fall_signs"][:,0]  # 21h FOLLOW5 only
    sides=np.where(fallback,fs,eventside).astype(np.int8)
    hours=np.where(fallback,21,f["event_hours"]).astype(np.int8)
    starts,_dirs,_tie=base.prepare(m)
    idx=starts[np.arange(N),hours]
    config,cfgid=regime.build_cfg()
    # Event uses locked SL .5%; fallback uses preentry 21h volume regime.
    eidx=cfgid["lock050"]
    recipeindices=np.where(fallback,
        np.where(np.array([f["features21"][di,21]["volume5"]>=1.25 for di in range(N)]),
              cfgid["trail075"],cfgid["trail050"]),
        eidx)
    baserecipes=config[recipeindices]
    if len(idx)!=477 or np.any(sides==0):
        raise AssertionError("One entry per weekday not enforced")
    assert np.array_equal(idx,starts[np.arange(N),hours])
    expected=[]
    for mode_i in range(2):
        ev=f["event"][mode_i]
        fl=f["fallback"][mode_i,"E"]
        pp,*_=online.pick_path(ev,eventidx,fl,fallbackidx,fallback)
        expected.append(pp)
    return dict(starts=idx,side=sides,hour=hours,mask=fallback,
        cfg=baserecipes,online_event_side_flips=int(np.sum((eventidx!=0)&(~fallback))),
        expected=np.stack(expected,axis=1),history=eventhist)


def calc(p,fee,gross,why,holding):
    stat=base.score(p,fee,gross,np.full(N,2*base.SLIP),why)
    stat["max_dd_2025"]=adaptive.period_dd(p[:NTRAIN])
    stat["max_dd_2026"]=adaptive.period_dd(p[NTRAIN:])
    stat["longest_losing_streak"]=base.max_loss_run(p<0)
    stat["mean_hold_min"]=round(float(np.mean(holding)),3)
    stat["early_bar_close_exits"]=int(np.sum(why==4))
    return stat


def splice(raw,event_policy,fallback_policy,eventmask,mode_i):
    profit,fees,gross,why,elapsed=raw
    i=np.where(eventmask,event_policy,fallback_policy).astype(int)
    d=np.arange(N)
    return profit[d,i,mode_i],fees[d,i,mode_i],gross[d,i],why[d,i],elapsed[d,i]


def candidate_record(raw,p_ev,p_fb,mask,mode_i):
    p,fee,g,r,t=splice(raw,p_ev,p_fb,~mask,mode_i)
    return calc(p,fee,g,r,t)


def rank_by_2025_group(raw,mask,mode_i,n=10):
    # isolate group: each record is judged by its earlier 2025 outcomes,
    # no 2026 contributions or comparisons permitted in ranking.
    p=raw[0][:NTRAIN,:,mode_i]
    selector=mask[:NTRAIN]
    values=p[selector,:]
    scores=[]
    for i in range(p.shape[1]):
        daily=values[:,i]
        w=int(np.sum(daily>0))
        profit=float(np.log1p(daily).sum())
        scores.append((w,profit,i))
    scores.sort(key=lambda x:(-x[0],-x[1],x[2]))
    picked=[i for _,_,i in scores[:n]]
    if 0 not in picked:picked.append(0)  # always include baseline
    return picked, scores[:5]


def display_ledger(raw,ev,fb,entryinfo,mode):
    mode_i=MODES.index(mode)
    p,c,g,why,t=splice(raw,ev,fb,~entryinfo["mask"],mode_i)
    df=pd.DataFrame(dict(
        day_ist=base.IST_DAYS,
        year=np.array(DAYS.year),
        month_ist=base.MONTH_LABELS,
        hour_ist=entryinfo["hour"],
        direction=np.where(entryinfo["side"]>0,"LONG","SHORT"),
        entry_kind=np.where(entryinfo["mask"],"MANDATORY_FALLBACK","VOLUME_SIGNAL"),
        event_rule_idx=int(ev),fallback_rule_idx=int(fb),
        net_account_pct=p*100,
        gross_points=g,fees_gst_btc_points=c,
        slippage_btc_points=2*base.SLIP,
        exit_reason=np.where(why==1,"TP",np.where(why==2,"PROTECTIVE_STOP",
                          np.where(why==3,"TIMEOUT","PRIOR_BAR_INVALIDATION"))),
        hold_minutes=t.astype(int)))
    if len(df)!=477 or df.day_ist.nunique()!=477:raise AssertionError("Missing daily trade")
    bymonth=df.groupby("month_ist",sort=True).agg(
        trades=("day_ist","count"),
        profitable_days=("net_account_pct",lambda x:int(np.sum(x>0))),
        loss_days=("net_account_pct",lambda x:int(np.sum(x<0))),
        net_compounded_pct=("net_account_pct",lambda x:float(100*(np.prod(1+x.to_numpy()/100)-1))),
        fees_gst_btc_points=("fees_gst_btc_points","sum"),
        gross_points=("gross_points","sum")
    ).reset_index()
    if len(bymonth)!=22:raise AssertionError("Missing 22 months")
    return df,bymonth


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=base.load()
    info=load_entries(m)
    policies,names=build_exit_policies()
    raw=replay_with_nextbar_exits(
        m.open.to_numpy(float),m.high.to_numpy(float),
        m.low.to_numpy(float),m.close.to_numpy(float),
        info["starts"],info["side"],info["cfg"],
        policies,base.COST,base.SLIP
    )
    if raw[0].shape!=(N,67,2):
        raise AssertionError("Incomplete 1m replay")
    # Exact reference Step6 outcome for every individual trade and both cost models.
    for mi,mode in enumerate(MODES):
        observed=raw[0][:,0,mi]
        expected=info["expected"][:,mi]
        if not np.allclose(observed,expected,rtol=0.,atol=1.e-13):
            raise AssertionError(f"BASELINE PER-TRADE PARITY FAILURE {mode}: maxabs={np.max(abs(observed-expected))}")
    baseline={}
    for mi,mode in enumerate(MODES):
        baseline[mode]=candidate_record(raw,0,0,info["mask"],mi)
        if mode=="scalper_offer":
            if baseline[mode]["profitable_days"]!=275 or abs(baseline[mode]["net_total_pct"]-17.7862)>0.00011:
                raise AssertionError("Old Step6 win/profit parity invalid")
        else:
            if baseline[mode]["profitable_days"]!=193 or abs(baseline[mode]["net_total_pct"]+11.101745)>0.00011:
                raise AssertionError("Old Step6 standard parity invalid")
    print("STEP7_BASELINE "+json.dumps(baseline,sort_keys=True),flush=True)
    print("STEP7_FIXED_PARAMETERS "+json.dumps(dict(early_exit_designs=67,
        trade_days=N,online_event_side_flips=info["online_event_side_flips"]),sort_keys=True),flush=True)

    rows=[];reported={}
    for mode in MODES:
        mi=MODES.index(mode)
        eventp,top_e=rank_by_2025_group(raw,~info["mask"],mi,10)
        fallp,top_f=rank_by_2025_group(raw,info["mask"],mi,10)
        # Evaluate event-only and fallback-only for every exit rule to
        # diagnose which trade type can be improved.
        for i,name in enumerate(names):
            for group,eidx,fidx in (("event_only",i,0),("fallback_only",0,i)):
                z=candidate_record(raw,eidx,fidx,info["mask"],mi)
                rows.append(dict(kind="single_group",group=group,event_exit=names[eidx],
                  fallback_exit=names[fidx],event_index=eidx,fallback_index=fidx,cost_model=mode,**z))
        # 2025-chosen candidate combinations ONLY. No 2026 sorting.
        combinations=[]
        for eidx in eventp:
            for fidx in fallp:
                z=candidate_record(raw,eidx,fidx,info["mask"],mi)
                rec=dict(kind="2025_shortlist_pair",group="both",event_exit=names[eidx],
                  fallback_exit=names[fidx],event_index=eidx,fallback_index=fidx,
                  cost_model=mode,**z)
                combinations.append(rec)
                rows.append(rec)
        group=pd.DataFrame(combinations)
        eligible=group[(group.return_2025_pct>0)&(group.max_dd_2025<=6)]
        if len(eligible):
            ranked=eligible.sort_values(["profitable_days_2025","return_2025_pct","max_dd_2025"],
                                        ascending=[False,False,True])
        else:
            ranked=group.sort_values(["return_2025_pct","profitable_days_2025"],
                                     ascending=[False,False])
        chosen=ranked.iloc[0].to_dict()
        eidx=int(chosen["event_index"]);fidx=int(chosen["fallback_index"])
        daily,monthly=display_ledger(raw,eidx,fidx,info,mode)
        daily.to_csv(OUT/(mode+"_2025_selected_477_daily.csv"),index=False)
        monthly.to_csv(OUT/(mode+"_2025_selected_22_months.csv"),index=False)
        # The existing Step6 exact result is published independently.
        olddaily,oldmonthly=display_ledger(raw,0,0,info,mode)
        olddaily.to_csv(OUT/(mode+"_baseline_477_daily.csv"),index=False)
        oldmonthly.to_csv(OUT/(mode+"_baseline_22_months.csv"),index=False)
        group.sort_values("return_2025_pct",ascending=False).head(20).to_csv(
            OUT/(mode+"_top20_train_profit_shortlist.csv"),index=False)
        combined_better=(group.profitable_days>baseline[mode]["profitable_days"]) & (
            group.net_total_pct>baseline[mode]["net_total_pct"]) & (
            group.max_closed_dd_pct<=baseline[mode]["max_closed_dd_pct"])
        optimistic=group.sort_values("net_total_pct",ascending=False).iloc[0].to_dict()
        reported[mode]=dict(
            selected_using_2025_only=chosen,
            shortlist_event_count=len(eventp),
            shortlist_fallback_count=len(fallp),
            shortlisted_pairs=len(group),
            qualified_2025_profitable_and_dd_under_6=int(len(eligible)),
            number_hindsight_pareto_better_than_step6=int(np.sum(combined_better)),
            full_history_hindsight_max_profit_not_selected=optimistic,
            selected_profitable_months=int(np.sum(monthly.net_compounded_pct>0)),
            selected_worst_month_pct=round(float(monthly.net_compounded_pct.min()),5),
            top5_2025_event_exit_only=top_e,
            top5_2025_fallback_exit_only=top_f,
            positive_2025_2026_both=int(np.sum((group.return_2025_pct>0)&(group.return_2026_pct>0)))
        )
        print("STEP7_SELECTED_"+mode.upper()+" "+json.dumps(reported[mode],sort_keys=True),flush=True)
        print("STEP7_MONTHLY_"+mode.upper()+"\n"+monthly.to_string(index=False),flush=True)

    result=pd.DataFrame(rows)
    assert len(result)<=800 and result.trades.eq(477).all()
    result.to_csv(OUT/"all_2025_screened_event_fallback_invalidation.csv",index=False)
    summary=dict(
        task="Causally exit earlier without dropping a single weekday BTCUSD trade",
        source="BTC Analysis 1m 2025-01-01..2026-10-31 UTC authentic continuous OHLCV",
        dates="477 full IST Monday-Friday days Jan2 2025-Oct30 2026",
        models=len(result),predeclared_exit_rules=names,
        selected_2025_only=True,year_2026_previously_research_exposed_not_blind=True,
        event_entries=260,forced_fallback_entries=217,
        original_step6_verified_per_trade=True,baseline=baseline,selected_results=reported,
        execution="stop first if 1m bar touches TP+SL; trailing update valid following bar; 1m CLOSE-based early exits always at NEXT minute OPEN",
        costs="1x notional, 0.05% taker per side+18% GST; if offer previously activated, close taker waived <=30minutes; 5 BTC USD price points adverse slippage each side",
        limitations=["Strong multiple-comparison overfit on 2025 and repeated 2026 analysis",
                     "2026 is NOT unseen independent holdout",
                     "No verified historical offer activation or actual bid/ask depth, funding, margin, fills or latency",
                     "No tick-level sequence; 1m stop-first conservative, close-based exits at subsequent open"])
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
        "# Step7 — BTCUSD every weekday, early trade invalidation",
        "","Exactly 477/477 IST weekday trades. Entry and long/short signals are EXACT Step6 online-selected, identical at individual trade level before exit change.",
        "","## Step6 per-trade parity verified","",json.dumps(baseline,indent=2),
        "","## 2025-only selection and 2026 check","",json.dumps(reported,indent=2),
        "","## Offer chosen 22 months","",
        pd.read_csv(OUT/"scalper_offer_2025_selected_22_months.csv").to_markdown(index=False),
        "","## Standard chosen 22 months","",
        pd.read_csv(OUT/"standard_2025_selected_22_months.csv").to_markdown(index=False),
        "","## Caveats",
        "Shortlist used only 2025 group-only profitability and winning days, with 2025 overall selection; 2026 research-exposed, not pristine independent. No direction change or trade skip; earliest invalidation executes only after previous 1m bar CLOSE. Historical Scalper Offer is assumed."
    ])+"\n")
    print("STEP7_INVALIDATION_COMPLETE",flush=True)

if __name__=="__main__":
    run()
