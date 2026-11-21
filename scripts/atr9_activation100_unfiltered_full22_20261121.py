#!/usr/bin/env python3
"""Unfiltered 1H EMA20/ST10,3: activation 100, 9xATR14 profit trail.

22 complete UTC months 2025-01..2026-10. Both BTC/ETH.
Entry ONLY from existing 1H EMA20 touch/reclaim in continuing ST trend;
NO volume ratio, NO volatility ratio, NO upper caps.
Initial 1m native MARK stop 2xATR(14), opposite ST exit preserved.
Trailing profit activated only when completed 1H close advances 100 BTC
points (ETH entry-scaled BTC-equivalent points). 1H completed best CLOSE
+/- 9x confirmed 1H ATR14; updates effective FOLLOWING hour only.
Both 1H close exit and 1M intrabar profit-trigger alternatives tested;
both MARK and traded-price profit sources, emergency stop always MARK.
No lookahead, no orders, no live bot modifications.
Reference ~$1000 notional, 0.05% taker fee both sides + 18% GST.
Unfunded model excludes funding, spreads, actual fills, PM/liquidation.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from atr_hybrid_1h_close_vs_1m_full22_20261121 import (
    data_arrays, replay, ledger_frame, get_summary, unit_tests, MONTHS
)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"1h_activation100_atr9_unfiltered_full22_20261121"
OUT.mkdir(parents=True,exist_ok=True)
ACTIVATION=100.
MULTIPLIER=9.
EXIT_MODES=(("1H_CLOSE",0),("1M_TRIGGER",1))
SOURCES=(("MARK",0),("TRADED",1))

def main():
    unit_tests()
    report={
       "study":"activation 100 points and 9xATR(14) hourly profit trailing, volume and volatility OFF",
       "months":MONTHS,
       "period_utc":"2025-01-01 through 2026-10-31 inclusive, complete months only",
       "assets":["BTCUSD","ETHUSD"],
       "volume_filter_enabled":False,
       "volatility_filter_enabled":False,
       "activation_btc_equivalent_points":ACTIVATION,
       "eth_activation":"Scaled from BTC equivalent points by ETH entry price /80000, tick rounded",
       "profit_trailing_atr14_multiplier":MULTIPLIER,
       "hourly_signal":"EMA20 touch/reclaim with continuing Supertrend(10,3)",
       "hourly_tp_rule":"Activate only on completed favorable 1H close, use best completed 1H close and 9xATR14; never loosen; effective next hour",
       "execution_modes":{"1H_CLOSE":"close-confirmed profit exit at next 1m traded OPEN",
                          "1M_TRIGGER":"previously installed hourly profit stop triggered by 1m high-low; exit traded 1m CLOSE as proxy"},
       "protective_stop":"2xATR14 initial emergency stop, checked every minute on MARK OHLC",
       "trend_flip":"opposite hourly Supertrend flip exits at following hour boundary",
       "costs":"0.05% taker each side and 18% GST; exclude true fills/slippage, spread, funding, liquidation",
       "capital":"fixed 1000USD target notional research only; not funded $100 wallet simulation",
       "selection":"No parameter selection in this run; user-chosen 100/9xATR",
       "scenarios":{},"datasets":{},
    }
    allrows=[]
    for asset in ("BTC","ETH"):
        args,info=data_arrays(asset)
        report["datasets"][asset]=info
        assert np.count_nonzero(args[9])>1000, "Original unfiltered signals absent"
        for mode,mode_id in EXIT_MODES:
            for source,source_id in SOURCES:
                raw,skips,openinfo=replay(*args,ACTIVATION,MULTIPLIER,int(asset=="ETH"),mode_id,source_id)
                ledger=ledger_frame(raw)
                full=get_summary(ledger,MONTHS)
                train=get_summary(ledger,MONTHS[:12])
                holdout=get_summary(ledger,MONTHS[12:])
                code=f"{asset.lower()}_{mode.lower()}_{source.lower()}"
                reasons=ledger.exit_reason.value_counts().to_dict() if len(ledger) else {}
                this={
                    "asset":asset,"exit_mode":mode,"price_source":source,
                    "all22":full,
                    "train2025":{k:v for k,v in train.items() if k!="monthly"},
                    "holdout2026_jan_oct":{k:v for k,v in holdout.items() if k!="monthly"},
                    "entry_signal_count":int(np.count_nonzero(args[9])),
                    "exit_reasons":{str(k):int(v) for k,v in reasons.items()},
                    "still_open_at_2026_10_31":bool(openinfo[0]),
                    "skipped_signals":{"entry_deviation":int(skips[0]),
                                       "minimum_contract":int(skips[1]),
                                       "native_mark_stop_already_crossed":int(skips[2]),
                                       "one_position_already_open":int(skips[3])}
                }
                report["scenarios"][code]=this
                pd.DataFrame([{"month_utc":k,**v} for k,v in full["monthly"].items()]).to_csv(
                    OUT/f"{code}_monthly.csv",index=False)
                ledger.to_csv(OUT/f"{code}_trades.csv.gz",index=False,compression="gzip")
                allrows.append({
                   "asset":asset,"exit_mode":mode,"price_source":source,
                   **{k:v for k,v in full.items() if k!="monthly"},
                   "train2025_usd":train["net_usd"],
                   "holdout2026_usd":holdout["net_usd"],
                   "still_open":bool(openinfo[0])
                })
                print("ATR9_100_RESULT",code,json.dumps({
                  "full_net":full["net_usd"],"pf":full["profit_factor"],
                  "months_positive":full["positive_months"],"trades":full["trades"],
                  "max_closed_trade_dd":full["max_closed_trade_drawdown_usd"],
                  "train2025":train["net_usd"],"holdout2026":holdout["net_usd"],
                  "exit_reasons":this["exit_reasons"]
                }),flush=True)
        del args
    pd.DataFrame(allrows).to_csv(OUT/"comparison.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    print("UNFILTERED_ACTIVATION100_ATR9_SUCCESS",OUT,flush=True)
if __name__=="__main__":
    main()
