#!/usr/bin/env python3
"""Independent one-trade/day BTC/ETH CROSS-MARKET LEAD-LAG study.
Novelty: unlike earlier 4H cross confirmation or two-leg residual reversion,
signal is the opposing asset's completed 1m 3/10/30-minute impulse while target
asset price has NOT followed yet. Trade only target asset, never both legs;
all signals causal before the following one-minute bar OPEN. One trade/day.
2025 selection, unchanged 2026 research-exposed historical check.
2025-01-01..2026-11-17 UTC, full calendar-day win frequencies.
Taker standard 0.05% each side + 18% GST, 2bp adverse slip each side.
Conservative 1bp funding debit at 00/08/16 UTC boundaries.
No liquidation, exact tick/lot size or order-book depth modeled.
DO NOT call any results a guaranteed daily-profit strategy.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import json, itertools

ROOT=Path("data/delta_india")
OUT=Path("analysis/daily_crossleadlag_20261118")
OUT.mkdir(parents=True, exist_ok=True)
START=pd.Timestamp("2025-01-01",tz="UTC")
END=pd.Timestamp("2026-11-18",tz="UTC")
CAPITAL=1000.
RISK=.005
MAX_LEV=2.
FEE=.0005*1.18
SLIP=.0002
FUND=.0001
WINDOWS=(3,10,30)
THRESH=(.0015,.003,.005)
GAPS=("flat","aligned")
TAKES=(.003,.006)
STOPS=(.002,.004)
HOLDS=(20,60)

def load(sym):
    files=sorted((ROOT/sym/"1m").glob("20??-??.csv.gz"))
    if len(files)<22:raise RuntimeError("Missing historical files: "+sym)
    cols=["time","open","high","low","close","volume"]
    x=pd.concat((pd.read_csv(p,compression="gzip",usecols=cols) for p in files),ignore_index=True)
    x=x[(x.time>=int(START.timestamp()))&(x.time<int(END.timestamp()))].sort_values("time").reset_index(drop=True)
    t=x.time.to_numpy(dtype=np.int64)
    if len(t)<950000 or len(t)%1440 or t[0]!=START.timestamp() or t[-1]!=END.timestamp()-60 or not np.all(np.diff(t)==60):
        raise ValueError(sym+" missing or non-consecutive 1m data")
    v=x[cols].to_numpy(float)
    if not np.isfinite(v).all():raise ValueError("Non-finite source")
    if (x.high<x.low).any() or (x.open<x.low).any() or (x.close<x.low).any() or (x.open>x.high).any() or (x.close>x.high).any():
        raise ValueError("Invalid OHLC")
    return x,{"symbol":sym,"minute_rows":len(x),"first":str(START),"last":str(END-pd.Timedelta(minutes=1)),"source_months":len(files),"missing_minutes":0}

def impulses(own,other):
    c=own.close.to_numpy(float)
    o=other.close.to_numpy(float)
    n=len(c)
    out={}
    info=[]
    for window,threshold,gap in itertools.product(WINDOWS,THRESH,GAPS):
        ownret=np.full(n,np.nan)
        otherret=np.full(n,np.nan)
        ownret[window:]=np.log(c[window:]/c[:-window])
        otherret[window:]=np.log(o[window:]/o[:-window])
        # Last CLOSE from each market at minute i can be used for entry i+1 OPEN.
        leader=np.abs(otherret)>=threshold
        sign=np.sign(otherret)
        if gap=="flat":
            lag=(np.abs(ownret)<.5*np.abs(otherret))
        else:
            lag=(ownret*otherret>0)&(np.abs(ownret)<.7*np.abs(otherret))
        valid=leader&lag&np.isfinite(ownret)&np.isfinite(otherret)
        # Signal completed minute i; next minute starts from index i+1.
        idx=np.flatnonzero(valid)+1
        idx=idx[(idx<n)]
        # Do not enter too close to funding or daily boundary; entries UTC 04:00-20:00.
        idx=idx[(idx%1440>=240)&(idx%1440<1200)]
        byday={}
        for k in idx:
            day=int(k//1440)
            if day not in byday:
                byday[day]=(int(k),int(np.sign(otherret[k-1])))
        out[(window,threshold,gap)]=byday
        info.append(dict(window=window,threshold=threshold,gap=gap,signals=len(idx),days_with_signal=len(byday)))
    return out,info

def simulate(px,entrydata,config):
    window,threshold,gap,take,stop,hold=config
    o,h,l,c,t=px
    eq=CAPITAL
    n_days=len(t)//1440
    rows=[]
    for day_id in range(n_days):
        start=eq
        evt=entrydata.get(day_id)
        net=0.;fee=0.;fund=0.;traded=False
        if evt and eq>0:
            k,sd=evt
            entry=float(o[k])*(1+sd*SLIP)
            qty=min(RISK*eq/(stop*entry),MAX_LEV*eq/entry)
            st=entry*(1-sd*stop)
            tp=entry*(1+sd*take)
            until=min(k+hold,((k//1440)+1)*1440)
            j=until-1
            exitprice=float(c[j])
            for v in range(k,until):
                if sd==1:
                    if l[v]<=st:
                        j=v;exitprice=min(float(o[v]),st);break
                    if h[v]>=tp:
                        j=v;exitprice=tp;break
                else:
                    if h[v]>=st:
                        j=v;exitprice=max(float(o[v]),st);break
                    if l[v]<=tp:
                        j=v;exitprice=tp;break
            closefill=exitprice*(1-sd*SLIP)
            fee=FEE*qty*(entry+closefill)
            crossings=sum(1 for v in range(k,j+1) if t[v]%28800==0)
            fund=FUND*qty*closefill*crossings
            net=sd*qty*(closefill-entry)-fee-fund
            eq+=net;traded=True
        rows.append((day_id,int(t[day_id*1440]),start,eq,net,fee,fund,int(traded)))
    return np.asarray(rows,dtype=float)

def score(r,sym,config,year):
    # Rows are UTC days; year boundary always 365 days since 2025-01-01.
    z=r[:365] if year==2025 else r[365:]
    x=z[:,4];won=x[x>1e-7];lost=x[x<-1e-7]
    start=float(z[0,2]);end=float(z[-1,3])
    nav=np.r_[start,z[:,3]]
    dd=float(np.min(nav/np.maximum.accumulate(nav)-1))*100
    lossrate=float(np.sum(-lost))
    pf=float(won.sum()/lossrate) if lossrate>0 else None
    window,thr,gap,tp,sl,hold=config
    return dict(symbol=sym,year=year,lookback_min=window,leader_threshold=thr,lag_type=gap,
        target_fraction=tp,stop_fraction=sl,max_hold_min=hold,
        days=len(z),trades=int(z[:,7].sum()),profitable_days=len(won),losing_days=len(lost),
        no_trade_days=int(len(z)-z[:,7].sum()),
        calendar_positive_day_pct=round(100*len(won)/len(z),3),
        traded_win_rate_pct=round(100*len(won)/max(1,len(won)+len(lost)),3),
        profit_factor=round(pf,4) if pf is not None else None,
        net_return_pct=round(100*(end/start-1),4),
        net_profit_usd=round(end-start,3),
        avg_net_per_calendar_day_usd=round(float(np.mean(x)),4),
        max_dayclose_drawdown_pct=round(dd,4),
        worst_day_usd=round(float(np.min(x)),4),
        fees_usd=round(float(z[:,5].sum()),4),
        funding_debit_usd=round(float(z[:,6].sum()),4))

def main():
    sources={};quality=[]
    for sym in ("BTCUSD","ETHUSD"):
        d,q=load(sym);sources[sym]=d;quality.append(q)
    if not np.array_equal(sources["BTCUSD"].time.to_numpy(),
                          sources["ETHUSD"].time.to_numpy()):
        raise RuntimeError("BTC ETH timestamps not aligned")
    summary=[];selected=[];monthly=[];signal_counts=[]
    for sym,other in (("BTCUSD","ETHUSD"),("ETHUSD","BTCUSD")):
        print("LOAD SIGNALS",sym,flush=True)
        d=sources[sym]
        eventmaps,signalinfo=impulses(d,sources[other])
        signal_counts.append({sym:signalinfo})
        prices=(d.open.to_numpy(float),d.high.to_numpy(float),d.low.to_numpy(float),
                d.close.to_numpy(float),d.time.to_numpy(dtype=np.int64))
        models={}
        for cfg in itertools.product(WINDOWS,THRESH,GAPS,TAKES,STOPS,HOLDS):
            rows=simulate(prices,eventmaps[cfg[:3]],cfg)
            a=score(rows,sym,cfg,2025)
            b=score(rows,sym,cfg,2026)
            summary.extend((a,b))
            models[cfg]=(rows,a,b)
        eligible=[(k,v) for k,v in models.items() if v[1]["net_return_pct"]>0
                  and v[1]["profit_factor"] is not None and v[1]["profit_factor"]>1
                  and v[1]["trades"]>=50]
        if eligible:
            chosen=max(eligible,key=lambda kv:(kv[1][1]["calendar_positive_day_pct"],
                                                kv[1][1]["net_return_pct"]))
            passes=True
        else:
            chosen=max(models.items(),key=lambda kv:(kv[1][1]["net_return_pct"],
                                                     kv[1][1]["calendar_positive_day_pct"]))
            passes=False
        cfg,(r,a,b)=chosen
        selected.extend([{**a,"passes_2025_minimum":passes},{**b,"passes_2025_minimum":passes}])
        utc=pd.to_datetime(r[:,1].astype(np.int64),unit="s",utc=True)
        periods=utc.strftime("%Y-%m")
        for m in pd.unique(periods):
            g=r[periods==m]
            month_start=g[0,2]
            monthly.append(dict(symbol=sym,month_utc=m,return_pct=round(100*(g[-1,3]/month_start-1),5),
                trades=int(g[:,7].sum()),profitable_days=int(np.sum(g[:,4]>1e-7)),
                losing_days=int(np.sum(g[:,4]<-1e-7)),
                no_trade_days=int(np.sum(g[:,7]==0)),fees_usd=round(float(g[:,5].sum()),3)))
        print("CHOSEN",sym,cfg,"passes",passes,a,b,flush=True)
    summary=pd.DataFrame(summary);selected=pd.DataFrame(selected)
    summary.to_csv(OUT/"summary.csv",index=False)
    selected.to_csv(OUT/"selected.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"selected_monthly.csv",index=False)
    meta=dict(study="1m BTC ETH other-asset impulse leading unfinished own-asset response",
        novelty="Distinct from existing 4H confirmation and two-leg relative-value: 1m lead-lag, ONE asset directional, one trade per UTC day.",
        closest_prior=["research/independent-crossasset-confirmation-pf-20261118",
                       "research/independent-crossasset-dispersion-pf-20261118",
                       "research/independent-pairs-residual-20261118-v1"],
        splits=dict(train="2025-01-01 through 2025-12-31 UTC",
                    check="2026-01-01 through 2026-11-17 UTC, previously research-exposed"),
        costs=dict(taker_fee_with_GST_each_side=FEE,adverse_slippage_each_side=SLIP,
                   funding_debit_per_boundary=FUND),
        sizing=dict(stop_risk_fraction=RISK,notional_leverage_cap=MAX_LEV),
        caveats=["No guarantee of any positive daily net PnL",
                 "2026 already inspected by other prior research; not pristine OOS",
                 "No orderbook, true funding settlements, lot sizes, liquidation engine or precise queue priority",
                 "1m OHLC stop-first pessimistic when target and stop touch",
                 "Notional liquidity/slippage simplified; 1m BTC/ETH different volatility",
                 "2026 November incomplete"],
        model_count_per_asset=144,input_quality=quality,
        event_counts=signal_counts,
        selection="2025 positive net PF>1 >=50 trades then highest positive calendar-day fraction; otherwise choose least-negative 2025; replay unchanged 2026")
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
    report=["# Independent 1m cross-asset lead-lag daily net research","","## Predeclared mechanics",
            "A completed 1m BTC/ETH impulse with own market not yet catching up triggers trade in lagging market at next 1m OPEN. One trade per UTC day, time-capped, stop-first.",
            "","## 2025-selected models replayed unchanged in 2026",
            "",selected.to_string(index=False),"","## Evidence caveats"]
    report.extend("- "+x for x in meta["caveats"])
    (OUT/"REPORT.md").write_text("\n".join(report)+"\n")
    print("COMPLETE",len(summary),"year rows",flush=True)
if __name__=="__main__": main()
