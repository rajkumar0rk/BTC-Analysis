"""Standalone synthetic-only QA. No historical return claims are made here."""
import pandas as pd
import numpy as np
from run_all import Book, repair_minute_in_memory, make_hourly, daily_with_warmup, self_test


def run():
    self_test()
    times=pd.date_range('2025-01-01',periods=180,freq='min',tz='UTC')
    values=np.linspace(100,101,len(times))
    minute=pd.DataFrame({'open':values,'high':values+1,'low':values-1,
                         'close':values+.01,'volume':np.ones(len(times))},index=times)
    h=make_hourly(minute,pd.Series(.6,index=pd.date_range('2025-01-01',periods=3,freq='h',tz='UTC')))
    assert len(h)==3 and (h.minutes==60).all()
    d,info=daily_with_warmup(minute,fetch=False)
    assert d.minutes.iloc[0]==180
    assert d.sma200.isna().all(), 'No pre-2025 warmup must not become an invented SMA200'
    now=pd.Timestamp('2026-01-01',tz='UTC')
    b=Book(10_000,.0005,.0002,.18,.001,False,2.)
    b.open('t',1,100,10,now)
    b.fund(.0001,100,now)
    assert b.cash<10000
    b.close('t',101,now+pd.Timedelta(minutes=31),'time')
    assert b.trades[0]['funding_proxy_usd']>0
    assert not b.trades[0]['scalper_fee_waiver']
    print('PASS: synthetic accounting, resampling, warmup veto, tax, funding proxy')


if __name__=='__main__':run()