#!/usr/bin/env python3
"""Scan time-of-day and weekday BTCUSD futures strategies, with prospective-style splits.

Uses only genuine Delta India BTCUSD perpetual 1m OHLCV and no future data in
signals. 5m/15m candle-follow/fade enters only after the candle has CLOSED.
Out-of-sample July-Oct 2026 is never used to select trading rules.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/time_day_strategy_research")
TRAIN_END=pd.Timestamp("2026-01-01",tz="UTC")
VALID_END=pd.Timestamp("2026-07-01",tz="UTC")
HORIZONS=(15,30,60,120,240,480)
SLIP=5.0
ROUND_TRIP_TAKER_GST=0.0005*1.18
APPROACHES=("clock_long","clock_short","prior5_follow","prior5_fade","prior15_follow","prior15_fade")
GROUPS=("ALL","WEEKDAY","WEEKEND","MON","TUE","WED","THU","FRI","SAT","SUN")

def load():
    fragments=[]
    paths=sorted(ROOT.glob("20??-??.csv.gz"))
    if not paths:
        raise RuntimeError("Missing Delta BTCUSD minute files")
    for file in paths:
        d=pd.read_csv(file,compression="gzip",usecols=["time","open","high","low","close","volume"])
        d["time"]=pd.to_datetime(d.time.astype("int64"),unit="s",utc=True)
        fragments.append(d)
    d=pd.concat(fragments,ignore_index=True).set_index("time").sort_index()
    if d.index.has_duplicates or d[["open","high","low","close","volume"]].isna().any().any():
        raise ValueError("Duplicate or missing raw OHLCV")
    gap=d.index.to_series().diff().iloc[1:]
    if not gap.eq(pd.Timedelta(minutes=1)).all():
        raise ValueError("Minute gap: refusing to invent missing candles")
    return d,len(paths)

def assign_period(stamps):
    return np.where(stamps<TRAIN_END,"train",np.where(stamps<VALID_END,"validation","holdout"))

def base_events(d):
    idx=np.arange(15,len(d)-max(HORIZONS),5,dtype=np.int64)
    # Absolute index is aligned to 00:00 UTC because the downloaded series
    # starts exactly at UTC midnight, has no missing minutes, and is continuous.
    stamps=d.index[idx]
    ny=stamps.tz_convert("America/New_York")
    oo=d.open.to_numpy(dtype=float)
    cc=d.close.to_numpy(dtype=float)
    prev5=np.sign(cc[idx-1]-oo[idx-5]).astype(np.int8)
    prev15=np.where(idx%15==0,np.sign(cc[idx-1]-oo[idx-15]),0).astype(np.int8)
    local_day=np.array([str(x) for x in ny.date])
    return idx,stamps,ny,local_day,prev5,prev15,oo,cc

def compute_events(d):
    idx,stamps,ny,days,prev5,prev15,oo,cc=base_events(d)
    entry=oo[idx]
    time_split=assign_period(stamps)
    weekday=ny.dayofweek
    clock=(ny.hour*60+ny.minute).astype(np.int16)
    # Include a signal-based candle direction alongside blind clock entry.
    side_by_method={
        "clock_long":np.ones(len(idx),dtype=np.int8),
        "clock_short":-np.ones(len(idx),dtype=np.int8),
        "prior5_follow":prev5,
        "prior5_fade":-prev5,
        "prior15_follow":prev15,
        "prior15_fade":-prev15}
    rows=[]
    for horizon in HORIZONS:
        exit_price=cc[idx+horizon-1]
        fee=ROUND_TRIP_TAKER_GST*(entry+exit_price)
        for method,side in side_by_method.items():
            good=(side!=0)
            trade_pts=side*(exit_price-entry)-fee-2*SLIP
            tbl=pd.DataFrame({
                "entry_index":idx[good],
                "utc_entry":stamps[good].astype(str),
                "ny_date":days[good],
                "ny_weekday":weekday[good],
                "clock":clock[good],
                "split":time_split[good],
                "approach":method,
                "minutes":horizon,
                "direction":side[good],
                "entry_price":entry[good].round(2),
                "future_price":exit_price[good].round(2),
                "gross_points":(side[good]*(exit_price[good]-entry[good])).round(3),
                "net_points":trade_pts[good].round(3)})
            rows.append(tbl)
    # ~5.4 million trade/event simulations; group and summarize without
    # ever choosing a parameter from holdout.
    return pd.concat(rows,ignore_index=True)

def summarize(events):
    collected=[]
    labels=("MON","TUE","WED","THU","FRI","SAT","SUN")
    for group in GROUPS:
        if group=="ALL":x=events
        elif group=="WEEKDAY":x=events[events.ny_weekday<5]
        elif group=="WEEKEND":x=events[events.ny_weekday>=5]
        else:x=events[events.ny_weekday==labels.index(group)]
        if x.empty:continue
        gb=x.groupby(["approach","minutes","clock","split"],observed=True).net_points
        summary=gb.agg(["size","mean","std","median",lambda z:(z>0).mean(),
                         lambda z:(z>=200).mean(),lambda z:(z>=500).mean()])
        summary.columns=["n","mean_net","std_net","median_net","win_frac","net200_frac","net500_frac"]
        summary=summary.reset_index()
        summary["day_group"]=group
        collected.append(summary)
    result=pd.concat(collected,ignore_index=True)
    result["mean_net"]=result.mean_net.round(3)
    result["median_net"]=result.median_net.round(3)
    result["win_pct"]=(100*result.win_frac).round(2)
    result["net200_pct"]=(100*result.net200_frac).round(2)
    result["net500_pct"]=(100*result.net500_frac).round(2)
    result["ny_entry_time"]=result.clock.map(lambda x:f"{int(x)//60:02d}:{int(x)%60:02d}")
    return result.drop(columns=["win_frac","net200_frac","net500_frac"])

def three_periods(summary):
    ix=["approach","minutes","clock","day_group"]
    cols=["n","mean_net","std_net","win_pct","net200_pct","net500_pct"]
    x=summary.pivot(index=ix,columns="split",values=cols)
    x.columns=[str(a)+"_"+str(b) for a,b in x.columns]
    x=x.reset_index()
    x["ny_entry_time"]=x.clock.map(lambda z:f"{int(z)//60:02d}:{int(z)%60:02d}")
    for period in ("train","validation","holdout"):
        for field in cols:
            name=field+"_"+period
            if name not in x:x[name]=np.nan
    # n guard adapted to pool breadth, chosen without examining performance.
    req=np.select([x.day_group.isin(["ALL","WEEKDAY"]),
                   x.day_group=="WEEKEND"],
                  [160,65],default=37)
    reqval=np.select([x.day_group.isin(["ALL","WEEKDAY"]),
                      x.day_group=="WEEKEND"],
                     [70,25],default=15)
    reqhold=np.select([x.day_group.isin(["ALL","WEEKDAY"]),
                      x.day_group=="WEEKEND"],
                     [45,15],default=9)
    x["eligible"]=(x.n_train>=req)&(x.n_validation>=reqval)&(x.n_holdout>=reqhold)
    x["train_se"]=x.std_net_train/np.sqrt(x.n_train)
    x["validation_se"]=x.std_net_validation/np.sqrt(x.n_validation)
    x["train_z"]=x.mean_net_train/x.train_se
    x["validation_z"]=x.mean_net_validation/x.validation_se
    # Ranking uses training and validation only. Never use holdout returns
    # or probabilities in candidate rank/selection.
    x["conservative_score"]=np.minimum(x.mean_net_train-1.96*x.train_se,
                                       x.mean_net_validation-1.96*x.validation_se)
    x["both_preholdout_positive"]=(x.mean_net_train>0)&(x.mean_net_validation>0)
    x["both_strong"]=x.eligible&(x.train_z>3.5)&(x.validation_z>2.7)
    return x

def candidate_replay(d,events,selected):
    """Three fixed protective stops; same entry time/direction as calendar scan.
    Simulated on all three splits, NEVER tuned by final holdout."""
    if selected.empty:return pd.DataFrame(),pd.DataFrame()
    highs=d.high.to_numpy()
    lows=d.low.to_numpy()
    closes=d.close.to_numpy()
    opens=d.open.to_numpy()
    replay=[]
    for row in selected.itertuples():
        group=row.day_group
        g=events[(events.approach==row.approach)&
                 (events.minutes==row.minutes)&(events.clock==row.clock)]
        if group=="WEEKDAY":g=g[g.ny_weekday<5]
        elif group=="WEEKEND":g=g[g.ny_weekday>=5]
        elif group!="ALL":g=g[g.ny_weekday==("MON","TUE","WED","THU","FRI","SAT","SUN").index(group)]
        if g.empty:continue
        # These are one position/day per candidate rule.
        assert not g.ny_date.duplicated().any()
        for e in g.itertuples():
            start=int(e.entry_index);side=int(e.direction)
            price=float(opens[start]);n=int(row.minutes)
            for stop in (250,500,800):
                for target in (0,500,1000):
                    stop_level=price-side*stop
                    target_level=price+side*target
                    exit_price=float(closes[start+n-1])
                    cause="time"
                    hold=n
                    for j in range(n):
                        k=start+j
                        hit_stop=(lows[k]<=stop_level) if side>0 else (highs[k]>=stop_level)
                        hit_target= ((highs[k]>=target_level) if side>0 else (lows[k]<=target_level)) if target else False
                        if hit_stop:
                            exit_price=stop_level;cause="stop";hold=j+1;break
                        if hit_target:
                            exit_price=target_level;cause="target";hold=j+1;break
                    net=side*(exit_price-price)-2*SLIP-ROUND_TRIP_TAKER_GST*(price+exit_price)
                    replay.append(dict(rule_id=int(row.rule_id),day_group=group,
                         ny_time=row.ny_entry_time,approach=row.approach,
                         minutes=int(row.minutes),split=e.split,ny_day=e.ny_date,
                         stop_points=stop,target_points=target,
                         cause=cause,held_minutes=hold,
                         net_points=round(net,3),gross_points=round(side*(exit_price-price),3)))
    tr=pd.DataFrame(replay)
    if tr.empty:return tr,pd.DataFrame()
    grouped=tr.groupby(["rule_id","stop_points","target_points","split"],observed=True).net_points
    stats=grouped.agg(["size","mean","median",lambda z:(z>0).mean()])
    stats.columns=["n","avg_net","median_net","win_rate"]
    stats=stats.reset_index()
    stats["win_pct"]=(100*stats.win_rate).round(2)
    stats.avg_net=stats.avg_net.round(2)
    stats.median_net=stats.median_net.round(2)
    return tr,stats.drop(columns=["win_rate"])

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    raw,month_count=load()
    events=compute_events(raw)
    quality=dict(source="Delta Exchange India BTCUSD perpetual native 1m",
        months=month_count,minute_candles=len(raw),
        utc_start=str(raw.index.min()),utc_end=str(raw.index.max()),
        zero_volume_candles=int((raw.volume==0).sum()),
        evaluated_event_outcomes=len(events),
        periods={"train":"2025","validation":"Jan-Jun 2026","holdout":"Jul-Oct 17 2026"})
    del raw # Re-read for protective path test only
    summary=summarize(events)
    allrules=three_periods(summary)
    eligible=allrules[allrules.eligible].copy()
    ranked=eligible.sort_values("conservative_score",ascending=False)
    positive=ranked[ranked.both_preholdout_positive].copy()
    strong=ranked[ranked.both_strong].copy()
    # Test twenty preselected rules with stop/target combinations,
    # one final holdout evaluation per preselected rule.
    finalists=(positive.head(20) if len(positive) else ranked.head(20)).copy()
    finalists=finalists.reset_index(drop=True)
    finalists.insert(0,"rule_id",np.arange(len(finalists),dtype=int)+1)
    raw,_=load()
    protective,protection_summary=candidate_replay(raw,events,finalists)
    # Only compact summary saved: raw OHLCV remains in source archive,
    # and per-rule protective trades are reproducible if needed.
    allrules.to_csv(OUT/"all_time_day_rules.csv",index=False)
    ranked.to_csv(OUT/"eligible_ranked_by_preholdout.csv",index=False)
    finalists.to_csv(OUT/"preselected_candidates.csv",index=False)
    if len(protective):protective.to_csv(OUT/"selected_rule_stop_trades.csv",index=False)
    if len(protection_summary):
        protection_summary.to_csv(OUT/"selected_rule_stop_target_summary.csv",index=False)
    # Baseline clock/day hourly patterns for each timeframe, without cherry picking.
    hour=summary[(summary.day_group.isin(["MON","TUE","WED","THU","FRI","SAT","SUN"]))&
        (summary.approach.isin(["clock_long","clock_short"]))&
        (summary.minutes.isin([60,240]))&(summary.clock%60==0)].copy()
    hour.to_csv(OUT/"hourly_weekday_baselines.csv",index=False)
    quality.update(eligible_rules=len(eligible),positive_both_train_validation=len(positive),
        strong_train_validation=len(strong),
        final_candidates=len(finalists),
        tested_unique_rules=int(len(allrules)),
        selection="Rank strictly on 2025 and Jan-Jun 2026. Holdout not used.")
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    lead=finalists[["rule_id","day_group","ny_entry_time","approach","minutes",
        "n_train","mean_net_train","n_validation","mean_net_validation",
        "n_holdout","mean_net_holdout","win_pct_holdout","conservative_score"]].copy()
    show=lead.head(20)
    after=protection_summary[protection_summary.split=="holdout"]
    selected_stop=after[after.target_points==0][after.stop_points==500]
    report=[
        "# BTCUSD Futures: Time-based and day-of-week trading strategies",
        "",
        "## What was tested",
        "The real Delta India BTCUSD 1-minute candles, Jan 2025 through Oct 17 2026.",
        "Every five minutes in America/New_York, adjusted automatically for US daylight saving.",
        "Day filters: each Monday–Sunday individually, all days, weekdays and weekends.",
        "Entry variants: clock LONG, clock SHORT, prior completed 5m candle follow/fade, prior completed 15m candle follow/fade.",
        "Holding durations: 15, 30, 60, 120, 240, 480 minutes. Signals are known at entry and never use future price information.",
        "Each time-and-day rule has at most one signal in any New York calendar day. Weekend periods are included.",
        "Fee model: both entries/exits taker 0.05% times 1.18 GST; slippage 5 BTC price points each side. No funding, spread/impact beyond modeled slippage, forced liquidation or position sizing.",
        "",
        "## Chronological data separation and selection",
        "TRAIN 2025, VALIDATION Jan-Jun 2026, holdout July 1–October 17 2026.",
        "The HOLDOUT is NEVER used to pick a candidate or its stop/target. The many scans mean apparent positive results can be luck.",
        "A positive finding must be robust to multiple comparisons, realistic protective stops, fee stress and new live-forward data before any capital deployment.",
        "Every winning percentage is a historical outcome, NOT a daily guarantee.",
        "",
        "## Data quality and multiple-tests warning",
        "~~~json",json.dumps(quality,indent=2),"~~~",
        "",
        "A conservative score is the WORSE 95%-style estimated lower mean bound in training and validation.",
        "Normal-style standard errors use individual date events; they are NOT autocorrelation or volatility-regime adjusted. The stringent exploratory screen requires train z>3.5 and validation z>2.7 and is NOT a family-wise correction.",
        "",
        "## Top rules selected exclusively on train+validation",
        show.to_markdown(index=False) if len(show) else "No eligible rules.",
        "",
        "## Protective stop retest of preselected rules (holdout only)",
        "Below uses 500 BTC price point hard stop, time exit at chosen duration, no profit target. Exactly the same day/time/entry rules as above.",
        selected_stop[["rule_id","n","avg_net","median_net","win_pct"]].to_markdown(index=False) if len(selected_stop) else "No candidates.",
        "",
        "Other stops (250, 500, 800) and targets (none, 500, 1000) are reported in selected_rule_stop_target_summary.csv. Intraminute stop/target ambiguity is assigned to STOP first.",
        "Do NOT choose the best result from these holdout stop variants and then claim a genuinely untouched test.",
        "",
        "## Files",
        "- all_time_day_rules.csv: every weekday/clock/entry/hold evaluated (including negative ones).",
        "- eligible_ranked_by_preholdout.csv: ordered using only earlier data.",
        "- hourly_weekday_baselines.csv: the honest full weekly clock context.",
        "- preselected_candidates.csv: candidates selected before holdout.",
        "- selected_rule_stop_trades.csv / selected_rule_stop_target_summary.csv: 1m path-aware protective-stop replay.",
        "",
        "## Interpretation",
        "Constant entry based on clock/day does not know market direction, and following/fading one 5m/15m candle remains a simplistic proxy.",
        "These are exploratory strategies, not identification of institutional orders or actual resting liquidity.",
        "A day may have a 500+ point high-low range yet have no profitable time entry.",
        "Fixed time exits without stops are diagnostic only; evaluate path-aware protective stops before contemplating live orders.",
        ""]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report),encoding="utf-8")
    print("COMPLETED",json.dumps(quality))
    print("PRESELECTED",show.to_string(index=False))
    print("STOP500",selected_stop.to_string(index=False))

if __name__=="__main__":
    main()
