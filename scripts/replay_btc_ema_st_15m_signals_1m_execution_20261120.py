#!/usr/bin/env python3
"""BTCUSD 15M EMA20+Supertrend exact original indicators, 1M stop/trail replay.

CONTROLLED COMPARISON with +$828.4954 original BTC 15M OHLC simulation.
Only replaces the historical 15M OHLC stop/trailing engine with 1M OHLC
sequence. Preserves 15M completed signal (EMA20 ST10/3 ATR14*2,
ATR expansion >=1, volume ratio >=1.5, 150/50 trail), 100x isolated
$10 margin, $100 wallet, 0.001 BTC lots, $1 preliquidation buffer, zero
funding/slippage, 0.05% taker and 18% GST. Uses same price path
and fee_net function as original, not an alternative signal generator.

Positions enter at next 1M open *after* the full confirmed 15M bar.
ST reversal exits at next 1M open after full confirmed 15M flip.
1M stop/trailing checks start from the entry minute.
Exits use 1M bar-end time as conservative holding-time upper bound.

Original 15M baseline is recomputed from source and asserted equal to the
previously recorded +828.4954 before accepting the 1M result.

A separate no-offer scenario removes hypothetical historical Scalper waiver.
Do not claim simulated 1M OHLC is exchange tick/mark executions.
"""
from __future__ import annotations
import hashlib,json,math,sys
from pathlib import Path
import numpy as np
import pandas as pd

import replay_btc_ema_st_screenshot as old_signals
import replay_btc_ema_st_100x as old_model
import replay_btc_ema_st_preliq_one_point as old_preliq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"vps-btc-ema-st"))
from preliq import pre_liq_buffer,pre_liq_stop,effective_stop

OUT=Path("analysis/btc_ema_st_15m_entry_1m_exit_20261120")
ORIGINAL_EXPECTED_NET=828.4954
INITIAL_CASH=100.
MAX_MARGIN=10.
LEV=100
TICK=0.5
LOT=.001
MAINT=.0025
BASE_FEE=.0005
GST=.18
TRAIL_ACT=150.
TRAIL_DIST=50.
START_BAR=36
FIRST_MONTH="2025-01"
LAST_COMPLETE_MONTH="2026-10"

def load_minutes():
    manifest=json.loads((old_signals.DATA/"manifest.json").read_text())
    frames=[]
    for x in manifest["partitions"]:
        f=old_signals.DATA/x["file"]
        assert hashlib.sha256(f.read_bytes()).hexdigest()==x["sha256_gzip"],f
        assert x["missing_minutes"]==0,(f,"source minute gap")
        z=pd.read_csv(f,compression="gzip",usecols=["time","open","high","low","close"])
        assert len(z)==x["observed_candles"]
        frames.append(z)
    minutes=pd.concat(frames,ignore_index=True)
    t=minutes.time.to_numpy(np.int64)
    assert (np.diff(t)==60).all()
    assert len(t)%15==0
    return minutes,manifest

def fee_model(q,ep,xp,side,held,reason,offer):
    # Reuse EXACT original fee, GST and simulated liquidation penalty function.
    f=old_model.fee_net(q,ep,xp,side,held,reason,"threshold")
    if not offer and f["eligible_scalper"]:
        assert reason!="liquidation"
        close_fee=q*xp*BASE_FEE
        close_gst=close_fee*GST
        f["exit_fee_usd"]=close_fee
        f["exit_gst_usd"]=close_gst
        f["net_usd"]-=close_fee+close_gst
        f["eligible_scalper"]=False
    return f

def replay_one_minute(raw,bars,offer):
    t=raw.time.to_numpy(np.int64)
    op=raw.open.to_numpy(float);hi=raw.high.to_numpy(float)
    lo=raw.low.to_numpy(float);cl=raw.close.to_numpy(float)
    b=bars.reset_index()
    bt=np.asarray(pd.DatetimeIndex(b.dt).as_unit("s").asi8,dtype=np.int64)
    assert len(b)*15==len(raw)
    assert bt[0]==t[0] and np.array_equal(bt,t[::15])
    em=b.ema.to_numpy(float);atr=b.atr14.to_numpy(float)
    direct=b.dir.to_numpy();ar=b.atr_ratio.to_numpy(float);vr=b.volume_ratio.to_numpy(float)
    bopen=b.open.to_numpy(float);bhigh=b.high.to_numpy(float)
    blow=b.low.to_numpy(float);bclose=b.close.to_numpy(float)
    wallet=INITIAL_CASH
    peak=wallet;maxdd=0.
    pos=None
    events=[]
    skip_wallet=0;skip_lots=0;eligible_signals=0
    modeled_liq=0;st_flip=0;exits_preliq=0
    n_raw=len(raw)
    def exit_position(j,exit_time,exit_price,reason):
        nonlocal wallet,peak,maxdd,pos,modeled_liq,st_flip,exits_preliq
        p=pos
        assert p is not None
        if reason=="liquidation":modeled_liq+=1
        if reason=="supertrend_flip":st_flip+=1
        if reason!="liquidation" and abs(p["sl"]-p["preliq"])<.0000001:
            exits_preliq+=1
        hold=max(0,(exit_time-p["entry_time"])/60)
        f=fee_model(p["qty"],p["entry"],exit_price,p["side"],hold,reason,offer)
        if reason=="liquidation":
            isolated_change=max(-p["margin"],f["gross_usd"]-f["liquidation_fee_usd"]-f["liquidation_gst_usd"])
            net=isolated_change-f["entry_fee_usd"]-f["entry_gst_usd"]
        else:
            isolated_change=f["gross_usd"]-f["exit_fee_usd"]-f["exit_gst_usd"]
            net=isolated_change-f["entry_fee_usd"]-f["entry_gst_usd"]
        previous=wallet
        wallet=max(0.,wallet+net)
        realized=wallet-previous
        peak=max(peak,wallet);maxdd=max(maxdd,100*(1-wallet/peak)) if peak else 100.
        events.append(dict(entry_epoch=p["entry_time"],exit_epoch=int(exit_time),
              entry_utc=pd.Timestamp(p["entry_time"],unit="s",tz="UTC").isoformat(),
              exit_utc=pd.Timestamp(exit_time,unit="s",tz="UTC").isoformat(),
              side="long" if p["side"]==1 else "short",entry_price=p["entry"],
              exit_price=float(exit_price),contracts=p["contracts"],qty_btc=p["qty"],
              isolated_margin_usd=p["margin"],initial_stop=p["initial_stop"],
              estimated_liquidation=p["liq"],preliq_stop=p["preliq"],
              exit_reason=reason,hold_minutes=round(hold,2),
              assumed_scalper_fee_waiver=bool(f["eligible_scalper"]),
              gross_usd=f["gross_usd"],net_usd=realized,
              entry_fee_usd=f["entry_fee_usd"],entry_gst_usd=f["entry_gst_usd"],
              exit_fee_usd=f["exit_fee_usd"],exit_gst_usd=f["exit_gst_usd"],
              liquidation_fee_usd=f["liquidation_fee_usd"],
              liquidation_gst_usd=f["liquidation_gst_usd"],
              wallet_before_usd=previous,wallet_after_usd=wallet))
        pos=None

    for j in range(n_raw):
        timestamp=int(t[j])
        closed_this_boundary=False
        # Only at 15m boundary do new *completed 15M* signals become known.
        if j%15==0 and j>=15:
            i=j//15-1
            assert int(bt[i]+900)==timestamp
            if pos is not None and i>0:
                side=pos["side"]
                flip=(side==1 and direct[i]==1 and direct[i-1]==-1) or (
                      side==-1 and direct[i]==-1 and direct[i-1]==1)
                if flip:
                    exit_position(j,timestamp,float(op[j]),"supertrend_flip")
                    closed_this_boundary=True
            # Previously held trade may have exited within the prior candle,
            # so a fresh signal on this just-completed 15M bar is eligible.
            if pos is None and not closed_this_boundary and i>=START_BAR:
                if all(math.isfinite(float(z)) for z in [em[i],atr[i],ar[i],vr[i]]):
                    side=0
                    if ar[i]>=1. and vr[i]>=1.5:
                        if direct[i]==-1 and direct[i-1]==-1 and blow[i]<=em[i] and bclose[i]>em[i]:
                            side=1
                        elif direct[i]==1 and direct[i-1]==1 and bhigh[i]>=em[i] and bclose[i]<em[i]:
                            side=-1
                    if side:
                        eligible_signals+=1
                        ep=float(op[j]) # Next 1m OPEN after confirmed 15m candle.
                        contracts=math.floor(MAX_MARGIN*LEV/(ep*LOT)+1e-10)
                        if contracts<1:skip_lots+=1
                        else:
                            qty=contracts*LOT;notional=qty*ep;margin=notional/LEV
                            entry_fee=notional*BASE_FEE*(1+GST)
                            if wallet+1e-9<margin+entry_fee:skip_wallet+=1
                            else:
                                liq=(ep-margin/qty)/(1-MAINT) if side==1 else (
                                      ep+margin/qty)/(1+MAINT)
                                bankruptcy=ep-side*margin/qty
                                atrpts=max(TICK,round(2*atr[i]/TICK)*TICK)
                                raw_stop=ep-side*atrpts
                                pos_side="buy" if side==1 else "sell"
                                near=pre_liq_stop(pos_side,liq,
                                    pre_liq_buffer("BTC",ep,TICK,1,80000),TICK)
                                initial=effective_stop(pos_side,raw_stop,near,ep)
                                assert (initial<ep if side==1 else initial>ep)
                                pos=dict(side=side,entry=ep,entry_time=timestamp,contracts=contracts,
                                    qty=qty,margin=margin,liq=liq,bankruptcy=bankruptcy,
                                    initial_stop=initial,preliq=near,
                                    sl=initial,best=ep,active=False)
        if pos is not None:
            p=pos
            # EXACT same historical path logic as original, but now each
            # individual 1-minute candle has its own inferred O-H-L-C ordering.
            if ((p["side"]==1 and op[j]<=p["liq"]) or (
                p["side"]==-1 and op[j]>=p["liq"])):
                xp=float(op[j]);reason="liquidation"
            else:
                xp,p["sl"],p["best"],p["active"],reason=old_model.path_exit(
                    op[j],hi[j],lo[j],cl[j],p["side"],p["entry"],
                    p["sl"],p["best"],p["active"],p["liq"])
            if xp is not None:
                exit_time=timestamp+60 # conservative latest minute timestamp
                exit_position(j,exit_time,float(xp),reason)

    tr=pd.DataFrame(events)
    if len(tr):
        tr["exit_month_ist"]=pd.to_datetime(tr.exit_epoch,unit="s",utc=True).dt.tz_convert(
            "Asia/Kolkata").dt.strftime("%Y-%m")
    gp=float(tr.loc[tr.net_usd>0,"net_usd"].sum()) if len(tr) else 0.
    gl=-float(tr.loc[tr.net_usd<0,"net_usd"].sum()) if len(tr) else 0.
    m=[]
    previous=INITIAL_CASH
    for month in pd.period_range(FIRST_MONTH,"2026-11",freq="M").astype(str):
        group=tr[tr.exit_month_ist==month] if len(tr) else tr
        change=float(group.net_usd.sum()) if len(group) else 0.
        end=previous+change
        m.append(dict(month=month,complete=month<=LAST_COMPLETE_MONTH,
                      net_usd=round(change,4),trades=int(len(group)),
                      wins=int((group.net_usd>0).sum()) if len(group) else 0,
                      losses=int((group.net_usd<0).sum()) if len(group) else 0,
                      ending_cash_usd=round(end,4)))
        previous=end
    complete=[z for z in m if z["complete"]]
    result=dict(initial_cash_usd=INITIAL_CASH,final_cash_usd=round(wallet,4),
         net_usd=round(wallet-INITIAL_CASH,4),
         trades=int(len(tr)),
         win_rate_pct=round(float((tr.net_usd>0).mean()*100),2) if len(tr) else None,
         profit_factor=round(gp/gl,4) if gl>0 else None,
         positive_complete_months=sum(z["net_usd"]>0 for z in complete),
         negative_complete_months=sum(z["net_usd"]<0 for z in complete),
         flat_complete_months=sum(z["net_usd"]==0 for z in complete),
         completed_months=22,
         max_closed_drawdown_pct=round(maxdd,2),
         exits_liquidation=modeled_liq,
         preliq_stop_touch_exits=exits_preliq,
         supertrend_flip_exits=st_flip,
         assumed_fee_waivers=int(tr.assumed_scalper_fee_waiver.sum()) if len(tr) else 0,
         skipped_wallet=skip_wallet,skipped_lots=skip_lots,
         eligible_signals_when_flat=eligible_signals,
         open_position_at_cutoff=bool(pos),
         fees_gst_usd=round(float(tr.entry_fee_usd.sum()+tr.entry_gst_usd.sum()+
                                 tr.exit_fee_usd.sum()+tr.exit_gst_usd.sum()+
                                 tr.liquidation_fee_usd.sum()+tr.liquidation_gst_usd.sum()),4) if len(tr) else 0.,
         monthly=m)
    assert result["completed_months"]==22
    if pos is None:
        assert abs(float(tr.net_usd.sum())-(wallet-INITIAL_CASH))<.0001
        assert abs(sum(x["net_usd"] for x in m)-(wallet-INITIAL_CASH))<.002
    return result,tr

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    # Baseline regression: SOURCE SCRIPT reproduced before changing execution.
    bars,manifest,n=old_signals.load()
    enriched=old_signals.indicators(bars)
    base_tr,base_stat=old_preliq.replay(enriched,0,"threshold")
    assert abs(base_stat["net_profit_usd"]-ORIGINAL_EXPECTED_NET)<.0002,      ("Original $828.50 baseline did not reproduce",base_stat["net_profit_usd"])
    base_tr.to_csv(OUT/"original_15m_ohlc_trades.csv.gz",index=False,compression="gzip")
    raw,raw_manifest=load_minutes()
    assert len(raw)==n and len(bars)*15==n
    scenarios={}
    for offer in (True,False):
        name="assumed_30m_offer" if offer else "no_offer"
        print("REPLAY_1M",name,flush=True)
        summary,trade=replay_one_minute(raw,enriched,offer)
        scenarios[name]=summary
        trade.to_csv(OUT/f"{name}_1m_trades.csv.gz",index=False,compression="gzip")
        pd.DataFrame(summary["monthly"]).to_csv(OUT/f"{name}_1m_monthly.csv",index=False)
        print("RESULT_1M",name,json.dumps({k:v for k,v in summary.items() if k!="monthly"},sort_keys=True),flush=True)
    doc=dict(status="completed",instrument="BTCUSD",
        history=dict(source=manifest["source"],minute_bars=n,
                     first_minute_utc=str(pd.Timestamp(int(raw.time.iloc[0]),unit="s",tz="UTC")),
                     last_minute_utc=str(pd.Timestamp(int(raw.time.iloc[-1]),unit="s",tz="UTC")),
                     full_complete_months="Jan 2025-Oct 2026",partial_nov_2026_included_in_total=True),
        comparison=dict(original_15m_ohlc={
            "net_usd":base_stat["net_profit_usd"],"trades":base_stat["completed_trades"],
            "profit_factor":base_stat["net_profit_factor"],
            "positive_complete_months":base_stat["profitable_completed_months"],
            "liquidations":base_stat["assumed_liquidations"]},
            one_minute=scenarios),
        preserved=dict(signal="confirmed 15M EMA20 and ST10/3, ATR ratio >=1.0, volume ratio >=1.5",
            atr_stop="2x ATR14 on 15M",
            trailing_activation_points=TRAIL_ACT,trailing_distance_points=TRAIL_DIST,
            initial_cash=INITIAL_CASH,margin_budget_per_trade=MAX_MARGIN,
            isolated_leverage=LEV,contract_size_btc=LOT,preliq_buffer_points=1,
            fees_taker_each_side=BASE_FEE,gst_on_fees=GST,scalper_assumed_window_minutes=30,
            spread=0,slippage=0,funding=0),
        changed=["Only entry execution at next 1M open after 15M close, and 1M OHLC stop/trail/exit resolution.",
                 "Supertrend flip is acted on at next 1M open after 15M close.",
                 "Offer eligibility derived from 1M conservative upper-bound hold time instead of 15M integer blocks."],
        limits=[
            "1M candle OHLC still infers intraminute high/low order, not real ticks, quotes or fills.",
            "No actual historical mark-price liquidation, spread, slippage, funding or latency.",
            "Offer active all-history is an optimistic assumption; compare the no-offer scenario.",
            "No pre-entry trading from unclosed 15-minute bars; 15M indicators unchanged.",
            "No VPS live bot or main branch modified.",
            "The previous +$828.50 includes partial Nov 2026; 22 complete months end Oct 2026.",
            "Fixed $10 margin per position, no replenishment or position size compounding."])
    (OUT/"summary.json").write_text(json.dumps(doc,indent=2)+"\n")
    md=["# Original BTC 15M EMA20+Supertrend: 1M OHLC stop/trailing validation",
        "Original script recomputed and +$828.4954 regression-verified from identical archived data.",
        "The only material execution change is 15M OHLC to 1M OHLC, plus consequent exact-minute timing.",
        "",
        "| Model | Net USD | Trades | Profit factor | Profitable complete months |",
        "|---|---:|---:|---:|---:|"]
    v=doc["comparison"]["original_15m_ohlc"]
    md.append(f'| Old 15M OHLC (assumed offer) | {v["net_usd"]:+.2f} | {v["trades"]} | {v["profit_factor"]} | {v["positive_complete_months"]}/22 |')
    for key,st in scenarios.items():
        md.append(f'| New 1M OHLC {key} | {st["net_usd"]:+.2f} | {st["trades"]} | {st["profit_factor"]} | {st["positive_complete_months"]}/22 |')
    md+=["","## Model limitations"]+[f"- {x}" for x in doc["limits"]]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(md)+"\n")
    print("COMPLETE_15M_1M_COMPARISON",json.dumps({
        "original_15m":v,
        "one_minute":{k:{q:val for q,val in st.items() if q!="monthly"} for k,st in scenarios.items()}
    },sort_keys=True),flush=True)
if __name__=="__main__":main()
