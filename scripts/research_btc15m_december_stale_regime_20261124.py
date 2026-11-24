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
OUT=Path("analysis/btc15m_december_stale_regime_20261124")
FLOOR={"80":(239.7694,9.570),"100":(348.5401,11.744)}
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
VARIANTS={"X000":("control",),"X001":("control",)}
def variant(spec,alternate=False):
    add((.8,.1,.1,.1) if alternate else (.9,.15,.1,.05),.012 if alternate else .015,None)
    VARIANTS[f"X{len(RULES)-1:03d}"]=spec
# Stale exits on completed 15-minute bars; no calendar-specific rules.
for mode,hours,threshold in itertools.product(
    ["stale","opposite"],[6,12,24,48,72,120,168],[0.,.5,1.]):
    variant((mode,hours,threshold))
# Only exit when both underperforming and below directional EMA on the latest closed bar.
for hours,threshold in itertools.product([12,24,48,72,120],[0.,.5,1.]):
    variant(("stale_ema",hours,threshold))
# Prevent entries fighting a broader trend, using fully closed 15m candles.
for lookback in [32,64,96,192,384]:
    for state in ["first","recovery","all"]:
        variant(("ema_gate",lookback,state))
# Require some directional efficiency rather than a sideways market.
for lookback,threshold,state in itertools.product([32,96],[.08,.15,.25],["first","recovery","all"]):
    variant(("er_gate",lookback,threshold,state))
# Limited combinations of causal trend confirmation and stale exits.
for h,lb in itertools.product([24,48,72,120],[96,384]):
    variant(("combo",h,0.,lb))
for h in [24,48,72,120]:
    variant(("stale",h,0.),True)
def key(name):
    return name.split("__Q_",1)[1].split("_SL300",1)[0]
def make_extra(df,ema,trend,valid,mode,primary):
    if mode=="combined12":
        candidate=base.make_signals(df,ema,trend,valid,"combined",12)[0]
    else:
        hi=df.high.to_numpy(float).reshape(-1,base.TF).max(axis=1)
        lo=df.low.to_numpy(float).reshape(-1,base.TF).min(axis=1)
        cl=df.close.to_numpy(float).reshape(-1,base.TF)[:,-1]
        candidate={};active=0;epoch=0
        n=12 if mode=="breakout12" else 24
        for j in range(101,len(trend)-1):
            if not valid[j] or not valid[j-1] or not np.isfinite(ema[j-1]) or trend[j]==0:continue
            side=int(trend[j])
            if side!=active:
                active=side;epoch+=1;continue
            aligned=side*(cl[j]-ema[j-1])>0 and side*(cl[j]-ema[j])>0
            if not aligned:continue
            if mode=="repeat_touch":
                hit=lo[j]<=ema[j-1]<=hi[j]
            else:
                hit=cl[j]>hi[j-n:j].max() if side==1 else cl[j]<lo[j-n:j].min()
            if hit:candidate[(j+1)*base.TF]=dict(epoch=epoch,side=side,signal_close_bar=j)
        # Ensure actual ST cycle identities match the original entry generator.
        for i,sig in primary.items():
            if i in candidate:
                assert candidate[i]["epoch"]==sig["epoch"],(mode,i)
    merged={i:dict(s,extra=True) for i,s in candidate.items()}
    merged.update(primary)
    return merged
def enrich_regime(ind):
    c=pd.Series(ind["C"],dtype=float)
    for n in [32,64,96,192,384]:
        ind[f"E{n}"]=c.ewm(span=n,adjust=False,min_periods=n).mean().to_numpy()
    for n in [32,96]:
        den=c.diff().abs().rolling(n).sum()
        ind[f"ER{n}"]=(c.diff(n)/den.replace(0,np.nan)).to_numpy()
def gate(fil,side,j,ema,ind,name,losses,cash,ref,sig):
    if not p.filter_entry(fil,side,j,ema,ind,name,losses):return False
    v=VARIANTS[key(name)]
    if v[0]=="ema_gate":
        _,n,state=v
        if state=="all" or (state=="first" and losses==0) or (state=="recovery" and losses>=1):
            return bool(side*(ind["C"][j]-ind[f"E{n}"][j])>0)
    if v[0]=="er_gate":
        _,n,threshold,state=v
        if state=="all" or (state=="first" and losses==0) or (state=="recovery" and losses>=1):
            return bool(side*ind[f"ER{n}"][j]>=threshold)
    if v[0]=="combo" and losses>=1:
        return bool(side*(ind["C"][j]-ind[f"E{v[3]}"][j])>0)
    return True
def stale_exit(name,pos,sec,raw,done,trend,ema,ind):
    v=VARIANTS[key(name)]
    if v[0] not in ("stale","opposite","stale_ema","combo"):return False
    if (sec-pos["entry_sec"])<v[1]*3600:return False
    # Only exit still-unprotected, underperforming positions; actual next-minute open.
    if pos["active"]:return False
    side=pos["side"]
    move=100*side*(raw-pos["raw_entry"])/pos["raw_entry"]
    if move>v[2]:return False
    if v[0]=="opposite" and trend[done]==side:return False
    if v[0]=="stale_ema" and side*(ind["C"][done]-ema[done])>=0:return False
    return True
def choose(name,losses,cash,ref,sig):
    if not sig.get("extra",False):return p.choose(name,losses,cash,ref)
    _,_,sl,tp,_=EXTRA[key(name)]
    return sl,tp/sl,None
def size(name,losses,cash,peak,side,fill,stop,sig):
    if not sig.get("extra",False):
        return p.exposure(name,losses,cash,peak,side,fill,stop)
    prof=name.split("__P_",1)[1].split("__Q_",1)[0]
    _,_,_,_,maxfrac=EXTRA[key(name)]
    _,buff,_=RULES[key(name)]
    ddlim={"80":.09731,"100":.11929}[prof]
    exit_fill=stop*(1-side*base.SLIP)
    loss_per_unit=side*(fill-exit_fill)+base.FEE*(fill+exit_fill)+buff*fill
    headroom=max(0.,cash-peak*(1-ddlim))
    risk_fraction=headroom*fill/(max(cash,1e-9)*max(loss_per_unit,1e-9))
    return min(PROFILES[prof]["scale"]*maxfrac,risk_fraction)
def factory():
    s=inspect.getsource(base.simulate)
    patches=[
        ("        if i in signal_indices and position is not None:",
         "        if position is not None and i%TF==0 and stale_exit(name,position,sec,raw_open,done,trend,ema,ind):\n            mark(raw_open)\n            close_trade(raw_open,sec,\"STALE_EXIT\")\n        if i in signal_indices and position is not None:"),
        ("if not check_filter(fil,side,j,ema,ind):",
         "if sig['epoch'] in seen_epochs or not gate(fil,side,j,ema,ind,name,losses_this_month,cash,month_reference,sig):"),
        ("entry=raw_open*(1+side*SLIP)",
         "riskmult,tpR,late=choose(name,losses_this_month,cash,month_reference,sig)\n                entry=raw_open*(1+side*SLIP)"),
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
    ns=dict(base.__dict__);ns.update(gate=gate,choose=choose,size=size,stale_exit=stale_exit)
    exec(compile(s,"<extra_recovery_simulator>","exec"),ns)
    return ns["simulate"]
def run(i,n):
    sim=factory();df,q=base.read_source("BTCUSD")
    ema,stline,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df);entry.enrich(df,ind,ema);enrich_regime(ind)
    primary=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    sigs={}
    cfg=(4,"ATRMIN_0p2","PCT",3.,3.,p.r.LOCK)
    before={};rows=[];months=[];ledgers=[]
    for prof in PROFILES:
        for path in base.PATHS:
            for code,expected in [("X000",FLOOR[prof]),("X001",{"80":(237.0877,9.565),"100":(347.7043,11.735)}[prof])]:
                name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{prof}__Q_{code}_SL300_TP3R"
                x,m,l=sim(df,ema,stline,trend,ind,name,cfg,primary,path)
                assert abs(x["net_return_pct"]-expected[0])<.005 and abs(x["max_floating_drawdown_pct"]-expected[1])<.005 and x["profitable_months"]==21 and x["trades"]==72,(prof,path,code,x)
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
                x.update(profile=prof,rule=code,tiers=str(tiers),buffer=buffer,extra_rule=str(VARIANTS[code]),
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
      winning_months=("profitable_months","min"),months_ge1=("months_ge1","min"),worst_month=("worst_month","min"),
      trades=("trades","min"),extra_trades=("extra_trades","min"),preserved21=("preserved21","min"),positive_month_drop=("positive_month_drop","max"))
    a["strict_floor"]=a.apply(lambda r:r.net>=FLOOR[r.profile][0]-.0001 and r.dd<=FLOOR[r.profile][1]+.0001,axis=1)
    a["qual22"]=a.strict_floor&(a.winning_months>=22)
    a["qual21"]=a.strict_floor&(a.winning_months>=21)
    a.to_csv(OUT/"ranked.csv",index=False)
    lines=["# BTCUSD 15m stale exits and causal regime filters", "", f"{len(RULES)} rules per profile; {len(s)} completed path simulations.",
           "Jan 2025–Oct 2026, 22 IST months. Repeated in-sample tuning; NOT forward validation.",
           "Strict benchmarks: 80% +239.7694% / 9.570% DD, 100% +348.5401% / 11.744% DD, 21 positive months.",
           "Same primary entries, optional fully closed-bar directional regime gates and time-based underperformance exits. No month-specific rule.",
           "Identical 1m OHLC paths, 0.05% taker per side plus GST18%, 0.02% slippage per side. No funding, liquidation or real orderbook.",
           "Minimum simulated notional 1% of equity; not a verified exchange minimum.", ""]
    for prof in PROFILES:
        x=a[a.profile==prof].sort_values(["winning_months","dd","net"],ascending=[False,True,False])
        x.to_csv(OUT/f"profile_{prof}.csv",index=False)
        lines.extend([f"## {prof}% exposure",f"Strict 22-month candidates: {int(x.qual22.sum())}; strict 21+: {int(x.qual21.sum())}.","",
           "### Passing latest benchmarks",x[x.qual21].head(20).to_markdown(index=False),
           "", "### Best monthly consistency regardless of profit/DD",x.head(20).to_markdown(index=False),""])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines[:12]),flush=True)
if __name__=="__main__":
    n=int(os.environ.get("SHARD_COUNT","24"))
    if len(sys.argv)>1 and sys.argv[1]=="aggregate":aggregate(n)
    else:run(int(os.environ.get("SHARD_INDEX","0")),n)
