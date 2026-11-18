#!/usr/bin/env python3
"""Independent paired BTC/ETH 1m lead-lag hypothesis. 2025 selection only.
When BTC makes a 5m move > threshold and ETH has not followed, trade ETH in
BTC's direction for 10-30m; reciprocal variant trades BTC on ETH's move.
No overlap, at most one entry per UTC day. Intraminute stop-first, next-minute
open entry. Standard taker 0.05%*1.18 GST on each side, 2bp slippage each
side; 1bp debit per funding timestamp, no credit. 0.5% risk, 2x max leverage.
No maker fills assumed. Funding cashflow proxy, not exchange ledger.
"""
import itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path("data/delta_india");OUT=Path("analysis/daily_btc_eth_leadlag_20261118");OUT.mkdir(parents=True,exist_ok=True)
START=int(pd.Timestamp("2025-01-01",tz="UTC").timestamp())
END=int(pd.Timestamp("2026-11-18",tz="UTC").timestamp())
FEE=.0005*1.18;SLIP=.0002;FUND=.0001
CONFIGS=list(itertools.product(("BTCUSD","ETHUSD"),(.003,.005,.008),(.15,.35,.55),(.003,.005),(.004,.007),(10,30)))
def load(sym):
    fs=sorted((ROOT/sym/"1m").glob("20??-??.csv.gz"))
    if len(fs)<22:raise RuntimeError("Missing archive "+sym)
    d=pd.concat((pd.read_csv(p,compression="gzip",usecols=["time","open","high","low","close","volume"]) for p in fs),ignore_index=True)
    d=d[(d.time>=START)&(d.time<END)].sort_values("time").reset_index(drop=True)
    t=d.time.to_numpy(np.int64)
    if len(t)!=(END-START)//60 or t[0]!=START or t[-1]!=END-60 or not np.all(np.diff(t)==60):raise ValueError("Missing/duplicate minutes "+sym)
    if not np.isfinite(d[["open","high","low","close","volume"]].to_numpy(float)).all():raise ValueError("Nonfinite")
    if (d.high<d.low).any() or (d.open<d.low).any() or (d.close<d.low).any() or (d.open>d.high).any() or (d.close>d.high).any():raise ValueError("Invalid OHLC")
    return d,dict(symbol=sym,files=len(fs),bars=len(t),missing_minutes=0,first_utc=str(pd.to_datetime(t[0],unit="s",utc=True)),last_utc=str(pd.to_datetime(t[-1],unit="s",utc=True)))
def simulate(a,b,config):
    leader,threshold,lag,stop,target,hold=config
    l=a if leader=="BTCUSD" else b
    f=b if leader=="BTCUSD" else a
    lc=l.close.to_numpy(float);fc=f.close.to_numpy(float)
    o=f.open.to_numpy(float);hi=f.high.to_numpy(float);lo=f.low.to_numpy(float);cl=f.close.to_numpy(float)
    times=f.time.to_numpy(np.int64)
    n=len(f);days=n//1440
    # Completed 5-minute leader move; follower is less than fraction of leader move.
    # Signals use j-5 through j-1, enter at open j.
    lm=np.full(n,np.nan);fm=np.full(n,np.nan)
    lm[5:]=lc[4:-1]/lc[:-5]-1
    fm[5:]=fc[4:-1]/fc[:-5]-1
    mask=(np.abs(lm)>=threshold)&(np.sign(lm)==np.sign(fm))&(np.abs(fm)<=np.abs(lm)*lag)
    # Avoid micro noise where follower direction is zero; allow zero follower movement.
    mask=(np.abs(lm)>=threshold)&(np.abs(fm)<=np.abs(lm)*lag)
    valid=np.flatnonzero(mask)
    byday={}
    for j in valid:
        mod=j%1440
        if mod<60 or mod>1380:continue
        byday.setdefault(j//1440,(int(j),int(np.sign(lm[j]))))
    equity=1000.;daily=[]
    for day in range(days):
        before=equity;net=0.;fee=0.;fund=0.;traded=False
        if day in byday:
            k,side=byday[day];traded=True
            entry=float(o[k])*(1+side*SLIP)
            qty=min(.005*equity/(entry*stop),2*equity/entry)
            st=entry*(1-side*stop);tg=entry*(1+side*target)
            last=min(k+hold,(day+1)*1440)
            exitindex=last-1;px=float(cl[exitindex])
            for j in range(k,last):
                if side==1:
                    if lo[j]<=st:px=min(float(o[j]),st);exitindex=j;break
                    if hi[j]>=tg:px=tg;exitindex=j;break
                else:
                    if hi[j]>=st:px=max(float(o[j]),st);exitindex=j;break
                    if lo[j]<=tg:px=tg;exitindex=j;break
            ex=px*(1-side*SLIP)
            fee=FEE*qty*(entry+ex)
            fund=FUND*qty*ex*sum(1 for j in range(k,exitindex+1) if times[j]%28800==0)
            net=side*qty*(ex-entry)-fee-fund
            equity+=net
        daystamp=str(pd.to_datetime(times[day*1440],unit="s",utc=True).date())
        daily.append((daystamp,int(daystamp[:4]),daystamp[:7],before,equity,net,fee,fund,int(traded)))
    return pd.DataFrame(daily,columns=["day","year","month","equity_before","equity_after","net","fees","funding","traded"])
def metrics(d,sym,config,year):
    g=d[d.year==year];p=g.net.to_numpy()
    w=p[p>1e-8];loss=p[p<-1e-8]
    eq=np.r_[g.equity_before.iloc[0],g.equity_after.to_numpy()]
    streak=mx=0
    for x in p:
        streak=streak+1 if x<-1e-8 else 0;mx=max(mx,streak)
    return dict(symbol=sym,year=year,leader=config[0],leader_move=config[1],follower_fraction=config[2],
        stop=config[3],target=config[4],hold_min=config[5],
        trades=int(g.traded.sum()),days=len(g),profitable_days=len(w),losing_days=len(loss),
        no_trade_days=int((g.traded==0).sum()),
        profitable_calendar_day_pct=round(100*len(w)/len(g),3),
        profit_factor=round(float(w.sum()/-loss.sum()),4) if len(loss) else None,
        net_return_pct=round(100*(eq[-1]/eq[0]-1),4),
        net_usd=round(float(eq[-1]-eq[0]),4),daily_mean_usd=round(float(p.mean()),4),
        daily_median_usd=round(float(np.median(p)),4),
        mean_losing_day_usd=round(float(loss.mean()),4) if len(loss) else None,
        worst_day_usd=round(float(p.min()),4),
        max_losing_streak=mx,max_dayclose_drawdown_pct=round(100*float(np.min(eq/np.maximum.accumulate(eq)-1)),4),
        fees_usd=round(float(g.fees.sum()),4),funding_debit_usd=round(float(g.funding.sum()),4))
def main():
    a,qa=load("BTCUSD");b,qb=load("ETHUSD")
    result=[];selected=[];monthly=[];all_daily={}
    for i,config in enumerate(CONFIGS):
        d=simulate(a,b,config)
        for year in (2025,2026):result.append(metrics(d,"ETHUSD" if config[0]=="BTCUSD" else "BTCUSD",config,year))
        if i%50==0:print("TEST",i,len(CONFIGS),flush=True)
    df=pd.DataFrame(result)
    for sym in ("BTCUSD","ETHUSD"):
        train=df[(df.symbol==sym)&(df.year==2025)]
        viable=train[(train.trades>=30)&(train.net_return_pct>0)&(train.profit_factor.fillna(0)>1)]
        eligible=not viable.empty
        rank=(viable if eligible else train).sort_values(
            ["profitable_calendar_day_pct","net_return_pct"] if eligible else ["net_return_pct","profitable_calendar_day_pct"],ascending=False)
        best=rank.iloc[0]
        config=(best.leader,float(best.leader_move),float(best.follower_fraction),float(best.stop),float(best.target),int(best.hold_min))
        selected.extend([{**row.to_dict(),"2025_criteria_pass":eligible} for _,row in df.iterrows() if row.symbol==sym and
            (row.leader,row.leader_move,row.follower_fraction,row.stop,row.target,row.hold_min)==config])
        d=simulate(a,b,config)
        for month,g in d.groupby("month"):
            monthly.append(dict(symbol=sym,month=month,net_return_pct=round(100*(g.equity_after.iloc[-1]/g.equity_before.iloc[0]-1),4),
                profitable_days=int((g.net>1e-8).sum()),losing_days=int((g.net<-1e-8).sum()),no_trade_days=int((g.traded==0).sum())))
        print("SELECTED",sym,config,eligible,flush=True)
    df.to_csv(OUT/"all_models.csv",index=False)
    pd.DataFrame(selected).to_csv(OUT/"selected.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"selected_monthly.csv",index=False)
    quality=dict(data=[qa,qb],hypothesis="Cross-asset BTC/ETH leader move and lagging follower continuation",
        model_count=len(CONFIGS),fee_per_side=FEE,slippage_per_side=SLIP,funding_8h_debit=FUND,
        selection="2025 >=30 trades, positive net return, PF>1 then maximum calendar profit-day rate. No eligible model: best net return is diagnostic failure.",
        limitations=["No actual L1 quotes, depth or contract lot validation",
          "Funding is assumed debit not actual cashflow", "No exchange liquidation simulation; max 2x notional",
          "2026 research exposed, not a pristine holdout","Daily zero trade counts as not profitable",
          "Minute OHLC uses pessimistic stop-first ordering; spread proxy only"])
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2))
    (OUT/"REPORT.md").write_text("# BTC ETH lead-lag daily-profit hypothesis\n\n"+pd.DataFrame(selected).to_string(index=False)+
       "\n\n## Monthly\n\n"+pd.DataFrame(monthly).to_string(index=False)+"\n\n## Caveats\n"+json.dumps(quality,indent=2))
    print("FINISHED",len(CONFIGS),"models",flush=True)
if __name__=="__main__":main()
