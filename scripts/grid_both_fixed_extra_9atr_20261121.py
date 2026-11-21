#!/usr/bin/env python3
"""Sweep BOTH enabled trailing controls: fixed activation/distance + extra stop.

Previous screenshot had:
 Fixed Trailing Distance ENABLED: activation=500, fixed distance=250
 Additional Trailing Stop Points ENABLED: 1000
 Prior user context: initial 9xATR(14) from completed 1H signal,
    1H EMA20/Supertrend(10,3), Supertrend flip exit ON,
    volume and volatility filters OFF, 1-minute stop monitoring.

New 6x5x4 parameter grid (120 combinations per asset):
  activation:          100,250,500,800,1500,3000 BTC-equivalent pts
  fixed trail distance:100,250,500,1000,2000
  additional stop:     250,500,1000,3000
Each pair evaluated with:
  SHARED_ACTIVATION: both trailing stops start after activation.
    These are mathematically identical to one trailing stop whose gap
    is MIN(fixed distance, additional stop), as both use the same 1m best
    observed high/low. This equivalence is regression verified.
  IMMEDIATE_EXTRA: independent extra-stop protection applies from ENTRY
    while fixed trailing activates after the specified points.
Both models: 1m MARK and TRADED high-low stop monitoring and stop update
only effective after current 1m candle completes (no lookahead).
Both assets BTCUSD/ETHUSD. 2 variants * 2 models * 2 assets * 120
= 960 scenario scores, but SHARED repeated effective gaps are simulated
once and reused (algorithmically exact equivalence).

Current incomplete week: Mon Nov16 00:00 IST - Sat Nov21 07:30 IST.
Full 22 completed UTC months: Jan2025-Oct2026. Report full 2025
training and Jan-Oct 2026 separately. Any selection on either period
remains in sample unless split strictly via prior 2025.
Public Delta India 1-minute traded and MARK historic candles; only
temporary November refresh in workflow, never commit raw market archives.

Costs assumed: 0.05% taker PER SIDE + GST18%; omits funding, true spread
and actual fills, latency, margin/liquidation. Flat ~$1000 notional research
sizing ignores insolvency (not a backtest of a funded $100 wallet).
No real TradingView Pine code for how dual controls interact was supplied;
neither joint-control interpretation is asserted to reproduce Pine exactly.
No live orders, research branch only.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

from current_week_100_300_initial9atr_20261121 import refresh_nov,WEEK_START,END
from extra_trailing_stop_100_300_initial9atr_full22_20261121 import INIT_STOP_SCALE,unit_tests as previous_tests
from optimize_1h_additional_trailing_stop_points_20261121 import prepare,compute as original_single
from backtest_dual_trail_screenshot_500_250_1000_20261121 import (
    dual_compute,measures,unit_tests as dual_unit_tests,export_frame,
)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"dual_trailing_all_values_9atr_week_full22_20261121"
OUT.mkdir(parents=True,exist_ok=True)

ACTIVATIONS=(100,250,500,800,1500,3000)
FIXED_DISTANCES=(100,250,500,1000,2000)
EXTRA_STOP_POINTS=(250,500,1000,3000)
SOURCES=(("MARK",0),("TRADED",1))
VARIANTS=("SHARED_ACTIVATION","IMMEDIATE_EXTRA")
FULL_START=int(pd.Timestamp("2025-01-01T00:00:00Z").timestamp())
FULL_END=int(pd.Timestamp("2026-11-01T00:00:00Z").timestamp())
YEAR_SPLIT=int(pd.Timestamp("2026-01-01T00:00:00Z").timestamp())
MONTHS=[str(p) for p in pd.period_range("2025-01","2026-10",freq="M")]
MIN_WEEK_TRADES=5
MIN_FULL_TRADES=100

# Independent successful earlier run used to test that this grid has not
# altered the engine or its price data.
REGRESSION={
 "BTC":{
  "MARK":{"SHARED_ACTIVATION":(17.3131,-1398.6889,7,870),
          "IMMEDIATE_EXTRA":(-42.6627,-1410.3505,12,1110)},
  "TRADED":{"SHARED_ACTIVATION":(20.7951,-1464.9717,7,873),
            "IMMEDIATE_EXTRA":(-39.1807,-1497.4238,12,1119)}},
 "ETH":{
  "MARK":{"SHARED_ACTIVATION":(24.094,-1680.0537,10,1006),
          "IMMEDIATE_EXTRA":(-31.3233,-1595.4367,22,1339)},
  "TRADED":{"SHARED_ACTIVATION":(24.064,-1694.1493,10,1017),
            "IMMEDIATE_EXTRA":(-29.6803,-1742.4762,22,1363)}}
}

def metric_slices(raw):
    exits=raw[:,1]
    full=raw[(exits>=FULL_START)&(exits<FULL_END)]
    week=raw[(exits>=WEEK_START)&(exits<END)]
    train=full[full[:,1]<YEAR_SPLIT]
    test=full[full[:,1]>=YEAR_SPLIT]
    m=measures(full)
    w=measures(week)
    t=measures(train)
    o=measures(test)
    if len(full):
        midx=(full[:,1].astype("int64").astype("datetime64[s]").
              astype("datetime64[M]").astype("int64")-
              np.datetime64("2025-01","M").astype("int64"))
    else:
        midx=np.empty(0,dtype=np.int64)
    if not np.all((midx>=0)&(midx<22)):
        raise AssertionError("Trade month out of 22-month window")
    months=[]
    for i,month in enumerate(MONTHS):
        months.append({"month_utc":month,**measures(full[midx==i])})
    if sum(x["trades"] for x in months)!=m["trades"]:
        raise AssertionError("Monthly trade reconciliation failed")
    if abs(sum(x["net_usd"] for x in months)-m["net_usd"])>.006:
        raise AssertionError("Monthly net reconciliation failed")
    return {
        "week":w,"full22":m,"training_2025":t,"holdout_2026":o,
        "positive_months":sum(x["net_usd"]>0 for x in months),
        "negative_months":sum(x["net_usd"]<0 for x in months),
        "zero_trade_months":sum(x["trades"]==0 for x in months)
    },months

def flatten(rec):
    return {
        "asset":rec["asset"],"source":rec["source"],
        "mode":rec["mode"],"activation":rec["activation"],
        "fixed_distance":rec["fixed_distance"],
        "additional_stop":rec["additional_stop"],
        "effective_shared_stop":rec["effective_shared_stop"],
        "week_net_usd":rec["week"]["net_usd"],
        "week_trades":rec["week"]["trades"],
        "week_pf":rec["week"]["profit_factor"],
        "week_winrate":rec["week"]["win_rate_pct"],
        "week_fees_gst":rec["week"]["fees_gst_usd"],
        "full22_net_usd":rec["full22"]["net_usd"],
        "full22_trades":rec["full22"]["trades"],
        "full22_pf":rec["full22"]["profit_factor"],
        "full22_positive_months":rec["positive_months"],
        "full22_drawdown_usd":rec["full22"]["max_closed_trade_drawdown_usd"],
        "training2025_net_usd":rec["training_2025"]["net_usd"],
        "test2026_net_usd":rec["holdout_2026"]["net_usd"],
        "open_at_cutoff":rec["open_at_cutoff"],
    }

def paired(mark,traded):
    assert (mark["asset"],mark["mode"],mark["activation"],mark["fixed_distance"],mark["additional_stop"])==(
            traded["asset"],traded["mode"],traded["activation"],traded["fixed_distance"],traded["additional_stop"])
    return {
        "asset":mark["asset"],"mode":mark["mode"],"activation":mark["activation"],
        "fixed_distance":mark["fixed_distance"],"additional_stop":mark["additional_stop"],
        "mark_week_net":mark["week"]["net_usd"],
        "traded_week_net":traded["week"]["net_usd"],
        "min_week_net":min(mark["week"]["net_usd"],traded["week"]["net_usd"]),
        "week_trades_min":min(mark["week"]["trades"],traded["week"]["trades"]),
        "mark_full_net":mark["full22"]["net_usd"],
        "traded_full_net":traded["full22"]["net_usd"],
        "min_full_net":min(mark["full22"]["net_usd"],traded["full22"]["net_usd"]),
        "full_trades_min":min(mark["full22"]["trades"],traded["full22"]["trades"]),
        "positive_months_min":min(mark["positive_months"],traded["positive_months"]),
        "min_train2025_net":min(mark["training_2025"]["net_usd"],traded["training_2025"]["net_usd"]),
        "min_test2026_net":min(mark["holdout_2026"]["net_usd"],traded["holdout_2026"]["net_usd"]),
        "mark_full_pf":mark["full22"]["profit_factor"],
        "traded_full_pf":traded["full22"]["profit_factor"],
        "mark_week_pf":mark["week"]["profit_factor"],
        "traded_week_pf":traded["week"]["profit_factor"],
    }

def find_days_ist(raw):
    exits=raw[:,1]
    weekly=raw[(exits>=WEEK_START)&(exits<END)]
    dates=(weekly[:,1].astype("int64").astype("datetime64[s]")+
           np.timedelta64(330,"m")).astype("datetime64[D]")
    return [{"day_ist":str(day.date()),
             **measures(weekly[dates==np.datetime64(str(day.date()))])}
            for day in pd.date_range("2026-11-16","2026-11-21")]

def assert_regression(asset,source,kind,result):
    expected_week,expected_full,week_trades,full_trades=REGRESSION[asset][source][kind]
    if (abs(result["week"]["net_usd"]-expected_week)>.0002 or
        abs(result["full22"]["net_usd"]-expected_full)>.0002 or
        result["week"]["trades"]!=week_trades or
        result["full22"]["trades"]!=full_trades):
        raise AssertionError(
           f"Baseline differs from previous verified backtest: "
           f"{asset} {source} {kind}: week {result['week']} full {result['full22']} "
           f"expected {(expected_week,expected_full,week_trades,full_trades)}")

def main():
    previous_tests()
    dual_unit_tests()
    evidence=refresh_nov()
    report={
       "study":"BOTH fixed trailing 500/250 and additional trailing 1000 control parameter sweep",
       "window":{
          "current_week_start_ist":"2026-11-16T00:00:00+05:30",
          "current_week_end_exclusive_ist":"2026-11-21T07:30:00+05:30",
          "full22":"Jan 2025-Oct 2026 completed UTC months",
       },
       "strategy":{
          "initial_stop":"9xATR(14) of completed 1H signal candle",
          "filters":{"volume":False,"volatility":False},
          "opposite_supertrend_flip":True,
          "signal":"1H EMA20 touch/reclaim continuing Supertrend10,3, both directions",
          "fixed_trailing_distance_enabled":True,
          "additional_trailing_stop_enabled":True,
          "one_open_position_per_asset":True,
          "profit_stop_edits":"Existing 1M stop checked first; next updated stop applies next 1M",
          "eth_points":"BTC-equivalent scaled entry/80000 rounded to tick",
       },
       "semantics":{
          "SHARED_ACTIVATION":"Fixed and Additional stop both activate after favorable entry movement >= activation; tighter point gap controls",
          "IMMEDIATE_EXTRA":"Additional stop point offset activates independently from entry; fixed-distance stop activates after favorable >= activation",
          "WARNING":"Cannot identify exact TradingView Pine precedence from screenshot; both are hypothetical live-code interpretations.",
       },
       "search":{
          "activation":list(ACTIVATIONS),"fixed_distance":list(FIXED_DISTANCES),
          "additional_stop":list(EXTRA_STOP_POINTS),"modes":list(VARIANTS),
          "models":["MARK","TRADED"],
          "total_reported_scenarios":len(ACTIVATIONS)*len(FIXED_DISTANCES)*len(EXTRA_STOP_POINTS)*len(VARIANTS)*2*2,
       },
       "costs":"0.05 percent taker per side plus 18% GST. No funding, actual slippage, bid-ask fill, liquidation, PM margin",
       "wallet_limitations":"Reference $1000 notional per trade with no wallet insolvency guard, not executable with $100 starting wallet after depletion",
       "data_sources":evidence,
       "selection_warning":"Highest-week and highest-22-month results are selected IN-SAMPLE; not proof of live profitability.",
       "regression":{},"rankings":{},"selected_details":{},
    }
    all_rows=[];all_months=[]
    for asset in ("BTC","ETH"):
        args,sourceinfo=prepare(asset)
        assert int(args[0][0])==FULL_START and int(args[0][-1])==END-60
        assert np.all(args[12][args[9]!=0]>0)
        cfg=[v.copy() for v in args]
        cfg[12]*=INIT_STOP_SCALE
        report["data_sources"][asset]["read_asset_info"]=sourceinfo
        # Source model cache for all combinations (file count is small).
        by_setting={}
        for source,sourceid in SOURCES:
            shared_cache={}
            for activation in ACTIVATIONS:
                for fixed in FIXED_DISTANCES:
                    for extra in EXTRA_STOP_POINTS:
                        for kind in VARIANTS:
                            k=(activation,fixed,extra,kind,source)
                            if kind=="SHARED_ACTIVATION":
                                tightest=min(fixed,extra)
                                cache_key=(activation,tightest)
                                if cache_key not in shared_cache:
                                    # Exact simplification: sharing the same
                                    # activation/time/highwater makes the
                                    # tighter independent stop equal to one
                                    # stop with min offset.
                                    raw,_,_,op=original_single(
                                         *cfg,float(activation),float(tightest),
                                         int(asset=="ETH"),sourceid,False)
                                    shared_cache[cache_key]=(raw,op)
                                raw,op=shared_cache[cache_key]
                            else:
                                raw,_,_,op=dual_compute(
                                    *cfg,float(activation),float(fixed),float(extra),
                                    int(asset=="ETH"),sourceid,1,1,1,False
                                )
                            scores,months=metric_slices(raw)
                            rec={
                               "asset":asset,"source":source,"mode":kind,
                               "activation":activation,"fixed_distance":fixed,
                               "additional_stop":extra,
                               "effective_shared_stop":min(fixed,extra) if kind=="SHARED_ACTIVATION" else None,
                               "open_at_cutoff":bool(op),
                               **scores
                            }
                            all_rows.append(flatten(rec))
                            by_setting[k]=(rec,raw,months)
                            for monthly in months:
                                all_months.append({
                                   "asset":asset,"source":source,"mode":kind,
                                   "activation":activation,"fixed_distance":fixed,
                                   "additional_stop":extra,**monthly
                                })
                            if (activation,fixed,extra)==(500,250,1000):
                                assert_regression(asset,source,kind,rec)
                            if (activation,fixed,extra) in ((500,250,1000),(500,1000,250)):
                                # Directly compare dual-stops implementation
                                # to the mathematically reduced one.
                                direct,_,_,_=dual_compute(
                                     *cfg,float(activation),float(fixed),float(extra),
                                     int(asset=="ETH"),sourceid,1,1,0,False)
                                if kind=="SHARED_ACTIVATION":
                                    if direct.shape[0]!=raw.shape[0] or not np.allclose(
                                           direct[:,:11],raw[:,:11],atol=1e-6,rtol=0):
                                        raise AssertionError(f"Shared reduction mismatch: {asset} {source}")
                                    report["regression"][f"{asset}_{source}_{activation}_{fixed}_{extra}"]=True
                print("DUAL_GRID_PROGRESS",asset,source,"activation",activation,flush=True)
        paired_rows=[]
        for kind in VARIANTS:
            for activation in ACTIVATIONS:
                for fixed in FIXED_DISTANCES:
                    for extra in EXTRA_STOP_POINTS:
                        a=by_setting[(activation,fixed,extra,kind,"MARK")][0]
                        b=by_setting[(activation,fixed,extra,kind,"TRADED")][0]
                        paired_rows.append(paired(a,b))
        eligible_week=[x for x in paired_rows if x["week_trades_min"]>=MIN_WEEK_TRADES]
        eligible_full=[x for x in paired_rows if x["full_trades_min"]>=MIN_FULL_TRADES]
        if not eligible_week or not eligible_full:raise AssertionError("No eligible configurations")
        top_week=sorted(eligible_week,key=lambda x:(x["min_week_net"],x["min_full_net"]),reverse=True)
        top_full=sorted(eligible_full,key=lambda x:(x["min_full_net"],x["positive_months_min"]),reverse=True)
        top_month=sorted(eligible_full,key=lambda x:(x["positive_months_min"],x["min_full_net"]),reverse=True)
        top_train=sorted(eligible_full,key=lambda x:(x["min_train2025_net"],x["min_test2026_net"]),reverse=True)
        report["rankings"][asset]={
            "total_triple_value_combinations":len(ACTIVATIONS)*len(FIXED_DISTANCES)*len(EXTRA_STOP_POINTS),
            "paired_interpretations":len(paired_rows),
            "eligible_week_pairs":len(eligible_week),
            "eligible_full22_pairs":len(eligible_full),
            "any_positive_22months_both_sources":any(x["mark_full_net"]>0 and x["traded_full_net"]>0 for x in paired_rows),
            "positive_week_both_sources":sum(x["min_week_net"]>0 for x in paired_rows),
            "top10_week":top_week[:10],
            "top10_full22":top_full[:10],
            "top10_months":top_month[:10],
            "best_2025_training_then_2026_holdout":top_train[0],
            "baseline_shared":paired(
               by_setting[(500,250,1000,"SHARED_ACTIVATION","MARK")][0],
               by_setting[(500,250,1000,"SHARED_ACTIVATION","TRADED")][0]),
            "baseline_immediate":paired(
               by_setting[(500,250,1000,"IMMEDIATE_EXTRA","MARK")][0],
               by_setting[(500,250,1000,"IMMEDIATE_EXTRA","TRADED")][0])
        }
        chosen={(500,250,1000,"SHARED_ACTIVATION"),
                (500,250,1000,"IMMEDIATE_EXTRA")}
        for top in (top_week[:5],top_full[:5],top_month[:3],[top_train[0]]):
            for x in top:
                chosen.add((x["activation"],x["fixed_distance"],x["additional_stop"],x["mode"]))
        report["selected_details"][asset]={}
        for activation,fixed,extra,kind in sorted(chosen):
            key=f"a{activation}_d{fixed}_s{extra}_{kind.lower()}"
            entry={}
            for source,sourceid in SOURCES:
                rec,raw,months=by_setting[(activation,fixed,extra,kind,source)]
                entry[source]={"stats":flatten(rec),"months":months,"daily_ist":find_days_ist(raw)}
                tag=f"{asset.lower()}_{source.lower()}_{key}"
                pd.DataFrame(months).to_csv(OUT/f"{tag}_monthly.csv",index=False)
                pd.DataFrame(entry[source]["daily_ist"]).to_csv(OUT/f"{tag}_daily_ist.csv",index=False)
                ts=raw[:,1]
                wkraw=raw[(ts>=WEEK_START)&(ts<END)]
                if kind=="SHARED_ACTIVATION":
                    # Single gap stop row-format, original frame_rows.
                    from optimize_1h_additional_trailing_stop_points_20261121 import frame_rows
                    frame_rows(wkraw).to_csv(OUT/f"{tag}_weekly_trades.csv",index=False)
                else:
                    export_frame(wkraw).to_csv(OUT/f"{tag}_weekly_trades.csv",index=False)
            report["selected_details"][asset][key]=entry
        print("DUAL_GRID_ASSET_COMPLETE",asset,json.dumps({
            "weekly_best":top_week[0],
            "historical_best":top_full[0],
            "positive_week":report["rankings"][asset]["positive_week_both_sources"],
            "any_22_month":report["rankings"][asset]["any_positive_22months_both_sources"],
        }),flush=True)
        del args,cfg,by_setting
    pd.DataFrame(all_rows).to_csv(OUT/"all_960_scenarios.csv",index=False)
    pd.DataFrame(all_months).to_csv(OUT/"all_monthly_scores.csv.gz",compression="gzip",index=False)
    (OUT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    print("DUAL_TRAIL_PARAM_GRID_COMPLETE",OUT,flush=True)

if __name__=="__main__":
    main()
