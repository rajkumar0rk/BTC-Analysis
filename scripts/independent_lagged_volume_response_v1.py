#!/usr/bin/env python3
# Independent paired historical test; no live orders. Source validator vendored. Push-triggered workflow.
"""Native BTC/ETH lagged-volume-response, audited 22 IST months."""
import sys, json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit
sys.path.insert(0,str(Path(__file__).resolve().parent))
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
def load(sym):
    path=Path("data/delta_india")/sym/"1m"
    meta=json.loads((path/"manifest.json").read_text())
    info={x["file"]:x for x in meta["partitions"]}
    chunks=[]
    for month in MONTHS:
        name=month+".csv.gz"; item=info.get(name)
        if item is None or item["missing_minutes"]!=0 or item["observed_candles"]!=item["expected_minutes"]:
            raise RuntimeError("Invalid source partition "+sym+"/"+name)
        p=path/name
        if hashlib.sha256(p.read_bytes()).hexdigest()!=item["sha256_gzip"]:
            raise RuntimeError("SHA mismatch "+sym+"/"+name)
        d=pd.read_csv(p,compression="gzip",usecols=["time","open","high","low","close","volume"])
        if len(d)!=item["observed_candles"]:raise RuntimeError("Row count mismatch")
        chunks.append(d)
    f=pd.concat(chunks,ignore_index=True).sort_values("time",kind="stable")
    t=f.time.to_numpy(np.int64)
    if not (np.diff(t)==60).all():raise RuntimeError("Missing or duplicate minutes")
    f.index=pd.to_datetime(t,unit="s",utc=True)
    if f.isna().any().any():raise RuntimeError("Missing data")
    if ((f.low<=0)|(f.high<f[["open","close","low"]].max(axis=1))|(f.low>f[["open","close"]].min(axis=1))).any():
        raise RuntimeError("Invalid OHLC")
    return f
ROOT=Path("data/delta_india")
OUT=Path("analysis/independent_lagged_volume_response_v1")
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
def metrics(sym,model,asset,signal_threshold,mode,stopmult,rr):
    # Completed hourly OHLC, label at right boundary; enter at next 1m open.
    b=asset[["open","high","low","close"]].resample("1h",label="right",closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last"})
    # Hypothesis: high volume in the first half-hour followed by large
    # directional returns in the second half signals delayed information
    # incorporation. This is observable lead-lag, not observed order flow.
    r=np.log(asset.close/asset.close.shift(1))
    v=asset.volume
    pos=asset.index.minute
    early=(pos<30)
    late=(pos>=30)
    early_vol=v.where(early).resample("1h",label="right",closed="left").sum()
    late_vol=v.where(late).resample("1h",label="right",closed="left").sum()
    early_move=r.where(early).resample("1h",label="right",closed="left").sum()
    late_move=r.where(late).resample("1h",label="right",closed="left").sum()
    # Relative volume front-loading and delayed directional response
    volume_share=early_vol/(early_vol+late_vol).replace(0,np.nan)
    delayed=late_move.abs()/(early_move.abs()+late_move.abs()).replace(0,np.nan)
    signal=volume_share*delayed
    count=asset.close.resample("1h",label="right",closed="left").count()
    prev=b.close.shift(1)
    tr=pd.concat([b.high-b.low,(b.high-prev).abs(),(b.low-prev).abs()],axis=1).max(axis=1)
    atr=tr.rolling(14,min_periods=14).mean()
    ret=np.log(b.close/prev)
    valid=(count==60)&signal.notna()&atr.notna()&(atr>0)&ret.notna()&(ret!=0)
    ev=np.flatnonzero((valid&(persistence<=persistence_threshold)).to_numpy())
    ix=asset.index.get_indexer(b.index[ev])
    keep=(ix>=0)&(ix<len(asset))
    ix=ix[keep];ev=ev[keep]
    sides=(np.where(ret.iloc[ev].to_numpy()>0,1,-1)*mode).astype(np.int32)
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
    row=dict(market=sym,model=model,persistence_threshold=persistence_threshold,mode=mode,stopmult=stopmult,rr=rr,
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
    # Discovery only on BTC 2025. ETH is never used to select candidates.
    btc=load("BTCUSD")
    print("VALIDATED BTCUSD",len(btc),flush=True)
    for persistence_threshold in (0.65,0.80):
        for mode in (1,-1):
            model=f"lagged_volume_response_{persistence_threshold:g}_mode{mode:+d}_SL1.5_RR2"
            row,mon,tdf=metrics("BTCUSD",model,btc,persistence_threshold,mode,1.5,2.)
            summaries.append(row);monthly.extend(mon)
            if not tdf.empty:trades.append(tdf)
            print("BTC_DISCOVERY",model,row["trades"],row["net_return_2025_pct"],flush=True)
    btcsum=pd.DataFrame(summaries)
    chosen=btcsum.sort_values(["net_return_2025_pct","profit_factor"],ascending=False).iloc[0]
    eth=load("ETHUSD")
    print("VALIDATED ETHUSD",len(eth),flush=True)
    model=chosen["model"]
    row,mon,tdf=metrics("ETHUSD",model,eth,float(chosen["persistence_threshold"]),int(chosen["mode"]),1.5,2.)
    summaries.append(row);monthly.extend(mon)
    if not tdf.empty:trades.append(tdf)
    summary=pd.DataFrame(summaries);months=pd.DataFrame(monthly)
    summary.to_csv(OUT/"paired_summary.csv",index=False)
    months.to_csv(OUT/"paired_monthly_22.csv",index=False)
    if trades:pd.concat(trades,ignore_index=True).to_csv(OUT/"paired_trade_ledgers.csv",index=False)
    # BTC ONLY selection on 2025; ETH never enters model or parameter choice.
    ranked=summary[summary.market=="BTCUSD"].copy()
    shared=ranked.sort_values(["net_return_2025_pct","profit_factor"],ascending=False).iloc[0]["model"]
    selected=summary[summary.model==shared].copy()
    selected.to_csv(OUT/"2025_only_selected.csv",index=False)
    quality=dict(source="original Delta India native trade 1m SHA256 checked by load()",
      months=22,initial_equity_usd=1000,risk_per_trade_pct=.5,max_notional_leverage=3,
      taker_fee_each_side=.0005,GST=.18,BTC_slippage_points_per_side=5,ETH_slippage_fraction_each_side=.0002,
      months_nav="Mark-to-market at IST calendar month boundary, open trades retained; monthly PF based on exits",
      missing_first_ist_2025_hours=5.5,excluded_november_2026=True,
      unmodeled=["funding","real order-book spread","market impact","margin/liquidation","lot constraints","live fills"],
      caveat="Sign-run persistence is observable, but does not prove institutional flow or aggressive side; 2026 research-exposed")
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    report=["# Native lagged volume-response paired BTC/ETH audit","",
      "Predeclared completed-hour volume-frontloading x delayed-return-share >=0.35 or 0.45; next 1m open continuation/reversal; stop-first 1m ATR exits.",
      "Same rule on both native instruments. No month-end liquidation. BTC-only 2025 parameter selection; identical frozen rules evaluated on ETH; 2026 historical validation.","",
      "## Complete summary","",summary.to_markdown(index=False),"",
      "## Monthly results","",months.to_markdown(index=False),"",
      "## Execution limitations","",json.dumps(quality,indent=2)]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("LAGGED_VOLUME_RESPONSE_AUDIT_COMPLETE",summary.to_json(orient="records"),flush=True)
if __name__=="__main__":main()
