#!/usr/bin/env python3
"""Stage18/20 BTC-first *monthly portfolio* improvement and stress replay.

This uses preserved Stage15/17/19 monthly backtests, NOT a fresh native 1m
trade-execution replay. Stage18/20 already blend independently sized sleeves.
BTC 2025 is the sole variant-selection sample. BTC 2026 and ETH are checks only.
No ETH tuning, no 2026 tuning, no live orders. Original baselines retained.
"""
import csv
import json
import math
from pathlib import Path

OUT=Path("analysis/stage18_stage20_improvement_20261120")
MONTHS=[f"{y}-{m:02d}" for y in (2025,2026) for m in range(1,13 if y==2025 else 11)]
REPO="rajkumar0rk/BTC-Analysis"
STAGE15="quiet_1h_weekly_3R"
STAGE17="1D_channel_20_no_trend_filter_trail_3atr"
STAGE19="strong_momentum_6h__4h_adx_le20__3R__480min"
STAGE20_SELECTED=Path("analysis/institutional_discovery_stage20_three_sleeve/selected_month_by_month.csv")
STAGE18_ALL=Path("analysis/institutional_discovery_stage18_monthly_dual_strategy/monthly_blended_returns.csv")
ETH20_SELECTED=Path("analysis/ethusd_all_strategy_replay/price_structures/source_results/institutional_discovery_stage20_three_sleeve/selected_month_by_month.csv")
ETH17_MONTHLY=Path("analysis/ethusd_all_strategy_replay/price_structures/source_results/institutional_discovery_stage17_swing_breakout/monthly_mark_to_market.csv")
ETH19_MONTHLY=Path("analysis/ethusd_all_strategy_replay/price_structures/source_results/institutional_discovery_stage19_new_1h_patterns/monthly_results.csv")
BASIS=("Stage18","Stage20")
# Predeclared, small causal search; no wide grid and no ETH/2026 selection.
VARIANTS={
 "Stage18":[
  ("original",.25,0.0,"none"),
  ("more_swing50",.50,0.0,"none"),
  ("prev_loss_half",.25,0.0,"prev_loss_half"),
  ("two_month_weak_half",.25,0.0,"two_month_weak_half")],
 "Stage20":[
  ("original",.25,.10,"none"),
  ("less_hourly05",.25,.05,"none"),
  ("prev_loss_half",.25,.10,"prev_loss_half"),
  ("two_month_weak_half",.25,.10,"two_month_weak_half"),
  ("less_hourly05_prev_loss_half",.25,.05,"prev_loss_half")]
}
STRESS_PCT=(0.0,0.10,0.25) # PESSIMISTIC extra NAV haircut EACH calendar month, incl inactive.
def read(path):
    with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def num(row,key):return float(row[key])
def monthmap(rows, selector, valkey):
    found={r["month_ist"]:num(r,valkey) for r in rows if selector(r) and r["month_ist"] in MONTHS}
    if sorted(found)!=MONTHS:raise AssertionError(f"month coverage {valkey}: {len(found)} of 22")
    return [found[m] for m in MONTHS]
def source_sleeves(symbol):
    if symbol=="BTCUSD":
        rows=read(STAGE18_ALL)
        select=lambda r: r["stage15"]==STAGE15 and r["stage17"]==STAGE17 and abs(num(r,"swing_weight")-.25)<1e-8
        base=monthmap(rows,select,"portfolio_pct")
        rang=monthmap(rows,select,"range_component_pct")
        swing=monthmap(rows,select,"swing_component_pct")
        aux=monthmap(read(STAGE20_SELECTED),lambda r:r["stage19_model"]==STAGE19,"stage19_month_pct")
        original20=monthmap(read(STAGE20_SELECTED),lambda r:r["stage19_model"]==STAGE19,"portfolio_month_pct")
    else:
        rows=read(ETH20_SELECTED)
        base=monthmap(rows,lambda r:True,"stage18_month_pct")
        swing=monthmap(read(ETH17_MONTHLY),lambda r:r["model"]==STAGE17,"month_return_pct")
        # Recover quiet-volume sleeve from exact frozen 75/25 Stage18 source
        rang=[(b-.25*s)/.75 for b,s in zip(base,swing)]
        aux=monthmap(read(ETH19_MONTHLY),lambda r:r["model"]==STAGE19,"modeled_return_pct")
        original20=[] # ETH source chose another hourly component, not the BTC-selected one
    for i,b in enumerate(base):
        if abs(b-(.75*rang[i]+.25*swing[i]))>.005:
            raise AssertionError(f"Stage18 source mismatch {symbol} {MONTHS[i]}")
    if original20:
        for i,c in enumerate(original20):
            if abs(c-(.9*base[i]+.1*aux[i]))>.005:
                raise AssertionError(f"Stage20 source mismatch {symbol} {MONTHS[i]}")
    return {"range":rang,"swing":swing,"hourly":aux,"stage18":base}
def raw_returns(d,weight,aux):
    return [((1-aux)*((1-weight)*r+weight*s)+aux*h) for r,s,h in
            zip(d["range"],d["swing"],d["hourly"])]
def risk_multipliers(raw,mode):
    out=[]
    for i in range(len(raw)):
        if mode=="none":fraction=1.
        elif mode=="prev_loss_half":fraction=.5 if i>0 and raw[i-1]<0 else 1.
        elif mode=="two_month_weak_half":
            fraction=.5 if i>=2 and ((1+raw[i-1]/100)*(1+raw[i-2]/100)-1)<0 else 1.
        else:raise ValueError(mode)
        out.append(fraction)
    return out
def calc(d,weight,aux,mode,stress):
    original=raw_returns(d,weight,aux)
    risk=risk_multipliers(original,mode)
    # Includes a deliberately conservative account-level monthly cost BUFFER
    # on top of all original fees/GST/assumed slippage, NOT new simulated fills.
    net=[x*f-stress for x,f in zip(original,risk)]
    if min(net)<=-100:raise AssertionError("bankrupt month")
    eq=100.;peak=eq;dd=0.;nav=[];rows=[]
    for m,x,o,f in zip(MONTHS,net,original,risk):
        old=eq;eq*=1+x/100;peak=max(peak,eq)
        dd=max(dd,100*(1-eq/peak))
        nav.append(eq)
        rows.append(dict(month=m,original_month_pct=round(o,7),
                         risk_fraction=f,extra_cost_buffer_pct=stress,
                         adjusted_month_pct=round(x,7),
                         start_nav=round(old,8),end_nav=round(eq,8),
                         result="positive" if x>1e-9 else "negative" if x<-1e-9 else "flat"))
    def split(a,b):
        q=net[a:b];v=100
        for x in q:v*=1+x/100
        return dict(net_pct=round(v-100,6),positive=sum(x>1e-9 for x in q),
                    negative=sum(x<-1e-9 for x in q),
                    flat=sum(abs(x)<=1e-9 for x in q),
                    worst_month_pct=round(min(q),6),
                    median_month_pct=round(sorted(q)[len(q)//2-1]/2+sorted(q)[len(q)//2]/2 if len(q)%2==0 else sorted(q)[len(q)//2],6))
    s25=split(0,12);s26=split(12,22)
    full=split(0,22)
    return rows,dict(net_2025_pct=s25["net_pct"],net_2026_JanOct_pct=s26["net_pct"],
                     net_22_month_pct=round(eq-100,6),positive_months=full["positive"],
                     losing_months=full["negative"],flat_months=full["flat"],
                     worst_month_pct=full["worst_month_pct"],
                     max_month_end_drawdown_pct=round(dd,6),
                     train_2025=s25,check_2026=s26)
def writecsv(path,rows):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    data={sym:source_sleeves(sym) for sym in ("BTCUSD","ETHUSD")}
    summaries=[];monthly=[];decisions=[];selection={}
    for family in BASIS:
        scored=[]
        for name,swing,aux,gate in VARIANTS[family]:
            btc_rows,train=calc(data["BTCUSD"],swing,aux,gate,.10)
            # Only the first 12 months (2025), after extra cost buffer, choose improvement.
            p=train["train_2025"]
            train_nav=100.;peak=100.;maxdd=0.
            for row in btc_rows[:12]:
                train_nav=row["end_nav"];peak=max(peak,train_nav)
                maxdd=max(maxdd,100*(1-train_nav/peak))
            score=p["net_pct"]-.75*maxdd-.25*max(0,-p["worst_month_pct"])
            scored.append(dict(family=family,variant=name,weight_swing=swing,weight_hourly=aux,
                               gate=gate,score_2025=round(score,6),
                               train_return_pct=p["net_pct"],train_winners=p["positive"],
                               train_dd_pct=round(maxdd,6)))
        # Rank strictly on BTC 2025; 2026 and ETH never influence choice.
        scored.sort(key=lambda z:(z["score_2025"],z["train_return_pct"],z["train_winners"]),reverse=True)
        chosen=scored[0]["variant"]
        selection[family]={"chosen_on_BTC2025":chosen,"ranking":scored,
                           "selection_rule":"BTC 2025 10bp-per-month stress return - 0.75*2025 month-end DD - 0.25*abs(worst losing month)"}
        for symbol in data:
            for name,weight,aux,gate in VARIANTS[family]:
                for stress in STRESS_PCT:
                    month,stat=calc(data[symbol],weight,aux,gate,stress)
                    identity=dict(family=family,market=symbol,variant=name,
                                  btc_2025_selected=name==chosen,
                                  swing_weight=weight,aux_weight=aux,month_risk_gate=gate,
                                  cost_buffer_pct_per_month=stress)
                    summaries.append(dict(**identity,**{k:v for k,v in stat.items() if k not in ("train_2025","check_2026")}))
                    monthly.extend([dict(**identity,**r) for r in month])
        bas=[r for r in summaries if r["family"]==family and r["market"]=="BTCUSD" and r["variant"]=="original" and r["cost_buffer_pct_per_month"]==0][0]
        sel=[r for r in summaries if r["family"]==family and r["market"]=="BTCUSD" and r["variant"]==chosen and r["cost_buffer_pct_per_month"]==0][0]
        eth=[r for r in summaries if r["family"]==family and r["market"]=="ETHUSD" and r["variant"]==chosen and r["cost_buffer_pct_per_month"]==0][0]
        stress=[r for r in summaries if r["family"]==family and r["market"]=="BTCUSD" and r["variant"]==chosen and r["cost_buffer_pct_per_month"]==.25][0]
        decisions.append(dict(family=family,selected_variant=chosen,
                              original_BTC_return_pct=bas["net_22_month_pct"],
                              selected_BTC_return_pct=sel["net_22_month_pct"],
                              change_BTC_percentage_points=round(sel["net_22_month_pct"]-bas["net_22_month_pct"],6),
                              selected_BTC_positive_months=sel["positive_months"],
                              selected_BTC_losing_months=sel["losing_months"],
                              selected_BTC_month_end_drawdown_pct=sel["max_month_end_drawdown_pct"],
                              selected_BTC_after_additional_25bp_monthly_pct=stress["net_22_month_pct"],
                              frozen_ETH_return_pct=eth["net_22_month_pct"],
                              frozen_ETH_positive_months=eth["positive_months"],
                              caution="Monthly portfolio overlay ONLY, not new execution-price simulation or proven live edge"))
    writecsv(OUT/"all_monthly_nav.csv",monthly)
    writecsv(OUT/"all_candidate_summary.csv",summaries)
    writecsv(OUT/"selected_comparisons.csv",decisions)
    (OUT/"selection_btc2025_only.json").write_text(json.dumps(selection,indent=2)+"\n")
    caveats=[
      "SOURCE is existing historical MONTHLY Stage18/20 component NAV returns; this is an executed portfolio-allocation/cost-stress BACKTEST, NOT an original 1m entry/fill/exit rerun.",
      "The immutable Stage18 baseline is the Stage20 base (75% BTC quiet 1H pullback, 25% daily20 Donchian); this is distinct from the Stage18 original top-ranked daily55 model.",
      "Stage20 historical baseline combines 90% fixed Stage18 with 10% BTC-selected hourly momentum sleeve; frozen to ETH with identical parameter definitions.",
      "BTC 2025 selects allocation/risk rule only. BTC 2026 and ETH use exactly frozen BTC-picked choice and were not used to pick it. Source hypotheses/parameters have already seen historic 2026: NOT pristine OOS.",
      "Original component backtests include taker fee, GST and assumed slippage, but DO NOT fully model real bid-ask spread, funding, individual lot minimums, cross-sleeve margin/liquidation or rebalancing fees.",
      "Additional stress is a deterministic conservative 10bp or 25bp monthly NAV haircut, even on flat/no-exposure months; NOT an exchange-verified fee or exact slippage re-execution.",
      "Portfolio component timing inconsistent (Stage15 realizes in exit month; Stage17 marks at month end; Stage19 monthly summary books exits); independent positions can overlap. Full one-minute integrated margin-aware replay remains mandatory before trading.",
      "ETH original price-normalized replay not independently verified against native ETH tick/contract size. Native ETH execution audit required.",
      "Month-end equity drawdown UNDERSTATES intramonth liquidation and equity troughs. No trade-level PF can be inferred from NAV-only series; trade-level PF NOT VERIFIED.",
      "January 2025 IST begins before source data and Oct 2026 upstream was flagged as incomplete in historical reports. Source hashes and dates should be independently re-audited.",
      "The 2025 model family was already screened extensively; new rule selection adds multiple-testing risk. No live/paper trading deployment was performed."
    ]
    report=["# Stage18 and Stage20 BTC-first controlled monthly portfolio improvements","",
            "Source baselines preserved, original trading engines unchanged.","",
            "## Completed BTC-first selection and frozen ETH check","",
            "| Family | BTC-2025-selected variant | Original BTC 22m | Selected BTC 22m | BTC positive months | BTC month-end DD | Selected ETH 22m | 25bp monthly extra-cost BTC |",
            "|---|---|---:|---:|---:|---:|---:|---:|"]
    for d in decisions:
        report.append(f"| {d['family']} | {d['selected_variant']} | {d['original_BTC_return_pct']:+.3f}% | {d['selected_BTC_return_pct']:+.3f}% | {d['selected_BTC_positive_months']}/22 | {d['selected_BTC_month_end_drawdown_pct']:.3f}% | {d['frozen_ETH_return_pct']:+.3f}% | {d['selected_BTC_after_additional_25bp_monthly_pct']:+.3f}% |")
    report+=["","## Predeclared improvement mechanisms","",
             "1. Increase Stage18 daily-trend sleeve allocation from 25% to 50% to test stronger diversification from quiet-volume intraday sleeve.",
             "2. Reduce Stage20 hourly momentum auxiliary sleeve allocation from 10% to 5% to test reducing noisy signal cost and monthly dispersion.",
             "3. At month start halve exposure after a fully completed negative previous month, or after a negative two-month compounded period. Never use current-month return to decide current-month exposure.",
             "4. Preserve original unswitched baselines and independently stress every variant by adding 10bp and 25bp monthly NAV costs.","",
             "## Critical limitations",*[f"- {c}" for c in caveats],"",
             "See all_candidate_summary.csv, all_monthly_nav.csv, selected_comparisons.csv, selection_btc2025_only.json for all BTC and ETH outcomes.",
             "Do not call a positive historical return a live-ready result until integrated 1m execution/margin and native ETH audits are finished."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    (OUT/"quality_and_limits.json").write_text(json.dumps({"period":MONTHS,"sources":[str(x) for x in (STAGE18_ALL,STAGE20_SELECTED,ETH20_SELECTED,ETH17_MONTHLY,ETH19_MONTHLY)],
                   "variants_per_family":{k:len(v) for k,v in VARIANTS.items()},
                   "caveats":caveats,"modeled_cost_stress_pct_per_calendar_month":STRESS_PCT,
                   "source_trade_level_PF":"UNAVAILABLE_CANNOT_INFER_FROM_MONTHLY_NAV",
                   "execution_model":"SOURCE_MONTHLY_PORTFOLIO_REPLAY"},indent=2)+"\n")
    # Print frozen train/check and stress scenarios for reproducible log inspection.
    for family in BASIS:
        chosen=selection[family]["chosen_on_BTC2025"]
        for symbol in ("BTCUSD","ETHUSD"):
            for name in ("original",chosen):
                if name=="original" and chosen=="original":
                    options=("original",)
                else:options=(name,)
                for label in options:
                    for stress in (0.0,0.10,0.25):
                        vals=[r for r in summaries if r["family"]==family and r["market"]==symbol and r["variant"]==label and r["cost_buffer_pct_per_month"]==stress]
                        if len(vals)!=1:raise AssertionError("Duplicate summary")
                        v=vals[0]
                        print("SELECTED_AUDIT "+json.dumps({"family":family,"market":symbol,"variant":label,
                             "stress_month_pct":stress,"net_2025":v["net_2025_pct"],
                             "net_2026_JanOct":v["net_2026_JanOct_pct"],
                             "net_22_month":v["net_22_month_pct"],
                             "positive_months":v["positive_months"],"losing_months":v["losing_months"],
                             "flat_months":v["flat_months"],
                             "max_month_end_dd":v["max_month_end_drawdown_pct"]},sort_keys=True))
    print("STAGE18_STAGE20_IMPROVEMENT_COMPLETE "+json.dumps(decisions,sort_keys=True))
if __name__=="__main__":main()
