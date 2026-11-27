"""Twelve predeclared RSI reversal confirmations; no threshold optimization."""
import csv,gzip,hashlib,itertools,json,math
from pathlib import Path
from decimal import Decimal as D
import research_rsi14_reversal_regimes_2025 as regimes
import research_rsi14_reversal_multiple_r_2024 as prior24
import research_rsi14_80_20_2025 as source25
import research_rsi14_reversal_risk_grid_2024_2025 as grid
from research_rsi14_reversal_regimes_2025 import dt,load_data,entry_sets,tests,export_bundle
OUT=Path("scratch/rsi14_reversal_confirmation")
H1=regimes.Timeframe(3600)

def hourly_rsi(rows,start):
    assert start%3600==0
    book=regimes.IndicatorBook((regimes.spec("rsi",H1,period=14),),history_limit=2)
    values=[None]*len(rows)
    for j in range(3,len(rows),4):
        g=rows[j-3:j+1];end=start+rows[j]["k"]*60
        ca=regimes.Candle(regimes.INSTRUMENT,H1,dt(end-3600),dt(end),
            D(str(g[0]["o"])),D(str(max(x["h"] for x in g))),D(str(min(x["l"] for x in g))),
            D(str(g[-1]["c"])),sum(D(str(x["v"])) for x in g))
        book.update(ca)
        v=book.get("rsi",H1,{"period":14})[-1]
        values[j]=None if v is None else float(v)
    return values

def threshold_signals(values):
    out=[];prev=None
    for j,r in enumerate(values[:-1]):
        if r is None:continue
        if prev is not None:
            if prev>=20>r:out.append((j,1))
            elif prev<=80<r:out.append((j,-1))
        prev=r
    return out

def confirmed_states(values,i,end,d):
    # Work in a symmetric RSI coordinate: long r, short 100-r.
    # The failure swing is causal: recovery, confirmed peak on decline,
    # higher trough above 20 on rebound, then strict break of that peak.
    recovered=False;failed_swing=False;state=0;peak=trough=None;prev=None
    result={}
    for j in range(i,end):
        raw=values[j]
        if raw is not None:
            r=raw if d==1 else 100-raw
            if r<=20:
                recovered=False;failed_swing=False;state=0;peak=trough=None
            else:
                recovered=True
                if state==0:
                    state=1;peak=r
                elif state==1:
                    if r<prev:
                        state=2;trough=r
                    else:peak=max(peak,r)
                elif state==2:
                    if r>prev:
                        state=3
                        if r>peak:failed_swing=True
                    else:trough=min(trough,r)
                elif state==3:
                    if r>peak:failed_swing=True
                    elif r<trough:
                        # New lower pullback invalidates the previous trough,
                        # but can establish a new one above 20.
                        state=2;trough=r
            prev=r
        result[j]=(recovered,failed_swing)
    return result

def confirmation_tests():
    vals=[19,25,35,30,27,29,34,36,19]
    s=confirmed_states(vals,0,len(vals),1)
    assert s[0]==(False,False) and s[1]==(True,False)
    assert not s[6][1] and s[7]==(True,True) and s[8]==(False,False)
    assert s==confirmed_states([100-v for v in vals],0,len(vals),-1)
    assert threshold_signals([21,19,None,19,81,None,50])==[(1,1),(4,-1)]

def make_entries(rows,signals,values):
    base=entry_sets(rows,signals)["liquidity-sweep"]
    end_by_trigger={i:(signals[q+1][0] if q+1<len(signals) else len(rows)-1) for q,(i,d) in enumerate(signals)}
    out={(mode,contraction):[] for mode in ("none","recovery","failure-swing") for contraction in (False,True)}
    for i,j,d,extreme in base:
        end=end_by_trigger[i]
        states=confirmed_states(values,i,end,d)
        col="l" if d==1 else "h"
        filled=set()
        for k in range(j,end):
            b=rows[k]
            extreme=min(extreme,b[col]) if d==1 else max(extreme,b[col])
            recovered,swing=states[k]
            a=rows[k-1]["atr"] if k else None
            contracting=a is not None and b["atr"] is not None and b["atr"]<a
            for mode,contraction in out:
                if (mode,contraction) in filled:continue
                if mode=="recovery" and not recovered:continue
                if mode=="failure-swing" and not swing:continue
                if contraction and not contracting:continue
                out[(mode,contraction)].append((i,k,d,extreme))
                filled.add((mode,contraction))
            if len(filled)==6:break
    assert out[("none",False)]==base
    return out

def run():
    tests();confirmation_tests()
    plans=list(itertools.product((15,60),("none","recovery","failure-swing"),(False,True)))
    assert len(plans)==12
    by_year={};defs=None;series={}
    for year,start,end,reader in ((2024,prior24.START,prior24.END,prior24.candles_2024),(2025,source25.START,source25.END,source25.candles)):
        regimes.START,regimes.END,regimes.candles=start,end,reader
        grid.START,grid.END=start,end
        bars,rows,signals,rec=load_data()
        values15=[r["r"] for r in rows];values60=hourly_rsi(rows,start)
        assert signals==threshold_signals(values15)
        signals60=threshold_signals(values60)
        entries={15:make_entries(rows,signals,values15),60:make_entries(rows,signals60,values60)}
        if defs is None:defs=rec.definitions
        else:assert defs==rec.definitions
        for k,v in rec.series.items():series.setdefault(k,[]).extend(v)
        by_year[year]=[]
        for tf,mode,contraction in plans:
            key=f"rsi{tf}m-sweep-{mode}"+("-atr-contraction" if contraction else "")
            cfg=dict(key=key,entry="liquidity-sweep",sl=1.5,tp=2,management="fixed",activation=0,distance=0)
            es=entries[tf][(mode,contraction)]
            v=grid.replay(bars,rows,es,cfg,rec)
            v["parameters"].update(rsi_setup_minutes=tf,rsi_confirmation=mode,atr_contraction=contraction)
            v["name"]=f"RSI14 {tf}M reversal | 15M sweep | {mode}"+(" | ATR contraction" if contraction else "")
            # The grid engine records 15m RSI, not hourly RSI. Annotate actual setup values separately.
            values=values15 if tf==15 else values60
            setup_by_time={dt(start+rows[i]["k"]*60).isoformat():values[i] for i,j,d,e in es}
            for tr in v["trades"]:
                tr["signal_context"]["setup_rsi_timeframe_minutes"]=tf
                tr["signal_context"]["setup_rsi"]=setup_by_time[tr["trigger_utc"]]
                tr["entry_reason"]=key
            v["summary"].update(threshold_signals=len(signals if tf==15 else signals60),sweep_setups=len(es))
            by_year[year].append(v)
            print("ENTRIES",year,key,len(es),len(v["trades"]))
        assert math.isclose(by_year[year][0]["summary"]["net"],3651.574285 if year==2024 else 10112.85959,abs_tol=1e-6),by_year[year][0]["summary"]
    variants=[grid.aggregate([a,b]) for a,b in zip(by_year[2024],by_year[2025])]
    for v in variants:print("RESULT",v["key"],json.dumps(v["summary"],allow_nan=False,separators=(",",":")))
    OUT.mkdir(parents=True,exist_ok=True)
    with gzip.open(OUT/"all_ledgers.json.gz","wt") as f:json.dump(variants,f,allow_nan=False,separators=(",",":"))
    results=[]
    for v in variants:
        s=v["summary"];row=dict(key=v["key"],**v["parameters"],**{k:x for k,x in s.items() if k not in ("monthly_entry_attribution","years")},**s["monthly_entry_attribution"])
        for y,ys in s["years"].items():
            for k in ("net","profitable_months","profit_factor","realized_drawdown_points","trades","threshold_signals","sweep_setups"):row[y+"_"+k]=ys[k]
        results.append(row)
    with (OUT/"all_results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    export_bundle(OUT/"backtest.json",family="rsi14-reversal-confirmation-2024-2025",symbol="BTCUSD",unit="price points",
        start_utc=dt(prior24.START).isoformat(),end_utc=dt(source25.END).isoformat(),execution_timeframe_minutes=1,signal_timeframe_minutes=15,
        costs="0.05% taker each side +18% GST; no Scalper Offer; additional slippage zero; funding/liquidation excluded; 1m Color.",
        variants=variants,indicator_definitions=defs,indicator_series=series,data_provenance=dict(
            manifest_2024=str(prior24.ROOT/"manifest.json"),manifest_2025=str(source25.ROOT/"manifest.json"),
            manifest_sha256_2024=hashlib.sha256((prior24.ROOT/"manifest.json").read_bytes()).hexdigest(),
            manifest_sha256_2025=hashlib.sha256((source25.ROOT/"manifest.json").read_bytes()).hexdigest(),
            selection="12 predeclared combinations: 2 setup timeframes x 3 RSI confirmation states x 2 ATR contraction choices; 2026 untouched",
            period="Feb 1 2024 12 UTC through Dec 31 2025; separate yearly replays with indicator reset and year-end accounting close",
            entry="unchanged 15m liquidity sweep; wait until optional confirmation requirements are simultaneously satisfied before next threshold crossing; next 1m open",
            recovery="completed setup-timeframe RSI back inside 20/80",
            failure_swing="completed setup-timeframe RSI recovery, peak, higher trough above 20 then peak break; mirror short; no pivot lookahead",
            contraction="latest completed 15m ATR14 below preceding completed 15m ATR14",
            hourly="native RSI14 indicator on completed hourly aggregation of 15m candles; no partial hourly candle",
            attribution="UTC entry month; realized drawdown; no trailing or protection"))
    print("TOTAL",len(variants),"PROFITABLE_BOTH",sum(all(y["net"]>0 for y in v["summary"]["years"].values()) for v in variants))
if __name__=="__main__":run()
