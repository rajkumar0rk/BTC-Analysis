#!/usr/bin/env python3
"""Stage 18: monthly-consistency search across TWO independent strategy families.

Component A: Stage15 1H quiet-volume 1H pullback 15M structural break with
4H ranging regime, 3R target, and original weekly risk guard.
Component B: Stage17 Daily 20-bar Donchian swing breakout, 2ATR initial
risk, 3 or 4 ATR trailing, EMA50 optional.

Use the ORIGINAL preserved Stage15 closed trade ledger to compound returns
by EXIT month IST, and the Stage17 monthly marked-to-market NAV series.
Pair the strategies as two distinct, independently sized portfolios that
are rebalanced at the start of each month. Intramonth interactions are NOT
simulated; results are a blended monthly NAV thought experiment.

Search is selected using 2025 ONLY; 2026 then reported as a historically
research-exposed chronological check. The trading ideas and indicators have
been evaluated on all historic data in earlier stages. NOT pristine OOS.
"""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd

OUT=Path("analysis/institutional_discovery_stage18_monthly_dual_strategy")
MONTHS=pd.period_range("2025-01","2026-11",freq="M").astype(str)
BASE_STAGE15="analysis/institutional_discovery_stage15_july_loss_controls"
BASE_STAGE17="analysis/institutional_discovery_stage17_swing_breakout"
RISK_FRACTION=.005
HISTORICAL_MONTHS_2026=11

FILTERS={
    "quiet_1h_weekly_3R":("1h_volume_ratio_le_1p2","weekly_minus_3R"),
    "quiet_1h_no_gate":("1h_volume_ratio_le_1p2","no_loss_gate"),
    "quiet_1h_daily2_weekly3":("1h_volume_ratio_le_1p2","daily_minus_2R_weekly_minus_3R"),
    "risk_700":("risk_le_700","no_loss_gate"),
    "risk_700_weekly3":("risk_le_700","weekly_minus_3R"),
    "baseline_weekly3":("unchanged","weekly_minus_3R"),
    "baseline_no_gate":("unchanged","no_loss_gate"),
}
DAILY_SWINGS=[
    "1D_channel_20_no_trend_filter_trail_3atr",
    "1D_channel_20_no_trend_filter_trail_4atr",
    "1D_channel_20_ema50_agrees_trail_3atr",
    "1D_channel_20_ema50_agrees_trail_4atr",
    "1D_channel_55_ema50_agrees_trail_3atr",
]
SWING_WEIGHTS=(.25,.5,.75)

def stage15_returns(path):
    tr=pd.read_csv(path)
    needed={"filter","guard","entry_unix","exit_unix","net_R"}
    if needed-set(tr.columns):
        raise AssertionError("Stage15 ledger lacks "+str(needed-set(tr.columns)))
    tr=tr.sort_values(["exit_unix","entry_unix"],kind="stable").copy()
    tr["entry_month_ist"]=pd.to_datetime(tr.entry_unix,unit="s",utc=True).dt.tz_convert(
        "Asia/Kolkata").dt.strftime("%Y-%m")
    tr["exit_month_ist"]=pd.to_datetime(tr.exit_unix,unit="s",utc=True).dt.tz_convert(
        "Asia/Kolkata").dt.strftime("%Y-%m")
    # Source original Stage15 monthly summary uses ENTRY month, not exit month.
    original=pd.read_csv(BASE_STAGE15+"/month_by_month.csv")
    selected=tr.merge(
        pd.DataFrame([dict(label=key,filter=f,guard=g) for key,(f,g) in FILTERS.items()]),
        on=["filter","guard"],how="inner")
    if selected.empty:raise RuntimeError("No Stage15 filtered trades")
    original_checks={}
    for label,(flt,g) in FILTERS.items():
        chosen=selected[selected.label==label]
        recorded=original[(original["filter"]==flt)&(original.guard==g)]
        if int(recorded.trades.sum())!=len(chosen):
            raise AssertionError("Stage15 source trade count mismatch for "+label)
        expected=recorded.net_R.sum()
        actual=chosen.net_R.sum()
        if abs(expected-actual)>.05:
            raise AssertionError("Stage15 source net R mismatch for "+label+
                                 f" expected {expected} actual {actual}")
        original_checks[label]=dict(trades=len(chosen),
            original_entry_month_sum_R=round(float(expected),4),
            actual_exit_month_sum_R=round(float(actual),4))
    monthly=[]
    for label,g in selected.groupby("label"):
        for m in MONTHS:
            one=g[g.exit_month_ist==m].sort_values(["exit_unix","entry_unix"])
            if one.empty:
                ret=0.
            else:
                fraction=1.+RISK_FRACTION*one.net_R.to_numpy(float)
                if (fraction<=0).any():
                    raise AssertionError("Stage15 risk model would bankrupt account")
                ret=(np.prod(fraction)-1)*100
            monthly.append(dict(stage15=label,month_ist=m,
                trades=len(one),ret_pct=float(ret),
                has_trading=int(len(one)>0),
                net_R=float(one.net_R.sum())))
    return pd.DataFrame(monthly),original_checks

def stage17_returns():
    src=pd.read_csv(BASE_STAGE17+"/monthly_mark_to_market.csv")
    selected=src[src.model.isin(DAILY_SWINGS)].copy()
    if len(selected)!=len(DAILY_SWINGS)*len(MONTHS):
        raise AssertionError("Stage17 monthly NAV incomplete")
    checks={}
    for model,g in selected.groupby("model"):
        g=g.sort_values("month_ist")
        first=g.month_ist.tolist()
        if first!=list(MONTHS):
            raise AssertionError("Stage17 month coverage invalid")
        nav=100.*np.cumprod(1.+g.month_return_pct.to_numpy(float)/100)
        if abs(nav[-1]-float(g.month_end_equity.iloc[-1]))>.03:
            raise AssertionError("Stage17 monthly NAV does not reconcile "+model)
        checks[model]=dict(months=len(g),
            last_nav=float(g.month_end_equity.iloc[-1]))
    selected=selected.rename(columns={
        "model":"stage17","month_return_pct":"ret_pct",
        "market_exposure":"has_trading"})
    return selected[["stage17","month_ist","ret_pct","has_trading"]],checks

def pair_results(a,b):
    pairs=[]
    months=[]
    for lab in FILTERS:
        x=a[a.stage15==lab].sort_values("month_ist")
        for swing in DAILY_SWINGS:
            y=b[b.stage17==swing].sort_values("month_ist")
            if x.month_ist.tolist()!=y.month_ist.tolist():
                raise AssertionError("Month alignment mismatch")
            for wt in SWING_WEIGHTS:
                label=f"{lab} + {swing} + swing_{int(wt*100)}pct"
                blended=wt*y.ret_pct.to_numpy(float)+(1-wt)*x.ret_pct.to_numpy(float)
                valid_trades=(x.has_trading.to_numpy(int)|y.has_trading.to_numpy(int))>0
                for i,month in enumerate(MONTHS):
                    months.append(dict(name=label,stage15=lab,stage17=swing,
                        swing_weight=wt,month_ist=month,
                        range_component_pct=round(float(x.ret_pct.iloc[i]),6),
                        swing_component_pct=round(float(y.ret_pct.iloc[i]),6),
                        portfolio_pct=round(float(blended[i]),6),
                        traded_or_held=int(valid_trades[i]),
                        status="No exposure" if not valid_trades[i] else (
                            "Profit" if blended[i]>1e-8 else
                            "Loss" if blended[i]<-1e-8 else "Flat")))
                train=blended[:12]
                check=blended[12:]
                active25=valid_trades[:12].sum()
                active26=valid_trades[12:].sum()
                def cpos(v):return int((v>1e-8).sum())
                def neg(v):return int((v<-1e-8).sum())
                def cagr(v):return float((np.prod(1.+v/100)-1)*100)
                nav=100*np.r_[1.,np.cumprod(1.+blended/100)]
                maxdd=100*float(np.max(1.-nav/np.maximum.accumulate(nav)))
                pairs.append(dict(name=label,stage15=lab,stage17=swing,
                    swing_weight=wt,
                    positive_months_2025=cpos(train),
                    losing_months_2025=neg(train),
                    no_exposure_months_2025=int(12-active25),
                    active_months_2025=int(active25),
                    return_2025_pct=round(cagr(train),4),
                    positive_months_2026=cpos(check),
                    losing_months_2026=neg(check),
                    no_exposure_months_2026=int(11-active26),
                    active_months_2026=int(active26),
                    return_2026_pct=round(cagr(check),4),
                    max_month_end_drawdown_pct=round(maxdd,4),
                    months_with_positive_return=cpos(blended),
                    months_with_nonpositive_return=int((blended<=1e-8).sum()),
                    perfect_every_month=bool(cpos(blended)==len(blended))))
    return pd.DataFrame(months),pd.DataFrame(pairs)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--stage15-ledger",type=Path,required=True)
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    a,audit15=stage15_returns(args.stage15_ledger)
    b,audit17=stage17_returns()
    monthly,pairs=pair_results(a,b)
    # Selection data: 2025 ONLY, no information from 2026 in ranking.
    train=pairs[(pairs.active_months_2025>=9)&
      (pairs.return_2025_pct>0)].copy()
    train=train.sort_values(
      ["positive_months_2025","losing_months_2025","return_2025_pct",
       "max_month_end_drawdown_pct"],
      ascending=[False,True,False,True],kind="stable")
    top=train.head(12)
    # All 2026 columns exposed AFTER selecting from 2025 ranks.
    train_rankings=top[["name","stage15","stage17","swing_weight",
        "positive_months_2025","losing_months_2025","no_exposure_months_2025",
        "return_2025_pct","positive_months_2026","losing_months_2026",
        "no_exposure_months_2026","return_2026_pct","max_month_end_drawdown_pct"]]
    monthly.to_csv(OUT/"monthly_blended_returns.csv",index=False)
    pairs.to_csv(OUT/"all_combinations.csv",index=False)
    train_rankings.to_csv(OUT/"ranked_by_2025_then_recheck_2026.csv",index=False)
    chosen=train.iloc[0].to_dict()
    cmp=monthly[monthly.name==chosen["name"]].copy()
    cmp.to_csv(OUT/"selected_monthly_results.csv",index=False)
    # Explicitly highlight that research already saw 2026 and this is not
    # a truly independent study; 2025-only rank prevents further hindsight.
    metadata=dict(analysis="Stage18 monthly diversification between quiet-volatility range pullback and daily breakout",
        stage15_source_run=44120459865,stage17_source_run=44128535269,
        reference_baselines=["Stage14 original","Stage14 monthly +3R profit lock"],
        monthly_span=list(MONTHS),candidate_combinations=len(pairs),
        selection_only_on="2025 monthly positive count, then losing count and 2025 return",
        selected=chosen,
        retrospective_any_all_months_winners=int(pairs.perfect_every_month.sum()),
        stage15_original_checks=audit15,stage17_original_checks=audit17,
        cost_model="both component backtests already include standard taker fees, GST, slippage",
        position_model="two separate independently traded component portfolios; blend monthly NAV returns with monthly rebalancing",
        risk_fraction_assumed_per_strategy=RISK_FRACTION,
        caveats=[
            "2026 has been researched repeatedly before, so not a pristine unseen holdout",
            "Independent portfolios can hold positions simultaneously; needs capital and margin for both",
            "Stage15 swing-independent trade ledger is compounded on EXIT IST month, Stage17 marks active exposure at IST month end",
            "Blended NAV assumes monthly rebalancing and exact fractional risk sizing, without cross margin constraints or transaction costs of rebalancing",
            "The Stage15 input uses historical Stage14-derived condition and weekly loss gate; selection is exploratory",
            "Portfolio trading fees/GST/slippage are taken from underlying simulations, not separately charged",
            "Historical 2026-10-31 missing, November 2026 partial",
            "Historical data reused; rank selection among 105 candidates is susceptible to multiple comparison bias",
            "Never interpret a profitable historical month as guaranteed future monthly profit",
            "No real order-book slippage, funding payments, liquidation or margin modeled"])
    (OUT/"quality.json").write_text(json.dumps(metadata,indent=2)+"\n")
    report=[
        "# Stage 18 — Find a monthly-profitable dual-pattern portfolio",
        "",
        "## Preserved strategies",
        "Stage14 unchanged and Stage14 + monthly +3R profit lock remain untouched.",
        "",
        "## New distinct pattern",
        "Run two *different* strategies in capital-separated sleeves:",
        "(A) 4H range / 1H quiet participation / 15M pullback breakout,",
        "(B) Daily Donchian directional swing breakout. Combine monthly returns",
        "with preallocated capital and monthly rebalance.",
        "",
        "## Selection",
        "105 fixed pairings: 7 range/volume controls x 5 daily swing models x 3",
        "weights. Rank ONLY Jan-Dec 2025 profitability (and losing months),",
        "then inspect Jan-Nov 2026 as previously researched chronology.",
        "",
        "**2026 is not a pristine OOS period; earlier work already exposed it.**",
        "",
        "## Best 2025-ranked mix and chronological 2026 outcome",
        pd.DataFrame([chosen]).to_markdown(index=False),"",
        "## Selected portfolio every month",
        cmp[["month_ist","range_component_pct","swing_component_pct",
             "portfolio_pct","traded_or_held","status"]].to_markdown(index=False),"",
        "## Top 2025-selected candidate pairings",
        train_rankings.to_markdown(index=False),"",
        "## Research caveats",
        *["- "+x for x in metadata["caveats"]],"",
        "Reproduction: python scripts/research_monthly_portfolio_stage18.py",
        "--stage15-ledger <original Stage15 artifact CSV.gz>.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE18_SUCCESS "+json.dumps({
        "variants":len(pairs),"qualified_on_2025":len(train),
        "perfect_every_month_retro":metadata["retrospective_any_all_months_winners"],
        "selected_name":chosen["name"],
        "selected_profitable_2025":chosen["positive_months_2025"],
        "selected_profitable_2026":chosen["positive_months_2026"],
        "selected_return_2025":chosen["return_2025_pct"],
        "selected_return_2026":chosen["return_2026_pct"]}))
    print("SELECTED_MONTHLY\n"+cmp.to_string(index=False))
    print("TOP10\n"+top.to_string(index=False))
if __name__=="__main__":
    main()
