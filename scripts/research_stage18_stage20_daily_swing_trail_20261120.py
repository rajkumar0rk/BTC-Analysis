#!/usr/bin/env python3
"""Native BTC 1m Stage17 swing ATR-trail distance improvement for Stage18/20.

Stage18/20 original portfolio mixed Stage15 and Stage17 monthly values. This
script re-executes BOTH Stage15 primary and Stage17 daily swing on genuine
BTCUSD 1m candles. Stage20's 10% Stage19 hourly sleeve remains archived.
Trades in independently capital-allocated sleeves can overlap; NO shared
margin/contract lot or liquidation engine. Historic 2026 is research-exposed.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive
import research_swing_donchian_stage17 as stage17
import research_stage18_stage20_signal_exit_improvement_20261120 as prior
import research_stage18_stage20_monthly_edge_20261120 as edge

OUT=Path("analysis/stage18_stage20_daily_swing_trailing_20261120")
MONTHS=prior.MONTHS
DAILY_MODELS={
 "Stage18":("1D",55,"ema50_agrees"),
 "Stage20":("1D",20,"no_trend_filter")
}
# Predeclared controlled sensitivity to DAILY ATR trailing distance. 3ATR is
# original; smaller exits protect faster, larger allow trends to run.
TRAIL_ATR=(1.5,2.0,2.5,3.0,3.5,4.0,4.5,5.0,6.0)
# The widening of the Stage15 prior-month efficiency regime to 25% was
# identified after examining 2026 in the earlier study (post hoc), so it is
# a SEPARATE exploratory scenario, NOT part of the clean 2025 selection.
CORES=("reference_5R","5R_regime_25pct_adx18")
def period(x):
    x=np.asarray(x,dtype=float)
    if np.any(~np.isfinite(x)) or np.any(x<=-100):raise AssertionError("Invalid NAV")
    nav=np.cumprod(1+x/100)
    highs=np.maximum.accumulate(np.r_[1.,nav])[1:]
    return dict(net_pct=round(float((nav[-1]-1)*100),6),
      positive=int((x>1e-8).sum()),losing=int((x<-1e-8).sum()),
      flat=int((abs(x)<=1e-8).sum()),
      dd_monthend_pct=round(float(100*np.max(1-nav/highs)),6),
      worst_pct=round(float(x.min()),6))
def metrics(navr):
    t=period(navr[:12]);c=period(navr[12:]);a=period(navr)
    return dict(train_2025_return_pct=t["net_pct"],
      train_2025_positive_months=t["positive"],
      train_2025_losing_months=t["losing"],
      train_2025_monthend_dd_pct=t["dd_monthend_pct"],
      train_2025_worst_month_pct=t["worst_pct"],
      check_2026JanOct_return_pct=c["net_pct"],
      check_2026JanOct_positive_months=c["positive"],
      check_2026JanOct_losing_months=c["losing"],
      all22_net_pct=a["net_pct"],
      all22_positive_months=a["positive"],
      all22_losing_months=a["losing"],
      all22_flat_months=a["flat"],
      all22_dd_monthend_pct=a["dd_monthend_pct"])
def swing_months(f,seg_start,mon_id,months,side,freq,lookback,trend,trail):
    sig,upd,atr,ref,nsig=stage17.signals(f,side,lookback,trend)
    O=f.open.to_numpy(np.float64);H=f.high.to_numpy(np.float64)
    L=f.low.to_numpy(np.float64);C=f.close.to_numpy(np.float64)
    T=f.time.to_numpy(np.int64)
    trades,marks,entries,expo,trade_dd=stage17.run_one(
       O,H,L,C,T,mon_id,seg_start,sig,upd,atr,ref,trail,len(months))
    vals=np.full(len(marks),np.nan)
    previous=100.
    for j,mark in enumerate(marks):
        vals[j]=100*(mark/previous-1)
        previous=mark
    r=np.array([z[5] for z in trades],dtype=float)
    gains=r[r>0].sum();loss=-r[r<0].sum()
    profile=dict(trades=len(trades),win=int((r>0).sum()),
      lose=int((r<0).sum()),trade_pf=round(float(gains/loss),5) if loss>0 else None,
      trade_to_trade_max_dd_pct=float(trade_dd)*100,signals=nsig)
    return vals,profile,trades
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,segstart,_,quality=read_archive()
    mon_id,months=stage17.build_months(f)
    if months[:22]!=MONTHS:raise AssertionError("IST month labels mismatch")
    daily_bars=stage17.higher_bars(f,"1D")
    sleeves=prior.saved_sleeves()
    events=pd.read_csv(prior.EVENTS)
    core_arrays={}
    for c in edge.CASES:
        if c[0] in CORES:
            g,_,_,_=edge.run_case(events,f,c)
            core_arrays[c[0]]={bps:prior.replay_nav(g,bps) for bps in (0,2,5)}
    if set(core_arrays)!=set(CORES):raise AssertionError("Missing trade-replayed core")
    results=[];monthly=[];trade_records=[];audit={}
    for family,(freq,lookback,trend) in DAILY_MODELS.items():
        # Signals depend on unchanged original Daily20/55 entry rules.
        sig,updates,atr,ref,signals_seen=stage17.signals(f,daily_bars,lookback,trend)
        O=f.open.to_numpy(np.float64);H=f.high.to_numpy(np.float64)
        L=f.low.to_numpy(np.float64);C=f.close.to_numpy(np.float64)
        T=f.time.to_numpy(np.int64)
        for trail in TRAIL_ATR:
            trades,marks,entries,expo,trade_dd=stage17.run_one(
              O,H,L,C,T,mon_id,segstart,sig,updates,atr,ref,trail,len(months))
            if not np.isfinite(marks).all():raise AssertionError("Missing monthly MTM")
            prior_nav=100.
            swing_full=[]
            for nav in marks:
                swing_full.append(100*(nav/prior_nav-1))
                prior_nav=nav
            swing=np.asarray(swing_full[:22],dtype=float)
            base_swing=sleeves["d55"] if family=="Stage18" else sleeves["d20"]
            if trail==3.0:
                diff=float(np.max(np.abs(swing-base_swing)))
                if diff>.035:raise AssertionError(f"Daily Stage17 baseline changed {family} {diff}")
                audit[family]=round(diff,8)
            v=np.asarray([t[5] for t in trades],dtype=float)
            winning=float(v[v>0].sum());losing=-float(v[v<0].sum())
            pf=winning/losing if losing>0 else None
            for core_name,stress_map in core_arrays.items():
                for stress,core in stress_map.items():
                    range_months=np.asarray([x["net_pct"] for x in core["monthly"]],float)
                    if family=="Stage18":
                        combined=.75*range_months+.25*swing
                    else:
                        combined=.9*(.75*range_months+.25*swing)+.1*sleeves["hourly"]
                    info=metrics(combined)
                    results.append(dict(family=family,core=core_name,
                      swing_trail_ATR=trail,stress_primary_bps_per_side=stress,
                      daily_swing_trades=int(len(trades)),daily_swing_pf=pf,
                      daily_swing_trade_dd_pct=float(trade_dd)*100,
                      daily_swing_positive_months=int((swing>1e-9).sum()),
                      **info))
                    monthly.extend(dict(family=family,core=core_name,
                      swing_trail_ATR=trail,stress_primary_bps_per_side=stress,
                      month_ist=m,monthly_account_pct=float(x),
                      range_pct=float(r),swing_pct=float(s)) for m,x,r,s in zip(
                         MONTHS,combined,range_months,swing))
            trade_records.extend(dict(family=family,swing_trail_ATR=trail,
              entry_unix=int(t[0]),exit_unix=int(t[1]),side=int(t[2]),
              initial_risk_pts=float(t[3]),net_price_points=float(t[4]),
              net_R=float(t[5]),exit_reason=int(t[6])) for t in trades)
    result=pd.DataFrame(results)
    m=pd.DataFrame(monthly)
    chosen={}
    for fam in DAILY_MODELS:
        # Only core=ORIGINAL 5R is used for causal BTC-2025 rule choice.
        train=result[(result.family==fam)&(result.core=="reference_5R")&
                     (result.stress_primary_bps_per_side==2)].copy()
        train["score_BTC2025"]=(train.train_2025_return_pct+
           .60*train.train_2025_positive_months-
           .80*train.train_2025_monthend_dd_pct-
           .30*np.maximum(0,-train.train_2025_worst_month_pct))
        train=train.sort_values(["score_BTC2025","train_2025_return_pct"],
                                 ascending=False,kind="stable")
        trail=float(train.iloc[0].swing_trail_ATR)
        chosen[fam]=trail
        print("STAGE17_SLEEVE_BASELINE_MATCH",fam,audit[fam])
        print("BTC2025_SWING_TRAIL_RANK",fam,train[[
           "swing_trail_ATR","score_BTC2025","train_2025_return_pct",
           "train_2025_positive_months","train_2025_monthend_dd_pct"]].to_json(orient="records"))
        print("FROZEN_2025_DAILY_TRAIL",fam,trail)
        for core in CORES:
            for multiple in dict.fromkeys((3.,trail)):
                for stress in (0,2,5):
                    row=result[(result.family==fam)&(result.core==core)&
                       (result.swing_trail_ATR==multiple)&
                       (result.stress_primary_bps_per_side==stress)]
                    print("STAGE17_NATIVE_MONTHLY_RESULT",row.iloc[0].to_json())
    result.to_csv(OUT/"all_daily_swing_exit_variants.csv",index=False)
    m.to_csv(OUT/"all_22_months_each_variant.csv",index=False)
    pd.DataFrame(trade_records).to_csv(OUT/"all_native_stage17_swing_trades.csv.gz",compression="gzip",index=False)
    (OUT/"selected_on_BTC2025.json").write_text(json.dumps(chosen,indent=2)+"\n")
    (OUT/"limitations.json").write_text(json.dumps(dict(
      1m_source_quality=quality,
      study="Actual BTC 1m replays of original Stage15 trades and Stage17 swing trade engine; Stage20 hourly sleeve remains archived monthly",
      change="Stage17 3xATR original trailing-stop spacing to alternative ATR distances; actual stop touch on 1m high/low; 14-day holding cap unchanged.",
      selection="Only BTC 2025 and reference 5R primary; add 2bp/side stress only to primary core; no 2026 selection or retuning",
      claims_not_supported=[
        "No native ETH replay.",
        "BTC 2026 already research-exposed; no pristine forward holdout",
        "Underlying 1m BTC source has known missing minute/day gap; 2025 Jan IST start incomplete.",
        "Concurrent strategy sleeves do NOT share a fully simulated actual account margin, liquidation, funding or contract-size engine.",
        "Original Stage17 assumes fractional risk sizing, 0.05% taker each side + GST + 5 index points slip each side; L1 liquidity/market impact absent.",
        "Portfolio is still a blend of monthly component returns, not exact intramonth common NAV; Stage15 books at trade exit month, Stage17 marks monthly.",
        "Widened 25% prior-month filter came from historically exposed 2026 comparison and is an exploratory secondary result."
      ],no_live_execution=True),indent=2,default=str)+"\n")
    print("NATIVE_1M_SWING_TRAILING_MONTHLY_RESULTS_COMPLETE",json.dumps(chosen))
if __name__=="__main__":main()
