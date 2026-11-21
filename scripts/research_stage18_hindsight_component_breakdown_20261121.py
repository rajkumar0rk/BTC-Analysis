#!/usr/bin/env python3
"""Historical Stage18 22/22 hindsight-fit component attribution, NON-LIVE.

Audit EVERY original sleeve in the published 22/22 LP portfolio. All inputs
come from the repo's independently run Stage17 (swing) / Stage19 (1H) /
Stage20 (5M inverse) monthly backtest outputs. Core/Donchian base from the
independently reproduced BTCUSD 1m 70/30 portfolio. All returns include
their original modeled taker fee+GST+slippage, but not funding/spread and
this is only a synthetic MONTHLY blend, not integrated fills.

Important: weights chosen with 2025+2026 hindsight. Do not deploy live.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

OUT=Path("analysis/stage18_hindsight_22of22_standalone_components_20261121")
BASE=Path("/tmp/stage18-70-30/scenario_monthly_22.csv")
STAGE17=Path("analysis/institutional_discovery_stage17_swing_breakout/monthly_mark_to_market.csv")
STAGE19=Path("analysis/institutional_discovery_stage19_new_1h_patterns/monthly_results.csv")
STAGE20=Path("analysis/institutional_discovery_stage20_inverse_direction/monthly_results.csv")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
EPS=1e-8
# These are EXPOSURE weights, not profitable standalone weights; LP was fit on
# all months with knowledge of September/January losing outcomes.
WEIGHTS={
    "Core 4H/1H/15M max SL700":.49,
    "Donchian 55 daily max hold30":.21,
    "Daily20 EMA50 ATR4":.05658120333467704,
    "Daily20 unfiltered ATR4":.02077211258288107,
    "H4 Donchian55 EMA50 ATR3":.005464099405663537,
    "H1 compression expansion ADX efficiency30 2R":.06323491342526413,
    "H1 compression expansion ADX efficiency30 3R":.10,
    "H1 compression expansion unfiltered 3R":.0022889697917677617,
    "H1 EMA20 pullback efficiency30 3R":.017355853375169938,
    "M5 inverted compression ATR1.5 4R":.034302848084576544,
}
SOURCES=[
    ("Daily20 EMA50 ATR4","stage17","1D_channel_20_ema50_agrees_trail_4atr"),
    ("Daily20 unfiltered ATR4","stage17","1D_channel_20_no_trend_filter_trail_4atr"),
    ("H4 Donchian55 EMA50 ATR3","stage17","4H_channel_55_ema50_agrees_trail_3atr"),
    ("H1 compression expansion ADX efficiency30 2R","stage19","compression_expansion_12h__4h_efficiency_ge30__2R__240min"),
    ("H1 compression expansion ADX efficiency30 3R","stage19","compression_expansion_12h__4h_efficiency_ge30__3R__240min"),
    ("H1 compression expansion unfiltered 3R","stage19","compression_expansion_12h__all__3R__240min"),
    ("H1 EMA20 pullback efficiency30 3R","stage19","ema20_pullback_confirm__4h_efficiency_ge30__3R__240min"),
    ("M5 inverted compression ATR1.5 4R","stage20",dict(
        pattern="compression_break",direction_mode="original",
        entry_filter="large_atr",stop_mode="atr1p5",
        target_R=4.0,hold_min=120,risk_fraction_pct=.5,
        max_leverage=5.0,cost_mode="standard_taker"))
]

def aligned(frame,return_col,description):
    frame=frame[frame.month_ist.isin(MONTHS)]
    assert len(frame)==22, f"{description} has {len(frame)} rows expected 22"
    if frame.month_ist.duplicated().any(): raise AssertionError(f"Duplicate source months for {description}")
    s=frame.set_index("month_ist").reindex(MONTHS)[return_col]
    if s.isna().any() or not np.isfinite(s.to_numpy(float)).all():
        raise AssertionError(f"Invalid monthly source {description}")
    return s.to_numpy(float)

def get_stats(v):
    a=np.asarray(v,float)
    eq=np.cumprod(1+a/100)
    return dict(compounded_22_month_pct=float(100*(eq[-1]-1)),
      compounded_2025_pct=float(100*(np.prod(1+a[:12]/100)-1)),
      compounded_JanOct2026_pct=float(100*(np.prod(1+a[12:]/100)-1)),
      profitable_months=int((a>EPS).sum()),
      loss_months=int((a<-EPS).sum()),
      flat_months=int((abs(a)<=EPS).sum()),
      worst_month_pct=float(a.min()),
      jan2025_pct=float(a[0]),jan2026_pct=float(a[12]),
      september2026_pct=float(a[20]),october2026_pct=float(a[21]))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if not np.isclose(sum(WEIGHTS.values()),1,atol=1e-12):raise AssertionError("Weights must sum to 100%")
    base=pd.read_csv(BASE)
    base=base[(base.scenario=="stage18_70_30_30d")&(base.extra_bps_side==0)]
    core=aligned(base[["month_ist","core_month_pct"]].rename(columns={"core_month_pct":"value"}),"value","core")
    don=aligned(base[["month_ist","donchian_month_pct"]].rename(columns={"donchian_month_pct":"value"}),"value","donchian")
    original=aligned(base[["month_ist","portfolio_month_pct"]].rename(columns={"portfolio_month_pct":"value"}),"value","70/30")
    if not np.allclose(.7*core+.3*don,original,atol=1e-8):raise AssertionError("Base 70/30 NAV not reconciled")
    if not np.isclose(get_stats(original)["compounded_22_month_pct"],14.438074,atol=.001):
        raise AssertionError("Original base result different from verified 1m backtest")
    data={"Core 4H/1H/15M max SL700":core,
          "Donchian 55 daily max hold30":don}
    sw=pd.read_csv(STAGE17)
    h=pd.read_csv(STAGE19)
    # Stage20 is >30 MB. Load ONLY required columns from original actual
    # source, using chunked CSV to avoid high RAM usage in small VPS.
    fields=["pattern","direction_mode","entry_filter","stop_mode","target_R",
            "hold_min","risk_fraction_pct","max_leverage","cost_mode","month_ist",
            "account_return_pct","trades"]
    selected20=[]
    inverse_filter=SOURCES[-1][2]
    for chunk in pd.read_csv(STAGE20,chunksize=40000,usecols=fields):
        cond=np.ones(len(chunk),dtype=bool)
        for col,value in inverse_filter.items():
            if isinstance(value,(int,float)):
                cond&=np.isclose(chunk[col].to_numpy(float),float(value))
            else:
                cond&=(chunk[col].astype(str).to_numpy()==value)
        if cond.any():selected20.append(chunk[cond].copy())
    if not selected20:raise AssertionError("Requested 5m inverse model absent from Stage20 archive")
    invert=pd.concat(selected20,ignore_index=True)
    for label,source,lookup in SOURCES:
        if source=="stage17":
            z=sw[sw.model==lookup]
            data[label]=aligned(z,"month_return_pct",label)
        elif source=="stage19":
            z=h[h.model==lookup]
            data[label]=aligned(z,"modeled_return_pct",label)
        elif source=="stage20":
            data[label]=aligned(invert,"account_return_pct",label)
    assert len(data)==len(WEIGHTS)

    summary=[];rows=[]
    z=np.zeros(len(MONTHS),dtype=float)
    for label,w in WEIGHTS.items():
        x=data[label]
        z+=w*x
        details=dict(component=label,allocation_pct=100*w,
                 september2026_portfolio_contribution_pct=100*w*x[20]/100,
                 **get_stats(x))
        summary.append(details)
        print("STANDALONE_COMPONENT",json.dumps(details))
        for i,m in enumerate(MONTHS):
            rows.append(dict(component=label,allocation_pct=100*w,
                month_ist=m,standalone_return_pct=float(x[i]),
                weighted_contribution_percentage_points=float(w*x[i])))
    results=get_stats(z)
    if not ((results["profitable_months"],results["loss_months"],results["flat_months"])==(22,0,0) and
            abs(results["compounded_22_month_pct"]-9.400879329779954)<0.015):
        raise AssertionError(f"Reported 22/22 hindsight portfolio doesn't reconcile: {results}")
    pd.DataFrame(summary).to_csv(OUT/"component_standalone_results_22months.csv",index=False)
    pd.DataFrame(rows).to_csv(OUT/"component_monthly_contributions.csv",index=False)
    pd.DataFrame(dict(month_ist=MONTHS,portfolio_month_pct=z,
           sep=np.where(z>EPS,"Profit",np.where(z<-EPS,"Loss","Flat")),
           equity_index=100*np.cumprod(1+z/100))).to_csv(
               OUT/"verified_22of22_hindsight_monthly.csv",index=False)
    metadata=dict(result=results,source_files=[str(STAGE17),str(STAGE19),str(STAGE20)],
         source_5m_rows=len(invert),weighted_monthly_returns_sum_22=list(map(float,z)),
         no_live_trading=True,
         selection="INVALID 2025-2026 full hindsight LP",
         cost="Sources include original modeled taker/GST/5 BTC pts slip per side, not extra costs",
         caveats=[
             "Numerous sleeve strategies individually lost money over 22 months",
             "This 22/22 blend is a hindsight fit; 2026 was inspected and used for allocations",
             "Small worst month gain disappears under extra modeled cost sensitivity",
             "Portfolio contributions are weighted monthly returns, not compounded attribution",
             "Synthetically rebalanced capital; not integrated shared-margin per-trade simulation",
             "No funding/actual spread/liquidation/lot-size model; no real-world 22/22 proof",
         ])
    (OUT/"audit.json").write_text(json.dumps(metadata,indent=2)+"\n")
    print("COMPONENT_STANDALONE_AUDIT_SUCCESS",json.dumps(dict(
        components=len(summary),summary=results,output=str(OUT))))
if __name__=="__main__":main()
