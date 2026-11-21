#!/usr/bin/env python3
"""NO TP, NO SL: 1H EMA20 second touch + 1 entry per Supertrend epoch.
No strategy exit exists; one position held until sample-end accounting mark.
"""
import json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from research_ema20_second_touch import read_source, features, MONTHS, FEE, SLIP

OUT=Path("analysis/ema20_second_touch_1h_no_tp_no_sl_20261121")
INITIAL=1000.
TF=60

def bt(frame,symbol):
    ema,atr,st,complete=features(frame,TF)
    op=frame.open.to_numpy(float)
    hi=frame.high.to_numpy(float)
    lo=frame.low.to_numpy(float)
    close=frame.close.to_numpy(float)
    times=frame.time.to_numpy("int64")
    assert times[0] % (TF*60)==0
    last_direction=0
    last_touch_h=-1
    count=0
    epoch=0
    traded_epochs=set()
    entry_info=None
    first_touch_time=None
    second_touch_time=None
    for i in range(len(frame)):
        htf=i//TF
        previous=htf-1
        if previous<100 or previous>=len(ema) or not complete[previous]:
            continue
        direction=int(st[previous])
        if direction==0 or not np.isfinite(ema[previous]):
            continue
        if last_direction!=direction:
            epoch+=1
            last_direction=direction
            count=0
            last_touch_h=-1
            first_touch_time=None
        # A single open position never closes, and no reentry is possible.
        if entry_info is not None:
            continue
        if epoch in traded_epochs or last_touch_h==htf:
            continue
        level=float(ema[previous])
        if not(lo[i]<=level<=hi[i]):
            continue
        last_touch_h=htf
        count+=1
        if count==1:
            first_touch_time=int(times[i])
            continue
        if count!=2:
            raise AssertionError("Unexpected touch count")
        if epoch in traded_epochs:
            raise AssertionError("More than one trade per Supertrend epoch")
        entry=level*(1+direction*SLIP)
        qty=INITIAL/entry
        fee_in=qty*entry*FEE
        traded_epochs.add(epoch)
        entry_info=dict(symbol=symbol,side=direction,entry=entry,qty=qty,
            entry_fee=fee_in,touch_1_utc=pd.Timestamp(first_touch_time,unit="s",tz="UTC").isoformat(),
            touch_2_utc=pd.Timestamp(int(times[i]),unit="s",tz="UTC").isoformat(),
            entry_time_utc=pd.Timestamp(int(times[i]),unit="s",tz="UTC").isoformat(),
            entry_index=i,entry_supertrend_epoch=epoch,entry_supertrend_direction=direction)
        break
    if entry_info is None:
        return [],dict(symbol=symbol,trade_count=0,unrealized_exit_count=0,remark="No valid second touch observed"),[]
    entry=entry_info["entry"]; side=entry_info["side"]; qty=entry_info["qty"]; fee_in=entry_info["entry_fee"]
    start=entry_info["entry_index"]
    entry_balance=INITIAL-fee_in
    # 1m mark-to-market realization proxy, NOT an order executed. Favorable
    # slippage never credited. Trade is not closed at any point in this series.
    prices=close[start:]
    exit_fill=prices*(1-side*SLIP)
    mtm=entry_balance+side*qty*(exit_fill-entry)-FEE*qty*exit_fill
    adverse_price=lo[start:] if side==1 else hi[start:]
    adverse_fill=adverse_price*(1-side*SLIP)
    worst_equity=entry_balance+side*qty*(adverse_fill-entry)-FEE*qty*adverse_fill
    # Peak of 1m CLOSE equity and conservative 1m wick adverse drawdown.
    peak=np.maximum.accumulate(np.r_[INITIAL,mtm])[1:]
    maxdd=float(np.max((peak-worst_equity)/peak)*100)
    crossing=np.nonzero(worst_equity<=0)[0]
    worst_idx=int(np.argmin(worst_equity))
    min_equity=float(worst_equity[worst_idx])
    worst_ts=pd.Timestamp(int(times[start+worst_idx]),unit="s",tz="UTC").isoformat()
    first_insolvent=(pd.Timestamp(int(times[start+int(crossing[0])]),unit="s",tz="UTC").isoformat()
      if len(crossing) else None)
    max_adverse=float(np.max(np.maximum(0.,(entry-adverse_price)*side)))
    max_adverse_pct=100*max_adverse/entry
    max_favorable=float(np.max(np.maximum(0.,(prices-entry)*side)))
    monthlies=[]
    prev=INITIAL
    for m in MONTHS:
        p=pd.Period(m,freq="M")
        end=(p+1).start_time.tz_localize("Asia/Kolkata").tz_convert("UTC")-pd.Timedelta(minutes=1)
        k=int(np.searchsorted(times,int(end.timestamp()),side="right")-1)
        if k<0 or times[k]!=int(end.timestamp()):
            raise RuntimeError("Missing exact month-end UTC minute: "+m)
        if k<start:
            equity=INITIAL
            active=False
        else:
            equity=float(mtm[k-start])
            active=True
        monthlies.append(dict(symbol=symbol,month_ist=m,
            trade_open_at_month_end=active,
            mark_to_market_equity_usd=round(equity,6),
            monthly_mtm_return_pct=round(100*(equity/prev-1),6) if prev>0 else None,
            realized_exit_pnl_usd=0.,net_floating_mark_pnl_usd=round(equity-INITIAL,6)))
        prev=equity
    last_equity=float(mtm[-1])
    hold_hours=(int(times[-1])-int(times[start]))/3600.
    result=dict(
        symbol=symbol,signal_tf="1h",execution_tf="1m",
        entries=1,normal_exits=0,tp_exits=0,sl_exits=0,
        position_open_at_end=True,forced_end_mark_only=True,
        entry_direction="LONG" if side==1 else "SHORT",
        entry_price=round(entry,5),entry_time_utc=entry_info["entry_time_utc"],
        sample_end_price=round(float(prices[-1]),5),
        sample_end_time_utc=pd.Timestamp(int(times[-1]),unit="s",tz="UTC").isoformat(),
        hypothetical_exit_fee_gst_usd=round(float(FEE*qty*exit_fill[-1]),5),
        entry_fee_gst_usd=round(fee_in,5),
        hypothetical_net_exit_value_usd=round(last_equity,5),
        hypothetical_net_return_pct=round(100*(last_equity/INITIAL-1),5),
        realized_closed_trade_return_pct=0.,
        max_mtm_equity_wick_drawdown_pct=round(maxdd,4),
        min_mtm_equity_usd=round(min_equity,4),
        min_mtm_time_utc=worst_ts,
        equity_at_or_below_zero=bool(len(crossing)>0),
        first_zero_equity_time_utc=first_insolvent,
        maximum_adverse_points=round(max_adverse,5),
        maximum_adverse_pct_of_entry=round(max_adverse_pct,4),
        maximum_favorable_close_points=round(max_favorable,5),
        holding_hours=round(hold_hours,2),
        holding_days=round(hold_hours/24,2),
        profitable_months_mark_to_market=sum(x["monthly_mtm_return_pct"] is not None and x["monthly_mtm_return_pct"]>0 for x in monthlies),
        losing_months_mark_to_market=sum(x["monthly_mtm_return_pct"] is not None and x["monthly_mtm_return_pct"]<0 for x in monthlies),
        supertrend_epoch_entry=epoch,
        one_trade_per_supertrend=True)
    return [entry_info],result,monthlies

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    all_rows=[]
    all_summary=[]
    all_monthly=[]
    quality={}
    for sym in ["BTCUSD","ETHUSD"]:
        print("RUN",sym,flush=True)
        data,q=read_source(sym)
        quality[sym]=q
        entries,s,monthly=bt(data,sym)
        all_rows.extend(entries)
        all_summary.append(s)
        all_monthly.extend(monthly)
        print("RESULT",json.dumps(s,sort_keys=True,default=str),flush=True)
    pd.DataFrame(all_rows).to_csv(OUT/"entries.csv",index=False)
    pd.DataFrame(all_summary).to_csv(OUT/"summary.csv",index=False)
    pd.DataFrame(all_monthly).to_csv(OUT/"monthly_mark_to_market.csv",index=False)
    quality["policy"]={
        "tp":"NONE","sl":"NONE","trailing":"NONE","supertrend_flip_exit":"NONE",
        "time_exit":"NONE","max_entry_count_per_confirmed_supertrend_epoch":1,
        "exit_status":"No normal exit. Position held to final sample mark only.",
        "fees":"0.05 percent taker per side plus 18 percent GST",
        "slippage":"0.02 percent adverse on entry and hypothetical exit",
        "size":"1x notional of initial USD1000 account, each asset independently",
        "exposure":"No funding, actual margin, liquidation, order book or live spreads",
        "first_month":"January 2025 starts only at midnight UTC; first 5.5h IST not covered"}
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    lines=["# 1H EMA20 second-touch with no TP, no SL, no other exit","",
       "No position can close normally; after first entry, the next exit is an accounting-only mark at 2026-10-31.",
       "One-per-Supertrend gate technically active but never tested for re-entry (position remains open).",
       "2025-01 through 2026-10, BTC/ETH Delta India 1m OHLC, mark-to-market returns include estimated hypothetical exit costs.","",
       "| Symbol | Direction | Entry UTC | Hypothetical net return | Peak-to-trough floating drawdown | Held days | Negative MTM months |",
       "|---|---|---|---:|---:|---:|---:|"]
    for s in all_summary:
        if s["entries"]:
            lines.append(f"| {s['symbol']} | {s['entry_direction']} | {s['entry_time_utc']} | {s['hypothetical_net_return_pct']:.3f}% | {s['max_mtm_equity_wick_drawdown_pct']:.3f}% | {s['holding_days']} | {s['losing_months_mark_to_market']}/22 |")
    lines += ["","## Interpretation",
       "- The return is **not realized trading PnL**: no TP, SL, flip, or time exit exists. Only a hypothetical forced end-of-sample sale/cover.",
       "- A single trade cannot measure a win rate or profit factor meaningfully.",
       "- Marked 1m price extremes approximate floating risk conservatively; there is no true tick-level entry/exit data.",
       "- No actual liquidation margin, funding, bid/ask spread, or overnight exposure costs; data history evaluated repeatedly and not untouched.",
       "- ETH and BTC remain independent accounts with 1x notional as an illustrative cash exposure. No leverage used.",
       "","See summary.csv, monthly_mark_to_market.csv, entries.csv, quality.json."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("BACKTEST_DONE",json.dumps(all_summary,default=str),flush=True)
if __name__=="__main__":main()
