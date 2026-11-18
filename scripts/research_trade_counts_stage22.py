#!/usr/bin/env python3
"""Stage 22 — audited monthly win/loss trade counts for Stage18 and Stage20.

Retain Stage14, Stage18, Stage20, Stage21 originals unchanged.
Verify original Actions artifacts from Stage15, 17, 19 and reconcile
model equity returns to Stage18 and Stage20 month-level reports.
Trade counts are settled on actual EXIT calendar month in Asia/Kolkata.
The 1D swing strategy marks OPEN positions to market at month-end, so a
month's PnL can be non-zero with 0 closed swing trades that month.

"Win" means after-fee / after-GST / after-assumed-slippage net_R>0;
loss <0; flat ==0. Each component is a separate sleeve and may overlap.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

OUT=Path("analysis/institutional_discovery_stage22_trade_audit")
BASE18=Path("analysis/institutional_discovery_stage18_monthly_dual_strategy")
BASE20=Path("analysis/institutional_discovery_stage20_three_sleeve")
S19=Path("analysis/institutional_discovery_stage19_new_1h_patterns")
MONTHS=pd.period_range("2025-01","2026-11",freq="M").astype(str).tolist()
S15_FILTER="1h_volume_ratio_le_1p2"
S15_GUARD="weekly_minus_3R"
S17_MODEL="1D_channel_20_no_trend_filter_trail_3atr"
S19_MODEL="strong_momentum_6h__4h_adx_le20__3R__480min"
TOL=0.025

def standardize(ledger, model, timestamp_col, net_col, part):
    z=ledger.copy()
    z["exit_unix"]=z[timestamp_col].astype("int64")
    z["net_R"]=z[net_col].astype(float)
    z["month_ist"]=pd.to_datetime(z.exit_unix,unit="s",utc=True).dt.tz_convert(
        "Asia/Kolkata").dt.strftime("%Y-%m")
    z["side"]=z["direction"] if "direction" in z else z["side"]
    z["component"]=part
    if (~np.isfinite(z.net_R.to_numpy(float))).any():
        raise AssertionError("Nonfinite R in "+part)
    if not set(z.month_ist).issubset(set(MONTHS)):
        raise AssertionError("Out of range exit month "+part)
    return z[["component","side","month_ist","exit_unix","net_R"]]

def source_trade_ledgers(stage15,stage17,stage19):
    a=pd.read_csv(stage15)
    a=a[(a["filter"]==S15_FILTER)&(a.guard==S15_GUARD)].copy()
    a["direction"]=np.where(a.side=="LONG","LONG","SHORT")
    a=standardize(a,S15_FILTER,"exit_unix","net_R","quiet_range")
    b=pd.read_csv(stage17)
    b=b[b.model==S17_MODEL].copy()
    b=standardize(b,S17_MODEL,"exit_utc_unix","net_R","daily20_swing")
    c=pd.read_csv(stage19)
    c=c[c.model==S19_MODEL].copy()
    c=standardize(c,S19_MODEL,"exit_unix","net_R","hourly_momentum")
    if len(a)!=64:
        raise AssertionError(f"Stage15 quiet volume expected 64 trades, found {len(a)}")
    if len(b)!=24:
        raise AssertionError(f"Stage17 Daily20 expected 24 trades, found {len(b)}")
    if len(c)!=119:
        raise AssertionError(f"Stage19 momentum expected 119 trades, found {len(c)}")
    return pd.concat([a,b,c],ignore_index=True)

def verify_ledger(trades):
    ref18=pd.read_csv(BASE18/"monthly_blended_returns.csv")
    ref18=ref18[
        (ref18.stage15=="quiet_1h_weekly_3R")&
        (ref18.stage17==S17_MODEL)&
        (np.isclose(ref18.swing_weight,.25))
    ].sort_values("month_ist")
    ref20=pd.read_csv(BASE20/"selected_month_by_month.csv").sort_values("month_ist")
    ref19=pd.read_csv(S19/"monthly_results.csv")
    ref19=ref19[ref19.model==S19_MODEL].sort_values("month_ist")
    assert ref18.month_ist.tolist()==MONTHS
    assert ref20.month_ist.tolist()==MONTHS
    assert ref19.month_ist.tolist()==MONTHS
    rows=[]
    for m in MONTHS:
        def group(comp):
            data=trades[(trades.component==comp)&(trades.month_ist==m)]
            return dict(n=len(data),wins=int((data.net_R>1e-9).sum()),
                        losses=int((data.net_R<-1e-9).sum()),
                        flats=int((data.net_R.abs()<=1e-9).sum()),
                        net_R=float(data.net_R.sum()),
                        long=int((data.side=="LONG").sum()),
                        short=int((data.side=="SHORT").sum()))
        a,b,c=[group(z) for z in ["quiet_range","daily20_swing","hourly_momentum"]]
        refa=ref18.loc[ref18.month_ist==m].iloc[0]
        refc=ref19.loc[ref19.month_ist==m].iloc[0]
        refp=ref20.loc[ref20.month_ist==m].iloc[0]
        q_r=100*(np.prod(1+.005*trades[
            (trades.component=="quiet_range")&(trades.month_ist==m)
        ].net_R.to_numpy(float))-1)
        h_r=100*(np.prod(1+.005*trades[
            (trades.component=="hourly_momentum")&(trades.month_ist==m)
        ].net_R.to_numpy(float))-1)
        if abs(q_r-float(refa.range_component_pct))>TOL:
            raise AssertionError(f"Stage15 source PnL disagrees {m}: {q_r} vs {refa.range_component_pct}")
        if abs(h_r-float(refc.modeled_return_pct))>TOL:
            raise AssertionError(f"Stage19 source PnL disagrees {m}: {h_r} vs {refc.modeled_return_pct}")
        expected18=.75*float(refa.range_component_pct)+.25*float(refa.swing_component_pct)
        if abs(expected18-float(refa.portfolio_pct))>.005:
            raise AssertionError(f"Stage18 source PnL disagrees {m}")
        expected20=.9*expected18+.1*h_r
        if abs(expected20-float(refp.portfolio_month_pct))>.03:
            raise AssertionError(f"Stage20 source PnL disagrees {m}")
        total=a["n"]+b["n"]+c["n"]
        wins=a["wins"]+b["wins"]+c["wins"]
        losses=a["losses"]+b["losses"]+c["losses"]
        flats=a["flats"]+b["flats"]+c["flats"]
        if total!=wins+losses+flats:
            raise AssertionError("trade count arithmetic not valid")
        rows.append(dict(month_ist=m,
            stage18_return_pct=float(refa.portfolio_pct),
            stage20_return_pct=float(refp.portfolio_month_pct),
            all_three_sleeve_closed_trades=total,
            winning_trades=wins,
            losing_trades=losses,
            flat_trades=flats,
            win_rate_pct=(100*wins/total if total else 0),
            quiet_sleeve_trades=a["n"],quiet_wins=a["wins"],quiet_losses=a["losses"],
            daily_swing_trades=b["n"],daily_swing_wins=b["wins"],daily_swing_losses=b["losses"],
            hourly_momentum_trades=c["n"],hourly_momentum_wins=c["wins"],hourly_momentum_losses=c["losses"],
            net_R_sum_unweighted=a["net_R"]+b["net_R"]+c["net_R"],
            all_sleeves_long=a["long"]+b["long"]+c["long"],
            all_sleeves_short=a["short"]+b["short"]+c["short"]))
    return pd.DataFrame(rows),ref18,ref20

def annual(months):
    rows=[]
    for year in ["2025","2026"]:
        z=months[months.month_ist.str.startswith(year)]
        for key in ["stage18","stage20"]:
            vals=z[f"{key}_return_pct"].to_numpy(float)
            rows.append(dict(strategy=key,year=year,
                observed_months=len(z),
                profitable_months=int((vals>1e-9).sum()),
                losing_months=int((vals<-1e-9).sum()),
                neutral_months=int((abs(vals)<=1e-9).sum()),
                total_trades=int(z.all_three_sleeve_closed_trades.sum())
                    if key=="stage20" else int((
                        z.quiet_sleeve_trades+z.daily_swing_trades).sum()),
                winning_trades=int(z.winning_trades.sum())
                    if key=="stage20" else int((
                        z.quiet_wins+z.daily_swing_wins).sum()),
                losing_trades=int(z.losing_trades.sum())
                    if key=="stage20" else int((
                        z.quiet_losses+z.daily_swing_losses).sum()),
                flat_trades=int(z.flat_trades.sum()),
                compounded_return_pct=round(float(
                    100*(np.prod(1+vals/100)-1)),4)))
    return pd.DataFrame(rows)

def main():
    cli=argparse.ArgumentParser()
    for p in ["stage15","stage17","stage19"]:
        cli.add_argument("--"+p,required=True,type=Path)
    args=cli.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    trades=source_trade_ledgers(args.stage15,args.stage17,args.stage19)
    months,_,_=verify_ledger(trades)
    totals=annual(months)
    months.to_csv(OUT/"monthly_trade_win_loss_audit.csv",index=False)
    totals.to_csv(OUT/"yearly_trade_win_loss_summary.csv",index=False)
    trades.to_csv(OUT/"closed_trade_details.csv.gz",index=False,compression="gzip")
    quality=dict(
        sources=dict(stage15="GH Actions 44120459865 Stage15 original full ledger",
           stage17="GH Actions 44128535269 Stage17 original full ledger",
           stage19="GH Actions 44234824670 Stage19 original full ledger"),
        preserved_candidates=["Stage14","Stage18","Stage20","Stage21"],
        months=MONTHS, stage18_definition="75% quiet-volume pullback / 25% Daily20 Donchian",
        stage20_definition="67.5% quiet-volume / 22.5% Daily20 Donchian / 10% 1H strong momentum breakout",
        cost_model="Net_R after standard 0.05% taker on entry and exit, GST 18%, 5 points adverse slippage per side",
        total_closed_component_trades=len(trades),
        annual=totals.to_dict("records"),
        limitations=[
            "Counted closed component trades, not one unified execution position; simultaneous overlapping sleeves can occur",
            "Stage18 counts only range + daily swing component; Stage20 adds momentum component",
            "Monthly percentage accounts for Daily swing mark-to-market open positions; its trade counts are based on EXIT month",
            "Monthly net R sums across sleeves ignore allocation weights and must not be interpreted as portfolio return",
            "No margin, contract minimums, funding, rebalancing, actual order book execution/impact",
            "Max drawdown from monthly NAV is not true intraday drawdown",
            "2026 November through 16th and 2026 Oct 31 source missing",
            "Only modeled historical returns are available; no future month can be guaranteed positive"])
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    report=[
        "# Stage22 — Audited monthly BTC trade counts and net returns (2025 + 2026)",
        "",
        "Stage14, 18, 20 and 21 preserved unchanged.",
        "**2025 and 2026 profitable months are both required**; no-trade/flat months not counted.",
        "",
        "## Yearly, fee/GST/slippage-adjusted figures",
        totals.to_markdown(index=False),"",
        "## Actual closed trades and monthly hypothetical returns",
        months[["month_ist","all_three_sleeve_closed_trades",
            "winning_trades","losing_trades","flat_trades","win_rate_pct",
            "stage18_return_pct","stage20_return_pct"]].to_markdown(index=False),"",
        "## Component trade counts",
        months[["month_ist","quiet_sleeve_trades","quiet_wins","quiet_losses",
          "daily_swing_trades","daily_swing_wins","daily_swing_losses",
          "hourly_momentum_trades","hourly_momentum_wins","hourly_momentum_losses"]].to_markdown(index=False),"",
        "## Limitations",
        *["- "+s for s in quality["limitations"]],"",
        "Detailed original closed trade ledger is archived as GitHub Actions artifact.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE22_SUCCESS "+json.dumps({"trades":len(trades),
        "months":len(months),"yearly":totals.to_dict("records")}))
    print("MONTHLY\n"+months[["month_ist","all_three_sleeve_closed_trades",
        "winning_trades","losing_trades","flat_trades",
        "stage18_return_pct","stage20_return_pct"]].to_string(index=False))
    print("ANNUAL\n"+totals.to_string(index=False))
if __name__=="__main__":
    main()
