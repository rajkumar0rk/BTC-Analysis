#!/usr/bin/env python3
"""Independent 5m displacement/volume climax continuation with convex ATR trailing.
Causal signal at close of 5m bar, enter next 1m open. No prior study imports.
2025 full year vs 2026 partial, explicitly not a full second calendar year.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit

OUT=Path("analysis/volume_climax_continuation_20261119")
FEE=.0005*1.18; SLIP=.0002; RISK=.005; MISSING_FUND=.0001
@njit(cache=True)
def replay(t,o,h,l,c,signal,atr,update_high,update_low,update_atr,funding,months,init_mult,trail_mult):
    cash=1000.;side=0;qty=0.;stop=0.;extreme=0.;fill=0.;startcash=0.;startfee=0.;fundsum=0.;ent_i=0;risk=0.
    peak=1000.;maxdd=0.;fees=0.;fundingpaid=0.
    trades=np.zeros((4000,9),np.float64);nt=0
    equity_month=np.full(23,np.nan)
    for i in range(len(t)):
        if side:
            if update_atr[i]>0:
                if side==1:
                    extreme=max(extreme,update_high[i]);stop=max(stop,extreme-trail_mult*update_atr[i])
                else:
                    extreme=min(extreme,update_low[i]);stop=min(stop,extreme+trail_mult*update_atr[i])
            if t[i]%28800==0:
                f=funding[i]
                payment=abs(qty*o[i])*MISSING_FUND if np.isnan(f) else qty*o[i]*side*f
                cash-=payment;fundsum+=payment;fundingpaid+=payment
            if (side==1 and l[i]<=stop) or (side==-1 and h[i]>=stop):
                px=min(o[i],stop) if side==1 else max(o[i],stop)
                exitfill=px*(1-side*SLIP)
                fee=abs(qty*exitfill)*FEE;fees+=fee
                cash+=side*qty*(exitfill-fill)-fee
                if nt<len(trades):
                    trades[nt,:]=[t[ent_i],t[i],side,cash-startcash,(cash-startcash)/risk,startfee+fee,fundsum,fill,exitfill];nt+=1
                side=0;qty=0.
        if side==0 and signal[i]!=0 and atr[i]>0 and cash>0:
            s=int(signal[i]);p=o[i]*(1+s*SLIP);distance=init_mult*atr[i]
            q=cash*RISK/distance
            if q*p<=cash*10:
                side=s;fill=p;qty=q;stop=p-s*distance;extreme=p;ent_i=i
                startcash=cash;risk=cash*RISK;fundsum=0.
                startfee=q*p*FEE;fees+=startfee;cash-=startfee
        equity=cash+side*qty*(c[i]*(1-side*SLIP)-fill)-abs(qty*c[i])*FEE if side else cash
        peak=max(peak,equity);maxdd=min(maxdd,equity/peak-1.)
        if i==len(t)-1 or months[i]!=months[i+1]:equity_month[months[i]]=equity
    if side:
        i=len(t)-1;ex=c[i]*(1-side*SLIP);fee=qty*ex*FEE;fees+=fee
        cash+=side*qty*(ex-fill)-fee
        if nt<len(trades):
            trades[nt,:]=[t[ent_i],t[i],side,cash-startcash,(cash-startcash)/risk,startfee+fee,fundsum,fill,ex];nt+=1
        equity_month[months[-1]]=cash
    return cash,maxdd,fees,fundingpaid,equity_month,trades[:nt]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    allmodels=[];allmonths=[];alltrades=[];q=[]
    for sym in ("BTCUSD","ETHUSD"):
        files=sorted((Path("data/delta_india")/sym/"1m").glob("20??-??.csv.gz"))
        d=pd.concat([pd.read_csv(p,compression="gzip",usecols=["time","open","high","low","close","volume"]) for p in files],ignore_index=True)
        d=d[(d.time>=pd.Timestamp("2025-01-01",tz="UTC").timestamp())&(d.time<pd.Timestamp("2026-11-18",tz="UTC").timestamp())]
        d=d.sort_values("time").reset_index(drop=True)
        t=d.time.to_numpy(np.int64)
        if len(t)<900000 or np.any(np.diff(t)!=60):raise RuntimeError("bad minute data "+sym)
        if not all(np.isfinite(d[k]).all() for k in ("open","high","low","close","volume")):raise RuntimeError("nonfinite data")
        d.index=pd.to_datetime(t,unit="s",utc=True)
        h=d.resample("5min",closed="left",label="left").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
        if not d.close.resample("5min").count().eq(5).all():raise RuntimeError("missing 5m")
        pc=h.close.shift(1)
        tr=pd.concat([h.high-h.low,(h.high-pc).abs(),(h.low-pc).abs()],axis=1).max(axis=1)
        atr=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
        volref=h.volume.shift(1).rolling(288,min_periods=288).median()
        barbody=(h.close-h.open).abs()
        barspan=h.high-h.low
        bodystrength=barbody/barspan.replace(0,np.nan)
        # Displacement: 5m range vs previous completed ATR, body and volume
        # extreme; second 5m bar confirms by holding beyond midpoint without
        # revisiting opposite side of impulse. Signal on second bar CLOSE.
        preatr=atr.shift(1)
        impulse_up=(h.close>h.open)&(bodystrength>.7)&(barspan>2*preatr)
        impulse_dn=(h.close<h.open)&(bodystrength>.7)&(barspan>2*preatr)
        follow_up=(h.low>h.low.shift(1)+(h.high.shift(1)-h.low.shift(1))*.5)&(h.close>h.close.shift(1))
        follow_dn=(h.high<h.high.shift(1)-(h.high.shift(1)-h.low.shift(1))*.5)&(h.close<h.close.shift(1))
        fs=Path("data/delta_india")/sym/"institutional/history/funding_1h"
        f=pd.concat([pd.read_csv(p,compression="gzip",usecols=["time","close"]) for p in sorted(fs.glob("20??-??.csv.gz"))],ignore_index=True)
        fmap={int(ts)+3600:float(v)/100 for ts,v in zip(f.time,f.close) if np.isfinite(v) and abs(v)<5}
        funding=np.zeros(len(t));miss=0
        for i in np.flatnonzero(t%28800==0):
            funding[i]=fmap.get(int(t[i]),np.nan)
            if np.isnan(funding[i]):miss+=1
        local=d.index.tz_convert("Asia/Kolkata")
        months=((local.year-2025)*12+local.month-1).to_numpy(np.int32)
        if months.min()!=0 or months.max()!=22:raise RuntimeError("month bounds")
        print("LOADED",sym,len(t),"funding_missing",miss,flush=True)
        for vratio in (3.,5.,8.,12.):
            for follow in (False,True):
                goodvol=h.volume>volref*vratio
                up=impulse_up&goodvol
                dn=impulse_dn&goodvol
                if follow:
                    up=up.shift(1,fill_value=False)&follow_up
                    dn=dn.shift(1,fill_value=False)&follow_dn
                sig5=np.where(up,1,np.where(dn,-1,0)).astype(np.int8)
                sig=np.zeros(len(t),np.int8);sigatr=np.zeros(len(t))
                uh=np.zeros(len(t));ul=np.zeros(len(t));ua=np.zeros(len(t))
                # Hour is not involved. Every completed 5m bar contributes
                # trailing extremes; never use the still-open bar.
                for k in range(1,len(h)):
                    i=k*5
                    if i>=len(t):break
                    sig[i]=sig5[k-1]
                    sigatr[i]=preatr.iloc[k-1] if np.isfinite(preatr.iloc[k-1]) else 0.
                    uh[i]=h.high.iloc[k-1];ul[i]=h.low.iloc[k-1]
                    ua[i]=atr.iloc[k-1] if np.isfinite(atr.iloc[k-1]) else 0.
                for init in (1.,1.5):
                    for trail in (5.,9.):
                        model=f"vol{vratio:g}_confirm{int(follow)}_stop{init:g}_trail{trail:g}"
                        cash,dd,fees,fund,marks,trades=replay(t,d.open.to_numpy(float),d.high.to_numpy(float),
                            d.low.to_numpy(float),d.close.to_numpy(float),sig,sigatr,uh,ul,ua,funding,months,init,trail)
                        pnl=trades[:,3];win=pnl[pnl>0];loss=pnl[pnl<0]
                        pf=float(win.sum()/-loss.sum()) if len(loss) else None
                        ratio=float(win.mean()/-loss.mean()) if len(win) and len(loss) else None
                        prev=1000.
                        for i,eq in enumerate(marks):
                            mon=f"{2025+i//12}-{i%12+1:02d}"
                            allmonths.append(dict(symbol=sym,model=model,month_ist=mon,
                                return_pct=round(100*(eq/prev-1),5),end_equity=round(eq,5)))
                            prev=eq
                        m=dict(symbol=sym,model=model,signals=int((sig!=0).sum()),
                            trades=len(trades),wins=len(win),losses=len(loss),
                            win_rate_pct=round(100*len(win)/len(trades),4) if len(trades) else None,
                            avg_win_loss_ratio=round(ratio,4) if ratio else None,
                            profit_factor=round(pf,4) if pf else None,
                            biggest_winner_R=round(float(trades[:,4].max()),4) if len(trades) else None,
                            winners_over_10R=int((trades[:,4]>=10).sum()),
                            return_2025_pct=round(100*(marks[11]/1000-1),4),
                            return_2026_partial_pct=round(100*(marks[-1]/marks[11]-1),4),
                            total_return_pct=round(100*(cash/1000-1),4),
                            max_drawdown_pct=round(dd*100,4),
                            fees_usd=round(fees,4),funding_proxy_usd=round(fund,4),
                            profitable_months=sum(allmonths[-23+i]["return_pct"]>0 for i in range(23)),
                            losing_months=sum(allmonths[-23+i]["return_pct"]<0 for i in range(23)))
                        allmodels.append(m)
                        for r in trades:
                            alltrades.append(dict(symbol=sym,model=model,
                                entry_utc=pd.to_datetime(int(r[0]),unit="s",utc=True),
                                exit_utc=pd.to_datetime(int(r[1]),unit="s",utc=True),
                                side="LONG" if r[2]>0 else "SHORT",net_usd=round(r[3],6),
                                net_R=round(r[4],6),fees_usd=round(r[5],6),
                                funding_proxy_usd=round(r[6],6),
                                entry_fill=round(r[7],5),exit_fill=round(r[8],5)))
        q.append(dict(symbol=sym,minutes=len(t),first=str(d.index[0]),last=str(d.index[-1]),
            funding_missing=miss))
    summary=pd.DataFrame(allmodels)
    ledger=pd.DataFrame(alltrades)
    summary.to_csv(OUT/"comparison.csv",index=False)
    pd.DataFrame(allmonths).to_csv(OUT/"monthly.csv.gz",index=False)
    ledger.to_csv(OUT/"trade_ledger.csv.gz",index=False)
    passing=summary[(summary.trades>=30)&(summary.win_rate_pct<=40)&
        (summary.avg_win_loss_ratio>=5)&(summary.biggest_winner_R>=10)&
        (summary.profit_factor>=1.5)&(summary.return_2025_pct>500)&
        (summary.return_2026_partial_pct>0)&(summary.max_drawdown_pct>-30)]
    passing.to_csv(OUT/"qualifying.csv",index=False)
    meta=dict(strategy="5m extreme-volume directional displacement with optional next-bar confirmation",
        grid="volume 3/5/8/12x prior 24h median, confirmation optional, ATR stop 1/1.5, trail 5/9",
        entry="next 1m open after 5m signal close",exit="1m wick stop; 5m completed bar ATR chandelier",
        costs="0.05% taker per side, 18% GST, 2bps adverse slippage per execution",
        funding="Delta 1h funding close proxy at 8h UTC settlements; 0.01% adverse when missing",
        risk="0.5% equity per initial stop, max 10x notional leverage, one position",
        caveats=["2026 incomplete; >500% target only testable for 2025 full calendar year",
                 "No untouched holdout; this is exploratory historical research",
                 "No L1 depth, actual fill, contract margin, liquidation or true funding cashflows",
                 "Same entry minute stop monitoring deferred to next minute",
                 "Extreme-volume thresholds are exploratory grid, not optimized validated parameters"],
        source=q,configurations=len(summary),qualifying=len(passing))
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
    top=summary.sort_values("return_2025_pct",ascending=False).head(12)
    (OUT/"REPORT.md").write_text("# Independent 5m volume-climax continuation\n\n"+
        f"Predeclared strict qualifiers: **{len(passing)}/{len(summary)}**.\n\n"+
        "## Top 2025 net returns\n\n"+top.to_markdown(index=False)+
        "\n\n## Strict qualifiers\n\n"+(passing.to_markdown(index=False) if len(passing) else "None")+
        "\n\n## Data and execution limitations\n\n"+
        "\n".join("- "+x for x in meta["caveats"])+"\n")
    print("RESULT",len(passing),"QUALIFIERS\n",top.to_string(index=False),flush=True)
if __name__=="__main__":main()
