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
OUT=Path("analysis/btc15m_single_position_management_20261124")
FLOOR={"80":(273.2603,9.542),"100":(407.8388,11.707)}
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
VARIANTS={"X000":("refine",2.45,3.,2,3.25,2.,1.,.25,9.),"X001":("control",)}
MANAGE={}
BASE=VARIANTS["X000"]
def variant(spec,tiers=(.9,.15,.1,.05)):
    add(tiers,.015,None)
    code=f"X{len(RULES)-1:03d}"
    VARIANTS[code]=BASE
    MANAGE[code]=spec
# Each family is independent. Same one-position, one-ST-cycle entry policy.
# Scale-in: start with a fraction of the original allowed quantity, add
# the remainder only after confirmation at a subsequent observed minute open.
for fraction,trigger,scope in itertools.product([.25,.5,.75],[.25,.5,1.,2.],["all","recovery"]):
    variant(("scale_in",fraction,trigger,scope))
# Partial profit: reduce once at an observed subsequent minute open.
for fraction,trigger,scope in itertools.product([.25,.5,.75],[1.,2.,3.,4.,6.],["all","recovery"]):
    variant(("partial_tp",fraction,trigger,scope))
# Time-conditioned risk reduction: close part of an underperforming position.
for fraction,hours,adverse in itertools.product([.25,.5,.75],[12,24,48,72],[0.,.75]):
    variant(("time_reduce",fraction,hours,adverse))
# Confirmed prior-bar swing range; only tighten the original stop,
# while retaining the original absolute target.
for n,buffer,floor in itertools.product([8,16,32,64],[0.,.25,.5],[1.5,2.]):
    variant(("structure",n,buffer,floor))
# Dynamic exposure: one reduction at an adverse move and one possible
# restoration after a subsequent recovery. No second signal or position.
for fraction,adverse,confirm in itertools.product([.25,.5,.75],[.75,1.25,1.75],[0.,.5,1.]):
    variant(("dynamic",fraction,adverse,confirm))
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
    return p.exposure(name,losses,cash,peak,side,fill,stop)
def pressure_lock(name,pos,cash,ref,losses,favorable,late):
    return base.delayed_protection_pct(favorable,late)
def structure_stop(name,side,entry,stop,j,ind):
    v=MANAGE.get(key(name))
    if v is None or v[0]!="structure":return stop
    _,n,buffer,floor=v
    if j+1<n:return stop
    level=float(np.min(ind["L"][j-n+1:j+1])) if side>0 else float(np.max(ind["H"][j-n+1:j+1]))
    candidate=level*(1-side*buffer/100)
    # Do not use a swing stop beyond the current entry or below the min distance.
    candidate=min(candidate,entry*(1-floor/100)) if side>0 else max(candidate,entry*(1+floor/100))
    return max(stop,candidate) if side>0 else min(stop,candidate)
def management_initial(name,planned,losses):
    v=MANAGE.get(key(name))
    if v is not None and v[0]=="scale_in" and (v[3]=="all" or losses>=1):
        return planned*v[1]
    return planned
def manage_open(name,pos,raw,sec,cash,peak):
    # All partial fills use a subsequent minute open, not a future wick.
    # Net cash excludes entry fees already debited; the complete cycle ledger
    # aggregates partial realization and all entry/exit fees exactly once.
    v=MANAGE.get(key(name))
    if v is None or v[0]=="structure" or sec<=pos["entry_sec"]:return cash
    mode=v[0];side=pos["side"];qty=pos["qty"]
    move=100*side*(raw-pos["raw_entry"])/pos["raw_entry"]
    if side*(raw-pos["stop"])<=0 or side*(raw-pos["target"])>=0:return cash
    reduce=False;restore=False
    if mode=="scale_in":
        restore=(pos["management_stage"]==0 and qty<pos["planned_qty"]*.999999 and move>=v[2])
    elif mode=="partial_tp":
        reduce=(pos["management_stage"]==0 and (v[3]=="all" or pos["entry_losses"]>=1) and move>=v[2])
    elif mode=="time_reduce":
        reduce=(pos["management_stage"]==0 and sec-pos["entry_sec"]>=v[2]*3600 and move<=-v[3])
    elif mode=="dynamic":
        reduce=(pos["management_stage"]==0 and move<=-v[2])
        restore=(pos["management_stage"]==1 and move>=v[3])
    if reduce:
        q=qty*v[1]
        fill=raw*(1-side*base.SLIP)
        gross=side*q*(fill-pos["entry"]);fee=base.FEE*q*fill
        pos["qty"]-=q
        pos["partial_gross"]+=gross;pos["partial_exit_fee"]+=fee
        pos["partial_exits"]+=1;pos["management_stage"]=1
        return cash+gross-fee
    if not restore:return cash
    # No pyramiding beyond original allowed quantity. Additional units
    # are bounded by the current mark equity and projected stop equity.
    fill=raw*(1+side*base.SLIP)
    exit_fill=pos["stop"]*(1-side*base.SLIP)
    current_stop_equity=cash+side*qty*(exit_fill-pos["entry"])-base.FEE*qty*exit_fill
    prof=name.split("__P_",1)[1].split("__Q_",1)[0]
    ddlim={"80":.09731,"100":.11929}[prof]
    buffer=.015
    loss=side*(fill-exit_fill)+base.FEE*(fill+exit_fill)+buffer*fill
    room=current_stop_equity-peak*(1-ddlim)-buffer*qty*pos["entry"]
    maxrisk=max(0.,room/max(loss,1e-9))
    proxy=raw*(1-side*base.SLIP)
    equity=cash+side*qty*(proxy-pos["entry"])-base.FEE*qty*proxy
    maxnotional=max(0.,PROFILES[prof]["scale"]*equity/fill-qty)
    q=min(pos["planned_qty"]-qty,maxrisk,maxnotional)
    if q<=0 or q*fill<.01*max(equity,1e-9):return cash
    fee=base.FEE*q*fill
    pos["entry"]=(pos["entry"]*qty+fill*q)/(qty+q)
    pos["qty"]=qty+q;pos["fee_in"]+=fee;pos["partial_entries"]+=1
    pos["management_stage"]=2
    return cash-fee
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
        ("qty=cash/entry","planned_qty=(cash/entry)*fraction\n                    qty=management_initial(name,planned_qty,losses_this_month)"),
        ("stop=entry-side*R","stop=structure_stop(name,side,entry,entry-side*R,j,ind)\n                R=side*(entry-stop)"),
        ("        # An overnight/minute opening price may already cross a rung.","        if position is not None and has_management(name):\n            mark(raw_open)\n            cash=manage_open(name,position,raw_open,sec,cash,eq_high)\n        # An overnight/minute opening price may already cross a rung."),
        ("net=gross-fee_out-p[\"fee_in\"]","net=gross+p.get('partial_gross',0.)-fee_out-p.get('partial_exit_fee',0.)-p[\"fee_in\"]"),
        ("fee_gst_usd=p[\"fee_in\"]+fee_out,","fee_gst_usd=p[\"fee_in\"]+fee_out+p.get('partial_exit_fee',0.),partial_entries=p.get('partial_entries',0),partial_exits=p.get('partial_exits',0),"),
        ("direction=\"LONG\" if p[\"side\"]==1 else \"SHORT\",entry=p[\"entry\"],",
         "direction=\"LONG\" if p[\"side\"]==1 else \"SHORT\",entry=p[\"entry\"],extra=p.get('extra',False),"),
        ("position=dict(side=side,entry=entry,raw_entry=raw_open,R=R,qty=qty,fee_in=fee_in,",
         "position=dict(side=side,entry=entry,raw_entry=raw_open,R=R,qty=qty,fee_in=fee_in,extra=sig.get('extra',False),planned_qty=planned_qty,entry_losses=losses_this_month,management_stage=0,partial_gross=0.,partial_exit_fee=0.,partial_entries=0,partial_exits=0,")]
    for a,b in patches:
        assert s.count(a)==1,a
        s=s.replace(a,b)
    ns=dict(base.__dict__);ns.update(gate=gate,choose=choose,size=size,pressure_lock=pressure_lock,structure_stop=structure_stop,management_initial=management_initial,manage_open=manage_open,has_management=lambda name: key(name) in MANAGE and MANAGE[key(name)][0]!="structure")
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
                x.update(profile=prof,rule=code,tiers=str(tiers),buffer=buffer,extra_rule=str(MANAGE.get(code)),partial_entries=int(l.partial_entries.sum()),partial_exits=int(l.partial_exits.sum()),dec_return=float(now[11]),
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
      trades=("trades","min"),extra_trades=("extra_trades","min"),partial_entries=("partial_entries","min"),partial_exits=("partial_exits","min"),preserved21=("preserved21","min"),positive_month_drop=("positive_month_drop","max"))
    a["strict_floor"]=a.apply(lambda r:r.net>=FLOOR[r.profile][0]-.0001 and r.dd<=FLOOR[r.profile][1]+.0001,axis=1)
    a["qual22"]=a.strict_floor&(a.winning_months>=22)
    a["qual21"]=a.strict_floor&(a.winning_months>=21)
    a.to_csv(OUT/"ranked.csv",index=False)
    lines=["# BTCUSD 15m single-strategy position management", "", f"{len(RULES)} rules per profile; {len(s)} completed path simulations.",
           "Jan 2025–Oct 2026, 22 IST months. Repeated in-sample tuning; NOT forward validation.",
           "Strict benchmarks: 80% +273.2603% / 9.542% DD, 100% +407.8388% / 11.707% DD, 21 positive months.",
           "Same primary entries; five separate position-management families. Partial fills use subsequent observed minute opens, with fees and weighted cost basis; no new entry signals or calendar-specific rules.",
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
