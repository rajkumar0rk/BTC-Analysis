#!/usr/bin/env python3
"""Predeclared realized third-moment tail-risk continuation; one signal/day, no grid."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

OUT=Path("analysis/daily_realized_skew_premium_20261119_v1")
ROOT=Path("data/delta_india")
START="2025-01-01"
END="2026-11-17"
FEE_RATE=.0005*1.18 # taker each way, GST included
SLIP_RATE=.0002 # each way adverse slippage; spread may be additional, stress below
STOP=.006
TARGET=.009
HOLD=120
SKW_THRESHOLD=.5
CAPITAL=1000.
NOTIONAL=1000. # 1x, avoids margin-based overstatement
def load(sym):
    paths=sorted((ROOT/sym/"1m").glob("20??-??.csv.gz"))
    if not paths: raise RuntimeError("Missing authentic archive: "+sym)
    z=[]
    for p in paths:
        if p.name[:7] > "2026-11":continue
        a=pd.read_csv(p,compression="gzip")
        needed={"time","open","high","low","close","volume"}
        if not needed.issubset(a):raise RuntimeError(f"{p}: missing {needed-set(a)}")
        a["ts"]=pd.to_datetime(a.time.astype("int64"),unit="s",utc=True)
        z.append(a[["ts","open","high","low","close","volume"]])
    x=pd.concat(z,ignore_index=True).set_index("ts").sort_index()
    if x.index.has_duplicates:raise RuntimeError("Duplicate minute bars "+sym)
    if x[["open","high","low","close"]].isna().any().any():raise RuntimeError("Null OHLC "+sym)
    return x.loc[START:END]
def evaluate(sym):
    x=load(sym)
    # Only completed minute returns before entry may enter the trailing skew statistic.
    r=np.log(x.close).diff()
    # Daily timestamp 00:00 UTC; previous 24h [yesterday 00:00, yesterday 23:59].
    rows=[]; trades=[]
    days=pd.date_range("2025-01-02","2026-11-17",freq="D",tz="UTC")
    for day in days:
        prev=x.loc[day-pd.Timedelta(days=1):day-pd.Timedelta(minutes=1)]
        today=x.loc[day:day+pd.Timedelta(minutes=HOLD-1)]
        # Daily 1m bars complete; a gap disqualifies day, no fabricated fills.
        complete=(len(prev)==1440 and len(today)==HOLD
                  and prev.index[0]==day-pd.Timedelta(days=1)
                  and prev.index[-1]==day-pd.Timedelta(minutes=1)
                  and today.index[0]==day and today.index[-1]==day+pd.Timedelta(minutes=HOLD-1))
        status="no_trade"; net=0.; gross=0.; fees=0.; slip=0.; side=0; skew=np.nan; exit_reason=""
        if complete:
            # 1439 within-day returns, excluding cross-midnight jump.
            v=np.diff(np.log(prev.close.to_numpy(dtype=float)))
            sigma=v.std()
            if sigma>0:
                skew=float(np.mean(((v-v.mean())/sigma)**3))
                # Economic hypothesis: negative realized tail asymmetry persists; positive opposite.
                side=-1 if skew < -SKW_THRESHOLD else (1 if skew > SKW_THRESHOLD else 0)
                if side:
                    entry=float(today.open.iloc[0]); exit_price=float(today.close.iloc[-1]);exit_reason="time"
                    for j,b in enumerate(today.itertuples()):
                        if side==1:
                            sl=entry*(1-STOP);tp=entry*(1+TARGET)
                            if b.low<=sl:exit_price=sl;exit_reason="stop";break
                            if b.high>=tp:exit_price=tp;exit_reason="target";break
                        else:
                            sl=entry*(1+STOP);tp=entry*(1-TARGET)
                            if b.high>=sl:exit_price=sl;exit_reason="stop";break
                            if b.low<=tp:exit_price=tp;exit_reason="target";break
                    gross=NOTIONAL*side*(exit_price-entry)/entry
                    fees=NOTIONAL*2*FEE_RATE
                    slip=NOTIONAL*2*SLIP_RATE
                    net=gross-fees-slip
                    status="profit" if net>0 else ("loss" if net<0 else "flat")
                    trades.append(dict(symbol=sym,day=str(day.date()),side=side,skew=skew,entry=entry,exit=exit_price,
                        exit_reason=exit_reason,gross_usd=gross,fees_gst_usd=fees,slippage_usd=slip,net_usd=net))
        else:
            status="data_gap"
        rows.append(dict(symbol=sym,day=str(day.date()),year=day.year,month=str(day.date())[:7],status=status,
            signal_skew=skew,side=side,gross_usd=gross,fees_gst_usd=fees,slippage_usd=slip,net_usd=net,
            stress_net_usd=net-(2*.0002*NOTIONAL if side else 0)))
    return pd.DataFrame(rows),pd.DataFrame(trades),dict(symbol=sym,archive_first=str(x.index[0]),archive_last=str(x.index[-1]),bars=len(x),
        expected_minutes=int((x.index[-1]-x.index[0]).total_seconds()/60)+1,missing_minutes=int((x.index[-1]-x.index[0]).total_seconds()/60)+1-len(x))
def stats(g):
    a=g.net_usd.to_numpy();tr=g[g.side!=0];w=a[a>0].sum();l=-a[a<0].sum()
    eq=np.r_[CAPITAL,CAPITAL+np.cumsum(a)]
    draw=(np.maximum.accumulate(eq)-eq).max()/CAPITAL*100
    streak=0;worst=0
    for z in a:
        streak=streak+1 if z<0 else 0;worst=max(worst,streak)
    return dict(days=len(g),profit_days=int((a>0).sum()),loss_days=int((a<0).sum()),no_trade_days=int((g.status=="no_trade").sum()),
        data_gap_days=int((g.status=="data_gap").sum()),trades=len(tr),profit_calendar_pct=round(100*np.mean(a>0),2),
        median_day_usd=round(float(np.median(a)),4),mean_day_usd=round(float(np.mean(a)),4),
        worst_day_usd=round(float(a.min()),4),net_usd=round(float(a.sum()),4),return_pct=round(float(a.sum()/CAPITAL*100),3),
        pf=round(float(w/l),4) if l>0 else None,max_drawdown_pct=round(float(draw),3),max_loss_day_streak=worst,
        fees_gst_usd=round(float(g.fees_gst_usd.sum()),4),slippage_usd=round(float(g.slippage_usd.sum()),4),
        stress_net_usd=round(float(g.stress_net_usd.sum()),4))
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    ledgers=[];trades=[];quality=[]
    for sym in ["BTCUSD","ETHUSD"]:
        d,t,q=evaluate(sym);ledgers.append(d);trades.append(t);quality.append(q)
    d=pd.concat(ledgers,ignore_index=True);t=pd.concat(trades,ignore_index=True)
    d.to_csv(OUT/"daily_ledger.csv",index=False);t.to_csv(OUT/"trade_ledger.csv",index=False)
    monthly=d.groupby(["symbol","month"],sort=True).agg(net_usd=("net_usd","sum"),profit_days=("net_usd",lambda x:(x>0).sum()),
        loss_days=("net_usd",lambda x:(x<0).sum()),trades=("side",lambda x:(x!=0).sum())).reset_index()
    monthly["net_return_pct"]=monthly.net_usd/CAPITAL*100
    monthly.to_csv(OUT/"monthly.csv",index=False)
    annual=[]
    for (sym,yr),g in d.groupby(["symbol","year"]):
        annual.append(dict(symbol=sym,year=int(yr),**stats(g)))
    pd.DataFrame(annual).to_csv(OUT/"annual.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    report=["# Pre-registered realized-skew tail-risk continuation","",
    "Hypothesis: trailing 24h 1m return third moment reveals persistent asymmetric tail-risk pressure, predicting same-sign 2h drift. Test independently for BTCUSD and ETHUSD; no optimization.",
    "Signal at 00:00 UTC based solely on 1439 within-previous-day completed 1m returns; long if skew > +0.5, short if skew < -0.5; otherwise no trade. Enter 00:00 minute open, stop 0.6%, target 0.9%, 120-minute time exit, first touched stop wins ambiguity. One position/day, fixed $1,000 notional on $1,000 equity, no averaging.",
    "Costs: taker each side 0.05% +18% GST, plus 0.02% slippage each side, total 0.158% of notional roundtrip; stress adds 0.04% roundtrip. Funding assumed zero for <=2h (unverified settlement timing); spread is represented only by slippage, so actual execution may be worse. This is NOT an executable quote/fee/funding replay; no orderbook queue, liquidation path or exchange minimums verified. No leverage, no borrowing. 2026 is research-exposed, not pristine holdout.",
    "Archive completeness is strict for entry signal and hold; missing minutes become DATA_GAP, never winning or losing days.",
    "", "## Data integrity",json.dumps(quality,indent=2),"","## Calendar-year results",pd.DataFrame(annual).to_markdown(index=False),"","## Every calendar month",monthly.to_markdown(index=False),"",
    "If the signal fails across both years after costs, REJECT rather than tune. No daily-profit strategy is claimed."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("RESEARCH_COMPLETE");print(pd.DataFrame(annual).to_string(index=False));print(json.dumps(quality))
if __name__=="__main__":main()
