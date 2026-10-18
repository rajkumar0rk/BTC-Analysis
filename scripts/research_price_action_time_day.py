#!/usr/bin/env python3
"""Research price-action BTCUSD strategies combined with NY time/day windows.

Input: 1m Delta India BTCUSD history. Signals from fully closed 5m bars.
No hindsight levels: overnight/opening levels used only after their windows;
previous NY day levels are shifted to the following day; lookbacks shifted.
Training 2025; validation Jan-Jun 2026; final holdout Jul-Oct 17 2026.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path("data/delta_india/BTCUSD/1m")
OUT = Path("analysis/price_action_time_day")
TRAIN_END = pd.Timestamp("2026-01-01", tz="UTC")
VALID_END = pd.Timestamp("2026-07-01", tz="UTC")
FEE_RATE = 0.0005 * 1.18  # per side, taker fee including GST
SLIP_POINTS = 5.0  # adverse slippage per side, assumed
EXITS = {
    "tp300_sl250_2h": ("fixed", 300, 250, 120),
    "tp500_sl350_4h": ("fixed", 500, 350, 240),
    "tp1000_sl500_8h": ("fixed", 1000, 500, 480),
    "time2h_sl400": ("time", None, 400, 120),
    "time4h_sl500": ("time", None, 500, 240),
    "trail350_after500_8h": ("trail", None, 500, 480),
}
DAY_GROUPS = ["ALL", "WEEKDAYS", "WEEKENDS", "MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

def load():
    frames = []
    files = sorted(DATA.glob("20??-??.csv.gz"))
    if not files:
        raise RuntimeError("No Delta India 1m candles")
    for filename in files:
        f = pd.read_csv(filename, compression="gzip", usecols=["time", "open", "high", "low", "close", "volume"])
        f["time"] = pd.to_datetime(f.time.astype("int64"), unit="s", utc=True)
        frames.append(f)
    a = pd.concat(frames, ignore_index=True).set_index("time").sort_index()
    if a.index.has_duplicates or a.isna().any().any():
        raise ValueError("Missing, null or duplicate 1m records")
    gaps = a.index.to_series().diff().iloc[1:]
    if not gaps.eq(pd.Timedelta(minutes=1)).all():
        raise ValueError("Non-consecutive 1m history; no synthetic bars")
    return a, len(files)

def resample_5m(one):
    ct = one.close.resample("5min", label="left", closed="left").count()
    b = one.resample("5min", label="left", closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    return b[ct == 5].copy()

def add_prior_levels(b):
    ny = b.index.tz_convert("America/New_York")
    b["day"] = [str(x) for x in ny.date]
    b["dow"] = ny.dayofweek
    b["clock"] = ny.hour * 60 + ny.minute
    b["session"] = np.select(
        [(b.clock >= 1140) | (b.clock < 180),
         b.clock < 570, b.clock < 690, b.clock < 960],
        ["ASIA_EVENING", "LONDON_EARLY", "US_OPEN", "US_AFTERNOON"],
        default="NY_EVENING")
    # Previous NY calendar day's *completed* high/low.
    daily = b.groupby("day", sort=True).agg(high=("high","max"),low=("low","min"))
    prior = daily.shift(1).reindex(b.day)
    b["prior_day_high"] = prior.high.to_numpy()
    b["prior_day_low"] = prior.low.to_numpy()

    overnight = b[(b.clock >= 0) & (b.clock < 570)].groupby("day").agg(
        high=("high","max"),low=("low","min"),count=("close","size"))
    o = overnight.reindex(b.day)
    # Overnight range is valid ONLY after 09:30 NY; no future data leakage.
    valid_overnight = (b.clock >= 570) & (o["count"].to_numpy() >= 95)
    b["overnight_high"] = np.where(valid_overnight,o.high.to_numpy(),np.nan)
    b["overnight_low"] = np.where(valid_overnight,o.low.to_numpy(),np.nan)

    opening = b[(b.clock >= 570) & (b.clock < 600)].groupby("day").agg(
        high=("high","max"),low=("low","min"),count=("close","size"))
    p = opening.reindex(b.day)
    # Opening range includes 09:30 through 09:55 5m candles; known at 10:00.
    valid_open = (b.clock >= 600) & (p["count"].to_numpy() == 6)
    b["opening_high"] = np.where(valid_open,p.high.to_numpy(),np.nan)
    b["opening_low"] = np.where(valid_open,p.low.to_numpy(),np.nan)

    # Previous completed 5-minute lookbacks, not including signal candle.
    for n in (6, 12, 24):
        b[f"high{n}"] = b.high.rolling(n,min_periods=n).max().shift(1)
        b[f"low{n}"] = b.low.rolling(n,min_periods=n).min().shift(1)
    b["median_range"] = (b.high-b.low).rolling(36,min_periods=36).median().shift(1)
    b["compression_width"] = (b.high.rolling(6,min_periods=6).max() -
                               b.low.rolling(6,min_periods=6).min()).shift(1)
    b["median_6_width"] = (b.high.rolling(6,min_periods=6).max() -
                           b.low.rolling(6,min_periods=6).min()).rolling(72,min_periods=72).median().shift(1)
    return b

def discover_signals(b):
    c=b.close
    o=b.open
    high=b.high
    low=b.low
    prev_c=c.shift(1)
    body=(c-o).abs()/(high-low).replace(0,np.nan)
    impulse=(body>=0.65)&((high-low)>=1.5*b.median_range)
    narrower=(b.compression_width < 0.65*b.median_6_width)
    signals={}
    # BUY/SHORT after 5m range BREAK close, not wick-only crossing.
    def level(name,hi,lo):
        signals[name+"_accept"]=(
            (c>hi)&(prev_c<=hi),
            (c<lo)&(prev_c>=lo))
        signals[name+"_sweep_reject"]=(
            (low<lo)&(c>lo)&(c>o),
            (high>hi)&(c<hi)&(c<o))
        # Reclaim/rejection after prior candle CLOSED beyond the level.
        signals[name+"_failed_break"]=(
            (prev_c<lo)&(c>lo)&(c>o),
            (prev_c>hi)&(c<hi)&(c<o))
    level("prev_day",b.prior_day_high,b.prior_day_low)
    level("overnight",b.overnight_high,b.overnight_low)
    level("opening30",b.opening_high,b.opening_low)

    signals["local_1h_break_accept"]=((c>b.high12)&(prev_c<=b.high12)&impulse,
                                       (c<b.low12)&(prev_c>=b.low12)&impulse)
    signals["local_2h_sweep_reject"]=((low<b.low24)&(c>b.low24)&(c>o),
                                      (high>b.high24)&(c<b.high24)&(c<o))
    signals["compression_ignite"]=(
        narrower&(c>b.high6)&impulse&(c>o),
        narrower&(c<b.low6)&impulse&(c<o))
    # Confirmation of a 5m sweep ONLY on next completed candle; side is reversal.
    prior_sweep_up=(low.shift(1)<b.low24.shift(1))&(c.shift(1)>b.low24.shift(1))
    prior_sweep_dn=(high.shift(1)>b.high24.shift(1))&(c.shift(1)<b.high24.shift(1))
    signals["sweep_nextbar_confirm"]=(
        prior_sweep_up&(c>c.shift(1))&(c>o),
        prior_sweep_dn&(c<c.shift(1))&(c<o))
    # No EMA / RSI / ATR inputs: purely OHLC-derived.
    events=[]
    for setup,(longs,shorts) in signals.items():
        direction=(longs.fillna(False).astype("int8")-shorts.fillna(False).astype("int8")).to_numpy()
        fired=np.flatnonzero(direction)
        seen=set()
        for i in fired:
            side=int(direction[i])
            if side not in (-1,1):continue
            date=b.day.iat[i]
            session=b.session.iat[i]
            key=(date,session)
            # One first signal per setup per local day and session, to prevent
            # highly correlated events being mistaken for independent trades.
            if key in seen:continue
            at=b.index[i]+pd.Timedelta(minutes=5)
            seen.add(key)
            events.append({
                "setup":setup,"ny_date":date,"weekday":int(b.dow.iat[i]),
                "session":session,"signal_end_utc":str(at),
                "entry_utc":at,"side":side})
    return pd.DataFrame(events).sort_values("entry_utc").reset_index(drop=True)

def simulate(one,events):
    idx=one.index
    op=one.open.to_numpy(dtype=float)
    hi=one.high.to_numpy(dtype=float)
    lo=one.low.to_numpy(dtype=float)
    close=one.close.to_numpy(dtype=float)
    results=[]
    for event in events.itertuples(index=False):
        pos=int(idx.searchsorted(event.entry_utc))
        if pos >= len(idx) or idx[pos] != event.entry_utc or pos+480>len(idx):continue
        side=int(event.side)
        entry_raw=op[pos]
        period=("train" if event.entry_utc<TRAIN_END else
                "validation" if event.entry_utc<VALID_END else "holdout")
        for exitname,(kind,target_distance,stop_distance,limit) in EXITS.items():
            stop=entry_raw-side*stop_distance
            target=(entry_raw+side*target_distance if target_distance is not None else np.nan)
            exit_raw=float(close[pos+limit-1])
            cause="timeout"
            held=limit
            best=entry_raw
            for k in range(limit):
                ix=pos+k
                # A gap beyond stop uses OPEN, not an overly optimistic stop fill.
                hit_stop=(lo[ix]<=stop if side>0 else hi[ix]>=stop)
                hit_tp=(hi[ix]>=target if side>0 else lo[ix]<=target) if target_distance is not None else False
                if hit_stop:
                    exit_raw=min(float(op[ix]),stop) if side>0 else max(float(op[ix]),stop)
                    held=k+1
                    cause="stop"
                    break
                if hit_tp:
                    exit_raw=target
                    held=k+1
                    cause="target"
                    break
                if kind=="trail":
                    best=max(best,hi[ix]) if side>0 else min(best,lo[ix])
                    if side*(best-entry_raw)>=500:
                        updated=best-side*350
                        stop=max(stop,updated) if side>0 else min(stop,updated)
                        # Updated stop becomes active at NEXT one-minute candle.
            entry_fill=entry_raw+side*SLIP_POINTS
            exit_fill=exit_raw-side*SLIP_POINTS
            gross=side*(exit_fill-entry_fill)
            fees=FEE_RATE*(entry_fill+exit_fill)
            net=gross-fees
            results.append({"setup":event.setup,"ny_date":event.ny_date,
                "weekday":event.weekday,"session":event.session,
                "entry_utc":str(event.entry_utc),"side":side,
                "exit":exitname,"period":period,"exit_reason":cause,
                "hold_min":held,"gross_points":round(gross,3),
                "fees_points":round(fees,3),"net_points":round(net,3)})
    return pd.DataFrame(results)

def grouped_summary(trades):
    records=[]
    for group in DAY_GROUPS:
        if group=="ALL":x=trades
        elif group=="WEEKDAYS":x=trades[trades.weekday<5]
        elif group=="WEEKENDS":x=trades[trades.weekday>=5]
        else:x=trades[trades.weekday==WEEKDAYS.index(group)]
        if x.empty:continue
        for (setup,session,exit,period),f in x.groupby(["setup","session","exit","period"],observed=True):
            vals=f.net_points.to_numpy(dtype=float)
            vcount=len(vals)
            records.append({"setup":setup,"session":session,"exit":exit,"period":period,
                "day_group":group,"n":vcount,"mean_net":round(float(vals.mean()),2),
                "median_net":round(float(np.median(vals)),2),
                "std_net":round(float(vals.std(ddof=1)),2) if vcount>1 else np.nan,
                "win_pct":round(100*float((vals>0).mean()),2),
                "net200_pct":round(100*float((vals>=200).mean()),2),
                "net500_pct":round(100*float((vals>=500).mean()),2),
                "stop_pct":round(100*float((f.exit_reason=="stop").mean()),2)})
    return pd.DataFrame(records)

def validate_and_rank(stats):
    idcols=["setup","session","exit","day_group"]
    data=stats.pivot(index=idcols,columns="period",
        values=["n","mean_net","std_net","win_pct","net200_pct"])
    data.columns=[f"{item}_{period}" for item,period in data.columns]
    data=data.reset_index()
    for period in ("train","validation","holdout"):
        for name in ("n","mean_net","std_net","win_pct","net200_pct"):
            column=f"{name}_{period}"
            if column not in data.columns:data[column]=np.nan
    broad=data.day_group.isin(["ALL","WEEKDAYS"])
    is_weekend=data.day_group=="WEEKENDS"
    min_train=np.where(broad,80,np.where(is_weekend,35,30))
    min_validation=np.where(broad,35,np.where(is_weekend,15,14))
    min_holdout=np.where(broad,20,np.where(is_weekend,9,8))
    eligible=(data.n_train>=min_train)&(data.n_validation>=min_validation)&(data.n_holdout>=min_holdout)
    data=data[eligible].copy()
    data["se_train"]=data.std_net_train/np.sqrt(data.n_train)
    data["se_validation"]=data.std_net_validation/np.sqrt(data.n_validation)
    data["train_lower"]=data.mean_net_train-1.96*data.se_train
    data["validation_lower"]=data.mean_net_validation-1.96*data.se_validation
    data["score"]=np.minimum(data.train_lower,data.validation_lower)
    data["two_period_positive"]=(data.mean_net_train>0)&(data.mean_net_validation>0)
    data["two_period_lower_positive"]=(data.train_lower>0)&(data.validation_lower>0)
    ranked=data.sort_values("score",ascending=False)
    # Prefer candidates positive in both discovery periods, never select
    # candidates based on holdout outcome.
    candidates=ranked[ranked.two_period_positive].head(20).copy()
    if candidates.empty:candidates=ranked.head(20).copy()
    return data,ranked,candidates

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    one,files=load()
    candles=add_prior_levels(resample_5m(one))
    signals=discover_signals(candles)
    trades=simulate(one,signals)
    if len(trades)==0:raise RuntimeError("No testable signals")
    stats=grouped_summary(trades)
    eligible,ranked,candidates=validate_and_rank(stats)
    quality={
        "exchange":"Delta Exchange India","symbol":"BTCUSD perpetual",
        "source_month_files":files,"native_1m_candles":len(one),
        "derived_5m_candles":len(candles),"zero_volume_minutes":int((one.volume==0).sum()),
        "signal_events":len(signals),"exit_replays":len(trades),
        "setup_count":signals.setup.nunique(),
        "eligible_rules":len(eligible),
        "two_period_positive_rules":int(eligible.two_period_positive.sum()),
        "two_period_lower_positive_rules":int(eligible.two_period_lower_positive.sum()),
        "train":"2025","validation":"2026-01 through 2026-06",
        "holdout":"2026-07-01 through 2026-10-17",
        "fees":"0.05% per side taker + 18% GST on fee; $5 slippage each side",
        "selection":"Training and validation only, never final holdout"}
    signals.to_csv(OUT/"price_action_signals.csv",index=False)
    trades.to_csv(OUT/"all_exit_trades.csv",index=False)
    stats.to_csv(OUT/"time_day_breakdown.csv",index=False)
    ranked.to_csv(OUT/"ranked_rules_preholdout.csv",index=False)
    candidates.to_csv(OUT/"preselected_candidates.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n",encoding="utf-8")
    display=["setup","session","day_group","exit","n_train","mean_net_train",
        "n_validation","mean_net_validation","n_holdout","mean_net_holdout",
        "win_pct_holdout","score"]
    report=[
        "# BTC Futures: price-action strategies + time-of-day + weekday filters",
        "",
        "## Data and design",
        "Original Delta Exchange India BTCUSD perpetual 1m OHLCV, resampled to 5m only for completed-price-structure signals.",
        "Signals after 5m close; entry at following 1m OPEN. Levels are based on previously completed bars, previous calendar day, completed overnight or completed NY 09:30-10:00 opening range.",
        "Entry families: previous day high/low acceptance, sweeps and failed breakouts; overnight range acceptance, sweeps and failed breakouts; NY opening 30m acceptance, sweeps and failed breakouts; recent 1h breakout, 2h sweep, 30m compression/ignition, and sweep-confirmation.",
        "Time windows (America/New_York DST aware): ASIA_EVENING=19:00-03:00; LONDON_EARLY=03:00-09:30; US_OPEN=09:30-11:30; US_AFTERNOON=11:30-16:00; NY_EVENING=16:00-19:00.",
        "Weekday subsets: all, weekdays/weekends, each Monday–Sunday. Only first setup occurrence per session per NY date (to reduce correlation).",
        "Exit variations: +300/-250 in 2h; +500/-350 in 4h; +1000/-500 in 8h; time 2h / -400 stop; time 4h / -500 stop; trailing 350 only once price first moves +500, 8h cap.",
        "All results are BTC **price points**, not account P&L. They include assumed round-trip taker fees and GST plus adverse $5 slippage per side. No funding, realized bid/ask or market impact.",
        "Train=2025, validation=Jan-Jun 2026, final untouched holdout=Jul-Oct 17 2026. Candidate ranking uses ONLY train and validation.",
        "The exploratory 1.96-standard-error lower bound is NOT multiple-testing adjusted; apparent winners still require later independent forward testing and realistic execution replay.",
        "",
        "## Data quality",
        "~~~json",json.dumps(quality,indent=2),"~~~",
        "",
        "## Candidates selected without seeing holdout",
        candidates[display].to_markdown(index=False) if len(candidates) else "No rules met minimum samples.",
        "",
        "## Strongest pre-holdout rules",
        ranked.head(35)[display].to_markdown(index=False) if len(ranked) else "No rules.",
        "",
        "## Interpretation",
        "Look for agreement across all three chronological periods, sufficient sample sizes, and positive expectancy after costs; a high win rate alone is not an edge.",
        "Repeated variants on the same date are correlated, and selected trade results do not prove institutional order flow.",
        "Do NOT optimize using Jul-Oct data then label it out-of-sample; do not force daily trades.",
        "This is research, not a live strategy or a promise of daily 200–500 points.",
        "",
        "## Reproducibility",
        "See scripts/research_price_action_time_day.py, price_action_signals.csv, all_exit_trades.csv, time_day_breakdown.csv and ranked_rules_preholdout.csv."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("RESEARCH COMPLETE",json.dumps(quality))
    print(candidates[display].to_string(index=False))
if __name__=="__main__":
    main()
