#!/usr/bin/env python3
"""Funding-settlement-boundary post-event drift, BTCUSD and ETHUSD.
Distinct hypothesis: 8h settlement clock affects directional continuation or
reversal in first 5/15m following UTC 00:00,08:00,16:00 boundary.
No funding rate direction is used, because settlement cashflow rates are not
available as verified forward-known inputs in this experiment.
1 trade per UTC calendar day, next-minute-open after completed signal.
2025 training, unchanged 2026 historical check (not pristine holdout).
Conservative taker+GST, 2bp adverse each fill, 1bp funding debit per crossing.
Stop-first OHLC. No martingale or averaging down.
"""
import itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path("data/delta_india")
OUT=Path("analysis/funding_boundary_drift_daily_20261118")
OUT.mkdir(parents=True,exist_ok=True)
START=pd.Timestamp("2025-01-01",tz="UTC")
END=pd.Timestamp("2026-11-18",tz="UTC")
FEE=.0005*1.18
SLIP=.0002
FUND=.0001
RISK=.005
LEV=2.
CAP=1000.
BOUNDARIES=(0,480,960)
PRE=(15,30,60)
POST=(5,15)
MODE=("follow","fade")
THRESH=(.001,.0025)
TP=(.003,.005)
SL=(.003,.005)
HOLD=(30,90)
# 3*2*2*2*2*2*2 = 192 variants per asset.
def load(symbol):
    paths=sorted((ROOT/symbol/"1m").glob("20??-??.csv.gz"))
    if len(paths)<22:raise ValueError("Insufficient files "+symbol)
    d=pd.concat((pd.read_csv(p,compression="gzip",usecols=["time","open","high","low","close","volume"]) for p in paths),ignore_index=True)
    d=d[(d.time>=int(START.timestamp()))&(d.time<int(END.timestamp()))].sort_values("time").reset_index(drop=True)
    t=d.time.to_numpy(np.int64)
    if len(t)%1440 or len(t)<950000 or t[0]!=int(START.timestamp()) or t[-1]!=int(END.timestamp())-60 or not np.all(np.diff(t)==60):
        raise ValueError("Nonconsecutive source: "+symbol)
    if not np.isfinite(d[["open","high","low","close","volume"]].to_numpy(float)).all():
        raise ValueError("Nonfinite source")
    if (d.high<d.low).any() or (d.open<d.low).any() or (d.close<d.low).any() or (d.open>d.high).any() or (d.close>d.high).any():
        raise ValueError("Bad OHLC source")
    return d,{"symbol":symbol,"bars":len(d),"months":len(paths),"missing_minutes":0,"first_utc":str(START),"last_utc":str(END-pd.Timedelta(minutes=1))}
def signals(d):
    c=d.close.to_numpy(float)
    out={}
    days=len(c)//1440
    for pre,post,mode,thr in itertools.product(PRE,POST,MODE,THRESH):
        byday={}
        for day in range(days):
            for boundary in BOUNDARIES:
                b=day*1440+boundary
                k=b+post
                if b-pre-1<0 or k>=len(c):continue
                # pre-event last completed minute is b-1, and first after
                # settlement is b; post-event last completed minute is k-1.
                before=np.log(c[b-1]/c[b-pre-1])
                after=np.log(c[k-1]/c[b-1])
                if abs(before)<thr or abs(after)<thr/3:continue
                # Require post-event move aligned with pre-event momentum.
                if np.sign(before)!=np.sign(after):continue
                side=int(np.sign(before))*(1 if mode=="follow" else -1)
                byday[day]=(k,side)
                break
        out[(pre,post,mode,thr)]=byday
    return out
def simulate(d,events,cfg):
    pre,post,mode,thr,tp,sl,hold=cfg
    o=d.open.to_numpy(float);h=d.high.to_numpy(float)
    l=d.low.to_numpy(float);c=d.close.to_numpy(float);t=d.time.to_numpy(np.int64)
    eq=CAP;rows=[]
    for day in range(len(d)//1440):
        before=eq;net=fees=funding=0.;traded=0
        if day in events and eq>0:
            k,side=events[day]
            entry=o[k]*(1+side*SLIP)
            qty=min(eq*RISK/(sl*entry),eq*LEV/entry)
            target=entry*(1+side*tp);stop=entry*(1-side*sl)
            until=min(k+hold,(day+1)*1440)
            j=until-1;px=c[j]
            for z in range(k,until):
                if side==1:
                    if l[z]<=stop:
                        j=z;px=min(o[z],stop);break
                    if h[z]>=target:
                        j=z;px=target;break
                else:
                    if h[z]>=stop:
                        j=z;px=max(o[z],stop);break
                    if l[z]<=target:
                        j=z;px=target;break
            exitfill=px*(1-side*SLIP)
            fees=FEE*qty*(entry+exitfill)
            funding=FUND*qty*exitfill*sum(1 for z in range(k,j+1) if t[z]%28800==0)
            net=side*qty*(exitfill-entry)-fees-funding
            eq+=net;traded=1
        rows.append((day,int(t[day*1440]),before,eq,net,fees,funding,traded))
    return np.array(rows,dtype=float)
def score(rows,symbol,cfg,year):
    x=rows[:365] if year==2025 else rows[365:]
    pnl=x[:,4];wins=pnl[pnl>1e-8];losses=pnl[pnl<-1e-8]
    start=x[0,2];end=x[-1,3]
    nav=np.r_[start,x[:,3]]
    pf=float(wins.sum()/-losses.sum()) if len(losses) else None
    streak=mx=0
    for p in pnl:
        streak=streak+1 if p<-1e-8 else 0
        mx=max(mx,streak)
    return dict(symbol=symbol,year=year,pre_min=cfg[0],post_min=cfg[1],
        mode=cfg[2],threshold=cfg[3],tp=cfg[4],sl=cfg[5],hold_min=cfg[6],
        calendar_days=len(x),trades=int(x[:,7].sum()),profitable_days=len(wins),
        losing_days=len(losses),no_trade_days=int(len(x)-x[:,7].sum()),
        positive_calendar_day_pct=round(100*len(wins)/len(x),3),
        win_rate_traded_pct=round(100*len(wins)/max(1,len(wins)+len(losses)),3),
        net_return_pct=round(100*(end/start-1),4),
        profit_factor=round(pf,4) if pf is not None else None,
        max_dayclose_dd_pct=round(100*float(np.min(nav/np.maximum.accumulate(nav)-1)),4),
        max_consecutive_losing_days=mx,
        median_calendar_day_usd=round(float(np.median(pnl)),4),
        mean_calendar_day_usd=round(float(np.mean(pnl)),4),
        mean_losing_day_usd=round(float(np.mean(losses)),4) if len(losses) else 0.,
        worst_day_usd=round(float(np.min(pnl)),4),
        fees_usd=round(float(x[:,5].sum()),4),
        funding_debit_usd=round(float(x[:,6].sum()),4))
def main():
    summary=[];selected=[];monthly=[];quality=[]
    for symbol in ("BTCUSD","ETHUSD"):
        print("LOADING",symbol,flush=True)
        d,q=load(symbol);quality.append(q)
        ev=signals(d)
        models={}
        for cfg in itertools.product(PRE,POST,MODE,THRESH,TP,SL,HOLD):
            r=simulate(d,ev[cfg[:4]],cfg)
            a=score(r,symbol,cfg,2025);b=score(r,symbol,cfg,2026)
            summary.extend((a,b));models[cfg]=(r,a,b)
        viable=[(k,v) for k,v in models.items() if v[1]["trades"]>=50 and v[1]["net_return_pct"]>0 and
                v[1]["profit_factor"] is not None and v[1]["profit_factor"]>1]
        eligible=viable if viable else list(models.items())
        if viable:
            chosen=max(eligible,key=lambda x:(x[1][1]["positive_calendar_day_pct"],x[1][1]["net_return_pct"]))
        else:
            chosen=max(eligible,key=lambda x:(x[1][1]["net_return_pct"],x[1][1]["positive_calendar_day_pct"]))
        cfg,(r,a,b)=chosen
        selected.extend([{**a,"passes_train":bool(viable)},{**b,"passes_train":bool(viable)}])
        months=pd.to_datetime(r[:,1].astype(np.int64),unit="s",utc=True).strftime("%Y-%m")
        for month in pd.unique(months):
            z=r[months==month]
            monthly.append(dict(symbol=symbol,month_utc=month,
                net_return_pct=round(100*(z[-1,3]/z[0,2]-1),4),
                trades=int(z[:,7].sum()),profitable_days=int((z[:,4]>1e-8).sum()),
                losing_days=int((z[:,4]<-1e-8).sum()),
                no_trade_days=int((z[:,7]==0).sum()),
                fees_usd=round(float(z[:,5].sum()),4)))
        print("SELECTED",symbol,cfg,"train viable",bool(viable),a,b,flush=True)
    pd.DataFrame(summary).to_csv(OUT/"summary.csv",index=False)
    pd.DataFrame(selected).to_csv(OUT/"selected.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"selected_monthly.csv",index=False)
    meta=dict(hypothesis="post-8h-funding-boundary directional drift/fade conditional on completed pre and post settlement price impulses",
        novelty="Specific funding-boundary event study, distinct from broad clock-only entry and unrelated funding carry; no funding-rate prediction",
        data_quality=quality,models_per_symbol=len(models),
        selection="2025 positive PF>1, net>0 and >=50 trades, then calendar positive-day rate; otherwise least negative 2025; unchanged 2026",
        fee_each_side=FEE,slippage_each_side=SLIP,funding_debit_each_crossing=FUND,
        risk_fraction_per_trade=RISK,leverage_notional_cap=LEV,
        caveats=["No verified historical funding-rate inputs; study tests boundary timing, NOT actual carry",
                 "2026 previously research-exposed, not a pristine holdout",
                 "Funding debit is conservative proxy, not actual settlement",
                 "No order book, lot-size, liquidation/margin or intraminute tick-path simulation",
                 "Stop wins tie against target, conservative",
                 "2026 Nov partial through Nov 17 UTC",
                 "No-trade days count against positive calendar-day frequency",
                 "No strategy guarantees daily profits"])
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
    (OUT/"REPORT.md").write_text("# Independent funding-boundary drift daily net study\n\n"+
        pd.DataFrame(selected).to_string(index=False)+"\n\n"+
        "## Assumptions and limitations\n\n"+json.dumps(meta,indent=2)+"\n")
    print("DONE",len(summary),"year rows",flush=True)
if __name__=="__main__":main()
