#!/usr/bin/env python3
"""BTCUSD Supertrend locked V1.0: independent monthly-win exits for each leg.

Treat each of the two legs *separately* in a shared one-position portfolio:
Line Touch locked at 1% activation / +.4% profit lock, SL .75% TP 1.5%,
and Bullish Flip original SL 3% TP .5%.
Test TOUCH exit adjustments with FLIP unchanged and FLIP adjustments with
TOUCH unchanged. Rank ONLY after checking:
* each previously profitable calendar month of the altered strategy has
  >= original month PnL (small 2c rounding tolerance);
* original leg's total PnL is preserved, and
* each originally profitable month of the combined portfolio retains PnL.
Allow neither profit-month reduction nor lower net total. Track months
with no trades separately; do not count them as wins.

Entire 2025-Jan to 2026-Oct is historical model-development data, NOT OOS.
Only last fully closed 1-minute high can activate lock/trailing protection.
Historical 1m OHLC ambiguous stop+TP is resolved stop-first.
"""
from pathlib import Path
from functools import lru_cache
import json
import numpy as np
import pandas as pd
import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as feat
import research_st_three_best_combined_portfolio as portfolio
import research_st_touch075_flip_lowvol_combination as original
import research_st_touch_flip_causal_regime_filters as htf
import research_st_touch_flip_reduce_loss_months as study
import research_second_green_percent_rr_scenarios as rr

OUT=Path("analysis/st_v1_separate_monthly_win_exits_20261124")
MONTHS=tuple(base.MONTHS)
def side(sl,tp,mode="off",arm=0.,value=0.,cap=0):
    return (float(sl),float(tp),str(mode),float(arm),float(value),int(cap))
TOUCH=side(.75,1.5,"lock",1.,.4)
FLIP=side(3.,.5)

def variants():
    t={"baseline":TOUCH}
    f={"baseline":FLIP}
    for sl in (.2,.3,.4,.5,.6,.75,.9,1.,1.25):
        for tp in (.75,1.,1.25,1.5,1.75,2.,2.5,3.):
            t[f"SL_{sl}_TP_{tp}"]=side(sl,tp,"lock",1.,.4)
    for sl in (.35,.5,.6,.75,1.):
      for arm in (.6,.8,1.,1.2,1.4):
       for lock in (.1,.2,.3,.4,.5,.6,.8):
        if lock>=arm:continue
        t[f"SL_{sl}_lock_{arm}_{lock}"]=side(sl,1.5,"lock",arm,lock)
    for arm in (.4,.6,.8,1.,1.2,1.4):
      for trail in (.15,.25,.35,.45,.55,.7,.9):
        t[f"trail_{arm}_{trail}"]=side(.75,1.5,"trail",arm,trail)
    for cap in (15,30,45,60,90,120,180,240,360,480,720,960):
        t[f"max_minutes_{cap}"]=side(.75,1.5,"lock",1.,.4,cap)

    for sl in (.2,.3,.4,.5,.6,.75,1.,1.25,1.5,2.,2.5,3.):
      for tp in (.2,.25,.3,.35,.4,.45,.5,.6,.75,1.,1.25,1.5,2.):
        f[f"SL_{sl}_TP_{tp}"]=side(sl,tp)
    for arm in (.1,.15,.2,.25,.3,.35,.4,.45,.5,.6,.75,1.):
      for lock in (0.,.025,.05,.075,.1,.15,.2,.25,.3,.4):
        if lock>=arm:continue
        f[f"lock_{arm}_{lock}"]=side(3.,.5,"lock",arm,lock)
    for arm in (.1,.15,.2,.25,.35,.4,.5,.6,1.):
      for trail in (.08,.12,.2,.25,.35,.45,.6):
        f[f"trail_{arm}_{trail}"]=side(3.,.5,"trail",arm,trail)
    for cap in (15,30,45,60,90,120,180,240,360,480,720,960):
        f[f"max_minutes_{cap}"]=side(3.,.5,"off",0,0,cap)
    return t,f

def mvec(ledger,name=None):
    if name is not None:ledger=ledger[ledger.strategy==name]
    s=ledger.groupby("exit_month_ist").net_pts.sum()
    return np.array([float(s.get(month,0)) for month in MONTHS])

def validate_months(new,reference):
    positive=reference>0.001
    drops=(positive & (new+0.035<reference))
    new_positive=int(np.count_nonzero(new>0.001))
    return dict(
     wins=new_positive,losses=int(np.count_nonzero(new<-.001)),
     flat=int(np.count_nonzero(abs(new)<=.001)),
     old_profit_months_non_degraded=int(np.count_nonzero(positive & ~drops)),
     old_profit_months_total=int(np.count_nonzero(positive)),
     old_profit_months_degraded=int(drops.sum()),
     total=round(float(new.sum()),2),
     total_delta=round(float(new.sum()-reference.sum()),2),
     losses_to_positive=int(np.count_nonzero((reference<-.001)&(new>.001))),
     losses_to_flat=int(np.count_nonzero((reference<-.001)&(abs(new)<=.001))),
     worst_month=round(float(new.min()),2))

def main():
    rr.configure_grid()
    portfolio.SPECS=original.COHORTS
    OUT.mkdir(parents=True,exist_ok=True)
    minute,bars,files=base.load()
    st,trend=base.supertrend(bars)
    vol,atrpct,atrel=feat.build_features(bars)
    ev,stopbars=feat.candidate_touch_events(
        minute,bars,st,trend,vol,atrpct,atrel)
    signals=portfolio.decode_signals(
        minute,bars,trend,vol,atrpct,atrel,ev,stopbars)
    cand=portfolio.compute_candidates(minute,trend,stopbars,signals)
    assert len(cand)==150
    ff=htf.features(bars,trend)
    entry_bar=cand.entry_bar.to_numpy(int)
    is_touch=(cand.strategy=="line_touch").to_numpy()
    mask=(is_touch&ff["1h_above_ema20_and_rising"].to_numpy(bool)[entry_bar])|(
          (~is_touch)&ff["1h_rsi50"].to_numpy(bool)[entry_bar])
    cand=cand[mask].copy().reset_index(drop=True)
    assert len(cand)==87
    op=minute.open.to_numpy(float)
    hi=minute.high.to_numpy(float)
    lo=minute.low.to_numpy(float)
    cl=minute.close.to_numpy(float)
    mminute=minute.index.tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
    n=len(hi)
    ctxs=[]
    for c in cand.itertuples():
        j=int(c.entry_idx)
        k=np.searchsorted(stopbars,int(c.entry_bar),side="left")
        end=min((int(stopbars[k])+1)*15,n) if k<len(stopbars) else n
        assert 0<=j<end<=n
        highs=hi[j:end]
        prevpeak=np.r_[-np.inf,np.maximum.accumulate(highs[:-1])]
        ctxs.append(dict(j=j,end=end,hi=highs,
          lo=lo[j:end],op=op[j:end],prevpeak=prevpeak,
          entry=float(c.entry_fill)))
    @lru_cache(maxsize=None)
    def replay(i,params):
        sl,tp,mode,arm,value,cap=params
        c=ctxs[i]
        j=c["j"];end=min(c["end"],j+cap) if cap else c["end"]
        t=end-j
        h=c["hi"][:t];l=c["lo"][:t];o=c["op"][:t]
        old=c["prevpeak"][:t]
        entry=c["entry"]
        static=entry*(1.-sl/100.)
        goal=entry*(1.+tp/100.)
        if mode=="off":stop=np.full(t,static)
        else:
            eligible=old>=entry*(1.+arm/100.)
            if mode=="lock":protection=np.full(t,entry*(1.+value/100.))
            elif mode=="trail":protection=old-entry*value/100.
            else:raise ValueError(mode)
            stop=np.where(eligible,np.maximum(static,protection),static)
        stophit=l<=stop
        targethit=h>=goal
        hit=np.flatnonzero(stophit|targethit)
        if len(hit):
            at=int(hit[0])
            idx=j+at
            mid=min(o[at],stop[at]) if stophit[at] else goal
            reason=("protective_stop" if stophit[at] and stop[at]>static+1e-7
                     else "stop" if stophit[at] else "target")
        elif end<n:
            idx=end;mid=op[end]
            reason="time_cap" if end<c["end"] else "original_ST_close"
        else:
            idx=n-1;mid=cl[-1];reason="archive_end"
        fill=mid-base.SLIP
        net=fill-entry-base.FEE*(entry+fill)
        return idx,float(mid),float(fill),float(net),reason
    def build(touch,flip):
        rows=[]
        for i,v in enumerate(cand.itertuples()):
            params=touch if v.strategy=="line_touch" else flip
            ix,mid,fill,net,reason=replay(i,params)
            d=v._asdict()
            d.update(exit_idx=ix,exit_utc=str(minute.index[ix]),
             exit_month_ist=str(mminute[ix]),exit_mid=mid,
             exit_fill=fill,fee_pts=base.FEE*(float(v.entry_fill)+fill),
             net_pts=net,win=int(net>0),reason=reason,
             holding_minutes=ix-int(v.entry_idx))
            rows.append(d)
        df=pd.DataFrame(rows)
        kept,blocked=portfolio.portfolio(df,
               ("line_touch","bullish_flip"),
               ("line_touch","bullish_flip"),global_cycle_cap=True)
        return kept,blocked

    base_ledger,_=build(TOUCH,FLIP)
    ref={k:mvec(base_ledger,k) for k in ("line_touch","bullish_flip")}
    ref["combined"]=mvec(base_ledger)
    assert len(base_ledger)==85
    assert abs(float(ref["combined"].sum())-19099.62)<.035
    assert abs(float(ref["line_touch"].sum())-13816.06)<.035
    assert abs(float(ref["bullish_flip"].sum())-5283.56)<.035
    assert (sum(ref["line_touch"]>.001),sum(ref["bullish_flip"]>.001))==(14,12)
    checkpoint=pd.read_csv(
       "analysis/st_v1_locked_monthly_by_strategy_20261122/monthly_contributions_wide.csv")
    assert len(checkpoint)==22
    for leg,col in (("line_touch","line_touch"),("bullish_flip","bullish_flip"),
                    ("combined","combined_points")):
        a=checkpoint[col].to_numpy(float)
        assert (np.abs(a-ref[leg])<.045).all(),(
                  leg,np.max(np.abs(a-ref[leg])))
    print("EXACT_MONTH_BY_MONTH_LOCKED_V1_PARITY_PASS",flush=True)
    touchvariants,flipvariants=variants()
    scenarios=[("baseline","none",TOUCH,FLIP)]
    scenarios += [(key,"line_touch",params,FLIP)
                    for key,params in touchvariants.items() if key!="baseline"]
    scenarios += [(key,"bullish_flip",TOUCH,params)
                    for key,params in flipvariants.items() if key!="baseline"]
    results=[]
    strict_candidates=[]
    for i,(name,changed,t,f) in enumerate(scenarios):
        ledger,blocked=build(t,f)
        touch_res=validate_months(mvec(ledger,"line_touch"),ref["line_touch"])
        flip_res=validate_months(mvec(ledger,"bullish_flip"),ref["bullish_flip"])
        combined=validate_months(mvec(ledger),ref["combined"])
        who=touch_res if changed=="line_touch" else flip_res
        strict_leg=(who["old_profit_months_degraded"]==0 and who["total_delta"]>=-.025)
        strict_combined=(combined["old_profit_months_degraded"]==0 and
                          combined["total_delta"]>=-.025)
        gain=who["wins"]-(14 if changed=="line_touch" else 12)
        row=dict(
          variant=name,changed=changed,
          touch_sl=t[0],touch_tp=t[1],touch_mode=t[2],
          touch_activation=t[3],touch_lock_or_trail=t[4],touch_timecap=t[5],
          flip_sl=f[0],flip_tp=f[1],flip_mode=f[2],
          flip_activation=f[3],flip_lock_or_trail=f[4],flip_timecap=f[5],
          trades_total=len(ledger),trades_touch=int(sum(ledger.strategy=="line_touch")),
          trades_flip=int(sum(ledger.strategy=="bullish_flip")),
          touch_monthly_wins=touch_res["wins"],
          flip_monthly_wins=flip_res["wins"],
          touch_profit_months_degraded=touch_res["old_profit_months_degraded"],
          flip_profit_months_degraded=flip_res["old_profit_months_degraded"],
          combined_profit_months_degraded=combined["old_profit_months_degraded"],
          touch_net=touch_res["total"],flip_net=flip_res["total"],
          combined_net=combined["total"],
          touch_delta=touch_res["total_delta"],
          flip_delta=flip_res["total_delta"],
          combined_delta=combined["total_delta"],
          changed_leg_profit_months_degraded=who["old_profit_months_degraded"],
          changed_leg_winning_months=who["wins"],
          changed_leg_winning_months_gain=gain,
          changed_leg_losses_converted_to_positive=who["losses_to_positive"],
          changed_leg_losses_converted_to_flat=who["losses_to_flat"],
          passes_leg_hard_constraints=strict_leg,
          passes_combined_hard_constraints=strict_combined,
          passes_all_hard_constraints=strict_leg and strict_combined,
          improves_monthly_wins=strict_leg and strict_combined and gain>0,
          blocked_by_overlap=blocked["blocked_overlaps"])
        results.append(row)
        if row["improves_monthly_wins"]:strict_candidates.append((row,ledger))
        if (i+1)%100==0:
          print("SCENARIOS_EVALUATED",i+1,"of",len(scenarios),flush=True)
    grid=pd.DataFrame(results)
    assert len(grid)==len(scenarios)
    grid.to_csv(OUT/"all_separate_exit_scenarios.csv",index=False)
    protected=grid[grid.passes_all_hard_constraints].sort_values(
       ["changed_leg_winning_months_gain","combined_net"],
       ascending=[False,False])
    protected.to_csv(OUT/"STRICT_no_harm_scenarios.csv",index=False)
    near=grid[(grid.changed_leg_winning_months_gain>0)&
              (grid.combined_net>=float(ref["combined"].sum())-.025)].sort_values(
        ["changed_leg_profit_months_degraded",
         "combined_profit_months_degraded","changed_leg_winning_months_gain",
         "combined_net"],ascending=[True,True,False,False])
    near.to_csv(OUT/"more_months_with_tradeoffs_DIAGNOSTIC.csv",index=False)
    focus=["baseline"]
    for leg in ("line_touch","bullish_flip"):
      x=grid[grid.changed==leg]
      focus+=x[x.improves_monthly_wins].sort_values(
          ["changed_leg_winning_months_gain","combined_delta"],
          ascending=[False,False]).variant.head(3).tolist()
      focus+=x.sort_values("changed_leg_winning_months_gain",
                          ascending=False).variant.head(2).tolist()
      focus+=x.sort_values("combined_delta",ascending=False).variant.head(2).tolist()
    focus=list(dict.fromkeys(focus))
    scenario_map={(name,changed):(t,f) for name,changed,t,f in scenarios}
    ledgers=[];months=[]
    for name in focus:
        row=grid[grid.variant==name].iloc[0]
        t,f=scenario_map[(name,row.changed)]
        led,_=build(t,f)
        l=led.copy();l["variant"]=name
        ledgers.append(l)
        for leg in ("line_touch","bullish_flip","combined"):
            m=mvec(led,leg)
            months.extend(dict(variant=name,leg=leg,month=month,net_pts=round(float(p),2))
                          for month,p in zip(MONTHS,m))
    pd.concat(ledgers,ignore_index=True).to_csv(
      OUT/"focus_trade_ledgers.csv.gz",index=False,compression="gzip")
    pd.DataFrame(months).to_csv(OUT/"focus_month_by_leg.csv",index=False)
    display=["variant","changed","touch_monthly_wins","flip_monthly_wins",
          "changed_leg_winning_months_gain","touch_net","flip_net",
          "combined_net","changed_leg_profit_months_degraded",
          "combined_profit_months_degraded","passes_all_hard_constraints"]
    report=[
      "# BTCUSD ST Locked V1.0: separately optimize monthly wins by leg",
      "",
      "Baseline verified against 22 per-leg months, 85 exclusive trades:",
      "Line Touch 14/22 positive months +13,816.06 net points;",
      "Bullish Flip 12/22 positive months +5,283.56 net points.",
      "Combined +19,099.62 net points, 17/22 profitable months.",
      "9 inactive/no-trade months for Flip are FLAT, not losses.",
      "",
      "## Strict individually profitable-month and combined non-degradation",
      "Condition: no reduction in the profit of any historically positive",
      "month of that leg OR combined portfolio; no decrease in total",
      "net profit of leg or combined. The other leg retains exact rules.",
      protected[display].head(35).to_markdown(index=False),
      "",
      "## Extra winning months but with tradeoffs (NOT eligible to lock)",
      near[display].head(30).to_markdown(index=False),
      "",
      "## Research limitations",
      "2025 and 2026 have already been used in model construction.",
      "This is an in-sample exit-parameter sensitivity grid, NOT",
      "independent OOS, and optimizing one historical loss can overfit.",
      "Increments 0.01 BTC point from rounding permitted, no funding,",
      "margin liquidation, depth or live order latency.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    (OUT/"quality.json").write_text(json.dumps(dict(
      total_tests=len(grid),
      touch_exit_tests=int((grid.changed=="line_touch").sum()),
      flip_exit_tests=int((grid.changed=="bullish_flip").sum()),
      baseline_line_touch_monthly_wins=14,
      baseline_flip_monthly_wins=12,
      baseline_line_touch_points=13816.06,
      baseline_flip_points=5283.56,
      baseline_combined_points=19099.62,
      hard_constraints_pass=int(grid.passes_all_hard_constraints.sum()),
      month_win_improvers_by_leg={
        leg:int(((grid.changed==leg)&grid.improves_monthly_wins).sum())
        for leg in ("line_touch","bullish_flip")},
      all_22_historical_months_seen=True,
      untouched_holdout=False,
      original_signals_and_fees_retained=True,
      one_position_one_supertrend_cycle=True),indent=2)+"\n")
    print("HARD_CONSTRAINT_AUDIT",OUT,flush=True)
    print("STRICT_WITH_IMPROVED_MONTHLY_WINS\n"+
      grid[grid.improves_monthly_wins][display].head(20).to_string(index=False),
      flush=True)
    print("MAX_WIN_MONTHS_EACH_LEG\n"+
      grid.groupby("changed").agg(max_months=("changed_leg_winning_months","max"),
       max_combined_profit=("combined_net","max"),
       hard_pass=("passes_all_hard_constraints","sum")).to_string(),flush=True)
    print("SUCCESS_SEPARATE_MONTHLY_WIN_EXIT_STUDY",flush=True)
if __name__=="__main__":
    main()
