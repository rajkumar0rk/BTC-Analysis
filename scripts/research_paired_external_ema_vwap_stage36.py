#!/usr/bin/env python3
"""Stage36: external EMA9/daily-VWAP crossover and breakout screening; zero-slippage, fee/GST included."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_paired_absorption_stage25 import load_native,exit_replay,profit_factor
OUT=Path("analysis/paired_external_ema_vwap_stage36")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
INIT=10000.;FEE=.0005*1.18;RISK=.005;LEV=3.;HOLD=3600

def events(f):
    """External xenoxavier EMA9 x UTC daily VWAP: cross-close, 3-bar arm, next-minute breakout."""
    b=f[["open","high","low","close","volume"]].resample("1h",closed="left",label="right").agg(
      {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    b["n"]=f.close.resample("1h",closed="left",label="right").count()
    typical=(b.high+b.low+b.close)/3
    day=b.index.floor("D")
    v=b.volume.groupby(day).cumsum()
    b["vwap"]=(typical*b.volume).groupby(day).cumsum()/v.replace(0,np.nan)
    b["ema"]=b.close.ewm(span=9,adjust=False,min_periods=9).mean()
    prev=b.close.shift(1)
    tr=pd.concat([b.high-b.low,(b.high-prev).abs(),(b.low-prev).abs()],axis=1).max(axis=1)
    b["atr"]=tr.ewm(span=14,adjust=False,min_periods=14).mean()
    cross=(b.ema>b.vwap)&(b.ema.shift(1)<=b.vwap.shift(1))&(b.close>b.ema)&(b.close>b.vwap)
    complete=b.n.eq(60)
    op=f.open.to_numpy(float); hi=f.high.to_numpy(float); ts=f.index
    results=[]; blocked_until=-1
    for i in np.flatnonzero(cross.to_numpy()):
        if i<30 or not complete.iloc[max(0,i-3):i+1].all():continue
        atr=float(b.atr.iloc[i]); trigger=float(b.high.iloc[i])
        if not np.isfinite(atr) or atr<=0 or 1.5*atr/trigger>=.038:continue
        for j in range(i+1,min(i+4,len(b))):
            if b.ema.iloc[j-1]<=b.vwap.iloc[j-1]:break
            k0=ts.searchsorted(b.index[j-1]);k1=ts.searchsorted(b.index[j])
            if k0<0 or k1>=len(f):break
            hits=np.flatnonzero(hi[k0:k1]>=trigger)
            if len(hits):
                k=k0+int(hits[0])+1
                if k<len(f) and k>blocked_until:
                    results.append((k,1,atr))
                    blocked_until=k+60
                break
    return results

def replay(f,symbol,stress):
    op=f.open.to_numpy(float);hi=f.high.to_numpy(float);lo=f.low.to_numpy(float);cl=f.close.to_numpy(float)
    ts=f.time.to_numpy(np.int64)
    eq=INIT;peak=INIT;dd=0.;busy=-1;records=[]
    for k,side,atr in events(f):
        if k<=busy:continue
        mid=float(op[k]);dist=1.5*atr
        if dist<=0 or dist/mid>.15:continue
        slip=(5. if stress else 0.) if symbol=="BTCUSD" else mid*(.0002 if stress else 0.)
        fill=mid+side*slip
        qty=min(eq*RISK/dist,eq*LEV/fill)
        if qty<=0:continue
        j,px,why,worst=exit_replay(op,hi,lo,cl,k,side,dist,2.0,HOLD)
        busy=int(j)
        outslip=(5. if stress else 0.) if symbol=="BTCUSD" else px*(.0002 if stress else 0.)
        exitfill=px-side*outslip
        pnl=qty*(side*(exitfill-fill)-FEE*(fill+exitfill))
        adverse=worst-side*((5. if stress else 0.) if symbol=="BTCUSD" else worst*(.0002 if stress else 0.))
        dd=max(dd,100*(1-(eq+qty*(side*(adverse-fill)-FEE*(fill+adverse)))/peak))
        start=eq;eq+=pnl
        if eq<=0:raise RuntimeError("Bankrupt account")
        peak=max(peak,eq);dd=max(dd,100*(1-eq/peak))
        records.append(dict(symbol=symbol,stress=stress,entry_unix=int(ts[k]),exit_unix=int(ts[j]),side=side,
            entry_mid=mid,exit_mid=px,entry_fill=fill,exit_fill=exitfill,quantity=qty,
            start_equity=start,end_equity=eq,net_usd=pnl,reason=("stop","target","timeout")[why]))
    columns=["symbol","stress","entry_unix","exit_unix","side","entry_mid","exit_mid","entry_fill","exit_fill",
             "quantity","start_equity","end_equity","net_usd","reason"]
    return pd.DataFrame(records,columns=columns),dd

def nav(g,f,month,symbol,stress):
    boundary=int((pd.Period(month,freq="M")+1).start_time.tz_localize("Asia/Kolkata").timestamp())-1
    ts=f.time.to_numpy(np.int64)
    i=int(np.searchsorted(ts,boundary,side="right"))-1
    if i<0:return INIT
    if boundary-ts[i]>60:raise AssertionError("Missing month-end mark "+month)
    done=g[g.exit_unix<=boundary]
    value=INIT+float(done.net_usd.sum())
    active=g[(g.entry_unix<=boundary)&(g.exit_unix>boundary)]
    if len(active)>1:raise AssertionError("Concurrent positions")
    for p in active.itertuples():
        mark=float(f.close.iloc[i])
        slip=(5. if stress else 0.) if symbol=="BTCUSD" else mark*(.0002 if stress else 0.)
        exitmark=mark-p.side*slip
        value+=p.quantity*(p.side*(exitmark-p.entry_fill)-FEE*(p.entry_fill+exitmark))
    return value

def audit(g,f,symbol,stress,dd):
    g=g.copy()
    g["month_ist"]=pd.to_datetime(g.exit_unix,unit="s",utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    previous=INIT;rows=[]
    for month in MONTHS:
        t=g[g.month_ist==month];end=nav(g,f,month,symbol,stress)
        rows.append(dict(symbol=symbol,stress=stress,month_ist=month,net_return_pct=100*(end/previous-1),
            start_equity=previous,end_equity=end,profit_factor=profit_factor(t.net_usd),
            trades=len(t),wins=int((t.net_usd>0).sum()),losses=int((t.net_usd<0).sum())))
        previous=end
    m=pd.DataFrame(rows)
    if not np.isclose(previous,INIT+g.net_usd.sum(),rtol=1e-7,atol=1e-5):
        raise AssertionError("NAV trade ledger reconciliation failed")
    t25=g[g.month_ist.str.startswith("2025-")]
    t26=g[g.month_ist.str.startswith("2026-")]
    s=dict(symbol=symbol,stress=stress,trades=len(g),wins=int((g.net_usd>0).sum()),losses=int((g.net_usd<0).sum()),
       overall_PF=profit_factor(g.net_usd),PF_2025=profit_factor(t25.net_usd),PF_2026_YTD=profit_factor(t26.net_usd),
       positive_months=int((m.net_return_pct>0).sum()),negative_months=int((m.net_return_pct<0).sum()),
       flat_months=int((m.net_return_pct==0).sum()),median_month_pct=float(m.net_return_pct.median()),
       worst_month_pct=float(m.net_return_pct.min()),max_drawdown_pct=dd,
       months_5pct=int((m.net_return_pct>=5).sum()),months_10pct=int((m.net_return_pct>=10).sum()),
       months_20pct=int((m.net_return_pct>=20).sum()),
       net_2025_pct=100*(m.iloc[11].end_equity/INIT-1),
       net_2026_JanOct_YTD_pct=100*(m.iloc[-1].end_equity/m.iloc[11].end_equity-1),
       net_22_month_pct=100*(previous/INIT-1))
    return m,s

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    monthly=[];summary=[];trades=[];quality={}
    for symbol in ("BTCUSD",):
        f,q=load_native(symbol);quality[symbol]=q
        for stress in (False,):
            g,dd=replay(f,symbol,stress)
            m,s=audit(g,f,symbol,stress,dd)
            monthly.append(m);summary.append(s);trades.append(g)
            if symbol=="BTCUSD" and (s["overall_PF"] is None or not np.isfinite(s["overall_PF"]) or s["overall_PF"]<=1 or s["trades"]<30 or s["net_22_month_pct"]<=0):
                break
    m=pd.concat(monthly,ignore_index=True);s=pd.DataFrame(summary);g=pd.concat(trades,ignore_index=True)
    m.to_csv(OUT/"all_22_months.csv",index=False)
    s.to_csv(OUT/"summary.csv",index=False)
    g.to_csv(OUT/"original_trade_ledger.csv.gz",index=False,compression="gzip")
    (OUT/"quality.json").write_text(json.dumps({"data":quality,"rules":"External EMA9 crossing above UTC daily VWAP, 1h close above both, breakout of setup high within 3 hours, next-minute fill, 1.5 ATR stop, 3 ATR target, 60h timeout","fee_per_side":.0005,"GST":.18,"BTC_slip":0,"ETH_slip_fraction":0,"risk_fraction":RISK,"leverage_cap":LEV,"limitations":["Funding omitted","Order-book impact and spread omitted","No contract lot rounding or maintenance margin","January 2025 IST first 330 minutes absent","2026 previously research-exposed","No 2026 or ETH tuning"]},indent=2))
    (OUT/"RESEARCH_REPORT.md").write_text("# Stage36 external EMA9 daily VWAP crossover breakout ZERO-SLIPPAGE SCREEN\n\nAdapted public xenoxavier EMA9-VWAP logic; no slippage screen with taker commission and GST. Funding unmodeled. Minute-level breakout detection and next-minute entry are conservative approximations, not rule-for-rule exact limit execution.\n\n"+m[~m.stress][["month_ist","symbol","net_return_pct","profit_factor","trades","wins","losses"]].to_markdown(index=False)+"\n\n"+s.to_markdown(index=False))
    print("STAGE36_COMPLETE",s.to_json(orient="records"))
if __name__=="__main__":main()
