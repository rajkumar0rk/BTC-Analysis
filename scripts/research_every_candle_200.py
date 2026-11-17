#!/usr/bin/env python3
"""Exhaustive every-candle BTCUSD 200-point first-passage research.

Every authentic 1-minute OHLCV row is inspected. A candidate signal only uses
completed past candles. Its fill is the immediately following 1-minute OPEN.
Both long and short are evaluated separately, never as simultaneous portfolios.

Do not mistake a retrospective perfect-entry label for an executable strategy.
All chronological periods are research-exposed; none is a pristine holdout.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit

BASE = Path("data/delta_india/BTCUSD/1m")
OUT = Path("analysis/institutional_discovery_stage6_every_candle_200")
STOP = np.array([0.5, 25., 50., 100., 150., 200., 300., 500.], dtype=np.float64)
MAX_MINUTES = 240
FEE = 0.0005 * 1.18  # taker 0.05% per side, 18% GST on fees
SLIPPAGE = 5.0  # deliberately adverse 5 BTC price points PER SIDE
PERIOD_NAMES = ("2025_train", "2026_H1_validation",
                "2026_H2_seen_recheck", "2026_Nov_recent_exploratory")
SEED = 20261117


def read_archive():
    files = sorted(BASE.glob("20??-??.csv.gz"))
    if len(files) < 12:
        raise ValueError("Historical monthly futures dataset not found")
    pieces = []
    for filename in files:
        x = pd.read_csv(filename, compression="gzip",
                        usecols=["time", "open", "high", "low", "close", "volume"])
        if len(x) == 0:
            raise ValueError("Empty partition " + str(filename))
        pieces.append(x)
    raw = pd.concat(pieces, ignore_index=True)
    raw["time"] = raw.time.astype("int64")
    raw = raw.sort_values("time", kind="stable").reset_index(drop=True)
    t = raw.time.to_numpy(np.int64)
    if np.any(np.diff(t) <= 0):
        raise ValueError("Duplicate or out of order timestamp; cannot research")
    for field in ("open", "high", "low", "close", "volume"):
        if not np.isfinite(raw[field].to_numpy(float)).all():
            raise ValueError("Missing/invalid " + field)
    if ((raw.low <= 0) | (raw.high < raw.low) | (raw.open < raw.low) |
        (raw.close < raw.low) | (raw.open > raw.high) |
        (raw.close > raw.high) | (raw.volume < 0)).any():
        raise ValueError("OHLCV is inconsistent")
    if (np.diff(t) % 60 != 0).any():
        raise ValueError("Non-minute timestamps")
    breaks = np.flatnonzero(np.diff(t) != 60) + 1
    starts = np.r_[0, breaks].astype(np.int32)
    ends = np.r_[breaks, len(t)].astype(np.int32)
    seg_end = np.empty(len(t), np.int32)
    seg_start = np.empty(len(t), np.int32)
    gaps = []
    for a, b in zip(starts, ends):
        seg_end[a:b] = b
        seg_start[a:b] = a
    for b in breaks:
        gaps.append(dict(after_utc=str(pd.to_datetime(t[b-1], unit="s", utc=True)),
                         before_utc=str(pd.to_datetime(t[b], unit="s", utc=True)),
                         missing_minutes=int((t[b]-t[b-1])//60-1)))
    raw.index = pd.to_datetime(raw.time, unit="s", utc=True)
    names = [x.name for x in files]
    quality = dict(source="Delta Exchange India BTCUSD 1m compressed API candles",
                   months=len(files), partitions=names, observed_candles=len(raw),
                   first_utc=str(raw.index[0]), last_utc=str(raw.index[-1]),
                   expected_dense_candles=int((t[-1]-t[0])//60+1),
                   missing_minutes=int((t[-1]-t[0])//60+1-len(raw)),
                   continuous_segments=len(ends), gaps=gaps)
    return raw, seg_start, seg_end, quality


@njit(cache=True)
def first_passage(op, hi, lo, seg_end, stops, horizon):
    """First touch offsets from the NEXT minute open. Stop wins same-bar tie.

    t200 and tnet are 0-based minutes; -1 denotes not reached by horizon.
    MAE up through the first target minute *includes that entire minute*.
    A 'clean' TP thus requires zero adverse OHLC movement even in its TP bar.
    """
    n = len(op)
    t200 = np.full((n, 2), -1, dtype=np.int16)
    tnet = np.full((n, 2), -1, dtype=np.int16)
    tstop = np.full((n, 2, len(stops)), -1, dtype=np.int16)
    mae200 = np.full((n, 2), np.nan, dtype=np.float32)
    for k in range(n):
        entry = op[k]
        last = min(k + horizon, seg_end[k])
        for d in range(2):
            side = 1 if d == 0 else -1
            # Exact gross move needed for 200 NET after a standard market
            # entry/exit, symmetric slip and fee on each executed notional.
            net_goal = (200. + 2.*5. + 2.*0.00059*entry) / (1.-0.00059*side)
            next_stop = 0
            max_adverse = 0.
            for j in range(k, last):
                good = hi[j]-entry if side == 1 else entry-lo[j]
                bad = entry-lo[j] if side == 1 else hi[j]-entry
                if bad > max_adverse:
                    max_adverse = bad
                while next_stop < len(stops) and max_adverse >= stops[next_stop]:
                    tstop[k,d,next_stop] = j-k
                    next_stop += 1
                if t200[k,d] == -1 and good >= 200.:
                    t200[k,d] = j-k
                    mae200[k,d] = max_adverse
                if tnet[k,d] == -1 and good >= net_goal:
                    tnet[k,d] = j-k
                if t200[k,d] >= 0 and tnet[k,d] >= 0:
                    break
    return t200, tnet, tstop, mae200


def periods(ix):
    t = ix.view("i8")
    c1 = pd.Timestamp("2026-01-01", tz="UTC").value
    c2 = pd.Timestamp("2026-07-01", tz="UTC").value
    c3 = pd.Timestamp("2026-11-01", tz="UTC").value
    p = np.empty(len(ix), np.int8)
    p[:] = 3
    p[t < c3] = 2
    p[t < c2] = 1
    p[t < c1] = 0
    return p


def engineer_features(f, seg_start, seg_end, p):
    """Predeclared price and volume features, available at signal close."""
    n = len(f)
    ix = f.index
    op = f.open.to_numpy(float)
    hi = f.high.to_numpy(float)
    lo = f.low.to_numpy(float)
    cl = f.close.to_numpy(float)
    v = f.volume.to_numpy(float)
    rg = np.maximum(hi-lo, 0)
    body = cl-op
    close_loc = np.divide(cl-lo, rg, out=np.full(n,0.5), where=rg>0)
    raw = pd.DataFrame(dict(op=op,hi=hi,lo=lo,cl=cl,vol=v,rg=rg), index=ix)
    range_med60 = raw.rg.rolling(60,min_periods=60).median().shift(1).to_numpy()
    volume_mean60 = raw.vol.rolling(60,min_periods=60).mean().shift(1).to_numpy()
    prev_high20 = raw.hi.rolling(20,min_periods=20).max().shift(1).to_numpy()
    prev_low20 = raw.lo.rolling(20,min_periods=20).min().shift(1).to_numpy()
    prev_high60 = raw.hi.rolling(60,min_periods=60).max().shift(1).to_numpy()
    prev_low60 = raw.lo.rolling(60,min_periods=60).min().shift(1).to_numpy()
    prev_high10 = raw.hi.rolling(10,min_periods=10).max().shift(1).to_numpy()
    prev_low10 = raw.lo.rolling(10,min_periods=10).min().shift(1).to_numpy()
    mean_range10 = raw.rg.rolling(10,min_periods=10).mean().shift(1).to_numpy()
    xvol = np.divide(v, volume_mean60,
                     out=np.zeros(n,dtype=float),where=volume_mean60>0)
    xrange = np.divide(rg,range_med60,
                      out=np.zeros(n,dtype=float),where=range_med60>0)
    trend60 = np.full(n,0.)
    trend60[60:] = cl[60:] - cl[:-60]
    prior_red = np.r_[False,body[:-1]<0]
    prior_green = np.r_[False,body[:-1]>0]
    signal = {}
    # All minutes, every directional candidate explicitly assessed.
    signal["every_minute_long"] = (np.ones(n,dtype=bool),1,"shift")
    signal["every_minute_short"] = (np.ones(n,dtype=bool),-1,"shift")
    burst = (xrange>=2) & (xvol>=1.5) & (np.abs(body)>=0.65*rg)
    signal["strong_burst_long"] = (burst & (body>0) & (close_loc>=.85),1,"shift")
    signal["strong_burst_short"] = (burst & (body<0) & (close_loc<=.15),-1,"shift")
    signal["20m_accepted_breakout_long"] = (
        (cl>prev_high20)&(close_loc>=.8)&(xvol>=1.25),1,"shift")
    signal["20m_accepted_breakout_short"] = (
        (cl<prev_low20)&(close_loc<=.2)&(xvol>=1.25),-1,"shift")
    signal["20m_rejected_sweep_long"] = (
        (lo<prev_low20)&(cl>prev_low20)&(close_loc>=.75)&(xrange>=1.),1,"shift")
    signal["20m_rejected_sweep_short"] = (
        (hi>prev_high20)&(cl<prev_high20)&(close_loc<=.25)&(xrange>=1.),-1,"shift")
    signal["60m_rejected_sweep_long"] = (
        (lo<prev_low60)&(cl>prev_low60)&(close_loc>=.8)&(xrange>=1.5),1,"shift")
    signal["60m_rejected_sweep_short"] = (
        (hi>prev_high60)&(cl<prev_high60)&(close_loc<=.2)&(xrange>=1.5),-1,"shift")
    signal["trend_pullback_reclaim_long"] = (
        (trend60>=3*range_med60)&prior_red&(body>0)&
        (close_loc>=.8)&(xrange>=1.)&(lo<=np.r_[lo[0],cl[:-1]]),1,"shift")
    signal["trend_pullback_reclaim_short"] = (
        (trend60<=-3*range_med60)&prior_green&(body<0)&
        (close_loc<=.2)&(xrange>=1.)&(hi>=np.r_[hi[0],cl[:-1]]),-1,"shift")
    compressed = mean_range10<=.7*range_med60
    signal["compression_break_long"] = (
        compressed&(cl>prev_high10)&(close_loc>=.8)&(xvol>=1.25),1,"shift")
    signal["compression_break_short"] = (
        compressed&(cl<prev_low10)&(close_loc<=.2)&(xvol>=1.25),-1,"shift")

    # Genuine completed 5m and 15m candle signals: the label "right"
    # marks the earliest following minute at which the aggregated bar exists.
    for m in (5,15):
        rule = f"{m}min"
        ohlcv = raw.resample(f"{m}min",closed="left",label="right").agg(
            op=("op","first"), hi=("hi","max"), lo=("lo","min"),
            cl=("cl","last"), vol=("vol","sum"), count=("cl","count"))
        ohlcv["range"] = ohlcv.hi-ohlcv.lo
        ohlcv["prior_high"] = ohlcv.hi.rolling(12,min_periods=12).max().shift(1)
        ohlcv["prior_low"] = ohlcv.lo.rolling(12,min_periods=12).min().shift(1)
        ohlcv["vavg"] = ohlcv.vol.rolling(12,min_periods=12).mean().shift(1)
        ohlcv["loc"] = (ohlcv.cl-ohlcv.lo)/ohlcv["range"].replace(0,np.nan)
        isfull = ohlcv["count"] == m
        vl = ohlcv.vol>=1.25*ohlcv.vavg
        up = isfull&vl&(ohlcv.cl>ohlcv.prior_high)&(ohlcv["loc"]>=.8)
        dn = isfull&vl&(ohlcv.cl<ohlcv.prior_low)&(ohlcv["loc"]<=.2)
        for label, condition, side in (("long",up,1),("short",dn,-1)):
            arr = np.zeros(n,dtype=bool)
            candidate_idx = ix.get_indexer(ohlcv.index[condition.fillna(False)])
            candidate_idx = candidate_idx[candidate_idx>=0]
            arr[candidate_idx] = True
            signal[f"{rule}_close_breakout_{label}"] = (arr,side,"direct")
    # A full four-hour 1m forward window plus 180 contiguous past minutes.
    # Never bridge a missing minute or a chronological period boundary.
    entries = np.arange(n)
    valid = ((entries-seg_start)>=180)&((seg_end-entries)>=MAX_MINUTES)
    future_end_index = np.minimum(entries+MAX_MINUTES-1,n-1)
    valid &= p[entries]==p[future_end_index]
    masks = {}
    for key,(cond,side,mode) in signal.items():
        cond=np.asarray(cond,dtype=bool)
        if mode=="shift":
            cond=np.r_[False,cond[:-1]]
        masks[key]=(cond&valid,side)
    return masks,valid


def hit_rates(mask, side, period, t200, tnet, tstop, mae, h):
    d=0 if side==1 else 1
    ids=np.flatnonzero(mask & (period==h[0]))
    if not len(ids):return None
    horizon=h[1]
    tp=t200[ids,d].astype(np.int32)
    net=tnet[ids,d].astype(np.int32)
    g=(tp>=0)&(tp<horizon)
    ng=(net>=0)&(net<horizon)
    clean=g & (mae[ids,d]<=0.)
    x=dict(period=PERIOD_NAMES[h[0]],horizon_min=horizon,
           signals=len(ids),target_200_pct=round(100*g.mean(),3),
           target_200_net_after_fees_pct=round(100*ng.mean(),3),
           clean_200_zero_adverse_pct=round(100*clean.mean(),5),
           clean_count=int(clean.sum()))
    for stop in (25,50,100,200,300):
        s=int(np.searchsorted(STOP,stop))
        first=tstop[ids,d,s]
        good = g & ((first<0)|(tp<first))
        # Count 200 NET target reached before the stop, including same-minute
        # stop-first tie handling. This is NOT a claim of realized profit.
        netgood=ng&((first<0)|(net<first))
        x[f"tp_before_stop_{stop}_pct"]=round(100*good.mean(),3)
        if stop == 100:
            x["net200_before_stop100_pct"]=round(100*netgood.mean(),3)
    return x


def run_replay(mask,side,period,op,hi,lo,cl,t200,tstop,stop,horizon):
    d=0 if side==1 else 1
    stop_index = -1 if stop is None else int(np.searchsorted(STOP,float(stop)))
    candidates=np.flatnonzero(mask)
    records=[]
    occupied_until=-1
    for k in candidates:
        if k<=occupied_until: continue
        tgt=int(t200[k,d])
        st=int(tstop[k,d,stop_index]) if stop_index>=0 else -1
        if st>=horizon:st=-1
        if tgt>=horizon:tgt=-1
        entry_mid=float(op[k])
        if st>=0 and (tgt<0 or st<=tgt):
            last=k+st
            barrier=entry_mid-side*stop
            exit_mid=(min(float(op[last]),barrier) if side==1
                      else max(float(op[last]),barrier))
            reason="stop"
        elif tgt>=0:
            last=k+tgt
            exit_mid=entry_mid+side*200.
            reason="target"
        else:
            last=k+horizon-1
            exit_mid=float(cl[last])
            reason="timeout"
        occupied_until=last
        fill_in=entry_mid+side*SLIPPAGE
        fill_out=exit_mid-side*SLIPPAGE
        gross=side*(exit_mid-entry_mid)
        realized_after_slip=side*(fill_out-fill_in)
        entryfee=FEE*fill_in
        exitfee=FEE*fill_out
        net_std=realized_after_slip-entryfee-exitfee
        # Scenario assumption: zero closing fee ONLY for qualifying <=30m;
        # fee voucher reimbursements are NOT booked as spendable cash.
        net_offer=realized_after_slip-entryfee-(0 if last-k+1<=30 else exitfee)
        records.append((int(k),int(last),int(period[k]),reason,
                        round(float(gross),3),round(float(net_std),3),
                        round(float(net_offer),3),int(last-k+1)))
    return records


def summarize_trades(ledger):
    rows=[]
    for keys,g in ledger.groupby(["rule","side","model","period"],sort=True):
        g=g.sort_values("entry_index")
        for fee in ("net_standard_pts","net_scalper_scenario_pts"):
            v=g[fee].to_numpy(float)
            gains=float(v[v>0].sum())
            losses=float(-v[v<0].sum())
            eq=np.r_[0.,np.cumsum(v)]
            dd=float(np.max(np.maximum.accumulate(eq)-eq))
            loss_series=v<=0
            longest=running=0
            for x in loss_series:
                running=running+1 if x else 0
                longest=max(longest,running)
            rows.append(dict(zip(["rule","side","model","period"],keys),
                fee_model="standard_taker" if fee=="net_standard_pts" else "eligible_scalper_scenario",
                trades=len(g),target_hits=int((g.reason=="target").sum()),
                profitable_trades=int((v>0).sum()),
                losses_or_flat=int((v<=0).sum()),
                win_pct=round(100*float((v>0).mean()),2),
                avg_net_pts=round(float(v.mean()),3),
                net_total_pts=round(float(v.sum()),2),
                worst_net_trade_pts=round(float(v.min()),2),
                profit_factor=round(gains/losses,3) if losses else None,
                max_drawdown_pts=round(dd,2),
                max_losing_streak=longest,
                avg_hold_min=round(float(g.duration_min.mean()),2)))
    return pd.DataFrame(rows)


def save_labels(f,p,valid,t200,tnet,tstop,mae):
    """Compressed per-minute labels: inspectable exhaustive record, not trades."""
    entries=np.flatnonzero(valid)
    fordir=[]
    for d, direction in enumerate(("long","short")):
        x=pd.DataFrame({
            "entry_unix_s": f.time.to_numpy(np.int64)[entries],
            "direction": direction,
            "period": p[entries],
            "entry_mid": f.open.to_numpy(float)[entries],
            "first_gross200_min_offset": t200[entries,d],
            "first_net200_min_offset": tnet[entries,d],
            "pre_target_max_adverse_pts": mae[entries,d],
            "first_0p5_stop_offset": tstop[entries,d,0],
            "first_25_stop_offset": tstop[entries,d,1],
            "first_50_stop_offset": tstop[entries,d,2],
            "first_100_stop_offset": tstop[entries,d,3],
            "first_200_stop_offset": tstop[entries,d,5],
            "first_300_stop_offset": tstop[entries,d,6]})
        fordir.append(x)
    table=pd.concat(fordir,ignore_index=True)
    table.to_csv(OUT/"every_candle_directional_labels.csv.gz",index=False,
                 compression={"method":"gzip","compresslevel":5,"mtime":0})


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f, seg_start, seg_end,quality=read_archive()
    p=periods(f.index)
    masks,valid=engineer_features(f,seg_start,seg_end,p)
    op=f.open.to_numpy(np.float64)
    hi=f.high.to_numpy(np.float64)
    lo=f.low.to_numpy(np.float64)
    cl=f.close.to_numpy(np.float64)
    t200,tnet,tstop,mae=first_passage(op,hi,lo,seg_end,STOP,MAX_MINUTES)
    save_labels(f,p,valid,t200,tnet,tstop,mae)
    rates=[]
    for name,(mask,side) in masks.items():
        for v in range(4):
            for horizon in (30,60,240):
                rec=hit_rates(mask,side,p,t200,tnet,tstop,mae,(v,horizon))
                if rec is not None:
                    rates.append(dict(rule=name,side=side,**rec))
    rates=pd.DataFrame(rates)
    rates.to_csv(OUT/"all_candle_conditional_rates.csv",index=False)

    # NY hours correctly handle US daylight saving time.
    ny=f.index.tz_convert("America/New_York")
    n_hour=np.asarray(ny.hour,dtype=np.int8)
    n_weekday=np.asarray(ny.dayofweek,dtype=np.int8)
    timed=[]
    for side,d in ((1,0),(-1,1)):
        for per in range(4):
            for hour in range(24):
                eligible=np.flatnonzero(valid&(p==per)&(n_hour==hour))
                if not len(eligible):continue
                tt=t200[eligible,d]
                st=tstop[eligible,d,3]
                good=(tt>=0)&(tt<30)
                success=good&((st<0)|(tt<st))
                clean=good&(mae[eligible,d]<=0)
                timed.append(dict(period=PERIOD_NAMES[per],side=side,
                    ny_hour=hour,eligible_candles=len(eligible),
                    tp200_within30_pct=round(100*good.mean(),3),
                    tp200_before_100stop_pct=round(100*success.mean(),3),
                    no_adverse_tp200_pct=round(100*clean.mean(),5)))
    pd.DataFrame(timed).to_csv(OUT/"new_york_hour_profile.csv",index=False)

    trades=[]
    for name,(mask,side) in masks.items():
        for stop,horizon in ((100,30),(100,60),(200,30),(200,60),(None,60)):
            model=(f"no_stop_timeout_{horizon}m" if stop is None else
                   f"sl{stop}_tp200_{horizon}m")
            for k,last,per,reason,gross,netstd,netoffer,mins in run_replay(
                    mask,side,p,op,hi,lo,cl,t200,tstop,stop,horizon):
                trades.append(dict(rule=name,side=side,model=model,
                    period=PERIOD_NAMES[per],entry_index=k,
                    entry_unix_s=int(f.time.iat[k]),exit_unix_s=int(f.time.iat[last]),
                    reason=reason,gross_pts=gross,
                    net_standard_pts=netstd,
                    net_scalper_scenario_pts=netoffer,duration_min=mins))
    ledger=pd.DataFrame(trades)
    if ledger.empty:
        raise ValueError("No executable strategy trades")
    ledger.to_csv(OUT/"trade_ledger.csv.gz",index=False,
                  compression={"method":"gzip","compresslevel":5,"mtime":0})
    summary=summarize_trades(ledger)
    summary.to_csv(OUT/"trade_summary.csv",index=False)

    # A no-loss backtest demands zero realized losing/flat trades with a
    # meaningful number of trades separately in every historical period.
    strict=summary[(summary.fee_model=="standard_taker")&
                   (summary.trades>=100)&(summary.losses_or_flat==0)]
    strict.to_csv(OUT/"zero_loss_candidates.csv",index=False)
    baseline=rates[rates.rule.isin(("every_minute_long","every_minute_short"))]
    sub=summary[(summary.fee_model=="standard_taker")&
                (summary.model=="sl100_tp200_30m")]
    ranked=sub[sub.period=="2025_train"].sort_values(
                ["avg_net_pts","trades"],ascending=[False,False])
    quality.update(dict(usable_entry_candles=int(valid.sum()),
        evaluated_directions=int(valid.sum())*2,
        direction_labels_stored=int(valid.sum())*2,
        conditional_rules=len(masks), conditional_rate_rows=len(rates),
        separately_replayed_trade_rows=len(ledger),
        strategy_summary_rows=len(summary),
        confirmed_zero_loss_candidates=int(len(strict)),
        warning="Overlapping hypothetical labels are NOT independent trades",
        splits=list(PERIOD_NAMES),
        models="200 gross point TP; stop 100, 200, or no stop; 30/60min forced timeout",
        gross200_vs_net200="200 net requires fee-adjusted larger first-passage target",
        no_adverse="strict conservative OHLC: entire TP minute may move against entry",
        fill="following minute open; stop wins ambiguous OHLC same-bar touches",
        historical_fee_assumptions=dict(taker_per_side=0.0005,
            GST_on_fee=0.18, slip_points_per_side=SLIPPAGE,
            optional_scalper_zero_exit_fee_if_hold_le_30m=True,
            offer_eligibility_not_verified_for_historical_trades=True),
        limitations=[
            "No historical bid/ask quote, order-book depth or intraminute tick path",
            "Favorable target may be unfillable at modeled high/low",
            "Missing source minutes not fabricated; skip signals spanning gaps",
            "All four historical splits are used for exploratory research, not pristine forward testing",
            "Overlapping minute labels produce severely correlated observations",
            "Fee voucher credits are not counted as cash; historical Scalper Offer unknown",
            "Funding, market impact, liquidation, capital and margin not reconstructed",
            "No ability to guarantee a 200-point move without losses",
            "Only rule-based subset scanned; many possible rules not tested",
            "200 BTC points represents quote-price move, not dollar account P&L"]))
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    report=[
        "# Stage 6 — Every BTCUSD 1m candle: 200 points, clean paths and executable entries",
        "",
        "## Dataset audit",
        f"- Real 1m candles loaded: **{len(f):,}**",
        f"- Fully eligible next-open entries: **{int(valid.sum()):,}** per direction",
        f"- All long+short entry paths evaluated: **{2*int(valid.sum()):,}**",
        f"- Gaps: **{quality['missing_minutes']:,}** missing minutes across **{len(quality['gaps'])}** breaks; never filled",
        f"- Predeclared directional rule names: **{len(masks)}**",
        f"- Strict zero-loss strategies with at least 100 trades in a period: **{len(strict)}** cells (not a guarantee)",
        "",
        "## Honest definitions",
        "- 'Clean 200' means no adverse midprice movement in ANY 1m OHLC bar before or in the TP minute.",
        "- First 200 achieved within horizon is an ex-post label, not an entry signal.",
        "- 200 net after standard fees requires a larger dynamic price target, computed using actual entry BTC price.",
        "- Same-bar stop and target ambiguity is ALWAYS counted as a stop.",
        "- One trade at a time separately for each candidate model, no forced daily trades.",
        "- Standard scenario: 0.05% taker each side + 18% GST and 5 points adverse slippage each side.",
        "- Scalper scenario: closing fee waived only if the modeled holding time is <=30m, conditional on eligibility.",
        "- All historical intervals including November 2026 are exploratory; do not claim an independent holdout.",
        "",
        "## Unconditional all-candle reference (not a portfolio)",
        baseline[["rule","period","horizon_min","signals","target_200_pct",
                 "clean_200_zero_adverse_pct","tp_before_stop_100_pct",
                 "target_200_net_after_fees_pct"]].to_markdown(index=False),
        "",
        "## Predeclared executable strategies at 200 gross TP / 100 stop / 30m max",
        sub[["rule","period","trades","win_pct","avg_net_pts",
             "profit_factor","max_drawdown_pts","worst_net_trade_pts",
             "losses_or_flat"]].to_markdown(index=False),
        "",
        "## Rankings from 2025 training only (not evidence of future profitability)",
        ranked[["rule","trades","avg_net_pts","win_pct","losses_or_flat"]].head(16).to_markdown(index=False),
        "",
        "## Reproducible audit artifacts",
        "- every_candle_directional_labels.csv.gz (one entry time per long/short case)",
        "- all_candle_conditional_rates.csv",
        "- new_york_hour_profile.csv",
        "- trade_ledger.csv.gz (one open trade at a time per independently measured setup)",
        "- trade_summary.csv",
        "- zero_loss_candidates.csv (may contain header only)",
        "- quality.json (archive gaps, fees, exact sample counts)",
        "",
        "## Safeguards / limitations",
        *["- "+x for x in quality["limitations"]],
        "",
        "Conclusions must come from the actual table, not from choosing perfect historical candles.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE6_COMPLETE",json.dumps(dict(candles=len(f),usable=int(valid.sum()),
        paths=2*int(valid.sum()),missing=quality["missing_minutes"],
        replay_rows=len(ledger),strict_zero_loss_cells=len(strict))))
    print("ALL_CANDLE_REFERENCE\n",baseline.to_string(index=False))
    print("2025_TRAIN_TOP_200PT_SCALPS\n",ranked.head(16).to_string(index=False))
    print("2026_H1_200PT_SCALPS\n",sub[sub.period=="2026_H1_validation"].to_string(index=False))
    print("2026_NOV_200PT_SCALPS\n",sub[sub.period=="2026_Nov_recent_exploratory"].to_string(index=False))

if __name__=="__main__":
    main()
