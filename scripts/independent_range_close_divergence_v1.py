#!/usr/bin/env python3
# Independent paired historical test; no live orders. Source validator vendored. Push-triggered workflow.
"""Native BTC/ETH short-vs-long realized volatility term structure, audited 22 IST months."""
import sys, json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit
sys.path.insert(0,str(Path(__file__).resolve().parent))
from eth_native_crossfamily_v2 import load, MONTHS
ROOT=Path("data/delta_india")
OUT=Path("analysis/independent_range_close_divergence_v1")
FEE=.0005*1.18
@njit(cache=True)
def replay(o,h,l,c,idx,side,dist,hold,slip_abs,slip_frac,stopmult,rr):
    rows=np.zeros((len(idx),11),np.float64)
    equity=1000.;busy=-1;n=0
    for a in range(len(idx)):
        k=int(idx[a]);sd=int(side[a])
        if k<=busy or k<1 or k>=len(c):continue
        stopdistance=dist[a]*stopmult
        if not np.isfinite(stopdistance) or stopdistance<=0:continue
        entry=o[k]+sd*(slip_abs+slip_frac*o[k])
        qty=min(equity*.005/stopdistance,equity*3./entry)
        if qty<=0:continue
        stop=entry-sd*stopdistance;tp=entry+sd*stopdistance*rr
        end=min(k+hold-1,len(c)-1);exitprice=c[end];j=end
        for t in range(k,end+1):
            if (sd==1 and l[t]<=stop) or (sd==-1 and h[t]>=stop):
                exitprice=min(stop,o[t]) if sd==1 else max(stop,o[t]);j=t;break
            if (sd==1 and h[t]>=tp) or (sd==-1 and l[t]<=tp):
                exitprice=tp;j=t;break
        px=exitprice-sd*(slip_abs+slip_frac*exitprice)
        pnl=qty*(sd*(px-entry)-FEE*(entry+px))
        rows[n,0]=k;rows[n,1]=j;rows[n,2]=sd;rows[n,3]=entry;rows[n,4]=px
        rows[n,5]=qty;rows[n,6]=pnl;rows[n,7]=equity;equity+=pnl;rows[n,8]=equity
        rows[n,9]=stop;rows[n,10]=tp
        n+=1;busy=j
        if equity<=0:break
    return rows[:n]
def metrics(sym,model,asset,jump_threshold,shock_threshold,stopmult,rr):
    # Completed hourly OHLC, label at the right boundary; enter at next 1m open.
    b=asset[["open","high","low","close"]].resample("1h",label="right",closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last"})
    # Completed-hour high-low excursions relative to close-to-close displacement.
    r=np.log(b.close/b.close.shift(1))
    excursion=np.log(b.high/b.low).pow(2).rolling(6,min_periods=6).sum()
    displacement=r.pow(2).rolling(6,min_periods=6).sum()
    jump=excursion/displacement.replace(0,np.nan)
    rms=np.sqrt(r.shift(1).pow(2).rolling(24,min_periods=24).mean())
    shock=r.abs()/rms.replace(0,np.nan)
    prev=b.close.shift(1)
    tr=pd.concat([b.high-b.low,(b.high-prev).abs(),(b.low-prev).abs()],axis=1).max(axis=1)
    atr=tr.rolling(14,min_periods=14).mean()
    valid=jump.notna()&shock.notna()&atr.notna()&(atr>0)
    ev=np.flatnonzero((valid & (jump>=jump_threshold) & (shock>=shock_threshold)).to_numpy())
    ix=asset.index.get_indexer(b.index[ev])
    keep=(ix>=0)&(ix<len(asset))
    ix=ix[keep];ev=ev[keep]
    sides=np.where(r.iloc[ev].to_numpy()>0,-1,1).astype(np.int32)
    distances=atr.iloc[ev].to_numpy(float)
    o=asset.open.to_numpy(float);h=asset.high.to_numpy(float);l=asset.low.to_numpy(float);c=asset.close.to_numpy(float)
    led=replay(o,h,l,c,ix.astype(np.int64),sides,distances,720,5. if sym=="BTCUSD" else 0.,0. if sym=="BTCUSD" else .0002,stopmult,rr)
    if len(led):
        entry=led[:,0].astype(int);ex=led[:,1].astype(int)
        tdf=pd.DataFrame(dict(market=sym,model=model,entry_utc=asset.index[entry].astype(str),exit_utc=asset.index[ex].astype(str),
           side=led[:,2].astype(int),entry_price=led[:,3],exit_price=led[:,4],qty=led[:,5],net_pnl_usd=led[:,6],
           equity_before_usd=led[:,7],equity_after_usd=led[:,8],stop=led[:,9],target=led[:,10]))
        exitcodes=np.asarray(asset.index[ex].tz_convert("Asia/Kolkata").year*100+asset.index[ex].tz_convert("Asia/Kolkata").month)
    else:tdf=pd.DataFrame();exitcodes=np.array([],int)
    # Account NAV mark at each IST month boundary: realized PnL plus open trade unrealized
    # using close mark and estimated liquidation cost (fee+slippage). No month-end forced exit.
    ist=asset.index.tz_convert("Asia/Kolkata")
    monthcodes=np.asarray(ist.year*100+ist.month,dtype=int)
    months=[];startnav=1000.;equitypath=[1000.]
    for month in MONTHS:
        mc=int(month.replace("-",""))
        last=np.flatnonzero(monthcodes==mc)[-1]
        # Trade PnL from exits <= boundary, no future trades included
        realized=1000.+float(led[led[:,1]<=last,6].sum()) if len(led) else 1000.
        active=led[(led[:,0]<=last)&(led[:,1]>last)] if len(led) else np.empty((0,11))
        unreal=0.
        for q in active:
            sd=q[2];px=c[last]-sd*(5. if sym=="BTCUSD" else .0002*c[last])
            unreal+=q[5]*(sd*(px-q[3])-FEE*(q[3]+px))
        endnav=realized+unreal
        vals=led[exitcodes==mc,6] if len(led) else np.array([])
        gain=float(vals[vals>0].sum());loss=float(-vals[vals<0].sum())
        pf=(gain/loss if loss>0 else ("infinite" if gain>0 else None))
        ret=100*(endnav/startnav-1) if startnav>0 else -100.
        months.append(dict(market=sym,model=model,month=month,profit_factor=pf,net_return_pct=ret,
          net_exit_pnl_usd=float(vals.sum()),month_nav_change_usd=endnav-startnav,
          trades=len(vals),wins=int((vals>0).sum()),losses=int((vals<0).sum()),
          nav_start_usd=startnav,nav_end_usd=endnav,open_positions_at_month_end=len(active)))
        startnav=endnav;equitypath.append(endnav)
    m=pd.DataFrame(months)
    strong5=int(((m.net_return_pct>=5)&m.profit_factor.map(lambda x:x=="infinite" or isinstance(x,(int,float)) and x>=1.5)&(m.trades>=3)).sum())
    strong10=int(((m.net_return_pct>=10)&m.profit_factor.map(lambda x:x=="infinite" or isinstance(x,(int,float)) and x>=1.5)&(m.trades>=3)).sum())
    totalgain=float(led[led[:,6]>0,6].sum()) if len(led) else 0.
    totalloss=float(-led[led[:,6]<0,6].sum()) if len(led) else 0.
    pf=totalgain/totalloss if totalloss>0 else None
    eq=np.array(equitypath)
    row=dict(market=sym,model=model,jump_threshold=jump_threshold,shock_threshold=shock_threshold,stopmult=stopmult,rr=rr,
      profit_factor=pf,net_return_22m_pct=100*(eq[-1]/eq[0]-1),
      net_return_2025_pct=100*(eq[12]/eq[0]-1),net_return_2026_jan_oct_pct=100*(eq[-1]/eq[12]-1),
      year2025_above_500pct=bool(eq[12]>6*eq[0]),year2026_ytd_above_500pct=bool(eq[-1]>6*eq[12]),
      strong_pf1p5_return5_months=strong5,strong_pf1p5_return10_months=strong10,
      positive_months=int((m.net_return_pct>0).sum()),trades=len(led),
      wins=int((led[:,6]>0).sum()) if len(led) else 0,losses=int((led[:,6]<0).sum()) if len(led) else 0,
      max_month_end_nav_drawdown_pct=float(100*(eq/np.maximum.accumulate(eq)-1).min()),
      worst_month_pct=float(m.net_return_pct.min()))
    return row,months,tdf
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    summaries=[];monthly=[];trades=[]
    for sym in ("BTCUSD","ETHUSD"):
        asset=load(sym)
        print("VALIDATED",sym,len(asset),flush=True)
        for jump_threshold in (3.0,5.0):
            for shock_threshold in (.5,1.0):
                model=f"range_close_{jump_threshold:g}_shock{shock_threshold:g}_SL1.5_RR2"
                row,mon,tdf=metrics(sym,model,asset,jump_threshold,shock_threshold,1.5,2.)
                summaries.append(row);monthly.extend(mon)
                if not tdf.empty:trades.append(tdf)
                print("RESULT",sym,model,row["trades"],row["net_return_22m_pct"],flush=True)
    summary=pd.DataFrame(summaries);months=pd.DataFrame(monthly)
    summary.to_csv(OUT/"paired_summary.csv",index=False)
    months.to_csv(OUT/"paired_monthly_22.csv",index=False)
    if trades:pd.concat(trades,ignore_index=True).to_csv(OUT/"paired_trade_ledgers.csv",index=False)
    # Select parameter combination using ONLY 2025 BTC+ETH results, never 2026
    ranked=summary.assign(train_score=summary.net_return_2025_pct)
    shared=ranked.groupby('model',as_index=False).train_score.mean().sort_values('train_score',ascending=False).iloc[0]['model']
    selected=ranked[ranked.model==shared].copy()
    selected.to_csv(OUT/"2025_only_selected.csv",index=False)
    quality=dict(source="original Delta India native trade 1m SHA256 checked by load()",
      months=22,initial_equity_usd=1000,risk_per_trade_pct=.5,max_notional_leverage=3,
      taker_fee_each_side=.0005,GST=.18,BTC_slippage_points_per_side=5,ETH_slippage_fraction_each_side=.0002,
      months_nav="Mark-to-market at IST calendar month boundary, open trades retained; monthly PF based on exits",
      missing_first_ist_2025_hours=5.5,excluded_november_2026=True,
      unmodeled=["funding","real order-book spread","market impact","margin/liquidation","lot constraints","live fills"],
      caveat="Range-to-close variance discrepancy is observable but does not identify actual liquidity replenishment or forced flow; 2026 already research-exposed")
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    report=["# Native range-vs-close variance divergence paired BTC/ETH audit","",
      "Predeclared completed-hour six-hour sum(log(high/low)^2) / sum(log(close/previous close)^2) >=3/5 and last hour shock >=0.5/1.0 times prior 24h RMS; fade last hour at next 1m open, 1m stop-first ATR exits.",
      "Same rule on both native instruments. No month-end liquidation. 2025-only parameter selection, 2026 historical validation.","",
      "## Complete summary","",summary.to_markdown(index=False),"",
      "## Monthly results","",months.to_markdown(index=False),"",
      "## Execution limitations","",json.dumps(quality,indent=2)]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("RANGE_CLOSE_DIVERGENCE_AUDIT_COMPLETE",summary.to_json(orient="records"),flush=True)
if __name__=="__main__":main()
