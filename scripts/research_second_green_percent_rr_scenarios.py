#!/usr/bin/env python3
"""BTCUSD 15m Supertrend original closing-stop plus percent SL:TP ratios.

Independent sensitivity test: 1:2 means SL=1% and TP=2% OF ENTRY BTC PRICE,
not points or leveraged account ROI. Keep original Supertrend closing exit,
entry signals and indicator settings unchanged. 1m stop-first OHLC replay.
Two second-green confirmations: after first bullish ST line touch or flip.

No profit-lock or trailing profit protection in this particular fixed-RR
experiment: this isolates risk/reward effects and does NOT replace the
percentage-profit-lock-only branch. Margin/funding/liquidation not modeled.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as filt
import research_supertrend_15m_profit_protection as protect
import research_supertrend_15m_second_green as green
import research_second_green_percent_grid as prior

OUT=Path("analysis/second_green_pct_rr_scenarios_20261122")
STOP_PCT=(.10,.12,.15,.20,.30,.50,.75,1.,1.5,2.,3.,4.,5.)
TARGET_PCT=(.12,.20,.24,.30,.40,.50,.60,.75,.90,1.,1.5,2.,2.25,3.,4.,5.,6.,8.,9.,10.,12.,15.)
MODELS=("after_line_touch","after_bullish_flip")

# Predefined ratios at both sub-1% and whole-percent magnitudes.
ASKED=[
 (.10,.20),(.10,.30),(.12,.24),(.20,.40),(.20,.60),
 (.30,.60),(.30,.90),(.50,1.),(.50,1.5),(.75,1.5),(.75,2.25),
 (1.,1.),(1.,2.),(1.,3.),(1.,4.),(1.,5.),(1.,6.),(1.,8.),
 (2.,2.),(2.,3.),(2.,4.),(2.,6.),(2.,8.),(2.,10.),(2.,12.),
 (3.,3.),(3.,4.),(3.,6.),(3.,9.),(3.,12.),(3.,15.),
 (4.,8.),(4.,12.),(5.,5.),(5.,10.),(5.,15.),
]
assert len(ASKED)==len(set(ASKED))
assert set(x[0] for x in ASKED).issubset(STOP_PCT)
assert set(x[1] for x in ASKED).issubset(TARGET_PCT)
def configure_grid():
    # Keep the previously verified causal model and fee treatment; only
    # extend the stop/target percent value axes.
    prior.SL_PCT=STOP_PCT
    prior.TP_PCT=TARGET_PCT
    prior.S=np.asarray(STOP_PCT,float)
    prior.T=np.asarray(TARGET_PCT,float)
    prior.NS=len(STOP_PCT)
    prior.NT=len(TARGET_PCT)
    prior.ALL_FINITE_SL=np.ones(len(STOP_PCT),dtype=bool)
    prior.RR_MASK=np.ones((prior.NS,prior.NT),dtype=bool)

def main():
    configure_grid()
    OUT.mkdir(parents=True,exist_ok=True)
    minute,bars,files=base.load()
    st,trend=base.supertrend(bars)
    vol,atrpct,atrrelative=filt.build_features(bars)
    events,stops=filt.candidate_touch_events(
        minute,bars,st,trend,vol,atrpct,atrrelative)
    opening=minute.open.to_numpy(float)
    months=minute.index.tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()

    # Guard same entry cohorts and cost calculations against last verified
    # 300/1200 fixed-point report before running new percentage comparisons.
    vf=filt.VOLUME["vol_ge_1p0"]
    af=filt.VOLATILITY["atrpct_ge_0p20"]
    firsttouch=protect.select_events(events,vf,af)
    touch_green=green.after_touch_green(firsttouch,bars,trend,stops,opening)
    flip_green=green.after_flip_green(bars,trend,vol,atrpct,atrrelative,
                                   vf,af,stops,opening)
    assert sum(months[x[2]] in base.MONTHS for x in touch_green)==108
    assert sum(months[x[2]] in base.MONTHS for x in flip_green)==197
    arrays=(minute.high.to_numpy(float),minute.low.to_numpy(float),
             opening,minute.close.to_numpy(float),minute.index)
    for kind,entries,n,expected in (
      ("after_line_touch",touch_green,108,4704.53),
      ("after_bullish_flip",flip_green,197,-24654.29)):
        ref=green.market_replay(entries,stops,arrays,300,1200,"off",months)
        ref=ref[ref.month_ist.isin(base.MONTHS)]
        assert len(ref)==n
        assert abs(float(ref.net_pts.sum())-expected)<.15,(kind,ref.net_pts.sum())
    print("ENTRY_AND_COST_PARITY_REFERENCE_PASS",flush=True)

    full=[];periods=[]
    for vn,vs in filt.VOLUME.items():
        for an,ats in filt.VOLATILITY.items():
            selected=protect.select_events(events,vs,ats)
            entry_methods={
              "after_line_touch":green.after_touch_green(
                 selected,bars,trend,stops,opening),
              "after_bullish_flip":green.after_flip_green(
                 bars,trend,vol,atrpct,atrrelative,vs,ats,stops,opening)}
            for kind,entries in entry_methods.items():
                rows,parts=prior.run_grid(entries,stops,minute,months,vn,an,kind)
                full.extend(rows)
                periods.extend(parts)
            print("FILTER_COMPLETED",vn,an,"evaluated",len(full),flush=True)

    table=pd.DataFrame(full)
    partition=pd.DataFrame(periods)
    target_count=2*len(filt.VOLUME)*len(filt.VOLATILITY)*len(STOP_PCT)*len(TARGET_PCT)
    assert len(table)==target_count
    assert len(partition)==target_count*5
    assert table.groupby(["entry_type","vol_filter","atr_filter"]).trades.nunique().eq(1).all()
    table.to_csv(OUT/"all_percent_risk_reward_grid.csv",index=False)
    partition.to_csv(OUT/"year_split_all_configs.csv.gz",index=False,compression="gzip")
    same=table[(table.vol_filter=="vol_ge_1p0")&
               (table.atr_filter=="atrpct_ge_0p20")]
    nofilter=table[(table.vol_filter=="vol_off")&
                   (table.atr_filter=="atr_off")]
    combined=pd.concat([same,nofilter],ignore_index=True)
    combined.to_csv(OUT/"matched_filters_and_unfiltered.csv",index=False)
    asked=pd.DataFrame(ASKED,columns=["sl_pct","tp_pct"])
    combos=table.merge(asked,on=["sl_pct","tp_pct"])
    assert len(combos)==len(ASKED)*2*len(filt.VOLUME)*len(filt.VOLATILITY)
    combos.to_csv(OUT/"all_requested_ratio_combinations.csv",index=False)
    matched=combos[(combos.vol_filter=="vol_ge_1p0")&
                   (combos.atr_filter=="atrpct_ge_0p20")].copy()
    matched=matched.merge(partition[partition.period.isin(["2025","2026_JanOct"])][
        ["entry_type","vol_filter","atr_filter","sl_pct","tp_pct",
         "period","net_pts","positive_months"]].pivot_table(
        index=["entry_type","vol_filter","atr_filter","sl_pct","tp_pct"],
        columns="period",values=["net_pts","positive_months"]
        ).reset_index(),on=["entry_type","vol_filter","atr_filter","sl_pct","tp_pct"])
    matched.to_csv(OUT/"matched_filter_requested_ratios_and_years.csv",index=False)

    robust=combos[combos.trades>=60].sort_values(
        ["net_pts","profitable_months"],ascending=False)
    robust.to_csv(OUT/"requested_ratios_min60trades_ranked.csv",index=False)
    cols=["entry_type","sl_pct","tp_pct","trades","wins",
          "win_rate_pct","sl_exits","tp_exits","close_stop_exits",
          "net_pts","net_pts_per_trade","max_drawdown_pts",
          "profitable_months","losing_months"]
    matched_plain=combos[(combos.vol_filter=="vol_ge_1p0")&
                         (combos.atr_filter=="atrpct_ge_0p20")]
    def listing(kind):
        x=matched_plain[matched_plain.entry_type==kind].copy()
        x["risk_reward"]=x.apply(
            lambda r:f"{r.sl_pct:g}% : {r.tp_pct:g}%",axis=1)
        return x[["risk_reward"]+cols].to_markdown(index=False)
    best=robust.head(25)
    report=[
      "# BTCUSD original Supertrend exit: percentage risk/reward scenarios",
      "",
      "Important: 1:2 = 1% BTC price hard stop / 2% BTC price take profit.",
      "Not BTC points, and not 1% or 2% on leveraged account equity.",
      "The original 15-minute Supertrend(10,3) closing exit remains ON.",
      "These are fixed percentage R:R exits, NOT the separate profit-lock",
      "experiment. There is no profit-trailing/step-up in this test.",
      "15m second GREEN confirmation after bullish line touch vs flip.",
      "Market fill third 15m open using 1m OHLC, 1m SL-first tie,",
      "taker each way 0.05%, GST 18%, 5 BTC points slip each way.",
      "22 completed IST entry months Jan2025-Oct2026.",
      "",
      f"Full factorial size {len(table)} (2 entries x 42 filters x",
      f"{len(STOP_PCT)} stop levels x {len(TARGET_PCT)} targets).",
      f"Explicit requested ratios: {len(ASKED)} x 2 entries x 42 filter pairs",
      f"= {len(combos)} cases.",
      "",
      "## Volume >=1.0x, ATR >=0.20%, after line touch",
      listing("after_line_touch"),
      "",
      "## Same filters, after bullish flip",
      listing("after_bullish_flip"),
      "",
      "## Top requested R:R combinations with >=60 trades (hindsight ranked)",
      best[["vol_filter","atr_filter"]+cols].to_markdown(index=False),
      "",
      "## Critical model limits",
      "- 15m Supertrend closing stop can exit before SL or TP.",
      "- 1m OHLC ordering ambiguous, SL wins same minute.",
      "- User-requested percentage SL/TP is not the same as percentage",
      "  profit protection; previous independent percent-lock study remains.",
      "- BTC price-point PnL normalized to 1-BTC equivalent, not actual equity.",
      "- No margin, liquidation, dynamic spread, funding or fills queue.",
      "- Multiple-hypothesis retrospective selection; no blind forward test.",
      "",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report))
    summary=dict(
      status="executed, parity verified",entries=list(MODELS),
      full_configurations=int(len(table)),
      specifically_requested_combinations=len(ASKED),
      specifically_requested_tests=int(len(combos)),
      filters=int(len(filt.VOLUME)*len(filt.VOLATILITY)),
      sl_levels=list(STOP_PCT),tp_levels=list(TARGET_PCT),
      same_filter_cohorts=dict(touch=108,flip=197),
      ST_closing_exit_enabled=True,
      price_stop_and_target_percentage=True,
      model_fee="0.05% per side with GST18, 5 BTC pts per side",
      units="BTC price points per 1 BTC equivalent, not equity ROI",
      liquidation_model=False,profit_protection=False)
    (OUT/"quality.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("VERIFIED_GRID",json.dumps(dict(
        full_cases=len(table),asked_cases=len(combos),
        profitable_asked=int((combos.net_pts>0).sum()),
        profitable_with_60_trades=int(((combos.net_pts>0)&
                                  (combos.trades>=60)).sum())),flush=True)
    print("MATCHED_FILTERS\n"+matched_plain[cols].to_string(index=False),flush=True)
    print("TOP_REQUESTED_OVER60\n"+best[["vol_filter","atr_filter"]+cols].to_string(index=False),flush=True)
    print("DONE",OUT/"RESEARCH_REPORT.md",flush=True)

if __name__=="__main__":main()
