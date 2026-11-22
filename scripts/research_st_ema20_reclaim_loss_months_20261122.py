#!/usr/bin/env python3
"""Causal loss-month audit and multi-family filter research for BTCUSD EMA20 Reclaim.

Keep the established 1H ST(10,3) / EMA20 Reclaim entry, volume >=1.25x,
2% entry-relative SL and selected percentage-based profit-lock ladders.
Signals must be from COMPLETED previous 1H candles. Research historical data
2025-01 to 2026-10 using 1m OHLC paths. No month-name avoidance rules.

Comparisons:
  * baseline 2%-3%-5% and 2%-2.5%-3%-5% and 1.75%-2%-3%-5% ladders
  * causal single gates / dual gates / limited triples,
  * 2025-only ranked training with unoptimized 2026 chronological validation
  * entire 22-month ranking (explicitly labelled as in-sample hindsight)
  * all losing-month trades, feature values and year/month attribution.
Never interpret these as independent forward-validated live results.
"""
from __future__ import annotations
import itertools
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_st_ema20_initial_sl_grid_20261122 import eng, prepare_entries, run, summarize, PATHS

OUT=Path("analysis/st_ema20_reclaim_loss_months_20261122")
MONTHS=list(pd.period_range("2025-01","2026-10",freq="M").astype(str))
YEAR_SPLIT=12
LADDERS={
 "L235":(2.,3.,5.),
 "L22535":(2.,2.5,3.,5.),
 "L175235":(1.75,2.,3.,5.),
}
BASE_ID="L235"
MIN_TRAIN_TRADES=13
MIN_TEST_TRADES=9

def indicator_features(h):
    out=h.copy()
    out["volume_ratio"]=out.volume/out.volume.shift(1).rolling(20,min_periods=20).mean().replace(0,np.nan)
    out["atr_pct"]=100*out.atr/out.close
    out["atr_expansion"]=out.atr/out.atr.shift(1).rolling(20,min_periods=20).mean().replace(0,np.nan)
    out["ema_slope_pct"]=100*out.side*(out.ema-out.ema.shift(4))/out.close
    out["ema_gap_pct"]=100*out.side*(out.close-out.ema)/out.close
    out["supertrend_gap_pct"]=100*out.side*(out.close-out.supertrend_line)/out.close
    delta=out.close.diff()
    gains=delta.clip(lower=0).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    losses=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    out["rsi14"]=100-100/(1+gains/losses.replace(0,np.nan))
    out["dir_rsi14"]=np.where(out.side==1,out.rsi14,100-out.rsi14)

    up=out.high.diff(); down=-out.low.diff()
    pdm=pd.Series(np.where((up>down)&(up>0),up,0.),index=out.index)
    mdm=pd.Series(np.where((down>up)&(down>0),down,0.),index=out.index)
    tr=pd.concat([out.high-out.low,(out.high-out.close.shift()).abs(),
                  (out.low-out.close.shift()).abs()],axis=1).max(axis=1)
    atr14=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean().replace(0,np.nan)
    pdi=100*pdm.ewm(alpha=1/14,adjust=False,min_periods=14).mean()/atr14
    mdi=100*mdm.ewm(alpha=1/14,adjust=False,min_periods=14).mean()/atr14
    dx=100*(pdi-mdi).abs()/(pdi+mdi).replace(0,np.nan)
    out["adx14"]=dx.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    out["hourly_body_atr"]=abs(out.close-out.open)/out.atr.replace(0,np.nan)
    out["hourly_range_atr"]=(out.high-out.low)/out.atr.replace(0,np.nan)
    ist=out.index.tz_convert("Asia/Kolkata")
    out["signal_hour_ist"]=ist.hour
    out["signal_weekday_ist"]=ist.dayofweek
    side=out.side.to_numpy()
    age=np.zeros(len(out),dtype=int)
    for j in range(1,len(age)):
        age[j]=age[j-1]+1 if side[j]==side[j-1] else 0
    out["supertrend_age_hours"]=age
    return out

def signal_table(entries,h):
    rows=[]
    cols=["volume_ratio","atr_pct","atr_expansion","ema_slope_pct",
          "ema_gap_pct","supertrend_gap_pct","dir_rsi14","adx14",
          "hourly_body_atr","hourly_range_atr","signal_hour_ist",
          "signal_weekday_ist","supertrend_age_hours"]
    for i,e in enumerate(entries):
        r=h.loc[pd.Timestamp(e["signal"])]
        row=dict(entry_id=i,side=e["side"],side_name="LONG" if e["side"]==1 else "SHORT",
            signal_utc=e["signal"],entry_index=e["entry_j"],
            entry_utc=str(h.index[0]+pd.Timedelta(minutes=int(e["entry_j"]))),
            entry_mid_price=float(e["entry"]),year=str(pd.Timestamp(e["signal"]).year))
        for c in cols:row[c]=float(r[c])
        rows.append(row)
    return pd.DataFrame(rows)

def gates(f):
    N=len(f)
    gates=[]
    seen=set()
    def add(category,name,mask):
        a=np.asarray(mask,dtype=bool)
        # Exclude unrestricted or zero-signal gates, or redundant exact masks.
        count=int(a.sum())
        if count==0 or count==N:return
        packed=tuple(a.tolist())
        if packed in seen:return
        seen.add(packed)
        gates.append(dict(category=category,name=name,mask=a,count=count))
    def threshold(category,col,mins=(),maxs=()):
        v=f[col].to_numpy(float)
        for lo in mins:
            add(category,f"{col} >= {lo:g}",np.isfinite(v)&(v>=lo))
        for hi in maxs:
            add(category,f"{col} <= {hi:g}",np.isfinite(v)&(v<=hi))

    # All values are available by the close of the signal H1 candle.
    threshold("volume","volume_ratio",mins=(1.5,1.75,2.,2.25,2.5,3.),
                                    maxs=(1.5,1.75,2.,2.5,3.,4.,5.,7.5))
    threshold("atr_pct","atr_pct",mins=(.35,.5,.75,1.,1.25,1.5,2.),
                                    maxs=(.5,.75,1.,1.25,1.5,2.,2.5,3.,4.))
    threshold("atr_expand","atr_expansion",mins=(.75,.9,1.,1.1,1.2,1.4,1.6),
                                          maxs=(.75,.9,1.,1.1,1.25,1.5,2.))
    threshold("ema_slope","ema_slope_pct",mins=(-.2,0.,.05,.1,.2,.3),
                                             maxs=(-.2,0.,.1,.2,.3,.5))
    threshold("ema_gap","ema_gap_pct",mins=(0.,.05,.1,.2,.3,.5,.75),
                                         maxs=(.1,.2,.3,.5,.75,1.,1.5))
    threshold("st_gap","supertrend_gap_pct",mins=(.1,.3,.5,.75,1.,1.5,2.),
                                                maxs=(.5,1.,1.5,2.,3.,5.))
    threshold("rsi","dir_rsi14",mins=(45.,50.,55.,60.,65.,70.,75.),
                                     maxs=(45.,50.,55.,60.,65.,70.,75.))
    threshold("adx","adx14",mins=(10.,15.,20.,25.,30.,35.,40.),
                                    maxs=(15.,20.,25.,30.,35.,40.,50.))
    threshold("body","hourly_body_atr",mins=(.1,.2,.35,.5,.75,1.),
                                            maxs=(.15,.25,.5,.75,1.,1.5))
    threshold("range","hourly_range_atr",mins=(.5,.75,1.,1.25,1.5,2.),
                                             maxs=(.75,1.,1.25,1.5,2.,2.5))
    threshold("age","supertrend_age_hours",mins=(3.,6.,12.,24.,48.,72.),
                                              maxs=(3.,6.,12.,24.,48.,72.,120.,240.))
    w=f.signal_weekday_ist.to_numpy(float)
    hour=f.signal_hour_ist.to_numpy(float)
    add("weekday","weekday Mon-Fri",w<=4)
    add("weekday","weekday Mon-Thu",w<=3)
    add("weekday","weekday Tue-Fri",(w>=1)&(w<=4))
    add("weekday","weekday Sat-Sun",w>=5)
    add("weekday","weekday exclude Friday",w!=4)
    add("weekday","weekday exclude Monday",w!=0)
    for start,end in ((0,6),(6,12),(12,18),(18,24),
                      (0,12),(12,24),(0,18),(6,18),(6,24),(18,6)):
        mask=(hour>=start)&(hour<end) if start<end else (hour>=start)|(hour<end)
        add("session",f"IST {start:02d}-{end:02d}",mask)
    add("direction","LONG only",f.side.to_numpy()==1)
    add("direction","SHORT only",f.side.to_numpy()==-1)
    print("Unique causal gates:",len(gates),flush=True)
    return gates

def compute_case_arrays(records):
    out={}
    for (ladder_id,path),r in records.items():
        assert len(r)==62,len(r)
        P=np.zeros((len(r),len(MONTHS)),dtype=np.float64)
        ix={k:i for i,k in enumerate(MONTHS)}
        entry_count_2025=np.zeros(len(r),dtype=bool)
        entry_count_2026=np.zeros(len(r),dtype=bool)
        years=np.zeros(len(r),dtype=int)
        exts=[]
        for i,x in r.iterrows():
            if x.exit_reason=="still_open":
                exts.append(pd.NaT);continue
            stamp=pd.Timestamp(x.exit_utc).tz_convert("Asia/Kolkata")
            exts.append(pd.Timestamp(x.exit_utc))
            if stamp.strftime("%Y-%m") in ix:
                P[i,ix[stamp.strftime("%Y-%m")]]=float(x.net_usd)
                years[i]=stamp.year
                entry_count_2025[i]=(stamp.year==2025)
                entry_count_2026[i]=(stamp.year==2026)
        out[(ladder_id,path)]=dict(P=P,
            times=pd.to_datetime(exts,utc=True),
            year25=entry_count_2025,year26=entry_count_2026,
            eligible=years!=0,raw=r)
    return out

def metric(mask, case):
    x=case["P"][mask].sum(axis=0)
    y25=x[:YEAR_SPLIT];y26=x[YEAR_SPLIT:]
    tr25=int((mask&case["year25"]).sum())
    tr26=int((mask&case["year26"]).sum())
    return dict(p25=int((y25>1e-8).sum()),p26=int((y26>1e-8).sum()),
        p22=int((x>1e-8).sum()),loss_months=int((x< -1e-8).sum()),
        flat_months=int((np.abs(x)<=1e-8).sum()),
        net25=round(float(y25.sum()),6),net26=round(float(y26.sum()),6),
        net22=round(float(x.sum()),6),tr25=tr25,tr26=tr26,
        trades=tr25+tr26)

def paired_stats(mask,cases,ladder_id):
    out=[metric(mask,cases[(ladder_id,p)]) for p in PATHS]
    return {
        "months_min":min(x["p22"] for x in out),
        "months_max":max(x["p22"] for x in out),
        "profit25_min":min(x["p25"] for x in out),
        "profit26_min":min(x["p26"] for x in out),
        "lossmonths_max":max(x["loss_months"] for x in out),
        "flatmonths_max":max(x["flat_months"] for x in out),
        "net25_min":min(x["net25"] for x in out),
        "net25_max":max(x["net25"] for x in out),
        "net26_min":min(x["net26"] for x in out),
        "net26_max":max(x["net26"] for x in out),
        "net22_min":min(x["net22"] for x in out),
        "net22_max":max(x["net22"] for x in out),
        "trade25_min":min(x["tr25"] for x in out),
        "trade26_min":min(x["tr26"] for x in out),
        "trades_min":min(x["trades"] for x in out),
    }

def validate(cases, features):
    allon=np.ones(len(features),dtype=bool)
    control={"L235":{"open_high_low_close":(14,13.522615),
                     "open_low_high_close":(15,13.746743)}}
    for path,(p,n) in control["L235"].items():
        x=metric(allon,cases[("L235",path)])
        assert x["p22"]==p,(path,x)
        assert abs(x["net22"]-n)<.00001,(path,x)

def best_ranks(df):
    valid=df[(df.trade25_min>=MIN_TRAIN_TRADES)&(df.trade26_min>=MIN_TEST_TRADES)]
    # CHRONOLOGICAL evaluation: rank by ONLY 2025 and see how 2026 behaves.
    chronological=valid.sort_values(
       ["profit25_min","net25_min","trade25_min","complexity"],
       ascending=[False,False,False,True]).head(40)
    # Whole-sample hindsight, explicitly not genuine OOS.
    both=valid[(valid.net25_min>0)&(valid.net26_min>0)&(valid.net22_min>0)]
    hindsight=both.sort_values(["months_min","net22_min","profit26_min","complexity"],
                              ascending=[False,False,False,True]).head(40)
    onlyone=valid[valid.complexity==1].sort_values(
       ["months_min","net22_min"],ascending=False).head(30)
    returns=both.sort_values("net22_min",ascending=False).head(30)
    return chronological,hindsight,onlyone,returns

def build_loss_audit(cases,f):
    rows=[]; trade_rows=[]
    for path in PATHS:
        case=cases[("L235",path)]
        t=case["raw"].copy()
        feat=f.reset_index(drop=True).add_prefix("signal_")
        t=pd.concat([t.reset_index(drop=True),feat],axis=1)
        t["month_ist"]=pd.to_datetime(t.exit_utc,utc=True).dt.tz_convert(
            "Asia/Kolkata").dt.strftime("%Y-%m")
        t=t[t.month_ist.isin(MONTHS)].copy()
        trade_rows.append(t)
        for mon in MONTHS:
            x=t[t.month_ist==mon].copy()
            net=float(x.net_usd.sum())
            rows.append(dict(path=path,month=mon,
               status="profit" if net>1e-8 else "loss" if net< -1e-8 else "flat",
               net_usd=round(net,6),trades=len(x),
               winning_trades=int((x.net_usd>0).sum()),
               losing_trades=int((x.net_usd<0).sum()),
               initial_stop_exits=int((x.exit_reason=="initial_stop").sum()),
               supertrend_flip_exits=int((x.exit_reason=="supertrend_flip").sum()),
               profit_lock_exits=int((x.exit_reason=="profit_lock").sum()),
               worst_trade_net_usd=round(float(x.net_usd.min()),6) if len(x) else 0,
               losing_trade_entry_utcs="; ".join(x.loc[x.net_usd<0,"entry_utc"].astype(str).tolist()),
               losing_trade_exit_reasons="; ".join(x.loc[x.net_usd<0,"exit_reason"].astype(str).tolist())))
    return pd.DataFrame(rows),pd.concat(trade_rows,ignore_index=True)

def main():
    engine=eng();engine.smoke_test()
    m,h,nfiles=engine.load()
    h=indicator_features(engine.features(h))
    entries=prepare_entries(engine,m,h,"reclaim")
    assert len(entries)==62,len(entries)
    f=signal_table(entries,h)
    assert len(f)==62
    records={}
    for name,ladder in LADDERS.items():
        for path in PATHS:
            t=run(engine,m,h,entries,"reclaim",path,"2%","pct",2.0,ladder_override=ladder)
            assert len(t)==62,len(t)
            records[(name,path)]=t
    cases=compute_case_arrays(records)
    validate(cases,f)

    # The gating mask applies at the FIRST candidate of a Supertrend cycle:
    # skipping a candidate does not retroactively select a different candidate.
    gate_list=gates(f)
    train_test=np.logical_or(cases[("L235",PATHS[0])]["year25"],cases[("L235",PATHS[0])]["year26"])
    num_gates=len(gate_list)
    config_masks={("all",):np.ones(len(f),dtype=bool)}
    for g in gate_list:
        config_masks[(g["name"],)]=g["mask"]
    # Distinct primitive feature families only. Do not use month/year as a gate.
    for a,b in itertools.combinations(gate_list,2):
        if a["category"]==b["category"]:continue
        z=a["mask"]&b["mask"]
        cnt=int(z.sum())
        if cnt<MIN_TRAIN_TRADES+MIN_TEST_TRADES: continue
        config_masks[(a["name"],b["name"])]=z
    print("Single + pair candidate masks",len(config_masks),flush=True)

    # Rank two-gate combinations on 2025 only to select a limited third gate.
    pair_scores=[]
    for key,mask in config_masks.items():
        if len(key)!=2:continue
        t=paired_stats(mask,cases,BASE_ID)
        if t["trade25_min"]<MIN_TRAIN_TRADES or t["trade26_min"]<MIN_TEST_TRADES:continue
        pair_scores.append((t["profit25_min"],t["net25_min"],len(key),key))
    pair_scores.sort(reverse=True)
    ranked_pairs=[x[-1] for x in pair_scores[:90]]
    cats={g["name"]:g["category"] for g in gate_list}
    for pair in ranked_pairs:
        for g in gate_list:
            if g["category"] in {cats[z] for z in pair}:continue
            mask=config_masks[pair]&g["mask"]
            config_masks[tuple(sorted(pair+(g["name"],)))]=mask
    print("Total entry filter combinations (unpruned)",len(config_masks),flush=True)

    # Deduplicate masks from different human-readable settings to avoid
    # claiming statistically independent tests for equivalent decisions.
    unique={}
    for key,mask in config_masks.items():
        if int(mask.sum())<MIN_TRAIN_TRADES+MIN_TEST_TRADES:continue
        signature=np.packbits(mask).tobytes()
        if signature not in unique or len(key)<len(unique[signature][0]):
            unique[signature]=(key,mask)
    print("Distinct tradable selection masks",len(unique),flush=True)
    rows=[]
    for ix,(key,mask) in enumerate(unique.values()):
        base=dict(filter_name=" AND ".join(key),complexity=0 if key==("all",) else len(key),
                  selected_entries=int(mask.sum()),family=BASE_ID)
        for ladder in LADDERS:
            stats=paired_stats(mask,cases,ladder)
            rows.append(dict(**base,ladder=ladder,**stats))
        if (ix+1)%2000==0:print("Scored",ix+1,"filters",flush=True)
    raw=pd.DataFrame(rows)
    chronological,hindsight,onlyone,topnet=best_ranks(raw)
    lossmonths,tradeaudit=build_loss_audit(cases,f)
    OUT.mkdir(parents=True,exist_ok=True)
    raw.to_csv(OUT/"all_filter_grid.csv",index=False)
    chronological.to_csv(OUT/"top_2025_selected_2026_validation.csv",index=False)
    hindsight.to_csv(OUT/"top_22_months_hindsight.csv",index=False)
    onlyone.to_csv(OUT/"best_single_gate_filters.csv",index=False)
    topnet.to_csv(OUT/"highest_net_both_years.csv",index=False)
    lossmonths.to_csv(OUT/"baseline_monthly_audit.csv",index=False)
    tradeaudit.to_csv(OUT/"baseline_trade_feature_audit.csv",index=False)
    f.to_csv(OUT/"signal_entry_features.csv",index=False)

    baseline=raw[(raw.filter_name=="all")&(raw.ladder=="L235")]
    assert len(baseline)==1
    report=(
        "# EMA20 Reclaim — causal filters, losing-month audit and chronological check\n\n"
        f"Baseline 62 fills, **{len(MONTHS)} months**, {len(m):,} 1m candles, "
        f"{len(gate_list)} causal primitive filters and {len(unique):,} unique signal-selection masks, "
        f"tested across 3 step-lock ladders and 2 possible 1m OHLC paths.\n\n"
        "## Frozen settings and failure analysis\n\n"
        "ST(10,3) + 1H EMA20 Reclaim, signal volume ratio >=1.25 (no maximum), 2% initial stop, 1m execution, "
        "0.001 BTC, taker fee/GST and 5 BTC points slippage per side.\n\n"
        "Filtering is applied using **only completed signal-hour information**, not the subsequently realized losing months. "
        "A skipped first candidate is NOT replaced by a future entry in that Supertrend cycle.\n\n"
        "### Original baseline\n\n"+baseline.to_markdown(index=False)+"\n\n"
        "### Baseline negative months by assumed intraminute price path\n\n"
        +lossmonths[lossmonths.status=="loss"].to_markdown(index=False)+"\n\n"
        "## Selected using 2025 only — measured on 2026 unchanged\n\n"
        +chronological.head(25).to_markdown(index=False)+"\n\n"
        "## Best 22-month HISTORICAL scores (includes 2026 in selection: IN-SAMPLE, optimistic)\n\n"
        +hindsight.head(25).to_markdown(index=False)+"\n\n"
        "## Highest nets with both calendar years positive\n\n"
        +topnet.head(15).to_markdown(index=False)+"\n\n"
        "### Important caveats\n\n"
        "- The 2026 period already influenced prior ladder research; this is a chronological split, not a pristine untouched holdout.\n"
        "- Multi-parameter hindsight selection has severe multiple-testing/overfitting risk, especially with only 62 trades.\n"
        "- The execution replay assumes hypothetical within-1m price ordering and immediate stop amendments, NOT actual live fills.\n"
        "- Funding, margin, mark-price liquidation, order-book depth, spread gaps and real slippage beyond assumed values are excluded.\n"
        "- Realized drawdown excludes floating adverse excursion; one-position-per-cycle rule is maintained.\n"
    )
    (OUT/"RESEARCH_REPORT.md").write_text(report)
    (OUT/"quality.json").write_text(json.dumps({
        "source":"Delta Exchange India BTCUSD 1m OHLCV",
        "lookback_ist_months":[MONTHS[0],MONTHS[-1]],
        "signal":{"timeframe":"1H","supertrend_atr":10,"supertrend_mult":3,"entry":"EMA20 Reclaim","volume_ratio_min":1.25},
        "execution":{"timeframe":"1m","initial_stop_pct":2.,"step_lock_ladders":LADDERS,
                     "qty_btc":engine.QTY,"fee_gst_side":engine.FEE,"slippage_btc_points_leg":engine.SLIP},
        "audit":{"total_source_1m_candles":len(m),"qualifying_entries":len(entries),
                 "primitive_entry_gates":num_gates,"unique_entry_filters":len(unique),
                 "backtest_configs":len(raw),"price_paths":len(PATHS)},
        "validation":"Reclaim 2-3-5% initial2% exact historical baseline verified in both paths",
        "bias":"2025 selection / 2026 diagnostic only; previously explored data is NOT untouched holdout"
    },indent=2)+"\n")
    print("SUCCESS",OUT,flush=True)
    print("BASE",baseline.to_string(index=False),flush=True)
    print("CHRONO 2025 selected, 2026 diagnostic",flush=True)
    print(chronological.head(8).to_string(index=False),flush=True)
    print("IN-SAMPLE HISTORICAL",flush=True)
    print(hindsight.head(10).to_string(index=False),flush=True)

if __name__=="__main__":
    main()
