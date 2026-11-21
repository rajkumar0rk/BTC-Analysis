#!/usr/bin/env python3
"""Stage 18 Strategy 2 ONLY: full 1-minute execution replay of Daily Donchian.
Independent 0.5%-risk NAV, monthly IST mark-to-market; no core sleeve or 75/25
blending. The original Stage17 55D/EMA50/2ATR/3ATR/14day rules are preserved.
Selection is 2025-only; 2026 is research-exposed, NOT a genuine OOS validation.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit
from research_every_candle_200 import read_archive, FEE, SLIPPAGE
import research_swing_donchian_stage17 as original
OUT=Path("analysis/stage18_independent_donchian_20261121")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
def case(name,days=55,trend="ema50_agrees",initial_atr=2.,trail_atr=3.,
         hold_days=14,opposite=True,history=120,
         min_break_atr=0.,min_volume_ratio=0.,
         atr_ratio_min=None,atr_ratio_max=None,side="both"):
    return dict(name=name,days=days,trend=trend,initial_atr=initial_atr,
        trail_atr=trail_atr,hold_days=hold_days,opposite=opposite,history=history,
        min_break_atr=min_break_atr,min_volume_ratio=min_volume_ratio,
        atr_ratio_min=atr_ratio_min,atr_ratio_max=atr_ratio_max,side=side)
CASES=[
 case("original_daily55_2atr_sl_3atr_trail"),
 case("channel20",days=20),case("channel30",days=30),
 case("channel40",days=40),case("channel70",days=70),
 case("channel80",days=80),
 case("daily55_trail2",trail_atr=2),
 case("daily55_trail2p5",trail_atr=2.5),
 case("daily55_trail3p5",trail_atr=3.5),
 case("daily55_trail4",trail_atr=4),
 case("daily55_trail5",trail_atr=5),
 case("daily55_sl1p5",initial_atr=1.5),
 case("daily55_sl2p5",initial_atr=2.5),
 case("daily55_sl3",initial_atr=3),
 case("daily55_hold7",hold_days=7),
 case("daily55_hold21",hold_days=21),
 case("daily55_hold30",hold_days=30),
 case("daily55_no_opposite_exit",opposite=False),
 case("daily55_no_ema50",trend="no_trend_filter"),
 case("daily55_long_only",side="long"),
 case("daily55_short_only",side="short"),
 case("daily55_breakout_0p2atr",min_break_atr=.2),
 case("daily55_breakout_0p5atr",min_break_atr=.5),
 case("daily55_volume_ge1",min_volume_ratio=1.),
 case("daily55_volume_ge1p5",min_volume_ratio=1.5),
 case("daily55_atr_ratio_le1",atr_ratio_max=1.),
 case("daily55_atr_ratio_ge1",atr_ratio_min=1.),
 case("daily55_history80",history=80),
 case("daily55_history90",history=90),
 case("channel20_history80",days=20,history=80),
 case("channel30_history80",days=30,history=80),
 case("channel40_history80",days=40,history=80),
 case("channel20_2atrtrail",days=20,trail_atr=2),
 case("channel20_4atrtrail",days=20,trail_atr=4),
 case("channel30_2p5atrtrail",days=30,trail_atr=2.5),
 case("channel30_4atrtrail",days=30,trail_atr=4),
 case("channel40_2p5atrtrail",days=40,trail_atr=2.5),
 case("channel40_4atrtrail",days=40,trail_atr=4),
 case("channel55_sl1p5_trail2p5",initial_atr=1.5,trail_atr=2.5),
 case("channel55_sl3_trail4",initial_atr=3.,trail_atr=4),
 case("channel55_trail4_hold21",trail_atr=4.,hold_days=21),
 case("channel55_trail3_hold21",trail_atr=3.,hold_days=21),
 case("channel30_trail3_hold21",days=30,hold_days=21),
 case("channel20_trail3_hold21",days=20,hold_days=21),
 case("channel30_long_only",days=30,side="long"),
 case("channel30_short_only",days=30,side="short"),
 case("channel20_long_only",days=20,side="long"),
 case("channel20_short_only",days=20,side="short"),
 case("channel30_no_ema",days=30,trend="no_trend_filter"),
 case("channel40_no_ema",days=40,trend="no_trend_filter"),
 case("channel30_history80_trail4",days=30,history=80,trail_atr=4),
 case("channel20_history80_trail4",days=20,history=80,trail_atr=4),
 case("channel30_history80_hold21",days=30,history=80,hold_days=21),
 case("channel40_history80_hold21",days=40,history=80,hold_days=21),
]
@njit(cache=True)
def replay(O,H,L,C,T,month_id,seg_start,signal,updates,atr,refclose,
           trail_mult,initial_mult,max_hold,exit_opposite,extra_bps,n_months):
    """Copy Stage17's causal stop-first simulator with explicit variable settings.
    Extra slippage is applied at every entry, stop/exit and monthly liquidation.
    """
    eq=100.
    open_eq=eq
    entry_fill=0.
    entry_mid=0.
    entry_time=-1
    entry_k=-1
    initial_risk=0.
    stop=0.
    side=0
    trades=[]
    month_equity=np.full(n_months,np.nan)
    month_entries=np.zeros(n_months,np.int32)
    month_exposure=np.zeros(n_months,np.int32)
    peak=eq
    maxdd=0.
    for k in range(len(O)):
        if k>0 and seg_start[k]==k and side!=0:
            old=k-1
            mid=C[old]
            exit_fill=mid-side*(SLIPPAGE+extra_bps*mid)
            net=side*(exit_fill-entry_fill)-FEE*(entry_fill+exit_fill)
            nr=net/initial_risk
            eq=open_eq*(1.+.005*nr)
            trades.append((entry_time,T[old],side,initial_risk,net,nr,3,entry_k,old))
            side=0
            if eq>peak:peak=eq
            maxdd=max(maxdd,(peak-eq)/peak)
        reverse=False
        # The completed daily close and its ATR are known at start of minute k.
        if side!=0 and updates[k] and np.isfinite(atr[k]):
            proposed=refclose[k]-side*trail_mult*atr[k]
            if side==1 and proposed>stop:stop=proposed
            if side==-1 and proposed<stop:stop=proposed
        if side!=0:
            month_exposure[month_id[k]]=1
            hit=(L[k]<=stop) if side==1 else (H[k]>=stop)
            if hit:
                mid=min(O[k],stop) if side==1 else max(O[k],stop)
                reason=0
            elif k-entry_k>=max_hold:
                mid=O[k]
                reason=1
            elif exit_opposite and signal[k]==-side:
                mid=O[k]
                reason=2
                reverse=True
            else: reason=-1
            if reason>=0:
                exit_fill=mid-side*(SLIPPAGE+extra_bps*mid)
                net=side*(exit_fill-entry_fill)-FEE*(entry_fill+exit_fill)
                nr=net/initial_risk
                eq=open_eq*(1.+.005*nr)
                trades.append((entry_time,T[k],side,initial_risk,net,nr,reason,entry_k,k))
                side=0
                if eq>peak:peak=eq
                maxdd=max(maxdd,(peak-eq)/peak)
        if side==0 and not reverse and signal[k]!=0 and np.isfinite(atr[k]):
            risk=initial_mult*atr[k]
            if 100<=risk<=10000:
                side=int(signal[k])
                entry_mid=O[k]
                entry_fill=entry_mid+side*(SLIPPAGE+extra_bps*entry_mid)
                initial_risk=risk
                stop=entry_mid-side*risk
                entry_time=T[k]
                entry_k=k
                open_eq=eq
                month_entries[month_id[k]]+=1
                month_exposure[month_id[k]]=1
        if k==len(O)-1 or month_id[k+1]!=month_id[k]:
            mark=eq
            if side!=0:
                mid=C[k]
                close_fill=mid-side*(SLIPPAGE+extra_bps*mid)
                net=side*(close_fill-entry_fill)-FEE*(entry_fill+close_fill)
                mark=open_eq*(1.+.005*net/initial_risk)
            month_equity[month_id[k]]=mark
    return trades,month_equity,month_entries,month_exposure,maxdd

def monthly_stats(x):
    v=np.asarray(x,float)
    nav=np.cumprod(1+v/100)
    peak=np.maximum.accumulate(np.r_[1.,nav])[1:]
    return dict(ret=float(100*(nav[-1]-1)),pos=int((v>1e-9).sum()),
        loss=int((v< -1e-9).sum()),flat=int((abs(v)<=1e-9).sum()),
        max_monthend_dd=float(100*np.max(1-nav/peak)),worst_month=float(v.min()))

def filter_signals(f,bars,c):
    b=bars
    if c["history"]!=120:
        b=bars.copy()
        cnt=(b.complete.astype(int)*1440)
        b["history_ok"]=cnt.rolling(c["history"],min_periods=c["history"]).min().eq(1440)
    sig,updates,atr,close,num=original.signals(f,b,c["days"],c["trend"])
    # Only features from fully completed signal-day candles may change entry.
    if any([c["min_break_atr"],c["min_volume_ratio"],
            c["atr_ratio_min"] is not None,c["atr_ratio_max"] is not None,
            c["side"]!="both"]):
        upper=b.high.shift(1).rolling(c["days"],min_periods=c["days"]).max()
        lower=b.low.shift(1).rolling(c["days"],min_periods=c["days"]).min()
        vratio=b.volume/(b.volume.shift(1).rolling(20,min_periods=20).mean())
        aratio=b.atr/b.median_prior_atr
        indices=f.index.get_indexer(b.index)
        for j,k in enumerate(indices):
            if k<0 or sig[k]==0:continue
            side=int(sig[k])
            if (c["side"]=="long" and side<0) or (c["side"]=="short" and side>0):
                sig[k]=0;continue
            dist=float((b.close.iat[j]-upper.iat[j]) if side>0 else
                       (lower.iat[j]-b.close.iat[j]))
            if dist< c["min_break_atr"]*float(b.atr.iat[j]):sig[k]=0;continue
            if c["min_volume_ratio"] and not (float(vratio.iat[j])>=c["min_volume_ratio"]):
                sig[k]=0;continue
            if c["atr_ratio_min"] is not None and not (float(aratio.iat[j])>=c["atr_ratio_min"]):
                sig[k]=0;continue
            if c["atr_ratio_max"] is not None and not (float(aratio.iat[j])<=c["atr_ratio_max"]):
                sig[k]=0;continue
    return sig,updates,atr,close,int((sig!=0).sum())

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,seg_start,_,quality=read_archive()
    mid,labels=original.build_months(f)
    nmonths=len(labels)
    assert labels[:22]==MONTHS
    O=f.open.to_numpy(np.float64);H=f.high.to_numpy(np.float64)
    L=f.low.to_numpy(np.float64);C=f.close.to_numpy(np.float64)
    T=f.time.to_numpy(np.int64)
    bars=original.higher_bars(f,"1D")
    baseline_c=CASES[0]
    sig,up,atr,cl,_=filter_signals(f,bars,baseline_c)
    reference=original.run_one(O,H,L,C,T,mid,seg_start,sig,up,atr,cl,3.,nmonths)
    ref_month=reference[1]
    actual=replay(O,H,L,C,T,mid,seg_start,sig,up,atr,cl,3.,2.,20160,True,0.,nmonths)
    diff=float(np.max(np.abs(ref_month-actual[1])))
    if diff>1e-8:raise AssertionError(f"Daily55 Stage17 baseline replay differs: {diff}")
    saved=pd.read_csv("analysis/institutional_discovery_stage17_swing_breakout/monthly_mark_to_market.csv")
    saved=saved[saved.model=="1D_channel_55_ema50_agrees_trail_3atr"].set_index("month_ist")
    source_expected=saved.reindex(MONTHS).month_return_pct.to_numpy(float)
    returns=100*(ref_month[1:22]/ref_month[:21]-1)
    returns=np.r_[100*(ref_month[0]/100-1),returns]
    source_delta=float(np.max(np.abs(source_expected-returns)))
    if source_delta>.002:raise AssertionError(f"Stored 22m Donchian monthly mismatch: {source_delta}")
    print("DONCHIAN_BASELINE_PARITY",json.dumps(dict(max_equity_delta=diff,max_saved_month_pct_delta=source_delta,baseline_trades=len(reference[0]))))
    records=[];months=[];ledgers=[]
    for c in CASES:
        sig,up,atr,cl,seen=filter_signals(f,bars,c)
        for cost in (0,2,5):
            tr,nav,ents,exposure,dd=replay(O,H,L,C,T,mid,seg_start,
                sig,up,atr,cl,float(c["trail_atr"]),float(c["initial_atr"]),
                int(c["hold_days"])*1440,bool(c["opposite"]),cost/10000.,nmonths)
            rets=100*(nav[:22]/np.r_[100.,nav[:21]]-1)
            full=monthly_stats(rets);train=monthly_stats(rets[:12]);seen26=monthly_stats(rets[12:])
            netR=np.array([t[5] for t in tr if t[1]<int(pd.Timestamp("2026-11-01",tz="Asia/Kolkata").timestamp())],float)
            pf=float(netR[netR>0].sum()/-netR[netR<0].sum()) if (netR<0).any() else None
            records.append(dict(model=c["name"],extra_slippage_bps_side=cost,
                signals=seen,trades=len(tr),
                netR_profit_factor=pf,
                train_2025_return_pct=train["ret"],train_2025_pos=train["pos"],
                train_2025_loss=train["loss"],train_2025_dd=train["max_monthend_dd"],
                exposed_2026_return_pct=seen26["ret"],exposed_2026_pos=seen26["pos"],
                net_22_pct=full["ret"],positive_months=full["pos"],
                negative_months=full["loss"],flat_months=full["flat"],
                monthend_dd_pct=full["max_monthend_dd"],worst_month_pct=full["worst_month"]))
            months.extend(dict(model=c["name"],extra_slippage_bps_side=cost,
                month_ist=m,return_pct=float(v),month_equity=float(nav[i]),
                entries=int(ents[i]),exposure=int(exposure[i]))
                for i,(m,v) in enumerate(zip(MONTHS,rets)))
            if cost==0:
                ledgers.extend(dict(model=c["name"],entry_unix=int(t[0]),
                      exit_unix=int(t[1]),direction=int(t[2]),initial_risk_pts=float(t[3]),
                      net_points=float(t[4]),net_R=float(t[5]),
                      reason=["stop","time_cap","reverse","gap"][t[6]])
                     for t in tr)
    df=pd.DataFrame(records)
    mr=pd.DataFrame(months)
    rank=df[df.extra_slippage_bps_side==2].copy()
    # No 2026 value enters the ranking.
    rank["score_2025_only"]=rank.train_2025_return_pct+.2*rank.train_2025_pos-.8*rank.train_2025_dd
    rank=rank.sort_values(["score_2025_only","train_2025_return_pct"],ascending=False,kind="stable")
    selected=str(rank.iloc[0].model)
    df.to_csv(OUT/"donchian_standalone_results.csv",index=False)
    mr.to_csv(OUT/"donchian_monthly_mtm.csv",index=False)
    pd.DataFrame(ledgers).to_csv(OUT/"donchian_real_1m_trade_ledgers.csv.gz",index=False,compression="gzip")
    (OUT/"donchian_methodology.json").write_text(json.dumps(dict(
        family="Stage18 Strategy 2 only",
        chosen_on_2025_only=selected,source=quality,cases=CASES,baseline_parity_max_delta=diff,
        baseline_saved_month_diff_pct=source_delta,fee="0.05% taker per side incl 18% GST, 5 BTC points per side",
        stress="Additional adverse 0/2/5 bps per side applied to each entry/exit and mark",
        risk="0.5% NAV per initial ATR stop with fractional size",
        caveats=[
         "Stage17 exact 1m engine reproduced baseline including month-end MTM, not combined core sleeve",
         "No tick path, spread, depth, funding, liquidation or minimum contract lot rounding",
         "Historical 2025/2026 repeatedly researched; results exploratory and multiple-tested",
         "Gap forced exit at last observed 1m close is hypothetical and may be impossible live",
         "Long/short max one position at a time, next 1m open after daily confirmation",
         "2026-10-31 UTC missing from source; November 2026 incomplete"]),
         indent=2,default=str))
    for x in df[df.model.isin([selected,"original_daily55_2atr_sl_3atr_trail"])].to_dict("records"):
        print("DONCHIAN_AUDIT",json.dumps(x,default=str))
    print("DONCHIAN_2025_ONLY_RANK",rank[["model","trades","train_2025_return_pct",
          "train_2025_pos","exposed_2026_return_pct","net_22_pct",
          "positive_months","negative_months","netR_profit_factor"]].head(15).to_json(orient="records"))
    print("DONCHIAN_STANDALONE_DONE",json.dumps(dict(cases=len(CASES),selected=selected)))
if __name__=="__main__":main()
