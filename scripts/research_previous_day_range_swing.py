#!/usr/bin/env python3
"""Pre-registered UTC prior-day range and confirmed earlier daily swing BTCUSD research."""
import itertools,json
from pathlib import Path
import numpy as np,pandas as pd
DATA=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/previous_day_range_swing")
FEE=.0005*1.18
SLIP=5.
PAIRS=((100,200),(200,400),(300,600),(400,800),(300,900),(400,1200))
TF=(1,5,15)
SESSIONS=("ALL_UTC","NY_OPEN","LONDON_OPEN","INDIA_MORNING")
SETUPS=("range_break","range_sweep","swing_break","swing_sweep")
def load():
    aa=[]
    for p in sorted(DATA.glob("20??-??.csv.gz")):
        z=pd.read_csv(p,compression="gzip",usecols=["time","open","high","low","close"])
        z.index=pd.to_datetime(z.pop("time").astype("int64"),unit="s",utc=True);aa.append(z)
    if not aa:raise RuntimeError("No underlying Delta 1m candles")
    f=pd.concat(aa).sort_index()
    if f.index.has_duplicates or f.isna().any().any() or not f.index.to_series().diff().iloc[1:].eq(pd.Timedelta(minutes=1)).all():
        raise ValueError("Invalid Delta 1m data")
    return f
def masks(idx):
    def m(tz,start,end):
        x=idx.tz_convert(tz);minute=x.hour*60+x.minute
        return np.asarray((x.dayofweek<5)&(minute>=start)&(minute<end))
    return {"ALL_UTC":np.ones(len(idx),dtype=bool),"NY_OPEN":m("America/New_York",570,720),
       "LONDON_OPEN":m("Europe/London",480,660),"INDIA_MORNING":m("Asia/Kolkata",540,720)}
def daily_levels(f):
    d=f.resample("1D",label="left",closed="left").agg({"high":"max","low":"min"})
    # center d-3 confirmed by end d-1 (2 full right-side days).
    # for date D, only pivots centered no later than D-3 (strictly before yesterday)
    hi=d.high.shift(2);lo=d.low.shift(2)
    center_hi=d.high.shift(3);center_lo=d.low.shift(3)
    is_hi=(center_hi==d.high.shift(1).rolling(5,min_periods=5).max())
    is_lo=(center_lo==d.low.shift(1).rolling(5,min_periods=5).min())
    # At opening of D, rolling window d-5..d-1 represents center d-3. Thus no future use.
    sh=center_hi.where(is_hi).ffill()
    sl=center_lo.where(is_lo).ffill()
    # CORRECTION: rolling window indexed D-1 contains days D-5..D-1
    return pd.DataFrame({"RH":d.high.shift(1),"RL":d.low.shift(1),"SH":sh,"SL":sl},index=d.index)
def run(f):
    op=f.open.to_numpy(float);hi=f.high.to_numpy(float);lo=f.low.to_numpy(float)
    n=len(f)
    lev=daily_levels(f)
    settle=np.asarray((f.index.hour%8==0)&(f.index.minute==0),int)
    cs=np.r_[0,np.cumsum(settle)]
    trades=[];checks=[]
    for tf in TF:
        t=f.resample(f"{tf}min",label="left",closed="left").agg({"open":"first","high":"max","low":"min","close":"last"})
        if not (f.close.resample(f"{tf}min").count()==tf).all():raise ValueError("Partial intraday candle")
        k=len(t)
        lk=lev.reindex(t.index,method="ffill")
        t_op=t.open.to_numpy(float);t_hi=t.high.to_numpy(float);t_lo=t.low.to_numpy(float);t_cl=t.close.to_numpy(float)
        past=np.r_[np.nan,t_cl[:-1]]
        ss=masks(t.index)
        for side,setup in itertools.product((1,-1),SETUPS):
            if setup.startswith("range"):
                col="RH" if side==1 else "RL"
                if setup=="range_sweep":col="RL" if side==1 else "RH"
            else:
                col="SH" if side==1 else "SL"
                if setup=="swing_sweep":col="SL" if side==1 else "SH"
            lv=lk[col].to_numpy(float)
            if setup.endswith("break"):
                sig=(t_cl>lv)&(past<=lv) if side==1 else (t_cl<lv)&(past>=lv)
            else:
                sig=((t_lo<lv)&(t_cl>lv)&(t_cl>t_op)) if side==1 else ((t_hi>lv)&(t_cl<lv)&(t_cl<t_op))
            candidates=np.flatnonzero(sig&np.isfinite(lv))
            for sess,pair,hold in itertools.product(SESSIONS,PAIRS,(120,240)):
                mask=ss[sess];last=-1;ignored_calendar=0;ignored_session=0;ignored_overlap=0
                for j in candidates:
                    entry=(j+1)*tf
                    if entry+hold>=n:continue
                    if not mask[j+1]:ignored_session+=1;continue
                    if entry<=last:ignored_overlap+=1;continue
                    if cs[entry+hold+1]-cs[entry]>0:ignored_calendar+=1;continue
                    sl,tp=pair
                    fill=op[entry]+side*SLIP;stop=fill-side*sl;target=fill+side*tp
                    ex=entry+hold;mid=op[ex];why="timeout"
                    for z in range(entry,entry+hold):
                        gap=op[z]<=stop if side==1 else op[z]>=stop
                        hit_sl=lo[z]<=stop if side==1 else hi[z]>=stop
                        hit_tp=hi[z]>=target if side==1 else lo[z]<=target
                        if gap:ex=z;mid=op[z];why="stop_gap";break
                        if hit_sl:ex=z;mid=stop;why="stop";break
                        if hit_tp:ex=z;mid=target;why="target";break
                    out=mid-side*SLIP
                    gross=side*(mid-op[entry]);net=side*(out-fill)-FEE*(fill+out)
                    last=ex
                    dt=f.index[entry]
                    period="train" if dt.year==2025 else ("validation" if dt<pd.Timestamp("2026-07-01",tz="UTC") else "recheck_seen")
                    trades.append(dict(side="LONG" if side==1 else "SHORT",setup=setup,tf=tf,session=sess,sl=sl,tp=tp,hold=hold,period=period,
                        entry_utc=str(dt),exit_utc=str(f.index[ex]),level=round(lv[j],2),entry=round(fill,2),exit=round(out,2),exit_reason=why,
                        duration_min=ex-entry,gross_pts=round(gross,3),net_pts=round(net,3),cost_pts=round(gross-net,3)))
                checks.append(dict(side="LONG" if side==1 else "SHORT",setup=setup,tf=tf,session=sess,sl=sl,tp=tp,hold=hold,
                    candidates=len(candidates),skip_session=ignored_session,skip_overlap=ignored_overlap,skip_funding=ignored_calendar))
    return pd.DataFrame(trades),pd.DataFrame(checks),lev
def summarize(tr):
    rows=[]
    for side,setup,tf,session,(sl,tp),hold,period in itertools.product(("LONG","SHORT"),SETUPS,TF,SESSIONS,PAIRS,(120,240),("train","validation","recheck_seen")):
        x=tr[(tr.side==side)&(tr.setup==setup)&(tr.tf==tf)&(tr.session==session)&(tr.sl==sl)&(tr.tp==tp)&(tr.hold==hold)&(tr.period==period)]
        v=x.net_pts.to_numpy(float)
        if len(v):
            cum=np.r_[0,v.cumsum()];win=v[v>0].sum();loss=-v[v<0].sum()
            metrics=dict(trades=len(v),net_mean_pts=round(float(v.mean()),2),gross_mean_pts=round(float(x.gross_pts.mean()),2),
                mean_cost_pts=round(float(x.cost_pts.mean()),2),win_pct=round(100*float((v>0).mean()),2),
                profit_factor=round(float(win/loss),3) if loss else None,
                max_drawdown_pts=round(float((np.maximum.accumulate(cum)-cum).max()),2),
                unique_days=x.entry_utc.str[:10].nunique(),median_duration_min=round(float(x.duration_min.median()),1))
        else:metrics=dict(trades=0,net_mean_pts=None,gross_mean_pts=None,mean_cost_pts=None,win_pct=None,
                profit_factor=None,max_drawdown_pts=None,unique_days=0,median_duration_min=None)
        rows.append(dict(side=side,setup=setup,tf=tf,session=session,sl=sl,tp=tp,hold=hold,period=period,**metrics))
    return pd.DataFrame(rows)
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f=load()
    t,c,l=run(f)
    if t.empty:raise RuntimeError("No trades")
    s=summarize(t)
    s.to_csv(OUT/"all_scenarios.csv",index=False)
    c.to_csv(OUT/"signal_exclusions.csv",index=False)
    t.to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    q=dict(one_minute_rows=len(f),first_utc=str(f.index[0]),last_utc=str(f.index[-1]),
       daily_bars=len(l),scenarios=len(s),scenario_trade_records=len(t),
       nominal_roundtrip_fee_rate_including_gst=2*FEE,adverse_slippage_points_each_side=SLIP,
       swing_center_two_left_two_right=True,day_boundary="UTC",
       l1_bid_ask_unavailable=True,seen_recheck_not_independent=True)
    (OUT/"quality.json").write_text(json.dumps(q,indent=2)+"\n")
    v=s[(s.period=="validation")&(s.trades>=25)].sort_values("net_mean_pts",ascending=False)
    summary=["# UTC previous-day range + confirmed older daily swing: BTCUSD study","","## Data and cost assumptions",
      json.dumps(q,indent=2),"","## Validation configurations with at least 25 trades (top 50)",
      v.head(50).to_markdown(index=False),"","## All scenario summaries",
      s.to_markdown(index=False),"","## Limitations","No L1 spread or funding-cashflow archive; taker/slippage model is approximate.",
      "Pivot levels use only two closed following daily bars; no lookahead. Multiple configurations overlap.",
      "Jul-Oct 2026 was previously inspected; it is not a pristine independent holdout.",
      "Past performance does not establish live executability or daily profits."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(summary)+"\n")
    print("PREV_DAY_SWING_RANGE_COMPLETED",json.dumps(q),flush=True)
    print("VALIDATION_TOP",v.head(15).to_string(index=False),flush=True)
if __name__=="__main__":main()
