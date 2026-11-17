#!/usr/bin/env python3
"""V8 BTC behavior discovery: catalogue large 2025 trend legs FIRST.

No indicator optimizer. Causal hourly features are evaluated only AFTER
retrospective leg labeling, against ALL hourly candidates (including failures).
No candle in 2026 is read. 2025 is a previously studied development dataset.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_v7_2_daily_4h_2025 import load_2025, aggregate, ema

START=pd.Timestamp("2025-03-01T00:00:00Z")
END=pd.Timestamp("2026-01-01T00:00:00Z")
SPLIT=pd.Timestamp("2025-09-01T00:00:00Z")
REVERSAL=1000.0
RISK=1000.0
TARGETS=(2000,5000)
HOURS=(24,48)

def trend_legs(m):
    """Ex-post, confirmed zigzag using 1m CLOSE and 1000-point reversal.

    Pivot timestamps refer to the ex-post extremes, NEVER real-time entry points.
    An unconfirmed final leg is deliberately excluded.
    """
    prices=m.close.to_numpy(dtype=float)
    stamps=m.index
    start_i=0
    min_i=max_i=0
    mode=0
    records=[]
    for i in range(1,len(prices)):
        p=prices[i]
        if mode==0:
            if p<prices[min_i]:min_i=i
            if p>prices[max_i]:max_i=i
            if p>=prices[min_i]+REVERSAL:
                mode=1;start_i=min_i;max_i=i
            elif p<=prices[max_i]-REVERSAL:
                mode=-1;start_i=max_i;min_i=i
            continue
        if mode==1:
            if p>prices[max_i]:max_i=i
            if p<=prices[max_i]-REVERSAL:
                if start_i<max_i:
                    records.append((stamps[start_i],stamps[max_i],stamps[i],
                                    "LONG",float(prices[max_i]-prices[start_i])))
                mode=-1;start_i=max_i;min_i=i
        else:
            if p<prices[min_i]:min_i=i
            if p>=prices[min_i]+REVERSAL:
                if start_i<min_i:
                    records.append((stamps[start_i],stamps[min_i],stamps[i],
                                    "SHORT",float(prices[start_i]-prices[min_i])))
                mode=1;start_i=min_i;max_i=i
    legs=pd.DataFrame(records,columns=["start_time","extreme_time","confirmation_time",
                                       "direction","size_points"])
    legs=legs.loc[(legs.start_time>=START)&(legs.confirmation_time<=END)].copy()
    legs["duration_hours"]=(legs.extreme_time-legs.start_time).dt.total_seconds()/3600
    legs["month"]=legs.start_time.dt.strftime("%Y-%m")
    legs["period"]=np.where(legs.start_time<SPLIT,"discovery","later_2025_check")
    return legs

def hourly_features(m):
    h=aggregate(m,"1h",60)
    d=aggregate(m,"1D",1440)
    four=aggregate(m,"4h",240)
    d["ema20"]=ema(d.close,20)
    d["ema50"]=ema(d.close,50)
    four["ema20"]=ema(four.close,20)
    four["ema50"]=ema(four.close,50)
    h["ema20"]=ema(h.close,20)
    h["prior12high"]=h.high.shift(1).rolling(12,min_periods=12).max()
    h["prior12low"]=h.low.shift(1).rolling(12,min_periods=12).min()
    h["momentum6"]=h.close-h.close.shift(6)
    h["body"]=h.close-h.open
    h["loc"]=(h.close-h.low)/(h.high-h.low).replace(0,np.nan)
    h["range_ratio"]=(h.high-h.low)/(h.high-h.low).rolling(48,min_periods=48).median().shift(1)
    h["vol_ratio"]=h.volume/h.volume.rolling(48,min_periods=48).mean().shift(1)
    h["prev_high"]=h.high.shift(1)
    h["prev_low"]=h.low.shift(1)
    for side,name in ((1,"long"),(-1,"short")):
        if side==1:
            day=(d.close>d.ema20)&(d.ema20>d.ema50)
            fourtrend=(four.close>four.ema20)&(four.ema20>four.ema50)
        else:
            day=(d.close<d.ema20)&(d.ema20<d.ema50)
            fourtrend=(four.close<four.ema20)&(four.ema20<four.ema50)
        h["day_"+name]=day.reindex(h.index,method="ffill").fillna(False).astype(bool)
        h["four_"+name]=fourtrend.reindex(h.index,method="ffill").fillna(False).astype(bool)
    return h

def signal_flags(z,side):
    # Every single rule below uses only the completed present/past OHLCV candle.
    if side==1:
        directed=z.body>0 and z["loc"]>=0.75
        accepted=z.close>z.prior12high and directed
        pb=z.low<=z.ema20 and z.close>z.ema20 and z.close>z.prev_high and z.body>0
        momentum=z.momentum6>=300
        aligned=z.day_long and z.four_long
    else:
        directed=z.body<0 and z["loc"]<=0.25
        accepted=z.close<z.prior12low and directed
        pb=z.high>=z.ema20 and z.close<z.ema20 and z.close<z.prev_low and z.body<0
        momentum=z.momentum6<=-300
        aligned=z.day_short and z.four_short
    impulse=directed and z.range_ratio>=1.5 and z.vol_ratio>=1.5
    return {
        "momentum6":bool(momentum),
        "day4h_alignment":bool(aligned),
        "accepted_12h_breakout":bool(accepted),
        "range_volume_impulse":bool(impulse),
        "trend_and_breakout":bool(aligned and accepted),
        "trend_and_pullback":bool(aligned and pb),
        "trend_and_impulse":bool(aligned and impulse),
    }

def first_hit(mask):
    hits=np.flatnonzero(mask)
    return int(hits[0]) if len(hits) else 2**31-1

def label_candidates(h,m):
    """Sample every COMPLETED 1H candle + BOTH directions; conservative 1m barriers.

    Entry reference is the next minute's OPEN. For TARGET and adverse on the
    same 1m candle, adverse wins. Features never inspect future bars.
    """
    highs=m.high.to_numpy(dtype=float)
    lows=m.low.to_numpy(dtype=float)
    opens=m.open.to_numpy(dtype=float)
    ix=m.index
    records=[]
    stop_before=dict()
    for ts,z in h.loc[(h.index>=START)&(h.index<=END-pd.Timedelta(hours=48))].iterrows():
        if ts==END:continue
        # Research every hour including weekends, then report weekday-only results too.
        begin=ix.searchsorted(ts)
        if begin+48*60>len(m):continue
        max_hi=highs[begin:begin+48*60]
        min_lo=lows[begin:begin+48*60]
        entry=float(opens[begin])
        for side in (1,-1):
            f=signal_flags(z,side)
            favorable=(max_hi-entry) if side==1 else (entry-min_lo)
            adverse=(entry-min_lo) if side==1 else (max_hi-entry)
            stop_at=first_hit(adverse>=RISK)
            targets={target:first_hit(favorable>=target) for target in TARGETS}
            o={
                "signal_time":ts,"month":ts.strftime("%Y-%m"),
                "period":"discovery" if ts<SPLIT else "later_2025_check",
                "direction":"LONG" if side==1 else "SHORT",
                "weekday_ist":bool(ts.tz_convert("Asia/Kolkata").weekday()<5),
                "entry_reference":entry,
                "first_1k_adverse_minute":int(stop_at) if stop_at<2**31-1 else -1,
                "favorable_max_24h":round(float(favorable[:24*60].max()),1),
                "favorable_max_48h":round(float(favorable.max()),1),
                "adverse_max_24h":round(float(adverse[:24*60].max()),1),
                "adverse_max_48h":round(float(adverse.max()),1),
            }
            for target in TARGETS:
                for hours in HOURS:
                    t=targets[target]
                    o[f"target{target}_{hours}h_before_stop"]=bool(t < hours*60 and t < stop_at)
            o.update(f)
            records.append(o)
    return pd.DataFrame(records)

CONDITIONS=["baseline_all_hours","momentum6","day4h_alignment","accepted_12h_breakout",
            "range_volume_impulse","trend_and_breakout","trend_and_pullback",
            "trend_and_impulse"]

def evaluate(candidates, legs):
    periods={
        "Mar-Aug_2025":candidates.period=="discovery",
        "Sep-Dec_2025":candidates.period=="later_2025_check",
        "All_Mar_Dec":pd.Series(True,index=candidates.index),
    }
    stats={}
    for pname,period in periods.items():
        stats[pname]={}
        for weekdays in (False,True):
            base=period & (candidates.weekday_ist if weekdays else True)
            key="weekdays_IST" if weekdays else "all_days"
            stats[pname][key]={}
            for c in CONDITIONS:
                data=candidates.loc[base & (candidates[c] if c!="baseline_all_hours" else True)]
                d={"opportunities":len(data)}
                for target in TARGETS:
                    for hours in HOURS:
                        col=f"target{target}_{hours}h_before_stop"
                        d[f"hit{target}_{hours}h"]=int(data[col].sum())
                        d[f"rate{target}_{hours}h_pct"]=round(float(data[col].mean())*100,2) if len(data) else None
                stats[pname][key][c]=d
    # Coverage: did each CAUSAL condition appear in the FIRST QUARTER of an
    # retrospectively catalogued trend? Not an executable pivot-entry claim.
    cover={}
    for min_size in TARGETS:
        relevant=legs.loc[legs.size_points>=min_size]
        cover[str(min_size)]={"legs":len(relevant),"conditions":{}}
        for c in CONDITIONS[1:]:
            count=0
            for leg in relevant.itertuples(index=False):
                first_quarter=leg.start_time+(leg.extreme_time-leg.start_time)/4
                subset=candidates.loc[(candidates.signal_time>=leg.start_time)&
                    (candidates.signal_time<=first_quarter)&
                    (candidates.direction==leg.direction)&candidates[c]]
                if len(subset):count+=1
            cover[str(min_size)]["conditions"][c]={
                "detected_early":count,
                "pct":round(100*count/len(relevant),2) if len(relevant) else None}
    return stats,cover

def make_report(legs,candidates,stats,cover):
    lines=[
        "# V8 — Reverse-engineering real BTC big moves (2025)", "",
        "**Descriptive discovery and causal-entry opportunity labels; NOT a profit-tested strategy.**",
        "Data: Delta India BTCUSD futures 1-minute candles, January–December 2025; evaluated March–December.",
        "",
        "## A. What big trends actually occurred?",
        "",
        "Trend legs are defined by a hindsight zigzag on 1m CLOSE with a 1,000-point reversal.",
        "Legs are considered *confirmed* only after the opposite 1,000-point reversal.",
        "The pivot start and end are retrospective labels, NOT knowable trade entry locations.",
        "",
        "| Size threshold | Confirmed legs | Median hours to extreme | Biggest leg (pts) |",
        "|---|---:|---:|---:|",
    ]
    for t in TARGETS:
        x=legs.loc[legs.size_points>=t]
        lines.append(f"| {t:,}+ pts | {len(x)} | {round(float(x.duration_hours.median()),1) if len(x) else '—'} | {round(float(x.size_points.max()),1) if len(x) else '—'} |")
    lines+=["","## B. Could we enter BEFORE the move?","",
        "From each completed 1H close, evaluate both sides against the next 24/48h on 1M OHLC:",
        "Reach +2,000 or +5,000 BTC points before −1,000; if same minute, loss first.",
        "This is **not** realized trade P&L. Every hourly candidate, including failures, is counted.",
        "Comparison split: March–August vs September–December 2025. Both are previously studied data.",
        "",
    ]
    for pname in ("Mar-Aug_2025","Sep-Dec_2025","All_Mar_Dec"):
        lines += [f"### {pname} — Weekdays IST only","",
            "| Completed-bar signal | Candidates | +2,000 first / 48h | +5,000 first / 48h |",
            "|---|---:|---:|---:|"]
        for cond,r in stats[pname]["weekdays_IST"].items():
            lines.append(f"| {cond} | {r['opportunities']} | {r['rate2000_48h_pct']}% ({r['hit2000_48h']}) | {r['rate5000_48h_pct']}% ({r['hit5000_48h']}) |")
        lines.append("")
    lines+=["## C. Did our signal occur early in a real trend leg?","",
        "Within the first 25% of each retrospectively labelled leg (no future data in the signal itself).",
        "| Causal condition | 2,000+ legs captured | 5,000+ legs captured |",
        "|---|---:|---:|"]
    for cond in CONDITIONS[1:]:
        a=cover["2000"]["conditions"][cond]
        b=cover["5000"]["conditions"][cond]
        lines.append(f"| {cond} | {a['detected_early']}/{cover['2000']['legs']} ({a['pct']}%) | {b['detected_early']}/{cover['5000']['legs']} ({b['pct']}%) |")
    lines+=["","## D. Monthly confirmed 2,000+ / 5,000+ trend legs","",
        "| Month | ≥2,000 pts | ≥5,000 pts |",
        "|---|---:|---:|"]
    for mo in [f"2025-{i:02d}" for i in range(3,13)]:
        a=legs[legs.month==mo]
        lines.append(f"| {mo} | {int((a.size_points>=2000).sum())} | {int((a.size_points>=5000).sum())} |")
    lines+=["","## Interpretation / limits",
        "- Pivot catalogue is hindsight. The causal signal quality is evaluated separately from every eligible hour and BOTH sides.",
        "- No trade is assumed to start at an ex-post pivot; a signal must exist before an outcome window.",
        "- All 2025 is development/previously observed data, including the later-year consistency split.",
        "- Stronger conditional success is not evidence of profitability without exclusive, real entry/exit replay after costs.",
        "- No lookahead into 2026, funding, bid/ask, fills or liquidation modeled.",
        "- Do not promote a condition to a trading strategy unless it beats the baseline and survives an execution backtest.",""]
    return "\n".join(lines)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--data-dir",type=Path,default=Path("data/delta_india/BTCUSD/1m"))
    parser.add_argument("--output-dir",type=Path,default=Path("analysis/v8_2025_behavior"))
    args=parser.parse_args()
    m=load_2025(args.data_dir)
    legs=trend_legs(m)
    if legs.empty: raise RuntimeError("No confirmed 2025 legs")
    h=hourly_features(m)
    opportunities=label_candidates(h,m)
    stats,coverage=evaluate(opportunities,legs)
    result={
        "period":"2025-03-01 to 2025-12-31, no 2026 candles",
        "source":"Delta India BTCUSD 1min futures OHLCV",
        "leg_confirmation_reversal_points":REVERSAL,
        "risk_barrier_points":RISK,
        "opportunity_rows":len(opportunities),
        "trend_leg_counts":{str(t):int((legs.size_points>=t).sum()) for t in TARGETS},
        "cohort_signal_quality":stats,
        "early_leg_coverage":coverage,
    }
    args.output_dir.mkdir(parents=True,exist_ok=True)
    legs.to_csv(args.output_dir/"v8_confirmed_legs.csv",index=False)
    opportunities.to_csv(args.output_dir/"v8_hourly_opportunities.csv",index=False)
    (args.output_dir/"v8_summary.json").write_text(json.dumps(result,indent=2)+"\n")
    r=make_report(legs,opportunities,stats,coverage)
    (args.output_dir/"V8_RESEARCH_REPORT.md").write_text(r+"\n")
    print(r)
    print("Research complete. Files:",args.output_dir)

if __name__=="__main__":
    main()
