#!/usr/bin/env python3
"""Stage 1 big-trend trend/5m-breakout/retest research using original Delta 1m candles."""
import itertools, json
from pathlib import Path
import numpy as np
import pandas as pd

DATA=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/big_trend_stage1")
FEE=.0005*1.18
SLIP=5.
SIDES=(1,-1)
TRENDS=("three_closes","two_structure")
LOOKBACKS=(12,24)
QUALS=("plain","compression_volume")
ENTRIES=("immediate","retest")
EXITS=("fixed_3r","trail_5r")
SESSIONS=("ALL_UTC","NY_OPEN","LONDON_OPEN","INDIA_MORNING")
PERIODS=("train","validation","recheck_seen")
def load():
    parts=[]
    for p in sorted(DATA.glob("20??-??.csv.gz")):
        z=pd.read_csv(p,compression="gzip",usecols=["time","open","high","low","close","volume"])
        z.index=pd.to_datetime(z["time"].astype("int64"),unit="s",utc=True)
        parts.append(z.drop(columns="time"))
    if not parts:raise RuntimeError("No real Delta BTCUSD 1m files")
    f=pd.concat(parts).sort_index()
    if f.index.has_duplicates or f.isna().any().any() or not f.index.to_series().diff().iloc[1:].eq(pd.Timedelta(minutes=1)).all():
        raise ValueError("1m time, null or uniqueness integrity failure")
    return f
def session_masks(idx):
    def mask(zone,start,end):
        x=idx.tz_convert(zone);m=x.hour*60+x.minute
        return np.asarray((x.dayofweek<5)&(m>=start)&(m<end))
    return {"ALL_UTC":np.ones(len(idx),bool),
       "NY_OPEN":mask("America/New_York",570,720),
       "LONDON_OPEN":mask("Europe/London",480,660),
       "INDIA_MORNING":mask("Asia/Kolkata",540,720)}
def features(f):
    # 5m row t is complete at t+5. Decision uses its close; fill next 5m OPEN.
    c=f.resample("5min",label="left",closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    if not (f.close.resample("5min").count()==5).all():
        raise ValueError("Incomplete 5m bars")
    h=f.resample("1h",label="left",closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last"})
    if not (f.close.resample("1h").count()==60).all():
        raise ValueError("Incomplete 1h bars")
    close_up=(h.close>h.close.shift(1))&(h.close.shift(1)>h.close.shift(2))&(h.close.shift(2)>h.close.shift(3))&(h.close>h.open)
    close_dn=(h.close<h.close.shift(1))&(h.close.shift(1)<h.close.shift(2))&(h.close.shift(2)<h.close.shift(3))&(h.close<h.open)
    up=(h.high>h.high.shift(1))&(h.low>h.low.shift(1))&(h.high.shift(1)>h.high.shift(2))&(h.low.shift(1)>h.low.shift(2))&(h.close>h.open)
    down=(h.high<h.high.shift(1))&(h.low<h.low.shift(1))&(h.high.shift(1)<h.high.shift(2))&(h.low.shift(1)<h.low.shift(2))&(h.close<h.open)
    hh={}
    for name,po,ne in [("three_closes",close_up,close_dn),("two_structure",up,down)]:
        hh[(name,1)]=po.shift(1).reindex(c.index,method="ffill").fillna(False).to_numpy(bool)
        hh[(name,-1)]=ne.shift(1).reindex(c.index,method="ffill").fillna(False).to_numpy(bool)
    candle_range=(c.high-c.low).replace(0,np.nan)
    tr=pd.concat([c.high-c.low,(c.high-c.close.shift()).abs(),(c.low-c.close.shift()).abs()],axis=1).max(axis=1)
    atr=tr.rolling(14,min_periods=14).mean().to_numpy(float)
    six=(c.high.rolling(6,min_periods=6).max()-c.low.rolling(6,min_periods=6).min())
    median=six.shift(1).rolling(72,min_periods=72).median()
    volavg=c.volume.shift(1).rolling(24,min_periods=24).mean()
    qualified=((six.shift(1)<.75*median)&(c.volume>=1.2*volavg)).fillna(False).to_numpy(bool)
    levels={}
    for look in LOOKBACKS:
        levels[(look,1)]=c.high.shift(1).rolling(look,min_periods=look).max().to_numpy(float)
        levels[(look,-1)]=c.low.shift(1).rolling(look,min_periods=look).min().to_numpy(float)
    return c,hh,atr,qualified,levels
def run(f,c,hour,atr,qualified,levels):
    one=f
    n=len(one); five=len(c)
    op=one.open.to_numpy(float);hi=one.high.to_numpy(float);lo=one.low.to_numpy(float)
    op5=c.open.to_numpy(float);hi5=c.high.to_numpy(float);lo5=c.low.to_numpy(float);cl5=c.close.to_numpy(float)
    sm=session_masks(c.index); settle=np.asarray((one.index.hour%8==0)&(one.index.minute==0),int);prefix=np.r_[0,np.cumsum(settle)]
    rec=[];audit=[]
    # One 5m index i corresponds to 1m index 5*i through 5*i+4, completed at 5*(i+1).
    for side,trend,look,qual,entry_style,exit_style,session in itertools.product(SIDES,TRENDS,LOOKBACKS,QUALS,ENTRIES,EXITS,SESSIONS):
        level=levels[(look,side)]
        previous=np.r_[np.nan,cl5[:-1]]
        body_ok=np.abs(cl5-op5)>=.5*np.maximum(hi5-lo5,.00001)
        is_bull=(cl5>op5) if side==1 else (cl5<op5)
        crossing=(cl5>level)&(previous<=level) if side==1 else (cl5<level)&(previous>=level)
        signal=hour[(trend,side)]&crossing&body_ok&is_bull&np.isfinite(atr)
        if qual=="compression_volume":signal &=qualified
        candidate=np.flatnonzero(signal)
        last_exit=-1;excluded_session=excluded_calendar=excluded_overlap=excluded_retest=0
        for i in candidate:
            if i>=five-55:continue
            entry5=i+1
            boundary=level[i]
            if entry_style=="retest":
                found=False
                for j in range(i+1,min(i+4,five-1)):
                    tol=.2*atr[i]
                    # Confirm completed retest candle j; fill at OPEN j+1.
                    match=(lo5[j]<=boundary+tol and cl5[j]>boundary) if side==1 else (hi5[j]>=boundary-tol and cl5[j]<boundary)
                    if match:
                        entry5=j+1;found=True;break
                if not found:
                    excluded_retest+=1;continue
            if not sm[session][entry5]:
                excluded_session+=1;continue
            entry_min=entry5*5
            if entry_min<=last_exit:excluded_overlap+=1;continue
            max_end=entry_min+240
            if max_end>=n:continue
            if prefix[max_end+1]-prefix[entry_min]:
                excluded_calendar+=1;continue
            stop_dist=float(np.clip(atr[i]*1.2,180,450))
            price_in=op[entry_min]+side*SLIP
            stop=price_in-side*stop_dist
            target=price_in+side*(3 if exit_style=="fixed_3r" else 5)*stop_dist
            trail=stop
            hit=max_end;out_mid=op[max_end];reason="timeout"
            mfe=0.;mae=0.
            for j in range(entry_min,max_end):
                # Conservative: process stops before targets; tightening only after whole prior minute closes.
                max_fav=(hi[j]-price_in) if side==1 else (price_in-lo[j])
                max_adv=(price_in-lo[j]) if side==1 else (hi[j]-price_in)
                mfe=max(mfe,max_fav);mae=max(mae,max_adv)
                gap_stop=(op[j]<=trail) if side==1 else (op[j]>=trail)
                touch_stop=(lo[j]<=trail) if side==1 else (hi[j]>=trail)
                touch_target=(hi[j]>=target) if side==1 else (lo[j]<=target)
                if gap_stop:hit=j;out_mid=op[j];reason="stop_gap";break
                if touch_stop:hit=j;out_mid=trail;reason="stop";break
                if touch_target:hit=j;out_mid=target;reason="target";break
                if exit_style=="trail_5r":
                    # Moves stop only for *future minute* after current minute trade-prices demonstrated favorable excursion.
                    if mfe>=3*stop_dist:trail=price_in+side*1.5*stop_dist
                    elif mfe>=2*stop_dist:trail=price_in
            price_out=out_mid-side*SLIP
            gross=side*(out_mid-op[entry_min])
            net=side*(price_out-price_in)-FEE*(price_in+price_out)
            last_exit=hit
            when=one.index[entry_min]
            period="train" if when.year==2025 else ("validation" if when<pd.Timestamp("2026-07-01",tz="UTC") else "recheck_seen")
            rec.append(dict(side="LONG" if side==1 else "SHORT",trend=trend,range_bars=look,qualifier=qual,entry_mode=entry_style,
                exit_mode=exit_style,session=session,period=period,entry_utc=str(when),exit_utc=str(one.index[hit]),
                entry_price=round(price_in,4),exit_price=round(price_out,4),
                stop_distance_pts=round(stop_dist,4),reason=reason,minutes_held=hit-entry_min,
                mfe_pts=round(mfe,2),mae_pts=round(mae,2),
                gross_pts=round(gross,4),net_pts=round(net,4),cost_pts=round(gross-net,4)))
        audit.append(dict(side="LONG" if side==1 else "SHORT",trend=trend,range_bars=look,qualifier=qual,
             entry_mode=entry_style,exit_mode=exit_style,session=session,initial_breakout_signals=len(candidate),
             excluded_no_retest=excluded_retest,excluded_session=excluded_session,
             excluded_overlap=excluded_overlap,excluded_funding_calendar=excluded_calendar))
    return pd.DataFrame(rec),pd.DataFrame(audit)
def summary(tr):
    records=[]
    for side,trend,look,qual,entry,exit_style,session,period in itertools.product(("LONG","SHORT"),TRENDS,LOOKBACKS,QUALS,ENTRIES,EXITS,SESSIONS,PERIODS):
        if len(tr):
            d=tr[(tr.side==side)&(tr.trend==trend)&(tr.range_bars==look)&(tr.qualifier==qual)&
                 (tr.entry_mode==entry)&(tr.exit_mode==exit_style)&(tr.session==session)&(tr.period==period)]
        else:d=pd.DataFrame()
        v=d.net_pts.to_numpy(float) if len(d) else np.array([])
        if len(v):
            cum=np.r_[0,v.cumsum()];wins=v[v>0].sum();loss=-v[v<0].sum()
            stats=dict(trades=len(v),net_mean_pts=round(float(v.mean()),3),
                gross_mean_pts=round(float(d.gross_pts.mean()),3),
                cost_mean_pts=round(float(d.cost_pts.mean()),3),
                win_pct=round(float(100*(v>0).mean()),2),
                profit_factor=round(float(wins/loss),3) if loss else None,
                max_drawdown_pts=round(float((np.maximum.accumulate(cum)-cum).max()),2),
                median_duration_min=round(float(d.minutes_held.median()),1),
                average_mfe_pts=round(float(d.mfe_pts.mean()),1),
                average_mae_pts=round(float(d.mae_pts.mean()),1),
                distinct_utc_days=d.entry_utc.str[:10].nunique())
        else:
            stats=dict(trades=0,net_mean_pts=None,gross_mean_pts=None,cost_mean_pts=None,
                win_pct=None,profit_factor=None,max_drawdown_pts=None,median_duration_min=None,
                average_mfe_pts=None,average_mae_pts=None,distinct_utc_days=0)
        records.append(dict(side=side,trend=trend,range_bars=look,qualifier=qual,entry_mode=entry,
            exit_mode=exit_style,session=session,period=period,**stats))
    return pd.DataFrame(records)
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f=load()
    five,hour,atr,qualified,levels=features(f)
    t,a=run(f,five,hour,atr,qualified,levels)
    summ=summary(t)
    summ.to_csv(OUT/"all_scenarios.csv",index=False)
    a.to_csv(OUT/"signal_exclusions.csv",index=False)
    t.to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    quality=dict(minute_rows=len(f),five_minute_rows=len(five),first=str(f.index[0]),
        last=str(f.index[-1]),configurations_per_period=128,configuration_period_rows=len(summ),
        scenario_trade_records=len(t),data_source="Original Delta India BTCUSD 1m OHLCV archive",
        roundtrip_futures_taker_rate_including_gst=FEE*2,slippage_each_side=SLIP,
        max_exposure_minutes=240,broker_l1_not_available=True,prior_recheck_already_seen=True)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    eligible=summ[(summ.period=="validation")&(summ.trades>=20)].sort_values("net_mean_pts",ascending=False)
    lines=["# Big-trend research: 1h confirmed structure + 5m breakout/retest, 1m conservative fills","",
        "Exploratory, NOT independently OOS, no fabricated executable order book.",json.dumps(quality,indent=2),"",
        "## Chronological validation ranked, >=20 trades",eligible.head(30).to_markdown(index=False),"",
        "## All results, including zero trades",summ.to_markdown(index=False),"",
        "## Exclusions by setup",a.to_markdown(index=False),"",
        "## Limitations",
        "1h features are based on prior completed candles; 5m breakout signals use only completed 5m bars; retests wait up to 3 completed 5m candles; all fills model next 1m OPEN.",
        "Funding-calendar avoidance, not realistic funding payment accounting. No market L1 fills or margin stress.",
        "Trailing stop changes become active no earlier than next completed minute, not the same candle that established MFE.",
        "Tests are correlated and 2026 Jul-Oct is previously seen; any positive subgroup is only an exploratory lead."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("BIG_TREND_FINISHED",json.dumps(quality),flush=True)
    print("VALIDATION_TOP",eligible.head(15).to_string(index=False),flush=True)
if __name__=="__main__":main()
