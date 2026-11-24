#!/usr/bin/env python3
"""Independent explicit 1m-candle audit of locked-V1 + bearish-flip SHORT.

Manually loop all SHORT execution minutes (do not reuse vectorized grid
exit cache), then reproduce published 18/22, +22,633.90, 85 unchanged
LONG core and max closed-equity DD 2642.53; test execution friction
sensitivity. Research only: all 2025-Oct2026 were already inspected.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as filt
import research_st_three_best_combined_portfolio as portfolio
import research_st_touch075_flip_lowvol_combination as original
import research_st_touch_flip_causal_regime_filters as htf
import research_st_preserve_all_profitable_month_pnl as coremod
import research_second_green_percent_rr_scenarios as rr

OUT=Path("analysis/st_v1_short_addon_independent_audit_20261124")
MONTHS=tuple(base.MONTHS)
def compare(a,b,tol=.04):
    return bool(abs(a-b)<=tol)
def main():
  rr.configure_grid()
  portfolio.SPECS=original.COHORTS
  OUT.mkdir(parents=True,exist_ok=True)
  minute,bars,files=base.load()
  st,trend=base.supertrend(bars)
  vol,atrp,atrrel=filt.build_features(bars)
  events,stops=filt.candidate_touch_events(
      minute,bars,st,trend,vol,atrp,atrrel)
  orig=portfolio.decode_signals(
      minute,bars,trend,vol,atrp,atrrel,events,stops)
  raw=portfolio.compute_candidates(minute,trend,stops,orig)
  g=htf.features(bars,trend)
  idx=raw.entry_bar.to_numpy(int)
  touch=(raw.strategy=="line_touch").to_numpy()
  masked=(touch&g["1h_above_ema20_and_rising"].to_numpy(bool)[idx])|(
      ~touch&g["1h_rsi50"].to_numpy(bool)[idx])
  core_raw=raw[masked].copy().reset_index(drop=True)
  all_core,n_touch=coremod.add_stopped_trade_replays(
      core_raw,minute,stops)
  core,_=portfolio.portfolio(all_core,
       ("line_touch","bullish_flip"),("line_touch","bullish_flip"),True)
  assert len(core)==85
  assert compare(float(core.net_pts.sum()),19099.62)
  assert int((core.strategy=="line_touch").sum())==67
  assert int((core.strategy=="bullish_flip").sum())==18
  op=minute.open.to_numpy(float)
  high=minute.high.to_numpy(float)
  low=minute.low.to_numpy(float)
  cl=minute.close.to_numpy(float)
  bopen=bars.open.to_numpy(float)
  bclose=bars.close.to_numpy(float)
  n=len(op)
  month=minute.index.tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
  # STOP when bearish ST resistance is breached on a COMPLETE 15m bar.
  bearish_fail=np.zeros(len(bars),bool)
  for i in range(1,len(bars)):
    if trend[i-1]==1 and (
       trend[i]==-1 or bclose[i]>st[i-1]):
      bearish_fail[i]=True
  bearish_stops=np.flatnonzero(bearish_fail)
  red_cycle=np.cumsum((trend==1)&
              np.r_[True,trend[:-1]!=1])
  entries=[]
  for flip in range(15,len(bars)-2):
     next15=flip+1
     third=flip+2
     # bearish flip confirmed at flip close, next candle RED closed.
     if not(trend[flip-1]==-1 and trend[flip]==1
            and trend[next15]==1 and
            bclose[next15]<bopen[next15]
            and not bearish_fail[next15]):
         continue
     if not(np.isfinite(vol[flip]) and vol[flip]<=.8 and
            np.isfinite(atrp[flip]) and atrp[flip]>=.2):
         continue
     j=third*15
     if month[j] not in MONTHS:continue
     assert red_cycle[flip]>0
     entries.append(dict(flip=flip,entry_idx=j,entry_bar=third,
                         st_cycle=-int(red_cycle[flip]),
                         vol_ratio=float(vol[flip]),
                         atr_pct=float(atrp[flip])))
  assert len(entries)==23,("expected 23 SHORT signals",len(entries))
  assert len(set(x["st_cycle"] for x in entries))==23
  print("CAUSAL_23_SHORT_SETUP_SIGNALS_PASS",flush=True)

  def short_replay(entry,slippage=5.,fee=base.FEE,stop_pct=1.):
    j=entry["entry_idx"]
    bj=entry["entry_bar"]
    ix=int(np.searchsorted(bearish_stops,bj,side="left"))
    end=min((int(bearish_stops[ix])+1)*15,n) if ix<len(bearish_stops) else n
    assert end>j
    sell=float(op[j]-slippage)
    stop=sell*(1+stop_pct/100.)
    target=sell*(1-.3/100.)
    exit_idx=None
    reason=None
    exitmid=None
    collision=False
    for mi in range(j,end):
       stop_hit=high[mi]>=stop
       take_hit=low[mi]<=target
       if not (stop_hit or take_hit):
          continue
       exit_idx=mi
       collision=bool(stop_hit and take_hit)
       if stop_hit:
           exitmid=float(max(op[mi],stop))
           reason="short_stop"
       else:
           exitmid=float(target)
           reason="short_take_profit"
       break
    if exit_idx is None:
       if end<n:
           exit_idx=end
           exitmid=float(op[end])
           reason="supertrend_close_exit"
       else:
           exit_idx=n-1
           exitmid=float(cl[-1])
           reason="data_end"
    cover=float(exitmid+slippage)
    fees=fee*(sell+cover)
    net=sell-cover-fees
    return dict(
       strategy="short_addon",
       signal_cycle=-entry["st_cycle"],
       st_cycle=entry["st_cycle"],
       entry_bar=entry["entry_bar"],
       entry_idx=j,
       exit_idx=exit_idx,
       entry_utc=str(minute.index[j]),
       exit_utc=str(minute.index[exit_idx]),
       entry_month_ist=str(month[j]),
       exit_month_ist=str(month[exit_idx]),
       sl_pct=stop_pct,tp_pct=.3,
       entry_fill=sell,exit_fill=cover,
       entry_mid=float(op[j]),exit_mid=exitmid,
       net_pts=net,fee_pts=fees,reason=reason,
       collision=int(collision),holding_minutes=exit_idx-j,
       win=int(net>0),vol_ratio=entry["vol_ratio"],
       atr_pct=entry["atr_pct"])
  core_by_month=np.array(
       [float(core.loc[core.exit_month_ist==m,"net_pts"].sum())
        for m in MONTHS])
  scenarios=[("reference_costs",5.,base.FEE,1.),
      ("higher_slippage_10pt",10.,base.FEE,1.),
      ("higher_slippage_20pt",20.,base.FEE,1.),
      ("higher_slippage_30pt",30.,base.FEE,1.),
      ("higher_fee_0p1pct",5.,.001*1.18,1.),
      ("higher_fee_0p1pct_plus_10pt",10.,.001*1.18,1.),
      ("stop_loss_0p75pct",5.,base.FEE,.75),
      ("stop_loss_1p5pct",5.,base.FEE,1.5)]
  quality=[]
  months=[]
  for name,slip,fee,sl in scenarios:
     shorts=pd.DataFrame([short_replay(entry,slip,fee,sl) for entry in entries])
     ledger,conf=portfolio.portfolio(
         pd.concat([core,shorts],ignore_index=True),
         ("line_touch","bullish_flip","short_addon"),
         ("line_touch","bullish_flip","short_addon"),True)
     chosen_core=ledger[ledger.strategy!="short_addon"]
     keep=ledger[ledger.strategy=="short_addon"]
     assert len(chosen_core)==85 and len(keep)==23,(name,len(chosen_core),len(keep))
     assert set(chosen_core.entry_idx)==set(core.entry_idx)
     assert compare(chosen_core.net_pts.sum(),core.net_pts.sum(),.00005)
     net=np.array([float(ledger.loc[ledger.exit_month_ist==m,"net_pts"].sum())
                   for m in MONTHS])
     diff=net-core_by_month
     if name=="reference_costs":
       assert float(diff.min())>-.04,(name,float(diff.min()))
     equity=ledger.sort_values("exit_idx").net_pts.to_numpy(float)
     equity=np.r_[0.,np.cumsum(equity)]
     drawdown=float(np.max(np.maximum.accumulate(equity)-equity))
     row=dict(scenario=name,short_count=len(keep),
      short_wins=int(sum(keep.net_pts>0)),short_losses=int(sum(keep.net_pts<=0)),
      original_core_count=len(chosen_core),
      original_core_unchanged=True,
      short_net=round(float(keep.net_pts.sum()),2),
      combined_total=round(float(net.sum()),2),
      net_2025=round(float(net[:12].sum()),2),
      net_2026=round(float(net[12:].sum()),2),
      profitable_months=int(sum(net>0)),
      losing_months=int(sum(net<0)),
      original_profitable_months_degraded=int(sum(
           (core_by_month>0)&(diff<-.04))),
      improved_old_losing_months=int(sum(
           (core_by_month<0)&(net>0))),
      max_closed_equity_drawdown=round(drawdown,2),
      short_win_rate_pct=round(100*sum(keep.net_pts>0)/len(keep),2),
      short_tp_exits=int((keep.reason=="short_take_profit").sum()),
      short_stops=int((keep.reason=="short_stop").sum()),
      short_st_close_exits=int(
          (keep.reason=="supertrend_close_exit").sum()),
      same_minute_sl_tp_conflicts=int(keep.collision.sum()))
     quality.append(row)
     for m,v,b in zip(MONTHS,net,core_by_month):
         months.append(dict(scenario=name,month_ist=m,
            core_net=round(float(b),2),combined_net=round(float(v),2),
            addition_net=round(float(v-b),2)))
     if name=="reference_costs":
       assert abs(float(net.sum())-22633.90)<.05
       assert abs(float(net[:12].sum())-16723.13)<.05
       assert abs(float(net[12:].sum())-5910.76)<.05
       assert sum(net>0)==18
       assert compare(drawdown,2642.53)
       assert float(net[MONTHS.index("2025-12")])>0
       shorts.to_csv(OUT/"independently_verified_23_short_trades.csv",index=False)
       ledger.to_csv(OUT/"independently_verified_108_portfolio_trades.csv",
                     index=False)
  results=pd.DataFrame(quality)
  results.to_csv(OUT/"execution_cost_robustness.csv",index=False)
  monthly=pd.DataFrame(months)
  monthly.to_csv(OUT/"all_cost_scenarios_monthly.csv",index=False)
  report=[
     "# BTC ST V1.0 bearish-flip SHORT add-on: independent trade-by-trade audit",
     "",
     "The 67 original Line Touch and 18 Bullish Flip LONG trades remain",
     "EXACTLY as locked. New 23 bearish SHORT trades use a fresh explicit",
     "1m bar-by-bar conservative replay, not the research grid's",
     "vectorized cached exits. Original 85 trades are not blocked.",
     "",
     "## Cost and stop sensitivity (SHORT leg only, LONG original costs unchanged)",
     results.to_markdown(index=False),
     "",
     "## Reference-case monthly before and after third SHORT leg",
     monthly[monthly.scenario=="reference_costs"].to_markdown(index=False),
     "",
     "## Important limits",
     "Multiple thousands of configurations were evaluated, 2025 and",
     "2026 already repeatedly inspected; NOT a genuine untouched",
     "holdout. This audit reproduces but does not prove forward alpha.",
     "SHORT margin, funding, liquidation and order-book depth are",
     "not modeled. All figures in BTC price points per 1 BTC equivalent.",
  ]
  (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
  (OUT/"quality.json").write_text(json.dumps(dict(
      independently_verified_23_short_trades=True,
      original_85_long_trades_preserved=True,
      prior_grid_pnl_and_closed_equity_dd_parity=True,
      independent_1m_exit_loop=True,
      historical_data_forward_unseen=False,
      additional_stress_tests=len(scenarios)-1,
      reference_case=quality[0],
      other_cases=quality[1:]),indent=2)+"\n")
  print("INDEPENDENT_AUDIT_PASSED")
  print(results.to_string(index=False),flush=True)
  print("REFERENCE_MONTHS")
  print(monthly[monthly.scenario=="reference_costs"].to_string(index=False),
        flush=True)
if __name__=="__main__":
  main()
