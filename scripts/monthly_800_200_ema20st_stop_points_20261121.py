#!/usr/bin/env python3
"""Monthly BTC/ETH 1h EMA20 ST trailing STOP POINTS: latest weekly winners.

Reads existing 2025-01..2026-11-17 verified 1m traded+MARK archive, fetching
any newer public Delta India prices through current 12-minute safety cutoff.
Does not touch collector or trading bots. Uses exact existing causal
point-stop 1m engine and 0.05%/side taker fees plus GST18%.
Does NOT model funding, real bid/ask fills, order-book slippage or PM
liquidation. $1000 target notional with unlimited reference funding
(equity curve can become negative), NOT a fundable $100 account.

Comparisons:
 Both BTC and ETH: activation 800, additional trailing-stop 200.
 Original Fixed Trailing Distance DISABLED. No other strategy change.

All monetary results are USD; month buckets are UTC. November 2026 is
PARTIAL until most recent minute, not a full month. Report model sensitivity.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone,timedelta
from pathlib import Path

import pandas as pd
from optimize_1h_additional_trailing_stop_points_20261121 import (
    checks,run_one,month_table,metrics,MONTHS
)
from week_nov16_2026_ema20st_stop_points import prepare

OUT=Path(__file__).resolve().parents[1]/"analysis"/"monthly_800_200_20261121"
OUT.mkdir(parents=True,exist_ok=True)
CFG={
    "BTC":{"activation800_stop200":(800,200)},
    "ETH":{"activation800_stop200":(800,200)}
}
def main():
    checks()
    end=int((datetime.now(timezone.utc)-timedelta(minutes=12)).timestamp())//60*60
    limit=pd.Timestamp(end,unit="s",tz="UTC")
    if not pd.Timestamp("2026-11-21 00:00",tz="UTC")<=limit<pd.Timestamp("2026-11-23",tz="UTC"):
        raise RuntimeError(f"Unexpected current period: {limit}")
    res={
      "title":"Monthly results: activation 800 / additional Trailing Stop Points 200, both BTC and ETH",
      "data_last_utc_inclusive":str(pd.Timestamp(end-60,unit="s",tz="UTC")),
      "partial_month_note":"Nov 2026 only up to cutoff. Excluded from 22-complete-month total.",
      "monthly_timezone":"UTC",
      "venue":"Delta India PRODUCTION 1m traded and MARK historical candles, not Delta DEMO",
      "stops":"1H EMA20/ST(10,3) stable direction; 2 ATR14 initial risk stop. Extra trailing stop points enabled; original fixed trailing distance OFF; 1m stop updates take effect in NEXT minute. Stop triggered via MARK or traded price candle.",
      "eth_conversion":"ETH activation/trailing points scaled by entry/80000 and rounded to .05 tick",
      "execution_assumptions":"1m mark/traded OHLC cross existing stop; exit approximated using 1m traded CLOSE when stop triggered within minute, traded OPEN for gap/flip",
      "costs":"regular taker fee 0.05% EACH side plus 18% GST; excludes funding, bid/ask execution slippage, liquidation",
      "sizing":"fixed target ~$1000 notional per trade. No wallet gate. Results are NOT possible $100 account trajectory if wallet depleted.",
      "selection_bias":"weekly-winner settings were selected IN SAMPLE using same week, not independent validation",
      "datasets":{},"configs":{},
    }
    compare=[]
    for asset,configs in CFG.items():
        args,info=prepare(asset,end)
        res["datasets"][asset]=info
        for name,(activation,stop) in configs.items():
            pair={"activation_points":activation,"trailing_stop_points":stop,"models":{}}
            mode_ledgers={}
            for mode in ("mark","traded"):
                ledger,summary=run_one(args,asset,mode,activation,stop,False)
                month=month_table(ledger)
                d={
                    "model":mode,
                    "train_2025":summary["train_2025"],
                    "holdout_2026_jan_oct":summary["holdout_2026_jan_oct"],
                    "complete_22_months":summary["all_22_months"],
                    "nov_2026_partial":summary["nov_2026_partial"],
                    "monthly":month,
                    "open_at_latest_cutoff":summary["open_position_at_end"],
                }
                pair["models"][mode]=d
                month_path=OUT/f"{asset.lower()}_{name}_{mode}_monthly.csv"
                pd.DataFrame(month).to_csv(month_path,index=False)
                ledger.to_csv(OUT/f"{asset.lower()}_{name}_{mode}_trades.csv.gz",
                              index=False,compression="gzip")
                mode_ledgers[mode]=ledger
                print("MONTHLY_RUN",asset,name,mode,json.dumps({
                    "full22":d["complete_22_months"]["net_usd"],
                    "train":d["train_2025"]["net_usd"],
                    "holdout":d["holdout_2026_jan_oct"]["net_usd"],
                    "nov_partial":d["nov_2026_partial"]["net_usd"],
                    "trades":d["complete_22_months"]["trades"]}),flush=True)
            res["configs"][f"{asset.lower()}_{name}"]=pair
            for i,m in enumerate(MONTHS):
                markrow=pair["models"]["mark"]["monthly"][i]
                traderow=pair["models"]["traded"]["monthly"][i]
                assert markrow["month_utc"]==m and traderow["month_utc"]==m
                compare.append({
                  "asset":asset,"setting":name,
                  "activation":activation,"trailing_stop_points":stop,
                  "month_utc":m,"complete_month":m<="2026-10",
                  "mark_net_usd":markrow["net_usd"],
                  "mark_trades":markrow["trades"],
                  "mark_pf":markrow["pf"],
                  "traded_net_usd":traderow["net_usd"],
                  "traded_trades":traderow["trades"],
                  "traded_pf":traderow["pf"],
                })
        del args
    pd.DataFrame(compare).to_csv(OUT/"monthly_all_combinations_comparison.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(res,indent=2)+"\n")
    print("MONTHLY_WEEKLY_WINNERS_COMPLETE",str(OUT),flush=True)

if __name__=="__main__":
    main()
