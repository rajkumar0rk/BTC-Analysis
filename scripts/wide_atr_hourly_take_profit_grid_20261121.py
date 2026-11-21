#!/usr/bin/env python3
"""Independent 22-month parameter search for hybrid 1H ATR take profit.

This tests MANY different activation/ATR values, not weekly settings.
BTC/ETH 1h EMA20+ST10,3 entry, 2xATR14 native MARK emergency stop on EVERY
1m, opposite Supertrend flip, one position per asset. Take-profit trailing
activated ONLY at completed favorable 1h CLOSE; anchor is best COMPLETED
1h CLOSE, no high/low peek. Trail multiple of current confirmed ATR14, never
loosens. New stop effective NEXT hour. Exit either:
  H_CLOSE    - on a confirmed completed 1h CLOSE crossing prior profit stop,
               execute following 1m TRADED open
  M1_TRIGGER - on 1m MARK/TRADED high/low crossing the LAST hourly profit stop,
               use same 1m traded CLOSE as delayed fill proxy
All modes preserve independent 1m MARK emergency stop. Same strategy/fees
as previous 4-variant baseline, with 2025 training and Jan-Oct2026 holdout.

Historical venue: Delta India PRODUCTION traded+mark 1m archives. Months:
January 2025 - October 2026 (22 FULL UTC calendar months), no weekly
selection, November excluded. No funding, actual fills, book, slippage,
PM margin/liquidation. Fixed ~$1000 notional, unfunded reference, cannot
assume executable with $100 starting balance.

Include profit exit counts so best-scoring setup that effectively has
NO TAKE PROFIT trigger is identified rather than misrepresented.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

from atr_hybrid_1h_close_vs_1m_full22_20261121 import (
    data_arrays, replay, ledger_frame, get_summary, unit_tests,
    MONTHS, OUT as PREVIOUS_OUT
)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"wide_hybrid_atr_profit_grid_full22_20261121"
OUT.mkdir(parents=True,exist_ok=True)

ACTIVATIONS=(0,100,250,500,800,1000,1500,2000,2500,4000)
ATR_MULTIPLIERS=(.5,.75,1.,1.5,2.,3.,4.,5.,8.)
EXITS=(("H_CLOSE",0),("M1_TRIGGER",1))
SOURCES=(("MARK",0),("TRADED",1))
BASELINES=[(500,1.),(800,1.5),(1000,2.),(1500,3.)]
MIN_TRADES=200
MIN_TP_EXITS=10

def make_key(asset,activation,atr,exit_name,price):
    return f"{asset.lower()}_a{activation}_atr{str(atr).replace('.','p')}_{exit_name.lower()}_{price.lower()}"

def score(df):
    full=get_summary(df,MONTHS)
    train=get_summary(df,MONTHS[:12])
    holdout=get_summary(df,MONTHS[12:])
    reason=df.exit_reason.value_counts().to_dict() if len(df) else {}
    nprofit=sum(int(reason.get(k,0)) for k in (
        "profit_stop_1m_cross","profit_1h_close_next_open","profit_stop_open_gap"))
    out={
       "full_net":full["net_usd"],
       "full_pf":full["profit_factor"],
       "full_trades":full["trades"],
       "full_wins":full["wins"],
       "full_winrate":full["win_rate_pct"],
       "full_positive_months":full["positive_months"],
       "full_negative_months":full["negative_months"],
       "full_maxdd_usd":full["max_closed_trade_drawdown_usd"],
       "full_gross":full["gross_usd"],
       "full_fees_gst":full["fees_gst_usd"],
       "train2025_net":train["net_usd"],
       "train2025_pf":train["profit_factor"],
       "train2025_positive_months":train["positive_months"],
       "test2026_net":holdout["net_usd"],
       "test2026_pf":holdout["profit_factor"],
       "test2026_positive_months":holdout["positive_months"],
       "tp_exits":nprofit,
       "emergency_exits":int(reason.get("mark_emergency_open_gap",0)+
                             reason.get("mark_emergency_1m_cross",0)),
       "flip_exits":int(reason.get("opposite_supertrend_flip",0)),
    }
    return out,full["monthly"]

def objective(row):
    return (row["worst_source_full_net"],row["worst_source_positive_months"])

def main():
    unit_tests()
    result={
      "study":"BTC ETH wider 1H ATR-based profit exit research, 22 complete months, NOT weekly",
      "period":"2025-01-01 UTC through 2026-10-31 UTC, inclusive (22 complete UTC months)",
      "variants":{"activations":list(ACTIVATIONS),
                  "atr_multipliers":list(ATR_MULTIPLIERS),
                  "exit_modes":[name for name,_ in EXITS],
                  "profit_price_sources":[name for name,_ in SOURCES],
                  "per_asset_scenarios":len(ACTIVATIONS)*len(ATR_MULTIPLIERS)*len(EXITS)*len(SOURCES)},
      "strategy":"1H EMA20 touch and close reclaim in continuing Supertrend10,3; independent 1m mark-triggered emergency 2xATR14; native 1H opposite-ST flip",
      "profit_rule":"Only activate at a completed 1H favorable close; best completed 1H close as high-watermark; trailing ATR multiple never loosens; exit next hour-close-confirmed or 1m triggered on last installed stop.",
      "venue":"Delta India production archived 1m historical MARK + traded OHLC, NOT Demo testnet",
      "fees":"0.05 percent each side taker plus 18 percent GST on fees; does NOT model funding, spread, actual fills, 3-second order latency or liquidation",
      "capital":"Fixed ~$1000 notional per trade without wallet guard. This is an unfundable reference if equity turns negative, NOT a true $100 account backtest.",
      "selection":"2025 training, Jan-Oct2026 holdout separately; in-sample 22-month rankings also shown. Profit triggers must actually occur for take-profit-effective ranking.",
      "min_trades":MIN_TRADES,
      "min_take_profit_exits_for_effective_ranking":MIN_TP_EXITS,
      "data":{},"rankings":{},"combinations":{},
    }
    all_rows=[]
    all_months=[]
    for asset in ("BTC","ETH"):
        args,provenance=data_arrays(asset)
        result["data"][asset]=provenance
        bypair={}
        assetrows=[]
        scenarios={}
        for activation in ACTIVATIONS:
            for mult in ATR_MULTIPLIERS:
                for exit_name,exitid in EXITS:
                    for price_name,priceid in SOURCES:
                        arr,skips,open_at_end=replay(*args,float(activation),float(mult),
                                                     int(asset=="ETH"),exitid,priceid)
                        df=ledger_frame(arr)
                        sc,monthly=score(df)
                        key=make_key(asset,activation,mult,exit_name,price_name)
                        row={
                          "asset":asset,"activation":activation,"atr_multiplier":mult,
                          "exit_mode":exit_name,"price_source":price_name,
                          **sc,
                          "open_at_month_end":bool(open_at_end[0]),
                        }
                        all_rows.append(row);assetrows.append(row)
                        scenarios[(activation,mult,exit_name,price_name)]=(row,monthly)
                        for month,values in monthly.items():
                            all_months.append({
                               "asset":asset,
                               "activation":activation,
                               "atr_multiplier":mult,
                               "exit_mode":exit_name,
                               "price_source":price_name,
                               "month_utc":month,
                               **values
                            })
                        if (activation,mult) in BASELINES and price_name=="MARK":
                            prior_key=f"{asset.lower()}_"+{
                              (500,1.):"A",(800,1.5):"B",
                              (1000,2.):"C",(1500,3.):"D"
                            }[(activation,mult)]+"_"+exit_name.lower()+"_mark"
                            # Independently recompute and assert a previous successful
                            # backtest, preventing silent parameter/engine drift.
                            earlier=json.loads((PREVIOUS_OUT/"summary.json").read_text())
                            expected=earlier["scenarios"][prior_key]["full22"]["net_usd"]
                            if abs(sc["full_net"]-expected)>.0001:
                                raise AssertionError(f"Baseline mismatch {prior_key}: {sc['full_net']} vs {expected}")
                    mark=scenarios[(activation,mult,exit_name,"MARK")][0]
                    traded=scenarios[(activation,mult,exit_name,"TRADED")][0]
                    paired={
                       "asset":asset,"activation":activation,"atr_multiplier":mult,
                       "exit_mode":exit_name,
                       "worst_source_full_net":min(mark["full_net"],traded["full_net"]),
                       "worst_source_positive_months":min(mark["full_positive_months"],
                                                           traded["full_positive_months"]),
                       "worst_source_train_net":min(mark["train2025_net"],traded["train2025_net"]),
                       "worst_source_holdout_net":min(mark["test2026_net"],traded["test2026_net"]),
                       "mark_full_net":mark["full_net"],
                       "traded_full_net":traded["full_net"],
                       "mark_positive_months":mark["full_positive_months"],
                       "traded_positive_months":traded["full_positive_months"],
                       "min_closed_trades":min(mark["full_trades"],traded["full_trades"]),
                       "min_tp_exits":min(mark["tp_exits"],traded["tp_exits"])
                    }
                    bypair[(activation,mult,exit_name)]=paired

        pd.DataFrame(assetrows).sort_values("full_net",ascending=False).to_csv(
            OUT/f"{asset.lower()}_all_scenario_scores.csv",index=False)
        viable=[x for x in bypair.values() if x["min_closed_trades"]>=MIN_TRADES]
        effective=[x for x in viable if x["min_tp_exits"]>=MIN_TP_EXITS]
        if not viable or not effective:
            raise RuntimeError(f"{asset}: no viable TP-triggering candidates")
        leader_net=max(effective,key=objective)
        leader_months=max(effective,key=lambda x:(x["worst_source_positive_months"],
                                                    x["worst_source_full_net"]))
        train_best=max(effective,key=lambda x:(x["worst_source_train_net"],
                                               x["worst_source_holdout_net"]))
        # Score best without TP-effective restriction, but label clearly.
        all_net=max(viable,key=objective)
        keypairs=[
           ("most_robust_full_net_with_TP",leader_net),
           ("most_profitable_months_with_TP",leader_months),
           ("best_2025_train_with_TP",train_best),
           ("overall_best_including_no_TP",all_net)
        ]
        result["rankings"][asset]={
            "best":{key:val for key,val in keypairs},
            "top10_robust_net":sorted(effective,key=objective,reverse=True)[:10],
            "top10_positive_months":sorted(effective,
                  key=lambda x:(x["worst_source_positive_months"],x["worst_source_full_net"]),reverse=True)[:10],
            "number_scenarios":len(assetrows),
            "number_paired_settings":len(bypair),
            "number_TP_effective_paired_settings":len(effective),
            "any_net_positive_both_sources":any(x["mark_full_net"]>0 and x["traded_full_net"]>0 for x in viable),
        }
        choices={
            (activation,mult,exit_name) for activation,mult,exit_name in
            [(a,m,e) for a,m,e in [(500,1.,"H_CLOSE"),(800,1.5,"H_CLOSE"),
                                  (1000,2.,"H_CLOSE"),(1500,3.,"H_CLOSE")]]
        }
        choices |= {(v["activation"],v["atr_multiplier"],v["exit_mode"]) for _,v in keypairs}
        choices |= {(v["activation"],v["atr_multiplier"],v["exit_mode"])
                    for v in result["rankings"][asset]["top10_robust_net"][:3]}
        result["combinations"][asset]=[]
        for activation,mult,exit_name in sorted(choices):
            item={"activation":activation,"atr_multiplier":mult,"exit_mode":exit_name}
            for price_name in ("MARK","TRADED"):
                row,monthly=scenarios[(activation,mult,exit_name,price_name)]
                item[price_name]={"score":row,"monthly":monthly}
                ledger,_,_=replay(*args,float(activation),float(mult),
                                   int(asset=="ETH"),0 if exit_name=="H_CLOSE" else 1,
                                   0 if price_name=="MARK" else 1)
                df=ledger_frame(ledger)
                filename=make_key(asset,activation,mult,exit_name,price_name)
                df.to_csv(OUT/f"{filename}_trades.csv.gz",index=False,compression="gzip")
                pd.DataFrame([{"month_utc":k,**v} for k,v in monthly.items()]).to_csv(
                    OUT/f"{filename}_monthly.csv",index=False)
            result["combinations"][asset].append(item)
        pd.DataFrame([p for p in bypair.values()]).sort_values(
             "worst_source_full_net",ascending=False).to_csv(
             OUT/f"{asset.lower()}_paired_mark_vs_traded.csv",index=False)
        print("WIDE_ATR_ASSET_COMPLETE",asset,json.dumps({
            "best_robust":leader_net,
            "most_months":leader_months,
            "train_best":train_best,
            "best_any":all_net,
            "viable_tp":len(effective),
            "any_positive_both":result["rankings"][asset]["any_net_positive_both_sources"],
        }),flush=True)
        del args

    pd.DataFrame(all_rows).to_csv(OUT/"all_scenario_scores.csv",index=False)
    pd.DataFrame(all_months).to_csv(OUT/"all_scenarios_monthly_net_pf.csv.gz",
                                   compression="gzip",index=False)
    (OUT/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print("WIDE_ATR_FULL22_COMPLETE",OUT,flush=True)

if __name__=="__main__":
    main()
