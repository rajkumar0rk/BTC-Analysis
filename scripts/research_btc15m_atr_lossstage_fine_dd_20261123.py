#!/usr/bin/env python3
"""Focused causal loss-stage position sizing: drawdown reduction first.

BTCUSD 15m ATR >=0.20% and 1m faithful original replay, 22 IST months.
Research profiles are kept distinct, max 0.80x or 1.00x BTC notional;
no changes to ST/EMA20 reclaim, 3% SL, 9% TP or +8/2 lock.
"""
import os,sys,itertools
from pathlib import Path
import pandas as pd
import numpy as np
import research_btc15m_atr_drawdown_first_both_20261123 as previous
base=previous.base
entry=previous.entry
OUT=Path("analysis/btc15m_atr_lossstage_fine_dd_20261123")
PROFILES=previous.PROFILES
BASE_AFTER_TWO={"80":(183.4472,10.916),"100":(260.5073,13.498)}
ORIGINAL={"80":(180.6308,11.879),"100":(255.8336,14.740)}
LOCK="LATE:8:2:1:0.25"

def profiles():
    f1=[.8,.9,1.0]
    f2=[.25,.3,.35,.4,.45,.5]
    f3=[.15,.2,.25,.3,.35,.4]
    f4=[.1,.15,.2,.25,.3]
    # All stages monotonic nonincreasing as realized losing trades accumulate.
    return [(f"T{int(round(a*1000))}x{int(round(b*1000))}x{int(round(c*1000))}x{int(round(d*1000))}",a,b,c,d)
        for a,b,c,d in itertools.product(f1,f2,f3,f4) if a>=b>=c>=d]

def fine_size(name,losses,cash,peak):
    profile=name.split("__P_",1)[1].split("__R_",1)[0]
    rule=name.split("__R_",1)[1].split("_SL300",1)[0]
    assert rule.startswith("T")
    a,b,c,d=[int(v)/1000 for v in rule[1:].split("x")]
    ladder=1.0 if losses==0 else a if losses==1 else b if losses==2 else c if losses==3 else d
    return PROFILES[profile][0]*ladder

def run(index,total):
    OUT.mkdir(parents=True,exist_ok=True)
    previous.size_rule=fine_size
    sim=previous.make_simulator()
    df,quality=base.read_source("BTCUSD")
    ema,stline,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df)
    entry.enrich(df,ind,ema)
    signals=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    cfg=(4,"ATRMIN_0p2","PCT",3.,3.,LOCK)
    for profile in PROFILES:
        name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{profile}__R_T1000x400x300x200_SL300_TP3R"
        for path in base.PATHS:
            row,mon,tr=sim(df,ema,stline,trend,ind,name,cfg,signals,path)
            ret,dd=BASE_AFTER_TWO[profile]
            assert abs(row["net_return_pct"]-ret)<.025 and abs(row["max_floating_drawdown_pct"]-dd)<.025 and row["profitable_months"]==18 and row["trades"]==73,(profile,row)
    rows=[];months=[]
    rules=profiles()
    for j,(code,a,b,c,d) in enumerate(rules):
        if j%total!=index:continue
        for profile in PROFILES:
            name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{profile}__R_{code}_SL300_TP3R"
            for path in base.PATHS:
                row,mon,ledger=sim(df,ema,stline,trend,ind,name,cfg,signals,path)
                monthly=mon.monthly_return_pct.to_numpy(float)
                row.update(profile=profile,rule=code,stage1=a,stage2=b,stage3=c,stage4=d,
                    losing_months=int((monthly<0).sum()),worst_month_pct=float(np.min(monthly)),
                    sum_negative_months_pct=float(np.minimum(monthly,0).sum()))
                mon["profile"]=profile;mon["rule"]=code
                rows.append(row);months.append(mon)
                print(f"RESULT {profile} {code} {path} profit={row['net_return_pct']} drawdown={row['max_floating_drawdown_pct']} months={row['profitable_months']}",flush=True)
    p=OUT/f"shard_{index}"
    p.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(p/"summary.csv",index=False)
    pd.concat(months,ignore_index=True).to_csv(p/"monthly.csv",index=False)
    print("SHARD_DONE",index,len(rows),flush=True)

def aggregate(count):
    parts=[pd.read_csv(OUT/f"shard_{i}"/"summary.csv",dtype={"profile":str}) for i in range(count)]
    monthly=[pd.read_csv(OUT/f"shard_{i}"/"monthly.csv",dtype={"profile":str}) for i in range(count)]
    s=pd.concat(parts,ignore_index=True)
    m=pd.concat(monthly,ignore_index=True)
    s["profile"]=s["profile"].astype(str)
    m["profile"]=m["profile"].astype(str)
    s.to_csv(OUT/"summary.csv",index=False)
    m.to_csv(OUT/"monthly.csv",index=False)
    rank=s.groupby(["profile","rule","stage1","stage2","stage3","stage4"],as_index=False).agg(
        max_floating_dd=("max_floating_drawdown_pct","max"),
        min_net_profit=("net_return_pct","min"),
        positive_months=("profitable_months","min"),
        negative_months=("losing_months","max"),
        worst_month_pct=("worst_month_pct","min"),
        losing_months_sum=("sum_negative_months_pct","min"),
        min_trades=("trades","min"))
    rank["passes_original_profit"]=rank.apply(lambda x:x.min_net_profit>=ORIGINAL[x.profile][0]-.001 and x.positive_months>=18,axis=1)
    rank["passes_strong_candidate"]=rank.apply(lambda x:x.min_net_profit>=BASE_AFTER_TWO[x.profile][0]-.001 and x.positive_months>=18,axis=1)
    rank["strict_lower_dd_than_strong"]=rank.apply(lambda x:bool(x.passes_strong_candidate and x.max_floating_dd<BASE_AFTER_TWO[x.profile][1]-.002),axis=1)
    rank["strict_lower_dd_than_original"]=rank.apply(lambda x:bool(x.passes_original_profit and x.max_floating_dd<ORIGINAL[x.profile][1]-.002),axis=1)
    rank.to_csv(OUT/"ranked.csv",index=False)
    lines=[
      "# BTCUSD 15M ATR filter: finer position sizing AFTER realized losses, drawdown-first",
      "",
      f"{len(rank)} profile-specific variants; both hypothetical intraminute OHLC path orderings. 22 in-sample IST months Jan2025–Oct2026.",
      "Original ST10/3 EMA20 reclaim + ATR10 >=0.20% at completed 15m signal; 1m exit replay.",
      "3% price SL, 9% TP, +8% favorable activation of profit protection (first +2% locked, +.25% per +1% move).",
      "Loss count within current IST month determines position sizing; 5 losses halt future entries until following month.",
      "Fees 0.05% taker each side with 18% GST and 0.02% adverse slippage per side; no funding/order book/gap execution/liquidation.",
      "No candidate leverages beyond the 80% or 100% original max exposure.",
      "Original baseline to retain (80): +180.6308%, 11.879% DD, 18 months. (100): +255.8336%, 14.740% DD, 18 months.",
      "Verified secondary candidates in every shard: (80) +183.4472%/10.916% DD; (100) +260.5073%/13.498% DD.",
      "This is heavily researched in-sample data, not forward predictive performance.",
      ""]
    for profile in PROFILES:
        a=rank[rank.profile==profile].copy()
        best=a[a.strict_lower_dd_than_strong].sort_values(["max_floating_dd","min_net_profit"],ascending=[True,False])
        okay=a[a.strict_lower_dd_than_original].sort_values(["max_floating_dd","min_net_profit"],ascending=[True,False])
        low=a.sort_values(["max_floating_dd","min_net_profit"],ascending=[True,False])
        a.to_csv(OUT/f"profile_{profile}.csv",index=False)
        lines.extend([f"## {profile}% exposure profile", "",
            f"Improves secondary drawdown and preserves its profit/months: {len(best)}.",
            f"Improves original drawdown and preserves its profit/months: {len(okay)}.",
            "", "### Best DD reductions with no profit reduction vs best current risk candidate",
            best.head(30).to_markdown(index=False) if len(best) else "None.",
            "", "### Best qualifying vs original profit threshold",
            okay.head(30).to_markdown(index=False) if len(okay) else "None.",
            "", "### Absolute lowest observed DD (may lose profit or months)",
            low.head(15).to_markdown(index=False),
            ""])
    lines.extend(["## Interpretation","Each candidate uses one uniform causal loss-stage ladder applied without knowledge of future trades.",
      "The 22 months were selected and mined repeatedly, so historical DD reductions should be validated prospectively; real slippage, funding, liquidation can cause worse outcomes."])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines[:12]),flush=True)
    for p in PROFILES:
        b=rank[(rank.profile==p)&(rank.strict_lower_dd_than_strong)].sort_values(["max_floating_dd","min_net_profit"],ascending=[True,False]).head(5)
        print("PROF",p,"top",b.to_dict("records"),flush=True)
if __name__=="__main__":
    n=int(os.environ.get("SHARD_COUNT","16"))
    if len(sys.argv)>1 and sys.argv[1]=="aggregate":aggregate(n)
    else:run(int(os.environ.get("SHARD_INDEX","0")),n)
