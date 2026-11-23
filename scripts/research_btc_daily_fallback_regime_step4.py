#!/usr/bin/env python3
"""Step 4: improve BTC mandatory-daily 21h fallback and exit by regime.

Every policy enters exactly once on 477 full Mon-Fri IST dates, no skips.
Frozen 18/19/20 5m-volume fade entry from Step2, 21/22h mandatory fallback
with 14 deterministic pre-entry side rules. Event/fallback exits can differ.
Uses the SAME causally next-bar-protected Step3 exit simulator and validates
the two known past baselines before reporting any purported improvement.
"""
from pathlib import Path
from itertools import product
import json
import numpy as np
import pandas as pd
import research_btc_every_weekday_reset_step1 as base
import research_btc_every_weekday_adaptive_step2 as ent
import research_btc_every_weekday_exit_protection_step3 as exits

OUT=Path("analysis/btc_daily_fallback_regime_step4")
POL=("vol5_fade","us_only","follow60")
MODES=base.MODES
FALLBACK_HOURS=(21,22)
FALLBACK_RULES=(
    "follow5","fade5","follow15","fade15",
    "follow60","fade60","follow240","fade240",
    "align15_60_else_fade5",
    "pullback60_else_fade5",
    "agree5_60_fade_else_follow60",
    "large60_follow_else_fade5",
    "vol5_fade_else_follow60",
    "edge60_fade_else_follow60",
)
# Pre-registered, static / lock / trailing / step protected exits. These
# seven quantities: kind, SL%, gross TP%, hold, activate%, value%, step%.
SPECS=(
    (0,1.00,3.00,30,0,0,0),
    (0,0.75,3.00,30,0,0,0),
    (0,0.50,3.00,30,0,0,0),
    (1,0.50,3.00,30,0.25,0.10,0),
    (1,0.75,3.00,30,0.25,0.10,0),
    (1,1.00,3.00,30,0.25,0.10,0),
    (1,0.75,3.00,30,0.35,0.10,0),
    (1,1.00,3.00,30,0.40,0.10,0),
    (1,1.00,3.00,30,0.60,0.20,0),
    (2,0.75,3.00,30,0.35,0.20,0),
    (2,0.50,3.00,30,0.35,0.20,0),
    (3,0.50,3.00,30,0.35,0.10,0.20),
)
KIND_NAMES=("static","lock","trailing","stepup")
assert len(SPECS)==12 and len(FALLBACK_RULES)==14
EXPECTED=len(FALLBACK_HOURS)*len(FALLBACK_RULES)*len(SPECS)**2*len(MODES)
assert EXPECTED==8064

def assert_config_engine_parity():
    cfg_full,names_full=exits.build_configs()
    found=[]
    for s in SPECS:
        matches=np.flatnonzero(np.all(np.isclose(cfg_full,np.array(s,float),atol=1e-9),axis=1))
        if len(matches)!=1:
            raise AssertionError(f"Frozen exit recipe not found: {s}, count {len(matches)}")
        found.append(int(matches[0]))
    return cfg_full[found], [names_full[i] for i in found]

def fallback_features(m,indices):
    close=m.close.to_numpy(float)
    opening=m.open.to_numpy(float)
    high=m.high.to_numpy(float)
    low=m.low.to_numpy(float)
    vol=m.volume.to_numpy(float)
    info={}
    for day in range(len(base.DAYS)):
        for hour in FALLBACK_HOURS:
            i=int(indices[day,hour])
            before=float(close[i-1])
            returns={t:before/float(opening[i-t])-1 for t in (5,15,60,240)}
            last5=float(np.sum(vol[i-5:i]))
            historical5=vol[i-105:i-5].reshape(20,5).sum(axis=1)
            avg=float(np.mean(historical5))
            vr=last5/avg if avg>0 else 0.
            peak=float(np.max(high[i-60:i]));bottom=float(np.min(low[i-60:i]))
            pos=(before-bottom)/(peak-bottom) if peak>bottom else .5
            info[day,hour]=dict(ret=returns,volume_ratio=vr,range_pos=pos)
    assert len(info)==len(base.DAYS)*len(FALLBACK_HOURS)
    return info

def sign(v):
    return 1 if v>=0 else -1

def direction(rule,f):
    r=f["ret"]
    a,b,c,d=(sign(r[k]) for k in (5,15,60,240))
    if rule=="follow5":return a
    if rule=="fade5":return -a
    if rule=="follow15":return b
    if rule=="fade15":return -b
    if rule=="follow60":return c
    if rule=="fade60":return -c
    if rule=="follow240":return d
    if rule=="fade240":return -d
    if rule=="align15_60_else_fade5":return b if b==c else -a
    if rule=="pullback60_else_fade5":return c if b!=c else -a
    if rule=="agree5_60_fade_else_follow60":return -a if a==c else c
    if rule=="large60_follow_else_fade5":return c if abs(r[60])>=.0025 else -a
    if rule=="vol5_fade_else_follow60":return -a if f["volume_ratio"]>=1.25 else c
    if rule=="edge60_fade_else_follow60":return -c if (f["range_pos"]>=.85 or f["range_pos"]<=.15) else c
    raise KeyError(rule)

def cache_entry_exits(m,entry_indices,policy_hours,policy_signs,cfg):
    o=m.open.to_numpy(float);h=m.high.to_numpy(float);l=m.low.to_numpy(float)
    ret={}
    # Existing event entry, including unused fallback-day placeholders.
    d=np.arange(len(base.DAYS))
    i0=entry_indices[d,policy_hours.astype(int)]
    ret["event"]=exits.run_exit_grid(o,h,l,i0,policy_hours,
                  policy_signs,cfg,base.COST,base.SLIP)
    # Both fallback sides at BOTH causal fixed hours, no future labels.
    for hour,side in product(FALLBACK_HOURS,(1,-1)):
        chosen=np.full(len(d),hour,dtype=np.int8)
        sides=np.full(len(d),side,dtype=np.int8)
        ix=entry_indices[d,hour]
        ret[f"fall_{hour}_{side}"]=exits.run_exit_grid(
            o,h,l,ix,chosen,sides,cfg,base.COST,base.SLIP)
    for tup in ret.values():
        if not np.isfinite(tup[0]).all():raise AssertionError("Nonfinite exit cube")
    return ret

def outcomes_for(ret,fall_mask,fallhour,fallsign,event_exit,fall_exit,model):
    n=len(base.DAYS);d=np.arange(n)
    er,ef,eg,ew,eh=ret["event"]
    # Freeze event side and entry time from old code (not optimized).
    p=er[:,event_exit,model].copy()
    c=ef[:,event_exit,model].copy()
    g=eg[:,event_exit].copy()
    w=ew[:,event_exit].copy()
    elapsed=eh[:,event_exit].copy()
    for side in (1,-1):
        use=fall_mask&(fallsign==side)
        if not np.any(use):continue
        fr,ff,fg,fw,fh=ret[f"fall_{fallhour}_{side}"]
        p[use]=fr[use,fall_exit,model]
        c[use]=ff[use,fall_exit,model]
        g[use]=fg[use,fall_exit]
        w[use]=fw[use,fall_exit]
        elapsed[use]=fh[use,fall_exit]
    return p,c,g,w,elapsed

def metrics(p,c,g,w,t):
    stats=base.score(p,c,g,np.full(len(p),2*base.SLIP),w)
    stats["max_dd_2025_pct"]=ent.period_dd(p[:base.NTRAIN])
    stats["max_dd_2026_pct"]=ent.period_dd(p[base.NTRAIN:])
    stats["worst_losing_streak"]=base.max_loss_run(p<0)
    stats["mean_minutes_in_position"]=round(float(np.mean(t)),2)
    return stats

def chosen_daily(p,c,g,w,duration,event_hour,event_side,event_mask,fb_hour,fb_sign,cfgE,cfgF):
    h=np.where(event_mask,event_hour,fb_hour)
    s=np.where(event_mask,event_side,fb_sign)
    df=pd.DataFrame(dict(
        date_ist=base.IST_DAYS,year=np.asarray(base.DAYS.year),
        month_ist=base.MONTH_LABELS,entry_hour_ist=h.astype(int),
        side=np.where(s==1,"LONG","SHORT"),
        signal_type=np.where(event_mask,"VOLUME_FADE","MANDATORY_FALLBACK"),
        exit_recipe=np.where(event_mask,cfgE,cfgF),
        net_account_pct=100*p,
        gross_btc_points=g,
        fees_gst_btc_points=c,
        slip_btc_points=np.full(len(p),2*base.SLIP),
        exit_reason=np.where(w==1,"TAKE_PROFIT",np.where(w==2,"PROTECTIVE_STOP","TIMEOUT")),
        hold_minutes=duration
    ))
    if len(df)!=477 or df.date_ist.nunique()!=477:raise AssertionError("Daily coverage dropped")
    months=df.groupby("month_ist",sort=True).agg(
        trade_days=("date_ist","size"),
        winning_days=("net_account_pct",lambda z:int((z>0).sum())),
        losing_days=("net_account_pct",lambda z:int((z<0).sum())),
        compounded_account_return_pct=("net_account_pct",lambda z:float(100*(np.prod(1+z.to_numpy()/100)-1))),
        fees_gst_points=("fees_gst_btc_points","sum"),
        gross_points=("gross_btc_points","sum")
    ).reset_index()
    if len(months)!=22:raise AssertionError("Not all 22 months included")
    return df,months

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=base.load()
    entry_idx,_,_=base.prepare(m)
    feats=ent.build_completed_candle_features(m,entry_idx)
    allhours,allsigns,allfallbacks=ent.choose_all_policy_entries(feats)
    pol_i=ent.POLICIES.index(POL)
    eventhour=allhours[pol_i].astype(int)
    eventside=allsigns[pol_i].astype(int)
    fallbackmask=allfallbacks[pol_i]
    eventmask=~fallbackmask
    assert int(eventmask.sum())==260 and int(fallbackmask.sum())==217
    assert (eventhour[eventmask]>=18).all() and (eventhour[eventmask]<=20).all()
    fallback= fallback_features(m,entry_idx)
    cfg,cfg_names=assert_config_engine_parity()
    exitCubes=cache_entry_exits(m,entry_idx,eventhour,eventside,cfg)
    # All 14 × 2 fallback choices are independent and pre-entry.
    policies={}
    for hour in FALLBACK_HOURS:
        for rule in FALLBACK_RULES:
            signs=np.array([direction(rule,fallback[di,hour]) for di in range(len(base.DAYS))],dtype=np.int8)
            assert np.all(np.abs(signs)==1)
            policies[hour,rule]=signs
    records=[]
    for (hour,rule),sides in policies.items():
        for eidx,fidx,mode_i in product(range(len(cfg)),range(len(cfg)),range(len(MODES))):
            p,c,g,w,t=outcomes_for(exitCubes,fallbackmask,hour,sides,eidx,fidx,mode_i)
            z=metrics(p,c,g,w,t)
            z.update(fallback_hour_ist=hour,fallback_direction_rule=rule,
                event_exit=cfg_names[eidx],fallback_exit=cfg_names[fidx],
                event_exit_idx=eidx,fallback_exit_idx=fidx,
                cost_model=MODES[mode_i],
                mandatory_fallback_days=int(fallbackmask.sum()),
                volume_signal_days=int(eventmask.sum()))
            records.append(z)
    result=pd.DataFrame(records)
    assert len(result)==EXPECTED and result.trades.eq(477).all()
    result.to_csv(OUT/"all_8064_fallback_and_exit_variants.csv",index=False)
    print("STEP4_FALLBACK_GRID "+json.dumps(dict(
        models=len(result),weekday_days=len(base.DAYS),signal_days=int(eventmask.sum()),
        forced_fallback_days=int(fallbackmask.sum()),exit_recipes=len(cfg),
        fallback_rules=len(FALLBACK_RULES),fallback_hours=list(FALLBACK_HOURS))),flush=True)
    # Mandatory parity with BOTH previous reported benchmarks.
    old_static=cfg_names.index("static__sl1__tp3__hold30__activation0__value0__step0")
    old_lock=cfg_names.index("lock__sl0.5__tp3__hold30__activation0.25__value0.1__step0")
    baseline={}
    for mode_i,mode in enumerate(MODES):
        if mode!="scalper_offer":continue
        signs=policies[21,"follow60"]
        for label,idx,expect,wins in (("static",old_static,8.222995,219),
                                      ("protected",old_lock,6.786696,265)):
            p,c,g,w,t=outcomes_for(exitCubes,fallbackmask,21,signs,idx,idx,mode_i)
            z=metrics(p,c,g,w,t)
            if abs(z["net_total_pct"]-expect)>0.00011 or z["profitable_days"]!=wins:
                raise AssertionError("Critical old baseline parity failure: "+str((label,z)))
            baseline[label]=z
        print("STEP4_BASELINE_PARITY "+json.dumps(baseline,sort_keys=True),flush=True)
    summaries={}
    for mode in MODES:
        sub=result[result.cost_model==mode].copy()
        eligible=sub[(sub.return_2025_pct>0)&(sub.max_dd_2025_pct<=8.)]
        if len(eligible):
            ranking=eligible.sort_values(["profitable_days_2025","return_2025_pct","max_dd_2025_pct"],
                                        ascending=[False,False,True])
        else:
            ranking=sub.sort_values(["return_2025_pct","profitable_days_2025"],
                                     ascending=[False,False])
        chosen=ranking.iloc[0].to_dict()
        hour=int(chosen["fallback_hour_ist"]);rule=chosen["fallback_direction_rule"]
        eidx=int(chosen["event_exit_idx"]);fidx=int(chosen["fallback_exit_idx"])
        mode_i=MODES.index(mode)
        p,c,g,w,t=outcomes_for(exitCubes,fallbackmask,hour,policies[hour,rule],eidx,fidx,mode_i)
        daily,months=chosen_daily(p,c,g,w,t,eventhour,eventside,eventmask,
                                  hour,policies[hour,rule],cfg_names[eidx],cfg_names[fidx])
        daily.to_csv(OUT/(mode+"_2025_selected_daily_477.csv"),index=False)
        months.to_csv(OUT/(mode+"_2025_selected_monthly_22.csv"),index=False)
        # Was gain genuinely robust BOTH years, or is that hindsight?
        positive_both=((sub.return_2025_pct>0)&(sub.return_2026_pct>0))
        if mode=="scalper_offer":
            dominates=((sub.profitable_days>baseline["protected"]["profitable_days"])&
                 (sub.net_total_pct>baseline["protected"]["net_total_pct"])&
                 (sub.max_closed_dd_pct<=baseline["protected"]["max_closed_dd_pct"]))
            improves_win_and_return=((sub.profitable_days>baseline["protected"]["profitable_days"])&
                 (sub.net_total_pct>baseline["protected"]["net_total_pct"]))
        else:
            dominates=pd.Series(False,index=sub.index)
            improves_win_and_return=dominates
        neighborhood=sub[(sub.fallback_hour_ist==hour)&
               (sub.fallback_direction_rule==rule)&
               (sub.event_exit==chosen["event_exit"])]
        hindsight=sub.sort_values(["net_total_pct","profitable_days"],ascending=False).iloc[0].to_dict()
        summary=dict(
            selected_using_2025_only=chosen,
            any_2025_net_positive_and_dd_below_8pct=bool(len(eligible)),
            qualifying_2025_variants=int(len(eligible)),
            full_history_hindsight_best_NOT_SELECTED=hindsight,
            all_variants_positive_both_years_in_hindsight=int(positive_both.sum()),
            count_improved_both_win_count_and_net_vs_protected_hindsight=int(improves_win_and_return.sum()),
            count_improved_win_count_profit_and_drawdown_vs_protected_hindsight=int(dominates.sum()),
            chosen_2025_win_days=int((p[:base.NTRAIN]>0).sum()),
            chosen_2026_win_days=int((p[base.NTRAIN:]>0).sum()),
            selected_full_months_profitable=int((months.compounded_account_return_pct>0).sum()),
            selected_worst_month_pct=float(months.compounded_account_return_pct.min()),
            adjacent_fallback_exit_models_same_rule=int(len(neighborhood)),
            adjacent_2025_positive=int((neighborhood.return_2025_pct>0).sum()),
            adjacent_2026_positive=int((neighborhood.return_2026_pct>0).sum())
        )
        summaries[mode]=summary
        print("STEP4_SELECTED_"+mode.upper()+" "+json.dumps(summary,sort_keys=True),flush=True)
        print("STEP4_MONTHLY_"+mode.upper()+"\n"+months.to_string(index=False),flush=True)
        if mode=="scalper_offer":
            near_result=sub[improves_win_and_return].sort_values(["profitable_days","net_total_pct"],ascending=False)
            near_result.to_csv(OUT/"hindsight_both_win_count_and_profit_improved.csv",index=False)
            print("STEP4_PARETO_HINDSIGHT "+json.dumps(
                near_result.head(5).to_dict("records"),sort_keys=True),flush=True)
    result.sort_values("return_2025_pct",ascending=False).head(100).to_csv(OUT/"top100_2025_in_sample.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(dict(
        purpose="Improve 477-trade mandatory BTC daily strategy without removing days",
        daily_entries_exact=477,volume_triggered_entries=260,mandatory_fallback_entries=217,
        2025_selection_only=True,research_exposed_2026_not_blind=True,
        exit_recipes=list(cfg_names),
        fallback_direction_candidates=list(FALLBACK_RULES),
        fallback_hours_ist=list(FALLBACK_HOURS),
        cost_model="1x notional, 0.05% taker fee each side +18% GST; 5 BTC point adverse slip each side; presumed regular scalper offer <=30min closing waiver when eligible",
        results=summaries,baseline=baseline,
        cautions=["Preexisting signal and 2026 years repeatedly researched, no independent holdout",
                 "8064 comparisons create overfit; full-period best is hindsight, not a recommendation",
                 "No full bid/ask depth, funding, maker execution, exchange latency or liquidation",
                 "1m OHLC same-bar double touch assumes stop first; trailing valid next minute only"]
    ),indent=2)+"\n")
    report=["# Step 4 — Fixing the losing mandatory BTC daily fallback",
      "",f"{len(result)} backtested variations, each with exactly 477 IST weekday entries (260 initial volume signals, 217 mandatory fallback trades); two fee models.",
      "","Frozen initial volume reversal entry from Step 2. No future market info used for fallback time, direction, or exit. Exit updates valid next minute only.",
      "",
      "## Historical baseline parity","",json.dumps(baseline,indent=2),
      "","## 2025-selected models and Jan-Oct 2026 recheck","",json.dumps(summaries,indent=2),
      "","## Selected Scalper Offer monthly table","",pd.read_csv(OUT/"scalper_offer_2025_selected_monthly_22.csv").to_markdown(index=False),
      "","## Selected standard fee monthly table","",pd.read_csv(OUT/"standard_2025_selected_monthly_22.csv").to_markdown(index=False),
      "","## Cautions","The user wants daily trade coverage and positive expectancy; no variant is validated by retrospective parameter selection. 2026 was researched before this study, so is NOT independently blind. Scalper Offer historically activated is assumed and must be verified live."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STEP4_DAILY_FALLBACK_IMPROVEMENT_COMPLETE",flush=True)

if __name__=="__main__":run()
