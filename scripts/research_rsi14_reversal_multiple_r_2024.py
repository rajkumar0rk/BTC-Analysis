"""2024 frozen liquidity-sweep R validation, no retuning."""
import csv,gzip,hashlib,json,math
from decimal import Decimal as D
import research_rsi14_reversal_regimes_2025 as regimes
from stage_repository_history import source_rows,month_bounds
from pathlib import Path
import numpy as np
from research_rsi14_reversal_regimes_2025 import (
    ROOT,START,END,FEE,TICK,dt,load_data,entry_sets,execute,tests,export_bundle,
    replay as original_replay,
)
ROOT=Path("data/delta_india/BTCUSD/2024_verified_archive")
RECOVERY=Path("data/delta_india/2024_recovery_candidates/BTCUSD")
START=int(__import__("datetime").datetime.fromisoformat("2024-02-01T12:00:00+00:00").timestamp())
END=1735689600
OUT=Path("scratch/rsi14_reversal_multiple_r_2024")
def candles_2024():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    assert manifest["synthetic_rows"]==0 and manifest["original_trade_rows_preserved"]
    metas={m["month"]:m for m in manifest["months"] if m["series"]=="trade_1m"}
    expected=START
    for month in range(2,13):
        key=f"2024-{month:02d}"
        if month in (2,12):
            doc=json.loads((RECOVERY/key/"manifest.json").read_text())
            m=next(x for x in doc["series"] if x["series"]=="trade_1m")
            assert m["synthetic_rows"]==0 and m["overlap_conflicts"]==0 and not m["request_errors"]
            path=RECOVERY/key/m["file"]
        else:
            m=metas[key];assert m["missing"]==0
            path=ROOT/"trade_1m"/(key+".csv.gz")
        _,rows=source_rows(path,m["sha256"],m["observed"])
        for row in rows:
            t=int(row[0])
            if month==3 and t<month_bounds("2024-03")[0]:continue
            if START<=t<END:
                assert t==expected,(key,t,expected)
                expected+=60
                yield t,*(D(v) for v in row[1:])
        # November IST data ends at Dec 1 minus 5.5h, while recovered
        # December UTC starts at midnight; append original December bridge.
        if month==11:
            m=metas["2024-12"]
            _,bridge=source_rows(ROOT/"trade_1m"/"2024-12.csv.gz",m["sha256"],m["observed"])
            dec_start=month_bounds("2024-12")[0]
            for row in bridge:
                t=int(row[0])
                if t>=dec_start:break
                assert t==expected,(t,expected)
                expected+=60
                yield t,*(D(v) for v in row[1:])
    assert expected==END

MULTIPLES=(0.25,0.5,0.75,1,1.25,1.5,2,2.5,3,4,5)
def replay(bars,rows,es,mode,plan,rec):
    O,H,L,C=bars;kind,s,t=plan
    assert kind=="atr" and s==1.5
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
        x,xp,reason=execute(O,H,L,C,k,d,sd,target,0,-1,empty)
        free=x+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
        vals={}
        for spec_obj,m in zip(rec.specs,rec.definitions):
            key={"rsi":"r","atr":"atr","ema":"ema","adx":"adx"}.get(spec_obj.base)
            if spec_obj.base=="bollinger":key="upper" if spec_obj.name.endswith("upper") else "lower"
            if key and b[key] is not None:vals[m["id"]]=b[key]
        trades.append(dict(entry_utc=dt(START+k*60).isoformat(),trigger_utc=dt(START+a["k"]*60).isoformat(),
            exit_utc=dt(END if reason==4 else START+x*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),
            stop_price=ep-d*sd,target_price=target,gross_points=gross,fee_points=fee,net_points=gross-fee,
            assumed_slippage_points=0,entry_reason=mode,exit_reason={1:"Initial stop",2:"Fixed target",4:"End of 2024 evaluation"}[reason],
            signal_context=dict(rsi14=a["r"],confirmation_rsi14=b["r"],confirmation_utc=dt(START+k*60).isoformat(),
                initial_risk_points=sd,setup_extreme=extreme,atr14=atr,adx14=b["adx"],h4_ema50=b["ema"]),indicator_values=vals))
    p=[x["net_points"] for x in trades];gain=math.fsum(max(0,n) for n in p);loss=-math.fsum(min(0,n) for n in p)
    months={f"2024-{m:02d}":0. for m in range(2,13)};eq=peak=dd=0.
    for tr,n in zip(trades,p):
        months[tr["entry_utc"][:7]]+=n;eq+=n;peak=max(peak,eq);dd=max(dd,peak-eq)
    wins=sum(n>0 for n in p)
    summary=dict(accounting="realized",open_position=None,trades=len(p),net=math.fsum(p),wins=wins,
        win_rate=100*wins/len(p) if p else 0,profit_factor=gain/loss if loss else None,
        realized_drawdown_points=dd,monthly_entry_attribution=months,profitable_months=sum(x>0 for x in months.values()))
    key=f"{mode}-{kind}-sl{s}-target{t}"
    params=dict(entry=mode,stop_kind=kind,stop_atr_multiple=s if kind=="atr" else None,target_multiple=t,
        target_unit="R",rsi_period=14,long_threshold=20,short_threshold=80,
        trading_days="all",signals_while_open="ignored")
    return dict(key=key,name="15M RSI14 Reversal | "+key,parameters=params,summary=summary,trades=trades)


def run():
    tests()
    regimes.START,regimes.END,regimes.candles=START,END,candles_2024
    bars,rows,signals,rec=load_data()
    mode="liquidity-sweep"
    es=entry_sets(rows,signals)[mode]
    variants=[]
    for r in MULTIPLES:
        v=replay(bars,rows,es,mode,("atr",1.5,r),rec)
        v["key"]=f"liquidity-sweep-atr1.5-{r}R"
        v["name"]=f"RSI14 Reversal | Liquidity sweep | {r}R"
        for t in v["trades"]:
            risk=t["signal_context"]["initial_risk_points"]
            assert abs(abs(t["target_price"]-t["entry_price"])-math.ceil(r*risk/TICK)*TICK)<1e-7
        variants.append(v)
        print("RESULT",v["key"],json.dumps(v["summary"],allow_nan=False,separators=(",",":")))
    OUT.mkdir(parents=True,exist_ok=True)
    with gzip.open(OUT/"all_ledgers.json.gz","wt") as f:json.dump(variants,f,allow_nan=False,separators=(",",":"))
    results=[dict(key=v["key"],**v["parameters"],**{k:x for k,x in v["summary"].items() if k!="monthly_entry_attribution"},**v["summary"]["monthly_entry_attribution"]) for v in variants]
    with (OUT/"all_results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    export_bundle(OUT/"backtest.json",family="rsi14-reversal-multiple-r-2024",symbol="BTCUSD",unit="price points",
        start_utc=dt(START).isoformat(),end_utc=dt(END).isoformat(),execution_timeframe_minutes=1,signal_timeframe_minutes=15,
        costs="0.05% taker each side +18% GST; no Scalper Offer; zero extra slippage; funding/liquidation excluded; 1m Color, stop gap at open.",
        variants=variants,recorder=rec,data_provenance=dict(
            manifest=str(ROOT/"manifest.json"),manifest_sha256=hashlib.sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),
            input_minutes=len(bars[0]),selection="11 frozen 2025 R multiples; 2024 historical holdout; no retuning; Feb 1 12:00 UTC to Jan 1 2025; partial February",
            entry="unchanged liquidity sweep; prior confirmed 2-left/2-right pivot, sweep and directional reclaim",
            target="R times actual tick-rounded initial risk, rounded up to tick",recovery_manifests={k:hashlib.sha256((RECOVERY/k/"manifest.json").read_bytes()).hexdigest() for k in ("2024-02","2024-12")},
            month_attribution="UTC entry month; trade-close drawdown",setup_expiry="next threshold crossing; signals during position ignored"))
    print("TOTAL",len(MULTIPLES),"PROFITABLE",sum(v["summary"]["net"]>0 for v in variants))
if __name__=="__main__":run()
