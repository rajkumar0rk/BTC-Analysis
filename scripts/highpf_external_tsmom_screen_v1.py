#!/usr/bin/env python3
"""External pooriag 60-day daily long-only momentum, BTC 2025 screening ONLY.
Original signal: close[t]/close[t-60]-1 > 0, exposure next daily bar.
Native Delta candles; modeled two-sided taker 0.05% + 18% GST, zero slippage.
Funding/spread/impact/margin not modeled. Research only.
"""
import csv,gzip,json,hashlib,math
from pathlib import Path
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/delta_india/BTCUSD/1m'
OUT=ROOT/'analysis/highpf_external_20261120/screen_v1'
OUT.mkdir(parents=True,exist_ok=True)
IST=ZoneInfo('Asia/Kolkata')
def parse_ts(v):
    v=str(v).strip()
    if v.replace('.','',1).isdigit():
        n=float(v)
        if n>1e12:n/=1000
        return datetime.fromtimestamp(n,timezone.utc)
    d=datetime.fromisoformat(v.replace('Z','+00:00'))
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)
def read_rows(path):
    with gzip.open(path,'rt',newline='') as f:
        reader=csv.DictReader(f)
        fields=reader.fieldnames or []
        def field(*names):
            for n in names:
                for k in fields:
                    if k.lower().strip()==n:return k
            raise ValueError(f'{path.name}: missing {names}; got {fields}')
        t=field('timestamp','time','datetime','date','start','open_time')
        o,h,l,c=(field(x) for x in ('open','high','low','close'))
        for row in reader:
            dt=parse_ts(row[t])
            op,hi,lo,cl=(float(row[k]) for k in (o,h,l,c))
            if not all(math.isfinite(v) and v>0 for v in (op,hi,lo,cl)) or hi<max(op,cl,lo) or lo>min(op,cl,hi):
                raise ValueError(f'invalid OHLC at {dt}')
            yield dt,cl
def main():
    files=sorted(BASE.glob('2025-*.csv.gz'))
    if len(files)!=12:raise RuntimeError(f'expected 12 2025 source files, found {len(files)}')
    rawhash={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    prices={}
    for p in files:
        for t,c in read_rows(p):
            if t in prices:raise ValueError(f'duplicate timestamp {t}')
            prices[t]=c
    times=sorted(prices)
    if not times:raise RuntimeError('no candles')
    gaps=[(a.isoformat(),b.isoformat()) for a,b in zip(times,times[1:]) if b-a!=timedelta(minutes=1)]
    if gaps:raise RuntimeError(f'{len(gaps)} timestamp gaps; first {gaps[:5]}')
    # UTC files start 2025-01-01 00:00 UTC: first IST day is incomplete.
    # Fail closed, never label incomplete 2025 calendar coverage as full.
    start=datetime(2024,12,31,18,30,tzinfo=timezone.utc)
    end=datetime(2025,12,31,18,29,tzinfo=timezone.utc)
    if times[0]>start or times[-1]<end:
        raise RuntimeError(f'INCOMPLETE_IST_COVERAGE required {start}..{end}; available {times[0]}..{times[-1]}. Need authentic 2024-12-31 and 2026-01 boundary candles.')
    daily={}
    for t in times:
        day=t.astimezone(IST).date()
        daily[day]=prices[t]
    days=sorted(d for d in daily if d.year==2025)
    if len(days)!=365:raise RuntimeError(f'incomplete 2025 IST daily coverage: {len(days)} days')
    # Signal at completed IST close; fill at following daily close-to-close return,
    # upstream shift(1) convention. No intrabar execution claim.
    nav=1.0; position=0; entry_nav=0; trades=[]; equity=[]; gross_total=fees_total=gst_total=0.0
    for i,day in enumerate(days):
        target=int(i>=60 and daily[day]>daily[days[i-60]])
        if i:
            ret=daily[day]/daily[days[i-1]]-1
            gross=nav*position*ret
            gross_total+=gross;nav+=gross
        if target!=position:
            fee=nav*0.0005
            gst=fee*0.18
            fees_total+=fee;gst_total+=gst
            nav-=fee+gst
            if position:trades.append({'exit_day':str(day),'entry_day':str(entry_day),'net_pnl_nav_units':nav-entry_nav})
            if target:entry_day=day;entry_nav=nav
            position=target
        equity.append({'date_ist':str(day),'nav':nav,'position_after_close':position})
    # Mark-to-market final open position; no fictitious closing fill.
    monthly=[]
    previous=1.0
    for month in range(1,13):
        series=[x for x in equity if int(x['date_ist'][5:7])==month]
        if not series:raise RuntimeError(f'missing month {month}')
        finish=series[-1]['nav']
        closed=[x['net_pnl_nav_units'] for x in trades if int(x['exit_day'][5:7])==month]
        wins=sum(x>0 for x in closed);losses=sum(x<0 for x in closed)
        pos=sum(x for x in closed if x>0);neg=-sum(x for x in closed if x<0)
        monthly.append({'month':f'2025-{month:02}','nav_return_pct':(finish/previous-1)*100,'closed_trades':len(closed),'wins':wins,'losses':losses,'realized_pf':pos/neg if neg else ('Infinity' if pos else None)})
        previous=finish
    peak=1.;dd=0.
    for x in equity:
        peak=max(peak,x['nav']);dd=min(dd,x['nav']/peak-1)
    def write(name,rows):
        with (OUT/name).open('w',newline='') as f:
            if not rows:return
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    write('trades.csv',trades);write('equity.csv',equity);write('monthly.csv',monthly)
    result={'source':'pooriag/crypto-strategy-backtest@fd210a38','market':'Delta India BTCUSD','year':2025,'zero_slippage':True,'commission_rate_each_side':0.0005,'gst_on_commission':0.18,'funding':'UNMODELED','gross_nav_units':gross_total,'commission_nav_units':fees_total,'gst_nav_units':gst_total,'ending_nav':nav,'net_return_pct':(nav-1)*100,'closed_trades':len(trades),'open_position':position,'max_drawdown_pct':dd*100,'source_sha256':rawhash,'note':'60-day warmup from within 2025; first 60 days flat; not original full-history warmup; screening only'}
    (OUT/'summary.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
