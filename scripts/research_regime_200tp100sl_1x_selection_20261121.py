#!/usr/bin/env python3
"""Causal BTC 200-TP/100-SL 1x market-regime evidence search.

This script deliberately contains a fixed, predeclared small candidate set.
It does not optimize on 2026, search stops, change leverage, or assert daily profitability.

Reuses the already-audited one-trade-per-IST-day 1m stop-first backtester
from research_btc_daily_200tp_100sl_1x_20261121.py.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_btc_daily_200tp_100sl_1x_20261121 as core

OUT=Path("analysis/btc_regime_200tp100sl_selection_20261121")
BASE_INITIAL_NAV=10000.
TRAIN_MIN_PER_HALF=30
CONFIDENCE_Z=1.96
WINDOWS={
    "2025_H1":("2025-01-02","2025-06-30"),
    "2025_H2":("2025-07-01","2025-12-31"),
    "2025_ALL":("2025-01-02","2025-12-31"),
    "2026_H1_SEEN":("2026-01-01","2026-06-30"),
    "2026_H2_SEEN":("2026-07-01","2026-10-30"),
    "ALL":("2025-01-02","2026-10-30"),
}

def wilder(series,period=14):
    return series.ewm(alpha=1/period,adjust=False,min_periods=period).mean()

def compute_features(f):
    # Continuous native 1m archive, left-labeled 15m / right-labeled 1h.
    b=f.resample("15min",label="left",closed="left").agg(
        open=("open","first"),high=("high","max"),low=("low","min"),
        close=("close","last"),volume=("volume","sum"),n=("close","size"))
    h=f.resample("1h",label="right",closed="left").agg(
        open=("open","first"),high=("high","max"),low=("low","min"),
        close=("close","last"),n=("close","size"))
    complete15=b.n.eq(15)
    complete_hour=h.n.eq(60)
    keep15=complete15.rolling(30,min_periods=30).sum().eq(30)
    keep1h=complete_hour.rolling(55,min_periods=55).sum().eq(55)
    C=b.close.where(complete15)
    H=h.high.where(complete_hour);L=h.low.where(complete_hour)
    HC=h.close.where(complete_hour)
    he20=HC.ewm(span=20,adjust=False,min_periods=50).mean()
    he50=HC.ewm(span=50,adjust=False,min_periods=50).mean()
    hour_previous=HC.shift(1)
    hour_tr=pd.concat([H-L,(H-hour_previous).abs(),
        (L-hour_previous).abs()],axis=1).max(axis=1)
    atr1=wilder(hour_tr,14)
    up=H.diff(); down=-L.diff()
    plusdm=up.where((up>down)&(up>0),0.)
    minusdm=down.where((down>up)&(down>0),0.)
    plusdi=100*wilder(plusdm,14)/atr1.replace(0,np.nan)
    minusdi=100*wilder(minusdm,14)/atr1.replace(0,np.nan)
    DX=100*(plusdi-minusdi).abs()/(plusdi+minusdi).replace(0,np.nan)
    adx=wilder(DX,14)
    at15=pd.concat([b.high-b.low,(b.high-C.shift(1)).abs(),
        (b.low-C.shift(1)).abs()],axis=1).max(axis=1)
    atr15=wilder(at15,14)
    e15=C.ewm(span=20,adjust=False,min_periods=20).mean()
    mean20=C.rolling(20,min_periods=20).mean()
    std20=C.rolling(20,min_periods=20).std()
    upper=mean20+2*std20
    lower=mean20-2*std20
    delta=C.diff()
    gain=wilder(delta.clip(lower=0),14)
    loss=wilder(-delta.clip(upper=0),14)
    rsi=100-100/(1+gain/loss.replace(0,np.nan))
    rsi=rsi.where(~((loss==0)&(gain>0)),100.)
    rsi=rsi.where(~((gain==0)&(loss>0)),0.)
    vref=b.volume.rolling(20,min_periods=20).mean().shift(1)
    volratio=b.volume/vref.replace(0,np.nan)
    end=b.index+pd.Timedelta(minutes=15)
    hour=pd.DataFrame({"close1h":HC.where(keep1h),
           "e20":he20.where(keep1h),"e50":he50.where(keep1h),
           "adx":adx.where(keep1h),"atr":atr1.where(keep1h)})
    aligned=hour.reindex(end,method="ffill")

    h_c=aligned.close1h.to_numpy(float);a20=aligned.e20.to_numpy(float)
    a50=aligned.e50.to_numpy(float);a_dx=aligned.adx.to_numpy(float)
    h_atr=aligned.atr.to_numpy(float)
    trend_bull=(a_dx>=25)&(a20>a50)&(h_c>a20)
    trend_bear=(a_dx>=25)&(a20<a50)&(h_c<a20)
    range_mode=(a_dx<=18)
    classified=np.isfinite(a_dx)&np.isfinite(a20)&np.isfinite(h_c)
    transition=(classified & ~(trend_bull|trend_bear|range_mode))
    regime=np.full(len(b),"UNCLASSIFIED",dtype="U16")
    regime[transition]="TRANSITION"
    regime[range_mode]="RANGE"
    regime[trend_bull]="TREND_UP"
    regime[trend_bear]="TREND_DOWN"
    # High volatility is defined BEFORE target testing using prior 1H ATR.
    highvol=classified&(h_atr/h_c>=.007)
    lowvol=classified&~highvol

    o=b.open.to_numpy(float);c=b.close.to_numpy(float)
    hi=b.high.to_numpy(float);lo=b.low.to_numpy(float)
    ema=e15.to_numpy(float)
    r=rsi.to_numpy(float)
    v=volratio.to_numpy(float)
    atr=atr15.to_numpy(float)
    prevhi=b.high.shift(1).to_numpy(float)
    prevlo=b.low.shift(1).to_numpy(float)
    hi8=b.high.rolling(8,min_periods=8).max().shift(1).to_numpy(float)
    lo8=b.low.rolling(8,min_periods=8).min().shift(1).to_numpy(float)
    hi12=b.high.rolling(12,min_periods=12).max().shift(1).to_numpy(float)
    lo12=b.low.rolling(12,min_periods=12).min().shift(1).to_numpy(float)
    hi16=b.high.rolling(16,min_periods=16).max().shift(1).to_numpy(float)
    lo16=b.low.rolling(16,min_periods=16).min().shift(1).to_numpy(float)
    width4=(b.high.rolling(4).max()-b.low.rolling(4).min()).shift(1).to_numpy(float)
    closepos=(c-lo)/np.where(hi>lo,hi-lo,np.nan)
    bullish=(c>o); bearish=(c<o)
    valid=keep15.to_numpy(bool)&classified&np.isfinite(v)&np.isfinite(atr)
    long_break=(c>prevhi)&bullish&(c>ema)
    short_break=(c<prevlo)&bearish&(c<ema)
    # "touch" genuinely requires an earlier complete 15m LOW<=EMA20 (HIGH>= EMA20).
    prior_touch_l=(b.low<=e15).rolling(4,min_periods=4).max().shift(1).fillna(0).to_numpy(bool)
    prior_touch_s=(b.high>=e15).rolling(4,min_periods=4).max().shift(1).fillna(0).to_numpy(bool)
    inside=(b.high.shift(1)<b.high.shift(2))&(b.low.shift(1)>b.low.shift(2))
    mother_hi=b.high.shift(2).to_numpy(float)
    mother_lo=b.low.shift(2).to_numpy(float)
    inside=inside.fillna(False).to_numpy(bool)
    previous_bull=(b.close.shift(1)>b.open.shift(1)).fillna(False).to_numpy(bool)
    previous_bear=(b.close.shift(1)<b.open.shift(1)).fillna(False).to_numpy(bool)
    upper_b=upper.to_numpy(float);lower_b=lower.to_numpy(float)
    prevc=b.close.shift(1).to_numpy(float)
    prevclose2=b.close.shift(2).to_numpy(float)
    prev_ema=e15.shift(1).to_numpy(float)
    previous_mid=(b.high.shift(1)+b.low.shift(1)).to_numpy(float)*.5
    impulse_prev=(b.high.shift(1)-b.low.shift(1)).to_numpy(float)
    atr_prev=atr15.shift(1).to_numpy(float)

    # Base setups. Every entry in each market family is a fixed deterministic rule.
    masks={}
    def add(name,one,two):
        masks[name]=(valid&one,valid&two)
    add("T01_PULLBACK_BREAK",trend_bull&prior_touch_l&long_break,
        trend_bear&prior_touch_s&short_break)
    add("T02_8BAR_BREAK",trend_bull&(c>hi8)&(closepos>=.75)&(v>=1.25)&(r>58),
        trend_bear&(c<lo8)&(closepos<=.25)&(v>=1.25)&(r<42))
    add("T03_INSIDE_RELEASE",trend_bull&inside&(c>mother_hi)&(closepos>=.75)&(v>=1.1),
        trend_bear&inside&(c<mother_lo)&(closepos<=.25)&(v>=1.1))
    add("T04_STRONG_CONT",trend_bull&long_break&((hi-lo)>=1.3*atr)&
          (closepos>=.8)&(v>=1.3)&(r>=60),
        trend_bear&short_break&((hi-lo)>=1.3*atr)&
          (closepos<=.2)&(v>=1.3)&(r<=40))
    add("T05_TWO_BAR",trend_bull&long_break&previous_bull&(prevc>prevclose2)&(v>=1.),
        trend_bear&short_break&previous_bear&(prevc<prevclose2)&(v>=1.))
    add("B01_SQUEEZE_IGNITION",(trend_bull|transition)&(a20>a50)&
          (width4<2.2*atr)&(c>hi8)&(v>=1.2)&(closepos>=.7),
        (trend_bear|transition)&(a20<a50)&(width4<2.2*atr)&
          (c<lo8)&(v>=1.2)&(closepos<=.3))
    add("B02_TRANSITION_BREAK",transition&(a20>a50)&(c>hi12)&
          (v>=1.25)&(closepos>=.8)&(r>55),
        transition&(a20<a50)&(c<lo12)&
          (v>=1.25)&(closepos<=.2)&(r<45))
    add("R01_12BAR_SWEEP",range_mode&(lo<lo12)&(c>lo12)&bullish&
          (v>=1.)&(r<52),
        range_mode&(hi>hi12)&(c<hi12)&bearish&
          (v>=1.)&(r>48))
    add("R02_BOLLINGER_REENTRY",range_mode&(prevc<lower.shift(1).to_numpy(float))&
          (c>lower_b)&bullish&(r<55),
        range_mode&(prevc>upper.shift(1).to_numpy(float))&
          (c<upper_b)&bearish&(r>45))
    add("R03_4H_SWEEP",range_mode&(lo<lo16)&(c>lo16)&bullish&(v>=.8),
        range_mode&(hi>hi16)&(c<hi16)&bearish&(v>=.8))
    add("V01_EXHAUSTION_FADE",transition&(impulse_prev>1.7*atr_prev)&previous_bear&
          bullish&(c>previous_mid)&(v>=.8),
        transition&(impulse_prev>1.7*atr_prev)&previous_bull&
          bearish&(c<previous_mid)&(v>=.8))
    add("M01_RECLAIM",trend_bull&(prevc<prev_ema)&
          long_break&(r>50)&(v>=1.),
        trend_bear&(prevc>prev_ema)&
          short_break&(r<50)&(v>=1.))
    # Benchmark at the first 15m close at 12:00 IST, always trade candle body direction.
    ist=end.tz_convert("Asia/Kolkata")
    dtime=np.asarray(ist.strftime("%H:%M"))
    anydirection=(dtime=="12:00")&valid&(bullish|bearish)
    masks["D00_FIXED_CLOCK_BENCHMARK"]=(anydirection&bullish,anydirection&bearish)

    # Exactly two predeclared versions for each economic strategy:
    #  baseline market-state qualification and stricter >=0.7% hourly ATR.
    all_masks={}
    for name,(ml,ms) in masks.items():
        all_masks[name]=(ml,ms)
        if not name.startswith("D00"):
            all_masks[name+"_HIGHVOL"]=(ml&highvol,ms&highvol)
    t=f.time.to_numpy(np.int64)
    sig_sec=end.to_numpy(dtype="datetime64[s]").astype(np.int64)
    loc=np.searchsorted(t,sig_sec,side="left")
    locsafe=np.minimum(loc,len(t)-1)
    exists=(loc<len(t))&(t[locsafe]==sig_sec)
    date=np.asarray(ist.strftime("%Y-%m-%d"))
    use=(date>=core.FULL_DAY_START)&(date<=core.FULL_DAY_END)&exists
    events={}
    for name,(ml,ms) in all_masks.items():
        hit=np.flatnonzero(use&(ml|ms)&~(ml&ms))
        events[name]=[(int(loc[i]),int(1 if ml[i] else -1)) for i in hit]
    reg_counts={str(x):int((regime==x).sum()) for x in ("TREND_UP","TREND_DOWN","RANGE","TRANSITION","UNCLASSIFIED")}
    quality={"completed_15m":int(complete15.sum()),"completed_1h":int(complete_hour.sum()),
      "period_valid_closed_signals":int(valid.sum()),
      "candidate_count":len(events),"raw_events_by_candidate":{k:len(v) for k,v in events.items()},
      "hour_regime_15m_bar_counts":reg_counts,
      "hourly_highvol_15m_bars":int(highvol.sum()),
      "hourly_lowvol_15m_bars":int(lowvol.sum()),
      "signal_1m_open_alignment":int(exists.sum()),
      "regime_classification":"1H completed ADX(14) >=25 plus EMA20/50 and hour close for up/down trend; ADX<=18 range; otherwise transition",
      "volatility_classification":"Completed 1H ATR14 / last 1H close >=0.007 high volatility"}
    return events,quality

def period_metrics(trades,start,end):
    sel=trades[(trades.day_ist>=start)&(trades.day_ist<=end)]
    n=len(sel)
    if n==0:
        return {"trades":0,"tp_first":0,"tp_first_pct":0.,"wins":0,
            "net_win_pct":0.,"net_points_mean":None,"net_points_lower95":None,
            "compounded_account_pct":0.,"mean_raw_points":None}
    points=(sel.net_usd/sel.btc_equivalent_qty).to_numpy(float)
    mean=float(np.mean(points))
    std=float(np.std(points,ddof=1)) if n>1 else float("inf")
    lower=mean-CONFIDENCE_Z*std/(n**.5)
    ret=sel.account_return_pct.to_numpy(float)
    return {"trades":n,"tp_first":int((sel.exit_reason=="target").sum()),
      "tp_first_pct":round(100*(sel.exit_reason=="target").mean(),3),
      "wins":int((sel.net_usd>0).sum()),
      "net_win_pct":round(100*(sel.net_usd>0).mean(),3),
      "net_points_mean":round(mean,3),
      "net_points_lower95":round(lower,3) if np.isfinite(lower) else None,
      "compounded_account_pct":round(float((np.prod(1+ret/100)-1)*100),4),
      "mean_raw_points":round(float(sel.gross_btc_price_points.mean()),3)}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,quality=core.load_1m()
    events,diag=compute_features(f)
    summary=[]
    ledgers={}
    for i,(name,ev) in enumerate(events.items()):
        if len(ev)==0:
            empty=pd.DataFrame(columns=["day_ist","net_usd","btc_equivalent_qty",
                 "exit_reason","account_return_pct","gross_btc_price_points"])
            ledger=empty
        else:
            ledger=core.replay(f,ev)
        ledgers[name]=ledger
        row={"candidate":name,"raw_signal_events":len(ev)}
        for p,(start,end) in WINDOWS.items():
            m=period_metrics(ledger,start,end)
            for k,v in m.items():
                row[p+"_"+k]=v
        summary.append(row)
        print("CANDIDATE_COMPLETE",i+1,len(events),name,
            "train",row["2025_ALL_net_points_mean"],
            "2026H1",row["2026_H1_SEEN_net_points_mean"],
            "2026H2",row["2026_H2_SEEN_net_points_mean"],flush=True)

    df=pd.DataFrame(summary)
    df["train_half_consistent"]=(df["2025_H1_trades"]>=TRAIN_MIN_PER_HALF)&(
      df["2025_H2_trades"]>=TRAIN_MIN_PER_HALF)&(
      df["2025_H1_net_points_mean"].fillna(-1e9)>0)&(
      df["2025_H2_net_points_mean"].fillna(-1e9)>0)
    df["train_qualified"]=df.train_half_consistent&(
      df["2025_ALL_net_points_lower95"].fillna(-1e9)>0)
    # Training period only: ranking must not consult 2026 in any form.
    df["training_score"]=df["2025_ALL_net_points_lower95"].fillna(-1e9)
    df=df.sort_values(["train_qualified","training_score","2025_ALL_trades"],
       ascending=[False,False,False],kind="stable").reset_index(drop=True)
    df["ranking_2025_only"]=np.arange(len(df))+1
    df.to_csv(OUT/"all_predeclared_candidates.csv",index=False)
    qualifying=df.loc[df.train_qualified]
    selected=str(qualifying.iloc[0].candidate) if len(qualifying) else None
    leading=str(df.iloc[0].candidate)
    # Report a 2025-only ranked exploratory leader even if NO strategy qualifies;
    # under NO circumstances call this unqualified leader a selected strategy.
    name_to_audit=selected or leading
    ledger=ledgers[name_to_audit]
    if len(ledger):
        daily,monthly,account=core.summarize(ledger,quality,diag)
        # The reused account simulator defaults to its older model label; correct
        # the metadata to identify the actual candidate being replayed here.
        account["strategy"]=name_to_audit
        ledger.to_csv(OUT/"leader_trades.csv",index=False)
        daily.to_csv(OUT/"leader_daily.csv",index=False)
        monthly.to_csv(OUT/"leader_monthly.csv",index=False)
    else:
        account={}
    leaders=df.head(12)
    periods=["2025_H1","2025_H2","2025_ALL","2026_H1_SEEN","2026_H2_SEEN","ALL"]
    split_tbl=[]
    for _,row in leaders.iterrows():
        for period in periods:
            split_tbl.append({"candidate":row.candidate,"2025_rank":int(row.ranking_2025_only),
              "period":period,"trades":int(row[period+"_trades"]),
              "tp_hit_first":int(row[period+"_tp_first"]),
              "tp_first_pct":row[period+"_tp_first_pct"],
              "net_win_pct":row[period+"_net_win_pct"],
              "mean_net_BTC_points":row[period+"_net_points_mean"],
              "net_account_return_pct":row[period+"_compounded_account_pct"]})
    by_period=pd.DataFrame(split_tbl)
    by_period.to_csv(OUT/"top12_period_checks.csv",index=False)
    notes=[
      "One or fewer trades opened per IST calendar date per independently tested candidate",
      "All strategy candidates use the same fixed 200 raw point TP / 100 raw point SL at 1x and 1m stop-first execution",
      "Regime classification is based ONLY on already closed 1h ADX14 + EMA20/50; no incomplete 1h current candle",
      "Stricter HIGHVOL variant checks completed 1h ATR14 / BTC close >=0.7%",
      "2025 only ranks; 2026 checks are retrospective SEEN historical data due earlier research; NOT untouched validation",
      "No funding, orderbook, bid/ask beyond assumed 5pt slippage, lot feasibility, or mark liquidation",
      "Historical train sample standard-error bound is heuristic and not multiple-testing or serial-dependence adjusted",
      "January 2025 (partial Jan1 IST) and October 2026 (Oct31 IST missing) are incomplete archive-boundary months",
      "No assumption that trading every day or net profit every day is achievable"]
    result={"decision":"QUALIFIED_2025_ONLY_NOT_FORWARD_VALIDATED" if selected else "NO_2025_TRAINING_QUALIFIED_STRATEGY",
      "qualified_candidate_count":len(qualifying),
      "total_predeclared_candidates":len(df),
      "preferred_by_2025_training_if_qualified":selected,
      "exploratory_2025_leader_not_qualified":None if selected else leading,
      "best_2025_candidate_2025_net_mean_points":df.iloc[0]["2025_ALL_net_points_mean"],
      "source_quality":quality,"event_quality":diag,
      "leader_full_1x_account_if_qualified_or_exploratory":account,
      "notes":notes}
    (OUT/"summary.json").write_text(json.dumps(result,indent=2,default=str)+"\n")
    view_cols=["ranking_2025_only","candidate","2025_ALL_trades",
       "2025_ALL_tp_first_pct","2025_ALL_net_win_pct",
       "2025_ALL_net_points_mean","2025_ALL_net_points_lower95",
       "2025_H1_net_points_mean","2025_H2_net_points_mean",
       "2026_H1_SEEN_trades","2026_H1_SEEN_net_points_mean",
       "2026_H2_SEEN_trades","2026_H2_SEEN_net_points_mean",
       "train_qualified"]
    report=[
       "# BTC +200/−100 scalp — causal regime and entry selection, 1× account",
       "",
       "**Decision: "+result["decision"]+"**",
       "",
       "## Rules and market regime",
       "",
       "- Long/short signal after complete 15m close, entry at next 1m OPEN. All 1h EMA20/50, ADX14 and ATR14 are from LAST COMPLETED 1H candle.",
       "- TREND_UP/DOWN: 1h ADX>=25 and EMA20>EMA50, hour close>EMA20 (reverse for short). RANGE: ADX<=18. Other classified hours: TRANSITION.",
       "- 12 predeclared pattern families × high-vol/no-extra-vol-gate plus one fixed 12:00 IST benchmark. No 2026-driven optimization.",
       "- Fixed raw 200 BTC points TP, 100 BTC points SL, 4h max hold or IST day-end, stop-first 1m replay. Full account 1× exposure with 0.05% fee per side and GST18% plus 5 adverse points/side.",
       "- Minimum 30 2025 trades in each half, positive mean after-cost BTC-equivalent points in BOTH halves, and positive normal-style 95%-lower mean bound on 2025 all. Otherwise **NO SELECTED STRATEGY**.",
       "",
       "## Complete-market 2025 and seen-2026 checks",
       "",
       df[view_cols].to_markdown(index=False),
       "",
       "## Top candidates by training-only score — chronological period audits",
       "",
       by_period.to_markdown(index=False),
       "",
       "## Selected candidate or exploratory leader — 1× net-account monthly PnL",
       "",
       "Selected candidate (when qualifying): "+str(selected),
       "",
       "Exploratory leader (not approved when no qualification): "+str(name_to_audit),
       "",
       "### Simulated actual account",
       "",
       pd.DataFrame([account]).drop(columns=[x for x in
           ("data_quality","entry_diagnostics","execution") if x in account],
           errors="ignore").T.to_markdown() if account else "No trades",
       "",
       "### Monthly",
       "",
       monthly.to_markdown(index=False) if account else "No trades",
       "",
       "## Important limits",
       ""
    ]
    report.extend("- "+s for s in notes)
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("FINAL_REGIME_SELECT",json.dumps({k:v for k,v in result.items()
       if k not in ("source_quality","event_quality","notes",
       "leader_full_1x_account_if_qualified_or_exploratory")},default=str))
    print("TOP_CANDIDATES\n"+df[view_cols].head(15).to_string(index=False))
    print("LEADER_ACCOUNT",json.dumps({k:v for k,v in account.items()
       if k not in ("data_quality","entry_diagnostics","execution")},default=str))

if __name__=="__main__": main()
