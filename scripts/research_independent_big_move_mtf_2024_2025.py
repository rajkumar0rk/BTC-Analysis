"""Independent higher timeframe alignment study; no threshold fitting."""
import csv,gzip,json,math
from pathlib import Path
import numpy as np
import research_independent_big_move_2024_2025 as base
OUT=Path("scratch/independent_big_move_mtf")
FILTERS=("none","1h","4h","1h-4h")
EXPECTED={2024:(-99339.70007,-19900.274605,-105468.701625,-70218.03965,-70994.627515,-77754.748795),2025:(-164153.975265,-65854.26684,-86692.83508,-209259.313055,-151899.12278,-142046.266385)}

def alignment(bars,tf):
    # Only use completed higher timeframe candle at each 15m signal close.
    close=bars[3,tf-1::tf]
    e20=base.ema(close,20);e50=base.ema(close,50)
    direction=np.where(e20>e50,1,np.where(e20<e50,-1,0))
    ix=(np.arange(1,bars.shape[1]//15+1)*15)//tf-1
    result=np.zeros(len(ix),dtype=np.int8)
    valid=ix>=0
    result[valid]=direction[ix[valid]]
    return result

def filters(bars):
    h1=alignment(bars,60);h4=alignment(bars,240)
    return {"1h":h1,"4h":h4,"1h-4h":np.where(h1==h4,h1,0)}

def tests():
    base.tests()
    # Increasing series: 4H trend first valid only after the 50th complete H4 bar.
    n=240*60;c=np.arange(n,dtype=float)+100;bars=np.array([c,c,c,c])
    h=alignment(bars,240)
    first=50*240//15-1
    assert np.all(h[:first]==0) and np.all(h[first:]==1)
    for key,d in filters(bars).items():
        truncated=filters(bars[:,:240*53])[key]
        assert np.array_equal(d[:len(truncated)],truncated),key
    # Long/short symmetry and no direction during warmup.
    assert np.array_equal(alignment(bars,60),-alignment(-bars,60))

def run():
    tests();by_year={}
    for year,start,end,reader in ((2024,base.data24.START,base.data24.END,base.data24.candles_2024),(2025,base.data25.START,base.data25.END,base.data25.candles)):
        bars=base.read_bars(reader,start,end)
        f=base.features(bars,15);ss=base.signals(f);align=filters(bars)
        by_year[year]=[]
        for name,expected in zip(base.FAMILIES,EXPECTED[year]):
            for filt in FILTERS:
                sig=ss[name] if filt=="none" else np.where(ss[name]==align[filt],ss[name],0).astype(np.int8)
                v=base.replay(bars,f,sig,name,15,start,end)
                if filt=="none":assert math.isclose(v["summary"]["net"],expected,abs_tol=1e-6),v["summary"]
                v["key"]+="-"+filt;v["name"]=v["key"]
                v["parameters"].update(trend_filter=filt,trend_rule="EMA20 versus EMA50 on latest completed higher timeframe candle")
                v["summary"]["unfiltered_signal_count"]=int(np.count_nonzero(ss[name]))
                by_year[year].append(v)
                print("YEAR",year,v["key"],json.dumps(v["summary"],separators=(",",":"),allow_nan=False))
    variants=[]
    for a,b in zip(by_year[2024],by_year[2025]):
        assert a["key"]==b["key"]
        trades=a["trades"]+b["trades"];months=list(a["summary"]["monthly_entry_attribution"])+list(b["summary"]["monthly_entry_attribution"])
        s=base.summarize(trades,months);s["years"]={"2024":a["summary"],"2025":b["summary"]}
        v=dict(key=a["key"],name=a["name"],parameters=a["parameters"],summary=s,trades=trades)
        variants.append(v);print("RESULT",v["key"],json.dumps(s,separators=(",",":"),allow_nan=False))
    assert len(variants)==24
    OUT.mkdir(parents=True,exist_ok=True)
    with gzip.open(OUT/"all_ledgers.json.gz","wt") as f:json.dump(variants,f,separators=(",",":"),allow_nan=False)
    rows=[]
    for v in variants:
        s=v["summary"];row=dict(key=v["key"],**v["parameters"],**{k:x for k,x in s.items() if not isinstance(x,dict)})
        for y,ys in s["years"].items():row.update({y+"_"+k:x for k,x in ys.items() if not isinstance(x,dict)})
        rows.append(row)
    with (OUT/"all_results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (OUT/"provenance.json").write_text(json.dumps(dict(families=base.RULES,filters=FILTERS,trend="EMA20>EMA50 long; EMA20<EMA50 short; both must agree for combined; latest completed candle only",
        signal_timeframe=15,initial_stop="2 ATR14",exit="unchanged ratcheting opposite 10-bar channel; no fixed target",execution="next 1m open; one position; 1m stop touch or gap",
        costs="0.05% taker each side +18% GST; no offer; funding/liquidation/extra slippage excluded",
        period="2024 Feb 1 12 UTC to Jan 1 2025 and full 2025; yearly reset and accounting close; 2026 untouched",
        selection="18 filtered variants and 6 exact unfiltered baselines; fixed parameters; not independent validation"),indent=2))
    print("TOTAL",len(variants))
if __name__=="__main__":run()
