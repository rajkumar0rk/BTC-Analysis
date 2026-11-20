#!/usr/bin/env python3
"""FROZEN BTC-2025-selected 48h breakout: native BTC/ETH 1m paired check.

No tuning against ETH, BTC 2026 or profitability after seeing outcomes.
Asset-specific 1m reads. Same 4H trend, 48 completed 1H Donchian, 2 ATR
initial stop/trailing on completed 1H bars. Risk 0.5% NAV, 3x theoretical
notional cap, single position PER asset. No hidden losing months.

BTC slippage baseline=adverse 5 BTC price points per side, same as prior
source. ETH slippage=adverse 1bp of entry/exit price each side: illustrative
rather than real historical L1. BOTH charge .05% taker+18%GST per side.
Extra pessimistic +2/+5bps each side sensitivity. Portfolio combines
0.25/0.5 capital allocations with no hidden leverage increase.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit
import research_every_candle_200 as source
import research_swing_donchian_stage17 as sw
import research_new_independent_1h_edge_20261120 as indep

OUT=Path("analysis/btc_eth_frozen_48h_breakout_20261120")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
FEE=0.0005*1.18
RISK=.005
MAX_LEVERAGE=3.
# All rules fixed before seeing native ETH outcome
STOP_ATR=2.
TRAIL_ATR=2.
CHANNEL_HOURS=48
ASSETS=("BTCUSD","ETHUSD")
EXTRA_COST_BPS=(0,2,5)

@njit(cache=True)
def replay(O,H,L,C,T,month_id,seg_start,sig,updates,ATR,reference,
           is_eth,extra_bps,nmonths):
    eq=100.;eq_at_entry=eq
    entry=0.;entry_fill=0.;entry_unix=-1;entry_k=-1
    risk=0.;stop=0.;side=0
    trades=[]
    monthly_marks=np.full(nmonths,np.nan,np.float64)
    peak=eq;maxdd=0.
    rejected_leverage=0
    for k in range(len(O)):
        if k>0 and seg_start[k]==k and side!=0:
            old=k-1;outmid=C[old]
            slip=(outmid*.0001 if is_eth else 5.)+extra_bps*outmid/10000.
            outfill=outmid-side*slip
            pnl=side*(outfill-entry_fill)-FEE*(entry_fill+outfill)
            eq=eq_at_entry*(1.+RISK*pnl/risk)
            trades.append((entry_unix,T[old],side,risk,pnl,pnl/risk,3))
            side=0
            if eq>peak:peak=eq
            maxdd=max(maxdd,(peak-eq)/peak)
        reverse=False
        if side!=0 and updates[k] and np.isfinite(ATR[k]):
            proposed=reference[k]-side*TRAIL_ATR*ATR[k]
            if side==1 and proposed>stop:stop=proposed
            if side==-1 and proposed<stop:stop=proposed
        if side!=0:
            hit=(L[k]<=stop) if side==1 else (H[k]>=stop)
            if hit:
                outmid=min(O[k],stop) if side==1 else max(O[k],stop)
                reason=0
            elif k-entry_k>=14*24*60:
                outmid=O[k];reason=1
            elif sig[k]==-side:
                outmid=O[k];reason=2;reverse=True
            else:reason=-1
            if reason>=0:
                slip=(outmid*.0001 if is_eth else 5.)+extra_bps*outmid/10000.
                outfill=outmid-side*slip
                pnl=side*(outfill-entry_fill)-FEE*(entry_fill+outfill)
                eq=eq_at_entry*(1.+RISK*pnl/risk)
                trades.append((entry_unix,T[k],side,risk,pnl,pnl/risk,reason))
                side=0
                if eq>peak:peak=eq
                maxdd=max(maxdd,(peak-eq)/peak)
        if side==0 and not reverse and sig[k]!=0 and np.isfinite(ATR[k]):
            r=2.*ATR[k]
            minrisk=2. if is_eth else 100.
            maxrisk=1000. if is_eth else 10000.
            if minrisk<=r<=maxrisk:
                implied=RISK*O[k]/r
                if implied>MAX_LEVERAGE:rejected_leverage+=1
                else:
                    side=int(sig[k]);entry=O[k]
                    slip=(entry*.0001 if is_eth else 5.)+extra_bps*entry/10000.
                    entry_fill=entry+side*slip
                    risk=r;stop=entry-side*r
                    entry_k=k;entry_unix=T[k];eq_at_entry=eq
        if k==len(O)-1 or month_id[k+1]!=month_id[k]:
            mark=eq
            if side!=0:
                mid=C[k]
                slip=(mid*.0001 if is_eth else 5.)+extra_bps*mid/10000.
                fill=mid-side*slip
                pnl=side*(fill-entry_fill)-FEE*(entry_fill+fill)
                mark=eq_at_entry*(1.+RISK*pnl/risk)
            monthly_marks[month_id[k]]=mark
    return trades,monthly_marks,maxdd,rejected_leverage

def monthly_pct(nav):
    if not np.isfinite(nav).all():raise AssertionError("Missing mark")
    return np.r_[100*(nav[0]/100-1.),100*(nav[1:]/nav[:-1]-1.)][:22]
def metrics(pcts):
    x=np.asarray(pcts)
    if (x<=-100).any():raise ValueError("Bankrupt account")
    growth=np.cumprod(1+x/100)
    peaks=np.maximum.accumulate(np.r_[1.,growth])[1:]
    return dict(net_pct=round(100*(growth[-1]-1),6),
       average_month_pct=round(float(x.mean()),6),
       median_month_pct=round(float(np.median(x)),6),
       profitable_months=int((x>1e-9).sum()),
       losing_months=int((x<-1e-9).sum()),
       flat_months=int((abs(x)<=1e-9).sum()),
       worst_month_pct=round(float(x.min()),6),
       max_monthend_dd_pct=round(float(100*np.max(1-growth/peaks)),6))
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    monthly={};reports=[];trade_rows=[];data_quality={}
    original_base=source.BASE
    for symbol in ASSETS:
        try:
            source.BASE=Path(f"data/delta_india/{symbol}/1m")
            f,seg_start,_,quality=source.read_archive()
        finally:
            source.BASE=original_base
        data_quality[symbol]=quality
        ids,months=sw.build_months(f)
        if months[:22]!=MONTHS:raise AssertionError("IST calendar mismatched")
        hour=indep.hourly_features(f)
        sg,updates,atr,ref=indep.configure_signals(f,hour,seg_start,
            ("frozen48",48,"break","4h","any",2.))
        O=f.open.to_numpy(np.float64);H=f.high.to_numpy(np.float64)
        L=f.low.to_numpy(np.float64);C=f.close.to_numpy(np.float64)
        T=f.time.to_numpy(np.int64)
        for stress in EXTRA_COST_BPS:
            trades,marks,dd,rejections=replay(
              O,H,L,C,T,ids,seg_start,sg,updates,atr,ref,symbol=="ETHUSD",
              stress,len(months))
            m=monthly_pct(marks)
            monthly[(symbol,stress)]=m
            rows=np.array([float(t[5]) for t in trades])
            pos=float(rows[rows>0].sum());neg=-float(rows[rows<0].sum())
            report=dict(market=symbol,extra_slip_bps_each_side=stress,
                completed_trades=len(trades),pf_net_R=round(pos/neg,6) if neg>0 else None,
                max_trade_close_dd_pct=round(float(dd*100),6),
                leverage_rejections=int(rejections),
                net_2025_pct=metrics(m[:12])["net_pct"],
                net_2026_JanOct_pct=metrics(m[12:])["net_pct"],**metrics(m))
            reports.append(report)
            print("FROZEN_48H_NATIVE_MARKET",json.dumps(report))
            if stress==0:
                trade_rows.extend(dict(market=symbol,entry_unix=int(t[0]),
                    exit_unix=int(t[1]),side=int(t[2]),risk_pts=float(t[3]),
                    net_pts=float(t[4]),net_R=float(t[5]),exit_reason_code=int(t[6]))
                    for t in trades)
    # At equal capital risk, blended 50/50 or 75/25 monthly NAV;
    # NOT additive account returns or doubling leverage.
    portfolios=[]
    for weight_ETH in (.25,.5,.75):
        for stress in EXTRA_COST_BPS:
            mix=(1-weight_ETH)*monthly[("BTCUSD",stress)]+weight_ETH*monthly[("ETHUSD",stress)]
            result=dict(weights_BTC=1-weight_ETH,weight_ETH=weight_ETH,
                 extra_slip_bps_each_side=stress,
                 net_2025_pct=metrics(mix[:12])["net_pct"],
                 net_2026_JanOct_pct=metrics(mix[12:])["net_pct"],
                 **metrics(mix))
            portfolios.append(result)
            print("BTC_ETH_FROZEN_PORTFOLIO",json.dumps(result))
            for m,v in zip(MONTHS,mix):
                reports.append(dict(market=f"{int((1-weight_ETH)*100)}BTC_{int(weight_ETH*100)}ETH",
                    extra_slip_bps_each_side=stress,month_ist=m,monthly_pct=float(v),
                    blend=True))
    # Honest, no selection: compare all weights, not choose on ETH heldout.
    pd.DataFrame([r for r in reports if not r.get("blend")]).to_csv(
        OUT/"native_market_summary.csv",index=False)
    pd.DataFrame(portfolios).to_csv(OUT/"all_weight_combinations.csv",index=False)
    pd.DataFrame([dict(market=sym,extra_slip_bps_each_side=s,month_ist=m,
            month_pct=float(v)) for (sym,s),series in monthly.items()
            for m,v in zip(MONTHS,series)]).to_csv(OUT/"each_asset_month.csv",index=False)
    pd.DataFrame(trade_rows).to_csv(OUT/"actual_trade_ledger.csv.gz",compression="gzip",index=False)
    (OUT/"quality_and_limitations.json").write_text(json.dumps(dict(
       data_quality=data_quality,frozen_rule="BTC2025 48 completed 1H Donchian, 4H and 1H EMA trends, 2 ATR initial/trailing, 14d time stop, 1m stop-first fills",
       BTC_baseline_adverse_slip="5 BTC/USD price points per side",
       ETH_baseline_adverse_slip="1bp of ETH price each side, illustrative",
       stress_bps_side=EXTRA_COST_BPS,
       costs="0.05% taker each side +18%GST",
       risk="0.5% initial NAV risk PER TRADE PER asset, max theoretical leverage 3x, capital weights fixed and capital-neutral",
       warnings=[
         "2025 train and 2026 chronology previously explored; no pristine holdout.",
         "Asset sizing assumes fractional quantities, no confirmed Delta integer contract lot or margin portfolio.",
         "Separate asset account NAVs are combined at month boundaries with no rebalancing transaction cost, not a real shared-margin multi-asset account.",
         "No actual funding, historical L1 spreads, maker eligibility, impact, tick-level ordering or liquidation.",
         "Known data gaps in source; excluded source gap transitions may be unrealizable in live trading.",
         "The same BTC-frozen rule is applied to ETH without ETH optimization; no future paper trading evidence.",
         "Do not infer monthly income consistency from profitable total NAV; every negative and flat month is retained."
       ],live_ready=False),indent=2,default=str))
    print("FROZEN_BTC_ETH_NATIVE_1M_BACKTEST_COMPLETE")
if __name__=="__main__":main()
