"""Bounded worker-local cache for validated immutable browser CSV replay.

Only trusted browser adapter may supply this cache to the simulator. Cache entries
are completed indicator outputs for the identical input stream, not strategy state.
"""
from collections import OrderedDict,deque
from itertools import islice
from .historical import frames
from ..indicators import IndicatorBook,IndicatorSpec,StreamingIndicator

MAX_VALUES=250_000

class ReplayCache:
    def __init__(self):
        self.key=None;self.rows=None;self.series=OrderedDict();self.size=0
        self.reset_stats()
    def reset_stats(self):
        self.stats={"candle_hit":False,"indicator_hits":0,"indicator_misses":0,"indicator_updates_reused":0}
    def select(self,key):
        self.reset_stats()
        if key!=self.key:
            self.key=key;self.rows=None;self.series.clear();self.size=0
        else:self.stats["candle_hit"]=self.rows is not None
        return self.rows
    def get(self,spec):
        values=self.series.get(spec)
        if values is not None:self.series.move_to_end(spec)
        return values
    def reserve(self,n):
        if n>MAX_VALUES:return False
        while self.size+n>MAX_VALUES and self.series:
            _,v=self.series.popitem(last=False);self.size-=len(v)
        return self.size+n<=MAX_VALUES
    def put(self,spec,values):
        if spec in self.series:return
        if self.reserve(len(values)):
            self.series[spec]=tuple(values);self.size+=len(values)
    def book(self,definitions,limit):
        return CachedBook(self,definitions,limit)

class CachedBook(IndicatorBook):
    def __init__(self,cache,definitions,limit):
        super().__init__(definitions,limit)
        self.cache=cache;self.by_timeframe={};self.states={}
        # Limit total live recording + previously cached values. Evicted entries
        # already referenced by a book remain valid until that scenario finishes.
        remaining=MAX_VALUES
        for spec,(indicator,history) in self.entries.items():
            n=len(cache.rows)*60//spec.timeframe.seconds
            values=cache.get(spec)
            if values is not None:
                if len(values)!=n:raise ValueError("cached indicator length mismatch")
                cache.stats["indicator_hits"]+=1
                record=None
            else:
                cache.stats["indicator_misses"]+=1
                record=[] if n<=remaining else None
                if record is not None:remaining-=n
            state=[spec,indicator,history,values,record,0,n]
            self.states[spec]=state
            self.by_timeframe.setdefault(spec.timeframe.seconds,[]).append(state)
    def update(self,candle):
        for state in self.by_timeframe.get(candle.timeframe.seconds,()):
            spec,indicator,history,values,record,index,n=state
            # Only reveal the next value as its candle completes. The cache
            # contains a complete series but no future output enters history.
            expected=self.cache.rows[0].open_utc
            elapsed=(candle.close_utc-expected).total_seconds()
            if elapsed!=(index+1)*spec.timeframe.seconds or index>=n:
                raise ValueError("indicator cache replay clock mismatch")
            if values is not None:
                value=values[index];self.cache.stats["indicator_updates_reused"]+=1
            else:
                value=indicator.update(candle)
                if record is not None:
                    record.append(value)
                    if index+1==n:self.cache.put(spec,record);state[4]=None
            history.append(value);state[5]+=1
