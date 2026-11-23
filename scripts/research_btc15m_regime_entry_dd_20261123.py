#!/usr/bin/env python3
"""Pre-entry, causal 15m market-state filtering over original BTC Reclaim simulator.

No look-ahead: features from fully completed 15m signal candle j (and past)
only. Tested on *already research-exposed* Jan2025-Oct2026 history; this
sweep is exploratory, not forward validation. Fees and GST handled by source.
"""
import os, sys, inspect
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc15m_adaptive_equity_risk_20261123 as risk

base = risk.base
OUT = Path("analysis/btc15m_regime_entry_dd_20261123")
TIER = {
 "T65_30_10": (.65,.30,.10),
 "T65_20_10": (.65,.20,.10),
 "T75_10_10": (.75,.10,.10),
 "T85_20_10": (.85,.20,.10),
 "T85_10_10": (.85,.10,.10),
}
RULES = {"any": ("any", 0)}
for x in [0.4, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0]:
    RULES[f"VOLMIN_{str(x).replace('.', 'p')}"] = ("vol_min", x)
for x in [1.0, 1.5, 2.0, 3.0, 4.0]:
    RULES[f"VOLMAX_{str(x).replace('.', 'p')}"] = ("vol_max", x)
for x in [.12,.2,.3,.4,.5,.7,.9,1.2]:
    RULES[f"ATRMAX_{str(x).replace('.', 'p')}"] = ("atr_max", x)
for x in [.05,.10,.15,.20,.3,.4]:
    RULES[f"ATRMIN_{str(x).replace('.', 'p')}"] = ("atr_min", x)
for x in [.10,.25,.40,.55]:
    RULES[f"BODY_{str(x).replace('.', 'p')}"] = ("body", x)
for x in [.05,.10,.15,.20,.30]:
    RULES[f"EMAMARGIN_{str(x).replace('.', 'p')}"] = ("margin_atr", x)
for x in [2,4,8,12]:
    RULES[f"EMASLOPE_{x}"] = ("slope", x)
for x in [10,15,20,25]:
    RULES[f"RSITREND_{x}"] = ("rsi_mid", x)  # signal's RSI must be >50+threshold/2 long, <50-threshold/2 short
for x in [.75,1.0,1.25,1.5,2.0]:
    RULES[f"RANGE_MAX_{str(x).replace('.', 'p')}"] = ("range_max", x)
for k in ["long","short"]:
    RULES[f"SIDE_{k}"] = ("side", k)
for k in ["weekday","weekend","morning","afternoon","evening","night"]:
    RULES[f"TIME_{k}"] = ("time", k)
for vol in [.5, .8, 1.2]:
    for atr in [.4, .6]:
        RULES[f"COMB_VOL{str(vol).replace('.', 'p')}_ATR{str(atr).replace('.', 'p')}"] = ("combo", (vol,atr))

CACHE = None

def enrich(df, ind, ema):
    global CACHE
    v=ind["V"]; c=ind["C"];o=ind["O"];h=ind["H"];l=ind["L"];a=ind["ATR"]
    vr=np.full(len(v),np.nan)
    for i in range(20,len(v)):
        prev=float(np.mean(v[i-20:i]))
        if prev>0:vr[i]=v[i]/prev
    # RSI14 Wilder using completed 15m closes only.
    up=np.maximum(0,np.diff(c)); down=np.maximum(0,-np.diff(c))
    rsi=np.full(len(c),np.nan)
    if len(c)>14:
        avgu=np.mean(up[:14]);avgd=np.mean(down[:14])
        rsi[14]=100 if avgd==0 else 100-100/(1+avgu/avgd)
        for i in range(15,len(c)):
            avgu=(avgu*13+up[i-1])/14
            avgd=(avgd*13+down[i-1])/14
            rsi[i]=100 if avgd==0 else 100-100/(1+avgu/avgd)
    dt=pd.to_datetime(df.time.to_numpy(np.int64)[::15],unit="s",utc=True).tz_convert("Asia/Kolkata")
    CACHE={"vol":vr, "atr_pct":100*a/c,
      "body":(c-o)/np.maximum(h-l,1e-9),
      "dist_atr":(c-ema)/np.maximum(a,1e-9),
      "atr":a, "close":c, "high":h, "low":l,
      "rsi":rsi, "hour":dt.hour.to_numpy(), "weekday":dt.dayofweek.to_numpy()}
    assert len(CACHE["hour"])==len(c)

def market_filter(fil,side,j,ema,ind):
    if fil=="any":return True
    kind,v=RULES[fil];z=CACHE
    if j>=len(z["close"]) or j<25:return False
    if kind=="vol_min":return z["vol"][j]>=v
    if kind=="vol_max":return z["vol"][j]<=v
    if kind=="atr_max":return z["atr_pct"][j]<=v
    if kind=="atr_min":return z["atr_pct"][j]>=v
    if kind=="body":return side*z["body"][j]>=v
    if kind=="margin_atr":return side*z["dist_atr"][j]>=v
    if kind=="slope":return side*(ema[j]-ema[j-v])>0
    if kind=="rsi_mid":return side*(z["rsi"][j]-50)>=v/2
    if kind=="range_max":return (z["high"][j]-z["low"][j])/max(z["atr"][j],1e-9)<=v
    if kind=="side":return (side==1)==(v=="long")
    if kind=="time":
        h=z["hour"][j];day=z["weekday"][j]
        if v=="weekday":return day<=4
        if v=="weekend":return day>=5
        if v=="morning":return 6<=h<12
        if v=="afternoon":return 12<=h<18
        if v=="evening":return 18<=h<24
        if v=="night":return 0<=h<6
    if kind=="combo":return z["vol"][j]>=v[0] and z["atr_pct"][j]<=v[1]
    raise RuntimeError(f"Invalid filter {fil}")

def tiered_size(name,losses):
    k=name.split("__SZ_",1)[1].split("_SL300",1)[0]
    s2,s3,s4=TIER[k]
    if losses>=4:return s4
    if losses>=3:return s3
    if losses>=2:return s2
    return 1.0

def modified_simulator():
    source=inspect.getsource(base.simulate)
    old1="if not check_filter(fil,side,j,ema,ind):"
    old2="qty=cash/entry"
    assert source.count(old1)==source.count(old2)==1
    source=source.replace(old1,"if not market_filter(fil,side,j,ema,ind):")
    source=source.replace(old2,"qty=(cash/entry)*tiered_size(name,losses_this_month)")
    ns=dict(base.__dict__)
    ns["market_filter"]=market_filter
    ns["tiered_size"]=tiered_size
    exec(compile(source,"<original_sim_filtered>","exec"),ns)
    return ns["simulate"]

def run(index,n):
    OUT.mkdir(parents=True,exist_ok=True)
    df,quality=base.read_source("BTCUSD")
    ema,stline,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df)
    enrich(df,ind,ema)
    signals=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    sim=modified_simulator()
    # Reproducible no-filter control using exact prior best model; fails closed.
    basecfg=(4,"any","PCT",3,3.0,"LATE:8.25:0:2:0.5")
    for path in base.PATHS:
        name="reclaim_NOFLIP_LATE825_MLOSS5__SZ_T65_30_10_SL300_TP3R"
        row,monthly,ledger=sim(df,ema,stline,trend,ind,name,basecfg,signals,path)
        assert abs(row["net_return_pct"]-162.964)<.02, row
        assert abs(row["max_floating_drawdown_pct"]-14.74)<.02, row
        assert int(row["profitable_months"])==18 and int(row["trades"])==72,row
    entries=list((tier,fil) for tier in TIER for fil in RULES)
    all_rows=[];all_months=[]
    for j,(tier,fil) in enumerate(entries):
        if j%n!=index:continue
        name=f"reclaim_NOFLIP_LATE825_MLOSS5__SZ_{tier}_SL300_TP3R"
        cfg=(4,fil,"PCT",3,3.0,"LATE:8.25:0:2:0.5")
        for path in base.PATHS:
            r,m,t=sim(df,ema,stline,trend,ind,name,cfg,signals,path)
            r["tier"]=tier;r["filter"]=fil
            m["tier"]=tier;m["filter"]=fil
            all_rows.append(r);all_months.append(m)
            print(f"RESULT {tier} {fil} {path} return={r['net_return_pct']} dd={r['max_floating_drawdown_pct']} months={r['profitable_months']}",flush=True)
    sub=OUT/f"shard_{index}"
    sub.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(all_rows).to_csv(sub/"summary.csv",index=False)
    pd.concat(all_months,ignore_index=True).to_csv(sub/"months.csv",index=False)
    print("SHARD",index,"finished",len(all_rows),flush=True)

def aggregate(n):
    s=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"summary.csv") for i in range(n)],ignore_index=True)
    m=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"months.csv") for i in range(n)],ignore_index=True)
    s.to_csv(OUT/"summary.csv",index=False)
    m.to_csv(OUT/"months.csv",index=False)
    score=s.groupby(["tier","filter"]).agg(
      worst_dd=("max_floating_drawdown_pct","max"),
      min_profit=("net_return_pct","min"),
      min_winning_months=("profitable_months","min"),
      min_trades=("trades","min"),
      max_filtered=("signals_filtered","max")
      ).reset_index()
    # Prior selected strongest >=162.964%, <=14.740%, >=18/22.
    score["pass_previous_profit"]=(score.min_profit>=162.964-.01)&(score.min_winning_months>=18)
    score["beats_previous"]=(score.pass_previous_profit)&(score.worst_dd<14.740-.001)
    score["pass_original_profit"]=(score.min_profit>=151.787-.01)&(score.min_winning_months>=18)
    score["target_12"]=(score.pass_original_profit)&(score.worst_dd<12)
    score["target_10"]=(score.pass_original_profit)&(score.worst_dd<10)
    score.sort_values(["worst_dd","min_profit"],ascending=[True,False]).to_csv(OUT/"ranked.csv",index=False)
    prior=score[score.beats_previous].sort_values(["worst_dd","min_profit"],ascending=[True,False])
    target=score[score.pass_original_profit].sort_values(["worst_dd","min_profit"],ascending=[True,False])
    best=score.sort_values(["worst_dd","min_profit"],ascending=[True,False])
    lines=["# BTCUSD 15m causal pre-entry filter and risk-size research",
      "",
      f"{len(score)} variants x 2 hypothetical intraminute paths. Jan2025–Oct2026 historical in-sample; NOT independent validation.",
      "Fifteen-minute indicators only and completed-bar signals; 1-minute exits in the unchanged original simulator.",
      "No Supertrend reversal exit, 3% SL, 9% TP, profit trigger 8.25%, BE lock, 5-loss month pause.",
      "Fees +18% GST plus 0.02% per-side slippage included; funding and live spread/gaps NOT fully modeled.",
      "Baseline revalidated for each shard/path: 72 trades, +162.964% return, 14.740% max floating DD, 18/22 positive months.",
      "",
      f"Strictly better than baseline profit and floating DD while retaining >=18 positive months: {len(prior)}",
      f"At least old +151.787% profit & >=18 positive months, below 12% DD: {int(score.target_12.sum())}; below 10% DD: {int(score.target_10.sum())}.",
      "",
      "## Pass strict objective",
      prior.head(40).to_markdown(index=False) if len(prior) else "None.",
      "", "## Smallest DD with >=151.787% profit and >=18 months",
      target.head(30).to_markdown(index=False) if len(target) else "None.",
      "", "## Overall lowest DD irrespective of return",
      best.head(20).to_markdown(index=False),
      "", "## Cautions",
      "Using the same history for model search can seriously overfit; prospective paper trading and no-lookahead forward testing are necessary.",
      "Max DD is floating intratrade peak-to-trough in 1x notional, not closed-trade DD."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines[:11]),flush=True)

if __name__=="__main__":
    n=int(os.environ.get("SHARD_COUNT","8"))
    if len(sys.argv)>1 and sys.argv[1]=="aggregate":aggregate(n)
    else:run(int(os.environ.get("SHARD_INDEX","0")),n)
