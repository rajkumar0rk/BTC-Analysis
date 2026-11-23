#!/usr/bin/env python3
"""BTCUSD mandatory weekday Step 5: causal regime-conditioned exit and fallback.

Every candidate makes precisely 477 trades, one each IST weekday; zero skipped.
2025-only selection for daily win rate subject to 2025 positive net and DD cap.
2026 is already research-exposed, not a pristine independent holdout.
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

OUT=Path("analysis/btc_daily_causal_regime_step5")
DAYS=base.DAYS
MODES=base.MODES
FALLBACK_HOURS=(21,22)
RULES=(
    "follow5","fade5","follow15","follow60",
    "follow5_if_large5_else_fade5",
    "follow5_if_align5_60_else_fade5",
    "follow5_if_highvol_else_follow60",
    "follow60_if_large60_else_follow5",
    "fade5_if_large5_else_follow5",
    "follow5_if_align5_15_else_follow60",
    "fade60_if_edge_else_follow5",
)
REGIMES=(
    "always_high","range60_ge_0p45","range60_ge_0p80",
    "magnitude5_ge_0p12","vol5_ge_1p25","align5_60",
)
# Exact parameter recipes present in established Step3 causal 1m simulator.
RECIPES={
    "lock050":(1,.50,3.,30,.25,.10,0.),
    "lock075":(1,.75,3.,30,.25,.10,0.),
    "lock100":(1,1.0,3.,30,.25,.10,0.),
    "trail050":(2,.50,3.,30,.35,.20,0.),
    "trail075":(2,.75,3.,30,.35,.20,0.),
    "static075":(0,.75,3.,30,0.,0.,0.),
    "static100":(0,1.0,3.,30,0.,0.,0.),
}
EVENT_EXIT=("lock050","lock075","lock100","trail050")
FALL_EXIT=("lock050","lock075","trail050","trail075","static075")
EXPECTED=len(RULES)*len(FALLBACK_HOURS)*len(EVENT_EXIT)*len(FALL_EXIT)*len(FALL_EXIT)*len(REGIMES)*len(MODES)
assert EXPECTED==13200
YEAR_TRAIN=base.NTRAIN

def build_cfg():
    complete,names=protection.build_configs()
    out=[]
    for k,recipe in RECIPES.items():
        hits=np.flatnonzero(np.all(np.isclose(complete,np.array(recipe,float)),axis=1))
        if len(hits)!=1:raise AssertionError("Cannot find replay recipe "+k)
        out.append(complete[hits[0]])
    return np.asarray(out,dtype=float),dict(zip(RECIPES.keys(),range(len(RECIPES))))

def features(m,index):
    o=m.open.to_numpy(float); c=m.close.to_numpy(float)
    high=m.high.to_numpy(float);low=m.low.to_numpy(float)
    v=m.volume.to_numpy(float)
    info={}
    for day in range(len(DAYS)):
        for hour in FALLBACK_HOURS:
            i=int(index[day,hour])
            close=float(c[i-1]);ret={}
            for n in (5,15,60):
                ret[n]=close/float(o[i-n])-1
            vr5=float(v[i-5:i].sum())
            pv=v[i-105:i-5].reshape(20,5).sum(axis=1)
            avg=float(pv.mean())
            vr5=vr5/avg if avg else 0.
            mx=float(high[i-60:i].max());mn=float(low[i-60:i].min())
            pct=100*(mx-mn)/float(o[i])
            pos=(close-mn)/(mx-mn) if mx>mn else .5
            info[day,hour]=dict(ret=ret,volume5=vr5,range60pct=pct,pos60=pos)
    return info

def sign(v):
    return 1 if v>=0 else -1

def side_for(rule,f):
    x=f["ret"]
    a,b,c=(sign(x[n]) for n in (5,15,60))
    if rule=="follow5":return a
    if rule=="fade5":return -a
    if rule=="follow15":return b
    if rule=="follow60":return c
    if rule=="follow5_if_large5_else_fade5":return a if abs(x[5])>=.001 else -a
    if rule=="follow5_if_align5_60_else_fade5":return a if a==c else -a
    if rule=="follow5_if_highvol_else_follow60":return a if f["volume5"]>=1.25 else c
    if rule=="follow60_if_large60_else_follow5":return c if abs(x[60])>=.003 else a
    if rule=="fade5_if_large5_else_follow5":return -a if abs(x[5])>=.0015 else a
    if rule=="follow5_if_align5_15_else_follow60":return a if a==b else c
    if rule=="fade60_if_edge_else_follow5":return -c if f["pos60"]>=.85 or f["pos60"]<=.15 else a
    raise KeyError(rule)

def is_high(rule,f):
    x=f["ret"]
    if rule=="always_high":return True
    if rule=="range60_ge_0p45":return f["range60pct"]>=.45
    if rule=="range60_ge_0p80":return f["range60pct"]>=.80
    if rule=="magnitude5_ge_0p12":return abs(x[5])>=.0012
    if rule=="vol5_ge_1p25":return f["volume5"]>=1.25
    if rule=="align5_60":return sign(x[5])==sign(x[60])
    raise KeyError(rule)

def outcome_for(cube,fmask,f_hour,f_sign,e_i,low_i,high_i,regime,model_i):
    a=np.arange(len(DAYS))
    er,ef,eg,ew,et=cube["event"]
    p=er[:,e_i,model_i].copy()
    fee=ef[:,e_i,model_i].copy()
    gross=eg[:,e_i].copy()
    reason=ew[:,e_i].copy()
    duration=et[:,e_i].copy()
    if np.any(fmask):
        for side in (1,-1):
            mask=fmask & (f_sign==side)
            if not np.any(mask):continue
            r,ff,g,w,t=cube[f"fall_{f_hour}_{side}"]
            use=np.flatnonzero(mask)
            chosen=np.where(regime[use],high_i,low_i)
            p[use]=r[use,chosen,model_i]
            fee[use]=ff[use,chosen,model_i]
            gross[use]=g[use,chosen]
            reason[use]=w[use,chosen]
            duration[use]=t[use,chosen]
    return p,fee,gross,reason,duration

def stats(p,fee,gross,reason,holding):
    z=base.score(p,fee,gross,np.full(len(p),base.SLIP*2),reason)
    z["max_dd_2025"]=adaptive.period_dd(p[:YEAR_TRAIN])
    z["max_dd_2026"]=adaptive.period_dd(p[YEAR_TRAIN:])
    z["worst_consecutive_losses"]=base.max_loss_run(p<0)
    z["mean_hold_minutes"]=round(float(np.mean(holding)),3)
    return z

def sample_day_stats(p,fee,gross,reason,duration,rule,hour,evh,evside,fmask,fsign,exit0,exit1,exit2,regime):
    all_hour=np.where(fmask,hour,evh)
    all_side=np.where(fmask,fsign,evside)
    recipes=np.where(~fmask,exit0,np.where(regime,exit2,exit1))
    df=pd.DataFrame(dict(
        date_ist=base.IST_DAYS,month_ist=base.MONTH_LABELS,year=np.asarray(DAYS.year),
        entry_hour_ist=all_hour.astype(int),
        side=np.where(all_side>0,"LONG","SHORT"),
        trigger_type=np.where(fmask,"MANDATORY_FALLBACK","VOLUME_SIGNAL"),
        fallback_regime_high=regime,
        exit_recipe=recipes,
        account_net_pct=100*p,
        gross_btc_points=gross,
        fees_gst_points=fee,
        adverse_slippage_btc_points=base.SLIP*2,
        hold_minutes=duration,
        exit_reason=np.where(reason==1,"TP",np.where(reason==2,"STOP","TIMEOUT"))
    ))
    if len(df)!=477 or df.date_ist.nunique()!=477:raise AssertionError("Missing daily trade")
    month=df.groupby("month_ist",sort=True).agg(
        trades=("date_ist","size"),
        positive_days=("account_net_pct",lambda s:int((s>0).sum())),
        losing_days=("account_net_pct",lambda s:int((s<0).sum())),
        compounded_net_pct=("account_net_pct",lambda s:float(100*(np.prod(1+s.to_numpy()/100)-1))),
        gross_points=("gross_btc_points","sum"),
        fees_gst_points=("fees_gst_points","sum")
    ).reset_index()
    if len(month)!=22:raise AssertionError("Missing month")
    return df,month

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=base.load()
    indices,_,_=base.prepare(m)
    past=adaptive.build_completed_candle_features(m,indices)
    hour_signal,side_signal,isfallback=adaptive.choose_all_policy_entries(past)
    i=adaptive.POLICIES.index(("vol5_fade","us_only","follow60"))
    event_hours=hour_signal[i].astype(int)
    event_sides=side_signal[i].astype(int)
    fallback=isfallback[i]
    assert int(fallback.sum())==217 and int((~fallback).sum())==260
    config,cfg_idx=build_cfg()
    cube=previous.cache_entry_exits(m,indices,event_hours,event_sides,config)
    f=features(m,indices)
    all_results=[]
    settings={}
    baselines={}
    # Known 2025..2026 baselines assert original simulation is identical.
    for label,rule,fh,e,lo,high,regime,winners,net in (
      ("protected_265","follow60",21,"lock050","lock050","lock050","always_high",265,6.786696),
      ("A_274","follow5",21,"lock050","trail075","trail075","always_high",274,14.434331),
      ("B_271","follow5",21,"lock050","trail050","trail050","always_high",271,15.522477),
      ("old_static_219","follow60",21,"static100","static100","static100","always_high",219,8.222995)
    ):
        sg=np.asarray([side_for(rule,f[d,fh]) for d in range(len(DAYS))],dtype=np.int8)
        hi=np.asarray([is_high(regime,f[d,fh]) for d in range(len(DAYS))],dtype=bool)
        p,c,g,w,t=outcome_for(cube,fallback,fh,sg,cfg_idx[e],cfg_idx[lo],cfg_idx[high],hi,1)
        z=stats(p,c,g,w,t)
        if abs(z["net_total_pct"]-net)>0.00011 or z["profitable_days"]!=winners:
            raise AssertionError(f"Parity failure {label}: {z['profitable_days']}, {z['net_total_pct']}")
        baselines[label]=z
    print("STEP5_BASELINE_PARITY "+json.dumps(baselines,sort_keys=True),flush=True)

    for fh,rule in product(FALLBACK_HOURS,RULES):
        sg=np.asarray([side_for(rule,f[d,fh]) for d in range(len(DAYS))],dtype=np.int8)
        if (sg==0).any():raise AssertionError("Any missing direction")
        byreg={r:np.asarray([is_high(r,f[d,fh]) for d in range(len(DAYS))],dtype=bool)
               for r in REGIMES}
        settings[fh,rule]=(sg,byreg)
        for e,low,high,regime,mode_i in product(EVENT_EXIT,FALL_EXIT,FALL_EXIT,REGIMES,range(len(MODES))):
            p,fee,g,w,t=outcome_for(cube,fallback,fh,sg,cfg_idx[e],
                        cfg_idx[low],cfg_idx[high],byreg[regime],mode_i)
            z=stats(p,fee,g,w,t)
            z.update(fallback_hour=fh,fallback_rule=rule,event_exit=e,
                    fallback_exit_low=low,fallback_exit_high=high,regime=regime,
                    cost_model=MODES[mode_i],mandatory_fallback_days=217,volume_signal_days=260,
                    n_high_fallback=int(np.sum(fallback & byreg[regime])))
            all_results.append(z)

    frame=pd.DataFrame(all_results)
    if len(frame)!=EXPECTED or not frame.trades.eq(477).all():
        raise AssertionError(f"Matrix size {len(frame)} vs {EXPECTED} or missing trades")
    frame.to_csv(OUT/"all_13200_regime_variants.csv",index=False)
    print("STEP5_GRID_COMPLETE "+json.dumps(dict(
        variants=len(frame),weekday_trades=477,primary_volume_entries=260,
        mandatory_fallback_entries=217,fallback_side_rules=len(RULES),
        regime_switches=len(REGIMES),cost_schedules=list(MODES)),sort_keys=True),flush=True)
    comparisons={}
    for model in MODES:
        sub=frame[frame.cost_model==model].copy()
        train=sub[(sub.return_2025_pct>0)&(sub.max_dd_2025<=8)]
        if len(train):
            ranked=train.sort_values(["profitable_days_2025","return_2025_pct","max_dd_2025"],
                                     ascending=[False,False,True])
        else:
            ranked=sub.sort_values(["return_2025_pct","profitable_days_2025"],ascending=[False,False])
        best=ranked.iloc[0].to_dict()
        fh=int(best["fallback_hour"]);rule=best["fallback_rule"];sg,regs=settings[fh,rule]
        p,c,g,w,t=outcome_for(cube,fallback,fh,sg,cfg_idx[best["event_exit"]],
            cfg_idx[best["fallback_exit_low"]],cfg_idx[best["fallback_exit_high"]],
            regs[best["regime"]],MODES.index(model))
        daily,monthly=sample_day_stats(p,c,g,w,t,rule,fh,event_hours,event_sides,fallback,
            sg,best["event_exit"],best["fallback_exit_low"],best["fallback_exit_high"],
            regs[best["regime"]])
        daily.to_csv(OUT/(model+"_selected_daily.csv"),index=False)
        monthly.to_csv(OUT/(model+"_selected_monthly.csv"),index=False)
        both=(sub.return_2025_pct>0)&(sub.return_2026_pct>0)
        baseB=baselines["B_271"]
        pareto=(sub.profitable_days>baseB["profitable_days"])&\
               (sub.net_total_pct>baseB["net_total_pct"])&\
               (sub.max_closed_dd_pct<=baseB["max_closed_dd_pct"])
        strong=(sub.profitable_days>=275)&(sub.net_total_pct>16)&(sub.win_months_all>=16)&(sub.max_closed_dd_pct<=6.71)
        opt=sub.sort_values(["net_total_pct","profitable_days"],ascending=False).iloc[0].to_dict()
        most_days=sub.sort_values(["profitable_days","net_total_pct"],ascending=False).iloc[0].to_dict()
        comparisons[model]=dict(
            selected_using_2025_only=best,
            qualified_2025_positive_and_below_8pct_dd=int(len(train)),
            model_profitable_both_years_hindsight=int(both.sum()),
            full_period_pareto_better_than_B_hindsight=int(pareto.sum()),
            high_quality_count_hindsight=int(strong.sum()),
            full_period_most_profitable_hindsight=opt,
            full_period_most_winning_days_hindsight=most_days,
            selected_2025_profitable_days=int(np.sum(p[:YEAR_TRAIN]>0)),
            selected_2026_profitable_days=int(np.sum(p[YEAR_TRAIN:]>0)),
            selected_months_profitable=int(np.sum(monthly.compounded_net_pct>0)),
            selected_worst_month_pct=round(float(monthly.compounded_net_pct.min()),5)
        )
        if model=="scalper_offer":
            sub[pareto].sort_values(["profitable_days","net_total_pct"],
                                    ascending=False).head(100).to_csv(OUT/"hindsight_B_improved_pareto.csv",index=False)
        print("STEP5_SELECTED_"+model.upper()+" "+json.dumps(comparisons[model],sort_keys=True),flush=True)
        print("STEP5_MONTHLY_"+model.upper()+"\n"+monthly.to_string(index=False),flush=True)

    (OUT/"summary.json").write_text(json.dumps(dict(
        scope="Causal regime-switching fixed-volume daily BTCUSD at 1x account notional",
        all_weekday_trades=477,month_count=22,
        variants=len(frame),fallback_signals=217,volume_signals=260,
        cost="taker 0.05% per leg + GST 18%, adverse 5 price points slippage per side, hypothetical preactivated regular 30m Scalper Offer closing fee waiver",
        verified_baselines=baselines,
        2025_selected_result=comparisons,
        limitations=["2026 previously exposed to research, NOT truly independent OOS",
          "13,200 multiple comparisons can overfit 2025 too",
          "November already inspected for B and A, do not select using November",
          "No actual historical offer eligibility, funding, orderbook, market impact, tick-level stop ordering"]),indent=2)+"\n")
    report=["# Step 5 — BTC mandatory daily causal regime exits",
        "",f"Backtested **{len(frame)} variants**, every variant with **477/477 IST weekday trades** at 1× account notional. No +0.2% fixed TP, all TP gross 3% with 30m exit cap.",
        "","## Verified previous baselines",json.dumps(baselines,indent=2),
        "","## 2025-only selections and research-exposed 2026 checks",json.dumps(comparisons,indent=2),
        "","## Scalper Offer selected 22-month table","",
        pd.read_csv(OUT/"scalper_offer_selected_monthly.csv").to_markdown(index=False),
        "","## Standard fees selected 22-month table","",
        pd.read_csv(OUT/"standard_selected_monthly.csv").to_markdown(index=False),
        "","## Cautions","No full-period hindsight winner is an independently validated strategy. Prior 2026 and November observations were already examined. Real exchange fees/fills, exact offer activation, funding, price impact and latency are not represented."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STEP5_CAUSAL_REGIME_COMPLETE",flush=True)

if __name__=="__main__":
    run()
