#!/usr/bin/env python3
"""Causal paired replay of freqtrade/freqtrade-strategies hlhb.py, pinned f3340ce.
Original 4h simultaneous RSI10(hl2) 50 crossing, EMA5/10 crossing, ADX14>25,
long-only. Original 32.11% SL, 1.86% trail activation/1.17% pullback, time ROI.
Conservative 1m execution, 1x exposure; see verdict for deviations.
"""
import hashlib,json
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"external_github_profit_hunt"/"freqtrade_hlhb_4h"
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
SHA="f3340ce11f5bdf62f598522e64d1f5638eaa13f5"
SRC="https://github.com/freqtrade/freqtrade-strategies/blob/"+SHA+"/user_data/strategies/hlhb.py"
FEE=.0005*1.18
START=10000.
def load(sym):
    base=ROOT/"data"/"delta_india"/sym/"1m"
    manifest=json.loads((base/"manifest.json").read_text())
    assert manifest["symbol"]==sym
    parts={p["file"][:7]:p for p in manifest["partitions"]}
    frames=[]
    for ym in MONTHS:
        p=parts[ym];assert p["missing_minutes"]==0,(sym,ym)
        path=base/p["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==p["sha256_gzip"]
        frames.append(pd.read_csv(path,compression="gzip",usecols=["time","open","high","low","close"]))
    d=pd.concat(frames,ignore_index=True)
    assert np.all(np.diff(d.time.to_numpy(np.int64))==60)
    return d
def indicators(d):
    n=240
    o=d.open.to_numpy(float).reshape(-1,n)[:,0]
    h=d.high.to_numpy(float).reshape(-1,n).max(axis=1)
    l=d.low.to_numpy(float).reshape(-1,n).min(axis=1)
    c=d.close.to_numpy(float).reshape(-1,n)[:,-1]
    hl2=(o+c)/2
    delta=np.diff(hl2,prepend=np.nan)
    gains=pd.Series(np.maximum(delta,0)).ewm(alpha=.1,adjust=False,min_periods=10).mean()
    losses=pd.Series(np.maximum(-delta,0)).ewm(alpha=.1,adjust=False,min_periods=10).mean()
    rsi=(100*gains/(gains+losses)).to_numpy()
    e5=pd.Series(c).ewm(span=5,adjust=False,min_periods=5).mean().to_numpy()
    e10=pd.Series(c).ewm(span=10,adjust=False,min_periods=10).mean().to_numpy()
    prev=np.r_[np.nan,c[:-1]]
    tr=np.maximum(h-l,np.maximum(abs(h-prev),abs(l-prev)))
    up=h-np.r_[np.nan,h[:-1]];down=np.r_[np.nan,l[:-1]]-l
    pdm=np.where((up>down)&(up>0),up,0.)
    mdm=np.where((down>up)&(down>0),down,0.)
    def wilder(x,n):
        return pd.Series(x).ewm(alpha=1/n,adjust=False,min_periods=n).mean().to_numpy()
    atr=wilder(tr,14);pdi=100*wilder(pdm,14)/atr;mdi=100*wilder(mdm,14)/atr
    dx=100*abs(pdi-mdi)/(pdi+mdi)
    adx=wilder(dx,14)
    cross_up=(rsi>50)&(np.r_[False,rsi[:-1]<=50])&(e5>e10)&(np.r_[False,e5[:-1]<=e10])&(adx>25)
    cross_dn=(rsi<50)&(np.r_[False,rsi[:-1]>=50])&(e5<e10)&(np.r_[False,e5[:-1]>=e10])&(adx>25)
    enter=np.zeros(len(d),dtype=np.int8);exit_sig=np.zeros(len(d),dtype=np.int8)
    enter[240::240]=cross_up[:-1].astype(np.int8)
    exit_sig[240::240]=cross_dn[:-1].astype(np.int8)
    enter[:240*35]=0
    return enter,exit_sig
def simulate(sym):
    d=load(sym);en,ex=indicators(d)
    ts=d.time.to_numpy(np.int64);o=d.open.to_numpy(float);h=d.high.to_numpy(float)
    l=d.low.to_numpy(float);c=d.close.to_numpy(float)
    ist_month=pd.to_datetime(ts,unit="s",utc=True).tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
    slip=.0005 if sym=="BTCUSD" else .0002
    cap=START;qty=0.;entry=0.;entryfee=0.;peak=0.;entrytime=0;trades=[]
    book={m:dict(month_ist=m,trades=0,wins=0,losses=0,profit=0.,loss=0.) for m in MONTHS}
    equity={};last=""
    for i in range(len(ts)):
        month=ist_month[i]
        if month!=last and last in book:
            equity[last]=cap+qty*(c[i-1]-entry)
        last=month
        if qty>0:
            peak=max(peak,h[i])
            age=(ts[i]-entrytime)//60
            # Source ROI declines from 62.25% immediately to 21.87% after 703m,
            # 3.63% after 2849m, 0 after 5520m.
            roi=.6225 if age<703 else (.2187 if age<2849 else (.0363 if age<5520 else 0.))
            trail=peak*(1-.0117) if peak>=entry*1.0186 else -np.inf
            stop=max(entry*(1-.3211),trail)
            stophit=l[i]<=stop
            roihit=h[i]>=entry*(1+roi) if roi>0 else True
            signal=ex[i]>0
            if stophit or roihit or signal:
                # If stop and ROI both touched in same 1m, stop FIRST.
                raw=min(o[i],stop) if stophit else (entry*(1+roi) if roihit and roi>0 else o[i])
                xp=raw*(1-slip);fee=qty*xp*FEE
                pnl=(xp-entry)*qty-entryfee-fee
                cap+=(xp-entry)*qty-fee
                z=book.get(month)
                if z is not None:
                    z["trades"]+=1;z["wins"]+=int(pnl>0);z["losses"]+=int(pnl<0)
                    z["profit"]+=max(pnl,0);z["loss"]+=max(-pnl,0)
                trades.append(dict(entry_utc=entrytime,exit_utc=int(ts[i]),entry_price=entry,exit_price=xp,qty=qty,net_trade_pnl=pnl,exit_month_ist=month,stop_first=bool(stophit)))
                qty=0.;entryfee=0.
        elif en[i]>0 and month in book and cap>0:
            entry=o[i]*(1+slip);qty=cap/entry
            entryfee=qty*entry*FEE;cap-=entryfee
            peak=entry;entrytime=int(ts[i])
    if last in book:equity[last]=cap+qty*(c[-1]-entry)
    rows=[];prev=START
    for month in MONTHS:
        z=book[month];end=equity[month];ret=100*(end/prev-1);prev=end
        pf=z["profit"]/z["loss"] if z["loss"] else (float("inf") if z["profit"] else float("nan"))
        rows.append({**z,"month_end_equity":end,"monthly_net_return_pct":ret,"profit_factor":round(pf,6) if np.isfinite(pf) else ("Infinity" if pf>0 else "N/A"),"high_pf_month":bool(pf>=1.5 and ret>0)})
    out=pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True)
    out.to_csv(OUT/(sym+"_22_months.csv"),index=False)
    pd.DataFrame(trades).to_csv(OUT/(sym+"_trades.csv.gz"),index=False,compression="gzip")
    p=out.profit.sum();loss=out.loss.sum();eq=out.month_end_equity.to_numpy()
    y25=out.loc[out.month_ist=="2025-12","month_end_equity"].iloc[0]
    drawdown=100*np.max(1-eq/np.maximum.accumulate(np.r_[START,eq])[1:])
    res=dict(symbol=sym,trades=len(trades),high_pf_months=int(out.high_pf_month.sum()),profitable_months=int((out.monthly_net_return_pct>0).sum()),losing_months=int((out.monthly_net_return_pct<0).sum()),no_trade_months=int((out.trades==0).sum()),aggregate_pf=float(p/loss) if loss else None,median_monthly_net_pct=float(out.monthly_net_return_pct.median()),net_2025_pct=float(100*(y25/START-1)),net_2026_ytd_pct=float(100*(eq[-1]/y25-1)),net_22m_pct=float(100*(eq[-1]/START-1)),max_month_end_drawdown_pct=float(drawdown),fully_verified=False)
    print("HLHB_PAIRED "+json.dumps(res),flush=True)
    return res
def main():
    results=[simulate(s) for s in ("BTCUSD","ETHUSD")]
    verdict=dict(source=SRC,sha=SHA,results=results,fully_verified=False,
      source_rules="4h RSI10(hl2) and EMA5/10 simultaneous bullish cross ADX14>25 long; opposite simultaneous cross exit; original Freqtrade ROI/trailing/stop schedule",
      deviations=["1x exposure, taker fills instead of source maker limit", "Wilder RSI/ADX approximate TA-Lib smoothing and may differ in early samples", "next completed 4h open entry and 1m stop-first OHLC replay"],
      limitations=["January 2025 IST missing 2024-12-31 18:30-23:59 UTC","No settled funding, L1 bid/ask/depth or margin/liquidation modeling","1m OHLC path unknown","2026 research-exposed, not pristine OOS"])
    (OUT/"verdict.json").write_text(json.dumps(verdict,indent=2)+"\n")
if __name__=="__main__":main()
