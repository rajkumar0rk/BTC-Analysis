#!/usr/bin/env python3
"""Independent paired BTC/ETH two-bar failed-breakout reversal, 2025-only selection.
Hour A closes outside the previous 12-hour range; hour B closes back inside.
Both bars fully closed before the next 1-minute OPEN. One position at a time.
No changes to earlier research, automations, or live systems.
"""
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
from eth_native_crossfamily_v2 import load,aggregate,FEE,RISK,CAP,MONTHS
from research_btc_eth_profit_factor_pairs import (
    replay_instrument,month_table,flatten,ledger_detail,
    BTC_SLIPPAGE_POINTS,ETH_SLIPPAGE_FRACTION)
OUT=Path("analysis/btc_eth_failed_breakout_pair_20261118")
def events(asset):
    b=aggregate(asset,"1h")
    top=b.high.shift(2).rolling(12,min_periods=12).max()
    bottom=b.low.shift(2).rolling(12,min_periods=12).min()
    # Breakout A and rejection B; both already completed at B close.
    long=(b.close.shift(1)<bottom)&(b.close>bottom)&(b.close<top)&(b.close>b.open)
    short=(b.close.shift(1)>top)&(b.close<top)&(b.close>bottom)&(b.close<b.open)
    # First break A must have crossed prior reference, not merely remained outside.
    long &= b.close.shift(2)>=bottom.shift(1)
    short &= b.close.shift(2)<=top.shift(1)
    valid=b.valid&b.atr.gt(0)
    event_ix=np.r_[np.flatnonzero((long&valid).to_numpy(bool)),
                   np.flatnonzero((short&valid).to_numpy(bool))]
    side=np.r_[np.ones(int((long&valid).sum()),dtype=np.int32),
               -np.ones(int((short&valid).sum()),dtype=np.int32)]
    k=asset.index.get_indexer(b.index[event_ix])
    keep=(k>=0)&(k<len(asset))
    k=k[keep];side=side[keep];event_ix=event_ix[keep]
    order=np.lexsort((-side,k))
    k=k[order];side=side[order];event_ix=event_ix[order]
    if len(k):
        u=np.r_[True,np.diff(k)!=0]
        k=k[u];side=side[u];event_ix=event_ix[u]
    return k,side,b.atr.to_numpy(float)[event_ix]
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[];monthly=[];ledgers=[]
    for symbol in ("BTCUSD","ETHUSD"):
        asset=load(symbol)
        k,side,atr=events(asset)
        ist=asset.index.tz_convert("Asia/Kolkata")
        mc=np.asarray(ist.year*100+ist.month,dtype=np.int32)
        for mult,rr,hold in [(1.5,2.,360),(2.5,2.,360),(1.5,3.,360),
                             (2.5,3.,360),(1.5,2.,720),(2.5,2.,720),
                             (1.5,3.,720),(2.5,3.,720)]:
            model=f"two_hour_failed_breakout__SL{mult:g}_RR{rr:g}_H{hold}"
            ledger=replay_instrument(asset.open.to_numpy(float),
                asset.high.to_numpy(float),asset.low.to_numpy(float),
                asset.close.to_numpy(float),mc,k,side,atr,rr,hold,mult,
                RISK,CAP,BTC_SLIPPAGE_POINTS if symbol=="BTCUSD" else 0.,
                ETH_SLIPPAGE_FRACTION if symbol=="ETHUSD" else 0.,FEE)
            mm=month_table(ledger,mc,symbol,model)
            summary=flatten(symbol,model,ledger,mm)
            rows.append(summary);monthly.extend(mm)
            ledgers.append(ledger_detail(symbol,model,ledger,asset))
        print("MARKET_FINISHED",symbol,"signals",len(k),flush=True)
    s=pd.DataFrame(rows);m=pd.DataFrame(monthly)
    # No hindsight parameter selection: 2025-only rank across both assets
    # on mean 2025 net return and 2025 positive months, penalize drawdown.
    piv=s.pivot(index="model",columns="market")
    scored=[]
    for model in sorted(s.model.unique()):
        q=s[s.model==model].set_index("market")
        if set(q.index)!={"BTCUSD","ETHUSD"}:continue
        scored.append(dict(model=model,
            train_2025_positive_months=int(q.positive_months_2025.sum()),
            train_2025_net_return_sum_pct=float(q.net_return_2025_pct.sum()),
            train_2025_pf_min=float(min(float(v) if v!="infinite" and v is not None else 0.
                                        for v in q.profit_factor_2025))))
    rank=pd.DataFrame(scored).sort_values(
        ["train_2025_positive_months","train_2025_net_return_sum_pct","train_2025_pf_min"],
        ascending=False)
    selected=rank.iloc[0].model
    s.to_csv(OUT/"all_pair_models.csv",index=False)
    m.to_csv(OUT/"all_monthly_net_pf.csv",index=False)
    pd.concat(ledgers,ignore_index=True).to_csv(OUT/"original_all_trade_ledgers.csv.gz",index=False,compression="gzip")
    rank.to_csv(OUT/"2025_only_selection.csv",index=False)
    s[s.model==selected].to_csv(OUT/"selected_both_markets.csv",index=False)
    m[m.model==selected].to_csv(OUT/"selected_22_months.csv",index=False)
    meta=dict(selected_model=selected,
        criteria="2025-only combined market ranking: number of positive months, then combined net account return, then minimum PF",
        models_per_market=8,months=22,markets=["BTCUSD","ETHUSD"],
        signals="Two completed 1h bars: breakout of previous 12h range, then close back inside; reverse at next 1m open",
        entry_timing="1h bars right-labelled; entry at next 1m OPEN after B completed",
        stop_first_gap_aware=True,risk_fraction=RISK,max_notional_leverage=CAP,
        fee_per_side_with_GST=FEE,btc_slippage_points_per_side=BTC_SLIPPAGE_POINTS,
        eth_slippage_fraction_per_side=ETH_SLIPPAGE_FRACTION,
        data="Native manifest-hash verified original 1m BTCUSD and ETHUSD",
        incomplete="Jan 2025 IST first 5.5h absent because data begins Jan1 UTC; Nov2026 excluded",
        caveats=["2026 previously examined; not independent OOS",
                 "No actual spread, funding, market impact, margin, liquidation or discrete lot sizes",
                 "Trade-close drawdown underestimates intratrade drawdown",
                 "Historical backtests are not forward profitability proof"])
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
    report=["# BTCUSD + ETHUSD: two-hour failed breakout reversal",
            "", "Independent, causal paired-market strategy study.",
            "Selection uses 2025 only; 2026 is previously exposed and not blind out of sample.",
            "", "## 2025-only selection",rank.to_markdown(index=False),
            "", "## Selected model, both markets",s[s.model==selected].to_markdown(index=False),
            "", "## 22 monthly net returns and profit factors",
            m[m.model==selected].to_markdown(index=False),
            "", "## Quality",json.dumps(meta,indent=2)]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("PAIR_RESEARCH_DONE",json.dumps(dict(selected_model=selected,
        best=s[s.model==selected][["market","profit_factor","net_return_pct",
        "positive_months","strong_months_pf_ge_1p5_positive_min3trades",
        "max_closed_trade_drawdown_pct","trades"]].to_dict("records"))),flush=True)
if __name__=="__main__":main()
