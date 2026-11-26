"""Bundled deterministic synthetic end-to-end fixture, not a market backtest."""
from datetime import datetime,timedelta,timezone
from decimal import Decimal as D
from hashlib import sha256
from ..contracts import (Instrument,AssetClass,Timeframe,Candle,DatasetRef,DataKind,
                         StrategyRef,BacktestConfig,CostModel,MarginMode,IntrabarPolicy)
from ..backtest import run_backtest
from ..examples.ema_supertrend import EMASupertrendExample
from ..serialization import fingerprint,to_wire
from pathlib import Path
import inspect

class Cancelled(Exception):pass


def execute_fixture(payload,progress):
    if set(payload)!={"kind","bars","signal_minutes"} or payload["kind"]!="reference_fixture":
        raise ValueError("untrusted job kind")
    n=payload["bars"];minutes=payload["signal_minutes"]
    if type(n) is not int or not 20<=n<=600 or type(minutes) is not int or minutes not in (1,5,15) or n%minutes:
        raise ValueError("invalid fixture parameters")
    start=datetime(2025,1,1,tzinfo=timezone.utc);end=start+timedelta(minutes=n)
    instrument=Instrument("synthetic","FIXTURE",AssetClass.CRYPTO_PERPETUAL,"USD","USD",D(".1"),D(".001"),D(1))
    tf=Timeframe(60);signal=Timeframe(minutes*60)
    candles=[]
    for i in range(n):
        p=D(100+(i%40 if i%80<40 else 40-i%40))
        close=p+D(1 if i%80<40 else -1)
        candles.append(Candle(instrument,tf,start+timedelta(minutes=i),start+timedelta(minutes=i+1),
                              p,max(p,close)+1,min(p,close)-1,close,D(10)))
    rows=tuple(candles);manifest=fingerprint(rows)
    data=DatasetRef("synthetic-fixture",instrument,DataKind.OHLCV,tf,start,end,manifest,"synthetic",0,True)
    code=sha256(inspect.getsource(EMASupertrendExample).encode()).hexdigest()
    params=dict(ema_period=3,atr_period=2,multiplier="2",exposure=".2")
    strategy=StrategyRef("builtin-ema-supertrend-fixture","1",code,fingerprint(params))
    cfg=BacktestConfig(strategy,instrument,(data,),start,end,signal,tf,D(100),"USD",D(1),MarginMode.ISOLATED,
                       CostModel(D(2),D(5),D(".18"),D(0),False,False,False,"synthetic-cost"),
                       IntrabarPolicy.BOTH_PATHS,"Asia/Kolkata","crypto-24x7")
    count=0
    def stream():
        nonlocal count
        for bar in rows:
            count+=1
            if count%8==0 and not progress(min(99,count*99//(2*n))):raise Cancelled()
            yield bar
    if not progress(0):raise Cancelled()
    result=run_backtest(cfg,lambda:EMASupertrendExample(signal,ema_period=3,atr_period=2,
                        multiplier=D(2),exposure=D(".2")),stream,linear_contract=True,
                        dataset_manifest_sha256=manifest)
    if not progress(99):raise Cancelled()
    return {"kind":"reference_fixture","synthetic":True,"result_sha256":result.result_sha256,
            "result":to_wire(result)}
