#!/usr/bin/env python3
"""ETHUSD EMA20/Supertrend: 1-hour signals/stop monitoring + BOTH minimum filters.

Reuses the established ETH screenshot replay implementation unchanged for
historical loading, EMA/ST, ATR stop, 100/50 fixed-price trailing, fills and
taker fees/GST. The only signal change is requiring both:
  ATR14(current)/SMA(ATR14 previous 20 completed hours) >= 1.0
  Vol(current)/SMA(Vol previous 20 completed hours) >= 1.5
The maximum volatility and volume filters remain disabled.
"""
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
import backtest_eth_ema_st_1h_27min_20261120 as baseline

OUT=Path("analysis/eth_ema_st_1h_min_vol_filters_20261120")
ATR_BASELINE=20
MIN_ATR_RATIO=1.0
VOLUME_BASELINE=20
MIN_VOLUME_RATIO=1.5

def filtered_features(bars):
    direction, atr14, long, short = baseline.features(bars)
    current_atr=pd.Series(atr14,dtype=float)
    current_vol=pd.Series(bars.volume.to_numpy(float),dtype=float)
    # Shift(1) guarantees current bar is not included in the baseline.
    atr_reference=current_atr.shift(1).rolling(ATR_BASELINE,min_periods=ATR_BASELINE).mean()
    volume_reference=current_vol.shift(1).rolling(VOLUME_BASELINE,min_periods=VOLUME_BASELINE).mean()
    a=current_atr.to_numpy(float)
    v=current_vol.to_numpy(float)
    a_ref=atr_reference.to_numpy(float)
    v_ref=volume_reference.to_numpy(float)
    with np.errstate(divide="ignore",invalid="ignore"):
        atr_ratio=a/a_ref
        volume_ratio=v/v_ref
    eligible=np.isfinite(atr_ratio)&np.isfinite(volume_ratio)&(atr_ratio>=MIN_ATR_RATIO)&(volume_ratio>=MIN_VOLUME_RATIO)
    return direction,atr14,long&eligible,short&eligible,{
        "raw_long_signals":int(long.sum()),
        "raw_short_signals":int(short.sum()),
        "filtered_long_signals":int((long&eligible).sum()),
        "filtered_short_signals":int((short&eligible).sum()),
        "bars_passing_filters":int(eligible.sum()),
    }

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    bars,quality=baseline.source()
    direction,atr14,long,short,checks=filtered_features(bars)
    # Exact original 100 ETH point activation and 50 ETH point trail.
    trades,signals,open_position=baseline.replay(
        bars,direction,atr14,long,short,percentage_scaled=False)
    if trades.empty:
        raise RuntimeError("No trades: filter or replay may be misconfigured")
    assert (trades.holding_minutes>=60).all()
    assert not trades.duplicated(["entry_ns","direction"]).any()
    after_cost=baseline.costs(trades,27,slippage_points=0.0)
    monthly=baseline.month_results(after_cost)
    totals=baseline.metrics(after_cost,monthly)
    monthly.to_csv(OUT/"monthly_1h_both_min_filters_27min_conservative.csv",index=False)
    after_cost.to_csv(OUT/"trades_1h_both_min_filters_27min_conservative.csv.gz",
                      index=False,compression="gzip")
    result={
        "instrument":"ETHUSD",
        "source":quality,
        "strategy":{
           "entry_timeframe":"1h","stop_monitoring_timeframe":"1h",
           "supertrend_atr":10,"supertrend_factor":3,"ema_length":20,
           "entry_pullback_mode":"EMA20",
           "st_touch_candle_shape":False,"st_wick_only_touch":False,
           "initial_stop":"ATR14 x 2",
           "trailing_stop_enabled":True,"trailing_mode":"Fixed Points (Original)",
           "trailing_distance_enabled":True,"trailing_activation_points":100,
           "trailing_distance_points":50,
           "independent_trailing_stop_points_enabled":False,
           "entry_volume_volatility_filter":"Both",
           "volatility_atr_length":14,
           "volatility_baseline_previous_candles":20,
           "enable_minimum_volatility":True,"minimum_volatility_atr_x":1.0,
           "enable_maximum_volatility":False,
           "volume_baseline_previous_candles":20,
           "enable_minimum_volume":True,"minimum_volume_x":1.5,
           "enable_maximum_volume":False,
           "quantity_per_contract_eth":0.01,
           "order_entry":"Taker","order_exit":"Taker",
           "taker_fee_pct_each_side":0.05,
           "gst_on_trading_fees_pct":18,
           "scalper_offer_assumed_active_entire_period":True,
           "scalper_qualifying_window_minutes":27,
           "funding_pct_per_8h":0,
           "slippage_per_fill_price_points":0
        },
        "signals":checks,
        "completed_trades":totals,
        "open_position_at_history_end":open_position,
        "notes":[
           "Identical original ETH 1h 100/50 backtest rules except BOTH minimum volume and ATR filters enabled for entry.",
           "Volume and ATR baselines use previous 20 fully closed hourly candles only; no look-ahead.",
           "27-minute Scalper Offer window cannot be confirmed for intrabar exits from 1h OHLC; conservative model charges closing fee on all trades.",
           "Fee and GST are modeled, not confirmed exchange settlement; offer entitlement historically unverified.",
           "Historical 1h OHLC fills approximate TradingView and live market; no actual orderbook spread, funding, liquidation or margin.",
           "One 0.01 ETH contract, constant size; no leverage or account compounding.",
           "22 complete UTC months January 2025 to October 2026."
        ]
    }
    (OUT/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    r=["# ETHUSD 1h EMA/ST with minimum ATR and volume filters",
       "", "Source: Delta Exchange India ETHUSD 1m data grouped into complete 1h bars.",
       "Exactly the existing fixed 100/50 ETH trailing strategy, 1h entry and 1h monitoring.",
       "Changed entry-filter master switch from Off to Both, with ATR(14) >= 1.0x average ATR over previous 20 bars and Volume >= 1.5x average of previous 20 bars.",
       "", "## Results (one 0.01 ETH contract, fees and GST modeled)",
       "", "| Trades | Net P&L USD | PF | Win rate | Positive months |",
       "|---:|---:|---:|---:|---:|",
       f"| {totals['trades']} | {totals['net_profit_usd']:+.4f} | {totals['profit_factor']} | {totals['win_rate_pct']:.3f}% | {totals['profitable_months']}/22 |",
       "", "## Monthly net profit (UTC)",
       "",monthly.to_markdown(index=False),
       "", "## Limitations",*["- "+x for x in result["notes"]]]
    (OUT/"REPORT.md").write_text("\n".join(r)+"\n")
    print("ETH_1H_BOTH_FILTERS "+json.dumps({
        "source":quality,"signals":checks,"totals":totals,
        "open_position":open_position},separators=(",",":"),default=str))
    print("MONTHLY_ETH_1H_BOTH_FILTERS\n"+monthly.to_csv(index=False))

if __name__=="__main__":
    main()
