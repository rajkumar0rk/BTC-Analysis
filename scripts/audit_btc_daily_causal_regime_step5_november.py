#!/usr/bin/env python3
"""Frozen C/D/E versus B: November 2-20 2026 BTCUSD 15 weekday audit.

This short period previously examined for old baseline B: not a blind holdout.
No entry or exit rules optimized on November. All C/D/E are hindsight-picked
from 2025-JanOct26 and not validated recommendations.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_btc_every_weekday_reset_step1 as base
import research_btc_every_weekday_exit_protection_step3 as protect
import audit_btc_daily_fallback_regime_november_2026 as nov

OUT=Path("analysis/btc_daily_causal_regime_step5/november_audit")
CASES={
 "B_old":("lock050","trail050","trail050"),
 "C_more_winning_days":("lock075","trail050","trail075"),
 "D_balanced_drawdown":("lock050","trail050","lock075"),
 "E_higher_profit_lower_dd":("lock050","trail050","trail075"),
}
RECIPES={
    "lock050":(1,.5,3.,30,.25,.10,0.),
    "lock075":(1,.75,3.,30,.25,.10,0.),
    "trail050":(2,.5,3.,30,.35,.20,0.),
    "trail075":(2,.75,3.,30,.35,.20,0.),
}

def cfg():
    full,names=protect.build_configs()
    rows=[]
    for key,c in RECIPES.items():
        hits=np.flatnonzero(np.all(np.isclose(full,np.array(c,dtype=float)),axis=1))
        if len(hits)!=1:raise AssertionError("Missing expected 1m exit "+key)
        rows.append(full[hits[0]])
    return np.asarray(rows,float),dict(zip(RECIPES,range(len(RECIPES))))

def measurements(p):
    eq=np.cumprod(1+p)
    peak=np.maximum.accumulate(np.r_[1.,eq])[1:]
    return dict(
        trades=len(p),profitable_days=int(np.sum(p>0)),losing_days=int(np.sum(p<0)),
        winning_day_pct=round(float(100*np.mean(p>0)),2),
        net_compounded_account_pct=round(float(100*(eq[-1]-1)),5),
        max_closed_dd_pct=round(float(100*np.max(1-eq/peak)),5),
        worst_day_pct=round(float(100*np.min(p)),5)
    )

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=nov.load_with_nov()
    start,hour,side,fall=nov.determine_entries(m,"follow5")
    assert len(start)==15 and np.unique(nov.NDAYS.strftime("%Y-%m-%d")).size==15
    v=m.volume.to_numpy(float)
    ratio=np.full(15,np.nan)
    for d,i in enumerate(start):
        vol5=float(np.sum(v[i-5:i]))
        prev=v[i-105:i-5].reshape(20,5).sum(axis=1)
        avg=float(np.mean(prev))
        ratio[d]=vol5/avg if avg>0 else 0.
    regime=(ratio>=1.25)&fall
    config,idx=cfg()
    er,ef,eg,why,elapsed=protect.run_exit_grid(
        m.open.to_numpy(float),m.high.to_numpy(float),m.low.to_numpy(float),
        start,hour,side,config,base.COST,base.SLIP)
    results=[];daily=[]
    d=np.arange(15)
    for case,(event,low,high) in CASES.items():
        chosen=np.where(fall,np.where(regime,idx[high],idx[low]),idx[event])
        for mi,model in enumerate(base.MODES):
            p=er[d,chosen,mi]
            c=ef[d,chosen,mi]
            gross=eg[d,chosen]
            r=why[d,chosen]
            t=elapsed[d,chosen]
            met=measurements(p)
            met.update(case=case,cost_model=model,event_entries=int(np.sum(~fall)),
                       fallback_entries=int(np.sum(fall)),
                       high_volume_fallback_entries=int(np.sum(regime)),
                       total_fees_gst_btc_points=round(float(c.sum()),2),
                       stop_exits=int(np.sum(r==2)),take_profit_exits=int(np.sum(r==1)),
                       timeout_exits=int(np.sum(r==3)))
            results.append(met)
            for j,day in enumerate(nov.NDAYS):
                daily.append(dict(
                    case=case,cost_model=model,date_ist=day.strftime("%Y-%m-%d"),
                    entry_hour_ist=int(hour[j]),side="LONG" if side[j]==1 else "SHORT",
                    signal="FALLBACK" if fall[j] else "VOLUME_EVENT",
                    preentry_vol5_ratio=round(float(ratio[j]),5),
                    volume_high_regime=bool(regime[j]),
                    chosen_exit=[*RECIPES][chosen[j]],
                    net_account_pct=round(float(p[j]*100),6),
                    gross_points=round(float(gross[j]),4),
                    fee_gst_points=round(float(c[j]),4),
                    exit_reason="STOP" if r[j]==2 else ("TP" if r[j]==1 else "TIMEOUT"),
                    hold_minutes=int(t[j])))
    tab=pd.DataFrame(results)
    path=pd.DataFrame(daily)
    if len(tab)!=8 or len(path)!=120:raise AssertionError("Incomplete audit")
    old=tab[(tab.case=="B_old")&(tab.cost_model=="scalper_offer")].iloc[0]
    if old.profitable_days!=10 or abs(old.net_compounded_account_pct-.01925)>.00011:
        raise AssertionError("Historical November B baseline changed: "+str(old.to_dict()))
    tab.to_csv(OUT/"four_frozen_cases_two_fee_models.csv",index=False)
    path.to_csv(OUT/"all_15_weekday_trades_4_cases.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(dict(
       dates="2026-11-02..2026-11-20 IST Monday-Friday, 15 full days",
       each_model_trades=15,previously_examined_november=True,
       no_retuning=True,
       costs="1x account notional; regular hypothetical Scalper Offer <=30min exit waiver; otherwise standard taker 0.05% per side+18% GST; 5 BTC points adverse slippage per side",
       results=results,
       limitations=["15-day retrospective window is statistically weak and was already studied for older B",
           "C/D/E from 26400 in-sample historical comparisons, high multiple-testing bias",
           "No exact historical offer eligibility, funding, order book or actual fills"]),indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
        "# November audit of B/C/D/E precommitted daily BTC rules","",
        "Four fixed strategies, precisely 15 IST Monday-Friday trading days each, 1x BTC futures notional; no new tuning.","",
        tab.to_markdown(index=False),"",
        "## All daily trades","",path.to_markdown(index=False),"",
        "## Caveats","Hindsight-selected backtest entries C/D/E cannot be considered validated by this 15-day audit, particularly because the November period had been examined previously for B."
    ])+"\n")
    print("NOV_STEP5_4_CANDIDATES "+json.dumps(results,sort_keys=True),flush=True)
    print("NOV_STEP5_DONE",flush=True)

if __name__=="__main__":
    run()
