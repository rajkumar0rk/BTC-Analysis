#!/usr/bin/env python3
"""BTC Stage18/20 entry/exit rule redesign from real 1m candles.
Compare weekly loss gate with unconstrained trading, more causal entries,
and longer/shorter payoff holding. Original signals, SL and fees preserved.
Select BTC 2025 only; 2026 is historically exposed, not pristine OOS.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive
from research_structure_rr_stage11 import replay_one
import research_july_drawdown_stage15 as stage
import research_stage18_stage20_signal_exit_improvement_20261120 as core
OUT=Path("analysis/stage18_stage20_guard_free_20261120")
MONTHS=core.MONTHS
# label, prior-month 4H efficiency cap, ADX cap, h1 volume cap,
# guard, direction, target multiple, max hold minutes
CASES=[
 ("original_3R",.15,18,1.2,"weekly_minus_3R","both",3,240),
 ("original_5R",.15,18,1.2,"weekly_minus_3R","both",5,240),
 ("5R_no_gate",.15,18,1.2,"no_loss_gate","both",5,240),
 ("5R_daily2R_gate",.15,18,1.2,"daily_minus_2R","both",5,240),
 ("5R_broader_eff25_guard",.25,18,1.2,"weekly_minus_3R","both",5,240),
 ("5R_broader_eff25_no_gate",.25,18,1.2,"no_loss_gate","both",5,240),
 ("5R_broader_eff30_no_gate",.30,18,1.2,"no_loss_gate","both",5,240),
 ("5R_broader_eff25_daily2R",.25,18,1.2,"daily_minus_2R","both",5,240),
 ("5R_eff25_no_gate_LONG",.25,18,1.2,"no_loss_gate","long",5,240),
 ("5R_eff25_no_gate_SHORT",.25,18,1.2,"no_loss_gate","short",5,240),
 ("5R_no_gate_480m",.15,18,1.2,"no_loss_gate","both",5,480),
 ("5R_eff25_no_gate_480m",.25,18,1.2,"no_loss_gate","both",5,480),
 ("8R_no_gate",.15,18,1.2,"no_loss_gate","both",8,240),
 ("8R_eff25_no_gate",.25,18,1.2,"no_loss_gate","both",8,240),
 ("5R_no_gate_broader_volume",.15,18,1.5,"no_loss_gate","both",5,240),
 ("5R_eff25_gate_broader_volume",.25,18,1.5,"weekly_minus_3R","both",5,240)
]
def execute(events,f,c):
    name,eff,adx,vr,guard,direction,target,hold=c
    e=events[(events.family==stage.FAMILY)&(events.previous_month_eff<=eff)&(events.h4_adx<=adx)]
    if direction=="long":e=e[e.side==1]
    if direction=="short":e=e[e.side==-1]
    stage.REWARD_R=target
    stage.HOLD_MINUTES=hold
    stage.replay_one=replay_one
    rows,skips=stage.simulate_candidates(e,f,name,guard,(e.h1_vr<=vr).to_numpy(bool))
    if not rows:raise ValueError("No trades "+name)
    g=pd.DataFrame(rows).sort_values(["exit_unix","entry_unix"],kind="stable")
    g["exit_month_ist"]=pd.to_datetime(g.exit_unix,unit="s",utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    g=g[g.exit_month_ist.isin(MONTHS)].copy()
    g["entry_mid"]=f.open.to_numpy(float)[g.k.to_numpy(int)]
    g["risk_fraction"]=np.minimum(core.RISK_FRACTION,core.MAX_LEVERAGE*g.initial_risk_pts/g.entry_mid)
    g["variant"]=name
    return g,skips
def stats(a):
    x=np.asarray(a,float)
    if not np.isfinite(x).all() or (x<=-100).any():raise AssertionError("Invalid NAV")
    nav=np.cumprod(1+x/100)
    peak=np.maximum.accumulate(np.r_[1,nav])[1:]
    return dict(ret=float(100*(nav[-1]-1)),wins=int((x>1e-9).sum()),
        loss=int((x<-1e-9).sum()),flat=int((abs(x)<=1e-9).sum()),
        dd=float(100*np.max(1-nav/peak)),worst=float(x.min()))
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,_,_,quality=read_archive()
    events=pd.read_csv(core.EVENTS)
    original=core.saved_sleeves()
    rec=[];monthly=[];trades=[]
    for case in CASES:
        g,skips=execute(events,f,case)
        trades.append(g)
        for stress in (0,2,5):
            result=core.replay_nav(g,stress)
            a=np.asarray([v["net_pct"] for v in result["monthly"]])
            for family in ("Stage18","Stage20"):
                portfolio=.75*a+.25*original["d55"] if family=="Stage18" else .9*(.75*a+.25*original["d20"])+.1*original["hourly"]
                train=stats(portfolio[:12]);check=stats(portfolio[12:]);allp=stats(portfolio)
                rec.append(dict(family=family,variant=case[0],guard=case[4],
                    direction=case[5],eff_max=case[1],target_R=case[6],hold_min=case[7],
                    trades=result["trades"],trades_2025=result["trades_2025"],
                    skipped_loss_gate=skips["skipped_by_loss_gate"],
                    core_pf=result["pf_net_R"],extra_slip_bps_side=stress,
                    train_2025=train["ret"],train_positive=train["wins"],train_dd=train["dd"],
                    validation_2026=check["ret"],check_positive=check["wins"],
                    net_22=allp["ret"],positive_22=allp["wins"],
                    negative_22=allp["loss"],flat_22=allp["flat"],dd_22=allp["dd"],
                    worst_month_22=allp["worst"]))
                monthly.extend(dict(family=family,variant=case[0],month=m,
                    stress_bps_side=stress,net_month_pct=float(x)) for m,x in zip(MONTHS,portfolio))
    df=pd.DataFrame(rec);monthly=pd.DataFrame(monthly)
    choices={}
    for family in ("Stage18","Stage20"):
        x=monthly[(monthly.family==family)&(monthly.variant=="original_3R")&(monthly.stress_bps_side==0)].set_index("month").reindex(MONTHS).net_month_pct.to_numpy()
        ref=original["ref18"] if family=="Stage18" else original["ref20"]
        delta=float(np.max(np.abs(x-ref)))
        if delta>.04:raise AssertionError(f"Original replay mismatch {family}: {delta}")
        r=df[(df.family==family)&(df.extra_slip_bps_side==2)&(df.trades_2025>=30)&(df.train_2025>0)].copy()
        r["train_score"]=r.train_2025+.5*r.train_positive-.8*r.train_dd
        r=r.sort_values(["train_score","train_2025"],ascending=False,kind="stable")
        choices[family]=str(r.iloc[0].variant)
        print("BTC2025_RANK",family,r[["variant","train_score","train_2025",
            "train_positive","trades_2025","train_dd"]].to_json(orient="records"))
        print("FROZEN_SELECTED",family,choices[family])
        for candidate in dict.fromkeys(["original_5R","5R_no_gate",
                    "5R_broader_eff25_no_gate",choices[family]]):
            for stress in (0,2,5):
                row=df[(df.family==family)&(df.variant==candidate)&(df.extra_slip_bps_side==stress)]
                print("AUDIT_RESULT",row.iloc[0].to_json())
        print("ALL_VARIANTS_CHRONOLOGICAL_CHECK",family,df[(df.family==family)&
            (df.extra_slip_bps_side==2)][["variant","train_2025","validation_2026",
            "net_22","positive_22"]].to_json(orient="records"))
    df.to_csv(OUT/"all_rule_results.csv",index=False)
    monthly.to_csv(OUT/"all_months.csv",index=False)
    pd.concat(trades,ignore_index=True).to_csv(OUT/"all_1m_trades.csv.gz",index=False,compression="gzip")
    (OUT/"BTC2025_selection.json").write_text(json.dumps(choices,indent=2))
    (OUT/"limitations.json").write_text(json.dumps(dict(
       source=quality,variants=CASES,
       status="Native 1m Stage15 core; Stage17/19 original month summaries; NOT full integrated portfolio",
       selection="BTC2025 only, after +2bp per order side; 2026 exposed and not used to pick",
       costs="0.05%/side taker plus GST18%, 5BTC points adverse slip per side; extra 0/2/5bps each side",
       issues=["No ETH native validation","No margin/funding/order-book/lot-size model",
         "BTC 2026 historically exposed; cannot claim independent validation",
         "Incomplete historical month source; 1m OHLC not tick",
         "Stage15 core PnL exit-month, not exact month-end open PnL",
         "Merging independent sleeves by monthly NAV assumes separate allocations, not exchange account-level fills",
         "Loss gates removed in some strategies deliberately; losing months/trades never excluded from metrics"],
       no_live_trading=True),indent=2,default=str))
    print("GUARD_REMOVAL_REAL_1M_COMPLETE",json.dumps(choices))
if __name__=="__main__":main()
