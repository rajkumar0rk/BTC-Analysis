#!/usr/bin/env python3
"""BTCUSD and ETHUSD 1H EMA20/Supertrend: ONLY trailing 100/50 -> 1/0.1.

Independent historical 1-minute OHLC stop replay of exactly the existing
1H EMA20/ST entry conditions. Every scored market minute comes from SHA256
verified 22-month Delta India BTCUSD/ETHUSD archives. The 1-hour entry
signals and ATR14 x2 stops are computed using existing research indicators.

The current 100x isolated $10-per-trade model, $100 account, no compounding,
2x ATR14 stop, 27-minute offered-fee eligibility sensitivity, 0.05% taker
each side, GST 18%, synthetic liquidation and 1 BTC / 0.20 ETH preliq buffer
are unchanged between OLD/NEW in THIS controlled comparison.

Important: simulated 1m OHLC barrier paths are NOT tick-by-tick fills or
Delta mark-price/portfolio-margin history, do not guarantee live results.
BTC trailing 0.1 is below assumed BTC tick 0.5 -> execution min 0.5.
"""
from __future__ import annotations
import hashlib,json,math,sys
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
import backtest_tv_ema_st_1h_27min_20261120 as btc
import backtest_eth_ema_st_1h_27min_20261120 as eth

OUT=Path("analysis/ema_st_1h_trailing_1_0p1_20261120")
START_CASH=100.
MARGIN=10.
LEV=100
MAINT=0.0025
FEE=.0005
GST=.18
SCALPER_MIN=27
MONTHS=btc.MONTHS
TICK={"BTC":0.5,"ETH":0.05}
CONTRACT={"BTC":0.001,"ETH":0.01}
PRELIQ_BUFFER={"BTC":1.,"ETH":0.20}

def read_minutes(module):
    manifest=json.loads((module.ROOT/"manifest.json").read_text())
    names=set(module.MONTHS)
    parts=[p for p in manifest["partitions"] if p["file"].replace(".csv.gz","") in names]
    assert len(parts)==22,(module.ROOT,len(parts))
    data=[]
    for p in parts:
        file=module.ROOT/p["file"]
        assert hashlib.sha256(file.read_bytes()).hexdigest()==p["sha256_gzip"],str(file)
        assert p["missing_minutes"]==0,str(file)
        x=pd.read_csv(file,compression="gzip",usecols=["time","open","high","low","close"])
        assert len(x)==p["observed_candles"],str(file)
        data.append(x)
    x=pd.concat(data,ignore_index=True)
    t=x.time.to_numpy(np.int64)
    assert np.all(np.diff(t)==60),"Missing minute data or timestamp duplicates"
    return x,manifest["source"]

def liquidation(entry,side):
    # Constant estimated maintenance 0.25%, not Delta mark or portfolio margin.
    return (entry*(1-1/LEV)/(1-MAINT) if side==1
            else entry*(1+1/LEV)/(1+MAINT))

def round_tick(x,tick):
    return max(tick,math.floor(x/tick+0.5)*tick)

def trail(asset,entry,variant):
    if variant=="new":
        return round_tick(1.,TICK[asset]),round_tick(.1,TICK[asset])
    if asset=="BTC":return 100.,50.
    return round_tick(entry*100/80000,TICK[asset]),round_tick(entry*50/80000,TICK[asset])

def walk(pos,open_,hi,lo,cl):
    # TradingView inferred OHLC ordering, but on the *minute* rather than 1H.
    path=(open_,hi,lo,cl) if abs(open_-hi)<abs(open_-lo) else (open_,lo,hi,cl)
    side=pos["side"]
    for a,z in zip(path[:-1],path[1:]):
        stop=pos["stop"]
        liq=pos["liq"]
        if (side==1 and a<=liq) or (side==-1 and a>=liq):
            return float(a),"liquidation"
        if (side==1 and a<=stop) or (side==-1 and a>=stop):
            return float(a),"stop_gap"
        favorable=(z>a if side==1 else z<a)
        if favorable:
            pos["best"]=max(pos["best"],z) if side==1 else min(pos["best"],z)
            if (pos["best"]-pos["entry"])*side >= pos["activation"]-1e-9:
                candidate=pos["best"]-side*pos["distance"]
                pos["stop"]=max(pos["stop"],candidate) if side==1 else min(pos["stop"],candidate)
                pos["trail_active"]=True
        else:
            # First barrier encountered on adverse segment, with synthetic liquidation.
            stop=pos["stop"]
            if side==1:
                first=max(stop,liq)
                if z<=first:
                    return float(first),"liquidation" if liq>=stop else ("trailing_stop" if pos["trail_active"] else "atr_or_preliq_stop")
            else:
                first=min(stop,liq)
                if z>=first:
                    return float(first),"liquidation" if liq<=stop else ("trailing_stop" if pos["trail_active"] else "atr_or_preliq_stop")
    return None,None

def replay(asset,minute,bar,direction,atr,long,short,variant,offer):
    src=minute
    times=src.time.to_numpy(np.int64)
    opens=src.open.to_numpy(float);highs=src.high.to_numpy(float)
    lows=src.low.to_numpy(float);closes=src.close.to_numpy(float)
    bar_ids=np.array(bar.index.as_unit("s").asi8,dtype=np.int64)
    index_lookup={int(ts):i for i,ts in enumerate(bar_ids)}
    tick=TICK[asset];contract=CONTRACT[asset]
    wallet=START_CASH
    peak=wallet
    dd=0.
    pos=None
    events=[]
    eligible=0
    entries_reached=0
    skipped_wallet=0
    skipped_lots=0
    modeled_liquidations=0
    for j in range(len(times)):
        t=int(times[j])
        closed_this_minute=False
        # A 1H signal is known only after candle close; execute at next minute OPEN.
        i=index_lookup.get(t)
        if i is not None:
            if pos is not None and i>0:
                flip=(pos["side"]==1 and direction[i]==1 and direction[i-1]==-1) or (
                      pos["side"]==-1 and direction[i]==-1 and direction[i-1]==1)
                if flip:
                    fill=float(opens[j])
                    reason="supertrend_flip"
                    closed_this_minute=True
                else:fill=None;reason=None
            else:fill=None;reason=None
            if fill is not None:
                realized,record=close(pos,fill,t,reason,wallet,offer)
                wallet=max(0.,wallet+realized)
                events.append(record)
                pos=None
                peak=max(peak,wallet);dd=max(dd,(peak-wallet)/peak*100)
        # 1H bars use label='right': bar[i] closes at timestamp t, so it is
        # the most recently COMPLETED candle at the next 1m open t.
        if pos is None and not closed_this_minute and i is not None and i>=1:
            signal_i=i
            if long[signal_i] or short[signal_i]:
                entries_reached+=1
                side=1 if long[signal_i] else -1
                entry=float(opens[j])
                n=math.floor(MARGIN*LEV/(entry*contract)+1e-10)
                if n<1:skipped_lots+=1
                else:
                    qty=n*contract
                    notional=entry*qty
                    reserved=notional/LEV
                    fee=notional*FEE*(1+GST)
                    if wallet+1e-9 <reserved+fee:
                        skipped_wallet+=1
                    else:
                        atrstop=entry-side*round_tick(2*float(atr[signal_i]),tick)
                        liq=liquidation(entry,side)
                        preliq=liq+PRELIQ_BUFFER[asset]*side
                        # a usable pre-liquidation stop must be strictly protective.
                        if (side==1 and liq<preliq<entry) or (side==-1 and liq>preliq>entry):
                            initial=max(atrstop,preliq) if side==1 else min(atrstop,preliq)
                        else:initial=atrstop
                        act,dist=trail(asset,entry,variant)
                        pos=dict(side=side,entry=entry,qty=qty,n=n,
                                 margin=reserved,entry_fee=fee,entry_time=t,
                                 initial=initial,stop=initial,liq=liq,trail_active=False,
                                 best=entry,activation=act,distance=dist)
                        wallet-=fee # pay entry fee now (not after close)
        if pos is not None:
            fill,reason=walk(pos,opens[j],highs[j],lows[j],closes[j])
            if fill is not None:
                realized,record=close(pos,fill,t+60,reason,wallet,offer)
                wallet=max(0.,wallet+realized)
                events.append(record)
                if reason=="liquidation":modeled_liquidations+=1
                if record["assumed_exit_fee_waiver"]:eligible+=1
                pos=None
                peak=max(peak,wallet);dd=max(dd,(peak-wallet)/peak*100)

    results=pd.DataFrame(events)
    if not results.empty:
        results["month_utc"]=pd.to_datetime(results.exit_epoch,unit="s",utc=True).dt.strftime("%Y-%m")
    mon=[]
    for month in MONTHS:
        z=results[results.month_utc==month] if not results.empty else results
        pnl=float(z.net_usd.sum()) if len(z) else 0.
        mon.append(dict(month=month,net_usd=round(pnl,4),trades=int(len(z)),
                        wins=int((z.net_usd>0).sum()) if len(z) else 0,
                        losses=int((z.net_usd<0).sum()) if len(z) else 0))
    sums=sum(x["net_usd"] for x in mon)
    winners=float(results.loc[results.net_usd>0,"net_usd"].sum()) if len(results) else 0.
    losers=-float(results.loc[results.net_usd<0,"net_usd"].sum()) if len(results) else 0.
    stats=dict(asset=asset,trailing_variant=variant,offer_assumed=offer,
        balance_initial_usd=START_CASH,balance_final_usd=round(wallet,4),
        realized_net_usd=round(wallet-START_CASH,4),
        completed_trades=int(len(results)),
        win_rate_pct=round(100*float((results.net_usd>0).mean()),2) if len(results) else None,
        profit_factor=round(winners/losers,4) if losers>0 else None,
        profitable_months=sum(x["net_usd"]>0 for x in mon),
        losing_months=sum(x["net_usd"]<0 for x in mon),
        flat_months=sum(abs(x["net_usd"])<0.00005 for x in mon),
        total_fees_gst=round(float(results.fees_gst_usd.sum()),4) if len(results) else 0.,
        liquidations=modeled_liquidations,assumed_scalper_eligible=eligible,
        max_closed_drawdown_pct=round(dd,2),
        signals_reached_while_flat=entries_reached,
        rejected_due_to_wallet=skipped_wallet,
        rejected_no_contract=skipped_lots,
        has_open_trade_at_end=pos is not None,
        monthly=mon)
    # The entry fee was deducted immediately. Open positions can make cash
    # differ from sum closed trade net; report and assert only if flat.
    if pos is None:
        assert abs(sum(float(x["net_usd"]) for x in events)-(wallet-START_CASH))<0.0001
    return stats,results

def close(pos,price,t,reason,wallet,offer):
    side=pos["side"];qty=pos["qty"]
    gross=(price-pos["entry"])*side*qty
    held=max(0.,(t-pos["entry_time"])/60)
    eligible=offer and held<=SCALPER_MIN and reason!="liquidation"
    exitfee=0. if eligible or reason=="liquidation" else price*qty*FEE*(1+GST)
    liqfee=price*qty*.0005*(1+GST) if reason=="liquidation" else 0.
    realized=(max(-pos["margin"],gross-liqfee) if reason=="liquidation"
              else gross-exitfee)
    # entry fee was subtracted from wallet at position open.
    net=realized-pos["entry_fee"]
    record=dict(entry_epoch=pos["entry_time"],exit_epoch=t,side="LONG" if side==1 else "SHORT",
         entry=pos["entry"],exit=price,contracts=pos["n"],
         gross_usd=gross,net_usd=net,fees_gst_usd=pos["entry_fee"]+exitfee+liqfee,
         entry_fee_included=True,assumed_exit_fee_waiver=eligible,
         trailing_activation=pos["activation"],trailing_distance=pos["distance"],
         exit_reason=reason,held_minutes=round(held,1))
    return realized,record

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    output={}
    for asset,module in (("BTC",btc),("ETH",eth)):
        print("LOADING_VERIFIED_1H_AND_1M",asset,flush=True)
        bars,quality=module.source()
        raw,source=read_minutes(module)
        direction,atr,long,short=module.features(bars)
        assert len(bars)==len(raw)//60
        outcomes={}
        for variant in ("old","new"):
            for offer in (False,True):
                label=f"{variant}_{'assumed_offer' if offer else 'no_offer'}"
                print("RUN",asset,label,flush=True)
                stat,trades=replay(asset,raw,bars,direction,atr,long,short,variant,offer)
                outcomes[label]=stat
                trades.to_csv(OUT/f"{asset.lower()}_{label}_trades.csv.gz",index=False,compression="gzip")
                pd.DataFrame(stat["monthly"]).to_csv(OUT/f"{asset.lower()}_{label}_monthly.csv",index=False)
                print("RESULT",json.dumps({k:v for k,v in stat.items() if k!="monthly"},sort_keys=True),flush=True)
        output[asset]=dict(source=quality,raw_source=source,results=outcomes)
        del raw,bars
    doc=dict(status="completed",scored_completed_months=MONTHS,
       description="Only trailing activation 100->1 price point and distance 50->0.1 price point; compare old with new using identical 1minute execution, isolated 100x and costs.",
       strategy=dict(timeframe="1h",ema=20,supertrend_atr=10,supertrend_factor=3,
         entry="confirmed supertrend and EMA20 touch/pullback close",
         initial_stop="2x ATR(14)",start_wallet=100,per_trade_margin_budget=10,
         leverage=100,margin_mode="isolated research proxy",
         pre_liquidation_buffer={"BTC":1.0,"ETH":0.20},
         taker_fee_rate_each_side=FEE,gst_rate=GST,scalper_assumed_minutes=27,
         master_volume_volatility_filter="off",
         model="1h closed entry signal, 1m historical OHLC barrier replay",
         trailing_old="BTC literal 100/50, ETH BTC-equivalent percent-scaled 100/50",
         trailing_new_input="activation 1, distance 0.1 literal price points",
         trailing_new_executable={"BTC":{"activation":1.,"distance":0.5},
                                  "ETH":{"activation":1.,"distance":0.1}},
         price_tick_assumed=TICK),
       assets=output,
       caveats=[
         "BTC 0.1 point is below assumed 0.5 venue tick, so distance 0.5 is used in executable simulation. A hypothetical 0.1 BTC stop is not submitted.",
         "1m OHLC cannot establish exact order fill, spread, intraminute path, stop latency or mark-price liquidation.",
         "Fee model 0.05% taker per side and 18% GST; alternative scenario assumes 27m Scalper offer on every eligible historical trade; entitlement not verified.",
         "Synthetic isolated 100x liquidation/preliq proxy is not current shared Delta Demo Portfolio Margin.",
         "No funding, spread, latency, slippage or options premium are modeled.",
         "Trade entry on next 1m OPEN after fully closed 1h signal; matching historical data spans Jan 2025-Oct 2026; excludes Nov partial month.",
         "Changing trailing by such tiny amounts produces near-zero gross winners relative to fees; this is not evidence of an investable strategy.",
         "All changes research branch only; running VPS bots have not been modified."
       ])
    (OUT/"summary.json").write_text(json.dumps(doc,indent=2,default=str)+"\n")
    summary=["# BTC + ETH 1H EMA20/Supertrend — 1 / 0.1 trailing sensitivity",
     "All other strategy settings matched in old versus new, isolated 100x test model.",
     "Source: verified raw Delta India one-minute files Jan 2025-Oct 2026.",
     "",
     "| Asset | Trailing | Fee policy | Net USD | PF | Trades | Positive months | Liquidations |",
     "|---|---|---|---:|---:|---:|---:|---:|"]
    for asset,val in output.items():
      for label,row in val["results"].items():
        summary.append(f'| {asset} | {label.split("_")[0]} | {"assumed offer" if row["offer_assumed"] else "no offer"} | {row["realized_net_usd"]:+.2f} | {row["profit_factor"]} | {row["completed_trades"]} | {row["profitable_months"]}/22 | {row["liquidations"]} |')
    summary.extend(["","See summary.json and per-asset trade/monthly CSVs.", "", "## Limitations"]+[f"- {x}" for x in doc["caveats"]])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(summary)+"\n")
    print("ALL_REPLAY_RESULTS_JSON",json.dumps({a:{k:{key:v for key,v in st.items() if key!="monthly"} for k,st in x["results"].items()} for a,x in output.items()},sort_keys=True),flush=True)
if __name__=="__main__":main()
