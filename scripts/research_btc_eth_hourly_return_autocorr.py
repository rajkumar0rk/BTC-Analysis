#!/usr/bin/env python3
"""BTCUSD/ETHUSD matched strategy pairs, monthly AFTER-COST profit-factor audit.

Reuses the EXACT causal family definitions from eth_native_crossfamily_v2.
Predeclared 52 families x 4 ATR/target settings (plus original fixed-percent
family); run the same configuration in BTCUSD and ETHUSD, no asset-specific
parameter tuning. Costs differ by instrument: BTC 5 absolute price points per
fill, ETH 0.02% of execution price per fill. Fees 0.05% each side + 18% GST.
Risk 0.5% of current equity / stop distance, capped at 3x notional, one
position at a time; conservative stop-before-target fills. Incomplete first
5.5h of Jan2025 IST disclosed. No funding/actual spreads/impact/real fills.
This is new paired-market replay, not evidence of forward profitability.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eth_native_crossfamily_v2 import (
    load, aggregate, signal_library, replay as original_replay,
    MONTHS, RISK, CAP, FEE, INITIAL_EQUITY
)

OUT = Path("analysis/btc_eth_hourly_return_autocorr_20261118")
ETH_SLIPPAGE_FRACTION = 0.0002
BTC_SLIPPAGE_POINTS = 5.0
MONTH_CODE = np.asarray([int(s.replace("-", "")) for s in MONTHS], np.int32)
LAST_CODE = 202610
MONTH_COUNT = len(MONTHS)

@njit(cache=True)
def replay_instrument(open_, high, low, close, month_codes,
                      event_idx, sides, stopdist, target_r, hold,
                      stop_mult, risk_pct, cap, abs_slip, frac_slip, fee):
    ledger=np.zeros((len(event_idx), 8), np.float64)
    n=0
    busy=-1
    equity=1000.0
    for i in range(len(event_idx)):
        k=int(event_idx[i])
        if k<=busy or k<=0 or k>=len(close) or month_codes[k]>LAST_CODE:
            continue
        sd=int(sides[i])
        distance=stopdist[i]*stop_mult
        if not np.isfinite(distance) or distance<=0:continue
        slip_entry=abs_slip+frac_slip*open_[k]
        entry=open_[k]+sd*slip_entry
        if entry<=0:continue
        qty=min(equity*risk_pct/distance, equity*cap/entry)
        if qty<=0:continue
        stop=entry-sd*distance
        target=entry+sd*distance*target_r
        finish=min(k+hold-1, len(close)-1)
        j=finish
        exit_px=close[finish]
        for v in range(k,finish+1):
            stop_hit=(low[v]<=stop if sd==1 else high[v]>=stop)
            if stop_hit:
                exit_px=min(stop,open_[v]) if sd==1 else max(stop,open_[v])
                j=v
                break
            tp_hit=(high[v]>=target if sd==1 else low[v]<=target)
            if tp_hit:
                exit_px=target
                j=v
                break
            if v==finish or (v+1<len(close) and month_codes[v+1]!=month_codes[v]):
                exit_px=close[v]
                j=v
                break
        slip_exit=abs_slip+frac_slip*exit_px
        true_exit=exit_px-sd*slip_exit
        pnl=qty*(sd*(true_exit-entry)-fee*(entry+true_exit))
        equity+=pnl
        ledger[n,0]=k
        ledger[n,1]=j
        ledger[n,2]=sd
        ledger[n,3]=entry
        ledger[n,4]=distance
        ledger[n,5]=qty
        ledger[n,6]=pnl
        ledger[n,7]=equity
        n+=1
        busy=j
        if equity<=0:break
    return ledger[:n]

def profit_factor(values):
    x=np.asarray(values,float)
    gain=float(x[x>0].sum())
    loss=float(-x[x<0].sum())
    if loss==0 and gain==0:return None,gain,loss
    if loss==0:return "infinite",gain,loss
    return gain/loss,gain,loss

def month_table(ledger, all_codes, symbol, model):
    closed_months=all_codes[ledger[:,1].astype(np.int64)] if len(ledger) else np.zeros(0,np.int32)
    equity=INITIAL_EQUITY
    result=[]
    for name,month_code in zip(MONTHS,MONTH_CODE):
        subset=ledger[closed_months==month_code]
        vals=subset[:,6] if len(subset) else np.zeros(0)
        w=int((vals>0).sum())
        l=int((vals<0).sum())
        pf,gain,loss=profit_factor(vals)
        after=float(subset[-1,7]) if len(subset) else equity
        ret=(after/equity-1)*100 if equity>0 else -100.0
        result.append(dict(market=symbol,model=model,month=name,net_return_pct=ret,
            profit_factor=pf,trades=int(len(vals)),wins=w,losses=l,
            winning_net_pnl_usd=gain,losing_net_pnl_abs_usd=loss,
            net_pnl_usd=float(vals.sum()),equity_start_usd=equity,equity_end_usd=after))
        equity=after
    return result

def flatten(symbol,model,ledger,months):
    vals=ledger[:,6] if len(ledger) else np.zeros(0)
    pf,gain,loss=profit_factor(vals)
    if pf=="infinite":pf_numeric=float("inf")
    else:pf_numeric=pf if pf is not None else 0.0
    monthly=pd.DataFrame(months)
    jan_dec=monthly.iloc[:12]
    jan_oct=monthly.iloc[12:]
    def yearly_pf(d):
        gain=float(d.winning_net_pnl_usd.sum())
        loss=float(d.losing_net_pnl_abs_usd.sum())
        if gain==0 and loss==0:return None
        if loss==0:return "infinite"
        return gain/loss
    pf_2025=yearly_pf(jan_dec)
    pf_2026=yearly_pf(jan_oct)
    year2025=(jan_dec.iloc[-1].equity_end_usd/INITIAL_EQUITY-1)*100
    year2026=(jan_oct.iloc[-1].equity_end_usd/jan_oct.iloc[0].equity_start_usd-1)*100
    equity_curve=np.r_[INITIAL_EQUITY,ledger[:,7]] if len(ledger) else np.array([INITIAL_EQUITY])
    dd=float((equity_curve/np.maximum.accumulate(equity_curve)-1).min()*100)
    strong=lambda d:int(sum((v=="infinite" or (isinstance(v,(int,float)) and v>=1.5))
          and ret>0 and trades>=3 for v,ret,trades in zip(d.profit_factor,d.net_return_pct,d.trades)))
    return dict(market=symbol,model=model,profit_factor=pf,
       total_positive_trade_pnl_usd=gain,total_losing_trade_pnl_abs_usd=loss,
       total_net_pnl_usd=float(vals.sum()),net_return_pct=float((equity_curve[-1]/INITIAL_EQUITY-1)*100),
       net_return_2025_pct=float(year2025),net_return_2026_pct=float(year2026),
       profit_factor_2025=pf_2025,profit_factor_2026=pf_2026,
       trades=len(vals),wins=int((vals>0).sum()),losses=int((vals<0).sum()),
       win_rate_pct=float(100*(vals>0).sum()/len(vals)) if len(vals) else 0.,
       positive_months=int((monthly.net_return_pct>0).sum()),
       loss_months=int((monthly.net_return_pct<0).sum()),
       zero_trade_months=int((monthly.trades==0).sum()),
       strong_months_pf_ge_1p5_positive_min3trades=strong(monthly),
       strong_months_2025=strong(jan_dec),strong_months_2026=strong(jan_oct),
       positive_months_2025=int((jan_dec.net_return_pct>0).sum()),
       positive_months_2026=int((jan_oct.net_return_pct>0).sum()),
       trades_2025=int(jan_dec.trades.sum()),trades_2026=int(jan_oct.trades.sum()),
       max_closed_trade_drawdown_pct=dd,worst_month_pct=float(monthly.net_return_pct.min()))

def events_for(sig, asset):
    b,long,short=sig
    idx0=np.r_[np.flatnonzero(long.to_numpy(bool)),np.flatnonzero(short.to_numpy(bool))]
    side=np.r_[np.ones(int(long.sum()),np.int32),-np.ones(int(short.sum()),np.int32)]
    k=asset.index.get_indexer(b.index[idx0])
    valid=(k>=0)&(k<len(asset))
    idx0=idx0[valid];side=side[valid];k=k[valid]
    order=np.lexsort((-side,k))
    k=k[order];idx0=idx0[order];side=side[order]
    if len(k):
        unique=np.r_[True,np.diff(k)!=0]
        k=k[unique];side=side[unique];idx0=idx0[unique]
    return b,k,side,idx0

def ledger_detail(symbol,model,ledger,asset):
    if len(ledger)==0:return pd.DataFrame()
    entry_indices=ledger[:,0].astype(int)
    exit_indices=ledger[:,1].astype(int)
    return pd.DataFrame(dict(market=symbol,model=model,
        entry_utc=asset.index[entry_indices].astype(str),
        exit_utc=asset.index[exit_indices].astype(str),
        side=ledger[:,2].astype(int),entry_price=ledger[:,3],
        stop_distance=ledger[:,4],position_quantity=ledger[:,5],
        trade_net_pnl_usd=ledger[:,6],equity_after_usd=ledger[:,7]))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    markets={symbol:load(symbol) for symbol in ("BTCUSD","ETHUSD")}
    assert markets["BTCUSD"].index.equals(markets["ETHUSD"].index)
    all_rows=[];all_months=[];save_ledgers={}
    for symbol,asset in markets.items():
        open_=asset.open.to_numpy(float);high=asset.high.to_numpy(float)
        low=asset.low.to_numpy(float);close=asset.close.to_numpy(float)
        ist=asset.index.tz_convert("Asia/Kolkata")
        month_code=np.asarray(ist.year*100+ist.month,dtype=np.int32)
        candles={s:aggregate(asset,s) for s in ("5min","15min","1h","4h")}
        sigs=signal_library(candles)
        # New pre-entry causal regime: one-hour log-return lag-one
        # autocorrelation across the preceding 72 fully completed hours.
        # The current hourly bar is deliberately excluded (shift one hour).
        # Distinct from prior directional-flip entropy and wick imbalance.
        hour=candles["1h"]
        hourly_return=np.log(hour.close/hour.close.shift(1))
        lagged=hourly_return.shift(1)
        rolling_corr=hourly_return.rolling(72,min_periods=72).corr(lagged).shift(1)
        hourly_regime=((rolling_corr<=-0.08)&hour.valid).fillna(False)
        regime_at_minute=hourly_regime.reindex(asset.index,method="ffill").fillna(False).to_numpy(bool)
        assert len(sigs)==52,(symbol,len(sigs))
        for label,sig in sigs.items():
            b,k,sides,idx0=events_for(sig,asset)
            if not len(k):continue
            keep=regime_at_minute[k]
            k=k[keep];sides=sides[keep];idx0=idx0[keep]
            if not len(k):continue
            stop_base=b.atr.to_numpy(float)[idx0]
            fixed="fixed100_200" in label
            if fixed:
                # Identical 100-point BTC proportion of CURRENT BTC price on
                # both assets, using concurrent observable pre-entry prices.
                btc=markets["BTCUSD"].open.to_numpy(float)
                stop_base=(asset.open.to_numpy(float)[k]*100.)/btc[k]
            timeframe=label.split(":")[0]
            hold={"5min":240,"15min":720,"1h":1440,"4h":4320}[timeframe]
            grid=[(1.,2.)] if fixed else [(1.5,2.),(2.5,2.),(1.5,3.),(2.5,3.)]
            for stop_mult,target_r in grid:
                model=label+f"__SL{stop_mult:g}_RR{target_r:g}"
                abs_slip=BTC_SLIPPAGE_POINTS if symbol=="BTCUSD" else 0.
                rel_slip=0. if symbol=="BTCUSD" else ETH_SLIPPAGE_FRACTION
                ledger=replay_instrument(open_,high,low,close,month_code,k,sides,
                    stop_base,target_r,hold,stop_mult,RISK,CAP,abs_slip,rel_slip,FEE)
                months=month_table(ledger,month_code,symbol,model)
                row=flatten(symbol,model,ledger,months)
                all_rows.append(row);all_months.extend(months)
                save_ledgers[(symbol,model)]=(ledger,asset)
        print("COMPLETED_MARKET",symbol,len([x for x in all_rows if x["market"]==symbol]),flush=True)
    models=pd.DataFrame(all_rows)
    months=pd.DataFrame(all_months)
    models.to_csv(OUT/"paired_all_model_summary.csv",index=False)
    models["full_2025_gt_500pct"]=models.net_return_2025_pct>500.
    models.to_csv(OUT/"yearly_2025_and_ytd_2026.csv",index=False)
    months.to_csv(OUT/"paired_all_model_monthly.csv",index=False)
    months["strong_pf_positive"]=months.apply(lambda r:
        (r.profit_factor=="infinite" or
         (isinstance(r.profit_factor,(int,float)) and r.profit_factor>=1.5))
         and r.net_return_pct>0 and r.trades>=3,axis=1)
    months["pf_ge1p5_net_ge5pct"]=months.strong_pf_positive & (months.net_return_pct>=5)
    months["net_ge10pct"]=months.net_return_pct>=10
    months["net_ge20pct"]=months.net_return_pct>=20
    months.to_csv(OUT/"monthly_milestones.csv",index=False)
    common=set(models.loc[models.market=="BTCUSD","model"])&set(models.loc[models.market=="ETHUSD","model"])
    assert len(common)>=150,("too few matched models",len(common))
    # Select for review using 2025 performance ONLY, separately BTC and ETH.
    # User goal is NOT 22/22: focus on PF, total gain and most strong months.
    selected_models=set()
    review=[]
    for symbol in markets:
        t=models[models.market==symbol].copy()
        t=t[(t.trades_2025>=35)&(t.net_return_2025_pct>0)]
        t=t.assign(train_score=(
            t.strong_months_2025*4+t.positive_months_2025*1.0+
            np.minimum(t.net_return_2025_pct,100)/20+
            t.profit_factor_2025.map(lambda x:(4. if x=="infinite" else min(float(x),4)) if x is not None else 0)))
        top=t.sort_values("train_score",ascending=False).head(6)
        for _,q in top.iterrows():
            selected_models.add(q.model)
            review.append(dict(selection_market=symbol,model=q.model,
                rationale="Ranked using 2025 net return, 2025 profit factor and monthly strength ONLY; 2026 not pristine OOS",
                training_2025_net_return_pct=q.net_return_2025_pct,
                training_2025_positive_months=int(q.positive_months_2025)))
    pd.DataFrame(review).to_csv(OUT/"2025_training_selected_candidates.csv",index=False)
    candidates=models[models.model.isin(selected_models)].copy()
    candidates.to_csv(OUT/"candidate_both_market_summary.csv",index=False)
    months[months.model.isin(selected_models)].to_csv(OUT/"candidate_monthly_22.csv",index=False)
    full_ledgers=[]
    for (sym,model),(ledger,asset) in save_ledgers.items():
        if model in selected_models:
            full_ledgers.append(ledger_detail(sym,model,ledger,asset))
    pd.concat(full_ledgers,ignore_index=True).to_csv(OUT/"candidate_trade_ledgers.csv",index=False)
    # ETH baseline reconciliation: unchanged old replay at nominal 0.25 ETH
    # points reproduces existing published 4H engulf 190/78/112/+16.085%.
    eth=markets["ETHUSD"];signals=signal_library({s:aggregate(eth,s) for s in ("5min","15min","1h","4h")})
    b,k,side,idx0=events_for(signals["4h:engulfing_reversal"],eth)
    ist=eth.index.tz_convert("Asia/Kolkata")
    mc=np.asarray(ist.year*100+ist.month,dtype=np.int32)
    base=original_replay(eth.open.to_numpy(float),eth.high.to_numpy(float),
        eth.low.to_numpy(float),eth.close.to_numpy(float),mc,k,side,
        b.atr.to_numpy(float)[idx0],3.,4320,1.5,RISK,CAP,.25,FEE)
    assert len(base)==190
    assert (base[:,6]>0).sum()==78
    assert abs(base[-1,7]-1160.8518786823975)<0.01
    # Print quality and top winners for audit, not a recommendation.
    quality=dict(markets=["BTCUSD","ETHUSD"],families=52,paired_models=len(common),
        executed_rows=len(models),months_per_market=MONTH_COUNT,
        initial_account_usd=INITIAL_EQUITY,risk_per_stop_pct=RISK*100,
        cap_notional_leverage=CAP,fees_per_side=0.0005,GST_on_fees=0.18,
        BTC_slippage_points_per_side=BTC_SLIPPAGE_POINTS,
        ETH_slippage_fraction_per_side=ETH_SLIPPAGE_FRACTION,
        ETH_original_replay_reconciled=True,
        novel_pre_entry_filter="72 fully completed hourly log returns with lag-one correlation <= -0.08; shifted one hour; anti-persistence regime",
        initial_month_gap="Jan 2025 IST first 5.5 hours absent: source starts Jan1 UTC",
        Nov2026="Excluded from monthly selection and entry eligibility",
        omitted_costs=["Funding","verified bid/ask spread","market impact","lot size","margin/liquidation","actual fills"],
        selection="2025 train candidates chosen before reading 2026; 2026 previously researched in repo; not independent forward data",
        previous_scripts_modified=False,novelty="New predeclared hourly log-return autocorrelation anti-persistence regime applied to 52 existing causal families; not a new underlying entry family")
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    top=models[(models.trades>=50)&(models.net_return_pct>0)].copy()
    top=top.assign(pf_sort=top.profit_factor.map(lambda x:float("inf") if x=="infinite" else (float(x) if x is not None else -1))).sort_values(["pf_sort","net_return_pct"],ascending=[False,False]).drop(columns="pf_sort")
    top.head(30).to_csv(OUT/"exploratory_profitable_top30.csv",index=False)
    print("RETURN_AUTOCORR_MONTHLY_DONE",json.dumps(dict(
        models_per_market=len(common),
        profitable_models_by_market={s:int(((models.market==s)&(models.net_return_pct>0)).sum()) for s in markets},
        pf_ge1p5_and_profitable_by_market={
            s:int(sum((r["market"]==s and r["net_return_pct"]>0 and r["profit_factor"]!="infinite"
                    and r["profit_factor"] is not None and float(r["profit_factor"])>=1.5) for r in all_rows))
            for s in markets},top_2025_selected=candidates.sort_values("net_return_pct",ascending=False).head(7)[[
                "market","model","profit_factor","net_return_pct","positive_months",
                "strong_months_pf_ge_1p5_positive_min3trades","trades","max_closed_trade_drawdown_pct"]].to_dict("records"))),flush=True)
    report=["# BTCUSD + ETHUSD return-autocorrelationd monthly PF audit",
        "",f"Tested **{len(common)} identical configurations on each market**",
        "using the same entry/exit/ATR/risk logic; only native asset price and explicit execution slippage differ.",
        "", "No longer requiring every month profitable. All outputs report both monthly net returns and monthly profit factors.",
        "", "## 2025-selected candidate pairs, full 22-month results", "",
        candidates.sort_values(["net_return_pct"],ascending=False).to_markdown(index=False),
        "", "## Sources / risks", "",
        "- Native Delta Exchange India 1m OHLCV, 2025-01-01 UTC through 2026-10-31 UTC; Jan 2025 IST first 5.5h missing.",
        "- 0.05% taker per side + 18% GST; BTC 5 adverse price points per side; ETH 0.02% adverse each side.",
        "- Funding, order-book spread, order impact, exchange liquidation/margin/lot constraints and actual fills not modeled.",
        "- Exact paired trade-level ledgers, all-model monthly results and cost metadata accompany report.",
        "- This is a proxy family audit using previously defined strategy families; no claimed live/forward validation."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")

if __name__=="__main__":
    main()
