#!/usr/bin/env python3
"""Native BTC/ETH sequential clustered extreme-arrival relaxation differential, audited 22 IST months."""
import sys, json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit
sys.path.insert(0,str(Path(__file__).resolve().parent))
from eth_native_crossfamily_v2 import load, MONTHS
ROOT=Path("data/delta_india")
OUT=Path("analysis/independent_extreme_cluster_relaxation_v1")
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
def signals(b, kappa, threshold):
    # kappa = abnormal magnitude multiplier, threshold = required prior event count.
    # Uses only fully closed hourly returns, and previous 48h reference median.
    r=np.log(b.close/b.close.shift(1))
    ref=r.abs().shift(1).rolling(48,min_periods=48).median().replace(0,np.nan)
    extreme=(r.abs()/ref)>kappa
    prior=extreme.shift(1).rolling(8,min_periods=8).sum()
    # First quiet hour following an extreme, after a dense 8-hour cluster.
    active=b["complete"] & (~extreme) & extreme.shift(1).fillna(False) & (prior>=threshold)
    # Direction of the preceding 8-hour net move, determined at boundary.
    drift=r.rolling(8,min_periods=8).sum()
    active=active & drift.notna() & (drift!=0)
    ev=np.flatnonzero(active.to_numpy(bool))
    direction=np.where(drift.iloc[ev].to_numpy(float)>0,1,-1).astype(np.int32)
    return ev,direction

def metrics(sym,model,asset,b,events,directions,atr,direction_mode,kappa,threshold,slip_factor=1.):
    event_pos=asset.index.searchsorted(b.index[events])
    good=(event_pos>=1)&(event_pos<len(asset)-720)&np.isfinite(atr.iloc[events].to_numpy(float))&(atr.iloc[events].to_numpy(float)>0.)
    ix=event_pos[good].astype(np.int64)
    sides=directions[good]*direction_mode
    distances=atr.iloc[events[good]].to_numpy(float)
    o=asset.open.to_numpy(float);h=asset.high.to_numpy(float)
    l=asset.low.to_numpy(float);c=asset.close.to_numpy(float)
    btcslip=5.*slip_factor if sym=="BTCUSD" else 0.
    ethslip=.0002*slip_factor if sym=="ETHUSD" else 0.
    led=replay(o,h,l,c,ix,sides,distances,720,btcslip,ethslip,1.5,2.5)
    if len(led):
        entry=led[:,0].astype(int);ex=led[:,1].astype(int)
        tdf=pd.DataFrame(dict(market=sym,model=model,entry_utc=asset.index[entry].astype(str),
            exit_utc=asset.index[ex].astype(str),side=led[:,2].astype(int),
            entry_price=led[:,3],exit_price=led[:,4],qty=led[:,5],net_pnl_usd=led[:,6],
            equity_before_usd=led[:,7],equity_after_usd=led[:,8],stop=led[:,9],target=led[:,10]))
        ext=asset.index[ex].tz_convert("Asia/Kolkata")
        exitcodes=np.asarray(ext.year*100+ext.month,dtype=np.int32)
    else:
        tdf=pd.DataFrame();exitcodes=np.array([],int)
    ist=asset.index.tz_convert("Asia/Kolkata")
    mcodes=np.asarray(ist.year*100+ist.month,dtype=np.int32)
    months=[];startnav=1000.;equitypath=[1000.]
    for month in MONTHS:
        mc=int(month.replace("-",""))
        at=np.flatnonzero(mcodes==mc)
        if not len(at):
            raise RuntimeError("Missing IST month "+month)
        last=at[-1]
        realized=1000.+float(led[led[:,1]<=last,6].sum()) if len(led) else 1000.
        active=led[(led[:,0]<=last)&(led[:,1]>last)] if len(led) else np.empty((0,11))
        unreal=0.
        for q in active:
            sd=q[2]
            px=c[last]-sd*(btcslip+ethslip*c[last])
            unreal+=q[5]*(sd*(px-q[3])-FEE*(q[3]+px))
        endnav=realized+unreal
        vals=led[exitcodes==mc,6] if len(led) else np.array([])
        gain=float(vals[vals>0].sum());loss=float(-vals[vals<0].sum())
        pf=(gain/loss if loss>0. else ("infinite" if gain>0. else None))
        ret=100.*(endnav/startnav-1.) if startnav>0. else -100.
        months.append(dict(market=sym,model=model,month=month,profit_factor=pf,
            net_return_pct=ret,net_exit_pnl_usd=float(vals.sum()),
            month_nav_change_usd=endnav-startnav,trades=len(vals),
            wins=int((vals>0).sum()),losses=int((vals<0).sum()),
            nav_start_usd=startnav,nav_end_usd=endnav,
            open_positions_at_month_end=len(active)))
        startnav=endnav;equitypath.append(endnav)
    m=pd.DataFrame(months)
    qualifies=m.profit_factor.map(lambda x:x=="infinite" or isinstance(x,(int,float)) and x>=1.5)
    strong5=int((qualifies&(m.net_return_pct>=5.)&(m.trades>=3)).sum())
    strong10=int((qualifies&(m.net_return_pct>=10.)&(m.trades>=3)).sum())
    gain=float(led[led[:,6]>0.,6].sum()) if len(led) else 0.
    loss=float(-led[led[:,6]<0.,6].sum()) if len(led) else 0.
    pf=gain/loss if loss>0 else ("infinite" if gain>0 else None)
    eq=np.asarray(equitypath)
    row=dict(market=sym,model=model,extreme_multiplier=kappa,min_cluster_events=threshold,
        direction="continuation" if direction_mode==1 else "contrarian",
        slippage_multiplier=slip_factor,profit_factor=pf,
        net_return_22m_pct=100.*(eq[-1]/eq[0]-1.),
        net_return_2025_pct=100.*(eq[12]/eq[0]-1.),
        net_return_2026_jan_oct_pct=100.*(eq[-1]/eq[12]-1.) if eq[12]>0 else -100.,
        year2025_above_500pct=bool(eq[12]>6.*eq[0]),
        year2026_ytd_above_500pct=bool(eq[-1]>6.*eq[12]),
        strong_pf1p5_return5_months=strong5,strong_pf1p5_return10_months=strong10,
        positive_months=int((m.net_return_pct>0).sum()),
        trades=len(led),wins=int((led[:,6]>0).sum()) if len(led) else 0,
        losses=int((led[:,6]<0).sum()) if len(led) else 0,
        max_monthend_nav_drawdown_pct=float(100.*(eq/np.maximum.accumulate(eq)-1.).min()),
        worst_month_pct=float(m.net_return_pct.min()))
    return row,months,tdf

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    summaries=[];monthly=[];trades=[]
    event_details={};assets={}
    import hashlib
    source_hash={}
    for sym in ("BTCUSD","ETHUSD"):
        asset=load(sym)
        # Keep exactly the first 22 complete IST calendar months; no November 2026.
        ist=asset.index.tz_convert("Asia/Kolkata")
        mcodes=np.asarray(ist.year*100+ist.month,dtype=np.int32)
        last=np.flatnonzero(mcodes==202610)[-1]
        asset=asset.iloc[:last+1].copy()
        assets[sym]=asset
        b=asset[["open","high","low","close"]].resample("1h",label="right",closed="left").agg(
            {"open":"first","high":"max","low":"min","close":"last"})
        counts=asset.close.resample("1h",label="right",closed="left").count()
        b["complete"]=(counts==60)
        prev=b.close.shift(1)
        tr=pd.concat([b.high-b.low,(b.high-prev).abs(),(b.low-prev).abs()],axis=1).max(axis=1)
        atr=tr.rolling(14,min_periods=14).mean()
        event_details[sym]=(b,atr)
        source_hash[sym]=hashlib.sha256((ROOT/sym/"1m"/"manifest.json").read_bytes()).hexdigest()
        print("LOADED_VERIFIED",sym,len(asset),len(b),flush=True)
        for kap in (2.0,2.5):
            for threshold in (3.,4.):
                ev,dr=signals(b,kap,threshold)
                for side in (1,-1):
                    label="cont" if side==1 else "fade"
                    model=f"cluster_x{kap:.2f}_count{threshold:.0f}_{label}"
                    row,mon,tdf=metrics(sym,model,asset,b,ev,dr,atr,side,kap,threshold)
                    summaries.append(row);monthly.extend(mon)
                    if not tdf.empty:trades.append(tdf)
                    print("RESULT",sym,model,row["trades"],row["net_return_22m_pct"],flush=True)
    summary=pd.DataFrame(summaries)
    months=pd.DataFrame(monthly)
    # Joint 2025-only selection: ONE shared model for BTC and ETH; no retuning using 2026.
    training=months[months.month.str.startswith("2025")].copy()
    training["good_pf"]=training.profit_factor.map(
        lambda x:x=="infinite" or isinstance(x,(int,float)) and x>=1.5)
    training["strong5"]=training.good_pf&(training.net_return_pct>=5.)&(training.trades>=3)
    training["strong10"]=training.good_pf&(training.net_return_pct>=10.)&(training.trades>=3)
    ranked=training.groupby("model").agg(strong5=("strong5","sum"),strong10=("strong10","sum"),
        positive=("net_return_pct",lambda x:int((x>0.).sum())),
        compounded_proxy=("net_return_pct","sum")).reset_index()
    ranked=ranked.sort_values(["strong5","strong10","positive","compounded_proxy"],
        ascending=[False,False,False,False],kind="stable")
    chosen=str(ranked.iloc[0]["model"])
    selected=summary[summary.model==chosen].copy()
    sensitivity_rows=[];sensitivity_months=[]
    for sym in ("BTCUSD","ETHUSD"):
        kap=float(selected[selected.market==sym].iloc[0].extreme_multiplier)
        threshold=float(selected[selected.market==sym].iloc[0].min_cluster_events)
        side=1 if str(selected[selected.market==sym].iloc[0].direction)=="continuation" else -1
        asset=assets[sym];b,atr=event_details[sym]
        ev,dr=signals(b,kap,threshold)
        row,mon,_=metrics(sym,chosen+"_sensitivity_2x_slippage",asset,b,ev,dr,atr,
            side,kap,threshold,slip_factor=2.)
        sensitivity_rows.append(row);sensitivity_months.extend(mon)
    summary.to_csv(OUT/"paired_summary.csv",index=False)
    months.to_csv(OUT/"paired_monthly_22.csv",index=False)
    selected.to_csv(OUT/"2025_only_selected.csv",index=False)
    ranked.to_csv(OUT/"2025_joint_parameter_selection.csv",index=False)
    pd.DataFrame(sensitivity_rows).to_csv(OUT/"selected_2x_slippage_summary.csv",index=False)
    pd.DataFrame(sensitivity_months).to_csv(OUT/"selected_2x_slippage_monthly.csv",index=False)
    if trades:pd.concat(trades,ignore_index=True).to_csv(OUT/"paired_trade_ledgers.csv",index=False)
    quality=dict(original_native_partition_sha256_verified_by_loader=True,
        sha256_manifest=source_hash,months=22,original_2025_ist_january_first_5h30m_missing=True,
        btc_repaired_october_checked_against_manifest=True,
        monthly_return="mark to market account NAV at IST end of month; no month-end forced liquidation",
        monthly_profit_factor="sum winning net-trade PnL / abs(sum losing net-trade PnL) for exits in month",
        full_year2025="compounded sequential NAV Jan-Dec",year2026="Jan-Oct YTD only",
        initial_equity_usd=1000,one_position_at_time=True,risk_per_trade=.005,
        max_notional_leverage=3,taker_fee_each_side=.0005,GST=.18,
        BTC_slip_points_each_side=5,ETH_slip_fraction_each_side=.0002,
        sensitivity_double_slippage=True,stop_first_gap_aware_1m=True,
        no_new_entry_last_12h=True,lagged_48_hour_baseline=True,
        training="single joint BTC+ETH 2025 selection, historically exposed 2026 fixed-parameter check",
        excluded_november_2026=True,
        omitted=["funding","real bid/ask spread","market impact","margin/liquidation","contract lots","live fills"])
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    report=["# Independent clustered extreme-arrival relaxation paired BTC ETH audit","",
        "PARTIAL OVERLAP differential: hourly extreme-arrival density followed by first quiet hour, continuation/fade at next 1m open, 1m stop-first 1.5 ATR SL, 2.5R TP, 12h maximum hold.",
        "Same 8 variants on BTC and ETH; 2025-only joint selection and 2026 fixed historical check.",
        "All USD PnL and account monthly NAV include modeled taker fees, GST and adverse slippage.",
        "Monthly profit factor is exit-month net-trade PF; monthly return is account month-end marked NAV including open position; they differ around boundaries.",
        "",
        "## Selected identical model on both assets (2025-only combined ranking)","",
        selected.to_markdown(index=False),"",
        "## All 22 months, selected model, both native assets side by side","",
        months[months.model==chosen].to_markdown(index=False),"",
        "## All variants summary","",summary.to_markdown(index=False),"",
        "## Combined 2025 selection ranking","",ranked.to_markdown(index=False),"",
        "## Doubled slippage sensitivity","",pd.DataFrame(sensitivity_rows).to_markdown(index=False),"",
        "## Execution limitations and data","",json.dumps(quality,indent=2)]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("CLUSTER_AUDIT_COMPLETE",chosen,selected.to_json(orient="records"),flush=True)
if __name__=="__main__":main()
