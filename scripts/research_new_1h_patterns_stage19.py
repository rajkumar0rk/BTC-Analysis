#!/usr/bin/env python3
"""Stage19: independent 1H BTC price-action patterns for monthly consistency.

New strategy families: liquidity sweep/reclaim, failed breakout, compressed
expansion, strong momentum, EMA20 pullback continuation, exhaustion reversal,
inside-bar breakout. Explicit LONG/SHORT rules, 4H regime pre-entry filters,
1m next-open fills, structural stops, stop-first replay. No Stage14/18 strategy
is modified. Training rank uses 2025 only; 2026 is previously explored
and cannot serve as a pristine OOS test.

All profits are simulated net R at the assumed fixed fraction 0.5% equity
risk per trade and standard taker fees/GST/slippage; no account margin model.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive, FEE, SLIPPAGE
from research_structure_rr_stage11 import replay_one
from research_monthly_regime_stage14 import regime_data

OUT=Path("analysis/institutional_discovery_stage19_new_1h_patterns")
MONTHS=pd.period_range("2025-01","2026-11",freq="M").astype(str)
PATTERNS=(
    "sweep_reclaim_12h","failed_break_12h","compression_expansion_12h",
    "strong_momentum_6h","ema20_pullback_confirm",
    "overextension_reversal","inside_bar_breakout")
REGIMES=("all","4h_adx_le20","4h_adx_ge25","4h_efficiency_ge30",
         "4h_atr_ratio_le1")
REWARDS=(2.0,3.0)
HOLDS=(240,480)
RISK_PCT=.005
MIN_RISK=125.
MAX_RISK=1500.

def build_candidates(f,seg_end):
    b=f[["open","high","low","close","volume"]].resample(
        "1h",label="right",closed="left").agg({
            "open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    b["cnt"]=f.close.resample("1h",label="right",closed="left").count()
    complete=b.cnt.rolling(60,min_periods=60).min().eq(60)
    prior=b.close.shift(1)
    tr=pd.concat([b.high-b.low,(b.high-prior).abs(),(b.low-prior).abs()],
                 axis=1).max(axis=1)
    b["atr"]=tr.rolling(14,min_periods=14).mean()
    b["ema20"]=b.close.ewm(span=20,adjust=False).mean()
    b["ema50"]=b.close.ewm(span=50,adjust=False).mean()
    b["h12"]=b.high.shift(1).rolling(12,min_periods=12).max()
    b["l12"]=b.low.shift(1).rolling(12,min_periods=12).min()
    b["h6"]=b.high.shift(1).rolling(6,min_periods=6).max()
    b["l6"]=b.low.shift(1).rolling(6,min_periods=6).min()
    b["medspan"]=tr.shift(1).rolling(24,min_periods=24).median()
    b["volratio"]=b.volume/b.volume.shift(1).rolling(
        20,min_periods=20).mean().replace(0,np.nan)
    span=(b.high-b.low).replace(0,np.nan)
    loc=(b.close-b.low)/span
    body=(b.close-b.open).abs()/span
    bull=b.close>b.open
    bear=b.close<b.open
    prev_inside=(b.high.shift(1)<b.high.shift(2))&(
        b.low.shift(1)>b.low.shift(2))
    prev_hi12=b.high.shift(2).rolling(12,min_periods=12).max()
    prev_lo12=b.low.shift(2).rolling(12,min_periods=12).min()
    comp3=(b.high.shift(1)-b.low.shift(1)+
           b.high.shift(2)-b.low.shift(2)+
           b.high.shift(3)-b.low.shift(3))/3 < .75*b.medspan
    prior_break_up=b.close.shift(1)>prev_hi12
    prior_break_dn=b.close.shift(1)<prev_lo12
    trendup=(b.close>b.ema50)&(b.ema20>b.ema50)&(
        b.ema20.diff(3)>0)
    trenddn=(b.close<b.ema50)&(b.ema20<b.ema50)&(
        b.ema20.diff(3)<0)
    # Candidate close is at bar right edge. Position enters 1m OPEN
    # bearing exactly that timestamp (the first minute after signal).
    patterns={
        "sweep_reclaim_12h": (
            (b.low<b.l12)&(b.close>b.l12)&bull&(loc>=.7),
            (b.high>b.h12)&(b.close<b.h12)&bear&(loc<=.3)),
        "failed_break_12h":(
            prior_break_dn&(b.close>prev_lo12)&bull&(loc>=.65),
            prior_break_up&(b.close<prev_hi12)&bear&(loc<=.35)),
        "compression_expansion_12h":(
            comp3&(b.close>b.h12)&bull&(loc>=.75)&
                (body>=.45)&(b.volratio>=1.2),
            comp3&(b.close<b.l12)&bear&(loc<=.25)&
                (body>=.45)&(b.volratio>=1.2)),
        "strong_momentum_6h":(
            (b.close>b.h6)&bull&(loc>=.8)&(body>=.65)&
                (b.volratio>=1.2),
            (b.close<b.l6)&bear&(loc<=.2)&(body>=.65)&
                (b.volratio>=1.2)),
        "ema20_pullback_confirm":(
            trendup&(b.low.shift(1)<=b.ema20.shift(1))&
                (b.close>b.high.shift(1))&bull&(loc>=.7),
            trenddn&(b.high.shift(1)>=b.ema20.shift(1))&
                (b.close<b.low.shift(1))&bear&(loc<=.3)),
        "overextension_reversal":(
            (b.close.shift(1)<b.ema20.shift(1)-1.6*b.atr.shift(1))&
                bull&(b.close>b.close.shift(1))&(loc>=.7),
            (b.close.shift(1)>b.ema20.shift(1)+1.6*b.atr.shift(1))&
                bear&(b.close<b.close.shift(1))&(loc<=.3)),
        "inside_bar_breakout":(
            prev_inside&(b.close>b.high.shift(1))&bull&(loc>=.7),
            prev_inside&(b.close<b.low.shift(1))&bear&(loc<=.3)),
    }
    if tuple(patterns)!=PATTERNS:
        raise AssertionError("Pattern list changed")
    h4,_,_,_=regime_data(f)
    columns=["valid","adx","eff8","atr_ratio"]
    # At the signal timestamp, the completed bar's 4H close is known.
    h4data=h4.reindex(b.index,method="ffill")
    b["h4_valid"]=h4data["valid"].fillna(False).to_numpy(bool)
    b["h4_adx"]=h4data["adx"].to_numpy(float)
    b["h4_eff8"]=h4data["eff8"].to_numpy(float)
    b["h4_atr_ratio"]=h4data["atr_ratio"].to_numpy(float)
    known=complete&b.h4_valid&b.atr.gt(0)&b.h4_adx.notna()
    indexes=f.index.get_indexer(b.index)
    O=f.open.to_numpy(np.float64)
    raw=[]
    for name,(long,short) in patterns.items():
        for side,flag in [(1,long),(-1,short)]:
            ix=np.flatnonzero((known&flag.fillna(False)).to_numpy(bool))
            for j in ix:
                k=int(indexes[j])
                if k<0:continue
                # Historical source gap clips the max holding window. The
                # gap exclusion is data-quality censoring, not a signal.
                if seg_end[k]-k<max(HOLDS):continue
                price=float(O[k])
                atr=float(b.atr.iat[j])
                if side==1:
                    structural=min(float(b.low.iat[j]),
                        float(b.low.shift(1).iat[j])) - .1*atr
                else:
                    structural=max(float(b.high.iat[j]),
                        float(b.high.shift(1).iat[j])) + .1*atr
                risk=side*(price-structural)
                if not np.isfinite(risk) or not MIN_RISK<=risk<=MAX_RISK:
                    continue
                raw.append((name,int(side),int(k),
                    int(f.time.iat[k]),float(structural),float(risk),
                    float(b.h4_adx.iat[j]),float(b.h4_eff8.iat[j]),
                    float(b.h4_atr_ratio.iat[j])))
    out=pd.DataFrame(raw,columns=[
        "pattern","side","k","unix","stop","risk","h4_adx",
        "h4_eff8","h4_atr_ratio"])
    if out.empty:raise RuntimeError("No new 1H patterns")
    return out.sort_values(["k","pattern","side"],kind="stable")

def gate_mask(e,regime):
    if regime=="all":return np.ones(len(e),bool)
    if regime=="4h_adx_le20":return (e.h4_adx<=20).to_numpy(bool)
    if regime=="4h_adx_ge25":return (e.h4_adx>=25).to_numpy(bool)
    if regime=="4h_efficiency_ge30":return (e.h4_eff8>=.30).to_numpy(bool)
    if regime=="4h_atr_ratio_le1":return (e.h4_atr_ratio<=1.).to_numpy(bool)
    raise ValueError(regime)

def simulate(f,all_events):
    O=f.open.to_numpy(np.float64)
    H=f.high.to_numpy(np.float64)
    L=f.low.to_numpy(np.float64)
    C=f.close.to_numpy(np.float64)
    T=f.time.to_numpy(np.int64)
    rec=[]
    model_n=[]
    for pat in PATTERNS:
        events=all_events[all_events.pattern==pat]
        for reg in REGIMES:
            el=events.loc[gate_mask(events,reg)]
            for rr in REWARDS:
                for hold in HOLDS:
                    model=f"{pat}__{reg}__{rr:g}R__{hold}min"
                    last=-1
                    n=0
                    for z in el.itertuples(index=False):
                        if z.k<=last:continue
                        exit_k,why,gross,net,offer,netR,risk=replay_one(
                            O,H,L,C,int(z.k),int(z.side),float(z.stop),
                            float(rr),int(hold))
                        last=int(exit_k)
                        t=int(T[exit_k])
                        dt=pd.Timestamp(t,unit="s",tz="UTC").tz_convert(
                            "Asia/Kolkata")
                        month=dt.strftime("%Y-%m")
                        rec.append(dict(model=model,pattern=pat,regime=reg,
                            target_R=rr,max_hold=hold,entry_unix=int(z.unix),
                            exit_unix=t,month_ist=month,
                            direction="LONG" if z.side==1 else "SHORT",
                            net_R=float(netR),net_price_points=float(net),
                            risk_price_points=float(risk),
                            reason=["stop","target","timeout"][int(why)]))
                        n+=1
                    model_n.append(dict(model=model,n=n))
    if not rec:raise RuntimeError("No trades generated")
    return pd.DataFrame(rec),pd.DataFrame(model_n)

def summarize(tr,nmodels):
    bymonth=[]
    comparison=[]
    for model,z in tr.groupby("model",sort=True):
        z=z.sort_values("exit_unix",kind="stable")
        counts=z.groupby("month_ist").size()
        total_equity=100.
        monthly_returns=[]
        for m in MONTHS:
            x=z[z.month_ist==m]
            v=x.net_R.to_numpy(float)
            if (1+RISK_PCT*v<=0).any():
                raise ValueError("Model equity wipeout")
            ret=(np.prod(1+RISK_PCT*v)-1)*100
            total_equity*=1+ret/100
            monthly_returns.append(float(ret))
            bymonth.append(dict(model=model,month_ist=m,
                trades=len(x),net_R=round(float(v.sum()),4),
                modeled_return_pct=round(float(ret),4),
                status="No trades" if len(x)==0 else (
                    "Profit" if ret>1e-8 else "Loss" if ret<-1e-8 else "Flat")))
        vals=np.array(monthly_returns)
        n25=int((vals[:12]>1e-8).sum())
        n26=int((vals[12:]>1e-8).sum())
        l25=int((vals[:12]<-1e-8).sum())
        l26=int((vals[12:]<-1e-8).sum())
        t25=(z.exit_unix<1735689600+365*86400).sum() # only a rough count, not for selection
        c25=100*(np.prod(1+vals[:12]/100)-1)
        c26=100*(np.prod(1+vals[12:]/100)-1)
        comparison.append(dict(model=model,pattern=z.pattern.iloc[0],
            regime=z.regime.iloc[0],target_R=z.target_R.iloc[0],
            max_hold=int(z.max_hold.iloc[0]),trades=len(z),
            profitable_months_2025=n25,losing_months_2025=l25,
            no_trade_months_2025=int(12-n25-l25),
            modeled_2025_pct=round(c25,4),
            profitable_months_2026=n26,losing_months_2026=l26,
            no_trade_months_2026=int(11-n26-l26),
            modeled_2026_pct=round(c26,4),
            all_23_positive=bool(n25==12 and n26==11),
            useful_2025=bool(n25>=9 and c25>0 and
                              (z.month_ist.str.startswith("2025")).sum()>=35)))
    if len(comparison)!=len(nmodels):
        raise AssertionError("Some new model has 0 trades")
    return pd.DataFrame(bymonth),pd.DataFrame(comparison)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,_,ends,quality=read_archive()
    ev=build_candidates(f,ends)
    trades,nmodels=simulate(f,ev)
    months,results=summarize(trades,nmodels)
    ranked=results[results.useful_2025].sort_values([
        "profitable_months_2025","losing_months_2025",
        "modeled_2025_pct"],ascending=[False,True,False])
    if ranked.empty:
        ranked=results.sort_values(["profitable_months_2025",
            "modeled_2025_pct"],ascending=False)
    top=ranked.head(20)
    ev.to_csv(OUT/"candidates.csv.gz",index=False,compression="gzip")
    trades.to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    months.to_csv(OUT/"monthly_results.csv",index=False)
    results.to_csv(OUT/"all_model_summary.csv",index=False)
    top.to_csv(OUT/"top_2025_ranked_models.csv",index=False)
    quality_out=dict(
        candles=len(f),months=len(MONTHS),source_missing_minutes=quality["missing_minutes"],
        original_pattern_families=list(PATTERNS),regimes=list(REGIMES),
        source_event_candidates=len(ev),distinct_models=len(results),
        simulated_trade_rows=len(trades),
        all_positive_23=int(results.all_23_positive.sum()),
        useful_2025_models=int(results.useful_2025.sum()),
        costs="standard taker 0.05% each leg +18% GST +5 BTC points adverse slippage each side",
        hypothetical_risk_fraction=RISK_PCT,
        strategy_selection="select best candidates using 2025 only, report 2026 despite prior research exposure",
        caveats=[
            "All historical 2026 data was used previously; not pristine forward holdout",
            "Multiple hypothesis testing across entry families and risk parameters",
            "Missing 1m source day 2026-10-31; simulations censor entries near source gaps",
            "1m OHLC stop-first; unmodeled funding, spread, impact and liquidation",
            "Months with no trade are not counted as profitable",
            "Account percentage is a hypothetical constant-risk sizing model",
            "Each configuration is exclusive-position standalone; do not sum overlapping models",
            "No daily/weekly guard; no guaranteed monthly return"])
    (OUT/"quality.json").write_text(json.dumps(quality_out,indent=2)+"\n")
    report=[
        "# Stage19 — Research NEW 1-hour pattern families for monthly consistency",
        "",
        "This does not modify any previous Stage14, Stage18 or profit-lock strategies.",
        "Seven new 1H price-action families, five pre-entry 4H regimes, 2/3R,",
        "4h and 8h hold tested on Delta BTCUSD 1m, all months 2025/2026.",
        "Structural 1H stops, conservative stop-first 1m replay, fee/GST/slip.",
        "",
        "## Train selection and test outcome",
        "Candidate family and conditions selected by 2025 month results only.",
        "**2026 is previously research exposed and is not a pristine validation**.",
        f"Sampled models: {len(results)}; true 23-positive: {int(results.all_23_positive.sum())}.",
        "",
        "## Top 2025-ranked configurations and 2026 behavior",
        top.to_markdown(index=False),"",
        "## Monthly performance (top 5)",
        months[months.model.isin(top.model.head(5))].to_markdown(index=False),"",
        "## Caveats",
        *["- "+c for c in quality_out["caveats"]],
        "Use exact monthly CSV and full ledger for evidence and portfolio experiments.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE19_SUCCESS "+json.dumps({
        "models":len(results),"candidate_events":len(ev),
        "trades":len(trades),"useful_2025":int(results.useful_2025.sum()),
        "all_positive":int(results.all_23_positive.sum())}))
    print("TOP MODELS\n"+top.to_string(index=False))
if __name__=="__main__":
    main()
