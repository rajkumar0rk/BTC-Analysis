#!/usr/bin/env python3
"""Stage25: independent 1h entries and 4h trend-context research.

Purpose: SEARCH for >=10% NET in EACH of 22 completed calendar months
Jan 2025--Oct 2026, without using 2026 to select the final strategy.

Signals: fully closed 1H bars only; enter next available 1m OPEN.
Execution: 1m intrabar stop FIRST, adverse stop gaps, dynamic trailing stop
updated using previous COMPLETED minute, monthly flattening to make monthly
NAV exact. One open position at a time per candidate setting.
Fees: Delta India futures taker 0.05% each side, GST 18% on fees,
5 BTC/USD price points adverse slippage per side. Funding and real spreads
not in archive. Test is historical and not a promise of future returns.

2026 has been inspected in earlier stages and is NOT a blind holdout.
The 2026-10-31 UTC day is missing (1,440 candles); October results incomplete.
"""
from pathlib import Path
import json
import math
import numpy as np
import pandas as pd
from numba import njit
# Self-contained new research. Reads ORIGINAL candle partitions only;
# never imports a previous analysis module or its fitted results.
BASE = Path("data/delta_india/BTCUSD/1m")
FEE = 0.0005 * 1.18
SLIPPAGE = 5.0

def read_archive():
    sources = sorted(BASE.glob("20??-??.csv.gz"))
    if len(sources) < 22:
        raise RuntimeError("Need full raw 2025 + Jan-Oct 2026 BTCUSD partitions")
    parts = [pd.read_csv(s, compression="gzip",
              usecols=["time","open","high","low","close","volume"])
              for s in sources]
    raw = pd.concat(parts,ignore_index=True).sort_values("time",kind="stable")
    raw = raw.reset_index(drop=True)
    unix = raw.time.to_numpy(np.int64)
    if not np.all(np.diff(unix)>0): raise ValueError("Timestamps duplicate/out of order")
    if not np.all((np.diff(unix)%60)==0): raise ValueError("Nonminute timestamps")
    for field in ["open","high","low","close","volume"]:
        if not np.isfinite(raw[field].to_numpy(float)).all():
            raise ValueError("Invalid raw OHLCV "+field)
    if ((raw.low<=0)|(raw.high<raw.low)|(raw.open<raw.low)|
        (raw.close<raw.low)|(raw.open>raw.high)|
        (raw.close>raw.high)|(raw.volume<0)).any():
        raise ValueError("Inconsistent raw candles")
    breaks=np.flatnonzero(np.diff(unix)!=60)+1
    begins=np.r_[0,breaks].astype(np.int32)
    ends=np.r_[breaks,len(raw)].astype(np.int32)
    segstart=np.empty(len(raw),np.int32)
    segend=np.empty(len(raw),np.int32)
    for start,end in zip(begins,ends):
        segstart[start:end]=start
        segend[start:end]=end
    qual={"source":"ORIGINAL Delta India BTCUSD 1m raw .csv.gz partitions only",
        "partition_count":len(sources),"first_utc":str(pd.to_datetime(unix[0],unit="s",utc=True)),
        "last_utc":str(pd.to_datetime(unix[-1],unit="s",utc=True)),
        "observed":int(len(raw)),"missing_minutes":int((unix[-1]-unix[0])//60+1-len(raw)),
        "gaps":[{"before":str(pd.to_datetime(unix[j-1],unit="s",utc=True)),
            "after":str(pd.to_datetime(unix[j],unit="s",utc=True)),
            "missing":int((unix[j]-unix[j-1])//60-1)} for j in breaks]}
    raw.index=pd.to_datetime(raw.time,unit="s",utc=True)
    return raw,segstart,segend,qual


OUT=Path("analysis/independent_stage25_hourly_trend")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str)
MONTH_CODES=np.array([int(m.replace("-","")) for m in MONTHS],dtype=np.int32)
PATS=("donchian_break","trend_reclaim","momentum_accel","squeeze_break","inside_bar_break")
LOOKBACKS=(12,24)
STOP_MULTIPLIERS=(1.5,2.5)
ALIGN=(False,True)
EXITS=("fixed_2R","fixed_3R","trail_2R","trail_3R")
HOLDS=(720,2880)
RISKS=(.005,.01,.02)
LEVERAGES=(3.,5.,10.)
MIN_STOP=150.
MAX_STOP=3500.

def make_events(f,seg_start,seg_end):
    """Independent hourly breakout, pullback and momentum signals."""
    h=f[["open","high","low","close","volume"]].resample(
        "1h",label="right",closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    cnt=f.close.resample("1h",label="right",closed="left").count()
    h["valid"]=cnt.rolling(48,min_periods=48).min().eq(60)
    pc=h.close.shift(1)
    tr=pd.concat((h.high-h.low,(h.high-pc).abs(),
                  (h.low-pc).abs()),axis=1).max(axis=1)
    h["atr"]=tr.rolling(20,min_periods=20).mean()
    h["ema20"]=h.close.ewm(span=20,adjust=False).mean()
    h["ema50"]=h.close.ewm(span=50,adjust=False).mean()
    h["vr"]=h.volume/h.volume.shift(1).rolling(20,min_periods=20).mean().replace(0,np.nan)
    h["range"]=h.high-h.low
    h["body"]=(h.close-h.open).abs()/h["range"].replace(0,np.nan)
    h["loc"]=(h.close-h.low)/h["range"].replace(0,np.nan)
    h["quiet"]=(h["range"].shift(1).rolling(6).mean()<
                .85*h["range"].shift(1).rolling(24).median())
    h4=f[["open","high","low","close"]].resample(
        "4h",label="right",closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last"})
    cnt4=f.close.resample("4h",label="right",closed="left").count()
    h4["valid"]=cnt4.rolling(50,min_periods=50).min().eq(240)
    h4["ema20"]=h4.close.ewm(span=20,adjust=False).mean()
    h4["ema50"]=h4.close.ewm(span=50,adjust=False).mean()
    eff=h4.close.diff(6).abs()/h4.close.diff().abs().rolling(6).sum().replace(0,np.nan)
    h4["bull"]=h4.valid&(h4.close>h4.ema20)&(h4.ema20>h4.ema50)&(h4.ema20>h4.ema20.shift(3))
    h4["bear"]=h4.valid&(h4.close<h4.ema20)&(h4.ema20<h4.ema50)&(h4.ema20<h4.ema20.shift(3))
    h4["eff"]=eff
    context=h4.reindex(h.index,method="ffill")
    h["trend_up"]=context.bull.fillna(False).to_numpy(bool)
    h["trend_down"]=context.bear.fillna(False).to_numpy(bool)
    h["eff_ok"]=context.eff.ge(.28).fillna(False).to_numpy(bool)
    bull=(h.close>h.open)&(h.body>=.5)&(h["loc"]>=.7)
    bear=(h.close<h.open)&(h.body>=.5)&(h["loc"]<=.3)
    event_idx=f.index.get_indexer(h.index)
    rows=[]
    for lb in LOOKBACKS:
        ph=h.high.shift(1).rolling(lb,min_periods=lb).max()
        pl=h.low.shift(1).rolling(lb,min_periods=lb).min()
        prior_median=h.close.shift(1).rolling(lb,min_periods=lb).median()
        inside=(h.high.shift(1)<h.high.shift(2))&(h.low.shift(1)>h.low.shift(2))
        sig={
            "donchian_break":(
                bull&(h.close>ph)&(h.vr>=1.0),
                bear&(h.close<pl)&(h.vr>=1.0)),
            "trend_reclaim":(
                bull&(h.ema20>h.ema50)&(h.low<=h.ema20)&(h.close>h.ema20)&
                (h.vr>=.75)&(h.close>prior_median),
                bear&(h.ema20<h.ema50)&(h.high>=h.ema20)&(h.close<h.ema20)&
                (h.vr>=.75)&(h.close<prior_median)),
            "momentum_accel":(
                bull&(h.close>ph)&(h["range"]>=1.35*h.atr)&(h.vr>=1.1),
                bear&(h.close<pl)&(h["range"]>=1.35*h.atr)&(h.vr>=1.1)),
            "squeeze_break":(
                h.quiet&bull&(h.close>ph)&(h["range"]>=1.15*h.atr)&(h.vr>=1.2),
                h.quiet&bear&(h.close<pl)&(h["range"]>=1.15*h.atr)&(h.vr>=1.2)),
            "inside_bar_break":(
                inside&bull&(h.close>h.high.shift(2))&(h.close>prior_median),
                inside&bear&(h.close<h.low.shift(2))&(h.close<prior_median))
        }
        for pat,(longmask,shortmask) in sig.items():
            for side,raw in ((1,longmask),(-1,shortmask)):
                valid=(raw&h.valid&h.atr.gt(0)).fillna(False).to_numpy(bool)
                for j in np.flatnonzero(valid):
                    k=int(event_idx[j])
                    if k<0 or k>=len(f) or k<seg_start[k]+200*60:continue
                    ist=h.index[j].tz_convert("Asia/Kolkata")
                    if ist.year*100+ist.month>202610:continue
                    aligned=bool(h.eff_ok.iat[j] and (
                        h.trend_up.iat[j] if side==1 else h.trend_down.iat[j]))
                    atr=float(h.atr.iat[j])
                    for sm in STOP_MULTIPLIERS:
                        risk=atr*sm
                        if not 200.<=risk<=5500.:continue
                        rows.append((pat,lb,side,k,round(risk,5),sm,aligned))
    ev=pd.DataFrame(rows,columns=[
       "pattern","lookback","side","k","risk_pts","stop_mult","hour_aligned"])
    if ev.empty:raise ValueError("No independent 1H entry events")
    return ev,h

@njit(cache=True)
def replay_series(op,hi,lo,cl,seg_end,month_codes,
                  entries,sides,risks,exit_mode,hold):
    n=len(entries)
    out=np.empty((n,7),dtype=np.float64)
    size=0
    busy=-1
    for z in range(n):
        k=int(entries[z])
        if k<=busy:continue
        side=int(sides[z])
        risk=float(risks[z])
        entry=float(op[k])
        stop=entry-side*risk
        target=entry+side*risk*(2. if exit_mode==0 else 3. if exit_mode==1 else 7. if exit_mode==2 else 10.)
        limit=min(k+hold,int(seg_end[k]))
        reason=3
        exitmid=float(cl[limit-1])
        j=limit-1
        for ix in range(k,limit):
            j=ix
            hit_stop=(lo[ix]<=stop if side==1 else hi[ix]>=stop)
            hit_tp=(hi[ix]>=target if side==1 else lo[ix]<=target)
            # Missing exact intra-minute sequencing: stop must win a tie.
            if hit_stop:
                exitmid=min(op[ix],stop) if side==1 else max(op[ix],stop)
                reason=0
                break
            if hit_tp:
                exitmid=target
                reason=1
                break
            # Flatten BEFORE the next calendar month (IST), at the current
            # minute close, so no trade carries unrealized PnL across months.
            month_ends_here=(ix+1<len(month_codes) and
                             month_codes[ix+1]!=month_codes[ix])
            if ix+1==limit or month_ends_here:
                exitmid=cl[ix]
                reason=2 if month_ends_here else 3
                break
            # Trailing updates are based on the COMPLETED current minute;
            # therefore updated stop may be hit no earlier than NEXT minute.
            if exit_mode>=2:
                favorable=side*(cl[ix]-entry)
                activation=(2. if exit_mode==2 else 3.)*risk
                buffer=(1. if exit_mode==2 else 1.5)*risk
                if favorable>=activation:
                    candidate=cl[ix]-side*buffer
                    if side==1:
                        stop=max(stop,candidate)
                    else:
                        stop=min(stop,candidate)
        fin=entry+side*SLIPPAGE
        fout=exitmid-side*SLIPPAGE
        net_pts=side*(fout-fin)-FEE*(fin+fout)
        out[size,0]=k
        out[size,1]=j
        out[size,2]=side
        out[size,3]=entry
        out[size,4]=risk
        out[size,5]=net_pts
        out[size,6]=reason
        size+=1
        busy=j
    return out[:size]

def stats(trades,months,stoprisk,lev,model):
    # No same-bar concurrent trades. Fractional BTC notional with leverage
    # and trade-risk constraint. Treat every month as an equity period;
    # daily/monthly compounding is multiplicative across trade closes.
    if len(trades)==0:return None,[]
    entry=trades[:,3]
    r=trades[:,4]
    pnl=trades[:,5]
    realized_risk=np.minimum(stoprisk,lev*r/entry)
    ret=realized_risk*pnl/r
    if np.any(ret<=-1.) or not np.isfinite(ret).all():return None,[]
    at_exit=trades[:,1].astype(np.int64)
    code=months[at_exit]
    monthly=[]
    for month,monthcode in zip(MONTHS,MONTH_CODES):
        pick=ret[code==monthcode]
        mval=(np.prod(1.+pick)-1.) if len(pick) else 0.
        v=pnl[code==monthcode]
        monthly.append({"month_ist":month,"return_pct":round(100*float(mval),6),
                        "trades":int(len(pick)),"wins":int((v>0).sum()),
                        "losses":int((v<0).sum()),"flat":int((v==0).sum())})
    train=monthly[:12]; check=monthly[12:22]
    cap=100.;peak=100.;dd=0.
    train_dd=0.;train_cap=100.;train_peak=100.
    for x,mc in zip(ret,code):
        cap*=1.+x
        peak=max(peak,cap)
        dd=max(dd,100*(1.-cap/peak))
        if mc < 202601:
            train_cap*=1.+x
            train_peak=max(train_peak,train_cap)
            train_dd=max(train_dd,100*(1.-train_cap/train_peak))
    def csum(series):
        return round((np.prod([1.+s["return_pct"]/100 for s in series])-1)*100,5)
    row={**model,"risk_pct":stoprisk*100,"max_leverage":lev,
         "trades_total":int(len(trades)),
         "trades_2025":int((code<202601).sum()),
         "2025_trade_close_drawdown_pct":round(train_dd,4),
         "wins":int((pnl>0).sum()),
         "losses":int((pnl<0).sum()),"flat":int((pnl==0).sum()),
         "win_rate_pct":round(100*float((pnl>0).mean()),3),
         "2025_months_ge10":sum(m["return_pct"]>=10. for m in train),
         "2026_months_ge10":sum(m["return_pct"]>=10. for m in check),
         "2025_positive":sum(m["return_pct"]>0 for m in train),
         "2026_positive":sum(m["return_pct"]>0 for m in check),
         "2025_negative":sum(m["return_pct"]<0 for m in train),
         "2026_negative":sum(m["return_pct"]<0 for m in check),
         "worst_2025_pct":min(m["return_pct"] for m in train),
         "worst_2026_pct":min(m["return_pct"] for m in check),
         "net_2025_pct":csum(train),"net_2026_pct":csum(check),
         "max_trade_close_drawdown_pct":round(dd,4),
         "all_22_months_ge10":all(m["return_pct"]>=10. for m in monthly)}
    return row,monthly

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,seg_start,seg_end,quality=read_archive()
    events,feature=make_events(f,seg_start,seg_end)
    # Only completed Jan 2025-Oct 2026 months in these tests. November
    # data may help causal lookback on Oct31 gap but is never scored.
    ix=pd.to_datetime(f.time,unit="s",utc=True).dt.tz_convert("Asia/Kolkata")
    monthcode=(ix.dt.year*100+ix.dt.month).to_numpy(np.int32)
    op=f.open.to_numpy(np.float64);hi=f.high.to_numpy(np.float64)
    lo=f.low.to_numpy(np.float64);cl=f.close.to_numpy(np.float64)
    rows=[]; ledgers={}; summaries={}; nreplays=0
    # Never include uncompleted November 2026 in account-model searches.
    events=events[events.k.map(lambda k: monthcode[int(k)]<=202610)]
    for pat in PATS:
      for lb in LOOKBACKS:
        for align in ALIGN:
          for sm in STOP_MULTIPLIERS:
            subset=events[(events.pattern==pat)&(events.lookback==lb)&
                          (events.stop_mult==sm)]
            if align: subset=subset[subset.hour_aligned]
            subset=subset.sort_values(["k","side"],kind="stable")
            if subset.empty:continue
            entries=subset.k.to_numpy(np.int64)
            sides=subset.side.to_numpy(np.int32)
            risks=subset.risk_pts.to_numpy(np.float64)
            for exit_mode,mode in enumerate(EXITS):
              for hold in HOLDS:
                ledger=replay_series(op,hi,lo,cl,seg_end,monthcode,
                                     entries,sides,risks,exit_mode,hold)
                if len(ledger)==0:continue
                nreplays+=1
                model=dict(pattern=pat,lookback=lb,hour_align=align,
                           stop_atr=sm,exit_policy=mode,max_hold_minutes=hold)
                key=(pat,lb,align,sm,mode,hold)
                ledgers[key]=ledger
                for risk in RISKS:
                  for lev in LEVERAGES:
                    row,mo=stats(ledger,monthcode,risk,lev,model)
                    if row is not None:
                        rows.append(row)
    summary=pd.DataFrame(rows)
    if summary.empty:raise RuntimeError("No completed account models")
    # Model CHOICE must use 2025 ONLY. 2026 scores are not ranking inputs.
    rank=summary.sort_values(
        ["2025_months_ge10","2025_positive","worst_2025_pct",
         "net_2025_pct","2025_trade_close_drawdown_pct"],
        ascending=[False,False,False,False,True],kind="stable")
    safe=rank[(rank["2025_trade_close_drawdown_pct"]<=40)&(rank.trades_2025>=35)]
    choice=(safe if not safe.empty else rank).iloc[0]
    key=(choice["pattern"],int(choice["lookback"]),bool(choice["hour_align"]),
         float(choice["stop_atr"]),choice["exit_policy"],int(choice["max_hold_minutes"]))
    selected_tr=ledgers[key]
    _,monthly=stats(selected_tr,monthcode,float(choice["risk_pct"])/100,
                     float(choice["max_leverage"]),dict(
                         pattern=choice["pattern"],lookback=int(choice["lookback"]),
                         hour_align=bool(choice["hour_align"]),stop_atr=float(choice["stop_atr"]),
                         exit_policy=choice["exit_policy"],
                         max_hold_minutes=int(choice["max_hold_minutes"])))
    monthfile=pd.DataFrame(monthly)
    ledger=pd.DataFrame(selected_tr,columns=["entry_idx","exit_idx","side","entry_price",
                                              "risk_points","net_points","exit_reason"])
    ledger["entry_utc"]=pd.to_datetime(f.time.to_numpy(np.int64)[ledger.entry_idx.astype(int)],
                                         unit="s",utc=True)
    ledger["exit_utc"]=pd.to_datetime(f.time.to_numpy(np.int64)[ledger.exit_idx.astype(int)],
                                        unit="s",utc=True)
    ledger["exit_month_ist"]=monthcode[ledger.exit_idx.astype(int)]
    ledger["net_R"]=ledger.net_points/ledger.risk_points
    ledger["risk_pct_used"]=np.minimum(
        float(choice["risk_pct"])/100,
        float(choice["max_leverage"])*ledger.risk_points/ledger.entry_price)*100
    ledger["account_return_pct"]=(ledger["risk_pct_used"]/100)*ledger["net_R"]*100
    ledger.to_csv(OUT/"selected_trade_ledger.csv",index=False)
    summary.to_csv(OUT/"all_account_models.csv",index=False)
    rank.head(30).to_csv(OUT/"top_2025_only.csv",index=False)
    monthfile.to_csv(OUT/"selected_monthly_2025_2026.csv",index=False)
    score=int(summary.all_22_months_ge10.sum())
    qa={
      "target":"10% net account return in all 22 completed IST calendar months",
      "genuine_result":bool(score),"matching_account_models":score,
      "models_evaluated":len(summary),"unique_trade_replays":nreplays,
      "raw_signal_events":len(events),"total_one_minute_candles":len(f),
      "source_quality":quality,
      "selected_2025_only":choice.to_dict(),
      "costs":{"taker_fee_per_side":.0005,"gst_on_fee":.18,
               "adverse_slippage_usd_each_side":float(SLIPPAGE)},
      "critical_limitations":[
         "2026 was previously researched and is NOT a blind out-of-sample check",
         "October 2026 is missing all 1m candles for Oct 31 UTC and is NOT fully verified",
         "November 2026 is excluded because incomplete",
         "2025-01 first five and a half IST hours are missing because archive starts Jan 1 UTC",
         "Intraminute stop versus target uses conservative stop-first",
         "Open stop can gap; actual stop fill can be worse than stop",
         "One position per strategy, no opposite position concurrency",
         "Month-boundary flattening closes each trade at final 1m close and pays exit costs",
         "Selected strategies are ranked ONLY on 2025, then checked unchanged on 2026",
         "Selection over many settings still overfits 2025 training",
         "Funding, order book spreads, queue position, impact, exchange margin and liquidation not modeled",
         "Small account lot size feasibility not modeled, no assurance of profitable live trading",
         "Drawdown sampled at trade close, not true intratrade equity lows",
         "Risk size and max leverage are hypothetical caps, not live trading recommendations"
      ]
    }
    (OUT/"quality.json").write_text(json.dumps(qa,indent=2,default=str)+"\n")
    display_cols=["pattern","lookback","hour_align","stop_atr","exit_policy",
        "max_hold_minutes","risk_pct","max_leverage","trades_total","wins","losses",
        "2025_months_ge10","2026_months_ge10","2025_positive","2026_positive",
        "worst_2025_pct","worst_2026_pct","net_2025_pct","net_2026_pct",
        "max_trade_close_drawdown_pct"]
    report=[
      "# Stage25 -- Independent BTC 1H trend and momentum search for +10% NET each month",
      "",
      "## Model and validity",
      "Original Delta BTCUSD raw 1m data. Closed 1H signals, optional 4H trend confirmation",
      "option, next 1m open fill, 1m stop-first replay, monthly flattening.",
      "One position at a time per model. Model selection 2025 only;",
      "2026 checked without adjustment. Fees 0.05% per side, 18% GST",
      "and 5 USD adverse slip each side (no funding/bid-ask modeled).",
      "",
      f"**All-22-month winners: {score} of {len(summary)} modeled account configurations**",
      "",
      "## 2025-ranked candidates (2026 scores shown only for audit)",
      rank.head(12)[display_cols].to_markdown(index=False),"",
      "## 2025-only selected candidate monthly actual net account P&L",
      monthfile.to_markdown(index=False),"",
      "## Caveats",
      *["- "+x for x in qa["critical_limitations"]],"",
      "An in-sample historical fit is NOT evidence of future guaranteed returns.",
      "October 2026 is an INCOMPLETE-DATA calendar month despite its completed date.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE24_RESULTS "+json.dumps({
        "account_models":len(summary),"signals":len(events),
        "trading_replays":nreplays,"all_22_months_over_10":score,
        "selected":choice[display_cols].to_dict()},default=str))
    print("MONTHLY\n"+monthfile.to_string(index=False))
if __name__=="__main__":
    main()
