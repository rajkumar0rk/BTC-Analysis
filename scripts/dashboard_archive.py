"""Conservative archive import. No synthesized fills, no combined strategies."""
import json, hashlib, math, re
from pathlib import Path
import numpy as np
import pandas as pd

# Every schema declares complete known independent configuration keys.
# Unknown schemas remain discoverable in the coverage catalog, not guessed.
SCHEMAS=[
 dict(glob="analysis/v7_2_2025/v7_2_trades.csv",keys=["entry_type","exit_type","direction"],side="direction",entry="entry_time",exit="exit_time",ep="entry_price",xp="exit_price",net="net_points",gross="gross_points",reason="exit_reason",signal="signal_time",trigger="entry_type",symbol="BTCUSD"),
 dict(glob="analysis/**/v8_1_trade_ledger.csv",keys=["variant","side"],side="side",entry="entry_utc",exit="exit_utc",ep="entry_price",xp="exit_price",net="net_points",gross="gross_points",reason="exit_reason",signal="signal_utc",symbol="BTCUSD"),
 dict(glob="analysis/mtf_swing_range_long/trade_ledger.csv*",keys=["trend","setup","session","target_r"],fixed_side=1,entry="entry_utc",exit="exit_utc",ep="entry",xp="exit",net="net_pts",gross="gross_pts",reason="exit_reason",trigger="setup",symbol="BTCUSD"),
 dict(glob="analysis/ethusd_native_atr_price_action/full_trade_ledger.csv*",keys=["model"],side="direction",entry="entry_unix",exit="exit_unix",ep="entry_price_usd",xp="exit_price_usd",net="net_eth_price_points",gross="gross_eth_price_points",reason="result",trigger="pattern",symbol="ETHUSD"),
]
for name,side in [("mtf_swing_range_long_fixed2r",1),("mtf_swing_range_short_fixed2r",-1),("mtf_swing_range_short_fixed3r",-1),("mtf_swing_range_long_fixed3r",1),("mtf_uptrend_short_fixed3r",-1)]:
    SCHEMAS.append(dict(glob=f"analysis/{name}/trade_ledger.csv*",keys=["trend","setup","session","sl_pts","tp_pts"],fixed_side=side,entry="entry_utc",exit="exit_utc",ep="entry",xp="exit",net="net_pts",gross="gross_pts",reason="exit_reason",trigger="setup",symbol="BTCUSD"))

def dump(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,allow_nan=False,separators=(",",":")),encoding="utf8")

def value(v):
    if pd.isna(v): return None
    if isinstance(v,np.generic): return v.item()
    return v

def stamp(v):
    if pd.isna(v): return None
    t=pd.to_datetime(v,unit="s",utc=True) if isinstance(v,(int,float,np.number)) else pd.to_datetime(v,utc=True,errors="coerce")
    return None if pd.isna(t) else t.isoformat()

def number(v):
    try:
        x=float(v)
        return x if math.isfinite(x) else None
    except (ValueError,TypeError): return None

def side(v):
    return 1 if str(v).upper() in ("1","1.0","LONG","BUY") else -1 if str(v).upper() in ("-1","-1.0","SHORT","SELL") else None

def stats(records):
    # Exit-ordered realized trade P&L; not mark-to-market account equity.
    ordered=sorted(records,key=lambda t:t["exit_utc"])
    p=np.array([t["net_points"] for t in ordered],float)
    eq=np.r_[0,np.cumsum(p)]
    dd=np.maximum.accumulate(eq)-eq
    loss=-p[p<0].sum()
    return dict(trades=len(p),net=round(float(p.sum()),6),win_rate=round(float((p>0).mean()*100),2),profit_factor=round(float(p[p>0].sum()/loss),4) if loss else None,drawdown=round(float(dd.max()),6))

def curve(records):
    ordered=sorted(records,key=lambda t:t["exit_utc"])
    p=np.array([t["net_points"] for t in ordered],float)
    eq=np.r_[0,np.cumsum(p)]
    dd=np.maximum.accumulate(eq)-eq
    # Bounded samples retain worst drawdown and terminal value in each bucket.
    stride=max(1,math.ceil(len(p)/450))
    ids={0,len(p)}
    for a in range(1,len(eq),stride):
        b=min(a+stride,len(eq));ids.add(a+int(dd[a:b].argmax()));ids.add(b-1)
    return [[ordered[i-1]["exit_utc"] if i else ordered[0]["entry_utc"],round(float(eq[i]),6),round(float(dd[i]),6)] for i in sorted(ids)]

def normalize(row,s):
    def get(k):
        col=s.get(k)
        return value(row.get(col)) if col else None
    entry,exit=stamp(get("entry")),stamp(get("exit"))
    direction=s.get("fixed_side") or side(get("side"))
    net=number(get("net"))
    if not entry or not exit or exit<entry or direction is None or net is None: return None
    ctx={k:value(row[k]) for k in ("atr","signal_atr","ema20","ema50","supertrend","risk_pts","stop_distance_eth_usd","target_distance_eth_usd","fee_gst_points","modeled_cost_points","fee_slippage_pts","equity_trade_return","mfe_points","mae_points","trail_stop_price","liquidation_price") if k in row and value(row[k]) is not None}
    return dict(entry_utc=entry,exit_utc=exit,trigger_utc=stamp(get("signal")),side=direction,entry_price=number(get("ep")),exit_price=number(get("xp")),entry_reason=get("trigger"),exit_reason=get("reason"),result=get("reason") or "Not recorded",net_points=net,gross_points=number(get("gross")),fee_points=number(row.get("fee_gst_points")),assumed_slippage_points=None,stop_price=number(row.get("stop_price")),target_price=number(row.get("target_price")),trailing_stop_price=number(row.get("trail_stop_price")),liquidation_price=number(row.get("liquidation_price")),signal_context=ctx,split=value(row.get("period")),audit="archived fields only")

def candle_shards(root,out,symbol):
    folder=root/"data"/"delta_india"/symbol/"1m"
    days=[]
    for path in sorted(folder.glob("20??-??.csv.gz")):
        d=pd.read_csv(path,usecols=["time","open","high","low","close","volume"])
        if d.time.duplicated().any() or d.isna().any().any(): raise ValueError(f"Invalid candles {path}")
        d=d.sort_values("time")
        for day,g in d.groupby(pd.to_datetime(d.time,unit="s",utc=True).dt.strftime("%Y-%m-%d")):
            rows=[[int(t),*[round(float(v),6) for v in vals]] for t,*vals in g[["time","open","high","low","close","volume"]].itertuples(index=False,name=None)]
            dump(out/"data"/"candles"/symbol/(day+".json"),rows);days.append(day)
    return sorted(set(days))

def extend(root,out):
    idxpath=out/"data"/"index.json"
    index=json.loads(idxpath.read_text())
    index["schema"]=2
    # Original audited run: maintain prior shard paths and enrich statistics.
    for r in index["runs"]:
        r.update(symbol="BTCUSD",unit="price points",source=index["source"],audit="execution-time",costs=index["costs"])
        records=[]
        for m in r["months"]:
            records.extend(json.loads((out/"data"/"runs"/r["id"]/(m["month"]+".json")).read_text()))
        r.update(stats(records))
        dump(out/"data"/"runs"/r["id"]/"curve.json",curve(records))
    # Use original daily shards for the first run, new symbol-specific paths for archive.
    # Limit generated website size; oversized/incompatible ledgers are explicitly cataloged.
    coverage=[]; seen=set(); supported_count=0; budget=240*1024*1024; used=0
    for s in SCHEMAS:
        matches=sorted(root.glob(s["glob"]))
        if not matches: coverage.append(dict(path=s["glob"],status="Missing archived ledger"));continue
        for path in matches:
            rel=str(path.relative_to(root));seen.add(rel)
            try:
                if path.stat().st_size>80*1024*1024: raise ValueError("Ledger exceeds safe single-file build limit")
                d=pd.read_csv(path,low_memory=False)
                cols=set(s["keys"]+[s[k] for k in ("entry","exit","net")])
                if not cols.issubset(d.columns): raise ValueError("Schema mismatch: "+str(sorted(cols-set(d.columns))))
                if not s.get("fixed_side") and s.get("side") not in d: raise ValueError("Missing recorded side")
                prepared=[]; invalid=0
                for keys,g in d.groupby(s["keys"],sort=True,dropna=False):
                    if not isinstance(keys,tuple): keys=(keys,)
                    records=[]
                    for row in g.to_dict("records"):
                        rec=normalize(row,s)
                        if rec is None: invalid+=1
                        else: records.append(rec)
                    if not records: continue
                    rid="a"+hashlib.sha256((rel+repr(keys)).encode()).hexdigest()[:18]
                    prepared.append((rid,keys,records))
                if invalid: raise ValueError(f"{invalid} invalid trade rows; entire ledger excluded")
                estimate=sum(len(json.dumps(rec,allow_nan=False,separators=(",",":"))) + 1 for _,_,rr in prepared for rec in rr)
                if used+estimate>budget: raise ValueError("Archive export size budget reached")
                for rid,keys,records in prepared:
                    config=" / ".join(f"{k}={v}" for k,v in zip(s["keys"],keys))
                    months=[]
                    by={}
                    for rec in sorted(records,key=lambda t:t["entry_utc"]):
                        by.setdefault(rec["entry_utc"][:7],[]).append(rec)
                    for month,rr in sorted(by.items()):
                        for j,rec in enumerate(rr): rec["id"]=f"{rid}-{month}-{j}"
                        dump(out/"data"/"runs"/rid/(month+".json"),rr)
                        months.append(dict(month=month,net=round(sum(t["net_points"] for t in rr),6),trades=len(rr),wins=sum(t["net_points"]>0 for t in rr)))
                    dump(out/"data"/"runs"/rid/"curve.json",curve(records))
                    index["runs"].append(dict(id=rid,strategy=path.parent.name+" / "+config,target=None,stop=None,months=months,symbol=s["symbol"],unit="price points",source=rel,audit="archived fields only",costs="Source model costs; consult original report. No inferred fees or fills.",**stats(records)))
                used+=estimate;supported_count+=len(prepared)
                coverage.append(dict(path=rel,status="Imported",configurations=len(prepared)))
            except (ValueError,KeyError,TypeError,OverflowError,MemoryError) as exc:
                coverage.append(dict(path=rel,status="Not imported: "+str(exc)))
    for path in sorted((root/"analysis").rglob("*")):
        if not path.is_file(): continue
        rel=str(path.relative_to(root))
        name=path.name.lower()
        if rel not in seen and ("ledger" in name or name.endswith("_trades.csv") or name.endswith("_trades.csv.gz")) and (name.endswith(".csv") or name.endswith(".csv.gz")):
            coverage.append(dict(path=rel,status="Adapter pending — source preserved"))
    for symbol in ("BTCUSD","ETHUSD"):
        try:
            days=candle_shards(root,out,symbol)
            index.setdefault("candle_days",{})[symbol]=days
        except (ValueError,OSError) as exc:
            index.setdefault("candle_days",{})[symbol]=[]
            coverage.append(dict(path=f"data/delta_india/{symbol}/1m",status="Candle export unavailable: "+str(exc)))
    dump(out/"data"/"coverage.json",coverage)
    index["archive_configurations"]=supported_count
    dump(idxpath,index)
