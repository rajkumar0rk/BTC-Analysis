#!/usr/bin/env python3
"""Stage32: precommitted hourly illiquidity-impact reversal; BTC selection, frozen ETH validation."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_paired_absorption_stage25 import load_native,exit_replay,profit_factor
OUT=Path("analysis/paired_impact_reversal_stage32")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
INIT=10000.;FEE=.0005*1.18;RISK=.005;LEV=3.;HOLD=480

def events(f):
    b=f[["open","high","low","close","volume"]].resample("1h",closed="left",label="right").agg(
      {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    b["n"]=f.close.resample("1h",closed="left",label="right").count()
    previous=b.close.shift(1)
    tr=pd.concat([b.high-b.low,(b.high-previous).abs(),(b.low-previous).abs()],axis=1).max(axis=1)
    b["atr"]=tr.shift(1).rolling(24,min_periods=24).median()
    b["ret"]=np.log(b.close/b.open)
    turnover=b.volume*((b.open+b.close)/2)
    b["impact"]=b.ret.abs()/turnover.replace(0,np.nan)
    threshold=b.impact.shift(1).rolling(168,min_periods=168).quantile(.9)
    vol_median=b.volume.shift(1).rolling(168,min_periods=168).median()
    location=(b.close-b.low)/(b.high-b.low).replace(0,np.nan)
    valid=b.n.eq(60)&b.n.shift(1).rolling(168,min_periods=168).min().eq(60)
    extreme=valid&(b.impact>threshold)&(b.volume<vol_median)&(b.ret.abs()>=.004)&b.atr.gt(0)
    side=np.where((b.ret>0)&(location>=.8),-1,np.where((b.ret<0)&(location<=.2),1,0))
    ix=f.index.get_indexer(b.index)
    return [(int(ix[i]),int(side[i]),float(b.atr.iloc[i])) for i in np.flatnonzero(extreme.to_numpy())
            if ix[i]>=0 and side[i]!=0 and np.isfinite(b.atr.iloc[i])]

def replay(f,symbol,stress):
    op=f.open.to_numpy(float);hi=f.high.to_numpy(float);lo=f.low.to_numpy(float);cl=f.close.to_numpy(float)
    ts=f.time.to_numpy(np.int64)
    eq=INIT;peak=INIT;dd=0.;busy=-1;records=[]
    for k,side,atr in events(f):
        if k<=busy:continue
        mid=float(op[k]);dist=1.5*atr
        if dist<=0 or dist/mid>.15:continue
        slip=(10. if stress else 5.) if symbol=="BTCUSD" else mid*(.00035 if stress else .0002)
        fill=mid+side*slip
        qty=min(eq*RISK/dist,eq*LEV/fill)
        if qty<=0:continue
        j,px,why,worst=exit_replay(op,hi,lo,cl,k,side,dist,1.5,HOLD)
        busy=int(j)
        outslip=(10. if stress else 5.) if symbol=="BTCUSD" else px*(.00035 if stress else .0002)
        exitfill=px-side*outslip
        pnl=qty*(side*(exitfill-fill)-FEE*(fill+exitfill))
        adverse=worst-side*((10. if stress else 5.) if symbol=="BTCUSD" else worst*(.00035 if stress else .0002))
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
        slip=(10. if stress else 5.) if symbol=="BTCUSD" else mark*(.00035 if stress else .0002)
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
    for symbol in ("BTCUSD","ETHUSD"):
        f,q=load_native(symbol);quality[symbol]=q
        for stress in (False,True):
            g,dd=replay(f,symbol,stress)
            m,s=audit(g,f,symbol,stress,dd)
            monthly.append(m);summary.append(s);trades.append(g)
    m=pd.concat(monthly,ignore_index=True);s=pd.DataFrame(summary);g=pd.concat(trades,ignore_index=True)
    m.to_csv(OUT/"all_22_months.csv",index=False)
    s.to_csv(OUT/"summary.csv",index=False)
    g.to_csv(OUT/"original_trade_ledger.csv.gz",index=False,compression="gzip")
    (OUT/"quality.json").write_text(json.dumps({"data":quality,"rules":"Hourly impact proxy 90th percentile prior 168h; low relative volume; abs log return >=0.4%; fade outer 20% close; next 1m open; 1.5 hourly ATR stop, 1.5R target, 8h timeout","fee_per_side":.0005,"GST":.18,"BTC_slip":5,"ETH_slip_fraction":.0002,"risk_fraction":RISK,"leverage_cap":LEV,"limitations":["Funding omitted","Order-book impact and spread omitted","No contract lot rounding or maintenance margin","January 2025 IST first 330 minutes absent","2026 previously research-exposed","No 2026 or ETH tuning"]},indent=2))
    (OUT/"RESEARCH_REPORT.md").write_text("# Stage32 BTC-first hourly impact-proxy fade\n\nPre-registered OHLCV illiquidity proxy; NOT observed impact. No parameter search.\n\n"+m[~m.stress][["month_ist","symbol","net_return_pct","profit_factor","trades","wins","losses"]].to_markdown(index=False)+"\n\n"+s.to_markdown(index=False))
    print("STAGE32_COMPLETE",s.to_json(orient="records"))
if __name__=="__main__":main()
