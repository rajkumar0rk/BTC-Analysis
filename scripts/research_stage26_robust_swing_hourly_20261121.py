#!/usr/bin/env python3
"""Stage26 - robust BTCUSD 4H Donchian and 1H EMA20 research.

Runs actual full 1-minute BTCUSD stop-first execution, original modeled Delta
India taker fee / GST / 5 BTC points per side, AND additional adverse 2/5bp
per side. Unlike Stage25, the 4H swing engine is also stress-tested on every
trade and marked-to-market at every IST month end.

Selection scores and filters use only 2025. 2026 is NOT an untouched holdout,
because it has been researched extensively. Never deploy or enable real orders.

Both series are standalone. Synthetic monthly capital-blend comparisons are
explicitly NOT shared margin-aware execution simulations.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit
from research_every_candle_200 import read_archive, FEE, SLIPPAGE
import research_swing_donchian_stage17 as swing
import research_new_1h_patterns_stage19 as hourly
from research_structure_rr_stage11 import replay_one
from research_stage25_optimize_five_negative_sleeves_20261121 import monthly_exit_replay

OUT=Path("analysis/stage26_robust_swing_hourly_20261121")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
BASELINE=Path("/tmp/stage18-70-30/scenario_monthly_22.csv")
EPS=1e-9

@njit(cache=True)
def swing_stressed(O,H,L,C,T,month_id,seg_start,signal,updates,atr,ref_close,
                   trail_mult,init_stop_atr,hold_minutes,extra_bps,n_months):
    equity=100.
    open_equity=equity
    entry_fill=0.
    entry_mid=0.
    entry_k=-1
    entry_risk=0.
    stop=0.
    side=0
    month_end=np.full(n_months,np.nan)
    entries=np.zeros(n_months,np.int32)
    total_trades=0
    one_bps=extra_bps/10000.
    for k in range(len(O)):
        # Match historical Stage17 treatment of discontinuous archive segments.
        if k>0 and seg_start[k]==k and side!=0:
            old=k-1
            mid=C[old]
            fill=mid-side*(SLIPPAGE+mid*one_bps)
            net=side*(fill-entry_fill)-FEE*(entry_fill+fill)
            equity=open_equity*(1+.005*net/entry_risk)
            total_trades+=1
            side=0
        reverse=False
        if side!=0 and updates[k] and np.isfinite(atr[k]):
            trail=ref_close[k]-side*trail_mult*atr[k]
            if side==1 and trail>stop:stop=trail
            if side==-1 and trail<stop:stop=trail
        if side!=0:
            hit=(L[k]<=stop) if side==1 else (H[k]>=stop)
            if hit:
                mid=min(O[k],stop) if side==1 else max(O[k],stop)
                reason=0
            elif k-entry_k>=hold_minutes:
                mid=O[k]
                reason=1
            elif signal[k]==-side:
                mid=O[k]
                reason=2
                reverse=True
            else:
                reason=-1
            if reason>=0:
                fill=mid-side*(SLIPPAGE+mid*one_bps)
                net=side*(fill-entry_fill)-FEE*(entry_fill+fill)
                equity=open_equity*(1+.005*net/entry_risk)
                total_trades+=1
                side=0
        if side==0 and not reverse and signal[k]!=0 and np.isfinite(atr[k]):
            risk=init_stop_atr*atr[k]
            if 100<=risk<=10000:
                side=int(signal[k])
                entry_mid=O[k]
                entry_fill=entry_mid+side*(SLIPPAGE+entry_mid*one_bps)
                entry_risk=risk
                stop=entry_mid-side*risk
                entry_k=k
                open_equity=equity
                entries[month_id[k]]+=1
        if k==len(O)-1 or month_id[k+1]!=month_id[k]:
            marked=equity
            if side!=0:
                mid=C[k]
                fill=mid-side*(SLIPPAGE+mid*one_bps)
                net=side*(fill-entry_fill)-FEE*(entry_fill+fill)
                marked=open_equity*(1+.005*net/entry_risk)
            month_end[month_id[k]]=marked
    return month_end,entries,total_trades

def monthly_from_equity(eq):
    x=np.asarray(eq[:22],float)
    if len(x)!=22 or not np.isfinite(x).all() or (x<=0).any():
        raise AssertionError("Invalid swing MTM series")
    return 100*(x/np.r_[100,x[:-1]]-1)

def stats(a):
    a=np.asarray(a,float)
    q=np.cumprod(1+a/100)
    peak=np.maximum.accumulate(np.r_[1.,q])[1:]
    return dict(total_pct=float(100*(q[-1]-1)),
        profitable_months=int((a>EPS).sum()),
        loss_months=int((a<-EPS).sum()),
        flat_months=int((abs(a)<=EPS).sum()),
        train_2025_pct=float(100*(np.prod(1+a[:12]/100)-1)),
        first6_2025_pct=float(100*(np.prod(1+a[:6]/100)-1)),
        second6_2025_pct=float(100*(np.prod(1+a[6:12]/100)-1)),
        seen_2026_JanOct_pct=float(100*(np.prod(1+a[12:]/100)-1)),
        seen_2026_profitable_months=int((a[12:]>EPS).sum()),
        worst_month_pct=float(a.min()),
        max_monthend_drawdown_pct=float(100*np.max(1-q/peak)),
        train_2025_max_monthend_dd_pct=float(100*np.max(
           1-q[:12]/np.maximum.accumulate(np.r_[1.,q[:12]])[1:])))

def train_ranking(s):
    # All input metrics from 2025 ONLY at +5bp adverse SLIPPAGE, not future.
    return (float(s["train_2025_pct"]) -
            .6*float(s["train_2025_max_monthend_dd_pct"]) +
            .10*sum(x>EPS for x in s.get("train_monthly",[])))

def record(rows,series,group,name,params,train_trades,trades_22,
           values,baseline=False):
    base=stats(values[0]);stress=stats(values[5])
    data=dict(group=group,model=name,params=json.dumps(params,sort_keys=True),
       is_baseline=baseline,train_trades=int(train_trades),
       trades_22=int(trades_22),
       **{f"base_{k}":v for k,v in base.items()},
       **{f"stress5_{k}":v for k,v in stress.items()})
    data["train_rank_score"]=(
        stress["train_2025_pct"]-.6*stress["train_2025_max_monthend_dd_pct"]+
        .10*int((values[5][:12]>EPS).sum()))
    data["train_halves_positive_stress5"]=bool(
        stress["first6_2025_pct"]>0 and stress["second6_2025_pct"]>0)
    rows.append(data)
    for cost in (0,5):
        arr=values[cost]
        for i,m in enumerate(MONTHS):
            series.append(dict(group=group,model=name,month_ist=m,
               extra_bps_per_side=cost,return_pct=float(arr[i])))
    return data

def optimize_4h(f,segstart):
    month_code,all_months=swing.build_months(f)
    if MONTHS!=all_months[:22]:raise AssertionError("4H months do not match")
    O=f.open.to_numpy(float);H=f.high.to_numpy(float)
    L=f.low.to_numpy(float);C=f.close.to_numpy(float);T=f.time.to_numpy(np.int64)
    bars=swing.higher_bars(f,"4H")
    rows=[];series=[]
    for channel in (16,20,24,30,40,55):
        for trend in ("ema50_agrees","no_trend_filter"):
            signal,updates,atr,ref_close,n=swing.signals(f,bars,channel,trend)
            for stop_atr in (1.5,2.0,2.5):
                for trail in (2.0,2.5,3.0,3.5):
                    for maxhold in (7*1440,14*1440):
                        name=f"4H_ch{channel}_{trend}_SL{stop_atr:g}_trail{trail:g}_hold{maxhold//1440}d"
                        eq0,ent0,total0=swing_stressed(O,H,L,C,T,month_code,segstart,
                            signal,updates,atr,ref_close,trail,stop_atr,maxhold,0,len(all_months))
                        eq5,ent5,total5=swing_stressed(O,H,L,C,T,month_code,segstart,
                            signal,updates,atr,ref_close,trail,stop_atr,maxhold,5,len(all_months))
                        if total0!=total5 or not np.array_equal(ent0,ent5):
                            raise AssertionError("Changed entry signals with fee stress")
                        baseline=(channel==55 and trend=="ema50_agrees" and
                                  stop_atr==2.0 and trail==3.0 and maxhold==14*1440)
                        if baseline:
                            ref,_,_,_,_=swing.run_one(O,H,L,C,T,month_code,segstart,
                                 signal,updates,atr,ref_close,3.0,len(all_months))
                            max_delta=float(np.max(np.abs(ref-eq0)))
                            if max_delta>1e-7:
                                raise AssertionError(f"Original Stage17 4H parity failed {max_delta}")
                            print("4H_ORIGINAL_ENGINE_PARITY",json.dumps(dict(max_equity_delta=max_delta)))
                        p=dict(channel=channel,EMA50=trend=="ema50_agrees",stop_atr=stop_atr,
                               trail_atr=trail,hold_days=maxhold//1440,
                               original_signal_count=n)
                        record(rows,series,"4H_DONCHIAN",name,p,int(ent0[:12].sum()),
                             total0,{0:monthly_from_equity(eq0),
                                     5:monthly_from_equity(eq5)},baseline)
    return rows,series

def optimize_1h(f,segend):
    ev=hourly.build_candidates(f,segend)
    e=ev[(ev.pattern=="ema20_pullback_confirm")&(ev.side==1)].copy()
    if len(e)<100:raise AssertionError("Missing 1H long candidate pool")
    O=f.open.to_numpy(float);H=f.high.to_numpy(float);L=f.low.to_numpy(float)
    C=f.close.to_numpy(float);T=f.time.to_numpy(np.int64)
    rows=[];series=[]
    for min_eff in (.20,.25,.30,.35,.40):
        for adx in ("any","le25","ge20"):
            for minrisk in (125.,300.,500.,700.):
                allowed=e[(e.h4_eff8>=min_eff)&(e.risk>=minrisk)]
                if adx=="le25":allowed=allowed[allowed.h4_adx<=25]
                if adx=="ge20":allowed=allowed[allowed.h4_adx>=20]
                for reward in (4.,5.,6.,7.):
                    for hold in (360,480,720):
                        name=f"H1_EMA_LONG_eff{min_eff:.2f}_{adx}_risk{minrisk:g}_{reward:g}R_{hold}min"
                        busy=-1;tr=[]
                        for z in allowed.itertuples(index=False):
                            k=int(z.k)
                            if k<=busy or segend[k]-k<hold:continue
                            j,reason,gross,net,offer,netR,risk=replay_one(
                                O,H,L,C,k,1,float(z.stop),reward,hold)
                            busy=int(j)
                            tr.append((int(z.unix),int(T[j]),float(risk),
                                       float(O[k]),float(netR)))
                        b0,by0,train0=monthly_exit_replay(tr,0)
                        b5,by5,train5=monthly_exit_replay(tr,5)
                        baseline=(min_eff==.30 and adx=="any" and minrisk==125
                                  and reward==5 and hold==480)
                        if baseline:
                            if abs(stats(b0)["total_pct"]-7.66400712106)>.01:
                                raise AssertionError(f"Stage25 1H baseline mismatch {stats(b0)}")
                            print("1H_STAGE25_BASELINE_PARITY",json.dumps(dict(
                                net_pct=stats(b0)["total_pct"],trades=len(tr),stress5_pct=stats(b5)["total_pct"])))
                        p=dict(pattern="ema20_pullback_confirm",direction="LONG",
                           h4_efficiency_min=min_eff,adx_filter=adx,
                           stop_risk_points_min=minrisk,R_target=reward,max_hold_min=hold)
                        record(rows,series,"1H_EMA20_LONG",name,p,train0,len(tr),
                                {0:b0,5:b5},baseline)
    return rows,series

def select_and_report(rows,series):
    df=pd.DataFrame(rows)
    mon=pd.DataFrame(series)
    # For 4H: 2025 participation >=20 trades; for H1 >=30.
    winners={}
    for group,z in df.groupby("group"):
        b=z[z.is_baseline]
        if len(b)!=1:raise AssertionError(f"Original {group} baseline count {len(b)}")
        mintrades=20 if group=="4H_DONCHIAN" else 30
        eligible=z[(z.train_trades>=mintrades)&
           (z.stress5_train_2025_pct>0)]
        if eligible.empty:
            winners[group]=b.iloc[0].to_dict()
            winners[group]["new_candidate_found"]=False
            print("NO_POSITIVE_2025_STRESS5_CANDIDATE",group)
        else:
            # 2025 ONLY rank. Favor both halves positive if any.
            both=eligible[eligible.train_halves_positive_stress5]
            pool=both if not both.empty else eligible
            best=pool.sort_values(["train_rank_score","train_trades"],ascending=False).iloc[0]
            winners[group]=best.to_dict()
            winners[group]["new_candidate_found"]=True
        print("SELECTED_FROM_2025_ONLY",json.dumps(winners[group],default=str))
        print("REPLAYED_BASELINE",json.dumps(b.iloc[0].to_dict(),default=str))

    df.to_csv(OUT/"all_optimized_swing_hourly_5bps.csv",index=False)
    mon.to_csv(OUT/"all_variants_monthly_0bps_5bps.csv.gz",compression="gzip",index=False)
    selectdf=pd.DataFrame(winners.values())
    selectdf.to_csv(OUT/"selected_2025_only_and_2026_results.csv",index=False)
    for g,row in winners.items():
        vals=mon[(mon.group==g)&(mon.model==row["model"])].copy()
        vals.to_csv(OUT/(g.lower()+"_2025selected_monthly.csv"),index=False)

    # Monthly simple blending, same independent return sources, not a shared
    # order book or margin account.
    bp=pd.read_csv(BASE)
    models={}
    for bps in (0,5):
        group=bp[(bp.scenario=="stage18_70_30_30d")&(bp.extra_bps_side==bps)].copy()
        group=group.set_index("month_ist").reindex(MONTHS)
        if group.portfolio_month_pct.isna().any():raise AssertionError("70/30 source missing")
        models[("base",bps)]=group.portfolio_month_pct.to_numpy(float)
        for g,row in winners.items():
            month=mon[(mon.group==g)&(mon.model==row["model"])&
                       (mon.extra_bps_per_side==bps)].set_index("month_ist").reindex(MONTHS)
            if month.return_pct.isna().any():raise AssertionError("Selected monthly missing")
            models[(g,bps)]=month.return_pct.to_numpy(float)

    portfolios=[];pmonth=[]
    # Allow baseline >=70% and each extra<=20%, never use future months to
    # choose weights. Fixed weights across every single month; no hindsight
    # switches / omissions.
    for w4 in (0,.05,.10,.15,.20):
        for w1 in (0,.05,.10,.15,.20):
            if w4+w1>.3+1e-9:continue
            anchor=1-w4-w1
            for bps in (0,5):
                r=(anchor*models[("base",bps)]+
                   w4*models[("4H_DONCHIAN",bps)]+
                   w1*models[("1H_EMA20_LONG",bps)])
                s=stats(r)
                name=f"base{anchor:.2f}_swing{w4:.2f}_hour{w1:.2f}"
                portfolios.append(dict(name=name,base_weight=anchor,swing_weight=w4,
                                      hourly_weight=w1,extra_bps_side=bps,**s))
                for mo,v in zip(MONTHS,r):
                    pmonth.append(dict(name=name,extra_bps_side=bps,month_ist=mo,
                                       return_pct=v))
    port=pd.DataFrame(portfolios)
    port.to_csv(OUT/"portfolio_fixed_weight_comparison.csv",index=False)
    pd.DataFrame(pmonth).to_csv(OUT/"portfolio_fixed_weight_monthly.csv",index=False)

    # Choose on 2025 cost stressed only, exact fixed weights. Predeclare
    # train criterion: net return penalized max drawdown, plus winning months.
    train=port[port.extra_bps_side==5].copy()
    train["selection"]=train.train_2025_pct-.5*train.train_2025_max_monthend_dd_pct
    # To avoid 2025 greed: require positive BOTH first/last 6 months.
    stable=train[(train.first6_2025_pct>0)&(train.second6_2025_pct>0)]
    if not stable.empty:train=stable
    chosen=train.sort_values("selection",ascending=False).iloc[0]
    keep=port[port.name==chosen["name"]]
    report=dict(name=str(chosen["name"]),comparison=keep.to_dict("records"),
                target="22 profitable months and positive long-run net return",
                selection="2025-only, +5bp adverse slip on EVERY sleeve",
                no_hindsight_month_selection=True,
                2026_seen_not_pristine=True,
                synthetic_not_integrated=True,
                no_live_execution=True)
    print("PORTFOLIO_2025_ONLY_WINNER",json.dumps(report,default=str))
    (OUT/"portfolio_selection.json").write_text(json.dumps(report,indent=2,default=str)+"\n")
    summary=dict(variants_tested=len(df),by_group=df.groupby("group").size().to_dict(),
                 positive_2025_stress5_by_group={x:int(((df.group==x)&
                    (df.stress5_train_2025_pct>0)).sum()) for x in df.group.unique()},
                 selected=winners,
                 reported_2026_is_exposed=True,
                 original_4h_engine_parity=True,
                 original_1h_engine_parity=True,
                 impact_and_funding_not_modeled=True)
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
    print("STAGE26_ROBUST_STRATEGY_SEARCH_COMPLETE",json.dumps(dict(
      variants=len(df),selected={k:dict(model=v["model"],
          net22=v["base_total_pct"],net22_cost5=v["stress5_total_pct"],
          months_win=v["base_profitable_months"],months_win_cost5=v["stress5_profitable_months"],
          train_cost5=v["stress5_train_2025_pct"],check2026_cost5=v["stress5_seen_2026_JanOct_pct"])
          for k,v in winners.items()},portfolio_2025selected=report),default=str))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,starts,ends,quality=read_archive()
    print("BTC_MINUTE_SOURCE",json.dumps(dict(candles=len(f),
          missing=quality["missing_minutes"],partitions=quality["months"])))
    rows=[];series=[]
    for fn,arg in ((optimize_4h,starts),(optimize_1h,ends)):
        r,m=fn(f,arg)
        rows.extend(r);series.extend(m)
        print("FAMILY_DONE",json.dumps(dict(family=fn.__name__,variants=len(r))))
    select_and_report(rows,series)
if __name__=="__main__":main()
