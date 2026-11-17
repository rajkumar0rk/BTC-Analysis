#!/usr/bin/env python3
"""Monthly audit of the exact Stage12 strategy using its original Actions trade ledger."""
from pathlib import Path
import argparse
import json
import pandas as pd

PATTERN = "06_inside_bar_break"
ENVIRONMENT = "aligned_trend_plus_5m_compression_break"
RATIO = 2.0
HOLD = 120
STAGE12 = Path("analysis/institutional_discovery_stage12_pretrend")
PERIODS = ["2025_train","2026_H1_validation","2026_H2_seen_recheck","2026_Nov_recent_exploratory"]
EXPECTED = [(34,155.80),(22,-61.77),(7,125.45),(1,1023.18)]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True, type=Path)
    args=ap.parse_args()
    data=pd.read_csv(args.ledger)
    required={"pattern","environment","reward_R","hold_minutes","entry_unix",
              "net_pts","period","direction","risk_pts"}
    if required-set(data.columns):
        raise ValueError("Ledger missing fields: "+str(required-set(data.columns)))
    selected=data[(data.pattern==PATTERN)&
                  (data.environment==ENVIRONMENT)&
                  (data.reward_R==RATIO)&
                  (data.hold_minutes==HOLD)].copy().sort_values("entry_unix")
    if selected.empty: raise ValueError("No exact strategy trades in artifact")
    reference=pd.read_csv(STAGE12/"strategy_results.csv")
    ref=reference[(reference.pattern==PATTERN)&
                  (reference.environment==ENVIRONMENT)&
                  (reference.reward_R==RATIO)&
                  (reference.hold_minutes==HOLD)&
                  (reference.fee_model=="standard_taker")]
    if len(ref)!=len(PERIODS): raise AssertionError("Stage12 summary periods inconsistent")
    for period,(expected_count,expected_mean) in zip(PERIODS,EXPECTED):
        rows=selected[selected.period==period]
        record=ref[ref.period==period]
        if len(record)!=1 or len(rows)!=expected_count or len(rows)!=int(record.trades.iloc[0]):
            raise AssertionError("Stage12 trade-count mismatch for "+period)
        if (abs(float(rows.net_pts.mean())-float(record.avg_net_pts.iloc[0]))>.02 or
            abs(float(rows.net_pts.mean())-expected_mean)>.02):
            raise AssertionError("Stage12 net-mean mismatch for "+period)
    selected["entry_utc"]=pd.to_datetime(selected.entry_unix,unit="s",utc=True)
    selected["entry_ist"]=selected.entry_utc.dt.tz_convert("Asia/Kolkata")
    selected["month"]=selected.entry_ist.dt.strftime("%Y-%m")
    selected["profitable"]=selected.net_pts>0
    months=pd.period_range("2025-01","2026-11",freq="M").astype(str)
    grp=selected.groupby("month").agg(
        trades=("net_pts","size"),
        long_trades=("direction",lambda x:int((x=="LONG").sum())),
        short_trades=("direction",lambda x:int((x=="SHORT").sum())),
        winning_trades=("profitable","sum"),
        net_points=("net_pts","sum"),
        avg_points_per_trade=("net_pts","mean"),
        biggest_winner=("net_pts","max"),
        worst_loser=("net_pts","min"))
    monthly=grp.reindex(months,fill_value=0)
    monthly.index.name="month_ist"
    monthly["win_pct"]=(100*monthly.winning_trades/
                         monthly.trades.replace(0,float("nan"))).fillna(0)
    monthly["status"]=monthly.apply(
        lambda z:"No trades" if z.trades==0 else
        "Profit" if z.net_points>0 else
        "Loss" if z.net_points<0 else "Flat",axis=1)
    monthly["coverage_note"]=""
    monthly.loc["2026-10","coverage_note"]="2026-10-31 missing in source archive"
    monthly.loc["2026-11","coverage_note"]="Partial: through 2026-11-16 23:59 UTC"
    for field in ("net_points","avg_points_per_trade","biggest_winner","worst_loser","win_pct"):
        monthly[field]=monthly[field].round(2)
    if int(monthly.trades.sum())!=len(selected):
        raise AssertionError("Monthly trade count reconciliation failed")
    if abs(monthly.net_points.sum()-selected.net_pts.sum())>.15:
        raise AssertionError("Monthly net points reconciliation failed")
    monthly.to_csv(STAGE12/"monthly_inside_bar_2R_IST.csv")
    quality={
        "pattern":PATTERN,"environment":ENVIRONMENT,"target_R":RATIO,
        "max_holding_minutes":HOLD,
        "source_action_run":44108340139,
        "source_artifact_id":14339268107,
        "time_zone":"Asia/Kolkata, month of entry",
        "trades":len(selected),
        "profitable_months":int((monthly.status=="Profit").sum()),
        "losing_months":int((monthly.status=="Loss").sum()),
        "flat_months":int((monthly.status=="Flat").sum()),
        "no_trade_months":int((monthly.status=="No trades").sum()),
        "net_total_price_points_equivalent":round(float(selected.net_pts.sum()),2),
        "year_summary":{},
        "limitations":[
            "Modeled net BTC quote-price points, not dollar-account return",
            "Standard taker fees, GST and slippage included; funding and order-book impact not",
            "2026-10-31 missing from source, 2026-11 partial",
            "This original historical dataset was previously researched; not an untouched forward test",
            "Entry month grouped in IST; no trades are not a profitable month"
        ]
    }
    for year in ("2025","2026"):
        y=monthly.loc[monthly.index.str.startswith(year)]
        quality["year_summary"][year]={
            "months":len(y),"profitable":int((y.status=="Profit").sum()),
            "loss":int((y.status=="Loss").sum()),
            "no_trades":int((y.status=="No trades").sum()),
            "trades":int(y.trades.sum()),"net_pts":round(float(y.net_points.sum()),2)}
    (STAGE12/"monthly_inside_bar_2R_quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    report=[
        "# Stage 12 exact inside-bar 2R strategy: Monthly consistency audit",
        "",
        "Pattern: 06_inside_bar_break; market state: aligned_trend_plus_5m_compression_break.",
        "2R reward, 120-minute hold, original structurally derived stop. No change to entries.",
        "Months assigned by entry timestamp in Asia/Kolkata.",
        "Net points include modeled 0.05% taker fees per side, 18% GST and 5 points per-side slippage.",
        "",
        "Profitable months: "+str(quality["profitable_months"])+"/"+str(len(monthly)),
        "Losing months: "+str(quality["losing_months"]),
        "Months without trades: "+str(quality["no_trade_months"]),
        "Net total points equivalent: "+str(quality["net_total_price_points_equivalent"]),
        "",
        monthly.reset_index()[["month_ist","trades","winning_trades","win_pct",
            "net_points","status","coverage_note"]].to_markdown(index=False),
        "",
        "The trade counts and averages for the four Stage12 research periods were",
        "reconciled against the original saved strategy summary and original Actions artifact.",
        "",
        "Limitations:",
        *["- "+s for s in quality["limitations"]],
    ]
    (STAGE12/"MONTHLY_INSIDE_BAR_REPORT.md").write_text("\n".join(report)+"\n")
    print("MONTHLY_STAGE12_DONE "+json.dumps(quality))
    print(monthly.reset_index()[["month_ist","trades","winning_trades",
                                "win_pct","net_points","status"]].to_string(index=False))

if __name__=="__main__":
    main()
