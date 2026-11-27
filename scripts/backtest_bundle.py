"""Versioned, producer-side export of real backtest observations.
No strategy-specific settings. Capture after the strategy updates its indicator book.
"""
import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ARTIFACT="btc-analysis-backtest-v1"

def _wire(v):
    if isinstance(v,Decimal):return float(v)
    if isinstance(v,datetime):return v.isoformat()
    raise TypeError(type(v).__name__)

class IndicatorRecorder:
    def __init__(self,book,panels=None):
        self.book=book;self.specs=tuple(book.entries);self.definitions=[];self.series={}
        panels=panels or {}
        for i,d in enumerate(self.specs):
            id=f"indicator_{i}"
            # Generic catalog display semantics, overridable by producer metadata.
            panel=panels.get(d.name,"price" if d.base in {"ema","sma","vwap","bollinger","donchian"} or d.name=="supertrend.line" else "panel")
            self.definitions.append(dict(id=id,name=d.name,timeframe_minutes=d.timeframe.seconds//60,panel=panel,parameters=dict(d.parameters)))
            self.series[id]=[]
    def completed(self,candle):
        t=int(candle.close_utc.timestamp())
        for d,m in zip(self.specs,self.definitions):
            if d.timeframe!=candle.timeframe:continue
            value=self.book.get(d.name,d.timeframe,dict(d.parameters))[-1]
            self.series[m["id"]].append([t,None if value is None else float(value)])

def export_bundle(path,*,family,symbol,unit,start_utc,end_utc,execution_timeframe_minutes,signal_timeframe_minutes,costs,variants,recorder=None,indicator_definitions=None,indicator_series=None,data_provenance=None):
    """variants: [{key,name,parameters,summary,trades,events?}].
    trades use canonical Explorer fields; summary preserves original accounting.
    """
    if recorder is not None:
        if indicator_definitions is not None or indicator_series is not None:raise ValueError("choose recorder or explicit series")
        indicator_definitions,indicator_series=recorder.definitions,recorder.series
    if indicator_definitions is None or indicator_series is None:raise ValueError("declare indicator history explicitly, including [] and {} for no indicators")
    obj=dict(schema=1,family=family,symbol=symbol,unit=unit,start_utc=start_utc,end_utc=end_utc,execution_timeframe_minutes=execution_timeframe_minutes,signal_timeframe_minutes=signal_timeframe_minutes,costs=costs,source_commit=os.environ["GITHUB_SHA"],source_run_id=int(os.environ["GITHUB_RUN_ID"]),source_attempt=int(os.environ.get("GITHUB_RUN_ATTEMPT","1")),data_provenance=data_provenance or {},indicator_definitions=indicator_definitions,indicator_series=indicator_series,variants=variants)
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,default=_wire,allow_nan=False,separators=(",",":")),encoding="utf8")
