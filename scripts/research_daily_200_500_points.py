#!/usr/bin/env python3
"""BTCUSD target-200/300/500-point feasibility on genuine Delta 1m data.
Pre-specified, chronological validation; 1 trade/day/strategy;
no real order book or actual fills. No selection on holdout returns.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import json

IN=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/delta_points_200_500")
SPLIT=pd.Timestamp("2026-07-01",tz="UTC")
START_HOLDOUT="2026-07-01"
SLIP_POINTS_PER_SIDE=5.0
TAKER_FEE_RATE=0.0005
GST=0.18
TARGETS=[200,300,500]
STOPS=[150,250]
HOLD_MINUTES=120
NY="America/New_York"

def input_data():
    months=sorted(IN.glob("20??-??.csv.gz"))
    if len(months)<12: raise RuntimeError("Expected 1m monthly BTCUSD data")
    a=[]
    for p in months:
        f=pd.read_csv(p,compression="gzip")
        f["time"]=pd.to_datetime(f.time.astype("int64"),unit="s",utc=True)
        a.append(f[["time","open","high","low","close","volume"]])
    d=pd.concat(a,ignore_index=True).set_index("time").sort_index()
    assert d.index.is_unique and d.index.is_monotonic_increasing
    assert not d.isna().any().any()
    return d

def resample(d,n):
    cnt=d.close.resample(f"{n}min").count()
    x=d.resample(f"{n}min").agg(dict(open="first",high="max",low="min",close="last",volume="sum"))
    return x[cnt==n].dropna()

def events(d):
    b5=resample(d,5)
    b15=resample(d,15)
    recs=[]
    def emit(name,t,side,tf):
        if side not in (1,-1):return
        when=t+pd.Timedelta(minutes=tf)
        if when not in d.index:return
        local=when.tz_convert(NY)
        recs.append(dict(strategy=name,trigger_utc=str(t),entry_utc=when,
                         date_ny=str(local.date()),side=side))
    # Fixed-clock opening candle direction; not a claim of edge.
    loc=d.index.tz_convert(NY)
    mask=(loc.dayofweek<5)&(loc.hour==9)&(loc.minute==30)
    for t,r in d.loc[mask].iterrows():
        emit("NY_0930_first_1m_direction",t,int(r.close>r.open)-int(r.close<r.open),1)
    # 5m: large US opening candle follow-through
    r5=b5.high-b5.low
    r5prev=r5.rolling(24,min_periods=24).median().shift(1)
    m5=r5>1.5*r5prev
    m5=m5 & ((b5.close-b5.open).abs()/r5.replace(0,np.nan)>0.55)
    z=b5.index.tz_convert(NY)
    for t,r in b5[(z.dayofweek<5)&(z.hour==9)&(z.minute==30)&m5].iterrows():
        emit("NY_0930_big_5m_follow",t,int(r.close>r.open)-int(r.close<r.open),5)
    # 15m: reverse an unusually large US opening candle
    r15=b15.high-b15.low
    r15prev=r15.rolling(8,min_periods=8).median().shift(1)
    m15=(r15>1.7*r15prev)&((b15.close-b15.open).abs()/r15.replace(0,np.nan)>0.6)
    z=b15.index.tz_convert(NY)
    for t,r in b15[(z.dayofweek<5)&(z.hour==9)&(z.minute==30)&m15].iterrows():
        emit("NY_0930_large_15m_fade",t,-(int(r.close>r.open)-int(r.close<r.open)),15)
    # Trend breakout in liquid US session. Only past candles in all operands.
    b5["hi12"]=b5.high.rolling(12,min_periods=12).max().shift(1)
    b5["lo12"]=b5.low.rolling(12,min_periods=12).min().shift(1)
    b5["ema20"]=b5.close.ewm(span=20,adjust=False).mean()
    b5["ema50"]=b5.close.ewm(span=50,adjust=False).mean()
    b5["prior24"]=r5prev
    z=b5.index.tz_convert(NY)
    cand=b5[(z.dayofweek<5)&(z.hour>=9)&(z.hour<16)]
    for t,r in cand.iterrows():
        # Require completed bar is within 09:35..16:00 ET.
        end=(t+pd.Timedelta(minutes=5)).tz_convert(NY)
        if end.hour<9 or (end.hour==9 and end.minute<35):continue
        span=r.high-r.low
        if pd.isna(r.hi12) or pd.isna(r.prior24) or span<1.2*r.prior24:continue
        if span<=0 or abs(r.close-r.open)/span<0.55:continue
        side=0
        if r.close>r.hi12 and r.ema20>r.ema50 and r.close>r.ema20:side=1
        if r.close<r.lo12 and r.ema20<r.ema50 and r.close<r.ema20:side=-1
        emit("US_trend_5m_12bar_break",t,side,5)
    # Data-discovered 15m sequence from earlier exploration. Confirm on new holdout only.
    span=(b15.high-b15.low)
    strong_green=(b15.close>b15.open)&(span>1.8*r15prev)&((b15.close-b15.open)/span.replace(0,np.nan)>0.60)
    seq=(b15.close.shift(2)<b15.open.shift(2)) & strong_green.shift(1).fillna(False) & (b15.close>b15.open)
    for t in b15.index[seq]:
        emit("15m_red_impulsegreen_green_short",t,-1,15)
    f=pd.DataFrame(recs).sort_values("entry_utc")
    # Only the first qualifying event for each strategy per NY calendar day.
    return f.drop_duplicates(["strategy","date_ny"],keep="first").reset_index(drop=True)

def opportunity(d):
    local=d.index.tz_convert(NY)
    a=d.copy()
    a["day"]=list(local.date)
    a["weekday"]=local.dayofweek<5
    a["tod"]=local.hour*60+local.minute
    day=a.groupby("day",sort=True).agg(hi=("high","max"),lo=("low","min"),weekday=("weekday","max"))
    day["range_points"]=day.hi-day.lo
    opening=a[(a.weekday)&(a.tod>=570)&(a.tod<690)].groupby("day").agg(hi=("high","max"),lo=("low","min"))
    opening["range_points"]=opening.hi-opening.lo
    opening["period"]="NY_0930_to_1130"
    day["period"]="full_NY_day"
    opening=opening[["range_points","period"]]
    day=day[["range_points","period","weekday"]]
    opening["weekday"]=True
    both=pd.concat([day,opening]).reset_index()
    both["split"]=np.where(pd.to_datetime(both.day.astype(str)).dt.tz_localize("UTC")<SPLIT,"discovery","holdout")
    both["ge200"]=both.range_points>=200
    both["ge500"]=both.range_points>=500
    summary=both.groupby(["period","split","weekday"],observed=True).agg(
        days=("day","size"),median_range_points=("range_points","median"),
        days_range_ge200_pct=("ge200","mean"),days_range_ge500_pct=("ge500","mean")).reset_index()
    for col in ["days_range_ge200_pct","days_range_ge500_pct"]:
        summary[col]=(summary[col]*100).round(2)
    summary.median_range_points=summary.median_range_points.round(1)
    return both,summary

def trade_sim(d,ev):
    raw_open=d.open.to_numpy()
    raw_high=d.high.to_numpy()
    raw_low=d.low.to_numpy()
    raw_close=d.close.to_numpy()
    ix=d.index
    rows=[]
    for _,r in ev.iterrows():
        entry_ts=r.entry_utc
        j=int(ix.searchsorted(entry_ts))
        if j>=len(ix) or ix[j]!=entry_ts:continue
        # Require the entire minute path (no missing bars).
        end=j+HOLD_MINUTES
        if end>len(d) or ix[end-1]!=ix[j]+pd.Timedelta(minutes=HOLD_MINUTES-1):continue
        price=float(raw_open[j])
        side=int(r.side)
        for target in TARGETS:
            for stop in STOPS:
                result="time"; exit_price=float(raw_close[end-1]); held=HOLD_MINUTES
                for k in range(j,end):
                    take=(raw_high[k]>=price+target) if side==1 else (raw_low[k]<=price-target)
                    lose=(raw_low[k]<=price-stop) if side==1 else (raw_high[k]>=price+stop)
                    if lose: # pessimistic on simultaneous touch
                        exit_price=price-side*stop;result="stop";held=k-j+1;break
                    if take:
                        exit_price=price+side*target;result="target";held=k-j+1;break
                gross=side*(exit_price-price)
                fee_pts=TAKER_FEE_RATE*(1+GST)*(price+exit_price)
                net=gross-fee_pts-2*SLIP_POINTS_PER_SIDE
                rows.append(dict(strategy=r.strategy,ny_day=r.date_ny,
                    split="discovery" if entry_ts<SPLIT else "holdout",
                    entry_utc=str(entry_ts),side=side,target_points=target,stop_points=stop,
                    result=result,held_min=held,entry_price=round(price,2),
                    gross_points=round(gross,3),fee_points=round(fee_pts,3),
                    assumed_slippage_points=10,net_points=round(net,3),
                    net_usd_per_0_001btc=round(net*.001,4)))
    trades=pd.DataFrame(rows)
    if len(trades)==0: raise RuntimeError("No trades simulated")
    return trades

def make_summary(x):
    a=x.copy()
    a["win"]=a.net_points>0
    a["hit_target"]=a.result=="target"
    def worst_streak(vals):
        n=best=0
        for v in vals:
            n=n+1 if v<=0 else 0
            best=max(best,n)
        return best
    out=[]
    for keys,g in a.sort_values("entry_utc").groupby(["strategy","split","target_points","stop_points"],observed=True):
        strategy,split,tgt,stop=keys
        ordered=g.net_points.to_numpy()
        cum=np.cumsum(ordered)
        dd=float(np.max(np.maximum.accumulate(np.concatenate(([0],cum)))[1:]-cum))
        out.append(dict(strategy=strategy,split=split,target_points=tgt,stop_points=stop,
            trades=len(g),days_traded=g.ny_day.nunique(),target_hit_pct=round(100*g.hit_target.mean(),2),
            profitable_after_fees_pct=round(100*g.win.mean(),2),
            avg_gross_points=round(g.gross_points.mean(),2),avg_net_points=round(g.net_points.mean(),2),
            median_net_points=round(g.net_points.median(),2),total_net_points=round(g.net_points.sum(),2),
            max_drawdown_points=round(dd,1),max_loss_streak=worst_streak(ordered)))
    return pd.DataFrame(out).sort_values(["strategy","target_points","stop_points","split"])

def report(quality,opp,summary,res):
    hold=summary[summary.split=="holdout"].copy()
    pick=hold.sort_values(["avg_net_points","trades"],ascending=[False,False])
    best=pick.iloc[0]
    lines=[
        "# Can BTCUSD futures deliver 200–500 points every day?",
        "",
        "**Answer: no guaranteed daily capture.** This study distinguishes daily price RANGE from realizable trade P&L.",
        "**BTC points are USD price units per BTC, not INR or USD account profit.**",
        "",
        "## Dataset and validation",
        json.dumps(quality,indent=2),
        "",
        "Discovery before 2026-07-01 UTC; holdout July 1–October 17, 2026.",
        "One trade per NY calendar day per signal type, 120-minute maximum hold. For every trade, entry is at next real 1m open *after a fully completed trigger candle*.",
        "If stop and target both touch in a 1m candle, STOP counts first (pessimistic). No fabricated price paths.",
        "Fee assumption: futures MARKET taker 0.05% on entry and 0.05% on exit plus 18% GST on these fees; simulated slippage 5 BTC points per side. Maker/discount tiers and funding NOT modeled.",
        "No guarantee next-minute open is executable at OHLCV price; backtest approximation only.",
        "",
        "## Historical opportunity (high-low only, NOT a trade signal)",
        "",opp.to_markdown(index=False),"",
        "A day's high minus low can be hundreds/thousands of points without providing a profitable known-entry trade.",
        "",
        "## Holdout results, target/stop matrix",
        "",hold.to_markdown(index=False),"",
        "## Best numerical holdout row (NOT automatically a validated edge)",
        "",
        f"{best.strategy} TP{int(best.target_points)}/SL{int(best.stop_points)}, "
        f"n={int(best.trades)}, target-hit={best.target_hit_pct}%, net-profitable={best.profitable_after_fees_pct}%, "
        f"average net={best.avg_net_points} BTC points per trade.",
        "This top row is **selected from the holdout** for descriptive reporting, not valid as future predictive evidence.",
        "",
        "## Conclusions",
        "- No setup here proves a daily consistent 200–500 point take-profit.",
        "- Treat unexplained zero-volume candles and contract/symbol behavior as data-quality caveats.",
        "- No simulated position sizing/leverage; 0.001 BTC exposure maps one BTC price point to approximately $0.001 P&L before fees.",
        "- Before live execution: obtain actual bid/ask, funding, latency and incremental order book data, and run another untouched date-block validation.",
        ""]
    (OUT/"README.md").write_text("\n".join(lines),encoding="utf-8")

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    d=input_data()
    info=dict(rows=len(d),first=str(d.index.min()),last=str(d.index.max()),
        zero_volume=int((d.volume==0).sum()))
    op,ops=opportunity(d)
    ev=events(d)
    tr=trade_sim(d,ev)
    sm=make_summary(tr)
    ops.to_csv(OUT/"daily_opportunity_summary.csv",index=False)
    sm.to_csv(OUT/"target_stop_results.csv",index=False)
    ev.to_csv(OUT/"candidate_entries.csv",index=False)
    tr.to_csv(OUT/"individual_trade_replay.csv",index=False)
    report(info,ops,sm,tr)
    print("COMPLETE")
    print("QUALITY",json.dumps(info))
    print(ops.to_string(index=False))
    print("HOLDOUT",sm[sm.split=="holdout"].to_string(index=False))
if __name__=="__main__":
    main()
