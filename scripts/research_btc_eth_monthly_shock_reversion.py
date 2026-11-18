#!/usr/bin/env python3
"""Independent hourly/4h post-shock snapback test on native BTC and ETH 1m.
The signal is the completed candle's ATR-normalized shock and a closing
rejection of its own range; next open entry. No future bars in the signal.
2025-only selection; 2026 shown without changing parameters.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from eth_native_crossfamily_v2 import load,aggregate,MONTHS,RISK,CAP,FEE,INITIAL_EQUITY
from research_btc_eth_monthly_volatility_balance import (
    replay_instrument,month_table,flatten,ledger_detail,events_for
)
OUT=Path("analysis/btc_eth_monthly_shock_reversion_20261118")
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    all_summary=[];all_month=[];all_ledgers=[]
    for symbol in ("BTCUSD","ETHUSD"):
        f=load(symbol)
        ist=f.index.tz_convert("Asia/Kolkata")
        codes=np.asarray(ist.year*100+ist.month,dtype=np.int32)
        op=f.open.to_numpy(float);hi=f.high.to_numpy(float)
        lo=f.low.to_numpy(float);cl=f.close.to_numpy(float)
        for frame in ("1h","4h"):
            x=aggregate(f,frame)
            prev=x.close.shift(1)
            # A completed large bar closes back near the opening side of its
            # range. Long after bearish shock with recovery, vice versa.
            span=(x.high-x.low).replace(0,np.nan)
            loc=(x.close-x.low)/span
            for shock in (1.2,1.8,2.4):
                for reclaim in (.25,.40):
                    long=(x.valid&(x.close<x.open)&
                        ((x.open-x.low)/x.atr>=shock)&
                        (loc>=reclaim)&(x.close<prev))
                    short=(x.valid&(x.close>x.open)&
                        ((x.high-x.open)/x.atr>=shock)&
                        (loc<=1-reclaim)&(x.close>prev))
                    _,k,side,j=events_for((x,long,short),f)
                    if not len(k):continue
                    stop=x.atr.to_numpy(float)[j]
                    for sm in (1.5,2.5):
                        for rr in (1.5,2.5):
                            model=f"{frame}:shock{shock:g}:reclaim{reclaim:g}:stop{sm:g}:rr{rr:g}"
                            led=replay_instrument(op,hi,lo,cl,codes,k,side,stop,rr,
                                1440 if frame=="1h" else 4320,sm,RISK,CAP,
                                5. if symbol=="BTCUSD" else 0.,
                                0. if symbol=="BTCUSD" else .0002,FEE)
                            months=month_table(led,codes,symbol,model)
                            summary=flatten(symbol,model,led,months)
                            all_summary.append(summary);all_month.extend(months)
                            if len(led):
                                all_ledgers.append(ledger_detail(symbol,model,led,f))
        print("COMPLETED",symbol,flush=True)
    s=pd.DataFrame(all_summary);m=pd.DataFrame(all_month)
    assert len(s[s.market=="BTCUSD"])==len(s[s.market=="ETHUSD"])
    s.to_csv(OUT/"all_summary.csv",index=False)
    m.to_csv(OUT/"all_22_months.csv",index=False)
    pd.concat(all_ledgers,ignore_index=True).to_csv(OUT/"original_all_trade_ledgers.csv.gz",index=False,compression="gzip")
    # Rank strictly by 2025-only monthly performance. No 2026 selection.
    selected=[]
    for symbol in ("BTCUSD","ETHUSD"):
        subset=s[(s.market==symbol)&(s.trades_2025>=12)].copy()
        subset["rank_score"]=subset.strong_months_2025*3+subset.positive_months_2025+subset.net_return_2025_pct.clip(-100,100)/10
        selected.extend(subset.sort_values("rank_score",ascending=False).head(3).model.tolist())
    selected=set(selected)
    s[s.model.isin(selected)].to_csv(OUT/"selected_pair_summary.csv",index=False)
    m[m.model.isin(selected)].to_csv(OUT/"selected_pair_months.csv",index=False)
    quality=dict(new_family="hourly and 4h ATR-normalized candle rejection after volatility shock",
        source="native BTCUSD/ETHUSD 1m manifest SHA verified by load()",months=MONTHS,
        model_count_per_market=int(len(s)//2),
        2025_selection="minimum 12 trades, 2025-only high-PF-month count, positive-month count and 2025 return",
        2026="2026 Jan-Oct YTD only; previously researched, not pristine OOS",
        fees="0.05% taker per side plus 18% GST",slippage="BTC 5 points per side; ETH 0.02% per side",
        risk="0.5% equity at stop, 3x notional cap",
        missing="funding, actual spreads, impact, margin/liquidation, lot sizes",
        jan2025="first 5.5h IST missing due to source UTC start",
        note="historical discovery, not live validation")
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    eligible=s[(s.trades>=50)&(s.net_return_pct>0)&(s.positive_months>=14)]
    strong=eligible[eligible.strong_months_pf_ge_1p5_positive_min3trades>=12]
    highyear=s[s.net_return_2025_pct>500]
    (OUT/"DECISION.md").write_text("# Independent shock-reversion paired audit\n\n"+
        f"Models per market: {len(s)//2}. Qualifying consistent monthly models: {len(strong)}. Full-year 2025 net >500% models: {len(highyear)}.\n\n"+
        "## 2025-selected BTC/ETH side-by-side\n\n"+
        s[s.model.isin(selected)].to_markdown(index=False)+
        "\n\n## All 22 monthly records of selected pairs\n\n"+
        m[m.model.isin(selected)].to_markdown(index=False)+
        "\n\n## Costs and limitations\n\n"+json.dumps(quality,indent=2)+"\n")
    print("SHOCK_REVERSION_DONE",json.dumps(dict(models_per_market=len(s)//2,
        positive_BTC=int(((s.market=="BTCUSD")&(s.net_return_pct>0)).sum()),
        positive_ETH=int(((s.market=="ETHUSD")&(s.net_return_pct>0)).sum()),
        strong_consistency=int(len(strong)),yearly_gt500=int(len(highyear)),
        selected=s[s.model.isin(selected)][["market","model","net_return_2025_pct",
        "net_return_2026_pct","profit_factor","positive_months",
        "strong_months_pf_ge_1p5_positive_min3trades","trades"]].to_dict("records"))),flush=True)
if __name__=="__main__":main()
