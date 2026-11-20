#!/usr/bin/env python3
"""Controlled 1H-only ATR stop, trailing activation and trailing exit sensitivity.

Prior 1M model: analysis/ema_st_1h_trailing_1_0p1_20261120/summary.json.
Use the EXACT same 1H signal arrays, 100x $10 sizing, $100 wallet, tick
rounding, 2xATR14 initial stop, pre-liquidation proxy, 0.05% taker+18% GST
as that earlier model. ONLY the stop/trailing evaluation frequency is changed
to complete 1H OHLC bars. Historical candle paths are *not* real tick paths.
This is NOT TradingView tick-level, exchange mark/liquidation, or fee parity.
"""
from __future__ import annotations
import json,math
from pathlib import Path
import numpy as np
import pandas as pd
import backtest_tv_ema_st_1h_27min_20261120 as btc
import backtest_eth_ema_st_1h_27min_20261120 as eth
import backtest_ema_st_1h_trail_1_0p1_20261120 as prior

OUT=Path("analysis/ema_st_1h_all_stops_hourly_1_0p1_20261120")
OLD=Path("analysis/ema_st_1h_trailing_1_0p1_20261120/summary.json")

def walk_with_path(pos,o,h,l,c,mode):
    """Prior walk exactly for inferred path, optionally test path ambiguity."""
    if mode=="inferred":
        return prior.walk(pos,o,h,l,c)
    side=pos["side"]
    adverse=l if side==1 else h
    favorable=h if side==1 else l
    if mode=="adverse_first": path=(o,adverse,favorable,c)
    elif mode=="favorable_first": path=(o,favorable,adverse,c)
    else:raise ValueError(mode)
    for a,z in zip(path[:-1],path[1:]):
        stop=pos["stop"];liq=pos["liq"]
        if (side==1 and a<=liq) or (side==-1 and a>=liq):
            return float(a),"liquidation"
        if (side==1 and a<=stop) or (side==-1 and a>=stop):
            return float(a),"stop_gap"
        favorable_seg=z>a if side==1 else z<a
        if favorable_seg:
            pos["best"]=max(pos["best"],z) if side==1 else min(pos["best"],z)
            if (pos["best"]-pos["entry"])*side >=pos["activation"]-1e-9:
                cand=pos["best"]-side*pos["distance"]
                pos["stop"]=max(pos["stop"],cand) if side==1 else min(pos["stop"],cand)
                pos["trail_active"]=True
        else:
            stop=pos["stop"]
            if side==1:
                first=max(stop,liq)
                if z<=first:
                    return float(first),"liquidation" if liq>=stop else (
                        "trailing_stop" if pos["trail_active"] else "atr_or_preliq_stop")
            else:
                first=min(stop,liq)
                if z>=first:
                    return float(first),"liquidation" if liq<=stop else (
                        "trailing_stop" if pos["trail_active"] else "atr_or_preliq_stop")
    return None,None

def walk_close_only(pos,o,h,l,c):
    """Only completed 1H CLOSE can activate or cross a protective stop.

    Real isolated liquidation may still occur intrabar. This is a *risk
    sensitivity*, not a broker emulator or safe live stop design.
    Uses next evaluated closing price for stop exits, never hour high/low
    to infer trailing profits. Does not activate and stop on same close.
    """
    side=pos["side"]
    liq=pos["liq"]
    # Even a candle-close-only software stop cannot defer exchange liquidation.
    if (side==1 and l<=liq) or (side==-1 and h>=liq):
        return float(liq),"liquidation"
    stop=pos["stop"] # stop from prior completed bar, not future candle extrema
    if (side==1 and c<=stop) or (side==-1 and c>=stop):
        return float(c),("trailing_stop_close" if pos["trail_active"]
                         else "atr_or_preliq_stop_close")
    gain=(c-pos["entry"])*side
    if gain>=pos["activation"]-1e-9:
        pos["trail_active"]=True
    if pos["trail_active"]:
        pos["best"]=max(pos["best"],c) if side==1 else min(pos["best"],c)
        proposed=pos["best"]-side*pos["distance"]
        pos["stop"]=max(pos["stop"],proposed) if side==1 else min(pos["stop"],proposed)
    return None,None

def replay_hourly(asset,b,direction,atr,long,short,mode="inferred",offer=False):
    op=b.open.to_numpy(float);hi=b.high.to_numpy(float)
    lo=b.low.to_numpy(float);cl=b.close.to_numpy(float)
    ts=np.array(b.index.as_unit("s").asi8,dtype=np.int64)
    assert np.all(np.diff(ts)==3600), "Hourly data discontinuity"
    tick=prior.TICK[asset];contract=prior.CONTRACT[asset]
    wallet=prior.START_CASH;peak=wallet;dd=0.
    entries=0;skipped_wallet=0;skipped_qty=0;pos=None
    realized=[];liquidations=0;assumed_offer_count=0
    for i in range(len(b)):
        start=int(ts[i])-3600;end=int(ts[i])
        closed_at_open=False
        # A Supertrend flip on the prior COMPLETED 1H candle can exit at
        # this candle's OPEN. No current bar lookahead is permitted.
        if pos is not None and i>=2:
            flipped=((pos["side"]==1 and direction[i-1]==1 and direction[i-2]==-1)
                     or (pos["side"]==-1 and direction[i-1]==-1 and direction[i-2]==1))
            if flipped:
                realized_delta,record=prior.close(pos,float(op[i]),start,
                                                   "supertrend_flip",wallet,offer)
                wallet=max(0.,wallet+realized_delta)
                record["bar_path"]=mode;record["stop_resolution"]="1h"
                realized.append(record)
                pos=None;closed_at_open=True
                peak=max(peak,wallet);dd=max(dd,(peak-wallet)/peak*100)
        # Only the previous hour's COMPLETED signal is tradeable here.
        if pos is None and not closed_at_open and i>=1:
            signal_i=i-1
            if long[signal_i] or short[signal_i]:
                entries+=1
                side=1 if long[signal_i] else -1
                entry=float(op[i])
                n=math.floor(prior.MARGIN*prior.LEV/(entry*contract)+1e-10)
                if n<1:skipped_qty+=1
                else:
                    qty=n*contract;notional=qty*entry
                    margin=notional/prior.LEV
                    fee=notional*prior.FEE*(1+prior.GST)
                    if wallet+1e-9<margin+fee:
                        skipped_wallet+=1
                    else:
                        dist=prior.round_tick(2*float(atr[signal_i]),tick)
                        initial_atr=entry-side*dist
                        liq=prior.liquidation(entry,side)
                        preliq=liq+prior.PRELIQ_BUFFER[asset]*side
                        if (side==1 and liq<preliq<entry) or (
                            side==-1 and liq>preliq>entry):
                            initial=max(initial_atr,preliq) if side==1 else min(initial_atr,preliq)
                        else:initial=initial_atr
                        activation,distance=prior.trail(asset,entry,"new")
                        pos=dict(side=side,entry=entry,qty=qty,n=n,
                            margin=margin,entry_fee=fee,entry_time=start,
                            initial=initial,stop=initial,liq=liq,trail_active=False,
                            best=entry,activation=activation,distance=distance)
                        wallet-=fee
        if pos is not None:
            # One OHLC stop/trailing evaluation for this entire hour.
            if mode=="close_only":
                fill,reason=walk_close_only(pos,float(op[i]),float(hi[i]),
                                            float(lo[i]),float(cl[i]))
            else:
                fill,reason=walk_with_path(pos,float(op[i]),float(hi[i]),
                                          float(lo[i]),float(cl[i]),mode)
            if fill is not None:
                # At 1H resolution the intrabar exit timestamp is unknowable.
                # Use the hour-END as conservative hold-time upper bound.
                realized_delta,record=prior.close(pos,fill,end,reason,wallet,offer)
                wallet=max(0.,wallet+realized_delta)
                record["bar_path"]=mode;record["stop_resolution"]="1h"
                realized.append(record)
                if reason=="liquidation":liquidations+=1
                if record["assumed_exit_fee_waiver"]:assumed_offer_count+=1
                pos=None;peak=max(peak,wallet)
                dd=max(dd,(peak-wallet)/peak*100)
    tr=pd.DataFrame(realized)
    if len(tr):
        tr["month_utc"]=pd.to_datetime(tr.exit_epoch,unit="s",utc=True).dt.strftime("%Y-%m")
    monthly=[]
    for month in prior.MONTHS:
        z=tr[tr.month_utc==month] if len(tr) else tr
        monthly.append(dict(month=month,net_usd=round(float(z.net_usd.sum()),4)
            if len(z) else 0.,trades=len(z),wins=int((z.net_usd>0).sum()) if len(z) else 0))
    gross_pos=float(tr.loc[tr.net_usd>0,"net_usd"].sum()) if len(tr) else 0.
    gross_neg=-float(tr.loc[tr.net_usd<0,"net_usd"].sum()) if len(tr) else 0.
    stats=dict(
        asset=asset,exit_monitoring="one_hour_OHLC",
        bar_path_model=mode,offer_assumed=offer,
        initial_wallet_usd=prior.START_CASH,
        final_cash_usd=round(wallet,4),
        net_usd=round(wallet-prior.START_CASH,4),
        trade_count=int(len(tr)),
        win_rate_pct=round(100*float((tr.net_usd>0).mean()),2) if len(tr) else None,
        profit_factor=round(gross_pos/gross_neg,4) if gross_neg>0 else None,
        winning_months=sum(x["net_usd"]>0 for x in monthly),
        losing_months=sum(x["net_usd"]<0 for x in monthly),
        flat_months=sum(abs(x["net_usd"])<.00005 for x in monthly),
        total_fees_gst_usd=round(float(tr.fees_gst_usd.sum()),4) if len(tr) else 0.,
        modeled_liquidations=liquidations,assumed_fee_waivers=assumed_offer_count,
        max_closed_drawdown_pct=round(dd,2),
        entry_signals_when_flat=entries,skipped_insufficient_wallet=skipped_wallet,
        skipped_no_contract=skipped_qty,open_at_end=pos is not None,
        monthly=monthly)
    if pos is None:
        assert abs(sum(x["net_usd"] for x in realized)-(wallet-prior.START_CASH))<1e-5, (asset,mode)
    return stats,tr

def test_synthetic_paths():
    # Hourly high and low alone don't identify whether tight profit trailing
    # triggered BEFORE an ATR stop. Test that order matters.
    p=dict(side=1,entry=100.,qty=.01,n=1,margin=10,entry_fee=0,
           entry_time=0,initial=95.,stop=95.,liq=90.,best=100.,
           activation=1.,distance=.1,trail_active=False)
    import copy
    outcome=[]
    for path in ("adverse_first","favorable_first","inferred"):
        pos=copy.deepcopy(p)
        fill,reason=walk_with_path(pos,100.,105.,94.,100.5,path)
        assert fill is not None
        outcome.append((path,fill,reason))
    assert outcome[0][1]!=outcome[1][1],outcome
    # Completed-close trailing cannot activate on high alone, and must
    # never retroactively exit at that high minus 0.1/0.5.
    pos=copy.deepcopy(p)
    price,reason=walk_close_only(pos,100.,105.,96.,100.5)
    assert price is None and not pos["trail_active"]
    price,reason=walk_close_only(pos,100.,105.,96.,101.5)
    assert price is None and pos["trail_active"]
    assert pos["stop"]>=101.4
    price,reason=walk_close_only(pos,101.5,103.,100.,101.3)
    assert reason=="trailing_stop_close" and price==101.3
    return outcome

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assert OLD.exists(),"Previous 1m experiment summary is missing"
    baseline=json.loads(OLD.read_text())
    assert baseline["strategy"]["trailing_new_input"]=="activation 1, distance 0.1 literal price points"
    assert len(baseline["scored_completed_months"])==22
    paths=test_synthetic_paths()
    summary=dict(
        status="completed",dates="2025-01-01 through 2026-10-31 UTC",
        completed_months=prior.MONTHS,
        changed_parameter_only="Stop ATR and trailing activation/trailing stop use 1H OHLC rather than 1M OHLC",
        preserved_settings={
            "signal_interval":"1h closed candle",
            "supertrend_reversal":"1h closed-candle signal, next bar open",
            "ema20_pullback_entry":True,
            "initial_atr_stop":"2 * 1h ATR14",
            "trailing_activation_literal_points":1,
            "trailing_distance_requested_literal_points":0.1,
            "BTC_trailing_distance_executable_points":0.5,
            "ETH_trailing_distance_executable_points":0.1,
            "BTC_tick_assumption":0.5,"ETH_tick_assumption":0.05,
            "starting_balance_usd":100,
            "fixed_margin_usd_per_trade":10,
            "leverage":100,
            "maintenance_proxy":.0025,
            "preliq_buffer":{"BTC":1,"ETH":0.2},
            "fee_each_side":.0005,"gst":.18,
            "funding_model":"excluded",
            "spread_slippage":"excluded",
        },
        hourly_stop_execution={
            "bar_processing":"one full 1H OHLC bar per iteration",
            "fill_model":"OHLC-inferred path, high-first if open closer to high, otherwise low-first; stop fill at modeled barrier",
            "timestamp":"1H bar end when intrabar stop is simulated; actual intrabar time UNKNOWN",
            "uncertainty_tests":"adverse-first and favorable-first extreme ordering, plus true candle-close-only decision",
            "close_only_rule":"Trigger stops and trailing activation only from completed 1H close, with synthetic intrabar liquidation risk preserved",
            "same_hour_trail_possible":True,
            "last_hourly_signal_used":"prior fully completed 1H bar"},
        synthetic_path_test=paths,assets={},
        caveats=[
            "This changes time resolution, not whether prices crossed a stop intrabar. No real 1H candle reveals high-vs-low chronology.",
            "An hourly inferred-path model may be dramatically optimistic versus the prior one-minute replay. Treat intrabar-path cases as sensitivity bounds, not confirmed fills.",
            "Close-only exits are filled at the 1H close optimistically and may be later than a broker fill; exchange liquidation can still happen intrabar.",
            "Underlying hourly OHLC cannot establish Delta mark-price liquidation, spreads, stop order latency or tick-size price fills.",
            "Conservative no-offer results use all fees; assumed 27-minute Scalper discount almost never qualifies on 1H bar-end times and does not prove eligibility.",
            "Synthetic 100x isolated margin/preliq proxy differs from actual shared Demo Portfolio Margin; entry fee is charged before trade close.",
            "BTC requested 0.1 trailing distance is below 0.5 assumed tick; modeled as 0.5. No strategy bots or live VPS orders were changed.",
        ])
    for asset,mod in (("BTC",btc),("ETH",eth)):
        print("LOADING_VERIFIED_HOURLY",asset,flush=True)
        bars,source=mod.source()
        assert len(bars)==16056
        direction,atr,long,short=mod.features(bars)
        scenarios={}
        for mode in ("inferred","adverse_first","favorable_first","close_only"):
            print("TEST_1H",asset,mode,flush=True)
            stats,trades=replay_hourly(asset,bars,direction,atr,long,short,mode,offer=False)
            scenarios[mode]=stats
            trades.to_csv(OUT/f"{asset.lower()}_1h_{mode}_trades.csv.gz",compression="gzip",index=False)
            pd.DataFrame(stats["monthly"]).to_csv(OUT/f"{asset.lower()}_1h_{mode}_monthly.csv",index=False)
            print("RESULT_1H",json.dumps({k:v for k,v in stats.items() if k!="monthly"},sort_keys=True),flush=True)
        previous=baseline["assets"][asset]["results"]["new_no_offer"]
        summary["assets"][asset]=dict(source=source,original_1m_no_offer={
            k:v for k,v in previous.items() if k!="monthly"},
            hourly_results=scenarios,
            difference_1h_minus_1m_usd=round(scenarios["inferred"]["net_usd"]-previous["realized_net_usd"],4))
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    header=["# 1H-only ATR and trailing monitoring backtest (1 / 0.1)",
        "",
        "**Entry and Supertrend reverse remain 1H.** Prior stop/trailing model is 1M; new is 1H OHLC. Fee assumptions and sizing unchanged.",
        "**Historical period:** January 2025–October 2026 (22 complete months). Verified Delta India archive.",
        "",
        "| Asset | Stop/trailing evaluation | Net USD | PF | Trades | Positive months |",
        "|---|---|---:|---:|---:|---:|"]
    for asset,p in summary["assets"].items():
        baseline_result=p["original_1m_no_offer"]
        header.append(f'| {asset} | Previous 1M | {baseline_result["realized_net_usd"]:+.2f} | {baseline_result["profit_factor"]} | {baseline_result["completed_trades"]} | {baseline_result["profitable_months"]}/22 |')
        for mode,r in p["hourly_results"].items():
            header.append(f'| {asset} | New 1H {mode} | {r["net_usd"]:+.2f} | {r["profit_factor"]} | {r["trade_count"]} | {r["winning_months"]}/22 |')
    header+=["","## Caveats"]+[f"- {x}" for x in summary["caveats"]]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(header)+"\n")
    print("ALL_1H_RESULTS",json.dumps({k:{mode:{
        x:y for x,y in v.items() if x!="monthly"}
        for mode,v in z["hourly_results"].items()} for k,z in summary["assets"].items()},sort_keys=True),flush=True)
if __name__=="__main__":main()
