#!/usr/bin/env python3
"""EMA9/21 1m with completed hourly/four-hour trend regimes; 12 fixed variants."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_ema9_21_quality_upgrade as base
from research_ema9_21_daily_quality_1m import load,ema,rma

OUT=Path("analysis/ema9_21_htf_regime")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()

def completed(m,rule):
    bars=int(pd.Timedelta(rule)/pd.Timedelta(minutes=1))
    c=m.close.resample(rule,closed="left",label="left").last()
    n=m.close.resample(rule,closed="left",label="left").count()
    return c.where(n.eq(bars))

def features(m):
    cl=m.close
    h1=completed(m,"1h")
    h4=completed(m,"4h")
    def expand(z):
        # Index label is bar open, so shift by 1 completed bar at next bar open.
        return z.shift(1).reindex(m.index,method="ffill")
    a9,a21=ema(h1,9),ema(h1,21)
    h1long=expand((a9>a21)&(h1>a9)).fillna(False)
    h1short=expand((a9<a21)&(h1<a9)).fillna(False)
    h4a,h4b=ema(h4,20),ema(h4,50)
    h4long=expand((h4a>h4b)&(h4>h4a)).fillna(False)
    h4short=expand((h4a<h4b)&(h4<h4a)).fillna(False)
    high1=m.high.resample("1h",closed="left",label="left").max()
    low1=m.low.resample("1h",closed="left",label="left").min()
    prev=h1.shift(1)
    tr=pd.concat([high1-low1,(high1-prev).abs(),(low1-prev).abs()],axis=1).max(axis=1)
    a=rma(tr,14)
    volgate=expand(a>=a.rolling(60,min_periods=60).median()).fillna(False)
    return {
      "h1_trend":(h1long.to_numpy(bool),h1short.to_numpy(bool)),
      "h1_h4_trend":((h1long&h4long).to_numpy(bool),(h1short&h4short).to_numpy(bool)),
      "h1_vol":((h1long&volgate).to_numpy(bool),(h1short&volgate).to_numpy(bool)),
    }

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    original=load()
    # Close all trades before first minute of Nov 2026 IST; no skipped last open P&L.
    cutoff=pd.Timestamp("2026-11-01 00:00:00",tz="Asia/Kolkata").tz_convert("UTC")
    m=original.loc[original.index<cutoff].copy()
    families,atr5=base.feature_frame(m)
    reg=features(m)
    rows=[];monthrows=[];ledgers={}
    for family in ("cross","trend_break"):
        for regime,(bull,bear) in reg.items():
            long,short=families[family]
            mask=(long&bull,short&bear)
            for maxhold in (720,2160):
                base.MAX_HOLD=maxhold
                ledger=base.sim(m,mask,atr5,"eu_us",2.5,3.0,slip=5.0)
                stats,monthly=base.summarize(ledger)
                key=f"{family}__{regime}__hold{maxhold}"
                rows.append({"variant":key,"family":family,"regime":regime,
                             "maxhold_min":maxhold,**stats})
                monthly["variant"]=key
                monthrows.append(monthly)
                ledgers[key]=ledger
                print("REGIME_VARIANT "+json.dumps(rows[-1],sort_keys=True),flush=True)
    ranked=pd.DataFrame(rows).sort_values(["return_2025_pct","max_closed_dd_pct"],
                                           ascending=[False,True])
    top=ranked.iloc[0].to_dict()
    key=top["variant"]
    outmon=pd.concat(monthrows)
    ranked.to_csv(OUT/"all_variants.csv",index=False)
    outmon.to_csv(OUT/"all_months.csv",index=False)
    ledgers[key].to_csv(OUT/"selected_trades.csv.gz",index=False,compression="gzip")
    topmonths=outmon.query("variant == @key")
    topmonths.to_csv(OUT/"selected_monthly.csv",index=False)
    (OUT/"selected.json").write_text(json.dumps({"selected_using_2025":top,
        "all_positive_2025":int((ranked.return_2025_pct>0).sum()),
        "positive_both_2025_and_2026":int(((ranked.return_2025_pct>0)&(ranked.return_2026_pct>0)).sum()),
        "note":"2026 seen historical recheck; never pristine. Funding, true spread, liquidity impacts excluded.",
        "period":"Jan 2025-Oct 2026 full IST calendar months; weekday IST signals only.",
        "source":"Delta India BTCUSD 1m OHLCV"},indent=2)+"\n")
    report=["# EMA9/21 BTCUSD 1m + completed HTF regime experiment","",
      "12 pre-registered variants; 2025-only ranking, 2026 already researched; cost: 0.05% taker per side, GST 18%, 5pts slip/side, 10% notional exposure.",
      "Max one entry per IST weekday, signal and execution weekday, with 12h/36h hold and pessimistic stop-first.",
      "","## Ranked variants","",ranked.to_markdown(index=False),"",
      "## Selected using 2025 only — month by month","",topmonths.to_markdown(index=False),
      "","Funding, real order book bid/ask, partial fills not modeled. Historical backtest only."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("BEST_2025_REGIME "+json.dumps(top,sort_keys=True),flush=True)
    print("MONTHLY_BEST_REGIME\n"+topmonths.to_string(index=False),flush=True)
    print("REGIME_CHECK_DONE",flush=True)

if __name__=="__main__":run()
