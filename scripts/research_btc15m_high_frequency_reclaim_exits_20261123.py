#!/usr/bin/env python3
"""BTCUSD 15m ONLY: retain >=300 Reclaim entries, test ST-distance exit pairs.
All signal indicators are 15m and ONLY 1m OHLC is used for execution.
Study is already in-sample (2025Jan-2026Oct), no genuine holdout.
"""
from pathlib import Path
import json
import pandas as pd
import research_btc15m_reclaim_risk_quality_20261123 as engine
from research_ema20_second_touch import read_source
from research_st_firsttouch_ema20_tp2r_stflip_1h15m import st_and_ema
from research_btc_15m_touch_reclaim_20261123 import make_signals
OUT=Path("analysis/btc15m_high_frequency_reclaim_exits_20261123")
PATHS=("O-H-L-C","O-L-H-C")
# config: wait four 15m candles, 15m-only entry quality, ST based risk,
# stop R scaling, TP R scaling, profit protection.
# Each entry filter (any, slope4, body35, slope8, margin10) has >=300 trades in control.
CONFIGS={
 "original_ST_3R":(4,"any","ST",1,3,"none"),
 "ST075_TP2":(4,"any","ST",.75,2,"none"),
 "ST075_TP3":(4,"any","ST",.75,3,"none"),
 "ST1_TP1":(4,"any","ST",1,1,"none"),
 "ST1_TP15":(4,"any","ST",1,1.5,"none"),
 "ST1_TP2":(4,"any","ST",1,2,"none"),
 "ST1_TP25":(4,"any","ST",1,2.5,"none"),
 "ST1_TP35":(4,"any","ST",1,3.5,"none"),
 "ST1_TP4":(4,"any","ST",1,4,"none"),
 "ST1_TP5":(4,"any","ST",1,5,"none"),
 "ST125_TP15":(4,"any","ST",1.25,1.5,"none"),
 "ST125_TP2":(4,"any","ST",1.25,2,"none"),
 "ST125_TP25":(4,"any","ST",1.25,2.5,"none"),
 "ST125_TP3":(4,"any","ST",1.25,3,"none"),
 "ST125_TP4":(4,"any","ST",1.25,4,"none"),
 "ST15_TP1":(4,"any","ST",1.5,1,"none"),
 "ST15_TP2":(4,"any","ST",1.5,2,"none"),
 "ST15_TP3":(4,"any","ST",1.5,3,"none"),
 "ST15_TP4":(4,"any","ST",1.5,4,"none"),
 "ST2_TP1":(4,"any","ST",2,1,"none"),
 "ST2_TP2":(4,"any","ST",2,2,"none"),
 "ST2_TP3":(4,"any","ST",2,3,"none"),
 "ST1_TP25_BE1":(4,"any","ST",1,2.5,"BE1"),
 "ST1_TP4_BE1":(4,"any","ST",1,4,"BE1"),
 "ST1_TP3_BE1":(4,"any","ST",1,3,"BE1"),
 "ST1_TP3_STEP2":(4,"any","ST",1,3,"STEP2"),
 "ST125_TP3_BE1":(4,"any","ST",1.25,3,"BE1"),
 "ST125_TP3_STEP2":(4,"any","ST",1.25,3,"STEP2"),
 "slope4_ST1_TP2":(4,"slope4","ST",1,2,"none"),
 "slope4_ST1_TP25":(4,"slope4","ST",1,2.5,"none"),
 "slope4_ST1_TP3":(4,"slope4","ST",1,3,"none"),
 "slope4_ST125_TP3":(4,"slope4","ST",1.25,3,"none"),
 "slope4_ST15_TP3":(4,"slope4","ST",1.5,3,"none"),
 "slope4_ST1_TP3_BE1":(4,"slope4","ST",1,3,"BE1"),
 "slope8_ST125_TP3":(4,"slope8","ST",1.25,3,"none"),
 "body35_ST125_TP3":(4,"body35","ST",1.25,3,"none"),
 "margin10_ST125_TP3":(4,"margin10","ST",1.25,3,"none"),
}
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    df,q=read_source("BTCUSD")
    ema,st,trend,valid=st_and_ema(df,15)
    ind=engine.make_indicators(df)
    signals=make_signals(df,ema,trend,valid,"reclaim",4)[0]
    results=[];monthly=[];ledgers=[]
    for name,cfg in CONFIGS.items():
        for path in PATHS:
            print("RUN",name,path,flush=True)
            r,m,t=engine.simulate(df,ema,st,trend,ind,name,cfg,signals,path)
            assert r["trades"]>=300,("Trade count lower than target",name,r["trades"])
            results.append(r);monthly.append(m);ledgers.append(t)
            print("RESULT",json.dumps(r,sort_keys=True),flush=True)
    sdf=pd.DataFrame(results)
    for path in PATHS:
        b=sdf[(sdf.config=="original_ST_3R")&(sdf.path_assumption==path)].iloc[0]
        assert int(b.trades)==434 and abs(float(b.net_return_pct)-(-44.5322))<.001,\
            ("BASELINE_MISMATCH",path,b.to_dict())
    print("BASELINE_PARITY_OK",flush=True)
    sdf.to_csv(OUT/"summary.csv",index=False)
    pd.concat(monthly,ignore_index=True).to_csv(OUT/"monthly_mark_to_market.csv",index=False)
    pd.concat(ledgers,ignore_index=True).to_csv(OUT/"trades.csv.gz",index=False,compression="gzip")
    strongest=sdf[sdf.path_assumption=="O-H-L-C"].sort_values("net_return_pct",ascending=False)
    table=strongest[["config","trades","win_rate_pct","profit_factor","net_return_pct","profitable_months",
        "return_2025_pct","return_2026_pct","max_floating_drawdown_pct"]]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
        "# BTCUSD 15m high trade-count reclaim exit comparison",
        "Only BTCUSD, 15m ST(10,3), EMA20; 1m price path only for SL/TP fills; no 1h.",
        "At least 300 entries for every variant; 22 completed IST months 2025Jan-2026Oct.",
        "1x notional and evolving $1000 capital, 0.05% per-side taker fee + GST18%, 0.02% per-side slip.",
        "Baseline 434 entries. 4 completed 15m candle reclaim window and 1 entry per Supertrend cycle.",
        "The 2025/2026 history has been researched, not an independent out-of-sample test.",
        "Risk is based on ST distance multiplied by the variant's stop factor, TP is the chosen multiple of that new R.",
        "Profit locks on selected cases; same confirmed opposite-ST exit.",
        "## Ranked O-H-L-C 1m price-path results","",table.to_markdown(index=False),
        "","See monthly_mark_to_market.csv, summary.csv, trades.csv.gz for detail.",
        "Funding, real spread, market depth, liquidation, tick order and latency excluded."])+"\n")
    (OUT/"quality.json").write_text(json.dumps({"BTCUSD":q,"asset":"BTCUSD","timeframe":"15m",
       "other_timeframes":[],"execution_timeframe":"1m","configurations":CONFIGS,
       "time_window":"2025Jan-2026Oct inclusive IST 22 months","estimated_fees_gst_per_side":engine.FEE,
       "slippage_per_side":engine.SLIP,"notional":1.0,"path_sensitivity":PATHS,
       "min_trades_each_case":300,"retrospective_optimisation":True},indent=2)+"\n")
    print("BACKTEST_DONE",len(sdf),flush=True)
if __name__=="__main__":
    main()
