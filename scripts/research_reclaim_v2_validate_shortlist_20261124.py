#!/usr/bin/env python3
"""Independent 1-minute price-path replay for selected Reclaim V2 causal filters.

Rebuild all 62 frozen BTCUSD 1H EMA20 Reclaim signals from original historical
Delta OHLCV, select 55 locked V1 trades, apply candidate entry-time conditions
to skip a subset, then run the unchanged 2% initial SL, 2%-3%-5% milestone
stop engine for each 1m path. No new signals, reentry, leverage, exposure,
or strategy changes. Each locked originally profitable month's USD must not
decrease, and no other month may worsen, across BOTH 1m path models.
Exploratory in-sample only. Additional slippage stress is a P&L-only approximation.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_st_ema20_initial_sl_grid_20261122 import eng,prepare_entries,run,summarize,MONTHS,PATHS
from research_st_ema20_reclaim_loss_months_20261122 import indicator_features,signal_table

OUT=Path("analysis/reclaim_v2_shortlist_validation_20261124")
FEE_MODEL_NOTE="0.001 BTC, 0.00059 taker fee with GST per side; 5 BTC-points slippage per leg"
STOP=2.
LADDER=(2.,3.,5.)
EPS=1.5e-6
EXPECTED={
 "LOCKED_V1":(55,15,5,2,20.037378,20.261506),
 "OR_2_COND":(50,16,4,2,25.963505,26.187633),
 "OR_3_COND":(47,17,2,3,28.425616,28.649744),
 "OR_AND_4_COND":(47,17,2,3,25.291921,25.516049),
 "OR_AND_4_COND_NO_SIDE":(47,17,2,3,25.609247,25.833375),
 "OR_AND_5_COND":(45,17,3,2,31.699673,31.923801),
}

def gate_masks(f):
    # Every variable below is a property of the completed SIGNAL 1H candle.
    vol=f.volume_ratio.to_numpy(float)
    adx=f.adx14.to_numpy(float)
    atr_exp=f.atr_expansion.to_numpy(float)
    candle_range=f.hourly_range_atr.to_numpy(float)
    candle_body=f.hourly_body_atr.to_numpy(float)
    st_gap=f.supertrend_gap_pct.to_numpy(float)
    ema_gap=f.ema_gap_pct.to_numpy(float)
    rsi=f.dir_rsi14.to_numpy(float)
    side=f.side.to_numpy(int)
    return {
      "LOCKED_V1":np.ones(len(f),bool),
      "OR_2_COND":(adx<=30)|(st_gap<=1.25),
      "OR_3_COND":(atr_exp>=1.2)|(adx<=30)|(candle_range<=1),
      "OR_AND_4_COND":((adx<=25)|(candle_range<=1)|(side==-1))&(vol<=3.5),
      "OR_AND_4_COND_NO_SIDE":((adx<=20)|(candle_range<=1)|(ema_gap>=.15))&(rsi<=60),
      "OR_AND_5_COND":((adx<=30)|(st_gap<=1.25)) & ((atr_exp>=1.2)|(st_gap>=1)|(candle_range<=1.25)),
    }

def eval_stress(t,extra):
    # This is NOT a full different-slip execution replay, only completed P&L
    # deduction on the exact same trades/time stamps as the baseline.
    w=t.copy()
    w.loc[w.exit_reason!="still_open","net_usd"]=(
         w.loc[w.exit_reason!="still_open","net_usd"]-2*0.001*extra)
    return w

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    engine=eng();engine.smoke_test()
    m,h,files=engine.load()
    h=indicator_features(engine.features(h))
    original_entries=prepare_entries(engine,m,h,"reclaim")
    assert len(original_entries)==62
    allf=signal_table(original_entries,h)
    frozen=(allf.ema_gap_pct<=1)&(allf.ema_slope_pct>=-.2)&(
             allf.supertrend_gap_pct>=.5)
    IDs=np.flatnonzero(frozen.to_numpy()).tolist()
    frozen_entries=[original_entries[i] for i in IDs]
    features=allf.iloc[IDs].reset_index(drop=True)
    assert len(frozen_entries)==55
    masks=gate_masks(features)
    records=[];allmonths=[];details=[];stress=[]
    for name,mask in masks.items():
        assert isinstance(mask,np.ndarray) and len(mask)==55
        entries=[e for e,on in zip(frozen_entries,mask) if on]
        assert len(entries)==EXPECTED[name][0],(name,len(entries))
        for path_index,path in enumerate(PATHS):
            t=run(engine,m,h,entries,"reclaim",path,"2%","pct",STOP,ladder_override=LADDER)
            result,monthly=summarize(t,"reclaim","2%",path)
            _,ep,loss,flat,netA,netB=EXPECTED[name]
            assert result["profitable_months"]==ep,(name,path,result)
            assert result["losing_months"]==loss,(name,path,result)
            assert result["flat_months"]==flat,(name,path,result)
            net=netA if path_index==0 else netB
            assert abs(result["total_net_usd"]-net)<1e-5,(name,path,net,result)
            result.update(profile=name,excluded_entries=55-len(entries))
            records.append(result)
            monthly["profile"]=name
            allmonths.append(monthly)
            t["profile"]=name
            t["path"]=path
            details.append(t)
            for added in (0,2,5,10,15,20,30):
                stressed=eval_stress(t,added)
                s,mon=summarize(stressed,"reclaim","2%",path)
                stress.append(dict(profile=name,path=path,additional_points_per_leg=added,
                    effective_slippage_points_per_leg=5+added,
                    approximate_positive_months=s["profitable_months"],
                    approximate_losing_months=s["losing_months"],
                    approximate_flat_months=s["flat_months"],
                    approximate_net_usd=s["total_net_usd"]))
        print("Replayed",name,len(entries),"signals, two OHLC paths",flush=True)
    allmon=pd.concat(allmonths,ignore_index=True)
    baseline=allmon[allmon.profile=="LOCKED_V1"].set_index(["path","month_ist"])
    audit=[]
    for row in allmon.itertuples(index=False):
        b=baseline.loc[(row.path,row.month_ist)]
        diff=float(row.net_usd-b.net_usd)
        assert diff>=-EPS,(row.profile,row.path,row.month_ist,row.net_usd,b.net_usd)
        audit.append(dict(profile=row.profile,path=row.path,month_ist=row.month_ist,
           frozen_v1_net_usd=round(float(b.net_usd),6),
           candidate_net_usd=round(float(row.net_usd),6),
           delta_usd=round(diff,6),
           original_profitable=bool(b.net_usd>EPS),
           still_profitable=bool(row.net_usd>EPS),
           status="profit" if row.net_usd>EPS else "loss" if row.net_usd<-EPS else "flat"))
    audit=pd.DataFrame(audit)
    summary=pd.DataFrame(records)
    summary.to_csv(OUT/"verified_path_metrics.csv",index=False)
    audit.to_csv(OUT/"verified_22_month_audit.csv",index=False)
    pd.DataFrame(stress).to_csv(OUT/"cost_stress_APPROX_NOT_FILL_REPLAY.csv",index=False)
    pd.concat(details,ignore_index=True).to_csv(OUT/"verified_trade_ledger.csv",index=False)
    paired=[]
    for name,g in summary.groupby("profile"):
        assert len(g)==2
        paired.append(dict(profile=name,trades=int(g.trades.min()),
          profitable_months=int(g.profitable_months.min()),
          losing_months=int(g.losing_months.max()),
          flat_months=int(g.flat_months.max()),
          net_usd_min=float(g.total_net_usd.min()),
          net_usd_max=float(g.total_net_usd.max()),
          net_2025_min=float(g.net_2025.min()),
          net_2026_min=float(g.net_2026.min()),
          closed_equity_dd_pct_worst=float(g.max_realized_dd_pct.max()),
          wins=int(g.wins.min()),losses=int(g.losses.max()),
          initial_stop_exits=int(g.stopped_trades.max()),
          monthly_PnL_no_worse_both_paths=True))
    paired=pd.DataFrame(paired).sort_values(
       ["profitable_months","losing_months","net_usd_min"],
       ascending=[False,True,False])
    paired.to_csv(OUT/"paired_shortlist.csv",index=False)
    # Signal-level audit to enable exact explanation of skipped trades.
    base_selected=features.copy()
    for name,mask in masks.items():base_selected["selected_"+name]=mask
    base_selected.to_csv(OUT/"signal_selection_audit.csv",index=False)
    q=dict(date_window="2025-01..2026-10 IST",completed_months=22,
       raw_1m_bars=len(m),source_files=files,
       original_reclaim_signals=62,locked_reclaim_signals=55,
       profiles=list(masks),
       baseline_replay_validated_both_paths=True,
       all_22_months_net_non_decrease_verified_both_paths=True,
       simulated_1m_price_paths=list(PATHS),
       executed_on_original_1m_archive=True,quantity_btc=engine.QTY,
       costs=FEE_MODEL_NOTE,initial_SL_pct=STOP,profit_lock_pct=LADDER,
       limitations=["An OHLC path assumption is not tick-by-tick truth",
          "No funding, exchange margin, liquidation, order-book fill depth or stop amendment latency",
          "Approximate stress deductions do not rerun entry and exit triggers",
          "2025 and 2026 were reused in parameter selection: no untouched OOS period",
          "Low trade count and high-dimensional search imply severe overfitting risk"])
    (OUT/"quality.json").write_text(json.dumps(q,indent=2)+"\n")
    fmt=paired[["profile","trades","profitable_months","losing_months","flat_months",
       "net_usd_min","net_usd_max","closed_equity_dd_pct_worst"]]
    report=(
       "# Reclaim V2 — independent complete 1m historical replay of the shortlisted monthly winners\n\n"
       "Frozen Reclaim V1 exact entry and risk execution engine; skip-only pre-signal filters "
       "based on completed 1H candle properties. No replacement entry in a skipped Supertrend cycle.\n\n"
       "### Candidate comparison across two intraminute path assumptions\n\n"
       +fmt.to_markdown(index=False)+"\n\n"
       "### Interpretation\n\n"
       "- OR_3_COND achieves 17/22 but Oct 2025 net is only approximately $0.007, very fragile to extra costs.\n"
       "- OR_AND_4_COND achieves 17/22, 2 losing, 3 flat months, with stronger Oct 2025 profit cushion than OR_3_COND.\n"
       "- OR_AND_5_COND achieves 17/22, 3 losing, 2 flat months, higher historical net but more conditions.\n"
       "- All original 15 profitable months preserved in USD, no month on either path made worse under the original cost model.\n\n"
       "### Caveats\n\n"
       "Search on repeated in-sample Jan 2025-Oct 2026 history is highly optimized; "
       "no guarantee of future monthly consistency. Price-path models assume continuous intraminute paths, "
       "not real tick sequencing. Existing leverage/liquidation and exchange amendment mechanics unmodeled. "
       "Stress sensitivity is only a trade-level P&L cost adjustment, not a re-executed orderbook simulator.\n")
    (OUT/"RESEARCH_REPORT.md").write_text(report)
    print("SUCCESS: 1m archive replay agrees with saved trade-ledger filter study",flush=True)
    print(paired.to_string(index=False),flush=True)

if __name__=="__main__":
    main()
