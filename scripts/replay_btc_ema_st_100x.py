#!/usr/bin/env python3
"""100x isolated-margin ACCOUNT backtest of screenshot BTCUSD EMA20/ST strategy.

Uses SAME 15m OHLC entry / trailing assumptions as replay_btc_ema_st_screenshot.py
but sizes positions dynamically to available equity and simulates intrabar
margin liquidation on the assumed 15m OHLC path (NOT historical Mark Price).
Two forced-liquidation fills: threshold (optimistic) and bankruptcy (stress).
All outputs are simulated and not a TradingView parity / live execution claim.
"""
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from replay_btc_ema_st_screenshot import load, indicators

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/"analysis/btc_ema_st_100x_20261119"
OUT.mkdir(parents=True, exist_ok=True)
INITIAL_EQUITY=100.0
LEVERAGE=100
MAINTENANCE=0.0025
BTC_LOT=0.001
NOTIONAL_CAP_USD=100_000.0
TAKER=0.0005
GST=0.18
LIQUIDATION_PENALTY=0.0005
SCALPER_WINDOW_MIN=30
ACTIVATION_POINTS=150
DISTANCE_POINTS=50
PARAMS={
 "starting_equity_usd":INITIAL_EQUITY,"selected_leverage":LEVERAGE,
 "initial_margin_fraction":1/LEVERAGE,"maintenance_margin_fraction":MAINTENANCE,
 "btc_lot_size":BTC_LOT,"notional_cap_usd_for_unscaled_margin":NOTIONAL_CAP_USD,
 "taker_fee_fraction_per_side":TAKER,"gst_on_fees":GST,
 "liquidation_penalty_fraction":LIQUIDATION_PENALTY,
 "scalper_waiver_holding_minutes":SCALPER_WINDOW_MIN,
 "atr_stop_multiplier":2,"trailing_activation_points":ACTIVATION_POINTS,
 "trailing_distance_points":DISTANCE_POINTS,
 "entry_and_stop_chart_tf":"15m","signal_candle_close_fill":True,
 "pyramiding":0,"slippage_points":0,"funding_pct":0,
 "margin_mode":"isolated","auto_margin_top_up":False,
 "reinvest_profit_and_rescale_every_trade":True,
 "opening_fee_outside_isolated_margin":True
}

def path_exit(o,h,l,c,side,ep,stop,best,active,liq_price):
    """Check stops vs margin barrier along assumed historical OHLC path."""
    seq=(o,h,l,c) if h-o<o-l else (o,l,h,c)
    for a,b in zip(seq,seq[1:]):
        if side==1:
            protective=max(stop,liq_price)
            if a<=protective:
                isliq=(liq_price>=stop)
                return (a if a==o else protective),stop,best,active,("liquidation" if isliq else "stop_gap" if a==o else "stop")
        else:
            protective=min(stop,liq_price)
            if a>=protective:
                isliq=(liq_price<=stop)
                return (a if a==o else protective),stop,best,active,("liquidation" if isliq else "stop_gap" if a==o else "stop")
        favorable = (b>a) if side==1 else (b<a)
        if favorable:
            activation=ep+side*ACTIVATION_POINTS
            if not active and ((side==1 and b>=activation) or (side==-1 and b<=activation)):
                active=True;best=activation
            if active:
                best=max(best,b) if side==1 else min(best,b)
                candidate=best-side*DISTANCE_POINTS
                stop=max(stop,candidate) if side==1 else min(stop,candidate)
        else:
            protective=max(stop,liq_price) if side==1 else min(stop,liq_price)
            hit = (b<=protective) if side==1 else (b>=protective)
            if hit:
                isliq=(liq_price>=stop) if side==1 else (liq_price<=stop)
                return protective,stop,best,active,("liquidation" if isliq else "trailing" if active else "initial_stop")
    return None,stop,best,active,None

def fee_net(q,ep,xp,side,hold_minutes,reason,fill_mode):
    entry_fee=q*ep*TAKER
    entry_gst=entry_fee*GST
    if reason=="liquidation":
        liquidation_fee=q*xp*LIQUIDATION_PENALTY
        liquidation_gst=liquidation_fee*GST
        close_fee=0.0;close_gst=0.0;eligible=False
    else:
        liquidation_fee=0.0;liquidation_gst=0.0
        eligible=0<=hold_minutes<=SCALPER_WINDOW_MIN
        close_fee=0.0 if eligible else q*xp*TAKER
        close_gst=close_fee*GST
    gross=q*(xp-ep)*side
    net=gross-entry_fee-entry_gst-close_fee-close_gst-liquidation_fee-liquidation_gst
    return dict(gross_usd=gross,net_usd=net,
        entry_fee_usd=entry_fee,entry_gst_usd=entry_gst,
        exit_fee_usd=close_fee,exit_gst_usd=close_gst,
        liquidation_fee_usd=liquidation_fee,liquidation_gst_usd=liquidation_gst,
        eligible_scalper=eligible)

def run_one(df,start,fill_mode):
    a=df.reset_index()
    op=a.open.to_numpy();hi=a.high.to_numpy();lo=a.low.to_numpy()
    cl=a.close.to_numpy();ema=a.ema.to_numpy();atr=a.atr14.to_numpy()
    dr=a.dir.to_numpy();ar=a.atr_ratio.to_numpy();vr=a.volume_ratio.to_numpy()
    t=a.dt.to_numpy()
    balance=INITIAL_EQUITY;peak=INITIAL_EQUITY;maxdd=0.
    trades=[];state=None;skip_no_margin=0;max_notional=0;max_qty=0
    for i in range(max(start,36),len(a)):
        if state:
            s=state
            xp,s['sl'],s['best'],s['active'],reason=path_exit(op[i],hi[i],lo[i],cl[i],
                s['side'],s['entry_price'],s['sl'],s['best'],s['active'],s['liq_price'])
            if xp is None and ((s['side']==1 and dr[i]==1 and dr[i-1]==-1) or
                               (s['side']==-1 and dr[i]==-1 and dr[i-1]==1)):
                xp=float(cl[i]);reason='supertrend_flip'
            if xp is not None:
                if reason=="liquidation" and fill_mode=="bankruptcy":
                    xp=s['bankruptcy_price']
                hold=(i-s['entry_i'])*15
                fin=fee_net(s['qty'],s['entry_price'],xp,s['side'],hold,reason,fill_mode)
                balance=max(0.0, balance+fin['net_usd'])
                peak=max(peak,balance)
                maxdd=max(maxdd,1-balance/peak if peak>0 else 1)
                trades.append(dict(
                    entry_utc=str(pd.Timestamp(t[s['entry_i']])+pd.Timedelta(minutes=15)),
                    exit_utc=str(pd.Timestamp(t[i])+pd.Timedelta(minutes=15)),
                    entry_price=s['entry_price'],exit_price=xp,
                    qty_btc=s['qty'],qty_contracts=s['qty_contracts'],
                    side='long' if s['side']==1 else 'short',reason=reason,
                    holding_minutes=hold,initial_margin_usd=s['initial_margin'],
                    liquidation_trigger_price=s['liq_price'],
                    equity_before=s['equity_before'],equity_after=balance,
                    **fin))
                state=None
        if state is None and np.isfinite(ema[i]) and np.isfinite(atr[i]) and np.isfinite(ar[i]) and np.isfinite(vr[i]):
            side=0
            if ar[i]>=1 and vr[i]>=1.5:
                if dr[i]==-1 and dr[i-1]==-1 and lo[i]<=ema[i] and cl[i]>ema[i]:side=1
                elif dr[i]==1 and dr[i-1]==1 and hi[i]>=ema[i] and cl[i]<ema[i]:side=-1
            if side:
                ep=float(cl[i])
                # 100x maximum notional, but have to pay taker entry fees + GST
                # outside initial margin. Under 100k tier margin=1% at 100x.
                unit_cost=BTC_LOT*ep*(1/LEVERAGE+TAKER*(1+GST))
                by_equity=math.floor((balance+1e-9)/unit_cost)
                by_tier=math.floor(NOTIONAL_CAP_USD/(ep*BTC_LOT))
                contracts=min(by_equity,by_tier)
                if contracts<1:
                    skip_no_margin+=1
                else:
                    q=contracts*BTC_LOT
                    notional=ep*q;im=notional/LEVERAGE
                    # liquidation: margin + unrealized PnL == 0.25% of current notional.
                    # Mark Price is unavailable, use historical 15m OHLC as proxy.
                    liq=(ep-im/q)/(1-MAINTENANCE) if side==1 else (ep+im/q)/(1+MAINTENANCE)
                    bankruptcy=ep-im/q*side
                    slpts=round(2*atr[i]/0.5)*0.5
                    sl=ep-side*max(slpts,0.5)
                    state=dict(side=side,qty=q,qty_contracts=contracts,entry_price=ep,
                        entry_i=i,sl=sl,best=ep,active=False,
                        liq_price=liq,bankruptcy_price=bankruptcy,
                        equity_before=balance,initial_margin=im)
                    max_notional=max(max_notional,notional)
                    max_qty=max(max_qty,q)
    z=pd.DataFrame(trades)
    if len(z):
        z['month_ist']=pd.to_datetime(z.exit_utc,utc=True).dt.tz_convert('Asia/Kolkata').dt.strftime('%Y-%m')
    return z,dict(ending_equity_usd=round(balance,4),
        starting_equity_usd=INITIAL_EQUITY,
        net_profit_usd=round(balance-INITIAL_EQUITY,4),
        return_pct=round((balance/INITIAL_EQUITY-1)*100,4),
        total_trades=len(z),
        liquidations=int((z.reason=='liquidation').sum()) if len(z) else 0,
        max_closed_equity_drawdown_pct=round(maxdd*100,2),
        skipped_signals_insufficient_margin=skip_no_margin,
        max_position_notional_usd=round(max_notional,2),
        max_position_btc=round(max_qty,3),
        has_open_position=state is not None,
        last_date_utc=str(t[-1]),start_date_utc=str(t[start]),liquidation_fill_mode=fill_mode)

def monthly(z):
    if z.empty:return pd.DataFrame()
    rows=[]
    for period,g in z.groupby('month_ist',sort=True):
        begin=float(g.equity_before.iloc[0]);end=float(g.equity_after.iloc[-1])
        profit=float(g.net_usd.sum())
        rows.append(dict(month_ist=period,trades=len(g),
            ending_equity_usd=round(end,4),
            starting_equity_usd=round(begin,4),
            net_usd=round(profit,4),
            return_pct=round(100*profit/begin,2) if begin>0 else None,
            liquidations=int((g.reason=='liquidation').sum()),
            winning_trades=int((g.net_usd>0).sum()),
            losing_trades=int((g.net_usd<0).sum()),
            completed_month=period<='2026-10'))
    return pd.DataFrame(rows)

def main():
    bars,m,n=load()
    x=indicators(bars)
    result={'settings':PARAMS,'source_minute_bars':n,
            'source_manifest_generated_utc':m['generated_at_utc'],
            'caveat':'Simulated 15m OHLC only; exchange liquidates by Mark Price not traded OHLC; no spread/slippage/funding, no auto-margin top-ups; 100x isolated. Unrealized intra-trade drawdown omitted.'}
    for period,start in [('all_history',0),('last_10000_15m',max(0,len(x)-10000))]:
        for mode in ('threshold','bankruptcy'):
            key=f'{period}_{mode}'
            trades,info=run_one(x,start,mode)
            trades.to_csv(OUT/f'{key}_trades.csv.gz',index=False,compression='gzip')
            month=monthly(trades)
            month.to_csv(OUT/f'{key}_monthly.csv',index=False)
            result[key]=info
            print('\\n',key,json.dumps(info))
            print(month.to_string(index=False))
    (OUT/'summary.json').write_text(json.dumps(result,indent=2))
    print('Backtest finished; outputs:',OUT)

if __name__=='__main__':main()
