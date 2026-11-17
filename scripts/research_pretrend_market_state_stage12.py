#!/usr/bin/env python3
"""Stage 12: search BTCUSD pre-move states rather than repeating entry shapes.

Existing Stage 11 5m structure signals are FROZEN; this isolates whether
prior completed 1h/4h trend, volatility transition and participation increase
directional expectancy. Entry is the subsequent 1m OPEN. Structural stops
and 2R/3R rewards are unchanged; same-bar stop wins ambiguity.

All historical 2026 periods have already been researched. Results are
exploratory chronology checks, NOT independent forward validation.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive, periods, PERIOD_NAMES, FEE, SLIPPAGE
from research_structure_rr_stage11 import candidates, replay_one

OUT = Path("analysis/institutional_discovery_stage12_pretrend")
FILTERS = (
    "all_eligible",
    "4h_slope_agrees",
    "1h_4h_slope_agrees",
    "4h_trend_1h_pullback",
    "dual_trend_plus_5m_activity",
    "1h_regime_expansion",
    "1h_quiet_then_5m_expansion",
    "1h_directional_high_volume",
    "1h_break_6bar_channel",
    "4h_break_6bar_channel",
    "aligned_trend_plus_5m_compression_break",
    "1h_trend_5m_vol_acceleration",
)
R_VALUES=(2.,3.)
HOLDS=(120,240)
MIN_RISK=150.0
MAX_RISK=1200.0


def mtf_frame(f,tf,count):
    """Right-edge label: candle available only after every source minute closed."""
    a = f[["open","high","low","close","volume"]].resample(
        tf,label="right",closed="left").agg({
            "open":"first","high":"max","low":"min",
            "close":"last","volume":"sum"})
    a["count"]=f.close.resample(tf,label="right",closed="left").count()
    # Require many consecutive fully completed higher-timeframe candles to
    # exclude stale values when the underlying UTC day is missing.
    a["valid"]=a["count"].rolling(16,min_periods=16).min().eq(count)
    a["span"]=a.high-a.low
    a["median_range"]=a.span.shift(1).rolling(12,min_periods=12).median()
    a["mean_volume"]=a.volume.shift(1).rolling(12,min_periods=12).mean()
    a["range_ratio"]=a.span/a.median_range.replace(0,np.nan)
    a["volume_ratio"]=a.volume/a.mean_volume.replace(0,np.nan)
    a["slope"]=a.close.diff(3)/a.median_range.replace(0,np.nan)
    a["last_return"]=a.close.diff(1)/a.median_range.replace(0,np.nan)
    a["prior_3_range"]=(a.span.shift(1)+a.span.shift(2)+a.span.shift(3))/(
        3*a.median_range.replace(0,np.nan))
    a["high_6"]=a.high.shift(1).rolling(6,min_periods=6).max()
    a["low_6"]=a.low.shift(1).rolling(6,min_periods=6).min()
    a["break_up"]=(a.close>a.high_6).astype(float)
    a["break_dn"]=(a.close<a.low_6).astype(float)
    a["dir_body"]=(a.close-a.open)/a.median_range.replace(0,np.nan)
    return a


def event_features(f,c):
    """Map only completely known higher-timeframe bars to 5m entry times."""
    time = f.index[c.k.to_numpy(np.int32)]
    h1=mtf_frame(f,"1h",60)
    h4=mtf_frame(f,"4h",240)
    x=c.copy()
    for name,frame in (("h1",h1),("h4",h4)):
        aligned=frame.reindex(time,method="ffill")
        for field in ("valid","slope","last_return","prior_3_range",
                      "range_ratio","volume_ratio","break_up","break_dn","dir_body"):
            x[f"{name}_{field}"]=aligned[field].to_numpy()
    x["entry_utc"]=time.astype(str)
    valid=(x.h1_valid & x.h4_valid &
           np.isfinite(x.h1_slope) & np.isfinite(x.h4_slope) &
           np.isfinite(x.h1_volume_ratio) & np.isfinite(x.h4_volume_ratio))
    x=x.loc[valid].copy()
    x=x[(x.risk_points>=MIN_RISK)&(x.risk_points<=MAX_RISK)].copy()
    if x.empty:raise ValueError("No entries after genuine MTF and risk checks")
    # 5m volume is the completed SIGNAL bar; 1h/4h values are previous
    # completed bars as-of the exact entry instant.
    x["slope1_side"]=x.side*x.h1_slope
    x["slope4_side"]=x.side*x.h4_slope
    x["last_return1_side"]=x.side*x.h1_last_return
    x["dirbody1_side"]=x.side*x.h1_dir_body
    x["break1_side"]=np.where(x.side==1,x.h1_break_up,x.h1_break_dn)
    x["break4_side"]=np.where(x.side==1,x.h4_break_up,x.h4_break_dn)
    x["agrees4"]=(x.slope4_side>=0.65)
    x["agrees1"]=(x.slope1_side>=0.65)
    x["activity5"]=(x.volume_ratio>=1.5)&(x.range_ratio>=1.3)
    x["vol_acceleration"]=(x.volume_ratio>=1.7)&(x.range_ratio>=1.25)
    x["hour_expansion"]=(x.h1_range_ratio>=1.5)&(x.h1_volume_ratio>=1.25)
    x["hour_quiet"]=(x.h1_prior_3_range<=.75)
    x["hour_body"]=(x.dirbody1_side>=.65)
    return x


def masks(x):
    result={
        "all_eligible":np.ones(len(x),dtype=bool),
        "4h_slope_agrees":x.agrees4.to_numpy(bool),
        "1h_4h_slope_agrees":(x.agrees4&x.agrees1).to_numpy(bool),
        "4h_trend_1h_pullback":(x.agrees4&(x.last_return1_side<=-.25)).to_numpy(bool),
        "dual_trend_plus_5m_activity":(x.agrees4&x.agrees1&x.activity5).to_numpy(bool),
        "1h_regime_expansion":(x.hour_expansion&x.hour_body).to_numpy(bool),
        "1h_quiet_then_5m_expansion":(x.hour_quiet&x.activity5).to_numpy(bool),
        "1h_directional_high_volume":((x.h1_volume_ratio>=1.5)&x.hour_body).to_numpy(bool),
        "1h_break_6bar_channel":(x.break1_side>=1.).to_numpy(bool),
        "4h_break_6bar_channel":(x.break4_side>=1.).to_numpy(bool),
        # This is an event-time activity contraction relative to the previous
        # hours, NOT the old fixed 3-bar 5m compression pattern.
        "aligned_trend_plus_5m_compression_break":
            (x.agrees4&x.hour_quiet&x.activity5).to_numpy(bool),
        "1h_trend_5m_vol_acceleration":(x.agrees1&x.vol_acceleration).to_numpy(bool),
    }
    if tuple(result)!=FILTERS:
        raise AssertionError("Filter mismatch")
    return result


def replay_all(x,op,hi,lo,cl):
    records=[]
    eligible=masks(x)
    # Each scenario is a STANDALONE one-at-a-time LONG/SHORT strategy.
    # Signals in different patterns and filters are not additive.
    for pat in sorted(x.pattern.unique()):
        maskpat=(x.pattern==pat).to_numpy(bool)
        for name,condition in eligible.items():
            sample=x.loc[maskpat&condition].sort_values(["k","side"],kind="stable")
            if sample.empty:continue
            for rr in R_VALUES:
                for h in HOLDS:
                    busy=-1
                    for z in sample.itertuples(index=False):
                        if z.k<=busy:continue
                        j,reason,gross,net,offer,netR,risk=replay_one(
                            op,hi,lo,cl,int(z.k),int(z.side),float(z.stop_price),
                            float(rr),int(h))
                        busy=int(j)
                        records.append((pat,name,z.period,z.direction,
                            float(rr),int(h),int(z.unix),int(z.unix+60*(j-z.k)),
                            int(z.k),int(j),int(reason),round(float(risk),2),
                            round(float(gross),3),round(float(net),3),
                            round(float(offer),3),round(float(netR),4),
                            round(float(z.volume_ratio),3),
                            round(float(z.range_ratio),3),
                            round(float(z.h1_slope),3),
                            round(float(z.h4_slope),3)))
    return pd.DataFrame(records,columns=[
        "pattern","environment","period","direction","reward_R","hold_minutes",
        "entry_unix","exit_unix","k","exit_k","exit_reason","risk_pts",
        "gross_pts","net_pts","scalper_whatif_pts","net_realized_R",
        "signal_volume_ratio","signal_volatility_ratio","h1_slope","h4_slope"])


def summarize(tr):
    rows=[]
    keys=["pattern","environment","reward_R","hold_minutes","period"]
    for names,g in tr.groupby(keys,sort=True):
        for fee,col in (("standard_taker","net_pts"),
                        ("eligible_scalper_whatif","scalper_whatif_pts")):
            v=g[col].to_numpy(float)
            eq=np.r_[0.,np.cumsum(v)]
            wins=v[v>0].sum()
            losses=-v[v<0].sum()
            rows.append(dict(zip(keys,names),fee_model=fee,trades=len(g),
                longs=int((g.direction=="LONG").sum()),
                shorts=int((g.direction=="SHORT").sum()),
                win_pct=round(100*float((v>0).mean()),2),
                avg_net_pts=round(float(v.mean()),2),
                avg_net_R=round(float(g.net_realized_R.mean()),3)
                    if fee=="standard_taker" else None,
                net_total_pts=round(float(v.sum()),2),
                profit_factor=round(float(wins/losses),3) if losses else None,
                worst_net_pts=round(float(v.min()),2),
                max_drawdown_pts=round(float(np.max(np.maximum.accumulate(eq)-eq)),2),
                target_hit_pct=round(100*float((g.exit_reason==1).mean()),2),
                avg_risk_pts=round(float(g.risk_pts.mean()),2),
                losses_or_flat=int((v<=0).sum())))
    return pd.DataFrame(rows)


def robustness(summary):
    out=[]
    keys=["pattern","environment","reward_R","hold_minutes"]
    for names,g in summary[summary.fee_model=="standard_taker"].groupby(keys,sort=True):
        available={z.period:z for z in g.itertuples()}
        if not all(n in available for n in PERIOD_NAMES[:3]):continue
        a,b,c=[available[n] for n in PERIOD_NAMES[:3]]
        enough=(a.trades>=60 and b.trades>=30 and c.trades>=20)
        out.append(dict(zip(keys,names),
           n_2025=a.trades,net_2025=a.avg_net_pts,
           n_2026H1=b.trades,net_2026H1=b.avg_net_pts,
           n_2026H2=c.trades,net_2026H2=c.avg_net_pts,
           enough_sample=enough,
           stable_positive=bool(enough and
                min(a.avg_net_pts,b.avg_net_pts,c.avg_net_pts)>0)))
    return pd.DataFrame(out)


def effect_table(summary):
    """Same pattern/period/R/hold baseline versus MTF-filtered trade results."""
    s=summary[summary.fee_model=="standard_taker"]
    keys=["pattern","reward_R","hold_minutes","period"]
    base=s[s.environment=="all_eligible"][keys+["trades","avg_net_pts"]].rename(
        columns={"trades":"baseline_trades","avg_net_pts":"baseline_net"})
    paired=s[s.environment!="all_eligible"].merge(base,on=keys,how="inner")
    paired["delta_net_pts"]= (paired.avg_net_pts-paired.baseline_net).round(2)
    return paired


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,seg_start,seg_end,q=read_archive()
    p=periods(f.index)
    raw,counts=candidates(f,seg_start,seg_end,p)
    x=event_features(f,raw)
    op=f.open.to_numpy(float)
    hi=f.high.to_numpy(float)
    lo=f.low.to_numpy(float)
    cl=f.close.to_numpy(float)
    tr=replay_all(x,op,hi,lo,cl)
    if tr.empty:raise ValueError("MTF replay produced zero trades")
    sm=summarize(tr)
    robust=robustness(sm)
    eff=effect_table(sm)
    tr.to_csv(OUT/"trade_ledger.csv.gz",index=False,compression={
        "method":"gzip","compresslevel":5,"mtime":0})
    x.to_csv(OUT/"pre_event_feature_snapshots.csv.gz",index=False,compression={
        "method":"gzip","compresslevel":5,"mtime":0})
    sm.to_csv(OUT/"strategy_results.csv",index=False)
    robust.to_csv(OUT/"chronological_consistency.csv",index=False)
    eff.to_csv(OUT/"environment_vs_baseline.csv",index=False)

    std=sm[sm.fee_model=="standard_taker"]
    good=robust[robust.stable_positive] if not robust.empty else robust
    metadata=dict(
        source="Delta Exchange India BTCUSD 1m futures",
        observed_1min_candles=len(f),
        observed_until_utc=str(f.index[-1]),
        missing_1min_candles=q["missing_minutes"],
        raw_structure_events=len(raw),mtf_and_risk_eligible_events=len(x),
        simulated_trade_rows=len(tr),standalone_model_summary_rows=len(sm),
        pattern_families=sorted(x.pattern.unique()),
        environment_filters=list(FILTERS),
        risk_points_range=[MIN_RISK,MAX_RISK],target_R=list(R_VALUES),
        holding_minutes=list(HOLDS),repeated_positive_models=len(good),
        positive_standard_cells=int((std.avg_net_pts>0).sum()),
        actual_2026_holdout=False,
        methodological_caveats=[
            "Unchanged Stage 11 structural 5m entry rules; only known-in-advance MTF market-state filters are added",
            "Completed 1H/4H candles, aligned to exact next-minute OPEN; prior 16 complete bars required to avoid stale gap joins",
            "1H/4H structures, volume, slopes computed from historical completed candles only",
            "No time-of-day filter; entries can occur any day/hour",
            "Stops beyond confirmed setup levels, 2R/3R targets, <=4h holds",
            "Stop-first 1m OHLC tie; worse fill on stop gaps",
            "Separate strategy simulation per entry pattern/environment/R/hold; trades across models overlap",
            "0.05% taker each side, 18% GST, 5-point adverse slippage per side",
            "Fee-offer sensitivity is conditional, not verified from historical executions",
            "No tick order book or realized bid/ask spread, market impact, margin, liquidation or funding cashflows",
            "Every 2026 period already investigated, not pristine independent validation",
            "Many comparisons cause selection bias; cannot guarantee positive expected results or no losses"])
    (OUT/"quality.json").write_text(json.dumps(metadata,indent=2)+"\n")
    candidate=std[(std.period=="2025_train")&(std.trades>=60)&
                  (std.environment!="all_eligible")].sort_values(
                   "avg_net_pts",ascending=False).head(12)
    keys=["pattern","environment","reward_R","hold_minutes"]
    follow=sm[(sm.fee_model=="standard_taker") &
              (sm.period!="2025_train")].merge(
                  candidate[keys].drop_duplicates(),on=keys,how="inner")
    report=[
        "# Stage 12 — Before BTC's directional move: 1H/4H structure, volatility and participation",
        "",
        "## Research design",
        "- Keep the Stage 11 **8 entry patterns identical**: break-retest, sweep-reclaim,",
        "  engulfing, inside-bar break, structure shift, compression breakout, etc.",
        "- Test only market-state modifiers derived from completed higher-timeframe bars:",
        "  4H or 1H trend agreement, countertrend pullback, volume/range participation,",
        "  channel acceptance, 1H quiet-to-expansion transition, and 5m activity.",
        "- Require >=16 fully complete consecutive 1H/4H candles for prior context.",
        "- Entry = following 1m open; stop beyond completed structure; TP = 2R or 3R.",
        "- One trade per configuration at a time, both LONG and SHORT.",
        "- Compare each condition to the exact pattern with no condition.",
        "- Standard taker + GST and adverse slippage included; separate conditional Scalper Offer study.",
        "- Historical 2025 used for rankings, chronological 2026 already inspected, not pristine OOS.",
        "",
        "## Best condition-specific 2025 models (research only)",
        candidate[["pattern","environment","reward_R","hold_minutes","trades",
                   "win_pct","avg_net_pts","profit_factor","avg_risk_pts"]].to_markdown(index=False), "",
        "## Those exact selections in the research-exposed 2026 periods",
        follow[["pattern","environment","reward_R","hold_minutes","period",
                "trades","win_pct","avg_net_pts","profit_factor"]].to_markdown(index=False), "",
        "## Stable-positive filters (>=60/30/20 trades across 2025, H1 and H2)",
        good.to_markdown(index=False) if len(good) else "No repeated positive setup at the chosen minimum sample sizes.", "",
        "## How much did MTF filtering change net expectancy versus the same unfiltered entry?",
        eff[(eff.period=="2025_train")&(eff.trades>=60)&
            (eff.baseline_trades>=60)].sort_values("delta_net_pts",ascending=False).head(20)[
            ["pattern","environment","reward_R","hold_minutes",
             "trades","baseline_trades","avg_net_pts","baseline_net",
             "delta_net_pts"]].to_markdown(index=False),"",
        "## What cannot be claimed",
        *["- "+s for s in metadata["methodological_caveats"]],"",
        "Reproduce: scripts/research_pretrend_market_state_stage12.py; raw ledgers and",
        "feature snapshots are stored as downloadable GitHub Actions artifacts.",
        ""]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE12_COMPLETED "+json.dumps({k:metadata[k] for k in (
        "observed_1min_candles","raw_structure_events",
        "mtf_and_risk_eligible_events","simulated_trade_rows",
        "positive_standard_cells","repeated_positive_models")}))
    print("BEST_TRAIN\n"+candidate.to_string(index=False))
    print("FOLLOW_2026\n"+follow.to_string(index=False))
    print("STABLE\n"+good.to_string(index=False))

if __name__=="__main__":
    main()
