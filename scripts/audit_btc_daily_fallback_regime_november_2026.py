#!/usr/bin/env python3
"""Frozen November 2–20, 2026 BTCUSD audit: 15 daily trades, NO retuning.

Compares two hindsight-only 2025–Oct2026 improved models and old baselines
on November data that were not used in the 8064-configuration grid. Historical
Scalper Offer opt-in remains hypothetical; no real orderbook or funding.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_btc_every_weekday_reset_step1 as base
import research_btc_every_weekday_adaptive_step2 as entries
import research_btc_every_weekday_exit_protection_step3 as exits

OUT=Path("analysis/btc_daily_fallback_regime_step4/november_audit")
NDAYS=pd.date_range("2026-11-02","2026-11-20",freq="B",tz="Asia/Kolkata")
assert len(NDAYS)==15
CASES={
   "old_protected":("follow60","lock050","lock050"),
   "old_static":("follow60","static100","static100"),
   "A_274_winning_days_hindsight":("follow5","lock050","trail075"),
   "B_271_winning_days_hindsight":("follow5","lock050","trail050"),
}
EXIT_TUPLES={
  "static100":(0,1.0,3.0,30,0,0,0),
  "lock050":(1,.5,3.,30,.25,.10,0),
  "trail075":(2,.75,3.,30,.35,.20,0),
  "trail050":(2,.5,3.,30,.35,.20,0),
}

def load_with_nov():
    m=base.load()
    p=base.SOURCE/"2026-11.csv.gz"
    n=pd.read_csv(p,compression="gzip",usecols=["time","open","high","low","close","volume"])
    n["time"]=pd.to_datetime(n.time.astype("int64"),unit="s",utc=True)
    n=n.set_index("time").sort_index()
    assert n.index[0]==pd.Timestamp("2026-11-01T00:00:00Z")
    assert n.index[-1]>=pd.Timestamp("2026-11-22T23:59:00Z")
    allm=pd.concat([m,n],axis=0)
    if (not allm.index.is_unique) or (not allm.index.to_series().diff().iloc[1:].eq(pd.Timedelta(minutes=1)).all()):
        raise AssertionError("Archive time discontinuity")
    if allm.isna().any().any() or ((allm.high<allm[["open","low","close"]].max(axis=1))|
        (allm.low>allm[["open","high","close"]].min(axis=1))|(allm.volume<0)).any():
        raise AssertionError("Invalid future audit OHLC")
    return allm

def determine_entries(m,rule):
    o=m.open.to_numpy(float); c=m.close.to_numpy(float); v=m.volume.to_numpy(float)
    idx=np.empty(len(NDAYS),dtype=np.int64)
    hours=np.empty(len(NDAYS),dtype=np.int8)
    sides=np.empty(len(NDAYS),dtype=np.int8)
    fallback=np.zeros(len(NDAYS),dtype=bool)
    last=[]
    for di,day in enumerate(NDAYS):
        daystart=int(m.index.get_indexer([day.tz_convert("UTC")])[0])
        daylast=int(m.index.get_indexer([(day+pd.Timedelta(minutes=1439)).tz_convert("UTC")])[0])
        if daystart<0 or daylast-daystart!=1439:raise AssertionError("Incomplete November IST day")
        decision=None
        for hour in (18,19,20):
            i=daystart+hour*60
            cl=float(c[i-1]);r5=cl/float(o[i-5])-1
            prev=v[i-105:i-5].reshape(20,5).sum(axis=1)
            ratio=float(np.sum(v[i-5:i])/np.mean(prev)) if np.mean(prev)>0 else 0.
            if ratio>=1.5:
                decision=(i,hour,-entries.direction(r5),False)
                break
        if decision is None:
            hour=21
            i=daystart+hour*60
            pclose=float(c[i-1])
            r5=pclose/float(o[i-5])-1
            r60=pclose/float(o[i-60])-1
            side=entries.direction(r5 if rule=="follow5" else r60)
            decision=(i,hour,side,True)
        i,h,side,usedfb=decision
        idx[di]=i;hours[di]=h;sides[di]=side;fallback[di]=usedfb
        assert i+30<=daylast
        last.append(dict(date_ist=day.strftime("%Y-%m-%d"),hour_ist=int(h),
                         side="LONG" if side==1 else "SHORT",
                         type="FALLBACK" if usedfb else "VOLUME_SIGNAL"))
    assert len(idx)==15 and len({x["date_ist"] for x in last})==15
    return idx,hours,sides,fallback

def exit_config_grid():
    full,names=exits.build_configs()
    subset=[]
    for alias,key in EXIT_TUPLES.items():
        hits=np.flatnonzero(np.all(np.isclose(full,np.array(key,float)),axis=1))
        if len(hits)!=1:raise AssertionError("Exit recipe not in frozen set "+alias)
        subset.append(full[hits[0]])
    return np.asarray(subset,dtype=float),list(EXIT_TUPLES.keys())

def evaluate(path):
    p=np.asarray(path)
    eq=np.cumprod(1+p)
    peak=np.maximum.accumulate(np.r_[1.,eq])[1:]
    return dict(
        daily_trades=len(p),profitable_days=int((p>0).sum()),
        losing_days=int((p<0).sum()),win_days_pct=round(100*float(np.mean(p>0)),2),
        compounded_net_account_return_pct=round(float(100*(eq[-1]-1)),5),
        max_closed_dd_pct=round(float(100*np.max(1-eq/peak)),5),
        worst_day_pct=round(float(100*np.min(p)),5),
        mean_day_pct=round(float(100*np.mean(p)),5))

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=load_with_nov()
    op=m.open.to_numpy(float);hi=m.high.to_numpy(float);lo=m.low.to_numpy(float)
    cfg,cfg_names=exit_config_grid()
    results=[];rows=[]
    for case,(rule,event_exit,fallback_exit) in CASES.items():
        start,hour,side,fb=determine_entries(m,rule)
        raw=exits.run_exit_grid(op,hi,lo,start,hour,side,cfg,base.COST,base.SLIP)
        er,ef,eg,why,elapsed=raw
        ei=cfg_names.index(event_exit)
        fi=cfg_names.index(fallback_exit)
        for mode_i,mode in enumerate(base.MODES):
            d=np.arange(len(NDAYS))
            pi=np.where(fb,fi,ei)
            p=er[d,pi,mode_i];f=ef[d,pi,mode_i]
            points=eg[d,pi];why_i=why[d,pi];time=elapsed[d,pi]
            metric=evaluate(p)
            metric.update(case=case,cost_model=mode,volume_entries=int((~fb).sum()),
                          fallback_entries=int(fb.sum()),
                          total_fees_gst_points=round(float(f.sum()),2),
                          tp=int((why_i==1).sum()),sl=int((why_i==2).sum()),
                          timeout=int((why_i==3).sum()))
            if metric["daily_trades"]!=15:raise AssertionError("Lost November weekday entry")
            results.append(metric)
            for z,day in enumerate(NDAYS):
                rows.append(dict(case=case,cost_model=mode,
                    date_ist=day.strftime("%Y-%m-%d"),entry_hour_ist=int(hour[z]),
                    direction="LONG" if side[z]>0 else "SHORT",
                    signal_type="VOLUME_FADE" if not fb[z] else "FALLBACK",
                    exit_rule=event_exit if not fb[z] else fallback_exit,
                    account_net_pct=100*float(p[z]),
                    gross_price_points=float(points[z]),
                    fees_gst_points=float(f[z]),
                    hold_minutes=int(time[z]),
                    exit_reason="STOP" if why_i[z]==2 else ("TARGET" if why_i[z]==1 else "TIMEOUT")))
    tab=pd.DataFrame(results); daily=pd.DataFrame(rows)
    if len(tab)!=len(CASES)*len(base.MODES) or len(daily)!=len(tab)*15:
        raise AssertionError("Invalid audit dimensions")
    tab.to_csv(OUT/"all_four_frozen_candidates_nov_2026.csv",index=False)
    daily.to_csv(OUT/"all_15_weekday_nov_2026_trades.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(dict(
        purpose="Later-than-Jan2025-Oct2026-grid audit of four FROZEN trading policies",
        sample="2026-11-02 to 2026-11-20 complete Mon-Fri IST dates, 15 trades each",
        comparisons=len(tab),
        no_retraining_or_selection_using_nov=True,
        results=tab.to_dict("records"),
        limitations=["All four policy choices informed by historical pre-November data; choosing A or B after November would create new selection bias",
          "Very short 15-day extension, far too little to prove a durable edge",
          "Offer history/activation not verified, no actual tick-level stop order fills, order book, funding or latency",
          "Side determined only before each 1m entry; trailing only adjusted after closed 1m bar"]),indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
        "# November 2026 later-period audit (not forward paper trading)",
        "","Four strategies, each independently frozen BEFORE inspecting these 15 weekdays.",
        "","## Unchanged results","",tab.to_markdown(index=False),
        "","## All November days","",daily.to_markdown(index=False),
        "","## Interpretation",
        "A or B was previously picked by inspection of the full 22-month 8,064 variant search. This is an additional 15-day chronological sample, NOT a statistically independent proof. The market may change and real order fills may worsen."
    ])+"\n")
    print("NOV_AUDIT_RESULTS "+json.dumps(tab.to_dict("records"),sort_keys=True),flush=True)
    print("NOV_AUDIT_COMPLETE",flush=True)

if __name__=="__main__":
    run()
