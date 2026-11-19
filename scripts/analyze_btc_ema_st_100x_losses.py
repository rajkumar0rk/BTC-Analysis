#!/usr/bin/env python3
"""Explain the four losing months by reading existing 100x position-level trade ledger.

No strategy parameters are modified; this is descriptive attribution ONLY.
"""
from pathlib import Path
import json
import pandas as pd
import numpy as np
OUT=Path('analysis/btc_ema_st_100x_20261119')
df=pd.read_csv(OUT/'last_10000_15m_threshold_trades.csv.gz')
df['entry_utc']=pd.to_datetime(df.entry_utc,utc=True)
df['exit_utc']=pd.to_datetime(df.exit_utc,utc=True)
df['month']=df.exit_utc.dt.tz_convert('Asia/Kolkata').dt.strftime('%Y-%m')
df['equity_change']=df.equity_after-df.equity_before
df['trade_return_pct']=100*df['equity_change']/df.equity_before.replace(0,np.nan)
df['gross_points']=np.where(df.side=='long',df.exit_price-df.entry_price,df.entry_price-df.exit_price)
fields=['entry_utc','exit_utc','side','reason','holding_minutes','entry_price',
    'exit_price','gross_points','qty_btc','initial_margin_usd',
    'equity_before','equity_after','trade_return_pct','equity_change',
    'entry_fee_usd','entry_gst_usd','exit_fee_usd','exit_gst_usd',
    'liquidation_fee_usd','liquidation_gst_usd','eligible_scalper']
res={}
for month in ['2026-08','2026-09','2026-10','2026-11']:
    z=df[df.month==month].copy()
    start=float(z.equity_before.iloc[0]);end=float(z.equity_after.iloc[-1])
    winners=z[z.equity_change>0]
    losers=z[z.equity_change<0]
    fees=z[['entry_fee_usd','entry_gst_usd','exit_fee_usd',
      'exit_gst_usd','liquidation_fee_usd','liquidation_gst_usd']].sum()
    top_losses=losers.nsmallest(5,'trade_return_pct')
    longest=z.sort_values('holding_minutes',ascending=False).head(3)
    reasc={}
    for key,v in z.groupby('reason'):
        reasc[key]=dict(count=len(v),total_wallet_delta_usd=round(float(v.equity_change.sum()),4))
    res[month]=dict(
      start_balance=round(start,4),end_balance=round(end,4),
      month_return_pct=round(100*(end/start-1),2),
      trades=len(z),wins=len(winners),losses=len(losers),
      total_winners_usd=round(float(winners.equity_change.sum()),4),
      total_losers_usd=round(float(losers.equity_change.sum()),4),
      total_gross_pnl_usd=round(float(z.gross_usd.sum()),4),
      fee_costs_usd={k:round(float(v),4) for k,v in fees.items()},
      qualifying_scalper_trades=int(z.eligible_scalper.sum()),
      liquidations=int((z.reason=='liquidation').sum()),
      liquidation_total_wallet_delta_usd=round(float(z[z.reason=='liquidation'].equity_change.sum()),4),
      stop_exit_total_wallet_delta_usd=round(float(z[z.reason.isin(['stop','initial_stop','trailing','stop_gap'])].equity_change.sum()),4),
      average_winner_pct_of_equity=round(float(winners.trade_return_pct.mean()),2) if len(winners) else None,
      average_loser_pct_of_equity=round(float(losers.trade_return_pct.mean()),2) if len(losers) else None,
      median_winner_pct=round(float(winners.trade_return_pct.median()),2) if len(winners) else None,
      median_loser_pct=round(float(losers.trade_return_pct.median()),2) if len(losers) else None,
      max_single_loss_pct=round(float(losers.trade_return_pct.min()),2) if len(losers) else None,
      max_single_gain_pct=round(float(winners.trade_return_pct.max()),2) if len(winners) else None,
      exit_reason_breakdown=reasc,
      worst_five_trades=[{k:(str(v) if isinstance(v,pd.Timestamp) else round(float(v),4) if isinstance(v,(float,np.floating)) else int(v) if isinstance(v,(np.integer,)) else v) for k,v in row.items()} for row in top_losses[fields].to_dict('records')]
    )
(OUT/'recent_month_loss_attribution.json').write_text(json.dumps(res,indent=2))
print(json.dumps(res,indent=2))
