#!/usr/bin/env python3
"""ALL MONTHS (no weekly selection): full-grid 1H EMA20+Supertrend Trailing Stop Points.

For BTCUSD and ETHUSD, backtest ALL 7 activation x 14 extra trailing-stop
point configurations for 22 complete UTC calendar months (2025-01 through
2026-10). Uses existing saved Delta India production trade 1m and MARK 1m
archives (no API calls). The November 2026 incomplete data is EXCLUDED from
every reported metric and monthly CSV. For each asset and config, evaluate
MARK-triggered and TRADED-triggered stop replay as independent sensitivities.

Additional Trailing Stop Points enabled; ORIGINAL Fixed Trailing Distance OFF.
Position rule from our TradingView script: once best price advances activation
points, set additional trailing-stop candidate best favorable observed price
minus stop points (LONG), or plus stop points (SHORT). Tighten ONLY, after
the complete minute; order effective starting following minute. Existing
initial protective stop is 2*ATR14; opposite ST flip exit preserved.

Historical reference trading size ~US$1,000 notional per trade. No depleted-
wallet guard, actual portfolio-margin liquidation, funding, spread, latency,
order book, nor guaranteed fills. 0.05% taker EACH leg + 18% GST, no voucher.
This is NOT a realizable US$100-equity return and NOT Demo testnet history.

Selection/ranking shows highest number of profitable months separately from
greatest full-period net return; objective results are IN SAMPLE. 2025/train
and Jan-Oct 2026/holdout are reported separately. Requires at least 100
closed trades for the monthly-consistency ranking, and a month is profitable
ONLY if that month net USD > 0, zero-trade months never count as profitable.

Existing grid summary is used to assert we exactly reproduce full-period net
from earlier research. All parameter-month results are saved, not only winners.
NO edits to strategy code, main branch, or trading infrastructure.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

from optimize_1h_additional_trailing_stop_points_20261121 import (
    ACTIVATIONS,STOPS,MONTHS,prepare,run_one,month_table,checks,
)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"22month_all_stop_points_grid_20261121"
OUT.mkdir(parents=True,exist_ok=True)
COMPLETE_MONTHS=MONTHS[:22]
PRIOR_PATH=ROOT/"analysis"/"full_history_trailing_stop_points_grid_20261121"/"summary.json"

# Fixed comparison settings, NOT selected after seeing this specific month.
CANDIDATES=((100,500),(800,100),(800,200),(100,750),
            (100,1500),(100,2000),(100,3000),(100,8000),
            (500,750),(800,3000))
MIN_TRADES=100

def validate_series(series,summary,prior):
    if len(series)!=22:
        raise RuntimeError("A complete 22 month series was not generated.")
    months=[r["month_utc"] for r in series]
    if months!=COMPLETE_MONTHS:
        raise RuntimeError("Month buckets not contiguous and complete.")
    total=round(sum(r["net_usd"] for r in series),2)
    expected=round(prior["all_22_months"]["net_usd"],2)
    # 22 x 0.0001 rounding is at most 0.0011.
    if abs(total-expected)>.02:
        raise RuntimeError(f"Monthly net mismatch {total} != {expected}")
    months_positive=sum(row["net_usd"]>0 for row in series)
    if months_positive!=prior["all_22_months"]["positive_months"]:
        raise RuntimeError("Profitable months mismatch prior independent run")
    if summary["all_22_months"]["trades"]!=prior["all_22_months"]["trades"]:
        raise RuntimeError("Trade count mismatched independent run")

def main():
    checks()
    prior=json.loads(PRIOR_PATH.read_text())
    report={
      "name":"22 complete monthly BTC/ETH activation / Trailing Stop Points grid",
      "window":"UTC 2025-01-01 through 2026-10-31 inclusive; NOV 2026 EXCLUDED",
      "timeframes":"1H EMA20+Supertrend10,3 entry; 1m stop monitor",
      "input":{
          "activations":list(ACTIVATIONS),
          "trailing_stop_points":list(STOPS),
          "configurations_per_asset":len(ACTIVATIONS)*len(STOPS),
          "models":["mark","traded"],
          "fixed_trailing_distance_enabled":False,
      },
      "rules":"Independent extra Trailing Stop Points with activation; 2xATR14 initial SL, ST flip exit; stops updated on completed 1m bars only and apply next minute.",
      "source":"Delta India PRODUCTION verified 1m traded and MARK REST archive. NOT DEMO history.",
      "fee_model":"0.05% per side taker fee plus 18% GST. NO real spread/funding/slippage/margin liquidation or exact L1 fills.",
      "wallet_warning":"Unfunded constant notional $1000 target; no wallet constraint. Negative equity and drawdown do NOT simulate realistic $100 account.",
      "selection_warning":"All full-22-month selections are IN-SAMPLE; no guaranteed future edge. 2025-only choices shown with untouched 2026 Jan-Oct holdout.",
      "data":{},"ranking":{},"selected":{}
    }
    all_months=[]
    all_summaries=[]
    for asset in ("BTC","ETH"):
        args,info=prepare(asset)
        report["data"][asset]=info
        series_by_mode={}
        for mode in ("mark","traded"):
            all_rows=[]
            monthly_records={}
            prior_rows={(v["activation"],v["trailing_stop_points"]):v
                       for v in prior["ranking"][f"{asset.lower()}_{mode}"]}
            for activation in ACTIVATIONS:
                for points in STOPS:
                    ledger,summary=run_one(args,asset,mode,activation,points,False)
                    monthly=month_table(ledger)[:22]
                    reference=prior_rows[(activation,points)]
                    validate_series(monthly,summary,reference)
                    positives=sum(m["net_usd"]>0 for m in monthly)
                    zeros=sum(m["trades"]==0 for m in monthly)
                    row={
                        "asset":asset,"model":mode,
                        "activation":int(activation),
                        "stop_points":int(points),
                        "trades":summary["all_22_months"]["trades"],
                        "wins":summary["all_22_months"]["wins"],
                        "losses":summary["all_22_months"]["losses"],
                        "net_usd":summary["all_22_months"]["net_usd"],
                        "gross_usd":summary["all_22_months"]["gross_usd"],
                        "fees_gst_usd":summary["all_22_months"]["fees_gst_usd"],
                        "profit_factor":summary["all_22_months"]["profit_factor"],
                        "positive_months":positives,
                        "negative_months":sum(m["net_usd"]<0 for m in monthly),
                        "zero_trade_months":zeros,
                        "train_2025_net_usd":summary["train_2025"]["net_usd"],
                        "holdout_2026_jan_oct_net_usd":summary["holdout_2026_jan_oct"]["net_usd"],
                    }
                    all_rows.append(row)
                    monthly_records[(int(activation),int(points))]=monthly
                    for m in monthly:
                        all_months.append({
                            "asset":asset,"model":mode,
                            "activation":int(activation),"stop_points":int(points),
                            **m
                        })
            pd.DataFrame(all_rows).sort_values(
                ["positive_months","net_usd"],ascending=False
            ).to_csv(OUT/f"{asset.lower()}_{mode}_rank_months.csv",index=False)
            series_by_mode[mode]={
                "records":monthly_records,
                "scores":{(row["activation"],row["stop_points"]):row for row in all_rows}
            }
            all_summaries.extend(all_rows)
            print("GRID_MONTHS_COMPLETE",asset,mode,len(all_rows),flush=True)

        combined=[]
        for key,m in series_by_mode["mark"]["scores"].items():
            t=series_by_mode["traded"]["scores"][key]
            combined.append({
                "activation":key[0],
                "stop_points":key[1],
                "mark":m,"traded":t,
                "min_net_usd":min(m["net_usd"],t["net_usd"]),
                "min_positive_months":min(m["positive_months"],t["positive_months"]),
                "sum_positive_months":m["positive_months"]+t["positive_months"],
                "min_trades":min(m["trades"],t["trades"])
            })
        enough=[x for x in combined if x["min_trades"]>=MIN_TRADES]
        if not enough:raise RuntimeError(f"No viable {asset} configs with >=100 trades")
        # Ranks by criteria with all-month results. None a future-performance claim.
        best_by_net=max(enough,key=lambda v:(v["min_net_usd"],v["min_positive_months"]))
        best_by_months=max(enough,key=lambda v:(v["min_positive_months"],v["min_net_usd"]))
        best_train=max(enough,key=lambda v:(v["mark"]["train_2025_net_usd"],v["min_net_usd"]))
        top5_net=sorted(enough,key=lambda v:(v["min_net_usd"],v["min_positive_months"]),reverse=True)[:5]
        top5_months=sorted(enough,key=lambda v:(v["min_positive_months"],v["min_net_usd"]),reverse=True)[:5]
        report["ranking"][asset]={
          "max_min_net":best_by_net,
          "max_min_positive_months":best_by_months,
          "best_2025_train_mark":best_train,
          "top5_robust_net":top5_net,
          "top5_robust_months":top5_months,
          "count_minimum_trades":len(enough),
          "any_profitable_both_models":sum(x["mark"]["net_usd"]>0 and x["traded"]["net_usd"]>0 for x in enough),
          "any_22_positive_months_both_models":sum(x["min_positive_months"]==22 for x in enough),
        }
        # Always include a fixed set of user-relevant parameter comparisons
        # and both monthly-consistency / least-negative optimized options.
        selected=sorted(set(CANDIDATES) | {
          (best_by_net["activation"],best_by_net["stop_points"]),
          (best_by_months["activation"],best_by_months["stop_points"]),
          (best_train["activation"],best_train["stop_points"]),
        })
        report["selected"][asset]={
          "configs":[{"activation":a,"stop_points":p,
                      "mark":series_by_mode["mark"]["scores"][(a,p)],
                      "traded":series_by_mode["traded"]["scores"][(a,p)]}
                     for a,p in selected]
        }
        for mode in ("mark","traded"):
            pivot=[{"month_utc":month} for month in COMPLETE_MONTHS]
            for a,p in selected:
                for i,v in enumerate(series_by_mode[mode]["records"][(a,p)]):
                    pivot[i][f"A{a}_S{p}_net_usd"]=v["net_usd"]
                    pivot[i][f"A{a}_S{p}_PF"]=v["pf"]
                    pivot[i][f"A{a}_S{p}_trades"]=v["trades"]
            pd.DataFrame(pivot).to_csv(
                OUT/f"{asset.lower()}_{mode}_selected_monthly_comparison.csv",index=False
            )
        report["selected"][asset]["selected_pairs"]=[
          {"activation":a,"stop_points":p} for a,p in selected
        ]
        print("ASSET_MONTHLY_RANKED",asset,json.dumps({
          "max_min_net":{"activation":best_by_net["activation"],"stop_points":best_by_net["stop_points"],
                         "min_net_usd":best_by_net["min_net_usd"],
                         "mark":best_by_net["mark"]["net_usd"],"traded":best_by_net["traded"]["net_usd"]},
          "max_min_positive_months":{"activation":best_by_months["activation"],"stop_points":best_by_months["stop_points"],
                                     "min_positive_months":best_by_months["min_positive_months"],
                                     "mark_positive":best_by_months["mark"]["positive_months"],
                                     "traded_positive":best_by_months["traded"]["positive_months"]},
          "profitable_both_models":report["ranking"][asset]["any_profitable_both_models"],
        }),flush=True)
        del args

    pd.DataFrame(all_months).to_csv(OUT/"all_22_monthly_98_settings_2_assets_2_models.csv.gz",
                                    index=False,compression="gzip")
    pd.DataFrame(all_summaries).to_csv(OUT/"all_22_summary_grid.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ALL_22_MONTHLY_RESEARCH_SUCCESS",OUT,flush=True)

if __name__=="__main__":
    main()
