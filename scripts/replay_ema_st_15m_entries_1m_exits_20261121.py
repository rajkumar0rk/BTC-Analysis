#!/usr/bin/env python3
"""Causal BTC/ETH EMA20 + Supertrend replay: 15m signals; REAL 1m OHLC exits.

Independent research only. Never authenticates with Delta or places orders.
Compared with the old 15m-OHLC path replays:
  * A completed 15m signal fills at the NEXT 1m open, not its own close.
  * Stops/liquidation proxy are inspected on each actual 1m OHLC bar.
  * Updated trailing stops are effective in the NEXT minute. No guessed O-H-L-C path.
  * Supertrend flip at 15m close exits at the NEXT minute open if still open.

One-minute bars STILL do not reveal intraminute order or live tick-by-tick
trailing. Stops' historical prices are idealized, and liquidation is a TRADED-
PRICE proxy, not Delta's MARK-price liquidation engine. No spread, funding,
price impact, order latency, or true offer-entitlement history is available.
"""
from __future__ import annotations
import hashlib, json, math, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from replay_btc_ema_st_screenshot import indicators  # exact original indicators

OUT = ROOT / 'analysis' / 'ema_st_15m_1m_20261121'
OUT.mkdir(parents=True, exist_ok=True)
EQUITY = 100.0
LEVERAGE = 100
MARGIN_BUDGET = 10.0
MAINTENANCE = 0.0025  # model proxy, NOT historical exchange liquidation rules
TAKER = 0.0005
GST = 0.18
LIQ_PENALTY = 0.0005
OFFER_MIN = 30
SETTINGS = {
    'signal_timeframe': '15m', 'exit_timeframe': '1m',
    'entry_fill': 'next 1m open after signal closes',
    'entry_conditions': 'EMA20 pullback close with sustained Supertrend(10,3), ATR14/20>=1 and volume/20>=1.5',
    'initial_stop': '2 x 15m ATR(14) from actual next-minute entry',
    'trailing': 'BTC 150 point activation / 50 point distance; ETH scaled by entry/80000 and rounded to 0.05',
    'trailing_stop_reprices': 'after completed 1m candle, active next 1m candle',
    'supertrend_flip': 'exit next 1m open after completed 15m flip',
    'starting_portfolio_usd': EQUITY, 'leverage': LEVERAGE,
    'fixed_isolated_margin_budget_per_trade_usd': MARGIN_BUDGET,
    'btc_lot': 0.001, 'eth_lot': 0.01,
    'taker_fee_each_side': TAKER, 'gst_on_fees': GST,
    'assumed_maintenance_fraction': MAINTENANCE,
    'assumed_liquidation_penalty_fraction': LIQ_PENALTY,
    'assumed_scalper_window_minutes': OFFER_MIN,
    'historical_offer_entitlement_verified': False,
    'funding': 'excluded; not zero in actual trading',
    'spread': 'excluded', 'live_liquidation_mark_price': 'unavailable',
    'intraminute_barrier_priority': 'existing stop/liquidation before trailing repricing',
}

def load(asset):
    d = ROOT / 'data' / 'delta_india' / f'{asset}USD' / '1m'
    m = json.loads((d / 'manifest.json').read_text())
    assert m['resolution'] == '1m' and m['symbol'] == f'{asset}USD'
    frames = []
    for part in m['partitions']:
        assert part['missing_minutes'] == 0, part
        p = d / part['file']
        assert hashlib.sha256(p.read_bytes()).hexdigest() == part['sha256_gzip'], p
        z = pd.read_csv(p, compression='gzip')
        assert len(z) == part['observed_candles'], p
        frames.append(z[['time', 'open', 'high', 'low', 'close', 'volume']])
    x = pd.concat(frames, ignore_index=True)
    t = x.time.to_numpy(dtype='int64')
    assert (t[1:] - t[:-1] == 60).all(), 'Missing or duplicate 1-minute bars'
    assert (t[0] % 900) == 0 and (len(x) % 15) == 0
    assert (x.high >= x[['open', 'close', 'low']].max(axis=1)).all()
    assert (x.low <= x[['open', 'close', 'high']].min(axis=1)).all()
    x['dt'] = pd.to_datetime(x.time, unit='s', utc=True)
    x = x.set_index('dt')
    f = x.resample('15min', origin='epoch', label='left', closed='left').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last',
        'volume': 'sum', 'time': 'count'})
    assert (f.time == 15).all(), 'Incomplete aggregated 15m bars'
    return x, indicators(f.drop(columns='time')), m

def decisions(f, n_minutes):
    """Decision made only once a 15m bar is closed; visible at NEXT 1m open."""
    entry = np.zeros(n_minutes, dtype='int8')
    stop_distance = np.zeros(n_minutes, dtype='float64')
    flip = np.zeros(n_minutes, dtype='int8')
    e = f.ema.to_numpy(); atr = f.atr14.to_numpy()
    d = f.dir.to_numpy(); ar = f.atr_ratio.to_numpy(); vr = f.volume_ratio.to_numpy()
    lo = f.low.to_numpy(); hi = f.high.to_numpy(); cl = f.close.to_numpy()
    for i in range(36, len(f) - 1):
        j = (i + 1) * 15
        if d[i] != d[i-1]:
            flip[j] = int(d[i])
        if not (np.isfinite(e[i]) and np.isfinite(atr[i]) and
                np.isfinite(ar[i]) and np.isfinite(vr[i])):
            continue
        if ar[i] < 1 or vr[i] < 1.5:
            continue
        side = 0
        if d[i] == d[i-1] == -1 and lo[i] <= e[i] and cl[i] > e[i]:
            side = +1
        elif d[i] == d[i-1] == +1 and hi[i] >= e[i] and cl[i] < e[i]:
            side = -1
        if side:
            entry[j] = side
            stop_distance[j] = 2 * float(atr[i])
    return entry, stop_distance, flip

def replay(asset, minute, f, offer, fill_mode, slippage_points):
    entry, stop_dist, flip = decisions(f, len(minute))
    op = minute.open.to_numpy(dtype='float64')
    hi = minute.high.to_numpy(dtype='float64')
    lo = minute.low.to_numpy(dtype='float64')
    dates = minute.index
    tick = 0.5 if asset == 'BTC' else 0.05
    lot = 0.001 if asset == 'BTC' else 0.01
    equity = EQUITY
    peak = EQUITY
    worstdd = 0.0
    trades = []
    open_position = None
    skipped_wallet = 0
    skipped_lot = 0
    all_signals = 0
    for j in range(37 * 15, len(minute)):
        # Once the preceding 15-minute candle closes, a flip exit can execute.
        old_position = open_position is not None
        closing = None
        if old_position:
            p = open_position
            if flip[j] == p['side']:
                closing = (float(op[j]), 'supertrend_flip')
        # A new signal is known only from the previous COMPLETED 15m candle.
        if not old_position and entry[j]:
            all_signals += 1
            side = int(entry[j])
            ep = float(op[j]) + side * slippage_points
            nlot = math.floor((MARGIN_BUDGET * LEVERAGE) / (ep * lot) + 1e-10)
            if nlot < 1:
                skipped_lot += 1
            else:
                qty = nlot * lot
                margin = ep * qty / LEVERAGE
                entry_fee_and_gst = ep * qty * TAKER * (1 + GST)
                if margin + entry_fee_and_gst > equity + 1e-9:
                    skipped_wallet += 1
                else:
                    initial_stop_points = max(tick, math.floor(stop_dist[j] / tick + .5) * tick)
                    liq = ((ep - margin/qty) / (1 - MAINTENANCE) if side == 1
                           else (ep + margin/qty) / (1 + MAINTENANCE))
                    activation = (150.0 if asset == 'BTC' else
                                  max(tick, math.floor((ep * 150 / 80000) / tick + .5) * tick))
                    distance = (50.0 if asset == 'BTC' else
                                max(tick, math.floor((ep * 50 / 80000) / tick + .5) * tick))
                    open_position = dict(side=side, ep=ep, qty=qty, margin=margin,
                        entry_j=j, stop=ep-side*initial_stop_points,
                        initial_stop=ep-side*initial_stop_points,
                        liq=liq, bankruptcy=ep-side*margin/qty,
                        activation=activation, distance=distance, best=ep,
                        active=False)
        if open_position is not None and closing is None:
            p = open_position
            side = p['side']
            stop, liq = p['stop'], p['liq']
            # If the 1m open jumped past any threshold, fill the observed open.
            if (side == 1 and op[j] <= liq) or (side == -1 and op[j] >= liq):
                closing = (float(op[j]), 'liquidation')
            elif (side == 1 and op[j] <= stop) or (side == -1 and op[j] >= stop):
                closing = (float(op[j]), 'stop_gap')
            else:
                # The closest protective threshold to entry is encountered first.
                barrier = max(stop, liq) if side == 1 else min(stop, liq)
                hit = (lo[j] <= barrier) if side == 1 else (hi[j] >= barrier)
                if hit:
                    is_liq = (liq >= stop) if side == 1 else (liq <= stop)
                    closing = (barrier, 'liquidation' if is_liq else
                               'trailing' if p['active'] else 'initial_stop')
                else:
                    # No fabricated order of high/low: only change the trail
                    # at the END of this minute, for the NEXT minute.
                    best = (max(p['best'], hi[j]) if side == 1 else
                            min(p['best'], lo[j]))
                    favorable = side * (best - p['ep'])
                    if favorable >= p['activation']:
                        p['active'] = True
                    if p['active']:
                        p['best'] = best
                        candidate = best - side*p['distance']
                        p['stop'] = max(stop, candidate) if side == 1 else min(stop, candidate)
        if closing is not None:
            p = open_position
            raw_exit, reason = closing
            exit_price = (p['bankruptcy'] if reason == 'liquidation' and fill_mode == 'bankruptcy'
                          else raw_exit - p['side'] * (0 if reason == 'liquidation' else slippage_points))
            qty, ep, side = p['qty'], p['ep'], p['side']
            gross = (exit_price-ep) * qty * side
            entry_fee = ep * qty * TAKER
            hold = j - p['entry_j']
            eligible = offer and (0 <= hold <= OFFER_MIN) and reason != 'liquidation'
            exit_fee = 0 if eligible or reason == 'liquidation' else exit_price*qty*TAKER
            liq_fee = exit_price * qty * LIQ_PENALTY if reason == 'liquidation' else 0.0
            gst = GST * (entry_fee + exit_fee + liq_fee)
            net = (max(-p['margin'], gross-liq_fee*(1+GST)) - entry_fee*(1+GST)
                   if reason == 'liquidation' else gross-entry_fee-exit_fee-gst)
            before = equity
            equity = max(0., equity + net)
            net = equity-before
            peak = max(peak, equity)
            worstdd = max(worstdd, 100*(1-equity/peak))
            trades.append(dict(asset=asset, entry_utc=str(dates[p['entry_j']]),
                exit_minute_utc=str(dates[j]), side='long' if side==1 else 'short',
                entry_price=ep, exit_price=exit_price, qty=qty, hold_minutes=hold,
                exit_reason=reason, initial_stop=p['initial_stop'],
                liquidation_proxy=p['liq'],
                gross_usd=gross, fee_entry_usd=entry_fee, fee_exit_usd=exit_fee,
                fee_liq_usd=liq_fee, gst_usd=gst, net_usd=net,
                equity_before_usd=before, equity_after_usd=equity,
                assumed_scalper_waiver=eligible))
            open_position = None
    z = pd.DataFrame(trades)
    wins = z.loc[z.net_usd>0, 'net_usd'].sum() if len(z) else 0.
    losses = -z.loc[z.net_usd<0, 'net_usd'].sum() if len(z) else 0.
    if len(z):
        z['exit_month_ist'] = pd.to_datetime(z.exit_minute_utc, utc=True).dt.tz_convert(
            'Asia/Kolkata').dt.strftime('%Y-%m')
    months = []
    previous = EQUITY
    bymonth = dict(tuple(z.groupby('exit_month_ist'))) if len(z) else {}
    for x in pd.period_range('2025-01', str(dates[-1].tz_convert('Asia/Kolkata').to_period('M')), freq='M'):
        month = str(x)
        subset = bymonth.get(month)
        end = previous if subset is None else float(subset.equity_after_usd.iloc[-1])
        profit = end-previous
        months.append(dict(month_ist=month, opening_usd=round(previous,4),
            net_usd=round(profit,4), return_pct=round(profit/previous*100,2) if previous else None,
            closing_usd=round(end,4), trades=0 if subset is None else len(subset),
            complete_month=month < '2026-11'))
        previous = end
    m = pd.DataFrame(months)
    completed = m[m.complete_month]
    stats = dict(asset=asset, result_status='simulated on genuine 1m OHLC',
        start_utc=str(dates[0]), end_utc=str(dates[-1]),
        complete_months=len(completed), profitable_complete_months=int((completed.net_usd>0).sum()),
        losing_complete_months=int((completed.net_usd<0).sum()),
        flat_complete_months=int((completed.net_usd==0).sum()),
        initial_equity_usd=EQUITY, end_closed_equity_usd=round(equity,4),
        net_profit_usd=round(equity-EQUITY,4), completed_trades=len(z),
        win_rate_pct=round(100*(z.net_usd>0).mean(),2) if len(z) else None,
        net_profit_factor=round(float(wins/losses),4) if losses>0 else None,
        liquidation_proxies=int((z.exit_reason=='liquidation').sum()) if len(z) else 0,
        max_closed_equity_drawdown_pct=round(worstdd,2),
        eligible_offer_trades=int(z.assumed_scalper_waiver.sum()) if len(z) else 0,
        skipped_insufficient_equity=skipped_wallet, skipped_too_small_lot=skipped_lot,
        signalled_entries_while_flat=all_signals,
        entry_fees_usd=round(float(z.fee_entry_usd.sum()),3) if len(z) else 0,
        exit_fees_usd=round(float(z.fee_exit_usd.sum()),3) if len(z) else 0,
        liq_fees_usd=round(float(z.fee_liq_usd.sum()),3) if len(z) else 0,
        gst_usd=round(float(z.gst_usd.sum()),3) if len(z) else 0,
        open_trade_at_end=open_position is not None,
        offer_hypothesis=bool(offer), liquidation_fill=fill_mode,
        adverse_slippage_points_per_side=slippage_points)
    return z, m, stats

def main():
    results = {'configuration': SETTINGS, 'datasets': {}, 'scenarios': {}}
    for asset in ('BTC', 'ETH'):
        minute, bars, manifest = load(asset)
        results['datasets'][asset] = dict(source=manifest['source'],
            minute_bars=len(minute), bars_15m=len(bars),
            archive_manifest_utc=manifest['generated_at_utc'])
        for offer in (False, True):
            for fill in ('threshold', 'bankruptcy'):
                for slip in (0.0, 0.5 if asset=='BTC' else 0.05):
                    label=f'{asset.lower()}_{"offer" if offer else "nooffer"}_{fill}_{"noslip" if slip==0 else "onetick"}'
                    trades, months, info = replay(asset,minute,bars,offer,fill,slip)
                    trades.to_csv(OUT / f'{label}_trades.csv.gz', index=False, compression='gzip')
                    months.to_csv(OUT / f'{label}_monthly.csv', index=False)
                    results['scenarios'][label] = info
                    print('BACKTEST_RESULT', label, json.dumps(info), flush=True)
    (OUT/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
    print('BACKTEST_COMPLETE', str(OUT), flush=True)

if __name__=='__main__':
    main()
