#!/usr/bin/env python3
"""Stage29 falsifiable hypothesis: low-liquidity 00-06 IST range sweeps reverse during 06-18 IST.
Pre-registered one setting; native BTC and ETH 1m, no selection/optimization.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_paired_absorption_stage25 import load_native,exit_replay,profit_factor
OUT=Path("analysis/paired_volatility_transition_stage29")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
INIT=10000.;FEE=.0005*1.18;RISK=.005;MAX_LEV=3.;HOLD=720

def signals(f):
    # Volatility transition: 4h compression followed by a completed 15m
    # directional range escape. Historical percentiles only, no future data.
    b=f[["open","high","low","close","volume"]].resample("15min",closed="left",label="right").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    b["count"]=f.close.resample("15min",closed="left",label="right").count()
    complete=b["count"].eq(15)
    prev=b.close.shift(1)
    tr=pd.concat([b.high-b.low,(b.high-prev).abs(),(b.low-prev).abs()],axis=1).max(axis=1)
    b["atr"]=tr.rolling(14,min_periods=14).mean()
    # All prior-range and compression features end BEFORE the signal bar.
    prior_hi=b.high.shift(1).rolling(16,min_periods=16).max()
    prior_lo=b.low.shift(1).rolling(16,min_periods=16).min()
    prior_width=(prior_hi-prior_lo)/b.close.shift(1)
    history_median=prior_width.shift(1).rolling(672,min_periods=672).median()
    # Compression threshold fixed ex ante, not optimized on 2026.
    compressed=(prior_width<history_median*.65)
    body=(b.close-b.open).abs()/(b.high-b.low).replace(0,np.nan)
    expansion=(tr>b.atr.shift(1)*1.5)&(body>=.6)
    long=compressed&expansion&(b.close>prior_hi)&(b.close>b.open)
    short=compressed&expansion&(b.close<prior_lo)&(b.close<b.open)
    good=complete&complete.shift(1).rolling(672,min_periods=672).min().eq(1)&b.atr.gt(0)
    candidates=b[good&(long|short)].copy()
    candidates["side"]=np.where(long.loc[candidates.index],1,-1)
    ix=f.index.get_indexer(candidates.index)
    return [(int(k),int(s),float(a)) for k,s,a in zip(ix,candidates.side,candidates.atr) if k>=0 and np.isfinite(a) and a>0]

def run(f,symbol,stress):
    op=f.open.to_numpy(float);hi=f.high.to_numpy(float);lo=f.low.to_numpy(float);cl=f.close.to_numpy(float)
    unix=f.time.to_numpy(np.int64)
    eq=INIT;peak=eq;dd=0.;busy=-1;records=[]
    for k,side,atr in signals(f):
        if k<=busy:continue
        ent=op[k];risk=2.*atr
        if risk<=0 or risk/ent>.15:continue
        slip=(10. if stress else 5.) if symbol=="BTCUSD" else ent*(.00035 if stress else .0002)
        fill=ent+side*slip
        qty=min(eq*RISK/risk,eq*MAX_LEV/fill)
        if qty<=0:continue
        j,px,why,worst=exit_replay(op,hi,lo,cl,k,side,risk,2.,HOLD)
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
    return pd.DataFrame(records),dd

def report(g,symbol,stress,dd):
    g=g.copy()
    if len(g):g["month_ist"]=pd.to_datetime(g.exit_unix,unit="s",utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    else:g["month_ist"]=pd.Series(dtype=str)
    eq=INIT;rows=[]
    for month in MONTHS:
        t=g[g.month_ist==month];start=eq;pnl=float(t.net_usd.sum());eq+=pnl
        rows.append(dict(symbol=symbol,stress=stress,month_ist=month,trades=len(t),
            wins=int((t.net_usd>0).sum()),losses=int((t.net_usd<0).sum()),
            profit_factor=profit_factor(t.net_usd),net_return_pct=100*pnl/start,
            net_pnl_usd=pnl,start_equity=start,end_equity=eq))
    if len(g) and not np.isclose(eq,g.iloc[-1].end_equity):raise AssertionError("Equity mismatch")
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
            m,s=report(trades,symbol,stress,dd)
            months.append(m);summaries.append(s);ledgers.append(trades)
    m=pd.concat(months,ignore_index=True);s=pd.DataFrame(summaries)
    t=pd.concat(ledgers,ignore_index=True)
    m.to_csv(OUT/"all_22_months.csv",index=False)
    s.to_csv(OUT/"summary.csv",index=False)
    t.to_csv(OUT/"original_trade_ledger.csv.gz",index=False,compression="gzip")
    (OUT/"quality.json").write_text(json.dumps(dict(data=quality,rule="15m close beyond preceding 4h high/low after prior 4h range width <65% of trailing 7-day historical median, signal true range >1.5x prior ATR and body >=60%; next-minute open continuation; 2 ATR stop; 2R target; 12h timeout; one position",risk_fraction=RISK,leverage_cap=MAX_LEV,
       fee_per_side=.0005,GST=.18,BTC_slip_per_side=5,ETH_slip_fraction_per_side=.0002,
       limitations=["No actual funding cashflows","No historical order book/spread/impact","No contract minima or liquidation maintenance stress","2025 January first 330 IST minutes absent","2026 is not pristine out-of-sample","Single preset, no optimization"]),indent=2))
    (OUT/"RESEARCH_REPORT.md").write_text("# Stage29: Volatility compression-to-expansion breakout (pre-registered)\n\n## Economic hypothesis\nVolatility clustering and dealer hedging can create directional continuation when a compressed four-hour range resolves into an abrupt high-conviction breakout. Falsified if after-cost monthly PF and account returns fail to persist, or stress costs destroy any advantage.\n\n## Base monthly ledger\n\n"+m[~m.stress][["month_ist","symbol","net_return_pct","profit_factor","trades","wins","losses"]].to_markdown(index=False)+"\n\n## 2025 full year and 2026 Jan-Oct YTD\n\n"+s.to_markdown(index=False)+"\n")
    print("STAGE29_COMPLETE",s.to_json(orient="records"))
if __name__=="__main__":main()
