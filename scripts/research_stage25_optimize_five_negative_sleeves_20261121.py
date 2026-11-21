#!/usr/bin/env python3
"""Stage25: independently optimize five LOSS-MAKING sleeves of Stage18 22/22 oracle.

This is an authentic BTCUSD 1m OHLC next-open/stop-first trade replay, NOT an
optimization of already-aggregated monthly numbers. We preserve frozen original
strategy definitions and independently test causal modifications.

IN-SAMPLE SELECTION: 2025 only. REPORT: Jan-Oct 2026, which is already exposed
to previous research (NOT a pristine forward holdout). 0.05% taker each leg,
18% GST and 5 BTC points adverse slip per side from source backtest engines.
Approximate 2/5bps surcharge on 1H/5M computed using entry quote notional on
BOTH execution legs; swing surcharge not computed because trades remain MTM
over months. Funding, actual spread, liquidation/lot sizing excluded.

No live orders, no overwriting the existing strategy, no month-based toggles.
"""
from pathlib import Path
from collections import Counter
import itertools
import json
import math
import numpy as np
import pandas as pd
import research_every_candle_200 as src
import research_swing_donchian_stage17 as swing
import research_new_1h_patterns_stage19 as hour
import research_signal_inversion_stage20 as five
from research_structure_rr_stage11 import replay_one

OUT=Path("analysis/stage25_optimize_five_negative_sleeves_20261121")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
MONTH_INDEX={m:i for i,m in enumerate(MONTHS)}
EPS=1e-8
ORIGINALS={
    "H4_DONCHIAN55":dict(model="4H_channel_55_ema50_agrees_trail_3atr",
                         expected_pct=-5.1027651),
    "H1_COMPRESSION_EFF30_2R":dict(model="compression_expansion_12h__4h_efficiency_ge30__2R__240min",
                                  expected_pct=-.06102713),
    "H1_COMPRESSION_UNFILTERED_3R":dict(model="compression_expansion_12h__all__3R__240min",
                                       expected_pct=-.13805138),
    "H1_EMA20_PULLBACK_EFF30_3R":dict(model="ema20_pullback_confirm__4h_efficiency_ge30__3R__240min",
                                     expected_pct=-11.99460565),
    "M5_COMPRESSION_LARGEATR_4R":dict(model="original_large_atr_atr1p5_4R_120min",
                                    expected_pct=-13.62346559),
}

def score(v):
    v=np.asarray(v,dtype=float)
    if len(v)!=22 or not np.isfinite(v).all():raise AssertionError("Missing or non-finite returns")
    nav=np.cumprod(1+v/100)
    if (nav<=0).any():raise AssertionError("Bankruptcy")
    peaks=np.maximum.accumulate(np.r_[1.,nav])[1:]
    # Train-only max equity drawdown.
    p25=np.maximum.accumulate(np.r_[1.,nav[:12]])[1:]
    return dict(
      net_22_pct=float(100*(nav[-1]-1)),
      profitable_22=int(np.count_nonzero(v>EPS)),
      losing_22=int(np.count_nonzero(v<-EPS)),
      flat_22=int(np.count_nonzero(np.abs(v)<=EPS)),
      train_2025_pct=float(100*(np.prod(1+v[:12]/100)-1)),
      train_2025_profitable=int(np.count_nonzero(v[:12]>EPS)),
      train_2025_losing=int(np.count_nonzero(v[:12]<-EPS)),
      train_2025_max_dd_pct=float(100*np.max(1-nav[:12]/p25)),
      seen_2026_pct=float(100*(np.prod(1+v[12:]/100)-1)),
      seen_2026_profitable=int(np.count_nonzero(v[12:]>EPS)),
      seen_2026_losing=int(np.count_nonzero(v[12:]<-EPS)),
      sep_2026_pct=float(v[20]),
      worst_month_pct=float(np.min(v)),
      max_monthend_dd_pct=float(100*np.max(1-nav/peaks)))

def conservative_r_bonus(risk,entry_mid,bps):
    # Additional bps per side, approximate notional using ENTRY mid on
    # both legs. Counts as additional adverse cost over existing base model.
    return (2*bps*1e-4*entry_mid)/risk

def monthly_exit_replay(trades,stress):
    # A trade tuple: (entry_unix, exit_unix, risk_pts, entry_mid, net_R).
    arr=np.ones(22,np.float64)
    trade_month=np.zeros(22,np.int32)
    train_trades=0
    for t0,t1,risk,entry,netR in trades:
        m=pd.Timestamp(int(t1),unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m")
        if m not in MONTH_INDEX:continue
        ix=MONTH_INDEX[m]
        net=netR-conservative_r_bonus(risk,entry,stress)
        used=min(.005,5*risk/entry)
        if used*net<=-1:raise AssertionError("Model bankrupt")
        arr[ix]*=(1+used*net)
        trade_month[ix]+=1
        if ix<12:train_trades+=1
    return 100*(arr-1),trade_month,train_trades

def selection_score(r,stress_bps=2):
    # Strict 2025 selection. Older months may already have been explored
    # but no 2026 values enter the parameter ranking.
    key="stress2_" if stress_bps==2 else ""
    return (float(r[key+"train_2025_pct"]) -
            .45*float(r[key+"train_2025_max_dd_pct"]) +
            .08*int(r[key+"train_2025_profitable"]))

def add_row(rows,month_rows,group,model,setting,monthly_by_stress,
            trade_count,train_trades,baseline=False):
    stats=score(monthly_by_stress[0])
    r=dict(group=group,model=model,parameters=json.dumps(setting,sort_keys=True),
           baseline=bool(baseline),trades=trade_count,train_2025_trades=train_trades,
           **stats)
    for b in (2,5):
        if b in monthly_by_stress:
            s=score(monthly_by_stress[b])
            for key,val in s.items():r[f"stress{b}_{key}"]=val
        else:
            for key in stats:r[f"stress{b}_{key}"]=np.nan
    # For swings no approximate surcharge is computed; use baseline cost
    # only and keep this clearly separated from 1h/5m cost rankings.
    r["cost_selection_bps"]=2 if 2 in monthly_by_stress else 0
    for k in MONTHS:
        i=MONTH_INDEX[k]
        z=dict(group=group,model=model,month_ist=k,
               net_month_pct=float(monthly_by_stress[0][i]),
               stress2_month_pct=float(monthly_by_stress.get(2,monthly_by_stress[0])[i]),
               stress5_month_pct=float(monthly_by_stress.get(5,monthly_by_stress[0])[i]),
               no_extra_cost_stress_for_swing=2 not in monthly_by_stress)
        month_rows.append(z)
    r["train_selection_score"]=selection_score(r,r["cost_selection_bps"])
    rows.append(r)

def swing_variants(f,segstart):
    mid,months=swing.build_months(f)
    if MONTHS!=months[:22]:raise AssertionError("Swing IST period boundaries differ")
    O=f.open.to_numpy(float);H=f.high.to_numpy(float)
    L=f.low.to_numpy(float);C=f.close.to_numpy(float);T=f.time.to_numpy(np.int64)
    raws=[];monthly=[]
    group="H4_DONCHIAN55"
    # Relaxes channel length, direction confirmation and trail, while preserving
    # initial stop 2x ATR and 14-day time cap. All updates after complete 4H.
    bars=swing.higher_bars(f,"4H")
    for look in (24,40,55,80):
        for trend in ("ema50_agrees","no_trend_filter"):
            sig,upd,atr,close,signals=swing.signals(f,bars,look,trend)
            for trail in (2.0,2.5,3.0,3.5,4.0,4.5,5.0):
                label=f"4H_channel_{look}_{trend}_trail_{trail:g}atr"
                trades,mE,entries,exposure,dd=swing.run_one(
                    O,H,L,C,T,mid,segstart,sig,upd,atr,close,trail,len(months))
                if np.isnan(mE).any():raise AssertionError("Missing MTM month")
                full=100*(mE[1:]/mE[:-1]-1)
                month=np.r_[100*(mE[0]/swing.START_EQUITY-1),full][:22]
                # trade exit month is only for sample count, not mark-to-market.
                ntrain=sum(pd.Timestamp(int(t[1]),unit="s",tz="UTC").tz_convert(
                    "Asia/Kolkata").year==2025 for t in trades)
                setting=dict(channel=look,trend=trend,trail_atr=trail,
                     initial_stop_atr=2,hold_days=14,source_signal_count=signals)
                add_row(raws,monthly,group,label,setting,{0:month},
                        len(trades),ntrain,baseline=label==ORIGINALS[group]["model"])
    return raws,monthly

def hour_variants(f,ends):
    ev=hour.build_candidates(f,ends)
    O=f.open.to_numpy(float);H=f.high.to_numpy(float)
    L=f.low.to_numpy(float);C=f.close.to_numpy(float)
    T=f.time.to_numpy(np.int64)
    raws=[];monthly=[]
    targets={
       "H1_COMPRESSION_EFF30_2R":("compression_expansion_12h","4h_efficiency_ge30",2.0),
       "H1_COMPRESSION_UNFILTERED_3R":("compression_expansion_12h","all",3.0),
       "H1_EMA20_PULLBACK_EFF30_3R":("ema20_pullback_confirm","4h_efficiency_ge30",3.0),
    }
    # Need unique baseline labels even when exploring same compression pattern
    # under two different original group identities.
    for group,(pattern,original_regime,original_rr) in targets.items():
        e=ev[ev.pattern==pattern]
        for reg in ("all","4h_efficiency_ge30","4h_adx_ge25","4h_atr_ratio_le1"):
            gated=e.loc[hour.gate_mask(e,reg)]
            for direction in ("both","long","short"):
                subset=gated if direction=="both" else gated[gated.side==(1 if direction=="long" else -1)]
                for rr,hold in itertools.product((1.5,2.,2.5,3.,4.,5.),
                                                  (120,240,480,720)):
                    model=f"{pattern}__{reg}__{direction}__{rr:g}R__{hold}min"
                    tr=[];busy=-1
                    for z in subset.itertuples(index=False):
                        k=int(z.k)
                        if k<=busy or ends[k]-k<hold:continue
                        j,why,gross,net,offer,netR,risk=replay_one(
                            O,H,L,C,k,int(z.side),float(z.stop),float(rr),int(hold))
                        busy=j
                        tr.append((int(z.unix),int(T[j]),float(risk),float(O[k]),float(netR)))
                    stresses={}
                    for bps in (0,2,5):
                        stresses[bps],nby,ntrain=monthly_exit_replay(tr,bps)
                    original=(reg==original_regime and direction=="both" and
                              rr==original_rr and hold==240)
                    setting=dict(pattern=pattern,regime=reg,side=direction,
                                 reward_R=rr,max_hold_minutes=hold,
                                 stop="source structural 1H",
                                 extra2bps_approximation="2bps per side x entry notional")
                    add_row(raws,monthly,group,model,setting,stresses,
                            len(tr),ntrain,baseline=original)
    return raws,monthly

def five_variants(f,segstart,segend):
    e=five.signals_source(f,segstart,segend)
    e=e[e.pattern=="compression_break"].copy()
    op=f.open.to_numpy(float);hi=f.high.to_numpy(float)
    lo=f.low.to_numpy(float);cl=f.close.to_numpy(float)
    ts=f.time.to_numpy(np.int64)
    group="M5_COMPRESSION_LARGEATR_4R"
    raws=[];monthly=[]
    for direction in ("original","reverse"):
        side_arr=e.side.to_numpy(np.int8)*(1 if direction=="original" else -1)
        gates=five.fit_filter(e,side_arr,"original")
        for filtername in ("large_atr","any","hour_trend_agrees_with_trade",
                           "hour_trend_opposes_trade","high_volume","low_volume"):
            sub=e.loc[gates[filtername]].sort_values(["k","side"],kind="stable")
            for stop,rr,hold in itertools.product(("atr1p5","atr2","atr3","struct3"),
                                                  (1.5,2.,3.,4.,5.),
                                                  (30,120,240)):
                model=f"{direction}_{filtername}_{stop}_{rr:g}R_{hold}min"
                tr=[];busy=-1
                for z in sub.itertuples(index=False):
                    k=int(z.k)
                    if k<=busy or segend[k]-k<hold:continue
                    side=int(z.side)*(1 if direction=="original" else -1)
                    r=float(z.struct_risk) if stop=="struct3" else (
                      float(stop[3:])*float(z.atr5) if stop in ("atr2","atr3") else
                      1.5*float(z.atr5))
                    if not math.isfinite(r) or r<120 or r>2000:continue
                    j,netR,offerR,net,offer,why=five.simulate_one(
                        op,hi,lo,cl,k,side,float(r),float(rr),int(hold))
                    busy=int(j)
                    tr.append((int(z.entry_unix),int(ts[j]),r,float(op[k]),float(netR)))
                stresses={}
                for bps in (0,2,5):
                    stresses[bps],nby,ntrain=monthly_exit_replay(tr,bps)
                original=(direction=="original" and filtername=="large_atr" and
                          stop=="atr1p5" and rr==4.0 and hold==120)
                setting=dict(pattern="5m compression_break",direction=direction,
                     filter=filtername,stop=stop,reward_R=rr,hold_min=hold,
                     risk_fraction=.005,max_leverage=5,
                     extra2bps_approximation="2bps per side x entry notional")
                add_row(raws,monthly,group,model,setting,stresses,len(tr),ntrain,
                        baseline=original)
    return raws,monthly

def chosen_strategy(group,g):
    # Intentionally use only 2025, not Sep2026 or total_22. 2026 seen before,
    # so even these selection decisions are research, not a pristine holdout.
    eligible=g[g.train_2025_trades>=8].copy()
    if len(eligible)==0:return None
    eligible=eligible.sort_values(["train_selection_score","train_2025_trades"],
                                  ascending=[False,False],kind="stable")
    return eligible.iloc[0]

def compare(rows,monthly):
    out=pd.DataFrame(rows)
    mon=pd.DataFrame(monthly)
    baseline=[];selected=[];histbest=[]
    for group,g in out.groupby("group",sort=False):
        ref=g[g.baseline]
        if len(ref)!=1:raise AssertionError(f"Need ONE baseline for {group}; got {len(ref)}")
        ref=ref.iloc[0]
        expected=ORIGINALS[group]["expected_pct"]
        if abs(float(ref.net_22_pct)-expected)>.1:
            raise AssertionError(f"Baseline parity for {group}: got {ref.net_22_pct}, expected {expected}")
        selectedrow=chosen_strategy(group,g)
        historical=g.sort_values("net_22_pct",ascending=False).iloc[0]
        for label,z,collection in (("BASELINE",ref,baseline),
                                   ("TRAIN2025_SELECTED",selectedrow,selected),
                                   ("INVALID_HINDSIGHT_BEST_22MONTH",historical,histbest)):
            if z is None:continue
            record=z.to_dict()
            record["selection_type"]=label
            collection.append(record)
            print(label,json.dumps(record,default=str))
    out.to_csv(OUT/"all_five_families_trade_replay_summary.csv",index=False)
    mon.to_csv(OUT/"all_candidate_monthly_results.csv.gz",compression="gzip",index=False)
    pd.DataFrame(baseline+selected+histbest).to_csv(
        OUT/"baseline_vs_train_selected_vs_invalid_hindsight.csv",index=False)
    bases={x["group"]:x for x in baseline}
    select={x["group"]:x for x in selected}
    months=[]
    for g in ORIGINALS:
        b=bases[g];s=select.get(g)
        for name,record in (("BASELINE",b),("TRAIN2025_SELECTED",s)):
            if record is None:continue
            v=mon[(mon.group==g)&(mon.model==record["model"])]
            if len(v)!=22:raise AssertionError("Missing monthly rows for "+g)
            months.extend(dict(row._asdict(),comparison=name) for row in v.itertuples(index=False))
    pd.DataFrame(months).to_csv(OUT/"baseline_and_selected_monthly.csv",index=False)
    quality=dict(
      groups=5,configs_tested=len(out),by_family=out.groupby("group").size().to_dict(),
      selected_2025_positive_count=sum(x["train_2025_pct"]>0 for x in selected),
      selected_seen2026_positive_count=sum(x["seen_2026_pct"]>0 for x in selected),
      selected_full22_positive_count=sum(x["net_22_pct"]>0 for x in selected),
      baseline_parity_verified=True,
      selected_strategies=selected,baseline_strategies=baseline,
      warnings=[
        "Selection is exclusively 2025 training; 2026 has been previously examined and is not pristine",
        "All five original models are unmodified; modified ones remain research candidates",
        "Stage17 swing MTM; Stage19 1H and Stage20 5M grouped by CLOSED trade EXIT month",
        "1m next-open entries and stop-first fills at modeled 0.05% taker+18%GST, 5BTC slip each leg",
        "Extra 2/5 bps surcharge per leg approximated using entry quote; for 1H and 5M only",
        "Stage17 MTM engine not fully re-costed at extra 2/5bps, so cross-family robustness is not directly comparable",
        "No actual bid/ask, futures funding, contract min size, exchange margins, liquidation or shared account",
        "A positive 22m return does not establish positive expectancy in unseen forward data",
        "No live execution, no alterations to active strategy, no guarantee of profitable calendar months",
      ])
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2,default=str)+"\n")
    print("STAGE25_OPTIMIZATION_COMPLETE",json.dumps(dict(
      variants=len(out), selected=selected, baseline_parity=True),default=str))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,segstart,segend,quality=src.read_archive()
    print("SOURCE_BTC_1M",json.dumps(dict(
      candles=len(f),files=quality["months"],missing_minutes=quality["missing_minutes"])))
    allrows=[];allmonths=[]
    for fun in (lambda:swing_variants(f,segstart),
                lambda:hour_variants(f,segend),
                lambda:five_variants(f,segstart,segend)):
        a,b=fun()
        allrows.extend(a);allmonths.extend(b)
        print("REPLAY_BLOCK_COMPLETE",json.dumps(dict(
            model_count=len(a),groups=Counter(row["group"] for row in a))))
    compare(allrows,allmonths)
if __name__=="__main__":
    main()
