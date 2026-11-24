#!/usr/bin/env python3
"""Optimize positive calendar months WITHOUT sacrificing profit or max floating DD.

BTCUSD 15m Supertrend10/3 EMA20 Reclaim, 15m ATR10/close >= 0.20%,
1m fills: 0.05% taker per side +18% GST and 0.02% slippage per side.
Two INDEPENDENT locked research baselines, 80% and 100% equity-notional.
Require >=19/22 positive months, profit >= baseline and intratrade maximum
floating DD <= baseline under BOTH simulated 1m OHLC orderings.
All results IN SAMPLE (Jan 2025–Oct 2026), no funding/liquidation book.
"""
import itertools, inspect, os, sys
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc15m_regime_entry_dd_20261123 as entry

base=entry.base
OUT=Path("analysis/btc15m_atr_monthly_win_improvement_20261124")
LOCK="LATE:8:2:1:0.25"
PROFILES={
    "80":dict(scale=.8,tiers=(1.,.35,.30,.10),net=185.0292,dd=10.465),
    "100":dict(scale=1.,tiers=(1.,.30,.25,.10),net=266.1034,dd=12.916),
}
# Only completed 15m signal-candle values (and older values) can be used.
FILTERS={"F000":("none",None)}
def addf(kind,vals):
    for val in vals:
        FILTERS[f"F{len(FILTERS):03d}"]=(kind,val)
addf("vol_min",[.2,.4,.6,.8,1.,1.2,1.5,2.])
addf("vol_max",[.5,.75,1.,1.2,1.5,2.,3.])
addf("rsi_direction_min",[0,2,5,10,15,20])
addf("rsi_direction_max",[0,2,5,10,15,20])
addf("ema_distance_min",[.05,.1,.2,.3,.5,1.])
addf("ema_distance_max",[.2,.4,.6,.8,1.,1.5,2.])
addf("body_min",[.05,.1,.2,.3,.4,.5])
addf("body_max",[.2,.3,.4,.5,.65])
addf("ema_slope",[2,4,8,12,16,24])
addf("range_max",[.75,1.,1.25,1.5,2.,3.])
addf("range_min",[.2,.4,.6,.8,1.,1.5])
addf("atr_max",[.25,.3,.4,.5,.6,.8,1.])
addf("atr_min",[.205,.21,.22,.23,.25,.3])
addf("side",["long","short"])
addf("time",["weekday","weekend","no_monday","no_friday","night","morning","afternoon","evening"])
for v,a in itertools.product([.6,.8,1.,1.2],[.25,.4,.6]):
    FILTERS[f"F{len(FILTERS):03d}"]=("vol_min_atr_max",(v,a))
for vol,margin in itertools.product([.4,.8,1.2],[.1,.2,.3]):
    FILTERS[f"F{len(FILTERS):03d}"]=("vol_min_dist_min",(vol,margin))
for vol,body in itertools.product([.4,.8,1.2],[.1,.2,.3]):
    FILTERS[f"F{len(FILTERS):03d}"]=("vol_min_body_min",(vol,body))

# Realized month-start equity guards, strictly observable before each new entry.
GUARDS={"G000":("none",0.)}
for v in [.05,.1,.25,.5,1.,1.5,2.,3.,4.,5.,7.5,10.]:
    GUARDS[f"G{len(GUARDS):03d}"]=("stop_after_realized_month_profit_pct",v)
for v in [1,2,3,4]:
    GUARDS[f"G{len(GUARDS):03d}"]=("stop_after_n_month_losses",v)
for x in [.5,1.,2.,3.]:
    GUARDS[f"G{len(GUARDS):03d}"]=("stop_after_month_profit_or_two_losses",x)

def rule_code(name):
    return name.split("__Q_",1)[1].split("_SL300",1)[0]

def profile_size(name,losses):
    profile=name.split("__P_",1)[1].split("__Q_",1)[0]
    z=PROFILES[profile]
    if losses>=4: tier=z["tiers"][3]
    elif losses>=3: tier=z["tiers"][2]
    elif losses>=2: tier=z["tiers"][1]
    else: tier=z["tiers"][0]
    return z["scale"]*tier

def candidate_entry_filter(fil,side,j,ema,ind,name):
    z=entry.CACHE
    if j<25 or j>=len(z["close"]) or not np.isfinite(z["atr_pct"][j]) or z["atr_pct"][j]<.20:
        return False
    code=rule_code(name)
    if not code.startswith("F"):return True
    kind,v=FILTERS[code]
    if kind=="none":return True
    if kind=="vol_min":return bool(z["vol"][j]>=v)
    if kind=="vol_max":return bool(z["vol"][j]<=v)
    if kind=="rsi_direction_min":return bool(side*(z["rsi"][j]-50)>=v)
    if kind=="rsi_direction_max":return bool(side*(z["rsi"][j]-50)<=v)
    if kind=="ema_distance_min":return bool(side*z["dist_atr"][j]>=v)
    if kind=="ema_distance_max":return bool(side*z["dist_atr"][j]<=v)
    if kind=="body_min":return bool(side*z["body"][j]>=v)
    if kind=="body_max":return bool(side*z["body"][j]<=v)
    if kind=="ema_slope":return bool(side*(ema[j]-ema[j-v])>0)
    if kind=="range_max":return bool((z["high"][j]-z["low"][j])/max(z["atr"][j],1e-9)<=v)
    if kind=="range_min":return bool((z["high"][j]-z["low"][j])/max(z["atr"][j],1e-9)>=v)
    if kind=="atr_max":return bool(z["atr_pct"][j]<=v)
    if kind=="atr_min":return bool(z["atr_pct"][j]>=v)
    if kind=="side":return bool((side==1)==(v=="long"))
    if kind=="time":
        h=z["hour"][j];d=z["weekday"][j]
        if v=="weekday":return bool(d<5)
        if v=="weekend":return bool(d>=5)
        if v=="no_monday":return bool(d!=0)
        if v=="no_friday":return bool(d!=4)
        if v=="night":return bool(h<6)
        if v=="morning":return bool(6<=h<12)
        if v=="afternoon":return bool(12<=h<18)
        if v=="evening":return bool(18<=h<24)
    if kind=="vol_min_atr_max":return bool(z["vol"][j]>=v[0] and z["atr_pct"][j]<=v[1])
    if kind=="vol_min_dist_min":return bool(z["vol"][j]>=v[0] and side*z["dist_atr"][j]>=v[1])
    if kind=="vol_min_body_min":return bool(z["vol"][j]>=v[0] and side*z["body"][j]>=v[1])
    raise ValueError((code,kind))

def candidate_guard(name,cash,month_reference,losses_this_month):
    code=rule_code(name)
    if not code.startswith("G"):return False
    kind,v=GUARDS[code]
    if kind=="none":return False
    month_return=100*(cash/month_reference-1) if month_reference>0 else 0
    if kind=="stop_after_realized_month_profit_pct":return bool(month_return>=v)
    if kind=="stop_after_n_month_losses":return bool(losses_this_month>=v)
    if kind=="stop_after_month_profit_or_two_losses":return bool(month_return>=v or losses_this_month>=2)
    raise ValueError((code,kind))

def modified_simulator():
    source=inspect.getsource(base.simulate)
    old_filter="if not check_filter(fil,side,j,ema,ind):"
    old_size="qty=cash/entry"
    old_guard="if i in signal_indices and position is None and block_entry:"
    for old in (old_filter,old_size,old_guard):
        assert source.count(old)==1, f"Simulator drift in original engine: {old}"
    source=source.replace(old_filter,"if not candidate_entry_filter(fil,side,j,ema,ind,name):")
    source=source.replace(old_size,"qty=(cash/entry)*profile_size(name,losses_this_month)")
    source=source.replace(old_guard,
        "if i in signal_indices and position is None and not block_entry:\n"
        "            block_entry=bool(candidate_guard(name,cash,month_reference,losses_this_month))\n"
        "        "+old_guard)
    ns=dict(base.__dict__)
    ns.update(candidate_entry_filter=candidate_entry_filter,profile_size=profile_size,candidate_guard=candidate_guard)
    exec(compile(source,"<monthly_win_causal_engine>","exec"),ns)
    return ns["simulate"]

def run(index,total):
    OUT.mkdir(parents=True,exist_ok=True)
    sim=modified_simulator()
    df,quality=base.read_source("BTCUSD")
    ema,stline,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df)
    entry.enrich(df,ind,ema)
    signals=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    cfg=(4,"ATRMIN_0p2","PCT",3.,3.,LOCK)
    for profile,z in PROFILES.items():
        name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{profile}__Q_F000_SL300_TP3R"
        for path in base.PATHS:
            row,mon,ledger=sim(df,ema,stline,trend,ind,name,cfg,signals,path)
            assert abs(row["net_return_pct"]-z["net"])<.005 and abs(row["max_floating_drawdown_pct"]-z["dd"])<.005 and row["profitable_months"]==18 and row["trades"]==73, ("FAIL original baseline",profile,path,row)
            print("BASELINE_CONFIRMED",profile,path,row["net_return_pct"],row["max_floating_drawdown_pct"],flush=True)
    rules=list(FILTERS)+list(GUARDS)
    rows=[];months=[]
    for i,rule in enumerate(rules):
        if i%total!=index:continue
        for profile in PROFILES:
            name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{profile}__Q_{rule}_SL300_TP3R"
            for path in base.PATHS:
                r,mo,ledger=sim(df,ema,stline,trend,ind,name,cfg,signals,path)
                returns=mo.monthly_return_pct.to_numpy(float)
                r.update(profile=profile,rule=rule,rule_detail=str(FILTERS.get(rule,GUARDS.get(rule))),
                  losing_months=int((returns<0).sum()),
                  worst_month_pct=round(float(returns.min()),5),
                  total_loss_months_pct=round(float(np.minimum(returns,0).sum()),5))
                mo["profile"]=profile;mo["rule"]=rule
                rows.append(r);months.append(mo)
                print(f"RESULT rule={rule} prof={profile} path={path} ret={r['net_return_pct']} dd={r['max_floating_drawdown_pct']} positive={r['profitable_months']}",flush=True)
    shard=OUT/f"shard_{index}"
    shard.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(shard/"summary.csv",index=False)
    pd.concat(months,ignore_index=True).to_csv(shard/"monthly.csv",index=False)
    print("SHARD_COMPLETE",index,len(rows),flush=True)

def aggregate(count):
    s=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"summary.csv",dtype={"profile":str,"rule":str}) for i in range(count)],ignore_index=True)
    mo=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"monthly.csv",dtype={"profile":str,"rule":str}) for i in range(count)],ignore_index=True)
    s.to_csv(OUT/"summary.csv",index=False)
    mo.to_csv(OUT/"monthly.csv",index=False)
    score=s.groupby(["profile","rule","rule_detail"],as_index=False).agg(
        worst_floating_dd=("max_floating_drawdown_pct","max"),
        min_profit=("net_return_pct","min"),positive_months=("profitable_months","min"),
        maximum_losing_months=("losing_months","max"),worst_month=("worst_month_pct","min"),
        sum_losing_month_returns=("total_loss_months_pct","min"),trades_min=("trades","min"))
    score["baseline_net"]=score.profile.map({p:z["net"] for p,z in PROFILES.items()})
    score["baseline_dd"]=score.profile.map({p:z["dd"] for p,z in PROFILES.items()})
    score["preserves_profit"]=score.min_profit >= score.baseline_net-0.0001
    score["preserves_dd"]=score.worst_floating_dd <= score.baseline_dd+0.0001
    score["more_winning_months"]=score.positive_months>=19
    score["qualifies"]=score.preserves_profit & score.preserves_dd & score.more_winning_months
    score.to_csv(OUT/"ranked.csv",index=False)
    lines=["# BTCUSD 15M ATR>=0.2% — increase PROFITABLE MONTHS WITHOUT REDUCING PROFIT",
       "",f"{len(score)} independent profile-rule pairs x 2 simulated 1m OHLC path orderings.",
       "Research periods: Jan 2025 through Oct 2026, 22 IST calendar months. All in-sample and highly optimized previously.",
       "Baseline 80%: +185.0292% net, 10.465% max FLOATING DD, 18/22 profitable months.",
       "Baseline 100%: +266.1034% net, 12.916% max FLOATING DD, 18/22 profitable months.",
       "Strict eligibility: >=19/22 profitable, profit not reduced even by 0.0001 percentage point, DD not raised even by 0.0001pp, BOTH price-path orders.",
       "Market-state entry filters based on completed 15m bars (never calendar month foreknowledge), and realized month-account controls based only on current known realized month P&L.",
       "Unchanged core: ST(10,3)/EMA20 reclaim + ATR(10)/close>=0.2%, SL3% TP9%, profit protect +8% activates +2% lock, +0.25% for each further 1%, 5 losing-trade monthly entry pause, capped notional <=1x.",
       "Costs: 0.05% taker EACH SIDE, GST18% of fees, 0.02% adverse per-side slippage. No funding, order-book, real fills or liquidation.",
       ""]
    for profile in PROFILES:
        x=score[score.profile==profile].copy()
        win=x[x.qualifies].sort_values(["positive_months","worst_floating_dd","min_profit"],ascending=[False,True,False])
        near=x[x.preserves_profit & x.preserves_dd].sort_values(["positive_months","worst_floating_dd","min_profit"],ascending=[False,True,False])
        partial=x[x.positive_months>=19].sort_values(["worst_floating_dd","min_profit"],ascending=[True,False])
        x.to_csv(OUT/f"profile_{profile}_ranked.csv",index=False)
        lines.extend([f"## {profile}% exposure separately",f"**QUALIFYING 19+ positive month profiles: {len(win)}**",
          "", "### Meeting ALL non-negotiable goals",
          win.head(35).to_markdown(index=False) if len(win) else "None.",
          "", "### Baseline profit and DD preserved (may have same 18/22 months)",
          near.head(15).to_markdown(index=False) if len(near) else "None.",
          "", "### 19+ month candidates failing either profit or DD floor (DO NOT ADOPT)",
          partial.head(15).to_markdown(index=False) if len(partial) else "None.",
          ""])
    lines.extend(["## Interpretation",
      "No change to user-locked 100% profile or shortlisted 80% profile: all results are research trials.",
      "A 22-month history with repeatedly tuned parameters is especially vulnerable to data-snooping; any candidate needs genuinely unseen forward data.",
      "Monthly win count is a 22-observation metric, not a guarantee of profitability."])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines[:13]),flush=True)
    for profile in PROFILES:
        xx=score[(score.profile==profile)&score.qualifies].sort_values(["positive_months","worst_floating_dd","min_profit"],ascending=[False,True,False])
        print("QUALIFIED",profile,len(xx),xx.head(6).to_dict("records"),flush=True)

if __name__=="__main__":
    total=int(os.environ.get("SHARD_COUNT","16"))
    if len(sys.argv)>1 and sys.argv[1]=="aggregate":aggregate(total)
    else:run(int(os.environ.get("SHARD_INDEX","0")),total)
