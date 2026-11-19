#!/usr/bin/env python3
"""Stage27 falsifiable hypothesis: low-liquidity 00-06 IST range sweeps reverse during 06-18 IST.
Pre-registered one setting; native BTC and ETH 1m, no selection/optimization.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_paired_absorption_stage25 import load_native,exit_replay,profit_factor
OUT=Path("analysis/paired_session_sweep_stage27")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
INIT=10000.;FEE=.0005*1.18;RISK=.005;MAX_LEV=3.;HOLD=720

def signals(f):
    # All timestamps are UTC, convert explicitly to IST; only completed 15m candles.
    b=f[["open","high","low","close"]].resample("15min",closed="left",label="right").agg(
        {"open":"first","high":"max","low":"min","close":"last"})
    b["count"]=f.close.resample("15min",closed="left",label="right").count()
    b=b[b["count"]==15].copy()
    local=b.index.tz_convert("Asia/Kolkata")
    b["day"]=local.strftime("%Y-%m-%d")
    b["clock"]=local.hour*60+local.minute
    # Session candles right edges 00:15..06:00. Exclude 00:00 edge.
    asian=b[(b.clock>0)&(b.clock<=360)].groupby("day").agg(
        session_high=("high","max"),session_low=("low","min"),bars=("close","count"))
    asian=asian[asian.bars==24]
    b=b.join(asian[["session_high","session_low"]],on="day")
    prevclose=b.close.shift(1)
    tr=pd.concat([b.high-b.low,(b.high-prevclose).abs(),(b.low-prevclose).abs()],axis=1).max(axis=1)
    b["atr"]=tr.rolling(14,min_periods=14).mean()
    b["range"]=(b.session_high-b.session_low)
    # One sweep per day, either upper or lower, close back inside by >= 0.10 ATR.
    window=(b.clock>360)&(b.clock<=1080)&b.session_high.notna()&(b["range"]>=b.atr*1.0)
    upper=window&(b.high>b.session_high+b.atr*.1)&(b.close<b.session_high-b.atr*.1)&(b.close>b.session_low)
    lower=window&(b.low<b.session_low-b.atr*.1)&(b.close>b.session_low+b.atr*.1)&(b.close<b.session_high)
    candidates=b[upper|lower].copy()
    candidates["side"]=np.where(upper.loc[candidates.index],-1,1)
    candidates=candidates.groupby("day",sort=True).head(1)
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
    (OUT/"quality.json").write_text(json.dumps(dict(data=quality,rule="00:00-06:00 IST range, first 06:00-18:00 15m upper/lower wick sweep 0.1 ATR and close 0.1 ATR inside; enter next minute open fading sweep; stop 2 ATR; target 2R; timeout 12h; one position",risk_fraction=RISK,leverage_cap=MAX_LEV,
       fee_per_side=.0005,GST=.18,BTC_slip_per_side=5,ETH_slip_fraction_per_side=.0002,
       limitations=["No actual funding cashflows","No historical order book/spread/impact","No contract minima or liquidation maintenance stress","2025 January first 330 IST minutes absent","2026 is not pristine out-of-sample","Single preset, no optimization"]),indent=2))
    (OUT/"RESEARCH_REPORT.md").write_text("# Stage27: Asian range liquidity sweep fade (pre-registered)\n\n## Economic hypothesis\nThin overnight liquidity permits stop runs beyond the first 6h IST range; failed breakouts close inside and revert. Falsified if monthly after-cost PF and net returns do not persist in both native markets or costs stress destroys edge.\n\n## Base monthly ledger\n\n"+m[~m.stress][["month_ist","symbol","net_return_pct","profit_factor","trades","wins","losses"]].to_markdown(index=False)+"\n\n## 2025 full year and 2026 Jan-Oct YTD\n\n"+s.to_markdown(index=False)+"\n")
    print("STAGE27_COMPLETE",s.to_json(orient="records"))
if __name__=="__main__":main()
