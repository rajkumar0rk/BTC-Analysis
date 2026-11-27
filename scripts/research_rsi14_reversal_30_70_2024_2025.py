"""RSI14 30/70 liquidity sweep versus frozen 20/80; no other changes."""
import csv,gzip,hashlib,json,math
from pathlib import Path
import research_rsi14_reversal_regimes_2025 as regimes
import research_rsi14_reversal_multiple_r_2024 as prior24
import research_rsi14_80_20_2025 as source25
import research_rsi14_reversal_risk_grid_2024_2025 as grid
from research_rsi14_reversal_regimes_2025 import dt,load_data,entry_sets,tests,export_bundle
OUT=Path("scratch/rsi14_reversal_30_70")

def threshold_signals(rows,low,high):
    out=[];prev=None
    for i,row in enumerate(rows[:-1]):
        r=row["r"]
        if prev is not None and r is not None:
            if prev>=low>r:out.append((i,1))
            elif prev<=high<r:out.append((i,-1))
        prev=r
    return out

def run():
    tests()
    assert threshold_signals([{"r":30},{"r":29},{"r":29},{"r":70},{"r":71},{"r":50}],30,70)==[(1,1),(4,-1)]
    ps=[(low,high,tp) for low,high in ((20,80),(30,70)) for tp in (2,2.5)]
    by_year={};defs=None;series={}
    for year,start,end,reader in ((2024,prior24.START,prior24.END,prior24.candles_2024),(2025,source25.START,source25.END,source25.candles)):
        regimes.START,regimes.END,regimes.candles=start,end,reader
        grid.START,grid.END=start,end
        bars,rows,signals,rec=load_data()
        assert threshold_signals(rows,20,80)==signals
        if defs is None:defs=rec.definitions
        else:assert defs==rec.definitions
        for k,v in rec.series.items():series.setdefault(k,[]).extend(v)
        by_year[year]=[]
        for low,high,tp in ps:
            sig=threshold_signals(rows,low,high)
            es=entry_sets(rows,sig)["liquidity-sweep"]
            cfg=dict(key=f"rsi{low}-{high}-sweep-sl1.5-tp{tp}R",entry="liquidity-sweep",sl=1.5,tp=tp,management="fixed",activation=0,distance=0)
            v=grid.replay(bars,rows,es,cfg,rec)
            v["parameters"].update(long_threshold=low,short_threshold=high)
            v["name"]=f"15M RSI14 Reversal {low}/{high} | Liquidity Sweep | {tp}R"
            v["summary"].update(threshold_signals=len(sig),sweep_setups=len(es))
            by_year[year].append(v)
            print("ENTRIES",year,low,high,tp,len(sig),len(es),len(v["trades"]))
        expected=(3651.574285,3205.44903) if year==2024 else (10112.85959,7986.49766)
        for v,net in zip(by_year[year][:2],expected):
            assert math.isclose(v["summary"]["net"],net,abs_tol=1e-6),v["summary"]
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
    export_bundle(OUT/"backtest.json",family="rsi14-reversal-30-70-2024-2025",symbol="BTCUSD",unit="price points",
        start_utc=dt(prior24.START).isoformat(),end_utc=dt(source25.END).isoformat(),execution_timeframe_minutes=1,signal_timeframe_minutes=15,
        costs="0.05% taker each side +18% GST; no Scalper Offer; additional slippage zero; funding/liquidation excluded; 1m Color.",
        variants=variants,indicator_definitions=defs,indicator_series=series,data_provenance=dict(
            manifest_2024=str(prior24.ROOT/"manifest.json"),manifest_2025=str(source25.ROOT/"manifest.json"),
            manifest_sha256_2024=hashlib.sha256((prior24.ROOT/"manifest.json").read_bytes()).hexdigest(),
            manifest_sha256_2025=hashlib.sha256((source25.ROOT/"manifest.json").read_bytes()).hexdigest(),
            selection="only requested standard RSI30/70 compared to frozen 20/80 at 2R and 2.5R; 2026 untouched",
            period="Feb 1 2024 12 UTC through Dec 31 2025; separate yearly replays with indicator reset and year-end accounting close",
            entry="prior confirmed 2-left/2-right pivot sweep with directional reclaim; expiry next threshold cross; one position",
            attribution="UTC entry month; realized drawdown; no trailing or protection"))
    print("TOTAL",len(variants))
if __name__=="__main__":run()
