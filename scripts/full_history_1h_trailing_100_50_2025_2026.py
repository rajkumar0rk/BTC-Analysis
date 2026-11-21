#!/usr/bin/env python3
"""Full-history BTCUSD/ETHUSD 1H EMA20+Supertrend + trailing stop analysis.

Uses archived *Delta India production* 1m traded OHLCV and independent 1m
MARK candles, January 2025 onward. This is not a Delta DEMO replay.
No synthetic intrabar low->high path is asserted as fact. Three models:
  minute_close: native MARK OHLC hits prior installed stop; trail is adjusted
                from completed MARK 1m CLOSE for use in the next minute.
  O-H-L-C: counterfactual minute mark open/high/low/close path, with immediate
           stop updates at the high or low observation.
  O-L-H-C: counterfactual minute mark open/low/high/close path.
Order of extreme observations in the counterfactual models is UNKNOWN.

Entries: next hourly boundary after complete prior 1H signal, TRADED minute
OPEN (the production Demo bot checks its public ticker ~10s after close, so
entry is a proxy). 0.2% stale-close filter. Actual last-to-book fill may differ.
Stops: 2xATR14 initial, BTC activation $100 / trail $50; ETH scaled by
entry/80000 to exchange tick. Stop triggered by MARK, exit modeled at the
same minute TRADED CLOSE -- an explicit delayed execution assumption, not
a verified taker fill. Gap exits use TRADED OPEN. Intra-minute book/slippage
unavailable. 0.05% taker each side + 18% GST; no scalper waiver and NO
funding, so this is NET-OF-ASSUMED-FEES, EX FUNDING and spread.
Wallet: independent $100 starting equity per instrument, maximum ~$1000
notional from $10 *100x and 1% PM risk-shock sizing assumption; budget is
NOT independent isolated margin. No true PM liquidation calculation.
No > wallet trades once current realized balance falls below $11.
History starts Jan 1 2025 UTC: allow 72h signal warmup before entries.
No calendar-day forced exits. No strategy changes or merges into main.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from replay_btc_ema_st_screenshot import indicators
from backtest_demo_1h_pm_20261120_ist import pm_size, round_stop

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"analysis"/"full_history_1h_trailing_100_50"
OUTPUT.mkdir(parents=True,exist_ok=True)
ASSETS=("BTC","ETH")
START="2025-01"
FULL_END="2026-10"
TAKER_RATE=0.0005
GST=0.18
EQUITY_START=100.0
BUDGET=10.0
MIN_WALLET=BUDGET+1
ENTRY_DIVERGENCE=.002
HOUR=3600

def monthly_files(asset,kind):
    base=ROOT/"data"/"delta_india"/(asset+"USD")
    path=(base/"1m") if kind=="traded" else (base/"institutional"/"history"/"mark_1m")
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path

def read_asset(asset):
    traded=monthly_files(asset,"traded")
    mark=monthly_files(asset,"mark")
    manifest=json.loads((traded/"manifest.json").read_text())
    assert manifest["symbol"]==asset+"USD" and "india.delta.exchange" in manifest["source"]
    entries=[x for x in manifest["partitions"] if START<=x["file"][:7]<="2026-11"]
    assert len(entries)==23,f"{asset}: expected 22 full months and partial Nov 2026, got {len(entries)}"
    assert [e["file"][:7] for e in entries]==[str(p) for p in pd.period_range("2025-01","2026-11",freq="M")]
    candle_parts=[];mark_parts=[]
    for record in entries:
        name=record["file"];a=traded/name;b=mark/name
        if not a.exists() or not b.exists():
            raise FileNotFoundError(str(a if not a.exists() else b))
        sha=hashlib.sha256(a.read_bytes()).hexdigest()
        if sha!=record["sha256_gzip"]:
            raise RuntimeError(f"{asset} traded data SHA256 mismatch {name}")
        if record["missing_minutes"] or record["observed_candles"]!=record["expected_minutes"]:
            # Nov partial expected_minutes in manifest should equal archived slice, not full month.
            raise RuntimeError(f"{asset} traded source incomplete {name}")
        traded_part=pd.read_csv(a,compression="gzip",usecols=["time","open","high","low","close","volume"])
        mark_part=pd.read_csv(b,compression="gzip",usecols=["time","open","high","low","close"])
        if len(traded_part)!=record["observed_candles"]:
            raise RuntimeError(f"{asset}: traded partition row count disagrees with manifest")
        for part in (traded_part,mark_part):
            for c in part.columns:
                part[c]=pd.to_numeric(part[c],errors="raise")
            if part.isna().any().any():raise RuntimeError(f"{asset} invalid OHLC {name}")
            if (part[["open","high","low","close"]].min(axis=1)<=0).any():
                raise RuntimeError(f"{asset}: nonpositive price {name}")
            if (part["high"]<part[["open","close","low"]].max(axis=1)).any() or (part["low"]>part[["open","close","high"]].min(axis=1)).any():
                raise RuntimeError(f"{asset}: inconsistent OHLC {name}")
            ts=part.time.to_numpy(dtype=np.int64)
            if len(ts)>1 and not np.all(np.diff(ts)==60):
                raise RuntimeError(f"{asset}: invalid intra-file spacing {name}")
        candle_parts.append(traded_part)
        mark_parts.append(mark_part)
    traded_df=pd.concat(candle_parts,ignore_index=True)
    mark_df=pd.concat(mark_parts,ignore_index=True)
    t=traded_df.time.to_numpy(dtype=np.int64)
    m=mark_df.time.to_numpy(dtype=np.int64)
    # No aligning/filling across price gaps, no unseen 1m OHLC synthesis.
    # Nov-2026 partial partition differs by asset/feed, trim ONLY the
    # unmatched final Nov minutes; Jan2025-Oct2026 must still be complete.
    if len(t)!=len(m):
        shared=min(len(t),len(m))
        assert t[shared-1]>=int(pd.Timestamp("2026-11-01",tz="UTC").timestamp())
        assert np.array_equal(t[:shared],m[:shared]),f"{asset} source mismatch before partial tail"
        traded_df=traded_df.iloc[:shared].copy()
        mark_df=mark_df.iloc[:shared].copy()
        t=t[:shared];m=m[:shared]
    assert np.array_equal(t,m),f"{asset} mark/traded timestamp mismatch"
    assert np.all(np.diff(t)==60),f"{asset}: historical 1m data gaps"
    assert t[0]==int(pd.Timestamp("2025-01-01",tz="UTC").timestamp())
    assert t[-1]>=int(pd.Timestamp("2026-11-17 23:59",tz="UTC").timestamp())
    assert t[-1]<int(pd.Timestamp("2026-11-22 00:00",tz="UTC").timestamp())
    idx=pd.to_datetime(t,unit="s",utc=True)
    traded_df.index=idx
    mark_df.index=idx
    return traded_df,mark_df,{
       "source":manifest["source"],
       "mark_source":"Delta India historical MARK:xxxxUSD 1m REST archive",
       "traded_rows":len(t),"mark_rows":len(m),
       "start_utc":str(idx[0]),"end_utc":str(idx[-1]),
       "mark_time_alignment_verified":True,
       "traded_sha256_verified":True,
       "all_minute_intervals_60s":True,
    }

def signal_map(df,asset):
    h=df.resample("1h",origin="epoch",label="left",closed="left").agg({
      "open":"first","high":"max","low":"min",
      "close":"last","volume":"sum","time":"count"
    })
    h=h[h.time==60].drop(columns=["time"])
    f=indicators(h)
    indices=np.asarray(f.index.view("int64")//1_000_000_000,dtype="int64")
    tick=.5 if asset=="BTC" else .05
    ema=f.ema.to_numpy(dtype=float);atr=f.atr14.to_numpy(dtype=float)
    d=f.dir.to_numpy(dtype=int)
    op=f.open.to_numpy(dtype=float);hi=f.high.to_numpy(dtype=float)
    lo=f.low.to_numpy(dtype=float);cl=f.close.to_numpy(dtype=float)
    events={}
    signals=0
    flips=0
    for i in range(1,len(f)):
        at=int(indices[i]+HOUR)
        if not (np.isfinite(ema[i]) and np.isfinite(atr[i])):
            continue
        flip=(d[i]!=d[i-1])
        if flip:flips+=1
        side=0
        if i>=72:
            if d[i]==d[i-1]==-1 and lo[i]<=ema[i] and cl[i]>ema[i]:
                side=1
            elif d[i]==d[i-1]==1 and hi[i]>=ema[i] and cl[i]<ema[i]:
                side=-1
        if side:signals+=1
        if flip or side:
            events[at]={
              "side":side,"flip":int(d[i]) if flip else 0,
              "stopdist":max(tick,round(2*float(atr[i])/tick)*tick),
              "close":float(cl[i]),"signal_utc":str(f.index[i])
            }
    return events,{"completed_1h_bars":len(f),"hourly_entry_signals":signals,
                   "hourly_st_flips":flips,"warmup_bars":72}

def mark_reaches_stop(lo,hi,stop,side):
    return lo<=stop if side==1 else hi>=stop

def trailing_rule(mark_price,entry,side,best,active,stop,activation,distance,tick):
    if (mark_price-entry)*side>=activation:active=True
    if active:
        best=max(best,mark_price) if side==1 else min(best,mark_price)
        candidate=round_stop(best-side*distance,tick,side)
        stop=max(stop,candidate) if side==1 else min(stop,candidate)
    return best,active,stop

def round_activation(asset,entry,tick):
    if asset=="BTC":return 100.,50.
    a=max(tick,math.floor((entry*100/80000)/tick+.5)*tick)
    d=max(tick,math.floor((entry*50/80000)/tick+.5)*tick)
    return a,d

def run_sim(asset,df,mark,events,kind):
    assert kind in ("minute_close","OHLC","OLHC")
    times=df.time.to_numpy(dtype=np.int64)
    trade_o=df.open.to_numpy(dtype=float)
    trade_c=df.close.to_numpy(dtype=float)
    mark_o=mark.open.to_numpy(dtype=float)
    mark_h=mark.high.to_numpy(dtype=float)
    mark_l=mark.low.to_numpy(dtype=float)
    mark_c=mark.close.to_numpy(dtype=float)
    tick=.5 if asset=="BTC" else .05
    value=.001 if asset=="BTC" else .01
    equity=EQUITY_START
    peak=EQUITY_START;max_dd=0.0
    trades=[];skips=Counter()
    active=None;signals_seen=0
    for i,ts in enumerate(times):
        evt=events.get(int(ts))
        entry_candidate=evt is not None and evt["side"]!=0
        if entry_candidate:signals_seen+=1
        initial_active=active is not None
        do_exit=False
        exit_reason=None
        px=None
        if active is not None:
            s=active["side"];stop=active["stop"]
            if (s==1 and mark_o[i]<=stop) or (s==-1 and mark_o[i]>=stop):
                do_exit=True;exit_reason="mark_stop_gap";px=trade_o[i]
            elif evt and evt["flip"]==s:
                do_exit=True;exit_reason="opposite_supertrend_flip";px=trade_o[i]
        if active is None and entry_candidate:
            entry=float(trade_o[i])
            s=evt["side"]
            if equity<MIN_WALLET:skips["wallet_below_11_usd"]+=1
            elif abs(entry-evt["close"])/evt["close"]>ENTRY_DIVERGENCE:
                skips["entry_deviation_gt_0.2pct"]+=1
            else:
                qtyc=pm_size(entry,value)
                if qtyc<=0:skips["less_than_one_contract"]+=1
                else:
                    # 2x ATR14 stop rounded with the bot's rounding semantics.
                    distance_atr=max(tick,round(2*evt["stopdist"]/tick)*tick)
                    st=round_stop(entry-s*distance_atr,tick,s)
                    if (s==1 and mark_o[i]<=st) or (s==-1 and mark_o[i]>=st):
                        skips["mark_already_crossed_at_entry"]+=1
                    else:
                        act,trail=round_activation(asset,entry,tick)
                        active={
                          "side":s,"entry":entry,"time":int(ts),"quantity":qtyc*value,
                          "contracts":qtyc,"initial_stop":st,"stop":st,
                          "best":entry,"trailing_active":False,
                          "activation":act,"distance":trail,
                          "stop_moves":0,"signal_bar":evt["signal_utc"]
                        }
        elif entry_candidate and initial_active:
            skips["existing_position"]+=1
        if active is None:continue
        s=active["side"]
        if not do_exit:
            if kind=="minute_close":
                if mark_reaches_stop(mark_l[i],mark_h[i],active["stop"],s):
                    do_exit=True;exit_reason="native_mark_stop";px=trade_c[i]
                else:
                    b,a,st=trailing_rule(mark_c[i],active["entry"],s,
                        active["best"],active["trailing_active"],active["stop"],
                        active["activation"],active["distance"],tick)
                    if abs(st-active["stop"])>tick/2:active["stop_moves"]+=1
                    active["best"]=b;active["trailing_active"]=a;active["stop"]=st
            else:
                if kind=="OHLC":points=(mark_o[i],mark_h[i],mark_l[i],mark_c[i])
                else:points=(mark_o[i],mark_l[i],mark_h[i],mark_c[i])
                previous=None
                for v in points:
                    stop=active["stop"]
                    # "Gap" at first mark open is already handled above.
                    if previous is not None and (
                       (s==1 and previous>stop and v<=stop) or
                       (s==-1 and previous<stop and v>=stop)
                    ):
                        do_exit=True;exit_reason="native_mark_trailing_path";px=trade_c[i]
                        break
                    b,a,st=trailing_rule(float(v),active["entry"],s,
                        active["best"],active["trailing_active"],stop,
                        active["activation"],active["distance"],tick)
                    if abs(st-stop)>tick/2:active["stop_moves"]+=1
                    active["best"]=b;active["trailing_active"]=a;active["stop"]=st
                    previous=v
        if not do_exit:continue
        if px is None:raise AssertionError("exit missing traded fill proxy")
        # On a SELL short, exiting by buying costs a regular taker fee;
        # same logic covers long side. Both fee legs are always modeled.
        qty=active["quantity"];entry=active["entry"]
        gross=(px-entry)*s*qty
        entry_fee=entry*qty*TAKER_RATE
        exit_fee=px*qty*TAKER_RATE
        gst=(entry_fee+exit_fee)*GST
        net=gross-entry_fee-exit_fee-gst
        equity+=net
        peak=max(peak,equity)
        if peak>0:max_dd=max(max_dd,(peak-equity)/peak*100)
        month=pd.Timestamp(int(ts),unit="s",tz="UTC").strftime("%Y-%m")
        trades.append({
          "asset":asset,"entry_utc":datetime.fromtimestamp(active["time"],timezone.utc).isoformat(),
          "exit_utc":datetime.fromtimestamp(int(ts),timezone.utc).isoformat(),
          "exit_month_utc":month,"side":"long" if s==1 else "short",
          "entry_price":entry,"exit_price_proxy":float(px),
          "gross_points":round((px-entry)*s,6),
          "qty":qty,"contracts":active["contracts"],
          "gross_usd":round(gross,6),"entry_fee_usd":round(entry_fee,6),
          "exit_fee_usd":round(exit_fee,6),"gst_usd":round(gst,6),
          "net_usd":round(net,6),"equity_after":round(equity,6),
          "initial_stop":active["initial_stop"],"final_stop":active["stop"],
          "activation":active["activation"],"trail":active["distance"],
          "trailing_active_at_exit":bool(active["trailing_active"]),
          "stop_moves":active["stop_moves"],
          "holding_minutes":round((ts-active["time"])/60,1),
          "exit_reason":exit_reason,
          "signal_bar_utc":active["signal_bar"],
        })
        active=None
    # Does not invent final closing order at archive end.
    extra=None
    if active:
        extra={
          "entry_utc":datetime.fromtimestamp(active["time"],timezone.utc).isoformat(),
          "entry_price":active["entry"],"side":"long" if active["side"]==1 else "short",
          "unrealized_gross_at_final_traded_close":round(
             (trade_c[-1]-active["entry"])*active["side"]*active["quantity"],4),
          "final_stop":active["stop"],
        }
    dftr=pd.DataFrame(trades)
    if dftr.empty:
        dftr=pd.DataFrame(columns=[
        "asset","entry_utc","exit_utc","exit_month_utc","side","net_usd","gross_usd"])
    if len(dftr):
        net=dftr.net_usd.to_numpy()
        gains=float(net[net>0].sum());losses=float(-net[net<0].sum())
        win=int((net>0).sum());loss=int((net<0).sum())
    else:
        gains=losses=0.;win=loss=0
    stats={
        "asset":asset,"method":kind,
        "starting_wallet_usd":EQUITY_START,
        "realized_wallet_end_usd":round(equity,4),
        "net_profit_usd":round(equity-EQUITY_START,4),
        "net_return_pct_on_start_wallet":round((equity/EQUITY_START-1)*100,4),
        "closed_trades":len(dftr),"wins":win,"losses":loss,
        "win_rate_pct":round(100*win/max(1,len(dftr)),3),
        "profit_factor_net":round(gains/losses,4) if losses>0 else None,
        "worst_closed_drawdown_pct":round(max_dd,4),
        "total_gross_usd":round(float(dftr.gross_usd.sum()),4) if len(dftr) else 0,
        "total_fees_gst_usd":round(float(dftr[["entry_fee_usd","exit_fee_usd","gst_usd"]].sum().sum()),4) if len(dftr) else 0,
        "hourly_candidates_seen":signals_seen,
        "skips":dict(skips),"still_open_at_end":extra,
        "actual_pm_liquidation_not_simulated":True,
        "actual_funding_not_included":True,
    }
    by_month={}
    for p in pd.period_range("2025-01","2026-11",freq="M"):
        month=str(p)
        part=dftr.loc[dftr["exit_month_utc"]==month] if len(dftr) else dftr
        mnet=float(part.net_usd.sum()) if len(part) else 0.0
        pos=float(part.loc[part.net_usd>0,"net_usd"].sum()) if len(part) else 0.0
        neg=-float(part.loc[part.net_usd<0,"net_usd"].sum()) if len(part) else 0.0
        by_month[month]={
          "status":"complete_UTC_month" if month<=FULL_END else "partial_UTC_month",
          "closed_trades":len(part),
          "wins":int((part.net_usd>0).sum()) if len(part) else 0,
          "losses":int((part.net_usd<0).sum()) if len(part) else 0,
          "net_usd":round(mnet,4),
          "profit_factor_net":round(pos/neg,4) if neg>0 else None,
          "no_losses":neg==0 and len(part)>0,
        }
    stats["monthly"]=by_month
    return dftr,stats

def test():
    assert mark_reaches_stop(90,102,95,1)
    assert not mark_reaches_stop(96,102,95,1)
    assert mark_reaches_stop(90,102,101,-1)
    assert not mark_reaches_stop(90,100,101,-1)
    assert trailing_rule(59900,60000,-1,60000,False,61000,100,50,.5)[2]==59950
    assert round_activation("BTC",60000,.5)==(100,50)
    assert round_activation("ETH",1740,.05)==(2.2,1.1)
    assert pm_size(62000,.001)==16

def main():
    test()
    output={"source":"Historical Delta Exchange India production BTC/ETH perpetual 1m traded and mark candles",
            "date_system":"UTC calendar month (complete months 2025-01 to 2026-10); ledger ISO UTC",
            "last_month":"2026-11 partial only",
            "assumptions":{
               "strategy":"1H EMA20 + Supertrend10,3 stable-direction EMA touch/close, no ATR/volume filter",
               "initial_stop":"2x ATR14 from entry",
               "trailing":"BTC 100/50 absolute USD; ETH proportional to entry/80000, rounded to exchange tick",
               "entry":"Next 1H boundary 1m traded open (live bot checks ~10s after bar close), >0.2% divergence rejected",
               "fill":"Stop trigger on 1m MARK, traded minute CLOSE used as delayed market execution price proxy; gap/flip at minute traded OPEN",
               "margin":"$100 account per asset, $10 sizing target and 100x notional ceiling; PM shock 1pct unverified",
               "costs":"0.05% taker each side +18% GST; no scalper waiver; excludes funding, spread, slippage beyond delayed fill",
               "liquidation":"No true account PM liquidation model; accounts below $11 cannot initiate new positions",
               "intraminute":"minute_close causal baseline, alternate hypothetical OHLC and OLHC price paths to show price-order uncertainty",
               "signal_warmup":"First 72 complete hourly candles excluded",
               "warnings":[
                 "Historic 1m OHLC cannot reveal order of high and low or true 3s mark polling",
                 "1m traded CLOSE is not the actual execution price for an earlier stop trigger",
                 "Funding/actual portfolio collateral/liquidation/slippage/latency are not verified",
                 "This is production historical data, NOT DEMO testnet history",
               ]
            },"datasets":{},"scenarios":{}}
    for asset in ASSETS:
        traded,mark,provenance=read_asset(asset)
        events,smeta=signal_map(traded,asset)
        provenance.update(smeta)
        output["datasets"][asset]=provenance
        for mode in ("minute_close","OHLC","OLHC"):
            print("RUN",asset,mode,flush=True)
            trades,stats=run_sim(asset,traded,mark,events,mode)
            name=f"{asset.lower()}_{mode.lower()}"
            trades.to_csv(OUTPUT/f"{name}_trades.csv.gz",index=False,compression="gzip")
            output["scenarios"][name]=stats
            # Format-friendly monthly CSV for each independent instrument.
            pd.DataFrame([{"month_utc":k,**v} for k,v in stats["monthly"].items()]).to_csv(
                OUTPUT/f"{name}_monthly.csv",index=False)
            concise={k:v for k,v in stats.items() if k!="monthly"}
            print("HISTORY_RESULT",name,json.dumps(concise,sort_keys=True),flush=True)
        del traded,mark
    # Side-by-side baseline table.
    rows=[]
    for m in pd.period_range("2025-01","2026-11",freq="M"):
        k=str(m)
        row={"month_utc":k,"complete_month":k<=FULL_END}
        for asset in ASSETS:
            a=output["scenarios"][f"{asset.lower()}_minute_close"]["monthly"][k]
            row[asset+"_net_usd"]=a["net_usd"]
            row[asset+"_trades"]=a["closed_trades"]
            row[asset+"_PF"]=a["profit_factor_net"]
        rows.append(row)
    pd.DataFrame(rows).to_csv(OUTPUT/"monthly_baseline_comparison.csv",index=False)
    (OUTPUT/"summary.json").write_text(json.dumps(output,indent=2)+"\n")
    print("FULL_HISTORY_SUCCESS",OUTPUT,flush=True)

if __name__=="__main__":
    main()
