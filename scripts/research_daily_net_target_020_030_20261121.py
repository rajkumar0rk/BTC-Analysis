#!/usr/bin/env python3
"""User-directed fixed-account-target sensitivity on unchanged BTC 15m scalp signals.

+0.20%, +0.30% net account per winner; -0.60% net hard stop; one trade/day.
Does not optimize signal conditions, asset, history or retrospectively filter dates.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

import research_daily_1pct_scalp_20261121 as src

OUT=Path("analysis/daily_net_020_030_scalp_20261121")
FIXED_TARGETS=(("net020",0.002),("net030",0.003))
STOP=-0.006
FAMILIES=("trend","sweep","combined")

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    bars,quality=src.read_data()
    if quality["missing_utc_minutes"]!=0:
        raise AssertionError("Unexpected minute gaps, reject current results")
    entries=src.features(bars)
    if not any(entries.values()):
        raise AssertionError("No eligible entry signals: source or timestamp bug")
    models=[];monthly_rows=[];daily_rows=[];ledger_rows=[]
    for tag,tp in FIXED_TARGETS:
        src.NET_TP=tp
        src.NET_SL=STOP
        assert src.LEVERAGE==2.0 and src.MAX_HOLD==240
        for family in FAMILIES:
            ledger=src.run_model(bars,entries,family)
            days,monthly,metrics=src.audit(ledger,family,quality)
            if len(days)!=669 or len(monthly)!=22:
                raise AssertionError("Incomplete IST calendar horizon")
            if len(ledger)!=len(set(ledger.day_ist)):
                raise AssertionError("One entry per day violated")
            target_n=int((ledger.exit_reason=="target").sum())
            if target_n:
                target_net=ledger.loc[ledger.exit_reason=="target","net_account_pct"].to_numpy(float)
                if not np.allclose(target_net,100*tp,atol=1e-6):
                    raise AssertionError("Net target did not reconcile to exact account percent")
            stop=ledger[ledger.exit_reason=="stop"]
            if len(stop) and np.any(stop.net_account_pct.to_numpy(float) > 100*STOP+1e-4):
                raise AssertionError("Net stop miscomputed")
            label=f"{tag}_{family}"
            metrics.update({
               "scenario":label,
               "net_target_account_pct":round(100*tp,2),
               "net_hard_stop_account_pct":round(100*STOP,2),
               "target_hits":target_n,
               "target_hit_rate_trading_days_pct":round(100*target_n/len(ledger),2) if len(ledger) else 0,
               "actual_win_rate_pct":round(100*metrics["profitable_trades"]/len(ledger),2) if len(ledger) else 0,
               "all_days_target_hit_pct":round(100*target_n/len(days),2),
               "avg_trade_account_return_pct":round(float(ledger.net_account_pct.mean()),4) if len(ledger) else 0
            })
            metrics.pop("days_net_1pct_target_reached",None)
            metrics.pop("daily_target_hit_pct_all_days",None)
            models.append({k:v for k,v in metrics.items() if k not in ("data_quality","constraints","model")})
            monthly=monthly.rename(columns={"target_1pct_days":"target_hit_days"})
            monthly["scenario"]=label
            monthly["target_account_pct"]=100*tp
            monthly_rows.append(monthly)
            days["scenario"]=label
            daily_rows.append(days)
            ledger["scenario"]=label
            ledger_rows.append(ledger)
    summary={"scenarios":models,"source_quality":quality,
      "research_classification":"PREDECLARED parameter sensitivity, NOT new alpha or independent holdout",
      "exact_rules":{
         "base_entry_replay":"scripts/research_daily_1pct_scalp_20261121.py",
         "net_account_take_profit_pct":[0.20,0.30],
         "net_account_stop_loss_pct":-0.60,
         "notional_exposure_multiplier":2.0,
         "entry_trades_max_per_ist_day":1,
         "trading_hours_ist":"12:00 to 18:59",
         "max_holding_minutes":240,
         "entry_timeframe":"15min completed, 1h EMA filter",
         "exit_timeframe":"native 1min stop first",
         "fee_gst":"0.05% taker/side +18% GST",
         "adverse_slippage":"5 BTC points/side"
      },
      "limitations":[
          "Previously reviewed sample; 2026 is NOT an unseen holdout",
          "Underlying signals were previously unprofitable at +1%/-1%",
          "Reducing TP without fee reduction need not improve expectancy",
          "No funding, measured spreads, lot sizing, liquidation, or order-book fills",
          "No minimum trade requirement; no-trade days count against daily-income objective",
          "Stop can slip worse if price gaps; target uses optimistic level fills within 1m OHLC",
          "Market orders at same 1-minute open assumed; does not simulate exchange API latency",
      ]}
    pd.concat(monthly_rows,ignore_index=True).to_csv(OUT/"monthly_results.csv",index=False)
    pd.concat(daily_rows,ignore_index=True).to_csv(OUT/"daily_results.csv",index=False)
    pd.concat(ledger_rows,ignore_index=True).to_csv(OUT/"trade_ledger.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    header=["# BTC futures daily scalp at +0.20% or +0.30% NET account return","",
      "Fixed inputs: 2x equity notional, one entry per IST day, 15m/1h signals,",
      "1m execution, take profit +0.20% or +0.30% **after** taker fees, GST",
      "and $5/side slippage; protective stop -0.60% net; 4h time expiry.","",
      "## Summary of six pre-registered scenarios",""]
    shown=["scenario","trades","profitable_trades","losing_or_flat_trades",
       "positive_days","negative_days","no_trade_or_flat_days",
       "target_hits","target_hit_rate_trading_days_pct",
       "net_compounded_return_pct","profit_factor_usd",
       "months_positive","months_negative","months_zero",
       "max_trade_close_drawdown_pct","total_fee_gst_usd","total_slippage_usd",
       "year2025_return_pct","year2026_JanOct_return_pct"]
    header += [pd.DataFrame(models)[shown].to_markdown(index=False),"",
       "## Every monthly outcome","",
       pd.concat(monthly_rows,ignore_index=True)[
         ["scenario","month_ist","trades","target_hit_days","winning_days","losing_days",
          "no_trade_or_flat_days","monthly_return_pct"]].to_markdown(index=False),"",
       "## Limitations",""]
    header +=["- "+v for v in summary["limitations"]]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(header)+"\n")
    print("NET_020_030_DAILY_AUDIT",json.dumps(models))
    print("MONTHLY_COUNTS")
    print(pd.concat(monthly_rows,ignore_index=True).to_string(index=False))

if __name__=="__main__":
    main()
