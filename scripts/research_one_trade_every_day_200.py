#!/usr/bin/env python3
"""BTCUSD one-trade-EVERY-day objective with gross +200 and net +200 scenarios.

Distinct from selective strategies: ALL New York dates with complete usable
data MUST produce exactly one entry per strategy. No cherry-picked no-trade days.
Selection uses 2025/Jan-Jun 2026, Jul-Oct 2026 holdout never selects rules.
"""
from pathlib import Path
import json
import math
import numpy as np
import pandas as pd

SRC=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/one_daily_trade_200_points")
TRAIN=pd.Timestamp("2026-01-01",tz="UTC")
HOLD=pd.Timestamp("2026-07-01",tz="UTC")
NY="America/New_York"
SLIP=5.0
FEE=0.0005*1.18
STOPS=(150,250,400)
HOLDS=(60,180,480)
TARGETS=("gross200","net200")
CLOCKS=("00:05","03:05","06:05","08:35","09:35","10:05","11:05","12:05","14:05","18:05")
DIRECTIONS=("last5_follow","last15_follow","last60_follow","last240_follow",
            "last5_fade","last15_fade","last60_fade","last240_fade")
EVENT_TYPES=("opening_impulse","opening_24bar_break","opening_24bar_sweep",
             "opening_strong_reversal")
def load():
    files=sorted(SRC.glob("20??-??.csv.gz"))
    if not files:raise RuntimeError("Missing Delta India 1m data")
    acc=[]
    for file in files:
        a=pd.read_csv(file,compression="gzip",usecols=["time","open","high","low","close","volume"])
        a["time"]=pd.to_datetime(a.time.astype("int64"),unit="s",utc=True)
        acc.append(a)
    d=pd.concat(acc,ignore_index=True).set_index("time").sort_index()
    if d.index.has_duplicates or d.isna().any().any():raise ValueError("Invalid raw OHLCV")
    if not d.index.to_series().diff().iloc[1:].eq(pd.Timedelta(minutes=1)).all():
        raise ValueError("A minute is missing in the original exchange feed")
    return d,len(files)

def minutes_of_day(d):
    local=d.index.tz_convert(NY)
    strings=np.asarray([str(x) for x in local.date])
    time=np.asarray(local.hour*60+local.minute)
    # Demand both NY midnight and 23:59 for a FULL NY calendar day.
    # DST 23/25 hour days are valid; do not rely on 1440-minute count.
    z=pd.DataFrame({"day":strings,"clock":time})
    agg=z.groupby("day").clock.agg(["min","max"])
    whole=set(agg.index[(agg["min"]==0)&(agg["max"]==1439)])
    dates=np.array(sorted(whole))
    # Ignore final days not known in full. Excludes partial first and last NY dates.
    last_index_by_day=z.groupby("day",sort=False).apply(
        lambda x:int(x.index.max()),include_groups=False).to_dict()
    return local,strings,time,dates,last_index_by_day

def get_side(o,c,i,window,invert=False):
    # Last completed window minutes only. Every signal uses information before i.
    if i<window:return 0
    delta=c[i-1]-o[i-window]
    if delta==0:return 0
    return (1 if delta>0 else -1)*(-1 if invert else 1)

def make_base_entries(d):
    o=d.open.to_numpy(dtype=float); c=d.close.to_numpy(dtype=float)
    h=d.high.to_numpy(dtype=float); l=d.low.to_numpy(dtype=float)
    v=d.volume.to_numpy(dtype=float)
    ny,days,mins,dates,last_by_day=minutes_of_day(d)
    if len(dates)<550:raise RuntimeError("Unexpected shortage of complete New York dates")
    # First 5m candle must be completed before the order at i. Convert 5m start
    # index into signal-available minute i = bar index + 5.
    f=d.resample("5min",closed="left",label="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    n=d.close.resample("5min").count()
    f=f[n==5].dropna()
    prior_hi=f.high.rolling(24,min_periods=24).max().shift(1)
    prior_lo=f.low.rolling(24,min_periods=24).min().shift(1)
    prior_median=(f.high-f.low).rolling(24,min_periods=24).median().shift(1)
    prior_volume=f.volume.rolling(24,min_periods=24).mean().shift(1)
    strong=(f.high-f.low)>1.5*prior_median
    body=(f.close-f.open).abs()/(f.high-f.low).replace(0,np.nan)
    volume=f.volume>prior_volume
    green=f.close>f.open
    red=f.close<f.open
    sweepup=(f.high>prior_hi)&(f.close<prior_hi)&red&volume
    sweepdown=(f.low<prior_lo)&(f.close>prior_lo)&green&volume
    breakoutup=(f.close>prior_hi)&green&strong&volume
    breakoutdn=(f.close<prior_lo)&red&strong&volume
    impulseup=green&strong&volume&(body>0.60)
    impulsedn=red&strong&volume&(body>0.60)
    # Price-action-only, no trading indicators: absolute levels, candle shapes,
    # volume, breakout/rejection and time windows.
    reversedup=(red.shift(1).fillna(False))&impulseup
    reverseddn=(green.shift(1).fillna(False))&impulsedn
    masks={
        "opening_impulse":(impulseup,impulsedn),
        "opening_24bar_break":(breakoutup,breakoutdn),
        "opening_24bar_sweep":(sweepdown,sweepup),
        "opening_strong_reversal":(reversedup,reverseddn)}
    events={}
    for label,(bull,bear) in masks.items():
        z=(bull.astype("int8")-bear.astype("int8")).to_numpy()
        available=f.index+pd.Timedelta(minutes=5)
        pos=d.index.searchsorted(available)
        good=(pos<len(d))
        pos=pos[good];values=z[good]
        # Event must start when NY date is 09:00 - 11:59,
        # and entry is at subsequent 1m open after signal close.
        valid=(mins[pos]>=540)&(mins[pos]<720)&(values!=0)
        mapping={}
        for idx,side in zip(pos[valid],values[valid]):
            day=days[idx]
            if day not in mapping: mapping[day]=(int(idx),int(side))
        events[label]=mapping
    # For every date, schedule at an exact NY wall-clock time.
    by_day={}
    for index,day in enumerate(days):
        if day in last_by_day:
            by_day.setdefault(day,{})[int(mins[index])]=index
    output=[]
    # 1 trade EVERY completed calendar day for each rule.
    for day in dates:
        slots=by_day[day]
        for clock in CLOCKS:
            hh,mm=map(int,clock.split(":"))
            idx=slots.get(hh*60+mm)
            if idx is None:raise RuntimeError(f"Missing clock for {day} {clock}")
            for direction in DIRECTIONS:
                period=int(direction.split("_")[0].replace("last",""))
                side=get_side(o,c,idx,period, direction.endswith("_fade"))
                if not side:side=get_side(o,c,idx,60)
                if not side:side=1
                output.append(dict(day=day,rule=f"clock_{clock}_{direction}",
                    entry_index=int(idx),side=int(side)))
        # Dynamic setup: first actual price-action event in 09:00-12:00,
        # otherwise deterministic 12:05 fallback (prior 60m direction).
        for label in EVENT_TYPES:
            candidate=events[label].get(day)
            if candidate is None:
                entry_idx=slots[12*60+5]
                event_side=get_side(o,c,entry_idx,60)
                if not event_side:event_side=1
                triggered=0
            else:
                entry_idx,event_side=candidate
                triggered=1
            for mode in ("follow","fade"):
                output.append(dict(day=day,rule=f"first_{label}_{mode}_else_1205",
                    entry_index=int(entry_idx),side=int(event_side if mode=="follow" else -event_side),
                    triggered=triggered))
    entries=pd.DataFrame(output)
    assert entries.groupby("rule").day.nunique().eq(len(dates)).all(), "One daily entry missing"
    quality={"calendar":"America/New_York includes DST","full_ny_days":len(dates),
            "first_full_ny_day":str(dates[0]),"last_full_ny_day":str(dates[-1]),
            "entry_rules":int(entries.rule.nunique()),
            "daily_entry_events":int(len(entries))}
    return entries,quality,last_by_day

def price_at_net_target(entry_px,side,desired_net):
    # At raw entry P and raw exit Q:
    # LONG net = (Q-P)-2*SLIP-FEE*(Q+P)
    # SHORT net= (P-Q)-2*SLIP-FEE*(P+Q)
    if side>0:
        return (desired_net+2*SLIP+(1+FEE)*entry_px)/(1-FEE)
    return ((1-FEE)*entry_px-2*SLIP-desired_net)/(1+FEE)

def replay(d,entries,last_idx):
    op=d.open.to_numpy(dtype=float)
    hi=d.high.to_numpy(dtype=float)
    lo=d.low.to_numpy(dtype=float)
    close=d.close.to_numpy(dtype=float)
    rows=[]
    for e in entries.itertuples():
        idx=int(e.entry_index)
        side=int(e.side)
        p=float(op[idx])
        limit_day=int(last_idx[e.day])-idx+1
        if limit_day<=0:raise RuntimeError("Empty day at entry")
        for target_kind in TARGETS:
            take=p+side*200 if target_kind=="gross200" else price_at_net_target(p,side,200)
            for stop in STOPS:
                loss_price=p-side*stop
                for hours in HOLDS:
                    n=min(hours,limit_day)
                    end=idx+n
                    # Numpy path lookups; any same-minute stop/target ambiguity
                    # assigned pessimistically to STOP, no intraminute oracle.
                    high=hi[idx:end]
                    low=lo[idx:end]
                    stop_hit=(low<=loss_price) if side>0 else (high>=loss_price)
                    tp_hit=(high>=take) if side>0 else (low<=take)
                    s=np.flatnonzero(stop_hit)
                    t=np.flatnonzero(tp_hit)
                    a=int(s[0]) if len(s) else n+1
                    b=int(t[0]) if len(t) else n+1
                    if a<=b and a<n:
                        exit_raw=loss_price
                        result="stop"
                        held=a+1
                    elif b<n:
                        exit_raw=take
                        result="target"
                        held=b+1
                    else:
                        exit_raw=float(close[end-1])
                        result="time"
                        held=n
                    fill_entry=p+side*SLIP
                    fill_exit=exit_raw-side*SLIP
                    gross=side*(fill_exit-fill_entry)
                    fees=FEE*(fill_entry+fill_exit)
                    net=gross-fees
                    rows.append((e.day,e.rule,target_kind,stop,hours,
                         "train" if d.index[idx]<TRAIN else "validation" if d.index[idx]<HOLD else "holdout",
                         result,side,idx,held,round(gross,3),round(fees,3),round(net,3)))
    cols=["ny_day","rule","target","stop","max_hold_min","period","outcome",
          "side","entry_index","held_min","gross_points","fees_points","net_points"]
    return pd.DataFrame.from_records(rows,columns=cols)

def describe(replay):
    # Each rule/exit has exactly one trade per day.
    r=replay.copy()
    r["hit"]=r.outcome.eq("target")
    r["winner"]=r.net_points.gt(0)
    r["net200"]=r.net_points.ge(199.9)
    gg=r.groupby(["rule","target","stop","max_hold_min","period"],observed=True).agg(
       days=("ny_day","nunique"),trades=("ny_day","size"),
       targets=("hit","sum"),success_pct=("hit","mean"),
       net200_days=("net200","sum"),net200_pct=("net200","mean"),
       profitable_days=("winner","sum"),profitable_pct=("winner","mean"),
       mean_net=("net_points","mean"),median_net=("net_points","median"),
       cumulative_net=("net_points","sum"),
       mean_hold_min=("held_min","mean"))
    gg=gg.reset_index()
    for col in ("success_pct","net200_pct","profitable_pct"):
        gg[col]=(gg[col]*100).round(2)
    for col in ("mean_net","median_net","cumulative_net","mean_hold_min"):
        gg[col]=gg[col].round(2)
    return gg

def find_candidates(summary,entries,quality):
    fields=["days","trades","targets","success_pct","net200_days","net200_pct",
            "profitable_days","profitable_pct","mean_net","median_net","cumulative_net"]
    table=summary.pivot(index=["rule","target","stop","max_hold_min"],columns="period",values=fields)
    table.columns=[a+"_"+b for a,b in table.columns]
    table=table.reset_index()
    for term in ("train","validation","holdout"):
        if "mean_net_"+term not in table:
            table["mean_net_"+term]=np.nan
    # For every-day strategy require enough coverage in both train, validation
    # and holdout; no missing day selection.
    if len(table)==0:raise RuntimeError("No results")
    good=table[(table.days_train>=330)&(table.days_validation>=165)&
               (table.days_holdout>=90)].copy()
    good["selection_score"]=np.minimum(good.mean_net_train,good.mean_net_validation)
    good["positive_before_holdout"]=(good.mean_net_train>0)&(good.mean_net_validation>0)
    # No holdout metrics influence selection.
    ranked=good.sort_values(["selection_score","success_pct_validation"],
                            ascending=[False,False])
    # Leading non-redundant setup families. Restrict to targets net200 since
    # user cares about 200 points in a single trade after costs.
    net200=ranked[ranked.target=="net200"]
    winners=net200[net200.positive_before_holdout]
    shortlist=(winners.head(20) if len(winners) else net200.head(20)).copy()
    # A fully fixed, all-days example with no selection.
    baseline=summary[(summary.rule=="clock_09:35_last15_follow")&
        (summary.target=="net200")&(summary.stop==250)&(summary.max_hold_min==180)]
    quality["compared_exit_combinations"]=len(table)
    quality["eligible_daily_rule_exit_combinations"]=len(good)
    quality["net200_both_earlier_periods_positive"]=len(winners)
    quality["min_daily_coverage"]="One entry per full New York day per rule"
    return ranked,shortlist,baseline

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    d,files=load()
    entries,quality,last=make_base_entries(d)
    quality.update(months=files,source_bars=len(d),first_utc=str(d.index.min()),
        last_utc=str(d.index.max()),zero_volume_minutes=int((d.volume==0).sum()),
        stop_points=list(STOPS),hold_minutes=list(HOLDS),targets=list(TARGETS),
        fee_model="0.05% taker each side + GST18%; slippage 5 BTC points each side",
        selection="2025 training plus Jan-Jun 2026 validation; Jul-Oct 2026 reserved")
    results=replay(d,entries,last)
    quality["simulated_trades"]=len(results)
    perrule=describe(results)
    ranked,chosen,baseline=find_candidates(perrule,entries,quality)
    # Small auditable daily ledgers for selected and fixed benchmark.
    ids=chosen[["rule","target","stop","max_hold_min"]].drop_duplicates()
    fixed=pd.DataFrame([dict(rule="clock_09:35_last15_follow",target="net200",
        stop=250,max_hold_min=180)])
    selections=pd.concat([ids,fixed],ignore_index=True).drop_duplicates()
    ledgers=results.merge(selections,on=["rule","target","stop","max_hold_min"])
    entries.to_csv(OUT/"one_entry_per_day_rules.csv",index=False)
    perrule.to_csv(OUT/"all_daily_rule_exit_summary.csv",index=False)
    ranked.to_csv(OUT/"ranked_daily_rules_preholdout.csv",index=False)
    chosen.to_csv(OUT/"preselected_daily_candidates.csv",index=False)
    ledgers.to_csv(OUT/"daily_trade_ledger_selected.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n",encoding="utf-8")
    columns=["rule","target","stop","max_hold_min",
             "days_train","success_pct_train","mean_net_train",
             "days_validation","success_pct_validation","mean_net_validation",
             "days_holdout","success_pct_holdout","mean_net_holdout","selection_score"]
    lines=[
        "# One BTCUSD futures trade EVERY day — can it capture 200 points?",
        "",
        "**Exact rule:** one entry on every complete America/New_York calendar day, 7 days/week. A target +200 points from that *one* trade. Both a raw +200 point BTC move and actual +200 net points after modeled fees are tested separately.",
        "A day with a failed target still counts as a trade and a failed day. Never exclude weekends, down days, or unprofitable sessions. Each price-action rule contains a deterministic midday fallback so that each date receives one trade.",
        "",
        "## Execution assumptions",
        "- True Delta India BTCUSD perpetual 1m OHLCV, completed 5m price-action events or past-only closed 5/15/60/240 minute trend.",
        "- Three protective **raw price-point** stops: 150/250/400. Three time-outs: 1h/3h/8h (capped at 23:59 New York to prevent overlapping next-day positions).",
        "- Profit target either **gross200** BTC market move or **net200** (gross target enlarged using entry price to compensate expected entry/exit taker fees, 18% GST on fees, and $5 slippage each side).",
        "- Same-minute TP+SL counts as SL. No lookahead. OHLCV stop/target fills approximate executable orders; funding, book spread beyond slippage, price jumps, liquidation and funding are not simulated.",
        "- Entry direction may be long or short; one opening per NY date. Direction determined by past market movement or 5m structure. Fallback entry uses price data available before 12:05 NY.",
        "- Test time-of-day rules and event-driven price action with a forced daily fallback separately; do not add their results together.",
        "",
        "## Chronological selection",
        "Training: 2025. Intermediate validation: Jan-Jun 2026. FINAL unseen holdout: July-Oct 2026.",
        "Ranking and candidate selection use only first two periods. Many rules => heavy multiple-testing risk. A small positive holdout is not proof of robustness.",
        "",
        "## Quality",
        json.dumps(quality,indent=2),
        "",
        "## Fixed example benchmark (pre-registered, no optimization)",
        "At 09:35 NY, follow the prior completed 15min direction; require +200 NET, $250 raw stop, max 3h.",
        baseline.to_markdown(index=False) if len(baseline) else "Benchmark unavailable.",
        "",
        "## Daily candidate results (selected before unseen holdout)",
        chosen[columns].to_markdown(index=False) if len(chosen) else "No eligible candidate.",
        "",
        "## Interpretation",
        "- The important metric is how often one daily trade NETS 200 points, alongside net expectancy and drawdown.",
        "- It is mathematically impossible for gross TP=200 to produce net +200 if brokerage fees and slippage are positive.",
        "- A 200 BTC-point price change is NOT $200 account profit: 0.001 BTC exposure yields about $0.20 gross.",
        "- A guarantee of +200 every calendar day cannot be established from finite historical data. Any historically lucky strategy needs forward paper validation.",
        "",
        "## Reproducible output",
        "See one_entry_per_day_rules.csv; all_daily_rule_exit_summary.csv; ranked_daily_rules_preholdout.csv; preselected_daily_candidates.csv; daily_trade_ledger_selected.csv.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("DAILY ONE TRADE FINISHED",json.dumps(quality))
    print(chosen[columns].head(15).to_string(index=False))
    print("BASELINE",baseline.to_string(index=False))

if __name__=="__main__":
    main()
