#!/usr/bin/env python3
"""V7: completed-4H-structure + completed-1H-acceptance, 2025-only study.

Event labeling, NOT an executable strategy or net-P&L backtest.
Target: +1000 BTC points before -500 adverse points within 24h/48h.
Signals use only fully closed hourly and four-hourly candles.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

START = pd.Timestamp("2025-03-01T00:00:00Z")
END = pd.Timestamp("2026-01-01T00:00:00Z")
TARGET, ADVERSE = 1000., 500.

def load(data_dir: Path) -> pd.DataFrame:
    parts = []
    for month in range(1, 13):
        path = data_dir / f"2025-{month:02d}.csv.gz"
        if not path.exists():
            raise FileNotFoundError(path)
        a = pd.read_csv(path, compression="gzip",
                        usecols=["time","open","high","low","close","volume"])
        a["time"] = pd.to_datetime(a.time.astype("int64"), unit="s", utc=True)
        parts.append(a.set_index("time"))
    f = pd.concat(parts).sort_index()
    assert len(f) == 365*24*60, f"Unexpected rows: {len(f)}"
    assert f.index.is_unique
    assert f.index.min() == pd.Timestamp("2025-01-01T00:00:00Z")
    assert f.index.max() == END-pd.Timedelta(minutes=1)
    assert (f.index[1:]-f.index[:-1] == pd.Timedelta(minutes=1)).all()
    assert f[["open","high","low","close","volume"]].notna().all().all()
    return f

def aggregate(f: pd.DataFrame, frequency: str, expected_count: int):
    ohlcv = f.resample(frequency, label="right", closed="left").agg(
        open=("open","first"), high=("high","max"), low=("low","min"),
        close=("close","last"), volume=("volume","sum"))
    counts = f.close.resample(frequency, label="right", closed="left").count()
    assert counts.eq(expected_count).all(), f"Incomplete {frequency} candles"
    return ohlcv

def context(h: pd.DataFrame, f: pd.DataFrame) -> pd.DataFrame:
    f = f.copy()
    f["bull"] = ((f.high > f.high.shift(1)) & (f.low > f.low.shift(1)) &
                 (f.high.shift(1) > f.high.shift(2)) &
                 (f.low.shift(1) > f.low.shift(2)))
    f["bear"] = ((f.high < f.high.shift(1)) & (f.low < f.low.shift(1)) &
                 (f.high.shift(1) < f.high.shift(2)) &
                 (f.low.shift(1) < f.low.shift(2)))
    h = h.copy()
    h["prior12_high"] = h.high.shift(1).rolling(12,min_periods=12).max()
    h["prior12_low"] = h.low.shift(1).rolling(12,min_periods=12).min()
    rng = (h.high-h.low).replace(0,np.nan)
    h["close_location"] = (h.close-h.low)/rng
    prev = h.close.shift(1)
    tr = pd.concat([h.high-h.low,(h.high-prev).abs(),(h.low-prev).abs()],axis=1).max(axis=1)
    h["atr14"] = tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    h["body_atr"] = (h.close-h.open).abs()/h.atr14.replace(0,np.nan)
    for name in ("bull","bear"):
        # 4h index labels are at candle END, so forward-fill only completed bars.
        h[name] = f[name].reindex(h.index,method="ffill").fillna(False).astype(bool)
    h["long_accept"] = (h.close>h.prior12_high) & (h.close_location>=0.75) & (h.close>h.open)
    h["short_accept"] = (h.close<h.prior12_low) & (h.close_location<=0.25) & (h.close<h.open)
    return h

def path_outcome(h: pd.DataFrame, i: int, side: int, duration: int):
    entry=float(h.iloc[i+1].open)
    highwater=0.; lowwater=0.; hit="NONE"; hit_hour=None
    for age,bar in enumerate(h.iloc[i+1:i+duration+1].itertuples(index=False),1):
        favorable=(float(bar.high)-entry) if side==1 else (entry-float(bar.low))
        adverse=(entry-float(bar.low)) if side==1 else (float(bar.high)-entry)
        highwater=max(highwater,favorable)
        lowwater=max(lowwater,adverse)
        if hit=="NONE":
            if adverse>=ADVERSE: hit="ADVERSE_FIRST";hit_hour=age
            elif favorable>=TARGET: hit="TARGET_FIRST";hit_hour=age
    return entry,highwater,lowwater,hit,hit_hour

def detect(h: pd.DataFrame):
    out=[]
    for i in range(len(h)):
        ts=h.index[i]
        if ts<START or ts>=END: continue
        if i+48>=len(h): continue  # Never read an hour from 2026.
        z=h.iloc[i]
        for side,accept,structure in ((1,"long_accept","bull"),(-1,"short_accept","bear")):
            if not bool(z[accept]): continue
            for duration in (24,48):
                entry,fav,adv,hit,age=path_outcome(h,i,side,duration)
                out.append(dict(signal_utc=ts.isoformat(),month=ts.strftime("%Y-%m"),
                    side="LONG" if side==1 else "SHORT",horizon_h=duration,
                    four_h_structure=bool(z[structure]),body_ge_0_4_atr=bool(z.body_atr>=0.4),
                    close_location=round(float(z.close_location),4),
                    atr14_1h=round(float(z.atr14),2),
                    next_hour_open=entry,
                    favorable_high_watermark_points=round(fav,1),
                    adverse_high_watermark_points=round(adv,1),
                    first_hit=hit,first_hit_hour=age,target_before_adverse=(hit=="TARGET_FIRST")))
    return pd.DataFrame(out)

def summarize(e: pd.DataFrame):
    cohorts={
        "breakout_acceptance_all":pd.Series(True,index=e.index),
        "breakout_and_4h_structure":e.four_h_structure,
        "breakout_structure_and_body":e.four_h_structure & e.body_ge_0_4_atr
    }
    def summary(x):
        return {"signals":len(x),"reached_target_before_adverse":int(x.target_before_adverse.sum()),
            "event_success_pct":round(100*x.target_before_adverse.mean(),2) if len(x) else None}
    results={"period":"2025-03-01 through 2025-12-31 (last 48h censored)",
        "target_pts":TARGET,"adverse_pts":ADVERSE,
        "warning":"This is event labeling, not a trading backtest or profitability claim",
        "cohorts":{},"monthly":{}}
    for key,mask in cohorts.items():
        results["cohorts"][key]={str(h):summary(e[mask & (e.horizon_h==h)])
                                  for h in (24,48)}
    for month in pd.period_range("2025-03","2025-12",freq="M"):
        name=str(month)
        results["monthly"][name]={
            key:summary(e[mask & (e.horizon_h==24) & (e.month==name)])
            for key,mask in cohorts.items()}
    return results

def report(s):
    lines=["# V7 — 2025 BTC structural trend research","",
        "**Research only: event labels, not realized trades. No 2026 data used.**","",
        "Signal: completed 1H close beyond 12 preceding completed 1H bars, closing in the outer 25% of candle range.",
        "Confirmation: two successive fully completed 4H higher-high/higher-low (LONG), or lower-high/lower-low (SHORT) candles.",
        "Variant: breakout body >= 0.4 x completed 1H ATR14.",
        "Outcome: next hourly OPEN reference; +1,000 favorable points before -500 adverse, within 24/48 hours. If both levels hit in one hour, count adverse first.",
        "Last 48 hours of December are censored because reading January 2026 is forbidden.","",
        "## Detection by cohort","",
        "| Cohort | 24h signals | 24h hits | 24h % | 48h signals | 48h hits | 48h % |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for key,v in s["cohorts"].items():
        a=v["24"];b=v["48"]
        lines.append(f"| {key} | {a['signals']} | {a['reached_target_before_adverse']} | {a['event_success_pct']} | {b['signals']} | {b['reached_target_before_adverse']} | {b['event_success_pct']} |")
    lines+=["","## Monthly 24h detection","",
        "| Month | Acceptance hits / signals | 4H structure hits / signals | 4H + body hits / signals |",
        "|---|---:|---:|---:|"]
    for month,groups in s["monthly"].items():
        vals=[groups[k] for k in ("breakout_acceptance_all","breakout_and_4h_structure","breakout_structure_and_body")]
        lines.append("| "+month+" | "+" | ".join(f"{v['reached_target_before_adverse']}/{v['signals']} ({v['event_success_pct']}%)" for v in vals)+" |")
    lines+=["","## Limitations",
        "- Signals can overlap; event-hit rate is not a real strategy win rate.",
        "- No fee, slippage, funding, account sizing, portfolio overlap, or exchange fill modeling.",
        "- 1H intrabar stop/target ambiguity scored adverse-first.",
        "- Must build and backtest executable rules before any profitability conclusion.",""]
    return "\n".join(lines)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--data-dir",type=Path,default=Path("data/delta_india/BTCUSD/1m"))
    parser.add_argument("--output-dir",type=Path,default=Path("analysis/v7_2025"))
    args=parser.parse_args()
    minute=load(args.data_dir)
    hour=aggregate(minute,"1h",60); four=aggregate(minute,"4h",240)
    events=detect(context(hour,four))
    if events.empty: raise RuntimeError("No acceptance events found")
    result=summarize(events)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/"v7_event_summary.json").write_text(json.dumps(result,indent=2)+"\n")
    events.to_csv(args.output_dir/"v7_event_ledger.csv",index=False)
    markdown=report(result)
    (args.output_dir/"V7_RESEARCH_REPORT.md").write_text(markdown+"\n")
    print(markdown)
    print("Artifacts:",args.output_dir)

if __name__=="__main__":
    main()
