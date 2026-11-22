#!/usr/bin/env python3
"""Postmortem of the verified three-best ST combined portfolio, 2025/2026.

Does not respecify or optimize any strategy, or take new historical trades.
Audits actual executed positions and actual exit months, plus ST regime.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_supertrend_15m_line_touch as base

SRC=Path("analysis/st_three_best_positive_months_combined_20261122")
OUT=Path("analysis/st_three_best_2026_failure_postmortem_20261122")
OUT.mkdir(parents=True,exist_ok=True)

POSITIONS=pd.read_csv(SRC/"selected_positions_by_policy.csv.gz")
MONTHLY=pd.read_csv(SRC/"entry_exit_and_mark_to_market_monthly.csv")
POLICIES=("standalone_line_touch","standalone_bullish_flip",
          "standalone_flip_breakout","exclusive_all_three_default",
          "exclusive_all_three_flip_first",
          "exclusive_touch_plus_flip","exclusive_touch_plus_breakout")

def group_summary(data,cols):
    rows=[]
    for key,g in data.groupby(cols,dropna=False):
        if not isinstance(key,tuple):key=(key,)
        n=len(g)
        wins=g[g.net_pts>0]
        losses=g[g.net_pts<=0]
        pos=float(wins.net_pts.sum())
        neg=float(losses.net_pts.sum())
        result=dict(zip(cols,key))
        result.update(
          trades=n,wins=len(wins),losses=len(losses),
          win_rate_pct=round(100*len(wins)/n,2),
          net_pts=round(float(g.net_pts.sum()),2),
          gross_win_pts=round(pos,2),
          gross_loss_pts=round(neg,2),
          mean_win_pts=round(float(wins.net_pts.mean()),2) if len(wins) else None,
          mean_loss_pts=round(float(losses.net_pts.mean()),2) if len(losses) else None,
          median_net_pts=round(float(g.net_pts.median()),2),
          max_loss_trade_pts=round(float(g.net_pts.min()),2),
          max_win_trade_pts=round(float(g.net_pts.max()),2),
          profit_factor=round(pos/abs(neg),3) if neg<0 else None,
          avg_hold_minutes=round(float(g.holding_minutes.mean()),2))
        rows.append(result)
    return pd.DataFrame(rows)

def market_regime():
    m,b,files=base.load()
    st,dir=base.supertrend(b)
    c=b.close.to_numpy(float)
    br=np.where((dir[1:]==-1)&(dir[:-1]!=-1))[0]+1
    ends=np.searchsorted(np.where((dir[1:]==1)&(dir[:-1]!=1))[0]+1,br,side="right")
    bear=np.where((dir[1:]==1)&(dir[:-1]!=1))[0]+1
    length=np.array([int(bear[ends[k]]-v) if ends[k]<len(bear)
                     else len(b)-int(v) for k,v in enumerate(br)])
    ist=b.index.tz_convert("Asia/Kolkata")
    times=ist[br]
    flip=pd.DataFrame(dict(
        month=times.strftime("%Y-%m"),year=times.strftime("%Y"),
        bullish_cycle_bars=length,
        green_1hr_or_less=(length<=4).astype(int),
        green_4hr_or_less=(length<=16).astype(int),
        green_8hr_or_less=(length<=32).astype(int)))
    flip=flip[(flip.month>="2025-01")&(flip.month<="2026-11")]
    summaries=[]
    for label,subset in [
        ("2025_full",flip[flip.year=="2025"]),
        ("2025_JanOct",flip[(flip.month>="2025-01")&(flip.month<="2025-11")]),
        ("2026_JanOct",flip[(flip.month>="2026-01")&(flip.month<="2026-11")])]:
        n=len(subset)
        summaries.append(dict(
            period=label,bullish_ST_flips=n,
            flips_shorter_than_or_eq_1hr=int(subset.green_1hr_or_less.sum()),
            flips_shorter_than_or_eq_4hr=int(subset.green_4hr_or_less.sum()),
            flips_shorter_than_or_eq_8hr=int(subset.green_8hr_or_less.sum()),
            pct_flips_revert_within_1hr=round(100*subset.green_1hr_or_less.mean(),2),
            pct_flips_revert_within_4hr=round(100*subset.green_4hr_or_less.mean(),2),
            pct_flips_revert_within_8hr=round(100*subset.green_8hr_or_less.mean(),2),
            median_bull_run_15m_bars=float(subset.bullish_cycle_bars.median())))
    reg=pd.DataFrame(summaries)
    reg.to_csv(OUT/"supertrend_market_regime_2025_2026.csv",index=False)
    flip.to_csv(OUT/"bullish_ST_cycle_duration_audit.csv",index=False)
    return reg

def main():
    p=POSITIONS[POSITIONS.policy.isin(POLICIES)].copy()
    assert p.groupby("policy").size()["exclusive_all_three_default"]==143
    p["year_exit"]=p.exit_month_ist.str.slice(0,4)
    p["year_entry"]=p.entry_month_ist.str.slice(0,4)
    p["period_exit"]=np.select(
        [p.exit_month_ist.between("2025-01","2025-10"),
         p.exit_month_ist.between("2025-01","2025-12"),
         p.exit_month_ist.between("2026-01","2026-10")],
         ["2025_JanOct","2025_full","2026_JanOct"],default="other")
    common=p[p.exit_month_ist.between("2025-01","2026-10")].copy()
    # 2025 full, 2025 Jan-Oct, 2026 Jan-Oct: explicit overlapping date cohorts.
    split=pd.concat([
        common[common.exit_month_ist.between("2025-01","2025-12")].assign(
              segment="2025_full"),
        common[common.exit_month_ist.between("2025-01","2025-10")].assign(
              segment="2025_JanOct"),
        common[common.exit_month_ist.between("2026-01","2026-10")].assign(
              segment="2026_JanOct")],ignore_index=True)
    overall=group_summary(split,["policy","segment"])
    strategic=group_summary(split,["policy","segment","strategy"])
    cause=group_summary(split,["policy","segment","reason"])
    monthstrategy=group_summary(common,["policy","exit_month_ist","strategy"])
    monthcause=group_summary(common,["policy","exit_month_ist","reason"])
    worst=common[common.policy=="exclusive_all_three_default"].sort_values(
        "net_pts").head(30).copy()
    worst["dollars_1btc_equiv"] = worst.net_pts
    default=p[p.policy=="exclusive_all_three_default"]
    dropped=p[p.policy=="exclusive_all_three_flip_first"]
    assert len(default)==143 and len(dropped)==143
    monthly=MONTHLY[MONTHLY.policy.isin(POLICIES)].copy()
    assert abs(float(default.net_pts.sum())-12898.88)<0.02
    for name,df in [
       ("postmortem_by_policy_and_period",overall),
       ("postmortem_by_policy_period_and_strategy",strategic),
       ("postmortem_by_policy_period_and_exit_reason",cause),
       ("postmortem_by_exit_month_and_strategy",monthstrategy),
       ("postmortem_by_exit_month_and_reason",monthcause),
       ("top30_losing_combined_trades",worst)]:
        df.to_csv(OUT/(name+".csv"),index=False)
    reg=market_regime()
    cols=["policy","segment","trades","wins","losses","win_rate_pct",
          "net_pts","gross_win_pts","gross_loss_pts","mean_win_pts",
          "mean_loss_pts","max_loss_trade_pts","profit_factor"]
    dl=overall[overall.policy=="exclusive_all_three_default"][cols]
    per=strategic[strategic.policy=="exclusive_all_three_default"]
    c=cause[cause.policy=="exclusive_all_three_default"]
    bymonth=monthly[monthly.policy=="exclusive_all_three_default"]
    by2026=bymonth[bymonth.month_ist.str.startswith("2026")]
    deficits=by2026[by2026.exit_month_realized_net_pts<0]
    drivers=monthstrategy[(monthstrategy.policy=="exclusive_all_three_default")&
                          (monthstrategy.exit_month_ist.isin(deficits.month_ist))]
    report=[
       "# BTCUSD 15m why portfolio failed Jan-Oct 2026 — verified trade postmortem",
       "",
       "Original three selected configurations, no retuning or future leakage;",
       "one-position portfolio default breakout>touch>flip, one ST bullish",
       "cycle; all net metrics in 1-BTC-equivalent price points.",
       "",
       "## Primary 2025 vs Jan-Oct 2026 trade attribution",
       dl.to_markdown(index=False),
       "",
       "## Contribution by strategy and period (actual exit month)",
       per[["segment","strategy","trades","wins","losses","net_pts",
            "gross_win_pts","gross_loss_pts","mean_win_pts","mean_loss_pts",
            "max_loss_trade_pts"]].to_markdown(index=False),
       "",
       "## Contribution by exit reason and period",
       c[["segment","reason","trades","wins","losses",
          "net_pts","mean_win_pts","mean_loss_pts"]].to_markdown(index=False),
       "",
       "## 2026 losing months' precise strategy contributions",
       drivers[["exit_month_ist","strategy","trades","wins","losses",
            "net_pts","gross_win_pts","gross_loss_pts"]].to_markdown(index=False),
       "",
       "## 2026 all months",
       by2026[["month_ist","newly_entered_trades",
                "exit_month_realized_net_pts"]].to_markdown(index=False),
       "",
       "## Worst individual trades in the combined portfolio",
       worst[["strategy","entry_utc","exit_utc","entry_fill",
              "exit_fill","net_pts","reason","holding_minutes"]].head(12).to_markdown(index=False),
       "",
       "## Supertrend 15m bullish cycle regime diagnostic",
       reg.to_markdown(index=False),
       "",
       "## Important interpretation",
       "2025 full year has 12 months, 2026 Jan-Oct has 10 months.",
       "Use the 2025 Jan-Oct segment for apples-to-apples length.",
       "Exit reasons are empirical from 1m replay; this test does not",
       "prove market microstructure caused the profitability change.",
       "Price data is the same archive used to SELECT these exact settings.",
       "No independent holdout; no margin/liquidation/funding models.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    (OUT/"quality.json").write_text(json.dumps(dict(
      source_trade_ledger=str(SRC/"selected_positions_by_policy.csv.gz"),
      linked_policies=POLICIES,periods=["2025_full","2025_JanOct","2026_JanOct"],
      verified_baseline_default_143_trades=True,
      no_changes_to_trade_fills=True,attribution="actual_exit_month_IST",
      market_regime="15m ST bullish cycle survival distribution",
      interpreted_without_funding_liquidation=True
      ),indent=2)+"\n")
    print("VERIFIED_PORTFOLIO_2026_POSTMORTEM",flush=True)
    print("DEFAULT_YEAR_SPLIT\n"+dl.to_string(index=False),flush=True)
    print("DEFAULT_STRATEGY_ATTRIBUTION\n"+per.to_string(index=False),flush=True)
    print("DEFAULT_EXIT_REASON_ATTRIBUTION\n"+c.to_string(index=False),flush=True)
    print("SUPER_TREND_REGIME\n"+reg.to_string(index=False),flush=True)
    print("WORST_TRADES\n"+worst.head(8)[
        ["strategy","entry_utc","exit_utc","net_pts","reason"]].to_string(index=False),flush=True)

if __name__=="__main__":
    main()
