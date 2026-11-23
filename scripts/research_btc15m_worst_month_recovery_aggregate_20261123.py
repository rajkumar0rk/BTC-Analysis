#!/usr/bin/env python3
"""Aggregate all 58 causal loss-pause variants; strict preservation of profitable months."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
OUT=Path("analysis/btc15m_worst_month_recovery_aware_20261123")
BASE="reclaim_NOFLIP_SL300_NONE_TP3R"
LATE="reclaim_NOFLIP_LATE825_SL300_TP3R"
def main():
    folders=[OUT/f"shard_{i}" for i in range(8)]
    for p in folders:
        assert (p/"summary.csv").is_file(),p
        assert (p/"monthly.csv").is_file(),p
    summary=pd.concat([pd.read_csv(p/"summary.csv") for p in folders],ignore_index=True)
    monthly=pd.concat([pd.read_csv(p/"monthly.csv") for p in folders],ignore_index=True)
    trades=pd.concat([pd.read_csv(p/"trades.csv.gz") for p in folders],ignore_index=True)
    assert len(summary)==140 and summary.config.nunique()==70
    assert summary.groupby("config").size().eq(2).all()
    assert summary.flip_exits.eq(0).all()
    assert monthly.groupby(["config","path_assumption"]).size().eq(22).all()
    orig=pd.read_csv("analysis/btc15m_reclaim_sl3_tp9_monthly_20261123/monthly_ohlc.csv")
    base=monthly[(monthly.config==BASE)&(monthly.path_assumption=="O-H-L-C")].sort_values("month_ist")
    assert np.allclose(base.monthly_return_pct.to_numpy(),orig.sort_values("month_ist").monthly_return_pct.to_numpy(),atol=1e-5)
    assert np.allclose(base.equity_usd.to_numpy(),orig.sort_values("month_ist").equity_usd.to_numpy(),atol=.001)
    assert len(base)==22
    baseline=base.set_index("month_ist").monthly_return_pct
    pos=baseline>0
    neg=baseline<0
    assert pos.sum()==16 and neg.sum()==6
    details=[]
    for _,row in summary.iterrows():
        sub=monthly[(monthly.config==row.config)&(monthly.path_assumption==row.path_assumption)]
        series=sub.set_index("month_ist").monthly_return_pct.reindex(baseline.index)
        assert series.notna().all()
        winning_delta=series[pos]-baseline[pos]
        losers_delta=series[neg]-baseline[neg]
        details.append(dict(**row.to_dict(),
          original_win_months_preserved=int((winning_delta>=-.00001).sum()),
          preserves_all_original_winning_months=bool((winning_delta>=-.00001).all()),
          positive_month_shortfall_pp=round(float((-winning_delta.clip(upper=0)).sum()),6),
          original_losing_months_improved=int((losers_delta>.00001).sum()),
          net_negative_month_sum_pp=round(float(series.clip(upper=0).sum()),4),
          worst_month_return_pct=round(float(series.min()),4),
          worst_month_name=str(series.idxmin()),
          mar2025_pct=round(float(series.loc["2025-03"]),4),
          dec2025_pct=round(float(series.loc["2025-12"]),4),
          apr2026_pct=round(float(series.loc["2026-04"]),4),
          total_net_not_reduced=bool(row.net_return_pct>=97.5183-.0001),
          worst_month_improved=bool(series.min()>baseline.min()+.0001)))
    ranked=pd.DataFrame(details)
    ranked.to_csv(OUT/"scored_summary.csv",index=False)
    summary.to_csv(OUT/"summary.csv",index=False)
    monthly.to_csv(OUT/"monthly_mark_to_market.csv",index=False)
    trades.to_csv(OUT/"trades.csv.gz",index=False,compression="gzip")
    p=ranked[ranked.path_assumption=="O-H-L-C"].copy()
    p["strict"]=p.preserves_all_original_winning_months&p.total_net_not_reduced&p.worst_month_improved
    qual=p[(p.config!=BASE)&(p.strict)]
    worse=p[(p.config!=BASE)].sort_values("worst_month_return_pct",ascending=False)
    net=p[(p.config!=BASE)].sort_values("net_return_pct",ascending=False)
    cols=["config","trades","net_return_pct","profitable_months",
          "original_win_months_preserved","original_losing_months_improved",
          "mar2025_pct","dec2025_pct","worst_month_return_pct",
          "net_negative_month_sum_pp","max_floating_drawdown_pct","pause_entries_skipped"]
    report=[
      "# BTCUSD 15M Reclaim — Repair the worst loss month without reducing profits",
      "",
      "Full 70-configuration, 140-path simulation, 22-month Jan2025–Oct2026, 1-minute exit execution.",
      "The original 15M Supertrend(10,3)+EMA20 Reclaim entry, 3% price SL and 9% fixed TP, no Supertrend flip exit.",
      "Causal recovery-aware risk limits: pause only after 2 or 3 net losing exits AND 0–8% observed realized equity drawdown from prior month-end, but only when the PREVIOUS completed month was profitable by 0–5%. A prior losing month disables pauses to allow recovery.",
      "Both no-protection original and +8.25% trigger/0% lock models used as control starting points.",
      "Every pause rule only blocks FUTURE signals; it never rewrites past trades or closes an already open trade.",
      "One trade per ST regime, no simultaneous positions. Original monthly equity returns exactly validated.",
      "Strict success = (a) every original 16 profitable month returns no worse, (b) total net return >= original +97.5183%, and (c) worst monthly return less negative than −15.3196%.",
      "Fee+18% GST on 0.05% taker each side and adverse 0.02% slippage each side modeled.",
      "1x notional, starting $1000 equity. Funding, real execution, gap slippage and liquidation NOT fully modeled.",
      "These 22 months have been heavily explored and are IN-SAMPLE, not prospective prediction.",
      "",
      "## Strict pass count",
      "",
      str(len(qual))+" of 69 non-original variants met all three conditions.",
      "",
      "## Strict qualifying models",
      "",
      qual[cols].to_markdown(index=False) if len(qual) else "None met the full requirements.",
      "",
      "## Best worst-month improvement (even if profitable months sacrificed)",
      "",
      worse[cols].head(20).to_markdown(index=False),
      "",
      "## Best net profit (even if worst month unchanged)",
      "",
      net[cols].head(20).to_markdown(index=False),
      "",
      "## Original six losing months",
      "",baseline[neg].to_string(),"",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    (OUT/"quality.json").write_text(json.dumps(dict(models=int(summary.config.nunique()),
        simulations=len(summary),months=22,strict_count=int(len(qual)),
        baseline_monthly_parity=True,original_profitable_months=16,
        original_net_return_pct=97.5183,unmodelled=["funding","real fills","orderbook impact","liquidation"],
        in_sample_optimization=True),indent=2))
    print("ALL_SHARDS_DONE",len(summary),int(len(qual)),flush=True)
    print("QUALIFYING\n"+(qual[cols].to_string(index=False) if len(qual) else "NONE"),flush=True)
    print("TOP_WORST_MONTH\n"+worse[cols].head(15).to_string(index=False),flush=True)
if __name__=="__main__":main()
