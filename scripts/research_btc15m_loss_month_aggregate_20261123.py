#!/usr/bin/env python3
"""Aggregate exact 7-shard BTCUSD monthly loss control replay.
Uses only previously realized data in strategy execution. Strict scoring is
performed AFTER the backtest to determine whether a candidate qualifies."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
OUT=Path("analysis/btc15m_loss_month_guards_parallel_20261123")
BASE="reclaim_NOFLIP_SL300_NONE_TP3R"
def main():
    shards=sorted(x for x in OUT.glob("shard_*") if x.is_dir())
    assert len(shards)==7,len(shards)
    for p in shards:
        assert (p/"summary.csv").is_file() and (p/"monthly.csv").is_file()
    summary=pd.concat([pd.read_csv(p/"summary.csv") for p in shards],ignore_index=True)
    months=pd.concat([pd.read_csv(p/"monthly.csv") for p in shards],ignore_index=True)
    trades=pd.concat([pd.read_csv(p/"trades.csv.gz") for p in shards],ignore_index=True)
    assert len(summary)==140,len(summary)
    assert summary.config.nunique()==70
    assert summary.groupby("config").size().eq(2).all()
    assert summary.flip_exits.eq(0).all()
    assert summary.groupby(["config","path_assumption"]).size().eq(1).all()
    assert months.groupby(["config","path_assumption"]).size().eq(22).all()
    original=pd.read_csv("analysis/btc15m_reclaim_sl3_tp9_monthly_20261123/monthly_ohlc.csv")
    b=months[(months.config==BASE)&(months.path_assumption=="O-H-L-C")].sort_values("month_ist")
    exp=original.sort_values("month_ist")
    assert len(b)==22
    assert np.allclose(b.monthly_return_pct,exp.monthly_return_pct,atol=1e-5)
    assert np.allclose(b.equity_usd,exp.equity_usd,atol=.001)
    assert summary[(summary.config==BASE)&(summary.path_assumption=="O-H-L-C")].iloc[0].trades==75
    assert abs(summary[(summary.config==BASE)&(summary.path_assumption=="O-H-L-C")].iloc[0].net_return_pct-97.5183)<.001
    base=b.set_index("month_ist").monthly_return_pct
    positive=base>0
    losing=base<0
    assert positive.sum()==16 and losing.sum()==6
    reports=[]
    for _,row in summary.iterrows():
        one=months[(months.config==row.config)&(months.path_assumption==row.path_assumption)]
        series=one.set_index("month_ist").monthly_return_pct.reindex(base.index)
        delta_positive=series[positive]-base[positive]
        delta_negative=series[losing]-base[losing]
        d=row.to_dict()
        d.update(
            all_original_16_profitable_months_preserved=bool((delta_positive>=-.00001).all()),
            original_profitable_months_not_worse=int((delta_positive>=-.00001).sum()),
            total_original_profitable_months_shortfall_pp=round(float((-delta_positive.clip(upper=0)).sum()),5),
            originally_negative_months_improved=int((delta_negative>0.00001).sum()),
            negative_months_count=int((series<0).sum()),
            sum_of_negative_month_returns_pct=round(float(series.clip(upper=0).sum()),4),
            worst_month_return_pct=round(float(series.min()),4),
            worst_month=str(series.idxmin()),
            mar2025_return_pct=round(float(series.loc["2025-03"]),4),
            dec2025_return_pct=round(float(series.loc["2025-12"]),4),
            apr2026_return_pct=round(float(series.loc["2026-04"]),4),
            jul2026_return_pct=round(float(series.loc["2026-07"]),4))
        reports.append(d)
    ranked=pd.DataFrame(reports)
    ranked.to_csv(OUT/"scored_summary.csv",index=False)
    summary.to_csv(OUT/"summary.csv",index=False)
    months.to_csv(OUT/"monthly_mark_to_market.csv",index=False)
    trades.to_csv(OUT/"trades.csv.gz",index=False,compression="gzip")
    first=ranked[ranked.path_assumption=="O-H-L-C"].copy()
    orig_sum=float(base.clip(upper=0).sum())
    strict=first[(first.config!=BASE)&first.all_original_16_profitable_months_preserved&
        (first.sum_of_negative_month_returns_pct>orig_sum+.0001)]
    improvement=first[first.config!=BASE].sort_values("net_return_pct",ascending=False)
    risk=first[(first.config!=BASE)].sort_values("worst_month_return_pct",ascending=False)
    cols=["config","trades","net_return_pct","profitable_months",
        "original_profitable_months_not_worse","total_original_profitable_months_shortfall_pp",
        "originally_negative_months_improved","sum_of_negative_month_returns_pct",
        "worst_month_return_pct","max_floating_drawdown_pct","monthly_guard_hits"]
    report=[
        "# BTCUSD 15M Reclaim — Losing-month reduction preserving profits",
        "",
        "70 distinct parameter sets x 2 hypothetical 1-minute OHLC paths = 140 simulations.",
        "Same original 3% initial stop / 9% take-profit, with Supertrend(10,3)+EMA20 Reclaim entry on 15m only, ST-flip exit OFF.",
        "Tested month-level equity circuit-breakers at 2-15%, late profit-lock activation at 2-7%, and selected combinations.",
        "Original 22 month results revalidated exactly against prior independently archived monthly dataset.",
        "Strict pass: every one of original 16 positive monthly % returns is >= original, AND sum of negative monthly returns improves.",
        "These thresholds were selected for study, not for trading. Backtest on already mined Jan2025-Oct2026 sample.",
        "Monthly return is month-end marked-to-market including unrealized PnL. 1x evolving $1000 notional.",
        "Costs: taker 0.05% each side + 18% GST and 0.02% adverse slippage each side. Funding, real spread and liquidation NOT included.",
        "Monthly guards use only observable current marked-to-market equity; they block entries until next calendar month and close at approximate barrier (market-open after gaps).",
        "",
        "## Key outcome",
        "Count of tested non-baseline configurations meeting strict criterion: **"+str(len(strict))+"**.",
        "Baseline positive months 16/22; baseline total net **+97.5183%**; original sum of losing-month % returns **"+str(round(orig_sum,4))+"**.",
        "",
        "## Strict qualifying configurations",
        "", strict[cols].to_markdown(index=False) if len(strict) else "None of the 69 non-baseline variants met the strict criterion.",
        "",
        "## Top total net returns (may sacrifice profitable months)",
        "",improvement[cols].head(20).to_markdown(index=False),"",
        "## Least severe worst month (may sacrifice profitable months)",
        "",risk[cols].head(20).to_markdown(index=False),"",
        "## Original monthly losses",
        "",base[losing].to_string(),"",
        "## Both 1-minute OHLC paths and complete monthly ledger",
        "Inspect scored_summary.csv, monthly_mark_to_market.csv, and trades.csv.gz.",
        "The dataset has already been repeatedly researched; any in-sample match to 16 months can overfit and must pass forward out-of-sample testing.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    (OUT/"quality.json").write_text(json.dumps(dict(
       configurations=70,results=140,original_months_exact_match=True,
       original_16_profitable_months=16,original_6_losing_months=6,
       strict_matching_non_baseline_count=int(len(strict)),
       missing_time_data=None,run_source="7 parallel GitHub Actions shards",
       unmodeled=["funding","real spreads","market impact","liquidation","latency"],
       in_sample_only=True),indent=2))
    print("LOSS_MONTH_SHARDS_ALL_VALIDATED",len(ranked),int(len(strict)),flush=True)
    print("TOP_RETURNS\n"+improvement[cols].head(15).to_string(index=False),flush=True)
    print("BEST_WORST_MONTH\n"+risk[cols].head(10).to_string(index=False),flush=True)
if __name__=="__main__": main()
