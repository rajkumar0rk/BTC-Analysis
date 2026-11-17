#!/usr/bin/env python3
"""V7.2: BTC 2025 daily/4h trend following, 1h entry, 1m stop replay.

Four fixed entry/exit combinations, not a profitability claim. All features use
completed candles. Source: 2025 Delta India BTCUSD futures OHLCV, no 2026.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

FEE_GST_PER_SIDE = 0.0005 * 1.18
SLIPPAGE_POINTS_PER_SIDE = 5.0
MAX_HOLD_MINUTES = 10 * 24 * 60
START = pd.Timestamp('2025-03-01', tz='UTC')
END = pd.Timestamp('2026-01-01', tz='UTC')


def load_2025(folder: Path) -> pd.DataFrame:
    parts = []
    for month in range(1, 13):
        path = folder / f'2025-{month:02d}.csv.gz'
        if not path.is_file():
            raise FileNotFoundError(path)
        x = pd.read_csv(path, compression='gzip', usecols=['time','open','high','low','close','volume'])
        x['time'] = pd.to_datetime(x.time.astype('int64'), unit='s', utc=True)
        parts.append(x.set_index('time'))
    out = pd.concat(parts).sort_index()
    assert len(out) == 525600, f'2025 minutes: {len(out)}'
    assert out.index.min() == pd.Timestamp('2025-01-01', tz='UTC')
    assert out.index.max() == END - pd.Timedelta(minutes=1)
    assert out.index.is_unique
    assert (out.index[1:] - out.index[:-1] == pd.Timedelta(minutes=1)).all()
    assert out[['open','high','low','close','volume']].notna().all().all()
    assert (out.high >= out.low).all()
    return out


def aggregate(m: pd.DataFrame, freq: str, expected: int) -> pd.DataFrame:
    c = m.close.resample(freq, closed='left', label='right').count()
    assert c.eq(expected).all(), f'Partial {freq} candle'
    return m.resample(freq, closed='left', label='right').agg(
        open=('open','first'), high=('high','max'), low=('low','min'),
        close=('close','last'), volume=('volume','sum'))


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False, min_periods=n).mean()


def indicators(m: pd.DataFrame):
    d = aggregate(m,'1D',1440)
    h4 = aggregate(m,'4h',240)
    h1 = aggregate(m,'1h',60)

    d['ema20'] = ema(d.close,20)
    d['ema50'] = ema(d.close,50)
    d['bull'] = (d.close > d.ema20) & (d.ema20 > d.ema50) & (d.ema20 > d.ema20.shift(3))
    d['bear'] = (d.close < d.ema20) & (d.ema20 < d.ema50) & (d.ema20 < d.ema20.shift(3))
    d['exit_long'] = d.close < d.ema20
    d['exit_short'] = d.close > d.ema20

    h4['ema20'] = ema(h4.close,20)
    h4['ema50'] = ema(h4.close,50)
    prev = h4.close.shift(1)
    true_range = pd.concat([h4.high-h4.low, (h4.high-prev).abs(), (h4.low-prev).abs()],axis=1).max(axis=1)
    h4['atr14'] = true_range.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    h4['bull'] = (h4.close > h4.ema20) & (h4.ema20 > h4.ema50)
    h4['bear'] = (h4.close < h4.ema20) & (h4.ema20 < h4.ema50)
    h4['exit_ema_long'] = h4.close < h4.ema20
    h4['exit_ema_short'] = h4.close > h4.ema20
    h4['prior10_low'] = h4.low.shift(1).rolling(10,min_periods=10).min()
    h4['prior10_high'] = h4.high.shift(1).rolling(10,min_periods=10).max()
    h4['exit_structure_long'] = h4.close < h4.prior10_low
    h4['exit_structure_short'] = h4.close > h4.prior10_high

    h1['ema20'] = ema(h1.close,20)
    h1['previous_high12'] = h1.high.shift(1).rolling(12,min_periods=12).max()
    h1['previous_low12'] = h1.low.shift(1).rolling(12,min_periods=12).min()
    h1['prev_high'] = h1.high.shift(1)
    h1['prev_low'] = h1.low.shift(1)
    span = (h1.high-h1.low).replace(0,np.nan)
    h1['close_location'] = (h1.close-h1.low)/span

    # A 1h signal evaluated at its close can use only the last completed daily and 4h bars.
    for direction in ('bull','bear'):
        h1[f'day_{direction}'] = d[direction].reindex(h1.index, method='ffill').fillna(False).astype(bool)
        h1[f'four_{direction}'] = h4[direction].reindex(h1.index, method='ffill').fillna(False).astype(bool)
    h1['atr4'] = h4.atr14.reindex(h1.index,method='ffill')

    h1['long_breakout'] = (h1.close > h1.previous_high12) & (h1.close_location >= 0.75) & (h1.close > h1.open)
    h1['short_breakout'] = (h1.close < h1.previous_low12) & (h1.close_location <= 0.25) & (h1.close < h1.open)
    h1['long_pullback'] = (h1.low <= h1.ema20) & (h1.close > h1.ema20) & (h1.close > h1.prev_high) & (h1.close > h1.open)
    h1['short_pullback'] = (h1.high >= h1.ema20) & (h1.close < h1.ema20) & (h1.close < h1.prev_low) & (h1.close < h1.open)
    return d,h4,h1


def candidates(h1):
    out=[]
    for ts,z in h1.loc[(h1.index>=START)&(h1.index<END)].iterrows():
        # Session filter: weekdays for new trades in India, but existing trades remain open across weekends.
        if ts.tz_convert('Asia/Kolkata').weekday() >= 5:
            continue
        if not np.isfinite(z.atr4) or z.atr4 <= 0:
            continue
        for side,flag in ((1,'bull'),(-1,'bear')):
            if not (z[f'day_{flag}'] and z[f'four_{flag}']):
                continue
            for entry_type in ('breakout','pullback'):
                if z[('long_' if side==1 else 'short_')+entry_type]:
                    out.append(dict(signal_time=ts,entry_time=ts,side=side,
                                    entry_type=entry_type,atr4=float(z.atr4)))
    return pd.DataFrame(out)


def minute_exit_flags(m: pd.DataFrame,d: pd.DataFrame,h4:pd.DataFrame):
    flags={}
    for exit_type in ('ema','structure'):
        for side,direction in ((1,'long'),(-1,'short')):
            daily=d[f'exit_{direction}'].reindex(m.index,method='ffill').fillna(False)
            four=h4[f'exit_{exit_type}_{direction}'].reindex(m.index,method='ffill').fillna(False)
            # Structural direction must reverse on 4h or daily COMPLETED bar.
            flags[(exit_type,side)]=(daily | four).to_numpy(dtype=bool)
    return flags


def execute(m,flags,signals,entry_type,exit_type):
    if signals.empty:
        return pd.DataFrame()
    x=signals[signals.entry_type==entry_type].sort_values('entry_time')
    idx=m.index
    o=m.open.to_numpy(dtype=float); hi=m.high.to_numpy(dtype=float)
    lo=m.low.to_numpy(dtype=float); cl=m.close.to_numpy(dtype=float)
    out=[];free_time=START
    for signal in x.itertuples(index=False):
        if signal.entry_time < free_time:
            continue
        i=idx.searchsorted(signal.entry_time)
        if i>=len(idx):
            break
        side=int(signal.side)
        entry=o[i]+side*SLIPPAGE_POINTS_PER_SIDE
        stop_distance=min(1000.0,max(250.0,2.0*signal.atr4))
        stop=entry-side*stop_distance
        end=min(i+MAX_HOLD_MINUTES,len(idx))
        # Separate exit logic evaluates only completed daily/4h bars and acts at next minute OPEN.
        exit_mask=flags[(exit_type,side)][i:end]
        stops=(lo[i:end]<=stop) if side==1 else (hi[i:end]>=stop)
        structural=np.flatnonzero(exit_mask)
        stop_indices=np.flatnonzero(stops)
        struct_i=i+int(structural[0]) if len(structural) else len(idx)+1
        stop_i=i+int(stop_indices[0]) if len(stop_indices) else len(idx)+1
        if struct_i<=stop_i and struct_i<end:
            j=struct_i;reason='STRUCTURE_EXIT';exit_raw=o[j]
            max_j=max(i,j) # exclude exit minute when exiting on open
        elif stop_i<end:
            j=stop_i;reason='INITIAL_STOP'
            exit_raw=min(stop,o[j]) if side==1 else max(stop,o[j])
            max_j=j+1
        else:
            j=end-1; reason='TIME_LIMIT' if end<len(idx) else 'YEAR_END'
            exit_raw=cl[j];max_j=j+1
        exit_price=exit_raw-side*SLIPPAGE_POINTS_PER_SIDE
        gross=side*(exit_price-entry)
        costs=(entry+exit_price)*FEE_GST_PER_SIDE
        net=gross-costs
        if max_j > i:
            mfe=(hi[i:max_j].max()-entry) if side==1 else (entry-lo[i:max_j].min())
            mae=(entry-lo[i:max_j].min()) if side==1 else (hi[i:max_j].max()-entry)
        else:
            mfe=mae=0.0
        out.append(dict(signal_time=signal.signal_time,entry_time=idx[i],exit_time=idx[j],
                        direction='LONG' if side==1 else 'SHORT',entry_type=entry_type,
                        exit_type=exit_type,entry_price=round(entry,2),exit_price=round(exit_price,2),
                        exit_reason=reason,stop_points=round(stop_distance,2),
                        gross_points=round(float(gross),2),fee_gst_points=round(float(costs),2),
                        net_points=round(float(net),2),duration_hours=round((j-i)/60,2),
                        mfe_points=round(max(0,float(mfe)),2),mae_points=round(max(0,float(mae)),2),
                        captured_1000plus=bool(gross>=1000),month=idx[j].strftime('%Y-%m')))
        free_time=idx[j]+pd.Timedelta(minutes=1)
    return pd.DataFrame(out)


def summarize(trades):
    months={f'2025-{i:02d}':0.0 for i in range(3,13)}
    if len(trades):
        for month,value in trades.groupby('month').net_points.sum().items():
            if month in months: months[month]=round(float(value),2)
    return dict(trades=int(len(trades)),wins=int((trades.net_points>0).sum()) if len(trades) else 0,
                win_rate_pct=round(100*float((trades.net_points>0).mean()),2) if len(trades) else None,
                net_points=round(float(trades.net_points.sum()),2) if len(trades) else 0.0,
                profitable_months=int(sum(v>0 for v in months.values())),
                captured_1000plus=int(trades.captured_1000plus.sum()) if len(trades) else 0,
                avg_duration_hours=round(float(trades.duration_hours.mean()),1) if len(trades) else None,
                monthly_net_points=months)


def report(summary):
    rows=[
        '# V7.2 — BTC longer-term trend following (2025)', '',
        '**Experimental backtest, not a proven edge. No 2026 data.**', '',
        '## Fixed, causal rules',
        '- Daily direction: completed daily close above/below EMA20; EMA20 above/below EMA50 and slopes in the same direction across 3 days.',
        '- 4H confirmation: completed close above/below EMA20, with EMA20/EMA50 aligned.',
        '- Breakout entry: completed 1H close breaks previous 12 completed 1H high/low; close in outer 25% of range.',
        '- Pullback entry: 1H touches EMA20 and closes back through it beyond previous 1H high/low.',
        '- Enter at next 1M OPEN; weekdays IST only for new entries. One position at a time per variant.',
        '- Initial stop: 2×4H ATR14, minimum 250, maximum 1,000 BTC price points; checked on every 1M candle.',
        '- Exit A: completed 4H close opposite EMA20 OR completed daily close opposite EMA20.',
        '- Exit B: completed 4H close beyond the previous 10 4H candle high/low OR completed daily close opposite EMA20.',
        '- Max holding 10 days. No fixed take profit. Stop checked with conservative gap fill.',
        '- Costs: taker 0.05% per side + 18% GST on trading fees, 5 BTC points adverse slippage each side.',
        '',
        '## Results by variant', '',
        '| Entry | Exit | Trades | Win rate | Net points | Months positive | Realized 1,000+ point wins | Avg hours |',
        '|---|---|---:|---:|---:|---:|---:|---:|',
    ]
    for key,v in summary['variants'].items():
        entry,exit_type=key.split('__')
        rows.append(f"| {entry} | {exit_type} | {v['trades']} | {v['win_rate_pct']}% | {v['net_points']} | {v['profitable_months']}/10 | {v['captured_1000plus']} | {v['avg_duration_hours']} |")
    rows += ['', '## Monthly net points (after modeled costs)', '',
             '| Month | Breakout/EMA | Breakout/Structure | Pullback/EMA | Pullback/Structure |',
             '|---|---:|---:|---:|---:|']
    keys=['breakout__ema','breakout__structure','pullback__ema','pullback__structure']
    for month in next(iter(summary['variants'].values()))['monthly_net_points']:
        rows.append('| '+month+' | '+' | '.join(str(summary['variants'][key]['monthly_net_points'][month]) for key in keys)+' |')
    rows += ['', '## Limitations',
        '- These are modeled BTC price-point results for a 1-BTC-equivalent position, NOT USD account P&L; actual margin, financing and liquidation are not modeled.',
        '- Funding, L1 depth, market impact, live slippage and execution outages excluded.',
        '- Four variants were compared on the same 2025 development window: do not treat the best as out-of-sample proof.',
        '- Exit month determines monthly realized P&L; forced year-end closure has no January 2026 data.',
        '- Profitability in all 10 months is a goal, not an assumption.', '',
    ]
    return '\n'.join(rows)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--data-dir',type=Path,default=Path('data/delta_india/BTCUSD/1m'))
    p.add_argument('--output-dir',type=Path,default=Path('analysis/v7_2_2025'))
    args=p.parse_args()
    minute=load_2025(args.data_dir)
    daily,four,hour=indicators(minute)
    signals=candidates(hour)
    flags=minute_exit_flags(minute,daily,four)
    variants={};ledgers=[]
    for entry_type in ('breakout','pullback'):
        for exit_type in ('ema','structure'):
            trades=execute(minute,flags,signals,entry_type,exit_type)
            key=entry_type+'__'+exit_type
            variants[key]=summarize(trades)
            if len(trades): ledgers.append(trades)
    summary={'dataset':'Delta India BTCUSD futures 2025 1m','period':'March through December 2025',
             'signal_count':int(len(signals)), 'variants':variants}
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/'V7_2_RESEARCH_REPORT.md').write_text(report(summary)+'\n',encoding='utf8')
    (args.output_dir/'v7_2_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    (pd.concat(ledgers,ignore_index=True) if ledgers else pd.DataFrame()).to_csv(args.output_dir/'v7_2_trades.csv',index=False)
    signals.to_csv(args.output_dir/'v7_2_signals.csv',index=False)
    print(report(summary))

if __name__=='__main__':
    main()
