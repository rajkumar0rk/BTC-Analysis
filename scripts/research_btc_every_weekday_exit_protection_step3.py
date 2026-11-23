#!/usr/bin/env python3
"""Step 3: improve BTCUSD exits WITHOUT deleting a single IST weekday trade.

Frozen entry policies from research_btc_every_weekday_adaptive_step2. Static TP/SL
versus causal 1m stepped lock, trailing stop and step-up lock. Each new stop update
is valid only on the *next* 1m bar, so no retroactive same-minute trailing fills.
"""
from pathlib import Path
from itertools import product
import json
import numpy as np
import pandas as pd
from numba import njit
import research_btc_every_weekday_reset_step1 as base
import research_btc_every_weekday_adaptive_step2 as entry

OUT=Path("analysis/btc_every_weekday_exit_protection_step3")
DAYS=base.DAYS
TWO_POLICIES=(
    ("fixed19_fade5","fixed","fixed"),
    ("vol5_fade","us_only","follow60"),
)
SLS=(0.15,0.30,0.50,0.75,1.00)
FIXED_TPS=(0.25,0.50,1.0,2.0,3.0)
TIMEOUTS=(10,20,30)
DYNAMIC_TPS=(1.0,3.0)
LOCK_ACTIVATE=(0.15,0.25,0.40,0.60)
LOCK_VALUES=(0.05,0.10,0.20)
TRAIL_ACTIVATE=(0.20,0.35,0.50,0.75)
TRAIL_DISTANCE=(0.10,0.20,0.30,0.50)
STEP_ACTIVATE=(0.20,0.35)
STEP_SIZE=(0.20,0.30)
STEP_LOCK=(0.05,0.10)
MODELS=("standard","scalper_offer")

# Each config: kind(0 static,1 lock,2 trailing,3 step), sl, tp, hold,
# activation, lock_or_trailing_distance, step_size. All percentages are
# BTC mid-entry gross price changes, not net return targets.
def build_configs():
    rows=[];names=[]
    def add(kind,sl,tp,hold,act,lock,step):
        rows.append((float(kind),sl,tp,float(hold),act,lock,step))
        names.append(
            f"{('static','lock','trailing','stepup')[kind]}__sl{sl:g}__tp{tp:g}"
            f"__hold{hold}__activation{act:g}__value{lock:g}__step{step:g}")
    for sl,tp,hold in product(SLS,FIXED_TPS,TIMEOUTS):
        add(0,sl,tp,hold,0.,0.,0.)
    for sl,tp,act,lock in product(SLS,DYNAMIC_TPS,LOCK_ACTIVATE,LOCK_VALUES):
        if lock<act:add(1,sl,tp,30,act,lock,0.)
    for sl,tp,act,trail in product(SLS,DYNAMIC_TPS,TRAIL_ACTIVATE,TRAIL_DISTANCE):
        add(2,sl,tp,30,act,trail,0.)
    for sl,tp,act,step,lock in product(SLS,DYNAMIC_TPS,STEP_ACTIVATE,STEP_SIZE,STEP_LOCK):
        if lock<act:add(3,sl,tp,30,act,lock,step)
    assert len(set(names))==len(names)
    return np.asarray(rows,dtype=float),names


@njit(cache=True)
def run_exit_grid(op,hi,lo,entry_idx,entry_hours,signs,config,fee_rate,slippage):
    n=len(entry_idx);q=len(config)
    ret=np.zeros((n,q,2),dtype=np.float64)
    fees=np.zeros((n,q,2),dtype=np.float64)
    gross=np.zeros((n,q),dtype=np.float64)
    reasons=np.zeros((n,q),dtype=np.int8)
    duration=np.zeros((n,q),dtype=np.int16)
    # 1m OHLC, 1 position/day. No re-entry after exit.
    for d in range(n):
        j0=int(entry_idx[d])
        side=float(signs[d])
        mid=op[j0]
        fillin=mid+side*slippage
        opening_fee=fee_rate*fillin
        for qidx in range(q):
            kind=int(config[qidx,0])
            sl=config[qidx,1]*.01
            tp=config[qidx,2]*.01
            hold=int(config[qidx,3])
            activation=config[qidx,4]*.01
            adjustment=config[qidx,5]*.01
            step=config[qidx,6]*.01
            hardstop=mid*(1.-side*sl)
            working_stop=hardstop
            target=mid*(1.+side*tp)
            best_favorable=0.
            exit_j=j0+hold
            midout=op[exit_j] # timeout at NEXT minute OPEN exactly at hold.
            why=3
            for t in range(hold):
                j=j0+t
                # First check the PREVIOUS minute's settled protective stop.
                stopped=lo[j]<=working_stop if side>0 else hi[j]>=working_stop
                targethit=hi[j]>=target if side>0 else lo[j]<=target
                if stopped:
                    midout=min(op[j],working_stop) if side>0 else max(op[j],working_stop)
                    exit_j=j;why=2;break
                if targethit:
                    midout=target
                    exit_j=j;why=1;break
                # Determine new stops from the bar that just completed.
                # Such stop becomes live for t+1 only, not this bar.
                favorable=(hi[j]-mid)/mid if side>0 else (mid-lo[j])/mid
                if favorable>best_favorable:best_favorable=favorable
                newstop=working_stop
                if kind==1:
                    # One-step profit lock, never loosen.
                    if best_favorable>=activation:
                        locklevel=mid*(1.+side*adjustment)
                        if side>0 and locklevel>newstop:newstop=locklevel
                        if side<0 and locklevel<newstop:newstop=locklevel
                elif kind==2:
                    # Continuous ratcheting stop, enabled from activation.
                    if best_favorable>=activation:
                        traillevel=mid*(1.+side*(best_favorable-adjustment))
                        if side>0 and traillevel>newstop:newstop=traillevel
                        if side<0 and traillevel<newstop:newstop=traillevel
                elif kind==3:
                    if best_favorable>=activation:
                        steps=int((best_favorable-activation+1.e-12)/step)
                        level=adjustment+steps*step
                        locklevel=mid*(1.+side*level)
                        if side>0 and locklevel>newstop:newstop=locklevel
                        if side<0 and locklevel<newstop:newstop=locklevel
                working_stop=newstop
            fillout=midout-side*slippage
            elapsed=exit_j-j0
            close_fee=fee_rate*fillout
            standard_fee=opening_fee+close_fee
            offer_fee=opening_fee+(0. if elapsed<=30 else close_fee)
            g=side*(midout-mid)
            after_slip=side*(fillout-fillin)
            ret[d,qidx,0]=(after_slip-standard_fee)/fillin
            ret[d,qidx,1]=(after_slip-offer_fee)/fillin
            fees[d,qidx,0]=standard_fee
            fees[d,qidx,1]=offer_fee
            gross[d,qidx]=g
            reasons[d,qidx]=why
            duration[d,qidx]=elapsed
    return ret,fees,gross,reasons,duration


def summary_stats(p,c,g,r,hold):
    if not np.isfinite(p).all() or len(p)!=len(DAYS):
        raise AssertionError("All 477 daily account returns required")
    z=base.score(p,c,g,np.full(len(p),2*base.SLIP),r)
    z["max_dd_2025_pct"]=entry.period_dd(p[:base.NTRAIN])
    z["max_dd_2026_pct"]=entry.period_dd(p[base.NTRAIN:])
    z["max_consecutive_losses"]=base.max_loss_run(p<0)
    z["mean_hold_minutes"]=round(float(np.mean(hold)),3)
    z["qualifying_30min_exits"]=int((hold<=30).sum())
    return z


def outcome(path,fees,gross,reasons,holds,hours,signs,fallback,policy):
    return pd.DataFrame(dict(day_ist=base.IST_DAYS,month_ist=base.MONTH_LABELS,
        year=np.asarray(DAYS.year),entry_hour_ist=hours.astype(int),
        side=np.where(signs==1,"LONG","SHORT"),
        fallback_21h=fallback,entry_policy=policy,
        account_net_pct=100*path,gross_points=gross,fee_gst_points=fees,
        adverse_slip_points=2*base.SLIP,hold_minutes=holds,
        exit_reason=np.where(reasons==2,"STOP",np.where(reasons==1,"TARGET","TIMEOUT"))))


def write_candidate(table,dir_signs,config,param_index,policy,mode,ret,fees,gross,reason,hold):
    cfg=config[param_index]
    p=ret[:,param_index,mode]
    c=fees[:,param_index,mode]
    g=gross[:,param_index]
    r=reason[:,param_index]
    elapsed=hold[:,param_index]
    pol_idx=entry.POLICIES.index(policy)
    daily=outcome(p,c,g,r,elapsed,dir_signs[0],dir_signs[1],
        dir_signs[2],str(policy))
    monthly=daily.groupby("month_ist",sort=True).agg(
        trades=("day_ist","size"),
        winning_days=("account_net_pct",lambda x:int((x>0).sum())),
        losing_days=("account_net_pct",lambda x:int((x<0).sum())),
        monthly_net_pct=("account_net_pct",lambda x:float(100*(np.prod(1+x/100)-1))),
        gross_points=("gross_points","sum"),
        fees_gst_points=("fee_gst_points","sum")).reset_index()
    if len(daily)!=477 or len(monthly)!=22:
        raise AssertionError("Coverage lost")
    return daily,monthly


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=base.load()
    idx,_,_=base.prepare(m)
    f=entry.build_completed_candle_features(m,idx)
    hours_all,side_all,fback_all=entry.choose_all_policy_entries(f)
    cfg,names=build_configs()
    expected=len(cfg)*len(TWO_POLICIES)*2
    allrows=[]
    stored={}
    for pol in TWO_POLICIES:
        pi=entry.POLICIES.index(pol)
        h=hours_all[pi].astype(int)
        s=side_all[pi]
        fb=fback_all[pi]
        starts=idx[np.arange(len(DAYS)),h]
        if len(np.unique(base.IST_DAYS))!=477 or (s==0).any():
            raise AssertionError("Missing required daily entry")
        if (h>21).any() or (h<9).any():
            raise AssertionError("Entry outside prior expected schedule")
        if (h*60+30>1439).any():
            raise AssertionError("Selected 30-minute trade crosses IST date")
        r,c,g,why,hold=run_exit_grid(
            m.open.to_numpy(float),m.high.to_numpy(float),m.low.to_numpy(float),
            starts,h,s,cfg,base.COST,base.SLIP)
        for i,label in enumerate(names):
            for mode_i,mode in enumerate(MODELS):
                stat=summary_stats(r[:,i,mode_i],c[:,i,mode_i],g[:,i],why[:,i],hold[:,i])
                row=dict(policy="__".join(pol),kind=("static","lock","trailing","stepup")[int(cfg[i,0])],
                    config_index=i,config=label,stop_pct=float(cfg[i,1]),
                    gross_tp_pct=float(cfg[i,2]),
                    max_hold_min=int(cfg[i,3]),activation_pct=float(cfg[i,4]),
                    lock_or_distance_pct=float(cfg[i,5]),step_pct=float(cfg[i,6]),
                    cost_model=mode,**stat)
                allrows.append(row)
        stored["__".join(pol)]=(pol,(h,s,fb),r,c,g,why,hold)
    results=pd.DataFrame(allrows)
    if len(results)!=expected or not results.trades.eq(477).all():
        raise AssertionError("Unexpected size or missed weekday entries")
    results.to_csv(OUT/"all_exit_variants.csv",index=False)
    print("STEP3_EXIT_GRID "+json.dumps(dict(policies=len(TWO_POLICIES),
          exit_configs_each=len(cfg),both_fee_variants=len(results),
          all_weekdays_each=int(results.trades.min())),sort_keys=True),flush=True)
    baselines={}
    for policy,polidx,baselineTP in [
        ("fixed19_fade5__fixed__fixed",0,1.0),
        ("vol5_fade__us_only__follow60",1,3.0)]:
        z=results[(results.policy==policy)&(results.kind=="static")&
            (results.stop_pct==1.0)&(results.gross_tp_pct==baselineTP)&
            (results.max_hold_min==30)&(results.cost_model=="scalper_offer")]
        if len(z)!=1:raise AssertionError("Missing previous unchanged strategy baseline")
        bv=z.iloc[0].to_dict()
        exact=-1.156951 if polidx==0 else 8.222995
        if abs(bv["net_total_pct"]-exact)>0.00010:
            raise AssertionError("Old replay parity failed: "+str((bv["net_total_pct"],exact)))
        baselines[policy]=bv
        print("STEP3_BASELINE_"+str(polidx)+" "+json.dumps(bv,sort_keys=True),flush=True)

    comparisons={}
    for pol in TWO_POLICIES:
        key="__".join(pol)
        _,parts,r,c,g,why,hold=stored[key]
        for mode_i,mode in enumerate(MODELS):
            z=results[(results.policy==key)&(results.cost_model==mode)]
            valid=z[(z.return_2025_pct>0)&(z.max_dd_2025_pct<=15)]
            if len(valid):
                ranked=valid.sort_values(
                    ["profitable_days_2025","return_2025_pct","max_dd_2025_pct"],
                    ascending=[False,False,True])
            else:
                ranked=z.sort_values(["return_2025_pct","profitable_days_2025"],
                    ascending=[False,False])
            best=ranked.iloc[0].to_dict()
            i=int(best["config_index"])
            p=r[:,i,mode_i]
            daily,monthly=write_candidate(z,parts,cfg,i,pol,mode_i,r,c,g,why,hold)
            fname=key+"__"+mode
            daily.to_csv(OUT/(fname+"_selected_477_daily.csv"),index=False)
            monthly.to_csv(OUT/(fname+"_selected_22_months.csv"),index=False)
            baseline_std=z[(z.kind=="static")&(z.stop_pct==1.)&
                (z.gross_tp_pct==(1. if key.startswith("fixed19") else 3.))&
                (z.max_hold_min==30)].iloc[0].to_dict()
            hindsight=z.sort_values("net_total_pct",ascending=False).iloc[0].to_dict()
            both=(z.return_2025_pct>0)&(z.return_2026_pct>0)
            improving=z[(z.profitable_days_2025>baseline_std["profitable_days_2025"])&
                (z.profitable_days_2026>baseline_std["profitable_days_2026"])&
                (z.return_2025_pct>baseline_std["return_2025_pct"])&
                (z.return_2026_pct>baseline_std["return_2026_pct"])]
            samekind=z[z.kind==best["kind"]]
            nearest=samekind[(abs(samekind.stop_pct-best["stop_pct"])<=.25+1e-10)&
                (abs(samekind.gross_tp_pct-best["gross_tp_pct"])<=1.+1e-10)]
            block=dict(
                selected_from_2025_only=best,
                baseline_same_policy_same_cost=baseline_std,
                has_positive_2025_candidate=bool(len(valid)),
                eligible_2025_positive_candidates=int(len(valid)),
                best_full_history_hindsight_NOT_selected=hindsight,
                positive_both_years_hindsight=int(both.sum()),
                improved_win_days_AND_net_both_years_vs_baseline_hindsight=int(len(improving)),
                adjacent_configs=len(nearest),
                adjacent_positive_2025=int((nearest.return_2025_pct>0).sum()),
                adjacent_positive_2026=int((nearest.return_2026_pct>0).sum()),
                selected_winning_months_2025=int((monthly.monthly_net_pct>0).sum()),
                selected_2025_profitable_days=int((p[:base.NTRAIN]>0).sum()),
                selected_2026_profitable_days=int((p[base.NTRAIN:]>0).sum()))
            comparisons[fname]=block
            print("STEP3_EXIT_SELECTED_"+fname.upper()+" "+json.dumps(block,sort_keys=True),flush=True)
            print("STEP3_EXIT_MONTHLY_"+fname.upper()+"\n"+monthly.to_string(index=False),flush=True)
    (OUT/"summary.json").write_text(json.dumps(dict(
        task="Improve exit quality without reducing 1 trade per Monday-Friday",
        rules="unchanged 2 pre-existing causal entry policies, 477 trades each",
        test_period="2025-01-02..2026-10-30 IST weekdays, full 1m archive",
        config_count=len(cfg),variant_count=len(results),
        cost_assumptions="Standard 0.05% taker/leg +18% GST; eligible regular Scalper Offer closing fee+GST waiver <=30m; 5 BTC points adverse slippage each leg; 1x notional",
        selection="2025 only; 2026 already research-exposed and not pristine forward holdout",
        no_lookahead="stop first in same minute; dynamic stop set from completed prior 1m bar only",
        exact_unmodified_baselines=baselines,selected_results=comparisons,
        caveats=["Offer historical activation not verified","No true tick ordering, orderbook spread, funding, latency or liquidation",
                 "Multiple-comparison risk even with 2025 selection; full-period hindsight is not deployable"]),indent=2)+"\n")
    report=["# BTCUSD Mandatory-Daily Step 3 — Exit protection backtest",
            "","Exactly 477 entries (260 in 2025, 217 in 2026) for each model. No trading Saturday/Sunday. Same frozen entries from previous step; exit logic is the only changed variable.",
            "",f"{len(cfg)} exit designs × 2 frozen entry rules × standard and hypothetical scalper fees = {len(results)} configurations.",
            "","## Exact historical baseline parity",json.dumps(baselines,indent=2),
            "","## Train 2025 selection / 2026 recheck",json.dumps(comparisons,indent=2),
            "","## Complete comparison",results.to_markdown(index=False),
            "","## Notes","No future intrabar high can retroactively tighten a stop during that minute; protective stops updated only after the bar. Entry selection was already exposed to 2026 and could be overfit; no genuine forward validation."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STEP3_EXIT_PROTECTION_COMPLETE",flush=True)

if __name__=="__main__":run()
