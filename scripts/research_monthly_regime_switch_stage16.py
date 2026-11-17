#!/usr/bin/env python3
"""Stage16 — regime-switching / rolling pattern selection for monthly consistency.

Original Stage14 baseline is preserved and reconciled EXACTLY to the original
downloaded trade ledger before analysis. Different pattern families can
represent continuation or reversal; selection only uses closed, known candles.
Rolling selectors use only "shadow" trades whose exit has ALREADY happened.
All 2025/2026 periods have previously been studied; NO virgin holdout.

Net R is normalized by original structural risk including standard fee+GST
and 5 adverse BTC-price points of slippage per side; illustrative equity grows
by a fixed 0.5% of current balance per 1R at entry. Each model one open trade.
"""
import argparse
import heapq
import json
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive
from research_structure_rr_stage11 import replay_one

OUT=Path("analysis/institutional_discovery_stage16_monthly_regime_switch")
ORIGINAL={
    "family":"S13_pullback_near_half_atr",
    "regime":"previous_month_ranging_4h_adx18",
    "R":3.0,
    "hold":240,
}
EQUITY_START=100.0
RISK_FRACTION=.005
MONTHS=pd.period_range("2025-01","2026-11",freq="M").astype(str)
ROLES={
    "S13_pullback_near_half_atr":"pullback_near",
    "S13_pullback_touch":"pullback_touch",
    "S11_01_sweep_rejection":"sweep",
    "S11_02_sweep_then_confirm":"sweep_confirm",
    "S11_03_breakout_retest":"retest",
    "S11_04_trend_pullback_engulf":"trend_engulf",
    "S11_05_market_structure_shift":"structure_shift",
    "S11_06_inside_bar_break":"inside",
    "S11_07_failed_break_followthrough":"failed_break",
    "S11_08_compression_breakout":"compression"
}
PROFILES=(
    "stage14_unchanged",
    "range_pullback_plus_trend_breakout",
    "range_sweep_plus_trend_compression",
    "range_pullback_plus_trend_pullback",
    "risk_limited_regime_switch",
    "full_three_regime_switch",
    "rolling_90day_selector",
    "rolling_180day_selector",
)
GUARDS=("no_guard","month_stop_minus3R","month_profit_lock_plus3R")
HOLD=240

def role_and_regime(event):
    """Return deterministic role and (if admissible) regime, using only event data."""
    role=ROLES.get(str(event.family))
    if role is None:return None,None
    d=int(event.side)*float(event.h4_directional_drift8)
    if (float(event.h4_adx)<=18 and
        np.isfinite(event.previous_month_eff) and
        float(event.previous_month_eff)<=.15):
        return role,"range_core"
    if float(event.h4_adx)<=18 and float(event.h4_eff8)<=.20:
        return role,"range_general"
    if float(event.h4_adx)>=25 and d>=1.5:
        return role,"trend"
    if 18<float(event.h4_adx)<25 and (
        float(event.h1_vr)>=1.3 and float(event.volume_ratio_5m)>=1.5):
        return role,"transition"
    return role,None

def matching(event, profile):
    role,reg=role_and_regime(event)
    if profile=="stage14_unchanged":
        return 3.0 if (role=="pullback_near" and reg=="range_core") else None
    if profile=="range_pullback_plus_trend_breakout":
        if reg=="range_core" and role=="pullback_near":return 3.
        if reg=="trend" and role in ("inside","retest"):return 3.
    elif profile=="range_sweep_plus_trend_compression":
        if reg in ("range_core","range_general") and role in ("sweep_confirm","failed_break"):return 2.
        if reg=="trend" and role in ("compression","trend_engulf"):return 3.
    elif profile=="range_pullback_plus_trend_pullback":
        if reg=="range_core" and role=="pullback_near":return 3.
        if reg=="trend" and role in ("pullback_touch","retest"):return 3.
    elif profile=="risk_limited_regime_switch":
        if reg=="range_core" and role=="pullback_near" and (
            float(event.risk_pts)<=700 and float(event.h4_atr_ratio)<=1.25):
            return 3.
        if reg=="trend" and role=="inside" and (
            float(event.volume_ratio_5m)>=1.2 and float(event.risk_pts)<=700):
            return 3.
    elif profile=="full_three_regime_switch":
        if reg=="range_core" and role in ("pullback_near","sweep_confirm"):return 3.
        if reg=="range_general" and role in ("sweep_confirm","failed_break"):return 2.
        if reg=="trend" and role in ("inside","retest","trend_engulf"):return 3.
        if reg=="transition" and role=="structure_shift":return 2.
    elif profile in ("rolling_90day_selector","rolling_180day_selector"):
        # Rolling eligibility calculated from shadow trade outcomes after exits.
        return matching(event,"full_three_regime_switch")
    return None

def load(source,f):
    ev=pd.read_csv(source/"event_states.csv.gz")
    orig=pd.read_csv(source/"trade_ledger.csv.gz")
    needed=["family","side","k","entry_unix","stop_price","risk_pts",
        "h4_adx","h4_eff8","h4_atr_ratio","h4_directional_drift8",
        "h1_vr","volume_ratio_5m","previous_month_eff"]
    missing=set(needed)-set(ev.columns)
    if missing:raise AssertionError("Original event columns missing "+str(missing))
    ev=ev[ev.family.isin(ROLES)].copy()
    ev=ev.sort_values(["k","family","side"],kind="stable")
    times=f.time.to_numpy(np.int64)
    k=ev.k.to_numpy(np.int32)
    if (times[k]!=ev.entry_unix.to_numpy(np.int64)).any():
        raise AssertionError("Stage14 original event indices differ from 1m source")
    # A truly missing prior month is not assumed ranging.
    return ev,orig

def simulate_rule(ev,f,profile,guard,rolling_allowed=None):
    O=f.open.to_numpy(np.float64)
    H=f.high.to_numpy(np.float64)
    L=f.low.to_numpy(np.float64)
    C=f.close.to_numpy(np.float64)
    unix=f.time.to_numpy(np.int64)
    data=[]
    busy=-1
    closed_month_R=defaultdict(float)
    reject_guard=0
    eligible=0
    for idx,row in enumerate(ev.itertuples(index=False)):
        rr=matching(row,profile)
        if rr is None:continue
        if rolling_allowed is not None and idx not in rolling_allowed:continue
        eligible+=1
        k=int(row.k)
        if k<=busy:continue
        entry_date=pd.Timestamp(int(row.entry_unix),unit="s",tz="UTC").tz_convert(
            "Asia/Kolkata")
        month=entry_date.strftime("%Y-%m")
        month_pl=closed_month_R[month]
        if ((guard=="month_stop_minus3R" and month_pl<=-3) or
            (guard=="month_profit_lock_plus3R" and month_pl>=3)):
            reject_guard+=1
            continue
        j,reason,gross,net,offer,netR,risk=replay_one(
            O,H,L,C,k,int(row.side),float(row.stop_price),float(rr),HOLD)
        busy=int(j)
        exit_ts=int(unix[j])
        exit_date=pd.Timestamp(exit_ts,unit="s",tz="UTC").tz_convert("Asia/Kolkata")
        # Realized return belongs to EXIT month, not entry month.
        closed_month_R[exit_date.strftime("%Y-%m")]+=float(netR)
        data.append(dict(profile=profile,guard=guard,
            entry_k=k,exit_k=int(j),entry_unix=int(row.entry_unix),
            exit_unix=exit_ts,entry_month_ist=month,
            month_ist=exit_date.strftime("%Y-%m"),
            role=str(row.family),direction="LONG" if int(row.side)==1 else "SHORT",
            regime=role_and_regime(row)[1],target_R=float(rr),
            risk_pts=round(float(risk),3),result=int(reason),
            gross_price_points=round(float(gross),3),
            net_price_points=round(float(net),3),
            net_R=round(float(netR),6)))
    return data,dict(eligible_signals=eligible,rejected_by_guard=reject_guard)

def past_shadow_select(ev,f,lookback_days):
    """Online maturity clock: never read a future trade result at its entry.

    Each eligible event is shadow-simulated for what would have happened if
    traded. Its result becomes usable ONLY at exit (j < next candidate k).
    Historical shadow events may overlap but cannot leak future close into
    earlier selection. Every role/market-regime is assessed separately.
    """
    op=f.open.to_numpy(np.float64)
    hi=f.high.to_numpy(np.float64)
    lo=f.low.to_numpy(np.float64)
    cl=f.close.to_numpy(np.float64)
    pending=[]
    observations=defaultdict(deque)
    allowed=set()
    selected_n=0
    for idx,row in enumerate(ev.itertuples(index=False)):
        rr=matching(row,"full_three_regime_switch")
        if rr is None:continue
        k=int(row.k)
        # Completed shadow trades only; even same-minute exits wait until next event.
        while pending and pending[0][0]<k:
            end,seq,key,score=heapq.heappop(pending)
            observations[key].append((end,score))
        limit=k-lookback_days*1440
        for key,bucket in observations.items():
            while bucket and bucket[0][0]<limit:
                bucket.popleft()
        _,reg=role_and_regime(row)
        fam=str(row.family)
        key=(reg,fam)
        history=observations[key]
        count=len(history)
        mean=float(np.mean([v for _,v in history])) if count else -99.
        # Do not over-select the biggest past winner: require >0.15R
        # and >=8 closed examples of THIS SAME role+regime in lookback.
        if count>=8 and mean>=.15:
            allowed.add(idx)
            selected_n+=1
        j,_,_,_,_,netR,_=replay_one(
            op,hi,lo,cl,k,int(row.side),float(row.stop_price),float(rr),HOLD)
        heapq.heappush(pending,(int(j),idx,key,float(netR)))
    return allowed,selected_n

def reconcile_original(rows,original):
    oracle=original[
        (original.family==ORIGINAL["family"])&
        (original.regime==ORIGINAL["regime"])&
        (original.target_R==ORIGINAL["R"])&
        (original.max_hold_min==ORIGINAL["hold"])
    ].sort_values(["entry_unix","direction"],kind="stable").reset_index(drop=True)
    current=pd.DataFrame(rows).sort_values(["entry_unix","direction"],
                                           kind="stable").reset_index(drop=True)
    if len(current)!=len(oracle):
        raise AssertionError(f"Baseline counts differ {len(current)} / {len(oracle)}")
    for label,col in (("entry_unix","entry_unix"),("exit_unix","exit_unix"),
                      ("direction","direction")):
        if (current[label].to_numpy()!=oracle[col].to_numpy()).any():
            raise AssertionError("Baseline original "+label+" mismatch")
    delta=np.abs(current.net_price_points.to_numpy(float)-
                 oracle.net_standard_pts.to_numpy(float))
    if delta.max()>.006:raise AssertionError("Baseline fee PnL mismatch")
    return dict(original_trade_count=len(oracle),
                maximum_net_points_drift=float(delta.max()))

def monthly_results(ledger):
    rows=[]
    scores=[]
    keys=["profile","guard"]
    for config,g in ledger.groupby(keys,sort=True):
        g=g.sort_values("exit_unix",kind="stable")
        equity=EQUITY_START
        # Fixed fraction risk per filled trade: account-equity percentage
        # return is net_R * 0.5% at exit, compounded in exit order.
        # No intratrade mark-to-market/forced liquidation represented.
        month_net=defaultdict(float)
        month_rets=defaultdict(list)
        month_n=defaultdict(int)
        month_equity_start={}
        month_equity_end={}
        for row in g.itertuples(index=False):
            m=row.month_ist
            if m not in month_equity_start:
                month_equity_start[m]=equity
            change=1.+RISK_FRACTION*row.net_R
            if change<=0:
                raise ValueError("Simulated trade wipes out account")
            equity*=change
            month_equity_end[m]=equity
            month_n[m]+=1
            month_net[m]+=float(row.net_R)
            month_rets[m].append(float(row.net_R))
        nprofit=nloss=nflat=nnotrade=0
        monthly_equity=EQUITY_START
        sequence=[]
        for month in MONTHS:
            n=month_n[month]
            prior=monthly_equity
            for netr in month_rets[month]:
                monthly_equity*=1.+RISK_FRACTION*netr
            r=(monthly_equity/prior-1)*100
            if n==0:
                status="No trades"; nnotrade+=1
            elif r>1e-10:
                status="Profit";nprofit+=1
            elif r < -1e-10:
                status="Loss";nloss+=1
            else:status="Flat";nflat+=1
            sequence.append(r)
            rows.append(dict(zip(keys,config),month_ist=month,
                trades=n,net_R=round(month_net[month],4),
                modeled_equity_return_pct=round(r,4),
                status=status))
        tmp=pd.DataFrame([x for x in rows if x["profile"]==config[0] and
                          x["guard"]==config[1]])
        year25=tmp[tmp.month_ist.str.startswith("2025")]
        year26=tmp[tmp.month_ist.str.startswith("2026")]
        total_net_R=float(g.net_R.sum())
        equity_curve=np.r_[EQUITY_START,
                           EQUITY_START*np.cumprod(1.+RISK_FRACTION*g.net_R.to_numpy(float))]
        max_dd=float(np.max(1.-equity_curve/
                           np.maximum.accumulate(equity_curve))*100)
        def subset_year(z):
            return dict(active=int((z.trades>0).sum()),
                wins=int((z.status=="Profit").sum()),
                loses=int((z.status=="Loss").sum()),
                idle=int((z.status=="No trades").sum()),
                netR=round(float(z.net_R.sum()),3),
                modeled_compound_pct=round(
                    float((np.prod(1.+z.modeled_equity_return_pct.to_numpy(float)/100)-1)*100),3))
        yr25=subset_year(year25)
        yr26=subset_year(year26)
        passed=(yr25["active"]>=9 and yr26["active"]>=8 and
                yr25["wins"]/max(1,yr25["active"])>=.75 and
                yr26["wins"]/max(1,yr26["active"])>=.75 and
                yr25["netR"]>0 and yr26["netR"]>0 and len(g)>=90 and
                # previously seen Jul-Oct 2026 needs >=15 trades
                len(g[(g.month_ist>="2026-07")&(g.month_ist<="2026-10")])>=15)
        scores.append(dict(profile=config[0],guard=config[1],
            trades=len(g),
            active_months_2025=yr25["active"],profitable_months_2025=yr25["wins"],
            losing_months_2025=yr25["loses"],inactive_months_2025=yr25["idle"],
            net_R_2025=yr25["netR"],model_compounded_pct_2025=yr25["modeled_compound_pct"],
            active_months_2026=yr26["active"],profitable_months_2026=yr26["wins"],
            losing_months_2026=yr26["loses"],inactive_months_2026=yr26["idle"],
            net_R_2026=yr26["netR"],model_compounded_pct_2026=yr26["modeled_compound_pct"],
            max_trade_to_trade_drawdown_pct=round(max_dd,3),
            modeled_total_return_pct=round((equity/EQUITY_START-1)*100,3),
            passed_research_gate=bool(passed)))
    return pd.DataFrame(rows),pd.DataFrame(scores)

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--original-artifact",required=True,type=Path)
    args=cli.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    f,_,_,quality=read_archive()
    e,original=load(args.original_artifact,f)
    rolling={}
    for days in (90,180):
        rolling[days],n=past_shadow_select(e,f,days)
        print(f"ROLLING_SHADOW_{days}D_ELIGIBLE={n}")
    allrows=[]
    guards_stats=[]
    for profile in PROFILES:
        for guard in GUARDS:
            keep=rolling[90] if profile=="rolling_90day_selector" else (
                 rolling[180] if profile=="rolling_180day_selector" else None)
            rows,st=simulate_rule(e,f,profile,guard,rolling_allowed=keep)
            guards_stats.append(dict(profile=profile,guard=guard,**st,
                actual_trades=len(rows)))
            allrows.extend(rows)
    if not allrows:raise RuntimeError("Zero trades in every model")
    ledger=pd.DataFrame(allrows)
    base=ledger[(ledger.profile=="stage14_unchanged")&(ledger.guard=="no_guard")]
    audit=reconcile_original(base.to_dict("records"),original)
    monthly,summary=monthly_results(ledger)
    guard_table=pd.DataFrame(guards_stats)
    summary=summary.merge(guard_table,on=["profile","guard"],how="left")
    passes=summary[summary.passed_research_gate]
    ledger.to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    monthly.to_csv(OUT/"monthly_results.csv",index=False)
    summary.to_csv(OUT/"strategy_comparison.csv",index=False)
    guard_table.to_csv(OUT/"entry_screen_audit.csv",index=False)
    audit_data=dict(
        source="Original Stage14 GitHub Actions artifact + source Delta BTC 1m candles",
        source_run=44118024590,
        stage14_reconciliation=audit,
        original_events=len(e),observed_candles=len(f),
        missing_minutes=quality["missing_minutes"],
        tested_profiles=list(PROFILES),tested_guards=list(GUARDS),
        strategy_count=len(summary),total_replayed_trade_rows=len(ledger),
        monthly_consistency_passes=len(passes),
        risk_per_trade_fraction=RISK_FRACTION,
        equity_model="each trade net R multiplied by 0.5% starting equity risk, compounded on exit",
        monthly_allocation="actual exit timestamp Asia/Kolkata",
        rolling_selector="min 8 closed shadow results from prior 90/180 days; mean net R >=0.15",
        severe_limitations=[
            "No historical 2026 month is an untouched test; all exposed by earlier stages",
            "Selection of specific market-regime portfolios is exploratory and may overfit",
            "Rolling shadow results become usable only after completion, but shadow trades can overlap",
            "Equity model assumes exact fractional risk sizing without margin limits or contract rounding",
            "No liquidation, capital/margin/funding cashflows or actual bid-ask depth modeled",
            "One source gap on 2026-10-31; November 2026 is partial",
            "A risk cap or monthly lock cannot guarantee profit every month",
            "Any no-trade months count separately, never as profitable",
            "1m OHLC with stop-first fills, historical slippage assumed 5 price points per side",
            "Standard Delta BTC taker fees plus GST included through Stage11 net R"]
    )
    (OUT/"quality.json").write_text(json.dumps(audit_data,indent=2)+"\n")
    baseline=summary[(summary.profile=="stage14_unchanged")&
                     (summary.guard=="no_guard")].iloc[0]
    comparable=summary[(summary.guard=="no_guard")].sort_values(
        ["profitable_months_2025","profitable_months_2026"],
        ascending=False)
    # Fully shown months for reference and 2025-selected candidate without cherry-picking July.
    compare=monthly[monthly.profile.isin(
        ["stage14_unchanged","range_pullback_plus_trend_breakout",
         "range_sweep_plus_trend_compression",
         "full_three_regime_switch","rolling_90day_selector"])&
        (monthly.guard=="no_guard")]
    report=[
        "# Stage 16 — Can regime switching improve consistency of monthly BTC returns?",
        "",
        "## Definitions",
        "Preserve original Stage14 pullback 3R model, replay from original Stage14",
        "event snapshots and original full trade ledger. Reconciliation: "+json.dumps(audit),
        "",
        "Test fixed complementary entry families:",
        "- Range-bound: 1H pullback reversal, confirmed sweep/failure",
        "- Trending: inside-bar and retest breakout, trend pullback engulf, compression breakout",
        "- Transition: market structure shift with high 1H+5M volume",
        "- Rolling 90/180-day shadow performance gate: uses ONLY already-closed outcomes",
        "- Optional monthly realized net-risk guard at -3R or +3R",
        "",
        "All models: one exclusive position, structural stop, 2R or 3R, max 240 min.",
        "Standard taker/GST/slippage included; monthly returns modeled at 0.5% risk per trade.",
        "Monthly returns booked in IST EXIT month (not entry month); no-trade months are neutral.",
        "",
        "## Best comparison with zero monthly lock",
        comparable[["profile","trades","active_months_2025","profitable_months_2025",
            "net_R_2025","model_compounded_pct_2025",
            "active_months_2026","profitable_months_2026",
            "net_R_2026","model_compounded_pct_2026",
            "max_trade_to_trade_drawdown_pct"]].to_markdown(index=False),"",
        "## All profiles including monthly risk guards",
        summary.to_markdown(index=False),"",
        "## Predeclared consistency gate",
        "Require >=9 active 2025 and >=8 active 2026 months, at least 75%",
        "of active months profitable each year, positive net R both years,",
        ">=90 trades and >=15 during Jul–Oct 2026. Passing historical gate",
        "would NOT establish deployability without new forward data.",
        "",
        f"Passing combinations: **{len(passes)} / {len(summary)}**",
        passes.to_markdown(index=False) if len(passes) else "None passed.", "",
        "## Monthly comparison of representative unguarded alternatives",
        compare.to_markdown(index=False), "",
        "## Limitations",
        *["- "+v for v in audit_data["severe_limitations"]],"",
        "The original baseline is unchanged. Results include failures.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE16_DONE "+json.dumps({
        "source_entries":len(e),"replayed_rows":len(ledger),
        "configurations":len(summary),"passes":len(passes),
        "verified_original_trades":audit["original_trade_count"]}))
    print("UNGARDED\n"+comparable.to_string(index=False))
    print("ALL_COMPARISONS\n"+summary.to_string(index=False))
    print("PASSED\n"+passes.to_string(index=False))
if __name__=="__main__":
    main()
