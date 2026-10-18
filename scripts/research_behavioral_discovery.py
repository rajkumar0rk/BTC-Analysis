#!/usr/bin/env python3
"""Reproducible historical discovery: BTC volatility regimes, not indicator folklore.
Causal hourly signals after fully closed futures/mark/OI/funding bars.
Train 2025, validation Jan-Jun 2026; July-Oct chronological recheck.
The later period was previously researched and is NOT globally untouched.
Hourly samples nonoverlapping for the next-hour volatility target.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

BASE=Path("data/delta_india/BTCUSD")
OUT=Path("analysis/institutional_discovery_stage2")
CUT1=pd.Timestamp("2026-01-01",tz="UTC")
CUT2=pd.Timestamp("2026-07-01",tz="UTC")
FEE=0.0005*1.18
SLIP=5.

def load(folder):
    files=sorted(folder.glob("20??-??.csv.gz"))
    if not files:raise ValueError(f"No data in {folder}")
    batches=[]
    for p in files:
        a=pd.read_csv(p,compression="gzip",usecols=["time","open","high","low","close","volume"])
        a["time"]=pd.to_datetime(a.time.astype("int64"),unit="s",utc=True)
        batches.append(a.set_index("time"))
    x=pd.concat(batches).sort_index()
    if x.index.has_duplicates or x[["open","high","low","close"]].isna().any().any():
        raise ValueError("Invalid OHLCV")
    return x

def features():
    f=load(BASE/"1m")
    m=load(BASE/"institutional/history/mark_1m")
    oi=load(BASE/"institutional/history/open_interest_5m")
    funding=load(BASE/"institutional/history/funding_1h")
    if not f.index.equals(m.index):raise ValueError("MARK mismatched")
    h=f.resample("1h").agg(dict(open="first",high="max",low="min",close="last",volume="sum"))
    assert f.close.resample("1h").count().eq(60).all()
    h["mark"]=m.close.resample("1h").last()
    h["oi"]=oi.close.resample("1h").last()
    # Rate stamped H is assumed only known after the corresponding hour;
    # shift one completed hourly period to be conservative about release.
    h["funding"]=funding.close.shift(1).reindex(h.index)
    h["range"]=h.high-h.low
    h["typical"]=h["range"].rolling(48,min_periods=48).median().shift(1)
    h["vol_ave"]=h.volume.rolling(48,min_periods=48).mean().shift(1)
    h["range_ratio"]=h["range"]/h.typical.replace(0,np.nan)
    h["volume_ratio"]=h.volume/h.vol_ave.replace(0,np.nan)
    h["oi_change_pct"]=100*h.oi.pct_change(fill_method=None)
    h["oi_z"]=(h.oi_change_pct-h.oi_change_pct.rolling(168,min_periods=96).mean().shift(1))/h.oi_change_pct.rolling(168,min_periods=96).std().shift(1).replace(0,np.nan)
    h["basis_bp"]=1e4*(h.close-h.mark)/h.mark.replace(0,np.nan)
    h["basis_z"]=(h.basis_bp-h.basis_bp.rolling(168,min_periods=96).mean().shift(1))/h.basis_bp.rolling(168,min_periods=96).std().shift(1).replace(0,np.nan)
    h["return_pct"]=100*(h.close-h.open)/h.open
    h["trend_prev_4h"]=h.close-h.close.shift(4)
    h["hi12"]=h.high.rolling(12,min_periods=12).max().shift(1)
    h["lo12"]=h.low.rolling(12,min_periods=12).min().shift(1)
    # Every outcome begins at the NEXT hourly OPEN after the completed bar.
    h["future_open"]=h.open.shift(-1)
    h["future_high"]=h.high.shift(-1)
    h["future_low"]=h.low.shift(-1)
    h["future_close"]=h.close.shift(-1)
    h["future_range"]=h.future_high-h.future_low
    h["future_abs_net"]=abs(h.future_close-h.future_open)
    h["future_range_500"]=(h.future_range>=500).astype(float)
    h["future_range_200"]=(h.future_range>=200).astype(float)
    h["future_range_1000"]=(h.future_range>=1000).astype(float)
    h["future_vol_expansion"]=(h.future_range>=1.5*h.typical).astype(float)
    h["future_vol_normalized"]=h.future_range/h.typical.replace(0,np.nan)
    ny=h.index.tz_convert("America/New_York")
    h["ny_start_hour"]=ny.hour.astype(int)
    h["ny_next_hour"]=((ny.hour+1)%24).astype(int)
    h["ny_weekday"]=ny.dayofweek.astype(int)
    h["ny_date"]=[str(x) for x in ny.date]
    h["period"]=np.where(h.index<CUT1,"train",np.where(h.index<CUT2,"validation","holdout"))
    h=h.iloc[180:-1].dropna(subset=["future_range","typical","oi_z","basis_z","volume_ratio","funding"])
    quality=dict(futures_1m=len(f),mark_1m=len(m),OI_5m=len(oi),
        funding_1h=len(funding),available_hourly_events=len(h),
        first=str(h.index.min()),last=str(h.index.max()),
        oi_changes_pct_p01_p50_p99=np.percentile(h.oi_change_pct,[1,50,99]).round(3).tolist(),
        hourly_range_points_p01_p50_p99=np.percentile(h["range"],[1,50,99]).round(2).tolist(),
        funding_distinct_values=int(funding.close.nunique()),
        funding_fraction_exact_point01=round(float((funding.close==.01).mean()),4))
    return f,h,quality

def masks(h):
    # Thresholds chosen before inspecting 2026 results. Prefer comparable
    # normalized measures to arbitrary BTC point thresholds.
    v=h.volume_ratio; r=h.range_ratio; o=h.oi_z; b=h.basis_z
    direction=np.sign(h.return_pct)
    return {
        "after_hourly_range_expansion_1p5":r>=1.5,
        "after_hourly_range_expansion_2x":r>=2,
        "after_hourly_compression_0p7":r<=.7,
        "after_hourly_compression_0p5":r<=.5,
        "after_large_volume_1p5":v>=1.5,
        "after_large_volume_2x":v>=2,
        "after_range_expansion_and_volume":(r>=1.5)&(v>=1.5),
        "after_compression_and_high_volume":(r<=.7)&(v>=1.5),
        "after_low_volume_compression":(r<=.7)&(v<=.8),
        "after_OI_rise_z1p5":o>=1.5,
        "after_OI_fall_zm1p5":o<=-1.5,
        "after_OI_change_abs_z2":abs(o)>=2,
        "after_OI_rise_and_range_expand":(o>=1.5)&(r>=1.5),
        "after_OI_fall_and_range_expand":(o<=-1.5)&(r>=1.5),
        "after_price_up_and_OI_rise":(direction>0)&(o>=1.5),
        "after_price_down_and_OI_rise":(direction<0)&(o>=1.5),
        "after_price_up_and_OI_fall":(direction>0)&(o<=-1.5),
        "after_price_down_and_OI_fall":(direction<0)&(o<=-1.5),
        "after_stretched_basis_abs_z2":abs(b)>=2,
        "after_high_basis_z2":b>=2,
        "after_low_basis_zm2":b<=-2,
        "after_basis_extreme_and_OI_add":(abs(b)>=1.5)&(o>=1.0),
        "after_breakout_12h_high":h.close>h.hi12,
        "after_breakdown_12h_low":h.close<h.lo12,
        "after_upper_sweep_12h":(h.high>h.hi12)&(h.close<h.hi12),
        "after_lower_sweep_12h":(h.low<h.lo12)&(h.close>h.lo12),
        "after_breakout_and_OI_add":(h.close>h.hi12)&(o>=1),
        "after_breakdown_and_OI_add":(h.close<h.lo12)&(o>=1),
        "after_4hour_strong_up":(h.trend_prev_4h>=1.5*h.typical),
        "after_4hour_strong_down":(h.trend_prev_4h<=-1.5*h.typical),
        "after_big_up_hour":(h.return_pct>0)&(r>=1.5),
        "after_big_down_hour":(h.return_pct<0)&(r>=1.5),
        "before_us_regular_0930_context":(h.ny_next_hour==10)&(h.ny_weekday<5),
        "start_ny_1800_context":(h.ny_next_hour==18)&(h.ny_weekday==6),
    }

def slices(h):
    rules=masks(h)
    rec=[]
    # Matching comparison against the local hour of day AND weekend/weekday.
    h=h.copy()
    h["clock_class"]=(h.ny_next_hour*2+(h.ny_weekday>=5).astype(int)).astype(int)
    metrics={
       "p200":"future_range_200",
       "p500":"future_range_500",
       "p1000":"future_range_1000",
       "p_regime_expand":"future_vol_expansion",
       "normalized_range":"future_vol_normalized"}
    for name,condition in rules.items():
        condition=condition.fillna(False)
        for period,period_df in h.groupby("period"):
            a=period_df.loc[condition.reindex(period_df.index).fillna(False)]
            if len(a)<1:continue
            for outcol,column in metrics.items():
                baseline=period_df.groupby("clock_class")[column].mean()
                matched=float(a.clock_class.map(baseline).mean())
                obs=float(a[column].mean())
                rec.append(dict(rule=name,period=period,metric=outcol,
                  n=len(a),days=a.ny_date.nunique(),
                  observed=round(obs,5),matched=round(matched,5),
                  uplift=round(obs-matched,5),ratio=round(obs/matched,4) if matched else np.nan))
    return pd.DataFrame(rec)

def candidate_selection(stats):
    keys=["rule","metric"]
    r=stats.pivot(index=keys,columns="period",values=["n","days","observed","matched","uplift","ratio"])
    r.columns=[f"{a}_{b}" for a,b in r.columns]
    r=r.reset_index()
    for col in ["n_train","n_validation","n_holdout","uplift_train","uplift_validation"]:
        if col not in r:r[col]=np.nan
    feasible=r[(r.n_train>=100)&(r.n_validation>=50)&(r.n_holdout>=20)].copy()
    # Only first two periods used for ranks; focus on range probability and
    # relative range to avoid selecting solely based on market price level.
    feasible["rank_score"]=np.minimum(feasible.uplift_train,feasible.uplift_validation)
    feasible["positive_early"]=(feasible.uplift_train>0)&(feasible.uplift_validation>0)
    eligible=feasible[feasible.metric.isin(["p500","p_regime_expand","normalized_range"])]
    ranked=eligible.sort_values("rank_score",ascending=False)
    return feasible,ranked

def block_ci(h,condition,col,seed=11,nboot=650):
    # Calendar-day bootstrap on conditional-vs-clock-matched uplift.
    # Validate within each chronological period independently.
    a=h.loc[condition]
    if len(a)<20:return None
    base=h.groupby("clock_class")[col].mean()
    x=(a[col]-a.clock_class.map(base)).groupby(a.ny_date).agg(["sum","count"])
    if len(x)<10:return None
    pairs=x[["sum","count"]].to_numpy(float)
    rng=np.random.default_rng(seed)
    s=rng.integers(len(pairs),size=(nboot,len(pairs)))
    val=pairs[s].sum(axis=1)
    uplift=val[:,0]/val[:,1]
    return tuple(np.quantile(uplift,[.025,.5,.975]).round(5))

def daily_trade_replay(fut,h,rules):
    # Non-overlap: one trade per day per rule, first signal only.
    # Strict directional test of next hour continuation / fade; measure actual
    # net expectancy. Do not report raw range as achievable entry profit.
    op=fut.open.to_numpy(float);hi=fut.high.to_numpy(float)
    lo=fut.low.to_numpy(float);close=fut.close.to_numpy(float)
    index=fut.index
    results=[]
    # Strategy hypotheses are fixed before the holdout is checked.
    for rule in rules:
        mask=masks(h)[rule].fillna(False)
        hh=h.loc[mask]
        hh=hh[~hh.ny_date.duplicated(keep="first")]
        for t,z in hh.iterrows():
            when=t+pd.Timedelta(hours=1)
            k=int(index.searchsorted(when))
            if k+60>=len(index) or index[k]!=when:continue
            # Direction only from completed, previous hour.
            direction=np.sign(z.close-z.open)
            if direction==0:continue
            for mode,side in [("follow",int(direction)),("fade",-int(direction))]:
                price=float(op[k]);openfill=price+side*SLIP
                for tp,stop in [(300,250),(500,350),(800,500)]:
                    stop_level=price-side*stop
                    tp_level=price+side*tp
                    arrhi=hi[k:k+60];arrlo=lo[k:k+60]
                    stop_hits=(arrlo<=stop_level) if side>0 else (arrhi>=stop_level)
                    tp_hits=(arrhi>=tp_level) if side>0 else (arrlo<=tp_level)
                    b=np.flatnonzero(stop_hits)
                    a=np.flatnonzero(tp_hits)
                    sb=int(b[0]) if len(b) else 60
                    sa=int(a[0]) if len(a) else 60
                    if sb<=sa and sb<60:exitprice=stop_level;kind="stop"
                    elif sa<60:exitprice=tp_level;kind="target"
                    else:exitprice=close[k+59];kind="timeout"
                    fill=exitprice-side*SLIP
                    profit=side*(fill-openfill)-FEE*(openfill+fill)
                    results.append(dict(rule=rule,period=z.period,date=z.ny_date,
                      entry_utc=str(when),mode=mode,target=tp,stop=stop,
                      reason=kind,net_pts=round(profit,3)))
    if not results:return pd.DataFrame(),pd.DataFrame()
    tr=pd.DataFrame(results)
    agg=tr.groupby(["rule","mode","target","stop","period"]).net_pts.agg(
        trades="count",mean_net="mean",win_rate=lambda z:(z>0).mean()).reset_index()
    agg["mean_net"]=agg.mean_net.round(2)
    agg["win_pct"]=(agg.win_rate*100).round(2)
    return tr,agg.drop(columns=["win_rate"])

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    fut,h,quality=features()
    stats=slices(h)
    feasible,ranked=candidate_selection(stats)
    # Select a brief list of distinct regimes by better of preliminary 2
    # windows; HOLDOUT not used. Do not find rule using holdout then claim test.
    s=ranked[ranked.positive_early]
    choices=s.drop_duplicates("rule").head(8).rule.tolist()
    if len(choices)<6:
        choices=list(dict.fromkeys(choices+ranked.rule.tolist()))[:8]
    contrasts=[]
    for rule in choices:
        mask=masks(h)[rule].fillna(False)
        for period in ("train","validation","holdout"):
            frame=h[h.period==period].copy()
            frame["clock_class"]=(frame.ny_next_hour*2+(frame.ny_weekday>=5).astype(int)).astype(int)
            choose=mask.reindex(frame.index).fillna(False)
            for col in ("future_range_500","future_vol_expansion","future_vol_normalized"):
                ci=block_ci(frame,choose,col)
                if ci:
                    contrasts.append(dict(rule=rule,period=period,metric=col,
                         n=int(choose.sum()),days=frame.loc[choose].ny_date.nunique(),
                         uplift_lower=ci[0],uplift_median=ci[1],uplift_upper=ci[2]))
    contrast=pd.DataFrame(contrasts)
    tr,trade_stats=daily_trade_replay(fut,h,choices)
    stats.to_csv(OUT/"all_conditional_findings.csv",index=False)
    ranked.to_csv(OUT/"ranked_early_periods.csv",index=False)
    feasible.to_csv(OUT/"all_eligible_features.csv",index=False)
    contrast.to_csv(OUT/"day_block_intervals.csv",index=False)
    if len(tr):tr.to_csv(OUT/"directional_trade_ledger.csv",index=False)
    if len(trade_stats):trade_stats.to_csv(OUT/"directional_trade_results.csv",index=False)
    h[["close","mark","oi","funding","range_ratio","volume_ratio","oi_z","basis_z",
       "future_range","future_range_500","future_vol_expansion","period"]].iloc[::6].to_csv(
           OUT/"six_hourly_feature_samples.csv")
    quality.update(total_predeclared_conditions=len(masks(h)),
        eligible_metric_tests=len(feasible),candidate_regimes=choices,
        notes=["Hourly next-period outcomes do not overlap",
          "Clock-matched means by NY next-hour and weekend/weekday",
          "The chronological holdout was previously seen by other studies; independent new forward data remains needed",
          "These are price-point ranges, NOT executable trade profits",
          "Gross future high-low is NOT a profitable tradable strategy"])
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    print("DISCOVERY_COMPLETED",json.dumps(quality))
    columns=["rule","metric","n_train","observed_train","matched_train",
             "uplift_train","n_validation","uplift_validation",
             "n_holdout","uplift_holdout","rank_score"]
    selected=ranked[ranked.rule.isin(choices)]
    if len(selected):print(selected[columns].head(30).to_string(index=False))
    if len(contrast):print("DAY_BLOCK_CI",contrast.to_string(index=False))
    lines=[
      "# Finding actual BTC futures market behavior: non-directional predictive regimes",
      "",
      "## Research question",
      "Before trying BUY/SELL rules, can market-structure, participation, open interest, basis, funding, and time context forecast the NEXT hour's price movement RANGE? A future hourly HIGH-LOW is a volatility observation, not an executable trading profit.",
      "",
      "All 1-hour samples are nonoverlapping, and all features use completed current/prior hourly candles. 2025=training; Jan-Jun 2026=validation; July-Oct 2026=chronological recheck (NOT globally untouched after earlier analyses).",
      "The baseline controls for next-hour New York clock hour and weekday/weekend, so trivial clock effects are reduced. Regime signal rates are measured against matched baseline rates within each chronological period.",
      "",
      "## Source/quality",
      "~~~json",json.dumps(quality,indent=2),"~~~",
      "",
      "## Selected preliminary regimes and chronological rechecks",
      "Selection uses only 2025 and Jan-Jun 2026; holdout is not used for ranking.",
      selected[columns].head(30).to_markdown(index=False) if len(selected) else "None selected.",
      "",
      "## Calendar-day bootstrap confidence intervals (exploratory)",
      "Lower > 0 in multiple periods indicates consistent evidence for a volatility-regime uplift, NOT guaranteed returns. These are NOT multiplicity-adjusted.",
      contrast.to_markdown(index=False) if len(contrast) else "No intervals computed.",
      "",
      "## Execution realism",
      "Optional directional follow/fade simulation uses next hourly OPEN, next 60 individual minutes with stop-first ambiguous fills, taker fee each side 0.05% plus 18% GST, and 5 BTC-point adverse slippage per side.",
      "One trade per NY day per rule, restricted to days with condition; +300/-250, +500/-350, +800/-500, one-hour timeout.",
      "Directional simulated results are separate from non-directional range findings. Do not conflate forecastable volatility with forecastable direction.",
      (trade_stats.to_markdown(index=False) if len(trade_stats) else "No directional trades."),
      "",
      "## Limitations",
      "- OHLCV/OI/funding/mark do not identify trading firms or record historical liquidation and full depth.",
      "- Percentile uncertainty is a within-period calendar-day bootstrap, without multiple-testing correction.",
      "- Prior analyses used some of the same final dates; future live data is the only genuinely fresh test.",
      "- Price-index regime thresholds are normalized to trailing range; fixed $500 threshold is also shown but is regime dependent.",
      "- Fees, funding charges, actual quotes and market impact might further worsen directional P&L.",
      "",
      "## Saved research files",
      "all_conditional_findings.csv, ranked_early_periods.csv, day_block_intervals.csv, directional_trade_ledger.csv, directional_trade_results.csv, six_hourly_feature_samples.csv."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
if __name__=="__main__":main()
