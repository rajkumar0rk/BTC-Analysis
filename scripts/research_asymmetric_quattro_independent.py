#!/usr/bin/env python3
"""Independent Quattro-style 4H long breakout on Delta India BTCUSD and ETHUSD 1m data.

This is a NEW self-contained study, not the external author's engine or his results.
Signals: completed 4H close above prior 20-bar high, with previous completed daily
EMA200 below signal close. Enter on next 4H open. Four-unit pyramid, each +0.5N,
N=Wilder 4H ATR14 frozen on first entry. Shared stop newest fill -2N,
10-bar Donchian-close exit next 4H open, gross catastrophe stop -5% initial
trade equity, 20x notional ceiling. One LONG only. Costs: 0.05% taker per
fill +18% GST on trading fee, 2bp adverse slippage per fill. Historical 1h
Delta FUNDING candles are only a PROXY (not cash settlement records); settle
at 00/08/16 UTC using previous hour close; charge 0.01% to long when absent
rather than falsely assuming free funding. Entries require 200 FULL previous
daily candles: Jan-Jul 2025 is EMA warmup, not a tested period.
No stop/entry use of an unclosed 4H or daily candle. Within a 1m bar,
stops take priority over pyramid adds; if added and new stop would also be
hit within the same minute, pessimistically exit. Equity monthly marked IST.
"""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path("data/delta_india")
OUT = Path("analysis/asymmetric_quattro_independent_20261118")
SYMBOLS = ("BTCUSD","ETHUSD")
INITIAL = 1000.0
UNIT_RISK_VARIANTS = (0.005,0.02) # conservative and externally published 2% unit risk
MAX_LEVERAGE=20.0
TAKER_WITH_GST = 0.0005 * 1.18
SLIP_BPS = 0.0002
HARD_PCT = 0.05
DEFAULT_MISSING_FUNDING = 0.0001  # charge 0.01% in missing 8h slots; sensitivity needed
START = pd.Timestamp("2025-01-01",tz="UTC")
END_EXCLUSIVE = pd.Timestamp("2026-11-18",tz="UTC")

def read_candles(symbol):
    files=sorted((ROOT/symbol/"1m").glob("20??-??.csv.gz"))
    if len(files)<22:
        raise RuntimeError(f"{symbol}: fewer than 22 monthly archives")
    d=pd.concat([pd.read_csv(p,compression="gzip",usecols=[
        "time","open","high","low","close","volume"]) for p in files],ignore_index=True)
    d=d.sort_values("time",kind="stable").reset_index(drop=True)
    d=d[(d.time>=int(START.timestamp()))&(d.time<int(END_EXCLUSIVE.timestamp()))]
    t=d.time.to_numpy(np.int64)
    if len(d)<900000 or (np.diff(t)<=0).any() or (np.diff(t)%60!=0).any():
        raise RuntimeError(f"{symbol}: invalid time order, resolution or insufficient data")
    for c in ("open","high","low","close","volume"):
        if not np.isfinite(d[c].to_numpy(float)).all():
            raise RuntimeError(f"{symbol}: nonfinite {c}")
    if ((d.low<=0)|(d.high<d.low)|(d.open<d.low)|(d.open>d.high)|
        (d.close<d.low)|(d.close>d.high)).any():
        raise RuntimeError(f"{symbol}: impossible OHLC")
    d.index=pd.to_datetime(d.time,unit="s",utc=True)
    gap=np.flatnonzero(np.diff(t)!=60)
    quality=dict(symbol=symbol,candle_count=len(d),first=str(d.index[0]),
        last=str(d.index[-1]),missing_minutes=int((t[-1]-t[0])//60+1-len(t)),
        gap_count=len(gap),gap_samples=[dict(from_utc=str(d.index[i]),
        to_utc=str(d.index[i+1]),minutes=int((t[i+1]-t[i])//60-1))
        for i in gap[:8]])
    return d,quality

def funding_proxy(symbol):
    files=sorted((ROOT/symbol/"institutional/history/funding_1h").glob("20??-??.csv.gz"))
    if not files: return {},0
    f=pd.concat([pd.read_csv(p,compression="gzip",usecols=["time","close"])
                 for p in files],ignore_index=True)
    f=f.drop_duplicates("time",keep="last")
    # Read Delta close as percentage, e.g. 0.01 = 0.01% = 0.0001.
    r={}
    for t,v in zip(f.time.to_numpy(np.int64), f.close.to_numpy(float)):
        if np.isfinite(v) and abs(v)<=5:
            r[int(t)+3600]=float(v)/100
    return r,len(f)

def build_signals(d):
    x=d[["open","high","low","close"]]
    b=x.resample("4h",closed="left",label="left").agg({
        "open":"first","high":"max","low":"min","close":"last"})
    count=x.close.resample("4h",closed="left",label="left").count()
    complete=count.eq(240)
    prev20_ok=complete.shift(1).rolling(20,min_periods=20).sum().eq(20)
    prev10_ok=complete.shift(1).rolling(10,min_periods=10).sum().eq(10)
    upper=b.high.shift(1).rolling(20,min_periods=20).max()
    lower=b.low.shift(1).rolling(10,min_periods=10).min()
    prev=b.close.shift(1)
    tr=pd.concat([b.high-b.low,(b.high-prev).abs(),
        (b.low-prev).abs()],axis=1).max(axis=1)
    b["atr"]=tr.ewm(alpha=1/14,adjust=False).mean()
    atr_ok=complete.rolling(14,min_periods=14).sum().eq(14)
    day=x.resample("1D",closed="left",label="right").agg({"close":"last"})
    daycount=x.close.resample("1D",closed="left",label="right").count()
    day_ok=daycount.eq(1440)
    day["ema200"]=day.close.ewm(span=200,adjust=False,min_periods=200).mean()
    day["history_ok"]=day_ok.rolling(200,min_periods=200).sum().eq(200)
    # Daily rows indexed at the time the day CLOSED (00:00 next UTC day).
    bar_end=b.index+pd.Timedelta(hours=4)
    daily_ema=day.ema200.reindex(bar_end,method="ffill").to_numpy()
    history=day.history_ok.reindex(bar_end,method="ffill").fillna(False).to_numpy(bool)
    valid=complete.to_numpy(bool)&prev20_ok.to_numpy(bool)&atr_ok.to_numpy(bool)&history
    entry=valid&(b.close.to_numpy()>upper.to_numpy())&(b.close.to_numpy()>daily_ema)
    exit_=complete.to_numpy(bool)&prev10_ok.to_numpy(bool)&(b.close.to_numpy()<lower.to_numpy())
    t=d.time.to_numpy(np.int64)
    entry_at=np.full(len(d),np.nan,np.float64)
    exit_at=np.zeros(len(d),dtype=np.bool_)
    candidate_count=int(entry.sum())
    for j,ok in enumerate(entry):
        if not ok:continue
        ts=int(bar_end[j].timestamp())
        i=int(np.searchsorted(t,ts))
        if i<len(t) and t[i]==ts:
            entry_at[i]=float(b.atr.iloc[j])
    for j,ok in enumerate(exit_):
        if not ok:continue
        ts=int(bar_end[j].timestamp())
        i=int(np.searchsorted(t,ts))
        if i<len(t) and t[i]==ts:
            exit_at[i]=True
    return entry_at,exit_at,{"signal_count":candidate_count,
        "first_valid_daily_ema_utc":str(day[day.history_ok].index.min()),
        "complete_4h_bars":int(complete.sum()),"missing_4h_bars":int((~complete).sum()),
        "daily_ema_history_requirement":"200 complete daily closes; first 200 days warmup",
        "signal_rules":"completed 4h close > prior 20 high and > latest completed daily EMA200",
        "exit_rules":"4h close < prior 10 low, filled next 4h open, or wick stop"}

def run(d,entry_at,exit_at,funding,risk):
    T=d.time.to_numpy(np.int64)
    O=d.open.to_numpy(float);H=d.high.to_numpy(float)
    L=d.low.to_numpy(float);C=d.close.to_numpy(float)
    bounds=pd.date_range("2025-01-01","2026-12-01",freq="MS",tz="Asia/Kolkata").tz_convert("UTC")
    bound_unix=np.asarray([int(x.timestamp()) for x in bounds],np.int64)
    codes=np.searchsorted(bound_unix,T,side="right")-1
    months=bounds.tz_convert("Asia/Kolkata").strftime("%Y-%m").tolist()[:-1]
    cash=INITIAL; units=[]; qty=0.0; weighted=0.0
    first_fill=0.0;N=0.0;stop=0.0;entry_acct=0.0;unit_risk=0.0
    first_index=0;entry_count=0;month_active=np.zeros(len(months),np.bool_)
    monthly_marks=np.full(len(months),np.nan);month_entries=np.zeros(len(months),np.int32)
    trades=[];total_fees=0.0;total_funding=0.0;unknown_fund=0
    cash_at_trade_start=0.0;trade_fees=0.0;trade_funding=0.0
    peak=INITIAL;min_dd=0.0;unit_hist={}
    gap_exits=0;pessimistic_same_minute=0
    def add(fill,sz,i):
        nonlocal cash,qty,weighted,total_fees,trade_fees,stop
        f=TAKER_WITH_GST*fill*sz
        cash-=f;trade_fees+=f;total_fees+=f
        weighted=(weighted*qty+fill*sz)/(qty+sz)
        qty+=sz;units.append((fill,sz))
        stop=max(stop,fill-2*N)
    def mark(px):
        if qty==0:return cash
        exit_fill=px*(1-SLIP_BPS)
        return cash+(exit_fill-weighted)*qty-TAKER_WITH_GST*exit_fill*qty
    def close(px,reason,i):
        nonlocal cash,qty,weighted,units,total_fees,trade_fees,trade_funding
        nonlocal total_funding,stop,entry_acct,first_fill,N,entry_count,gap_exits
        final_fill=px*(1-SLIP_BPS)
        gross=(final_fill-weighted)*qty
        fee=TAKER_WITH_GST*final_fill*qty
        cash+=gross-fee;total_fees+=fee;trade_fees+=fee
        net=cash-cash_at_trade_start
        trades.append(dict(entry_utc=str(pd.to_datetime(T[first_index],unit="s",utc=True)),
            exit_utc=str(pd.to_datetime(T[i],unit="s",utc=True)),
            entry_month_ist=str(pd.to_datetime(T[first_index],unit="s",utc=True).tz_convert("Asia/Kolkata").strftime("%Y-%m")),
            units=len(units),first_entry=round(first_fill,5),last_fill=round(final_fill,5),
            original_atr=round(N,5),gross_price_pnl=round(gross,5),
            fees_usd=round(trade_fees,5),funding_usd=round(trade_funding,5),
            net_usd=round(net,5),net_R=round(net/unit_risk,5),
            account_after=round(cash,5),exit_reason=reason,
            held_hours=round((T[i]-T[first_index])/3600,2)))
        unit_hist[len(units)]=unit_hist.get(len(units),0)+1
        if reason=="data_gap":gap_exits+=1
        qty=0.0;weighted=0.0;units=[];stop=0.0;entry_acct=0.0
        N=0.0;first_fill=0.0;entry_count=0
    for i in range(len(T)):
        if i>0 and T[i]-T[i-1]!=60 and qty:
            close(O[i],"data_gap",i)
        if exit_at[i] and qty:
            close(O[i],"donchian_10_exit",i)
        if np.isfinite(entry_at[i]) and qty==0 and cash>0:
            n=float(entry_at[i]);r=cash*risk;sz=r/(2*n)
            fill=O[i]*(1+SLIP_BPS)
            if sz*fill<=cash*MAX_LEVERAGE and n>0:
                entry_acct=cash;cash_at_trade_start=cash;first_index=i
                N=n;first_fill=fill;unit_risk=r;stop=fill-2*n
                trade_fees=0.0;trade_funding=0.0
                add(fill,sz,i);month_entries[codes[i]]+=1;entry_count+=1
        if qty:
            month_active[codes[i]]=True
            if T[i]%28800==0: # funding settlements proxy, UTC 00/08/16
                rate=funding.get(int(T[i]))
                if rate is None:
                    rate=DEFAULT_MISSING_FUNDING
                    unknown_fund+=1
                charge=qty*O[i]*rate
                cash-=charge;trade_funding+=charge;total_funding+=charge
            hard=weighted-HARD_PCT*entry_acct/qty
            level=max(stop,hard)
            if L[i]<=level:
                close(min(O[i],level),"hard_5pct" if hard>=stop else "unit_stop",i)
            else:
                while qty and len(units)<4:
                    trigger=first_fill+0.5*len(units)*N
                    if H[i]<trigger:break
                    fill=max(O[i],trigger)*(1+SLIP_BPS)
                    sz=unit_risk/(2*N)
                    if (qty+sz)*fill>max(cash,1)*MAX_LEVERAGE:break
                    prior_stop=stop
                    add(fill,sz,i)
                    # 1m OHLC cannot prove low occurred before or after the add.
                    # If tightened stop and low both happen, worst case exit.
                    hard=weighted-HARD_PCT*entry_acct/qty
                    new_level=max(stop,hard)
                    if L[i]<=new_level:
                        pessimistic_same_minute+=1
                        close(min(O[i],new_level),"ambiguous_1m_stop",i)
                        break
        if qty:
            mm=mark(C[i])
        else:mm=cash
        if mm>peak:peak=mm
        if peak>0:min_dd=min(min_dd,mm/peak-1)
        if i==len(T)-1 or codes[i+1]!=codes[i]:
            if codes[i]>=0 and codes[i]<len(months):
                monthly_marks[codes[i]]=mm
    if qty:
        close(C[-1],"end_of_data",len(T)-1)
        monthly_marks[codes[-1]]=cash
    ret=[];prev=INITIAL
    for j,mon in enumerate(months):
        e=float(monthly_marks[j])
        if not np.isfinite(e):
            continue
        ret.append(dict(symbol="",risk_per_unit=risk,month_ist=mon,
            net_return_pct=round((e/prev-1)*100,4),
            start_equity=round(prev,4),end_equity=round(e,4),
            entries=int(month_entries[j]),exposure=bool(month_active[j]),
            month_status="profit" if e>prev+1e-8 else "loss" if e<prev-1e-8 else "flat"))
        prev=e
    w=[a["net_usd"] for a in trades if a["net_usd"]>0]
    l=[a["net_usd"] for a in trades if a["net_usd"]<0]
    summ=dict(unit_risk=risk,starting_equity=INITIAL,final_equity=round(cash,4),
        net_return_pct=round((cash/INITIAL-1)*100,4),trades=len(trades),
        win_rate_pct=round(len(w)/len(trades)*100,3) if trades else None,
        profit_factor=round(sum(w)/-sum(l),4) if l else None,
        average_win_usd=round(np.mean(w),4) if w else None,
        average_loss_usd=round(np.mean(l),4) if l else None,
        biggest_winner_R=round(max((a["net_R"] for a in trades),default=0),3),
        max_mark_to_market_drawdown_pct=round(min_dd*100,3),
        entry_fees_plus_exit_fees_usd=round(total_fees,3),
        funding_proxy_usd=round(total_funding,3),missing_funding_settlement_count=unknown_fund,
        data_gap_exits=gap_exits,pessimistic_same_minute_exits=pessimistic_same_minute,
        pyramid_units_distribution=unit_hist,
        positive_months=sum(a["month_status"]=="profit" for a in ret),
        negative_months=sum(a["month_status"]=="loss" for a in ret),
        flat_months=sum(a["month_status"]=="flat" for a in ret))
    return summ,ret,trades

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    summaries=[];months=[];trades=[];q=[]
    for sym in SYMBOLS:
        print("LOADING",sym,flush=True)
        d,data_q=read_candles(sym)
        rates,fcount=funding_proxy(sym)
        ent,ex,sig_q=build_signals(d)
        for risk in UNIT_RISK_VARIANTS:
            print("REPLAY",sym,risk,flush=True)
            summ,mm,tt=run(d,ent,ex,rates,risk)
            summ["symbol"]=sym
            summaries.append(summ)
            for z in mm:z["symbol"]=sym
            for z in tt:z["symbol"]=sym;z["risk_per_unit"]=risk
            months+=mm;trades+=tt
            print("RESULT",json.dumps(summ),flush=True)
        q.append({**data_q,**sig_q,"funding_observations":fcount})
    sm=pd.DataFrame(summaries);mo=pd.DataFrame(months);tr=pd.DataFrame(trades)
    sm.to_csv(OUT/"summary.csv",index=False)
    mo.to_csv(OUT/"monthly_ist.csv",index=False)
    tr.to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    meta=dict(source="Delta Exchange India one-minute OHLCV 2025-01 to 2026-11-17",
        method="Independent from public Quattro strategy spec, LONG only",
        fee="0.05% taker per fill plus 18% GST on fee",
        slippage="2 basis points adverse on each fill (entry, add, exit)",
        funding="Delta 1h FUNDING candle close at preceding hour is a proxy, not verified settlement",
        missing_funding="Assume 0.01% CHARGE each missing 8-hour settlement; not actual known payment",
        margin="20x notional cap only; margin eligibility/liquidation not reconstructed",
        caveats=["Daily EMA200 needs 200 complete days, so first 200 days are warmup",
            "No genuine untouched holdout (all historical periods previously research exposed)",
            "Long-only source code condition is close above daily EMA200; README mentions rising EMA and is inconsistent",
            "Fees, GST, hypothetical slippage, and funding proxy included; not actual order book",
            "For contradictory 1m stop/add OHLC ordering, pessimistic fill assumption used",
            "At 1m data gap, unknown gap exposure exits at next observed open",
            "Monthly net equity is IST mark-to-market including estimated close-out fee",
            "Partial November 2026, no 2022-2024 archived Delta data",
            "Pyramiding 4 x 2% initial nominal risk can produce large account drawdowns",
            "Not automatically a tradable or safe strategy"],
        data=q,variant_count=len(summaries))
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
    lines=["# Independent Quattro-style breakout: BTCUSD + ETHUSD, Delta India",
        "","## Result summary",sm.to_markdown(index=False),"",
        "## Monthly IST mark-to-market",mo.to_markdown(index=False),"",
        "## Caveats",*[f"- {x}" for x in meta["caveats"]],
        "","Source: scripts/research_asymmetric_quattro_independent.py"]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("COMPLETE",len(sm),"models",len(tr),"trades",len(mo),"monthly rows",flush=True)
if __name__=="__main__": main()
