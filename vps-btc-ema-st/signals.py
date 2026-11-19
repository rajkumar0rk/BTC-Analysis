"""Causal 15m signal with EXACT research indicator implementation imported.

Source: BTC-Analysis/scripts/replay_btc_ema_st_screenshot.py : indicators()
The live candle is never used; no intrabar entry or lookahead.
"""
import sys,time,math
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT/"scripts") not in sys.path:sys.path.insert(0,str(ROOT/"scripts"))
from replay_btc_ema_st_screenshot import indicators

BAR_SECONDS=900
def closed_bars(raw,now=None):
    now=time.time() if now is None else now
    # Give exchange historical feed 10 seconds to finalize closed candle.
    current_start=int((now-10)//BAR_SECONDS)*BAR_SECONDS
    rows=[]
    for x in raw:
        epoch=int(x["time"])
        if epoch+BAR_SECONDS<=current_start:
            rows.append((epoch,float(x["open"]),float(x["high"]),
                        float(x["low"]),float(x["close"]),float(x["volume"])))
    rows=sorted(set(rows),key=lambda x:x[0])
    if len(rows)<100:
        raise ValueError("Insufficient closed 15m candle history (need >=100)")
    if any(rows[i][0]-rows[i-1][0]!=BAR_SECONDS for i in range(1,len(rows))):
        raise ValueError("Missing or duplicate historical 15m candles")
    if rows[-1][0] != current_start-BAR_SECONDS:
        raise ValueError("Latest completed 15m bar missing or stale")
    df=pd.DataFrame(rows,columns=["time","open","high","low","close","volume"])
    df["dt"]=pd.to_datetime(df.pop("time"),unit="s",utc=True)
    df=df.set_index("dt")
    return df
def signal(frame):
    f=indicators(frame)
    x=f.iloc[-1]
    prior=f.iloc[-2]
    necessary=["ema","atr14","atr_ratio","volume_ratio"]
    if not all(math.isfinite(float(x[k])) for k in necessary):
        return None
    if x.atr_ratio<1.0 or x.volume_ratio<1.5:return None
    direction=int(x["dir"])
    if direction==int(prior["dir"])==-1 and x.low<=x.ema and x.close>x.ema:
        side="buy"
    elif direction==int(prior["dir"])==1 and x.high>=x.ema and x.close<x.ema:
        side="sell"
    else:return None
    return {"bar_ts":int(frame.index[-1].timestamp()),"side":side,
            "signal_close":float(x.close),"atr14":float(x.atr14),
            "stop_distance_points":round(float(2*x.atr14)*2)/2,
            "atr_ratio":float(x.atr_ratio),"volume_ratio":float(x.volume_ratio)}
def quantize_stop(price,tick,side):
    # For long stop round up (closer); short stop round down (closer).
    return (math.ceil((price-1e-9)/tick)*tick if side=="buy"
            else math.floor((price+1e-9)/tick)*tick)
def size_contracts(price,contract_value,trade_margin,leverage):
    if min(price,contract_value,trade_margin,leverage)<=0:raise ValueError("Bad size inputs")
    return max(0,math.floor(trade_margin*leverage/(price*contract_value)+1e-10))
def stop_safe(entry,stop,side,leverage,maintenance_fraction,buffer_fraction):
    # Conservative proxy, NOT actual exchange mark-price liquidation formula.
    im=1/leverage
    distance=abs(entry-stop)/entry
    permitted=im-maintenance_fraction-buffer_fraction
    direction_ok=(stop<entry if side=="buy" else stop>entry)
    return direction_ok and permitted>0 and distance<permitted
