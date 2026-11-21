#!/usr/bin/env python3
"""Causal full-history optimization of the EXTRA 'Trailing Stop Points' control.

Exact control semantics copied from user's TradingView Pine:
  Enable Trailing Stop: ON
  Enable Trailing Stop Points: ON
  Enable Trailing Distance (Fixed Points): OFF
  Activation Points: parameter A
  Trailing Stop Points: parameter S
  1H signal: EMA20 touch/reclaim in continuing Supertrend10,3 (both sides).
  Initial 2xATR14 stop; opposite 1H Supertrend flip exits.

LONG managed stop = max(prior stop, highest observed 1m HIGH since entry - S);
SHORT managed stop = min(prior stop, lowest observed 1m LOW since entry + S).
Only adjust after full 1m candle completes; effective from NEXT 1m minute.
Even after activation the new trailing point stop can be below entry. No
profit-lock assumption. The stop never loosens. This honors the additional
point-based control instead of confusing it with the original fixed trail.
ETH values follow historical Demo strategy convention: BTC point settings
normalized by entry/80000 and rounded to instrument tick; not raw ETH $500.

Use public Delta India production 1m trade OHLCV and MARK 1m OHLC, Jan 2025
through Nov17 2026. Optimize only 22 COMPLETE UTC months Jan 2025-Oct 2026.
November results are partial and excluded from ranking.

Two trigger/observation lenses:
  mark: mirror Delta native MARK stop trigger; 1m MARK highs/lows determine
        custom stop. Traded 1m CLOSE as fill-price proxy for in-minute trigger.
  traded: mirror Pine traded-price stop trigger/observation; 1m TRADED highs/
        lows determine custom stop. Same-minute traded CLOSE is fill proxy.
Neither reproduces precise stop placement or order execution. The 1m candle's
completed high/low update is effective NEXT minute, never retroactive.
At each new 1H signal, entry is 1m traded OPEN (actual bot checks ~10s later).
Reject >0.2% close-to-entry drift. Stop follows bidirectional mark/trade
ranges only if that stop was already active before the current minute's range.

Cross-validation:
  Select 2025 in-sample best net candidates, inspect Jan-Oct 2026 independent
  holdout and all 22 month profile; report separate full-period top rows.
  Fixed-notional reference does NOT imply a $100 wallet could fund 22 months.
  Also run wallet-guarded $100 replay for chosen candidates.

Fees are explicit: 0.05% taker both sides + 18% GST, no Scalper waiver.
Funding, genuine exchange fills, order book, leverage liquidation and margin
account risks are not modeled. ALL gains/losses are hypothetical.
No changes to actual trading bot, main branch, or user's production data.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit

from full_history_1h_trailing_100_50_2025_2026 import read_asset, signal_map

OUT=Path(__file__).resolve().parents[1]/"analysis"/"full_history_trailing_stop_points_grid_20261121"
OUT.mkdir(parents=True,exist_ok=True)
ACTIVATIONS=(50,100,200,300,500,800,1000)
STOPS=(50,100,200,300,500,750,1000,1500,2000,2500,3000,4000,6000,8000)
MONTHS=[str(x) for x in pd.period_range("2025-01","2026-11",freq="M")]
TRAIN_END=12
TEST_END=22
YEAR_BEGIN=2025
# 22 complete calendar months Jan 2025-Oct 2026; Nov-2026 is partial.
FEE=.0005
GST=.18
START_WALLET=100.
MIN_WALLET=11.
BUDGET=10.
MAX_LEVERAGED_NOTIONAL=1000.
MAX_SLIP=.002

@njit(cache=True)
def stop_round(raw,tick,side):
    if side==1:
        return math.ceil((raw-1e-9)/tick)*tick
    return math.floor((raw+1e-9)/tick)*tick

@njit(cache=True)
def point_scale(btcpoints,entry,tick,eth):
    if eth==0:
        return float(btcpoints)
    raw=(entry*btcpoints/80000.0)/tick
    return max(tick,math.floor(raw+.5+1e-9)*tick)

@njit(cache=True)
def compute(time_s,traded_o,traded_h,traded_l,traded_c,
            mark_o,mark_h,mark_l,mark_c,
            signal,flip,signalclose,stopdist,
            activation_points,stop_points,asset_eth,mode,guard_wallet):
    """Rows: [entry_time,exit_time,side,entry,exit,qty,gross,fees_gst,net,
       init_stop,final_stop,activation,trail_stop,edit_count,exit_code]."""
    n=len(time_s)
    tick=.05 if asset_eth else .5
    val=.01 if asset_eth else .001
    max_trades=10000
    trades=np.zeros((max_trades,15),dtype=np.float64)
    ntrades=0
    # skip counts: existing signal, deviation, minwallet, size, initial-stop-cross
    skips=np.zeros(5,dtype=np.int64)
    wallet=START_WALLET
    active=0
    side=0;entry=0.;quantity=0.;entry_t=0.
    best=0.;stop=0.;initial_stop=0.;activated=0
    activation=0.;trailingstop=0.;edits=0
    # O(1) per minute; 1m high/low observations known only at bar close.
    for i in range(n):
        s=signal[i]
        fl=flip[i]
        open_t=traded_o[i];close_t=traded_c[i]
        if mode==0:
            o=mark_o[i];h=mark_h[i];lo=mark_l[i]
        else:
            o=open_t;h=traded_h[i];lo=traded_l[i]
        exit_code=0;exit_price=0.
        was_active=active==1
        if was_active:
            # Previously installed stop active from minute open.
            if (side==1 and o<=stop) or (side==-1 and o>=stop):
                exit_code=1;exit_price=open_t
            elif fl==side:
                exit_code=2;exit_price=open_t
        if active==0 and s!=0:
            if guard_wallet and wallet<MIN_WALLET:
                skips[2]+=1
            elif abs(open_t-signalclose[i])/signalclose[i]>MAX_SLIP:
                skips[1]+=1
            else:
                c=math.floor(MAX_LEVERAGED_NOTIONAL/(open_t*val)+1e-10)
                if c<1:
                    skips[3]+=1
                else:
                    proposed=stop_round(open_t-s*stopdist[i],tick,s)
                    # Initial native stop only valid if mark/traded source
                    # has not already crossed its price at decision.
                    if (s==1 and o<=proposed) or (s==-1 and o>=proposed):
                        skips[4]+=1
                    else:
                        active=1;side=s;entry=open_t;quantity=c*val
                        entry_t=time_s[i];best=entry;activated=0
                        stop=proposed;initial_stop=stop
                        activation=point_scale(activation_points,entry,tick,asset_eth)
                        trailingstop=point_scale(stop_points,entry,tick,asset_eth)
                        edits=0
        elif was_active and s!=0:
            skips[0]+=1

        if active==0:
            continue
        if exit_code==0:
            # Stop already installed before observed candle. Do NOT use this
            # candle's HIGH/LOW to tighten then fill the stop retroactively.
            if (side==1 and lo<=stop) or (side==-1 and h>=stop):
                exit_code=3;exit_price=close_t
            else:
                # Activation and new stop are computed AFTER this 1m bar closes;
                # active only for next 1m candle, not earlier this minute.
                if side==1:
                    best=max(best,h)
                else:
                    best=min(best,lo)
                if side*(best-entry)>=activation:
                    activated=1
                if activated==1:
                    candidate=stop_round(best-side*trailingstop,tick,side)
                    tighter=max(stop,candidate) if side==1 else min(stop,candidate)
                    if abs(tighter-stop)>tick/2:
                        stop=tighter;edits+=1
        if exit_code!=0:
            gross=(exit_price-entry)*side*quantity
            fees=(entry+exit_price)*quantity*FEE*(1.+GST)
            net=gross-fees
            wallet+=net
            if ntrades>=max_trades:
                raise ValueError("trade buffer exceeded")
            trades[ntrades,0]=entry_t
            trades[ntrades,1]=time_s[i]
            trades[ntrades,2]=side
            trades[ntrades,3]=entry
            trades[ntrades,4]=exit_price
            trades[ntrades,5]=quantity
            trades[ntrades,6]=gross
            trades[ntrades,7]=fees
            trades[ntrades,8]=net
            trades[ntrades,9]=initial_stop
            trades[ntrades,10]=stop
            trades[ntrades,11]=activation
            trades[ntrades,12]=trailingstop
            trades[ntrades,13]=edits
            trades[ntrades,14]=exit_code
            ntrades+=1
            active=0
    return trades[:ntrades],skips,wallet,active

def prepare(asset):
    trade,mark,info=read_asset(asset)
    events,meta=signal_map(trade,asset)
    ts=trade["time"].to_numpy(dtype=np.int64)
    side=np.zeros(len(ts),dtype=np.int8)
    flip=np.zeros(len(ts),dtype=np.int8)
    signalclose=np.zeros(len(ts),dtype=np.float64)
    stopdist=np.zeros(len(ts),dtype=np.float64)
    first=int(ts[0]);last=int(ts[-1])
    for t,ev in events.items():
        if t<first or t>last:continue
        index=(int(t)-first)//60
        if ts[index]!=t:raise ValueError("event misalignment")
        side[index]=int(ev["side"])
        flip[index]=int(ev["flip"])
        signalclose[index]=float(ev["close"])
        stopdist[index]=float(ev["stopdist"])
    args=[
      ts,
      trade.open.to_numpy(dtype=np.float64),
      trade.high.to_numpy(dtype=np.float64),
      trade.low.to_numpy(dtype=np.float64),
      trade.close.to_numpy(dtype=np.float64),
      mark.open.to_numpy(dtype=np.float64),
      mark.high.to_numpy(dtype=np.float64),
      mark.low.to_numpy(dtype=np.float64),
      mark.close.to_numpy(dtype=np.float64),
      side,flip,signalclose,stopdist
    ]
    return args,{**info,**meta}

def frame_rows(rows):
    if not len(rows):
        return pd.DataFrame(columns=[
            "entry_utc","exit_utc","side","entry_price","exit_price_proxy",
            "position_quantity","gross_usd","fees_gst_usd","net_usd",
            "initial_stop","final_stop","activation_points","trailing_stop_points",
            "stop_edits","exit_reason","month_utc"])
    tr=pd.DataFrame(rows,columns=[
      "entry_s","exit_s","side","entry_price","exit_price_proxy",
      "position_quantity","gross_usd","fees_gst_usd","net_usd",
      "initial_stop","final_stop","activation_points","trailing_stop_points",
      "stop_edits","exit_code"])
    tr["entry_utc"]=pd.to_datetime(tr.entry_s,unit="s",utc=True).astype(str)
    tr["exit_utc"]=pd.to_datetime(tr.exit_s,unit="s",utc=True).astype(str)
    tr["month_utc"]=pd.to_datetime(tr.exit_s,unit="s",utc=True).dt.strftime("%Y-%m")
    tr["side"]=tr.side.map({1.:"long",-1.:"short"})
    tr["exit_reason"]=tr.exit_code.map({1.:"stop_gap",2.:"supertrend_flip",3.:"stop_crossed_in_minute"})
    return tr.drop(columns=["entry_s","exit_s","exit_code"])

def metrics(df,months):
    z=df[df.month_utc.isin(months)]
    net=float(z.net_usd.sum())
    winners=float(z[z.net_usd>0].net_usd.sum())
    losers=-float(z[z.net_usd<0].net_usd.sum())
    cumulative=np.r_[0.,np.cumsum(z.net_usd.to_numpy())]
    dd=float(np.max(np.maximum.accumulate(cumulative)-cumulative))
    count=len(z)
    return {
      "trades":count,"wins":int((z.net_usd>0).sum()),"losses":int((z.net_usd<0).sum()),
      "net_usd":round(net,4),
      "gross_usd":round(float(z.gross_usd.sum()),4),
      "fees_gst_usd":round(float(z.fees_gst_usd.sum()),4),
      "profit_factor":round(winners/losers,4) if losers else None,
      "win_rate_pct":round(int((z.net_usd>0).sum())/count*100,2) if count else None,
      "max_closed_trade_drawdown_usd":round(dd,4),
      "positive_months":sum(float(z[z.month_utc==m].net_usd.sum())>0 for m in months),
      "negative_months":sum(float(z[z.month_utc==m].net_usd.sum())<0 for m in months),
    }

def month_table(df):
    result=[]
    for m in MONTHS:
        z=df[df.month_utc==m]
        gain=float(z[z.net_usd>0].net_usd.sum())
        loss=-float(z[z.net_usd<0].net_usd.sum())
        result.append({"month_utc":m,"complete_month":m<="2026-10",
                       "net_usd":round(float(z.net_usd.sum()),4),"trades":len(z),
                       "wins":int((z.net_usd>0).sum()),"losses":int((z.net_usd<0).sum()),
                       "pf":round(gain/loss,4) if loss else None})
    return result

def run_one(args,asset,mode,activation,stoppoints,wallet_guard=False):
    res,skips,wallet,openpos=compute(
        *args,float(activation),float(stoppoints),1 if asset=="ETH" else 0,
        0 if mode=="mark" else 1,wallet_guard)
    f=frame_rows(res)
    return f,{"asset":asset,"mode":mode,"activation":activation,
           "trailing_stop_points":stoppoints,"fixed_distance_enabled":False,
           "wallet_guard_enabled":wallet_guard,
           "research_wallet_balance_usd":round(float(wallet),4),
           "open_position_at_end":bool(openpos),
           "skips":{"already_open":int(skips[0]),"deviation":int(skips[1]),
                    "wallet_depleted":int(skips[2]),"size":int(skips[3]),
                    "invalid_initial_stop":int(skips[4])},
           "train_2025":metrics(f,MONTHS[:TRAIN_END]),
           "holdout_2026_jan_oct":metrics(f,MONTHS[TRAIN_END:TEST_END]),
           "all_22_months":metrics(f,MONTHS[:TEST_END]),
           "nov_2026_partial":metrics(f,MONTHS[TEST_END:])}

def checks():
    assert stop_round(60000.1,.5,1)==60000.5
    assert stop_round(60000.9,.5,-1)==60000.5
    assert point_scale(500.,60000.,.5,0)==500.
    assert abs(point_scale(500.,1600.,.05,1)-10)<1e-8
    assert abs(point_scale(100.,1600.,.05,1)-2)<1e-8
    # Demonstrate no retroactive stop activation in the source:
    txt=Path(__file__).read_text()
    assert txt.index("if (side==1 and lo<=stop)")<txt.index("best=max(best,h)")

def main():
    checks()
    root={
      "source":"BTC-Analysis archived Delta India PROD trade 1m and MARK 1m",
      "data_window":"2025-01-01 UTC to 2026-11-17 23:59 UTC; 22 complete months 2025-01 through 2026-10",
      "interpretation":"User Pine ENABLE Trailing Stop Points, DISABLE original Fixed Trailing Distance. 1m highest/lowest stop updates effective next minute.",
      "fee_model":"0.05% taker EACH side, GST 18%, no promo; NOT funding/margin/spread actual",
      "risk_caveat":"Fixed-notional $1000 target reference ignores wallet depletion; if results net lower than -$100 it could not be funded with stated $100 start",
      "execution_caveat":"No real intraminute path or actual market fills. 1m low/high can trigger previously installed mark/traded stop, next correction from completed bar only. Exit modeled at same 1m traded close.",
      "trade_entry":"At completed-hour boundary 1m trade OPEN, 0.2% drift gate; not actual 10s later",
      "selection":"2025 train, 2026 Jan-Oct holdout; all22 ranked separately",
      "grid":{"activations":ACTIVATIONS,"trailing_stop_points":STOPS},
      "datasets":{},"ranking":{},"selected":{},"checks":{}
    }
    for asset in ("BTC","ETH"):
        args,info=prepare(asset)
        root["datasets"][asset]=info
        for mode in ("mark","traded"):
            rows=[]
            print("GRID_START",asset,mode,flush=True)
            for a in ACTIVATIONS:
                for st in STOPS:
                    _,summary=run_one(args,asset,mode,a,st)
                    rows.append(summary)
            rows.sort(key=lambda v:v["all_22_months"]["net_usd"],reverse=True)
            label=f"{asset.lower()}_{mode}"
            root["ranking"][label]=rows
            pd.DataFrame([{
              "activation":x["activation"],
              "trailing_stop_points":x["trailing_stop_points"],
              **{f"training_{k}":v for k,v in x["train_2025"].items()},
              **{f"holdout_{k}":v for k,v in x["holdout_2026_jan_oct"].items()},
              **{f"full_{k}":v for k,v in x["all_22_months"].items()}
            } for x in rows]).to_csv(OUT/f"{label}_grid.csv",index=False)
            trainbest=max(rows,key=lambda x:x["train_2025"]["net_usd"])
            fullbest=rows[0]
            fixed=next(x for x in rows if x["activation"]==100 and x["trailing_stop_points"]==500)
            best100=max((x for x in rows if x["activation"]==100),key=lambda x:x["train_2025"]["net_usd"])
            candidates=[("requested_activation100_stop500",fixed),
                        ("best_activation100_train_2025",best100),
                        ("best_training_2025",trainbest),("best_all22_in_sample",fullbest)]
            root["selected"][label]={}
            for name,s in candidates:
                f,recheck=run_one(args,asset,mode,s["activation"],s["trailing_stop_points"])
                monthly=month_table(f)
                root["selected"][label][name]={"summary":recheck,"monthly":monthly}
                f.to_csv(OUT/f"{label}_{name}_trades.csv.gz",index=False,compression="gzip")
                pd.DataFrame(monthly).to_csv(OUT/f"{label}_{name}_monthly.csv",index=False)
                if name in ("requested_activation100_stop500","best_activation100_train_2025","best_training_2025"):
                    f2,gated=run_one(args,asset,mode,s["activation"],s["trailing_stop_points"],True)
                    root["selected"][label][name]["wallet_guarded"]=gated
                    f2.to_csv(OUT/f"{label}_{name}_wallet_guarded_trades.csv.gz",index=False,compression="gzip")
            print("GRID_COMPLETE",label,
                  json.dumps({"requested":fixed,"train_best":trainbest,"all22_best":fullbest},separators=(",",":")),
                  flush=True)
        del args
    (OUT/"summary.json").write_text(json.dumps(root,indent=2)+"\n")
    print("TRAILING_STOP_POINTS_GRID_FINISHED",OUT,flush=True)

if __name__=="__main__":
    main()
