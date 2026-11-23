#!/usr/bin/env python3
"""Deleveraging sweep applied to the newly identified causal ATR(10) >=0.2% entry filter.

Exact original 15m ST/EMA20 reclaim and 1-minute engine; fees/GST/slip included.
Keeps 5-loss monthly pause, three-tier post-loss sizing, TP 9%, SL 3%,
+8.25% profit protection with 0% first lock. Uniformly reduces *all* trade
sizes to harvest ATR filter return buffer. No configuration >1x notional.
Jan2025-Oct2026 is research-exposed / historical in-sample.
"""
import os,sys
from pathlib import Path
import pandas as pd
import research_btc15m_regime_entry_dd_20261123 as entry
risk=entry.risk
base=entry.base
OUT=Path("analysis/btc15m_atr_deleveraged_dd_20261123")
TIERS=list(entry.TIER.keys())
BASE_TIER=entry.tiered_size
SCALES=[.55,.60,.65,.70,.725,.75,.775,.80,.825,.85,.875,.90,.925,.95,.975,1.00]
FILTER="ATRMIN_0p2"

def scaled_tier(name,losses):
    p=name.split("__U_",1)[1].split("__SZ_",1)[0]
    factor=int(p)/1000.0
    assert 0<factor<=1
    return factor*BASE_TIER(name,losses)

def run(index,n):
    entry.tiered_size=scaled_tier
    sim=entry.modified_simulator()
    df,quality=base.read_source("BTCUSD")
    ema,stline,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df)
    entry.enrich(df,ind,ema)
    signals=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    cfg=(4,FILTER,"PCT",3,3.0,"LATE:8.25:0:2:0.5")
    for path in base.PATHS:
        name="reclaim_NOFLIP_LATE825_MLOSS5__U_1000__SZ_T65_30_10_SL300_TP3R"
        r,mo,ledger=sim(df,ema,stline,trend,ind,name,cfg,signals,path)
        assert abs(r["net_return_pct"]-229.037)<.02 and abs(r["max_floating_drawdown_pct"]-14.740)<.02 and int(r["profitable_months"])==18 and int(r["trades"])==71,r
    rows=[];months=[]
    combos=[(tier,scale) for tier in TIERS for scale in SCALES]
    for ix,(tier,scale) in enumerate(combos):
        if ix%n!=index: continue
        size=int(round(scale*1000))
        name=f"reclaim_NOFLIP_LATE825_MLOSS5__U_{size}__SZ_{tier}_SL300_TP3R"
        for path in base.PATHS:
            r,mo,ledger=sim(df,ema,stline,trend,ind,name,cfg,signals,path)
            r["tier"]=tier;r["uniform_scale"]=scale
            mo["tier"]=tier;mo["uniform_scale"]=scale
            rows.append(r);months.append(mo)
            print(f"RESULT {tier} {scale:.3f} {path} ret={r['net_return_pct']} dd={r['max_floating_drawdown_pct']} months={r['profitable_months']}",flush=True)
    p=OUT/f"shard_{index}"
    p.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(p/"summary.csv",index=False)
    pd.concat(months,ignore_index=True).to_csv(p/"monthly.csv",index=False)
    print("SHARD_COMPLETE",index,len(rows),flush=True)

def aggregate(n):
    s=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"summary.csv") for i in range(n)],ignore_index=True)
    m=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"monthly.csv") for i in range(n)],ignore_index=True)
    s.to_csv(OUT/"summary.csv",index=False)
    m.to_csv(OUT/"monthly.csv",index=False)
    groups=s.groupby(["tier","uniform_scale"]).agg(
        worst_dd=("max_floating_drawdown_pct","max"),
        worst_path_profit=("net_return_pct","min"),
        winning_months=("profitable_months","min"),
        trades=("trades","min"),
        return_2025=("return_2025_pct","min"),
        return_2026=("return_2026_pct","min"),
    ).reset_index()
    groups["strict_better"]=(groups.worst_dd<14.740-.001)&(groups.worst_path_profit>=162.964-.01)&(groups.winning_months>=18)
    groups["dd12_net162"]=(groups.worst_dd<12)&(groups.worst_path_profit>=162.964-.01)&(groups.winning_months>=18)
    groups["dd12_net151"]=(groups.worst_dd<12)&(groups.worst_path_profit>=151.787-.01)&(groups.winning_months>=18)
    groups["dd10_net151"]=(groups.worst_dd<10)&(groups.worst_path_profit>=151.787-.01)&(groups.winning_months>=18)
    groups.sort_values(["worst_dd","worst_path_profit"],ascending=[True,False]).to_csv(OUT/"ranked.csv",index=False)
    strict=groups[groups.strict_better].sort_values(["worst_dd","worst_path_profit"],ascending=[True,False])
    t12=groups[groups.dd12_net162].sort_values(["worst_dd","worst_path_profit"],ascending=[True,False])
    t12weak=groups[groups.dd12_net151].sort_values(["worst_dd","worst_path_profit"],ascending=[True,False])
    t10=groups[groups.dd10_net151].sort_values(["worst_dd","worst_path_profit"],ascending=[True,False])
    md=[
      "# BTCUSD 15m ATR0.2 minimum volatility — position-scale drawdown research",
      "",
      f"{len(groups)} variants tested in both 1m OHLC path orders. Historical sample Jan2025–Oct2026.",
      "Exact 15m-only Supertrend(10,3)/EMA20 reclaim entry. New filter ATR10/close >=0.20% evaluated at completed signal bar.",
      "3% SL, 9% TP, late protection activates at +8.25% and first lock at 0%; 5 losing exits per IST month halts new entries.",
      "Tiered 1x post-loss sizing; uniform global size factors 55%–100%. No additional leverage.",
      "Modeled 0.05% taker fee per side +18% GST, 0.02% adverse slippage per side; funding and live depth not modeled.",
      "**All 22 months heavily selected / in-sample. Do not treat these as forward results.**",
      "Verified control in every shard and both paths: 71 trades, +229.037% total return, 14.740% floating DD, 18/22 profitable months.",
      "",
      f"Strict improvement over +162.964%/14.74%/18 months: {len(strict)} variants.",
      f"Under 12% floating DD and >=162.964% return with >=18 months: {len(t12)}.",
      f"Under 12% floating DD and >=151.787% return with >=18 months: {len(t12weak)}.",
      f"Under 10% floating DD and >=151.787% return with >=18 months: {len(t10)}.",
      "",
      "## Best strictly lower DD preserving +162.964% and 18 positive months",
      strict.head(30).to_markdown(index=False) if len(strict) else "None.",
      "", "## Candidates below 12% with >=162.964% net",
      t12.head(30).to_markdown(index=False) if len(t12) else "None.",
      "", "## Candidates below 10% with >=151.787% net",
      t10.head(20).to_markdown(index=False) if len(t10) else "None.",
      "", "## All lowest-drawdown variants",
      groups.sort_values(["worst_dd","worst_path_profit"],ascending=[True,False]).head(30).to_markdown(index=False),
      "",
      "## Interpretation",
      "No variant uses more than the original 1x notional. Expected profit can fall in future unseen regimes; volatility signal filters and adaptive sizing may overfit this heavily researched sample."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(md)+"\n")
    print("\n".join(md[:15]),flush=True)

if __name__=="__main__":
    n=int(os.environ.get("SHARD_COUNT","8"))
    if len(sys.argv)>1 and sys.argv[1]=="aggregate":aggregate(n)
    else:run(int(os.environ.get("SHARD_INDEX","0")),n)
