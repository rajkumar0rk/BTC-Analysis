#!/usr/bin/env python3
"""Read-only Delta BTCUSD / CryptoQuantix strategy reproduction.

MacroCore: faithful rule-port. TrendBreakdown: requires actual taker-buy volume;
optionally accepts Binance cross-venue proxy (explicitly NOT exact reproduction).
FundingSqueeze: uses indicative Delta funding OHLC observation, NOT settled cashflow.
No changes to BTC-Analysis files. Never infer missing market data.
"""
from __future__ import annotations
import argparse, json, csv, math, time, hashlib, sys, io, zipfile
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import requests
import run_macrocore as source

UTC = timezone.utc
START = pd.Timestamp('2025-01-01',tz='UTC')
END = pd.Timestamp('2026-11-01',tz='UTC')
BASE = 'https://api.india.delta.exchange/v2/history/candles'


def history_delta(symbol, resolution, start, stop, chunk_seconds, session=None):
    """Request only genuinely absent periods, with finite retries and validation."""
    session = session or requests.Session()
    rows=[]
    for lo in range(int(start.timestamp()),int(stop.timestamp()),chunk_seconds):
        hi=min(int(stop.timestamp())-1,lo+chunk_seconds-1)
        params={'symbol':symbol,'resolution':resolution,'start':lo,'end':hi}
        result=None
        for retry in range(4):
            try:
                response=session.get(BASE,params=params,timeout=35,headers={'Accept':'application/json'})
                response.raise_for_status()
                payload=response.json()
                if payload.get('success') is not True or not isinstance(payload.get('result'),list):
                    raise ValueError('Delta API returned non-success response')
                result=payload['result'];break
            except (requests.RequestException,ValueError) as e:
                if retry==3: raise RuntimeError(f'Delta historical source failed: {symbol} {resolution} {lo}-{hi}: {e}') from e
                time.sleep(min(8,2**retry))
        rows.extend(v for v in result if lo<=int(v.get('time',-1))<=hi)
        time.sleep(.08)
    if not rows: raise ValueError(f'No Delta history available: {symbol} {resolution} {start}..{stop}')
    df=pd.DataFrame(rows).drop_duplicates('time')
    df['time']=pd.to_datetime(pd.to_numeric(df.time),unit='s',utc=True)
    df=df.set_index('time').sort_index()
    for col in ['open','high','low','close','volume']:
        if col not in df: df[col]=np.nan
        df[col]=pd.to_numeric(df[col],errors='coerce')
    if df[['open','high','low','close']].isna().any().any():
        raise ValueError(f'Nonfinite Delta data: {symbol} {resolution}')
    # FUNDING:BTCUSD is a rate series. Negative funding is legitimate!
    if not symbol.startswith('FUNDING:') and (df.low<=0).any():
        raise ValueError(f'Invalid nonpositive price: {symbol} {resolution}')
    return df


def repair_minute_in_memory(minute, *, fetch=True):
    expected=pd.date_range(START,END,freq='min',inclusive='left')
    missing=expected.difference(minute.index)
    audit={'missing_original':len(missing),'missing_examples':[str(x) for x in missing[:6]],'fetched':0,'repaired':False}
    if len(missing)==0: audit['repaired']=True;return minute,audit
    if not fetch: return minute,audit
    groups=[];start=prev=missing[0]
    for t in missing[1:]:
        if t-prev>pd.Timedelta(minutes=1):groups.append((start,prev+pd.Timedelta(minutes=1)));start=t
        prev=t
    groups.append((start,prev+pd.Timedelta(minutes=1)))
    fetched=[]
    for lo,stop in groups:
        try:
            sub=history_delta('BTCUSD','1m',lo,stop,1200*60)
            fetched.append(sub[['open','high','low','close','volume']])
        except Exception as exc:
            print(f'WARNING no Delta gap fill for {lo}..{stop}: {exc}',file=sys.stderr)
    if fetched:
        missing_data=pd.concat(fetched).loc[lambda d: d.index.isin(missing)]
        audit['fetched']=len(missing_data)
        minute=pd.concat([minute,missing_data]).sort_index()
        if not minute.index.is_unique: raise ValueError('Duplicate minutes after repair')
    audit['remaining']=len(expected.difference(minute.index))
    audit['repaired']=audit['remaining']==0
    return minute,audit


def daily_with_warmup(minute, *, fetch=True):
    d=minute.resample('1D').agg(open=('open','first'),high=('high','max'),low=('low','min'),close=('close','last'),minutes=('close','count'))
    info={'warmup_from_delta_api':False,'warmup_rows':0,'first_200day_ready':None}
    if fetch:
        try:
            # Fetch only pre-2025 daily candles; the 2025+ minute archive is reused.
            pre=history_delta('BTCUSD','1d',pd.Timestamp('2024-03-01',tz='UTC'),START,320*86400)
            pre=pre.loc[pre.index<START]
            if len(pre)>=200:
                pre=pre[['open','high','low','close']].copy();pre['minutes']=1440
                d=pd.concat([pre,d]).sort_index()
                if not d.index.is_unique: raise ValueError('Overlapping daily warmup dates')
                info.update(warmup_from_delta_api=True,warmup_rows=len(pre))
            else: info['error']=f'Only {len(pre)} pre-2025 daily observations'
        except Exception as exc:
            info['error']=str(exc)
    tr=pd.concat([(d.high-d.low),(d.high-d.close.shift()).abs(),(d.low-d.close.shift()).abs()],axis=1).max(axis=1)
    d['atr20']=tr.rolling(20,min_periods=20).mean()
    d['sma200']=d.close.rolling(200,min_periods=200).mean()
    d['rv30']=d.close.pct_change().rolling(30,min_periods=30).std()*np.sqrt(365)
    ready=d.loc[(d.sma200.notna())&(d.index>=START)]
    if len(ready):info['first_200day_ready']=str(ready.index[0])
    return d,info


def load_funding(root, *,fetch=True):
    folder=root/'data/delta_india/BTCUSD/institutional/history/funding_1h'
    frames=[]
    for p in sorted(folder.glob('20??-??.csv.gz')):
        if not ('2025-01'<=p.stem[:7]<='2026-10'):continue
        f=pd.read_csv(p,compression='gzip',usecols=['time','close']);f.time=pd.to_datetime(f.time.astype('int64'),unit='s',utc=True)
        frames.append(f.set_index('time').close.astype(float))
    data=pd.concat(frames).sort_index() if frames else pd.Series(dtype=float)
    if not data.index.is_unique:raise ValueError('Duplicate funding timestamps')
    info={'source':'Delta FUNDING:BTCUSD OHLC historical rate observations, NOT realized cashflow ledger','observations_original':len(data)}
    expected=pd.date_range(START,END,freq='h',inclusive='left')
    miss=expected.difference(data.index)
    if fetch and len(miss):
        # Only fetch absent hours; do not replace archived rates.
        groups=[];begin=prev=miss[0]
        for t in miss[1:]:
            if t-prev>pd.Timedelta(hours=1):groups.append((begin,prev+pd.Timedelta(hours=1)));begin=t
            prev=t
        groups.append((begin,prev+pd.Timedelta(hours=1)))
        for st,en in groups:
            try:
                f=history_delta('FUNDING:BTCUSD','1h',st,en,800*3600)
                new=f.close[f.index.isin(miss)]
                data=pd.concat([data,new]).sort_index()
            except Exception as exc: print(f'WARNING funding gap {st}..{en}: {exc}',file=sys.stderr)
    if not data.index.is_unique:raise ValueError('Duplicate funding hours')
    # Last hour of 2024 is needed for a Jan 1 funding event if a position is open.
    boundary=START-pd.Timedelta(hours=1)
    if fetch and boundary not in data.index:
        try:
            old=history_delta('FUNDING:BTCUSD','1h',boundary,START,3600)
            data=pd.concat([data,old.close]).sort_index()
        except Exception as exc:
            print(f'WARNING cannot retrieve boundary funding rate: {exc}',file=sys.stderr)
    info.update(observations_final=len(data),hours_missing=len(expected.difference(data.index)),
                prior_2025_settlement_observation_available=bool(boundary in data.index))
    # Each hourly candle is a rate observation (percent units; 0.01 means 0.01%).
    # The previous completed hour alone may be observed at settlement time.
    return data,info


def load_flow(root,hours,mode,flow_path=None):
    if mode=='strict':
        if flow_path is None:
            return pd.Series(np.nan,index=hours),{'mode':'strict','available':0,'warning':'No genuine historical Delta taker-buy data; TrendBreakdown DISABLED'}
        df=pd.read_csv(flow_path)
        required={'time','buy_ratio'}
        if not required.issubset(df.columns):raise ValueError('Flow CSV requires time,buy_ratio columns')
        df.time=pd.to_datetime(df.time,utc=True)
        vals=pd.Series(pd.to_numeric(df.buy_ratio,errors='coerce').values,index=df.time).reindex(hours)
        if vals.dropna().lt(0).any() or vals.dropna().gt(1).any():raise ValueError('Invalid buy ratio')
        return vals,{'mode':'genuine_user_supplied_flow','available':int(vals.notna().sum())}
    if mode=='no-flow-filter':
        return pd.Series(-1.,index=hours),{'mode':'ABLATION_WITHOUT_FLOW_GATE','available':len(hours),'warning':'The original TrendBreakdown buy-ratio gate has been REMOVED; NOT strategy parity'}
    if mode!='binance-proxy':raise ValueError(f'Unknown flow mode {mode}')
    session=requests.Session();all_bars=[]
    st=int(hours.min().timestamp()*1000);stop=int((hours.max()+pd.Timedelta(hours=1)).timestamp()*1000)
    api_error=None
    for lo in range(st,stop,1250*3600000):
        hi=min(stop-1,lo+1250*3600000-1)
        try:
            resp=session.get('https://fapi.binance.com/fapi/v1/klines',params={'symbol':'BTCUSDT','interval':'1h','startTime':lo,'endTime':hi,'limit':1500},timeout=45)
            resp.raise_for_status();all_bars.extend(resp.json())
        except Exception as exc:
            api_error=str(exc);break
        time.sleep(.1)
    if api_error:
        # Binance Futures REST returns HTTP 451 to some GitHub-hosted runners.
        # Public archive files are still accessible from Binance Vision CDN.
        all_bars=[]
        vision_error=None
        for month in pd.period_range('2025-01','2026-10',freq='M'):
            key=str(month)
            url=f'https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-{key}.zip'
            try:
                rr=session.get(url,timeout=65)
                rr.raise_for_status()
                with zipfile.ZipFile(io.BytesIO(rr.content)) as zf:
                    names=[name for name in zf.namelist() if name.endswith('.csv')]
                    if not names:raise ValueError('Binance Vision archive contains no CSV')
                    with zf.open(names[0]) as f:
                        for row in csv.reader(io.TextIOWrapper(f,encoding='utf-8')):
                            if not row or not row[0].isdigit():continue
                            all_bars.append(row)
            except Exception as exc:
                vision_error=f'{key}: {exc}'
                break
        if vision_error:
            print(f'WARNING Binance API {api_error}; Binance Vision {vision_error}; TrendBreakdown flow unavailable',file=sys.stderr)
            return pd.Series(np.nan,index=hours),{'mode':'binance-proxy','available':0,
                'api_error':api_error,'vision_error':vision_error}
    def stamp_to_utc(v):
        x=int(v)
        return pd.Timestamp(x,unit='us' if x>10**14 else 'ms',tz='UTC')
    vals={stamp_to_utc(v[0]):float(v[9])/float(v[5]) if float(v[5])>0 else np.nan for v in all_bars}
    s=pd.Series(vals).reindex(hours)
    coverage=s.notna().groupby(s.index.strftime('%Y-%m')).sum().astype(int).to_dict()
    return s,{'mode':'BINANCE_BTCUSDT_CROSS_VENUE_PROXY_NOT_DELTA','available':int(s.notna().sum()),
              'monthly_available':coverage,
              'source':'Binance Futures REST' if not api_error else 'Binance Vision monthly archive',
              'note':'Aggressor direction is from another instrument and venue; NOT exact Delta trade flow'}


def make_hourly(minute,flow):
    h=minute.resample('1h').agg(open=('open','first'),high=('high','max'),low=('low','min'),close=('close','last'),volume=('volume','sum'),minutes=('close','count'))
    h['sma48']=h.close.rolling(48,min_periods=48).mean()
    tr=pd.concat([(h.high-h.low),(h.high-h.close.shift()).abs(),(h.low-h.close.shift()).abs()],axis=1).max(axis=1)
    h['atr14']=tr.rolling(14,min_periods=14).mean()
    h['prev48low']=h.low.shift(1).rolling(48,min_periods=48).min()
    h['prev168high']=h.high.shift(1).rolling(168,min_periods=168).max()
    h['buy_ratio']=flow.reindex(h.index)
    return h


class Book:
    def __init__(self,capital,fee,slip,gst,contract,scalp,cap):
        self.cash=float(capital);self.fee=fee;self.slip=slip;self.gst=gst
        self.contract=contract;self.scalp=scalp;self.gross_cap=cap
        self.positions={};self.fills=[];self.trades=[];self.daily=[]
        self.costs={'fee':0.,'gst':0.,'slippage':0.,'funding_proxy':0.};self.missing_funding=0;self.missing_funding_times=[]
    def equity(self,price):
        return self.cash+sum(p['side']*p['qty']*(price-p['entry_exec']) for p in self.positions.values())
    def cap_qty(self,price,qty):
        eq=self.equity(price)
        gross=sum(abs(p['qty']*price) for p in self.positions.values())
        free=max(0.,self.gross_cap*max(eq,0.)-gross)
        n=min(qty,free/price)
        return math.floor(n/self.contract+1e-9)*self.contract
    def open(self,strategy,side,price,qty,t,*,sl=None,tp=None,maxhold=None):
        if strategy in self.positions or qty<=0 or self.cash<=0:return
        qty=self.cap_qty(price,qty)
        if qty<=0:return
        actual=price*(1+side*self.slip)
        fee=actual*qty*self.fee;tax=fee*self.gst;slipc=price*qty*self.slip
        self.cash-=fee+tax
        self.costs['fee']+=fee;self.costs['gst']+=tax;self.costs['slippage']+=slipc
        self.positions[strategy]=dict(strategy=strategy,side=side,qty=qty,entry_mid=price,entry_exec=actual,
            entry_t=t,entry_equity=self.equity(price),entry_fee=fee,entry_tax=tax,entry_slip=slipc,
            sl=sl,tp=tp,maxhold=maxhold,funding_proxy=0.,entry_notional=qty*price,
            max_close=price,stop_level=price*.75 if strategy=='MacroCore' else None,realized_rebalance_pnl=0.)
        self.fills.append(dict(time=t,strategy=strategy,action='ENTRY',side=side,price=price,qty=qty,fee=fee,gst=tax,slippage=slipc))
    def close(self,strategy,price,t,reason):
        p=self.positions.pop(strategy,None)
        if p is None:return
        side,qty=p['side'],p['qty']
        actual=price*(1-side*self.slip)
        pnl=side*qty*(actual-p['entry_exec'])
        waiver=bool(self.scalp and (t-p['entry_t'])<=pd.Timedelta(minutes=30))
        fee=0. if waiver else qty*actual*self.fee
        tax=fee*self.gst
        self.cash+=pnl-fee-tax
        slipc=qty*price*self.slip
        self.costs['fee']+=fee;self.costs['gst']+=tax;self.costs['slippage']+=slipc
        gross=side*qty*(price-p['entry_mid'])+p['realized_rebalance_pnl']
        net=pnl+p['realized_rebalance_pnl']-p['entry_fee']-p['entry_tax']-fee-tax-p['funding_proxy']
        self.trades.append(dict(strategy=strategy,side='LONG' if side>0 else 'SHORT',
            entry_time=p['entry_t'],exit_time=t,entry=p['entry_mid'],exit=price,qty=qty,
            gross_usd=gross,fee_usd=p['entry_fee']+fee,gst_usd=p['entry_tax']+tax,
            slippage_usd=p['entry_slip']+slipc,funding_proxy_usd=p['funding_proxy'],
            net_model_usd=net,win=net>0,reason=reason,scalper_fee_waiver=waiver))
        self.fills.append(dict(time=t,strategy=strategy,action='EXIT',side=side,price=price,qty=qty,fee=fee,gst=tax,slippage=slipc))
    def rebalance_macro(self,price,t,target_qty):
        p=self.positions.get('MacroCore')
        if not p: return
        target_qty=math.floor(max(0.,target_qty)/self.contract+1e-9)*self.contract
        d=target_qty-p['qty']
        if abs(d)<self.contract-.00000000001:return
        if d>0: d=min(d,self.cap_qty(price,d));d=math.floor(d/self.contract+1e-9)*self.contract
        if abs(d)<1e-12:return
        mid=price*(1+(1 if d>0 else -1)*self.slip)
        fee=abs(d)*mid*self.fee;tax=fee*self.gst
        self.cash-=fee+tax
        self.costs['fee']+=fee;self.costs['gst']+=tax;self.costs['slippage']+=abs(d)*price*self.slip
        # Realize reduction PnL into cash so mark-to-market remains continuous.
        if d<0: self.cash+=-d*(mid-p['entry_exec'])
        old_qty=p['qty']
        if d>0:
            p['entry_exec']=(p['entry_exec']*old_qty + d*mid)/(old_qty+d)
            p['entry_mid']=(p['entry_mid']*old_qty + d*price)/(old_qty+d)
        else:
            p['realized_rebalance_pnl']+=-d*(mid-p['entry_exec'])
        p['qty']+=d
        p['entry_fee']+=fee;p['entry_tax']+=tax;p['entry_slip']+=abs(d)*price*self.slip
        self.fills.append(dict(time=t,strategy='MacroCore',action='REBALANCE',side=1,price=price,qty=d,fee=fee,gst=tax,slippage=abs(d)*price*self.slip))
        if p['qty']<self.contract-.00000000001:self.close('MacroCore',price,t,'rebalance_flat')
    def fund(self,rate,price,t):
        # Only an INDICATIVE cashflow scenario, never a confirmed funding ledger.
        if rate is None or not math.isfinite(rate):
            if self.positions:
                self.missing_funding+=1;self.missing_funding_times.append(t)
            return
        for p in self.positions.values():
            amount=p['side']*p['qty']*price*rate
            self.cash-=amount;p['funding_proxy']+=amount
            self.costs['funding_proxy']+=amount


def reward_target(entry_price, side, stop_distance, risk_reward):
    # Correct orientation is essential: SHORT targets BELOW entry.
    if risk_reward<=0:return None
    return entry_price+side*stop_distance*risk_reward


def backtest(minute,daily,hourly,funding,*,capital,fee,slip,gst,contract,scalp,cap):
    b=Book(capital,fee,slip,gst,contract,scalp,cap)
    # Signals and cashflows are only based on completed previous bars.
    keys=minute.index;op=minute.open.to_numpy();hi=minute.high.to_numpy();lo=minute.low.to_numpy();cl=minute.close.to_numpy()
    opened=None
    last_fs=pd.Timestamp('2000-01-01',tz='UTC')
    monthly_observed={}
    hourly_idx=set(hourly.index)
    for i in range(len(minute)):
        t=keys[i];o=float(op[i]);h=float(hi[i]);l=float(lo[i]);c=float(cl[i]);
        if t<START:continue
        if not math.isfinite(o) or not math.isfinite(c):raise ValueError(f'Bad minute at {t}')
        # Complete previous daily candle available only at UTC midnight.
        if t.hour==0 and t.minute==0:
            day=t-pd.Timedelta(days=1);prev=daily.loc[day] if day in daily.index else None
            if prev is not None and prev['minutes']==1440 and pd.notna(prev.sma200):
                macro=b.positions.get('MacroCore')
                if macro:
                    macro['max_close']=max(macro['max_close'],float(prev.close))
                    if pd.notna(prev.atr20) and prev.close<macro['max_close']-5.*prev.atr20:
                        b.close('MacroCore',o,t,'chandelier')
                else:
                    if prev.close>prev.sma200 and pd.notna(prev.rv30):
                        expo=1. if prev.rv30<=0 else min(1.,.30/float(prev.rv30))
                        expo=max(0.,min(1.,round(expo/.25)*.25))
                        b.open('MacroCore',1,o,b.equity(o)*expo/o,t)
                if 'MacroCore' in b.positions and pd.notna(prev.rv30):
                    expo=1. if prev.rv30<=0 else min(1.,.30/float(prev.rv30))
                    expo=max(0.,min(1.,round(expo/.25)*.25))
                    b.rebalance_macro(o,t,b.equity(o)*expo/o)
        # Exit existing tactical trades at next candle open upon elapsed duration.
        for name,p in list(b.positions.items()):
            if p['maxhold'] is not None and t-p['entry_t']>=p['maxhold']:
                b.close(name,o,t,'time')
        # Hourly signals are for the previous fully CLOSED hour only.
        if t.minute==0:
            prev_hour=t-pd.Timedelta(hours=1)
            dy=t.floor('D')-pd.Timedelta(days=1)
            yr=daily.loc[dy] if dy in daily.index else None
            bar=hourly.loc[prev_hour] if prev_hour in hourly_idx else None
            ready=bool(bar is not None and yr is not None and yr.minutes==1440 and pd.notna(yr.sma200) and
                bar.minutes==60 and pd.notna(bar.sma48) and pd.notna(bar.atr14))
            if ready and b.cash>0:
                bull=bool(yr.close>yr.sma200)
                if 'TrendBreakdown' not in b.positions and pd.notna(bar.buy_ratio):
                    sig=0;hold=24
                    if (not bull and pd.notna(bar.prev48low) and bar.close<bar.prev48low
                        and bar.close<bar.sma48 and (bar.buy_ratio<.5 or bar.buy_ratio==-1)) :sig=-1
                    elif (bull and pd.notna(bar.prev168high) and bar.close>bar.prev168high
                        and bar.close>bar.sma48 and (bar.buy_ratio>.5 or bar.buy_ratio==-1)):sig=1;hold=168
                    if sig:
                        dist=2*bar.atr14
                        risk=min(max(b.equity(o),0)*.01/dist, max(b.equity(o),0)/o)
                        b.open('TrendBreakdown',sig,o,risk,t,sl=o-sig*dist,
                               tp=reward_target(o,sig,dist,2.) if sig<0 else None,
                               maxhold=pd.Timedelta(hours=hold))
                # FundingSqueeze contrarian: previous completed funding hour observed,
                # assumed 8h settlement. A proxy for research, NOT live payout.
                if t.hour in (0,8,16) and 'FundingSqueeze' not in b.positions and t-last_fs>=pd.Timedelta(hours=8):
                    rate=funding.get(prev_hour,np.nan)
                    prev30day=dy-pd.Timedelta(days=30)
                    earlier=daily.loc[prev30day] if prev30day in daily.index else None
                    if (pd.notna(rate) and float(rate)>=.01 and not bull and earlier is not None
                        and pd.notna(earlier.sma200) and yr.sma200<earlier.sma200 and bar.close<bar.sma48):
                        dist=2*bar.atr14
                        risk=min(max(b.equity(o),0)*.01/dist,max(b.equity(o),0)/o)
                        b.open('FundingSqueeze',-1,o,risk,t,sl=o+dist,tp=o-2*dist,maxhold=pd.Timedelta(hours=24))
                        if 'FundingSqueeze' in b.positions:last_fs=t
        # Intraminute stop / target: conservative SL if both levels touched.
        for name,p in list(b.positions.items()):
            side=p['side']
            if name=='MacroCore':
                stop=p['stop_level']
                if l<=stop:b.close(name,min(o,stop),t,'disaster_stop')
                continue
            slp=p['sl'];tpp=p['tp']
            if slp is not None and (l<=slp if side>0 else h>=slp):
                b.close(name,min(o,slp) if side>0 else max(o,slp),t,'stop')
            elif tpp is not None and (h>=tpp if side>0 else l<=tpp):
                b.close(name,tpp,t,'target')
        if t.minute==0 and t.hour in (0,8,16):
            obs=funding.get(t-pd.Timedelta(hours=1),np.nan)
            # Delta FUNDING historical rate values are displayed as percent.
            b.fund(float(obs)/100. if pd.notna(obs) else None,o,t)
        if t.hour==23 and t.minute==59:
            b.daily.append(dict(day=t.floor('D'),equity=b.equity(c),cash=b.cash,position_count=len(b.positions)))
        if b.equity(c)<=0:
            raise RuntimeError(f'Modeled account insolvent at {t}')
    return b


def monthly_report(book,source_audit,minute,warm_info,flow_info,funding_info,capital,funding_series=None):
    days=pd.DataFrame(book.daily).set_index('day') if book.daily else pd.DataFrame(columns=['equity'])
    trades=pd.DataFrame(book.trades)
    rows=[];prev_cap=float(capital)
    original={x['month']:x for x in source_audit}
    for month in pd.period_range('2025-01','2026-10',freq='M'):
        s=str(month)
        st=pd.Timestamp(month.start_time,tz='UTC');en=pd.Timestamp((month+1).start_time,tz='UTC')
        group=days.loc[(days.index>=st)&(days.index<en)]
        actual=len(minute.loc[(minute.index>=st)&(minute.index<en)])
        expected=int((en-st)/pd.Timedelta(minutes=1))
        complete=(actual==expected and len(group)==int((en-st).days))
        warmup=warm_info.get('warmup_from_delta_api',False) or st>=pd.Timestamp('2025-08-01',tz='UTC')
        # Distinguish an estimated PnL with missing cost data from a complete estimate.
        fr_expected=pd.date_range(st,en,freq='8h',inclusive='left')
        f_in_month=funding_series.index.intersection(fr_expected-pd.Timedelta(hours=1)) if funding_series is not None else []
        funding_complete=not any(st<=tt<en for tt in book.missing_funding_times)
        flow_complete=bool(flow_info['mode']=='ABLATION_WITHOUT_FLOW_GATE' or (
            flow_info['mode'] in ('strict','genuine_user_supplied_flow') and flow_info.get('available',0)>0) or
            flow_info.get('monthly_available',{}).get(s,0)==int((en-st)/pd.Timedelta(hours=1)))
        # A missing flow gate disables TB entirely in strict mode and must not be
        # mislabeled as a valid reproduction of the combined three-sleeve system.
        status=('MODELLED' if complete and warmup and funding_complete and flow_complete else
            ('MISSING_CANDLES' if not complete else 'UNWARMED_SMA200' if not warmup else
             'FUNDING_RATE_GAP' if not funding_complete else 'FLOW_MISSING'))
        ret=100*(float(group.equity.iloc[-1])/prev_cap-1) if len(group) else None
        if len(group):prev_cap=float(group.equity.iloc[-1])
        mt=trades[trades.exit_time.astype('datetime64[ns, UTC]').between(st,en-pd.Timedelta(nanoseconds=1))] if len(trades) else trades
        rows.append(dict(month=s,status=status,monthly_return_pct=ret if status=='MODELLED' else None,
             diagnostic_unverified_pct=ret,complete_minutes=actual,expected_minutes=expected,
             trades=int(len(mt)),winning_trades=int(mt.win.sum()) if len(mt) else 0,
             losing_trades=int((~mt.win).sum()) if len(mt) else 0))
    return pd.DataFrame(rows),days,trades


def self_test():
    b=Book(10000,.0005,.0002,.18,.001,False,2.)
    t=pd.Timestamp('2026-01-01',tz='UTC')
    b.open('TrendBreakdown',1,100.,10.,t,sl=95.,tp=110.,maxhold=pd.Timedelta(hours=24))
    assert 'TrendBreakdown' in b.positions
    b.close('TrendBreakdown',110.,t+pd.Timedelta(hours=1),'target')
    assert len(b.trades)==1 and b.trades[0]['net_model_usd']>0
    assert 0<b.trades[0]['gst_usd']<b.trades[0]['fee_usd']
    # 30-minute waiver applies only when explicitly enabled; not automatically.
    c=Book(10000,.0005,.0002,.18,.001,True,2.)
    c.open('tb',-1,100.,10.,t)
    c.close('tb',99.,t+pd.Timedelta(minutes=20),'test')
    assert c.trades[0]['scalper_fee_waiver'] and c.trades[0]['net_model_usd']>0
    assert reward_target(100,-1,5,2)==90, 'SHORT TP must be below entry'
    assert reward_target(100,1,5,2)==110, 'LONG TP must be above entry'
    print('SELF_TEST_PASS fee,gst,slippage,scalper_waiver,portfolio_bookkeeping,TP_orientation')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root',type=Path)
    p.add_argument('--output-dir',type=Path,default=Path('/tmp/cryptoquantix-independent-results'))
    p.add_argument('--fee',type=float,default=.0005,help='Default taker 0.05 percent per side, fraction')
    p.add_argument('--slippage',type=float,default=.0002,help='Assumed 0.02 percent side, fraction')
    p.add_argument('--gst',type=float,default=.18)
    p.add_argument('--capital',type=float,default=10000.)
    p.add_argument('--flow-mode',choices=['strict','binance-proxy','no-flow-filter'],default='binance-proxy')
    p.add_argument('--flow-csv',type=Path,default=None)
    p.add_argument('--scalper-offer',action='store_true',help='Only 30m or shorter round trips receive closing fee waiver')
    p.add_argument('--no-api',action='store_true',help='Disable fetching missing warmup/gap/funding; source-only study')
    p.add_argument('--self-test',action='store_true')
    args=p.parse_args()
    if args.self_test:self_test();return
    if args.data_root is None:p.error('--data-root required')
    root=args.data_root.resolve();out=args.output_dir.resolve()
    if root==out or root in out.parents:p.error('Output cannot be inside read-only source repo')
    if min(args.fee,args.slippage,args.gst,args.capital)<0 or args.capital<=0:p.error('Invalid fee/capital input')
    out.mkdir(parents=True,exist_ok=True)
    audit=source.data_audit(root)
    minute=source.read_history(root,audit)
    minute,repair=repair_minute_in_memory(minute,fetch=not args.no_api)
    daily,warm=daily_with_warmup(minute,fetch=not args.no_api)
    hours=pd.date_range(START,END,freq='h',inclusive='left')
    flow,flow_info=load_flow(root,hours,args.flow_mode,args.flow_csv)
    hourly=make_hourly(minute,flow)
    funding,funding_info=load_funding(root,fetch=not args.no_api)
    b=backtest(minute,daily,hourly,funding,capital=args.capital,fee=args.fee,slip=args.slippage,
               gst=args.gst,contract=.001,scalp=args.scalper_offer,cap=2.)
    monthly,days,trades=monthly_report(b,audit,minute,warm,flow_info,funding_info,args.capital,funding)
    months=monthly[monthly.status=='MODELLED'];net=monthly.monthly_return_pct.dropna()
    draw=(1-days.equity/days.equity.cummax()).max()*100 if len(days) else None
    summary={'status':'INDEPENDENT_RESEARCH_PROXY_NOT_EXACT_DELTA_EXECUTION','months_modelled':len(months),
     'months_profitable':int((net>0).sum()),'months_losing':int((net<0).sum()),
     'total_model_equity_return_pct':(float(days.equity.iloc[-1])/args.capital-1)*100 if len(days) else None,
     'daily_mark_to_market_drawdown_pct':float(draw) if draw is not None else None,
     'funding_settlements_without_rate_while_open':b.missing_funding,'trade_count':len(trades),'winners':int(trades.win.sum()) if len(trades) else 0,
     'losers':int((~trades.win).sum()) if len(trades) else 0,
     'flow':flow_info,'funding':funding_info,'warmup':warm,'minute_repair':repair,
     'cost_model':{'fee_side_taker':args.fee,'slippage_side_assumed':args.slippage,'GST_on_fee':args.gst,
      'scalper_offer_enabled':args.scalper_offer,'contract_BTC':.001,'leverage_gross_cap':2.0},
     'CAVEAT':['Funding is an observation-based PROXY, not settled exchange payments',
      'Binance taker-buy volume is CROSS-VENUE PROXY, not authentic Delta orderflow',
      'CryptoQuantix original engine has not been run byte-for-byte',
      'No actual bid-ask data, forced liquidations or funding settlement ledger verified']}
    monthly.to_csv(out/'monthly_results.csv',index=False)
    days.to_csv(out/'daily_equity.csv')
    trades.to_csv(out/'closed_trades.csv',index=False)
    pd.DataFrame(b.fills).to_csv(out/'fills.csv',index=False)
    pd.DataFrame(audit).to_csv(out/'archive_manifest_verified.csv',index=False)
    (out/'summary.json').write_text(json.dumps(summary,indent=2,default=str)+'\n')
    print(json.dumps(summary,indent=2,default=str))
    print(monthly[['month','status','monthly_return_pct','trades','winning_trades','losing_trades']].to_string(index=False))

if __name__=='__main__':main()