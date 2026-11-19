#!/usr/bin/env python3
"""Replay screenshot BTCUSD EMA20/Supertrend strategy using verified Delta India 1m candles.
Historical broker-emulator approximation: 15m open -> nearer extreme -> farther extreme -> close.
No Bar Magnifier, latency, spreads, actual funding or slippage. Research use only.
"""
import hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data/delta_india/BTCUSD/1m'
OUT=ROOT/'analysis/btc_ema_st_screenshot_20261119'
OUT.mkdir(parents=True,exist_ok=True)
PARAMS={
 'entry_tf':'15m','stop_monitoring_tf':'15m','supertrend_atr':10,'supertrend_factor':3,
 'ema_length':20,'pullback_mode':'EMA20','require_st_shape':True,'st_wick_only':True,
 'stop_mode':'Auto','initial_atr_length':14,'initial_atr_multiplier':2,
 'st_stop_buffer_points':50,'trailing_master':True,'trailing_mode':'Fixed Points (Original)',
 'enable_fixed_distance':True,'activation_points':150,'trailing_distance_points':50,
 'enable_additional_trailing_stop':False,'additional_trailing_stop_points':100,
 'atr_trailing_length':14,'atr_trailing_factor':2,'atr_trailing_activation':200,
 'st_trailing_offset':50,'st_trailing_activation':0,
 'filter_mode':'Both','volatility_atr_length':14,'atr_baseline_candles':20,
 'enable_min_volatility':True,'min_volatility_x':1.0,
 'enable_max_volatility':False,'max_volatility_x':1.0,
 'volume_baseline_candles':20,'enable_min_volume':True,'min_volume_x':1.5,
 'enable_max_volume':False,'max_volume_x':20,
 'btc_per_contract':0.001,'contracts':1,'entry_fill':'Taker','exit_fill':'Taker',
 'maker_fee_pct':0.02,'taker_fee_pct':0.05,'gst_pct':18,'scalper_enabled':True,
 'offer_active_full_history':True,'offer_qualifying_minutes':100000,
 'signed_funding_per_8h_pct':0,'voucher_informational':True,'monthly_voucher_cap_usd':100,
 'tick_size_usd':0.5,'default_calc_bars_count':10000,'assumed_slippage_points':0
}

def load():
 m=json.loads((DATA/'manifest.json').read_text())
 frames=[];n=0
 for p in m['partitions']:
  path=DATA/p['file']
  assert path.is_file(),path
  assert hashlib.sha256(path.read_bytes()).hexdigest()==p['sha256_gzip'],path
  assert p['missing_minutes']==0,(path,'missing minutes')
  x=pd.read_csv(path,compression='gzip')
  assert len(x)==p['observed_candles'],path
  assert {'time','open','high','low','close','volume'}.issubset(x.columns),x.columns
  frames.append(x[['time','open','high','low','close','volume']]);n+=len(x)
 df=pd.concat(frames,ignore_index=True)
 ts=df['time'].to_numpy(dtype=np.int64)
 assert np.all(np.diff(ts)==60),'1m history has gaps or duplicates'
 df['dt']=pd.to_datetime(df.time,unit='s',utc=True)
 df=df.set_index('dt')
 bars=df.resample('15min',origin='epoch',label='left',closed='left').agg(
   {'open':'first','high':'max','low':'min','close':'last','volume':'sum','time':'count'})
 assert np.all(bars.time.to_numpy()==15),'Incomplete 15m bars'
 return bars.drop(columns='time'),m,n

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

def simulate_bar(o,h,l,c,side,ep,sl,best,active):
 seq=(o,h,l,c) if h-o<o-l else (o,l,h,c)
 activation=ep+side*PARAMS['activation_points'];distance=PARAMS['trailing_distance_points']
 for a,b in zip(seq,seq[1:]):
  if (side==1 and a<=sl) or (side==-1 and a>=sl):
   return (a if a==o else sl),sl,best,active,'stop_gap' if a==o else 'stop'
  favorable=(b>a) if side==1 else (b<a)
  if favorable:
   if (not active) and (b>=activation if side==1 else b<=activation):
    active=True;best=activation
   if active:
    best=max(best,b) if side==1 else min(best,b)
    candidate=best-side*distance
    sl=max(sl,candidate) if side==1 else min(sl,candidate)
  else:
   if (side==1 and b<=sl) or (side==-1 and b>=sl):
    return sl,sl,best,active,'trailing' if active else 'initial_stop'
 return None,sl,best,active,None

def replay(x,start):
 p=PARAMS
 a=x.reset_index();t=a['dt'].to_numpy();op=a.open.to_numpy();hi=a.high.to_numpy();lo=a.low.to_numpy();cl=a.close.to_numpy()
 ema=a.ema.to_numpy();atr=a.atr14.to_numpy();dr=a.dir.to_numpy()
 ar=a.atr_ratio.to_numpy();vr=a.volume_ratio.to_numpy()
 events=[];position=0;entry_price=0;entry_i=0;sl=0;best=0;active=False
 tick=p['tick_size_usd']
 for i in range(max(start,36),len(a)):
  if position:
   xp,sl,best,active,reason=simulate_bar(op[i],hi[i],lo[i],cl[i],position,entry_price,sl,best,active)
   if xp is None and ((position==1 and dr[i]==1 and dr[i-1]==-1) or (position==-1 and dr[i]==-1 and dr[i-1]==1)):
    xp=float(cl[i]);reason='supertrend_flip'
   if xp is not None:
    dire=position;gross_pts=(xp-entry_price)*dire
    btc=p['contracts']*p['btc_per_contract'];hold_min=(i-entry_i)*15
    eligible=p['scalper_enabled'] and p['offer_active_full_history'] and hold_min<=p['offer_qualifying_minutes']
    fee_entry=entry_price*btc*p['taker_fee_pct']/100
    fee_exit=0 if eligible else xp*btc*p['taker_fee_pct']/100
    gst=(fee_entry+fee_exit)*p['gst_pct']/100
    net_usd=gross_pts*btc-fee_entry-fee_exit-gst
    events.append({'entry_utc':str(pd.Timestamp(t[entry_i])+pd.Timedelta(minutes=15)),
     'exit_utc':str(pd.Timestamp(t[i])+pd.Timedelta(minutes=15)),
     'side':'long' if dire==1 else 'short','entry_price':entry_price,'exit_price':float(xp),
     'gross_points':float(gross_pts),'net_points':float(net_usd/btc),'net_usd':float(net_usd),
     'entry_fee_usd':float(fee_entry),'exit_fee_usd':float(fee_exit),'gst_usd':float(gst),
     'scalper_eligible':eligible,'hold_minutes':hold_min,'exit_reason':reason})
    position=0
  if position==0 and np.isfinite(ema[i]) and np.isfinite(atr[i]) and np.isfinite(ar[i]) and np.isfinite(vr[i]):
   if ar[i]>=1.0 and vr[i]>=1.5:
    if dr[i]==-1 and dr[i-1]==-1 and lo[i]<=ema[i] and cl[i]>ema[i]:position=1
    elif dr[i]==1 and dr[i-1]==1 and hi[i]>=ema[i] and cl[i]<ema[i]:position=-1
    if position:
     entry_i=i;entry_price=float(cl[i]);slpts=max(1,round(2*atr[i]/tick))*tick
     sl=entry_price-position*slpts;best=entry_price;active=False
 return pd.DataFrame(events),{'has_open_trade':bool(position),'last_bar_time_utc':str(t[-1]),
   'start_bar':start,'start_date_utc':str(t[start])}

def summarize(df):
 if df.empty:return {'trades':0}
 net=df.net_usd.to_numpy();n=len(net)
 d=np.maximum.accumulate(np.r_[0,np.cumsum(net)])-np.r_[0,np.cumsum(net)]
 wins=net[net>0].sum();losses=-net[net<0].sum()
 return {'trades':n,'net_wins':int((net>0).sum()),'net_losses':int((net<0).sum()),
 'net_win_rate_pct':round(float((net>0).mean()*100),2),
 'profit_factor_net':round(float(wins/losses),4) if losses>0 else None,
 'gross_points':round(float(df.gross_points.sum()),2),
 'net_points':round(float(df.net_points.sum()),2),
 'net_usd_1_contract':round(float(net.sum()),3),
 'entry_fees_usd':round(float(df.entry_fee_usd.sum()),3),
 'exit_fees_usd':round(float(df.exit_fee_usd.sum()),3),
 'gst_usd':round(float(df.gst_usd.sum()),3),
 'eligible_scalper_trades':int(df.scalper_eligible.sum()),
 'max_closed_equity_drawdown_usd':round(float(d.max()),3),
 'average_net_points_per_trade':round(float(df.net_points.mean()),2)}

def run():
 bars,manifest,minute_count=load();x=indicators(bars)
 outputs={'settings':PARAMS,'dataset':{'source':manifest['source'],
  'manifest_generated_at_utc':manifest['generated_at_utc'],
  'minute_candles':minute_count,'15m_candles':len(bars),
  'first_15m':str(bars.index[0]),'last_15m':str(bars.index[-1])},
  'replay_note':'TradingView four-tick historical OHLC path; no Bar Magnifier, spread, slippage, realized funding or leverage. Execution approximation, not identical to TradingView.'}
 for name,start in [('all_history',0),('tv_last_10000_bars',max(0,len(x)-10000))]:
  trades,meta=replay(x,start)
  trades.to_csv(OUT/f'{name}_trades.csv.gz',index=False,compression='gzip')
  if len(trades):
   times=pd.to_datetime(trades.exit_utc,utc=True).dt.tz_convert('Asia/Kolkata')
   trades['exit_month_ist']=times.dt.strftime('%Y-%m')
   mm=trades.groupby('exit_month_ist',sort=True).apply(
    lambda z:pd.Series(summarize(z)),include_groups=False).reset_index()
   mm['complete_month']=mm.exit_month_ist<='2026-10'
  else:mm=pd.DataFrame()
  mm.to_csv(OUT/f'{name}_monthly.csv',index=False)
  outputs[name]={**summarize(trades),**meta,'monthly_file':f'{name}_monthly.csv'}
  print('\n########',name,'########')
  print(json.dumps(outputs[name],indent=2));print(mm.to_string(index=False))
 (OUT/'summary.json').write_text(json.dumps(outputs,indent=2))
 print('\nRESULTS_IN_DIR',OUT)

if __name__=='__main__':run()
