#!/usr/bin/env python3
"""Independent MacroCore V1 reproduction on READ-ONLY BTC-Analysis Delta candles.

This is NOT the full CryptoQuantix portfolio: TrendBreakdown requires taker buy
volume not in Delta's OHLCV archive; FundingSqueeze requires a point-in-time
settlement/cashflow model. The optional Delta funding-rate proxy is NOT a ledger.

No code reads prior BTC-Analysis strategy results. No data is changed in-place.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from datetime import timezone
import numpy as np
import pandas as pd

START = pd.Timestamp('2025-01-01', tz='UTC')
END = pd.Timestamp('2026-11-01', tz='UTC')
DAY_MINUTES = 1440


def data_audit(root: Path, through='2026-10'):
    """Validate source partitions without decompressing; use original manifest."""
    root = root.resolve()
    d = root / 'data/delta_india/BTCUSD/1m'
    manifest = json.loads((d / 'manifest.json').read_text())
    entries = []
    for p in manifest['partitions']:
        name = p['file']
        if not (name.startswith('2025-') or name.startswith('2026-')) or name[:7] > through:
            continue
        f = d / name
        if not f.is_file():
            raise FileNotFoundError(f'Archive partition missing: {f}')
        actual = hashlib.sha256(f.read_bytes()).hexdigest()
        expected = p['sha256_gzip']
        if actual != expected:
            raise ValueError(f'SHA-256 checksum mismatch for {name}')
        entries.append(dict(month=name[:7], expected=p['expected_minutes'], observed=p['observed_candles'],
                            missing=p['missing_minutes'], sha256=actual, bytes=f.stat().st_size))
    if len(entries) != 22:
        raise ValueError(f'Expected 22 monthly partitions Jan 2025–Oct 2026, got {len(entries)}')
    return entries


def read_history(root: Path, entries):
    d = root / 'data/delta_india/BTCUSD/1m'
    frames = []
    for e in entries:
        p = d / (e['month'] + '.csv.gz')
        f = pd.read_csv(p, compression='gzip', usecols=['time', 'open', 'high', 'low', 'close', 'volume'])
        if len(f) != e['observed']:
            raise ValueError(f'Unexpected row count in {p}: {len(f)} vs manifest {e["observed"]}')
        f['time'] = pd.to_datetime(f['time'].astype('int64'), unit='s', utc=True)
        f = f.set_index('time').sort_index()
        if not f.index.is_unique or (f.index.second != 0).any():
            raise ValueError(f'Duplicate or irregular timestamps in {p}')
        if not np.isfinite(f.to_numpy(dtype=float)).all():
            raise ValueError(f'Invalid numbers in {p}')
        invalid = (f['low'] <= 0) | (f['high'] < f[['open','close','low']].max(axis=1)) | (f['low'] > f[['open','close','high']].min(axis=1))
        if invalid.any():
            raise ValueError(f'Invalid OHLC candles in {p}')
        frames.append(f)
    m = pd.concat(frames).sort_index()
    if not m.index.is_unique:
        raise ValueError('Duplicate timestamp across partitions')
    return m


def prepare_daily(minute: pd.DataFrame):
    bars = minute.resample('1D', closed='left', label='left').agg(
        open=('open','first'), high=('high','max'), low=('low','min'),
        close=('close','last'), volume=('volume','sum'), minutes=('close','count'))
    bars = bars.loc[START:END - pd.Timedelta(days=1)].copy()
    expected = pd.date_range(START, END, freq='1D', inclusive='left')
    bars = bars.reindex(expected)
    bad = bars['minutes'].ne(DAY_MINUTES)
    # Do not trade past any missing minute/day; no invented candles.
    if bad.any():
        first_bad = bad[bad].index[0]
        clean = bars.loc[bars.index < first_bad].copy()
    else:
        first_bad = None
        clean = bars.copy()
    if len(clean) == 0:
        raise ValueError('No complete daily candles available')
    daily_returns = clean['close'].pct_change()
    clean['sma200'] = clean['close'].rolling(200, min_periods=200).mean()
    prev_close = clean['close'].shift(1)
    tr = pd.concat([(clean['high']-clean['low']), (clean['high']-prev_close).abs(),
                    (clean['low']-prev_close).abs()], axis=1).max(axis=1)
    clean['atr20'] = tr.rolling(20, min_periods=20).mean()
    clean['rv30'] = daily_returns.rolling(30, min_periods=30).std() * math.sqrt(365)
    return clean, first_bad


def funding_proxy(root: Path):
    """Delta FUNDING:BTCUSD candle CLOSE values, not real settled cashflows."""
    d = root / 'data/delta_india/BTCUSD/institutional/history/funding_1h'
    frames = []
    for key in pd.period_range('2025-01', '2026-10', freq='M'):
        path = d / (str(key) + '.csv.gz')
        if not path.exists():
            continue
        df = pd.read_csv(path, compression='gzip', usecols=['time', 'close'])
        df['time'] = pd.to_datetime(df['time'].astype('int64'), unit='s', utc=True)
        frames.append(df.set_index('time')['close'].astype(float))
    if not frames:
        raise ValueError('Funding-rate proxy files not found')
    f = pd.concat(frames).sort_index()
    if not f.index.is_unique:
        raise ValueError('Duplicate funding observations')
    # Settlement assumption is exactly 00/08/16 UTC. Last CLOSED hour only.
    shifted = f.shift(1, freq='1h')
    settled = shifted[shifted.index.hour.isin([0, 8, 16])]
    # Delta history source displays rates in PERCENT: 0.01 is 0.01%.
    return (settled / 100.0).groupby(settled.index.floor('D')).sum(min_count=3)


def simulate(d: pd.DataFrame, *, capital=10000., fee_side=.001, slip_side=.0005,
             gst=.18, target_vol=.30, funding=None):
    """Daily signal / next-open fills; futures mark-to-market; 25% intraday guard.

    Reproduces MacroCore's SMA200 entry, 5xATR20 Chandelier exit and 30%
    annual-volatility exposure sizing. 1m data are used to validate complete days
    and calculate the daily low; the first touch may have worse live fills.
    """
    cash=float(capital)  # Account equity, with futures PnL credited daily.
    qty=0.0
    entry=0.0
    max_close=0.0
    exit_next=False
    daylog=[]
    fills=[]
    closed=[]
    position_equity_start=None
    position_entry_day=None
    prev_close=None
    for day, r in d.iterrows():
        o,h,l,c=map(float,[r['open'],r['high'],r['low'],r['close']])
        day_fee=day_gst=day_slip=day_funding=0.0
        signal_ready=bool(pd.notna(r['sma200']) and pd.notna(r['atr20']))
        # Every day opens using signals only from yesterday's completed data.
        if prev_close is not None and qty:
            cash+=qty*(o-prev_close)
        yesterday=d.index.get_loc(day)-1
        yr=d.iloc[yesterday] if yesterday>=0 else None
        previous_ready=bool(yr is not None and pd.notna(yr['sma200']) and pd.notna(yr['rv30']))
        expo=0.
        if previous_ready:
            rv=float(yr['rv30'])
            expo=1. if rv<=0 or not math.isfinite(rv) else min(1.,target_vol/rv)
            expo=min(1.,max(0.,round(expo/.25)*.25))

        def trade_to(new_qty, raw_px, why):
            nonlocal cash,qty,day_fee,day_gst,day_slip
            nonlocal position_equity_start, position_entry_day
            delta=new_qty-qty
            if abs(delta)<1e-12:
                return
            is_entry = qty == 0 and new_qty > 0
            is_exit = qty > 0 and new_qty == 0
            if is_entry:
                position_equity_start=float(cash)
                position_entry_day=day
            notional=abs(delta)*raw_px
            f=notional*fee_side
            s=notional*slip_side
            tax=f*gst
            cash-=(f+s+tax)
            day_fee+=f;day_slip+=s;day_gst+=tax
            fills.append({'time':str(day), 'action':'BUY' if delta>0 else 'SELL',
                          'reason':why,'price':raw_px,'delta_btc':delta,'fee':f,
                          'gst':tax,'slippage':s})
            qty=new_qty
            if is_exit:
                net=cash-position_equity_start
                closed.append({'entry_date':str(position_entry_day), 'exit_date':str(day),
                               'net_pnl_usd':net, 'win':net>0, 'reason':why})
                position_equity_start=None
                position_entry_day=None

        # Exit based on yesterday's chandelier signal; no same-open re-entry.
        just_exited=False
        if qty and exit_next:
            trade_to(0.,o,'chandelier_next_open')
            entry=max_close=0.;just_exited=True
        exit_next=False
        # Enter when yesterday's CLOSED day passed SMA200.
        if not qty and not just_exited and previous_ready and yr['close']>yr['sma200'] and expo>0:
            desired=cash*expo/o
            if desired>0:
                trade_to(desired,o,'sma200_entry_next_open')
                entry=o;max_close=float(yr['close'])
        # Rebalance only if a position remains; target exposure based on prior day.
        elif qty and not just_exited and previous_ready:
            desired=max(0.,cash*expo/o)
            trade_to(desired,o,'vol_target_rebalance')

        # Intraday crash protection at original entry*0.75; assume stop is
        # worse of stop and an opening gap, still excludes L1 order-book impact.
        if qty and l<=entry*.75:
            stop_fill=min(o,entry*.75)
            cash+=qty*(stop_fill-o)
            trade_to(0.,stop_fill,'disaster_stop')
            entry=max_close=0.
        elif qty:
            cash+=qty*(c-o)
            max_close=max(max_close,c)
            if signal_ready and c<max_close-5.*float(r['atr20']):
                exit_next=True

        # Optional indicative cashflow only. Funding rate observations are NOT
        # confirmed payments; approximation uses daily close for notional.
        if funding is not None and qty and day in funding.index:
            rate=funding.loc[day]
            if pd.notna(rate):
                day_funding=qty*c*float(rate)
                cash-=day_funding
        equity=cash
        daylog.append({'date':day, 'equity':equity, 'qty_btc':qty, 'ready':signal_ready,
                       'fee':day_fee,'gst':day_gst,'slippage':day_slip,
                       'funding_proxy':day_funding,'open':o,'close':c})
        prev_close=c
    return pd.DataFrame(daylog).set_index('date'),pd.DataFrame(fills),pd.DataFrame(closed)


def monthly_stats(daily, source_months, first_bad, starting_equity):
    rows=[]
    for j,mm in enumerate(pd.period_range('2025-01','2026-10',freq='M')):
        key=str(mm)
        observed=next((x for x in source_months if x['month']==key),None)
        z=daily[daily.index.strftime('%Y-%m')==key]
        end_month=pd.Timestamp((mm+1).start_time,tz='UTC')
        first_month=pd.Timestamp(mm.start_time,tz='UTC')
        full=bool(observed and observed['missing']==0 and len(z)==int((end_month-first_month).days))
        # A SMA200 based on missing 2024 history is NOT a valid flat return.
        warmed=bool(len(z) and z['ready'].all())
        status='VALID' if full and warmed else ('INCOMPLETE_DATA' if not full else 'WARMUP_INSUFFICIENT')
        # Jan-Jul 2025 are unavailable as full, unbiased monthly tests.
        if len(z):
            month_end=float(z.equity.iloc[-1])
            previous=daily[daily.index<first_month]
            beginning=float(previous.equity.iloc[-1]) if len(previous) else float(starting_equity)
            ret=100*(month_end/beginning-1)
            fee=z.fee.sum();gst=z.gst.sum();slip=z.slippage.sum();fp=z.funding_proxy.sum()
        else:
            ret=fee=gst=slip=fp=None
        rows.append({'month':key,'status':status,'candles_observed':observed['observed'] if observed else None,
                     'candles_missing':observed['missing'] if observed else None,
                     'days_simulated':len(z),'net_return_pct':ret if status=='VALID' else None,
                     'diagnostic_partial_return_pct':ret,'fees_usd':fee,'gst_usd':gst,
                     'slippage_usd':slip,'indicative_funding_usd':fp})
    return pd.DataFrame(rows)


def self_test():
    idx=pd.date_range('2025-01-01',periods=280,freq='D',tz='UTC')
    px=50000*np.cumprod(1+.0012+.001*np.sin(np.arange(len(idx))/5))
    d=pd.DataFrame({'open':px*.999,'high':px*1.005,'low':px*.995,'close':px,
                    'minutes':1440},index=idx)
    d['sma200']=d['close'].rolling(200).mean()
    d['atr20']=(d.high-d.low).rolling(20).mean()
    d['rv30']=d.close.pct_change().rolling(30).std()*np.sqrt(365)
    log,fills,closed=simulate(d)
    assert np.isfinite(log.equity.to_numpy()).all()
    assert (log.fee>=0).all() and (log.gst>=0).all() and (log.slippage>=0).all()
    assert len(fills)>0, 'Expected entry/rebalance events'
    assert log.ready.iloc[0]==False and log.ready.iloc[-1]==True
    print('SELF_TEST_PASS', json.dumps({'synthetic_days':len(d),'fills':len(fills),'note':'Synthetic data are NOT market backtest results'}))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root',type=Path,help='Path to a local clone of BTC-Analysis (READ ONLY)')
    p.add_argument('--output-dir',type=Path,default=Path('outputs/cryptoquantix_independent'))
    p.add_argument('--capital',type=float,default=10000.)
    p.add_argument('--fee-side',type=float,default=.001,help='Fraction of notional, 0.001 = 0.10%% (model assumption)')
    p.add_argument('--slip-side',type=float,default=.0005,help='Fraction of notional, 0.0005 = 0.05%% (model assumption)')
    p.add_argument('--gst',type=float,default=.18,help='18%% tax applied to trading fee only')
    p.add_argument('--indicative-funding-proxy',action='store_true',help='NOT actual funding settlements; exploratory scenario only')
    p.add_argument('--self-test',action='store_true')
    args=p.parse_args()
    if args.self_test:
        self_test(); return
    if args.data_root is None:
        p.error('--data-root is required (unless --self-test)')
    root=args.data_root.resolve();out=args.output_dir.resolve()
    if out==root or root in out.parents:
        p.error('--output-dir must NOT be inside BTC-Analysis; source is read-only')
    if args.capital<=0 or any(x<0 for x in [args.fee_side,args.slip_side,args.gst]):
        p.error('Capital must be positive and costs nonnegative')
    audit=data_audit(root)
    minute=read_history(root,audit)
    daily,bad=prepare_daily(minute)
    fproxy=funding_proxy(root) if args.indicative_funding_proxy else None
    eq,fills,closed=simulate(daily,capital=args.capital,fee_side=args.fee_side,
                      slip_side=args.slip_side,gst=args.gst,funding=fproxy)
    months=monthly_stats(eq,audit,bad,args.capital)
    out.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(audit).to_csv(out/'source_data_audit.csv',index=False)
    eq.to_csv(out/'daily_equity.csv')
    fills.to_csv(out/'fills.csv',index=False)
    closed.to_csv(out/'closed_positions.csv',index=False)
    months.to_csv(out/'monthly_results.csv',index=False)
    valid=months[months.status=='VALID']
    stats={'status':'PARTIAL_REPRODUCTION_NOT_FULL_CRYPTOQUANTIX_PORTFOLIO',
       'source_repo':'rajkumar0rk/BTC-Analysis (READ ONLY)',
       'source_venue':'Delta Exchange India BTCUSD perpetual 1m candles',
       'strategy':'CryptoQuantix MacroCore ONLY',
       'start':'2025-01-01','end_requested':'2026-10-31',
       'first_invalid_day':str(bad) if bad is not None else None,
       'first_signal_warmup_date':str(daily[daily.sma200.notna()].index.min()),
       'valid_months':len(valid),
       'closed_positions':len(closed),
       'winning_positions':int(closed.win.sum()) if len(closed) else 0,
       'losing_positions':int((~closed.win).sum()) if len(closed) else 0,
       'peak_to_trough_daily_drawdown_pct':float((1-eq.equity/eq.equity.cummax()).max()*100),
       'missing_inputs':[
          '2024 pre-2025 200-day SMA warm-up (needed for complete Jan-Jun 2025)',
          'Taker buy volume on BTC trades for TrendBreakdown',
          'Actual settled funding transfers for FundingSqueeze + precise P&L',
          'Missing 1440 minutes in 2026-10 Delta candle archive',
          'Tick-level fills and exact Delta maker/taker fee tier'],
       'costs':{'fee_side_assumption':args.fee_side,'slippage_side_assumption':args.slip_side,
                'GST_on_fees':args.gst,'funding_proxy_mode':bool(args.indicative_funding_proxy)},
       'final_simulated_equity':float(eq.equity.iloc[-1])}
    (out/'run_summary.json').write_text(json.dumps(stats,indent=2)+'\n')
    print(json.dumps(stats,indent=2))
    print('\nMONTHLY VALIDITY (N/A = not a valid full-month backtest):')
    print(months[['month','status','net_return_pct','candles_missing']].to_string(index=False))


if __name__=='__main__':
    main()