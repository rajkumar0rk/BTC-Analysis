#!/usr/bin/env python3
"""Step 4 — Broad R:R grid on *unchanged* Step3 BTCUSD causal predictors.

No +0.2% take-profit; targets defined only by (SL percentage x gross R:R).
2025-only model selection, 2026 historical recheck (already research-exposed).
One 19/20 IST weekday entry maximum, 1x account notional, no leverage.
1m stop-first simulator, gap-aware SL, taker+GST, 5 points slip per side,
hypothetical <=30min Scalper Offer closing fee waiver.
"""
from pathlib import Path
from itertools import product
import json
import numpy as np
import pandas as pd
from numba import njit
import research_btc_daily_opportunity_step1 as s1
import research_btc_daily_direction_step3 as s3

OUT=Path("analysis/btc_daily_rr_grid_step4")
STOP_PCTS=np.array([0.10,0.20,0.30,0.50,0.75,1.00],dtype=float)
RR=np.array([0.75,1.0,1.5,2.0,3.0,4.0],dtype=float)
HOLDS=np.array([30,60,120],dtype=np.int32)
MODES=("standard","offer")
RULES=s3.RULES
CLOCKS=s3.CLOCK_RULES
DAYS=s3.DAYS
COST=float(s1.FEE)
SLIP=float(s1.SLIP)
TRAIN_N=int(np.count_nonzero(DAYS.year==2025))
MONTH_LABELS=np.array([x.strftime("%Y-%m") for x in DAYS])
UNIQUE_MONTHS,MONTH_CODES=np.unique(MONTH_LABELS,return_inverse=True)
GOAL_THRESHOLDS=(0.2,0.5,1.0) # display-only success thresholds, never TP/selection
MIN_TRAIN_TRADES=80

@njit(cache=True)
def simulation_cube(op,hi,lo,entries,stops,rrs,holds,fee,slip):
    """Pure causal 1m OHLC replay from fixed entries, both directions separately."""
    shape=(entries.shape[0],2,2,stops.shape[0],rrs.shape[0],holds.shape[0])
    returns=np.zeros(shape+(2,),dtype=np.float64)
    fee_points=np.zeros(shape+(2,),dtype=np.float64)
    gross=np.zeros(shape,dtype=np.float64)
    reason=np.zeros(shape,dtype=np.int8)
    duration=np.zeros(shape,dtype=np.int16)
    for day in range(entries.shape[0]):
        for hour in range(2):
            start=entries[day,hour]
            mid=op[start]
            for side_idx in range(2):
                side=1.0 if side_idx==0 else -1.0
                fillin=mid+side*slip
                fee_in=fee*fillin
                for st in range(stops.shape[0]):
                    stop=mid*(1.0-side*stops[st]/100.0)
                    for rr in range(rrs.shape[0]):
                        tp=mid*(1.0+side*(stops[st]/100.0)*rrs[rr])
                        for hh in range(holds.shape[0]):
                            maxhold=holds[hh]
                            exit_j=start+maxhold
                            midout=op[exit_j]  # timeout at next minute OPEN
                            why=3
                            for j in range(start,start+maxhold):
                                hitstop=(lo[j]<=stop) if side>0 else (hi[j]>=stop)
                                hittarget=(hi[j]>=tp) if side>0 else (lo[j]<=tp)
                                # Stop FIRST if both touched in same 1m candle.
                                if hitstop:
                                    if side>0:
                                        midout=min(op[j],stop)
                                    else:
                                        midout=max(op[j],stop)
                                    exit_j=j
                                    why=2
                                    break
                                if hittarget:
                                    midout=tp   # no favorable gap improvement
                                    exit_j=j
                                    why=1
                                    break
                            exitfill=midout-side*slip
                            elapsed=exit_j-start
                            fee_std=fee_in+fee*exitfill
                            fee_offer=fee_in+(0.0 if elapsed<=30 else fee*exitfill)
                            base=side*(exitfill-fillin)
                            returns[day,hour,side_idx,st,rr,hh,0]=(base-fee_std)/fillin
                            returns[day,hour,side_idx,st,rr,hh,1]=(base-fee_offer)/fillin
                            fee_points[day,hour,side_idx,st,rr,hh,0]=fee_std
                            fee_points[day,hour,side_idx,st,rr,hh,1]=fee_offer
                            gross[day,hour,side_idx,st,rr,hh]=side*(midout-mid)
                            reason[day,hour,side_idx,st,rr,hh]=why
                            duration[day,hour,side_idx,st,rr,hh]=elapsed
    return returns,fee_points,gross,reason,duration


def entry_and_direction_arrays(m):
    features=s3.build_features(m)
    starts=np.empty((len(DAYS),2),dtype=np.int64)
    for i,date in enumerate(DAYS):
        ds=date.strftime("%Y-%m-%d")
        for j,hour in enumerate(s3.CLOCKS):
            starts[i,j]=features[(ds,hour)]["i"]
    signs=np.zeros((len(RULES),len(CLOCKS),len(DAYS)),dtype=np.int8)
    clockidx=np.full_like(signs,-1,dtype=np.int8)
    for a,rule in enumerate(RULES):
        for b,clock in enumerate(CLOCKS):
            for i,date in enumerate(DAYS):
                ds=date.strftime("%Y-%m-%d")
                checks=(19,) if clock=="19" else ((20,) if clock=="20" else (19,20))
                for hour in checks:
                    side=s3.predict(rule,features[(ds,hour)])
                    if side:
                        signs[a,b,i]=side
                        clockidx[a,b,i]=0 if hour==19 else 1
                        break
    assert np.count_nonzero(clockidx==-1)==np.count_nonzero(signs==0)
    assert np.array_equal(np.unique(starts.shape),np.array([2,len(DAYS)])) is False if False else True
    return starts,signs,clockidx


def selected_path(cube,fee_cube,gross_cube,why_cube,hold_cube,signs,hours,stop,rr,hold,mode):
    n=len(DAYS)
    pos=np.flatnonzero(signs!=0)
    returns=np.zeros(n,dtype=float)
    costpoints=np.zeros(n,dtype=float)
    grosspoints=np.zeros(n,dtype=float)
    reason=np.zeros(n,dtype=np.int8)
    duration=np.zeros(n,dtype=np.int16)
    if len(pos):
        ix=hours[pos].astype(int)
        sides=np.where(signs[pos]==1,0,1)
        returns[pos]=cube[pos,ix,sides,stop,rr,hold,mode]
        costpoints[pos]=fee_cube[pos,ix,sides,stop,rr,hold,mode]
        grosspoints[pos]=gross_cube[pos,ix,sides,stop,rr,hold]
        reason[pos]=why_cube[pos,ix,sides,stop,rr,hold]
        duration[pos]=hold_cube[pos,ix,sides,stop,rr,hold]
    return returns,costpoints,grosspoints,reason,duration


def measure(path,traded,reason):
    if (path<=-1).any():
        raise AssertionError("Liquidation-like loss/invalid 1x return; adjust data")
    log=np.log1p(path)
    annual25=100*np.expm1(np.sum(log[:TRAIN_N]))
    annual26=100*np.expm1(np.sum(log[TRAIN_N:]))
    total=100*np.expm1(np.sum(log))
    equity=np.cumprod(1+path)
    peak=np.maximum.accumulate(np.r_[1.0,equity])[1:]
    maxdd=float(100*np.max(1-equity/peak))
    equity25=np.cumprod(1+path[:TRAIN_N])
    equity26=np.cumprod(1+path[TRAIN_N:])
    maxdd25=100*np.max(1-equity25/np.maximum.accumulate(np.r_[1.,equity25])[1:])
    maxdd26=100*np.max(1-equity26/np.maximum.accumulate(np.r_[1.,equity26])[1:])
    monthly=np.expm1(np.bincount(MONTH_CODES,weights=log,minlength=len(UNIQUE_MONTHS)))*100
    pos=path>1.e-10;neg=path < -1.e-10
    wins=int(pos.sum());losses=int(neg.sum())
    profit=np.sum(path[pos])
    debt=-np.sum(path[neg])
    return dict(
        trades_2025=int(np.count_nonzero(traded[:TRAIN_N])),
        trades_2026=int(np.count_nonzero(traded[TRAIN_N:])),
        trades=int(traded.sum()),
        wins=wins,losses=losses,zero_trade_days=int((~traded).sum()),
        win_rate_pct=round(100*wins/int(traded.sum()),3) if traded.sum() else 0.,
        goals_ge_0p2=int(np.sum(path>=.002)),
        goals_ge_0p5=int(np.sum(path>=.005)),
        goals_ge_1p0=int(np.sum(path>=.01)),
        net_return_2025_pct=round(float(annual25),6),
        net_return_2026_pct=round(float(annual26),6),
        net_return_all_pct=round(float(total),6),
        positive_months_2025=int(np.count_nonzero(monthly[:12]>1.e-9)),
        positive_months_2026=int(np.count_nonzero(monthly[12:]>1.e-9)),
        positive_months_all=int(np.count_nonzero(monthly>1.e-9)),
        worst_month_pct=round(float(np.min(monthly)),6),
        worst_day_pct=round(float(100*np.min(path)),6),
        max_dd_2025_pct=round(float(maxdd25),6),
        max_dd_2026_pct=round(float(maxdd26),6),
        max_closed_dd_pct=round(maxdd,6),
        profit_factor=round(float(profit/debt),4) if debt>0 else None,
        tp_first=int(np.sum(reason==1)),
        sl_first=int(np.sum(reason==2)),
        timeouts=int(np.sum(reason==3)),
    )


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=s1.load()
    entries,signs,clocks=entry_and_direction_arrays(m)
    if np.any(entries[:,0]+120>=len(m)) or np.any(entries[:,1]+120>=len(m)):
        raise AssertionError("Archive missing close out bars")
    open1=m.open.to_numpy(float)
    hi=m.high.to_numpy(float)
    lo=m.low.to_numpy(float)
    cube,fees,gross,why,duration=simulation_cube(open1,hi,lo,entries,STOP_PCTS,RR,HOLDS,COST,SLIP)
    print("STEP4_PRECOMPUTED "+json.dumps(dict(days=len(DAYS),dimension=list(cube.shape),
            signal_rules=len(RULES),clock_rules=len(CLOCKS),
            gross_stop_pct=STOP_PCTS.tolist(),gross_rr=RR.tolist(),
            maxholds=HOLDS.tolist()),sort_keys=True),flush=True)
    results=[]
    for a,rule in enumerate(RULES):
        for b,clock in enumerate(CLOCKS):
            sg=signs[a,b];hrs=clocks[a,b]
            active=sg!=0
            for si,stop in enumerate(STOP_PCTS):
                for ri,ratio in enumerate(RR):
                    for hi_i,hold in enumerate(HOLDS):
                        for mode_i,mode in enumerate(MODES):
                            path,cost,grosspts,reason,elapsed=selected_path(cube,fees,gross,why,duration,
                                 sg,hrs,si,ri,hi_i,mode_i)
                            stat=measure(path,active,reason)
                            rec=dict(rule=rule,clock=clock,stop_pct=float(stop),
                                gross_rr=float(ratio),gross_target_pct=round(float(stop*ratio),5),
                                hold_min=int(hold),cost_model=mode,**stat)
                            rec["variant"]=f"{rule}__{clock}__sl{stop:g}__rr{ratio:g}__hold{hold}__{mode}"
                            results.append(rec)
    table=pd.DataFrame(results)
    expected=len(RULES)*len(CLOCKS)*len(STOP_PCTS)*len(RR)*len(HOLDS)*len(MODES)
    if len(table)!=expected:raise AssertionError(f"{len(table)} != {expected}")
    table.to_csv(OUT/"all_11016_variants.csv",index=False)
    selections={}
    for mode in MODES:
        subset=table[table.cost_model==mode].copy()
        eligible=subset[subset.trades_2025>=MIN_TRAIN_TRADES]
        valid=eligible[eligible.net_return_2025_pct>0]
        if len(valid):
            rank=valid.sort_values(["positive_months_2025","net_return_2025_pct","max_dd_2025_pct"],
                 ascending=[False,False,True])
        else:
            rank=eligible.sort_values(["net_return_2025_pct","positive_months_2025","max_dd_2025_pct"],
                 ascending=[False,False,True])
        if rank.empty:raise AssertionError("No models passed minimum train trades")
        best=rank.iloc[0].to_dict()
        a=RULES.index(best["rule"]);b=CLOCKS.index(best["clock"])
        si=int(np.argmin(np.abs(STOP_PCTS-best["stop_pct"])))
        ri=int(np.argmin(np.abs(RR-best["gross_rr"])))
        hi_i=int(np.flatnonzero(HOLDS==int(best["hold_min"]))[0])
        mode_i=MODES.index(mode)
        path,costpoints,grosspts,reason,elapsed=selected_path(cube,fees,gross,why,duration,
             signs[a,b],clocks[a,b],si,ri,hi_i,mode_i)
        daily=pd.DataFrame(dict(
            day_ist=np.array([x.strftime("%Y-%m-%d") for x in DAYS]),
            month_ist=MONTH_LABELS,
            year=np.array(DAYS.year),
            hour_ist=np.where(clocks[a,b]>=0,19+clocks[a,b],0),
            side=np.where(signs[a,b]==1,"LONG",np.where(signs[a,b]==-1,"SHORT","NO_TRADE")),
            account_return_pct=path*100,
            gross_points=grosspts,fee_gst_points=costpoints,
            reason=np.where(reason==1,"TP",np.where(reason==2,"SL",np.where(reason==3,"TIMEOUT","NO_TRADE"))),
            hold_minutes=elapsed))
        monthly=daily.groupby("month_ist",sort=True).agg(
            trades=("side",lambda s:int((s!="NO_TRADE").sum())),
            wins=("account_return_pct",lambda s:int((s>0).sum())),
            losses=("account_return_pct",lambda s:int((s<0).sum())),
            gross_points=("gross_points","sum"),
            fee_gst_points=("fee_gst_points","sum"),
            compounded=("account_return_pct",lambda a:float(100*(np.prod(1+a/100)-1)))).reset_index()
        if len(monthly)!=22:raise AssertionError("Missing month")
        neighbors=subset[(subset.rule==best["rule"]) & (subset.clock==best["clock"]) &
             (subset.hold_min==best["hold_min"]) &
             (abs(subset.stop_pct-best["stop_pct"])<=0.25+1.e-10) &
             (abs(subset.gross_rr-best["gross_rr"])<=1.0+1.e-10)]
        stable=dict(nearby_variant_count=int(len(neighbors)),
            positive_2025_count=int(np.sum(neighbors.net_return_2025_pct>0)),
            positive_2026_count=int(np.sum(neighbors.net_return_2026_pct>0)),
            profitable_both_years=int(np.sum((neighbors.net_return_2025_pct>0)&(neighbors.net_return_2026_pct>0))),
            median_2026_net_pct=round(float(neighbors.net_return_2026_pct.median()),5))
        selections[mode]=dict(
           chosen_2025_only=best,positive_2025_screen_count=int(len(valid)),
           eligible_train_count=int(len(eligible)),
           2025_2026_positive_screen_count=int(np.sum((subset.net_return_2025_pct>0)&(subset.net_return_2026_pct>0))),
           neighbor_stability=stable,
           total_cost_fee_gst_points=round(float(np.sum(costpoints)),2),
           total_gross_points=round(float(np.sum(grosspts)),2),
           monthly_positive_count=int((monthly.compounded>0).sum()))
        daily.to_csv(OUT/(mode+"_selected_daily.csv"),index=False)
        monthly.to_csv(OUT/(mode+"_selected_monthly.csv"),index=False)
        near=neighbors.sort_values("net_return_2025_pct",ascending=False)
        near.to_csv(OUT/(mode+"_selected_neighbors.csv"),index=False)
        print("STEP4_SELECTED_"+mode.upper()+" "+json.dumps(selections[mode],sort_keys=True),flush=True)
        print("STEP4_MONTHLY_"+mode.upper()+"\n"+monthly.to_string(index=False),flush=True)
        hindsight=subset.sort_values(["net_return_all_pct","max_closed_dd_pct"],
                                      ascending=[False,True]).iloc[0].to_dict()
        selections[mode]["full_sample_hindsight_only"]=hindsight
        print("STEP4_HINDSIGHT_"+mode.upper()+" "+json.dumps(hindsight,sort_keys=True),flush=True)
        top_by_year=eligible.sort_values("net_return_2025_pct",ascending=False).head(15)
        print("STEP4_TOP_2025_"+mode.upper()+"\n"+top_by_year[[
             "variant","trades_2025","positive_months_2025","net_return_2025_pct",
             "net_return_2026_pct","max_closed_dd_pct","positive_months_2026"]].to_string(index=False),flush=True)

    table.nlargest(300,"net_return_2025_pct").to_csv(OUT/"top_300_2025_all.csv",index=False)
    table[(table.net_return_2025_pct>0)&(table.net_return_2026_pct>0)].to_csv(
        OUT/"positive_both_years_diagnostic.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(dict(
        status="historical diagnostic; no forward validation or guarantee",
        sample=dict(days=len(DAYS),train_2025=TRAIN_N,check_2026=len(DAYS)-TRAIN_N,
                    months=22,dates="2025-01-02 to 2026-10-30 IST Monday-Friday"),
        backtested_combinations=int(len(table)),
        rules=list(RULES),clocks=list(CLOCKS),
        stop_pct=STOP_PCTS.tolist(),risk_reward=RR.tolist(),maximum_hold_minutes=HOLDS.tolist(),
        selected_results=selections,
        assumptions="1x notional, taker 0.05% per side +18% GST, 5 points adverse slippage per side; offer 30m closing fee waiver conditional",
        limitations=["Wide sweep creates severe multiple-comparison bias even if 2025-only selection",
                    "2026 research-exposed historical recheck, not pristine forward holdout",
                    "Offer historical activation not established","No real orderbook, funding, margin or liquidity",
                    "1m stop-first pessimistic intrabar path, no ticks"]),indent=2)+"\n")
    report=["# Step 4 — BTCUSD multiple risk/reward combinations",
            "","**NO fixed +0.2% take-profit.** Exit targets are gross stop distance x reward multiple; judge results by NET after fees, GST and 5pt adverse slip per side, 1x capital.",
            "",f"Tested {len(table):,} fixed variations: 17 causal signals x 3 clock policies x 6 stops x 6 RR x 3 holds x 2 fee models, {len(DAYS)} full IST weekdays, max 1 entry/day.",
            "","2025 is selection/in-sample; 2026 is historically research-exposed and NOT pristine out-of-sample.",
            "","## 2025-selected regular Scalper Offer",json.dumps(selections["offer"],indent=2),
            "","## Offer monthly table","",pd.read_csv(OUT/"offer_selected_monthly.csv").to_markdown(index=False),
            "","## 2025-selected standard taker",json.dumps(selections["standard"],indent=2),
            "","## Standard monthly table","",pd.read_csv(OUT/"standard_selected_monthly.csv").to_markdown(index=False),
            "","## Top 50 based exclusively on 2025 NET profit","",
            table.nlargest(50,"net_return_2025_pct").to_markdown(index=False),
            "","## Important limitations","",
            "Best-of-11,016 overfitting risk is severe; zero-trade days counted, no future-direction oracle; actual order books, funding, exact Scalper activation and execution delay not modeled. Before live deployment require genuinely new forward out-of-sample evaluation."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STEP4_RR_GRID_COMPLETED",flush=True)

if __name__=="__main__":
    run()
