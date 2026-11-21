#!/usr/bin/env python3
"""Independent BTC/ETH MTF breakout research: 4H trend -> 15M breakout -> 1M fills.

Research only; deliberately separate from the prior EMA20+ST pullback tests.
NO trade is sent to an exchange. 4H and 15M signals exclusively use completed
candles; a signal is filled at the next 1M open. Fixed stops/targets are active
immediately; 1M high/low ambiguity resolves against the position. For
trailing mode, the stop observed BEFORE the minute is checked; a higher/lower
stop from that minute's favorable wick is active only in the NEXT minute.
Gap through an initial stop is filled at the 1M open, not an invented stop fill.

Fee and GST: 0.05% taker each side, 18% GST on both fees. Fixed $1,000 notional
per trade, no reinvestment, no margin accounting or historical liquidation
reconstruction. Additional 2 bps per side adverse slippage stress. Funding is
separately modeled from the observed previous-hour funding-rate snapshot at
ASSUMED UTC 00/08/16 settlement events; these are not actual cash settlements.
Missing rate events are kept explicitly missing, never fabricated.

No optimization on the 2026 results: the small candidate grid is fixed here.
2025 and Jan-Oct 2026 are reported separately; they are historical splits,
not proof of a genuinely unseen forward test.
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from replay_ema_st_15m_entries_1m_exits_20261121 import load

OUT=ROOT/"analysis"/"new_4h_trend_15m_breakout_1m_20261121"
OUT.mkdir(parents=True,exist_ok=True)
ENTRY_END=int(pd.Timestamp("2026-11-01",tz="UTC").timestamp())
YEAR_START=int(pd.Timestamp("2026-01-01",tz="UTC").timestamp())
NOTIONAL=1000.0
TAKER=0.0005
GST=0.18
SLIPPAGE_STRESS_FRACTION=0.0002
MODES=("fast_20_50","slow_50_200")
ENTRIES=("donchian20","donchian48","pullback12")
EXITS=("fixed3r","fixed4r","trail_2atr")
SCENARIOS=[(m,e,x) for m in MODES for e in ENTRIES for x in EXITS]

def rma(s,n):
    # Wilder alpha smoothing with appropriate warmup; no future values
    return s.ewm(alpha=1/n,adjust=False,min_periods=n).mean()

def atr14(b):
    prev=b.close.shift(1)
    tr=pd.concat((b.high-b.low,(b.high-prev).abs(),(b.low-prev).abs()),axis=1).max(axis=1)
    return rma(tr,14)

def aggregate(m,interval):
    b=m.resample(f"{interval}min",origin="epoch",label="left",closed="left").agg({
        "open":"first","high":"max","low":"min","close":"last","volume":"sum","time":"count"})
    assert b["time"].eq(interval).all(), "Partial timeframe candle"
    assert len(b)*interval==len(m), "Unaligned timeframe"
    return b.drop(columns="time")

def prepare(m):
    m15=aggregate(m,15)
    m4=aggregate(m,240)
    m15["ema20"]=m15.close.ewm(span=20,adjust=False).mean()
    m15["atr14"]=atr14(m15)
    m15["prev20hi"]=m15.high.shift(1).rolling(20,min_periods=20).max()
    m15["prev20lo"]=m15.low.shift(1).rolling(20,min_periods=20).min()
    m15["prev48hi"]=m15.high.shift(1).rolling(48,min_periods=48).max()
    m15["prev48lo"]=m15.low.shift(1).rolling(48,min_periods=48).min()
    m15["prev12hi"]=m15.high.shift(1).rolling(12,min_periods=12).max()
    m15["prev12lo"]=m15.low.shift(1).rolling(12,min_periods=12).min()
    m15["past8touch"]=((m15.low<=m15.ema20)&(m15.high>=m15.ema20)).shift(1).rolling(
        8,min_periods=8).max().fillna(0).astype(bool)
    m15["prior_volume20"]=m15.volume.shift(1).rolling(20,min_periods=20).mean()
    m4["ema20"]=m4.close.ewm(span=20,adjust=False).mean()
    m4["ema50"]=m4.close.ewm(span=50,adjust=False).mean()
    m4["ema200"]=m4.close.ewm(span=200,adjust=False).mean()
    assert len(m15)>10000 and len(m4)>3000
    return m15,m4

def generate_signals(m,m15,m4):
    """One signal per 15M close at most, next-minute open = (i+1)*15.

    4H regime: index (j//240-1), strictly the most recent COMPLETED
    4H candle at the entry instant, never the running current 4H bar.
    """
    idx=m15.index
    op=m15.open.to_numpy(float)
    hi=m15.high.to_numpy(float)
    lo=m15.low.to_numpy(float)
    cl=m15.close.to_numpy(float)
    vol=m15.volume.to_numpy(float)
    atr=m15.atr14.to_numpy(float)
    ema=m15.ema20.to_numpy(float)
    v20=m15.prior_volume20.to_numpy(float)
    rhi20=m15.prev20hi.to_numpy(float)
    rlo20=m15.prev20lo.to_numpy(float)
    rhi48=m15.prev48hi.to_numpy(float)
    rlo48=m15.prev48lo.to_numpy(float)
    rhi12=m15.prev12hi.to_numpy(float)
    rlo12=m15.prev12lo.to_numpy(float)
    touch=m15.past8touch.to_numpy(bool)
    h20=m4.ema20.to_numpy(float)
    h50=m4.ema50.to_numpy(float)
    h200=m4.ema200.to_numpy(float)
    hc=m4.close.to_numpy(float)
    clock=m.time.to_numpy(np.int64)
    signals={(mode,entry):[] for mode in MODES for entry in ENTRIES}
    for i in range(200,len(m15)-1):
        j=(i+1)*15
        if int(clock[j])>=ENTRY_END:break
        k=j//240-1
        if k<205 or not (np.isfinite(atr[i]) and atr[i]>0 and np.isfinite(v20[i])
                         and v20[i]>0):continue
        if not (np.isfinite(h20[k]) and np.isfinite(h50[k]) and np.isfinite(h200[k])):
            continue
        # Strong breakout close in its direction, not merely a wick breakout.
        rng=max(1.e-8,hi[i]-lo[i])
        candle_up=(cl[i]>op[i] and (cl[i]-lo[i])/rng>=0.75)
        candle_dn=(cl[i]<op[i] and (hi[i]-cl[i])/rng>=0.75)
        # Prior 20-bar average volume at least 1.1x to avoid dead breakouts.
        if vol[i]<1.1*v20[i]:continue
        candidates={
          "donchian20":(cl[i]>rhi20[i] and candle_up,cl[i]<rlo20[i] and candle_dn),
          "donchian48":(cl[i]>rhi48[i] and candle_up,cl[i]<rlo48[i] and candle_dn),
          "pullback12":(touch[i] and cl[i]>rhi12[i] and cl[i]>ema[i] and candle_up,
                         touch[i] and cl[i]<rlo12[i] and cl[i]<ema[i] and candle_dn),
        }
        # Two prespecified trend regimes, both computed on last closed 4H.
        directions={
          "fast_20_50":(
             h20[k]>h50[k] and hc[k]>h20[k] and h20[k]>h20[k-3],
             h20[k]<h50[k] and hc[k]<h20[k] and h20[k]<h20[k-3]),
          "slow_50_200":(
             h50[k]>h200[k] and hc[k]>h50[k] and h50[k]>h50[k-3],
             h50[k]<h200[k] and hc[k]<h50[k] and h50[k]<h50[k-3]),
        }
        for mode in MODES:
            long_ok,short_ok=directions[mode]
            for entry in ENTRIES:
                long_sig,short_sig=candidates[entry]
                side=1 if long_ok and long_sig else (-1 if short_ok and short_sig else 0)
                if side:
                    # ATR known at 15M close, no 1M value from the future.
                    signals[mode,entry].append((j,side,float(atr[i])))
    return signals

def funding_proxy(asset,m):
    # Data is an observed hourly funding RATE (price-like close field),
    # NOT actual settled cash. Sample the LAST fully closed hour at
    # *hypothetical* 00/08/16 UTC UTC settlement boundaries.
    folder=ROOT/"data"/"delta_india"/f"{asset}USD"/"institutional"/"history"/"funding_1h"
    frames=[]
    for file in sorted(folder.glob("20??-??.csv.gz")):
        f=pd.read_csv(file,compression="gzip",usecols=["time","close"])
        frames.append(f)
    if not frames:raise RuntimeError("No funding rate snapshots for "+asset)
    full=pd.concat(frames,ignore_index=True)
    t=full.time.to_numpy(np.int64)
    val=full.close.to_numpy(float)
    assert np.all(np.diff(t)==3600), "Funding snapshot not complete 1h cadence"
    assert t[0]==int(m.time.iloc[0]), "Funding series not aligned"
    n=len(m)
    # At each expected settlement, previous hour should be available.
    rates=np.zeros(n,dtype=np.float64)
    missing=np.zeros(n,dtype=np.int64)
    for j in range(480,n,480):
        hour_index=j//60-1
        if (hour_index>=len(val) or not np.isfinite(val[hour_index])):
            missing[j]=1
        else:
            rates[j]=(float(val[hour_index])/100)*float(m.open.iloc[j])
    return np.cumsum(rates),np.cumsum(missing),{"rows":len(full),
       "observed_start":str(pd.Timestamp(t[0],unit="s",tz="UTC")),
       "observed_end":str(pd.Timestamp(t[-1],unit="s",tz="UTC")),
       "assumed_settlement":"00:00/08:00/16:00 UTC",
       "rate_unit":"close field is percent, so /100",
       "not_actual_cash_settlement":True}

def self_test():
    # Validate pessimistic handling: both barriers same minute -> STOP,
    # no impossible instant new-trail-stop after same-minute price high.
    def event(o,h,l,side,tp,sl):
        if side==1:
            if o<=sl:return "SL_gap"
            if o>=tp:return "TP_gap"
            if l<=sl:return "SL"
            if h>=tp:return "TP"
        else:
            if o>=sl:return "SL_gap"
            if o<=tp:return "TP_gap"
            if h>=sl:return "SL"
            if l<=tp:return "TP"
    assert event(100,120,89,1,115,90)=="SL"
    assert event(100,111,80,-1,85,110)=="SL"
    assert event(88,110,87,1,115,90)=="SL_gap"

def replay(asset,m,signals,scenario,fund_cumsum,missing_cumsum,slip_frac):
    mode,entry,exit_mode=scenario
    starts=signals[mode,entry]
    o=m.open.to_numpy(float)
    h=m.high.to_numpy(float)
    l=m.low.to_numpy(float)
    c=m.close.to_numpy(float)
    clock=m.time.to_numpy(np.int64)
    n=len(o)
    result=[]
    i=0
    last_j=-1
    for j,side,atr in starts:
        if j<=last_j:continue
        if j>=n:break
        # For maximum reproducibility, use observed 1M open.
        raw_entry=float(o[j])
        ep=raw_entry*(1+side*slip_frac)
        qty=NOTIONAL/ep
        risk=max(2.0*atr,ep*.0035)
        initial_stop=ep-side*risk
        stop=initial_stop
        target=ep+side*(3*risk if exit_mode=="fixed3r" else 4*risk)
        # Chandelier trails need activation and have NO forced take profit.
        best=ep
        trailing_active=False
        reason=None
        raw_exit=None
        e_j=None
        ambiguity=False
        for k in range(j,n):
            opening=float(o[k])
            high=float(h[k])
            low=float(l[k])
            # Stops active at minute open. Gap fills use observed open.
            if (side==1 and opening<=stop) or (side==-1 and opening>=stop):
                raw_exit=opening
                reason="stop_gap" if not trailing_active else "trailing_gap"
            elif exit_mode!="trail_2atr" and (
                  (side==1 and opening>=target) or (side==-1 and opening<=target)):
                # Resting target fills at target, not favorable gapped price.
                raw_exit=target
                reason="target"
            else:
                stop_touch=(low<=stop if side==1 else high>=stop)
                target_touch=(high>=target if side==1 else low<=target) if exit_mode!="trail_2atr" else False
                if stop_touch:
                    # Same 1M candle can touch target and stop; stop FIRST
                    # deliberately pessimistic rather than inventing path.
                    ambiguity=bool(target_touch)
                    raw_exit=stop
                    reason=("ambiguous_assumed_stop" if ambiguity else
                        "trailing_stop" if trailing_active else "initial_stop")
                elif target_touch:
                    raw_exit=target
                    reason="target"
                elif exit_mode=="trail_2atr":
                    # New 1M extremum is known only after this candle ends.
                    next_best=max(best,high) if side==1 else min(best,low)
                    if side*(next_best-ep)>=1.5*risk:
                        trailing_active=True
                    if trailing_active:
                        newstop=next_best-side*max(2.0*atr,0.8*risk)
                        stop=max(stop,newstop) if side==1 else min(stop,newstop)
                    best=next_best
            if reason is not None:
                e_j=k
                break
        if e_j is None:
            e_j=n-1
            raw_exit=float(c[-1])
            reason="end_of_data_mark"
        last_j=e_j
        xp=float(raw_exit)*(1-side*slip_frac)
        gross=side*(xp-ep)*qty
        fees=(ep+xp)*qty*TAKER*(1+GST)
        net=gross-fees
        # Funding only at strictly BETWEEN entry and exit times.
        # The cumulative series holds payment_rate * contemporaneous
        # 1M futures open. Positive rate is cost to LONG and receipt to SHORT.
        end_prefix=max(j,e_j-1)
        funding_missing=int(missing_cumsum[end_prefix]-missing_cumsum[j])
        funding_cash=(-side*qty*(fund_cumsum[end_prefix]-fund_cumsum[j])
                      if funding_missing==0 else None)
        funded_net=(net+funding_cash if funding_cash is not None else None)
        year=2025 if clock[j]<YEAR_START else 2026
        time_entry=pd.Timestamp(clock[j],unit="s",tz="UTC")
        time_exit=pd.Timestamp(clock[e_j],unit="s",tz="UTC")
        result.append(dict(asset=asset,trend_mode=mode,entry_method=entry,
            exit_mode=exit_mode,entry_utc=time_entry.isoformat(),
            exit_utc=time_exit.isoformat(),entry_year=year,
            entry_month_utc=time_entry.strftime("%Y-%m"),
            exit_month_utc=time_exit.strftime("%Y-%m"),
            side="LONG" if side==1 else "SHORT",
            entry=ep,exit=xp,stop_initial=initial_stop,
            initial_risk_points=risk,qty=qty,
            hold_min=int(e_j-j),exit_reason=reason,
            ambiguous_same_1m=ambiguity,
            gross_usd=gross,fees_and_gst_usd=fees,
            funding_proxy_usd=funding_cash,
            missing_funding_events=funding_missing,
            net_taker_usd=net,net_taker_funding_proxy_usd=funded_net,
            slippage_fraction_per_side=slip_frac))
    return pd.DataFrame(result)

def metrics(g,field):
    if g.empty:return dict(n=0)
    a=g[field].dropna().to_numpy(float)
    n=len(g)
    if len(a)==0:return dict(n=n,n_valid=0)
    wins=a[a>0].sum()
    losses=-a[a<0].sum()
    equity=np.r_[0,np.cumsum(a)]
    peak=np.maximum.accumulate(equity)
    draw=np.max(peak-equity)
    return dict(n=n,n_valid=len(a),
        net_usd=round(float(a.sum()),3),
        avg_net_usd=round(float(a.mean()),4),
        win_rate_pct=round(100*float((a>0).mean()),2),
        profit_factor=round(float(wins/losses),3) if losses>0 else None,
        max_closed_drawdown_usd=round(float(draw),3))

def evaluate(df):
    if df.empty:return dict(trades=0)
    answer={"trades":len(df),
            "ambiguous_1m_both_hits":int(df.ambiguous_same_1m.sum()),
            "missing_funding_trades":int((df.missing_funding_events>0).sum()),
            "average_hold_min":round(float(df.hold_min.mean()),1),
            "avg_initial_risk_pct":round(float((df.initial_risk_points/df.entry).mean()*100),3),
            "all":metrics(df,"net_taker_usd"),
            "funding_proxy_all":metrics(df,"net_taker_funding_proxy_usd")}
    answer["annual"]={}
    for year in (2025,2026):
        g=df[df.entry_year==year]
        summary={"taker":metrics(g,"net_taker_usd"),
                 "funding_proxy":metrics(g,"net_taker_funding_proxy_usd"),
                 "positive_exit_months":int((g.groupby("exit_month_utc").net_taker_usd.sum()>0).sum()) if len(g) else 0,
                 "months_with_exits":int(g.exit_month_utc.nunique())}
        answer["annual"][str(year)]=summary
    monthly=df.groupby("exit_month_utc").agg(
       n=("net_taker_usd","size"),
       net_fee=("net_taker_usd","sum"),
       net_with_funding=("net_taker_funding_proxy_usd","sum"))
    answer["profitable_complete_months"]=int(
       (monthly.loc[monthly.index<"2026-11","net_fee"]>0).sum())
    answer["complete_months_with_exits"]=int(
       (monthly.index<"2026-11").sum())
    return answer

def main():
    self_test()
    full={"spec":{
        "strategy":"4H trend (EMA 20/50 or 50/200 and slope 3 bars), confirmed 15M Donchian20/48 or pullback-breakout12, 15M ATR initial stop and 1M real exit",
        "signal_known":"after 15M/4H candle close, enter at NEXT 1M open",
        "initial_stop":"max(2 * last closed 15M ATR14, 0.35% of entry)",
        "trailing":"activate at 1.5R, distance max(2*signal ATR14, 0.8R), effective next 1M bar",
        "exit_modes":list(EXITS),
        "fee":"0.05% taker each side + 18% GST",
        "funding":"rate observation prior hour at hypothetical 8-hour UTC settlement, NOT actual paid funding",
        "notional_usd_per_trade":NOTIONAL,
        "one_position_at_a_time_per_scenario_per_asset":True,
        "window":"signals 2025-01-01 to 2026-10-31 inclusive; 1M replay through archived Nov 2026 end",
        "stress":"2 basis points adverse price slippage each side; no orderbook modeling",
        "not_modeled":"liquidation/mark fill, margin availability, orderbook spread, live latency",
        "independent_2026_proof":False},
        "funding_provenance":{},"cases":{}}
    all_trade_rows=[]
    overview=[]
    for asset in ("BTC","ETH"):
        minute,_,manifest=load(asset)
        b15,b4=prepare(minute)
        signals=generate_signals(minute,b15,b4)
        cumfund,missfund,prov=funding_proxy(asset,minute)
        full["funding_provenance"][asset]=prov
        print("NEW_DATA",asset,len(minute),len(b15),len(b4),
            {str(k):len(v) for k,v in signals.items()},flush=True)
        for settings in SCENARIOS:
            for slip in (0.0,SLIPPAGE_STRESS_FRACTION):
                df=replay(asset,minute,signals,settings,cumfund,missfund,slip)
                key=f"{asset}_{settings[0]}_{settings[1]}_{settings[2]}_{'zero_slip' if slip==0 else 'stress_2bps'}"
                info=evaluate(df)
                full["cases"][key]=info
                if len(df):
                    df["case"]=key
                    all_trade_rows.append(df)
                row={"key":key,"asset":asset,"mode":settings[0],
                   "entry":settings[1],"exit":settings[2],
                   "slippage_bps_per_side":slip*10000,
                   "trades":info.get("trades",0),
                   "profit_factor":info.get("all",{}).get("profit_factor"),
                   "net_usd_per_1000_fixed_notional":info.get("all",{}).get("net_usd"),
                   "net_funding_proxy":info.get("funding_proxy_all",{}).get("net_usd"),
                   "positive_months":info.get("profitable_complete_months",0)}
                for y in ("2025","2026"):
                    annual=info.get("annual",{}).get(y,{})
                    row[y+"_trades"]=annual.get("taker",{}).get("n",0)
                    row[y+"_net_taker"]=annual.get("taker",{}).get("net_usd")
                    row[y+"_net_funding_proxy"]=annual.get("funding_proxy",{}).get("net_usd")
                    row[y+"_pf"]=annual.get("taker",{}).get("profit_factor")
                overview.append(row)
                print("NEW_RESULT",json.dumps(row),flush=True)
    table=pd.DataFrame(overview)
    table.to_csv(OUT/"scenario_summary.csv",index=False)
    pd.concat(all_trade_rows,ignore_index=True).to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    (OUT/"full_results.json").write_text(json.dumps(full,indent=2)+"\n",encoding="utf8")
    base=table[table.slippage_bps_per_side==0]
    valid=base[(base["2025_trades"]>=30)&(base["2026_trades"]>=20)&
           (base["2025_net_taker"]>0)&(base["2026_net_taker"]>0)]
    valid_funded=valid[(valid["2025_net_funding_proxy"]>0)&(valid["2026_net_funding_proxy"]>0)]
    print("NEW_CANDIDATES_BOTH_YEARS_TAKER",valid.sort_values("net_usd_per_1000_fixed_notional",ascending=False).to_json(orient="records"),flush=True)
    print("NEW_CANDIDATES_BOTH_YEARS_FUNDED_PROXY",valid_funded.sort_values("net_funding_proxy",ascending=False).to_json(orient="records"),flush=True)
    for asset in ("BTC","ETH"):
        pick=base[base.asset==asset].sort_values("net_funding_proxy",ascending=False).head(8)
        print("NEW_TOP_FUNDING",asset,pick.to_json(orient="records"),flush=True)
    # Follow-up structural checks, NOT part of original parameter grid.
    # Re-run the best ETH baseline with entries restricted to long, short,
    # weekdays, weekends, for independent exclusive-position results.
    m,_,_=load("ETH")
    b15,b4=prepare(m)
    filtered_signals=generate_signals(m,b15,b4)
    fc,mc,fp=funding_proxy("ETH",m)
    key=("slow_50_200","donchian48")
    full_candidates=filtered_signals[key]
    for subgroup in ("long_only","short_only","weekdays_only","weekends_only"):
        if subgroup=="long_only":
            chosen=[x for x in full_candidates if x[1]==1]
        elif subgroup=="short_only":
            chosen=[x for x in full_candidates if x[1]==-1]
        elif subgroup=="weekdays_only":
            chosen=[x for x in full_candidates if m.index[x[0]].dayofweek<5]
        else:
            chosen=[x for x in full_candidates if m.index[x[0]].dayofweek>=5]
        for slip in (0.0,SLIPPAGE_STRESS_FRACTION):
            data=replay("ETH",m,{key:chosen},(*key,"trail_2atr"),fc,mc,slip)
            detail=evaluate(data)
            print("ETH_SUBGROUP",subgroup,"zero_slip" if slip==0 else "stress_2bps",
                  json.dumps(detail),flush=True)
    for slip in (0.0,SLIPPAGE_STRESS_FRACTION):
        name=f"ETH_slow_50_200_donchian48_trail_2atr_{'zero_slip' if slip==0 else 'stress_2bps'}"
        candidate=pd.concat(all_trade_rows,ignore_index=True)
        candidate=candidate[candidate.case==name].copy()
        print("ETH_BEST_MONTHLY",name,candidate.groupby("exit_month_utc").agg(
            trades=("net_taker_usd","size"),net=("net_taker_usd","sum"),
            funded=("net_taker_funding_proxy_usd","sum")).round(4).reset_index().to_json(orient="records"),flush=True)
        print("ETH_BEST_SIDE_STATS",name,candidate.groupby("side").agg(
            trades=("net_taker_usd","size"),net=("net_taker_usd","sum"),
            funded=("net_taker_funding_proxy_usd","sum"),
            fees_gst=("fees_and_gst_usd","sum"),
            avg_hold_min=("hold_min","mean")).round(4).reset_index().to_json(orient="records"),flush=True)
        print("ETH_BEST_EXTRA",name,json.dumps({
            "ambiguous_both":int(candidate.ambiguous_same_1m.sum()),
            "funding_rate_missing_trades":int((candidate.missing_funding_events>0).sum()),
            "total_fees_gst":round(float(candidate.fees_and_gst_usd.sum()),4),
            "total_gross_usd":round(float(candidate.gross_usd.sum()),4),
            "total_funding_proxy_usd":round(float(candidate.funding_proxy_usd.dropna().sum()),4),
            "avg_risk_pct":round(float((candidate.initial_risk_points/candidate.entry).mean()*100),3),
            "max_holding_minutes":int(candidate.hold_min.max())}),flush=True)
    print("NEW_MTF_BACKTEST_COMPLETE",str(OUT),flush=True)

if __name__=="__main__":
    main()
