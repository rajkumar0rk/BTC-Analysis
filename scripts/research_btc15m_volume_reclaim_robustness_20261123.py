#!/usr/bin/env python3
"""BTCUSD 15M-only volume-confirmed EMA20 reclaim: limited robustness study.

No 1h logic. All indicators from completed 15m bars. 1m only for fills/stops/TPs.
Relative volume is vs the PREVIOUS 20 completed 15m candles (never current).
Same 2025-Jan through 2026-Oct IST Delta historical data and trading costs.
"""
from pathlib import Path
import json
import pandas as pd
import research_btc15m_reclaim_risk_quality_20261123 as base
from research_ema20_second_touch import read_source
from research_st_firsttouch_ema20_tp2r_stflip_1h15m import st_and_ema
from research_btc_15m_touch_reclaim_20261123 import make_signals

OUT=Path("analysis/btc15m_volume_reclaim_robustness_20261123")
PATHS=("O-H-L-C","O-L-H-C")
# Each row: reclaim window in completed 15m bars, 15m-only quality filter,
# risk reference, risk multiple, target multiple, profit-protection exit.
CONFIGS={
 "vol120_ST_3R":(4,"volume120","ST",1.0,3.0,"none"),
 "vol150_ST_3R":(4,"volume150","ST",1.0,3.0,"none"),
 "vol120_ST_2R":(4,"volume120","ST",1.0,2.0,"none"),
 "vol120_ST_2p5R":(4,"volume120","ST",1.0,2.5,"none"),
 "vol120_ST_3p5R":(4,"volume120","ST",1.0,3.5,"none"),
 "vol120_ST_4R":(4,"volume120","ST",1.0,4.0,"none"),
 "vol150_ST_2R":(4,"volume150","ST",1.0,2.0,"none"),
 "vol150_ST_2p5R":(4,"volume150","ST",1.0,2.5,"none"),
 "vol150_ST_3p5R":(4,"volume150","ST",1.0,3.5,"none"),
 "vol150_ST_4R":(4,"volume150","ST",1.0,4.0,"none"),
 "vol150_ST_5R":(4,"volume150","ST",1.0,5.0,"none"),
 "vol120_ST_0p75risk_3R":(4,"volume120","ST",0.75,3.0,"none"),
 "vol120_ST_1p25risk_3R":(4,"volume120","ST",1.25,3.0,"none"),
 "vol150_ST_0p75risk_3R":(4,"volume150","ST",0.75,3.0,"none"),
 "vol150_ST_1p25risk_3R":(4,"volume150","ST",1.25,3.0,"none"),
 "vol120_ST_3R_BE1":(4,"volume120","ST",1.0,3.0,"BE1"),
 "vol120_ST_3R_STEP2":(4,"volume120","ST",1.0,3.0,"STEP2"),
 "vol150_ST_3R_BE1":(4,"volume150","ST",1.0,3.0,"BE1"),
 "vol150_ST_3R_STEP2":(4,"volume150","ST",1.0,3.0,"STEP2"),
 "vol120_slope4_ST_3R":(4,"volume120+slope4","ST",1.0,3.0,"none"),
 "vol150_slope4_ST_3R":(4,"volume150+slope4","ST",1.0,3.0,"none"),
 "vol120_body35_ST_3R":(4,"volume120+body35","ST",1.0,3.0,"none"),
 "vol150_body35_ST_3R":(4,"volume150+body35","ST",1.0,3.0,"none"),
 "vol120_margin10_ST_3R":(4,"volume120+margin10","ST",1.0,3.0,"none"),
 "vol150_margin10_ST_3R":(4,"volume150+margin10","ST",1.0,3.0,"none"),
 "vol120_LONG_ST_3R":(4,"volume120+longonly","ST",1.0,3.0,"none"),
 "vol120_SHORT_ST_3R":(4,"volume120+shortonly","ST",1.0,3.0,"none"),
 "vol150_LONG_ST_3R":(4,"volume150+longonly","ST",1.0,3.0,"none"),
 "vol150_SHORT_ST_3R":(4,"volume150+shortonly","ST",1.0,3.0,"none"),
 "vol150_wait1_ST_3R":(1,"volume150","ST",1.0,3.0,"none"),
 "vol150_wait2_ST_3R":(2,"volume150","ST",1.0,3.0,"none"),
 "vol150_wait8_ST_3R":(8,"volume150","ST",1.0,3.0,"none"),
 "vol120_CAP2ATR_3R":(4,"volume120","CAP",2.0,3.0,"none"),
 "vol150_CAP2ATR_3R":(4,"volume150","CAP",2.0,3.0,"none"),
}
Original_check_filter=base.check_filter
def check_filter(name,side,j,ema,ind):
    for sub in name.split("+"):
        if sub=="longonly":
            if side!=1:return False
        elif sub=="shortonly":
            if side!=-1:return False
        elif not Original_check_filter(sub,side,j,ema,ind):
            return False
    return True
base.check_filter=check_filter

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    df,quality=read_source("BTCUSD")
    ema,line,trend,valid=st_and_ema(df,15)
    ind=base.make_indicators(df)
    sig_cache={}
    results=[];monthlies=[];ledgers=[]
    for name,cfg in CONFIGS.items():
        wait=cfg[0]
        if wait not in sig_cache:
            sig_cache[wait]=make_signals(df,ema,trend,valid,"reclaim",wait)[0]
        for path in PATHS:
            print("RUN",name,path,flush=True)
            row,mm,tt=base.simulate(df,ema,line,trend,ind,name,cfg,sig_cache[wait],path)
            results.append(row);monthlies.append(mm);ledgers.append(tt)
            print("RESULT",json.dumps(row,sort_keys=True),flush=True)
    rdf=pd.DataFrame(results)
    # Validate past volume-filter findings exactly before comparison.
    references={"vol120_ST_3R":(136,-8.8966),"vol150_ST_3R":(81,-4.9002)}
    for config,(trades_expected,return_expected) in references.items():
        for path in PATHS:
            row=rdf[(rdf.config==config)&(rdf.path_assumption==path)].iloc[0]
            assert int(row.trades)==trades_expected and abs(row.net_return_pct-return_expected)<.001,\
                ("HISTORICAL_CONTROL_CHANGED",config,path,row.to_dict())
    print("BASELINE_PARITY_OK",flush=True)
    rdf.to_csv(OUT/"summary.csv",index=False)
    pd.concat(monthlies,ignore_index=True).to_csv(OUT/"monthly_mark_to_market.csv",index=False)
    pd.concat(ledgers,ignore_index=True).to_csv(OUT/"trades.csv.gz",index=False,compression="gzip")
    (OUT/"quality.json").write_text(json.dumps({
        "BTCUSD":quality,"configurations":CONFIGS,"asset":"BTCUSD",
        "signal_timeframe":"15m","other_signal_timeframes":[],"execution_timeframe":"1m",
        "indicators":"ST Wilder 10x3, EMA20, ATR10, optional 15m candle/vol data",
        "fee_incl_GST_per_side":base.FEE,"adverse_slippage_per_side":base.SLIP,
        "initial_capital":1000.0,"leverage_notional":1.0,
        "hypothetical_1min_paths":PATHS,
        "selection_limitation":"All test months have been examined, not true out-of-sample; cannot infer profitability after tuning",
        "excluded":"spread, funding, liquidation, leverage risk, depth, latency"
        },indent=2)+"\n")
    table=rdf[rdf.path_assumption=="O-H-L-C"].sort_values("net_return_pct",ascending=False)
    table=table[["config","trades","win_rate_pct","profit_factor","net_return_pct",
        "profitable_months","profitable_2025_months","profitable_2026_months",
        "return_2025_pct","return_2026_pct","max_floating_drawdown_pct"]]
    stable=table[(table.trades>=50)&(table.return_2025_pct>0)&(table.return_2026_pct>0)]
    lines=["# BTCUSD 15M only — Reclaim + relative-volume sensitivity","",
        "30+ prespecified variants: all 15m ST(10,3) and EMA20 with frozen 15m volume context; 1m execution only.",
        "Jan 2025-Oct 2026 IST, 22 months; 1x notional $1000 equity.",
        "Taker 0.05% each side, GST 18%, adverse slippage 0.02% each side.",
        "No 1h signals. Reclaim requires a later separate 15m close back over/under EMA20 after initial close through it.",
        "One trade per ST cycle. Stops can be ST-distance based or capped at 2x ATR10; confirmed ST flip remains an exit.",
        "2026 is already studied; these are *in-sample* outcomes, not independent out-of-sample.", "",
        "## Ranked O-H-L-C 1m path outcomes","",table.to_markdown(index=False),"",
        "## Both-year positive with >=50 trades: retrospective screen","",
        stable.to_markdown(index=False) if len(stable) else "None found.","",
        "The 1m path hypotheses are not historical tick order. No depth, spread, funding or liquidation model.",
        "See summary.csv, monthly_mark_to_market.csv, trades.csv.gz and quality.json." ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("BACKTEST_DONE",len(rdf),flush=True)

if __name__=="__main__":
    main()
