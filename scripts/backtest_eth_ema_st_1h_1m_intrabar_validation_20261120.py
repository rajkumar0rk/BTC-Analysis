#!/usr/bin/env python3
"""ETHUSD one-minute intrabar execution cross-check for 1h EMA/ST signal logic.

Separate sensitivity to 1h TradingView OHLC path: keep signals on CLOSED 1h
bars, but execute stops/trails on 1m historical OHLC and assign 1m upper-bound
timestamps for 27m Scalper Offer. No API orders, margin, funding, or spread.
"""
import hashlib
import json
import numpy as np
import pandas as pd
from pathlib import Path
import backtest_eth_ema_st_1h_27min_20261120 as h

def minutes():
    manifest=json.loads((h.ROOT/"manifest.json").read_text())
    months=set(h.MONTHS)
    parts=[p for p in manifest["partitions"] if p["file"][:-7] in months]
    assert len(parts)==22
    raw=[]
    for p in parts:
        file=h.ROOT/p["file"]
        assert hashlib.sha256(file.read_bytes()).hexdigest()==p["sha256_gzip"]
        assert p["missing_minutes"]==0
        f=pd.read_csv(file,compression="gzip",usecols=["time","open","high","low","close"])
        assert len(f)==p["observed_candles"]
        raw.append(f)
    d=pd.concat(raw,ignore_index=True)
    assert (np.diff(d.time.to_numpy(np.int64))==60).all()
    return d

def replay_m1(b,raw,direction,atr14,long,short,scaled):
    open_=raw.open.to_numpy(float)
    high_=raw.high.to_numpy(float)
    low_=raw.low.to_numpy(float)
    close_=raw.close.to_numpy(float)
    times=raw.time.to_numpy(np.int64)
    pos=None
    records=[]
    for j in range(len(raw)):
        t=int(times[j])
        # The hourly bar just closed at the START of this minute.
        # Re-check the most recently closed hourly signal, not chart forming bar.
        if j>=60 and j%60==0:
            i=j//60-1
            assert int(b.index[i].timestamp())==t
            closed_at_boundary=False
            if pos is not None and i>0:
                down=int(direction[i])==1 and int(direction[i-1])==-1
                up=int(direction[i])==-1 and int(direction[i-1])==1
                if (pos["side"]==1 and down) or (pos["side"]==-1 and up):
                    # Flip known exactly at hour close; fill assumed next 1m open.
                    p=pos
                    fill=float(open_[j])
                    records.append(dict(
                      entry_ns=p["entry_ns"],exit_ns=t*1_000_000_000,
                      entry_utc=pd.Timestamp(p["entry_ns"],unit="ns",tz="UTC").isoformat(),
                      exit_utc=pd.Timestamp(t,unit="s",tz="UTC").isoformat(),
                      direction="LONG" if p["side"]==1 else "SHORT",
                      entry_price=p["entry"],exit_price=fill,
                      gross_points=(fill-p["entry"])*p["side"],
                      exit_reason="supertrend_flip_close",
                      holding_minutes=(t*1_000_000_000-p["entry_ns"])/60_000_000_000,
                      initial_sl=p["initial"],initial_atr14=p["atr14"]))
                    pos=None;closed_at_boundary=True
            if pos is None and not closed_at_boundary and (long[i] or short[i]):
                side=1 if long[i] else -1
                entry=float(open_[j])
                assert np.isfinite(atr14[i])
                dist=h.round_ticks(atr14[i]*h.SL_ATR_MULT)*h.TICK
                activation=(max(h.TICK,h.round_ticks(entry*h.TRAIL_ACTIVATION/80000)*h.TICK)
                            if scaled else h.TRAIL_ACTIVATION)
                trailing=(max(h.TICK,h.round_ticks(entry*h.TRAIL_DISTANCE/80000)*h.TICK)
                          if scaled else h.TRAIL_DISTANCE)
                pos=dict(entry=entry,entry_ns=t*1_000_000_000,side=side,
                         initial=entry-side*dist,atr14=float(atr14[i]),
                         activation_points=activation,distance_points=trailing,
                         trail=None,best=entry)

        if pos is None:continue
        # Consistent monotonic path rule, but independently for each 1m bar.
        o=float(open_[j]);hi=float(high_[j]);lo=float(low_[j]);cl=float(close_[j])
        path=(o,hi,lo,cl) if abs(o-hi)<abs(o-lo) else (o,lo,hi,cl)
        for k in range(1,4):
            fill,pos["trail"],pos["best"],reason=h.segment_exit(
                path[k-1],path[k],pos["entry"],pos["side"],
                pos["initial"],pos["trail"],pos["best"],
                pos["activation_points"],pos["distance_points"])
            if fill is not None:
                p=pos
                exit_ns=(t+60)*1_000_000_000 # conservative 1m close time
                records.append(dict(
                   entry_ns=p["entry_ns"],exit_ns=exit_ns,
                   entry_utc=pd.Timestamp(p["entry_ns"],unit="ns",tz="UTC").isoformat(),
                   exit_utc=pd.Timestamp(exit_ns,unit="ns",tz="UTC").isoformat(),
                   direction="LONG" if p["side"]==1 else "SHORT",
                   entry_price=p["entry"],exit_price=float(fill),
                   gross_points=(float(fill)-p["entry"])*p["side"],
                   exit_reason=reason,
                   holding_minutes=(exit_ns-p["entry_ns"])/60_000_000_000,
                   initial_sl=p["initial"],initial_atr14=p["atr14"]))
                pos=None
                break
    trades=pd.DataFrame(records)
    assert len(trades)
    assert not trades.duplicated(["entry_ns","direction"]).any()
    assert trades.exit_ns.is_monotonic_increasing
    assert (trades.holding_minutes>0).all()
    return trades

def main():
    b,qual=h.source()
    m=minutes()
    direct,atr14,long,short=h.features(b)
    h.OUT.mkdir(parents=True,exist_ok=True)
    outputs={}
    for name,scaled in [("fixed_100_50",False),("pct_scaled",True)]:
        trades=replay_m1(b,m,direct,atr14,long,short,scaled=scaled)
        d=h.costs(trades,h.SCREENSHOT_SCALP_MIN)
        bad=h.costs(trades,h.SCREENSHOT_SCALP_MIN,slippage_points=0.5)
        rows={}
        for label,df in [("zero_slippage",d),("0p5_point_each_side",bad)]:
            monthly=h.month_results(df)
            rows[label]=h.metrics(df,monthly)
            monthly.to_csv(h.OUT/f"monthly_1minute_execution_{name}_{label}.csv",index=False)
        d.to_csv(h.OUT/f"trades_1minute_execution_{name}.csv.gz",index=False,compression="gzip")
        outputs[name]=rows
    result={"status":"completed_1m_intrabar_sensitivity_not_tv_parity",
            "data_source":qual,"execution_resolution":"one_minute_OHLC",
            "signal_timeframe":"one_hour_closed",
            "fee_window_minutes":27,
            "one_contract_eth":h.QTY_ETH,
            "cases":outputs,
            "limitations":[
             "1-minute market candles permit more realistic stop ordering but still lack tick/order-book fills.",
             "1h screenshot trading view chart stop-monitoring differs from 1m intrabar model; comparison is a sensitivity, not exact strategy parity.",
             "1-minute exit time uses end of minute, at most one minute after approximate touch.",
             "No mark-price liquidation, funding, order-book spread, execution latency, isolated margin or leverage simulation.",
             "The 27m ETH Scalper Offer eligibility is hypothetical pending exchange entitlement verification."]}
    (h.OUT/"intrabar_1m_validation.json").write_text(json.dumps(result,indent=2)+"\n")
    with (h.OUT/"INTRABAR_VALIDATION.md").open("w") as f:
        f.write("# ETHUSD 1-minute intrabar cross-check of 1-hour EMA/ST signals\n\n")
        f.write("| ETH trailing setup | Slippage case | Trades | Net USD / 0.01 ETH contract | PF | Positive months | Eligible exits |\n")
        f.write("|---|---|---:|---:|---:|---:|---:|\n")
        for label,cases in outputs.items():
            for scenario,v in cases.items():
                f.write(f"| {label} | {scenario} | {v['trades']} | {v['net_profit_usd']:+.4f} | {v['profit_factor']} | {v['profitable_months']}/22 | {v['scalp_eligible']} |\n")
        f.write("\nThis is a 1-minute stop-monitoring sensitivity, **not** the exact 1-hour stop-monitoring screenshot. Offer assumed active, funding/spread omitted.\n")
    print("ETH_1MIN_SENSITIVITY "+json.dumps(outputs,separators=(",",":"),default=str),flush=True)

if __name__=="__main__":
    main()
