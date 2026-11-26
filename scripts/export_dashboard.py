"""Publish actual recorded backtest ledgers. Never rerun a strategy to display it."""
import json, shutil, os
from pathlib import Path
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"dashboard-dist"
SOURCE=ROOT/"analysis/delta_points_200_500/individual_trade_replay.csv"
def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,separators=(",",":"),allow_nan=False),encoding="utf-8")
def main():
    trades=pd.read_csv(SOURCE)
    required={"strategy","target_points","stop_points","entry_utc","exit_utc","trigger_utc","entry_reason","exit_reason","signal_context","entry_price","exit_price","net_points","side"}
    if not required.issubset(trades.columns) or trades.empty:
        raise ValueError("Actual BTC ledger missing required execution audit fields")
    for col in ("entry_utc","exit_utc","trigger_utc"):
        ts=pd.to_datetime(trades[col],utc=True,errors="raise",format="mixed")
        if ts.isna().any():raise ValueError("Missing recorded timestamp: "+col)
        trades[col]=ts.dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    if OUT.exists():shutil.rmtree(OUT)
    shutil.copytree(ROOT/"dashboard",OUT,ignore=shutil.ignore_patterns("README.md"))
    runs=[]
    for i,((name,tp,sl),g) in enumerate(trades.groupby(["strategy","target_points","stop_points"],sort=True)):
        g=g.sort_values("entry_utc").copy()
        g["month"]=g.entry_utc.str[:7]
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
    write(OUT/"data"/"index.json",dict(schema=2,instrument="BTCUSD",first=trades.entry_utc.min(),last=trades.exit_utc.max(),commit=os.getenv("GITHUB_SHA","local"),source=str(SOURCE.relative_to(ROOT)),costs="0.05% taker each side + 18% GST; 5 points slippage each side; funding not modeled; no leverage or account sizing",eth_workflow_run=os.getenv("DASHBOARD_ETH_RUN",""),runs=runs))
    from dashboard_archive import extend
    extend(ROOT,OUT)
    from curate_dashboard import curate
    curate(ROOT,OUT)
    print(f"Imported {len(runs)} actual BTC configurations, {len(trades)} recorded trades; no backtest rerun")
if __name__=="__main__":main()
