#!/usr/bin/env python3
"""New independent BTC/ETH DAILY-NET test: UTC session-anchored VWAP
exhaustion/reversal, one trade per calendar day. Evaluates profitable-day
coverage rather than requiring 100% win days. STRICT 5m close -> next 1m open.
Pessimistic intraminute stop-first, standard Delta taker fees plus GST and
2bp slippage per side, and conservative 1bp funding debit per 8h crossing.
2025 used to pick parameters; 2026 evaluation is previously research-exposed
and is NOT a pristine holdout. Backtest is research, not a profit promise.
"""
from pathlib import Path
import json
import itertools
import numpy as np
import pandas as pd

DATA=Path("data/delta_india")
OUT=Path("analysis/daily_net_vwap_reversion_20261118")
OUT.mkdir(parents=True,exist_ok=True)
SYMBOLS=("BTCUSD","ETHUSD")
START="2025-01-01"
END="2026-11-18"
EQUITY0=1000.
RISK=.005
MAX_LEV=2.
FEE=.0005*1.18
SLIP=.0002
FUNDING_DEBIT=.0001
DEV=(.003,.005,.007)
TARG=(.0035,.005,.0075)
STOP=(.003,.005)
HOLD=(90,180)
VOL=(1.0,1.25)

def source(symbol):
    files=sorted((DATA/symbol/"1m").glob("20??-??.csv.gz"))
    if len(files)<22: raise RuntimeError("Missing historical monthly files: "+symbol)
    cols=["time","open","high","low","close","volume"]
    d=pd.concat((pd.read_csv(p,compression="gzip",usecols=cols) for p in files),ignore_index=True)
    lo=int(pd.Timestamp(START,tz="UTC").timestamp())
    hi=int(pd.Timestamp(END,tz="UTC").timestamp())
    d=d[(d.time>=lo)&(d.time<hi)].sort_values("time").reset_index(drop=True)
    t=d.time.to_numpy(dtype=np.int64)
    if len(t)<950000 or t[0]!=lo or t[-1]!=hi-60 or not np.all(np.diff(t)==60):
        raise ValueError(symbol+" missing minute or malformed UTC calendar")
    if not np.isfinite(d[cols].to_numpy(float)).all():
        raise ValueError(symbol+" nonfinite data")
    if (d.high<d.low).any() or (d.open<d.low).any() or (d.close<d.low).any() or (d.open>d.high).any() or (d.close>d.high).any():
        raise ValueError(symbol+" invalid OHLC")
    return d,{"symbol":symbol,"rows":len(d),"first_utc":str(pd.to_datetime(t[0],unit="s",utc=True)),
              "last_utc":str(pd.to_datetime(t[-1],unit="s",utc=True)),
              "source_files":len(files),"missing_minutes":0}

def events(d):
    index=pd.to_datetime(d.time,unit="s",utc=True)
    b=d.set_index(index)[["open","high","low","close","volume"]].resample(
        "5min",label="left",closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    bar_count=d.set_index(index)["close"].resample("5min").count()
    if len(b)*5!=len(d) or not bar_count.eq(5).all():
        raise ValueError("Unclosed 5-minute aggregation")
    day=b.index.floor("D")
    cum_dollars=(b.volume*(b.high+b.low+b.close)/3).groupby(day).cumsum()
    cum_volume=b.volume.groupby(day).cumsum().replace(0,np.nan)
    vwap=cum_dollars/cum_volume
    distance=(b.close/vwap-1).to_numpy(float)
    prev_red=(b.close.shift(1)<b.open.shift(1)).fillna(False)
    prev_green=(b.close.shift(1)>b.open.shift(1)).fillna(False)
    reverses_up=((b.close>b.open)&prev_red).to_numpy(bool)
    reverses_down=((b.close<b.open)&prev_green).to_numpy(bool)
    prior_vol=b.volume.shift(1).rolling(24,min_periods=24).median().replace(0,np.nan)
    vratio=(b.volume/prior_vol).to_numpy(float)
    # Completed 5-minute close after UTC 03:00, no new entries after 20:00.
    close_hour=(b.index.hour*60+b.index.minute+5).to_numpy()
    eligible=(close_hour>=180)&(close_hour<1200)&np.isfinite(distance)&np.isfinite(vratio)
    eligible&=(np.abs(distance)>=min(DEV))&(vratio>=min(VOL))
    sides=np.where((distance<0)&reverses_up,1,np.where((distance>0)&reverses_down,-1,0))
    eligible&=(sides!=0)
    byday={}
    for j in np.flatnonzero(eligible):
        day_id=int(j//288)
        k=int((j+1)*5) # next 1-minute open, after completed 5m signal
        byday.setdefault(day_id,[]).append((k,int(sides[j]),float(abs(distance[j])),float(vratio[j])))
    return byday,{"closed_5m_bars":len(b),"base_signal_count":int(eligible.sum()),"calendar_days":int(len(b)//288)}

def trade(d,t,o,h,l,c,k,side,eq,tp,sl,hold):
    entry=o[k]*(1+side*SLIP)
    qty=min(eq*RISK/(sl*entry),eq*MAX_LEV/entry)
    stop=entry*(1-side*sl)
    target=entry*(1+side*tp)
    end=min(k+hold,((k//1440)+1)*1440)
    reason="time"
    exit_index=end-1
    exit_px=float(c[exit_index])
    for j in range(k,end):
        if side==1:
            stop_hit=l[j]<=stop
            target_hit=h[j]>=target
            if stop_hit:
                exit_index=j;exit_px=min(float(o[j]),stop);reason="stop";break
            if target_hit:
                exit_index=j;exit_px=target;reason="target";break
        else:
            stop_hit=h[j]>=stop
            target_hit=l[j]<=target
            if stop_hit:
                exit_index=j;exit_px=max(float(o[j]),stop);reason="stop";break
            if target_hit:
                exit_index=j;exit_px=target;reason="target";break
    exit_fill=exit_px*(1-side*SLIP)
    gross=side*qty*(exit_fill-entry)
    fees=FEE*qty*(entry+exit_fill)
    settlements=sum(1 for j in range(k,exit_index+1) if t[j]%28800==0)
    funding=settlements*FUNDING_DEBIT*qty*exit_fill
    net=gross-fees-funding
    return net,fees,funding,reason,exit_index-k+1,entry,exit_fill

def replay(d,byday,config):
    dev,tp,sl,hold,vol=config
    t=d.time.to_numpy(dtype=np.int64)
    o=d.open.to_numpy(float);h=d.high.to_numpy(float)
    l=d.low.to_numpy(float);c=d.close.to_numpy(float)
    eq=EQUITY0;days=[];trades=[]
    n_days=len(d)//1440
    for day_id in range(n_days):
        before=eq;ev=None
        for candidate in byday.get(day_id,()):
            if candidate[2]>=dev and candidate[3]>=vol:
                ev=candidate;break
        day=pd.to_datetime(int(t[day_id*1440]),unit="s",utc=True).strftime("%Y-%m-%d")
        if ev is not None:
            k,side,dist,vr=ev
            net,fees,funding,reason,mins,entry,ex=trade(d,t,o,h,l,c,k,side,eq,tp,sl,hold)
            eq+=net
            trades.append(dict(day=day,side="LONG" if side>0 else "SHORT",
                entry_utc=int(t[k]),exit_utc=int(t[k+mins-1]),entry=entry,exit=ex,
                vwap_deviation_pct=100*dist,volume_ratio=vr,net_usd=net,
                fees_usd=fees,funding_debit_usd=funding,exit_reason=reason))
        else:
            net=0.;fees=0.;funding=0.
        days.append(dict(day=day,year=int(day[:4]),month=day[:7],
            day_net_usd=net,equity_start=before,equity_end=eq,fees_usd=fees,
            funding_debit_usd=funding,trade=int(ev is not None)))
    return pd.DataFrame(days),pd.DataFrame(trades)

def summarize(daily,symbol,config,year):
    g=daily[daily.year==year]
    pnl=g.day_net_usd.to_numpy()
    profits=pnl[pnl>1e-8];losses=pnl[pnl<-1e-8]
    prev=float(g.equity_start.iloc[0]);last=float(g.equity_end.iloc[-1])
    equity=np.r_[prev,g.equity_end.to_numpy(float)]
    peak=np.maximum.accumulate(equity)
    pf=float(profits.sum()/-losses.sum()) if len(losses) else None
    dev,tp,sl,hold,vol=config
    streak=0;max_streak=0
    for p in pnl:
        streak=streak+1 if p<-1e-8 else 0
        max_streak=max(max_streak,streak)
    return dict(symbol=symbol,year=year,dev=dev,tp=tp,sl=sl,hold_min=hold,
        volume_ratio_min=vol,trades=int(g.trade.sum()),days=len(g),
        profit_days=len(profits),loss_days=len(losses),no_trade_days=int((g.trade==0).sum()),
        positive_calendar_day_pct=round(100*len(profits)/len(g),3),
        win_rate_traded_pct=round(100*len(profits)/(len(profits)+len(losses)),3) if (len(profits)+len(losses)) else None,
        profit_factor=round(pf,4) if pf is not None else None,
        net_return_pct=round(100*(last/prev-1),4),
        net_profit_usd=round(last-prev,4),
        avg_calendar_day_usd=round(float(pnl.mean()),4),
        fees_usd=round(float(g.fees_usd.sum()),4),
        assumed_funding_usd=round(float(g.funding_debit_usd.sum()),4),
        worst_day_usd=round(float(pnl.min()),4),
        max_consecutive_losing_days=max_streak,
        max_close_day_drawdown_pct=round(100*float(np.min(equity/peak-1)),4))

def main():
    summaries=[];quality=[];selected=[];selected_month=[];selected_days=[]
    for symbol in SYMBOLS:
        print("LOAD",symbol,flush=True)
        d,q=source(symbol)
        events_by_day,sigquality=events(d)
        quality.append({**q,**sigquality})
        cached={}
        configs=list(itertools.product(DEV,TARG,STOP,HOLD,VOL))
        for config in configs:
            daily,trades=replay(d,events_by_day,config)
            year25=summarize(daily,symbol,config,2025)
            year26=summarize(daily,symbol,config,2026)
            summaries.extend((year25,year26))
            cached[config]=daily
        x=pd.DataFrame([r for r in summaries if r["symbol"]==symbol and r["year"]==2025])
        # Selection based only on 2025 history. 2026 remains a check,
        # not a truly unseen holdout (prior research exposure).
        eligible=x[(x.trades>=30)&(x.profit_factor.fillna(0)>1.)&(x.net_return_pct>0)]
        if len(eligible):
            best=eligible.sort_values(["positive_calendar_day_pct","net_return_pct"],
                                      ascending=False).iloc[0]
            passes=True
        else:
            best=x.sort_values(["net_return_pct","positive_calendar_day_pct"],
                               ascending=False).iloc[0]
            passes=False
        config=(float(best.dev),float(best.tp),float(best.sl),int(best.hold_min),float(best.volume_ratio_min))
        selected.extend([dict(r,train_criteria_pass=passes) for r in summaries
                         if r["symbol"]==symbol and (r["dev"],r["tp"],r["sl"],r["hold_min"],r["volume_ratio_min"])==config])
        daily=cached[config].copy();daily["symbol"]=symbol
        selected_days.append(daily)
        for month,g in daily.groupby("month",sort=True):
            p=float(g.equity_start.iloc[0]);last=float(g.equity_end.iloc[-1])
            selected_month.append(dict(symbol=symbol,month_utc=month,
                net_return_pct=round(100*(last/p-1),4),
                trades=int(g.trade.sum()),
                profitable_days=int((g.day_net_usd>1e-8).sum()),
                losing_days=int((g.day_net_usd<-1e-8).sum()),
                fees_usd=round(float(g.fees_usd.sum()),4)))
        print("SELECTED",symbol,config,"2025 eligible",passes,"2026",
              next(x for x in selected if x["symbol"]==symbol and x["year"]==2026),flush=True)
    pd.DataFrame(summaries).to_csv(OUT/"summary.csv",index=False)
    pd.DataFrame(selected).to_csv(OUT/"selected.csv",index=False)
    pd.DataFrame(selected_month).to_csv(OUT/"selected_monthly.csv",index=False)
    pd.concat(selected_days).to_csv(OUT/"selected_daily.csv.gz",index=False,compression="gzip")
    meta=dict(study="UTC-session anchored VWAP exhaustion two-candle reversal",
        parameters=dict(deviation=DEV,target=TARG,stop=STOP,hold_minutes=HOLD,
                        volume_ratio=VOL,models_per_symbol=len(configs)),
        entry="Completed 5-minute candle opposite prior candle, close beyond session VWAP deviation; next 1-minute open",
        exit="Fixed percentage target or stop, stop first when ambiguous; time cap; no overnight trades",
        sizing="Risk 0.5% of equity to nominal stop, notional capped at 2x account equity, at most one trade per UTC day",
        fee="0.05% taker per entry and exit plus 18% GST, 2bp per-side adverse fill slippage",
        funding="Assumed 1bp debit per funding boundary crossed; not actual settled cashflow",
        caveats=["Not every day has a signal; no forced trades",
                 "2026 previously viewed, not a genuine forward holdout",
                 "No order book, spread model, exact intraminute sequence or exchange lot constraints",
                 "Liquidation and margin risk not simulated",
                 "Per-day drawdown uses day-close NAV, not intraday high water",
                 "2026 November only partial through 17 November UTC"],
        data=quality,selection="2025 positive return+PF>1 and >=30 trades; rank highest calendar profit-day frequency; test 2026 unchanged")
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
    report=["# Independent daily net-profit strategy research","",
       "Hypothesis: small mean-reversion moves around UTC day-anchored VWAP, after exhaustion and a 5m reversal candle.",
       "","Selection uses only 2025. 2026 research-exposed historical check, not a live-forward validation.","",
       "## Selected models — 2025 and 2026",pd.DataFrame(selected).to_markdown(index=False) if False else pd.DataFrame(selected).to_string(index=False),
       "","## Interpretation","A winning backtest cannot guarantee daily net profit. No-trade days count against calendar-day coverage.",
       "","## Caveats"]+[f"- {v}" for v in meta["caveats"]]
    (OUT/"REPORT.md").write_text("\n".join(report)+"\n")
    print("DONE",len(summaries),"year rows",flush=True)
if __name__=="__main__":main()
