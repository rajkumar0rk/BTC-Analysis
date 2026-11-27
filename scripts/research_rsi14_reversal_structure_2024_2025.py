"""RSI14 reversal: structural changes, 16 factorial combinations, 2024-25 only."""
import csv,gzip,hashlib,itertools,json,math
from pathlib import Path
import numpy as np
import research_rsi14_reversal_regimes_2025 as regimes
import research_rsi14_reversal_multiple_r_2024 as prior24
import research_rsi14_80_20_2025 as source25
from research_rsi14_reversal_risk_grid_2024_2025 import aggregate
from research_rsi14_reversal_regimes_2025 import FEE,TICK,dt,load_data,entry_sets,pivots,execute,tests,export_bundle
OUT=Path("scratch/rsi14_reversal_structure")
START=END=0

def plans():
    out=[]
    for breakout,trend,struct_sl,struct_tp in itertools.product((False,True),repeat=4):
        key="sweep"+"".join("-"+name for name,on in zip(("breakout","h4","struct-sl","struct-tp"),(breakout,trend,struct_sl,struct_tp)) if on)
        out.append(dict(key=key,breakout=breakout,trend=trend,struct_sl=struct_sl,struct_tp=struct_tp))
    return out

def make_entries(bars,rows,signals):
    base=entry_sets(rows,signals)["liquidity-sweep"]
    known=pivots(rows);C=bars[3];H=bars[1];L=bars[2]
    ends={i:(rows[signals[q+1][0]]["k"] if q+1<len(signals) else len(C)) for q,(i,d) in enumerate(signals)}
    direct=[];confirmed=[]
    for i,j,d,extreme in base:
        k=rows[j]["k"]
        edge=rows[j]["h"] if d==1 else rows[j]["l"]
        sweep_extreme=rows[j]["l"] if d==1 else rows[j]["h"]
        direct.append((i,j,k,d,sweep_extreme))
        until=ends[i]
        hits=np.flatnonzero(d*(C[k:until-1]-edge)>0)
        if len(hits):
            idx=k+int(hits[0])+1
            if idx<until and idx<len(C):
                confirmed.append((i,j,idx,d,sweep_extreme))
    return {False:direct,True:confirmed},known

def cost_rr(ep,stop,target,d):
    loss=d*(ep-stop)+(ep+stop)*FEE
    win=d*(target-ep)-(ep+target)*FEE
    return win/loss if loss>0 else -1

def replay(bars,rows,es,known,config,rec):
    O,H,L,C=bars;trades=[];free=0;empty=np.empty(0,dtype=np.float64)
    rejected={"trend":0,"invalid_stop":0,"structural_target":0,"net_rr":0}
    for i,j,k,d,extreme in es:
        a,b=rows[i],rows[j]
        if a["k"]<free or k<free or k>=len(O):continue
        # k is next 1m open after either the 15m rejection or a completed
        # 1m breakout. Latest closed 15m index is k//15-1.
        z=k//15-1;now=rows[z];ep=float(O[k]);atr=now["atr"]
        if config["trend"] and (now["ema"] is None or d*(now["h4close"]-now["ema"])<=0):
            rejected["trend"]+=1;continue
        if config["struct_sl"]:
            stop=extreme-d*TICK
            sd=d*(ep-stop)
        else:
            if atr is None or atr<=0:continue
            sd=max(TICK,math.ceil(1.5*atr/TICK)*TICK)
            stop=ep-d*sd
        if sd<=0:
            rejected["invalid_stop"]+=1;continue
        if config["struct_tp"]:
            opposing=known[-d][z]
            if opposing is None or d*(opposing[1]-ep)<=0:
                rejected["structural_target"]+=1;continue
            target=math.floor(opposing[1]/TICK)*TICK if d==1 else math.ceil(opposing[1]/TICK)*TICK
            if cost_rr(ep,stop,target,d)<2:
                rejected["net_rr"]+=1;continue
        else:
            target=ep+d*math.ceil(2*sd/TICK)*TICK
        x,xp,reason=execute(O,H,L,C,k,d,sd,target,0,-1,empty)
        free=x+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
        vals={}
        for spec_obj,m in zip(rec.specs,rec.definitions):
            key={"rsi":"r","atr":"atr","ema":"ema","adx":"adx"}.get(spec_obj.base)
            if spec_obj.base=="bollinger":key="upper" if spec_obj.name.endswith("upper") else "lower"
            if key and now[key] is not None:vals[m["id"]]=now[key]
        trades.append(dict(entry_utc=dt(START+k*60).isoformat(),trigger_utc=dt(START+a["k"]*60).isoformat(),
            exit_utc=dt(END if reason==4 else START+x*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),
            stop_price=stop,target_price=target,gross_points=gross,fee_points=fee,net_points=gross-fee,
            assumed_slippage_points=0,entry_reason=config["key"],exit_reason={1:"Initial stop",2:"Fixed target",4:"End of yearly evaluation"}[reason],
            signal_context=dict(rsi14=a["r"],confirmation_rsi14=b["r"],confirmation_utc=dt(START+k*60).isoformat(),
                rejection_utc=dt(START+b["k"]*60).isoformat(),initial_risk_points=sd,swept_extreme=extreme,
                estimated_net_rr=cost_rr(ep,stop,target,d),atr14=atr,h4_ema50=now["ema"]),indicator_values=vals))
    p=[x["net_points"] for x in trades];gain=math.fsum(max(0,n) for n in p);loss=-math.fsum(min(0,n) for n in p)
    months={f"{dt(START).year}-{m:02d}":0. for m in range(dt(START).month,13)};eq=peak=dd=0.
    for tr,n in zip(trades,p):
        months[tr["entry_utc"][:7]]+=n;eq+=n;peak=max(peak,eq);dd=max(dd,peak-eq)
    wins=sum(n>0 for n in p)
    summary=dict(accounting="realized",open_position=None,trades=len(p),net=math.fsum(p),wins=wins,
        win_rate=100*wins/len(p) if p else 0,profit_factor=gain/loss if loss else None,
        realized_drawdown_points=dd,monthly_entry_attribution=months,profitable_months=sum(x>0 for x in months.values()),rejected=rejected)
    params=dict(entry="liquidity-sweep",breakout_1m=config["breakout"],h4_ema50_filter=config["trend"],
        stop_kind="sweep-candle-extreme" if config["struct_sl"] else "atr",stop_atr_multiple=None if config["struct_sl"] else 1.5,
        target_kind="last-confirmed-opposing-pivot" if config["struct_tp"] else "fixed-R",
        target_multiple=None if config["struct_tp"] else 2,minimum_net_rr=2 if config["struct_tp"] else None,
        rsi_period=14,long_threshold=20,short_threshold=80,trading_days="all",signals_while_open="ignored")
    return dict(key=config["key"],name="15M RSI14 Reversal | "+config["key"],parameters=params,summary=summary,trades=trades)

def run():
    global START,END
    tests();assert cost_rr(10000,9900,10200,1)<2
    assert cost_rr(10000,10100,9800,-1)<2
    ps=plans();assert len(ps)==16;by_year={};defs=None;series={}
    for year,start,end,reader in ((2024,prior24.START,prior24.END,prior24.candles_2024),(2025,source25.START,source25.END,source25.candles)):
        START,END=start,end;regimes.START,regimes.END,regimes.candles=start,end,reader
        bars,rows,signals,rec=load_data()
        es,known=make_entries(bars,rows,signals)
        print("ENTRIES",year,{k:len(v) for k,v in es.items()})
        if defs is None:defs=rec.definitions
        else:assert defs==rec.definitions
        for k,v in rec.series.items():series.setdefault(k,[]).extend(v)
        by_year[year]=[replay(bars,rows,es[p["breakout"]],known,p,rec) for p in ps]
        ref=by_year[year][0]
        assert math.isclose(ref["summary"]["net"],3651.574285 if year==2024 else 10112.85959,abs_tol=1e-6),ref["summary"]
    variants=[aggregate([a,b]) for a,b in zip(by_year[2024],by_year[2025])]
    for v in variants:print("RESULT",v["key"],json.dumps(v["summary"],allow_nan=False,separators=(",",":")))
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
    export_bundle(OUT/"backtest.json",family="rsi14-reversal-structure-2024-2025",symbol="BTCUSD",unit="price points",
        start_utc=dt(prior24.START).isoformat(),end_utc=dt(source25.END).isoformat(),execution_timeframe_minutes=1,signal_timeframe_minutes=15,
        costs="0.05% taker each side +18% GST; no Scalper Offer; additional slippage zero; funding/liquidation excluded; 1m Color.",
        variants=variants,indicator_definitions=defs,indicator_series=series,data_provenance=dict(
            manifest_2024=str(prior24.ROOT/"manifest.json"),manifest_2025=str(source25.ROOT/"manifest.json"),
            manifest_sha256_2024=hashlib.sha256((prior24.ROOT/"manifest.json").read_bytes()).hexdigest(),
            manifest_sha256_2025=hashlib.sha256((source25.ROOT/"manifest.json").read_bytes()).hexdigest(),
            selection="16 predeclared combinations of four structural switches; rejection already in baseline; 2024-25 training only; 2026 untouched",
            period="Feb 1 2024 12 UTC through Dec 31 2025; separate yearly replays with indicator reset and year-end accounting close",
            entry="original directional rejection of prior confirmed 2-left/2-right pivot; optional subsequent completed 1m close beyond rejection candle extreme",
            trend="latest completed H4 close relative to EMA50 at entry",
            stop="one tick beyond rejection candle swept extreme, or standard 1.5 ATR",
            target="latest confirmed opposing 15m pivot at entry, only if net planned reward/risk >=2 including fees on entry and exit; otherwise skip; fixed baseline 2R gross",
            attribution="UTC entry month; realized drawdown; no trailing or fee protection"))
    print("TOTAL",len(variants),"PROFITABLE_BOTH",sum(all(y["net"]>0 for y in v["summary"]["years"].values()) for v in variants))
if __name__=="__main__":run()
