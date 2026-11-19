#!/usr/bin/env python3
"""Fee sensitivity using EXACT same entry/exit ledgers, not a new signal backtest."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'analysis/btc_ema_st_screenshot_20261119'
def summ(df):
 net=df.net_usd.values
 positive=float(net[net>0].sum())
 negative=float(-net[net<0].sum())
 running=np.r_[0,net.cumsum()]
 return {'trades':len(df),'net_usd_1_contract':round(float(net.sum()),3),
  'net_points':round(float((net/.001).sum()),2),
  'wins':int((net>0).sum()),'losses':int((net<0).sum()),
  'win_rate_pct':round(float((net>0).mean()*100),2),
  'net_profit_factor':round(positive/negative,4) if negative>0 else None,
  'close_fee_usd':round(float(df.exit_fee_usd.sum()),3),
  'entry_fee_usd':round(float(df.entry_fee_usd.sum()),3),
  'gst_usd':round(float(df.gst_usd.sum()),3),
  'fee_waiver_qualified_trades':int(df.eligible.sum()),
  'max_closed_equity_drawdown_usd':round(float((np.maximum.accumulate(running)-running).max()),3)}
report={}
for mode in ('all_history','tv_last_10000_bars'):
 src=pd.read_csv(OUT/f'{mode}_trades.csv.gz')
 for tag,window in (('published_30min',30),('no_scalper',-1)):
  a=src.copy()
  a['eligible']=a.hold_minutes<=window
  a['exit_fee_usd']=np.where(a.eligible,0,a.exit_price*.001*.0005)
  a['gst_usd']=(a.entry_fee_usd+a.exit_fee_usd)*.18
  a['net_usd']=a.gross_points*.001-a.entry_fee_usd-a.exit_fee_usd-a.gst_usd
  a['exit_month_ist']=pd.to_datetime(a.exit_utc,utc=True).dt.tz_convert('Asia/Kolkata').dt.strftime('%Y-%m')
  m=a.groupby('exit_month_ist',sort=True).apply(lambda x:pd.Series(summ(x)),include_groups=False).reset_index()
  m['complete_month']=m.exit_month_ist<='2026-10'
  dest=f'{mode}_{tag}_monthly.csv'
  m.to_csv(OUT/dest,index=False)
  report[f'{mode}_{tag}']={**summ(a),'monthly_file':dest}
print(json.dumps(report,indent=2))
(OUT/'realistic_fee_sensitivity.json').write_text(json.dumps(report,indent=2))
