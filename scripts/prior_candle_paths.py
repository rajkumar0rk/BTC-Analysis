"""Past-only direction estimators. Each estimate uses candles strictly before i."""
import numpy as np
import pandas as pd
METHODS=("COLOR","D1","D3","D5","MOMENTUM","EMA_SLOPE","STRUCTURE")
def directions(frame):
    o,h,l,c=(frame[k].astype(float) for k in ("open","high","low","close"))
    side=np.sign(c-o)
    ema=c.ewm(span=5,adjust=False).mean()
    hh=(h>h.shift(1))&(l>l.shift(1))
    ll=(h<h.shift(1))&(l<l.shift(1))
    return dict(D1=side.shift(1),D3=np.sign(side.rolling(3).sum()).shift(1),
                D5=np.sign(side.rolling(5).sum()).shift(1),
                MOMENTUM=np.sign(c-c.shift(5)).shift(1),
                EMA_SLOPE=np.sign(ema.diff()).shift(1),
                STRUCTURE=(hh.astype(int)-ll.astype(int)).shift(1))
def low_first(method,row,guess):
    o,h,l,c=row[:4]
    if method=="COLOR":return c>o or (c==o and o-l<=h-o)
    # Ties: fixed low-first; no use of current extremes or close in prediction.
    return not (guess<0)
