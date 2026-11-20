#!/usr/bin/env python3
"""Independent audit of Nov 20 Demo 1h backtest vs Demo indicator time semantics.

No orders, no live-journal access. Uses archived read-only TESTNET candles and
distinct counterfactual fill assumptions; never conflates MARK and traded fill.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from backtest_demo_1h_pm_20261120_ist import (
    OUT, ENTRY_START, ENTRY_END, TZ,
    candidate_signals, indicators, MAX_DEVIATION,
)

REPORT_DIR=OUT
AUDIT=REPORT_DIR/"execution_audit.json"

def read(asset, name):
    p=REPORT_DIR/f"{asset.lower()}_{name}.csv.gz"
    data=pd.read_csv(p,compression="gzip")
    assert "dt" in data.columns or "time" in data.columns
    if "dt" in data.columns:
        data["dt"]=pd.to_datetime(data["dt"],utc=True)
    else:
        data["dt"]=pd.to_datetime(data.time,unit="s",utc=True)
    return data.set_index("dt",drop=False).sort_index()

def inspect(asset):
    h=read(asset,"demo_1h_source")
    trade=read(asset,"demo_traded_1m_source")
    mark=read(asset,"demo_mark_1m_source")
    assert len(trade)==len(mark)==1440
    events,candidates=candidate_signals(h,asset)
    full=indicators(h[["open","high","low","close","volume"]])
    rolling_parity=[]
    for token,ev in events.items():
        t=pd.Timestamp(ev["signal_time_utc"])
        last=t-pd.Timedelta(hours=1)
        first=t-pd.Timedelta(hours=1000)
        window=h.loc[first:last]
        if len(window)!=1000:
            raise AssertionError(f"Expected 1000 exact Demo history bars at {t} but got {len(window)}")
        now=indicators(window[["open","high","low","close","volume"]]).iloc[-1]
        now_prev=indicators(window[["open","high","low","close","volume"]]).iloc[-2]
        prev_full=full.loc[last]
        side=(1 if int(now.dir)==int(now_prev.dir)==-1 and now.low<=now.ema and now.close>now.ema
              else -1 if int(now.dir)==int(now_prev.dir)==1 and now.high>=now.ema and now.close<now.ema
              else 0)
        flip=int(now.dir) if int(now.dir)!=int(now_prev.dir) else 0
        old_side=ev["side"]
        old_flip=ev["flip_direction"]
        rolling_parity.append(dict(
            hour_ist=str(t.tz_convert(TZ)), full_history_side=old_side,
            demo_last_1000_side=side, same_side=old_side==side,
            full_history_flip=old_flip, demo_last_1000_flip=flip,
            same_flip=old_flip==flip,
            ema_diff=round(float(now.ema-prev_full.ema),8),
            atr14_diff=round(float(now.atr14-prev_full.atr14),8),
            demo_rolling_atr14=round(float(now.atr14),5),
        ))

    fill_risks=[]
    for scenario in ("single_close_nooffer",):
        csv=REPORT_DIR/f"{asset.lower()}_{scenario}_trades.csv"
        z=pd.read_csv(csv)
        for _,row in z.iterrows():
            when=pd.Timestamp(row.exit_ist).tz_convert("UTC")
            bar=trade.loc[when]
            markbar=mark.loc[when]
            fill=float(row.exit_proxy)
            q=float(row.qty)
            entry=float(row.entry)
            side=-1 if row.side=="short" else 1
            fee=(entry+fill)*q*0.0005*1.18
            pnl=(fill-entry)*side*q-fee
            if abs(pnl-row.net_usd)>.0003:
                raise AssertionError(f"Ledger PNL mismatch {asset} {when}: {pnl} {row.net_usd}")
            mark_outside=not(float(bar.low)-.00001<=fill<=float(bar.high)+.00001)
            low=float(bar.low)
            high=float(bar.high)
            close=float(bar.close)
            def pnl_at(x):
                return round(((x-entry)*side*q)-(entry+x)*q*.0005*1.18,4)
            fill_risks.append(dict(
                entry_ist=row.entry_ist, exit_ist=row.exit_ist,
                side=row.side,reason=row.exit_reason,
                entry_price=entry, mark_trigger_used_as_fill=fill,
                traded_low=low,traded_high=high,traded_close=close,
                mark_low=float(markbar.low),mark_high=float(markbar.high),
                trigger_outside_traded_ohlc=mark_outside,
                net_original_mark_fill=round(float(row.net_usd),4),
                net_fill_traded_close=pnl_at(close),
                net_fill_traded_worst=pnl_at(low if side==1 else high),
                net_fill_traded_best=pnl_at(high if side==1 else low),
            ))

    gate_details=[]
    for event in candidates:
        t=pd.Timestamp(event["signal_at_utc"])
        first=trade.loc[t]
        following=trade.loc[t+pd.Timedelta(minutes=1)]
        signal=float(event["signal_close"])
        limit_low=signal*(1-MAX_DEVIATION)
        limit_high=signal*(1+MAX_DEVIATION)
        low=float(first.low);high=float(first.high)
        possible=not(high<limit_low or low>limit_high)
        always=low>=limit_low and high<=limit_high
        next_open=float(following.open)
        gate_details.append(dict(
            signal_ist=str(t.tz_convert(TZ)),
            symbol=asset+"USD",side=event["side"],
            prior_hour_close=signal,
            first_minute_low=low,first_minute_high=high,
            first_minute_close=float(first.close),
            minute_later_open=next_open,
            gate_0_2pct_possible_after_10s=possible,
            gate_0_2pct_guaranteed_from_whole_minute=always,
            gate_at_minute_later_open=limit_low<=next_open<=limit_high,
            note="Actual 10-second ticker price unobserved: minute OHLC gate possible is NOT an order",
        ))

    return dict(
        date_ist="2026-11-20",asset=asset,
        rolling_1000_hour_indicator_parity=rolling_parity,
        candidate_gate_sensitivity=gate_details,
        original_trade_mark_vs_traded_audit=fill_risks,
        mark_fill_outside_traded_minute_count=sum(x["trigger_outside_traded_ohlc"] for x in fill_risks),
        post_10second_quote_unavailable=True,
        actual_order_execution_unverified=True,
    )

def main():
    result={a:inspect(a) for a in ("BTC","ETH")}
    AUDIT.write_text(json.dumps(result,indent=2)+"\n")
    for a,data in result.items():
        print("AUDIT_ASSET",a,json.dumps({
            "all_rolling_signal_parity":all(x["same_side"] for x in data["rolling_1000_hour_indicator_parity"]),
            "all_rolling_flip_parity":all(x["same_flip"] for x in data["rolling_1000_hour_indicator_parity"]),
            "mark_fills_outside_traded_range":data["mark_fill_outside_traded_minute_count"],
            "candidate_gates":data["candidate_gate_sensitivity"],
            "trades":data["original_trade_mark_vs_traded_audit"],
        }),flush=True)
    print("AUDIT_COMPLETE",AUDIT)

if __name__=="__main__":
    main()
