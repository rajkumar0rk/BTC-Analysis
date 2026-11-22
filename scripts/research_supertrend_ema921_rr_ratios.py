#!/usr/bin/env python3
"""Supplementary RR 1:3/1:4 grid for existing BTCUSD Supertrend EMA9/21 signals.

Reuses previously computed fixed grid results where available; computes ONLY
newly requested stop-target pairs. See NOVELTY_CHECK.md for preregistration.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_supertrend_ema921 import source, minute_alignment, IST, FEE, SLIP, MONTHS
from research_supertrend_ema921_fixed_grid import simulate, scoring, START_MONTH

OUT = Path("analysis/supertrend_ema921_rr_ratios")
PRIOR = Path("analysis/supertrend_ema921_fixed_grid")
THREE = [(100,300),(150,450),(200,600),(300,900),(400,1200),
         (500,1500),(600,1800),(800,2400),(1000,3000)]
FOUR = [(100,400),(200,800),(300,1200),(400,1600),
        (500,2000),(600,2400),(800,3200),(1000,4000)]
PAIRS = THREE + FOUR
TFS = (5, 15, 60)
assert len(PAIRS)==len(set(PAIRS))==17

def key_of(tf,sl,tp):
    return (str(tf)+"m",int(sl),int(tp))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    old_summary=pd.read_csv(PRIOR/"summary.csv")
    old_month=pd.read_csv(PRIOR/"monthly_results.csv",dtype={"month_ist":str})
    all_old={(str(x.timeframe),int(x.sl_points),int(x.tp_points))
             for x in old_summary.itertuples(index=False)}
    pairs_present=[(sl,tp) for sl,tp in PAIRS if ("5m",sl,tp) in all_old]
    assert len(pairs_present)==5, f"Expected 5 reused exact pairs, got {pairs_present}"
    expected={(100,300),(200,800),(500,1500),(500,2000),(1000,3000)}
    assert set(pairs_present)==expected
    pairs_new=[p for p in PAIRS if p not in expected]
    assert len(pairs_new)==12
    raw,gaps=source()
    if gaps: raise RuntimeError(f"Missing source minutes: {gaps[:3]}")
    dt=raw.index.tz_convert(IST)
    monthcode=np.asarray(dt.year,dtype=np.int32)*12+np.asarray(dt.month,dtype=np.int32)
    op=raw.open.to_numpy(float)
    hi=raw.high.to_numpy(float)
    lo=raw.low.to_numpy(float)
    cl=raw.close.to_numpy(float)
    summaries=[];monthly=[];ledgers=[]; signal_stats={}

    for tf in TFS:
        sig,stats=minute_alignment(raw,tf)
        signal_stats[str(tf)]=stats
        prev=np.r_[0,sig[:-1]]
        events=np.flatnonzero((sig!=0)&(sig!=prev)).astype(np.int32)
        sides=sig[events].astype(np.int8)
        print(f"TIMEFRAME {tf}m, event_count={len(events)}",flush=True)
        for sl,tp in PAIRS:
            ratio="1:3" if (sl,tp) in THREE else "1:4"
            selector=((old_summary.timeframe.eq(str(tf)+"m")) &
                      old_summary.sl_points.eq(sl) &
                      old_summary.tp_points.eq(tp))
            if (sl,tp) in expected:
                assert selector.sum()==1
                prior_s=old_summary.loc[selector].iloc[0].to_dict()
                old_sel=((old_month.timeframe.eq(str(tf)+"m")) &
                         old_month.sl_points.eq(sl) & old_month.tp_points.eq(tp))
                assert old_sel.sum()==22
                prev_month=old_month.loc[old_sel]
                summaries.append({**prior_s, "risk_reward_ratio":ratio,
                                  "source":"prior_fixed_grid_reused"})
                monthly.extend([{**row.to_dict(),"risk_reward_ratio":ratio,
                                "source":"prior_fixed_grid_reused"}
                               for _,row in prev_month.iterrows()])
                print(f"REUSE {tf}m {sl}/{tp} net={prior_s['total_net_1x_account_return_pct']:.3f}% "
                      f"months_positive={prior_s['positive_months_22']}/22",flush=True)
                continue
            result=simulate(op,hi,lo,cl,monthcode,events,sides,float(sl),float(tp))
            s,m,_=scoring(result,monthcode,tf,sl,tp)
            summaries.append({**s,"risk_reward_ratio":ratio,"source":"newly_replayed"})
            monthly.extend([{**row,"risk_reward_ratio":ratio,"source":"newly_replayed"} for row in m])
            ei,xi,sd,reason,gross,fees,net,pct=result
            n=len(ei)
            ledger=pd.DataFrame({"timeframe":[f"{tf}m"]*n,
                "sl_points":[sl]*n,"tp_points":[tp]*n,
                "risk_reward_ratio":[ratio]*n,
                "entry_ist":dt[ei].astype(str),"exit_ist":dt[xi].astype(str),
                "month_ist":[MONTHS[int(ix)] for ix in monthcode[xi]-START_MONTH],
                "side":np.where(sd==1,"LONG","SHORT"),
                "exit_reason":np.array(["stop","target","stop_gap",
                   "stop_first_both","month_flat","end_of_data"])[reason],
                "gross_points_per_btc":np.round(gross,4),
                "fees_gst_per_btc":np.round(fees,4),
                "slippage_points_per_btc":[2*SLIP]*n,
                "net_points_per_btc":np.round(net,4),
                "net_trade_1x_return_pct":pct,
                "entry_index":ei,"exit_index":xi})
            ledgers.append(ledger)
            print(f"NEW {tf}m {sl}/{tp} trades={s['trades']} "
                  f"wins={s['wins']} months_positive={s['positive_months_22']} "
                  f"return={s['total_net_1x_account_return_pct']:.3f}%",flush=True)
    sm=pd.DataFrame(summaries);mo=pd.DataFrame(monthly)
    assert len(sm)==51 and len(mo)==51*22
    sm.to_csv(OUT/"summary.csv",index=False)
    mo.to_csv(OUT/"monthly_results.csv",index=False)
    pd.concat(ledgers,ignore_index=True).to_csv(OUT/"new_trade_ledger.csv.gz",
                                                 index=False,compression="gzip")
    best=sm.sort_values(["total_net_1x_account_return_pct",
                         "positive_months_22"],ascending=False)
    best_months=sm.sort_values(["positive_months_22",
                                "total_net_1x_account_return_pct"],ascending=False)
    cols=["timeframe","sl_points","tp_points","risk_reward_ratio","trades",
          "wins","losses","win_rate_pct","total_net_1x_account_return_pct",
          "profit_factor","positive_months_22","negative_months_22",
          "max_trade_close_drawdown_pct","source"]
    top=best[cols].head(15)
    besttime=best.groupby("timeframe",sort=False).head(1)
    quality={"source":"Delta India BTCUSD perpetual 1m historical OHLCV",
       "earliest_utc":str(raw.index[0]),"latest_utc":str(raw.index[-1]),
       "raw_candles":len(raw),"gaps":gaps,
       "pairs_three":THREE,"pairs_four":FOUR,
       "total_combinations":len(sm),
       "reused_combinations":sum(sm.source.eq("prior_fixed_grid_reused")),
       "fresh_combinations":sum(sm.source.eq("newly_replayed")),
       "signal_stats":signal_stats,
       "fee_with_gst_per_side":FEE, "adverse_slippage_points_per_side":SLIP,
       "only_new_ledger":"Prior pair ledgers preserved in original analysis/supertrend_ema921_fixed_grid/trade_ledger.csv.gz",
       "historical_exposure_warning":"Data already studied; this is sensitivity analysis, NOT a blind out-of-sample validation"}
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2))
    lines=["# BTCUSD Supertrend EMA9/21 — fixed 1:3 and 1:4 RR sensitivity",
      "", "**Partial-overlap robustness audit — not a new trading strategy.**",
      "",
      "## Best net 1x account return in each independent timeframe",
      "",besttime[cols].to_markdown(index=False,floatfmt=".2f"),
      "",
      "## Top 15 by compounded net 1x account return",
      "",top.to_markdown(index=False,floatfmt=".2f"),
      "",
      "## Top 12 by positive IST months",
      "",best_months[cols].head(12).to_markdown(index=False,floatfmt=".2f"),
      "",
      "## All combinations, after-cost returns (%)",
      ""]
    for tf in TFS:
        sub=sm[sm.timeframe.eq(f"{tf}m")]
        show=sub[["sl_points","tp_points","risk_reward_ratio","trades",
                  "wins","losses","win_rate_pct","total_net_1x_account_return_pct",
                  "positive_months_22","max_trade_close_drawdown_pct"]]
        lines += [f"### {tf}m", "", show.to_markdown(index=False,floatfmt=".2f"),""]
    lines += ["## Caveats and audit detail", "",
      f"- Total {len(sm)} independent configuration/timeframe results, including {int(quality['fresh_combinations'])} fresh simulations and {int(quality['reused_combinations'])} exact prior-run results (not re-run).",
      "- Entries and exit methodology unchanged: completed Supertrend ATR10×3 + EMA9/21 same-timeframe alignment, enter next 1m open; actual 1m OHLC stop-first touch; month-end flatten.",
      "- 1× notional account return, 0.05% taker fee per side, 18% GST on fee, $5 adverse slippage per side.",
      "- No actual spread/market impact, funding, live fills, margin, liquidation or real-time order validity model.",
      "- The original 2025-Jan IST month lacks first 330 minutes; all subsequent IST months complete.",
      "- All 2025–2026 periods have been seen in earlier research, so parameter search here cannot prove an out-of-sample edge.",
      "- Newly computed per-trade ledger in new_trade_ledger.csv.gz. Prior exact pair ledgers remain under analysis/supertrend_ema921_fixed_grid/.",
      "", "## Machine-readable outputs",
      "",
      "- summary.csv",
      "- monthly_results.csv",
      "- new_trade_ledger.csv.gz",
      "- quality.json",
      "- NOVELTY_CHECK.md",""]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines))
    print("DONE",json.dumps({"tested":int(len(sm)),"fresh":int(quality['fresh_combinations']),
        "reused":int(quality['reused_combinations']),
        "positive_overall":int((sm.total_net_1x_account_return_pct>0).sum()),
        "max_profitable_months":int(sm.positive_months_22.max())}),flush=True)
    print("BEST",best.head(3)[cols].to_json(orient="records"),flush=True)

if __name__=="__main__":
    main()
