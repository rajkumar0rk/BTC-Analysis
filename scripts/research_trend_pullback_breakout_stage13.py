#!/usr/bin/env python3
"""Stage13: 4H EMA trend, completed 1H EMA20 pullback, later 15M breakout, 1M fills.

Two predefined pullback definitions, two volume choices, 2R/3R, and 4h/8h
timeouts. This is historical exploratory research, not forward validation.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit
from research_every_candle_200 import read_archive, periods, PERIOD_NAMES, FEE, SLIPPAGE

OUT=Path("analysis/institutional_discovery_stage13_4h_1h_15m")
PB=("touch","near_half_atr")
VOL=("any","volume_1p2x")
RR=(2.0,3.0)
HOLD=(240,480)
MIN_RISK,MAX_RISK=150.0,1600.0

def tf(f,unit,history):
    key={15:"15min",60:"1h",240:"4h"}[unit]
    a=f[["open","high","low","close","volume"]].resample(
        key,closed="left",label="right").agg({
        "open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    a["count"]=f.close.resample(key,closed="left",label="right").count()
    a["valid"]=a["count"].rolling(history,min_periods=history).min().eq(unit)
    prior=a.close.shift(1)
    true_range=pd.concat([a.high-a.low,(a.high-prior).abs(),
                          (a.low-prior).abs()],axis=1).max(axis=1)
    a["atr14"]=true_range.rolling(14,min_periods=14).mean()
    return a

def events(f,start,end,p):
    four=tf(f,240,60)
    hour=tf(f,60,50)
    quarter=tf(f,15,30)
    four["ema20"]=four.close.ewm(span=20,adjust=False).mean()
    four["ema50"]=four.close.ewm(span=50,adjust=False).mean()
    four["bull"]=four.valid&(four.close>four.ema20)&(
        four.ema20>four.ema50)&(four.ema20.diff(3)>0)
    four["bear"]=four.valid&(four.close<four.ema20)&(
        four.ema20<four.ema50)&(four.ema20.diff(3)<0)
    hour["ema20"]=hour.close.ewm(span=20,adjust=False).mean()
    q=quarter
    q["high4"]=q.high.shift(1).rolling(4,min_periods=4).max()
    q["low4"]=q.low.shift(1).rolling(4,min_periods=4).min()
    q["support5"]=q.low.rolling(5,min_periods=5).min()
    q["resistance5"]=q.high.rolling(5,min_periods=5).max()
    q["vol_ratio"]=q.volume/q.volume.shift(1).rolling(20,min_periods=20).mean().replace(0,np.nan)
    rng=(q.high-q.low).replace(0,np.nan)
    loc=(q.close-q.low)/rng
    body=(q.close-q.open).abs()/rng
    q["long_break"]=q.valid&(q.close>q.high4)&(q.close>q.open)&(
        loc>=.75)&(body>=.40)
    q["short_break"]=q.valid&(q.close<q.low4)&(q.close<q.open)&(
        loc<=.25)&(body>=.40)
    # Hour candle must have been fully completed BEFORE the 15M breakout candle.
    # 15-minute shift excludes the hour currently closing at the same moment.
    times=q.index
    h=hour.reindex(times-pd.Timedelta(minutes=15),method="ffill")
    h.index=times
    f4=four.reindex(times,method="ffill")
    f4.index=times
    fi=f.index
    locs=fi.get_indexer(times)
    raw=[]
    skipped=dict(source_gap=0,risk=0,period_boundary=0)
    for side in (1,-1):
        trending=(f4.bull if side==1 else f4.bear).fillna(False)
        breakout=(q.long_break if side==1 else q.short_break).fillna(False)
        base=trending & breakout & h.valid.fillna(False)
        for mode in PB:
            margin=0.0 if mode=="touch" else 0.5
            pull=(h.low<=h.ema20+margin*h.atr14)&(h.close>h.ema20) if side==1 else (
                  h.high>=h.ema20-margin*h.atr14)&(h.close<h.ema20)
            which=np.flatnonzero((base & pull.fillna(False)).to_numpy(bool))
            for j in which:
                k=int(locs[j])
                if k<0 or k-start[k]<60*24*10 or end[k]-k<max(HOLD):
                    skipped["source_gap"]+=1
                    continue
                if p[k]!=p[k+max(HOLD)-1]:
                    skipped["period_boundary"]+=1
                    continue
                entry=float(f.open.iat[k])
                buffer=max(10.0,0.1*float(q.atr14.iat[j]))
                if side==1:
                    stop=min(float(h.low.iat[j]),float(q.support5.iat[j]))-buffer
                else:
                    stop=max(float(h.high.iat[j]),float(q.resistance5.iat[j]))+buffer
                risk=side*(entry-stop)
                if not np.isfinite(risk) or not MIN_RISK<=risk<=MAX_RISK:
                    skipped["risk"]+=1
                    continue
                raw.append(dict(k=k,unix=int(f.time.iat[k]),
                    side=side,pullback=mode,period=PERIOD_NAMES[int(p[k])],
                    direction="LONG" if side==1 else "SHORT",
                    stop_price=stop,risk_pts=risk,
                    volume_ratio=float(q.vol_ratio.iat[j])))
    data=pd.DataFrame(raw)
    if data.empty:raise ValueError("No completed 4H/1H/15M entries")
    return data.sort_values(["k","side"]),skipped

@njit(cache=True)
def play(O,H,L,C,k,side,stop,R,horizon):
    entry=O[k]
    risk=side*(entry-stop)
    target=entry+side*R*risk
    for j in range(k,k+horizon):
        stop_hit=L[j]<=stop if side==1 else H[j]>=stop
        take_hit=H[j]>=target if side==1 else L[j]<=target
        if stop_hit:
            mid=min(O[j],stop) if side==1 else max(O[j],stop)
            reason=0
            break
        if take_hit:
            mid=target
            reason=1
            break
    else:
        j=k+horizon-1
        mid=C[j]
        reason=2
    a=entry+side*SLIPPAGE
    b=mid-side*SLIPPAGE
    gross=side*(mid-entry)
    net=side*(b-a)-FEE*(a+b)
    offer=side*(b-a)-FEE*a-(0. if j-k+1<=30 else FEE*b)
    return j,reason,gross,net,offer

def simulate(ev,f):
    O=f.open.to_numpy(np.float64)
    H=f.high.to_numpy(np.float64)
    L=f.low.to_numpy(np.float64)
    C=f.close.to_numpy(np.float64)
    results=[]
    for pb in PB:
        subset=ev[ev.pullback==pb]
        for vol in VOL:
            sub=subset if vol=="any" else subset[subset.volume_ratio>=1.2]
            sub=sub.sort_values(["k","side"])
            for R in RR:
                for horizon in HOLD:
                    busy=-1
                    for e in sub.itertuples():
                        if e.k<=busy:continue
                        j,why,gross,net,offer=play(O,H,L,C,int(e.k),int(e.side),
                            float(e.stop_price),float(R),int(horizon))
                        busy=j
                        results.append(dict(pullback=pb,volume=vol,target_R=R,
                            max_hold_min=horizon,period=e.period,
                            entry_unix=int(e.unix),
                            exit_unix=int(e.unix+60*(j-e.k)),
                            direction=e.direction,reason=int(why),
                            risk_pts=round(float(e.risk_pts),2),
                            gross_pts=round(float(gross),2),
                            net_pts=round(float(net),2),
                            offer_whatif=round(float(offer),2)))
    tr=pd.DataFrame(results)
    if tr.empty:raise ValueError("No executed trades")
    return tr

def reports(tr):
    summary=[]
    for names,g in tr.groupby(["pullback","volume","target_R","max_hold_min","period"]):
        for fee,col in (("standard_taker","net_pts"),("scalper_whatif","offer_whatif")):
            v=g[col].to_numpy(float)
            eq=np.r_[0.,np.cumsum(v)]
            profit=float(v[v>0].sum())
            loss=float(-v[v<0].sum())
            summary.append(dict(zip(["pullback","volume","target_R","max_hold_min","period"],names),
                fee=fee,trades=len(g),longs=int((g.direction=="LONG").sum()),
                shorts=int((g.direction=="SHORT").sum()),
                wins=int((v>0).sum()),losses=int((v<=0).sum()),
                win_rate=round(100*float((v>0).mean()),2),
                mean_net=round(float(v.mean()),2),net_total=round(float(v.sum()),2),
                profit_factor=round(profit/loss,3) if loss else None,
                worst_trade=round(float(v.min()),2),
                max_drawdown=round(float(np.max(np.maximum.accumulate(eq)-eq)),2)))
    sm=pd.DataFrame(summary)
    months=pd.period_range("2025-01","2026-11",freq="M").astype(str)
    tr=tr.copy()
    tr["month"]=pd.to_datetime(tr.entry_unix,unit="s",utc=True).dt.tz_convert(
        "Asia/Kolkata").dt.strftime("%Y-%m")
    monthly=[]
    keys=["pullback","volume","target_R","max_hold_min"]
    for names,g in tr.groupby(keys):
        m=g.groupby("month").net_pts.agg(["count","sum"]).reindex(months,fill_value=0)
        for month,z in m.iterrows():
            n=int(z["count"]);pts=float(z["sum"])
            monthly.append(dict(zip(keys,names),month_ist=month,trades=n,
                net_pts=round(pts,2),status="No trade" if n==0 else
                    "Profit" if pts>0 else "Loss" if pts<0 else "Flat"))
    mo=pd.DataFrame(monthly)
    checks=[]
    for names,g in mo.groupby(keys):
        s=sm[(sm.fee=="standard_taker")&
             (sm.pullback==names[0])&(sm.volume==names[1])&
             (sm.target_R==names[2])&(sm.max_hold_min==names[3])]
        periods={z.period:z for z in s.itertuples()}
        y25=g[g.month_ist.str.startswith("2025")]
        y26=g[g.month_ist.str.startswith("2026")]
        active25=int((y25.trades>0).sum())
        active26=int((y26.trades>0).sum())
        good25=int((y25.status=="Profit").sum())
        good26=int((y26.status=="Profit").sum())
        enough=all(t in periods for t in PERIOD_NAMES[:3]) and (
            periods[PERIOD_NAMES[0]].trades>=50 and
            periods[PERIOD_NAMES[1]].trades>=25 and
            periods[PERIOD_NAMES[2]].trades>=15)
        positive=all(t in periods for t in PERIOD_NAMES[:3]) and (
            min(periods[t].mean_net for t in PERIOD_NAMES[:3])>0)
        passes=bool(enough and positive and active25>=9 and active26>=8 and
            good25/active25>=.7 and good26/active26>=.7)
        checks.append(dict(zip(keys,names),
            trades_2025=int(y25.trades.sum()),profitable_2025=good25,
            losing_2025=int((y25.status=="Loss").sum()),no_trade_2025=int((y25.trades==0).sum()),
            net_2025=round(float(y25.net_pts.sum()),2),
            trades_2026=int(y26.trades.sum()),profitable_2026=good26,
            losing_2026=int((y26.status=="Loss").sum()),no_trade_2026=int((y26.trades==0).sum()),
            net_2026=round(float(y26.net_pts.sum()),2),
            sufficient_samples=bool(enough),positive_2025_H1_H2=bool(positive),
            passes_monthly_gate=passes))
    return sm,mo,pd.DataFrame(checks)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,start,end,q=read_archive()
    p=periods(f.index)
    ev,skip=events(f,start,end,p)
    trades=simulate(ev,f)
    sm,mo,check=reports(trades)
    ev.to_csv(OUT/"events.csv.gz",index=False,compression="gzip")
    trades.to_csv(OUT/"trades.csv.gz",index=False,compression="gzip")
    sm.to_csv(OUT/"strategy_summary.csv",index=False)
    mo.to_csv(OUT/"monthly_IST.csv",index=False)
    check.to_csv(OUT/"monthly_consistency.csv",index=False)
    meta=dict(archive_candles=len(f),source_gap_minutes=q["missing_minutes"],
        date_range=[str(f.index[0]),str(f.index[-1])],events=len(ev),
        trades_across_models=len(trades),strategy_variants=16,
        standard_positive_cells=int(((sm.fee=="standard_taker")&(sm.mean_net>0)).sum()),
        monthly_gate_passes=int(check.passes_monthly_gate.sum()),
        skipped_candidates=skip,
        rules=dict(trend="4H close>EMA20>EMA50 and EMA20 rising over three completed bars (inverse SHORT)",
            pullback="Prior fully completed 1H candle touches 1H EMA20, closes back on trend side; alternate within half ATR",
            trigger="Later complete 15M candle close beyond previous four 15M candle highs/lows; body>=40%, close in last 25% of range",
            volume="Breakout 15M volume>=1.2x prior 20 bars optional",
            entry="Immediate next 1M OPEN after 15M candle close",
            stop="Beyond 1H pullback and recent five 15M candle extreme plus max(10 points, 0.1x ATR15)",
            stop_risk_points=[MIN_RISK,MAX_RISK],
            reward_R=list(RR),max_hold_minutes=list(HOLD)),
        caveats=[
            "All tested historical periods already used in previous research, not a pristine out-of-sample test",
            "2026-10-31 is missing from source; 2026-11 ends Nov 16",
            "Fees 0.05% taker/side, 18% GST, adverse 5 BTC points slippage per side; included in standard net",
            "Scalper Offer closing fee waiver is hypothetical and not assumed for standard PnL",
            "Funding, order-book spreads, margin, liquidation and impact not modeled",
            "Stops resolved first when OHLC bar touches stop and target; gap stop can fill worse",
            "All months with zero trades included; no guarantee of monthly profitability",
            "Aggregate BTC price points are not account profit or capital returns",
            "One open trade at a time within a model, LONG and SHORT mutually exclusive"])
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
    baseline=mo[(mo.pullback=="touch")&(mo.volume=="volume_1p2x")&
                (mo.target_R==2)&(mo.max_hold_min==480)]
    report=[
        "# Stage 13 — 4H trend + 1H EMA20 pullback + 15M breakout",
        "",
        "Rules predeclared: two pullback strictness choices, optional 15M breakout volume,",
        "2R/3R target and 4h/8h maximum hold, 16 strategy configurations.",
        "Every signal uses completed candles, next 1M OPEN execution, and structural stop.",
        "No fixed trading time. Historical 2026 has already been researched.",
        "",
        "## Monthly research consistency",
        check.to_markdown(index=False),"",
        "## Full standard after-fee period results",
        sm[sm.fee=="standard_taker"].to_markdown(index=False),"",
        "## Baseline monthly table: strict touch + volume + 2R + 8h",
        baseline.to_markdown(index=False),"",
        "## Interpretation",
        "A passed research gate requires >=70% profitable active months in each year,",
        "at least 9 active months 2025 and 8 in 2026, and positive expectancy in",
        "2025, 2026 H1 and 2026 H2 with >=50/25/15 trades.",
        "Passing historical rules does NOT establish live profitability.",
        "",
        "## Caveats",
        *["- "+v for v in meta["caveats"]],
        "",
        "Reproduce using scripts/research_trend_pullback_breakout_stage13.py.",
        "Detailed events/trades saved in the associated GitHub Actions artifact."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE13_DONE "+json.dumps({k:meta[k] for k in (
        "archive_candles","events","trades_across_models",
        "standard_positive_cells","monthly_gate_passes")}))
    print("MONTHLY_CONSISTENCY\n"+check.to_string(index=False))
    print("BASELINE_MONTHLY\n"+baseline.to_string(index=False))
    print("2025_STANDARD\n"+sm[(sm.fee=="standard_taker")&
                             (sm.period=="2025_train")].to_string(index=False))

if __name__=="__main__":
    main()
