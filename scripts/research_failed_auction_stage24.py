#!/usr/bin/env python3
"""Stage24: causal two-hour failed-auction BTC futures reversal; 22 complete IST months only."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive,FEE,SLIPPAGE

OUT=Path("analysis/institutional_discovery_stage24_failed_auction")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,seg_start,seg_end,quality=read_archive()
    # Reject fabricated continuity; audit missing UTC Oct31 explicitly.
    utc=f.index
    oct31=((utc>=pd.Timestamp("2026-10-31",tz="UTC"))&
           (utc<pd.Timestamp("2026-11-01",tz="UTC")))
    october_utc_complete=int(oct31.sum())==1440
    # IST calendar month coverage is assessed separately, not inferred from UTC labels.
    idx=utc.tz_convert("Asia/Kolkata")
    counts=pd.Series(1,index=idx).resample("MS").sum()
    coverage={m:int(counts.get(pd.Timestamp(m+"-01",tz="Asia/Kolkata"),0)) for m in MONTHS}
    hourly=f[["open","high","low","close"]].resample("1h",closed="left",label="right").agg(
        {"open":"first","high":"max","low":"min","close":"last"})
    hourly["n"]=f.close.resample("1h",closed="left",label="right").count()
    hourly["valid"]=hourly.n.rolling(16,min_periods=16).min().eq(60)
    prevhigh=hourly.high.shift(2).rolling(12,min_periods=12).max()
    prevlow=hourly.low.shift(2).rolling(12,min_periods=12).min()
    atr=(hourly.high-hourly.low).rolling(14,min_periods=14).mean()
    # Hour A closes beyond its preceding 12h channel; hour B rejects that auction.
    long=(hourly.close.shift(1)<prevlow)&(hourly.close>prevlow)&(hourly.close<hourly.open.shift(1))
    short=(hourly.close.shift(1)>prevhigh)&(hourly.close<prevhigh)&(hourly.close>hourly.open.shift(1))
    ix=f.index.get_indexer(hourly.index)
    events=[]
    for z in np.flatnonzero(hourly.valid.to_numpy(bool)):
        k=int(ix[z])
        if k<0 or k-seg_start[k]<960 or seg_end[k]-k<720:continue
        m=idx[k].strftime("%Y-%m")
        if m not in MONTHS:continue
        for side,signal in ((1,long),(-1,short)):
            if bool(signal.iat[z]) and np.isfinite(atr.iat[z]) and atr.iat[z]>0:
                events.append((k,side,float(atr.iat[z])))
    op=f.open.to_numpy(float);hi=f.high.to_numpy(float)
    lo=f.low.to_numpy(float);cl=f.close.to_numpy(float)
    trades=[]
    for mult in (1.5,2.5):
        for rr in (2.,3.):
            for hold in (360,720):
                busy=-1
                for k,side,vol in events:
                    if k<=busy:continue
                    risk=float(np.clip(mult*vol,150.,1600.))
                    stop=op[k]-side*risk
                    target=op[k]+side*rr*risk
                    for j in range(k,k+hold):
                        if (side==1 and lo[j]<=stop) or (side==-1 and hi[j]>=stop):
                            px=min(op[j],stop) if side==1 else max(op[j],stop)
                            reason="stop";break
                        if (side==1 and hi[j]>=target) or (side==-1 and lo[j]<=target):
                            px=target;reason="target";break
                    else:
                        j=k+hold-1;px=cl[j];reason="timeout"
                    busy=j
                    if idx[j].strftime('%Y-%m') not in MONTHS:continue
                    entryfill=op[k]+side*SLIPPAGE
                    exitfill=px-side*SLIPPAGE
                    net=side*(exitfill-entryfill)-FEE*(entryfill+exitfill)
                    fraction=min(.005,5*risk/op[k])
                    trade_return=fraction*net/risk
                    trades.append(dict(mult=mult,rr=rr,hold=hold,entry_unix=int(f.time.iat[k]),
                        exit_unix=int(f.time.iat[j]),month_ist=idx[j].strftime("%Y-%m"),
                        side=side,net_points=float(net),trade_return=float(trade_return),
                        reason=reason))
    ledger=pd.DataFrame(trades)
    if ledger.empty:raise RuntimeError("No executable candidate trades")
    ledger.to_csv(OUT/"original_trade_ledger.csv.gz",index=False,compression="gzip")
    monthly=[];ranks=[]
    for key,g in ledger.groupby(["mult","rr","hold"]):
        vals=[]
        peak=equity=1.;dd=0.
        for m in MONTHS:
            s=g[g.month_ist==m].sort_values("exit_unix")
            ret=s.trade_return.to_numpy()
            month_ret=float(np.prod(1+ret)-1)
            vals.append(month_ret)
            for v in ret:
                equity*=1+v;peak=max(peak,equity);dd=max(dd,1-equity/peak)
            monthly.append(dict(mult=key[0],rr=key[1],hold=key[2],month_ist=m,
                trades=len(s),winning_trades=int((s.net_points>0).sum()),
                losing_trades=int((s.net_points<0).sum()),
                breakeven_trades=int((s.net_points==0).sum()),
                net_account_return_pct=round(100*month_ret,6)))
        ranks.append(dict(mult=key[0],rr=key[1],hold=key[2],
            positive_2025=int((np.array(vals[:12])>0).sum()),
            positive_2026=int((np.array(vals[12:])>0).sum()),
            min_2025_pct=float(100*min(vals[:12])),
            max_closed_trade_drawdown_pct=round(100*dd,5),
            total_trades=len(g)))
    allmonthly=pd.DataFrame(monthly)
    ranked=pd.DataFrame(ranks).sort_values(
        ["positive_2025","min_2025_pct"],ascending=[False,False])
    best=ranked.iloc[0]
    chosen=allmonthly[(allmonthly.mult==best.mult)&
        (allmonthly.rr==best.rr)&(allmonthly.hold==best.hold)]
    allmonthly.to_csv(OUT/"all_monthly.csv",index=False)
    ranked.to_csv(OUT/"2025_only_ranking.csv",index=False)
    chosen.to_csv(OUT/"selected_22_months.csv",index=False)
    passed=bool((chosen.net_account_return_pct>0).all())
    meta=dict(positive_months=int((chosen.net_account_return_pct>0).sum()),
        total_months=22,all_22_positive=passed,
        october_31_utc_complete=october_utc_complete,
        oct31_utc_candles=int(oct31.sum()),
        month_observation_counts=coverage,
        chosen_model=best.to_dict(),source_quality=quality,
        caveats=["2026 is previously exposed, not pristine forward validation",
        "October 31 UTC incomplete means October must not be called fully verified",
        "Funding, order book spread, market impact, liquidation and discrete lots unmodeled",
        "One position per model; risk capped at 0.5% equity and 5x notional",
        "Stop wins same-minute ambiguous OHLC; gap stops use adverse open",
        "Drawdown at trade closes only; intratrade drawdown can be larger",
        "No-trade months are zero, not positive",
        "November 2026 excluded entirely"])
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2,default=str)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text(
        "# Stage24 — two-hour failed auction, 22 completed IST months\n\n"+
        "Select parameters by 2025 only; replay fixed on Jan-Oct 2026. "+
        "This is research-exposed history, not independent validation.\n\n"+
        "## Ranked candidates\n"+ranked.to_markdown(index=False)+"\n\n"+
        "## Selected model, net account returns after taker/GST/slippage\n"+
        chosen.to_markdown(index=False)+"\n\n"+
        "## Audit and limitations\n```json\n"+json.dumps(meta,indent=2,default=str)+"\n```\n")
    print("STAGE24_COMPLETE",json.dumps(dict(positive_months=meta["positive_months"],
        all_22_positive=passed,oct31_utc_candles=int(oct31.sum()),
        selected=best.to_dict()),default=str))
if __name__=="__main__":main()
