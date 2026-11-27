"""Predeclared 72 liquidity sweep experiments, 2024/2025 only, 2026 reserved."""
import csv,gzip,hashlib,json,math
from pathlib import Path
import numpy as np
from numba import njit
import research_rsi14_reversal_regimes_2025 as regimes
import research_rsi14_reversal_multiple_r_2024 as prior24
import research_rsi14_80_20_2025 as source25
from research_rsi14_reversal_regimes_2025 import FEE,TICK,dt,load_data,entry_sets,pivots,execute,tests,export_bundle
OUT=Path("scratch/rsi14_reversal_risk_grid")
START=END=0

def plans():
    def config(entry,s,t,m="fixed",a=0,z=0):
        return dict(key=f"{entry}-sl{s}-tp{t}R-{m}-{a}-{z}",entry=entry,sl=s,tp=t,management=m,activation=a,distance=z)
    result=[config("liquidity-sweep",s,t) for s in (.5,1,1.5,2,2.5,3) for t in (1,1.5,2,2.5,3,4)]
    for t in (2,2.5):
        result.extend(config("liquidity-sweep",1.5,t,"fee",a,0) for a in (.5,1,1.5))
        result.extend(config("liquidity-sweep",1.5,t,"lock",1.5,z) for z in (.25,.5,1))
        result.extend(config("liquidity-sweep",1.5,t,"trail",a,z) for a in (1,1.5,2) for z in (.5,1,1.5))
        result.extend(config(e,1.5,t) for e in ("sweep-breakout","sweep-retest","sweep-depth"))
    assert len(result)==len({p["key"] for p in result})==72
    return result

@njit
def update_stop(ep,d,risk,best,stop,activation,distance,mode):
    if d*(best-ep)<activation*risk:return stop
    if mode==1:
        raw=ep*(1+d*FEE)/(1-d*FEE)
        new=math.ceil(raw/TICK)*TICK if d==1 else math.floor(raw/TICK)*TICK
    elif mode==2:
        raw=ep+d*distance*risk
        new=math.ceil(raw/TICK)*TICK if d==1 else math.floor(raw/TICK)*TICK
    else:
        raw=best-d*distance*risk
        new=math.floor(raw/TICK)*TICK if d==1 else math.ceil(raw/TICK)*TICK
    if d*(best-new)<0:return stop
    return max(stop,new) if d==1 else min(stop,new)

@njit
def managed(O,H,L,C,i,d,risk,target,activation,distance,mode):
    ep=O[i];initial=ep-d*risk;stop=initial;best=ep
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        if d*(o-stop)<=0:return j,o,1 if stop==initial else 5
        if d*(o-target)>=0:return j,target,2
        best=max(best,o) if d==1 else min(best,o)
        stop=update_stop(ep,d,risk,best,stop,activation,distance,mode)
        if c>o or (c==o and o-l<=h-o):seq=(o,l,h,c)
        else:seq=(o,h,l,c)
        for k in range(3):
            a,b=seq[k],seq[k+1]
            if d*(b-a)<0:
                if d*(a-stop)>=0 and d*(b-stop)<=0:return j,stop,1 if stop==initial else 5
            elif d*(b-a)>0:
                if d*(a-target)<=0 and d*(b-target)>=0:return j,target,2
                best=max(best,b) if d==1 else min(best,b)
                stop=update_stop(ep,d,risk,best,stop,activation,distance,mode)
    return len(O)-1,C[-1],4

def managed_tests():
    # Bullish OLHC: adverse movement before activation cannot trigger an unarmed stop.
    o=np.array([10000.]);h=np.array([10600.]);l=np.array([9800.]);c=np.array([10050.])
    j,p,r=managed(o,h,l,c,0,1,500,11500,1,.5,2)
    assert r==5 and p==10250,(p,r)
    # Bearish OHLC: initial stop is hit before later favorable move.
    c=np.array([9900.]);h=np.array([10600.]);l=np.array([9000.])
    j,p,r=managed(o,h,l,c,0,1,500,11500,1,.5,2)
    # first high activates protection, then reversal exits at protected stop
    assert r==5 and p==10250,(p,r)
    o=np.array([10000.]);h=np.array([10100.]);l=np.array([9400.]);c=np.array([9950.])
    j,p,r=managed(o,h,l,c,0,-1,500,8500,1,.5,2)
    assert r==5 and p==9750,(p,r)

def extended_entries(rows,signals):
    base=entry_sets(rows,signals)["liquidity-sweep"]
    out={"liquidity-sweep":base,"sweep-breakout":[],"sweep-retest":[],"sweep-depth":[]}
    known=pivots(rows);ends={i:(signals[q+1][0] if q+1<len(signals) else len(rows)-1) for q,(i,d) in enumerate(signals)}
    for i,j,d,extreme in base:
        p=known[d][i-1] if i else None
        if p is None:continue
        level=p[1];b=rows[j];col="l" if d==1 else "h";edge=b["h"] if d==1 else b["l"]
        if b["atr"] is not None and d*(level-b[col])>=.25*b["atr"]:
            out["sweep-depth"].append((i,j,d,extreme))
        found=set()
        for k in range(j+1,ends[i]):
            x=rows[k]
            if d*(x["c"]-edge)>0 and "sweep-breakout" not in found:
                out["sweep-breakout"].append((i,k,d,extreme));found.add("sweep-breakout")
            if d*(x[col]-level)<=0 and d*(x["c"]-level)>0 and d*(x["c"]-x["o"])>0 and "sweep-retest" not in found:
                out["sweep-retest"].append((i,k,d,extreme));found.add("sweep-retest")
            if len(found)==2:break
    return out

def replay(bars,rows,es,config,rec):
    O,H,L,C=bars;mode=config["entry"];s=config["sl"];t=config["tp"];kind="atr"
    trades=[];free=0;empty=np.empty(0,dtype=np.float64)
    ids={ (d.base,d.name,d.timeframe.seconds):m["id"] for d,m in zip(rec.specs,rec.definitions)}
    # Recorder order is canonical and matches book specifications.
    for i,j,d,extreme in es:
        a,b=rows[i],rows[j];k=b["k"]
        if a["k"]<free or k<free or k>=len(O):continue
        ep=float(O[k]);atr=b["atr"]
        if kind=="atr":
            if atr is None or atr<=0:continue
            sd=max(TICK,math.ceil(s*atr/TICK)*TICK)
            td=max(TICK,math.ceil(t*sd/TICK)*TICK)
        else:
            level=(a["l"] if d==1 else a["h"]) if kind=="signal" else extreme
            stop=level-d*TICK;sd=d*(ep-stop)
            if sd<=0:continue
            td=max(TICK,math.ceil(t*sd/TICK)*TICK)
        target=ep+d*td
        if config["management"]=="fixed":
            x,xp,reason=execute(O,H,L,C,k,d,sd,target,0,-1,empty)
        else:
            x,xp,reason=managed(O,H,L,C,k,d,sd,target,config["activation"],config["distance"],{"fee":1,"lock":2,"trail":3}[config["management"]])
        free=x+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
        vals={}
        for spec_obj,m in zip(rec.specs,rec.definitions):
            key={"rsi":"r","atr":"atr","ema":"ema","adx":"adx"}.get(spec_obj.base)
            if spec_obj.base=="bollinger":key="upper" if spec_obj.name.endswith("upper") else "lower"
            if key and b[key] is not None:vals[m["id"]]=b[key]
        trades.append(dict(entry_utc=dt(START+k*60).isoformat(),trigger_utc=dt(START+a["k"]*60).isoformat(),
            exit_utc=dt(END if reason==4 else START+x*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),
            stop_price=ep-d*sd,target_price=target,gross_points=gross,fee_points=fee,net_points=gross-fee,
            assumed_slippage_points=0,entry_reason=mode,exit_reason={1:"Initial stop",2:"Fixed target",4:"End of yearly evaluation",5:"Managed stop"}[reason],
            signal_context=dict(rsi14=a["r"],confirmation_rsi14=b["r"],confirmation_utc=dt(START+k*60).isoformat(),
                initial_risk_points=sd,setup_extreme=extreme,atr14=atr,adx14=b["adx"],h4_ema50=b["ema"]),indicator_values=vals))
    p=[x["net_points"] for x in trades];gain=math.fsum(max(0,n) for n in p);loss=-math.fsum(min(0,n) for n in p)
    months={f"{dt(START).year}-{m:02d}":0. for m in range(dt(START).month,13)};eq=peak=dd=0.
    for tr,n in zip(trades,p):
        months[tr["entry_utc"][:7]]+=n;eq+=n;peak=max(peak,eq);dd=max(dd,peak-eq)
    wins=sum(n>0 for n in p)
    summary=dict(accounting="realized",open_position=None,trades=len(p),net=math.fsum(p),wins=wins,
        win_rate=100*wins/len(p) if p else 0,profit_factor=gain/loss if loss else None,
        realized_drawdown_points=dd,monthly_entry_attribution=months,profitable_months=sum(x>0 for x in months.values()))
    key=config["key"]
    params=dict(entry=mode,stop_kind=kind,stop_atr_multiple=s if kind=="atr" else None,target_multiple=t,
        target_unit="R",management=config["management"],activation_R=config["activation"],distance_or_lock_R=config["distance"],rsi_period=14,long_threshold=20,short_threshold=80,
        trading_days="all",signals_while_open="ignored")
    return dict(key=key,name="15M RSI14 Reversal | "+key,parameters=params,summary=summary,trades=trades)



def aggregate(vs):
    trades=[t for v in vs for t in v["trades"]]
    p=[t["net_points"] for t in trades];gain=math.fsum(max(0,x) for x in p);loss=-math.fsum(min(0,x) for x in p)
    eq=peak=dd=0.
    for x in p: eq+=x;peak=max(peak,eq);dd=max(dd,peak-eq)
    months={k:x for v in vs for k,x in v["summary"]["monthly_entry_attribution"].items()}
    wins=sum(x>0 for x in p)
    summary=dict(accounting="realized",open_position=None,trades=len(p),net=math.fsum(p),wins=wins,win_rate=100*wins/len(p) if p else 0,profit_factor=gain/loss if loss else None,realized_drawdown_points=dd,monthly_entry_attribution=months,profitable_months=sum(x>0 for x in months.values()))
    summary["years"]={str(y):v["summary"] for y,v in zip((2024,2025),vs)}
    return dict(key=vs[0]["key"],name=vs[0]["name"],parameters=vs[0]["parameters"],summary=summary,trades=trades)

def run():
    global START,END
    tests();managed_tests();ps=plans();by_year={};defs=None;series={}
    for year,start,end,reader in ((2024,prior24.START,prior24.END,prior24.candles_2024),(2025,source25.START,source25.END,source25.candles)):
        START,END=start,end;regimes.START,regimes.END,regimes.candles=start,end,reader
        bars,rows,signals,rec=load_data()
        es=extended_entries(rows,signals)
        print("ENTRIES",year,{k:len(v) for k,v in es.items()})
        if defs is None:defs=rec.definitions
        else:assert defs==rec.definitions
        for k,v in rec.series.items():series.setdefault(k,[]).extend(v)
        by_year[year]=[replay(bars,rows,es[p["entry"]],p,rec) for p in ps]
        ref=next(v for v,p in zip(by_year[year],ps) if p["entry"]=="liquidity-sweep" and p["sl"]==1.5 and p["tp"]==2 and p["management"]=="fixed")
        assert math.isclose(ref["summary"]["net"],3651.574285 if year==2024 else 10112.85959,abs_tol=1e-6),ref["summary"]
    variants=[aggregate([a,b]) for a,b in zip(by_year[2024],by_year[2025])]
    for v in variants:
        print("RESULT",v["key"],json.dumps(v["summary"],allow_nan=False,separators=(",",":")))
    OUT.mkdir(parents=True,exist_ok=True)
    with gzip.open(OUT/"all_ledgers.json.gz","wt") as f:json.dump(variants,f,allow_nan=False,separators=(",",":"))
    results=[]
    for v in variants:
        s=v["summary"];row=dict(key=v["key"],**v["parameters"],**{k:x for k,x in s.items() if k not in ("monthly_entry_attribution","years")},**s["monthly_entry_attribution"])
        for y,ys in s["years"].items():
            for k in ("net","profitable_months","profit_factor","realized_drawdown_points","trades"):row[y+"_"+k]=ys[k]
        results.append(row)
    with (OUT/"all_results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    selected={}
    for key in ("fixed","fee","lock","trail"):
        group=[v for v in variants if v["parameters"]["management"]==key]
        for v in (max(group,key=lambda v:(v["summary"]["profitable_months"],v["summary"]["net"])),max(group,key=lambda v:v["summary"]["net"])):
            selected[v["key"]]=v
    for entry in ("sweep-breakout","sweep-retest","sweep-depth"):
        v=max((v for v in variants if v["parameters"]["entry"]==entry),key=lambda v:(v["summary"]["profitable_months"],v["summary"]["net"]))
        selected[v["key"]]=v
    export_bundle(OUT/"backtest.json",family="rsi14-reversal-risk-grid-2024-2025",symbol="BTCUSD",unit="price points",
        start_utc=dt(prior24.START).isoformat(),end_utc=dt(source25.END).isoformat(),execution_timeframe_minutes=1,signal_timeframe_minutes=15,
        costs="0.05% taker each side +18% GST; no Scalper Offer; additional slippage zero; funding/liquidation excluded; 1m Color.",
        variants=list(selected.values()),indicator_definitions=defs,indicator_series=series,data_provenance=dict(
            manifest_2024=str(prior24.ROOT/"manifest.json"),manifest_2025=str(source25.ROOT/"manifest.json"),
            manifest_sha256_2024=hashlib.sha256((prior24.ROOT/"manifest.json").read_bytes()).hexdigest(),
            manifest_sha256_2025=hashlib.sha256((source25.ROOT/"manifest.json").read_bytes()).hexdigest(),
            selection="72 predeclared variants; 36 SL/TP grid, 30 exit-management experiments, 6 entry variants; 2024-25 training only; 2026 untouched",
            period="Feb 1 2024 12 UTC through Dec 31 2025; separate yearly replays with indicator reset and year-end accounting close",
            fee_protection="exact fee-adjusted break-even rounded favorably to tick, only when price reaches it",
            lock="activation at 1.5R, gross lock distance; trailing measured from favorable extreme; fixed TP remains",
            entry="baseline liquidity sweep; breakout/retest use subsequent completed 15m close; depth >=0.25 ATR",
            attribution="UTC entry month; realized drawdown; all cases archived, leaders submitted"))
    print("TOTAL",len(variants),"PROFITABLE_BOTH",sum(all(y["net"]>0 for y in v["summary"]["years"].values()) for v in variants),"SUBMITTED",len(selected))
if __name__=="__main__":run()
