#!/usr/bin/env python3
"""Causal, price-level-preserving ETHUSD normalization for BTC-point model audits.

Use the original first BTCUSD/ETHUSD 1m OPEN as a PREDECLARED constant
scaling anchor; no future labels, no time-varying exchange-rate transforms.

Let S=BTC_open[2025-01-01T00:00Z]/ETH_open[2025-01-01T00:00Z].
For all future bars, ETH_syn=S*ETH_ohlc, so 200 BTC-index points
means EXACTLY (200/S) native ETH price points, not 200 ETH points.
A constant scaling preserves bar/candle geometry, percentage returns,
EMA crossovers, RSI, ATR multiples, and model cost percentages.
It does NOT implement a time-local BTC/ETH ratio at each trade; those
would need a separate hand-reviewed per-entry conversion. This is a
fixed Jan2025 *equivalent percent* sensitivity, not an exact port of
every strategy. ETH liquidity/margin and volume are NOT normalized.

Historical 2026-11 incomplete, excluded for 22-month research.
"""
from pathlib import Path
import csv
import gzip
import hashlib
import io
import json
import os
import shutil
import numpy as np
import pandas as pd

DEST=Path("data/eth_normalized_2025_anchor")
OHLC=("open","high","low","close")
MONTHS=[str(x) for x in pd.period_range("2025-01","2026-11",freq="M")]
TARGET_MONTHS=[str(x) for x in pd.period_range("2025-01","2026-10",freq="M")]

def first_row(path):
    with gzip.open(path,"rt") as f:
        rd=csv.DictReader(f)
        r=next(rd)
    return int(r["time"]),float(r["open"])

def normalized_write(src,dst,scale,expected_step):
    dst.parent.mkdir(parents=True,exist_ok=True)
    d=pd.read_csv(src,compression="gzip")
    expected_cols=["time","open","high","low","close","volume"]
    if not set(expected_cols).issubset(d.columns):
        raise ValueError("Invalid OHLCV columns "+str(src))
    a=d.time.to_numpy(np.int64)
    if len(a)==0 or len(np.unique(a))!=len(a):
        raise ValueError("Empty or duplicated synthetic source "+str(src))
    if (np.diff(a)!=expected_step).any():
        raise ValueError("Gap or irregular timestamp in "+str(src))
    for col in OHLC:
        d[col]=d[col].astype(float)*scale
    if ((d.low<=0)|(d.high<d.low)|(d.high<d[["open","close"]].max(axis=1))|
        (d.low>d[["open","close"]].min(axis=1))).any():
        raise ValueError("Normalized OHLCV invalid "+str(src))
    tmp=dst.with_suffix(".tmp")
    # Gzip timestamp/headers are not synthetic; bars are deterministically scaled.
    with gzip.open(tmp,"wt",newline="") as f:
        d.to_csv(f,index=False,lineterminator="\n",float_format="%.12g")
    os.replace(tmp,dst)
    return {"file":dst.name,"rows":len(d),
            "sha256":hashlib.sha256(dst.read_bytes()).hexdigest(),
            "source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),
            "first":int(a[0]),"last":int(a[-1])}

def prepare():
    btc=Path("data/delta_india/BTCUSD/1m")
    eth=Path("data/delta_india/ETHUSD/1m")
    bt,bo=first_row(btc/"2025-01.csv.gz")
    et,eo=first_row(eth/"2025-01.csv.gz")
    if bt!=et or bt!=1735689600:
        raise ValueError("BTC and ETH Jan2025 first minute not aligned")
    if not (bo>1000 and eo>100):raise ValueError("Invalid 2025 opening reference prices")
    scale=bo/eo
    # Use unchanged native OI, funding; model assumption warnings below.
    partitions=[]
    for m in MONTHS:
        partitions.append(normalized_write(eth/(m+".csv.gz"),
                                           DEST/"1m"/(m+".csv.gz"),scale,60))
    # For mark/futures basis, BOTH futures and mark must use same scaling.
    inst=Path("data/delta_india/ETHUSD/institutional/history")
    mark=inst/"mark_1m"
    if mark.is_dir():
        for m in MONTHS:
            path=mark/(m+".csv.gz")
            if path.exists():
                normalized_write(path,DEST/"institutional/history/mark_1m"/(m+".csv.gz"),scale,60)
    for kind in ("open_interest_5m","funding_1h"):
        d=DEST/"institutional/history"/kind
        d.mkdir(parents=True,exist_ok=True)
        src=inst/kind
        for m in MONTHS:
            p=src/(m+".csv.gz")
            if p.exists():
                q=d/(m+".csv.gz")
                if not q.exists():q.symlink_to(p.resolve())
    history={
       "source":"Original Delta Exchange India ETHUSD 1m; constant scalar index for original BTC-point models",
       "method":"Fixed price ratio anchored on FIRST available Jan 1, 2025 minute",
       "reference_timestamp_utc":"2025-01-01T00:00:00Z",
       "target_months":TARGET_MONTHS,
       "diagnostic_only_partial_november_2026":True,
       "btc_first_open":bo,"eth_first_open":eo,
       "synthetic_multiplier_btc_index_per_eth_price_point":scale,
       "equivalent_eth_price_points_per_200_btc_index_points":200./scale,
       "equivalent_eth_price_points_per_100_btc_index_points":100./scale,
       "equivalent_eth_slippage_price_points_per_5_index_points":5./scale,
       "synthetic_equivalent_not_current_ratio":True,
       "btc_oct31_source_NOT_REQUIRED":"Only Jan 1 2025 BTC reference candle is used; no BTC Oct data used",
       "partitions":partitions,
       "cautions":[
          "ETHUSD candles have been linearly scaled into a BTC-index price unit; results in price-point terms are NOT native ETH units",
          "A fixed ratio from January 2025 does not represent current BTC/ETH ratio on every future trade; this is an anchor-based sensitivity",
          "The scale DOES NOT change native ETH volume, OI, funding, order book, contract precision or margin",
          "Original BTC point targets/slippage are now native ETH 200/scale and 5/scale respectively",
          "Model results depend on original strategy code; no funding, bid/ask or liquidation model automatically added",
          "A 2025-01 first 00:00 UTC source means initial 5.5 hours of IST Jan 2025 unavailable",
          "2026-11 PARTIAL data included only to satisfy original historical split diagnostics; November must be EXCLUDED from all 22-month profitability targets",
          "Code consuming multiple feeds must ensure units and timestamp conventions are consistent"
       ]
    }
    DEST.mkdir(parents=True,exist_ok=True)
    (DEST/"manifest.json").write_text(json.dumps(history,indent=2)+"\n")
    return history

if __name__=="__main__":
    x=prepare()
    print(json.dumps({k:v for k,v in x.items() if k!="partitions"},indent=2))
