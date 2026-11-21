#!/usr/bin/env python3
"""Stage 18 Strategy 1 ONLY: independent core signal/exit research on actual BTC 1m.
Historical BTC 2025 used for candidate selection; 2026 already previously researched.
Fully replay every alternative from original Stage14 candidate signals; do not filter
the already executed baseline trade ledger. No blending with any Donchian strategy.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive
import research_july_drawdown_stage15 as s15
import research_stage18_stage20_signal_exit_improvement_20261120 as risk_nav
import research_stage18_exit_improvement_20261121 as exit_engine

OUT=Path("analysis/stage18_independent_core_20261121")
MONTHS=risk_nav.MONTHS
# case(label, eff, adx, vol_ratio_max, risk_min, risk_max, direction, R, hold, features)
def case(name, eff=.25, adx=18., vol=1.2, minrisk=150., maxrisk=1600.,
         direction="both", reward=5., hold=240, atrlo=None, atrhi=None,
         vr5lo=None, vr5hi=None):
    return dict(name=name,eff=eff,adx=adx,vol=vol,minrisk=minrisk,maxrisk=maxrisk,
                direction=direction,reward=reward,hold=hold,
                atrlo=atrlo,atrhi=atrhi,vr5lo=vr5lo,vr5hi=vr5hi)

CASES=[
 case("original_core_5R_4h"),
 case("core_maxrisk_500",maxrisk=500),
 case("core_maxrisk_700",maxrisk=700),
 case("core_maxrisk_900",maxrisk=900),
 case("core_maxrisk_1200",maxrisk=1200),
 case("core_minrisk_300",minrisk=300),
 case("core_minrisk_400",minrisk=400),
 case("core_risk_200_900",minrisk=200,maxrisk=900),
 case("core_risk_250_1100",minrisk=250,maxrisk=1100),
 case("adx_limit_12",adx=12),
 case("adx_limit_15",adx=15),
 case("adx_limit_22",adx=22),
 case("adx_limit_25",adx=25),
 case("adx_limit_30",adx=30),
 case("adx_unrestricted",adx=1000),
 case("eff_limit_0p15",eff=.15),
 case("eff_limit_0p20",eff=.20),
 case("eff_limit_0p30",eff=.30),
 case("eff_limit_0p40",eff=.40),
 case("eff_limit_0p60",eff=.60),
 case("eff_unrestricted",eff=2.),
 case("h1vol_le_0p8",vol=.8),
 case("h1vol_le_1p0",vol=1.0),
 case("h1vol_le_1p5",vol=1.5),
 case("h1vol_le_2p0",vol=2.0),
 case("h1vol_unrestricted",vol=1000.),
 case("long_only",direction="long"),
 case("short_only",direction="short"),
 case("atr4_ratio_le_0p8",atrhi=.8),
 case("atr4_ratio_le_1p0",atrhi=1.),
 case("atr4_ratio_ge_1p0",atrlo=1.),
 case("breakout_volume_ge_1p0",vr5lo=1.),
 case("breakout_volume_ge_1p2",vr5lo=1.2),
 case("breakout_volume_le_1p0",vr5hi=1.),
 case("r3_240",reward=3.),
 case("r4_240",reward=4.),
 case("r6_240",reward=6.),
 case("r8_240",reward=8.),
 case("r5_180",hold=180),
 case("r5_360",hold=360),
 case("r5_480",hold=480),
 # Regime hypotheses, not optimized weights. Keep the original 4H/1H/15M signal.
 case("adx22_eff30",adx=22,eff=.30),
 case("adx25_eff40",adx=25,eff=.40),
 case("adx30_eff40",adx=30,eff=.40),
 case("adx25_vol15",adx=25,vol=1.5),
 case("eff30_vol15",eff=.30,vol=1.5),
 case("adx22_eff30_vol15",adx=22,eff=.30,vol=1.5),
 case("adx25_eff40_vol15",adx=25,eff=.40,vol=1.5),
 case("adx30_eff60_vol20",adx=30,eff=.60,vol=2.0),
 case("adx25_eff40_risk700",adx=25,eff=.4,maxrisk=700),
 case("adx25_eff40_risk900",adx=25,eff=.4,maxrisk=900),
 case("eff30_risk700",eff=.30,maxrisk=700),
 case("eff40_risk700",eff=.40,maxrisk=700),
 case("adx22_risk700",adx=22,maxrisk=700),
 case("vol15_risk700",vol=1.5,maxrisk=700),
 case("adx22_eff30_risk700",adx=22,eff=.30,maxrisk=700),
 case("adx25_eff40_vol15_risk900",adx=25,eff=.40,vol=1.5,maxrisk=900),
 case("adx25_eff40_vol15_r6",adx=25,eff=.40,vol=1.5,reward=6.),
 case("adx25_eff40_vol15_hold360",adx=25,eff=.40,vol=1.5,hold=360),
]
def load_events(f):
    e=pd.read_csv(risk_nav.EVENTS)
    ix=f.time.to_numpy(np.int64)
    source_ts=e.entry_unix.to_numpy(np.int64)
    corrected=pd.Index(ix).get_indexer(source_ts)
    if (corrected<0).any():raise AssertionError("Original events not found in BTC 1m archive")
    stale=int(np.count_nonzero(e.k.to_numpy(int)!=corrected))
    e=e.copy()
    e["k"]=corrected
    print("CORE_REINDEXED_EVENTS",json.dumps(dict(source=len(e),stale=stale)))
    return e

def metrics(month_returns):
    v=np.asarray(month_returns,float)
    nav=np.cumprod(1+v/100)
    peak=np.maximum.accumulate(np.r_[1.,nav])[1:]
    return dict(net_pct=float(100*(nav[-1]-1)),
        positive_months=int((v>1e-9).sum()),
        negative_months=int((v< -1e-9).sum()),
        flat_months=int((abs(v)<=1e-9).sum()),
        monthend_dd_pct=float(100*np.max(1-nav/peak)),
        worst_month_pct=float(v.min()))

def run_case(f,events,c):
    e=events[(events.family==s15.FAMILY)&
             (events.previous_month_eff<=c["eff"])&
             (events.h4_adx<=c["adx"])&
             (events.h1_vr<=c["vol"])&
             (events.risk_pts>=c["minrisk"])&
             (events.risk_pts<=c["maxrisk"])]
    if c["direction"]=="long":e=e[e.side==1]
    if c["direction"]=="short":e=e[e.side==-1]
    if c["atrlo"] is not None:e=e[e.h4_atr_ratio>=c["atrlo"]]
    if c["atrhi"] is not None:e=e[e.h4_atr_ratio<=c["atrhi"]]
    if c["vr5lo"] is not None:e=e[e.volume_ratio_5m>=c["vr5lo"]]
    if c["vr5hi"] is not None:e=e[e.volume_ratio_5m<=c["vr5hi"]]
    e=e.sort_values(["k","side"],kind="stable")
    O=f.open.to_numpy(float);H=f.high.to_numpy(float)
    L=f.low.to_numpy(float);C=f.close.to_numpy(float)
    T=f.time.to_numpy(np.int64)
    busy=-1;rows=[];hold=int(c["hold"])
    for z in e.itertuples(index=False):
        k=int(z.k)
        if k<=busy or k+hold>len(T):continue
        if T[k+hold-1]-T[k]!=60*(hold-1):continue
        j,reason,gross,net,netR,risk=exit_engine.replay(O,H,L,C,k,int(z.side),
                float(z.stop_price),float(c["reward"]),hold,"fixed",{})
        busy=j
        rows.append(dict(variant=c["name"],entry_unix=int(T[k]),exit_unix=int(T[j]),
                direction=int(z.side),reason=reason,entry_mid=float(O[k]),
                initial_risk_pts=float(risk),net_pts=float(net),net_R=float(netR),
                held_minutes=int(j-k+1)))
    if not rows:return None
    g=pd.DataFrame(rows).sort_values(["exit_unix","entry_unix"],kind="stable")
    g["exit_month_ist"]=pd.to_datetime(g.exit_unix,unit="s",utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    g=g[g.exit_month_ist.isin(MONTHS)].copy().reset_index(drop=True)
    if g.empty:return None
    g["risk_fraction"]=np.minimum(risk_nav.RISK_FRACTION,
                                 risk_nav.MAX_LEVERAGE*g.initial_risk_pts/g.entry_mid)
    return g

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,_,_,quality=read_archive()
    events=load_events(f)
    outputs=[];trades=[];monthrows=[]
    baseline=None
    for c in CASES:
        g=run_case(f,events,c)
        if g is None:continue
        trades.append(g)
        if c["name"]=="original_core_5R_4h":baseline=g.copy()
        for bps in (0,2,5):
            rv=risk_nav.replay_nav(g,bps)
            ar=np.asarray([z["net_pct"] for z in rv["monthly"]])
            whole=metrics(ar);train=metrics(ar[:12]);check=metrics(ar[12:])
            outputs.append(dict(model=c["name"],extra_slippage_bps_side=bps,
                trades=len(g),wins=int((g.net_R>0).sum()),stops=int((g.reason=="stop").sum()),
                targets=int((g.reason=="target").sum()),timeouts=int((g.reason=="timeout").sum()),
                net_R_profit_factor=float(rv["pf_net_R"]),
                train_2025_return_pct=train["net_pct"],
                train_2025_pos=train["positive_months"],
                train_2025_dd=train["monthend_dd_pct"],
                exposed_2026_return_pct=check["net_pct"],
                exposed_2026_pos=check["positive_months"],
                **whole))
            monthrows.extend(dict(model=c["name"],extra_slippage_bps_side=bps,
                 month_ist=m,return_pct=float(v),number_trades=int(z["trades"]),
                 net_R=float(z["net_R"])) for m,v,z in zip(MONTHS,ar,rv["monthly"]))
    if baseline is None or len(baseline)!=75:raise AssertionError("Core baseline 75 trades missing")
    # Independently verify that 75 baseline trades replay unchanged.
    old=exit_engine.simulate(events,f,exit_engine.CASES[0])
    if (not np.array_equal(old.entry_unix.to_numpy(),baseline.entry_unix.to_numpy()) or
        not np.array_equal(old.exit_unix.to_numpy(),baseline.exit_unix.to_numpy()) or
        np.max(np.abs(old.net_R.to_numpy()-baseline.net_R.to_numpy()))>1e-5):
        raise AssertionError("Core baseline fill parity failed")
    print("CORE_BASELINE_PARITY_75_OK")
    summary=pd.DataFrame(outputs)
    monthly=pd.DataFrame(monthrows)
    stress=summary[summary.extra_slippage_bps_side==2].copy()
    # Rank using 2025 stressed standalone after-cost return and 2025-only DD.
    stress["score_2025_only"]=(stress.train_2025_return_pct +
                      .2*stress.train_2025_pos -
                      .8*stress.train_2025_dd)
    stress=stress.sort_values(["score_2025_only","train_2025_return_pct"],
                              ascending=False,kind="stable")
    sel=str(stress.iloc[0].model)
    summary.to_csv(OUT/"core_1m_standalone_results.csv",index=False)
    monthly.to_csv(OUT/"core_22_months.csv",index=False)
    pd.concat(trades,ignore_index=True).to_csv(OUT/"core_all_trades.csv.gz",index=False,compression="gzip")
    (OUT/"core_methodology.json").write_text(json.dumps(dict(
        family="Stage18 Strategy 1 only",
        source=quality,cases=CASES,number_cases=len(CASES),
        baseline="original_core_5R_4h",chosen_on_2025_only=sel,
        selection="BTC 2025 standalone monthly net return and month-end DD after extra 2bp per side",
        caveats=[
         "All 2025 and 2026 historical periods are research exposed, not true forward OOS",
         "1m OHLC stop-first and next minute entry; fees 0.05% per side plus GST18%",
         "5 BTC pts adverse slip per side; extra 0/2/5 bps each side stress",
         "Position risk 0.5% NAV with 3x notional cap",
         "Funding, actual bid/ask, margin/liquidations and intrabar tick path excluded",
         "Core exits allocated to exit IST month; no mark-to-market of open trades at month end",
         "Selection performed only on 2025 with reused history, multiple tests, overfit danger",
         "Strategy 2/Donchian NOT present in this backtest"]),indent=2,default=str))
    for x in summary[(summary.model.isin([sel,"original_core_5R_4h"]))].to_dict("records"):
        print("CORE_AUDIT",json.dumps(x,default=str))
    print("CORE_2025_ONLY_RANK",stress[["model","trades","train_2025_return_pct",
          "train_2025_pos","exposed_2026_return_pct","net_pct",
          "positive_months","negative_months","net_R_profit_factor"]].head(15).to_json(orient="records"))
    print("CORE_STANDALONE_DONE",json.dumps(dict(cases=len(CASES),selected=sel)))
if __name__=="__main__":main()
