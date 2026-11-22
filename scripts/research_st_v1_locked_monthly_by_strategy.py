#!/usr/bin/env python3
"""Break down the EXACT frozen BTCUSD ST V1.0 combined portfolio by strategy.

No signal/exit changes; Line Touch locked at +0.4 after +1.0, Bullish
Flip original. One position at once, one per ST cycle, original costs.
Actual exit month in IST, full 2025 & Jan-Oct 2026.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as feat
import research_st_three_best_combined_portfolio as port
import research_st_touch075_flip_lowvol_combination as fixed
import research_st_touch_flip_causal_regime_filters as htf
import research_second_green_percent_rr_scenarios as rr
import research_st_preserve_all_profitable_month_pnl as locked

OUT=Path("analysis/st_v1_locked_monthly_by_strategy_20261122")
def main():
    rr.configure_grid()
    port.SPECS=fixed.COHORTS
    OUT.mkdir(parents=True,exist_ok=True)
    minute,bars,files=base.load()
    st,trend=base.supertrend(bars)
    vol,ap,ar=feat.build_features(bars)
    ev,stopbars=feat.candidate_touch_events(
        minute,bars,st,trend,vol,ap,ar)
    signal_sets=port.decode_signals(
        minute,bars,trend,vol,ap,ar,ev,stopbars)
    candidates=port.compute_candidates(minute,trend,stopbars,signal_sets)
    assert len(candidates)==150
    flags=htf.features(bars,trend)
    barids=candidates.entry_bar.to_numpy(int)
    is_touch=(candidates.strategy=="line_touch").to_numpy()
    eligible=(is_touch&flags["1h_above_ema20_and_rising"].to_numpy(bool)[barids]) | (
       (~is_touch)&flags["1h_rsi50"].to_numpy(bool)[barids])
    filtered=candidates[eligible].copy().reset_index(drop=True)
    assert len(filtered)==87
    modified,count=locked.add_stopped_trade_replays(filtered,minute,stopbars)
    combined,blocked=port.portfolio(
        modified,("line_touch","bullish_flip"),
        ("line_touch","bullish_flip"),global_cycle_cap=True)
    assert len(combined)==85
    assert combined.st_cycle.is_unique
    total2025=combined.loc[combined.exit_month_ist.str.startswith("2025"),"net_pts"].sum()
    total2026=combined.loc[combined.exit_month_ist.str.startswith("2026"),"net_pts"].sum()
    assert abs(total2025-14553.35)<.03,total2025
    assert abs(total2026-4546.27)<.03,total2026
    assert abs(combined.net_pts.sum()-19099.62)<.03
    assert len(combined.query("strategy=='line_touch'")) + len(combined.query("strategy=='bullish_flip'"))==85

    raw=combined.groupby(["exit_month_ist","strategy"],as_index=False).agg(
      trades=("net_pts","size"),wins=("win","sum"),
      net_points=("net_pts","sum"))
    all_months=pd.MultiIndex.from_product([base.MONTHS,["line_touch","bullish_flip"]],
                         names=["exit_month_ist","strategy"])
    raw=raw.set_index(["exit_month_ist","strategy"]).reindex(
      all_months,fill_value=0).reset_index()
    raw["net_points"]=raw.net_points.round(2)
    raw.to_csv(OUT/"monthly_contributions_long.csv",index=False)
    bymonth=raw.pivot(index="exit_month_ist",columns="strategy",
                       values="net_points").reset_index()
    bymonth.columns.name=None
    bymonth["combined_points"]=(
         bymonth["line_touch"]+bymonth["bullish_flip"]).round(2)
    bymonth["total_trades"]=(
       raw.pivot(index="exit_month_ist",columns="strategy",
                  values="trades").sum(axis=1).values)
    # Round-to-cent displays may differ +/- .01; evaluate against exact
    # unrounded historical original monthly proof.
    checkpoint=pd.read_csv(
      "analysis/st_touch_flip_exit_protection_20261122/focus_profiles_monthly.csv")
    ck=checkpoint[checkpoint.profile=="touch_lock_1.0_0.4"].set_index("month_ist")
    assert len(ck)==22
    for row in bymonth.itertuples():
       asserted=float(ck.loc[row.exit_month_ist,"exit_month_realized_net_pts"])
       assert abs(row.combined_points-asserted)<.04,(
           row.exit_month_ist,row.combined_points,asserted)
    bymonth["year"]=bymonth.exit_month_ist.str[:4]
    bymonth.to_csv(OUT/"monthly_contributions_wide.csv",index=False)

    all_=pd.DataFrame({
       "strategy":["Line Touch","Bullish Flip","Combined portfolio"],
       "trades":[int(sum(combined.strategy=="line_touch")),
                 int(sum(combined.strategy=="bullish_flip")),len(combined)],
       "wins":[int(combined.query("strategy=='line_touch'").win.sum()),
               int(combined.query("strategy=='bullish_flip'").win.sum()),
               int(combined.win.sum())],
       "2025_net_points":[round(combined.loc[(combined.strategy==x)&
           (combined.exit_month_ist.str.startswith("2025")),"net_pts"].sum(),2)
          for x in ("line_touch","bullish_flip")] + [round(total2025,2)],
       "2026_JanOct_net_points":[round(combined.loc[(combined.strategy==x)&
           (combined.exit_month_ist.str.startswith("2026")),"net_pts"].sum(),2)
          for x in ("line_touch","bullish_flip")] + [round(total2026,2)],
       "total_net_points":[round(combined.loc[combined.strategy==x,"net_pts"].sum(),2)
          for x in ("line_touch","bullish_flip")] + [round(combined.net_pts.sum(),2)],
    })
    all_.to_csv(OUT/"summary_strategy_contributions.csv",index=False)
    combined.to_csv(OUT/"locked_v1_exact_trade_ledger.csv.gz",index=False,compression="gzip")
    report=[
      "# Locked V1.0 BTCUSD ST: actual exit-month strategy breakdown",
      "",
      "Original frozen strategy. Line Touch: SL 0.75%, TP 1.5%,",
      "1h close>EMA20 + rising EMA20, Volume>=1, ATR%>=.2,",
      "profit stop locked at +0.4% following a PRIOR completed",
      "1m candle reaching +1%. Bullish Flip: SL 3%, TP .5%,",
      "last completed 1h RSI14>=50, vol<=.8, ATR%>=.2.",
      "Both LONG ONLY, one concurrent, one per ST bullish cycle,",
      "and original ST closing exit. All estimates include fees/GST/slippage.",
      "",
      "## Totals by strategy inside the combined one-position portfolio",
      all_.to_markdown(index=False),
      "",
      "## 2025 monthly by individual component",
      bymonth[bymonth.year=="2025"][[
          "exit_month_ist","line_touch","bullish_flip",
          "combined_points","total_trades"]].to_markdown(index=False),
      "",
      "## Jan-Oct 2026 monthly by individual component",
      bymonth[bymonth.year=="2026"][[
          "exit_month_ist","line_touch","bullish_flip",
          "combined_points","total_trades"]].to_markdown(index=False),
      "",
      "## Execution and caveats",
      "P&L reported in BTC price points for 1 BTC-equivalent position.",
      "No funding, margin liquidation, leverage account ROI, order latency.",
      "History used to optimize strategy; not true out-of-sample.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    (OUT/"quality.json").write_text(json.dumps(dict(
       source_files=int(len(files)),source_candidate_signals=150,
       HTF_eligible_signals=len(filtered),locked_line_touch_replayed=count,
       exclusive_trades=len(combined),all_22_month_parity=True,
       net_2025=round(float(total2025),2),
       net_2026=round(float(total2026),2),
       month_attribution="realized_exit_month_IST",
       individual_contributions_sum_to_combined=True,
       original_strategy_parameters_unchanged=True,
       future_out_of_sample_validation=False),indent=2)+"\n")
    print("SUCCESS_V1_LOCKED_INDIVIDUAL_STRATEGY_MONTHLY_PARITY")
    print(all_.to_string(index=False),flush=True)
    print(bymonth.to_string(index=False),flush=True)

if __name__=="__main__":
    main()
