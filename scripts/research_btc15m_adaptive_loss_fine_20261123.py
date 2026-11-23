#!/usr/bin/env python3
"""Fine sweep on exact validated 22-month BTC 15m Reclaim + 5-loss pause.
No signal/fee/exit changes. Max 1x notional. Pre-exposed historical data.
"""
import os,sys
from pathlib import Path
import pandas as pd
import research_btc15m_adaptive_equity_risk_20261123 as risk
base=risk.base
OUT=Path("analysis/btc15m_adaptive_loss_fine_20261123")
SCALES=[.10,.15,.20,.25,.30,.35,.40,.45,.50,.55,.60,.65,.70,.75,.80,.85,.90,.95]
MODELS=[]
for count in (2,3,4):
    for scale in SCALES:
        key=f"L{count}_{int(round(scale*100)):02d}"
        MODELS.append((key,("loss",count,scale,1.0)))
        risk.MODEL_DICT[key]=("loss",count,scale,1.0)

def run(index,nshards):
    assert 0<=index<nshards
    d,quality=base.read_source("BTCUSD")
    ema,stline,trend,valid=base.st_and_ema(d,base.TF)
    ind=base.make_indicators(d)
    signals=base.make_signals(d,ema,trend,valid,"reclaim",4)[0]
    sim=risk.make_size_sim()
    for path in base.PATHS:
        row,mo,ledger=sim(d,ema,stline,trend,ind,risk.REFERENCE,risk.BASECFG,signals,path)
        risk.verify_baseline(row)
    sums=[];months=[]
    for k,(key,settings) in enumerate(MODELS):
        if k%nshards!=index: continue
        name=f"reclaim_NOFLIP_LATE825_MLOSS5__SZ_{key}_SL300_TP3R"
        for path in base.PATHS:
            row,mon,ledger=sim(d,ema,stline,trend,ind,name,risk.BASECFG,signals,path)
            row["size_mode"]=key;row["risk_after_n_losses"]=settings[1];row["size_after_n_losses"]=settings[2]
            sums.append(row)
            mon["size_mode"]=key
            months.append(mon)
            print(key,path,"profit",row["net_return_pct"],"dd",row["max_floating_drawdown_pct"],"profitable_months",row["profitable_months"],flush=True)
    out=OUT/f"shard_{index}"
    out.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(sums).to_csv(out/"summary.csv",index=False)
    pd.concat(months,ignore_index=True).to_csv(out/"monthly.csv",index=False)
    print("SHARD_COMPLETE",index,len(sums),flush=True)

def aggregate(nshards):
    OUT.mkdir(parents=True,exist_ok=True)
    s=pd.concat([pd.read_csv(OUT/f"shard_{j}"/"summary.csv") for j in range(nshards)],ignore_index=True)
    m=pd.concat([pd.read_csv(OUT/f"shard_{j}"/"monthly.csv") for j in range(nshards)],ignore_index=True)
    s.to_csv(OUT/"summary.csv",index=False)
    m.to_csv(OUT/"monthly.csv",index=False)
    rank=s.groupby("size_mode").agg(
        count=("risk_after_n_losses","first"),
        low_size=("size_after_n_losses","first"),
        min_return_pct=("net_return_pct","min"),
        max_floating_dd_pct=("max_floating_drawdown_pct","max"),
        positive_months_min=("profitable_months","min"),
        trades=("trades","min")).reset_index()
    rank["beats_original"]=(rank.min_return_pct>=151.787-.01)&(rank.positive_months_min>=18)&(rank.max_floating_dd_pct<19.948)
    rank["beats_first_improvement"]=(rank.min_return_pct>=172.101-.01)&(rank.positive_months_min>=18)&(rank.max_floating_dd_pct<16.662)
    rank["target_12"]=(rank.min_return_pct>=151.787-.01)&(rank.positive_months_min>=18)&(rank.max_floating_dd_pct<12)
    rank["target_10"]=(rank.min_return_pct>=151.787-.01)&(rank.positive_months_min>=18)&(rank.max_floating_dd_pct<10)
    rank.sort_values(["max_floating_dd_pct","min_return_pct"],ascending=[True,False]).to_csv(OUT/"ranked.csv",index=False)
    best=rank[rank.beats_original].sort_values(["max_floating_dd_pct","min_return_pct"],ascending=[True,False])
    bigger=rank[rank.beats_first_improvement].sort_values(["max_floating_dd_pct","min_return_pct"],ascending=[True,False])
    txt=[
      "# BTCUSD 15M Reclaim — fine grid on after-loss position size",
      "",
      "54 position-sizing variants x 2 ordered 1-minute OHLC paths, original execution code re-run and baseline checked against +151.787% / 19.948% / 18 months / 72 trades.",
      "Entry, fees+GST, 0.02% per-side adverse slippage, 3% SL, 9% TP, +8.25% break-even protection, five-loss monthly pause unchanged.",
      "Position size AFTER N monthly losing exits is set to 10%–95% of account equity; before then remains 100%. All variants <= 1x notional.",
      "**The full 22 months have already been used repeatedly for parameter selection. This is in-sample sensitivity, not evidence of future profitability. Funding and actual execution effects excluded.**",
      "",
      f"Compared to old baseline 151.787%/19.948%, {len(best)} of {len(rank)} meet higher/equal profit, >=18 positive months, lower DD.",
      f"Compared to initial improvement 172.101%/16.662%, {len(bigger)} are additionally better.",
      f"With DD <12% and >=151.787% profit & >=18 positive months: {int(rank.target_12.sum())}; DD <10%: {int(rank.target_10.sum())}.",
      "",
      "## Best variants preserving original profit and winning-month count",
      best.head(30).to_markdown(index=False) if len(best) else "None.",
      "",
      "## Strict improvements over +172.101%/16.662%",
      bigger.head(30).to_markdown(index=False) if len(bigger) else "None.",
      "",
      "## All variants with smallest drawdown",
      rank.sort_values(["max_floating_dd_pct","min_return_pct"],ascending=[True,False]).head(20).to_markdown(index=False),
      "",
      "## Study quality",
      "Both O-H-L-C and O-L-H-C price paths must satisfy the metrics. Actual gaps, market depth, slippage and funding may alter results."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(txt)+"\n")
    print("\n".join(txt[:11]),flush=True)
if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="aggregate": aggregate(int(os.environ.get("SHARD_COUNT", "8")))
    else: run(int(os.environ.get("SHARD_INDEX","0")),int(os.environ.get("SHARD_COUNT","8")))
