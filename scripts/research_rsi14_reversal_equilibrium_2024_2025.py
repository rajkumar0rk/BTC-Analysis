"""Equilibrium exit comparison; fixed entry definitions, no new parameter grid."""
import csv,gzip,hashlib,json,math
from pathlib import Path
import numpy as np
import research_rsi14_reversal_regimes_2025 as regimes
import research_rsi14_reversal_multiple_r_2024 as prior24
import research_rsi14_80_20_2025 as source25
import research_rsi14_reversal_risk_grid_2024_2025 as grid
import research_rsi14_reversal_confirmation_2024_2025 as conf
from research_rsi14_reversal_regimes_2025 import dt,execute,FEE,TICK,export_bundle
OUT=Path("scratch/rsi14_reversal_equilibrium")

def levels(rows):
    ema=np.full(len(rows)+1,np.nan);sma=ema.copy();rsi=ema.copy()
    for j,b in enumerate(rows,1):
        if b["r"] is not None:rsi[j]=b["r"]
        if j>=20:
            sma[j]=math.fsum(x["c"] for x in rows[j-20:j])/20
            ema[j]=sma[j] if j==20 else ema[j-1]+(2/21)*(b["c"]-ema[j-1])
    return ema,sma,rsi

def risk_metrics(trades,months):
    values=[t["net_points"]/abs(t["entry_price"]-t["stop_price"]) for t in trades]
    rm={m:0. for m in months};eq=peak=dd=0.
    for t,r in zip(trades,values):
        rm[t["entry_utc"][:7]]+=r;eq+=r;peak=max(peak,eq);dd=max(dd,peak-eq)
    gain=math.fsum(max(0,r) for r in values);loss=-math.fsum(min(0,r) for r in values)
    return dict(net_R=math.fsum(values),avg_R=math.fsum(values)/len(values) if values else 0,
        pf_R=gain/loss if loss else None,drawdown_R=dd,monthly_R=rm,profitable_R_months=sum(r>0 for r in rm.values()))

def dynamic_replay(bars,rows,es,key,mode,rec,start,end,ema,sma,rsi):
    O,H,L,C=bars;free=0;trades=[];skipped=0
    level=ema if mode=="ema20" else sma
    hits={d:np.flatnonzero(d*(rsi-50)>=0)*15 for d in (1,-1)}
    for i,j,d,extreme in es:
        a,b=rows[i],rows[j];k=b["k"]
        if a["k"]<free or k<free or k>=len(O):continue
        ep=float(O[k]);atr=b["atr"]
        if atr is None or atr<=0:continue
        sd=max(TICK,math.ceil(1.5*atr/TICK)*TICK)
        mid=-1
        if mode=="rsi50":
            if not np.isfinite(rsi[k//15]) or d*(rsi[k//15]-50)>=0:
                skipped+=1;continue
            idx=np.searchsorted(hits[d],k,side="right")
            if idx<len(hits[d]):mid=int(hits[d][idx])
            x,xp,reason=execute(O,H,L,C,k,d,sd,0,1,mid,ema)
            initial_target=None
        else:
            initial_target=float(level[k//15])
            if not np.isfinite(initial_target) or d*(initial_target-ep)<=0:
                skipped+=1;continue
            x,xp,reason=execute(O,H,L,C,k,d,sd,0,2,-1,level)
        free=x+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
        vals={}
        for sp,m in zip(rec.specs,rec.definitions):
            f={"rsi":"r","atr":"atr","ema":"ema","adx":"adx"}.get(sp.base)
            if sp.base=="bollinger":f="upper" if sp.name.endswith("upper") else "lower"
            if f and b[f] is not None:vals[m["id"]]=b[f]
        vals.update(reversal_ema20=float(ema[k//15]),reversal_bb_middle=float(sma[k//15]))
        trades.append(dict(entry_utc=dt(start+k*60).isoformat(),trigger_utc=dt(start+a["k"]*60).isoformat(),
            exit_utc=dt(end if reason==4 else start+x*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),
            stop_price=ep-d*sd,target_price=initial_target,gross_points=gross,fee_points=fee,net_points=gross-fee,assumed_slippage_points=0,
            entry_reason="liquidity-sweep",exit_reason={1:"Initial stop",2:"Equilibrium price reached",3:"RSI50 reached",4:"End of yearly evaluation"}[reason],
            signal_context=dict(rsi14=a["r"],confirmation_rsi14=b["r"],confirmation_utc=dt(start+k*60).isoformat(),initial_risk_points=sd,
                setup_extreme=extreme,atr14=atr,adx14=b["adx"],h4_ema50=b["ema"]),indicator_values=vals))
    p=[t["net_points"] for t in trades];gain=math.fsum(max(0,x) for x in p);loss=-math.fsum(min(0,x) for x in p)
    months={f"{dt(start).year}-{m:02d}":0. for m in range(dt(start).month,13)};eq=peak=dd=0.
    for t,x in zip(trades,p):
        months[t["entry_utc"][:7]]+=x;eq+=x;peak=max(peak,eq);dd=max(dd,peak-eq)
    wins=sum(x>0 for x in p)
    s=dict(accounting="realized",open_position=None,trades=len(p),net=math.fsum(p),wins=wins,win_rate=100*wins/len(p) if p else 0,
        profit_factor=gain/loss if loss else None,realized_drawdown_points=dd,monthly_entry_attribution=months,profitable_months=sum(x>0 for x in months.values()),already_at_equilibrium_skips=skipped)
    return dict(key=key,name="RSI reversal equilibrium | "+key,parameters=dict(entry="liquidity-sweep",stop_atr_multiple=1.5,exit=mode,rsi_period=14,long_threshold=20,short_threshold=80),summary=s,trades=trades)

def tests():
    regimes.tests();conf.confirmation_tests()
    a,b,c=levels([{"c":float(j),"r":25} for j in range(1,22)])
    assert np.isnan(a[19]) and a[20]==b[20]==10.5 and a[21]==b[21]==11.5 and c[20]==25
    # stop takes precedence at the open; dynamic equilibrium updated at the minute boundary.
    O=np.array([100.,101.]);H=np.array([103.,103.]);L=np.array([99.,100.]);C=np.array([102.,102.])
    assert execute(O,H,L,C,0,1,10,0,2,-1,np.array([102.]))==(0,102.,2)
    assert execute(O,H,L,C,0,1,10,0,1,1,np.array([102.]))==(1,101.,3)

def run():
    tests()
    configs=((15,False,"15m-baseline"),(60,False,"1h-sweep"),(60,True,"1h-sweep-contraction"))
    modes=("2R","rsi50","ema20","bb-middle")
    expected={2024:(3651.574285,1797.47779,630.50891),2025:(10112.85959,7121.862695,8625.62726)}
    by_year={};defs=None;series={}
    for year,start,end,reader in ((2024,prior24.START,prior24.END,prior24.candles_2024),(2025,source25.START,source25.END,source25.candles)):
        regimes.START,regimes.END,regimes.candles=start,end,reader;grid.START,grid.END=start,end
        bars,rows,signals,rec=regimes.load_data()
        vals15=[r["r"] for r in rows];vals60=conf.hourly_rsi(rows,start)
        es={15:conf.make_entries(rows,signals,vals15),60:conf.make_entries(rows,conf.threshold_signals(vals60),vals60)}
        ema,sma,rsi=levels(rows)
        current=list(rec.definitions)+[dict(id="reversal_ema20",name="ema.value",timeframe_minutes=15,panel="overlay",parameters={"period":20}),dict(id="reversal_bb_middle",name="bollinger.middle",timeframe_minutes=15,panel="overlay",parameters={"period":20,"multiplier":2})]
        if defs is None:defs=current
        else:assert defs==current
        for k,v in rec.series.items():series.setdefault(k,[]).extend(v)
        for name,arr in (("reversal_ema20",ema),("reversal_bb_middle",sma)):
            series.setdefault(name,[]).extend([[start+row["k"]*60,None if not np.isfinite(arr[j]) else float(arr[j])] for j,row in enumerate(rows,1)])
        by_year[year]=[]
        for (tf,contraction,label),net in zip(configs,expected[year]):
            for mode in modes:
                key=label+"-"+mode;entries=es[tf][("none",contraction)]
                if mode=="2R":
                    cfg=dict(key=key,entry="liquidity-sweep",sl=1.5,tp=2,management="fixed",activation=0,distance=0)
                    v=grid.replay(bars,rows,entries,cfg,rec)
                    assert math.isclose(v["summary"]["net"],net,abs_tol=1e-6),v["summary"]
                    v["summary"]["already_at_equilibrium_skips"]=0
                else:v=dynamic_replay(bars,rows,entries,key,mode,rec,start,end,ema,sma,rsi)
                v["parameters"].update(rsi_setup_minutes=tf,atr_contraction=contraction,exit=mode)
                v["name"]="RSI reversal | "+key
                s=v["summary"];s.update(risk_metrics(v["trades"],s["monthly_entry_attribution"]))
                s["gross_points"]=math.fsum(t["gross_points"] for t in v["trades"])
                s["fee_points"]=math.fsum(t["fee_points"] for t in v["trades"])
                by_year[year].append(v)
                print("YEAR",year,key,json.dumps(s,separators=(",",":"),allow_nan=False))
    variants=[]
    for a,b in zip(by_year[2024],by_year[2025]):
        v=grid.aggregate([a,b]);s=v["summary"];s.update(risk_metrics(v["trades"],s["monthly_entry_attribution"]))
        s["already_at_equilibrium_skips"]=sum(x["summary"]["already_at_equilibrium_skips"] for x in (a,b))
        variants.append(v);print("RESULT",v["key"],json.dumps(s,separators=(",",":"),allow_nan=False))
    OUT.mkdir(parents=True,exist_ok=True)
    with gzip.open(OUT/"all_ledgers.json.gz","wt") as f:json.dump(variants,f,allow_nan=False,separators=(",",":"))
    results=[]
    for v in variants:
        s=v["summary"];row={"key":v["key"],**{k:x for k,x in s.items() if not isinstance(x,dict)}}
        for y,ys in s["years"].items():row.update({y+"_"+k:x for k,x in ys.items() if not isinstance(x,dict)})
        results.append(row)
    with (OUT/"all_results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    export_bundle(OUT/"backtest.json",family="rsi14-reversal-equilibrium-2024-2025",symbol="BTCUSD",unit="price points",
        start_utc=dt(prior24.START).isoformat(),end_utc=dt(source25.END).isoformat(),execution_timeframe_minutes=1,signal_timeframe_minutes=15,
        costs="0.05% taker each side +18% GST; no Scalper Offer; extra slippage zero; funding/liquidation excluded; 1m Color.",
        variants=variants,indicator_definitions=defs,indicator_series=series,data_provenance=dict(
            manifest_2024=str(prior24.ROOT/"manifest.json"),manifest_2025=str(source25.ROOT/"manifest.json"),
            selection="3 existing entries x 4 fixed exit policies; 2026 untouched",
            period="Feb 1 2024 12 UTC through Dec 31 2025; yearly resets and year-end closes",
            exit="RSI50 at completed 15m close then next 1m open; EMA20/SMA20 latest closed 15m level, intraminute touch; skip if equilibrium already reached at entry",
            equal_risk="sum net points / initial risk points per trade; fixed risk amount, no compounding or leverage model",
            attribution="UTC entry month; realized drawdown"))
    print("TOTAL",len(variants))
if __name__=="__main__":run()
