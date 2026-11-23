#!/usr/bin/env python3
"""Step 2: 1m STOP-first vs +0.2% net account or fixed gross TP from IST anchors.

This is deliberately a fixed-time unconditional LONG/SHORT counterfactual.
Results cannot become an executable strategy by picking the winning direction
retrospectively. No predictive filters and no leverage.
"""
from pathlib import Path
from itertools import product
import json

import numpy as np
import pandas as pd

import research_btc_daily_opportunity_step1 as s1

OUT=Path("analysis/btc_daily_target_first_step2")
ANCHORS=(9,15,18,19,20,21)
STOPS=(0.10,0.20,0.30,0.50)
TARGETS=("net0p2","gross0p35","gross0p50")
HOLDS=(30,120)
SIDES=(1,-1)
FEE=s1.FEE
SLIP=s1.SLIP
GOAL=s1.GOAL
TZ="Asia/Kolkata"
START,END=s1.START,s1.END

def takeprofit_price(mid,side,goal,elapsed):
    # Need true target net after time-dependent offer.
    needs=s1.required_mid_exit(mid)
    if goal=="net0p2":
        if elapsed<30:
            return needs["offer_long"] if side>0 else needs["offer_short"]
        return needs["standard_long"] if side>0 else needs["standard_short"]
    t=0.35/100 if goal=="gross0p35" else 0.50/100
    return mid*(1+side*t)

def simulate_one(op,hi,lo,daystart,hour,side,stop_pct,target_mode,hold):
    i=daystart+hour*60
    mid=float(op[i])
    fillin=mid+side*SLIP
    stop=mid*(1-side*stop_pct/100)
    reason="timeout";j=i
    midout=None
    for j in range(i,i+hold):
        target=takeprofit_price(mid,side,target_mode,j-i)
        stopped=(lo[j]<=stop if side>0 else hi[j]>=stop)
        targeted=(hi[j]>=target if side>0 else lo[j]<=target)
        if stopped:
            midout=min(float(op[j]),stop) if side>0 else max(float(op[j]),stop)
            reason="stop"
            break
        if targeted:
            # Exact limit at threshold, no favorable gap price improvement.
            midout=float(target)
            reason="target"
            break
    else:
        j=i+hold
        midout=float(op[j])
    exitfill=midout-side*SLIP
    duration=j-i
    waived=(duration<=30)
    openfee=FEE*fillin
    closefee=0.0 if waived else FEE*exitfill
    gross=side*(midout-mid)
    netpts=side*(exitfill-fillin)-openfee-closefee
    account_return=netpts/fillin
    return dict(exit_utc="",exit_reason=reason,hold_minutes=int(duration),
        eligible_scalper=waived,mid_entry=mid,mid_exit=midout,
        stop_btcusd=stop,fee_gst_points=openfee+closefee,
        gross_points=gross,net_points=netpts,account_ret=account_return)

def run_all(m):
    localdays=pd.date_range(START,END,freq="B",tz=TZ)
    op=m.open.to_numpy(float);hi=m.high.to_numpy(float);lo=m.low.to_numpy(float)
    rows=[]
    for day in localdays:
        ds=day.strftime("%Y-%m-%d")
        first=int(m.index.get_indexer([day.tz_convert("UTC")])[0])
        last=int(m.index.get_indexer([(day+pd.Timedelta(minutes=1439)).tz_convert("UTC")])[0])
        if first<0 or last-first!=1439:raise AssertionError("Incomplete IST day")
        for hour,stop,target,hold,side in product(ANCHORS,STOPS,TARGETS,HOLDS,SIDES):
            if first+hour*60+hold>last:
                raise AssertionError("Holding interval crosses day end")
            x=simulate_one(op,hi,lo,first,hour,side,stop,target,hold)
            x.update(day_ist=ds,year=int(day.year),hour_ist=int(hour),
                     direction="LONG" if side>0 else "SHORT",
                     stop_pct=float(stop),target_mode=target,
                     max_hold_minutes=int(hold))
            rows.append(x)
    ledger=pd.DataFrame(rows)
    if len(ledger)!=len(localdays)*len(ANCHORS)*len(STOPS)*len(TARGETS)*len(HOLDS)*len(SIDES):
        raise AssertionError("Incomplete scenario cube")
    if (ledger.hold_minutes>ledger.max_hold_minutes).any():
        raise AssertionError("Exceeded max hold")
    if ledger[["account_ret","net_points","gross_points"]].isna().any().any():
        raise AssertionError("Missing returns")
    return ledger

def metrics(z):
    z=z.sort_values("day_ist")
    daily=z.account_ret.to_numpy(float)
    wealth=np.cumprod(1+daily)
    peak=np.maximum.accumulate(np.r_[1.0,wealth])[1:]
    dd=np.max(1-wealth/peak)*100
    isgoal=daily>=GOAL-1e-10
    return dict(days=int(len(z)),
         tp_first=int(z.exit_reason.eq("target").sum()),
         tp_first_pct=round(float(100*z.exit_reason.eq("target").mean()),3),
         sl_first=int(z.exit_reason.eq("stop").sum()),
         sl_first_pct=round(float(100*z.exit_reason.eq("stop").mean()),3),
         timeout=int(z.exit_reason.eq("timeout").sum()),
         days_net_ge_0p2=int(isgoal.sum()),
         days_net_ge_0p2_pct=round(100*float(isgoal.mean()),3),
         net_win_days=int((daily>0).sum()),
         net_loss_days=int((daily<0).sum()),
         scalper_eligible=int(z.eligible_scalper.sum()),
         average_net_day_pct=round(100*float(np.mean(daily)),5),
         compounded_account_return_pct=round(float((wealth[-1]-1)*100),5),
         max_closed_trade_drawdown_pct=round(float(dd),5),
         worst_day_pct=round(100*float(min(daily)),5),
         total_fee_gst_points=round(float(z.fee_gst_points.sum()),2))

def group_metrics(ledger):
    results=[]
    for (yr,h,stop,tar,hold,side),z in ledger.groupby([
        "year","hour_ist","stop_pct","target_mode","max_hold_minutes","direction"],sort=True):
        y=metrics(z)
        y.update(period=str(yr),hour_ist=int(h),stop_pct=float(stop),
                 target_mode=tar,max_hold_minutes=int(hold),direction=side)
        results.append(y)
    for (h,stop,tar,hold,side),z in ledger.groupby([
        "hour_ist","stop_pct","target_mode","max_hold_minutes","direction"],sort=True):
        y=metrics(z)
        y.update(period="all",hour_ist=int(h),stop_pct=float(stop),
                 target_mode=tar,max_hold_minutes=int(hold),direction=side)
        results.append(y)
    return pd.DataFrame(results)

def oracle(ledger):
    # Either long or short could have reached the target before SL on that day.
    # Explicitly impossible ex-ante without direction predictor.
    p=ledger.pivot_table(index=["day_ist","year","hour_ist","stop_pct",
                                 "target_mode","max_hold_minutes"],
        columns="direction",values="exit_reason",aggfunc="first")
    p=p.reset_index()
    p["either_tp_first"]=p["LONG"].eq("target") | p["SHORT"].eq("target")
    q=p.groupby(["year","hour_ist","stop_pct","target_mode","max_hold_minutes"],
                sort=True).agg(n_days=("either_tp_first","size"),
                   oracle_either_tp_days=("either_tp_first","sum")).reset_index()
    q["oracle_either_tp_pct"]=np.round(q.oracle_either_tp_days/q.n_days*100,3)
    return q

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=s1.load()
    ledger=run_all(m)
    g=group_metrics(ledger)
    o=oracle(ledger)
    # Prefixed fixed 19:00 / 20:00 cases 30 minute net 0.2 target
    examples=g[(g.hour_ist.isin([18,19,20,21])) &
      (g.target_mode=="net0p2") & (g.max_hold_minutes==30) &
      (g.stop_pct.isin([0.1,0.2,0.3,0.5]))].copy()
    exam_oracle=o[(o.hour_ist.isin([18,19,20,21])) &
      (o.target_mode=="net0p2") & (o.max_hold_minutes==30) &
      (o.stop_pct.isin([0.1,0.2,0.3,0.5]))].copy()
    # Train year only; a diagnostic if any fixed-direction unconditional rule
    # is positive. No tuning on 2026 outcomes.
    train=g[g.period=="2025"].sort_values([
       "compounded_account_return_pct","days_net_ge_0p2",
       "max_closed_trade_drawdown_pct"],ascending=[False,False,True])
    best=train.iloc[0].to_dict()
    lookup=g[(g.period=="2026") & (g.hour_ist==best["hour_ist"]) &
       (g.stop_pct==best["stop_pct"])&(g.target_mode==best["target_mode"]) &
       (g.max_hold_minutes==best["max_hold_minutes"]) &
       (g.direction==best["direction"])]
    if len(lookup)!=1:raise AssertionError("Missing 2026 selected fixed rule")
    check=lookup.iloc[0].to_dict()
    # same fixed rule, results across 22 IST months
    selected=ledger[(ledger.hour_ist==best["hour_ist"]) &
       (ledger.stop_pct==best["stop_pct"])&(ledger.target_mode==best["target_mode"]) &
       (ledger.max_hold_minutes==best["max_hold_minutes"]) &
       (ledger.direction==best["direction"])].copy()
    selected["month_ist"]=selected.day_ist.str[:7]
    bymonth=[]
    for mon,z in selected.groupby("month_ist",sort=True):
        x=metrics(z)
        x["month_ist"]=mon
        bymonth.append(x)
    monthly=pd.DataFrame(bymonth)
    g.to_csv(OUT/"grouped_stop_target_first_results.csv",index=False)
    o.to_csv(OUT/"hindsight_either_side_target_first.csv",index=False)
    examples.to_csv(OUT/"fixed_18_19_20_21_30m_0p2net.csv",index=False)
    exam_oracle.to_csv(OUT/"oracle_18_19_20_21_30m_0p2net.csv",index=False)
    selected.to_csv(OUT/"selected_2025_daily_trade_ledger.csv.gz",index=False,compression="gzip")
    monthly.to_csv(OUT/"selected_2025_monthly.csv",index=False)
    # Also expose all 6 anchors / 4 stops for step 3 without requiring
    # extracting the ~140k-row ledger from CI logs.
    g[(g.target_mode=="net0p2")].to_csv(OUT/"net0p2_all_clocks_sides_stops.csv",index=False)
    summary=dict(study="step2: 1m first TP vs SL, fixed-time every-day LONG and SHORT independently",
       data_ist_start=START,data_ist_end=END,
       eligible_weekdays=int(ledger.day_ist.nunique()),
       scenarios_per_day=len(ANCHORS)*len(STOPS)*len(TARGETS)*len(HOLDS)*len(SIDES),
       hypothetical_scenarios=int(len(ledger)),
       preselected_ist_hours=list(ANCHORS),stops_pct=list(STOPS),
       targets=list(TARGETS),max_hold_minutes=list(HOLDS),
       oracle_direction_note="EITHER SIDE target-first uses hindsight and is NOT tradable",
       selected_using_2025_only=best,
       historical_2026_recheck=check,
       positive_train_2025_cases=int((train.compounded_account_return_pct>0).sum()),
       critical_limitations=[
          "Every listed long/short is its OWN hypothetical once-daily strategy, never simultaneous positions",
          "No advance direction model or filter; hindsight side chooser is not trading performance",
          "Stop-first if TP and SL both hit in same 1m bar; no true tick ordering",
          "Fee waiver assumed opted in; historical offer eligibility unverified",
          "No real orderbook, funding, bid/ask, liquidation, partial fills, or impact modeled",
          "2025 best-of-288 is in-sample optimized; 2026 is previously studied, not virgin holdout",
          "Within-30m target levels account for entry fees+GST, exit waiver, and both-side slippage"])
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    report=["# Step 2 — BTCUSD fixed-clock target first versus stop first",
            "","This is **not a validated strategy**. Every clock hour tests unconditional LONG and SHORT independently; a hindsight either-side winner cannot be predicted before entry.",
            "","477 weekdays, 6 fixed times IST, 4 stops, 3 target types, 2 holding limits, 2 trade sides. 1-minute stop-first, taker opening fee+GST and conditional <=30minute closing fee waiver; 5 BTC price points adverse slippage per side; no leverage.",
            "","## Example: 30-minute, NET +0.2% account TP","",
            examples.to_markdown(index=False),
            "","## Oracle either-side 30-minute target before stop","",
            exam_oracle.to_markdown(index=False),
            "","## Best selected using 2025-only outcomes (diagnostic, likely overfit)","",
            json.dumps(best,indent=2),
            "","## Same fixed setup, 2026 (historical check, NOT untouched)","",
            json.dumps(check,indent=2),
            "","## 22 month table for 2025-selection","",
            monthly.to_markdown(index=False),
            "","## Limitations","",
            "This study only determines first-touch ordering for fixed-clock positions with a fully known side, not how direction is predicted. Historical OHLC1m cannot resolve intrabar sequencing; stop first for double touches. The Scalper Offer's real historical activation is not verified.",
            ""]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report))
    print("STEP2_SELECTED_2025 "+json.dumps(best,sort_keys=True),flush=True)
    print("STEP2_CHECK_2026 "+json.dumps(check,sort_keys=True),flush=True)
    compact=examples[(examples.hour_ist.isin([19,20])) &
                     (examples.stop_pct.isin([0.2,0.3]))]
    print("STEP2_FIXED_19_20\n"+compact.to_string(index=False),flush=True)
    cmp=exam_oracle[(exam_oracle.hour_ist.isin([19,20])) &
                    (exam_oracle.stop_pct.isin([0.2,0.3]))]
    print("STEP2_ORACLE_19_20\n"+cmp.to_string(index=False),flush=True)
    print("STEP2_COMPLETE",flush=True)

if __name__=="__main__":
    run()
