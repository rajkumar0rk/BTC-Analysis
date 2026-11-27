"""Original research EMA20, ATR and Supertrend implementation, moved unchanged.

Source: BTC-Analysis/scripts/replay_btc_ema_st_screenshot.py,
branch feature/vps-preliquidation-stops-20261120.
No historical archive or side effects required.
"""
import numpy as np
import pandas as pd

def rma(s,n):
 v=s.to_numpy(dtype=float);out=np.full(len(v),np.nan)
 valid=np.flatnonzero(~np.isnan(v));seed=valid[n-1]
 out[seed]=np.mean(v[valid[:n]])
 for i in range(seed+1,len(v)):
  out[i]=(out[i-1]*(n-1)+v[i])/n
 return pd.Series(out,index=s.index)

def indicators(x):
 prev=x.close.shift(1)
 tr=pd.concat([x.high-x.low,(x.high-prev).abs(),(x.low-prev).abs()],axis=1).max(axis=1)
 atr10=rma(tr,10);atr14=rma(tr,14)
 ema=x.close.ewm(alpha=2/21,adjust=False).mean()
 mid=(x.high+x.low)/2
 ub=(mid+3*atr10).to_numpy();lb=(mid-3*atr10).to_numpy()
 close=x.close.to_numpy();final_up=np.full(len(x),np.nan);final_lo=np.full(len(x),np.nan)
 direction=np.full(len(x),0,dtype=np.int8);st=np.full(len(x),np.nan)
 for i in range(len(x)):
  if np.isnan(ub[i]):continue
  if i==0 or np.isnan(final_up[i-1]):
   final_up[i]=ub[i];final_lo[i]=lb[i];direction[i]=1;st[i]=final_up[i];continue
  pu=final_up[i-1];pl=final_lo[i-1]
  final_up[i]=ub[i] if (ub[i]<pu or close[i-1]>pu) else pu
  final_lo[i]=lb[i] if (lb[i]>pl or close[i-1]<pl) else pl
  if direction[i-1]==1:direction[i]= -1 if close[i]>final_up[i] else 1
  else:direction[i]=1 if close[i]<final_lo[i] else -1
  st[i]=final_lo[i] if direction[i]==-1 else final_up[i]
 x=x.copy()
 x['ema']=ema;x['atr14']=atr14;x['st']=st;x['dir']=direction
 x['atr_ratio']=atr14/atr14.shift(1).rolling(20,min_periods=20).mean()
 x['volume_ratio']=x.volume/x.volume.shift(1).rolling(20,min_periods=20).mean()
 return x

