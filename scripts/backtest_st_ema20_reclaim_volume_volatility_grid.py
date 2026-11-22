#!/usr/bin/env python3
"""Causal volume and volatility gates on existing independent EMA20 RECLAIM trade ledgers."""
import importlib.util
import itertools
import json
from pathlib import Path
import numpy as np
import pandas as pd

PREV=Path("scripts/backtest_st_ema20_large_percent_locks.py")
BASE=Path("analysis/st_ema20_large_percent_locks_1h")
OUT=Path("analysis/st_ema20_reclaim_volume_volatility_grid_1h")
PATHS=("open_high_low_close","open_low_high_close")
LADDERS={
 "0.14%":"S01_only_0p14",
 "0.50%":"S02_only_0p50",
 "0.75%":"S03_only_0p75",
 "1.00%":"S04_only_1",
 "2.00%":"S06_only_2",
 "5.00%":"S09_only_5",
 "1-2-5%":"L05_1_2_5",
 "2-3-5%":"L10_2_3_5",
}
VOL_MIN=(0.,.5,.75,1.,1.25,1.5,2.)
VOL_MAX=(np.inf,2.5)
ATR_MIN=(0.,.35,.5,.75,1.,1.25)
ATR_MAX=(np.inf,1.25,1.75,2.5)
EXP_MIN=(0.,.9,1.1,1.3)
MONTHS=list(pd.period_range("2025-01","2026-10",freq="M").astype(str))


def engine():
    spec=importlib.util.spec_from_file_location("btc_original",PREV)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def enrich_h(h):
    h=h.copy()
    # Current signal hour volume is known at signal bar close; denominator only
    # considers the PREVIOUS 20 COMPLETE hours.
    h["vol_ratio"]=h.volume / h.volume.shift(1).rolling(20,min_periods=20).mean().replace(0,np.nan)
    h["atr_pct"]=100*h.atr/h.close
    h["atr_expand"]=h.atr/h.atr.shift(1).rolling(20,min_periods=20).mean().replace(0,np.nan)
    return h


def load_trades(h):
    comparison=pd.read_csv(BASE/"comparison.csv")
    alltrades={}
    for label,ladder in LADDERS.items():
        for path in PATHS:
            name=f"reclaim_{ladder}_{path}"
            t=pd.read_csv(BASE/f"{name}_trades.csv")
            t["signal_ts"]=pd.to_datetime(t.signal_utc,utc=True)
            t["entry_ts"]=pd.to_datetime(t.entry_utc,utc=True)
            t["exit_ts"]=pd.to_datetime(t.exit_utc,utc=True)
            assert t.entry_ts.ge(t.signal_ts+pd.Timedelta(hours=1)).all()
            assert t.entry_ts.is_unique and t.exit_ts.ge(t.entry_ts).all()
            hh=h.reindex(pd.DatetimeIndex(t.signal_ts))
            features=hh[["vol_ratio","atr_pct","atr_expand"]].to_numpy(float)
            # Relative volume may legitimately be zero on a low-activity signal candle.
            # Other malformed values are invalid for ACTIVE filters only; an OFF
            # filter must preserve the exact, unfiltered baseline trade ledger.
            # Initial January 2025 signal may predate the 20 *valid ATR* warmup.
            # It remains in unfiltered baseline and is rejected only when
            # a filter using that missing feature is enabled.
            ref=comparison.loc[(comparison.entry_mode=="reclaim")&
                 (comparison.ladder==ladder)&(comparison.intraminute_path==path)]
            assert len(ref)==1 and abs(float(ref.net_usd.iloc[0])-t.net_usd.sum())<0.002
            t["net"]=t.net_usd.astype(float)
            t["month"]=(t.exit_ts+pd.Timedelta(hours=5,minutes=30)).dt.tz_localize(None).dt.to_period("M").astype(str)
            alltrades[(label,path)]={"ledger":t,"vol":features[:,0],"atr":features[:,1],"exp":features[:,2]}
    return alltrades


def cat(config):
    vmin,vmax,amin,amax,emin=config
    vol=(vmin>0 or np.isfinite(vmax))
    atr=(amin>0 or np.isfinite(amax) or emin>0)
    return ("both" if vol and atr else "volume" if vol else "volatility" if atr else "unfiltered")


def metric(label,path,record,config):
    vmin,vmax,amin,amax,emin=config
    vol_filter = np.ones(len(record["vol"]),dtype=bool) if (vmin==0 and np.isinf(vmax)) else (
        np.isfinite(record["vol"]) & (record["vol"]>=vmin) & (record["vol"]<=vmax))
    atr_filter = np.ones(len(record["atr"]),dtype=bool) if (amin==0 and np.isinf(amax)) else (
        np.isfinite(record["atr"]) & (record["atr"]>=amin) & (record["atr"]<=amax))
    exp_filter = np.ones(len(record["exp"]),dtype=bool) if emin==0 else (
        np.isfinite(record["exp"]) & (record["exp"]>=emin))
    mask=vol_filter & atr_filter & exp_filter
    t=record["ledger"].loc[mask].copy()
    t=t.sort_values("exit_ts")
    a=t.net.to_numpy(float)
    n=len(a)
    equity=100+np.cumsum(a)
    if n:
        peak=np.maximum.accumulate(np.r_[100.,equity])[1:]
        dd=float(np.max((peak-equity)/np.maximum(peak,1e-8))*100)
    else:dd=0.
    mm=t.groupby("month")["net"].sum().to_dict()
    complete={k:float(mm.get(k,0.)) for k in MONTHS}
    out={
       "ladder":label,"path":path,"category":cat(config),
       "vmin":vmin,"vmax":vmax,"amin":amin,"amax":amax,"emin":emin,
       "trades":n,"wins":int((a>0).sum()),"losses":int((a<0).sum()),
       "win_pct":round(100*float((a>0).mean()),3) if n else 0.,
       "net":round(float(a.sum()),4),
       "net2025":round(sum(x for k,x in complete.items() if k.startswith("2025")),4),
       "net2026":round(sum(x for k,x in complete.items() if k.startswith("2026")),4),
       "months_pos":sum(x>1e-8 for x in complete.values()),
       "max_realized_dd_pct":round(dd,3),
       "fee_total":round(float(t.fees_usd.sum()),4),
       "locks":int((t.exit_reason=="profit_lock").sum()),
       "flips":int((t.exit_reason=="supertrend_flip").sum()),
       "n2025":int(t.month.str.startswith("2025").sum()),
       "n2026":int(t.month.str.startswith("2026").sum()),
    }
    return out


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    e=engine()
    mins,h,file_count=e.load()
    h=enrich_h(e.features(h))
    del mins
    records=load_trades(h)
    grids=[]
    for vmin,vmax,amin,amax,emin in itertools.product(VOL_MIN,VOL_MAX,ATR_MIN,ATR_MAX,EXP_MIN):
        if vmin<=vmax and amin<=amax:
            grids.append((vmin,vmax,amin,amax,emin))
    print(f"Read {file_count} months and validated {len(records)} independent trade ledgers; {len(grids)} filter grids",flush=True)
    rows=[]
    for i,c in enumerate(grids):
        for (label,path),data in records.items():
            rows.append(metric(label,path,data,c))
        if (i+1)%200==0:print(f"Finished {i+1}/{len(grids)} causal gate settings",flush=True)
    r=pd.DataFrame(rows)
    r.to_csv(OUT/"all_scenarios.csv",index=False)
    key=["ladder","category","vmin","vmax","amin","amax","emin"]
    g=r.groupby(key,dropna=False)
    pairs=g.agg(
        trades_min=("trades","min"),
        net_worst=("net","min"),net_best=("net","max"),
        year2025_worst=("net2025","min"),
        year2026_worst=("net2026","min"),
        months_min=("months_pos","min"),
        winrate_min=("win_pct","min"),
        dd_worst=("max_realized_dd_pct","max"),
        year2025_mintrades=("n2025","min"),
        year2026_mintrades=("n2026","min")
    ).reset_index()
    assert len(pairs)*2==len(r),"Missing one intraminute path"
    pairs["eligible"]=(pairs.trades_min>=35)&(pairs.year2025_mintrades>=12)&(pairs.year2026_mintrades>=12)
    pairs["both_paths_positive"]=pairs.net_worst>0
    pairs["both_years_positive"]=(pairs.year2025_worst>0)&(pairs.year2026_worst>0)
    pairs=pairs.sort_values(["eligible","net_worst","months_min"],ascending=[False,False,False])
    pairs.to_csv(OUT/"paired_comparison.csv",index=False)
    pairs.loc[pairs.eligible].groupby("ladder",sort=False,group_keys=False).head(10).to_csv(OUT/"top_by_ladder.csv",index=False)
    top=pairs.loc[pairs.eligible&(pairs.category=="both")]
    top.head(50).to_csv(OUT/"top_combined_filters.csv",index=False)
    baseline=r.loc[r.category=="unfiltered"]
    assert len(baseline)==len(records),"Baseline setup differs from prior history"
    baseline.to_csv(OUT/"baseline.csv",index=False)

    # Preselected transfer test from PRIOR Touch research: same volume/ATR
    # thresholds, now on Reclaim entries and same 2→3→5% profit locks.
    transferred_config=(0.0,2.5,0.0,1.25,0.0)
    transferred_rows=[metric("2-3-5%",p,records[("2-3-5%",p)],transferred_config) for p in PATHS]
    pd.DataFrame(transferred_rows).to_csv(OUT/"transferred_touch_balanced.csv",index=False)

    # Export full month P&L for the unfiltered versus transferred settings.
    mon=[]
    for path in PATHS:
        data=records[("2-3-5%",path)]
        t=data["ledger"]
        features_ok=(np.isfinite(data["vol"]) & (data["vol"]<=2.5) &
                     np.isfinite(data["atr"]) & (data["atr"]<=1.25))
        for name,mask in (("unfiltered",np.ones(len(t),dtype=bool)),
                          ("touch_balanced_transfer",features_ok)):
            subset=t.loc[mask]
            bymonth=subset.groupby("month").net.sum().to_dict()
            bycounts=subset.groupby("month").size().to_dict()
            for month in MONTHS:
                mon.append(dict(path=path,configuration=name,month=month,
                                trades=int(bycounts.get(month,0)),
                                net_usd=round(float(bymonth.get(month,0)),5)))
    pd.DataFrame(mon).to_csv(OUT/"2_3_5_monthly_before_after_transfer.csv",index=False)

    assert (baseline.trades.max()==227), "Baseline candidate count drift"
    winners=top.loc[top.both_paths_positive]
    consistent=winners.loc[winners.both_years_positive]
    best=top.iloc[0] if len(top) else None

    if best is not None:
        c=(best.vmin,best.vmax,best.amin,best.amax,best.emin)
        for path in PATHS:
            data=records[(best.ladder,path)]
            t=data["ledger"].copy()
            t["signal_volume_ratio"]=data["vol"]
            t["signal_atr_pct"]=data["atr"]
            t["signal_atr_expansion"]=data["exp"]
            t["accepted"]=(t.signal_volume_ratio.ge(c[0])&t.signal_volume_ratio.le(c[1])&
                           t.signal_atr_pct.ge(c[2])&t.signal_atr_pct.le(c[3])&
                           t.signal_atr_expansion.ge(c[4]))
            t.to_csv(OUT/f"top_{path}_trade_audit.csv",index=False)

    features=records[("0.75%",PATHS[0])]
    quantiles={col:{str(q):round(float(np.nanquantile(np.where(np.isfinite(features[col]),features[col],np.nan),q)),4)
                    for q in (0,.1,.25,.5,.75,.9,1)}
               for col in ("vol","atr","exp")}
    doc={
       "status":"complete",
       "historical_source_files":file_count,
       "source_first_utc":str(h.index[0]),"source_last_hour_utc":str(h.index[-1]),
       "signal_features":"Completed 1H signal bar volume / previous 20h volume; ATR10 percent of close; ATR10 / previous 20h ATR10",
       "signal_warmup_excludes_current_bar_from_rolling_denominators":True,
       "entry_selection":"Retain original first-filled signal; if volume/volatility filter rejects it, skip rest of same ST cycle",
       "filter_configurations":len(grids),"exit_ladders":list(LADDERS),"two_intraminute_paths":list(PATHS),
       "total_scenarios":len(rows),"paired_scenarios":len(pairs),
       "combined_eligible_count":len(top),
       "both_paths_positive_count":len(winners),
       "both_paths_and_years_positive_count":len(consistent),
       "best_combined_filter":({k:(None if pd.isna(v) else float(v) if isinstance(v,np.floating) else int(v) if isinstance(v,np.integer) else bool(v) if isinstance(v,np.bool_) else v)
                               for k,v in best.to_dict().items()} if best is not None else None),
       "feature_quantiles":quantiles,
       "missing_signal_feature_counts":{col:int((~np.isfinite(features[col])).sum()) for col in ("vol","atr","exp")},
       "transfer_config_volume_max":2.5,"transfer_config_atr_max_pct":1.25,
       "transfer_reclaim_exit_ladder":"2-3-5%",
       "exclusions":["Not a fresh holdout; user previously evaluated both 2025 and 2026","No funding, margin, liquidation, ticks, stop amendment latency","Realized-exit max DD only; excludes floating drawdown","Precomputed stop trade ledgers assume one of two hypothetical minute OHLC paths"]
    }
    (OUT/"quality.json").write_text(json.dumps(doc,indent=2)+"\n")
    report=[
        "# BTCUSD EMA20 Reclaim: 1H volume and volatility filters",
        f"Archive 2025-01 through 2026-11-20; {len(grids)} signal filters × 8 exit configurations × 2 price paths = {len(rows)} scenarios.",
        "",
        "## Unfiltered reference",
        baseline[["ladder","path","trades","net","win_pct","months_pos"]].to_string(index=False),
        "",
        "## Preselected Touch filter transferred to Reclaim 2-3-5%",
        pd.DataFrame(transferred_rows)[["path","trades","wins","win_pct","net","months_pos","net2025","net2026","max_realized_dd_pct"]].to_string(index=False),
        "",
        "## Best eligible combined filters, ranking by WORST intraminute-path PnL",
        top[["ladder","vmin","vmax","amin","amax","emin","trades_min","net_worst","net_best","year2025_worst","year2026_worst","months_min"]].head(30).to_string(index=False),
        "",
        f"Eligible volume+volatility pairs: {len(top)}; net positive in both paths: {len(winners)}; positive in both paths and both years: {len(consistent)}.",
        "",
        "WARNING: large sweep of historical thresholds, severe selection bias. No untouched out-of-sample test. No live trading claim.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print(json.dumps({"configurations":len(grids),"scenarios":len(rows),"eligible_both_filters":len(top),
        "positive_both_paths":len(winners),"positive_both_paths_years":len(consistent),
        "best10":top.head(10).replace([np.inf,-np.inf],[9999,-9999]).to_dict("records")},indent=2),flush=True)


if __name__=="__main__":
    main()
