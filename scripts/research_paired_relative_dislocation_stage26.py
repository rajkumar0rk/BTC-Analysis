#!/usr/bin/env python3
"""Stage26 BTC/ETH 4h relative-value dislocation reversion, matched causal rules."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_paired_absorption_stage25 import load_native,exit_replay,profit_factor
OUT=Path("analysis/paired_relative_dislocation_stage26")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
KEYS=["z_threshold","min_reversion","atr_stop","reward_R"]
CONFIGS=[(z,r,a,reward) for z in (1.2,1.8) for r in (.15,.35)
         for a in (1.5,2.5) for reward in (2.,3.)]
FEE=.0005*1.18;RISK=.005;MAX_LEVER=3.;INITIAL=10000.;HOLD=2880

def market_4h(f):
    b=f[["open","high","low","close"]].resample(
        "4h",closed="left",label="right").agg(
        {"open":"first","high":"max","low":"min","close":"last"})
    b["count"]=f.close.resample("4h",closed="left",label="right").count()
    b["good"]=b["count"].rolling(122,min_periods=122).min().eq(240)
    prev=b.close.shift(1)
    tr=pd.concat([b.high-b.low,(b.high-prev).abs(),(b.low-prev).abs()],axis=1).max(axis=1)
    b["atr"]=tr.rolling(14,min_periods=14).mean()
    return b

def signals(fbtc,feth):
    b=market_4h(fbtc);e=market_4h(feth)
    if not b.index.equals(e.index):raise AssertionError("4h markets not synchronized")
    spread=np.log(b.close/e.close)
    hist=spread.shift(1) # completed 4h prior history only
    mean=hist.rolling(120,min_periods=120).mean()
    sigma=hist.rolling(120,min_periods=120).std()
    z=(spread-mean)/sigma.replace(0,np.nan)
    prev=z.shift(1)
    valid=b.good&e.good&z.notna()&prev.notna()&(
        np.sign(z)==np.sign(prev))&(np.abs(z)<np.abs(prev))
    ix=fbtc.index.get_indexer(b.index)
    events=[]
    for i in np.flatnonzero(valid.to_numpy(bool)):
        k=int(ix[i]);zz=float(z.iat[i])
        delta=float(abs(prev.iat[i])-abs(zz))
        if k<0 or not np.isfinite(delta):continue
        events.append((k,-1 if zz>0 else 1,abs(zz),delta,
            float(b.atr.iat[i]),float(e.atr.iat[i])))
    return np.asarray(events,dtype=float).reshape(-1,6)

def sim_one(f,events,symbol,stress):
    op=f.open.to_numpy(float);hi=f.high.to_numpy(float)
    lo=f.low.to_numpy(float);cl=f.close.to_numpy(float)
    unix=f.time.to_numpy(np.int64)
    slip_btc=10. if stress else 5.
    slip_eth=.00035 if stress else .0002
    records=[];metrics=[]
    for zthr,minimum,atrstop,reward in CONFIGS:
        equity=INITIAL;peak=equity;dd=0.;busy=-1
        for kf,sidebtc,z,delta,atrbtc,atreth in events:
            k=int(kf);side=int(sidebtc) if symbol=="BTCUSD" else -int(sidebtc)
            if k<=busy or z<zthr or delta<minimum:continue
            atr=float(atrbtc if symbol=="BTCUSD" else atreth)
            ent=float(op[k]);risk=atr*atrstop
            if not np.isfinite(risk) or risk<=0 or risk/ent>.15:continue
            slip=slip_btc if symbol=="BTCUSD" else slip_eth*ent
            fill_in=ent+side*slip
            qty=min(equity*RISK/risk,equity*MAX_LEVER/fill_in)
            if qty<=0:continue
            j,exit_mid,why,worst=exit_replay(op,hi,lo,cl,k,side,risk,reward,HOLD)
            busy=j
            slip_out=slip_btc if symbol=="BTCUSD" else slip_eth*exit_mid
            fill_out=exit_mid-side*slip_out
            pnl=qty*(side*(fill_out-fill_in)-FEE*(fill_in+fill_out))
            adverse_out=worst-side*(slip_btc if symbol=="BTCUSD" else slip_eth*worst)
            open_low=equity+qty*(side*(adverse_out-fill_in)-FEE*(fill_in+adverse_out))
            dd=max(dd,100*(1-min(equity,open_low)/peak))
            start_equity=equity;equity+=pnl
            if equity<=0:raise RuntimeError("Bankrupt model")
            peak=max(peak,equity);dd=max(dd,100*(1-equity/peak))
            records.append(dict(symbol=symbol,z_threshold=zthr,min_reversion=minimum,
                atr_stop=atrstop,reward_R=reward,stress=stress,
                entry_unix=int(unix[k]),exit_unix=int(unix[j]),side=side,
                zscore_at_signal=z,reversion_score=delta,entry_mid=ent,
                exit_mid=float(exit_mid),entry_fill=fill_in,exit_fill=fill_out,
                quantity=qty,leverage=qty*fill_in/start_equity,
                start_equity_usd=start_equity,end_equity_usd=equity,
                risk_distance=risk,net_usd=float(pnl),
                reason=("stop","target","timeout")[why]))
        metrics.append(dict(symbol=symbol,z_threshold=zthr,min_reversion=minimum,
            atr_stop=atrstop,reward_R=reward,stress=stress,
            final_equity_usd=equity,max_drawdown_pct=dd))
    return pd.DataFrame(records),pd.DataFrame(metrics)

def month_reports(ledger,metrics):
    cols=["symbol"]+KEYS+["stress"]
    ledger["month_ist"]=pd.to_datetime(ledger.exit_unix,unit="s",utc=True
        ).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    months=[];summaries=[]
    for row in metrics.itertuples(index=False):
        settings={k:getattr(row,k) for k in cols}
        g=ledger
        for k,v in settings.items():g=g[g[k]==v]
        g=g.sort_values(["exit_unix","entry_unix"],kind="stable")
        equity=INITIAL;monthly=[]
        for mon in MONTHS:
            s=g[g.month_ist==mon]
            pnl=float(s.net_usd.sum());start=equity;equity+=pnl
            d=dict(settings,month_ist=mon,trades=len(s),
                wins=int((s.net_usd>0).sum()),losses=int((s.net_usd<0).sum()),
                net_pnl_usd=pnl,gross_profit_net_usd=float(s.net_usd.clip(lower=0).sum()),
                gross_loss_net_usd=float(s.net_usd.clip(upper=0).sum()),
                profit_factor=profit_factor(s.net_usd),
                net_return_pct=100*pnl/start,start_equity_usd=start,end_equity_usd=equity)
            months.append(d);monthly.append(d)
        if not np.isclose(equity,row.final_equity_usd):raise AssertionError("Equity ledger mismatch")
        m=pd.DataFrame(monthly);v=m.net_return_pct.to_numpy(float)
        if m.trades.sum()!=len(g):raise AssertionError("Monthly trade count mismatch")
        meaningful=m[(m.trades>=3)&np.isfinite(m.profit_factor)]
        t25=g[g.month_ist.str.startswith("2025-")]
        t26=g[g.month_ist.str.startswith("2026-")]
        summaries.append(dict(settings,
            trades=len(g),wins=int((g.net_usd>0).sum()),
            losses=int((g.net_usd<0).sum()),PF_overall=profit_factor(g.net_usd),
            PF_2025=profit_factor(t25.net_usd),PF_2026YTD=profit_factor(t26.net_usd),
            strong_months=int(((m.profit_factor>=1.5)&(m.trades>=3)).sum()),
            strong_positive_months=int(((m.profit_factor>=1.5)&(m.trades>=3)&(m.net_return_pct>0)).sum()),
            strong_5pct_months=int(((m.profit_factor>=1.5)&(m.trades>=3)&(m.net_return_pct>=5)).sum()),
            months_positive=int((v>0).sum()),months_negative=int((v<0).sum()),
            months_ge5pct=int((v>=5).sum()),months_ge10pct=int((v>=10).sum()),
            months_ge20pct=int((v>=20).sum()),
            median_month_return_pct=float(np.median(v)),
            median_finite_PF_3trades=float(meaningful.profit_factor.median()) if len(meaningful) else None,
            worst_month_pct=float(min(v)),
            net_return_2025_FULL_YEAR_pct=100*(m.iloc[11].end_equity_usd/INITIAL-1),
            net_return_2026_JanOct_YTD_pct=100*(m.iloc[-1].end_equity_usd/m.iloc[11].end_equity_usd-1),
            net_return_22months_pct=100*(equity/INITIAL-1),
            max_drawdown_pct=float(row.max_drawdown_pct),
            over_500pct_2025_full_year=bool(m.iloc[11].end_equity_usd>6*INITIAL)))
    return pd.DataFrame(months),pd.DataFrame(summaries)

def match(df,setting):
    for k in KEYS:df=df[df[k]==setting[k]]
    return df

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    btc,quality_btc=load_native("BTCUSD")
    eth,quality_eth=load_native("ETHUSD")
    if not btc.index.equals(eth.index):raise AssertionError("Original source timestamps differ")
    events=signals(btc,eth)
    if not len(events):raise RuntimeError("Zero relative-price events")
    ledgers=[];scenarios=[]
    for symbol,f in (("BTCUSD",btc),("ETHUSD",eth)):
        for stress in (False,True):
            tr,m=sim_one(f,events,symbol,stress)
            ledgers.append(tr);scenarios.append(m)
    trades=pd.concat(ledgers,ignore_index=True)
    metrics=pd.concat(scenarios,ignore_index=True)
    if trades.empty:raise RuntimeError("No trades")
    trades.to_csv(OUT/"all_original_trade_ledgers.csv.gz",index=False,compression="gzip")
    monthly,summary=month_reports(trades,metrics)
    monthly.to_csv(OUT/"all_months.csv.gz",index=False,compression="gzip")
    summary.to_csv(OUT/"all_summaries.csv",index=False)
    rankings=[]
    for params,s in summary[~summary.stress].groupby(KEYS):
        if len(s)!=2:raise AssertionError("Missing paired scenario")
        x=match(monthly,dict(zip(KEYS,params)))
        x=x[(~x.stress)&x.month_ist.str.startswith("2025-")]
        rankings.append(dict(zip(KEYS,params),
            jointly_pf1p5_and_5pct=int(((x.profit_factor>=1.5)&(x.trades>=3)&(x.net_return_pct>=5)).sum()),
            strong_pf_months=int(((x.profit_factor>=1.5)&(x.trades>=3)).sum()),
            positive_months=int((x.net_return_pct>0).sum()),
            median_month_return=float(x.net_return_pct.median()),
            trades_2025=int(x.trades.sum()),
            drawdown=float(s.max_drawdown_pct.max())))
    ranks=pd.DataFrame(rankings).sort_values(
        ["jointly_pf1p5_and_5pct","strong_pf_months","positive_months",
         "median_month_return","trades_2025","drawdown"],
        ascending=[False,False,False,False,False,True],kind="stable")
    ranks.to_csv(OUT/"2025_shared_ranking.csv",index=False)
    chosen=ranks.iloc[0]
    chosen_month=match(monthly,chosen)
    chosen_month=chosen_month[~chosen_month.stress].sort_values(["month_ist","symbol"])
    chosen_month.to_csv(OUT/"selected_22_months.csv",index=False)
    chosen_summary=match(summary,chosen)
    chosen_summary.to_csv(OUT/"selected_summaries.csv",index=False)
    match(trades,chosen).to_csv(OUT/"selected_original_trade_ledger.csv.gz",index=False,compression="gzip")
    quality={"rule":"4h log BTC/ETH price ratio z-score vs previous 120 completed 4h bars; enter relative mean reversion after initial inward z-score movement",
        "causality":"Completed 4h right-edge signals, execution on next 1m open; no future values in history",
        "independent_models_each_market":len(CONFIGS),"candidate_events":len(events),
        "shared_2025_selection_only":True,
        "sources":{"BTCUSD":quality_btc,"ETHUSD":quality_eth},
        "fees":{"taker_side":.0005,"GST":.18,"BTC_slip_per_side":5,"BTC_stress":10,
           "ETH_slip_fraction_per_side":.0002,"ETH_stress":.00035},
        "risk":{"initial_usd":INITIAL,"trade_risk":RISK,"max_leverage":MAX_LEVER,
           "max_hold_minutes":HOLD},
        "limitations":["2025 January missing first 330 IST minutes",
           "Funding settlement cashflow not reconstructed",
           "Actual historical bid-ask, L2 depth and price impact not verified",
           "Contract lot sizes, maintenance margin and liquidation not verified",
           "Contrarian side on BTC vs ETH does not guarantee synchronized market-neutral hedge",
           "Same 1m bar stop/target ambiguous => stop wins; gap stop adverse",
           "2026 previously seen, not a pristine forward holdout"]}
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2,default=str)+"\n")
    report=["# Stage26 cross-asset relative BTC/ETH dislocation and reversion",
        "Both native perpetual instruments use identical dimensionless rules, symmetric relative directions.",
        "2025 shared monthly selection applied unchanged in 2026; no live validation.",
        "## 2025-only candidate ranking",ranks.head(12).to_markdown(index=False),
        "## Selected BTC vs ETH 22 IST calendar months",
        chosen_month[["month_ist","symbol","net_return_pct","profit_factor","trades",
                     "wins","losses"]].to_markdown(index=False),
        "## 2025 full calendar year vs 2026 Jan-Oct YTD",
        chosen_summary.to_markdown(index=False),"## Assumptions and exclusions",
        json.dumps(quality,indent=2)]
    (OUT/"RESEARCH_REPORT.md").write_text("\n\n".join(report)+"\n")
    print("STAGE26_COMPLETE",json.dumps({"candidate_events":len(events),
        "selected":chosen_summary[~chosen_summary.stress].to_dict(orient="records")},default=str))
if __name__=="__main__":main()
