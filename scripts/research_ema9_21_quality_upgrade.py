#!/usr/bin/env python3
"""Pre-registered differential: quality entries + 5m ATR exit for BTCUSD 1m EMA9/21.

Max one weekday IST entry; first qualifying signal; chronological 2025 selection,
2026 historical recheck. No leverage, 10% notional exposure; no funding modeled.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_ema9_21_daily_quality_1m import load,ema,rma,FEE,ALLOCATION

OUT=Path("analysis/ema9_21_quality_upgrade")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
SESSIONS=("all","eu_us")
FAMILIES=("cross","pullback_break","trend_break","reclaim")
STOP_MULT=(1.5,2.5)
RRS=(2.0,3.0)
MAX_HOLD=720
SLIP=5.0

def feature_frame(m):
    op,hi,lo,cl,vol=[m[x] for x in ("open","high","low","close","volume")]
    fast=ema(cl,9);slow=ema(cl,21)
    prev=cl.shift()
    tr=pd.concat([hi-lo,(hi-prev).abs(),(lo-prev).abs()],axis=1).max(axis=1)
    atr1=rma(tr,14)
    up=hi.diff().clip(lower=0)
    dn=(-lo.diff()).clip(lower=0)
    p=rma(up.where(up>dn,0.0),14)
    q=rma(dn.where(dn>up,0.0),14)
    positive=100*p/rma(tr,14).replace(0,np.nan)
    negative=100*q/rma(tr,14).replace(0,np.nan)
    adx=rma(100*(positive-negative).abs()/(positive+negative).replace(0,np.nan),14)

    close5=cl.resample("5min",closed="left",label="left").last()
    count5=cl.resample("5min",closed="left",label="left").count()
    close15=cl.resample("15min",closed="left",label="left").last()
    count15=cl.resample("15min",closed="left",label="left").count()
    close5=close5.where(count5.eq(5))
    close15=close15.where(count15.eq(15))
    htf_up=pd.Series(True,index=m.index)
    htf_dn=pd.Series(True,index=m.index)
    for closex in (close5,close15):
        a=ema(closex,9).shift(1).reindex(m.index,method="ffill")
        b=ema(closex,21).shift(1).reindex(m.index,method="ffill")
        htf_up &= (a>b)
        htf_dn &= (a<b)

    hi5=hi.resample("5min",closed="left",label="left").max()
    lo5=lo.resample("5min",closed="left",label="left").min()
    c5=close5
    t5=pd.concat([hi5-lo5,(hi5-c5.shift()).abs(),(lo5-c5.shift()).abs()],axis=1).max(axis=1)
    atr5=rma(t5,14).shift(1).reindex(m.index,method="ffill")
    # Signal evaluated at 1m bar CLOSE, i.e. available to next minute's OPEN.
    ratio=vol/vol.rolling(20,min_periods=20).mean().replace(0,np.nan)
    candle_range=(hi-lo).replace(0,np.nan)
    body=((cl-op).abs()/candle_range).fillna(0)
    bull_bar=cl>op
    bear_bar=cl<op
    crosslong=(fast>slow)&(fast.shift(1)<=slow.shift(1))
    crossshort=(fast<slow)&(fast.shift(1)>=slow.shift(1))
    touchlong=pd.Series(False,index=m.index)
    touchshort=pd.Series(False,index=m.index)
    for k in range(1,6):
        touchlong|=(lo.shift(k)<=slow.shift(k))
        touchshort|=(hi.shift(k)>=slow.shift(k))
    trendlong=(fast>slow)&(slow>slow.shift(3))
    trendshort=(fast<slow)&(slow<slow.shift(3))
    vol1=(ratio>=1.1)&(adx>=18)
    volumehigh=(ratio>=1.3)&(adx>=22)
    bull_base=htf_up&bull_bar&(positive>negative)
    bear_base=htf_dn&bear_bar&(negative>positive)

    masks={
        "cross": (
            crosslong&bull_base&vol1,
            crossshort&bear_base&vol1,
        ),
        "pullback_break":(
            trendlong&bull_base&touchlong&(cl>hi.shift(1).rolling(5,min_periods=5).max())&vol1,
            trendshort&bear_base&touchshort&(cl<lo.shift(1).rolling(5,min_periods=5).min())&vol1,
        ),
        "trend_break":(
            trendlong&bull_base&volumehigh&(body>=0.55)&(cl>hi.shift(1).rolling(15,min_periods=15).max()),
            trendshort&bear_base&volumehigh&(body>=0.55)&(cl<lo.shift(1).rolling(15,min_periods=15).min()),
        ),
        "reclaim":(
            trendlong&bull_base&touchlong&vol1&(cl>fast)&(cl.shift(1)<=fast.shift(1)),
            trendshort&bear_base&touchshort&vol1&(cl<fast)&(cl.shift(1)>=fast.shift(1)),
        ),
    }
    data={}
    for name,(long,short) in masks.items():
        data[name]=(long.fillna(False).to_numpy(bool),short.fillna(False).to_numpy(bool))
    return data,atr5.to_numpy(float)

def sim(m,mask,atr5,session,stop_mult,rr,slip=SLIP):
    lo_signal,short_signal=mask
    op=m.open.to_numpy(float);hi=m.high.to_numpy(float)
    lo=m.low.to_numpy(float);cl=m.close.to_numpy(float)
    idx=m.index
    local=idx.tz_convert("Asia/Kolkata")
    days=np.asarray(local.strftime("%Y-%m-%d"))
    months=np.asarray(local.strftime("%Y-%m"))
    weekday=np.asarray(local.weekday<5)
    mins=np.asarray(local.hour*60+local.minute)
    event=lo_signal|short_signal
    allow=weekday & np.roll(weekday,-1) & (months>="2025-01")&(months<="2026-11")
    allow[-1]=False
    if session=="eu_us":allow &= (mins>=13*60+30)&(mins<23*60+30)
    candidates=np.flatnonzero(event&allow&np.isfinite(atr5)&(atr5>0))
    last_exit=-1;last_day=""
    trades=[]
    for signal in candidates:
        if signal<=last_exit or days[signal]==last_day:continue
        entryi=signal+1
        if entryi>=len(m):break
        side=1 if lo_signal[signal] else -1
        midin=op[entryi]
        fillin=midin+side*slip
        risk=stop_mult*atr5[signal]
        stop=fillin-side*risk
        target=fillin+side*rr*risk
        # Intraminute stop wins if both touched; stop gap -> worse open.
        end=min(entryi+MAX_HOLD,len(m)-1)
        j=entryi
        reason="timeout"
        while j<end:
            stophit=(lo[j]<=stop) if side==1 else (hi[j]>=stop)
            targethit=(hi[j]>=target) if side==1 else (lo[j]<=target)
            if stophit:
                midout=min(op[j],stop) if side>0 else max(op[j],stop)
                reason="stop";break
            if targethit:
                midout=target
                reason="target";break
            j+=1
        else:
            midout=op[end]
            j=end
        fillout=midout-side*slip
        gross=side*(midout-midin)
        net=side*(fillout-fillin)-FEE*(fillin+fillout)
        last_exit=j;last_day=days[signal]
        trades.append(dict(signal_utc=str(idx[signal]),entry_utc=str(idx[entryi]),
            exit_utc=str(idx[j]),signal_day_ist=days[signal],
            exit_month_ist=months[j],side=side,exit_reason=reason,
            risk_points=round(float(risk),3),hold_mins=int(j-entryi),
            entry_fill=float(fillin),gross_points=float(gross),
            fee_gst_points=float(FEE*(fillin+fillout)),slippage_points=float(2*slip),
            net_points=float(net),account_return=float(ALLOCATION*net/fillin)))
    return pd.DataFrame.from_records(trades,columns=[
        "signal_utc","entry_utc","exit_utc","signal_day_ist","exit_month_ist",
        "side","exit_reason","risk_points","hold_mins","entry_fill",
        "gross_points","fee_gst_points","slippage_points","net_points","account_return"])

def metrics(df):
    overall={"trades":int(len(df)),"wins":int((df.net_points>0).sum()) if len(df) else 0,
             "losses":int((df.net_points<0).sum()) if len(df) else 0}
    pos=float(df.loc[df.net_points>0,"net_points"].sum())
    neg=float(-df.loc[df.net_points<0,"net_points"].sum())
    overall.update(win_rate_pct=round(100*overall["wins"]/len(df),2) if len(df) else 0,
        profit_factor=round(pos/neg,3) if neg else None,
        net_points=round(float(df.net_points.sum()),2),
        gross_points=round(float(df.gross_points.sum()),2),
        fee_gst_points=round(float(df.fee_gst_points.sum()),2),
        slip_points=round(float(df.slippage_points.sum()),2))
    return overall

def summarize(df):
    months=[]
    equity=1.0;peak=1.0;drawdown=0.0
    annual_equity={"2025":1.0,"2026":1.0}
    for mon in MONTHS:
        trades=df.loc[df.exit_month_ist==mon].sort_values("exit_utc")
        start=equity
        for r in trades.account_return:
            equity*=1+float(r)
            annual_equity[mon[:4]]*=1+float(r)
            peak=max(peak,equity);drawdown=max(drawdown,1-equity/peak)
        months.append(dict(month_ist=mon,trades=len(trades),wins=int((trades.net_points>0).sum()),
            losses=int((trades.net_points<0).sum()),net_points=round(float(trades.net_points.sum()),2),
            account_return_pct=round(100*(equity/start-1),6)))
    monthly=pd.DataFrame(months)
    x=metrics(df)
    x.update(net_return_pct=round((equity-1)*100,5),
       return_2025_pct=round((annual_equity["2025"]-1)*100,5),
       return_2026_pct=round((annual_equity["2026"]-1)*100,5),
       positive_2025=int((monthly.iloc[:12].account_return_pct>0).sum()),
       positive_2026=int((monthly.iloc[12:].account_return_pct>0).sum()),
       max_closed_dd_pct=round(100*drawdown,5),
       worst_month_pct=round(float(monthly.account_return_pct.min()),5))
    return x,monthly

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=load()
    families,atr5=feature_frame(m)
    records=[];allmonth=[];ledgers={}
    for family in FAMILIES:
        for session in SESSIONS:
            for mult in STOP_MULT:
                for rr in RRS:
                    key=f"{family}__{session}__atr{mult:g}__rr{rr:g}"
                    ledger=sim(m,families[family],atr5,session,mult,rr)
                    result,monthly=summarize(ledger)
                    result.update(variant=key,signal=family,session=session,
                                  stop_atr5_mult=mult,rr=rr)
                    records.append(result)
                    monthly["variant"]=key
                    allmonth.append(monthly)
                    ledgers[key]=ledger
                    print("VARIANT "+json.dumps(result,sort_keys=True),flush=True)
    rank=pd.DataFrame(records)
    # 2025 only selection, tie break lower realized DD and higher number of trades.
    rank=rank.sort_values(["return_2025_pct","max_closed_dd_pct","trades"],
                          ascending=[False,True,False])
    best=str(rank.iloc[0].variant)
    # Conservative slippage alternative for preselected 2025 winner, no retuning.
    r=rank.iloc[0]
    halfledger=sim(m,families[r.signal],atr5,r.session,float(r.stop_atr5_mult),float(r.rr),slip=0.5)
    halfsummary,halfmonth=summarize(halfledger)
    print("BEST_2025 "+json.dumps(r.to_dict(),sort_keys=True),flush=True)
    print("SELECTED_0_5_SLIP "+json.dumps(halfsummary,sort_keys=True),flush=True)
    print("SELECTED_MONTHLY_5_SLIP\n"+pd.concat(allmonth).query("variant == @best").to_string(index=False),flush=True)
    print("SELECTED_MONTHLY_0_5_SLIP\n"+halfmonth.to_string(index=False),flush=True)
    rank.to_csv(OUT/"all_variants.csv",index=False)
    pd.concat(allmonth).to_csv(OUT/"all_months.csv",index=False)
    ledgers[best].to_csv(OUT/"selected_5pt_ledger.csv.gz",index=False,compression="gzip")
    halfledger.to_csv(OUT/"selected_halfpt_ledger.csv.gz",index=False,compression="gzip")
    halfmonth.to_csv(OUT/"selected_halfpt_monthly.csv",index=False)
    (OUT/"selected.json").write_text(json.dumps({"selected_2025":r.to_dict(),
       "half_point_slippage":halfsummary,
       "note":"Selection optimized on 2025 and reported 2026 recheck; 2026 has also been seen by earlier research.",
       "data_utc_start":str(m.index.min()),"data_utc_end":str(m.index.max()),
       "cost_model":"0.05% per side taker + 18% GST, 5 pts adverse per side, 10% notional exposure, no leverage; funding excluded",
       "max_hold_minutes":MAX_HOLD,"trade_days":"Monday-Friday Asia/Kolkata"},indent=2)+"\n")
    report=["# EMA9/21 1m weekday quality upgrade — frozen 32 variants",
            "","2025-only ranking; 2026 **historical recheck, NOT pristine holdout**. Overnight risk bounded to <=720m. Stops-first within each 1m candle.",
            "","## Top 10 ranked on 2025 account return","",
            rank.head(10).to_markdown(index=False),"",
            "## 2025-selected monthly","",
            pd.concat(allmonth).query("variant == @best").to_markdown(index=False),"",
            "## 0.5 point slippage sensitivity, selected fixed rules","",
            halfmonth.to_markdown(index=False),"",
            "**Caution:** results are in-sample explorations; actual fills/funding may differ; do not claim a validated edge."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("EMA_QUALITY_UPGRADE_COMPLETE",flush=True)

if __name__=="__main__":
    run()
