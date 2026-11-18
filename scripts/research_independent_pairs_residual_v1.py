#!/usr/bin/env python3
"""Independent ETH/BTC two-leg dollar-neutral 1h residual mean-reversion study."""
import sys,json
from pathlib import Path
import numpy as np,pandas as pd
from numba import njit
sys.path.insert(0,str(Path(__file__).resolve().parent))
from eth_native_crossfamily_v2 import load,MONTHS
OUT=Path("analysis/independent_pairs_residual_v1")
FEE=.0005*1.18
@njit
def run(bopen,bclose,eopen,eclose,mc,idx,z,mean,std,entryz,stopz,hold):
    out=np.zeros((len(idx),11),np.float64)
    n=0;busy=-1;eq=1000.
    for i in range(len(idx)):
        k=idx[i]
        if k<=busy or k>=len(mc) or mc[k]>202610:continue
        zi=z[i];sd=std[i];mu=mean[i]
        if not np.isfinite(zi) or not np.isfinite(sd) or sd<=0 or abs(zi)<entryz:continue
        side=-1. if zi>0 else 1. # ETH leg direction; BTC opposite
        # PnL for a fixed equal-dollar ETH/BTC pair; each leg notional <=equity
        # Stop-based risk sizing; cap total gross at 2x equity
        gap=stopz*sd
        leg_notional=min(eq,eq*.005/gap)
        if leg_notional<=0:break
        eb=eopen[k];ee=eopen[k]
        if eb<=0 or ee<=0:continue
        # Entry BTC 5 points and ETH 0.02%, both adverse to trade direction
        bside=-side
        bentry=eb+bside*5.
        eentry=ee*(1.+side*.0002)
        if bentry<=0 or eentry<=0:continue
        # stop residual = entry ratio log +- stopz*std
        ratio0=np.log(ee/eb)
        stop=ratio0+side*(-stopz*sd)
        finish=min(k+hold-1,len(mc)-1)
        j=finish;bx=bclose[finish];ex=eclose[finish]
        for v in range(k,finish+1):
            r=np.log(eclose[v]/bclose[v])
            stop_hit=(r<=stop if side>0 else r>=stop)
            mean_hit=(r>=mu if side>0 else r<=mu)
            if stop_hit or mean_hit or v==finish or (v+1<len(mc) and mc[v+1]!=mc[v]):
                j=v;bx=bclose[v];ex=eclose[v];break
        # Exit slippage adverse for closing both positions
        bexit=bx-bside*5.
        eexit=ex*(1.-side*.0002)
        if bexit<=0 or eexit<=0:continue
        bp=leg_notional*bside*(bexit/bentry-1.)
        ep=leg_notional*side*(eexit/eentry-1.)
        costs=leg_notional*FEE*(1.+bexit/bentry+1.+eexit/eentry)
        pnl=bp+ep-costs
        eq+=pnl
        out[n,0]=k;out[n,1]=j;out[n,2]=side;out[n,3]=leg_notional
        out[n,4]=bp;out[n,5]=ep;out[n,6]=costs;out[n,7]=pnl
        out[n,8]=eq;out[n,9]=zi;out[n,10]=sd
        n+=1;busy=j
        if eq<=0:break
    return out[:n]

def pf(x):
    pos=x[x>0].sum();neg=-x[x<0].sum()
    return None if pos==0 and neg==0 else ("infinite" if neg==0 else float(pos/neg))

def monthly(ledger,monthcodes,config):
    months=monthcodes[ledger[:,1].astype(np.int64)] if len(ledger) else np.array([],np.int32)
    rows=[];eq=1000.
    for m in MONTHS:
        code=int(m.replace("-",""))
        q=ledger[months==code];x=q[:,7] if len(q) else np.zeros(0)
        after=float(q[-1,8]) if len(q) else eq
        rows.append(dict(config=config,month=m,monthly_pf=pf(x),
            net_return_pct=(after/eq-1)*100 if eq>0 else -100.,
            net_usd=float(x.sum()),trades=len(x),wins=int((x>0).sum()),losses=int((x<0).sum()),
            equity_start_usd=eq,equity_end_usd=after))
        eq=after
    return rows

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    btc=load("BTCUSD");eth=load("ETHUSD")
    assert btc.index.equals(eth.index)
    ist=btc.index.tz_convert("Asia/Kolkata")
    mc=np.asarray(ist.year*100+ist.month,dtype=np.int32)
    # Fully closed 1h bars only. Index label is the NEXT hour's open.
    b1=btc.close.resample("1h",closed="left",label="right").last()
    e1=eth.close.resample("1h",closed="left",label="right").last()
    ratio=np.log(e1/b1)
    ix=btc.index
    summaries=[];monthrows=[];ledgers={}
    for lookback in (120,240,480):
        mu=ratio.rolling(lookback,min_periods=lookback).mean()
        sd=ratio.rolling(lookback,min_periods=lookback).std()
        z=(ratio-mu)/sd
        k=ix.get_indexer(ratio.index)
        valid=k>=0
        k=k[valid].astype(np.int64)
        zs=z.to_numpy(float)[valid];mus=mu.to_numpy(float)[valid];sds=sd.to_numpy(float)[valid]
        for threshold in (1.5,2.,2.5):
            for stop in (1.5,2.):
                for hold in (1440,2880):
                    name=f"ratio_revert_L{lookback}_Z{threshold:g}_stop{stop:g}_hold{hold//60}h"
                    ledger=run(btc.open.to_numpy(float),btc.close.to_numpy(float),
                        eth.open.to_numpy(float),eth.close.to_numpy(float),mc,k,zs,mus,sds,threshold,stop,hold)
                    rows=monthly(ledger,mc,name)
                    monthrows.extend(rows);ledgers[name]=ledger
                    x=ledger[:,7] if len(ledger) else np.zeros(0)
                    eq=np.r_[1000.,ledger[:,8]] if len(ledger) else np.array([1000.])
                    d=pd.DataFrame(rows)
                    strong5=int(((d.monthly_pf.map(lambda p:p=="infinite" or (isinstance(p,(int,float)) and p>=1.5)))&(d.net_return_pct>=5)&(d.trades>=3)).sum())
                    strong10=int(((d.monthly_pf.map(lambda p:p=="infinite" or (isinstance(p,(int,float)) and p>=1.5)))&(d.net_return_pct>=10)&(d.trades>=3)).sum())
                    summaries.append(dict(config=name,overall_pf=pf(x),total_return_pct=(eq[-1]/1000.-1)*100,
                        return_2025_pct=(d.iloc[11].equity_end_usd/1000.-1)*100,
                        return_2026_jan_oct_pct=(d.iloc[-1].equity_end_usd/d.iloc[12].equity_start_usd-1)*100,
                        yearly_2025_above_500=bool((d.iloc[11].equity_end_usd/1000.-1)>5),
                        ytd_2026_above_500=bool((d.iloc[-1].equity_end_usd/d.iloc[12].equity_start_usd-1)>5),
                        positive_months=int((d.net_return_pct>0).sum()),strong5_months=strong5,strong10_months=strong10,
                        trades=len(x),wins=int((x>0).sum()),losses=int((x<0).sum()),
                        max_closed_trade_dd_pct=float((eq/np.maximum.accumulate(eq)-1).min()*100)))
    summary=pd.DataFrame(summaries)
    monthlydf=pd.DataFrame(monthrows)
    # Rank exclusively using 2025: not a blind 2026 test.
    train=monthlydf[monthlydf.month<="2025-12"]
    score=train.groupby("config").agg(train_positive=("net_return_pct",lambda x:(x>0).sum()),
        train_return=("net_return_pct",lambda x:np.prod(1+x/100)-1))
    score["score"]=score.train_positive+np.clip(score.train_return,-1,1)*10
    winner=score.sort_values("score",ascending=False).index[0]
    summary.to_csv(OUT/"all_config_summary.csv",index=False)
    monthlydf.to_csv(OUT/"all_config_monthly.csv",index=False)
    monthlydf[monthlydf.config==winner].to_csv(OUT/"2025_selected_monthly_22.csv",index=False)
    selected=ledgers[winner]
    if len(selected):
        pd.DataFrame(dict(entry_utc=ix[selected[:,0].astype(int)].astype(str),
            exit_utc=ix[selected[:,1].astype(int)].astype(str),
            eth_direction=selected[:,2],notional_per_leg_usd=selected[:,3],
            btc_gross_pnl_usd=selected[:,4],eth_gross_pnl_usd=selected[:,5],
            total_fees_gst_usd=selected[:,6],pair_net_pnl_usd=selected[:,7],
            account_equity_usd=selected[:,8],entry_z=selected[:,9],entry_ratio_std=selected[:,10])).to_csv(OUT/"2025_selected_trade_ledger.csv",index=False)
    quality=dict(strategy="Two-leg ETH BTC ratio residual mean reversion",configs=36,months=22,
        selected_by="2025 positive-month count + capped 2025 return only",selected=winner,
        cost_btc_slip_points_per_fill=5,cost_eth_slip_fraction_per_fill=.0002,
        fee_per_side_including_gst=FEE,initial_equity=1000,
        monthly_booking="Forced actual two-leg liquidation on final 1m close before IST month boundary",
        data="Original BTC and ETH Delta India 1m manifest and SHA256 validated",
        initial_gap="Jan2025 IST first 5.5 hours absent",
        known_limitations=["1m CLOSE-only residual stop, no intraminute worst-case","funding","actual spread/depth","market impact","margin/liquidation","lot constraints","2026 previously inspected, not virgin out of sample"],
        instrument_interpretation="A single two-leg pair, not standalone BTC and ETH performance")
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2))
    top=summary.sort_values("total_return_pct",ascending=False).head(8)
    report="# Independent ETH/BTC dollar-neutral residual reversion\n\n"
    report+="Novelty: differential two-leg pair, not two standalone asset backtests. Historical, not live validation.\n\n"
    report+="## 2025-selected candidate\n\n"+summary[summary.config==winner].to_markdown(index=False)+"\n\n"
    report+="## Highest total returns (exploratory, hindsight)\n\n"+top.to_markdown(index=False)+"\n\n"
    report+="## All 22 monthly results for 2025-selected configuration\n\n"+monthlydf[monthlydf.config==winner].to_markdown(index=False)+"\n\n"
    report+="2025 full-year >500% and 2026 Jan-Oct YTD >500% shown separately. All monthly values are after modeled two-leg fees/GST/slippage, with incomplete execution-cost coverage.\n"
    (OUT/"RESEARCH_REPORT.md").write_text(report)
    print("RESEARCH_DONE",json.dumps(dict(selected=winner,selected_summary=summary[summary.config==winner].to_dict("records"),top=top.head(3).to_dict("records"))),flush=True)
if __name__=="__main__":main()
