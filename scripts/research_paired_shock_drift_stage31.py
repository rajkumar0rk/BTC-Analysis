#!/usr/bin/env python3
"""Stage31 falsifiable hypothesis: shock-driven directional drift after high-range high-volume 1h bars.
Pre-registered one setting; native BTC and ETH 1m, no selection/optimization.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_paired_absorption_stage25 import load_native,exit_replay,profit_factor
OUT=Path("analysis/paired_shock_drift_stage31")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
INIT=10000.;FEE=.0005*1.18;RISK=.005;MAX_LEV=3.;HOLD=1440

def signals(f):
    # Mechanism: institutional risk-rebalancing and liquidation-driven
    # volatility shocks may create delayed directional price drift.
    # Fixed before observing results; 2025 BTC decides rejection, 2026 BTC
    # is temporal recheck, ETH never used to tune.
    b=f[["open","high","low","close","volume"]].resample(
        "1h",closed="left",label="right").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    b["n"]=f.close.resample("1h",closed="left",label="right").count()
    prev=b.close.shift(1)
    tr=pd.concat([b.high-b.low,(b.high-prev).abs(),(b.low-prev).abs()],axis=1).max(axis=1)
    b["atr"]=tr.shift(1).rolling(24,min_periods=24).median()
    # Shock defined relative to the prior completed 24-hour distribution.
    prior_range=(b.high-b.low).shift(1).rolling(24,min_periods=24).median()
    prior_volume=b.volume.shift(1).rolling(168,min_periods=168).median()
    span=(b.high-b.low).replace(0,np.nan)
    location=(b.close-b.low)/span
    impulse=(b.close-b.open)/b.atr.replace(0,np.nan)
    shock=(span>=2.0*prior_range)&(b.volume>=1.5*prior_volume)
    long=shock&(impulse>=1.25)&(location>=.8)
    short=shock&(impulse<=-1.25)&(location<=.2)
    complete=b.n.eq(60)&b.n.shift(1).rolling(168,min_periods=168).min().eq(60)
    candidates=b[complete&(long|short)&b.atr.gt(0)].copy()
    candidates["side"]=np.where(long.loc[candidates.index],1,-1)
    ix=f.index.get_indexer(candidates.index)
    return [(int(k),int(s),float(a)) for k,s,a in zip(ix,candidates.side,candidates.atr)
            if k>=0 and np.isfinite(a) and a>0]

def run(f,symbol,stress):
    op=f.open.to_numpy(float);hi=f.high.to_numpy(float);lo=f.low.to_numpy(float);cl=f.close.to_numpy(float)
    unix=f.time.to_numpy(np.int64)
    eq=INIT;peak=eq;dd=0.;busy=-1;records=[]
    for k,side,atr in signals(f):
        if k<=busy:continue
        ent=op[k];risk=1.5*atr
        if risk<=0 or risk/ent>.15:continue
        slip=(10. if stress else 5.) if symbol=="BTCUSD" else ent*(.00035 if stress else .0002)
        fill=ent+side*slip
        qty=min(eq*RISK/risk,eq*MAX_LEV/fill)
        if qty<=0:continue
        j,px,why,worst=exit_replay(op,hi,lo,cl,k,side,risk,3.,HOLD)
        busy=j
        slipout=(10. if stress else 5.) if symbol=="BTCUSD" else px*(.00035 if stress else .0002)
        exitfill=px-side*slipout
        pnl=qty*(side*(exitfill-fill)-FEE*(fill+exitfill))
        adverse=worst-side*((10. if stress else 5.) if symbol=="BTCUSD" else worst*(.00035 if stress else .0002))
        dd=max(dd,100*(1-(eq+qty*(side*(adverse-fill)-FEE*(fill+adverse)))/peak))
        start=eq;eq+=pnl
        if eq<=0:raise RuntimeError("Bankruptcy")
        peak=max(peak,eq);dd=max(dd,100*(1-eq/peak))
        records.append(dict(symbol=symbol,stress=stress,entry_unix=int(unix[k]),exit_unix=int(unix[j]),
            side=side,entry_mid=ent,exit_mid=px,entry_fill=fill,exit_fill=exitfill,
            quantity=qty,leverage=qty*fill/start,start_equity=start,end_equity=eq,
            net_usd=pnl,reason=("stop","target","timeout")[why]))
    return pd.DataFrame(records,columns=['symbol','stress','entry_unix','exit_unix','side','entry_mid','exit_mid','entry_fill','exit_fill','quantity','leverage','start_equity','end_equity','net_usd','reason']),dd

def month_end_nav(g, f, month, symbol, stress):
    """After-cost mark-to-market NAV at IST month end, without using future prices."""
    boundary=int((pd.Period(month,freq="M")+1).start_time.tz_localize("Asia/Kolkata").timestamp())-1
    unix=f.time.to_numpy(np.int64)
    i=int(np.searchsorted(unix,boundary,side="right"))-1
    if i<0: return INIT
    if boundary-int(unix[i])>60:
        raise ValueError(f"Missing month-end mark {month}: last bar {int(unix[i])}")
    mark=float(f.close.iloc[i])
    done=g[g.exit_unix<=boundary]
    nav=INIT+float(done.net_usd.sum())
    active=g[(g.entry_unix<=boundary)&(g.exit_unix>boundary)]
    if len(active)>1: raise AssertionError("Overlapping positions")
    for p in active.itertuples():
        slip=(10. if stress else 5.) if symbol=="BTCUSD" else mark*(.00035 if stress else .0002)
        exit_mark=mark-p.side*slip
        nav+=p.quantity*(p.side*(exit_mark-p.entry_fill)-FEE*(p.entry_fill+exit_mark))
    return nav

def report(g,symbol,stress,dd,f):
    g=g.copy()
    if len(g):g["month_ist"]=pd.to_datetime(g.exit_unix,unit="s",utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    else:g["month_ist"]=pd.Series(dtype=str)
    eq=INIT;rows=[]
    for month in MONTHS:
        t=g[g.month_ist==month];start=eq
        eq=month_end_nav(g,f,month,symbol,stress)
        pnl=eq-start
        rows.append(dict(symbol=symbol,stress=stress,month_ist=month,trades=len(t),
            wins=int((t.net_usd>0).sum()),losses=int((t.net_usd<0).sum()),
            profit_factor=profit_factor(t.net_usd),net_return_pct=100*pnl/start,
            net_pnl_usd=pnl,start_equity=start,end_equity=eq))
    if len(g) and int(g.exit_unix.max())<=int(f.time.iloc[-1]) and not np.isclose(
        eq,INIT+g.net_usd.sum(),rtol=1e-7,atol=1e-5):
        raise AssertionError("Final NAV vs realized ledger mismatch")
    m=pd.DataFrame(rows)
    t25=g[g.month_ist.str.startswith("2025-")];t26=g[g.month_ist.str.startswith("2026-")]
    strong=(m.trades>=3)&(m.profit_factor>=1.5)
    summary=dict(symbol=symbol,stress=stress,trades=len(g),wins=int((g.net_usd>0).sum()),
        losses=int((g.net_usd<0).sum()),overall_PF=profit_factor(g.net_usd),
        PF_2025=profit_factor(t25.net_usd),PF_2026_YTD=profit_factor(t26.net_usd),
        positive_months=int((m.net_return_pct>0).sum()),negative_months=int((m.net_return_pct<0).sum()),
        strong_months=int(strong.sum()),strong_5pct_months=int((strong&(m.net_return_pct>=5)).sum()),
        months_5pct=int((m.net_return_pct>=5).sum()),months_10pct=int((m.net_return_pct>=10).sum()),
        months_20pct=int((m.net_return_pct>=20).sum()),median_month_return_pct=float(m.net_return_pct.median()),
        median_finite_month_PF=float(m.loc[(m.trades>=3)&np.isfinite(m.profit_factor),"profit_factor"].median()),
        worst_month_pct=float(m.net_return_pct.min()),max_drawdown_pct=dd,
        net_2025_full_year_pct=100*(m.iloc[11].end_equity/INIT-1),
        net_2026_JanOct_YTD_pct=100*(m.iloc[-1].end_equity/m.iloc[11].end_equity-1),
        net_22_month_pct=100*(eq/INIT-1),full_year_2025_exceeds_500pct=bool(m.iloc[11].end_equity>6*INIT))
    return m,summary

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    months=[];summaries=[];ledgers=[];quality={}
    for symbol in ("BTCUSD","ETHUSD"):
        f,q=load_native(symbol);quality[symbol]=q
        for stress in (False,True):
            trades,dd=run(f,symbol,stress)
            m,s=report(trades,symbol,stress,dd,f)
            months.append(m);summaries.append(s);ledgers.append(trades)
    m=pd.concat(months,ignore_index=True);s=pd.DataFrame(summaries)
    t=pd.concat(ledgers,ignore_index=True)
    m.to_csv(OUT/"all_22_months.csv",index=False)
    s.to_csv(OUT/"summary.csv",index=False)
    t.to_csv(OUT/"original_trade_ledger.csv.gz",index=False,compression="gzip")
    (OUT/"quality.json").write_text(json.dumps(dict(data=quality,rule="Completed 1h volatility+volume shock (range >=2x prior 24h median, volume >=1.5x prior 7d median, close in outer 20% and directional body >=1.25x prior ATR); next-minute open; 1.5 ATR stop, 3R target, 24h timeout, one position",risk_fraction=RISK,leverage_cap=MAX_LEV,
       fee_per_side=.0005,GST=.18,BTC_slip_per_side=5,ETH_slip_fraction_per_side=.0002,
       limitations=["No actual funding cashflows","No historical order book/spread/impact","No contract minima or liquidation maintenance stress","2025 January first 330 IST minutes absent","2026 is not pristine out-of-sample","Single preset, no optimization"]),indent=2))
    (OUT/"RESEARCH_REPORT.md").write_text("# Stage31: Shock-driven delayed directional drift (pre-registered)\n\n## Economic hypothesis\nLarge directional price and volume shocks may induce delayed continuation through risk rebalancing and forced-flow propagation; falsified if subsequent price drift cannot overcome execution costs. Falsified if after-cost monthly PF and account returns fail to persist, or stress costs destroy any advantage.\n\n## Base monthly ledger\n\n"+m[~m.stress][["month_ist","symbol","net_return_pct","profit_factor","trades","wins","losses"]].to_markdown(index=False)+"\n\n## 2025 full year and 2026 Jan-Oct YTD\n\n"+s.to_markdown(index=False)+"\n")
    print("STAGE31_COMPLETE",s.to_json(orient="records"))
if __name__=="__main__":main()
