#!/usr/bin/env python3
"""Faithful BTC 15m reclaim alternate time exits, 1m execution, 22-month history.
One optional modification to original simulator: close any still-open trade
on the FIRST 1m open at a precommitted holding-time limit. No future info.
No 1h signal/filter, no Supertrend reversal exit and max 1x notional.
"""
import os,sys,inspect
from pathlib import Path
import pandas as pd
import research_btc15m_adaptive_equity_risk_20261123 as risk
base=risk.base
OUT=Path("analysis/btc15m_time_exit_dd_20261123")
TIERS={
"T65_30_10":(.65,.30,.10),
"T65_20_10":(.65,.20,.10),
"T75_10_10":(.75,.10,.10),
"T85_20_10":(.85,.20,.10),
"T85_10_10":(.85,.10,.10),
}
HOURS=[0,12,24,48,72,96,120,168,240,336,480,720,960,1440]

def multiplier(name,losses):
    key=name.split("__SZ_",1)[1].split("_SL300",1)[0]
    x,y,z=TIERS[key]
    if losses>=4:return z
    if losses>=3:return y
    if losses>=2:return x
    return 1.

def simulator():
    source=inspect.getsource(base.simulate)
    before="wait,fil,risk_mode,riskmult,tpR,lock=cfg"
    assert source.count(before)==1
    source=source.replace(before,before+"""\n    time_stop_hours=int(name.split("__MAXH_",1)[1].split("__SZ_",1)[0]) if "__MAXH_" in name else 0""")
    size="qty=cash/entry"
    assert source.count(size)==1
    source=source.replace(size,"qty=(cash/entry)*multiplier(name,losses_this_month)")
    target="if i in signal_indices and position is not None:"
    assert source.count(target)==1
    source=source.replace(target,"""if position is not None and time_stop_hours>0 and sec>=position["entry_sec"]+time_stop_hours*3600:\n            close_trade(raw_open,sec,"TIME_EXIT")\n        """+target)
    ns=dict(base.__dict__); ns["multiplier"]=multiplier
    exec(compile(source,"<validated_sim_optional_time_exit>","exec"),ns)
    return ns["simulate"]

def run(idx,n):
    sim=simulator()
    df,quality=base.read_source("BTCUSD")
    ema,stline,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df)
    signals=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    cfg=(4,"any","PCT",3,3.0,"LATE:8.25:0:2:0.5")
    for path in base.PATHS:
        c,mon,led=sim(df,ema,stline,trend,ind,"reclaim_NOFLIP_LATE825_MLOSS5__MAXH_0__SZ_T65_30_10_SL300_TP3R",cfg,signals,path)
        assert int(c["trades"])==72 and int(c["profitable_months"])==18 and abs(c["net_return_pct"]-162.964)<.02 and abs(c["max_floating_drawdown_pct"]-14.740)<.02, c
    out=OUT/f"shard_{idx}"
    out.mkdir(parents=True,exist_ok=True)
    rows=[];monthly=[]
    combos=[(tier,h) for tier in TIERS for h in HOURS]
    for i,(tier,hrs) in enumerate(combos):
        if i%n!=idx:continue
        name=f"reclaim_NOFLIP_LATE825_MLOSS5__MAXH_{hrs}__SZ_{tier}_SL300_TP3R"
        for path in base.PATHS:
            r,mo,ledger=sim(df,ema,stline,trend,ind,name,cfg,signals,path)
            r["tier"]=tier;r["timeout_hours"]=hrs
            mo["tier"]=tier;mo["timeout_hours"]=hrs
            rows.append(r);monthly.append(mo)
            print(f"RUN {tier} limit {hrs}h {path} return={r['net_return_pct']} dd={r['max_floating_drawdown_pct']} month={r['profitable_months']}",flush=True)
    pd.DataFrame(rows).to_csv(out/"summary.csv",index=False)
    pd.concat(monthly,ignore_index=True).to_csv(out/"monthly.csv",index=False)
    print("SHARD COMPLETE",idx,len(rows),flush=True)

def aggregate(n):
    s=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"summary.csv") for i in range(n)],ignore_index=True)
    months=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"monthly.csv") for i in range(n)],ignore_index=True)
    s.to_csv(OUT/"summary.csv",index=False)
    months.to_csv(OUT/"monthly.csv",index=False)
    ranked=s.groupby(["tier","timeout_hours"]).agg(
        max_floating_dd=("max_floating_drawdown_pct","max"),
        min_net=("net_return_pct","min"),
        min_profitable_months=("profitable_months","min"),
        min_trades=("trades","min"),max_trades=("trades","max"),
        max_fee_gst=("fees_gst_usd","max")).reset_index()
    ranked["qualify_current"]= (ranked.max_floating_dd<14.740-.001)&(ranked.min_net>=162.964-.01)&(ranked.min_profitable_months>=18)
    ranked["qualify_original"]= (ranked.max_floating_dd<14.740-.001)&(ranked.min_net>=151.787-.01)&(ranked.min_profitable_months>=18)
    ranked["target12"]= (ranked.max_floating_dd<12)&(ranked.min_net>=151.787-.01)&(ranked.min_profitable_months>=18)
    ranked.sort_values(["max_floating_dd","min_net"],ascending=[True,False]).to_csv(OUT/"ranked.csv",index=False)
    best=ranked[ranked.qualify_current].sort_values(["max_floating_dd","min_net"],ascending=[True,False])
    weaker=ranked[ranked.qualify_original].sort_values(["max_floating_dd","min_net"],ascending=[True,False])
    report=["# BTCUSD 15m Reclaim — causal maximum-holding-time research",
      "",f"{len(ranked)} variants x two intra-1m OHLC order assumptions; original engine and 14.74%/+162.964%/18-month benchmark verified each shard.",
      "Only new exit is first 1m open at selected time-limit; stop, target and 8.25% late-protection evaluated normally until then.",
      "Position sizes max 1x, based on number of prior realized losing trades within same IST month; five-loss monthly entry pause on.",
      "Jan2025–Oct2026 repeatedly mined data, in-sample only, no out-of-sample claim. Fees plus GST and 0.02% per-side adverse slippage; funding and real execution unmodeled.",
      "",f"Strict improvements over +162.964% /14.74% /18 months: {len(best)}",
      f"Improvements over +151.787% /14.74% /18 months: {len(weaker)}; <12% DD qualifying: {int(ranked.target12.sum())}",
      "", "## Best strict qualifying models",
      best.head(30).to_markdown(index=False) if len(best) else "None.",
      "", "## Best meeting original net and winning months",
      weaker.head(30).to_markdown(index=False) if len(weaker) else "None.",
      "", "## Lowest DD irrespective of profit",
      ranked.sort_values(["max_floating_dd","min_net"],ascending=[True,False]).head(25).to_markdown(index=False),
      "", "## Important",
      "All reported DD is maximum open-position inclusive floating drawdown. Test assumptions are theoretical OHLC paths, not tick-level order book fills. Reducing hold time can lower DD while losing large trends, so preserve profit and month conditions."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("\n".join(report[:10]),flush=True)
if __name__=="__main__":
    n=int(os.environ.get("SHARD_COUNT","8"))
    if len(sys.argv)>1 and sys.argv[1]=="aggregate":aggregate(n)
    else:run(int(os.environ.get("SHARD_INDEX","0")),n)
