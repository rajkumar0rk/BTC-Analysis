#!/usr/bin/env python3
"""Step 2: causal dynamic time/direction; precisely ONE entry per IST weekday.

Compare 85 deterministic *daily* entry policies x 6 stops x 6 gross risk/reward
ratios x 3 holds x 2 cost models on 477 full weekdays (2025 + Jan-Oct 2026).

Select by 2025 profitable-day counts subject to positive net return / drawdown;
2026 is only a research-exposed historical recheck, NOT unseen validation.
"""
from pathlib import Path
from itertools import product
import json
import numpy as np
import pandas as pd
import research_btc_every_weekday_reset_step1 as base

OUT=Path("analysis/btc_every_weekday_adaptive_step2")
DAYS=base.DAYS
HOURS=(9,12,15,18,19,20,21)
WINDOWS={
  "all_sessions":(9,12,15,18,19,20),
  "eu_us":(15,18,19,20),
  "us_only":(18,19,20),
}
FALLBACKS=("fade5","follow60")
TRIGGERS=(
 "impulse15_follow","impulse15_fade",
 "impulse60_follow","impulse60_fade",
 "vol5_follow","vol5_fade",
 "align15_60_follow","align15_60_fade",
 "pullback15_60","range_edge_revert","range_edge_follow",
 "breakout120_follow","volatility15_follow","volatility15_fade",
)
POLICIES=[("fixed19_fade5","fixed","fixed")] + list(product(TRIGGERS,WINDOWS,FALLBACKS))
N_EXPECTED=len(POLICIES)*len(base.STOPS)*len(base.RR)*len(base.HOLDS)*len(base.MODES)
assert len(POLICIES)==85 and N_EXPECTED==18360

def direction(x):
    # A zero-change value is a deterministic +1 fallback sign.
    return 1 if x>=0 else -1

def build_completed_candle_features(m,starts):
    close=m.close.to_numpy(float)
    op=m.open.to_numpy(float)
    high=m.high.to_numpy(float)
    low=m.low.to_numpy(float)
    volume=m.volume.to_numpy(float)
    feats={}
    for d in range(len(DAYS)):
        for hour in HOURS:
            idx=int(starts[d,hour])
            if idx<240:
                raise AssertionError("No 4h history before candidate")
            pclose=float(close[idx-1])
            r5=pclose/op[idx-5]-1
            r15=pclose/op[idx-15]-1
            r60=pclose/op[idx-60]-1
            r240=pclose/op[idx-240]-1
            curvol=float(np.sum(volume[idx-5:idx]))
            historical=volume[idx-105:idx-5].reshape(20,5).sum(axis=1)
            vr=curvol/float(historical.mean()) if historical.mean()>0 else 0.
            max60=float(np.max(high[idx-60:idx]))
            min60=float(np.min(low[idx-60:idx]))
            range_pos=(pclose-min60)/(max60-min60) if max60>min60 else .5
            prevhigh=float(np.max(high[idx-120:idx-30]))
            prevlow=float(np.min(low[idx-120:idx-30]))
            recent15=float(high[idx-15:idx].max()-low[idx-15:idx].min())
            old15=[]
            for k in range(1,7):
                a=idx-15*(k+1)
                b=idx-15*k
                old15.append(float(high[a:b].max()-low[a:b].min()))
            median15=float(np.median(old15))
            vrange=recent15/median15 if median15>0 else 0.
            feats[d,hour]=dict(
               r5=r5,r15=r15,r60=r60,r240=r240,
               volume5_ratio=vr,position60=range_pos,
               above_old120=pclose>prevhigh,
               below_old120=pclose<prevlow,
               range15_ratio=vrange)
    assert len(feats)==len(DAYS)*len(HOURS)
    return feats

def decide_trigger(trigger,f):
    a=direction(f["r15"])
    b=direction(f["r60"])
    if trigger=="impulse15_follow":
        return a if abs(f["r15"])>=.0015 else 0
    if trigger=="impulse15_fade":
        return -a if abs(f["r15"])>=.0015 else 0
    if trigger=="impulse60_follow":
        return b if abs(f["r60"])>=.0040 else 0
    if trigger=="impulse60_fade":
        return -b if abs(f["r60"])>=.0040 else 0
    if trigger=="vol5_follow":
        return direction(f["r5"]) if f["volume5_ratio"]>=1.5 else 0
    if trigger=="vol5_fade":
        return -direction(f["r5"]) if f["volume5_ratio"]>=1.5 else 0
    if trigger=="align15_60_follow":
        return a if a==b and abs(f["r15"])>=.0008 and abs(f["r60"])>=.0025 else 0
    if trigger=="align15_60_fade":
        return -a if a==b and abs(f["r15"])>=.0008 and abs(f["r60"])>=.0025 else 0
    if trigger=="pullback15_60":
        return b if a!=b and abs(f["r15"])>=.0008 and abs(f["r60"])>=.0025 else 0
    if trigger=="range_edge_revert":
        return -1 if f["position60"]>=.85 else (1 if f["position60"]<=.15 else 0)
    if trigger=="range_edge_follow":
        return 1 if f["position60"]>=.85 else (-1 if f["position60"]<=.15 else 0)
    if trigger=="breakout120_follow":
        if f["volume5_ratio"]<1.25:return 0
        if f["above_old120"]:return 1
        return -1 if f["below_old120"] else 0
    if trigger=="volatility15_follow":
        return a if f["range15_ratio"]>=1.5 else 0
    if trigger=="volatility15_fade":
        return -a if f["range15_ratio"]>=1.5 else 0
    raise KeyError(trigger)

def choose_all_policy_entries(features):
    hours=np.empty((len(POLICIES),len(DAYS)),dtype=np.int8)
    signs=np.empty((len(POLICIES),len(DAYS)),dtype=np.int8)
    fallback=np.zeros((len(POLICIES),len(DAYS)),dtype=bool)
    for pi,(trigger,session,fback) in enumerate(POLICIES):
        for d in range(len(DAYS)):
            if trigger=="fixed19_fade5":
                hours[pi,d]=19
                signs[pi,d]=-direction(features[d,19]["r5"])
                continue
            selected=False
            # **CAUSAL**: must stop as soon as the first qualifying check occurs.
            # Never compare future feature strengths to decide a past entry time.
            for hour in WINDOWS[session]:
                side=decide_trigger(trigger,features[d,hour])
                if side:
                    hours[pi,d]=hour
                    signs[pi,d]=side
                    selected=True
                    break
            if not selected:
                hours[pi,d]=21
                f=features[d,21]
                signs[pi,d]=(-direction(f["r5"]) if fback=="fade5"
                            else direction(f["r60"]))
                fallback[pi,d]=True
    assert np.all((hours>=9)&(hours<=21))
    assert np.all(np.abs(signs)==1)
    assert hours.shape==(85,477) and signs.shape==hours.shape
    return hours,signs,fallback

def choose_outcome(cube,fees,gross,slippts,reasons,durations,hours,signs,stop_i,rr_i,hold_i,mode_i):
    d=np.arange(len(DAYS))
    side=np.where(signs==1,0,1)
    return (cube[d,hours,side,stop_i,rr_i,hold_i,mode_i],
        fees[d,hours,side,stop_i,rr_i,hold_i,mode_i],
        gross[d,hours,side,stop_i,rr_i,hold_i],
        slippts[d,hours,side,stop_i,rr_i,hold_i],
        reasons[d,hours,side,stop_i,rr_i,hold_i],
        durations[d,hours,side,stop_i,rr_i,hold_i])

def period_dd(path):
    equity=np.cumprod(1+path)
    peak=np.maximum.accumulate(np.r_[1.,equity])[1:]
    return round(float(100*np.max(1-equity/peak)),5)

def max_losing_run(path):
    return base.max_loss_run(path<0)

def daily_table(path,fee,gross,slippage,reasons,duration,hour,signs,isfallback):
    return pd.DataFrame({
        "day_ist":base.IST_DAYS,
        "year":np.asarray(DAYS.year),
        "month_ist":base.MONTH_LABELS,
        "entry_hour_ist":hour.astype(int),
        "side":np.where(signs>0,"LONG","SHORT"),
        "used_21h_fallback":isfallback,
        "account_net_return_pct":100*path,
        "gross_price_points":gross,
        "trading_fees_gst_price_points":fee,
        "adverse_slippage_price_points":slippage,
        "exit_reason":np.where(reasons==1,"TP",np.where(reasons==2,"SL","TIMEOUT")),
        "holding_minutes":duration.astype(int)
    })

def monthly_table(daily):
    out=daily.groupby("month_ist",sort=True).agg(
        trades=("day_ist","count"),
        positive_days=("account_net_return_pct",lambda s:int((s>0).sum())),
        losing_days=("account_net_return_pct",lambda s:int((s<0).sum())),
        net_return_pct=("account_net_return_pct",
            lambda s:float(100*(np.prod(1+s.to_numpy(dtype=float)/100)-1))),
        gross_points=("gross_price_points","sum"),
        fees_gst_points=("trading_fees_gst_price_points","sum")
    ).reset_index()
    if len(out)!=22 or not out.trades.equals(
          pd.Series(DAYS.strftime("%Y-%m")).value_counts().sort_index().reset_index(drop=True).rename("trades")):
        # Number of full weekdays for each IST month must match ledger exactly.
        expected=pd.Series(DAYS.strftime("%Y-%m")).value_counts().sort_index()
        if not np.array_equal(out.trades.to_numpy(),expected.to_numpy()):
            raise AssertionError("Monthly day coverage invalid")
    return out

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=base.load()
    entry_indices,_,_=base.prepare(m)
    features=build_completed_candle_features(m,entry_indices)
    choices,signs,fallback=choose_all_policy_entries(features)
    cube,fees,gross,slippts,reasons,durations=base.simulate(
        m.open.to_numpy(float),m.high.to_numpy(float),m.low.to_numpy(float),
        entry_indices,base.STOPS,base.RR,base.HOLDS,base.COST,base.SLIP)
    records=[]
    for pi,(trigger,session,fb) in enumerate(POLICIES):
        h=choices[pi].astype(int);s=signs[pi]
        fb_count=int(fallback[pi].sum())
        for si,stop in enumerate(base.STOPS):
            for ri,ratio in enumerate(base.RR):
                for hi,hold in enumerate(base.HOLDS):
                    for mi,mode in enumerate(base.MODES):
                        path,fee,grossp,slip,reason,duration=choose_outcome(
                          cube,fees,gross,slippts,reasons,durations,h,s,si,ri,hi,mi)
                        stat=base.score(path,fee,grossp,slip,reason)
                        stat.update(
                            max_dd_2025_pct=period_dd(path[:base.NTRAIN]),
                            max_dd_2026_pct=period_dd(path[base.NTRAIN:]),
                            max_consecutive_losing_days=max_losing_run(path),
                            fallback_days=fb_count,
                            fallback_rate_pct=round(100*fb_count/len(DAYS),2),
                            entry_hours_19_pct=round(float(np.mean(h==19)*100),2),
                            entry_hours_21_pct=round(float(np.mean(h==21)*100),2),
                            trigger=trigger,session=session,fallback_direction=fb,
                            stop_pct=float(stop),reward_rr=float(ratio),
                            gross_tp_pct=round(float(stop*ratio),5),
                            max_hold_minutes=int(hold),cost_model=mode,
                            id=f"{trigger}__{session}__{fb}__stop{stop:g}__rr{ratio:g}__hold{hold}__{mode}"
                        )
                        records.append(stat)
    result=pd.DataFrame(records)
    if len(result)!=N_EXPECTED or not result.trades.eq(477).all():
        raise AssertionError("NOT one per weekday for all configurations")
    result.to_csv(OUT/"all_18360_variants.csv",index=False)
    print("STEP2_COMPLETED_GRID "+json.dumps(dict(
        unique_models=len(result),daily_entry_policies=len(POLICIES),
        weekdays=len(DAYS),train_days=base.NTRAIN,check_days=len(DAYS)-base.NTRAIN,
        daily_trades_min=int(result.trades.min()),daily_trades_max=int(result.trades.max())
    ),sort_keys=True),flush=True)
    summaries={}
    for mode in base.MODES:
        z=result[result.cost_model==mode]
        eligible=z[(z.return_2025_pct>0)&(z.max_dd_2025_pct<=15.)]
        positive_count=int((z.return_2025_pct>0).sum())
        if len(eligible):
            rank=eligible.sort_values(
                ["profitable_days_2025","return_2025_pct","max_dd_2025_pct"],
                ascending=[False,False,True])
        else:
            rank=z.sort_values(["return_2025_pct","profitable_days_2025"],
                               ascending=[False,False])
        chosen=rank.iloc[0].to_dict()
        pi=POLICIES.index((chosen["trigger"],chosen["session"],chosen["fallback_direction"]))
        si=int(np.where(np.isclose(base.STOPS,chosen["stop_pct"]))[0][0])
        ri=int(np.where(np.isclose(base.RR,chosen["reward_rr"]))[0][0])
        hi=int(np.where(base.HOLDS==chosen["max_hold_minutes"])[0][0])
        mi=base.MODES.index(mode)
        p,c,g,sl,reason,dur=choose_outcome(cube,fees,gross,slippts,reasons,durations,
            choices[pi].astype(int),signs[pi],si,ri,hi,mi)
        daily=daily_table(p,c,g,sl,reason,dur,choices[pi],signs[pi],fallback[pi])
        months=monthly_table(daily)
        # Adjacent risk/reward neighborhood under the SAME causal entry rule.
        nearby=z[(z.trigger==chosen["trigger"])&
            (z.session==chosen["session"])&
            (z.fallback_direction==chosen["fallback_direction"])&
            (z.max_hold_minutes==chosen["max_hold_minutes"])&
            (abs(z.stop_pct-chosen["stop_pct"])<=.25+1e-10)&
            (abs(z.reward_rr-chosen["reward_rr"])<=1.+1e-10)]
        both=(z.return_2025_pct>0)&(z.return_2026_pct>0)
        reliable={}
        for cut in (55,60,70):
            a=z[both&(z.profitable_days_2025_pct>=cut)&
                (z.profitable_days_2026_pct>=cut)]
            reliable[str(cut)+"pct_winning_days_both_years_positive_net"]=int(len(a))
        for ext,frame in (("selected_daily",daily),("selected_monthly",months),
                          ("selected_risk_reward_neighbors",nearby)):
            frame.to_csv(OUT/f"{mode}_{ext}.csv",index=False)
        summary=dict(
            chosen_using_2025_only=chosen,
            profitable_2025_candidates=positive_count,
            profitable_and_max_15pct_dd_2025=int(len(eligible)),
            total_models_profitable_both_years_hindsight=int(both.sum()),
            strong_daily_and_profitable_both_years_hindsight=reliable,
            neighborhood_tested=int(len(nearby)),
            neighboring_2025_positive=int((nearby.return_2025_pct>0).sum()),
            neighboring_2026_positive=int((nearby.return_2026_pct>0).sum()),
            neighboring_both_positive=int(((nearby.return_2025_pct>0)&
                                           (nearby.return_2026_pct>0)).sum()),
            actual_477_trades=int(len(daily)),
            selected_2025_win_days=int((p[:base.NTRAIN]>0).sum()),
            selected_2026_win_days=int((p[base.NTRAIN:]>0).sum()),
            selected_worst_losing_streak=base.max_loss_run(p<0),
            selected_positive_months=int((months.net_return_pct>0).sum()))
        oracle=z.sort_values("net_total_pct",ascending=False).iloc[0].to_dict()
        summary["hindsight_best_22_months_NOT_selected"]=oracle
        summaries[mode]=summary
        print("STEP2_SELECTED_"+mode.upper()+" "+json.dumps(summary,sort_keys=True),flush=True)
        print("STEP2_MONTHLY_"+mode.upper()+"\n"+months.to_string(index=False),flush=True)
    baseline=result[(result.trigger=="fixed19_fade5")&
        (result.stop_pct==1.)&(result.reward_rr==1.)&
        (result.max_hold_minutes==30)&(result.cost_model=="scalper_offer")]
    assert len(baseline)==1
    baseline=baseline.iloc[0].to_dict()
    # Regression check: unchanged 19:00 5m fade baseline from previous step.
    if abs(float(baseline["net_total_pct"])+1.156951)>0.0001:
        raise AssertionError("Baseline parity against Step1 failed")
    if baseline["profitable_days"]!=241:
        raise AssertionError("Baseline winning-day count changed")
    print("STEP2_STEP1_PARITY "+json.dumps(baseline,sort_keys=True),flush=True)
    (OUT/"summary.json").write_text(json.dumps(dict(
        status="historical research only, NOT validated for live",
        utc_data_range=f"{m.index.min()} .. {m.index.max()}",
        calendar="Asia/Kolkata, Mon-Fri only, full 477-day coverage",
        variants=len(result),mandatory_daily_entries=477,
        candidates=dict(triggers=list(TRIGGERS),sessions=WINDOWS,
            fallback_sides=list(FALLBACKS),stops_pct=base.STOPS.tolist(),
            rewards=base.RR.tolist(),holds=base.HOLDS.tolist(),fees=list(base.MODES)),
        cost_approximations="1x BTC account notional; 0.05% taker each leg + 18% GST; conditional prior-activated regular Scalper Offer closing waiver <=30m; 5 BTC quote-point slippage each leg",
        selected_results=summaries,step1_parity_baseline=baseline,
        limitations=[
            "2026 is research-exposed historical data, NOT a pristine out-of-sample forward test",
            "Best-of-18360 selection overfits 2025 and can still fail going forward",
            "Real-orderbook spread, funding, latency, and offer historical activation unknown",
            "Only full 1m OHLC; same-bar stop and TP assumes stop first",
            "Exactly 1 trade per IST weekday is enforced, but does not imply winning daily"]),
        indent=2)+"\n")
    report=[
        "# BTCUSD mandatory daily strategy — Restarted Step 2 adaptive causal entry",
        "",
        "Every strategy entered EXACTLY once on all 477 Mon-Fri IST dates. No fixed +0.2% TP; static gross reward is stop_pct × R, with multiple R and stop values.",
        "",
        "2025-only selection requires positive net account return and <=15% 2025 peak-to-trough DD. Rank on count of 2025 profitable days then return and DD. 2026 has already been researched and is not pristine unseen.",
        "",
        "## Selected Scalper Offer",json.dumps(summaries["scalper_offer"],indent=2),
        "",
        "## Selected Standard taker",json.dumps(summaries["standard"],indent=2),
        "",
        "## Scalper Offer 22-month account returns","",
        pd.read_csv(OUT/"scalper_offer_selected_monthly.csv").to_markdown(index=False),
        "",
        "## Standard 22-month account returns","",
        pd.read_csv(OUT/"standard_selected_monthly.csv").to_markdown(index=False),
        "",
        "## Existing Step1 parity baseline","",json.dumps(baseline,indent=2),
        "",
        "## Limitations",
        "The chosen 2025 result is in-sample and has severe many-trial overfitting risk. 2026 has been revisited in past BTC research and is not a blind holdout. Real fills, funding, market impact and historical offer qualification are not established."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STEP2_DAILY_ADAPTIVE_COMPLETE",flush=True)

if __name__=="__main__":
    run()
