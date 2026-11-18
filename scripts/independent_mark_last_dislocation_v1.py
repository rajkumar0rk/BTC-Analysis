#!/usr/bin/env python3
"""Independent native MARK vs last-price dislocation replay, paired BTC/ETH, 2025-2026."""
import sys, json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit
sys.path.insert(0,str(Path(__file__).resolve().parent))
from eth_native_crossfamily_v2 import load, MONTHS
ROOT=Path("data/delta_india")
OUT=Path("analysis/independent_mark_last_dislocation_v1")
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
def get_mark(sym,idx):
    base=ROOT/sym/"institutional/history/mark_1m"
    meta=json.loads((ROOT/sym/"institutional/history_manifest.json").read_text())
    assert meta["series"]["mark_1m"]["native_source_symbol"]=="MARK:"+sym
    chunks=[]
    for month in MONTHS:
        p=base/(month+".csv.gz")
        d=pd.read_csv(p,compression="gzip")
        if "time" not in d.columns or "close" not in d.columns:raise RuntimeError("Mark schema "+str(d.columns))
        chunks.append(d[["time","close"]])
    f=pd.concat(chunks,ignore_index=True)
    f.index=pd.to_datetime(f.time.astype("int64"),unit="s",utc=True)
    assert f.index.equals(idx),"Mark 1m must align native trade-price 1m"
    assert f.close.notna().all() and (f.close>0).all()
    return f.close.astype(float)
def metrics(sym,model,asset,mark,threshold,stopmult,rr):
    # completed 5m candles: last and mark sampled at right edge; signal placed at NEXT minute open
    last5=asset.close.resample("5min",label="right",closed="left").last()
    mark5=mark.resample("5min",label="right",closed="left").last()
    prem=last5/mark5-1
    avg=prem.shift(1).rolling(288,min_periods=288).mean()
    std=prem.shift(1).rolling(288,min_periods=288).std()
    z=(prem-avg)/std.replace(0,np.nan)
    # Independent last-price 5m ATR, using completed candles only
    b=asset[["open","high","low","close"]].resample("5min",label="right",closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last"})
    prev=b.close.shift()
    tr=pd.concat([b.high-b.low,(b.high-prev).abs(),(b.low-prev).abs()],axis=1).max(axis=1)
    atr=tr.rolling(14,min_periods=14).mean()
    valid=z.notna() & atr.notna() & (std>0)
    # don't let extreme nonsensical mark dislocations become signals
    valid &= prem.abs()<.03
    ev=np.flatnonzero((valid & (z.abs()>=threshold)).to_numpy())
    ix=asset.index.get_indexer(z.index[ev])
    keep=(ix>=0)&(ix<len(asset))
    ix=ix[keep];ev=ev[keep]
    sides=np.where(z.iloc[ev].to_numpy()>0,-1,1).astype(np.int32)
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
    row=dict(market=sym,model=model,threshold=threshold,stopmult=stopmult,rr=rr,
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
        asset=load(sym);mark=get_mark(sym,asset.index)
        print("VALIDATED",sym,len(asset),float((asset.close/mark-1).abs().median()),flush=True)
        for threshold in (2.,3.):
            for stopmult in (1.5,2.5):
                model=f"mark_last_z{threshold:g}_SL{stopmult:g}_RR2"
                row,mon,tdf=metrics(sym,model,asset,mark,threshold,stopmult,2.)
                summaries.append(row);monthly.extend(mon)
                if not tdf.empty:trades.append(tdf)
                print("RESULT",sym,model,row["trades"],row["net_return_22m_pct"],flush=True)
    summary=pd.DataFrame(summaries);months=pd.DataFrame(monthly)
    summary.to_csv(OUT/"paired_summary.csv",index=False)
    months.to_csv(OUT/"paired_monthly_22.csv",index=False)
    if trades:pd.concat(trades,ignore_index=True).to_csv(OUT/"paired_trade_ledgers.csv",index=False)
    # Select parameter combination using ONLY 2025 BTC+ETH results, never 2026
    ranked=summary.assign(train_score=summary.net_return_2025_pct+summary.profit_factor.fillna(0)*2)
    selected=ranked.groupby("market").apply(lambda x:x.sort_values("train_score",ascending=False).head(1),include_groups=False).reset_index()
    selected.to_csv(OUT/"2025_only_selected.csv",index=False)
    quality=dict(source="original Delta India native trade 1m SHA256 checked by load() and native MARK: 1m history",
      marks_validated="native mark timestamps and density equal trade price timestamps",
      months=22,initial_equity_usd=1000,risk_per_trade_pct=.5,max_notional_leverage=3,
      taker_fee_each_side=.0005,GST=.18,BTC_slippage_points_per_side=5,ETH_slippage_fraction_each_side=.0002,
      months_nav="Mark-to-market at IST calendar month boundary, open trades retained; monthly PF based on exits",
      missing_first_ist_2025_hours=5.5,excluded_november_2026=True,
      unmodeled=["funding","real order-book spread","market impact","margin/liquidation","lot constraints","live fills"],
      caveat="mark price is an exchange calculation, not independently executable; basis may be mechanical and 2026 already researched")
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    report=["# Native mark-to-last dislocation paired BTC/ETH audit","",
      "Predeclared 5m premium z-score >2 or >3, 24h rolling baseline, fade at next 1m open, 1m stop-first ATR exits.",
      "Same rule on both native instruments. No month-end liquidation. 2025-only parameter selection, 2026 historical validation.","",
      "## Complete summary","",summary.to_markdown(index=False),"",
      "## Monthly results","",months.to_markdown(index=False),"",
      "## Execution limitations","",json.dumps(quality,indent=2)]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("AUDIT_COMPLETE",summary.to_json(orient="records"),flush=True)
if __name__=="__main__":main()
