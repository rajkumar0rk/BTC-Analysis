#!/usr/bin/env python3
"""Additional causal recovery setups, with latest 21-month controls.
No calendar-selected trades, no future data, one position and at most one
filled entry per actual Supertrend cycle. Normal entries take precedence.
"""
import os,sys,inspect,itertools
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc15m_atr_month21_fine_risk_20261124 as p
base=p.base
entry=p.entry
PROFILES=p.PROFILES
OUT=Path("analysis/btc15m_x102_combined_recovery_20261124")
FLOOR={"80":(271.2282,9.543),"100":(404.6151,11.708)}
RULES={}
EXTRA={}
def add(tiers,buffer,extra):
    code=f"X{len(RULES):03d}"
    RULES[code]=(tiers,buffer,extra)
    EXTRA[code]=extra
    p.RULES[code]=("losses",2,3.,9.,"LATE:4:2:1:0.25")
    p.SIZING[code]=tiers
    p.CAPS[code]=(1.,buffer)
    p.RECOVERY[code]=(1,0,.2)
    p.MINIMUM[code]=.01
add((.9,.15,.1,.05),.015,None)
add((.8,.1,.1,.1),.012,None)
VARIANTS={"X000":("refine",2.5,3.,2,3.5,2.,1.,.25,9.),"X001":("control",)}
ALLOC={}
def variant(spec,tiers=(.9,.15,.1,.05),buffer=.015,allocation=None):
    add(tiers,buffer,None)
    code=f"X{len(RULES)-1:03d}"
    VARIANTS[code]=spec
    ALLOC[code]=allocation
# Exact successful alternative controls.
variant(("refine",2.45,3.,2,4.,2.,1.,.25,9.))
variant(("refine",2.5,3.,2,4.,2.,1.,.25,9.),(.9,.1,.1,.2))
# Combine independently useful stop, lock and late-loss exposure rules.
for ss,act,tiers in itertools.product([2.4,2.45,2.5],[3.25,3.5,3.75,4.],[(.9,.15,.1,.05),(.9,.1,.1,.2),(.9,.1,.1,.4),(.9,.1,.2,.4)]):
    variant(("refine",ss,3.,2,act,2.,1.,.25,9.),tiers)
# Preserve equity risk headroom for later entries by reducing early risk
# when existing peak drawdown is already substantial.
for threshold,weight,late_size,ss in itertools.product(
    [1.,2.,3.,4.],[.35,.65,.85],[.25,.75],[2.45,2.5]):
    variant(("refine",ss,3.,2,3.5,2.,1.,.25,9.),(.9,.1,.1,late_size),.015,(threshold,weight,2))
# Drawdown-based early risk adjustment and differentiated loss-ladder.
for threshold,weight,early_size,late_size in itertools.product(
    [1.5,3.],[.25,.5,.75],[.5,.75],[.5,1.]):
    variant(("refine",2.45,3.,2,3.5,2.,1.,.25,9.),(early_size,.15,.1,late_size),.015,(threshold,weight,2))
# Reduce first-entry risk only if prior equity drawdown is large; leave later
# entry recovery governed by original exposure caps.
for threshold,weight in itertools.product([.5,1.5,2.5,3.5,4.5],[.2,.4,.6,.8]):
    variant(("refine",2.45,3.,2,3.5,2.,1.,.25,9.),(.9,.1,.1,.5),.015,(threshold,weight,1))
def key(name):
    return name.split("__Q_",1)[1].split("_SL300",1)[0]
def gate(fil,side,j,ema,ind,name,losses,cash,ref,sig):
    return p.filter_entry(fil,side,j,ema,ind,name,losses)
def choose(name,losses,cash,ref,sig,ind,side,j):
    sl,rr,late=p.choose(name,losses,cash,ref)
    v=VARIANTS[key(name)]
    if v[0]=="control":return sl,rr,late
    if losses<1:return sl,rr,late
    _,short_sl,long_sl,trigger,act,locked,step,inc,target=v
    new_sl=short_sl if side<0 else long_sl
    if losses>=trigger:late=(act,locked,step,inc)
    else:late=tuple(map(float,p.r.LOCK.split(":")[1:]))
    return new_sl,target/new_sl,late
def size(name,losses,cash,peak,side,fill,stop,sig):
    original=p.exposure(name,losses,cash,peak,side,fill,stop)
    v=ALLOC.get(key(name))
    if v is None:return original
    threshold,weight,until=v
    if losses<until and peak>0 and 100*(1-cash/peak)>=threshold:
        return original*weight
    return original
def pressure_lock(name,pos,cash,ref,losses,favorable,late):
    ordinary=base.delayed_protection_pct(favorable,late)
    v=VARIANTS[key(name)]
    if v[0] not in ("pressure","floor") or ref<=0 or 100*(1-cash/ref)<v[1]:
        return ordinary
    if v[0]=="pressure":
        extra=base.delayed_protection_pct(favorable,tuple(v[2:]))
    else:
        # cash is net of entry fee, but not of the future exit fee.
        side=pos["side"];qty=pos["qty"]
        if qty<=0:return ordinary
        required=ref*(1+v[2]/100.)
        raw=(required-cash+side*qty*pos["entry"])/(qty*(side-base.FEE)*(1-side*base.SLIP))
        if not np.isfinite(raw) or raw<=0:return ordinary
        needed=max(.16,100*side*(raw-pos["raw_entry"])/pos["raw_entry"])
        extra=needed if favorable>=needed+v[3] else None
    if ordinary is None:return extra
    if extra is None:return ordinary
    return max(ordinary,extra)
def factory():
    s=inspect.getsource(base.simulate)
    patches=[
        ("return delayed_protection_pct(raw_favorable,late)",
         "return pressure_lock(name,position,cash,month_reference,losses_this_month,raw_favorable,late)"),
        ("if not check_filter(fil,side,j,ema,ind):",
         "if sig['epoch'] in seen_epochs or not gate(fil,side,j,ema,ind,name,losses_this_month,cash,month_reference,sig):"),
        ("entry=raw_open*(1+side*SLIP)",
         "riskmult,tpR,late=choose(name,losses_this_month,cash,month_reference,sig,ind,side,j)\n                entry=raw_open*(1+side*SLIP)"),
        ("if not (np.isfinite(R) and R>0 and stop>0 and valid_target and R_ST>0):",
         "fraction=size(name,losses_this_month,cash,eq_high,side,entry,stop,sig)\n                if not (np.isfinite(R) and R>0 and stop>0 and valid_target and R_ST>0 and fraction>=.01):"),
        ("qty=cash/entry","qty=(cash/entry)*fraction"),
        ("direction=\"LONG\" if p[\"side\"]==1 else \"SHORT\",entry=p[\"entry\"],",
         "direction=\"LONG\" if p[\"side\"]==1 else \"SHORT\",entry=p[\"entry\"],extra=p.get('extra',False),"),
        ("position=dict(side=side,entry=entry,raw_entry=raw_open,R=R,qty=qty,fee_in=fee_in,",
         "position=dict(side=side,entry=entry,raw_entry=raw_open,R=R,qty=qty,fee_in=fee_in,extra=sig.get('extra',False),")]
    for a,b in patches:
        assert s.count(a)==1,a
        s=s.replace(a,b)
    ns=dict(base.__dict__);ns.update(gate=gate,choose=choose,size=size,pressure_lock=pressure_lock)
    exec(compile(s,"<extra_recovery_simulator>","exec"),ns)
    return ns["simulate"]
def run(i,n):
    sim=factory();df,q=base.read_source("BTCUSD")
    ema,stline,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df);entry.enrich(df,ind,ema)
    prev=np.r_[ind["C"][0],ind["C"][:-1]]
    tr=np.maximum(ind["H"]-ind["L"],np.maximum(abs(ind["H"]-prev),abs(ind["L"]-prev)))
    ind["LONG_ATR"]=pd.Series(tr).ewm(alpha=1/48,adjust=False,min_periods=48).mean().to_numpy()
    primary=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    sigs={}
    cfg=(4,"ATRMIN_0p2","PCT",3.,3.,p.r.LOCK)
    before={};rows=[];months=[];ledgers=[]
    for prof in PROFILES:
        for path in base.PATHS:
            for code,expected in [("X000",FLOOR[prof]),("X001",{"80":(237.0877,9.565),"100":(347.7043,11.735)}[prof])]:
                name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{prof}__Q_{code}_SL300_TP3R"
                x,m,l=sim(df,ema,stline,trend,ind,name,cfg,primary,path)
                assert abs(x["net_return_pct"]-expected[0])<.005 and abs(x["max_floating_drawdown_pct"]-expected[1])<.005 and x["profitable_months"]==21 and x["trades"]==(76 if code=="X000" else 72),(prof,path,code,x)
                if code=="X000":before[prof,path]=m.monthly_return_pct.to_numpy(float)
                if i==0:
                    l["profile"]=prof;l["rule"]=code;ledgers.append(l)
    for j,(code,(tiers,buffer,extra)) in enumerate(RULES.items()):
        if j%n!=i:continue
        signals=primary if extra is None else sigs[extra[0]]
        for prof in PROFILES:
            for path in base.PATHS:
                name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{prof}__Q_{code}_SL300_TP3R"
                x,m,l=sim(df,ema,stline,trend,ind,name,cfg,signals,path)
                now=m.monthly_return_pct.to_numpy(float);old=before[prof,path]
                drops=np.maximum(0,old[old>0]-now[old>0])
                x.update(profile=prof,rule=code,tiers=str(tiers),buffer=buffer,extra_rule=str((VARIANTS[code],ALLOC.get(code))),dec_return=float(now[11]),
                    worst_month=float(now.min()),months_ge1=int((now>=1).sum()),losing_months=int((now<0).sum()),
                    preserved21=int((drops<=.00001).sum()),positive_month_drop=float(drops.sum()),extra_trades=int(l.extra.sum()))
                m["profile"]=prof;m["rule"]=code;rows.append(x);months.append(m)
                if x["profitable_months"]>=22 or (x["profitable_months"]>=21 and x["net_return_pct"]>=FLOOR[prof][0] and x["max_floating_drawdown_pct"]<=FLOOR[prof][1]):
                    l["profile"]=prof;l["rule"]=code;ledgers.append(l)
                print("RESULT",prof,code,path,x["profitable_months"],x["net_return_pct"],x["max_floating_drawdown_pct"],x["extra_trades"],flush=True)
    d=OUT/f"shard_{i}";d.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(d/"summary.csv",index=False)
    pd.concat(months,ignore_index=True).to_csv(d/"monthly.csv",index=False)
    if ledgers:pd.concat(ledgers,ignore_index=True).to_csv(d/"ledger.csv",index=False)
def aggregate(n):
    s=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"summary.csv",dtype={"profile":str}) for i in range(n)],ignore_index=True)
    m=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"monthly.csv",dtype={"profile":str}) for i in range(n)],ignore_index=True)
    s.to_csv(OUT/"summary.csv",index=False);m.to_csv(OUT/"monthly.csv",index=False)
    a=s.groupby(["profile","rule","tiers","buffer","extra_rule"],as_index=False,dropna=False).agg(
      net=("net_return_pct","min"),dd=("max_floating_drawdown_pct","max"),
      winning_months=("profitable_months","min"),months_ge1=("months_ge1","min"),worst_month=("worst_month","min"),dec_return=("dec_return","min"),
      trades=("trades","min"),extra_trades=("extra_trades","min"),preserved21=("preserved21","min"),positive_month_drop=("positive_month_drop","max"))
    a["strict_floor"]=a.apply(lambda r:r.net>=FLOOR[r.profile][0]-.0001 and r.dd<=FLOOR[r.profile][1]+.0001,axis=1)
    a["qual22"]=a.strict_floor&(a.winning_months>=22)
    a["qual21"]=a.strict_floor&(a.winning_months>=21)
    a.to_csv(OUT/"ranked.csv",index=False)
    lines=["# BTCUSD 15m X102 combined recovery and drawdown reserve", "", f"{len(RULES)} rules per profile; {len(s)} completed path simulations.",
           "Jan 2025–Oct 2026, 22 IST months. Repeated in-sample tuning; NOT forward validation.",
           "Strict benchmarks: 80% +271.2282% / 9.543% DD, 100% +404.6151% / 11.708% DD, 21 positive months.",
           "Same primary entries; joint recovery rules and drawdown-aware early exposure reduction. No calendar-specific rule.",
           "Identical 1m OHLC paths, 0.05% taker per side plus GST18%, 0.02% slippage per side. No funding, liquidation or real orderbook.",
           "Minimum simulated notional 1% of equity; not a verified exchange minimum.", ""]
    for prof in PROFILES:
        x=a[a.profile==prof].sort_values(["winning_months","dd","net"],ascending=[False,True,False])
        x.to_csv(OUT/f"profile_{prof}.csv",index=False)
        lines.extend([f"## {prof}% exposure",f"Strict 22-month candidates: {int(x.qual22.sum())}; strict 21+: {int(x.qual21.sum())}.","",
           "### Passing latest benchmarks",x[x.qual21].head(20).to_markdown(index=False),
           "", "### Best monthly consistency regardless of profit/DD",x.head(20).to_markdown(index=False),"","### Best December return (all months still replayed)",x.sort_values(["dec_return","winning_months","net"],ascending=False).head(12).to_markdown(index=False),""])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines[:12]),flush=True)
if __name__=="__main__":
    n=int(os.environ.get("SHARD_COUNT","24"))
    if len(sys.argv)>1 and sys.argv[1]=="aggregate":aggregate(n)
    else:run(int(os.environ.get("SHARD_INDEX","0")),n)
