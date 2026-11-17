#!/usr/bin/env python3
"""Stage 15 — Audit July 2025 losses and test non-calendar protective filters.

IMPORTANT:
- The Stage14 strategy remains UNCHANGED: S13 near-half-ATR 1H pullback,
  previous-month ranging regime, 4H ADX <=18, 3R, 240-minute timeout.
- Inputs are the original Stage14 GitHub Actions EVENT and TRADE artifacts.
- New filters use only fields observable BEFORE each entry. No July/month
  exclusion, no knowledge of future winning trades.
- A skipped entry makes the next entry available: simulate each protective
  variant from the COMPLETE candidate event list, not a filtered trade ledger.
- Max-day/week realized-loss gates use R units of closed trades ONLY.
- All 2025 and 2026 windows have already been inspected; no true holdout.
"""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd

from research_every_candle_200 import read_archive, FEE, SLIPPAGE
from research_structure_rr_stage11 import replay_one

OUT = Path("analysis/institutional_discovery_stage15_july_loss_controls")
STAGE14 = Path("analysis/institutional_discovery_stage14_monthly_regimes")
FAMILY = "S13_pullback_near_half_atr"
REGIME = "previous_month_ranging_4h_adx18"
REWARD_R = 3.0
HOLD_MINUTES = 240
MONTHS = pd.period_range("2025-01", "2026-11", freq="M").astype(str)
FEATURES = [
    "h4_adx", "h4_eff8", "h4_atr_ratio", "h4_vr", "h1_vr",
    "h1_prior3quiet", "volume_ratio_5m", "risk_pts",
    "previous_month_eff"
]
# Predeclared before reading the original individual trade outcomes.
FILTER_NAMES = [
    "unchanged",
    "adx_le_15", "adx_le_12",
    "4h_efficiency_le_20pct",
    "4h_atr_ratio_le_1",
    "1h_volume_ratio_le_1p2",
    "1h_volume_ratio_ge_1p2",
    "breakout_volume_ge_1p2", "breakout_volume_ge_1p5",
    "risk_le_700", "risk_le_500",
    "adx_le_15_and_breakout_volume_ge_1p2",
    "adx_le_15_and_atr_ratio_le_1",
    "long_only", "short_only"
]
GUARDS = {
    "no_loss_gate": (None, None),
    "daily_minus_1R": (-1.0, None),
    "daily_minus_2R": (-2.0, None),
    "weekly_minus_3R": (None, -3.0),
    "daily_minus_2R_weekly_minus_3R": (-2.0, -3.0)
}


def selected_events(original_events):
    required = [
        "family","k","side","entry_unix","stop_price","risk_pts","month_ist",
        "period","previous_month_eff","h4_adx",*FEATURES
    ]
    absent = sorted(set(required) - set(original_events.columns))
    if absent:
        raise ValueError("Original Stage14 event artifact lacks " + str(absent))
    e = original_events[
        (original_events.family == FAMILY) &
        (original_events.previous_month_eff <= .15) &
        (original_events.h4_adx <= 18)
    ].copy().sort_values(["k", "side"], kind="stable")
    if e.empty: raise ValueError("No Stage14 original eligible events")
    return e


def filters(e):
    a=e.h4_adx
    vol=e.volume_ratio_5m
    expr={
        "unchanged": np.ones(len(e), dtype=bool),
        "adx_le_15": (a<=15).to_numpy(bool),
        "adx_le_12": (a<=12).to_numpy(bool),
        "4h_efficiency_le_20pct": (e.h4_eff8<=.20).to_numpy(bool),
        "4h_atr_ratio_le_1": (e.h4_atr_ratio<=1.).to_numpy(bool),
        "1h_volume_ratio_le_1p2": (e.h1_vr<=1.2).to_numpy(bool),
        "1h_volume_ratio_ge_1p2": (e.h1_vr>=1.2).to_numpy(bool),
        "breakout_volume_ge_1p2": (vol>=1.2).to_numpy(bool),
        "breakout_volume_ge_1p5": (vol>=1.5).to_numpy(bool),
        "risk_le_700": (e.risk_pts<=700).to_numpy(bool),
        "risk_le_500": (e.risk_pts<=500).to_numpy(bool),
        "adx_le_15_and_breakout_volume_ge_1p2": ((a<=15)&(vol>=1.2)).to_numpy(bool),
        "adx_le_15_and_atr_ratio_le_1": ((a<=15)&(e.h4_atr_ratio<=1)).to_numpy(bool),
        "long_only": (e.side==1).to_numpy(bool),
        "short_only": (e.side==-1).to_numpy(bool)
    }
    if list(expr) != FILTER_NAMES: raise AssertionError("Filter catalog changed")
    return expr


def period_week(ts):
    # ISO week makes Monday reset unambiguous across December/January.
    local = ts.tz_convert("Asia/Kolkata")
    y,w,_ = local.isocalendar()
    return f"{y:04d}-W{w:02d}"


def simulate_candidates(e, f, condition_name, guard_name, condition):
    day_cap, week_cap = GUARDS[guard_name]
    O=f.open.to_numpy(np.float64)
    H=f.high.to_numpy(np.float64)
    L=f.low.to_numpy(np.float64)
    C=f.close.to_numpy(np.float64)
    source_t=f.time.to_numpy(np.int64)
    subset=e.loc[condition].sort_values(["k","side"],kind="stable")
    last=-1
    day_returns={}
    week_returns={}
    rows=[]
    skipped_guard=0
    skipped_overlap=0
    for z in subset.itertuples(index=False):
        k=int(z.k)
        if k<=last:
            skipped_overlap+=1
            continue
        entry_ts=pd.Timestamp(int(z.entry_unix), unit="s", tz="UTC")
        local=entry_ts.tz_convert("Asia/Kolkata")
        day=str(local.date())
        week=period_week(entry_ts)
        if (day_cap is not None and day_returns.get(day,0.0) <= day_cap) or (
            week_cap is not None and week_returns.get(week,0.0) <= week_cap):
            skipped_guard+=1
            continue
        j,why,gross,net,offer,netR,risk=replay_one(O,H,L,C,k,int(z.side),
            float(z.stop_price),float(REWARD_R),int(HOLD_MINUTES))
        last=int(j)
        exit_ts=pd.Timestamp(int(source_t[j]),unit="s",tz="UTC")
        # Record realized PNL on EXIT date/week, never when trade opened.
        exit_day=str(exit_ts.tz_convert("Asia/Kolkata").date())
        exit_week=period_week(exit_ts)
        # Future PNL is not used until the next candidate arrives after j;
        # there are no overlapping trades because k <= last is blocked.
        day_returns[exit_day]=day_returns.get(exit_day,0.)+float(netR)
        week_returns[exit_week]=week_returns.get(exit_week,0.)+float(netR)
        rows.append(dict(filter=condition_name,guard=guard_name,
            k=k,entry_unix=int(z.entry_unix),
            exit_unix=int(source_t[j]),month_ist=str(z.month_ist),
            side="LONG" if z.side==1 else "SHORT",period=str(z.period),
            reason=["stop","target","timeout"][int(why)],
            initial_risk_pts=round(float(risk),3),
            net_pts=round(float(net),3),net_R=round(float(netR),6),
            gross_pts=round(float(gross),3),
            h4_adx=float(z.h4_adx),h4_eff8=float(z.h4_eff8),
            h4_atr_ratio=float(z.h4_atr_ratio),
            h1_vr=float(z.h1_vr),
            volume_ratio_5m=float(z.volume_ratio_5m),
            previous_month_eff=float(z.previous_month_eff)))
    return rows, dict(skipped_by_loss_gate=skipped_guard,skipped_by_overlap=skipped_overlap)


def reconcile_baseline(replayed, original_ledger):
    original = original_ledger[
        (original_ledger.family==FAMILY) &
        (original_ledger.regime==REGIME) &
        (original_ledger.target_R==REWARD_R) &
        (original_ledger.max_hold_min==HOLD_MINUTES)
    ].sort_values(["entry_unix","direction"],kind="stable").reset_index(drop=True)
    fresh = replayed.sort_values(["entry_unix","side"],kind="stable").reset_index(drop=True)
    if len(original)!=len(fresh):
        raise AssertionError(f"Original Stage14 trades {len(original)} but replay {len(fresh)}")
    for name,original_name,new_name in [
        ("entry timestamps","entry_unix","entry_unix"),
        ("exit timestamps","exit_unix","exit_unix"),
        ("entry sides","direction","side")
    ]:
        if not (original[original_name].to_numpy()==fresh[new_name].to_numpy()).all():
            mismatch=np.flatnonzero(original[original_name].to_numpy()!=fresh[new_name].to_numpy())[:8]
            raise AssertionError(f"Stage14 {name} mismatch at {mismatch.tolist()}")
    max_delta=float(np.abs(original.net_standard_pts.to_numpy(float)-
                           fresh.net_pts.to_numpy(float)).max())
    if max_delta>.006:raise AssertionError(f"Net PnL mismatch: {max_delta}")
    monthly_expected=pd.read_csv(STAGE14/"monthly_results.csv")
    monthly_expected=monthly_expected[
        (monthly_expected.family==FAMILY)&(monthly_expected.regime==REGIME)&
        (monthly_expected.target_R==REWARD_R)&
        (monthly_expected.max_hold_min==HOLD_MINUTES)]
    grouped=fresh.groupby("month_ist").net_pts.agg(["size","sum"])
    for z in monthly_expected.itertuples(index=False):
        if z.month_ist not in grouped.index:
            actual_n,actual_pnl=0,0.0
        else:
            actual_n=int(grouped.loc[z.month_ist,"size"])
            actual_pnl=float(grouped.loc[z.month_ist,"sum"])
        if actual_n!=int(z.trades) or abs(actual_pnl-float(z.net_pts))>.04:
            raise AssertionError(f"Original monthly mismatch at {z.month_ist}: {actual_n},{actual_pnl} vs {z.trades},{z.net_pts}")
    return dict(original_trades=len(original),
                largest_individual_net_difference_pts=round(max_delta,6),
                months_reconciled=len(monthly_expected),
                july_2025_net_pts=round(float(grouped.loc["2025-07","sum"]),2),
                july_2025_trades=int(grouped.loc["2025-07","size"]))


def july_diagnosis(base):
    july=base[base.month_ist=="2025-07"].copy()
    if july.empty:raise AssertionError("July 2025 missing")
    july["entry_ist"]=pd.to_datetime(july.entry_unix,unit="s",utc=True).dt.tz_convert("Asia/Kolkata").astype(str)
    july["exit_ist"]=pd.to_datetime(july.exit_unix,unit="s",utc=True).dt.tz_convert("Asia/Kolkata").astype(str)
    july["result"]=np.where(july.net_pts>0,"profit","loss_or_flat")
    july=july.sort_values("entry_unix")
    july.to_csv(OUT/"july_2025_original_trade_diagnostics.csv",index=False)
    rows=[]
    for col in ["side","reason","result"]:
        for val,g in july.groupby(col,sort=True):
            rows.append(dict(segment=col,value=str(val),trades=len(g),
                net_pts=round(float(g.net_pts.sum()),2),
                net_R=round(float(g.net_R.sum()),3),
                wins=int((g.net_pts>0).sum()),
                average_risk_pts=round(float(g.initial_risk_pts.mean()),2)))
    breakdown=pd.DataFrame(rows)
    breakdown.to_csv(OUT/"july_2025_breakdown.csv",index=False)
    feature_rows=[]
    for feature in ("h4_adx","h4_eff8","h4_atr_ratio","h1_vr","volume_ratio_5m",
                    "initial_risk_pts","previous_month_eff"):
        for result,g in july.groupby("result",sort=True):
            feature_rows.append(dict(feature=feature,outcome=result,trades=len(g),
                median=round(float(g[feature].median()),4),
                mean=round(float(g[feature].mean()),4)))
    pd.DataFrame(feature_rows).to_csv(OUT/"july_winner_loser_feature_comparison.csv",index=False)
    return july,breakdown


def summarize_variants(ledger, skipped):
    monthly=[]
    grouped=[]
    for (flt,guard),g in ledger.groupby(["filter","guard"],sort=True):
        g=g.sort_values(["entry_unix","side"],kind="stable")
        v=g.net_R.to_numpy(float)
        equity=np.r_[0.,v.cumsum()]
        dd=float(np.max(np.maximum.accumulate(equity)-equity))
        means=g.groupby("month_ist")[["net_pts","net_R"]].sum()
        counts=g.groupby("month_ist").size()
        yearcounts={}
        for month in MONTHS:
            n=int(counts.get(month,0))
            net_pts=round(float(means.loc[month,"net_pts"]),2) if n else 0.
            net_R=round(float(means.loc[month,"net_R"]),4) if n else 0.
            stat="No trades" if n==0 else "Profit" if net_R>0 else "Loss" if net_R<0 else "Flat"
            monthly.append(dict(filter=flt,guard=guard,month_ist=month,
                trades=n,net_pts=net_pts,net_R=net_R,status=stat))
        # 2025 and 2026 H1 research diagnostic; H2 remains sparse.
        all_m=pd.DataFrame([z for z in monthly if z["filter"]==flt and z["guard"]==guard])
        m25=all_m[all_m.month_ist.str.startswith("2025")]
        m26=all_m[all_m.month_ist.str.startswith("2026")]
        m_ex_jul=m25[m25.month_ist!="2025-07"]
        periods={}
        for key,z in g.groupby("period"):
            periods[str(key)]=dict(n=len(z),net_R=round(float(z.net_R.sum()),3),
                net_pts=round(float(z.net_pts.sum()),2))
        win25=int((m25.status=="Profit").sum())
        win26=int((m26.status=="Profit").sum())
        n25=int((m25.trades>0).sum())
        n26=int((m26.trades>0).sum())
        nH2=periods.get("2026_H2_seen_recheck",{}).get("n",0)
        robust=(n25>=9 and n26>=8 and win25/max(1,n25)>=.75 and
                win26/max(1,n26)>=.75 and
                periods.get("2025_train",{}).get("n",0)>=60 and
                periods.get("2026_H1_validation",{}).get("n",0)>=30 and nH2>=20 and
                all(periods.get(k,{}).get("net_R",-1)<=float("inf") and
                    periods.get(k,{}).get("net_R",0)>0
                    for k in ("2025_train","2026_H1_validation","2026_H2_seen_recheck")))
        jul=all_m.loc[all_m.month_ist=="2025-07"].iloc[0]
        grouped.append(dict(filter=flt,guard=guard,trades=len(g),
            n2025=int(m25.trades.sum()),net_R_2025=round(float(m25.net_R.sum()),3),
            positive_months_2025=win25,losing_months_2025=int((m25.status=="Loss").sum()),
            active_months_2025=n25,net_R_2025_except_july=round(float(m_ex_jul.net_R.sum()),3),
            positive_months_2025_except_july=int((m_ex_jul.status=="Profit").sum()),
            n2026=int(m26.trades.sum()),net_R_2026=round(float(m26.net_R.sum()),3),
            positive_months_2026=win26,losing_months_2026=int((m26.status=="Loss").sum()),
            active_months_2026=n26,
            n2026H1=periods.get("2026_H1_validation",{}).get("n",0),
            net_R_2026H1=periods.get("2026_H1_validation",{}).get("net_R",0),
            n2026H2=nH2,
            net_R_2026H2=periods.get("2026_H2_seen_recheck",{}).get("net_R",0),
            july_trades=int(jul.trades),july_net_pts=float(jul.net_pts),
            july_net_R=float(jul.net_R),
            all_months_positive=False,
            max_drawdown_R=round(dd,3),
            gate_passed=bool(robust),
            **skipped[(flt,guard)]))
    # Month-by-month row labels should never count a no-trade month as a profit.
    return pd.DataFrame(monthly),pd.DataFrame(grouped)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--original-artifact",type=Path,required=True)
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    src=args.original_artifact
    ev=pd.read_csv(src/"event_states.csv.gz")
    old_ledger=pd.read_csv(src/"trade_ledger.csv.gz")
    e=selected_events(ev)
    f,_,_,data_quality=read_archive()
    t=f.time.to_numpy(np.int64)
    k=e.k.to_numpy(np.int32)
    if (t[k]!=e.entry_unix.to_numpy(np.int64)).any():
        raise AssertionError("Original source index no longer matches archived Stage14 events")
    conditions=filters(e)
    result=[]
    skip_stats={}
    for fname,mask in conditions.items():
        for gname in GUARDS:
            rows,skip=simulate_candidates(e,f,fname,gname,mask)
            if not rows:continue
            result.extend(rows)
            skip_stats[(fname,gname)]=skip
    ledger=pd.DataFrame(result)
    if ledger.empty:raise RuntimeError("Protective strategy simulation has no trade rows")
    baseline=ledger[(ledger["filter"]=="unchanged")&
                    (ledger.guard=="no_loss_gate")]
    audit=reconcile_baseline(baseline,old_ledger)
    july,diag=july_diagnosis(baseline)
    monthly,summary=summarize_variants(ledger,skip_stats)
    # All scenarios are independent; do not add their R/PnL.
    ledger.to_csv(OUT/"variant_trade_ledger.csv.gz",index=False,
                  compression={"method":"gzip","compresslevel":5,"mtime":0})
    monthly.to_csv(OUT/"month_by_month.csv",index=False)
    summary.to_csv(OUT/"protective_filter_comparison.csv",index=False)
    # The original July loss can only be "improved" by skipping entries if
    # the rest of the year is not damaged. Rankings use 2025 EXCLUDING July
    # and are strictly exploratory, since all periods were seen in earlier stages.
    ranking=summary[(summary.n2025>=30)&
                    (summary.n2026H1>=15)].sort_values(
        ["positive_months_2025_except_july","net_R_2025_except_july"],
        ascending=[False,False])
    ranking.head(16).to_csv(OUT/"ranked_without_july_lookback.csv",index=False)
    unchanged=summary[(summary["filter"]=="unchanged") &
                      (summary.guard=="no_loss_gate")].iloc[0]
    meta=dict(source_run=44118024590,
        source_artifact="btc-stage14-monthly-regime-trades",
        dataset_observed_minutes=len(f),
        source_missing_minutes=data_quality["missing_minutes"],
        original_selected_entry_candidates=len(e),
        original_reconciliation=audit,
        july_2025_original=dict(trades=len(july),
            winners=int((july.net_pts>0).sum()),
            losing_or_flat=int((july.net_pts<=0).sum()),
            net_pts=round(float(july.net_pts.sum()),2),
            net_R=round(float(july.net_R.sum()),3)),
        standalone_scenarios=len(summary),
        scenarios_passing_monthly_gate=int(summary.gate_passed.sum()),
        filters=list(FILTER_NAMES),safeguards=list(GUARDS),
        validation="The exact untouched Stage14 entry/exit timestamps and net PnL were matched before testing new filters",
        caveats=[
            "July 2025 is a known bad outcome; all July improvements are retrospective",
            "No filter uses calendar month label (including July) to trigger entries",
            "Daily/weekly safeguards use realized net R from *closed* trades only",
            "A daily/weekly cap prevents subsequent entries; cannot limit stop gap losses",
            "Each filtered scenario replays from all eligible signals, not from baseline winners",
            "Risk normalized R represents constant per-trade risk concept, not actual account PnL",
            "Prices are 1m OHLC, stop-first, slippage 5 points per side, standard taker fees and GST",
            "Source 1m has one missing day 2026-10-31, 2026-11 partial",
            "Funding, quote spread, market impact and liquidation not modeled",
            "All 2026 historical windows already exposed; no truly independent forward verification",
            "15 filters times five safeguards creates multiple-testing risk",
            "Zero-trade months are not counted as profitable"])
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
    top=ranking.head(12)
    focus=summary[(summary["filter"]=="unchanged") |
                  ((summary.guard=="no_loss_gate")&
                   (summary["filter"].isin(["adx_le_15","h1_volume_ratio_le_1p2",
                        "breakout_volume_ge_1p2","risk_le_700"])))]
    report=[
        "# Stage 15 — Preserve Stage 14; investigate July 2025 and pre-entry no-trade filters",
        "",
        "## Exact original strategy retained",
        f"- Entry: {FAMILY} / {REGIME}, 3R structural stop, 240-minute maximum hold",
        "- Data: exact original Stage 14 Actions event and trade artifacts, verified against the original CSV",
        f"- **Reconciliation:** {json.dumps(audit)}",
        "",
        "## July 2025 original trade diagnosis",
        f"- Total trades: {len(july)}; winners: {int((july.net_pts>0).sum())}; losses/flat: {int((july.net_pts<=0).sum())}",
        f"- Net price points after standard costs: {july.net_pts.sum():.2f}; net normalized R: {july.net_R.sum():.3f}",
        diag.to_markdown(index=False),
        "",
        "## Distinguishing 2025 July winners from losers (DESCRIPTIVE; not a predictive proof)",
        pd.read_csv(OUT/"july_winner_loser_feature_comparison.csv").to_markdown(index=False),
        "",
        "## Entire-history comparisons (each scenario replays its own trades)",
        focus[["filter","guard","n2025","positive_months_2025","net_R_2025",
            "n2026","positive_months_2026","net_R_2026",
            "july_trades","july_net_pts","july_net_R","max_drawdown_R"]].to_markdown(index=False),
        "",
        "## Non-July 2025 ranking, then JULY and 2026 as already-known checks",
        top[["filter","guard","n2025","positive_months_2025_except_july",
            "net_R_2025_except_july","july_trades","july_net_R",
            "n2026H1","net_R_2026H1","n2026H2","net_R_2026H2"]].to_markdown(index=False),
        "",
        f"## Gate result: {int(summary.gate_passed.sum())}/{len(summary)} configurations",
        "Requires >=9 active 2025 and >=8 active 2026 months, >=75% positive active months",
        "in both years, >=60/30/20 independent trades and positive net R",
        "in 2025/2026 H1/H2. All previously inspected periods; passing would still be exploratory.",
        "",
        "## Limitations",
        *["- "+v for v in meta["caveats"]],
        "",
        "## Files",
        "- july_2025_original_trade_diagnostics.csv",
        "- july_2025_breakdown.csv",
        "- july_winner_loser_feature_comparison.csv",
        "- protective_filter_comparison.csv and month_by_month.csv",
        "- variant_trade_ledger.csv.gz as downloadable GitHub Actions artifact",
        "- quality.json for reproduction and reconciliation",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE15_COMPLETED "+json.dumps({
        "baseline_trades":audit["original_trades"],
        "original_july_trades":len(july),
        "original_july_net_points":meta["july_2025_original"]["net_pts"],
        "scenario_count":len(summary),
        "gate_passes":meta["scenarios_passing_monthly_gate"]}))
    print("JULY_BREAKDOWN\n"+diag.to_string(index=False))
    print("SELECTED_SCENARIOS\n"+focus.to_string(index=False))
    print("TOP_NON_JULY\n"+top.to_string(index=False))

if __name__=="__main__":
    main()
