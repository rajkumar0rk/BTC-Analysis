#!/usr/bin/env python3
"""BTCUSD 15m compression -> 5m momentum breakout, 1m trade execution.

Reproducible 2025 selection / 2026 historical recheck. At most one trade per IST
weekday; 100% equity notional (1x); zero-trade weekdays count as failing +0.2%.
Fees: taker 0.05% per side +18% GST, 5 pts adverse slippage EACH side.
Scalper sensitivity assumes user pre-opted into 30-minute closing-fee waiver.
"""
from pathlib import Path
from itertools import product
import json
import numpy as np
import pandas as pd

SRC=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/btc_15m_compression_5m_momentum_daily")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
START="2025-01-02"
END="2026-10-30"
FEE=0.0005*1.18
SLIP=5.0
HOLD=240
COMP=((4,1.9),(8,2.8))
VOLS=(1.10,1.35)
TRENDS=("ema20_50","ema9_21")
STOPS=(1.25,1.75)
TARGETS=(2.0,3.0)
DAY_INDEX=pd.date_range(START,END,freq="B")
DAYS=np.asarray(DAY_INDEX.strftime("%Y-%m-%d"))
DAY_MAP={x:i for i,x in enumerate(DAYS)}
DAYS2025=sum(x[:4]=="2025" for x in DAYS)
N_BARS=5

def load():
    chunks=[]
    for mon in MONTHS+["2026-11"]:
        path=SRC/(mon+".csv.gz")
        if not path.exists():raise FileNotFoundError(path)
        d=pd.read_csv(path,compression="gzip",usecols=["time","open","high","low","close","volume"])
        d["time"]=pd.to_datetime(d.time.astype("int64"),unit="s",utc=True)
        chunks.append(d)
    m=pd.concat(chunks,ignore_index=True).set_index("time").sort_index()
    if m.index.has_duplicates or m.isna().any().any():raise ValueError("Duplicate/null candles")
    if not m.index.to_series().diff().iloc[1:].eq(pd.Timedelta(minutes=1)).all():
        raise ValueError("Missing original 1m candles")
    if (m.high<m[["open","low","close"]].max(axis=1)).any() or (m.low>m[["open","high","close"]].min(axis=1)).any():
        raise ValueError("Invalid OHLC")
    if (m.volume<0).any() or (m.close<=0).any():raise ValueError("Invalid volume or price")
    assert m.index[0]==pd.Timestamp("2025-01-01T00:00:00Z")
    assert m.index[-1]>=pd.Timestamp("2026-11-01T00:00:00Z")
    return m

def ema(s,n):
    return s.ewm(span=n,adjust=False,min_periods=n).mean()

def rma(s,n):
    return s.ewm(alpha=1/n,adjust=False,min_periods=n).mean()

def aggregate(m,n):
    rule=f"{n}min" if n<60 else "1h"
    d=m[["open","high","low","close","volume"]].resample(rule,label="right",closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    count=m.close.resample(rule,label="right",closed="left").count()
    assert count.min()==n,(rule,"non-full bar")
    return d

def atr(d):
    prev=d.close.shift(1)
    tr=pd.concat((d.high-d.low,(d.high-prev).abs(),(d.low-prev).abs()),axis=1).max(axis=1)
    return rma(tr,14)

def features(m):
    a5=aggregate(m,5)
    a15=aggregate(m,15)
    a1=aggregate(m,60)
    atr5=atr(a5)
    atr15=atr(a15)
    local=a5.index.tz_convert("Asia/Kolkata")
    sigdays=np.asarray(local.strftime("%Y-%m-%d"))
    mins=np.asarray(local.hour*60+local.minute)
    weekdays=np.asarray(local.weekday<5)
    validtime=(weekdays&(sigdays>=START)&(sigdays<=END)&
               (mins>=9*60)&(mins<19*60))
    entryi=m.index.get_indexer(a5.index)  # end of 5m bar == next 1m open
    validtime &= entryi>=0
    # The range boundary at 10:15 excludes the just-completed 10:00-10:15
    # 15m candle: last eligible 15m window ends 10:00.
    t15=(a5.index-pd.Timedelta(nanoseconds=1)).floor("15min")
    t1=(a5.index-pd.Timedelta(nanoseconds=1)).floor("1h")
    hist15={}
    for n,limit in COMP:
        q=pd.DataFrame({"upper":a15.high.rolling(n,min_periods=n).max(),
                        "lower":a15.low.rolling(n,min_periods=n).min(),
                        "atr15":atr15},index=a15.index).reindex(t15)
        hist15[n]={"upper":q.upper.to_numpy(float),"lower":q.lower.to_numpy(float),
                   "valid":((q.upper-q.lower)<=limit*q.atr15).fillna(False).to_numpy(bool)}
    h1=pd.DataFrame(index=a1.index)
    h1["ema20"]=ema(a1.close,20);h1["ema50"]=ema(a1.close,50)
    h1["ema9"]=ema(a1.close,9);h1["ema21"]=ema(a1.close,21)
    h1["close"]=a1.close
    hourly=h1.reindex(t1)
    regimes={
       "ema20_50":((hourly.close>hourly.ema20)&(hourly.ema20>hourly.ema50),
                   (hourly.close<hourly.ema20)&(hourly.ema20<hourly.ema50)),
       "ema9_21":((hourly.close>hourly.ema9)&(hourly.ema9>hourly.ema21),
                  (hourly.close<hourly.ema9)&(hourly.ema9<hourly.ema21)),
    }
    regimes={k:(x.fillna(False).to_numpy(bool),y.fillna(False).to_numpy(bool))
             for k,(x,y) in regimes.items()}
    candle_range=(a5.high-a5.low).replace(0,np.nan)
    body=((a5.close-a5.open).abs()/candle_range).fillna(0).to_numpy(float)
    position=((a5.close-a5.low)/candle_range).fillna(0.5).to_numpy(float)
    bullish=(a5.close>a5.open).to_numpy(bool)&(body>=0.6)&(position>=0.8)
    bearish=(a5.close<a5.open).to_numpy(bool)&(body>=0.6)&(position<=0.2)
    strong=(candle_range>=0.7*atr5).fillna(False).to_numpy(bool)
    vratio=(a5.volume/a5.volume.shift(1).rolling(20,min_periods=20).mean().replace(0,np.nan)).to_numpy(float)
    q={"a5":a5,"atr5":atr5.to_numpy(float),"validtime":validtime,
       "entryi":entryi,"sigdays":sigdays,"bull":bullish,"bear":bearish,"strong":strong,
       "vratio":vratio,"last5close":a5.close.shift(1).to_numpy(float),
       "close5":a5.close.to_numpy(float),"hist15":hist15,"regimes":regimes}
    return q

def event_candidates(q,n,vol,trend,mult,rr):
    h=q["hist15"][n]
    a,b=q["regimes"][trend]
    close=q["close5"];prior=q["last5close"]
    upper=h["upper"];lower=h["lower"]
    shared=q["validtime"]&h["valid"]&q["strong"]& (q["vratio"]>=vol)&np.isfinite(q["atr5"])
    # Predict required gross target from already closed breakout candle and ATR.
    # No access to the next minute's open until AFTER signal choice.
    roughfill=close
    risk=mult*q["atr5"]
    predicted_net=(rr*risk-2*SLIP-FEE*(2*roughfill+rr*risk))/roughfill
    shared &= predicted_net>=0.002
    longs=shared&a&q["bull"]&(close>upper)&(prior<=upper)
    shorts=shared&b&q["bear"]&(close<lower)&(prior>=lower)
    candidates=np.flatnonzero(longs|shorts)
    return candidates,longs,shorts

def sim(m,q,n,vol,trend,mult,rr):
    events,longs,shorts=event_candidates(q,n,vol,trend,mult,rr)
    op=m.open.to_numpy(float);hi=m.high.to_numpy(float)
    lo=m.low.to_numpy(float);cl=m.close.to_numpy(float)
    indices=m.index
    out=[];used=set()
    last_exit=-1
    for k in events:
        day=q["sigdays"][k]
        if day in used:continue
        entryi=int(q["entryi"][k])
        if entryi<=last_exit:continue
        if day not in DAY_MAP:raise AssertionError("Invalid day")
        assert pd.Timestamp(day).weekday()<5
        direction=1 if longs[k] else -1
        midin=float(op[entryi])
        fillin=midin+direction*SLIP
        risk=mult*float(q["atr5"][k])
        if risk<=0 or not np.isfinite(risk):continue
        stop=fillin-direction*risk
        tp=fillin+direction*rr*risk
        if entryi+HOLD>=len(m):continue
        used.add(day)
        reason="timeout"
        j=entryi
        for j in range(entryi,entryi+HOLD):
            stophit=(lo[j]<=stop if direction==1 else hi[j]>=stop)
            targethit=(hi[j]>=tp if direction==1 else lo[j]<=tp)
            if stophit:
                midout=min(float(op[j]),stop) if direction==1 else max(float(op[j]),stop)
                reason="stop"
                break
            if targethit:
                midout=tp
                reason="target"
                break
        else:
            j=entryi+HOLD
            midout=float(op[j])
        fillout=midout-direction*SLIP
        elapsed=float((indices[j]-indices[entryi]).total_seconds()/60)
        eligible=elapsed<=30
        feein=FEE*fillin
        feeout=FEE*fillout
        gross=direction*(midout-midin)
        slippage=2*SLIP
        standard=gross-slippage-feein-feeout
        offer=standard+(feeout if eligible else 0.)
        exitday=str(indices[j].tz_convert("Asia/Kolkata").date())
        if exitday!=day:
            raise AssertionError(f"Trade from {day} exited on {exitday}, daily attribution invalid")
        last_exit=j
        out.append(dict(signal_utc=str(q["a5"].index[k]),
                        entry_utc=str(indices[entryi]),exit_utc=str(indices[j]),
                        day_ist=day,month_ist=day[:7],side="LONG" if direction==1 else "SHORT",
                        exit_reason=reason,entry_mid=round(midin,5),
                        entry_fill=round(fillin,5),exit_fill=round(fillout,5),
                        risk_points=round(risk,5),gross_points=round(gross,5),
                        slippage_points=slippage,open_fee_gst_points=round(feein,5),
                        close_fee_gst_points=round(feeout,5),
                        scalper_eligible=bool(eligible),hold_minutes=elapsed,
                        standard_net_points=round(standard,5),
                        offer_net_points=round(offer,5),
                        standard_return=standard/fillin,
                        offer_return=offer/fillin))
    return pd.DataFrame.from_records(out,columns=[
        "signal_utc","entry_utc","exit_utc","day_ist","month_ist","side","exit_reason",
        "entry_mid","entry_fill","exit_fill","risk_points","gross_points","slippage_points",
        "open_fee_gst_points","close_fee_gst_points","scalper_eligible","hold_minutes",
        "standard_net_points","offer_net_points","standard_return","offer_return"])

def score(ledger,mode):
    retcol="offer_return" if mode=="offer" else "standard_return"
    netcol="offer_net_points" if mode=="offer" else "standard_net_points"
    daily=pd.DataFrame({"day_ist":DAYS,"net_account_pct":np.zeros(len(DAYS))})
    if len(ledger):
        assert ledger.day_ist.nunique()==len(ledger)
        daily.loc[[DAY_MAP[x] for x in ledger.day_ist], "net_account_pct"]=ledger[retcol].to_numpy(float)*100
    daily["year"]=daily.day_ist.str[:4]
    daily["month_ist"]=daily.day_ist.str[:7]
    daily["status"]=np.where(daily.net_account_pct>=0.2-1e-9,"GOAL",
                        np.where(daily.net_account_pct>0,"SMALL_GAIN",
                        np.where(daily.net_account_pct<0,"LOSS","NO_TRADE")))
    # Compounding over net account changes; unleveraged 100% notional equity.
    equity=np.cumprod(1+daily.net_account_pct.to_numpy(float)/100)
    peak=np.maximum.accumulate(np.r_[1,equity])[1:]
    dd=np.max((1-equity/peak)*100) if len(equity) else 0.
    monthly=(daily.assign(factor=1+daily.net_account_pct/100).
                groupby("month_ist",sort=True).agg(
                 trades=("net_account_pct",lambda s:int((s!=0).sum())),
                 goal_days=("status",lambda s:int((s=="GOAL").sum())),
                 losing_days=("status",lambda s:int((s=="LOSS").sum())),
                 factor=("factor","prod")))
    monthly["net_account_pct"]=(monthly.factor-1)*100
    monthly=monthly.reset_index().drop(columns="factor")
    assert monthly.month_ist.tolist()==MONTHS
    n=len(ledger)
    wins=int((ledger[netcol]>0).sum()) if n else 0
    losses=int((ledger[netcol]<0).sum()) if n else 0
    gains=float(ledger.loc[ledger[netcol]>0,netcol].sum()) if n else 0.
    losspts=float(-ledger.loc[ledger[netcol]<0,netcol].sum()) if n else 0.
    e25=np.prod(1+daily.loc[daily.year=="2025","net_account_pct"].to_numpy()/100)
    e26=np.prod(1+daily.loc[daily.year=="2026","net_account_pct"].to_numpy()/100)
    goal2025=int(((daily.year=="2025")&(daily.status=="GOAL")).sum())
    goal2026=int(((daily.year=="2026")&(daily.status=="GOAL")).sum())
    summary=dict(
       cost_model=mode,eligible_weekdays=len(DAYS),trades=n,
       winning_trades=wins,losing_trades=losses,
       win_rate_pct=round(100*wins/n,3) if n else 0,
       trade_days_pct=round(100*n/len(DAYS),3),
       goal_0p2_days=goal2025+goal2026,
       goal_0p2_days_2025=goal2025,goal_0p2_days_2026=goal2026,
       goal_0p2_days_pct=round(100*(goal2025+goal2026)/len(DAYS),3),
       profitable_but_below_goal_days=int((daily.status=="SMALL_GAIN").sum()),
       losing_days=int((daily.status=="LOSS").sum()),
       no_trade_days=int((daily.status=="NO_TRADE").sum()),
       worst_daily_pct=round(float(daily.net_account_pct.min()),5),
       max_closed_dd_pct=round(float(dd),5),
       return_2025_pct=round(100*(e25-1),5),
       return_2026_pct=round(100*(e26-1),5),
       net_return_pct=round(100*(equity[-1]-1),5) if len(equity) else 0.,
       winning_months=int((monthly.net_account_pct>0).sum()),
       losing_months=int((monthly.net_account_pct<0).sum()),
       flat_months=int((monthly.net_account_pct==0).sum()),
       profit_factor=round(gains/losspts,4) if losspts else None,
       gross_points=round(float(ledger.gross_points.sum()),2) if n else 0.,
       net_points=round(float(ledger[netcol].sum()),2) if n else 0.,
       total_slippage_points=round(float(ledger.slippage_points.sum()),2) if n else 0.,
       total_open_fees_gst_points=round(float(ledger.open_fee_gst_points.sum()),2) if n else 0.,
       total_close_fees_gst_points=round(float(ledger.close_fee_gst_points.sum()*(1.0)) if mode=="standard" else float(ledger.loc[~ledger.scalper_eligible,"close_fee_gst_points"].sum()),2) if n else 0.,
       scalper_eligible_trades=int(ledger.scalper_eligible.sum()) if n else 0,
       max_hold_minutes=HOLD
    )
    return summary,monthly,daily

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=load()
    q=features(m)
    variants=[];monthly_tables=[];candidate_data={}
    for (n,ratio),vol,trend,mult,rr in product(COMP,VOLS,TRENDS,STOPS,TARGETS):
        name=f"c{n}x{ratio:g}_v{vol:g}_{trend}_stop{mult:g}_rr{rr:g}"
        ledger=sim(m,q,n,vol,trend,mult,rr)
        if len(ledger) and (ledger.day_ist.nunique()!=len(ledger)):
            raise AssertionError("Not one entry per weekday")
        candidate_data[name]=ledger
        for mode in ("standard","offer"):
            stat,monthly,daily=score(ledger,mode)
            stat.update(variant=name,compress_bars=n,compress_atr_limit=ratio,
                        vol_ratio_min=vol,hourly_trend=trend,stop_atr5=mult,reward_rr=rr)
            variants.append(stat)
            monthly["variant"]=name
            monthly["cost_model"]=mode
            monthly_tables.append(monthly)
            print("VARIANT "+json.dumps(stat,sort_keys=True),flush=True)
    allv=pd.DataFrame(variants)
    allmonths=pd.concat(monthly_tables,ignore_index=True)
    allv.to_csv(OUT/"all_variants.csv",index=False)
    allmonths.to_csv(OUT/"all_months.csv",index=False)
    selected={}
    for mode in ("standard","offer"):
        z=allv[allv.cost_model==mode].copy()
        positive=z[z.return_2025_pct>0].copy()
        valid=len(positive)>0
        if valid:
            ranked=positive.sort_values(["goal_0p2_days_2025","return_2025_pct","max_closed_dd_pct"],
                                         ascending=[False,False,True])
        else:
            ranked=z.sort_values(["return_2025_pct","goal_0p2_days_2025","max_closed_dd_pct"],
                                  ascending=[False,False,True])
        winner=ranked.iloc[0].to_dict()
        selected[mode]=dict(selected_using_2025=winner,had_positive_2025_candidate=bool(valid))
        name=winner["variant"]
        ledger=candidate_data[name]
        summary,monthly,daily=score(ledger,mode)
        ledger.to_csv(OUT/(f"{mode}_selected_trades.csv.gz"),index=False,compression="gzip")
        daily.to_csv(OUT/(f"{mode}_selected_daily.csv"),index=False)
        monthly.to_csv(OUT/(f"{mode}_selected_monthly.csv"),index=False)
        print("SELECTED_"+mode.upper()+" "+json.dumps(selected[mode],sort_keys=True),flush=True)
        print("SELECTED_"+mode.upper()+"_MONTHS\n"+monthly.to_string(index=False),flush=True)
        hindsight=z.sort_values("net_return_pct",ascending=False).iloc[0].to_dict()
        selected[mode]["full_sample_hindsight_best_not_selected"]=hindsight
        print("HINDSIGHT_"+mode.upper()+" "+json.dumps(hindsight,sort_keys=True),flush=True)

    (OUT/"summary.json").write_text(json.dumps(dict(
       summary=selected,source="Delta India BTCUSD 1min OHLCV continuous",
       evaluated_dates=f"{START}..{END}",calendar_timezone="Asia/Kolkata",
       trade_limit="maximum one weekday entry 09:00–19:00 IST",
       account_exposure="1x 100% account notional, no leverage",
       daily_goal="+0.2% net account profit for every weekday, including zero-trade days",
       fee_model="taker 0.05% each side, 18% GST, 5 BTC price points adverse slippage each side",
       offer_model="conditional zero closing fee for <=30m position; historical eligibility is counterfactual",
       limitations=["No historical funding payments","No order book/spread/market impact",
                    "30m eligibility based on 1m candle timestamps, not fill seconds",
                    "2026 historically examined; not pristine unseen data","Partial 2025-01-01 IST excluded"]),indent=2)+"\n")
    report=["# BTCUSD: 15m compression / 5m breakout / 1m execution",
            "","**Daily target:** >=+0.2% NET ACCOUNT on each available IST weekday (1x notional). A no-trade day counts as 0% and FAILS target.",
            "",f"**Dataset:** 2025-01 through 2026-10, {len(DAYS)} complete eligible weekdays ({START} to {END}). November tail only. Max one entry per weekday.",
            "**Cost:** 0.05% taker/side+18% GST+5 points/side adverse slippage. Offer counterfactual waives closing fee only when <=30 minutes and assumed opted in.",
            "**Selection:** Positive 2025 account performance required, then most +0.2% weekdays in 2025, tie 2025 return/lower DD. If no positive 2025 candidate, choose least negative for diagnosis, NOT endorsement. 2026 is researched historical check.",
            "","## 2025-selected standard fees",json.dumps(selected["standard"],indent=2),
            "","## 2025-selected Scalper Offer counterfactual",json.dumps(selected["offer"],indent=2)]
    for mode in ("standard","offer"):
        name=selected[mode]["selected_using_2025"]["variant"]
        report+=["",f"## {mode}: full IST monthly table — {name}","",
            pd.read_csv(OUT/f"{mode}_selected_monthly.csv").to_markdown(index=False)]
    report+=["","## All configurations after fees","",allv.sort_values(["cost_model","return_2025_pct"],ascending=[True,False]).to_markdown(index=False),
             "","**Limitations:** Not a guaranteed daily-profit strategy; no actual funding, order book, margin or liquidation modeling. 2026 prior exposure makes it an imperfect historical check."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("BTC_COMP_MOMENTUM_DAILY_COMPLETED",flush=True)

if __name__=="__main__":run()
