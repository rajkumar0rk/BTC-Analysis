#!/usr/bin/env python3
"""BTCUSD isolated $100/$10/100x research replay with mark-price liquidation.

Historical accepted strategy event streams are FROZEN. Early liquidation may
alter later signal eligibility; not a full strategy signal-regeneration engine.
One open BTCUSD position in this shared-wallet replay, auto-topup disabled.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
import numpy as np
import pandas as pd

START=100.
MARGIN_MAX=10.
LEVERAGE=100.
LOT=.001
FEE=.0005*1.18
LIQ_FEE=.0005*1.18
MM=.0025
SLIP=5.
END=int(pd.Timestamp("2026-11-01",tz="Asia/Kolkata").timestamp())
PRIORITY={"core":0,"donchian":1,"hourly":2}
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()

def recreate_exit(netpts,side,entry_fill):
    # Ledger net price points includes BOTH taker+GST charges and 5pt each-side slip.
    return (netpts+(side+FEE)*entry_fill)/(side-FEE)

def get_events(core_path,don_path,f,seg_end):
    c=pd.read_csv(core_path)
    d=pd.read_csv(don_path)
    c=c[c.variant=="core_maxrisk_700"]
    d=d[d.model=="channel20_2atrtrail"]
    assert len(c)==63 and len(d)==20,(len(c),len(d))
    ev=[]
    for name,tab in (("core",c),("donchian",d)):
        for r in tab.itertuples(index=False):
            if int(r.entry_unix)>=END:continue
            ev.append(dict(strategy=name,entry=int(r.entry_unix),
               exit=int(r.exit_unix),side=int(r.direction),
               netpts=float(r.net_pts if name=="core" else r.net_points),
               reason=str(r.reason)))
    sys.path.insert(0,str(Path("scripts").resolve()))
    import research_new_1h_patterns_stage19 as h
    from research_structure_rr_stage11 import replay_one
    all_ev=h.build_candidates(f,seg_end)
    selected=all_ev[(all_ev.pattern=="ema20_pullback_confirm") &
                     (all_ev.h4_eff8>=.30)]
    O=f.open.to_numpy(float);H=f.high.to_numpy(float)
    L=f.low.to_numpy(float);C=f.close.to_numpy(float);T=f.time.to_numpy(np.int64)
    busy=-1;hourly=[];n_exits_22=0
    for r in selected.itertuples(index=False):
        if int(r.k)<=busy:continue
        j,why,gross,net,offer,net_R,risk=replay_one(
            O,H,L,C,int(r.k),int(r.side),float(r.stop),3.,480)
        busy=int(j)
        if int(T[j])<END:n_exits_22+=1
        if int(r.unix)<END:
            hourly.append(dict(strategy="hourly",entry=int(r.unix),
              exit=int(T[j]),side=int(r.side),netpts=float(net),
              reason=("stop","target","timeout")[int(why)]))
    assert n_exits_22==196,("Hourly source reconciliation failed",n_exits_22)
    ev+=hourly
    return ev,dict(core=len(c),donchian=len(d),
                   hourly_exits_in_22mo=n_exits_22,hourly_entries=len(hourly))

def mark_history(t):
    root=Path("data/delta_india/BTCUSD/institutional/history/mark_1m")
    files=sorted(p for p in root.glob("20??-??.csv.gz")
                 if p.name[:7]<="2026-10")
    if len(files)<22:raise RuntimeError("Missing native mark-price source")
    frames=[pd.read_csv(p,compression="gzip",usecols=["time","open","high","low","close"])
            for p in files]
    x=pd.concat(frames,ignore_index=True).sort_values("time",kind="stable")
    if x.time.duplicated().any():raise AssertionError("Duplicate mark data")
    m=x.set_index("time").reindex(t)[["open","high","low","close"]].to_numpy(float)
    if not np.isfinite(m).all():raise RuntimeError("Uncovered historic mark-price minute")
    return m

def run(args):
    sys.path.insert(0,str(Path("scripts").resolve()))
    from research_every_candle_200 import read_archive
    full,seg_start,seg_end,quality=read_archive()
    events,counts=get_events(args.core,args.donchian,full,seg_end)
    f=full[(full.time>=int(pd.Timestamp("2025-01-01",tz="UTC").timestamp())) &
           (full.time<END)]
    if len(f)<900000:raise RuntimeError("Historic futures 1m data incomplete")
    t=f.time.to_numpy(np.int64)
    O=f.open.to_numpy(float)
    mark=mark_history(t)
    idx={int(v):i for i,v in enumerate(t)}
    byminute={}
    for e in events:
        k=idx.get(e["entry"])
        if k is None:continue
        byminute.setdefault(k,[]).append(e)
    for v in byminute.values():v.sort(key=lambda x:PRIORITY[x["strategy"]])
    # IST calendar month/day derived from completed UTC minute boundaries.
    dt=pd.to_datetime(t+19800,unit="s",utc=True)
    days=dt.strftime("%Y-%m-%d").to_numpy()
    mons=dt.strftime("%Y-%m").to_numpy()
    cash=START;position=None
    trades=[];daily=[];monthly=[]
    fe_entry=fe_exit=fe_liq=0.
    liquidations=skipped_busy=skipped_funds=skipped_lot=0
    prev_day=prev_month=None
    start_day=start_month=last_equity=START
    daily_peak=daily_min=START
    all_peak=START
    max_account_dd=max_daily_dd=0.
    max_account_dd_time=max_daily_dd_day=None

    def equity(mark_price):
        if position is None:return cash
        return cash+max(0.,position["margin"]+
            position["side"]*position["qty"]*(mark_price-position["entry_price"]))

    def close(k,liquidate=False,trigger=None,reason=""):
        nonlocal position,cash,fe_exit,fe_liq,liquidations
        p=position;s=p["side"]
        if liquidate:
            mid=float(trigger)
            px=max(.5,mid-s*SLIP)
        else:
            px=max(.5,recreate_exit(p["netpts"],s,p["entry_price"]))
        raw_gross=p["qty"]*s*(px-p["entry_price"])
        trad_fee=FEE*p["qty"]*px
        liq_fee=(LIQ_FEE*p["qty"]*mid) if liquidate else 0.
        remaining=max(0.,p["margin"]+raw_gross)
        paid_exit=min(trad_fee,remaining)
        paid_liq=min(liq_fee,max(0.,remaining-paid_exit))
        recovery=max(0.,remaining-paid_exit-paid_liq)
        cash+=recovery
        fe_exit+=paid_exit;fe_liq+=paid_liq
        if liquidate:liquidations+=1
        trades.append(dict(strategy=p["strategy"],entry_unix=p["entry_unix"],
            exit_unix=int(t[k]),side=s,lots=p["lots"],qty_btc=p["qty"],
            entry_fill=p["entry_price"],exit_fill=px,initial_margin=p["margin"],
            entry_fee=p["entry_fee"],exit_fee=paid_exit,liquidation_fee=paid_liq,
            pnl_after_fees=recovery-p["margin"]-p["entry_fee"],
            liquidated=liquidate,exit_reason=reason or p["reason"],
            account_cash_after=cash))
        position=None

    for k,ts in enumerate(t):
        day=days[k];mon=mons[k]
        if prev_day is None:
            prev_day=day
        elif day!=prev_day:
            daily.append(dict(day_ist=str(prev_day),start_equity=start_day,
                end_equity=last_equity,net_pnl=last_equity-start_day,
                daily_return_pct=100*(last_equity/start_day-1) if start_day else 0.,
                intraday_drawdown_pct=100*(daily_peak-daily_min)/daily_peak if daily_peak else 0.))
            prev_day=day;start_day=last_equity;daily_peak=daily_min=last_equity
        if prev_month is None:
            prev_month=mon
        elif mon!=prev_month:
            monthly.append(dict(month_ist=str(prev_month),start_equity=start_month,
                end_equity=last_equity,net_pnl=last_equity-start_month,
                return_pct=100*(last_equity/start_month-1) if start_month else 0.))
            prev_month=mon;start_month=last_equity

        closed=False
        if position is not None:
            p=position;s=p["side"];mo,mh,ml,mc=mark[k]
            # Remaining isolated margin = maintenance margin at liquidation price.
            liq_px=(s*p["entry_price"]-p["margin"]/p["qty"])/(s-MM)
            crossed=ml<=liq_px if s==1 else mh>=liq_px
            if crossed:
                gap=mo<liq_px if s==1 else mo>liq_px
                close(k,True,float(mo if gap else liq_px),
                      "maintenance_margin_mark_price")
                closed=True
            elif int(ts)>=p["exit_unix"]:
                close(k,False,reason=p["reason"]);closed=True
        if k in byminute:
            proposals=byminute[k]
            if position is not None or closed:skipped_busy+=len(proposals)
            else:
                e=proposals[0]
                skipped_busy+=len(proposals)-1
                s=int(e["side"])
                entry=max(.5,float(O[k])+s*SLIP)
                lots=math.floor((MARGIN_MAX*LEVERAGE)/(entry*LOT)+1e-12)
                if lots<1:skipped_lot+=1
                else:
                    qty=lots*LOT
                    im=qty*entry/LEVERAGE
                    ef=FEE*qty*entry
                    reserve_exit=ef
                    if cash<im+ef+reserve_exit-1e-9:skipped_funds+=1
                    else:
                        cash-=im+ef
                        fe_entry+=ef
                        position=dict(strategy=e["strategy"],entry_unix=e["entry"],
                            exit_unix=e["exit"],side=s,lots=lots,qty=qty,
                            entry_price=entry,margin=im,entry_fee=ef,
                            netpts=float(e["netpts"]),reason=e["reason"])
                        mo,mh,ml,mc=mark[k]
                        liq_px=(s*entry-im/qty)/(s-MM)
                        crossed=ml<=liq_px if s==1 else mh>=liq_px
                        if crossed:
                            gap=mo<liq_px if s==1 else mo>liq_px
                            close(k,True,float(mo if gap else liq_px),
                                  "entry_minute_mark_liquidation")
        last_equity=equity(float(mark[k,3]))
        if position is None:adverse=last_equity
        else:
            lo_or_hi=float(mark[k,2] if position["side"]==1 else mark[k,1])
            adverse=min(last_equity,equity(lo_or_hi))
        daily_peak=max(daily_peak,last_equity)
        daily_min=min(daily_min,adverse)
        dd=100*(daily_peak-daily_min)/daily_peak if daily_peak else 0
        if dd>max_daily_dd:
            max_daily_dd=dd;max_daily_dd_day=str(day)
        all_peak=max(all_peak,last_equity)
        cur=100*(all_peak-adverse)/all_peak if all_peak else 0
        if cur>max_account_dd:
            max_account_dd=cur;max_account_dd_time=int(ts)
    daily.append(dict(day_ist=str(prev_day),start_equity=start_day,
        end_equity=last_equity,net_pnl=last_equity-start_day,
        daily_return_pct=100*(last_equity/start_day-1) if start_day else 0.,
        intraday_drawdown_pct=100*(daily_peak-daily_min)/daily_peak if daily_peak else 0.))
    monthly.append(dict(month_ist=str(prev_month),start_equity=start_month,
        end_equity=last_equity,net_pnl=last_equity-start_month,
        return_pct=100*(last_equity/start_month-1) if start_month else 0.))
    tr=pd.DataFrame(trades);dy=pd.DataFrame(daily);mn=pd.DataFrame(monthly)
    if len(mn)!=22:raise AssertionError("22-month monthly coverage failure")
    worst_day=dy.loc[dy.net_pnl.idxmin()].to_dict()
    worst_month=mn.loc[mn.net_pnl.idxmin()].to_dict()
    groups=(tr.groupby("strategy").agg(n=("strategy","size"),
      liquidations=("liquidated","sum"),net_pnl=("pnl_after_fees","sum"))
      .reset_index().to_dict("records")) if len(tr) else []
    report=dict(status="MODEL_1M_LIQUIDATION_AWARE_NOT_EXCHANGE_FILLED",
      starting_balance=START,margin_limit_per_trade=MARGIN_MAX,leverage=LEVERAGE,
      lot_size_btc=LOT,fee_taker_plus_gst=FEE,
      liquidation_penalty_plus_gst=LIQ_FEE,maintenance_margin=MM,
      one_shared_position=True,auto_margin_topup=False,
      target_source_event_counts=counts,total_source_events=len(events),
      historical_minutes=int(len(t)),final_account_equity=float(last_equity),
      net_profit=float(last_equity-START),trades_executed=int(len(tr)),
      wins=int((tr.pnl_after_fees>0).sum()) if len(tr) else 0,
      losses=int((tr.pnl_after_fees<0).sum()) if len(tr) else 0,
      liquidations=int(liquidations),
      skipped_busy=int(skipped_busy),skipped_funds=int(skipped_funds),
      skipped_min_lot=int(skipped_lot),
      profitable_months=int((mn.net_pnl>1e-9).sum()),
      losing_months=int((mn.net_pnl< -1e-9).sum()),
      flat_months=int((abs(mn.net_pnl)<=1e-9).sum()),
      entry_fees=float(fe_entry),exit_fees=float(fe_exit),
      liquidation_penalties=float(fe_liq),
      total_fees=float(fe_entry+fe_exit+fe_liq),
      worst_calendar_day=worst_day,worst_month=worst_month,
      maximum_daily_intraday_drawdown_pct=float(max_daily_dd),
      maximum_daily_drawdown_date=str(max_daily_dd_day),
      maximum_account_drawdown_pct=float(max_account_dd),
      maximum_account_drawdown_utc=(
        str(pd.Timestamp(max_account_dd_time,unit="s",tz="UTC"))
        if max_account_dd_time is not None else None),
      by_strategy=groups,has_position_at_cutoff=bool(position),
      limitations=[
       "Uses frozen independent source strategy event streams; post-liquidation re-entry signals are not regenerated",
       "Single BTCUSD position shared across three signal families; old 73.5/22.5/4 monthly NAV weights cannot be applied to one $10 fixed-margin position",
       "1m mark OHLC used for liquidation; exact intraminute chronology and liquidation execution price not available",
       "Conservatively charges ordinary exit taker fee AND liquidation penalty, each incl GST, when liquidation is triggered",
       "Liquidation recovery modeled at threshold or gap mark with 5 BTC price points adverse slip, not actual Delta IOC liquidation fills",
       "No historical funding cashflows or realistic spread/depth, orderqueue, INR conversion, or exchange ADL behavior",
       "No independent prospective validation of 2025–2026 hindsight-exposed signals"
       ])
    args.out.mkdir(parents=True,exist_ok=True)
    tr.to_csv(args.out/"trades.csv",index=False)
    dy.to_csv(args.out/"daily.csv",index=False)
    mn.to_csv(args.out/"monthly.csv",index=False)
    (args.out/"summary.json").write_text(json.dumps(report,indent=2,default=str)+"\n")
    print("FULL100X_RESULT "+json.dumps(report,default=str))
    print("FULL100X_MONTHLY\n"+mn.to_string(index=False))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--core",type=Path,required=True)
    p.add_argument("--donchian",type=Path,required=True)
    p.add_argument("--out",type=Path,
      default=Path("analysis/stage18_100x_liquidation_20261122"))
    run(p.parse_args())

# Repeatable push run after workflow registration; unchanged algorithm.
