#!/usr/bin/env python3
"""Independent trend-acceleration impulse strategy, not a breakout or squeeze.

Causal 1H momentum acceleration: trailing 6h return in ATR units exceeds
prior 6h return by threshold 1.5/2.5 ATR, recent 12h direction consistency
>= 0.67/0.75, volume > 1.0/1.5x prior 48h average. Opposite for shorts.
Initial 1.25/2 ATR stop; very wide 8/12 ATR trailing stop; no target.
Research only, with realistic friction and 1m stop execution.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit

DATA=Path("data/delta_india")
OUT=Path("analysis/convex_trend_acceleration_20261119")
ASSETS=("BTCUSD","ETHUSD")
START_EQUITY=1000.
RISK=.005
FEE=.0005*1.18
SLIP=.0002
MISSING_FUNDING=.0001
MAX_LEVERAGE=10.
START=pd.Timestamp("2025-01-01",tz="UTC")
END=pd.Timestamp("2026-11-18",tz="UTC")

def load(symbol):
    root=DATA/symbol/"1m"
    files=sorted(root.glob("20??-??.csv.gz"))
    if len(files)<22: raise RuntimeError(f"{symbol} not enough files")
    d=pd.concat((pd.read_csv(f,compression="gzip",usecols=["time","open","high","low","close","volume"]) for f in files),ignore_index=True)
    d=d[(d.time>=START.timestamp())&(d.time<END.timestamp())].sort_values("time").reset_index(drop=True)
    time=d.time.to_numpy(np.int64)
    if len(d)<900000 or np.any(np.diff(time)!=60):
        raise RuntimeError(f"{symbol} missing/duplicated minutes")
    for c in ("open","high","low","close","volume"):
        if not np.isfinite(d[c]).all():raise RuntimeError(f"{symbol} invalid {c}")
    if ((d.low<=0)|(d.high<d.low)|(d.open<d.low)|(d.close<d.low)|
        (d.open>d.high)|(d.close>d.high)).any():raise RuntimeError("bad OHLC")
    d.index=pd.to_datetime(d.time,unit="s",utc=True)
    return d

def funding_arr(symbol,t):
    fpath=DATA/symbol/"institutional/history/funding_1h"
    d=pd.concat((pd.read_csv(p,compression="gzip",usecols=["time","close"]) for p in sorted(fpath.glob("20??-??.csv.gz"))),ignore_index=True)
    d=d.drop_duplicates("time",keep="last")
    d=d[np.isfinite(d.close)&(d.close.abs()<=5)]
    rate={int(x)+3600:float(v)/100 for x,v in zip(d.time,d.close)}
    out=np.zeros(len(t),np.float64)
    missing=0
    for i in np.flatnonzero(t%28800==0):
        x=rate.get(int(t[i]))
        if x is None:
            x=np.nan;missing+=1
        out[i]=x
    return out,{"funding_rows":len(d),"missing_settlement_observations":missing}

def signals(d,impulse,consistency,volume_ratio):
    x=d[["open","high","low","close","volume"]]
    h=x.resample("1h",closed="left",label="left").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    counts=x.close.resample("1h",closed="left",label="left").count()
    complete=counts.eq(60)
    prev=h.close.shift(1)
    tr=pd.concat([(h.high-h.low),(h.high-prev).abs(),(h.low-prev).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    # Difference of two nonoverlapping 6-hour price displacements.
    recent=h.close-h.close.shift(6)
    older=h.close.shift(6)-h.close.shift(12)
    accel=(recent-older)/atr
    candle_sign=np.sign(h.close-h.close.shift(1))
    up=candle_sign.gt(0).rolling(12,min_periods=12).mean()
    down=candle_sign.lt(0).rolling(12,min_periods=12).mean()
    volume_base=h.volume.shift(1).rolling(48,min_periods=48).mean()
    volume_ok=h.volume>volume_ratio*volume_base
    ok=complete.rolling(200,min_periods=200).min().eq(True)&atr.gt(0)&volume_ok
    # No price-channel breakout or volatility-compression predicate is used.
    long=ok&(accel>impulse)&(recent>0)&(up>=consistency)
    short=ok&(accel< -impulse)&(recent<0)&(down>=consistency)
    t=d.time.to_numpy(np.int64);n=len(d)
    side=np.zeros(n,np.int8);in_atr=np.zeros(n,np.float64)
    last_high=np.zeros(n,np.float64);last_low=np.zeros(n,np.float64)
    last_atr=np.zeros(n,np.float64)
    for j in range(1,len(h)):
        k=j*60
        if k>=n:break
        if long.iloc[j-1] or short.iloc[j-1]:
            side[k]=1 if long.iloc[j-1] else -1
            in_atr[k]=atr.iloc[j-1]
        if bool(complete.iloc[j-1]):
            last_high[k]=h.high.iloc[j-1]
            last_low[k]=h.low.iloc[j-1]
            last_atr[k]=atr.iloc[j-1] if np.isfinite(atr.iloc[j-1]) else 0
    return side,in_atr,last_high,last_low,last_atr,int(long.sum()+short.sum())

@njit(cache=True)
def replay(t,o,hi,lo,cl,sig,sigatr,last_high,last_low,last_atr,fr,month_id,stopmul,trailmul,nmonths):
    cash=START_EQUITY;side=0;qty=0.;entry_fill=0.;open_equity=0.;entry_risk=0.;entry_i=0
    st=0.;maxfav=0.;fee_total=0.;fund_total=0.;pos_fee=0.;pos_fund=0.;peak=START_EQUITY;dd=0.
    mark=np.full(nmonths,np.nan);month_entries=np.zeros(nmonths,np.int32);month_expose=np.zeros(nmonths,np.int32)
    log=np.zeros((5000,11),np.float64);count=0
    for i in range(len(t)):
        if side:
            month_expose[month_id[i]]=1
            if last_atr[i]>0:
                if side==1:
                    maxfav=max(maxfav,last_high[i])
                    st=max(st,maxfav-trailmul*last_atr[i])
                else:
                    maxfav=min(maxfav,last_low[i])
                    st=min(st,maxfav+trailmul*last_atr[i])
            if t[i]%28800==0:
                if np.isnan(fr[i]):
                    pay=abs(qty*o[i]) * MISSING_FUNDING
                else:
                    pay=qty*o[i]*fr[i]*side
                cash-=pay;pos_fund+=pay;fund_total+=pay
            hit=(lo[i]<=st if side==1 else hi[i]>=st)
            if hit:
                px=min(o[i],st) if side==1 else max(o[i],st)
                fill=px*(1-side*SLIP)
                gross=side*(fill-entry_fill)*qty
                fee=FEE*fill*qty
                cash+=gross-fee;fee_total+=fee;pos_fee+=fee
                if count<len(log):
                    log[count,0]=t[entry_i];log[count,1]=t[i];log[count,2]=side
                    log[count,3]=cash-open_equity;log[count,4]=(cash-open_equity)/entry_risk
                    log[count,5]=pos_fee;log[count,6]=pos_fund
                    log[count,7]=entry_fill;log[count,8]=fill;log[count,9]=stopmul;log[count,10]=trailmul
                    count+=1
                side=0;qty=0.
        if not side and sig[i]!=0 and sigatr[i]>0 and cash>0:
            sd=int(sig[i]);sdist=stopmul*sigatr[i]
            fill=o[i]*(1+sd*SLIP)
            riskcash=cash*RISK
            q=riskcash/sdist
            if q*fill<=cash*MAX_LEVERAGE and sdist>0 and q>0:
                open_equity=cash;entry_risk=riskcash;side=sd;qty=q;entry_fill=fill
                entry_i=i;st=fill-sd*sdist;maxfav=fill
                fee=FEE*fill*qty;cash-=fee;pos_fee=fee;pos_fund=0.;fee_total+=fee
                month_entries[month_id[i]]+=1;month_expose[month_id[i]]=1
                # Stops can trigger inside the entry minute; 1m wick monitored next minute
                # to avoid applying pre-entry high/low of same 1m candle.
        if side:
            liquid=cl[i]*(1-side*SLIP)
            equity=cash+side*(liquid-entry_fill)*qty-FEE*liquid*qty
        else:equity=cash
        if equity>peak:peak=equity
        if peak>0 and (equity/peak-1)<dd:dd=equity/peak-1
        if i==len(t)-1 or month_id[i+1]!=month_id[i]:
            mark[month_id[i]]=equity
    if side:
        i=len(t)-1
        fill=cl[i]*(1-side*SLIP)
        fee=FEE*fill*qty;cash+=side*(fill-entry_fill)*qty-fee
        fee_total+=fee;pos_fee+=fee
        if count<len(log):
            log[count,0]=t[entry_i];log[count,1]=t[i];log[count,2]=side
            log[count,3]=cash-open_equity;log[count,4]=(cash-open_equity)/entry_risk
            log[count,5]=pos_fee;log[count,6]=pos_fund
            log[count,7]=entry_fill;log[count,8]=fill;log[count,9]=stopmul;log[count,10]=trailmul
            count+=1
        mark[month_id[-1]]=cash
    return cash,mark,month_entries,month_expose,log[:count],fee_total,fund_total,dd

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    all_summary=[];all_months=[];all_trades=[];quality=[]
    dates=pd.date_range("2025-01-01","2026-12-01",freq="MS",tz="Asia/Kolkata").tz_convert("UTC")
    cut=np.array([int(v.timestamp()) for v in dates],np.int64)
    months=dates.tz_convert("Asia/Kolkata").strftime("%Y-%m").tolist()[:-1]
    for symbol in ASSETS:
        print("LOADING",symbol,flush=True)
        d=load(symbol);t=d.time.to_numpy(np.int64)
        fund,fq=funding_arr(symbol,t)
        mid=np.searchsorted(cut,t,side="right")-1
        if mid.min()<0 or mid.max()>=len(months):
            raise RuntimeError(f"invalid IST month IDs: {mid.min()},{mid.max()}")
        q={"symbol":symbol,"n_candles":len(d),"first":str(d.index[0]),
            "last":str(d.index[-1]),**fq}
        setups=0
        for impulse in (1.5,2.5):
            for consistency in (0.67,0.75):
                for volume_ratio in (1.0,1.5):
                    sig,a,h,l,atr,nsig=signals(d,impulse,consistency,volume_ratio)
                    for init in (1.25,2.):
                        for trail in (8.,12.):
                            model=f"accel{impulse:g}_consistency{consistency:g}_vol{volume_ratio:g}_init{init:g}atr_trail{trail:g}atr"
                            cash,marks,entries,exposures,log,fees,funds,dd=replay(
                                t,d.open.to_numpy(float),d.high.to_numpy(float),
                                d.low.to_numpy(float),d.close.to_numpy(float),
                                sig,a,h,l,atr,fund,mid,init,trail,len(months))
                            p=log[:,3]
                            win=p[p>0];loss=p[p<0]
                            pf=win.sum()/-loss.sum() if len(loss) else np.nan
                            ratio=win.mean()/-loss.mean() if len(win) and len(loss) else np.nan
                            nbig=int((log[:,4]>=10).sum())
                            row=dict(symbol=symbol,model=model,signals=nsig,
                                trades=len(log),wins=len(win),losses=len(loss),
                                win_rate_pct=round(100*len(win)/len(log),3) if len(log) else None,
                                profit_factor=round(pf,4) if np.isfinite(pf) else None,
                                avg_win_loss_ratio=round(ratio,4) if np.isfinite(ratio) else None,
                                biggest_winner_R=round(log[:,4].max(),3) if len(log) else None,
                                winners_over_10R=nbig,net_return_pct=round(100*(cash/START_EQUITY-1),3),
                                max_drawdown_pct=round(100*dd,3),
                                fees_usd=round(fees,3),funding_proxy_usd=round(funds,3))
                            prev=START_EQUITY
                            returns={}
                            for im,mon in enumerate(months):
                                eq=marks[im];pct=100*(eq/prev-1)
                                month_row=dict(symbol=symbol,model=model,month_ist=mon,
                                    return_pct=round(pct,4),end_equity=round(eq,5),
                                    entries=int(entries[im]),exposure=int(exposures[im]))
                                all_months.append(month_row)
                                returns[mon]=pct
                                prev=eq
                            row["return_2025_pct"]=round(100*(marks[11]/START_EQUITY-1),3)
                            row["return_2026_pct"]=round(100*(marks[-1]/marks[11]-1),3)
                            row["profit_months"]=sum(x>1e-9 for x in returns.values())
                            row["loss_months"]=sum(x< -1e-9 for x in returns.values())
                            row["active_months"]=int(sum(exposures))
                            all_summary.append(row)
                            for record in log:
                                all_trades.append(dict(symbol=symbol,model=model,
                                    entry_utc=pd.to_datetime(int(record[0]),unit="s",utc=True),
                                    exit_utc=pd.to_datetime(int(record[1]),unit="s",utc=True),
                                    side="LONG" if record[2]>0 else "SHORT",
                                    pnl_usd=round(record[3],5),net_R=round(record[4],5),
                                    fees=round(record[5],5),funding_proxy=round(record[6],5),
                                    entry_fill=round(record[7],4),exit_fill=round(record[8],4)))
                            setups+=1
        quality.append({**q,"variants":setups})
        print("COMPLETED",symbol,setups,"variants",flush=True)
    summ=pd.DataFrame(all_summary)
    monthly=pd.DataFrame(all_months)
    ledger=pd.DataFrame(all_trades)
    summ.to_csv(OUT/"model_comparison.csv",index=False)
    monthly.to_csv(OUT/"monthly_ist.csv.gz",index=False,compression="gzip")
    ledger.to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    # Predeclared pass thresholds; no results are optimized retroactively.
    selected=summ[(summ.return_2025_pct>=500)&(summ.trades>=30)&(summ.win_rate_pct<=40)&
        (summ.avg_win_loss_ratio>=5)&(summ.biggest_winner_R>=10)&
        (summ.profit_factor>=1.5)&(summ.return_2025_pct>0)&
        (summ.return_2026_pct>0)&(summ.max_drawdown_pct>-30)].copy()
    selected.to_csv(OUT/"qualifying_models.csv",index=False)
    # Exploratory asymmetric candidates have a lower PF threshold than confirmed models.
    # Report them transparently but NEVER call them validated without untouched holdout.
    candidate=summ[(summ.return_2025_pct>=500)&(summ.trades>=60)&(summ.win_rate_pct<=40)&
        (summ.avg_win_loss_ratio>=5)&(summ.biggest_winner_R>=10)&
        (summ.profit_factor>=1.3)&(summ.return_2025_pct>0)&
        (summ.return_2026_pct>0)&(summ.max_drawdown_pct>-25)].copy()
    candidate.to_csv(OUT/"promising_exploratory_models.csv",index=False)
    cand_month=[];cand_stats=[];cand_ledger=[]
    for _,chosen in candidate.iterrows():
        sym=chosen["symbol"];model=chosen["model"]
        t=ledger[(ledger.symbol==sym)&(ledger.model==model)].copy()
        t["exit_month_ist"]=pd.to_datetime(t.exit_utc,utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
        w=t[t.pnl_usd>0].pnl_usd.to_numpy(float);loss=t[t.pnl_usd<0].pnl_usd.to_numpy(float)
        vals=t.pnl_usd.to_numpy(float)
        max_l=cur=0
        for v in vals:
            if v<=0:cur+=1;max_l=max(max_l,cur)
            else:cur=0
        top=sorted([float(v) for v in w],reverse=True)
        cand_stats.append(dict(symbol=sym,model=model,trades=len(t),
            max_consecutive_losses=max_l,biggest_profit_usd=round(top[0],4) if top else None,
            top1_fraction_of_positive_pnl=round(top[0]/sum(top),4) if top else None,
            top3_fraction_of_positive_pnl=round(sum(top[:3])/sum(top),4) if top else None,
            net_after_removing_largest_winner_usd=round(sum(vals)-(top[0] if top else 0),4),
            average_positive_trade_usd=round(np.mean(w),4) if len(w) else None,
            average_negative_trade_usd=round(np.mean(loss),4) if len(loss) else None))
        cand_ledger.append(t)
        for mon,group in t.groupby("exit_month_ist"):
            p=group.pnl_usd.to_numpy(float)
            gp=float(p[p>0].sum());gl=float(-p[p<0].sum())
            cand_month.append(dict(symbol=sym,model=model,exit_month_ist=mon,
                closed_trades=len(group),win_trades=int((p>0).sum()),
                loss_trades=int((p<0).sum()),net_realized_usd=round(float(p.sum()),4),
                realized_profit_factor=round(gp/gl,4) if gl else None))
    pd.DataFrame(cand_stats).to_csv(OUT/"candidate_concentration.csv",index=False)
    pd.DataFrame(cand_month).to_csv(OUT/"candidate_monthly_pf.csv",index=False)
    if cand_ledger:pd.concat(cand_ledger,ignore_index=True).to_csv(OUT/"candidate_trade_ledger.csv",index=False)
    meta=dict(study="Independent trend-acceleration impulse with asymmetric trailing",
        tested_period="2025-01-01 to 2026-11-17 UTC",
        signal="Completed 1H 6h-vs-prior-6h acceleration, 12h direction persistence, volume confirmation",
        stop="ATR initial 1.25x/2x; chandelier trail 8x/12x from completed 1H highs/lows",
        sizing="0.5% equity initial stop risk, one position maximum",
        cost="0.05% taker each side plus 18% GST; 2bps adverse slip per execution",
        funding="Delta 1h candles used as rate proxies; missing settlements charged 0.01%",
        missing_funding="Positive rate charged for longs, paid to shorts where source available; 0.01% charge when absent",
        caveats=["Open source historical data already research-exposed; 2026 is not independent untouched holdout",
                 "Monthly NAV and unrealized liquidation fee at IST calendar boundary",
                 "1min bar OHLC cannot provide order book, spread, or exact intrabar order",
                 "The same-minute entry candle stop check deferred to next 1min open",
                 "True settled funding cashflows and liquidation margin not independently verified",
                 "2026 November partial; no 2022-2024 Delta history in repository",
                 "No qualifying model is NOT evidence all asymmetric strategies fail"],
        data=quality,models=len(summ),passing_models=len(selected),promising_exploratory_models=len(candidate))
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
    report=["# Independent trend-acceleration impulse strategy research",
        "",f"**Predeclared qualifying models: {len(selected)}/{len(summ)}**",
        "","## Qualifying results",selected.to_markdown(index=False) if len(selected) else "None",
        "","## Top models by 2025 performance (2026 reported without selecting on it)",
        summ.sort_values("return_2025_pct",ascending=False).head(12).to_markdown(index=False),
        "","## Promising exploratory candidates (not validated)",candidate.to_markdown(index=False) if len(candidate) else "None",
        "","## Candidate trade concentration",pd.DataFrame(cand_stats).to_markdown(index=False) if cand_stats else "None",
        "","## Caution",*[f"- {s}" for s in meta["caveats"]]]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("QUALIFIERS",len(selected))
    print(selected.to_string(index=False))
    print("TOP2025\n",summ.sort_values("return_2025_pct",ascending=False).head(10).to_string(index=False))
if __name__=="__main__":main()
