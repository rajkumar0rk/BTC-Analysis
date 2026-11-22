#!/usr/bin/env python3
"""Audit maximum positive months among three existing 15m ST entry variants.

Read archived fixed percentage R:R grid; no new selection, candle generation
or fresh backtest. These statistics attribute P&L to ENTRY month (the
backtest's preexisting convention), which is not cash-realized exit month.
"""
from pathlib import Path
import json
import pandas as pd

ROOT=Path("analysis/st_touch_flip_breakout_three_way_20261122")
INPUT=ROOT/"all_36036_fixed_percent_combinations.csv.gz"
OUT=ROOT/"monthly_win_maximizers"
OUT.mkdir(parents=True,exist_ok=True)
df=pd.read_csv(INPUT)
assert len(df)==36036
KINDS=("after_line_touch","after_bullish_flip","flip_plus_green_breakout")
SCOPES={
    "same_filters":lambda x:x[(x.vol_filter=="vol_ge_1p0") & (x.atr_filter=="atrpct_ge_0p20")],
    "all_filters":lambda x:x,
}
results=[]
for kind in KINDS:
    x=df[df.entry_type==kind].copy()
    assert len(x)==12012
    for scope,fn in SCOPES.items():
        z=fn(x)
        for min_trades in (1,20,50,75,100):
            for net_constraint in ("any_net","net_positive"):
                v=z[z.trades>=min_trades]
                if net_constraint=="net_positive": v=v[v.net_pts>0]
                if v.empty:continue
                v=v.sort_values(
                  ["profitable_months","net_pts","losing_months","trades"],
                  ascending=[False,False,True,False])
                h=v.iloc[0]
                results.append(dict(
                    entry_type=kind,scope=scope,min_trades=min_trades,
                    constraint=net_constraint,
                    positive_months=int(h.profitable_months),
                    losing_months=int(h.losing_months),
                    flat_months=int(h.flat_months),
                    sl_pct=float(h.sl_pct),tp_pct=float(h.tp_pct),
                    trades=int(h.trades),wins=int(h.wins),
                    losses=int(h.trades-h.wins),win_rate_pct=float(h.win_rate_pct),
                    net_pts=float(h.net_pts),max_drawdown_pts=float(h.max_drawdown_pts),
                    volume_filter=h.vol_filter,atr_filter=h.atr_filter,
                    candidate_count=int(len(v))))
output=pd.DataFrame(results)
output.to_csv(OUT/"maximum_profitable_months_by_strategy_and_constraint.csv",index=False)
# Full list near top; sort by months, then net points, preserving losers
df.sort_values(["profitable_months","net_pts"],ascending=[False,False]).head(150).to_csv(
    OUT/"top150_month_win_settings.csv",index=False)
same=output[(output.scope=="same_filters")&(output.min_trades==20)]
all50=output[(output.scope=="all_filters")&(output.min_trades==50)]
cols=["entry_type","constraint","positive_months","losing_months",
      "flat_months","sl_pct","tp_pct","trades","wins","losses",
      "win_rate_pct","net_pts","max_drawdown_pts","volume_filter","atr_filter"]
notes=[
  "# BTCUSD 15m: Highest profitable month count, three ST strategies",
  "",
  "Data from the verified three-way grid, 36,036 settings, 22 complete",
  "entry months Jan 2025 through Oct 2026. Prior ST closing exit retained.",
  "Fixed % SL/TP, no profit protection; 1m stop-first OHLC replay.",
  "Net BTC price points after 0.05% taker each way, 18% GST and 5 points",
  "adverse slippage each way. No liquidation or margin modeled.",
  "",
  "IMPORTANT: Monthly P&L is credited to ENTRY month in this historic",
  "grid, even if a position closes in a later month. It does not establish",
  "monthly realized cash P&L.",
  "",
  "## Highest positive months with SAME filters, >=20 trades",
  same[cols].to_markdown(index=False),
  "",
  "## Highest positive months across all 42 filters, >=50 trades",
  all50[cols].to_markdown(index=False),
  "",
  "## Entire benchmark settings with top monthly positive months",
  df.sort_values(["profitable_months","net_pts"],ascending=[False,False]).head(20)[
      ["entry_type","vol_filter","atr_filter","sl_pct","tp_pct",
       "trades","wins","net_pts","profitable_months","losing_months",
       "flat_months"]].to_markdown(index=False),
  "",
  "## Warning",
  "Maximizing winning months across 36,036 previously viewed configurations",
  "is in-sample optimization. A config with many positive months may lose",
  "overall (the few bad months can erase many small winning months).",
  "To claim durable consistency, require out-of-sample and exit-month",
  "cashflow/equity mark-to-market audit with liquidation and funding.",
]
(OUT/"REPORT.md").write_text("\n".join(notes)+"\n")
(OUT/"quality.json").write_text(json.dumps(dict(
    source="all_36036_fixed_percent_combinations.csv.gz",
    configurations=len(df),
    monthly_attribution="entry month IST not actual exit month",
    total_months=22,from_month="2025-01",to_month="2026-10",
    methodology="positive_months count from prior backtest; no new replay",
    no_untouched_out_of_sample=True),indent=2)+"\n")
print("MAX_POSITIVE_MONTHS_SAME_FILTERS\n"+same[cols].to_string(index=False),flush=True)
print("MAX_POSITIVE_MONTHS_ALL_FILTERS_50\n"+all50[cols].to_string(index=False),flush=True)
print("POSITIVE_MONTH_AUDIT_COMPLETED",len(df),flush=True)

if __name__=="__main__":main()
