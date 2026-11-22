#!/usr/bin/env python3
"""BTCUSD historical 1m OHLC path replay: initial SL grid for frozen EMA20 Touch/Reclaim setups.

Touch: 1H ST(10,3), EMA20 Touch, signal volume ratio [1.25,2.5],
       0.14% one-rung profit lock.
Reclaim: 1H ST(10,3), EMA20 Reclaim, signal volume >=1.25,
         2%-3%-5% step profit locks.
First valid fill per ST cycle; existing entry rules preserved.

Original 1m price-path simulator is reused. A candidate initial stop is
active immediately after the entry fill; profit locks may only tighten it.
All results are exploratory, not guaranteed executable exchange fills.
"""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import numpy as np
import pandas as pd

SRC=Path("scripts/backtest_st_ema20_large_percent_locks.py")
OUT=Path("analysis/st_ema20_initial_sl_grid_20261122")
PATHS=("open_high_low_close","open_low_high_close")
MONTHS=list(pd.period_range("2025-01","2026-10",freq="M").astype(str))
STOPS=[("OFF","off",0.0)]
STOPS += [(f"{v}pts","pts",float(v)) for v in (100,200,300,500,800,1000,1500,2000)]
STOPS += [(f"{v:g}%","pct",float(v)) for v in (0.25,0.5,1.0,2.0,3.0)]
EXPECTED={("touch","open_high_low_close"):(50,0.725036),
          ("touch","open_low_high_close"):(50,0.723046),
          ("reclaim","open_high_low_close"):(62,11.498422),
          ("reclaim","open_low_high_close"):(62,11.722550)}

def eng():
    spec=importlib.util.spec_from_file_location("base_ema_st_engine",SRC)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def prepare_entries(engine,minutes,hourly,mode):
    entries=engine.entry_candidates(minutes,hourly,mode)
    selected=[]
    for e in entries:
        signal=pd.Timestamp(e["signal"])
        v=float(hourly.loc[signal,"volume_ratio"])
        if np.isfinite(v) and v>=1.25 and (mode!="touch" or v<=2.5):
            selected.append(e)
    return selected

def run(engine, m, h, entries, mode, path, stop_id, kind, stop_value):
    ladder=(0.14,) if mode=="touch" else (2.0,3.0,5.0)
    op=m.open.to_numpy(float); hi=m.high.to_numpy(float)
    lo=m.low.to_numpy(float); close=m.close.to_numpy(float)
    hside=h.side.to_numpy(); times=m.index; total=len(op)
    outputs=[]
    for ev in entries:
        side=int(ev["side"]); j0=int(ev["entry_j"])
        entry=float(ev["entry"]); mid_entry=entry-side*engine.SLIP
        distance=(stop_value if kind=="pts" else
                  entry*stop_value/100. if kind=="pct" else None)
        stop=(entry-side*distance) if distance is not None else None
        cross=set(); max_adverse=0.; max_favorable=0.
        flip_hour=np.flatnonzero(hside[j0//60:]!=side)
        flip_j=(int(j0//60+flip_hour[0])+1)*60 if len(flip_hour)>0 else total
        flip_j=min(flip_j,total)
        exj=None; exmid=None; reason=None
        for j in range(j0,flip_j):
            nodes=engine.bar_path(op[j],hi[j],lo[j],close[j],path)
            part=engine.simulate_bar(nodes,side,entry,mid_entry,stop,ladder,j==j0)
            stop=part["stop"];cross.update(part["rungs"])
            max_adverse=max(max_adverse,float(part["adverse"]))
            max_favorable=max(max_favorable,float(part["favorable"]))
            if part["exit_mid"] is not None:
                exj=j;exmid=float(part["exit_mid"])
                reason=("initial_stop" if side*(exmid-entry)<0 else "profit_lock")
                break
        if exj is None and flip_j<total:
            exj=flip_j;exmid=float(op[flip_j]);reason="supertrend_flip"
        if exj is None:
            outputs.append(dict(strategy=mode,stop=stop_id,path=path,
                entry_utc=str(times[j0]),exit_utc="",side=side,
                net_usd=np.nan,gross_usd=np.nan,fees_usd=np.nan,
                exit_reason="still_open",max_adverse_points=max_adverse))
            continue
        fill=exmid-side*engine.SLIP
        gross=engine.QTY*side*(fill-entry)
        fees=engine.QTY*engine.FEE*(entry+fill)
        net=gross-fees
        outputs.append(dict(strategy=mode,stop=stop_id,path=path,
           side=side,entry_utc=str(times[j0]),exit_utc=str(times[exj]),
           signal_utc=ev["signal"],entry_price=round(entry,2),
           exit_price=round(fill,2),hold_min=exj-j0,
           gross_usd=round(gross,6),fees_usd=round(fees,6),
           net_usd=round(net,6),exit_reason=reason,
           max_adverse_points=round(max_adverse,2),
           max_favorable_points=round(max_favorable,2),
           highest_rung=max(cross) if cross else 0.))
    return pd.DataFrame(outputs)

def summarize(t,mode,stop_id,path):
    done=t[t.exit_reason!="still_open"].copy()
    done["month_ist"]=pd.to_datetime(done.exit_utc,utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    done=done[done.month_ist.isin(MONTHS)]
    mon=done.groupby("month_ist").net_usd.sum().reindex(MONTHS,fill_value=0.)
    monthly=pd.DataFrame(dict(strategy=mode,stop=stop_id,path=path,
           month_ist=MONTHS,net_usd=mon.round(6).values))
    monthly["status"]=np.where(monthly.net_usd>1e-8,"Profit",
                         np.where(monthly.net_usd< -1e-8,"Loss","Flat"))
    monthly["trades"]=[int((done.month_ist==mo).sum()) for mo in MONTHS]
    yearly={}
    for yr in ("2025","2026"):
        y=monthly[monthly.month_ist.str.startswith(yr)]
        yearly[yr]=dict(profitable=int((y.net_usd>1e-8).sum()),
                        losing=int((y.net_usd< -1e-8).sum()),
                        flat=int((y.net_usd.abs()<=1e-8).sum()),
                        net_usd=round(float(y.net_usd.sum()),5))
    vals=done.net_usd.to_numpy(float)
    equity=100+np.cumsum(vals)
    peaks=np.maximum.accumulate(np.r_[100.,equity])[1:]
    dd_pct=float(np.max(100*(peaks-equity)/peaks)) if len(equity) else 0.
    report=dict(strategy=mode,stop=stop_id,path=path,
       trades=int(len(done)),wins=int((done.net_usd>0).sum()),
       losses=int((done.net_usd<0).sum()),
       win_rate_pct=round(float((done.net_usd>0).mean()*100),3) if len(done) else 0.,
       total_net_usd=round(float(done.net_usd.sum()),6),
       total_gross_usd=round(float(done.gross_usd.sum()),6),
       total_fees_usd=round(float(done.fees_usd.sum()),6),
       profitable_months=int((mon>1e-8).sum()),
       losing_months=int((mon< -1e-8).sum()),
       flat_months=int((mon.abs()<=1e-8).sum()),
       max_realized_dd_pct=round(dd_pct,3),
       stopped_trades=int((done.exit_reason=="initial_stop").sum()),
       profit_lock_exits=int((done.exit_reason=="profit_lock").sum()),
       st_flip_exits=int((done.exit_reason=="supertrend_flip").sum()),
       open_trades=int((t.exit_reason=="still_open").sum()),
       profitable_2025=yearly["2025"]["profitable"],
       profitable_2026=yearly["2026"]["profitable"],
       losing_2025=yearly["2025"]["losing"],
       losing_2026=yearly["2026"]["losing"],
       net_2025=yearly["2025"]["net_usd"],
       net_2026=yearly["2026"]["net_usd"])
    return report,monthly

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    engine=eng()
    engine.smoke_test()
    m,h,nfiles=engine.load()
    h=engine.features(h)
    h["volume_ratio"]=(h.volume/h.volume.shift(1).rolling(20,min_periods=20).mean().replace(0,np.nan))
    configs={"touch":prepare_entries(engine,m,h,"touch"),
             "reclaim":prepare_entries(engine,m,h,"reclaim")}
    assert len(configs["touch"])==52, ("touch_count",len(configs["touch"]))
    assert len(configs["reclaim"])==62, ("reclaim_count",len(configs["reclaim"]))
    summaries=[];allmonthly=[];alltrades=[]
    for mode,entries in configs.items():
        for path in PATHS:
            for stop_id,kind,stop_value in STOPS:
                t=run(engine,m,h,entries,mode,path,stop_id,kind,stop_value)
                score,monthly=summarize(t,mode,stop_id,path)
                summaries.append(score);allmonthly.append(monthly);alltrades.append(t)
                if kind=="off":
                    count,expected=EXPECTED[(mode,path)]
                    assert score["trades"]==count,(mode,path,score)
                    assert abs(score["total_net_usd"]-expected)<0.003,(mode,path,score)
                print(mode,path,stop_id,score["profitable_months"],score["losing_months"],score["total_net_usd"],"stopped",score["stopped_trades"],flush=True)
    sf=pd.DataFrame(summaries)
    mf=pd.concat(allmonthly,ignore_index=True)
    tf=pd.concat(alltrades,ignore_index=True)
    sf.to_csv(OUT/"summary.csv",index=False)
    mf.to_csv(OUT/"monthly.csv",index=False)
    tf.to_csv(OUT/"trades.csv",index=False)
    paired=[]
    for (mode,stop),q in sf.groupby(["strategy","stop"],sort=False):
        assert len(q)==2
        paired.append(dict(strategy=mode,stop=stop,
             months_worst=int(q.profitable_months.min()),months_best=int(q.profitable_months.max()),
             net_worst=float(q.total_net_usd.min()),net_best=float(q.total_net_usd.max()),
             net2025_worst=float(q.net_2025.min()),net2026_worst=float(q.net_2026.min()),
             dd_worst=float(q.max_realized_dd_pct.max()),
             stopped_min=int(q.stopped_trades.min()),stopped_max=int(q.stopped_trades.max()),
             positive_in_both_years=bool((q.net_2025.gt(0)&q.net_2026.gt(0)).all())))
    pp=pd.DataFrame(paired).sort_values(["months_worst","net_worst"],ascending=False)
    pp.to_csv(OUT/"paired_comparison.csv",index=False)
    meta=dict(source="Delta Exchange India BTCUSD 1m",
          source_files=nfiles,minute_bars=len(m),first_utc=str(m.index.min()),last_utc=str(m.index.max()),
          entry_count={k:len(v) for k,v in configs.items()},timeframe="1h signal + 1m stop/lock replay",
          fee_side_with_gst=engine.FEE,slippage_points_each_side=engine.SLIP,quantity_btc=engine.QTY,
          validated_no_stop_baselines=EXPECTED, stop_specs=[dict(label=a,unit=b,value=c) for a,b,c in STOPS],
          caveats=["Intraminute OHLC high/low order unresolved: both plausible paths modeled",
                   "No order book, fill latency, stop amendment latency, funding, liquidation or margin",
                   "Realized drawdown only; floating equity risk may be much greater",
                   "Historical configurations selected after observing full 2025-26 dataset",
                   "Initial stop starts at fill-relative price; locks tighten stop only when price reaches next rung",
                   "One entry filled per ST cycle, as in preserved source engine",
                   "No forward validation, no guarantee of monthly profits"])
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("# BTCUSD EMA20 Touch and Reclaim with initial stop-loss\n\n"+
       "The first row of each strategy is the frozen no-initial-SL control.\n"+
       "22 completed IST months, Jan 2025 through Oct 2026.\n"+
       "All returns in USD, 0.001 BTC per trade, fees/GST/5-point per-leg slippage included.\n\n"+
       pp.to_markdown(index=False)+"\n\n"+
       "Actual live stops can gap/slip. OHLC paths and 2025-26 selection are exploratory.\n")
    print("SUCCESS results in",OUT,flush=True)

if __name__=="__main__":
    main()
