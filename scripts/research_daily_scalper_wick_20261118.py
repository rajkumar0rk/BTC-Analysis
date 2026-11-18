#!/usr/bin/env python3
"""1-minute volatility wick and rejection microstructure study for daily-profit
coverage, BTCUSD and ETHUSD Delta India futures, 2025-01-01 to 2026-11-17.
Causal: signal on completed 1m candle; next minute OPEN is entry; stop first
for ambiguous OHLC. One trade per UTC calendar day, no overnight.
STANDARD fee: taker 0.05% each side * 1.18 GST. Hypothetical 30-min
Scalper Offer scenario: closing fee zero only if opted-in and offer active.
The offer fee scenario is counterfactual for earlier historical dates.
Adverse slippage 2bp EACH side; funding charged pessimistic 1bp per 8h
boundary. 2026 has research exposure and isn't untouched holdout.
"""
from pathlib import Path
import json
import itertools
import numpy as np
import pandas as pd

BASE=Path("data/delta_india")
OUT=Path("analysis/daily_scalper_wick_20261118")
OUT.mkdir(parents=True,exist_ok=True)
START=pd.Timestamp("2025-01-01",tz="UTC")
END=pd.Timestamp("2026-11-18",tz="UTC")
SYMBOLS=("BTCUSD","ETHUSD")
CAPITAL=1000.;RISK=.005;LEV=2.;FEE=.0005*1.18;SLIP=.0002;FUND_DEBIT=.0001
TP=(.0025,.004,.006);SL=(.0025,.0045);HOLD=(15,30)
PATS=("wick","sweep","confirm","impulse")
SESSIONS=("all","utc_00_08","utc_12_20")
COSTS=("standard","offer_counterfactual")

def load(sym):
    paths=sorted((BASE/sym/"1m").glob("20??-??.csv.gz"))
    if len(paths)<22:raise RuntimeError("Insufficient source files for "+sym)
    cols=["time","open","high","low","close","volume"]
    d=pd.concat((pd.read_csv(p,compression="gzip",usecols=cols) for p in paths),ignore_index=True)
    d=d[(d.time>=int(START.timestamp()))&(d.time<int(END.timestamp()))].sort_values("time").reset_index(drop=True)
    tt=d.time.to_numpy(dtype=np.int64)
    if len(tt)%1440 or len(tt)<950000 or tt[0]!=START.timestamp() or tt[-1]!=END.timestamp()-60 or not np.all(np.diff(tt)==60):
        raise ValueError(sym+" has missing minutes or partial UTC day")
    if not np.isfinite(d[cols].to_numpy(float)).all():raise ValueError("Nonfinite source")
    if (d.high<d.low).any() or (d.open<d.low).any() or (d.close<d.low).any() or (d.open>d.high).any() or (d.close>d.high).any():
        raise ValueError("Invalid OHLCV")
    return d,{"symbol":sym,"minute_bars":len(d),"first_utc":str(START),"last_utc":str(END-pd.Timedelta(minutes=1)),"missing_minutes":0,"source_files":len(paths)}

def signals(d):
    o=d.open.to_numpy(float);h=d.high.to_numpy(float);l=d.low.to_numpy(float);c=d.close.to_numpy(float);v=d.volume.to_numpy(float)
    span=h-l
    q=pd.Series(span).shift(1).rolling(60,min_periods=60).median().to_numpy()
    vs=pd.Series(v).shift(1).rolling(60,min_periods=60).median().to_numpy()
    rh=pd.Series(h).shift(1).rolling(60,min_periods=60).max().to_numpy()
    rl=pd.Series(l).shift(1).rolling(60,min_periods=60).min().to_numpy()
    ratio=span/np.where(span>0,span,np.nan)
    lw=(np.minimum(o,c)-l)/np.where(span>0,span,np.nan)
    uw=(h-np.maximum(o,c))/np.where(span>0,span,np.nan)
    body=np.abs(c-o)/np.where(span>0,span,np.nan)
    liquid=(span>=1.75*q)&(v>=1.5*vs)&(vs>0)&np.isfinite(q)
    lwok=liquid&(lw>=.55)&((c-l)/np.where(span>0,span,np.nan)>=.65)
    uwok=liquid&(uw>=.55)&((c-l)/np.where(span>0,span,np.nan)<=.35)
    sweep_long=lwok&(l<rl)&(c>rl)
    sweep_short=uwok&(h>rh)&(c<rh)
    # Confirmation is defined on a NEW fully finished minute after prior wick.
    confirm_long=np.zeros(len(d),bool)
    confirm_short=np.zeros(len(d),bool)
    confirm_long[1:]=lwok[:-1]&(c[1:]>c[:-1])&(c[1:]>o[1:])
    confirm_short[1:]=uwok[:-1]&(c[1:]<c[:-1])&(c[1:]<o[1:])
    impact=liquid&(body>=.70)
    imp_long=impact&(c>rh)&(c>o)
    imp_short=impact&(c<rl)&(c<o)
    patterns={
      "wick":(lwok,uwok),
      "sweep":(sweep_long,sweep_short),
      "confirm":(confirm_long,confirm_short),
      "impulse":(imp_long,imp_short)}
    out={};counts={}
    for pat,(bu,be) in patterns.items():
        side=np.where(bu,1,np.where(be,-1,0))
        indices=np.flatnonzero(side)
        byday={}
        for j in indices:
            k=int(j+1);mod=k%1440
            # Enter on next minute, leave enough time to flatten before UTC day end.
            if k>=len(d) or mod<60 or mod>1410:continue
            byday.setdefault(k//1440,[]).append((k,int(side[j])))
        out[pat]=byday;counts[pat]=sum(len(x) for x in byday.values())
    return out,counts

def simulate(day_id,events,config,prices,capital):
    pat,session,tp,sl,hold,cost=config
    k=None;side=None
    for at,sd in events.get(day_id,()):
        mod=at%1440
        if session=="utc_00_08" and mod>=480:continue
        if session=="utc_12_20" and not(720<=mod<1200):continue
        k=at;side=sd;break
    if k is None:return 0.,0.,0.,False
    o,h,l,c,t=prices
    entry=float(o[k])*(1+side*SLIP)
    qty=min(capital*RISK/(entry*sl),capital*LEV/entry)
    target=entry*(1+side*tp);stop=entry*(1-side*sl)
    end=min(k+hold,((k//1440)+1)*1440)
    exitindex=end-1;px=float(c[exitindex])
    for j in range(k,end):
        if side==1:
            if l[j]<=stop:
                px=min(float(o[j]),stop);exitindex=j;break
            if h[j]>=target:
                px=target;exitindex=j;break
        else:
            if h[j]>=stop:
                px=max(float(o[j]),stop);exitindex=j;break
            if l[j]<=target:
                px=target;exitindex=j;break
    exitfill=px*(1-side*SLIP)
    entryfee=FEE*qty*entry
    exitfee=0. if cost=="offer_counterfactual" else FEE*qty*exitfill
    funding=FUND_DEBIT*qty*exitfill*sum(1 for j in range(k,exitindex+1) if t[j]%28800==0)
    net=qty*side*(exitfill-entry)-entryfee-exitfee-funding
    return net,entryfee+exitfee,funding,True

def run_one(d,events,config,dates,prices):
    cap=CAPITAL
    rec=[]
    for day_id,day in enumerate(dates):
        prev=cap
        pnl,fees,funding,traded=simulate(day_id,events[config[0]],config,prices,cap)
        cap+=pnl
        rec.append((str(day)[:10],int(day.year),pnl,prev,cap,traded,fees,funding))
    return pd.DataFrame(rec,columns=["day","year","pnl","equity_start","equity_end","traded","fees","funding"])

def report_year(sym,config,r,year):
    x=r[r.year==year]
    wins=x.pnl.to_numpy()[x.pnl.to_numpy()>1e-8]
    losses=x.pnl.to_numpy()[x.pnl.to_numpy()<-1e-8]
    start=float(x.equity_start.iloc[0]);end=float(x.equity_end.iloc[-1])
    pf=(wins.sum()/-losses.sum()) if len(losses) else None
    nav=np.r_[start,x.equity_end.to_numpy()]
    dd=100*np.min(nav/np.maximum.accumulate(nav)-1)
    pat,sess,tp,sl,hold,cost=config
    return dict(symbol=sym,year=year,pattern=pat,session=sess,tp=tp,sl=sl,
        hold_min=hold,cost=cost,net_return_pct=round(100*(end/start-1),4),
        trades=int(x.traded.sum()),profitable_days=len(wins),losing_days=len(losses),
        no_trade_days=int((~x.traded).sum()),
        profitable_calendar_days_pct=round(100*len(wins)/len(x),3),
        win_rate_traded_pct=round(100*len(wins)/(len(wins)+len(losses)),3) if len(wins)+len(losses) else None,
        profit_factor=round(float(pf),4) if pf is not None else None,
        fees_usd=round(float(x.fees.sum()),3),
        funding_debit_usd=round(float(x.funding.sum()),3),
        max_dayclose_drawdown_pct=round(dd,3))

def main():
    results=[];selected=[];quality=[]
    cfgs=list(itertools.product(PATS,SESSIONS,TP,SL,HOLD,COSTS))
    dates=pd.date_range(START,END-pd.Timedelta(days=1),freq="D")
    for sym in SYMBOLS:
        print("LOAD",sym,flush=True)
        d,q=load(sym)
        evs,counts=signals(d)
        quality.append({**q,"signal_counts":counts,"tested_models":len(cfgs)})
        prices=(d.open.to_numpy(float),d.high.to_numpy(float),d.low.to_numpy(float),
                d.close.to_numpy(float),d.time.to_numpy(np.int64))
        train=[];cache={}
        for i,config in enumerate(cfgs):
            daily=run_one(d,evs,config,dates,prices)
            results.append(report_year(sym,config,daily,2025))
            results.append(report_year(sym,config,daily,2026))
            train.append(results[-2])
            if i%50==0:print("DONE",sym,i,"of",len(cfgs),flush=True)
        x=pd.DataFrame(train)
        viable=x[(x.trades>=50)&(x.profit_factor.fillna(0)>1)&(x.net_return_pct>0)]
        passed=bool(len(viable))
        choices=viable if passed else x
        best=choices.sort_values(["profitable_calendar_days_pct","net_return_pct"],
                                 ascending=False).iloc[0] if passed else choices.sort_values(
                                 ["net_return_pct","profitable_calendar_days_pct"],ascending=False).iloc[0]
        config=(str(best.pattern),str(best.session),float(best.tp),float(best.sl),int(best.hold_min),str(best.cost))
        rows=[x for x in results if x["symbol"]==sym and (x["pattern"],x["session"],x["tp"],x["sl"],x["hold_min"],x["cost"])==config]
        selected.extend([dict(x,passes_2025_minimum=passed) for x in rows])
        print("SELECTED",sym,config,passed,rows,flush=True)
    pd.DataFrame(results).to_csv(OUT/"summary.csv",index=False)
    pd.DataFrame(selected).to_csv(OUT/"selected.csv",index=False)
    qual=dict(data=quality,models_per_symbol=len(cfgs),date_start=str(START),
        date_end_exclusive=str(END),selection_rule="Choose 2025 trade count >=50, PF>1 and net profit >0, then maximize profitable calendar days; replay unchanged 2026",
        trading_costs={"standard_taker_entry_exit":FEE,"scalper_counterfactual_entry":FEE,
                       "scalper_counterfactual_exit":0.,"slippage_each_fill":SLIP,
                       "funding_8h_crossing_debit":FUND_DEBIT},
        caveats=["No strategy guaranteed positive daily net PnL",
            "Offer scenario assumes opt-in and eligible 30m close; NOT valid historical offer availability for all 2025",
            "2026 previously research exposed, cannot claim untouched holdout",
            "1m candle cannot resolve order book liquidity or intrabar sequences; stop-first ambiguity",
            "Funding proxy, leverage/margin/lots and slippage are approximations",
            "Profit day count includes no-trade days as zero, not profit",
            "2026 through November 17 UTC, not full year"])
    (OUT/"quality.json").write_text(json.dumps(qual,indent=2)+"\n")
    (OUT/"REPORT.md").write_text("# Independent short-window daily scalping research\n\n"+
          "Train-ranked on 2025 only; 2026 is research-exposed historical replay.\n\n"+
          "## Selected models\n\n"+pd.DataFrame(selected).to_string(index=False)+"\n\n"+
          "## Assumptions\n\n"+json.dumps(qual,indent=2)+"\n")
    print("FINISHED",len(results),"rows",flush=True)
if __name__=="__main__": main()
