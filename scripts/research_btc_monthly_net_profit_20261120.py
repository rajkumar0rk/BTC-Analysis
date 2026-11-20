#!/usr/bin/env python3
"""BTC MONTHLY NET RETURNS: risk-matched 1h breakout strategies on real 1m candles.

Not an extra-leverage or month-censoring optimization. Different signal
frequencies (12/24/36/48/72 hourly Donchian) and initial ATR-stop / trailing
ATR-stop produce different actual entries/exits on the 1m OHLC tape.
At most 0.5% NAV initial risk/trade and 3x implied notional leverage.
Select ONLY BTC-2025 after-cost score. BTC-2026 previously researched,
thus chronological check rather than pristine unseen holdout.
All months including losing months and zero-trade months are reported.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit
from research_every_candle_200 import read_archive, FEE, SLIPPAGE
from research_swing_donchian_stage17 import build_months, run_one as original_run
from research_new_independent_1h_edge_20261120 import hourly_features, configure_signals

OUT=Path("analysis/btc_monthly_net_returns_20261120")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
# All 20 variants declared BEFORE reading their outcomes. The 48h,2ATR/2ATR
# configuration is the immutable prior reference; no intra-period retuning.
# label, lookback completed 1h candles, initial risk ATR, trail ATR
CONFIGS=[
 ("prior_break48_stop2_trail2",48,2.,2.),
 ("break48_stop1p0_trail1p5",48,1.,1.5),
 ("break48_stop1p25_trail1p5",48,1.25,1.5),
 ("break48_stop1p5_trail1p5",48,1.5,1.5),
 ("break48_stop1p5_trail2",48,1.5,2.),
 ("break48_stop1p75_trail2",48,1.75,2.),
 ("break48_stop2_trail1p5",48,2.,1.5),
 ("break48_stop2_trail1p75",48,2.,1.75),
 ("break36_stop1p25_trail1p5",36,1.25,1.5),
 ("break36_stop1p5_trail2",36,1.5,2.),
 ("break36_stop2_trail2",36,2.,2.),
 ("break24_stop1p25_trail1p5",24,1.25,1.5),
 ("break24_stop1p5_trail2",24,1.5,2.),
 ("prior_break24_stop2_trail2",24,2.,2.),
 ("break12_stop1p25_trail1p5",12,1.25,1.5),
 ("break12_stop1p5_trail1p5",12,1.5,1.5),
 ("break12_stop2_trail2",12,2.,2.),
 ("break72_stop1p5_trail1p5",72,1.5,1.5),
 ("break72_stop2_trail1p5",72,2.,1.5),
 ("break72_stop2_trail2",72,2.,2.),
]
STRESS_BPS=(0,2,5,10)
RISK_NAV=.005
MAX_NOTIONAL=3.

@njit(cache=True)
def engine(O,H,L,C,T,month_id,seg_start,sig,upd,atr,ref,stop_atr,trail_atr,extra_bps,nmonths):
    equity=100.;open_equity=equity;entry_fill=0.;entry_mid=0.
    entry_unix=-1;entry_k=-1;initial_risk=0.;stop=0.;side=0
    trades=[]
    month_nav=np.full(nmonths,np.nan,np.float64)
    entries=np.zeros(nmonths,np.int32)
    expo=np.zeros(nmonths,np.int32)
    peak=equity;maxdd=0.;skipped_leverage=0
    for k in range(len(O)):
        if k>0 and seg_start[k]==k and side!=0:
            old=k-1
            mid=C[old]
            fill=mid-side*(SLIPPAGE+extra_bps*mid/10000.)
            pnl=side*(fill-entry_fill)-FEE*(entry_fill+fill)
            r=pnl/initial_risk
            equity=open_equity*(1.+RISK_NAV*r)
            trades.append((entry_unix,T[old],side,initial_risk,pnl,r,3,entry_k,old))
            side=0
            if equity>peak:peak=equity
            maxdd=max(maxdd,(peak-equity)/peak)
        reversed_exit=False
        if side!=0 and upd[k] and np.isfinite(atr[k]):
            newstop=ref[k]-side*trail_atr*atr[k]
            if side==1 and newstop>stop:stop=newstop
            if side==-1 and newstop<stop:stop=newstop
        if side!=0:
            expo[month_id[k]]=1
            hit=(L[k]<=stop) if side==1 else (H[k]>=stop)
            if hit:
                outmid=min(O[k],stop) if side==1 else max(O[k],stop)
                reason=0
            elif k-entry_k>=14*24*60:
                outmid=O[k];reason=1
            elif sig[k]==-side:
                outmid=O[k];reason=2;reversed_exit=True
            else:reason=-1
            if reason>=0:
                fill=outmid-side*(SLIPPAGE+extra_bps*outmid/10000.)
                pnl=side*(fill-entry_fill)-FEE*(entry_fill+fill)
                r=pnl/initial_risk
                equity=open_equity*(1.+RISK_NAV*r)
                trades.append((entry_unix,T[k],side,initial_risk,pnl,r,reason,entry_k,k))
                side=0
                if equity>peak:peak=equity
                maxdd=max(maxdd,(peak-equity)/peak)
        if side==0 and not reversed_exit and sig[k]!=0 and np.isfinite(atr[k]):
            risk=stop_atr*atr[k]
            # Existing engine rule: 100 <= 2ATR risk <= 10,000.
            # For smaller distances require no smaller than 100-price-point SL.
            if 100<=risk<=10000:
                lev=RISK_NAV*O[k]/risk
                if lev>MAX_NOTIONAL:
                    skipped_leverage+=1
                else:
                    side=int(sig[k]);entry_mid=O[k]
                    entry_fill=entry_mid+side*(SLIPPAGE+extra_bps*entry_mid/10000.)
                    initial_risk=risk;stop=entry_mid-side*risk
                    entry_k=k;entry_unix=T[k];open_equity=equity
                    entries[month_id[k]]+=1;expo[month_id[k]]=1
        if k==len(O)-1 or month_id[k+1]!=month_id[k]:
            marked=equity
            if side!=0:
                mid=C[k];fill=mid-side*(SLIPPAGE+extra_bps*mid/10000.)
                pnl=side*(fill-entry_fill)-FEE*(entry_fill+fill)
                marked=open_equity*(1.+RISK_NAV*pnl/initial_risk)
            month_nav[month_id[k]]=marked
    return trades,month_nav,entries,expo,maxdd,skipped_leverage

def metrics(monthly):
    x=np.asarray(monthly,float)
    if len(x)<1 or not np.isfinite(x).all() or (x<=-100).any():raise ValueError("Invalid NAV")
    acc=np.cumprod(1.+x/100.)
    peak=np.maximum.accumulate(np.r_[1.,acc])[1:]
    return dict(total_pct=float((acc[-1]-1.)*100.),
      positive_months=int((x>1e-9).sum()),negative_months=int((x<-1e-9).sum()),
      flat_months=int((np.abs(x)<=1e-9).sum()),
      mean_month_pct=float(x.mean()),median_month_pct=float(np.median(x)),
      worst_month_pct=float(x.min()),monthend_drawdown_pct=float(100.*np.max(1.-acc/peak)))
def to_months(nav):
    if not np.isfinite(nav).all():raise ValueError("Missing monthly mark")
    return np.r_[100.*(nav[0]/100.-1.),100.*(nav[1:]/nav[:-1]-1.)][:22]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,seg_start,_,quality=read_archive()
    monid,labels=build_months(f)
    if labels[:22]!=MONTHS:raise AssertionError("Month boundaries shifted")
    hour=hourly_features(f)
    O=f.open.to_numpy(np.float64);H=f.high.to_numpy(np.float64)
    L=f.low.to_numpy(np.float64);C=f.close.to_numpy(np.float64)
    T=f.time.to_numpy(np.int64)
    results=[];monthly=[];ledgers=[]
    for name,look,sl,trail in CONFIGS:
        signal,updated,atr,reference=configure_signals(
          f,hour,seg_start,(name,look,"break","4h","any",trail))
        for cost in STRESS_BPS:
            trades,marks,entries,exposure,dd,skip=engine(
                O,H,L,C,T,monid,seg_start,signal,updated,atr,reference,
                sl,trail,cost,len(labels))
            mon=to_months(marks)
            tr=metrics(mon[:12]);check=metrics(mon[12:]);full=metrics(mon)
            Rs=np.asarray([t[5] for t in trades],dtype=float)
            gain=float(Rs[Rs>0].sum());loss=float(-Rs[Rs<0].sum())
            pf=gain/loss if loss>0 else None
            cutoff=int(pd.Timestamp("2026-01-01",tz="Asia/Kolkata").tz_convert("UTC").timestamp())
            n2025=int(sum(t[0]<cutoff for t in trades))
            results.append(dict(variant=name,channel_hour_bars=look,
                initial_stop_atr=sl,trailing_distance_atr=trail,
                extra_slippage_bps_each_side=cost,
                trade_count=int(len(trades)),trades_2025=n2025,skipped_leverage=skip,
                trade_PF=pf,trade_close_dd_pct=float(dd)*100,
                net_2025_pct=tr["total_pct"],net_2026_pct=check["total_pct"],
                net_22_pct=full["total_pct"],positive_2025=tr["positive_months"],
                positive_2026=check["positive_months"],positive_22=full["positive_months"],
                negative_22=full["negative_months"],flat_22=full["flat_months"],
                avg_month_22_pct=full["mean_month_pct"],
                median_month_22_pct=full["median_month_pct"],
                avg_month_2025_pct=tr["mean_month_pct"],
                worst_month_pct=full["worst_month_pct"],
                dd_2025_pct=tr["monthend_drawdown_pct"],
                dd_22_pct=full["monthend_drawdown_pct"]))
            monthly.extend(dict(variant=name,extra_slippage_bps_each_side=cost,
                month_ist=m,net_pct=float(v)) for m,v in zip(MONTHS,mon))
            if cost==0:
                ledgers.extend(dict(variant=name,entry_unix=int(t[0]),
                    exit_unix=int(t[1]),side=int(t[2]),stop_pts=float(t[3]),
                    net_price_pts=float(t[4]),net_R=float(t[5]),
                    exit_reason_code=int(t[6])) for t in trades)
    df=pd.DataFrame(results)
    mo=pd.DataFrame(monthly)
    # Full baseline self-check: exact original native trade/fill/mark parity.
    cfg=("prior_break48_stop2_trail2",48,"break","4h","any",2.)
    sg,upd,at,ref=configure_signals(f,hour,seg_start,cfg)
    raw,m,_,_,dd=original_run(O,H,L,C,T,monid,seg_start,sg,upd,at,ref,2.,len(labels))
    fresh=mo[(mo.variant=="prior_break48_stop2_trail2")&
             (mo.extra_slippage_bps_each_side==0)].set_index("month_ist").reindex(MONTHS).net_pct.to_numpy()
    parity_diff=float(np.max(np.abs(to_months(m)-fresh)))
    if len(raw)!=int(df[(df.variant=="prior_break48_stop2_trail2")&
                        (df.extra_slippage_bps_each_side==0)].iloc[0].trade_count) or parity_diff>1e-8:
        raise AssertionError(f"Original 48hour 1m engine parity failed: {parity_diff}")
    print("BASELINE_PARITY_SUCCESS",len(raw),parity_diff)
    # 2025 ONLY score, larger monthly profits PRIMARY, penalize downside/DD,
    # compare at +2bp/side adverse fill stress, no 2026 scouting.
    train=df[(df.extra_slippage_bps_each_side==2)&
       (df.trades_2025>=60)&(df.net_2025_pct>0)&(df.trade_PF>1)].copy()
    train["score_2025_monthly_profit"]=(
       train.avg_month_2025_pct - .08*train.dd_2025_pct +
       .025*train.positive_2025)
    train=train.sort_values(["score_2025_monthly_profit","net_2025_pct"],
                             ascending=False,kind="stable")
    selected=train.iloc[0].variant if len(train) else None
    print("BTC2025_AVG_MONTHLY_PROFIT_RANK",train[[
        "variant","score_2025_monthly_profit","net_2025_pct","net_2026_pct",
        "avg_month_2025_pct","positive_2025","trades_2025",
        "dd_2025_pct","trade_PF"]].to_json(orient="records"))
    print("FROZEN_BTC2025_SELECTION",selected)
    for name in dict.fromkeys(["prior_break48_stop2_trail2",selected]):
        if name is None:continue
        for stress in STRESS_BPS:
            row=df[(df.variant==name)&(df.extra_slippage_bps_each_side==stress)].iloc[0]
            print("MONTHLY_NET_PROFIT_RESULT",row.to_json())
    print("ALL_BTC2026_CHRONOLOGICAL_CHECKS",df[df.extra_slippage_bps_each_side==2][[
        "variant","net_2025_pct","net_2026_pct","net_22_pct","avg_month_22_pct",
        "positive_22","negative_22","worst_month_pct","dd_22_pct"]].to_json(orient="records"))
    df.to_csv(OUT/"all_strategy_net_monthly_summaries.csv",index=False)
    mo.to_csv(OUT/"each_calendar_month_all_variants.csv",index=False)
    pd.DataFrame(ledgers).to_csv(OUT/"actual_trade_ledger.csv.gz",compression="gzip",index=False)
    (OUT/"selection_BTC2025.json").write_text(json.dumps({"selection":selected},indent=2))
    (OUT/"quality_and_limits.json").write_text(json.dumps(dict(
        actual_1m_source=quality,baseline_trade_count=len(raw),baseline_parity_max_pct=parity_diff,
        variants=CONFIGS,cost_stress_bps_each_side=STRESS_BPS,
        methodology="Single position BTCUSD, 1h completed close signals / 4h completed trend confirmation; next 1m open; structural ATR stop and full H1 close trailing; original 1m OHLC stop-first/gap logic.",
        risk="Max initial 0.5% of account NAV per trade, implied notional cap <=3x; no leverage changes across variants",
        costs="0.05% taker/side + 18% GST + adverse 5 BTC price points/side; stress adds 2/5/10 bps EACH side",
        known_limits=[
          "2025 and 2026 both repeatedly examined; no genuinely pristine holdout.",
          "One minute OHLC midprice cannot verify historical quote spread, slippage, intraminute fill ordering or true liquidation.",
          "No native ETH replay, funding, exact contract size/collateral nor margin/liquidation.",
          "Known historical missing data in early 2025 IST and October 31 2026.",
          "Results are standalone monthly NAV (not additive to already busy Stage18/20 positions).",
          "Extra signal search creates multiple-testing risk; strong 2025 train can weaken in research-exposed 2026.",
          "No live orders sent; do not claim genuine forward profitability."
        ]),indent=2,default=str))
    print("BTC_MONTHLY_NET_PROFIT_RESEARCH_COMPLETE",json.dumps({"selected":selected}))
if __name__=="__main__":main()
