#!/usr/bin/env python3
"""BTCUSD $100 wallet, $10 sizing budget x 100, CROSS collateral simulation.

Cross means initial margin is NOT subtracted from collateral. Entire wallet,
plus unrealized PNL, is tested against maintenance requirement using 1m MARK
OHLC. One active BTCUSD contract position; 0.001 BTC lot rounding. Source
signals are frozen independently computed history, not live order fills.
Research only: NOT a faithful Delta India cross liquidation-engine replica.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive
from research_stage18_100x_liquidation_20261122 import (
    get_events, mark_history, recreate_exit, END, FEE, LIQ_FEE,
    MM, SLIP, LOT, MARGIN_MAX, LEVERAGE, START, PRIORITY,
)

CROSS_IM = 0.005    # BTCUSD maximum offered leverage 200x / initial 0.5%
NOTIONAL_BUDGET = MARGIN_MAX * LEVERAGE
DNAME = "analysis/stage18_100x_cross_20261122"

def cross_liquidation_price(wallet, p):
    """Solve wallet + unrealised PNL = maintenance + estimated exit taker fee.

    Effective collateral at margin test includes *all* wallet, not $10.
    A negative long-side threshold means no liquidation at positive prices.
    """
    s=p["side"]; q=p["qty"]; entry=p["entry"]
    threshold=(s*entry-wallet/q)/(s-MM-FEE)
    if s==1 and threshold<=0:return None
    if not np.isfinite(threshold) or threshold<=0:
        raise ValueError("Invalid cross maintenance threshold")
    return float(threshold)

def run(args):
    full,seg_start,seg_end,quality=read_archive()
    events,source=get_events(args.core,args.donchian,full,seg_end)
    first=int(pd.Timestamp("2025-01-01",tz="UTC").timestamp())
    f=full[(full.time>=first)&(full.time<END)]
    if len(f)<900000:raise RuntimeError("Insufficient 1-minute BTCUSD data")
    t=f.time.to_numpy(np.int64)
    opens=f.open.to_numpy(float)
    marks=mark_history(t)
    idx={int(u):k for k,u in enumerate(t)}
    candidates={}
    for e in events:
        k=idx.get(e["entry"])
        if k is not None:candidates.setdefault(k,[]).append(e)
    for group in candidates.values():
        group.sort(key=lambda v:PRIORITY[v["strategy"]])
    dt=pd.to_datetime(t+19800,unit="s",utc=True)
    days=dt.strftime("%Y-%m-%d").to_numpy()
    months=dt.strftime("%Y-%m").to_numpy()

    wallet=START;position=None
    fees_entry=fees_exit=fees_liq=0.
    liquidations=skips_busy=skips_funds=skips_lot=0
    trades=[];daily=[];monthly=[]
    prev_day=prev_month=None
    start_day=start_month=last_equity=START
    day_peak=START;day_max_dd=0.
    all_peak=START;max_dd=0.;max_dd_time=None
    max_day_dd=0.;max_day_dd_day=None
    max_notional=0.

    def equity(price):
        if position is None:return wallet
        p=position
        return max(0.,wallet + p["side"]*p["qty"]*(price-p["entry"]))

    def exit_trade(k,liq=False,mark_trigger=None,why=None):
        nonlocal position,wallet,fees_exit,fees_liq,liquidations
        p=position; s=p["side"];qty=p["qty"]
        px=(float(mark_trigger)-s*SLIP if liq else
            recreate_exit(p["netpts"],s,p["entry"]))
        px=max(.5,px)
        exit_fee=FEE*qty*px
        penalty=LIQ_FEE*qty*float(mark_trigger) if liq else 0.
        pnl_gross=s*qty*(px-p["entry"])
        old_wallet=wallet
        wallet=max(0., wallet+pnl_gross-exit_fee-penalty)
        fees_exit+=min(exit_fee,max(0.,old_wallet+pnl_gross))
        fees_liq+=min(penalty,max(0.,old_wallet+pnl_gross-exit_fee))
        if liq:liquidations+=1
        trades.append(dict(strategy=p["strategy"],entry_unix=p["entry_unix"],
            exit_unix=int(t[k]),side=s,qty_btc=qty,lots=p["lots"],
            notional_at_entry=p["notional"],entry_fill=p["entry"],
            exit_fill=px,entry_fee=p["entry_fee"],exit_fee=exit_fee,
            liquidation_fee=penalty,liquidated=liq,reason=why or p["reason"],
            net_pnl=wallet-p["wallet_at_entry"],
            account_equity_after=wallet))
        position=None

    for k,ts in enumerate(t):
        day=days[k];month=months[k]
        if prev_day is None:prev_day=day
        elif day!=prev_day:
            daily.append(dict(day_ist=str(prev_day),start_equity=start_day,
                 end_equity=last_equity,net_pnl=last_equity-start_day,
                 return_pct=100*(last_equity/start_day-1) if start_day>0 else 0.,
                 intraday_drawdown_pct=day_max_dd))
            prev_day=day;start_day=last_equity
            day_peak=last_equity;day_max_dd=0.
        if prev_month is None:prev_month=month
        elif month!=prev_month:
            monthly.append(dict(month_ist=str(prev_month),start_equity=start_month,
                  end_equity=last_equity,net_pnl=last_equity-start_month,
                  return_pct=100*(last_equity/start_month-1) if start_month>0 else 0.))
            prev_month=month;start_month=last_equity

        closed=False
        if position is not None:
            mo,mh,ml,mc=marks[k]
            px=cross_liquidation_price(wallet,position)
            if px is not None and ((position["side"]==1 and ml<=px) or
                                   (position["side"]==-1 and mh>=px)):
                crossed_open=(mo<=px if position["side"]==1 else mo>=px)
                trigger=float(mo if crossed_open else px)
                exit_trade(k,True,trigger,"cross_margin_mark_liquidation")
                closed=True
            elif int(ts)>=position["exit_unix"]:
                exit_trade(k,False,None,position["reason"])
                closed=True
        if k in candidates:
            proposals=candidates[k]
            if position is not None or closed:skips_busy+=len(proposals)
            else:
                entry_event=proposals[0];skips_busy+=len(proposals)-1
                side=int(entry_event["side"])
                entry=max(.5,float(opens[k])+side*SLIP)
                lots=math.floor(NOTIONAL_BUDGET/(entry*LOT)+1e-12)
                if lots<1:skips_lot+=1
                else:
                    qty=lots*LOT;notional=qty*entry
                    fee=FEE*notional
                    min_collateral=CROSS_IM*notional
                    if wallet<min_collateral+2*fee-1e-9:skips_funds+=1
                    else:
                        before=wallet
                        wallet-=fee;fees_entry+=fee
                        max_notional=max(max_notional,notional)
                        position=dict(strategy=entry_event["strategy"],side=side,
                          qty=qty,lots=lots,notional=notional,entry=entry,
                          entry_unix=entry_event["entry"],exit_unix=entry_event["exit"],
                          netpts=float(entry_event["netpts"]),reason=entry_event["reason"],
                          entry_fee=fee,wallet_at_entry=before)
                        mo,mh,ml,mc=marks[k]
                        px=cross_liquidation_price(wallet,position)
                        if px is not None and ((side==1 and ml<=px) or (side==-1 and mh>=px)):
                            crossed_open=(mo<=px if side==1 else mo>=px)
                            exit_trade(k,True,float(mo if crossed_open else px),
                                "same_minute_cross_liquidation")

        last_equity=equity(float(marks[k,3]))
        if position is None:adverse=last_equity
        else:
            worst_price=float(marks[k,2] if position["side"]==1 else marks[k,1])
            adverse=min(last_equity,equity(worst_price))
        # Causal approximation based on previous 1m close and the current
        # 1m adverse extreme; exact intraminute sequence not known.
        day_max_dd=max(day_max_dd,
            100*(day_peak-adverse)/day_peak if day_peak>0 else 0.)
        if day_max_dd>max_day_dd:
            max_day_dd=day_max_dd;max_day_dd_day=str(day)
        cur_dd=100*(all_peak-adverse)/all_peak if all_peak>0 else 0.
        if cur_dd>max_dd:max_dd=cur_dd;max_dd_time=int(ts)
        day_peak=max(day_peak,last_equity)
        all_peak=max(all_peak,last_equity)

    daily.append(dict(day_ist=str(prev_day),start_equity=start_day,
        end_equity=last_equity,net_pnl=last_equity-start_day,
        return_pct=100*(last_equity/start_day-1) if start_day>0 else 0.,
        intraday_drawdown_pct=day_max_dd))
    monthly.append(dict(month_ist=str(prev_month),start_equity=start_month,
        end_equity=last_equity,net_pnl=last_equity-start_month,
        return_pct=100*(last_equity/start_month-1) if start_month>0 else 0.))

    tr=pd.DataFrame(trades);dy=pd.DataFrame(daily);mn=pd.DataFrame(monthly)
    assert len(mn)==22,("Wrong month count",len(mn))
    assert np.isclose(last_equity,START+mn.net_pnl.sum(),atol=1e-6)
    groups=(tr.groupby("strategy").agg(n=("strategy","size"),
        liquidations=("liquidated","sum"),net_pnl=("net_pnl","sum"))
        .reset_index().to_dict("records")) if len(tr) else []
    report=dict(status="CROSS_WALLET_1M_LIQUIDATION_APPROXIMATION_NOT_EXCHANGE_FILLS",
       source_events=source,source_event_count=len(events),
       historical_minutes=int(len(t)),starting_wallet=START,
       per_trade_budget_usd=MARGIN_MAX,notional_multiplier=LEVERAGE,
       maximum_position_notional_budget=NOTIONAL_BUDGET,
       max_notional_filled=float(max_notional),
       margin_model="CROSS ENTIRE WALLET SUPPORTS MM",
       initial_margin_requirement_rate=CROSS_IM,
       maintenance_margin_rate=MM,
       taker_fee_plus_gst_rate=FEE,
       liquidation_penalty_plus_gst_rate_assumed=LIQ_FEE,
       final_balance=float(last_equity),net_pnl=float(last_equity-START),
       return_pct=float(100*(last_equity/START-1)),
       trades_executed=int(len(tr)),
       wins=int((tr.net_pnl>1e-9).sum()) if len(tr) else 0,
       losses=int((tr.net_pnl<-1e-9).sum()) if len(tr) else 0,
       liquidations=int(liquidations),skips_busy=int(skips_busy),
       skips_insufficient_collateral=int(skips_funds),skips_min_lot=int(skips_lot),
       profitable_months=int((mn.net_pnl>1e-9).sum()),
       losing_months=int((mn.net_pnl<-1e-9).sum()),
       flat_months=int((abs(mn.net_pnl)<=1e-9).sum()),
       fees_entry=float(fees_entry),fees_exit=float(fees_exit),
       penalties_liquidation=float(fees_liq),
       costs_total=float(fees_entry+fees_exit+fees_liq),
       max_account_drawdown_pct=float(max_dd),
       max_account_drawdown_utc=(str(pd.Timestamp(max_dd_time,unit="s",tz="UTC"))
          if max_dd_time is not None else None),
       max_daily_intraday_drawdown_pct=float(max_day_dd),
       max_daily_drawdown_day_ist=max_day_dd_day,
       worst_day=dy.loc[dy.net_pnl.idxmin()].to_dict(),
       worst_month=mn.loc[mn.net_pnl.idxmin()].to_dict(),
       breakdown=groups,has_open_position_at_end=position is not None,
       funding_applied=False,
       caveats=[
         "Cross margin uses all wallet funds; the $10 is position sizing not isolated liquidation collateral",
         "Historical signal streams are frozen; reentry after a prior liquidation is not regenerated",
         "197 reconstructed H1 exits versus 196 archived monthly trade count; source parity warning",
         "Position on same BTCUSD contract is exclusive, not real concurrent cross offset or portfolio allocation",
         "Cross IM 0.5% and MM 0.25% BTCUSD small size; margin rates may change",
         "Cross liquidation assumes full position force-closed at 1m mark threshold; actual Delta may partially liquidate",
         "Liquidation fee rate uses 0.05% BTC isolated penalty as proxy; cross-specific schedule not verified",
         "Funding excluded. No live bid/ask spreads, depth, exact intraminute sequence, or historical USD/INR",
         "Trade returns in USD-equivalent, not actual INR settlement wallet statement",
         "The old 21/22 monthly allocation is not executed in this fixed-notional single-position test",
         "Real exchange fills, execution chronology, funding cashflows and real-forward performance unverified"
       ])
    args.out.mkdir(parents=True,exist_ok=True)
    tr.to_csv(args.out/"trades.csv",index=False)
    dy.to_csv(args.out/"daily.csv",index=False)
    mn.to_csv(args.out/"monthly.csv",index=False)
    (args.out/"summary.json").write_text(json.dumps(report,indent=2,default=str)+"\n")
    print("CROSS100X_RESULT "+json.dumps(report,default=str))
    print("CROSS100X_MONTHLY\n"+mn.to_string(index=False))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--core",type=Path,required=True)
    p.add_argument("--donchian",type=Path,required=True)
    p.add_argument("--out",type=Path,default=Path(DNAME))
    run(p.parse_args())
