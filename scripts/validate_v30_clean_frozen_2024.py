#!/usr/bin/env python3
"""Replay V28 and V29 frozen configurations on Mar–Dec 2024 only.
February provides indicators only. Native bars; no search or parameter changes."""
import hashlib,json,itertools
from pathlib import Path
import numpy as np
import pandas as pd
import research_v28_clean_single_setup as v28
import research_v29_clean_trend_conditioned as v29
ROOT=Path("data/delta_india/BTCUSD/2024_verified_archive")
OUT=Path("analysis/v30_march_december_2024")
START=pd.Timestamp("2024-02-01",tz="UTC")
END=v29.ist("2025-01-01")
def load():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    result={}
    for label,step in (("trade_1m",60),("mark_1m",60),("funding_1h",3600)):
        parts=[]
        for item in manifest["months"]:
            if item["series"]!=label or item["month"]<"2024-02":continue
            assert item["missing"]==0,item
            p=ROOT/label/(item["month"]+".csv.gz")
            assert hashlib.sha256(p.read_bytes()).hexdigest()==item["sha256"]
            parts.append(v29.read_frame(p))
        z=pd.concat(parts).sort_index()
        a=START-pd.Timedelta(hours=1) if step==3600 else START
        b=END.floor("h") if step==3600 else END
        z=z.loc[(z.index>=a)&(z.index<b)]
        expected=pd.date_range(a,b-pd.Timedelta(seconds=step),freq="h" if step==3600 else "min")
        assert z.index.equals(expected),(label,len(z),len(expected))
        assert ((z.low<=z[["open","close"]].min(axis=1))&(z.high>=z[["open","close"]].max(axis=1))).all()
        result[label]=z
    m=result["trade_1m"];mk=result["mark_1m"];fr=result["funding_1h"]
    prev=fr.reindex(m.index.floor("h")-pd.Timedelta(hours=1))
    assert not prev.isna().any().any()
    local=m.index.tz_convert(v29.IST)
    ctx=dict(op=m.open.to_numpy(float),hi=m.high.to_numpy(float),lo=m.low.to_numpy(float),cl=m.close.to_numpy(float),mo=mk.open.to_numpy(float),mh=mk.high.to_numpy(float),ml=mk.low.to_numpy(float),rate=prev.close.to_numpy(float)/100,adverse_long=np.maximum(prev.high.to_numpy(float)/100,0),adverse_short=np.minimum(prev.low.to_numpy(float)/100,0),weekday=local.dayofweek.to_numpy(),day=np.asarray(local.strftime("%Y%m%d"),dtype=np.int32),sw=len(m),end=len(m))
    return m,ctx,manifest
def main():
    m,ctx,manifest=load()
    for name,mod,source in (("v28",v28,"analysis/v28_clean_single_setup/frozen.json"),("v29",v29,"analysis/v29_clean_trend_conditioned/frozen.json")):
        frozen=Path(source)
        raw=frozen.read_bytes();cfg=json.loads(raw)["config"]
        ev=mod.signals(m,cfg["family"],cfg["timeframe"],cfg["lookback"])
        p=mod.period(m,ctx,ev,"2024-03-01","2025-01-01")
        assert p[3]==10
        mod.OUT=OUT/name;mod.OUT.mkdir(parents=True,exist_ok=True)
        mod.report(ctx,p,cfg,"replay","2024-03")
        (mod.OUT/"quality.json").write_text(json.dumps(dict(frozen_sha256=hashlib.sha256(raw).hexdigest(),config=cfg,archive_totals=manifest["totals"],scored_months=[str(x) for x in pd.period_range("2024-03","2024-12",freq="M")],warmup_start=str(START),start=str(v29.ist("2024-03-01")),end_exclusive=str(END),no_retuning=True,funding_proxy=True,liquidation_proxy=True),indent=2))
        print("REPLAY COMPLETE",name,flush=True)
if __name__=="__main__":main()
