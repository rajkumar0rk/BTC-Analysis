#!/usr/bin/env python3
"""Stage 17: distinct BTC directional SWING breakout system.

Long-horizon Donchian close breakout (4H 24/55 bars or 1D 20/55 bars),
optional 50-period EMA filter, 2 x ATR initial stop and 3/4 x ATR
trailing stop tightened ONLY on completely closed higher-timeframe bars.
One position across LONG/SHORT, 1m stop fills, opposite breakout exit,
14-day time cap. Market-to-market equity at IST calendar month end.

All 2025/2026 data was previously used in other research. No untouched
holdout. This is exploratory and not a monthly-profit guarantee.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit
from research_every_candle_200 import read_archive, FEE, SLIPPAGE

OUT=Path("analysis/institutional_discovery_stage17_swing_breakout")
START_EQUITY=100.0
RISK_FRACTION=0.005
MAX_HOLD_MIN=14*24*60
CONFIGS=[
    ("4H",24),("4H",55),("1D",20),("1D",55)
]
TREND_CHOICES=("no_trend_filter","ema50_agrees")
TRAIL_MULS=(3.0,4.0)

def build_months(f):
    starts=pd.date_range("2025-01-01","2026-12-01",freq="MS",
        tz="Asia/Kolkata").tz_convert("UTC")
    boundary=np.asarray([int(ts.timestamp()) for ts in starts],dtype=np.int64)
    codes=np.searchsorted(boundary,f.time.to_numpy(np.int64),side="right")-1
    if codes.min()<0 or codes.max()>=len(starts)-1:
        raise ValueError(f"archive outside boundaries: codes={codes.min()}, {codes.max()}; boundary={boundary[0]}, {boundary[-1]}; first,last = {int(f.time.iloc[0])}, {int(f.time.iloc[-1])}")
    labels=starts.tz_convert("Asia/Kolkata").strftime("%Y-%m").tolist()[:-1]
    return codes.astype(np.int32),labels

def higher_bars(f,timeframe):
    unit=240 if timeframe=="4H" else 1440
    freq="4h" if timeframe=="4H" else "1D"
    bars=f[["open","high","low","close","volume"]].resample(
        freq,label="right",closed="left").agg({
        "open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    count=f.close.resample(freq,label="right",closed="left").count()
    bars["complete"]=(count==unit)
    # Explicitly require 120 consecutive complete bars, so a missing
    # source day cannot cause a previously observed channel to be reused.
    bars["history_ok"]=count.rolling(120,min_periods=120).min().eq(unit)
    pc=bars.close.shift(1)
    tr=pd.concat([(bars.high-bars.low),(bars.high-pc).abs(),
        (bars.low-pc).abs()],axis=1).max(axis=1)
    bars["atr"]=tr.rolling(14,min_periods=14).mean()
    bars["ema50"]=bars.close.ewm(span=50,adjust=False).mean()
    bars["median_prior_atr"]=bars.atr.shift(1).rolling(20,min_periods=20).median()
    return bars

def signals(f,bars,lookback,trendchoice):
    upper=bars.high.shift(1).rolling(lookback,min_periods=lookback).max()
    lower=bars.low.shift(1).rolling(lookback,min_periods=lookback).min()
    # Signal is valid only once on crossing a channel, not repeatedly
    # on every candle remaining outside the prior range.
    previous_upper=upper.shift(1)
    previous_lower=lower.shift(1)
    is_long=(bars.close>upper)&(bars.close.shift(1)<=previous_upper)
    is_short=(bars.close<lower)&(bars.close.shift(1)>=previous_lower)
    if trendchoice=="ema50_agrees":
        is_long&=(bars.close>bars.ema50)&(bars.ema50.diff(3)>0)
        is_short&=(bars.close<bars.ema50)&(bars.ema50.diff(3)<0)
    valid=bars.history_ok&bars.atr.gt(0)&bars.complete
    is_long&=valid
    is_short&=valid
    ix=f.index.get_indexer(bars.index)
    signal=np.zeros(len(f),np.int8)
    atr=np.full(len(f),np.nan,np.float64)
    close=np.full(len(f),np.nan,np.float64)
    updates=np.zeros(len(f),np.bool_)
    nsignal=0
    for j,k in enumerate(ix):
        if k<0 or not bool(valid.iloc[j]):continue
        updates[k]=True
        atr[k]=float(bars.atr.iloc[j])
        close[k]=float(bars.close.iloc[j])
        if bool(is_long.iloc[j]):
            signal[k]=1
            nsignal+=1
        elif bool(is_short.iloc[j]):
            signal[k]=-1
            nsignal+=1
    return signal,updates,atr,close,nsignal

@njit(cache=True)
def run_one(O,H,L,C,T,month_id,seg_start,signal,updates,atr,ref_close,
            trail_mult,n_months):
    equity=START_EQUITY
    open_equity=equity
    entry_fill=0.
    entry_mid=0.
    entry_unix=-1
    entry_k=-1
    entry_risk=0.
    stop=0.
    side=0
    trades=[]
    month_end_equity=np.full(n_months,np.nan)
    month_entry_count=np.zeros(n_months,np.int32)
    month_exposure=np.zeros(n_months,np.int32)
    # trade-to-trade realized equity drawdown
    peak=equity
    maxdrawdown=0.
    reason_code=0
    for k in range(len(O)):
        # A source data gap terminates exposure BEFORE the missing candles,
        # at the final observed close. It is not claimed as a realistic
        # execution during an outage.
        if k>0 and seg_start[k]==k and side!=0:
            old=k-1
            exit_mid=C[old]
            exit_fill=exit_mid-side*SLIPPAGE
            net=side*(exit_fill-entry_fill)-FEE*(entry_fill+exit_fill)
            netR=net/entry_risk
            equity=open_equity*(1.+RISK_FRACTION*netR)
            trades.append((entry_unix,T[old],side,entry_risk,net,netR,3,
                           entry_k,old))
            side=0
            if equity>peak:peak=equity
            maxdrawdown=max(maxdrawdown,(peak-equity)/peak)
        reverse=False
        if side!=0 and updates[k] and np.isfinite(atr[k]):
            trail=ref_close[k]-side*trail_mult*atr[k]
            if side==1 and trail>stop:
                stop=trail
            if side==-1 and trail<stop:
                stop=trail
        if side!=0:
            month_exposure[month_id[k]]=1
            hit=(L[k]<=stop) if side==1 else (H[k]>=stop)
            if hit:
                exit_mid=min(O[k],stop) if side==1 else max(O[k],stop)
                reason_code=0
            elif k-entry_k>=MAX_HOLD_MIN:
                exit_mid=O[k]
                reason_code=1
            elif signal[k]==-side:
                exit_mid=O[k]
                reason_code=2
                reverse=True
            else:
                reason_code=-1
            if reason_code>=0:
                exit_fill=exit_mid-side*SLIPPAGE
                net=side*(exit_fill-entry_fill)-FEE*(entry_fill+exit_fill)
                netR=net/entry_risk
                equity=open_equity*(1.+RISK_FRACTION*netR)
                trades.append((entry_unix,T[k],side,entry_risk,net,netR,
                               reason_code,entry_k,k))
                side=0
                if equity>peak:peak=equity
                maxdrawdown=max(maxdrawdown,(peak-equity)/peak)
        if side==0 and not reverse and signal[k]!=0 and np.isfinite(atr[k]):
            risk=2.0*atr[k]
            if 100<=risk<=10000:
                side=int(signal[k])
                entry_mid=O[k]
                entry_fill=entry_mid+side*SLIPPAGE
                entry_risk=risk
                stop=entry_mid-side*risk
                entry_k=k
                entry_unix=T[k]
                open_equity=equity
                month_entry_count[month_id[k]]+=1
                month_exposure[month_id[k]]=1
        # Monthly equity is marked using the liquidatable mid-close.
        # The full open/exit costs are estimated on mark, consistent with
        # realizations and with the equity model's fixed risk amount.
        if k==len(O)-1 or month_id[k+1]!=month_id[k]:
            mark=equity
            if side!=0:
                liquidate=C[k]-side*SLIPPAGE
                net=side*(liquidate-entry_fill)-FEE*(entry_fill+liquidate)
                mark=open_equity*(1.+RISK_FRACTION*net/entry_risk)
            month_end_equity[month_id[k]]=mark
    return trades,month_end_equity,month_entry_count,month_exposure,maxdrawdown

def make_reports(f,seg_start,month_id,months):
    O=f.open.to_numpy(np.float64)
    H=f.high.to_numpy(np.float64)
    L=f.low.to_numpy(np.float64)
    C=f.close.to_numpy(np.float64)
    T=f.time.to_numpy(np.int64)
    reports=[]
    all_trades=[]
    monthly=[]
    for tf,nbar in CONFIGS:
        bars=higher_bars(f,tf)
        for trend in TREND_CHOICES:
            sig,upd,atr,ref_close,total_signals=signals(f,bars,nbar,trend)
            for mult in TRAIL_MULS:
                label=f"{tf}_channel_{nbar}_{trend}_trail_{mult:g}atr"
                trades,mE,entries,exposure,maxDD=run_one(O,H,L,C,T,
                    month_id,seg_start,sig,upd,atr,ref_close,mult,len(months))
                if np.isnan(mE).any():
                    raise AssertionError("Missing monthly valuation for "+label)
                eqprev=START_EQUITY
                for mid,month in enumerate(months):
                    end=float(mE[mid])
                    change=100*(end/eqprev-1)
                    active=bool(exposure[mid])
                    status="No exposure" if not active else (
                        "Profit" if change>1e-9 else
                        "Loss" if change< -1e-9 else "Flat")
                    monthly.append(dict(model=label,month_ist=month,
                        signals_seen=total_signals,
                        entries=int(entries[mid]),market_exposure=int(active),
                        month_return_pct=round(change,4),
                        month_end_equity=round(end,5),status=status))
                    eqprev=end
                for trade in trades:
                    start,end,side,risk,net,netR,why,entry_idx,exit_idx=trade
                    all_trades.append(dict(model=label,entry_utc_unix=start,
                        exit_utc_unix=end,direction="LONG" if side==1 else "SHORT",
                        initial_risk_pts=round(risk,3),
                        net_price_points=round(net,3),net_R=round(netR,5),
                        exit_reason=["atr_stop","time_cap","opposite_breakout","source_gap"][why],
                        held_minutes=int((end-start)/60)))
                reports.append(dict(model=label,timeframe=tf,channel_lookback=nbar,
                    trend=trend,trail_ATR=mult,signals_seen=total_signals,
                    trades=len(trades),max_trade_to_trade_drawdown_pct=round(maxDD*100,3),
                    total_return_pct=round(100*(mE[-1]/START_EQUITY-1),3),
                    last_month_valuation=round(float(mE[-1]),4)))
    return pd.DataFrame(monthly),pd.DataFrame(reports),pd.DataFrame(all_trades)

def evaluate(m,info):
    out=[]
    for model,g in m.groupby("model"):
        row=info[info.model==model].iloc[0].to_dict()
        for year in (2025,2026):
            y=g[g.month_ist.str.startswith(str(year))]
            row[f"profit_{year}"]=int((y.status=="Profit").sum())
            row[f"loss_{year}"]=int((y.status=="Loss").sum())
            row[f"inactive_{year}"]=int((y.status=="No exposure").sum())
            row[f"active_{year}"]=int((y.market_exposure>0).sum())
            row[f"return_{year}_pct"]=round(float(
                (np.prod(1+y.month_return_pct.to_numpy(float)/100)-1)*100),3)
        # Require broad exposure/positive months for a monthly-profit thesis.
        row["monthly_gate_pass"] = bool(
            row["active_2025"]>=9 and row["active_2026"]>=8 and
            row["profit_2025"]>=9 and row["profit_2026"]>=8 and
            row["return_2025_pct"]>0 and row["return_2026_pct"]>0 and
            row["trades"]>=30)
        out.append(row)
    return pd.DataFrame(out)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,segstart,_,quality=read_archive()
    mid,months=build_months(f)
    monthly,model_info,trades=make_reports(f,segstart,mid,months)
    check=evaluate(monthly,model_info)
    monthly.to_csv(OUT/"monthly_mark_to_market.csv",index=False)
    check.to_csv(OUT/"model_comparison.csv",index=False)
    trades.to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    meta=dict(
        source="Delta Exchange India BTCUSD 1-minute historical candles",
        observed_1minute_candles=len(f),missing_minutes=quality["missing_minutes"],
        dates=[str(f.index[0]),str(f.index[-1])],
        strategy_family="Long-horizon 4H/Daily Donchian CLOSE breakout with ATR trailing",
        configs=len(check),replayed_trade_rows=len(trades),
        monthly_gate_passes=int(check.monthly_gate_pass.sum()),
        monthly_equity_rule="Monthly end-of-month mark-to-market in IST, net of hypothetical liquidation fees",
        risk_fraction_per_trade=RISK_FRACTION,
        fees="0.05% taker each leg, GST 18%, 5 points adverse slippage per leg",
        exits=["2x ATR initial stop","3x or 4x ATR trailing tightened on full TF candle close",
               "opposite breakout","14 elapsed-day cap","close before historical source gap"],
        caveats=[
            "All 2025 and 2026 are research-exposed; no new forward holdout",
            "2026-10-31 source missing; 2026-11 incomplete through Nov16",
            "Month-end marks on last available minute, not necessarily an executable liquidation",
            "Exact fractional position size assumed; real minimum contract, leverage and margin can differ",
            "Trading fees/GST and assumed slippage included, not actual quote spread/market depth/funding",
            "Losses may exceed initial risk in adverse gap fills; no guaranteed monthly profit",
            "No fixed monthly exit; month returns reflect mark-to-market unrealized PnL",
            "One position at a time across LONG and SHORT; no concurrent trades",
            "Signal on FULL completed 4H or Daily candle, next 1m open execution",
            "A missing source day triggers a conservative forced exit on last observed candle",
            "16 configurations create multiple testing risk; any attractive result remains exploratory"])
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
    rank=check.sort_values(["profit_2025","profit_2026",
                            "return_2025_pct"],ascending=False)
    candidates=rank.head(3).model.tolist()
    report=[
        "# Stage17 — Distinct multi-day BTC swing Donchian breakout and ATR trailing",
        "",
        "## Predeclared strategy",
        "4H 24/55-bar channel or 1D 20/55-bar channel close-break. Only new",
        "crossings count. Optional EMA50 confirmation, 2x ATR initial stop,",
        "3x/4x ATR trailing after each completed signal-timeframe candle,",
        "opposite breakout exit or 14-day time cap. One position at a time.",
        "",
        "## Monthly account-style method",
        "All trades sized at hypothetical 0.5% of account per initial 1R.",
        "Monthly NAV marked to market on last observed minute IST,",
        "including estimated round-trip liquidation fees and adverse slippage.",
        "This prevents a multi-day open winner from appearing as an",
        "artificial zero-trade month; monthly inactive means no position held.",
        "",
        f"**Monthly-profit criteria passed: {meta['monthly_gate_passes']}/{len(check)}**",
        "",
        "## Full comparison",
        check.to_markdown(index=False),"",
        "## Month-by-month top three 2025-ranked models",
        monthly[monthly.model.isin(candidates)].to_markdown(index=False),"",
        "## Research caveats",
        *["- "+x for x in meta["caveats"]],
        "",
        "Reproduce with scripts/research_swing_donchian_stage17.py."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE17_COMPLETE "+json.dumps({
        "candles":len(f),"models":len(check),"trades":len(trades),
        "monthly_passes":meta["monthly_gate_passes"]}))
    print("MODELS\n"+check.to_string(index=False))
    print("MONTHLY_BEST\n"+monthly[monthly.model.isin(candidates)].to_string(index=False))
if __name__=="__main__":
    main()
