#!/usr/bin/env python3
"""Stage 7: When does a BTCUSD +200 point move happen? IST hour, day, volume, volatility.

Uses every authentic Delta India 1-minute candle. Entry is NEXT 1-minute open
after all feature windows are complete. No future labels used for selection.
2025 used to rank candidate filters; 2026 H1 and late 2026 are inspected only
for reporting. All history has been researched before: no untouched holdout.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

from research_every_candle_200 import (
    read_archive, periods, first_passage, run_replay,
    summarize_trades, STOP, MAX_MINUTES, PERIOD_NAMES, FEE, SLIPPAGE,
)

OUT = Path("analysis/institutional_discovery_stage7_time_volume")
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
SIDE_NAMES = {1: "LONG", -1: "SHORT"}
STOP_100_IDX = int(np.flatnonzero(STOP == 100)[0])
STOP_200_IDX = int(np.flatnonzero(STOP == 200)[0])


def create_filters(f, seg_start, seg_end, p):
    n = len(f)
    op = f.open.to_numpy(float)
    hi = f.high.to_numpy(float)
    lo = f.low.to_numpy(float)
    cl = f.close.to_numpy(float)
    volume = f.volume.to_numpy(float)
    idx = np.arange(n)

    # Overlapping 5-minute snapshots available at the CURRENT 1-minute open:
    # prior five COMPLETE 1-minute candles only, never the entry candle.
    x = pd.DataFrame({"high": hi, "low": lo, "volume": volume})
    range5 = (x.high.rolling(5, min_periods=5).max() -
              x.low.rolling(5, min_periods=5).min()).shift(1)
    volume5 = x.volume.rolling(5, min_periods=5).sum().shift(1)
    # Reference period ends before the last five candles, to prevent the
    # shock from contaminating its own historical baseline.
    typical_range5 = range5.rolling(60, min_periods=60).median().shift(5)
    typical_volume5 = volume5.rolling(60, min_periods=60).mean().shift(5)
    vol_ratio = (volume5 / typical_volume5.replace(0, np.nan)).to_numpy()
    range_ratio = (range5 / typical_range5.replace(0, np.nan)).to_numpy()
    # No signals spanning a source gap or a chrono testing boundary.
    limit = np.minimum(idx + 60 - 1, n-1)
    valid = (idx - seg_start >= 80) & (seg_end - idx >= 60) & (p == p[limit])
    valid &= np.isfinite(vol_ratio) & np.isfinite(range_ratio)
    valid &= typical_range5.to_numpy() > 0

    india = f.index.tz_convert("Asia/Kolkata")
    hour = np.asarray(india.hour, dtype=np.int8)
    weekday = np.asarray(india.dayofweek, dtype=np.int8)
    block = hour // 3
    selectors = {}

    def add(name, group, cond):
        selectors[name] = (group, np.asarray(cond,dtype=bool) & valid)

    add("all_hours_days", "baseline", np.ones(n,dtype=bool))
    for h in range(24):
        add(f"IST_{h:02d}h", "hour", hour == h)
    for d in range(7):
        add("weekday_"+WEEKDAYS[d], "day", weekday == d)
    for b in range(8):
        add(f"IST_{3*b:02d}-{3*(b+1):02d}", "3hour_block", block == b)
    for threshold in (1.5, 2.0, 3.0):
        v = vol_ratio >= threshold
        r = range_ratio >= threshold
        tag = str(threshold).replace(".", "p")
        add(f"high_volume_{tag}x", "volume", v)
        add(f"high_volatility_{tag}x", "volatility", r)
        add(f"high_volume_and_volatility_{tag}x", "joint", v & r)
        # Specific session combined with high-volume OR high-volatility.
        if threshold <= 2:
            for b in range(8):
                add(f"IST_{3*b:02d}-{3*(b+1):02d}_volume_{tag}x",
                    "session_volume", (block==b)&v)
                add(f"IST_{3*b:02d}-{3*(b+1):02d}_volatility_{tag}x",
                    "session_volatility", (block==b)&r)
            for d in range(7):
                add(f"{WEEKDAYS[d]}_volume_{tag}x",
                    "day_volume",(weekday==d)&v)
                add(f"{WEEKDAYS[d]}_volatility_{tag}x",
                    "day_volatility",(weekday==d)&r)
    # Two-dimensional hour x weekday analysis, fully exploratory.
    for d in range(7):
        for h in range(24):
            add(f"{WEEKDAYS[d]}_IST_{h:02d}h","weekday_hour",
                (weekday==d)&(hour==h))
    return selectors,valid,hour,weekday,vol_ratio,range_ratio


def rates_for(mask, p, side, time_200, time_net, time_stop, mae, horizon):
    ids=np.flatnonzero(mask)
    d=0 if side==1 else 1
    t=time_200[ids,d].astype(np.int32)
    tn=time_net[ids,d].astype(np.int32)
    s100=time_stop[ids,d,STOP_100_IDX].astype(np.int32)
    s200=time_stop[ids,d,STOP_200_IDX].astype(np.int32)
    t_ok=(t>=0)&(t<horizon)
    net_ok=(tn>=0)&(tn<horizon)
    tp100=t_ok & ((s100 < 0) | (t < s100))
    tp200=t_ok & ((s200 < 0) | (t < s200))
    net100=net_ok & ((s100<0) | (tn<s100))
    clean=t_ok&(mae[ids,d]<=0)
    return dict(signals=len(ids),
        gross_200_reached_pct=round(float(100*t_ok.mean()),3),
        net_200_possible_pct=round(float(100*net_ok.mean()),3),
        gross_200_before_100stop_pct=round(float(100*tp100.mean()),3),
        gross_200_before_200stop_pct=round(float(100*tp200.mean()),3),
        net_200_before_100stop_pct=round(float(100*net100.mean()),3),
        no_adverse_200_pct=round(float(100*clean.mean()),4),
        hits_200_before_100stop=int(tp100.sum()),
        net_hits_200_before_100stop=int(net100.sum()))


def prepare_tables(selectors,p,hour,weekday,t200,tnet,tstop,mae):
    records=[]
    for name,(group,base) in selectors.items():
        for per in range(4):
            mask = base & (p==per)
            if not mask.any(): continue
            for side in (1,-1):
                for horizon in (30,60):
                    metrics=rates_for(mask,p,side,t200,tnet,tstop,mae,horizon)
                    records.append(dict(filter=name,kind=group,
                        period=PERIOD_NAMES[per], side=SIDE_NAMES[side],
                        horizon_min=horizon,**metrics))
    full=pd.DataFrame(records)
    full.to_csv(OUT/"all_time_day_volume_volatility_rates.csv",index=False)
    return full


def select_candidate_filters(rates):
    """Choose candidate configurations from 2025 outcomes ONLY.

    The filter selection is still exploratory and multiple-hypothesis tested;
    2026 periods are NOT pristine new data.
    """
    f=rates[(rates.period=="2025_train")&(rates.horizon_min==30)&
            (rates.signals >= 3000)].copy()
    f["score"] = (f.gross_200_before_100stop_pct)
    # Select 12 on gross 200-before-100 probability and 12 on net 200
    # probability; include all fixed univariate filters and baseline.
    sorted_gross=f.sort_values(["score","signals"],ascending=[False,False])
    sorted_net=f.sort_values(["net_200_before_100stop_pct","signals"],
                             ascending=[False,False])
    pick=set(sorted_gross.head(12)["filter"])|set(sorted_net.head(12)["filter"])
    pick |= {k for k,v in f.groupby("filter") if v.kind.iloc[0] in
             ("baseline","hour","day","3hour_block","volume","volatility","joint")}
    selected=sorted(pick)
    reasons=[]
    for name in selected:
        rows=f[f["filter"]==name]
        if rows.empty:continue
        reasons.append(dict(filter=name,group=rows.kind.iloc[0],
                            selected_by="train_rank" if
                            name in set(sorted_gross.head(12)["filter"])|
                                    set(sorted_net.head(12)["filter"])
                            else "predeclared_univariate"))
    pd.DataFrame(reasons).to_csv(OUT/"selected_filters_2025_only.csv",index=False)
    return selected


def replay_models(f,p,selectors,selected,t200,tstop):
    op=f.open.to_numpy(np.float64)
    hi=f.high.to_numpy(np.float64)
    lo=f.low.to_numpy(np.float64)
    cl=f.close.to_numpy(np.float64)
    records=[]
    for name in selected:
        mask=selectors[name][1]
        for side in (1,-1):
            for stop,horizon in ((100,30),(200,30),(100,60),(200,60)):
                for k,last,per,reason,gross,netstd,netoffer,mins in run_replay(
                        mask,side,p,op,hi,lo,cl,t200,tstop,stop,horizon):
                    records.append(dict(rule=name,side=side,
                        model=f"SL{stop}_TP200_{horizon}m",
                        period=PERIOD_NAMES[per],entry_index=k,
                        entry_unix_s=int(f.time.iloc[k]),
                        exit_unix_s=int(f.time.iloc[last]),
                        reason=reason,gross_pts=gross,
                        net_standard_pts=netstd,
                        net_scalper_scenario_pts=netoffer,
                        duration_min=mins))
    trades=pd.DataFrame(records)
    if trades.empty:raise ValueError("No trades")
    trades.to_csv(OUT/"trade_ledger.csv.gz",index=False,
                  compression={"method":"gzip","mtime":0,"compresslevel":5})
    summary=summarize_trades(trades)
    summary["side"] = summary.side.map(SIDE_NAMES)
    summary.to_csv(OUT/"trade_summary.csv",index=False)
    return trades,summary


def report(rates,summary,quality,selected):
    baseline=rates[(rates["filter"]=="all_hours_days")&
                    (rates.horizon_min==30)]
    f=rates[(rates.period=="2025_train")&(rates.horizon_min==30)&
            (rates.signals>=3000)]
    # All prospective 2026 reporting rows are displayed for train-ranked
    # selections; positive-looking train observations aren't achievements.
    best=f.sort_values("gross_200_before_100stop_pct",ascending=False).head(14)
    std=summary[(summary.fee_model=="standard_taker")&
                (summary.model=="SL100_TP200_30m")]
    byper=std.groupby("period").agg(
        tested=("rule","size"),positive=("avg_net_pts",lambda x:int((x>0).sum())),
        zero_loss=("losses_or_flat",lambda x:int((x==0).sum())),
        max_net=("avg_net_pts","max")).reset_index()
    rows=[
        "# Stage 7 — Every BTC 1-minute candle: time, weekday, volume and volatility",
        "",
        "## Predeclared setup",
        "- Dataset: Delta India BTCUSD authentic 1m futures, first Jan 2025 to latest archive.",
        "- Entry: next 1m open; only previous completed 5m candles used for high volume/range.",
        "- Time zone: Asia/Kolkata, DST-free. Hour is the actual entry timestamp.",
        "- High volume = last completed rolling 5m total volume / older 60-window mean",
        "  above fixed 1.5x / 2x / 3x thresholds.",
        "- High volatility = last completed rolling 5m high-low range / older 60-window",
        "  median above fixed 1.5x / 2x / 3x thresholds.",
        "- Test all 24 IST hours, 7 days, 3h blocks, and intersections.",
        "- Missing minute history never filled; conditions crossing gaps removed.",
        "- Ex-post +200 reaches cannot be treated as predictable entry signals.",
        "- Uses standard 0.05% taker/side + 18% GST and adverse 5 points/side slippage;",
        "  alternate Scalper Offer closing-fee waiver is a hypothetical eligible scenario.",
        "- Same 1m stop and TP bar: stop FIRST; no independent tick path.",
        "- Each independent rule/direction/stop/horizon permits only one concurrent position.",
        "",
        "## All-candle 30-minute reference",
        baseline.to_markdown(index=False),"",
        "## 2025 training: highest 200-before-100-stop event probabilities",
        best.to_markdown(index=False),"",
        "## Selected entries: net results by period (200 gross TP, 100 stop, 30min maximum)",
        byper.to_markdown(index=False),"",
        "## Highest net expectancy on each period: NEVER a forward recommendation",
    ]
    for period in PERIOD_NAMES:
        pick=std[(std.period==period)&(std.trades>=25)].sort_values(
            "avg_net_pts",ascending=False).head(12)
        rows.extend(["",f"### {period}",pick[[
            "rule","side","trades","win_pct","avg_net_pts","profit_factor",
            "losses_or_flat"]].to_markdown(index=False) if len(pick)
            else "No sufficient observations"])
    rows.extend(["", "## Readout and limitations",
        "- Clock/day effects are observational. Large differences may be regime and sampling effects.",
        "- Training ranks are selected from multiple thresholds. 2026 was previously studied;",
        "  there is NO pristine out-of-sample evaluation.",
        "- Overlapping +200 first-passage events are correlated and should NOT be summed as trades.",
        "- A positive hit probability alone does not cover fees and stopped-out losses.",
        "- Standard price range is not actual bid/ask quote depth, funding or market impact.",
        "- No guarantee of a zero-loss trade, and no live deployment recommendation.",
        "",
        "## Files",
        "- all_time_day_volume_volatility_rates.csv — exhaustive group comparisons",
        "- selected_filters_2025_only.csv — selection audit",
        "- trade_summary.csv — full standard and Scalper Offer what-if net outcomes",
        "- trade_ledger.csv.gz — independently simulated entries",
        "- quality.json — data and research limitations",
    ])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(rows)+"\n")


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,seg_start,seg_end,quality=read_archive()
    p=periods(f.index)
    selectors,valid,hour,weekday,volume_ratio,range_ratio=create_filters(
        f,seg_start,seg_end,p)
    split_counts={PERIOD_NAMES[i]:int(np.count_nonzero(valid&(p==i)))
                  for i in range(4)}
    if min(split_counts.values()) < 1000:
        raise ValueError("Chronological period problem "+str(split_counts))
    op=f.open.to_numpy(np.float64); hi=f.high.to_numpy(np.float64)
    lo=f.low.to_numpy(np.float64)
    t200,tnet,tstop,mae=first_passage(op,hi,lo,seg_end,STOP,MAX_MINUTES)
    rates=prepare_tables(selectors,p,hour,weekday,t200,tnet,tstop,mae)
    selected=select_candidate_filters(rates)
    trades,summary=replay_models(f,p,selectors,selected,t200,tstop)
    s=summary[summary.fee_model=="standard_taker"]
    o=summary[summary.fee_model=="eligible_scalper_scenario"]
    quality.update(dict(
        study="IST hour/weekday and preceding completed 5m volume/volatility",
        indicator_timing="entry minute OPEN; all features from earlier completed minutes",
        eligible_candidates=int(valid.sum()),filter_count=len(selectors),
        filtered_rate_rows=len(rates),replayed_filter_count=len(selected),
        simulated_trade_rows=len(trades),summary_rows=len(summary),
        standard_positive_groups=int((s.avg_net_pts>0).sum()),
        scalper_whatif_positive_groups=int((o.avg_net_pts>0).sum()),
        zero_loss_standard_groups=int((s.losses_or_flat==0).sum()),
        period_usable_counts=split_counts,
        historical_splits=list(PERIOD_NAMES),
        future_horizons_minutes=[30,60],
        stops_tested_points=[100,200],
        target_points_gross=200,
        fee_standard_per_side=FEE,
        slippage_points_per_side=SLIPPAGE,
        note="All 2026 data have been inspected before; 2025 selection does not create a pristine holdout",
        limitations=[
            "No intraminute tick path or actual order book; adverse stop-first within 1m",
            "No verified real order eligibility for historical Scalper Offer",
            "No market impact, bid/ask, liquidation or margin/funding cashflows",
            "Multiple-hypothesis search over day and time combinations",
            "Overlap in all-candle labels means strongly dependent observations",
            "Trade summaries are per-condition standalone, not combined portfolio",
            "No zero-loss or profitability guarantee"
        ]))
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    report(rates,summary,quality,selected)
    view=summary[(summary.fee_model=="standard_taker")&
                 (summary.model=="SL100_TP200_30m")]
    print("STAGE7_DONE",json.dumps(dict(candles=len(f),valid=int(valid.sum()),
        filters=len(selectors),replayed=len(selected),trade_rows=len(trades),
        plus_groups=int((view.avg_net_pts>0).sum()),periods=split_counts)))
    print("TRAIN_TOP",rates[(rates.period=="2025_train")&
        (rates.horizon_min==30)&(rates.signals>=3000)].sort_values(
        "gross_200_before_100stop_pct",ascending=False).head(12).to_string(index=False))
    print("NET_TOP",view.sort_values("avg_net_pts",ascending=False).head(24).to_string(index=False))

if __name__=="__main__":
    main()
