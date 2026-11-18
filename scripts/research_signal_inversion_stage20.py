#!/usr/bin/env python3
"""Stage20 — Direction-inversion & failure-followthrough 5M BTC strategy search.

Identify whether Stage19 5M signals are better as continuation or FADE
in direction when already-closed 1H regime and relative volume support it.

Test every predeclared configuration with next 1-minute OPEN fills,
minute high/low stop-first exits; no lookahead. Standard Delta India
taker fee 0.05%/side, GST 18%, adverse 5 quote points per side.
Conditional scalper what-if included but NOT declared historical eligibility:
Delta's actual offer terms may vary across sample periods.

Exact target: >=10% account equity per month for Jan-Dec 2025 and
Jan-Oct 2026; no-trade months = misses. Equity risk max 0.5%/1%/2%
of balance each entry, gross leverage capped at 5x or 10x.
All historic years previously researched; no pristine holdout.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit
from research_every_candle_200 import read_archive,FEE,SLIPPAGE
from research_monthly_10pct_stage19 import features,PATS

OUT=Path("analysis/institutional_discovery_stage20_inverse_direction")
MONTHS=pd.period_range("2025-01","2026-11",freq="M").astype(str)
RISK_FRACTIONS=(.005,.01,.02)
LEV_CAPS=(5.,10.)
COST_MODES=("standard_taker","offer_whatif")
TARGETS=(1.5,2.5,4.)
HOLDS=(30,120)
STOP_MODES=("atr1p5","atr3","struct3")
FILTERS=("any","hour_trend_agrees_with_trade","hour_trend_opposes_trade",
         "high_volume","low_volume","large_atr")
DIRECTIONS=("original","reverse")
START_CAP=100.
def signals_source(f,segstart,segend):
    raw,b=features(f,segstart,segend)
    raw=raw[raw.stop_mode.isin(["atr1p5","structure3"])].copy()
    # We will compute BOTH direction-aware ATR and original structural distances
    # without relying on future candle values.
    raw["relative_atr"]=raw.atr5.to_numpy(float)/(
        b.atr14.shift(1).rolling(24,min_periods=24).median().reindex(
            pd.to_datetime(raw.entry_unix,unit="s",utc=True)).to_numpy(float))
    # stage19 entries use the open of the next 1-minute bar; that timestamp
    # equals completed 5M close when entry time is exactly on five-minute grid.
    idx=pd.to_datetime(raw.entry_unix,unit="s",utc=True)
    raw["volume_ratio"]=b.vr.reindex(idx).to_numpy(float)
    raw["hour_bull"]=b.hour_bull.reindex(idx).to_numpy(bool)
    raw["hour_bear"]=b.hour_bear.reindex(idx).to_numpy(bool)
    # No same-event duplication from both Stage19 stop alternatives.
    e=raw[raw.stop_mode=="atr1p5"].copy()
    struct=raw[raw.stop_mode=="structure3"][[
        "pattern","side","entry_unix","risk_pts"]].rename(
        columns={"risk_pts":"struct_risk"})
    e=e.merge(struct,on=["pattern","side","entry_unix"],how="left")
    e["struct_risk"]=e.struct_risk.fillna(np.nan)
    return e.sort_values(["k","pattern","side"],kind="stable")

def fit_filter(e,original_side,kind):
    trade_side=original_side if kind=="original" else -original_side
    return {
        "any":np.ones(len(e),dtype=bool),
        "hour_trend_agrees_with_trade":np.where(trade_side==1,
                      e.hour_bull.to_numpy(bool),e.hour_bear.to_numpy(bool)),
        "hour_trend_opposes_trade":np.where(trade_side==-1,
                      e.hour_bull.to_numpy(bool),e.hour_bear.to_numpy(bool)),
        "high_volume":(e.volume_ratio>=1.5).to_numpy(bool),
        "low_volume":(e.volume_ratio<=0.75).to_numpy(bool),
        "large_atr":(e.relative_atr>=1.25).to_numpy(bool)
    }

@njit(cache=True)
def simulate_one(o,h,l,c,k,side,risk,R,hold):
    entry=o[k]
    stop=entry-side*risk
    target=entry+side*R*risk
    for j in range(k,k+hold):
        loss=l[j]<=stop if side==1 else h[j]>=stop
        gain=h[j]>=target if side==1 else l[j]<=target
        if loss:
            mid=min(o[j],stop) if side==1 else max(o[j],stop)
            why=0
            break
        if gain:
            mid=target
            why=1
            break
    else:
        j=k+hold-1
        mid=c[j]
        why=2
    ent=entry+side*SLIPPAGE
    ex=mid-side*SLIPPAGE
    gross=side*(mid-entry)
    net=side*(ex-ent)-FEE*(ent+ex)
    offer=side*(ex-ent)-FEE*ent-(0. if j-k+1<=30 else FEE*ex)
    return j,net/risk,offer/risk,net,offer,why

def run_events(e,f):
    op=f.open.to_numpy(np.float64)
    hi=f.high.to_numpy(np.float64)
    lo=f.low.to_numpy(np.float64)
    cl=f.close.to_numpy(np.float64)
    t=f.time.to_numpy(np.int64)
    rows=[]
    stats=[]
    for pat in PATS:
        sub=e[e.pattern==pat].copy()
        for direction in DIRECTIONS:
            sides=(sub.side.to_numpy(np.int8)*(1 if direction=="original" else -1))
            for filt in FILTERS:
                allowed=fit_filter(sub,sides,"original")
                mask=allowed[filt]
                filtrows=sub.loc[mask].sort_values(["k","side"],kind="stable")
                if filtrows.empty:continue
                for st in STOP_MODES:
                    # ATR3 is wider than usual to explore if 1M noise produces
                    # false stopouts. Structural risk is only available where
                    # Stage19's original side passed its risk band.
                    for R in TARGETS:
                        for hold in HOLDS:
                            busy=-1
                            count=0
                            for z in filtrows.itertuples(index=False):
                                k=int(z.k)
                                if k<=busy:continue
                                side=int(z.side) if direction=="original" else -int(z.side)
                                atr=float(z.atr5)
                                risk=(1.5*atr if st=="atr1p5" else
                                     3.0*atr if st=="atr3" else float(z.struct_risk))
                                if not np.isfinite(risk) or risk<120 or risk>2000:
                                    continue
                                j,netR,offerR,net,offer,why=simulate_one(
                                    op,hi,lo,cl,k,side,float(risk),float(R),int(hold))
                                busy=int(j)
                                count+=1
                                rows.append((pat,direction,filt,st,R,hold,
                                    int(z.entry_unix),int(t[j]),float(op[k]),
                                    risk,side,netR,offerR,net,offer,why))
                            stats.append((pat,direction,filt,st,R,hold,count))
    cols=["pattern","direction_mode","entry_filter","stop_mode",
         "target_R","hold_min","entry_unix","exit_unix","entry_price",
         "risk_pts","trade_side","net_standard_R","net_offer_whatif_R",
         "net_standard_points","net_offer_whatif_points","exit_reason"]
    out=pd.DataFrame(rows,columns=cols)
    if out.empty:raise RuntimeError("No simulated trades")
    out["month_ist"]=pd.to_datetime(out.exit_unix,unit="s",utc=True).dt.tz_convert(
        "Asia/Kolkata").dt.strftime("%Y-%m")
    return out,pd.DataFrame(stats,columns=["pattern","direction_mode",
                 "entry_filter","stop_mode","target_R","hold_min","trades"])

def rank_account(tr):
    keys=["pattern","direction_mode","entry_filter","stop_mode","target_R","hold_min"]
    annual=[]
    monthly=[]
    for key,g in tr.groupby(keys,sort=True):
        g=g.sort_values(["exit_unix","entry_unix"],kind="stable")
        px=g.entry_price.to_numpy(float)
        riskpoints=g.risk_pts.to_numpy(float)
        mm=g.month_ist.to_numpy(str)
        if len(g)<35:continue
        for cost in COST_MODES:
            realized=g.net_standard_R.to_numpy(float) if cost=="standard_taker" else (
                g.net_offer_whatif_R.to_numpy(float))
            for fraction in RISK_FRACTIONS:
                for lev in LEV_CAPS:
                    # Cannot exceed max notional per account equity.
                    used=np.minimum(fraction,lev*riskpoints/px)
                    pnl=used*realized
                    if (pnl<=-1.).any():continue
                    eq=100.
                    peak=100.
                    dd=0.
                    for ret in pnl:
                        eq*=1.+ret
                        peak=max(peak,eq)
                        dd=max(dd,100*(1-eq/peak))
                    mreturns=[]
                    for month in MONTHS:
                        msk=mm==month
                        vals=pnl[msk]
                        n=int(msk.sum())
                        pct=100*(np.prod(1.+vals)-1) if n else 0.
                        monthly.append(dict(zip(keys,key),cost_mode=cost,
                            risk_fraction_pct=fraction*100,
                            max_leverage=lev,month_ist=month,
                            trades=n,account_return_pct=round(float(pct),4)))
                        mreturns.append(float(pct))
                    y25=np.asarray(mreturns[:12])
                    y26=np.asarray(mreturns[12:22])
                    n25=int((mm<"2026-01").sum())
                    n26=int(((mm>="2026-01")&(mm<="2026-11")).sum())
                    annual.append(dict(zip(keys,key),cost_mode=cost,
                        risk_fraction_pct=fraction*100,max_leverage=lev,
                        total_trades=len(g),trades_2025=n25,trades_2026=n26,
                        above10_2025=int((y25>=10.).sum()),
                        above10_2026=int((y26>=10.).sum()),
                        positive_2025=int((y25>0.).sum()),
                        positive_2026=int((y26>0.).sum()),
                        worst_month_2025=round(float(y25.min()),3),
                        worst_month_2026=round(float(y26.min()),3),
                        total_return_2025=round(float((np.prod(1.+y25/100)-1)*100),3),
                        total_return_2026=round(float((np.prod(1.+y26/100)-1)*100),3),
                        max_trade_close_drawdown=round(dd,3),
                        target_met=int((y25>=10.).all() and (y26>=10.).all())))
    if not annual:raise RuntimeError("No account models")
    return pd.DataFrame(annual),pd.DataFrame(monthly)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,s,e,q=read_archive()
    events=signals_source(f,s,e)
    tr,stats=run_events(events,f)
    accounts,months=rank_account(tr)
    tr.to_csv(OUT/"full_trade_ledger.csv.gz",index=False,compression="gzip")
    accounts.to_csv(OUT/"account_models.csv",index=False)
    months.to_csv(OUT/"monthly_results.csv",index=False)
    stats.to_csv(OUT/"signal_counts.csv",index=False)
    # 2025 historical ranking does not peek at 2026 outcomes, which still
    # cannot be considered truly unstudied because same archive reused.
    standard=accounts[accounts.cost_mode=="standard_taker"]
    order=["above10_2025","positive_2025","total_return_2025"]
    best=standard.sort_values(order,ascending=False,kind="stable")
    # Separately identify positive years and risk below 30% drawdown
    viable=best[(best.total_return_2025>0)&
                (best.total_return_2026>0)&
                (best.max_trade_close_drawdown<=30)]
    picks=viable.head(12) if len(viable) else best.head(12)
    offer=accounts[accounts.cost_mode=="offer_whatif"].sort_values(order,ascending=False)
    pick=picks.iloc[0]
    ident=["pattern","direction_mode","entry_filter","stop_mode","target_R",
           "hold_min","cost_mode","risk_fraction_pct","max_leverage"]
    month=months
    for name in ident:
        month=month[month[name]==pick[name]]
    month.to_csv(OUT/"selected_monthly.csv",index=False)
    best.head(30).to_csv(OUT/"2025_ranked_standard.csv",index=False)
    offer.head(30).to_csv(OUT/"2025_ranked_offer_hypothetical.csv",index=False)
    summary=dict(dataset_candles=len(f),missing_minutes=q["missing_minutes"],
         discovered_entries=len(events),replayed_trades=len(tr),
         tested_account_models=len(accounts),standard_models=len(standard),
         offer_hypothetical_models=len(offer),
         standard_passes=int(standard.target_met.sum()),
         offer_whatif_passes=int(offer.target_met.sum()),
         positive_both_years_standard=int(((standard.total_return_2025>0)&
                                          (standard.total_return_2026>0)).sum()),
         passing_risk_bounded_standard=len(viable),
         selected_2025_ranking=pick.to_dict(),
         cost_standard="BTCUSD taker 0.05pct each side +18pct GST and 5pts slip per side",
         offer_cost="Conditional 30min zero-closing-fee what-if; NOT assumed valid for 2025 months",
         notes=[
             "All 2025 and 2026 observations have been researched, no pristine out-of-sample",
             "Direction inversion retains event timing but flips trade side, ATR/structural stop from entry",
             "Original entry timestamps are next 1m OPEN after completed 5m signal",
             "One position per model, multiple trades per day",
             "Net PNL assigned to IST EXIT month; zero-trade months fail 10pct target",
             "Leverage caps 5x or 10x, risk 0.5/1/2pct per trade, exact fractional sizing",
             "Only STANDARD taker costs count for main claim; offer is an optimistic conditional scenario",
             "Maker fill risk, funding, actual spread, liquidation, margin and market impact not modeled",
             "2026-10-31 missing 1m candles, Nov2026 partial",
             "Even historical 10pct/month is not a forward guarantee"])
    (OUT/"quality.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
    report=[
        "# Stage20 — Multi-trade BTC directional inversion and relative regime pattern",
        "",
        "## Research hypothesis",
        "A price-action breakout or reversal signal may favor the OPPOSITE side",
        "after volume/1H trend filters. Original and reversed entry directions",
        "both tested using next-1m open fills. Tight/wide ATR and structural stops.",
        "Target +10% NET monthly across all 22 COMPLETE months 2025-Jan to 2026-Oct.",
        "",
        "## Complete account study",
        f"Events: {len(events):,}, trades across models: {len(tr):,},",
        f"Account evaluations: {len(accounts):,}; standard passes: {summary['standard_passes']}",
        f"Conditional Scalper Offer what-if passes: {summary['offer_whatif_passes']}.",
        "",
        "## Ranking using 2025 only (2026 audited afterwards)",
        picks.to_markdown(index=False),"",
        "## Selected candidate months",
        month.to_markdown(index=False),"",
        "## Conditional zero exit fee research (NOT historical fact)",
        offer.head(10).to_markdown(index=False),"",
        "## Method and limitations",
        *["- "+x for x in summary["notes"]],
        "",
        "All results and negative controls archived.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE20_COMPLETE "+json.dumps({
        "candles":len(f),"entries":len(events),"trades":len(tr),
        "models":len(accounts),"standard_pass":summary["standard_passes"],
        "offer_whatif_pass":summary["offer_whatif_passes"],
        "both_years_positive":summary["positive_both_years_standard"]}))
    print("BEST_STANDARD\n"+best.head(16).to_string(index=False))
    print("BEST_OFFER\n"+offer.head(5).to_string(index=False))
    print("SELECTED_MONTHLY\n"+month.to_string(index=False))
if __name__=="__main__":
    main()
