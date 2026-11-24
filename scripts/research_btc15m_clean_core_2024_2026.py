#!/usr/bin/env python3
"""Core-only replay. No adaptive management, filters or loss-based sizing."""
import inspect,hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc15m_worst_month_loss_pause_20261123 as base
OUT=Path("analysis/btc15m_clean_core_2024_2026")
DATA=Path("_validation_data")
def engine():
    src=inspect.getsource(base.simulate)
    a="qty=cash/entry"
    assert src.count(a)==1
    src=src.replace(a,'qty=(cash/entry)*float(name.split("__P_")[1])/100')
    ns=dict(base.__dict__)
    exec(compile(src,"<core_only>","exec"),ns)
    return ns["simulate"]
def run(df,months,year,start_i):
    base.MONTHS=months
    sim=engine()
    ema,stline,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df)
    sig=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    sig={i:v for i,v in sig.items() if i>=start_i}
    rows=[];monthly=[];ledger=[]
    for p in (80,100):
        for path in base.PATHS:
            x,m,l=sim(df,ema,stline,trend,ind,f"reclaim_NOFLIP_CORE__P_{p}",(4,"any","PCT",3.,3.,"none"),sig,path)
            for k in ("profitable_2025_months","profitable_2026_months","return_2025_pct","return_2026_pct"):x.pop(k,None)
            x.update(profile=p,period=year)
            m["profile"]=p;m["period"]=year;l["profile"]=p;l["period"]=year
            rows.append(x);monthly.append(m);ledger.append(l)
    return rows,monthly,ledger
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    training,q=base.read_source("BTCUSD")
    months=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
    rows,monthly,ledger=run(training,months,"2025-2026",0)
    # Exact same previously verified holdout data, not re-downloaded.
    frames=[]
    for mon in pd.period_range("2024-08","2024-12",freq="M").astype(str):
        f=DATA/(mon+".csv.gz")
        meta=json.loads((DATA/(mon+".json")).read_text())
        assert meta["complete"] and hashlib.sha256(f.read_bytes()).hexdigest()==meta["sha256"]
        d=pd.read_csv(f)
        assert len(d)==meta["expected"]
        frames.append(d)
    df=pd.concat(frames,ignore_index=True)
    assert np.all(np.diff(df.time.to_numpy(np.int64))==60)
    df.index=pd.to_datetime(df.time,unit="s",utc=True)
    assert len(df)%15==0
    start=pd.Timestamp("2024-09-01",tz="Asia/Kolkata").tz_convert("UTC")
    start_i=int(np.searchsorted(df.time.to_numpy(),int(start.timestamp())))
    x,m,l=run(df,["2024-09","2024-10","2024-11","2024-12"],"2024",start_i)
    rows+=x;monthly+=m;ledger+=l
    s=pd.DataFrame(rows);m=pd.concat(monthly,ignore_index=True);l=pd.concat(ledger,ignore_index=True)
    s.to_csv(OUT/"summary.csv",index=False);m.to_csv(OUT/"monthly.csv",index=False);l.to_csv(OUT/"ledger.csv",index=False)
    lines=["# BTCUSD 15m core-only backtest","", "EMA20 reclaim within 4 completed candles following Supertrend(10,3) interaction. One position per cycle; next minute entry. Fixed SL3%, TP9%; no ST flip exit. No ATR/EMA slope/RSI filter, monthly guard, adaptive stops/locks, drawdown sizing, loss sizing, scale-in/out or hedging. Fixed 80% or 100% of equity notional.", "", "Starting equity $1000 independently each period; fee 0.05% per side + GST18%, slip 0.02% per side; funding not modeled. 2024 Sep-Dec only, August warmup. 2025-2026 same archive as previous research.","",s[["period","profile","path_assumption","trades","wins","losses","net_return_pct","max_floating_drawdown_pct","profitable_months","fees_gst_usd"]].to_markdown(index=False),"","## Monthly results",m.pivot(index="month_ist",columns=["profile","path_assumption"],values="monthly_return_pct").to_markdown(),""]
    (OUT/"REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines),flush=True)
if __name__=="__main__":main()
