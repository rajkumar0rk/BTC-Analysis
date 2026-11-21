#!/usr/bin/env python3
"""Audit historic daily realized-close frequency WITHOUT editing Stage18 signals.

The combined 70/30 daily realized-exit proxy is NOT a daily portfolio NAV:
Stage18's Donchian component is MTM monthly while open, and true intraday
portfolio execution / shared collateral are not modeled.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

SOURCE=Path("analysis/stage18_btc_70core_30donchian_implementation")
OUT=Path("analysis/stage18_daily_realized_audit_20261121")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()

def ledger(path,kind):
    t=pd.read_csv(path)
    expected={"exit_unix","net_R"}
    if kind=="core": expected.add("risk_fraction")
    if expected-set(t):
        raise RuntimeError("Missing trade ledger columns: "+str(expected-set(t)))
    if not np.isfinite(t.net_R.to_numpy(float)).all():
        raise RuntimeError("Invalid net R")
    t["exit_ist"]=pd.to_datetime(t.exit_unix,unit="s",utc=True).dt.tz_convert("Asia/Kolkata")
    t["exit_day_ist"]=t.exit_ist.dt.strftime("%Y-%m-%d")
    t["exit_month_ist"]=t.exit_ist.dt.strftime("%Y-%m")
    t["notional_risk_fraction"]=t.risk_fraction.to_numpy(float) if kind=="core" else 0.005
    t["trade_return_fraction"]=t.net_R.to_numpy(float)*t.notional_risk_fraction.to_numpy(float)
    if ((1+t.trade_return_fraction)<=0).any():
        raise RuntimeError("Single trade bankrupts portfolio")
    t["component"]=kind
    return t[t.exit_month_ist.isin(MONTHS)].copy()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    summary=pd.read_csv(SOURCE/"scenario_summary.csv")
    selected=summary[(summary.scenario=="stage18_70_30_30d")&(summary.extra_bps_side==0)]
    if len(selected)!=1:raise AssertionError("Verified 70/30 snapshot missing")
    verified=selected.iloc[0]
    if ((round(float(verified.total_return_pct),2)!=14.44)
        or (int(verified.positive_months),int(verified.negative_months),int(verified.flat_months))!=(19,2,1)):
        raise AssertionError("Stage18 historical monthly reproducibility check failed")
    core=ledger(SOURCE/"core_700point_1m_trades.csv","core")
    swing=ledger(SOURCE/"donchian_30day_trades.csv","swing")
    if len(core)!=63:raise AssertionError(f"Expected 63 core trades, found {len(core)}")
    trades=pd.concat([core,swing],ignore_index=True)
    start=pd.Timestamp("2025-01-01",tz="Asia/Kolkata")
    end=pd.Timestamp("2026-10-31",tz="Asia/Kolkata")
    idx=pd.date_range(start,end,freq="D")
    by={}
    for name,g in trades.groupby("component"):
        records=[]
        for day,grp in g.groupby("exit_day_ist"):
            returns=grp.sort_values("exit_ist").trade_return_fraction.to_numpy(float)
            records.append((day,len(returns),100*(np.prod(1+returns)-1)))
        by[name]=pd.DataFrame(records,columns=["day","n","net_pct_proxy"]).set_index("day")
    out=pd.DataFrame({"day":idx.strftime("%Y-%m-%d")})
    for kind in ("core","swing"):
        g=by[kind]
        out[kind+"_exits"]=out.day.map(g.n).fillna(0).astype(int)
        out[kind+"_realized_net_pct_proxy"]=out.day.map(g.net_pct_proxy).fillna(0.0).astype(float)
    out["total_exits"]=out.core_exits+out.swing_exits
    out["weighted_daily_realized_exit_pct_proxy"]=(
        0.7*out.core_realized_net_pct_proxy+0.3*out.swing_realized_net_pct_proxy)
    out["month_ist"]=out.day.str[:7]
    eps=1e-9
    out["day_state"]=np.where(out.total_exits==0,"no_exit",
       np.where(out.weighted_daily_realized_exit_pct_proxy>eps,"positive_exit_day",
       np.where(out.weighted_daily_realized_exit_pct_proxy< -eps,"negative_exit_day",
       "flat_exit_day")))
    monthly=out.groupby("month_ist",sort=True).agg(
       calendar_days=("day","size"),trade_exit_days=("total_exits",lambda x:int((x>0).sum())),
       positive_exit_days=("day_state",lambda x:int((x=="positive_exit_day").sum())),
       negative_exit_days=("day_state",lambda x:int((x=="negative_exit_day").sum())),
       flat_exit_days=("day_state",lambda x:int((x=="flat_exit_day").sum())),
       no_exit_days=("day_state",lambda x:int((x=="no_exit").sum())),
       core_exits=("core_exits","sum"),swing_exits=("swing_exits","sum")
    ).reset_index()
    n_days=len(out)
    positives=int((out.day_state=="positive_exit_day").sum())
    negative=int((out.day_state=="negative_exit_day").sum())
    noexit=int((out.day_state=="no_exit").sum())
    trade_days=int((out.total_exits>0).sum())
    assessment={
       "source":"Stage18 70% Core 30% Donchian rechecked native BTCUSD 1m",
       "verified_compounded_monthly_net_22m_pct":round(float(verified.total_return_pct),5),
       "verified_months_profitable":int(verified.positive_months),
       "verified_months_losing":int(verified.negative_months),
       "verified_months_flat":int(verified.flat_months),
       "core_closed_trades":len(core),"swing_closed_trades":len(swing),
       "all_ist_calendar_dates":n_days,
       "dates_with_at_least_one_exit":trade_days,
       "dates_with_positive_realized_exit_proxy":positives,
       "dates_with_negative_realized_exit_proxy":negative,
       "dates_without_any_exit":noexit,
       "positive_calendar_date_pct":round(100*positives/n_days,4),
       "positive_given_exit_day_pct":round(100*positives/trade_days,4) if trade_days else None,
       "daily_profit_possible_every_day_in_history":bool(positives==n_days),
       "limitations":[
         "No trading or realized exit on most days means no claim of daily income",
         "Realized-exit-day proxy is not mark-to-market NAV, cannot recreate combined daily account equity",
         "Daily55 long-hold positions can gain/lose on days with no exit",
         "0.7/0.3 weighted daily net proxy uses standalone 0.5% risk-per-trade returns and does not model daily rebalancing",
         "Only pre-existing model parameters tested; no after-the-fact day filter",
         "Fees incl GST and $5/side slip were modeled upstream; funding and actual order book depth omitted",
         "All 2025 and 2026 data already researched; no untouched forward sample",
       ]
    }
    out.to_csv(OUT/"daily_realized_exit_proxy.csv",index=False)
    monthly.to_csv(OUT/"monthly_daily_outcomes.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(assessment,indent=2)+"\n")
    lines=["# Stage18 70/30 daily-realized profitability audit","",
      "## Real monthly account NAV snapshot (source backtest)","",
      f"- 22-month compounded net: **{assessment['verified_compounded_monthly_net_22m_pct']:.4f}%**",
      f"- Profitable/loss/flat months: **{assessment['verified_months_profitable']}/{assessment['verified_months_losing']}/{assessment['verified_months_flat']}**",
      "",
      "## Daily REALIZED-EXIT proxy (NOT daily account PnL)","",
      f"- Total IST calendar dates: **{n_days}**",
      f"- Days with one or more trade exits: **{trade_days}**",
      f"- Positive realized-exit days: **{positives}**",
      f"- Negative realized-exit days: **{negative}**",
      f"- No-exit days: **{noexit}**",
      f"- Positive-calendar-day frequency: **{100*positives/n_days:.2f}%**",
      f"- Positive fraction of exit days: **{100*positives/trade_days:.2f}%**" if trade_days else "- No realized exits",
      f"- Source core and Donchian closed trades: **{len(core)}** / **{len(swing)}**",
      "", "## Monthly counts of daily realized exits","",monthly.to_markdown(index=False),"",
      "## Important limitations",""]
    lines.extend("- "+x for x in assessment["limitations"])
    lines.extend(["", "Stage18 historical 70/30 results are retrospective and a synthetic MONTHLY blend.",
      "It is NOT possible to infer profitable every day from profitable months or positive exit days.",
      ""])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines))
    print("DAILY_REALIZED_EXIT_AUDIT_COMPLETE",json.dumps({k:v for k,v in assessment.items() if k!="limitations"}))

if __name__=="__main__":main()
