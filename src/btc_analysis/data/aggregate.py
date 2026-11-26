"""Causal streaming OHLCV aggregation. No incomplete/gapped bucket is emitted."""
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from .store import CoverageError
from ..contracts import Candle, Timeframe


def aggregate(candles, timeframe: Timeframe, *, as_of=None, strict=True, anchor=0):
    """UTC epoch-aligned bars, or explicit anchor. Session-specific anchors must be
    supplied by a reviewed calendar. Does not invent bars across market closures.
    Input must be same instrument, strictly chronological base candles.
    """
    if type(anchor) is not int or (as_of is not None and type(as_of) is not int):
        raise ValueError("anchor/as_of must be UTC epoch seconds")
    target=timeframe.seconds
    group=[]; bucket=None; prev=None; instrument=None; base=None
    def flush():
        if not group:
            return None
        first=group[0]; last=group[-1]
        start=int(first.open_utc.timestamp()); end=int(last.close_utc.timestamp())
        complete=start==bucket and end==bucket+target and len(group)==target//base
        if not complete:
            if strict:
                raise CoverageError(f"incomplete aggregate bucket {bucket}")
            return None
        with localcontext() as ctx:
            ctx.prec=50
            volume=sum((x.volume for x in group),Decimal(0))
        return Candle(instrument,timeframe,first.open_utc,last.close_utc,
                      first.open,max(x.high for x in group),min(x.low for x in group),
                      last.close,volume)
    for c in candles:
        t=int(c.open_utc.timestamp()); end=int(c.close_utc.timestamp())
        if as_of is not None and end>as_of:
            break
        if base is None:
            base=c.timeframe.seconds; instrument=c.instrument
            if target%base or anchor%base:
                raise ValueError("aggregate timeframe/anchor incompatible with source")
        if c.instrument!=instrument or c.timeframe.seconds!=base or (prev is not None and t<=prev):
            raise ValueError("mixed or nonchronological source")
        k=anchor+((t-anchor)//target)*target
        if bucket is not None and k!=bucket:
            out=flush()
            if out is not None:
                yield out
            group=[]
            if strict and k!=bucket+target:
                raise CoverageError("missing aggregate bucket")
        if group and t!=prev+base:
            # Missing within bucket: never emit it, even in lenient mode.
            if strict:
                raise CoverageError("gap inside aggregate bucket")
        bucket=k; group.append(c); prev=t
    if group:
        # The final currently forming bucket is withheld, not classified as a gap.
        if as_of is None or bucket+target<=as_of:
            out=flush()
            if out is not None:
                yield out
