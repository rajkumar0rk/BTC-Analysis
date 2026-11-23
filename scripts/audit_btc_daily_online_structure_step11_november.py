#!/usr/bin/env python3
"""November 2026 audit of 2025-selected Step11 daily BTC online fallback.

15 exact IST Mon–Fri entries. On each Nov fallback day, select among 6 arms
using ONLY previous completed fallback days' after-Scalper shadow returns.
The November period had already been inspected for Step8, not pristine.
No model training or selection over November full results.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

import research_btc_every_weekday_reset_step1 as base
import research_btc_daily_causal_regime_step5 as regime
import research_btc_every_weekday_exit_protection_step3 as protection
import research_btc_daily_structure_step10 as structural
import research_btc_daily_online_structure_step11 as study
import audit_btc_daily_fallback_regime_november_2026 as nov

OUT=Path("analysis/btc_daily_online_structure_step11/november_audit")
DAYS=nov.NDAYS
N=15

def nov_structure(m,index,date):
    op=m.open.to_numpy(float)
    hi=m.high.to_numpy(float)
    lo=m.low.to_numpy(float)
    close=m.close.to_numpy(float)
    vol=m.volume.to_numpy(float)
    i=int(index)
    y=float(close[i-1])
    q={"r60":y/float(op[i-60])-1}
    up=float(hi[i-60:i].max());dn=float(lo[i-60:i].min())
    q["position60"]=(y-dn)/(up-dn) if up>dn else .5
    q["sma_gap"]=float(close[i-20:i].mean()/close[i-60:i].mean()-1)
    prev_high=float(hi[i-125:i-5].max())
    prev_low=float(lo[i-125:i-5].min())
    q["donchian_up_margin"]=y/prev_high-1
    q["donchian_dn_margin"]=prev_low/y-1
    sessionstart=date+pd.Timedelta(hours=9)
    start=int(m.index.get_indexer([sessionstart.tz_convert("UTC")])[0])
    assert start>=0 and i>start
    mid=(hi[start:i]+lo[start:i]+close[start:i])/3.
    amounts=vol[start:i]
    total=float(np.sum(amounts))
    av=float(np.dot(mid,amounts)/total) if total>0 else float(np.mean(close[start:i]))
    q["vwap_gap"]=y/av-1
    for key,ver in q.items():
        if not np.isfinite(ver):raise AssertionError("Nonfinite Nov preentry feature "+key)
    return q

def metrics(p):
    eq=np.cumprod(1+p)
    peak=np.maximum.accumulate(np.r_[1.,eq])[1:]
    return dict(trades=len(p),profitable_days=int(np.sum(p>0)),
                losing_days=int(np.sum(p<0)),
                profitable_day_pct=round(float(100*np.mean(p>0)),3),
                compounded_net_pct=round(float(100*(eq[-1]-1)),6),
                max_closed_dd_pct=round(float(100*np.max(1-eq/peak)),6),
                worst_day_pct=round(float(np.min(p)*100),6))

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    # Prior shadow outcomes end in Oct2026, no November data in training.
    prev=study.shadow(base.load())
    oldmask=prev["mask"]
    history=[
        [float(x) for x in prev["returns"]["scalper_offer"][0][d,:]]
        for d in np.flatnonzero(oldmask)
    ]
    assert len(history)==217 and all(len(row)==6 for row in history)
    m=nov.load_with_nov()
    indices,hours,base_side,fall=nov.determine_entries(m,"follow5")
    assert len(indices)==15 and int(np.sum(fall))==6 and int(np.sum(~fall))==9
    cfg,lookup=regime.build_cfg()
    op=m.open.to_numpy(float)
    hi=m.high.to_numpy(float)
    lo=m.low.to_numpy(float)
    rows_long=protection.run_exit_grid(
        op,hi,lo,indices,hours,np.ones(N,dtype=np.int8),cfg,base.COST,base.SLIP)
    rows_short=protection.run_exit_grid(
        op,hi,lo,indices,hours,-np.ones(N,dtype=np.int8),cfg,base.COST,base.SLIP)
    cache={1:rows_long,-1:rows_short}
    volume=m.volume.to_numpy(float)
    ratio=np.ones(N,dtype=float)
    for d,i in enumerate(indices):
        prevvol=volume[i-105:i-5].reshape(20,5).sum(axis=1)
        avg=float(prevvol.mean())
        ratio[d]=float(volume[i-5:i].sum()/avg) if avg>0 else 0.
    def exact(d,side,recipe,fee_mode):
        result=cache[int(side)]
        ci=lookup[recipe]
        mi=base.MODES.index(fee_mode)
        return (float(result[0][d,ci,mi]),
                float(result[1][d,ci,mi]),
                float(result[2][d,ci]),
                int(result[3][d,ci]),
                int(result[4][d,ci]))
    side_arms=np.tile(base_side[:,None],(1,6))
    for d in range(N):
        if not fall[d]:continue
        f=nov_structure(m,indices[d],DAYS[d])
        for a,(_,kind,level) in enumerate(study.ARMS):
            if not a:continue
            override=structural.desired_for(kind,level,f)
            if override:
                side_arms[d,a]=override
    # The selected 2025 policy = previous last60 FALLBACK days, all 6 arms,
    # scoring MEAN offer net return, no margin, minimum 15 past observations.
    chosen=np.zeros(N,dtype=np.int8)
    prior_n=np.zeros(N,dtype=np.int16)
    for d in range(N):
        if not fall[d]:continue
        previous=history[-60:]
        prior_n[d]=len(previous)
        if len(previous)>=15:
            scores=np.mean(np.asarray(previous,dtype=float),axis=0)
            arm=int(np.argmax(scores))
            if arm>0 and scores[arm]>scores[0]:
                chosen[d]=arm
        # Append completed current day's shadow outcomes only AFTER selection.
        recipe="trail075" if ratio[d]>=1.25 else "trail050"
        history.append([exact(d,side_arms[d,a],recipe,"scalper_offer")[0]
                        for a in range(6)])
    assert np.all(chosen[~fall]==0)
    results=[];daily=[]
    for model in ("Step8_original","Step11_selected"):
        for fee in base.MODES:
            path=[]
            for d,day in enumerate(DAYS):
                arm=int(chosen[d]) if (model=="Step11_selected" and fall[d]) else 0
                side=int(side_arms[d,arm])
                recipe=("lock050" if not fall[d] else
                        "trail075" if ratio[d]>=1.25 else "trail050")
                r,c,g,why,t=exact(d,side,recipe,fee)
                path.append(r)
                daily.append(dict(
                    model=model,fee_model=fee,date_ist=day.strftime("%Y-%m-%d"),
                    hour_ist=int(hours[d]),signal="FORCED_FALLBACK" if fall[d] else "VOLUME_EVENT",
                    direction="LONG" if side>0 else "SHORT",
                    direction_override_from_step8=bool(arm>0 and side!=base_side[d]),
                    selected_arm=study.ARMS[arm][0],previous_fallback_days=int(prior_n[d]),
                    net_account_pct=round(r*100,6),
                    gross_btc_points=round(g,5),
                    fee_gst_btc_points=round(c,5),
                    reason="STOP" if why==2 else ("TARGET" if why==1 else "TIMEOUT"),
                    hold_minutes=int(t)))
            p=np.asarray(path)
            z=metrics(p)
            z.update(model=model,fee_model=fee,
                event_days=int(np.sum(~fall)),mandatory_fallback_days=int(np.sum(fall)),
                alternate_fallback_arm_days=int(np.sum((chosen>0)&fall)) if model=="Step11_selected" else 0,
                actual_side_override_days=int(np.sum((chosen>0)&fall&
                    (side_arms[np.arange(N),chosen]!=base_side))) if model=="Step11_selected" else 0)
            results.append(z)
    table=pd.DataFrame(results);ledger=pd.DataFrame(daily)
    if len(table)!=4 or len(ledger)!=60 or not table.trades.eq(15).all():
        raise AssertionError("Missing daily trade or fee scenario")
    b=table[(table.model=="Step8_original")&
            (table.fee_model=="scalper_offer")].iloc[0]
    if b.profitable_days!=10 or abs(float(b.compounded_net_pct)-.019249)>.00011:
        raise AssertionError("November verified Step8 baseline changed "+str(b.to_dict()))
    table.to_csv(OUT/"frozen_2025_policy_november_results.csv",index=False)
    ledger.to_csv(OUT/"every_nov_weekday_trade_step8_step11.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(dict(
        frozen_policy="Step11 mean-net all6 direction arms last60 previous completed fallback sessions, min15, no margin; other conditions frozen Step8",
        Nov_sample="2026-11-02 through 2026-11-20 IST, 15 full weekdays",
        nov_period_research_exposed=True,one_trade_every_weekday=True,
        results=results,
        limitations=[
            "The selected strategy was chosen using 2025 36-variant grid after prior many research exposures; November audit not pristine",
            "Only 15 later weekdays, insufficient evidence for sustainable profit",
            "Historical Scalper Offer activation unverified; no funding, market depth, real fills/latency or tick-level stop sequence"]),
        indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
        "# Step11 frozen policy versus Step8 across 15 Nov 2026 BTC weekdays",
        "",
        "One mandatory position on all 15 complete IST Mon-Fri days, no 2026 November retuning. Online selector only refers to settled past fallback-shadow results.",
        "",
        table.to_markdown(index=False),
        "",
        "## Exact November individual trade ledger",
        ledger.to_markdown(index=False),
        "",
        "## Caveat",
        "Nov2026 was already examined for Step8/other versions, and actual fee waivers/fills cannot be inferred from OHLCV. Not a blind real-world validation."
    ])+"\n")
    print("STEP11_NOVEMBER_AUDIT "+json.dumps(results,sort_keys=True),flush=True)
    print("STEP11_NOVEMBER_COMPLETE",flush=True)

if __name__=="__main__":
    run()
