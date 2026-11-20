#!/usr/bin/env python3
"""Read-only historical ETHUSD 1h EMA20/ST 100x replay with $0.20 pre-liquidation stop.

ONE strategy change versus the 2026-11-20 reference 100x replay:
  When the current stop is farther away than a modeled stop $0.20 before
  the modeled liquidation price, tighten that stop to the pre-liquidation
  barrier. For a LONG this is liquidation+$0.20 (rounded UP to tick); for
  a SHORT liquidation-$0.20 (rounded DOWN).
No entry filtering, trailing changes, sizing changes, or caps.
Stop-market price-level simulation is NOT a fill or avoidance guarantee.
"""
from pathlib import Path
import json
import math
import pandas as pd
import numpy as np
import backtest_eth_ema_st_1h_100x_20261120 as original

OUT=Path("analysis/eth_ema_st_1h_100x_preliq_020_20261120")
BUFFER_USD=0.20
TICK=0.05
ORIGINAL_BENCHMARK_NET=3826.8616
ORIGINAL_BENCHMARK_LIQ=230
_ORIGINAL_STOP_OR_LIQ=original.stop_or_liquidation

def rounded_preliq(liq,side):
    # These are price ticks, not contract values.
    if side==1:
        return math.ceil((liq+BUFFER_USD-1e-10)/TICK)*TICK
    if side==-1:
        return math.floor((liq-BUFFER_USD+1e-10)/TICK)*TICK
    raise AssertionError("Invalid side")

def guarded_stop_or_liquidation(a,z,p):
    """Simulate *existing* ATR/trail plus tighter pre-liq stop, same 1h OHLC path."""
    side=p["side"]
    entry=p["entry"]
    liq=p["liquidation_price"]
    native=p["initial_stop"]
    if p["trail"] is not None:
        native=max(native,p["trail"]) if side==1 else min(native,p["trail"])
    preliq=rounded_preliq(liq,side)
    stop=max(native,preliq) if side==1 else min(native,preliq)
    # A preliq stop must be an exit barrier in the adverse direction.
    assert (stop<entry if side==1 else stop>entry),(entry,liq,stop)

    # Original logic treats a price opening beyond the liquidation barrier as
    # liquidation. Keep this behavior: gap-through protection cannot be guaranteed.
    if (side==1 and a<=liq) or (side==-1 and a>=liq):
        return float(a),"liquidation"
    if (side==1 and a<=stop) or (side==-1 and a>=stop):
        preliq_active=(preliq>native if side==1 else preliq<native)
        return float(a),("preliq_gap" if preliq_active else "stop_gap")

    # Favorable segment has unchanged original activation and trail behavior.
    if (z-a)*side>0:
        return _ORIGINAL_STOP_OR_LIQ(a,z,p)
    if (z-a)*side>=0:
        return None,None

    # For adverse moves, the tighter stop is struck before estimated liquidation
    # unless there is a gap, which is checked above.
    if (side==1 and z<=stop) or (side==-1 and z>=stop):
        preliq_active=(preliq>native if side==1 else preliq<native)
        return float(stop),("pre_liquidation_stop" if preliq_active else "initial_or_trailing_stop")
    return None,None

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    bars,quality=original.base.source()
    direction,atr14,long,short=original.base.features(bars)

    # Replay baseline from the SAME frozen branch/data to prevent any
    # accidental differences beyond adding $0.20 pre-liq protection.
    baseline,baseline_stats,_=original.run_replay(
        bars,direction,atr14,long,short)
    if (abs(baseline_stats["net_profit_usd"]-ORIGINAL_BENCHMARK_NET)>0.001
            or baseline_stats["modeled_liquidations"]!=ORIGINAL_BENCHMARK_LIQ):
        raise AssertionError("Original 100x strategy benchmark changed; comparison invalid")

    original.stop_or_liquidation=guarded_stop_or_liquidation
    protected,protected_stats,position=original.run_replay(
        bars,direction,atr14,long,short)

    monthly=original.monthly_results(protected)
    baseline_monthly=original.monthly_results(baseline)
    assert len(monthly)==22 and len(baseline_monthly)==22
    assert abs(monthly.net_profit_usd.sum()-protected_stats["net_profit_usd"])<0.003
    assert protected_stats["modeled_liquidations"]<=baseline_stats["modeled_liquidations"]

    protected_stats["profitable_months"]=int((monthly.net_profit_usd>0).sum())
    protected_stats["losing_months"]=int((monthly.net_profit_usd<0).sum())
    protected_stats["flat_months"]=int((monthly.net_profit_usd==0).sum())
    protected_stats["pre_liquidation_stop_exits"]=int(
        protected.reason.isin(["pre_liquidation_stop","preliq_gap"]).sum())
    protected_stats["pre_liquidation_price_level_exits"]=int(
        (protected.reason=="pre_liquidation_stop").sum())
    protected_stats["pre_liquidation_gapped_exits"]=int(
        (protected.reason=="preliq_gap").sum())
    baseline_stats["profitable_months"]=int((baseline_monthly.net_profit_usd>0).sum())
    baseline_stats["losing_months"]=int((baseline_monthly.net_profit_usd<0).sum())

    comparison={
      "status":"completed_replay_preliq_020_assumed_stop_fill",
      "source":"BTC-Analysis ETHUSD 22-month verified 1m archive, 1h candle replay",
      "source_metadata":quality,
      "instrument":"ETHUSD",
      "unchanged_settings":{
          "initial_balance_usd":100,"isolated_margin_per_trade_usd":10,"leverage":100,
          "signal_timeframe":"1h","stop_monitoring_timeframe":"1h",
          "entry_rule":"EMA20 pullback, Supertrend(10,3) direction",
          "initial_stop":"2 ATR(14)",
          "trailing_activation_btc_equivalent_points":100,
          "trailing_distance_btc_equivalent_points":50,
          "trailing_activation_eth_entry_pct":0.125,
          "trailing_distance_eth_entry_pct":0.0625,
          "master_volume_volatility_filter":"Off",
          "fee_taker_each_side":0.0005,"GST_on_fees":0.18,
          "scalper_eligibility_window_min":27,"funding":0,"slippage":0,
          "ETH_per_contract":0.01,
          "maintenance_margin_proxy_rate":0.0025,
      },
      "only_change":{
          "pre_liquidation_protective_stop_enabled":True,
          "pre_liquidation_ETH_buffer_usd":BUFFER_USD,
          "long_stop": "max(native ATR/trailing stop, CEIL((estimated liquidation price + 0.20)/0.05)*0.05)",
          "short_stop":"min(native ATR/trailing stop, FLOOR((estimated liquidation price - 0.20)/0.05)*0.05)",
          "entry_filter_changed":False,
      },
      "baseline_100x_without_preliq":baseline_stats,
      "protected_100x_with_preliq":protected_stats,
      "warnings":[
        "Pre-liquidation stop is not an entry filter; it tightens the exit price to a modeled threshold.",
        "1h OHLC replay assumes the protective stop fills at its level on a crossing; stop execution may slip or fail in real trading.",
        "Liquidation modeled from last-trade candle prices and an assumed 0.25% maintenance rate, not actual historical Delta mark-price liquidation.",
        "The $0.20 buffer is Delta-Algo-Demo's ETH demo setting. Whether it is adequate requires exchange-confirmed liquidation and order-book testing.",
        "At a bar opening beyond liquidation, the model records liquidation, not a pre-liquidation fill.",
        "Historical 27-minute scalper fee eligibility cannot be proven with 1h OHLC; replay conservatively charges exit taker fee on all trades.",
        "Funding, spread, slippage and latency are excluded, as in the original 100x backtest.",
        "Returns are simulated, not reliable forecasts; no account or margin-mode change was made."]}

    protected.to_csv(OUT/"protected_trades.csv.gz",index=False,compression="gzip")
    monthly.to_csv(OUT/"protected_monthly.csv",index=False)
    baseline_monthly.to_csv(OUT/"baseline_monthly.csv",index=False)
    (OUT/"comparison.json").write_text(json.dumps(comparison,indent=2)+"\n")
    report=["# ETHUSD 1h 100x — $0.20 pre-liquidation stop comparison",
            "",
            "Settings unchanged from baseline except adding a protective stop $0.20 before estimated liquidation, tick-aligned.",
            "",
            "| Model | Net profit | Ending balance | PF | Trades | Modeled liquidations | Pre-liq exits | Profitable months |",
            "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for label,d in [("Without preliq",baseline_stats),("With preliq + $0.20",protected_stats)]:
        report.append(f"| {label} | {d['net_profit_usd']:+.2f} | {d['ending_balance_usd']:.2f} | {d['profit_factor']} | {d['trades']} | {d['modeled_liquidations']} | {d.get('pre_liquidation_stop_exits','-')} | {d['profitable_months']}/22 |")
    report+=["","## Monthly P&L: pre-liquidation enabled","",monthly.to_markdown(index=False),
              "","## Caveats",""]
    report.extend("- "+w for w in comparison["warnings"])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("ETH_PRELIQ_COMPARISON "+json.dumps(
        {"baseline":baseline_stats,"preliq":protected_stats},separators=(",",":"),default=str),flush=True)
    print("ETH_PRELIQ_MONTHLY\n"+monthly.to_csv(index=False),flush=True)

if __name__=="__main__":
    main()
