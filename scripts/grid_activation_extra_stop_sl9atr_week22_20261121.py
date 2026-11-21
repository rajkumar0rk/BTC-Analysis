#!/usr/bin/env python3
"""Independent 1H EMA20/Supertrend(10,3) extra stop point grid with 9xATR14 SL.

User's request 2026-11-21:
- Fixed numeric activation + ADDITIONAL Trailing Stop Points (NOT 'fixed
  trailing distance', NOT fixed target, NOT hour-close profit trail)
- Initial 1H ATR14 stop = 9x, 1M monitoring
- Volume and volatility filters OFF, Supertrend flip exit ON.
- Examine current IST week Nov16 00:00 through Nov21 07:30, alongside full
  22 complete months Jan2025-Oct2026, both BTCUSD and ETHUSD.

Causal original compute(): stop trigger on existing 1m mark/traded OHLC,
 new stop moves only when 1m candle complete, effective NEXT 1m, no
 retroactive high/low use. Native ATR is derived at previous completed 1H
 entry signal bar. BTC points are scaled to ETH by entry/80000, tick-rounded.

Source: existing SHA-verified Delta India PROD traded and mark 1m archives,
 plus fresh retrieved Nov minute bars via PUBLIC Delta India history API.
 The current-week restore is TEMPORARY for this workflow; only analytical
 reports and ledgers commit, NEVER market archives. No synthesized candles.
 Initial signal stopdist = 2x 1H ATR14, scale by 9/2 (same signal candle).
 0.05% taker fee EACH side + GST 18%, excluded: funding, bid/ask spread,
 actual fills, liquidity/market impact, live order latency, PM liquidation,
 and realistic capital insufficiency with $100. ~$1000 fixed notional
 research model continues even if wallet reference equity becomes negative.
 This is a parameter search IN-SAMPLE, not forward-tested profitability.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

from current_week_100_300_initial9atr_20261121 import (
    refresh_nov, WEEK_START, END,
)
from extra_trailing_stop_100_300_initial9atr_full22_20261121 import (
    INIT_STOP_SCALE, INIT_ATR14_MULT, unit_tests,
)
from optimize_1h_additional_trailing_stop_points_20261121 import (
    prepare, compute, frame_rows,
)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"grid_extra_stop_initial9atr_week22_20261121"
OUT.mkdir(parents=True,exist_ok=True)
FULL_START=int(pd.Timestamp("2025-01-01T00:00:00Z").timestamp())
FULL_END=int(pd.Timestamp("2026-11-01T00:00:00Z").timestamp())
YEAR_2026=int(pd.Timestamp("2026-01-01T00:00:00Z").timestamp())
MONTH0=np.datetime64("2025-01","M").astype("int64")
MONTHS=[str(p) for p in pd.period_range("2025-01","2026-10",freq="M")]
ACTIVATIONS=(50,100,200,300,500,800,1000,1500,2000,3000)
STOP_POINTS=(50,100,200,300,500,750,1000,1500,2000,3000,4000,6000,8000)
PRICE_MODELS=(("mark",0),("traded",1))
MIN_WEEK_TRADES=5
MIN_FULL_TRADES=70

def perf(rows):
    """Original compute() ledger 15 columns, metrics on CLOSED trades only."""
    n=len(rows)
    net=rows[:,8] if n else np.empty(0,dtype=np.float64)
    gross=rows[:,6] if n else np.empty(0,dtype=np.float64)
    fees=rows[:,7] if n else np.empty(0,dtype=np.float64)
    wins=net[net>0];losses=-net[net<0]
    equity=np.r_[0.,np.cumsum(net)]
    dd=float(np.max(np.maximum.accumulate(equity)-equity))
    return {
        "trades":n,
        "wins":len(wins),
        "losses":len(losses),
        "win_rate_pct":round(100.*len(wins)/n,2) if n else None,
        "net_usd":round(float(net.sum()),4),
        "gross_usd":round(float(gross.sum()),4),
        "fees_gst_usd":round(float(fees.sum()),4),
        "profit_factor":round(float(wins.sum()/losses.sum()),4) if len(losses) else None,
        "max_closed_trade_drawdown_usd":round(dd,4)
    }

def monthly_rows(full):
    if len(full):
        dates=full[:,1].astype("int64").astype("datetime64[s]")
        indexes=(dates.astype("datetime64[M]").astype("int64")-MONTH0).astype(int)
        if not np.all((0<=indexes)&(indexes<22)):
            raise AssertionError("Incomplete monthly range selected")
    else:
        indexes=np.empty(0,dtype=int)
    result=[]
    for i,month in enumerate(MONTHS):
        row=perf(full[indexes==i])
        result.append({"month_utc":month,**row})
    return result

def days_ist(weekly):
    if len(weekly):
        d=(weekly[:,1].astype("int64").astype("datetime64[s]")+
          np.timedelta64(330,"m")).astype("datetime64[D]")
    else:
        d=np.empty(0,dtype="datetime64[D]")
    dates=pd.date_range("2026-11-16","2026-11-21")
    return [
        {"date_ist":str(day.date()),**perf(weekly[d==np.datetime64(str(day.date()))])}
        for day in dates
    ]

def one(args,asset,mode,act,stop):
    t=args[0]
    assert t[0]==FULL_START
    assert t[-1]==END-60
    assert np.all(np.diff(t[-13000:])==60)
    ledger,skips,wallet,openpos=compute(
        *args,float(act),float(stop),int(asset=="ETH"),mode,False
    )
    t_exit=ledger[:,1]
    h=ledger[(t_exit>=FULL_START)&(t_exit<FULL_END)]
    week=ledger[(t_exit>=WEEK_START)&(t_exit<END)]
    m=monthly_rows(h)
    full=perf(h)
    w=perf(week)
    train=perf(h[h[:,1]<YEAR_2026])
    holdout=perf(h[h[:,1]>=YEAR_2026])
    assert abs(sum(row["net_usd"] for row in m)-full["net_usd"])<.005
    return {
      "asset":asset,"model":PRICE_MODELS[mode][0],
      "activation":act,"extra_trailing_stop_points":stop,
      "week":w,"full22":full,
      "train_2025":train,"test_2026_jan_oct":holdout,
      "positive_months":sum(row["net_usd"]>0 for row in m),
      "negative_months":sum(row["net_usd"]<0 for row in m),
      "zero_trade_months":sum(row["trades"]==0 for row in m),
      "open_at_cutoff":bool(openpos),
      "reference_unfunded_wallet_balance":round(float(wallet),4),
      "stop_updated_trades":int((ledger[:,13]>0).sum()),
      "skipped_due_to_position":int(skips[0])
    },m,days_ist(week),week

def sanity(asset,mode,record):
    # Full-history and current-week baselines from two independent earlier
    # successful GitHub Action runs with the exact 100/300, 9xATR controls.
    reference={
      "BTC":{
        "mark":{"full":-2213.8824,"week":16.7238,"trades":1558,"week_trades":13},
        "traded":{"full":-2288.7399,"week":23.0398,"trades":1570,"week_trades":13}
      },
      "ETH":{
        "mark":{"full":-2481.0237,"week":-25.1871,"trades":1784,"week_trades":23},
        "traded":{"full":-2389.9684,"week":-19.7533,"trades":1797,"week_trades":22}
      },
    }
    prev=reference[asset][mode]
    if (abs(record["full22"]["net_usd"]-prev["full"])>.0002
        or abs(record["week"]["net_usd"]-prev["week"])>.0002
        or record["full22"]["trades"]!=prev["trades"]
        or record["week"]["trades"]!=prev["week_trades"]):
        raise AssertionError(f"Regression fail {asset} {mode}: {record}, expected {prev}")

def flatten(x):
    return {
        "asset":x["asset"],"model":x["model"],
        "activation":x["activation"],"trailing_stop_points":x["extra_trailing_stop_points"],
        "week_net_usd":x["week"]["net_usd"],
        "week_pf":x["week"]["profit_factor"],"week_trades":x["week"]["trades"],
        "week_fees_gst":x["week"]["fees_gst_usd"],
        "full22_net_usd":x["full22"]["net_usd"],
        "full22_pf":x["full22"]["profit_factor"],
        "full22_trades":x["full22"]["trades"],
        "full22_positive_months":x["positive_months"],
        "full22_negative_months":x["negative_months"],
        "full22_max_closed_trade_dd_usd":x["full22"]["max_closed_trade_drawdown_usd"],
        "train2025_net_usd":x["train_2025"]["net_usd"],
        "test2026_net_usd":x["test_2026_jan_oct"]["net_usd"],
        "open_at_cutoff":x["open_at_cutoff"],
        "unfunded_wallet_reference":x["reference_unfunded_wallet_balance"],
    }

def pair(x,y):
    return {
      "asset":x["asset"],
      "activation":x["activation"],
      "trailing_stop_points":x["extra_trailing_stop_points"],
      "mark":flatten(x),"traded":flatten(y),
      "min_week_net_usd":min(x["week"]["net_usd"],y["week"]["net_usd"]),
      "max_week_net_usd":max(x["week"]["net_usd"],y["week"]["net_usd"]),
      "min_week_trades":min(x["week"]["trades"],y["week"]["trades"]),
      "min_full_net_usd":min(x["full22"]["net_usd"],y["full22"]["net_usd"]),
      "min_full_pf":min(x["full22"]["profit_factor"] or 0,y["full22"]["profit_factor"] or 0),
      "min_full_positive_months":min(x["positive_months"],y["positive_months"]),
      "min_full_trades":min(x["full22"]["trades"],y["full22"]["trades"]),
      "min_train2025_net":min(x["train_2025"]["net_usd"],y["train_2025"]["net_usd"]),
      "min_test2026_net":min(x["test_2026_jan_oct"]["net_usd"],y["test_2026_jan_oct"]["net_usd"]),
    }

def main():
    unit_tests()
    evidence=refresh_nov()
    output={
      "study":"100/300 family: wide search in activation and EXTRA trailing STOP points with initial SL 9xATR14",
      "requested_controls":{
         "volume_filter_enabled":False,
         "volatility_filter_enabled":False,
         "fixed_trailing_distance_enabled":False,
         "additional_trailing_stop_enabled":True,
         "initial_stop":"9xATR(14) on completed signal 1H, monitor 1m",
         "supertrend_opposite_flip_exit_enabled":True,
         "signal":"1H EMA20 touch/reclaim + Supertrend(10,3), both LONG/SHORT",
         "stop_rule":"LONG=max(previous,highest completed 1m high - extra stop points), SHORT=min(previous,lowest completed 1m low + extra stop points), activate after favorable excursion reaches activation",
         "causality":"Update at completed 1m candle effective next 1m only",
         "eth_points":"BTC-equivalent at entry/80000, tick rounded",
      },
      "search":{"activation":list(ACTIVATIONS),"trailing_stop_points":list(STOP_POINTS),
                "configs_per_asset":len(ACTIVATIONS)*len(STOP_POINTS),
                "models":["mark","traded"]},
      "periods":{"week_start_ist":"2026-11-16T00:00:00+05:30",
                 "week_end_exclusive_ist":"2026-11-21T07:30:00+05:30",
                 "full22_utc":"2025-01-01 to 2026-10-31 inclusive"},
      "costs":"0.05% taker each way plus 18% GST, NO funding or true execution slippage/spread/liquidation",
      "wallet_caveat":"~$1000 fixed reference notional without equity guard. Not an executable $100 starting wallet return; open positions not included.",
      "selection_caveat":"Weekly and full22 winners selected IN SAMPLE; result not validated live, week incomplete.",
      "data":evidence,"rankings":{},"selected_monthly":{},
    }
    allscenarios=[]
    allmonths=[]
    pairedrows=[]
    for asset in ("BTC","ETH"):
        raw,info=prepare(asset)
        assert raw[0][-1]==END-60
        assert np.array_equal(raw[9],raw[9].copy())
        assert np.all(raw[12][raw[9]!=0]>0)
        cfg=[v.copy() for v in raw]
        cfg[12]*=INIT_STOP_SCALE
        assert INIT_ATR14_MULT==9. and INIT_STOP_SCALE==4.5
        output["data"][asset]["full_source_info"]=info
        grouped={}
        for act in ACTIVATIONS:
            for stop in STOP_POINTS:
                candidates={}
                for model,mid in PRICE_MODELS:
                    rec,monthly,daily,week_trades=one(cfg,asset,mid,act,stop)
                    if (act,stop)==(100,300):
                        sanity(asset,model,rec)
                    candidates[model]=rec
                    allscenarios.append(flatten(rec))
                    for row in monthly:
                        allmonths.append({
                           "asset":asset,"model":model,
                           "activation":act,"trailing_stop_points":stop,
                           **row
                        })
                    if (act,stop) in ((100,300),(1000,200)):
                        code=f"{asset.lower()}_{model}_a{act}_s{stop}"
                        pd.DataFrame(daily).to_csv(OUT/f"{code}_daily_ist.csv",index=False)
                        frame_rows(week_trades).to_csv(OUT/f"{code}_weekly_trades.csv",index=False)
                record=pair(candidates["mark"],candidates["traded"])
                grouped[(act,stop)]=record
                pairedrows.append(record)
            print("GRID_9ATR_ASSET_PROGRESS",asset,"activation",act,"completed",
                  len(STOP_POINTS)*len(PRICE_MODELS), "simulations",flush=True)

        rows=list(grouped.values())
        enough_week=[x for x in rows if x["min_week_trades"]>=MIN_WEEK_TRADES]
        enough_full=[x for x in rows if x["min_full_trades"]>=MIN_FULL_TRADES]
        if len(enough_full)<30:raise AssertionError("Unexpectedly few eligible full22 configurations")
        rank_week=sorted(enough_week,key=lambda x:(x["min_week_net_usd"],x["min_full_net_usd"]),reverse=True)
        rank_full=sorted(enough_full,key=lambda x:(x["min_full_net_usd"],x["min_full_positive_months"]),reverse=True)
        rank_months=sorted(enough_full,key=lambda x:(x["min_full_positive_months"],x["min_full_net_usd"]),reverse=True)
        rank_train=sorted(enough_full,key=lambda x:(x["min_train2025_net"],x["min_test2026_net"]),reverse=True)
        output["rankings"][asset]={
            "total_parameter_combinations":len(rows),
            "week_included":len(enough_week),
            "full22_included":len(enough_full),
            "positive_current_week_both_sources":sum(x["min_week_net_usd"]>0 for x in rows),
            "positive_full22_both_sources":sum(x["mark"]["full22_net_usd"]>0 and x["traded"]["full22_net_usd"]>0 for x in rows),
            "positive_all_22_months_both_sources":sum(x["min_full_positive_months"]==22 for x in rows),
            "top10_week_net":rank_week[:10],
            "top10_full22_net":rank_full[:10],
            "top10_full22_positive_months":rank_months[:10],
            "best_2025_training_then_2026_holdout":rank_train[0],
            "baseline100_300":grouped[(100,300)],
            "prior1000_200":grouped[(1000,200)],
        }
        relevant={(100,300),(1000,200)}
        relevant.update((z["activation"],z["trailing_stop_points"]) for z in
                        (rank_week[:5]+rank_full[:5]+rank_months[:3]+rank_train[:1]))
        report_months={}
        for (act,stop) in sorted(relevant):
            monthly_map={}
            for model,mid in PRICE_MODELS:
                rec,monthly,daily,week_trades=one(cfg,asset,mid,act,stop)
                monthly_map[model]=monthly
                code=f"{asset.lower()}_{model}_a{act}_s{stop}"
                pd.DataFrame(monthly).to_csv(OUT/f"{code}_monthly.csv",index=False)
                pd.DataFrame(daily).to_csv(OUT/f"{code}_daily_ist.csv",index=False)
                frame_rows(week_trades).to_csv(OUT/f"{code}_weekly_trades.csv",index=False)
            report_months[f"a{act}_stop{stop}"]={
                 "settings":grouped[(act,stop)],
                 "mark_monthly":monthly_map["mark"],
                 "traded_monthly":monthly_map["traded"]
            }
        output["selected_monthly"][asset]=report_months
        print("GRID_9ATR_ASSET_SUMMARY",asset,json.dumps({
          "top_week":rank_week[0],
          "top_22months":rank_full[0],
          "top_month_consistency":rank_months[0],
          "positive_week_both":output["rankings"][asset]["positive_current_week_both_sources"],
          "positive_full_both":output["rankings"][asset]["positive_full22_both_sources"],
        }),flush=True)
        del cfg,raw
    pd.DataFrame(allscenarios).to_csv(OUT/"all_scenario_scores.csv",index=False)
    pd.DataFrame(allmonths).to_csv(OUT/"all_scenario_monthly_results.csv.gz",index=False,compression="gzip")
    pd.DataFrame([{
         k:v for k,v in rec.items() if k not in ("mark","traded")
      } for rec in pairedrows]).to_csv(OUT/"paired_mark_traded_ranked.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(output,indent=2)+"\n")
    print("100_300_FAMILY_INITIAL9ATR_FULL_WEEK_GRID_PASS",str(OUT),flush=True)

if __name__=="__main__":
    main()
