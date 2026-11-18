#!/usr/bin/env python3
"""Novel family: 5m REALIZED-VOLATILITY REGIME TRANSITION after 60m compression.
Entry at next 1m open; compare shock continuation vs shock fade, no wick/EMA/VWAP.
One trade max per UTC day, no overnight. 2025 train, 2026 research-exposed check.
Delta taker fee 5bps each side * 1.18 GST; 2bps adverse slippage each side,
1bp funding debit per crossed 8h boundary. No grid/martingale.
"""
import numpy as np,pandas as pd,json,itertools
from pathlib import Path
ROOT=Path("data/delta_india");OUT=Path("analysis/daily_volatility_shock_fade_20261119")
OUT.mkdir(parents=True,exist_ok=True)
START=int(pd.Timestamp("2025-01-01",tz="UTC").timestamp())
END=int(pd.Timestamp("2026-11-18",tz="UTC").timestamp())
FEE=.0005*1.18;SLIP=.0002;FUND=.0001
MODES=("follow","fade");SHOCK=(1.5,2.,3.);COMPRESSION=(.7,1.)
TP=(.003,.005,.008);SL=(.003,.005);HOLD=(30,90)
CAP=1000.;RISK=.005;LEV=2.

def load(sym):
    files=sorted((ROOT/sym/"1m").glob("20??-??.csv.gz"))
    if len(files)<22:raise ValueError(sym+" missing source months")
    cols=["time","open","high","low","close","volume"]
    d=pd.concat((pd.read_csv(p,compression="gzip",usecols=cols) for p in files),ignore_index=True)
    d=d[(d.time>=START)&(d.time<END)].sort_values("time").reset_index(drop=True)
    t=d.time.to_numpy(np.int64)
    if len(t)!=987840 or t[0]!=START or t[-1]!=END-60 or not np.all(np.diff(t)==60):
        raise ValueError(sym+" gaps in minute timestamps")
    if not np.isfinite(d[cols].to_numpy(float)).all():raise ValueError("nonfinite")
    if (d.high<d.low).any() or (d.open<d.low).any() or (d.close<d.low).any() or (d.open>d.high).any() or (d.close>d.high).any():
        raise ValueError("invalid OHLC")
    return d,dict(symbol=sym,source_files=len(files),rows=len(d),missing_minutes=0,first=START,last=END-60)

def signals(d):
    # 5m realized movement: sum absolute log returns of last 5 fully completed 1m candles.
    c=d.close.to_numpy(float)
    r=np.r_[np.nan,np.abs(np.diff(np.log(c)))]
    v5=pd.Series(r).rolling(5,min_periods=5).sum()
    # Prior 60-minute baseline, ending BEFORE current 5m shock.
    prior=v5.shift(5).rolling(60,min_periods=60).median()
    # Prior 60m compression vs earlier 6h baseline.
    prior60=v5.shift(5).rolling(60,min_periods=60).median()
    earlier=v5.shift(65).rolling(300,min_periods=300).median()
    # New shock: last 5m realized vol exceeds lagged baseline, after a quiet regime.
    v5=v5.to_numpy();prior=prior.to_numpy();prior60=prior60.to_numpy();earlier=earlier.to_numpy()
    delta=np.r_[np.full(5,np.nan),np.log(c[5:]/c[:-5])]
    out={};counts=[]
    for shock,compression in itertools.product(SHOCK,COMPRESSION):
        mask=(v5>=shock*prior)&(prior60<=compression*earlier)&(prior>0)&np.isfinite(earlier)&(np.abs(delta)>.0002)
        # Signal ONLY on completed 5m bar, 5th minute indices 4,9,14...
        mask &= np.arange(len(c))%5==4
        # next minute open: index k = signal index + 1
        ks=np.flatnonzero(mask)+1
        ks=ks[(ks<len(c))&(ks%1440>=180)&(ks%1440<1200)]
        byday={}
        for k in ks:
            day=int(k//1440)
            if day not in byday:byday[day]=(int(k),int(np.sign(delta[k-1])))
        out[(shock,compression)]=byday
        counts.append(dict(shock=shock,compression=compression,signals=len(ks),days=len(byday)))
    return out,counts

def replay(px,events,config):
    mode,shock,comp,tp,sl,hold=config
    o,h,l,c,t=px
    eq=CAP;rows=[]
    for day in range(len(t)//1440):
        before=eq;net=fees=funding=0.;traded=0
        ev=events.get(day)
        if ev and eq>0:
            k,side=ev
            if mode=="fade":side=-side
            entry=float(o[k])*(1+side*SLIP)
            qty=min(eq*RISK/(sl*entry),eq*LEV/entry)
            target=entry*(1+side*tp);stop=entry*(1-side*sl)
            until=min(k+hold,(day+1)*1440)
            j=until-1;exit_px=float(c[j])
            for x in range(k,until):
                if side>0:
                    if l[x]<=stop:j=x;exit_px=min(float(o[x]),stop);break
                    if h[x]>=target:j=x;exit_px=target;break
                else:
                    if h[x]>=stop:j=x;exit_px=max(float(o[x]),stop);break
                    if l[x]<=target:j=x;exit_px=target;break
            fill=exit_px*(1-side*SLIP)
            fees=FEE*qty*(entry+fill)
            funding=FUND*qty*fill*sum(1 for x in range(k,j+1) if t[x]%28800==0)
            net=side*qty*(fill-entry)-fees-funding
            eq+=net;traded=1
        rows.append((day,t[day*1440],before,eq,net,fees,funding,traded))
    return np.asarray(rows,float)

def metrics(sym,config,year,rows):
    z=rows[:365] if year==2025 else rows[365:]
    x=z[:,4];pos=x[x>1e-8];neg=x[x<-1e-8]
    nav=np.r_[z[0,2],z[:,3]];pf=float(pos.sum()/-neg.sum()) if len(neg) else None
    streak=max_streak=0
    for y in x:
        streak=streak+1 if y<0 else 0;max_streak=max(max_streak,streak)
    mode,shock,comp,tp,sl,hold=config
    return dict(symbol=sym,year=year,mode=mode,shock=shock,compression=comp,tp=tp,sl=sl,hold=hold,
        days=len(z),trades=int(z[:,7].sum()),profitable_days=len(pos),losing_days=len(neg),
        no_trade_days=int(len(z)-z[:,7].sum()),profitable_calendar_day_pct=round(100*len(pos)/len(z),3),
        net_return_pct=round(100*(z[-1,3]/z[0,2]-1),4),
        profit_factor=round(pf,4) if pf is not None else None,
        median_day_usd=round(float(np.median(x)),4),mean_day_usd=round(float(np.mean(x)),4),
        worst_day_usd=round(float(np.min(x)),4),
        max_losing_day_streak=max_streak,
        max_dayclose_drawdown_pct=round(100*float(np.min(nav/np.maximum.accumulate(nav)-1)),4),
        fees_usd=round(float(z[:,5].sum()),3),funding_debit_usd=round(float(z[:,6].sum()),3))

def main():
    summaries=[];selected=[];monthly=[];quality=[]
    configs=list(itertools.product(MODES,SHOCK,COMPRESSION,TP,SL,HOLD))
    for sym in ("BTCUSD","ETHUSD"):
        print("LOADING",sym,flush=True)
        d,q=load(sym);events,counts=signals(d)
        quality.append({**q,"event_counts":counts})
        px=tuple(d[k].to_numpy(float) for k in ("open","high","low","close"))+(d.time.to_numpy(np.int64),)
        best=None;bestcfg=None;bestrows=None;passed=False
        for i,cfg in enumerate(configs):
            rows=replay(px,events[(cfg[1],cfg[2])],cfg)
            a=metrics(sym,cfg,2025,rows);b=metrics(sym,cfg,2026,rows)
            summaries.extend((a,b))
            eligible=a["trades"]>=50 and a["net_return_pct"]>0 and a["profit_factor"] is not None and a["profit_factor"]>1
            key=(int(eligible),a["profitable_calendar_day_pct"] if eligible else a["net_return_pct"],a["net_return_pct"])
            if best is None or key>best:
                best=key;bestcfg=cfg;bestrows=rows;bestpair=(a,b);passed=eligible
            if i%40==0:print("PROGRESS",sym,i,"of",len(configs),flush=True)
        selected.extend([{**r,"passes_2025_minimum":passed} for r in bestpair])
        times=pd.to_datetime(bestrows[:,1].astype(np.int64),unit="s",utc=True).strftime("%Y-%m")
        for m in pd.unique(times):
            z=bestrows[times==m]
            monthly.append(dict(symbol=sym,month=m,return_pct=round(100*(z[-1,3]/z[0,2]-1),4),
                profitable_days=int((z[:,4]>1e-8).sum()),losing_days=int((z[:,4]<-1e-8).sum()),
                no_trade_days=int((z[:,7]==0).sum()),trades=int(z[:,7].sum()),
                fees_usd=round(float(z[:,5].sum()),3)))
        print("SELECTED",sym,bestcfg,passed,bestpair,flush=True)
    pd.DataFrame(summaries).to_csv(OUT/"summary.csv",index=False)
    pd.DataFrame(selected).to_csv(OUT/"selected.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"selected_monthly.csv",index=False)
    meta=dict(hypothesis="5m realized-volatility shock after 60m compression; follow or fade direction",
        novel_vs=["VWAP exhaustion","wick reversal","1m cross-asset lead-lag","4h cross-market confirmation"],
        models_per_asset=len(configs),quality=quality,
        selection="2025 net positive, PF>1 and >=50 trades, maximize profitable calendar days; otherwise highest 2025 net return. Replay fixed settings 2026.",
        split="2025 training; 2026-01-01 through 2026-11-17 research-exposed historical check, not pristine holdout",
        costs={"taker_each_side_with_GST":FEE,"slippage_each_side":SLIP,"funding_debit_per_8h_crossing":FUND},
        sizing={"equity_start_usd":CAP,"risk_per_stop":RISK,"notional_leverage_cap":LEV},
        limitations=["Funding debit is proxy not actual historical settlements",
                     "No orderbook, spread/market-impact depth, contract minimum size, liquidation or margin engine",
                     "1m OHLC stop-first, no intrabar ordering", "No forced daily trades",
                     "2026 November partial", "Historical strategy returns cannot guarantee daily income"])
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
    (OUT/"REPORT.md").write_text("# Independent realized-volatility regime-transition research\n\n"+
        "## Selected 2025 configurations replayed in 2026\n\n"+
        pd.DataFrame(selected).to_string(index=False)+"\n\n## Caveats\n\n"+
        "\n".join("- "+x for x in meta["limitations"])+"\n")
    print("FINISHED",len(summaries),"year-model rows",flush=True)
if __name__=="__main__":main()
