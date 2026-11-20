#!/usr/bin/env python3
"""BTC 48-hour breakout: actual 1m trailing activation and worse-fill stress.

Selected entry rule was frozen on BTC 2025 in earlier experiment. This
research varies only exit mechanics with a small declared family and checks
baseline versus original Stage17 run_one at 0bps with exact NAV/trade parity.
Each execution fee+GST and adverse slippage on both sides; no fake maker fills.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit
from research_every_candle_200 import FEE, SLIPPAGE, read_archive
import research_new_independent_1h_edge_20261120 as indep
import research_swing_donchian_stage17 as original

OUT=Path("analysis/independent_48h_breakout_exit_cost_stress_20261120")
MONTHS=indep.MONTHS
# trail ATR distance, activation in initial risk-R, takeprofit cap in R;
# no finite target is encoded by cap=0. 14-day original time cap unchanged.
EXITS=[
 ("original_trail2",2.0,0.,0.),
 ("trail1p5",1.5,0.,0.),
 ("trail2p5",2.5,0.,0.),
 ("activate1R_trail2",2.0,1.,0.),
 ("activate2R_trail2",2.0,2.,0.),
 ("activate3R_trail2",2.0,3.,0.),
 ("activate1R_trail1p5",1.5,1.,0.),
 ("activate2R_trail1p5",1.5,2.,0.),
 ("activate2R_trail3",3.0,2.,0.),
 ("trail2_cap5R",2.0,0.,5.),
 ("trail2_cap8R",2.0,0.,8.),
 ("activate2R_trail2_cap8R",2.0,2.,8.),
]
COST_BPS=(0,2,5,10)

@njit(cache=True)
def run_one_stressed(O,H,L,C,T,mid,segment_start,signal,updates,atr,ref_close,
                     trail_mult,activate_R,target_R,extra_slip_bps,n_months):
    equity=100.
    open_equity=equity
    entry_fill=0.
    entry_mid=0.
    entry_unix=-1
    entry_k=-1
    entry_risk=0.
    stop=0.
    side=0
    best=0.
    trades=[]
    month_end=np.full(n_months,np.nan)
    entries=np.zeros(n_months,np.int32)
    exposure=np.zeros(n_months,np.int32)
    peak=equity;maxdd=0.
    for k in range(len(O)):
        # Source outage: forced exit at last observed price, not a realistic
        # executable outage exit. Expose in report. Same as original.
        if k>0 and segment_start[k]==k and side!=0:
            old=k-1
            exitmid=C[old]
            fill=exitmid-side*(SLIPPAGE+extra_slip_bps*exitmid/10000.)
            net=side*(fill-entry_fill)-FEE*(entry_fill+fill)
            netR=net/entry_risk
            equity=open_equity*(1+.005*netR)
            trades.append((entry_unix,T[old],side,entry_risk,net,netR,3,entry_k,old))
            side=0
            if equity>peak:peak=equity
            maxdd=max(maxdd,(peak-equity)/peak)
        reverse=False
        # Trail only from completed preceding 1h bar, at first 1m opening
        # following completed hour. Activation based on previous 1m observed
        # favorable extreme; no current minute OHLC is used before its exit.
        if side!=0 and updates[k] and np.isfinite(atr[k]):
            favorable=side*(best-entry_mid)/entry_risk
            if favorable+1e-12>=activate_R:
                proposed=ref_close[k]-side*trail_mult*atr[k]
                if side==1 and proposed>stop:stop=proposed
                if side==-1 and proposed<stop:stop=proposed
        if side!=0:
            exposure[mid[k]]=1
            hit=(L[k]<=stop) if side==1 else (H[k]>=stop)
            target=entry_mid+side*target_R*entry_risk
            hit_target=(target_R>0 and ((H[k]>=target) if side==1 else (L[k]<=target)))
            if hit:
                outmid=min(O[k],stop) if side==1 else max(O[k],stop)
                reason=0
            elif hit_target:
                outmid=target
                reason=4
            elif k-entry_k>=14*24*60:
                outmid=O[k]
                reason=1
            elif signal[k]==-side:
                outmid=O[k]
                reason=2
                reverse=True
            else:
                reason=-1
            if reason>=0:
                fill=outmid-side*(SLIPPAGE+extra_slip_bps*outmid/10000.)
                net=side*(fill-entry_fill)-FEE*(entry_fill+fill)
                netR=net/entry_risk
                equity=open_equity*(1+.005*netR)
                trades.append((entry_unix,T[k],side,entry_risk,net,netR,reason,entry_k,k))
                side=0
                if equity>peak:peak=equity
                maxdd=max(maxdd,(peak-equity)/peak)
        if side==0 and not reverse and signal[k]!=0 and np.isfinite(atr[k]):
            risk=2.*atr[k]
            if 100<=risk<=10000:
                side=int(signal[k])
                entry_mid=O[k]
                entry_fill=entry_mid+side*(SLIPPAGE+extra_slip_bps*entry_mid/10000.)
                entry_risk=risk
                stop=entry_mid-side*risk
                best=entry_mid
                entry_k=k
                entry_unix=T[k]
                open_equity=equity
                entries[mid[k]]+=1
                exposure[mid[k]]=1
        # Track max favorable excursion AFTER deciding the current minute's
        # stop/target outcome; usable only on the subsequent 1H completion.
        if side!=0:
            if side==1 and H[k]>best:best=H[k]
            elif side==-1 and L[k]<best:best=L[k]
        if k==len(O)-1 or mid[k+1]!=mid[k]:
            mark=equity
            if side!=0:
                outmid=C[k]
                fill=outmid-side*(SLIPPAGE+extra_slip_bps*outmid/10000.)
                net=side*(fill-entry_fill)-FEE*(entry_fill+fill)
                mark=open_equity*(1+.005*net/entry_risk)
            month_end[mid[k]]=mark
    return trades,month_end,entries,exposure,maxdd

def metrics(month):
    x=np.asarray(month,float)
    if not np.isfinite(x).all() or (x<=-100).any():raise ValueError("Invalid NAV")
    nav=np.cumprod(1+x/100)
    peak=np.maximum.accumulate(np.r_[1,nav])[1:]
    return dict(return_pct=float(100*(nav[-1]-1)),
                positive=int((x>1e-9).sum()),losing=int((x<-1e-9).sum()),
                flat=int((abs(x)<=1e-9).sum()),
                monthly_dd_pct=float(100*np.max(1-nav/peak)),
                worst_month_pct=float(x.min()))
def month_returns(marks):
    return np.r_[100*(marks[0]/100-1),100*(marks[1:]/marks[:-1]-1)][:22]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,seg_start,_,quality=read_archive()
    mid,labels=original.build_months(f)
    h=indep.hourly_features(f)
    cfg=indep.CONFIGS[[x[0] for x in indep.CONFIGS].index("break48_trend")]
    sig,updates,atr,ref=indep.configure_signals(f,h,seg_start,cfg)
    op=f.open.to_numpy(np.float64);hi=f.high.to_numpy(np.float64)
    lo=f.low.to_numpy(np.float64);cl=f.close.to_numpy(np.float64)
    t=f.time.to_numpy(np.int64)
    # First ensure our independently coded 1m engine EXACTLY reproduces
    # original Stage17 for zero-activation, zero-extra-slip, no-TP case.
    r0,m0,_,_,_=original.run_one(op,hi,lo,cl,t,mid,seg_start,sig,updates,atr,ref,2.,len(labels))
    nr,nm,_,_,_=run_one_stressed(op,hi,lo,cl,t,mid,seg_start,sig,updates,atr,ref,
                                2.,0.,0.,0,len(labels))
    worst=float(np.max(np.abs(m0-nm)))
    if worst>.00001 or len(r0)!=len(nr):
        raise AssertionError(f"Native engine parity FAIL: monthend NAV drift {worst}, trades {len(r0)}/{len(nr)}")
    for a,b in zip(r0,nr):
        if a[0]!=b[0] or a[1]!=b[1] or abs(a[5]-b[5])>1e-7:
            raise AssertionError("Native trade parity FAIL")
    print("NATIVE_1M_COST_ENGINE_PARITY",json.dumps(dict(trades=len(nr),max_monthend_nav_drift=worst)))
    results=[];months=[];ledger=[]
    for name,trail,act,tp in EXITS:
        for stress in COST_BPS:
            trades,marks,entries,expo,dd=run_one_stressed(
                op,hi,lo,cl,t,mid,seg_start,sig,updates,atr,ref,
                trail,act,tp,stress,len(labels))
            mr=month_returns(marks)
            a=metrics(mr);tr=metrics(mr[:12]);check=metrics(mr[12:])
            netRs=np.array([x[5] for x in trades],float)
            wins=netRs[netRs>0].sum();loss=-netRs[netRs<0].sum()
            pf=float(wins/loss) if loss>0 else None
            train_entry_count=sum(int(row[0])<int(pd.Timestamp("2026-01-01",tz="Asia/Kolkata").tz_convert("UTC").timestamp()) for row in trades)
            result=dict(exit_rule=name,trailing_ATR=trail,activate_R=act,TP_R=tp,
                extra_slip_bps_side=stress,trades=len(trades),trades_2025=train_entry_count,
                net_R_pf=pf,mean_R=float(netRs.mean()) if len(netRs) else None,
                max_trade_to_trade_dd_pct=dd*100,
                net2025=tr["return_pct"],positive2025=tr["positive"],
                dd2025=tr["monthly_dd_pct"],net2026=check["return_pct"],
                positive2026=check["positive"],net22=a["return_pct"],
                positive22=a["positive"],losing22=a["losing"],flat22=a["flat"],
                max_monthend_dd22=a["monthly_dd_pct"])
            results.append(result)
            months.extend(dict(exit_rule=name,extra_slip_bps_side=stress,
                month_ist=m,net_account_pct=float(v)) for m,v in zip(MONTHS,mr))
            if stress==0:
                ledger.extend(dict(exit_rule=name,entry_unix=int(v[0]),exit_unix=int(v[1]),
                    side=int(v[2]),initial_risk_pts=float(v[3]),net_pts=float(v[4]),
                    net_R=float(v[5]),exit_code=int(v[6])) for v in trades)
    df=pd.DataFrame(results)
    train=df[(df.extra_slip_bps_side==5)&(df.trades_2025>=35)&
             (df.net2025>0)&(df.net_R_pf>1)].copy()
    train["selection_BTC2025"]=train.net2025+.5*train.positive2025-.75*train.dd2025
    train=train.sort_values(["selection_BTC2025","net2025"],ascending=False,kind="stable")
    pick=str(train.iloc[0].exit_rule) if not train.empty else "original_trail2"
    print("STRESS_5BP_BTC2025_RANK",train.to_json(orient="records"))
    print("FROZEN_BTC2025_EXIT_SELECTION",pick)
    for variant in dict.fromkeys(("original_trail2",pick)):
        for stress in COST_BPS:
            r=df[(df.exit_rule==variant)&(df.extra_slip_bps_side==stress)].iloc[0]
            print("NATIVE_EXIT_STRESS_RESULT",r.to_json())
    df.to_csv(OUT/"all_exit_coststress_results.csv",index=False)
    pd.DataFrame(months).to_csv(OUT/"monthly_stressed_account_NAV.csv",index=False)
    pd.DataFrame(ledger).to_csv(OUT/"actual_1m_trades.csv.gz",compression="gzip",index=False)
    (OUT/"BTC2025_cost_stressed_selection.json").write_text(json.dumps({"chosen":pick},indent=2))
    (OUT/"limitations.json").write_text(json.dumps(dict(
      source_quality=quality,parity_trades=len(nr),
      original_vs_new_engine_max_drift=worst,exit_configurations=EXITS,
      extra_slip_bps_side=COST_BPS,
      fills="0.05% taker/side +18%GST and 5 BTC points adverse/side PLUS 0/2/5/10bp extra adverse market slippage each side",
      notes=[
       "Causal 1H signal from complete candles; stops fill on 1m OHLC stop first and gap open",
       "ATR trailing only after completed 1h candle; no lookahead from present minute",
       "Winner selected on BTC 2025 ONLY under highest stress +5bp each side",
       "BTC 2026 already researched and only chronological check, not pristine OOS",
       "No native ETH validation",
       "No actual historical funding, orderbook spread, contract minimums or exchange-level simultaneous margin engine",
       "Gross simulation uses 0.5% NAV fractional exposure and 3x theoretical leverage filter",
       "Missing BTC source gaps at first IST hours Jan2025 and Oct31 2026",
       "Not approved for real-money use, no live orders"
      ]),indent=2,default=str))
    print("BREAK48_NATIVE_EXIT_STRESS_BACKTEST_COMPLETE",json.dumps({"chosen":pick}))
if __name__=="__main__":main()
