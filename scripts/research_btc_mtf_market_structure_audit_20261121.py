#!/usr/bin/env python3
"""Describe PRESENT BTCUSD 1H+4H market structure, not future direction.

Frozen rules and audit in analysis/btc_mtf_market_structure_audit_20261121/
NOVELTY_CHECK.md. Never trade on a classification or claim regime 'accuracy'
without independently labelled true market states.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc_regime_attribution_20261121 as base

OUT=Path("analysis/btc_mtf_market_structure_audit_20261121")
OUT.mkdir(parents=True,exist_ok=True)
STATES=["shock","confirmed_trend_up","confirmed_trend_down","breakout_up","breakout_down",
        "transition","compression","range","mixed_uncertain"]
MONTHS=[str(m) for m in pd.period_range("2025-01","2026-10",freq="M")]
CUTOFF=pd.Timestamp("2026-11-01",tz="Asia/Kolkata").tz_convert("UTC")

def features4(one):
    h=one.resample("4h").agg(open=("open","first"),high=("high","max"),
                             low=("low","min"),close=("close","last"))
    count=one.close.resample("4h").count()
    if not count.eq(240).all():
        raise RuntimeError("Partial 4H bar in native 1M history")
    prev=h.close.shift()
    tr=pd.concat([h.high-h.low,(h.high-prev).abs(),(h.low-prev).abs()],axis=1).max(axis=1)
    h["atr"]=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    dh=h.high.diff(); dl=-h.low.diff()
    plus=dh.where((dh>dl)&(dh>0),0.).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    minus=dl.where((dl>dh)&(dl>0),0.).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    h["plus_di"]=100*plus/h.atr
    h["minus_di"]=100*minus/h.atr
    dx=100*(h.plus_di-h.minus_di).abs()/(h.plus_di+h.minus_di).replace(0,np.nan)
    h["adx"]=dx.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    h["ema20"]=h.close.ewm(span=20,adjust=False,min_periods=20).mean()
    h["ema50"]=h.close.ewm(span=50,adjust=False,min_periods=50).mean()
    h["slope2"]=h.ema20-h.ema20.shift(2)
    h["er6"]=(h.close-h.close.shift(6)).abs()/h.close.diff().abs().rolling(6).sum().replace(0,np.nan)
    h["valid"]=np.isfinite(h[["atr","plus_di","minus_di","adx","ema20","ema50","slope2","er6"]].to_numpy(float)).all(axis=1)
    h["available_utc"]=h.index+pd.Timedelta(hours=4)
    return h

def align_complete4(h,h4):
    # 4H rows explicitly stamp their END, not START. Never infer future 4H
    # high/close from a yet-unfinished 4H candle.
    cols=["available_utc","close","atr","adx","plus_di","minus_di","ema20",
          "ema50","slope2","er6","valid"]
    src=h4[cols].copy().rename(columns={"valid":"valid4"})
    src=src.reset_index(drop=True).sort_values("available_utc")
    left=pd.DataFrame({"decision_closed_utc":h.index+pd.Timedelta(hours=1),
                       "i":np.arange(len(h),dtype=int)})
    joined=pd.merge_asof(left,src,left_on="decision_closed_utc",right_on="available_utc",direction="backward")
    if not (joined.loc[joined.available_utc.notna(),"available_utc"]<=
            joined.loc[joined.available_utc.notna(),"decision_closed_utc"]).all():
        raise RuntimeError("4H lookahead occurred")
    result=pd.DataFrame(index=h.index)
    for col in cols:
        result[col]=joined[col].to_numpy()
    return result

def classify(one):
    h=base.features(one)
    h4=features4(one)
    known=align_complete4(h,h4)
    atr=h.atr
    slope=h.ema20-h.ema20.shift(4)
    up1=(h.ema20>h.ema50)&(h.close>h.ema20)&(h.adx>=20)&(h.plus_di>h.minus_di)&(slope>0)&(h.er12>=.22)
    dn1=(h.ema20<h.ema50)&(h.close<h.ema20)&(h.adx>=20)&(h.minus_di>h.plus_di)&(slope<0)&(h.er12>=.22)
    up4=(known.ema20>known.ema50)&(known.close>known.ema20)&(known.adx>=20)&(known.plus_di>known.minus_di)&(known.slope2>0)&(known.er6>=.20)
    dn4=(known.ema20<known.ema50)&(known.close<known.ema20)&(known.adx>=20)&(known.minus_di>known.plus_di)&(known.slope2<0)&(known.er6>=.20)
    valid=(h.valid & known.valid4.eq(True) & np.isfinite(slope))
    if (up1&dn1).any() or (up4&dn4).any():
        raise RuntimeError("Bull and bear trend simultaneous")
    prev=h.close.shift()
    tr=pd.concat([h.high-h.low,(h.high-prev).abs(),(h.low-prev).abs()],axis=1).max(axis=1)
    shock=(tr>2.2*atr)|(h.atr_ratio>=1.8)
    cu=up1&up4
    cd=dn1&dn4
    bu=(h.close>h.hi24)&~(cu|cd)
    bd=(h.close<h.lo24)&~(cu|cd)
    trans=(up1&dn4)|(dn1&up4)
    compress=(h.atr_ratio<=.75)&(h.er12<=.22)&(h.adx<=24)
    rang=(h.adx<=19)&(h.er12<=.35)&((known.ema20-known.ema50).abs()/known.atr<=1.2)
    raw=np.select(
      [shock.fillna(False).to_numpy(),cu.fillna(False).to_numpy(),cd.fillna(False).to_numpy(),
       bu.fillna(False).to_numpy(),bd.fillna(False).to_numpy(),trans.fillna(False).to_numpy(),
       compress.fillna(False).to_numpy(),rang.fillna(False).to_numpy()],
      STATES[:8],default="mixed_uncertain")
    state=np.where(valid.to_numpy(bool),raw,"unclassified")
    hr=pd.DataFrame(index=h.index)
    hr["state"]=state
    hr["valid"]=valid.to_numpy(bool)
    hr["close"]=h.close
    hr["atr"]=atr
    hr["decision_close_utc"]=h.index+pd.Timedelta(hours=1)
    hr["available4_utc"]=known.available_utc
    hr["trend_1h_side"]=np.where(up1,1,np.where(dn1,-1,0))
    hr["trend_4h_side"]=np.where(up4,1,np.where(dn4,-1,0))
    hr["prior24h_net_atr"]=(h.close-h.close.shift(24))/atr
    hr["month_ist"]=hr.decision_close_utc.dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    if not ((hr.state=="unclassified")==~hr.valid).all():
        raise RuntimeError("State warmup/valid mismatch")
    if not hr.loc[hr.valid,"state"].isin(STATES).all():
        raise RuntimeError("Unexpected actionable state")
    if not (hr.loc[hr.valid,"decision_close_utc"]>=hr.loc[hr.valid,"available4_utc"]).all():
        raise RuntimeError("Unfinished 4H data was used")
    return hr

def past_recomputation(one,full):
    checks=[]
    for end in ("2025-05-17T00:00:00Z","2025-12-19T00:00:00Z","2026-08-17T00:00:00Z"):
        cutoff=pd.Timestamp(end)
        hist=classify(one.loc[one.index<cutoff])
        expected=full.loc[hist.index]
        revised=int((hist.state!=expected.state).sum())
        flags=int((hist.valid!=expected.valid).sum())
        if revised or flags:
            raise RuntimeError(f"Repainting at {end}: labels={revised}, validity={flags}")
        checks.append(dict(prefix_exclusive_utc=end,hours=len(hist),
                           revised_state_labels=revised,revised_validity_flags=flags))
    return checks

def results(one,hr,manifest,checks):
    valid=hr.valid & hr.month_ist.isin(MONTHS)
    active=hr.loc[valid].copy()
    n=len(active)
    if n<15000:raise RuntimeError("Too few complete IST months of state coverage")
    share=active.state.value_counts().reindex(STATES,fill_value=0)
    distribution=pd.DataFrame({"state":STATES,"hours":share.to_numpy(int),
                 "share_pct":(100*share/n).round(3).to_numpy()})
    distribution.to_csv(OUT/"market_state_distribution.csv",index=False)
    monthly=pd.crosstab(active.month_ist,active.state).reindex(index=MONTHS,columns=STATES,fill_value=0)
    monthly_percent=monthly.div(monthly.sum(axis=1),axis=0)*100
    monthly_percent.round(4).to_csv(OUT/"monthly_state_percent.csv")
    monthly.to_csv(OUT/"monthly_state_hours.csv")
    yearstate=pd.crosstab(active.index.year,active.state).reindex(columns=STATES,fill_value=0)
    yearstate.to_csv(OUT/"yearly_state_hours.csv")
    running=(active.state!=active.state.shift()).cumsum()
    durations=active.groupby(running).agg(state=("state","first"),hours=("state","size"))
    run_stats=durations.groupby("state").agg(runs=("hours","size"),
       median_consecutive_hours=("hours","median"),mean_consecutive_hours=("hours","mean")).reset_index()
    run_stats.to_csv(OUT/"state_run_lengths.csv",index=False)
    eligible=active[active.state.isin(("confirmed_trend_up","confirmed_trend_down"))].copy()
    expected=np.where(eligible.state=="confirmed_trend_up",1,-1)
    structural=np.where(eligible.prior24h_net_atr>1,1,
                        np.where(eligible.prior24h_net_atr < -1,-1,0))
    reference_defined=structural!=0
    agreement=int(np.sum(structural[reference_defined]==expected[reference_defined]))
    structure_stats=dict(confirmed_hours=len(eligible),
        backward24h_reference_available_hours=int(reference_defined.sum()),
        confirmed_trend_matches_past24h_direction_pct=round(100*agreement/int(reference_defined.sum()),3) if reference_defined.any() else None,
        independent_structure_reference="current completed close minus close 24h earlier / current 1H ATR; if |value|>1, compare direction. Backward-looking price structure only, NOT true market-state accuracy.",
        active_1h_up_hours=int((active.trend_1h_side==1).sum()),
        active_1h_down_hours=int((active.trend_1h_side==-1).sum()),
        active_4h_up_hours=int((active.trend_4h_side==1).sum()),
        active_4h_down_hours=int((active.trend_4h_side==-1).sum()),
        opposing_hourly_and_4h_trends=int(((active.trend_1h_side*active.trend_4h_side)==-1).sum()))
    allhours=hr
    rows=[]
    for period in ("2025","2026"):
        for k in (4,12):
            anchors=np.arange(0,len(allhours)-k,k,dtype=int)
            for state in STATES:
                j=[int(z) for z in anchors if allhours.state.iat[z]==state
                   and allhours.valid.iat[z]
                   and allhours.decision_close_utc.iat[z+k] <= CUTOFF
                   and allhours.index[z].year==int(period)]
                if not j:continue
                future=allhours.close.to_numpy(float)[np.array(j)+k]-allhours.close.to_numpy(float)[j]
                futureatr=future/allhours.atr.to_numpy(float)[j]
                aligned=None
                if state in ("confirmed_trend_up","confirmed_trend_down","breakout_up","breakout_down"):
                    side=1 if state.endswith("_up") else -1
                    aligned=round(float(100*np.mean(future*side>0)),3)
                rows.append(dict(year=period,state=state,horizon_hours=k,
                   nonoverlap_starts=len(j),future_up_pct=round(float(100*np.mean(future>0)),3),
                   future_down_pct=round(float(100*np.mean(future<0)),3),
                   mean_future_return_ATR=round(float(futureatr.mean()),4),
                   same_direction_followthrough_pct=aligned))
    future=pd.DataFrame(rows)
    future.to_csv(OUT/"future_direction_diagnostics.csv",index=False)
    state_changes=100*(active.state!=active.state.shift()).iloc[1:].mean()
    quality=dict(
        source="Delta India BTCUSD native 1M SHA256 checked against manifest",
        native_minute_bars=len(one),native_partitions=len(manifest["partitions"]),
        full_hours=len(hr),complete_ist_months=22,
        eligible_1h_with_known_closed_4h=int(n),
        initial_warmup_unclassified_hours=int((~hr.valid).sum()),
        timestamp_no_gaps=True,all_1h_complete_60m=True,all_4h_complete_240m=True,
        unfinished_4h_used=False,
        source_history_prefix_replays=checks,
        unchanged_prefix_history=all(x["revised_state_labels"]==0 and x["revised_validity_flags"]==0 for x in checks),
        mixed_uncertain_share_pct=round(float(100*(active.state=="mixed_uncertain").mean()),3),
        one_hour_label_switch_pct=round(float(100*state_changes),3),
        **structure_stats,
        external_regime_ground_truth_available=False,
        reliable_future_direction_demonstrated=False,
        strategy_pnl_backtest_performed=False,
        all_months_profitable_target_proved=False)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    active[["state","valid","close","atr","decision_close_utc","available4_utc",
            "trend_1h_side","trend_4h_side","prior24h_net_atr","month_ist"]].to_csv(
           OUT/"hourly_market_state_ledger.csv")
    focus=future[future.state.isin(["confirmed_trend_up","confirmed_trend_down",
                                     "breakout_up","breakout_down","range","mixed_uncertain"])]
    lines=[
      "# BTC 1H+4H market-state detector: present-state vs future-direction audit",
      "",
      "## Precisely what is fixed",
      "A trend is a measurable CURRENT market structure, not a forecast that every future 1H/4H close will continue up/down. This detector waits for the last completed 4H candle, requires alignment with a finished 1H signal, and leaves uncertain regimes explicitly unconfirmed. It distinguishes confirmed trend, breakout, shock, transition, compression, range and mixed markets; it does NOT force future direction trades.",
      "",
      "## Quality checks","~~~json",json.dumps(quality,indent=2),"~~~","",
      "## State shares across all 22 complete IST months",
      distribution.to_markdown(index=False),"",
      "## How quickly each state changes",
      run_stats.round(3).to_markdown(index=False),"",
      "## Year-specific trend and future continuation diagnostic (NOT ground-truth state accuracy)",
      focus.to_markdown(index=False),"",
      "## Separate classification from profitable execution",
      "A 4H trend confirmation is available only after its 4H bar has closed; the last 1H bar may enter a countertrend retracement while the 4H trend persists. State alignment with a past 24H directional price reference is a retrospective observation, NOT knowledge of what the next 4H candle will do.",
      "No strategy trade was backtested here. Matching current structure does not establish directional edge or 22/22 profitable months. The existing models' after-cost PnL and forecasting failures remain valid unless new independent evidence contradicts them.",
      "",
      "## Missing live-readiness inputs",
      "Unobserved true market regime labels; historical L1/L2 order book and actual spread; funding cash settlements; margin/liquidation/exchange fill feasibility. No live strategy deployment and no main-branch merge.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("QUALITY",json.dumps(quality))
    print("DISTRIBUTION")
    print(distribution.to_string(index=False))
    print("CONFIRMED_TREND_FUTURE_DIAGNOSTICS")
    print(future[future.state.isin(["confirmed_trend_up","confirmed_trend_down"])].to_string(index=False))
    print("DONE")

def main():
    one,manifest=base.load()
    full=classify(one)
    checks=past_recomputation(one,full)
    results(one,full,manifest,checks)

if __name__=="__main__":
    main()
