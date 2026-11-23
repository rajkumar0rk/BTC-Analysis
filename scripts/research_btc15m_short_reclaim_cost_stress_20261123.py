#!/usr/bin/env python3
"""Prespecified cost stress on already-chosen BTCUSD 15m short-only reclaim candidates.

Does not retune the entry. 1m is execution, all signal indicators 15m.
22 completed IST months Jan 2025-Oct 2026, no 1h indicators.
"""
import json
from pathlib import Path
import pandas as pd
import research_btc15m_volume_reclaim_robustness_20261123 as robustness
import research_btc15m_reclaim_risk_quality_20261123 as engine
from research_ema20_second_touch import read_source
from research_st_firsttouch_ema20_tp2r_stflip_1h15m import st_and_ema
from research_btc_15m_touch_reclaim_20261123 import make_signals

OUT=Path("analysis/btc15m_short_reclaim_cost_stress_20261123")
CASES={
 "base_taker05_slip02":(.0005*1.18,.0002),
 "same_fee_slip04":(.0005*1.18,.0004),
 "same_fee_slip06":(.0005*1.18,.0006),
 "taker075_slip04":(.00075*1.18,.0004),
}
CHOICES={
 "volume120_SHORT":(4,"volume120+shortonly","ST",1.0,3.0,"none"),
 "volume150_SHORT":(4,"volume150+shortonly","ST",1.0,3.0,"none"),
}
PATHS=("O-H-L-C","O-L-H-C")
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    df,quality=read_source("BTCUSD")
    ema,line,trend,valid=st_and_ema(df,15)
    ind=engine.make_indicators(df)
    signals=make_signals(df,ema,trend,valid,"reclaim",4)[0]
    results=[];monthly=[];trades=[]
    for cost_name,(fee,slip) in CASES.items():
        engine.FEE=fee
        engine.SLIP=slip
        for name,cfg in CHOICES.items():
            for path in PATHS:
                print("RUN",cost_name,name,path,flush=True)
                row,mm,tt=engine.simulate(df,ema,line,trend,ind,name,cfg,signals,path)
                row["cost_case"]=cost_name
                row["fee_plus_gst_each_side"]=fee
                row["slippage_each_side"]=slip
                mm.insert(0,"cost_case",cost_name)
                tt.insert(0,"cost_case",cost_name)
                results.append(row);monthly.append(mm);trades.append(tt)
                print("RESULT",json.dumps(row,sort_keys=True),flush=True)
    rdf=pd.DataFrame(results)
    for choice,n,ret in [("volume120_SHORT",57,7.0098),("volume150_SHORT",32,5.7505)]:
        for path in PATHS:
            row=rdf[(rdf.config==choice)&(rdf.cost_case=="base_taker05_slip02")&(rdf.path_assumption==path)].iloc[0]
            assert int(row.trades)==n and abs(float(row.net_return_pct)-ret)<.001,\
                 ("BASELINE_CONTROL_NOT_REPRODUCED",choice,path,row.to_dict())
    print("BASELINE_PARITY_OK",flush=True)
    rdf.to_csv(OUT/"summary.csv",index=False)
    pd.concat(monthly,ignore_index=True).to_csv(OUT/"monthly_mark_to_market.csv",index=False)
    pd.concat(trades,ignore_index=True).to_csv(OUT/"trades.csv.gz",compression="gzip",index=False)
    table=rdf[rdf.path_assumption=="O-H-L-C"][["config","cost_case","trades","wins",
           "win_rate_pct","profit_factor","net_return_pct","profitable_months",
           "return_2025_pct","return_2026_pct","max_floating_drawdown_pct"]]
    report=["# BTCUSD 15M Reclaim SHORT-only — cost sensitivity","",
       "Fixed signal choices from prior 22-month experiment. This is sensitivity, not additional entry optimisation.",
       "SHORT only; 15m ST(10,3), EMA20, reclaim within 4 completed 15m bars, 15m volume compared to previous 20 15m bars. One entry per ST regime.",
       "1x notional, $1000 initial. 1m OHLC price paths only for exits. Opposite confirmed ST flip / 1R stop / 3R TP.",
       "Jan 2025–Oct 2026 already used for selection: **not** a true out-of-sample test.","",
       "## Costs", "Each cost case lists (fee including 18% GST per side, adverse slip per side).","",
       json.dumps(CASES,indent=2),"",
       "## Results (O-H-L-C assumed 1m path)","",table.to_markdown(index=False),"",
       "No funding, tick-level bid/ask spread, depth, liquidation or latency modeled. Costs cannot validate performance on their own.",
       "See summary.csv and monthly_mark_to_market.csv."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    (OUT/"quality.json").write_text(json.dumps(dict(source_quality=quality,configurations=CHOICES,costs=CASES,
      asset="BTCUSD",signal_tf="15m",higher_tf_signals=False,execution_tf="1m",
      paths=PATHS,notional_multiplier=1,initial_equity_usd=1000,
      holdout_status="already-examined research data; overfitting risk",funding_and_liquidation=False),indent=2)+"\n")
    print("BACKTEST_DONE",len(rdf),flush=True)
if __name__=="__main__":
    main()
