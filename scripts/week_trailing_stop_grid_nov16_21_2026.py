#!/usr/bin/env python3
"""Current week parameter grid. Distinguishes EXTRA trailing stop points from original fixed trailing distance.

Read-only public 1m traded+MARK candles; run complete 1H EMA20+Supertrend
indicator history for signal/position warmup, then report 2026-11-16 through
runner cutoff in Asia/Kolkata. Weekly parameter selection is IN-SAMPLE.
Compared to separate 2025 train / 2026 Jan-Oct validation from archive.
No broker trades, real fills, funding, spread, or PM liquidation.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd

from week_nov16_2026_ema20st_stop_points import prepare,stats,CONFIG,OUTPUT as UNUSED,WEEK_BEGIN,IST
from optimize_1h_additional_trailing_stop_points_20261121 import (
    ACTIVATIONS, STOPS, compute,frame_rows, checks
)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"weekly_stop_points_grid_20261121"
OUT.mkdir(parents=True,exist_ok=True)
HISTORY=ROOT/"analysis"/"full_history_trailing_stop_points_grid_20261121"/"summary.json"
ASSETS=("BTC","ETH")
MODELS=("mark","traded")
MIN_WEEK_TRADES=4

def hist_lookup(asset):
    archive=json.loads(HISTORY.read_text())
    d={}
    for mode in MODELS:
        for entry in archive["ranking"][asset.lower()+"_"+mode]:
            k=(int(entry["activation"]),int(entry["trailing_stop_points"]))
            d[(mode,*k)]={
               "train_2025_net_usd":entry["train_2025"]["net_usd"],
               "holdout_2026_jan_oct_net_usd":entry["holdout_2026_jan_oct"]["net_usd"],
               "prior_22_month_net_usd":entry["all_22_months"]["net_usd"],
               "prior_22_month_positive_months":entry["all_22_months"]["positive_months"],
               "prior_22_month_profit_factor":entry["all_22_months"]["profit_factor"],
            }
    return d

def run_param(args,asset,mode,activation,distance):
    # "distance" below is EXTRA trailing stop points; Fixed Distance switch OFF.
    records,skips,wallet,openpos=compute(
        *args,float(activation),float(distance),
        1 if asset=="ETH" else 0,
        0 if mode=="mark" else 1,
        False
    )
    f=frame_rows(records)
    return f,int(openpos)

def main():
    from datetime import datetime,timezone,timedelta
    checks()
    end=int((datetime.now(timezone.utc)-timedelta(minutes=12)).timestamp())//60*60
    endtime=pd.Timestamp(end,unit="s",tz="UTC")
    if not pd.Timestamp("2026-11-21",tz="UTC")<=endtime<pd.Timestamp("2026-11-23",tz="UTC"):
        raise RuntimeError(f"unexpected run time {endtime}")
    report={
      "title":"2026-11-16 week: EMA20 Supertrend trailing STOP POINTS, multiple activation/stop combinations",
      "week_begin_ist":str(WEEK_BEGIN),
      "end_exclusive_ist":str(endtime.tz_convert(IST)),
      "calendar_week_incomplete":True,
      "venue":"Delta India production historical 1m; not Delta Demo testnet",
      "settings":"EMA20+Supertrend10,3 1H entry, ATR14*2 initial stop; 1m point trailing, fixed trailing distance DISABLED",
      "stop_semantics":"candidate LONG = best 1m high - stop_points, SHORT = best 1m low + stop_points; applied from following minute; exchange MARK or traded proxy alternative",
      "eth_points":"BTC-equivalent activation and trailing stop points scaled by ETH entry/80000, tick-rounded",
      "cost":"Regular 0.05% each side plus 18% GST, estimated, exclude funding, actual bid/ask fills, spread, slippage, liquidation",
      "sizing":"Unfunded constant target notional near $1000 per position, not a realistic $100 equity simulation",
      "optimization_caveat":"Selecting best on the very same partial week is overfitting; benchmark using 2025 train and 2026 Jan-Oct holdout. Prior history is also a tested grid and cannot prove profitability.",
      "grid":{"activation_points":list(ACTIVATIONS),"stop_points":list(STOPS),"combinations_per_asset":len(ACTIVATIONS)*len(STOPS)},
      "datasets":{},"results":{}
    }
    for asset in ASSETS:
        args,info=prepare(asset,end)
        report["datasets"][asset]=info
        historical=hist_lookup(asset)
        allrows=[]
        file_rows={}
        for activation in ACTIVATIONS:
            for stop in STOPS:
                per={}
                for mode in MODELS:
                    ledger,openpos=run_param(args,asset,mode,activation,stop)
                    weekly,s=stats(ledger,endtime)
                    prior=historical[(mode,int(activation),int(stop))]
                    per[mode]={"week":s,"open_position_at_cutoff":bool(openpos),
                               **prior}
                mark=per["mark"]["week"];traded=per["traded"]["week"]
                keep={"asset":asset,"activation":int(activation),"trailing_stop_points":int(stop),
                  "fixed_trailing_distance_enabled":False,
                  "mark_net_usd":mark["net_realized_usd"],
                  "mark_trades":mark["completed_trades"],
                  "mark_wins":mark["wins"],
                  "mark_pf":mark["profit_factor"],
                  "traded_net_usd":traded["net_realized_usd"],
                  "traded_trades":traded["completed_trades"],
                  "traded_pf":traded["profit_factor"],
                  "min_model_net_usd":min(mark["net_realized_usd"],traded["net_realized_usd"]),
                  "max_model_net_usd":max(mark["net_realized_usd"],traded["net_realized_usd"]),
                  "both_min_4trades":min(mark["completed_trades"],traded["completed_trades"])>=MIN_WEEK_TRADES,
                  "hist2025_mark_net_usd":per["mark"]["train_2025_net_usd"],
                  "hist2026_holdout_mark_net_usd":per["mark"]["holdout_2026_jan_oct_net_usd"],
                  "hist22months_mark_net_usd":per["mark"]["prior_22_month_net_usd"],
                  "hist22_positive_months":per["mark"]["prior_22_month_positive_months"],
                  "open_mark":per["mark"]["open_position_at_cutoff"],
                  "open_traded":per["traded"]["open_position_at_cutoff"],
                  }
                allrows.append(keep)
                file_rows[(int(activation),int(stop))]=per
        weekly=pd.DataFrame(allrows)
        weekly.sort_values(["min_model_net_usd","mark_net_usd"],
                           ascending=False).to_csv(OUT/f"{asset.lower()}_all_98_combinations.csv",index=False)
        valid=[x for x in allrows if x["both_min_4trades"]]
        if not valid:raise RuntimeError(f"No {asset} candidate with >=4 trades under both trigger models")
        selected_by_robust=max(valid,key=lambda x:(x["min_model_net_usd"],x["mark_net_usd"]))
        selected_by_mark=max(valid,key=lambda x:(x["mark_net_usd"],x["min_model_net_usd"]))
        selected_fixed100=max([x for x in valid if x["activation"]==100],
                               key=lambda x:(x["min_model_net_usd"],x["mark_net_usd"]))
        selected_hist=max(allrows,key=lambda x:x["hist2025_mark_net_usd"])
        selected_hist100=max([x for x in allrows if x["activation"]==100],
                             key=lambda x:x["hist2025_mark_net_usd"])
        picked={
          "best_week_robust_both_models_min4trades":selected_by_robust,
          "best_week_mark_min4trades":selected_by_mark,
          "best_week_activation100_robust_min4trades":selected_fixed100,
          "historical_2025_train_best":selected_hist,
          "historical_2025_train_best_activation100":selected_hist100,
          "original_100_500":next(x for x in allrows if (x["activation"],x["trailing_stop_points"])==(100,500)),
        }
        for kind,row in picked.items():
            a=row["activation"];st=row["trailing_stop_points"]
            details=file_rows[(a,st)]
            for mode in MODELS:
                led,_=run_param(args,asset,mode,a,st)
                wk,_=stats(led,endtime)
                wk.to_csv(OUT/f"{asset.lower()}_{kind}_{mode}_week_trades.csv",index=False)
            picked[kind]={**row,"mark_daily":details["mark"]["week"]["daily_exit_ist"],
                         "traded_daily":details["traded"]["week"]["daily_exit_ist"],
                         "mark_gross":details["mark"]["week"]["gross_realized_usd"],
                         "mark_fees_gst":details["mark"]["week"]["assumed_fees_gst_usd"],
                         "traded_gross":details["traded"]["week"]["gross_realized_usd"],
                         "traded_fees_gst":details["traded"]["week"]["assumed_fees_gst_usd"]}
        report["results"][asset]={"selected":picked,
                                   "top10_min_model_net":sorted(valid,
                                       key=lambda x:x["min_model_net_usd"],reverse=True)[:10],
                                   "top10_mark_net":sorted(valid,
                                       key=lambda x:x["mark_net_usd"],reverse=True)[:10],
                                   "tested":len(allrows),
                                   "min_four_trades_candidates":len(valid),
                                   "positive_both_models":sum(
                                       x["mark_net_usd"]>0 and x["traded_net_usd"]>0 for x in valid)}
        print("WEEK_GRID_ASSET_COMPLETE",asset,
              json.dumps({"selected":picked,"n_candidates":len(allrows),"n_valid":len(valid)},
                         separators=(",",":")),flush=True)
        del args
    (OUT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    print("WEEK_GRID_PASS",OUT,flush=True)

if __name__=="__main__":
    main()
