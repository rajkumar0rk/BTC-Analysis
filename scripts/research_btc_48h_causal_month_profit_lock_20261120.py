#!/usr/bin/env python3
"""BTCUSD frozen 48-hour breakout, real 1m exit replay + CAUSAL monthly locks.

The locked variant only uses net-R from already CLOSED trades in the current
IST month; it never knows if a month eventually ends winning/losing.
No hidden loss trades, no hindsight month weighting, no leverage escalation.
Only ORIGINAL 48h signal, unchanged 2ATR initial SL / 2ATR 1h-close trailer.
Research target is 22/22 positive net months, not guaranteed.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit
from research_every_candle_200 import read_archive, FEE, SLIPPAGE
from research_swing_donchian_stage17 import build_months, run_one as original_replay
from research_new_independent_1h_edge_20261120 import hourly_features, configure_signals

OUT=Path("analysis/btc_48h_month_profit_lock_20261120")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
# Guard values in realized net multiples of initial 2xATR risk, not dollars.
# Using prior completed trades' net PnL only and resetting each IST month.
# name, +month_profit_R_lock, -month_loss_R_halt
CASES=[
 ("unmodified",1e9,-1e9),
 ("profit_after_0p5R",0.5,-1e9),
 ("profit_after_1R",1.,-1e9),
 ("profit_after_2R",2.,-1e9),
 ("profit_after_3R",3.,-1e9),
 ("profit_after_4R",4.,-1e9),
 ("profit_after_5R",5.,-1e9),
 ("loss_after_minus_2R",1e9,-2.),
 ("loss_after_minus_3R",1e9,-3.),
 ("loss_after_minus_4R",1e9,-4.),
 ("profit_1R_loss_minus_2R",1.,-2.),
 ("profit_2R_loss_minus_2R",2.,-2.),
 ("profit_3R_loss_minus_3R",3.,-3.),
 ("profit_4R_loss_minus_3R",4.,-3.),
 ("profit_5R_loss_minus_3R",5.,-3.),
]
EXTRA_SLIP_BPS=(0,2,5)
RISK_FRACTION=.005

@njit(cache=True)
def guarded_replay(O,H,L,C,T,monid,seg_start,signal,updated,atr,reference,
                   monthly_profit_R_cap,monthly_loss_R_cap,extra_bps,nmon):
    eq=100.;open_eq=eq
    entry_mid=0.;entry_fill=0.;entry_unix=-1;entry_k=-1
    initial_risk=0.;stop=0.;side=0
    trades=[]
    marks=np.full(nmon,np.nan)
    entered=np.zeros(nmon,np.int32)
    held=np.zeros(nmon,np.int32)
    realized_month_R=np.zeros(nmon,np.float64)
    blocked_profit=np.zeros(nmon,np.int32)
    blocked_loss=np.zeros(nmon,np.int32)
    peak=eq;maxdd=0.
    for k in range(len(O)):
        if k>0 and seg_start[k]==k and side!=0:
            # Non-executable data-outage liquidation uses prior available close
            # consistently with the historical Stage17 baseline.
            old=k-1
            mid=C[old]
            fill=mid-side*(SLIPPAGE+extra_bps*mid/10000.)
            net=side*(fill-entry_fill)-FEE*(entry_fill+fill)
            netR=net/initial_risk
            eq=open_eq*(1.+RISK_FRACTION*netR)
            realized_month_R[monid[old]]+=netR
            trades.append((entry_unix,T[old],side,initial_risk,net,netR,3))
            side=0
            if eq>peak:peak=eq
            maxdd=max(maxdd,(peak-eq)/peak)
        reverse=False
        if side!=0 and updated[k] and np.isfinite(atr[k]):
            candidate=reference[k]-side*2.*atr[k]
            if side==1 and candidate>stop:stop=candidate
            if side==-1 and candidate<stop:stop=candidate
        if side!=0:
            held[monid[k]]=1
            stop_hit=(L[k]<=stop) if side==1 else (H[k]>=stop)
            if stop_hit:
                exit_mid=min(O[k],stop) if side==1 else max(O[k],stop)
                reason=0
            elif k-entry_k>=14*24*60:
                exit_mid=O[k];reason=1
            elif signal[k]==-side:
                exit_mid=O[k];reason=2;reverse=True
            else:reason=-1
            if reason>=0:
                fill=exit_mid-side*(SLIPPAGE+extra_bps*exit_mid/10000.)
                net=side*(fill-entry_fill)-FEE*(entry_fill+fill)
                netR=net/initial_risk
                eq=open_eq*(1.+RISK_FRACTION*netR)
                realized_month_R[monid[k]]+=netR
                trades.append((entry_unix,T[k],side,initial_risk,net,netR,reason))
                side=0
                if eq>peak:peak=eq
                maxdd=max(maxdd,(peak-eq)/peak)
        if side==0 and not reverse and signal[k]!=0 and np.isfinite(atr[k]):
            if realized_month_R[monid[k]]>=monthly_profit_R_cap:
                blocked_profit[monid[k]]+=1
            elif realized_month_R[monid[k]]<=monthly_loss_R_cap:
                blocked_loss[monid[k]]+=1
            else:
                risk=2.*atr[k]
                if 100<=risk<=10000:
                    side=int(signal[k])
                    entry_mid=O[k]
                    entry_fill=entry_mid+side*(SLIPPAGE+extra_bps*entry_mid/10000.)
                    initial_risk=risk
                    stop=entry_mid-side*risk
                    entry_k=k
                    entry_unix=T[k]
                    open_eq=eq
                    entered[monid[k]]+=1
                    held[monid[k]]=1
        if k==len(O)-1 or monid[k+1]!=monid[k]:
            mark=eq
            if side!=0:
                mid=C[k]
                fill=mid-side*(SLIPPAGE+extra_bps*mid/10000.)
                net=side*(fill-entry_fill)-FEE*(entry_fill+fill)
                mark=open_eq*(1.+RISK_FRACTION*net/initial_risk)
            marks[monid[k]]=mark
    return trades,marks,entered,held,blocked_profit,blocked_loss,realized_month_R,maxdd

def month_pct(marks):
    if not np.isfinite(marks).all():raise AssertionError("Missing month")
    return np.r_[100*(marks[0]/100-1.),100*(marks[1:]/marks[:-1]-1.)][:22]

def stats(series):
    x=np.asarray(series,float)
    if not np.isfinite(x).all() or np.any(x<=-100):raise AssertionError("Invalid NAV")
    compounded=np.cumprod(1.+x/100.)
    peak=np.maximum.accumulate(np.r_[1.,compounded])[1:]
    return dict(compounded_net_pct=float(100*(compounded[-1]-1.)),
                average_month_pct=float(np.mean(x)),
                median_month_pct=float(np.median(x)),
                positive=int(np.count_nonzero(x>1e-9)),
                positive_gt_0p1pct=int(np.count_nonzero(x>=.1)),
                negative=int(np.count_nonzero(x<-1e-9)),
                flat=int(np.count_nonzero(np.abs(x)<=1e-9)),
                worst_month_pct=float(x.min()),
                max_monthend_dd_pct=float(100*np.max(1.-compounded/peak)))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,seg_start,_,quality=read_archive()
    monid,months=build_months(f)
    if months[:22]!=MONTHS:raise AssertionError("Month labels mismatch")
    h=hourly_features(f)
    signal,updated,atr,reference=configure_signals(
        f,h,seg_start,("frozen_48h",48,"break","4h","any",2.))
    O=f.open.to_numpy(np.float64)
    H=f.high.to_numpy(np.float64)
    L=f.low.to_numpy(np.float64)
    C=f.close.to_numpy(np.float64)
    T=f.time.to_numpy(np.int64)
    orig_trades,orig_nav,_,_,_=original_replay(
        O,H,L,C,T,monid,seg_start,signal,updated,atr,reference,2.,len(months))
    records=[];rows=[];ledgers=[]
    for case,profit,loss in CASES:
        for slip in EXTRA_SLIP_BPS:
            trades,marks,entered,held,blockedp,blockedl,monthlyR,dd=guarded_replay(
                O,H,L,C,T,monid,seg_start,signal,updated,atr,reference,
                profit,loss,slip,len(months))
            if case=="unmodified" and slip==0:
                drift=float(np.max(np.abs(orig_nav-marks)))
                if drift>1e-9 or len(orig_trades)!=len(trades):
                    raise AssertionError(f"Original Stage17 trade/month baseline not replicated: NAV drift {drift} trades {len(orig_trades)} {len(trades)}")
                for old,new in zip(orig_trades,trades):
                    if old[0]!=new[0] or old[1]!=new[1] or abs(float(old[5])-float(new[5]))>1e-8:
                        raise AssertionError("Original Stage17 trade baseline differs")
                print("ORIGINAL_48H_BASELINE_RECONCILED",json.dumps(dict(trades=len(trades),max_nav_diff=drift)))
            monthly=month_pct(marks)
            full=stats(monthly);train=stats(monthly[:12]);check=stats(monthly[12:])
            R=np.array([float(x[5]) for x in trades],dtype=float)
            gains=R[R>0].sum();losses=-R[R<0].sum()
            pf=float(gains/losses) if losses>0 else None
            rec=dict(variant=case,month_profit_lock_R=None if profit>=1e8 else profit,
                     month_loss_halt_R=None if loss<=-1e8 else loss,
                     extra_adverse_slip_bps_each_side=slip,
                     trade_count=len(trades),trade_PF=pf,
                     blocked_by_profit=int(blockedp.sum()),blocked_by_loss=int(blockedl.sum()),
                     trade_close_dd_pct=float(dd*100),
                     train_2025_net_pct=train["compounded_net_pct"],
                     train_2025_positive=train["positive"],
                     train_2025_gt_0p1=train["positive_gt_0p1pct"],
                     train_2025_dd_pct=train["max_monthend_dd_pct"],
                     check_2026_JanOct_net_pct=check["compounded_net_pct"],
                     check_2026_positive=check["positive"],
                     full_22_net_pct=full["compounded_net_pct"],
                     avg_month_pct=full["average_month_pct"],
                     median_month_pct=full["median_month_pct"],
                     positive_months=full["positive"],
                     positive_gt_0p1pct_months=full["positive_gt_0p1pct"],
                     negative_months=full["negative"],flat_months=full["flat"],
                     worst_month_pct=full["worst_month_pct"],
                     max_monthend_dd_pct=full["max_monthend_dd_pct"],
                     achieved_22_of_22=full["positive"]==22,
                     achieved_22_of_22_gt_0p1=full["positive_gt_0p1pct"]==22)
            records.append(rec)
            rows.extend(dict(variant=case,slippage_bps_side=slip,
                month_ist=month,net_pct=float(net),
                entry_count=int(entered[i]),held=bool(held[i]),
                blocked_profit=int(blockedp[i]),blocked_loss=int(blockedl[i]),
                realized_closed_trade_R=float(monthlyR[i]))
                for i,(month,net) in enumerate(zip(MONTHS,monthly)))
            if slip==0:
                ledgers.extend(dict(variant=case,entry_unix=int(x[0]),
                  exit_unix=int(x[1]),side=int(x[2]),initial_stop_pts=float(x[3]),
                  net_price_points=float(x[4]),net_R=float(x[5]),
                  exit_reason_code=int(x[6])) for x in trades)
    df=pd.DataFrame(records)
    train=df[df.extra_adverse_slip_bps_each_side==2].copy()
    # STRICTLY chronological training-only selection: prioritize month count
    # and meaningful positive months, then net after cost and DD. Only BTC
    # 2025 used; full 2026 results are completely excluded from the ranking.
    train["score_BTC2025"]=(
       4.*train.train_2025_gt_0p1+
       2.*train.train_2025_positive+
       .25*train.train_2025_net_pct-
       .25*train.train_2025_dd_pct)
    train=train.sort_values(["score_BTC2025","train_2025_net_pct"],ascending=False,kind="stable")
    choice=str(train.iloc[0].variant)
    print("BTC2025_MONTHLY_CONSISTENCY_RANKING",train[[
       "variant","score_BTC2025","train_2025_positive","train_2025_gt_0p1",
       "train_2025_net_pct","check_2026_JanOct_net_pct","positive_months",
       "positive_gt_0p1pct_months","worst_month_pct"]].to_json(orient="records"))
    print("FROZEN_2025_SELECTED",choice)
    for name in dict.fromkeys(["unmodified",choice]):
        for stress in EXTRA_SLIP_BPS:
            r=df[(df.variant==name)&(df.extra_adverse_slip_bps_each_side==stress)].iloc[0]
            print("MONTHLY_PROFIT_LOCK_RESULT",r.to_json())
    print("ALL_22_MONTH_CHECK",df[df.extra_adverse_slip_bps_each_side==2][[
        "variant","train_2025_net_pct","check_2026_JanOct_net_pct",
        "full_22_net_pct","positive_months","negative_months",
        "flat_months","worst_month_pct","achieved_22_of_22"
    ]].to_json(orient="records"))
    df.to_csv(OUT/"all_monthly_profit_lock_variants.csv",index=False)
    pd.DataFrame(rows).to_csv(OUT/"all_22_months_and_rejected_signals.csv",index=False)
    pd.DataFrame(ledgers).to_csv(OUT/"all_native_trade_ledgers.csv.gz",compression="gzip",index=False)
    (OUT/"BTC2025_frozen_selection.json").write_text(json.dumps({"chosen":choice},indent=2))
    (OUT/"quality_and_limits.json").write_text(json.dumps(dict(
        source_quality=quality,variant_design=CASES,
        selection="BTC 2025 only under extra 2 bps adverse slippage per order side; 2026 not used",
        baseline_parity="Exact original 48h Stage17 198-trade/mark match required",
        methodology="Profit/loss locks block NEW signals based only on realized net risk multiples of already closed trades within current IST month; open trades managed unchanged",
        source_fills="0.05% taker fee each side plus GST18% and 5 BTC price points adverse slip/side; extra 0/2/5 bps per side",
        limits=[
          "No 22/22 claim without explicit count of actual positive calendar months; flat months fail.",
          "No artificial cash payout or hidden end-of-month oracle; realized closed trade R controls a future entry only.",
          "Closed trade net R risk fractions are simplified; contractual lot, margin and intraminute bid/ask not verified.",
          "BTC 2025 and BTC 2026 both repeatedly historically examined, not pristine prospective validation.",
          "Missing early-2025 and end-Oct2026 1m source data, no ETH native forward check for this variant.",
          "No funding, exact spread, liquidation or maker execution; month-end drawdown understates intramonth.",
          "Profit-lock can suppress good later trades, may lower net return or introduce zero/losing months.",
          "Do not modify live trading strategy or main branch; research only."
        ],live_ready=False),indent=2,default=str))
    print("CAUSAL_MONTHLY_PROFIT_LOCK_REPLAY_COMPLETE",json.dumps({"selected":choice}))
if __name__=="__main__":main()
