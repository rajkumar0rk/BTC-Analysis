"""Publish execution-instrumented reproduction of an existing experiment; no new strategy search."""
import json, shutil, os
from pathlib import Path
import pandas as pd
import numpy as np
import research_daily_200_500_points as engine

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"dashboard-dist"
START="2025-01-01"
END="2026-10-17 23:59:00"

def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,separators=(",",":"),allow_nan=False),encoding="utf-8")

def main():
    d=engine.input_data().loc[START:END]
    expected=pd.date_range(START,END,freq="min",tz="UTC")
    if not d.index.equals(expected):
        raise RuntimeError("Original research interval has missing or unexpected candles")
    ev=engine.events(d)
    trades=engine.trade_sim(d,ev)
    if OUT.exists(): shutil.rmtree(OUT)
    shutil.copytree(ROOT/"dashboard",OUT,ignore=shutil.ignore_patterns("README.md"))
    # UTC daily shards: browser requests only days surrounding a selected trade.
    for day,g in d.groupby(d.index.strftime("%Y-%m-%d"),sort=True):
        rows=[[int(t.timestamp()),*[round(float(v),6) for v in vals]] for t,vals in zip(g.index,g[["open","high","low","close","volume"]].to_numpy())]
        write(OUT/"data"/"candles"/(day+".json"),rows)
    runs=[]
    for i,((name,tp,sl),g) in enumerate(trades.groupby(["strategy","target_points","stop_points"],sort=True)):
        g=g.sort_values("entry_utc").copy()
        g["month"]=pd.to_datetime(g.entry_utc,utc=True).dt.strftime("%Y-%m")
        months=[]
        for month,m in g.groupby("month",sort=True):
            records=json.loads(m.drop(columns=["month"]).to_json(orient="records"))
            for j,rec in enumerate(records):
                rec["id"]=f"{i}-{month}-{j}"
                rec["signal_context"]=json.loads(rec["signal_context"])
            write(OUT/"data"/"runs"/str(i)/(month+".json"),records)
            months.append(dict(month=month,net=round(float(m.net_points.sum()),3),trades=len(m),wins=int((m.net_points>0).sum())))
        p=g.net_points.to_numpy()
        eq=np.r_[0,np.cumsum(p)]
        losses=-p[p<0].sum()
        runs.append(dict(id=str(i),strategy=name,target=int(tp),stop=int(sl),trades=len(g),net=round(float(p.sum()),3),win_rate=round(float((p>0).mean()*100),2),profit_factor=round(float(p[p>0].sum()/losses),3) if losses else None,drawdown=round(float((np.maximum.accumulate(eq)-eq).max()),3),months=months))
    write(OUT/"data"/"index.json",dict(schema=1,instrument="BTCUSD",first=str(d.index[0]),last=str(d.index[-1]),bars=len(d),commit=os.getenv("GITHUB_SHA","local"),source="scripts/research_daily_200_500_points.py",costs="0.05% taker each side + 18% GST; 5 points slippage each side; funding not modeled; no leverage or account sizing",runs=runs))
    print(f"Exported {len(runs)} configurations, {len(trades)} trades, {len(d)} candles")

if __name__=="__main__":
    main()
