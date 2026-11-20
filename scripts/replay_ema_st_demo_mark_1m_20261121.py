#!/usr/bin/env python3
"""Delta Demo-like *historical approximation* for the legacy EMA20+ST 15m bot.

Inputs: actual Delta India 1-minute TRADED candles for completed 15m signals,
and actual Delta India 1-minute MARK candles for native mark-triggered stops.
No historical 3-second feed, bid/ask, fill tape, or account liquidation-price
history exists in the input archive. Thus this is not an exact 3-second replay.

Causal rules:
  * Signal on completed 15m candles; market entry at next traded 1m open.
  * Starting with entry minute, an exchange-native protective mark stop persists
    throughout each minute; check MARK open (gap) and MARK high/low.
  * On completed 15m Supertrend flip, market-exit at next 1m open; existing
    stop/liquidation wins if MARK open gaps beyond protection.
  * Monitor latest mark *observation* once per minute (minute close), then
    recompute/trail stop effective NEXT minute. Two observation scenarios:
       "close": minute-close mark approximates a periodic poll;
       "extreme": favorable minute extreme as an optimistic availability proxy
                  (effective NEXT minute; NEVER assumed before same-bar stop).
    Neither scenario can reproduce precise 3-second observations.
  * 2*ATR14 initial stop; optional 1-point BTC / $0.20 ETH pre-liquidation
    mark stop, close to modeled 100x liquidation.
  * Fees 0.05% taker per side plus 18% GST; optional HYPOTHETICAL 30-minute
    Scalper exit-fee waiver. No funding, L1 spread, real liquidation mark
    threshold, latency, real fill price basis, or market-impact reconstruction.
  * $100 portfolio; $10 fixed isolated per-trade margin, 100x, no auto add.

The real VPS execution code is NOT modified or run here.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from replay_ema_st_15m_entries_1m_exits_20261121 import load, decisions

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis" / "ema_st_demo_mark_1m_20261121"
OUT.mkdir(parents=True, exist_ok=True)

EQUITY = 100.0
MARGIN = 10.0
LEV = 100.
MAINTENANCE = 0.0025
FEE = 0.0005
GST = 0.18
LIQ_PENALTY = 0.0005

NOTES = {
    "strategy": "legacy_15m EMA20 plus Supertrend(10,3)",
    "signal": "closed 15m trade OHLC; next minute traded open entry",
    "native_stop_trigger": "1m MARK OHLC touches previously active mark stop",
    "trailing_reprice": "minute close mark observation; edit effective from next minute",
    "scenarios": {
        "close": "best favorable sampled minute CLOSE, closest guaranteed observation",
        "extreme": "best favorable 1m MARK extreme available after minute closes, upper-observation proxy, never same-minute trailing execution",
    },
    "pre_liquidation": "enabled; 1 BTC point or $0.20 ETH before 100x modeled threshold",
    "liquidation_source": "modeled 0.25%-maintenance proxy; historic Delta position liquidation_price is unavailable",
    "capital": {"initial_equity_usd": EQUITY, "isolated_margin_per_trade_usd": MARGIN, "leverage": 100},
    "trailing": "BTC 150 activation/50 distance; ETH entry * 150/80000 and 50/80000 rounded to tick",
    "taker_fee_fraction": FEE,
    "gst_on_fees_fraction": GST,
    "scalper_offer": "hypothetical <=30min exit-fee waiver when enabled; entitlement not verified",
    "excluded": ["historical bid/ask and spread", "slippage beyond tested fixed tick", "funding payments", "latency and order-fill uncertainty", "3-second individual mark observations", "actual Delta account liquidation-price history"],
    "limit": "Minute mark OHLC only identifies touched old stops; cannot establish within-minute trailing adjustment or real trade fills.",
}


def load_mark(asset, expected_times):
    symbol = f"{asset}USD"
    base = ROOT / "data" / "delta_india" / symbol / "institutional"
    manifest = json.loads((base / "history_manifest.json").read_text(encoding="utf-8"))
    assert manifest["symbol"] == symbol
    series = manifest["series"]["mark_1m"]
    assert series["native_source_symbol"] == f"MARK:{symbol}"
    frames = []
    for p in series["partitions"]:
        path = ROOT / p["partition"]
        data = pd.read_csv(path, compression="gzip", usecols=["time", "open", "high", "low", "close"])
        assert len(data) == p["rows"], path
        assert int(data.time.iloc[0]) == pd.Timestamp(p["first_utc"]).timestamp()
        assert int(data.time.iloc[-1]) == pd.Timestamp(p["last_utc"]).timestamp()
        frames.append(data)
    marks = pd.concat(frames, ignore_index=True)
    t = marks.time.to_numpy(dtype="int64")
    assert (np.diff(t) == 60).all(), "Mark minute data must be dense and in UTC sequence"
    assert (marks.high >= marks[["open", "close", "low"]].max(axis=1)).all()
    assert (marks.low <= marks[["open", "close", "high"]].min(axis=1)).all()
    original = pd.Index(t)
    expected = pd.Index(expected_times)
    common = expected.intersection(original)
    assert len(common) >= 980000, "Unexpected incomplete mark/trade overlap"
    positions = original.get_indexer(common)
    # Make sure all mark samples line up with traded minutes.
    assert (positions >= 0).all()
    marks = marks.iloc[positions].reset_index(drop=True)
    return marks, common.to_numpy(dtype="int64"), {
        "mark_rows_in_manifest": series["rows_saved"],
        "mark_first": series["earliest_utc"],
        "mark_last": series["latest_utc"],
        "overlap_minutes": len(marks),
        "mark_manifest_utc": manifest["generated_utc"],
    }


def trigger_old_stop(side, mark_open, mark_high, mark_low, stop, liq, flip):
    """Return mark barrier touch, with open-gap and current native stop priority.

    Stop price is a trigger, not a guaranteed fill. Historical trade/mark basis
    and execution liquidity unavailable. Report proxy using mark trigger.
    """
    if side == 1:
        if mark_open <= liq: return float(mark_open), "liq_gap_proxy"
        if mark_open <= stop: return float(mark_open), "native_stop_gap"
    else:
        if mark_open >= liq: return float(mark_open), "liq_gap_proxy"
        if mark_open >= stop: return float(mark_open), "native_stop_gap"
    if flip: return None, "supertrend_flip"
    threshold = max(stop, liq) if side == 1 else min(stop, liq)
    if side == 1 and mark_low <= threshold or side == -1 and mark_high >= threshold:
        is_liq = liq >= stop if side == 1 else liq <= stop
        return float(threshold), "liquidation_proxy" if is_liq else "native_stop_touch"
    return None, None


def evaluate(asset, minute, mark, bars, sampling, offer, slip, entry_start=None, entry_end=None):
    assert sampling in ("close", "extreme")
    tick = .5 if asset == "BTC" else .05
    lot = .001 if asset == "BTC" else .01
    buf = 1.0 if asset == "BTC" else .20
    N = len(minute)

    decision, dist, flip = decisions(bars, N)
    op = minute.open.to_numpy(dtype=float)
    idx = minute.index
    mo, mh, ml, mc = (mark[z].to_numpy(dtype=float) for z in ("open", "high", "low", "close"))

    equity = EQUITY
    peak = EQUITY
    dd_max = 0.
    position = None
    trades = []
    n_signal = n_wallet = n_lot = 0
    ambiguous = 0
    for j in range(37*15, N):
        just_opened = False
        prior = position is not None
        mark_exit = None
        reason = None

        if prior:
            p = position
            mark_exit, reason = trigger_old_stop(
                p["side"], mo[j], mh[j], ml[j], p["stop"], p["liq"], flip[j] == p["side"])

        if (not prior and decision[j] and
            (entry_start is None or idx[j] >= entry_start) and
            (entry_end is None or idx[j] < entry_end)):
            n_signal += 1
            side = int(decision[j])
            entry = float(op[j] + side*slip)
            contracts = math.floor(MARGIN*LEV/(entry*lot)+1e-10)
            if contracts < 1:
                n_lot += 1
            else:
                qty = contracts*lot
                margin = entry*qty/LEV
                fee_in = entry*qty*FEE*(1+GST)
                if equity < margin+fee_in:
                    n_wallet += 1
                else:
                    ad = max(tick, math.floor(dist[j]/tick+.5)*tick)
                    atr_stop = entry-side*ad
                    liq = ((entry-margin/qty)/(1-MAINTENANCE) if side == 1 else
                           (entry+margin/qty)/(1+MAINTENANCE))
                    preliq = math.ceil((liq+buf)/tick-1e-9)*tick if side == 1 \
                        else math.floor((liq-buf)/tick+1e-9)*tick
                    stop = max(preliq,atr_stop) if side == 1 else min(preliq,atr_stop)
                    # Model the bot's entry rejection if protected stop is
                    # at/through trade entry. Do not silently disable protection.
                    if (side == 1 and stop >= entry) or (side == -1 and stop <= entry):
                        continue
                    activation = 150. if asset == "BTC" else max(
                        tick, math.floor(entry*150/80000/tick+0.5)*tick)
                    distance = 50. if asset == "BTC" else max(
                        tick, math.floor(entry*50/80000/tick+0.5)*tick)
                    position = dict(side=side, entry=entry, entry_j=j, qty=qty,
                                    margin=margin, stop=stop, atr_stop=atr_stop,
                                    liq=liq, preliq=preliq,
                                    bankruptcy=entry-side*margin/qty,
                                    activation=activation, distance=distance,
                                    best=entry, active=False, initial_stop=stop)
                    just_opened = True
                    mark_exit, reason = trigger_old_stop(
                        side, mo[j], mh[j], ml[j], stop, liq, False)

        if position is not None and reason is not None:
            p = position
            side = p["side"]
            if reason == "supertrend_flip":
                # Action only after completed bar; next minute traded-open.
                fill = op[j]-side*slip
                mark_trigger = None
            else:
                # Idealized mark-trigger fill, NOT actual traded bid/ask.
                # For an adverse minute-open gap use observed MARK open.
                # One-tick adverse execution fill perturbation is scenario.
                fill = float(mark_exit)-side*slip
                mark_trigger = float(mark_exit)
            is_liq = reason in ("liq_gap_proxy", "liquidation_proxy")
            if is_liq:
                fill = max(0., fill)
            hold = (j-p["entry_j"])
            entry_fee = p["entry"]*p["qty"]*FEE
            waived = bool(offer and hold <= 30 and not is_liq)
            exit_fee = 0. if waived or is_liq else fill*p["qty"]*FEE
            liq_fee = fill*p["qty"]*LIQ_PENALTY if is_liq else 0.
            gross = (fill-p["entry"])*side*p["qty"]
            if is_liq:
                # Isolated notional loss cannot debit more than initial margin,
                # separate wallet entry fee still debited. Exact venue mark
                # liquidation fills/insurance treatment are unavailable.
                net = max(-p["margin"],gross-liq_fee*(1+GST))-entry_fee*(1+GST)
            else:
                net = gross-(entry_fee+exit_fee)*(1+GST)
            before = equity
            equity = max(0., equity+net)
            peak = max(peak,equity)
            dd_max = max(dd_max,100*(1-equity/peak))
            trades.append(dict(
                asset=asset, entry_utc=str(idx[p["entry_j"]]),
                exit_utc=str(idx[j]),side="long" if side==1 else "short",
                entry_traded_proxy=p["entry"], exit_price_proxy=fill,
                mark_stop_trigger=mark_trigger, qty=p["qty"],
                minutes_held=hold, reason=reason, sampled_mode=sampling,
                stop_at_exit=p["stop"], initial_stop=p["initial_stop"],
                modeled_liq=p["liq"], modeled_preliq=p["preliq"],
                gross_usd=gross, net_usd=equity-before,
                entry_fee_usd=entry_fee,exit_fee_usd=exit_fee,
                liquidation_fee_usd=liq_fee,gst_usd=GST*(entry_fee+exit_fee+liq_fee),
                equity_before=before, equity_after=equity,
                scalper_waiver_hypothesis=waived,
            ))
            position = None

        if position is not None:
            p = position
            side = p["side"]
            # Whether a low and a favorable activation high BOTH occurred this
            # minute cannot be ordered. We never assume favorable high first.
            if sampling == "extreme":
                favorable = mh[j] if side == 1 else ml[j]
                adverse = ml[j] if side == 1 else mh[j]
                if (side*(favorable-p["entry"])>=p["activation"]
                    and (side==1 and adverse<=p["stop"] or
                         side==-1 and adverse>=p["stop"])):
                    ambiguous += 1

            # This sample is available only AFTER the mark minute is complete,
            # so the next stop update becomes effective in minute j+1.
            observed = mc[j] if sampling == "close" else (
                mh[j] if side == 1 else ml[j])
            if (observed-p["entry"])*side >= p["activation"]:
                p["active"] = True
            if p["active"]:
                p["best"] = max(p["best"],observed) if side == 1 else min(p["best"],observed)
                candidate = p["best"]-side*p["distance"]
                # Match native stop tick rounding.
                candidate = (math.ceil(candidate/tick-1e-9)*tick if side==1
                             else math.floor(candidate/tick+1e-9)*tick)
                p["stop"] = max(p["stop"],candidate) if side == 1 else min(p["stop"],candidate)
    t = pd.DataFrame(trades)
    if len(t):
        t["month_ist"] = pd.to_datetime(t.exit_utc,utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    groups = {m:g for m,g in t.groupby("month_ist")} if len(t) else {}
    months = []
    cash = EQUITY
    for per in pd.period_range("2025-01",str(idx[-1].tz_convert("Asia/Kolkata").to_period("M")),freq="M"):
        month = str(per)
        group = groups.get(month)
        after = cash if group is None else float(group.equity_after.iloc[-1])
        months.append(dict(month_ist=month, starting_usd=round(cash,4),
                           pnl_usd=round(after-cash,4),
                           ending_usd=round(after,4),
                           trades=0 if group is None else len(group),
                           is_complete_month=month<"2026-11"))
        cash = after
    m = pd.DataFrame(months)
    full = m[m.is_complete_month]
    profits = float(t.loc[t.net_usd>0,"net_usd"].sum()) if len(t) else 0.
    losses = -float(t.loc[t.net_usd<0,"net_usd"].sum()) if len(t) else 0.
    summary = {
        "asset":asset, "sample":sampling, "scalper_waiver_hypothesis":bool(offer),
        "slippage_tick":slip,"net_usd":round(equity-EQUITY,4),
        "ending_usd":round(equity,4),"trades":len(t),
        "win_rate_pct":round(100*(t.net_usd>0).mean(),2) if len(t) else None,
        "net_profit_factor":round(profits/losses,4) if losses>0 else None,
        "modeled_liquidation_count":int(t.reason.isin(["liq_gap_proxy","liquidation_proxy"]).sum()) if len(t) else 0,
        "max_closed_equity_drawdown_pct":round(dd_max,2),
        "full_months":len(full),"profitable_months":int((full.pnl_usd>0).sum()),
        "losing_months":int((full.pnl_usd<0).sum()),
        "flat_months":int((full.pnl_usd==0).sum()),
        "signals_when_flat":n_signal,
        "skipped_wallet":n_wallet,"skipped_contract":n_lot,
        "ambiguous_mark_minutes_not_optimistically_ordered":ambiguous,
        "entry_fee_sum":round(float(t.entry_fee_usd.sum()),3) if len(t) else 0.,
        "exit_fee_sum":round(float(t.exit_fee_usd.sum()),3) if len(t) else 0.,
        "liquidation_fee_sum":round(float(t.liquidation_fee_usd.sum()),3) if len(t) else 0.,
        "gst_sum":round(float(t.gst_usd.sum()),3) if len(t) else 0.,
        "position_open_at_data_end":position is not None,
        "last_execution_minute_utc":str(idx[-1]),
    }
    if position is not None:
        p = position
        last_price = float(minute.close.iloc[-1])
        open_gross = (last_price-p['entry'])*p['side']*p['qty']
        estimated_close_fee = last_price*p['qty']*FEE
        estimated_entry_fee = p['entry']*p['qty']*FEE
        summary['open_at_end'] = {
            'entry_time_utc': str(idx[p['entry_j']]),
            'entry_price': p['entry'],
            'side': 'long' if p['side'] == 1 else 'short',
            'quantity': p['qty'],
            'last_trade_close': last_price,
            'last_mark_close': float(mark['close'].iloc[-1]),
            'current_stop': p['stop'],
            'gross_unrealized_usd': round(open_gross,4),
            'hypothetical_net_if_closed_usd': round(open_gross-(estimated_entry_fee+estimated_close_fee)*(1+GST),4),
            'note': 'Hypothetical closing value only; this trade remains OPEN at IST day end',
        }
    else:
        summary['open_at_end'] = None
    return t,m,summary


def unit_test():
    # Mark stop fires on low even if high is large: never assume high first.
    assert trigger_old_stop(1,100.,200.,89.,90.,85.,False)==(90.,"native_stop_touch")
    assert trigger_old_stop(1,80.,200.,79.,90.,85.,False)==(80.,"liq_gap_proxy")
    assert trigger_old_stop(-1,100.,111.,80.,110.,115.,False)==(110.,"native_stop_touch")
    assert trigger_old_stop(1,100.,110.,99.,90.,85.,True)==(None,"supertrend_flip")
    # Current minute protection wins over the pending flip at a gap.
    assert trigger_old_stop(-1,120.,121.,100.,110.,115.,True)==(120.,"liq_gap_proxy")
    # No assumptions that a mark high could have been sampled by a 3s poll.


def main():
    unit_test()
    output={"method":NOTES,"datasets":{},"results":{}}
    for asset in ("BTC","ETH"):
        minute, bars, trade_manifest = load(asset)
        tm = minute["time"].to_numpy(dtype="int64")
        mark, overlap, info = load_mark(asset,tm)
        if len(overlap)!=len(tm):
            # Archive overlap may end 1-2 days earlier than traded series.
            assert len(overlap)%15==0, "Expected complete 15m buckets"
            minute = minute.iloc[:len(overlap)].copy()
            bars = bars.iloc[:len(overlap)//15].copy()
        assert (minute.time.to_numpy(dtype="int64")==overlap).all()
        assert len(mark)==len(minute)
        output["datasets"][asset]=dict(
            trade_minutes=len(minute), mark_minutes=len(mark), mark_history=info,
            signal_bars_15m=len(bars),first_utc=str(minute.index[0]),
            last_utc=str(minute.index[-1]))
        for sample in ("close","extreme"):
            for offer in (False,True):
                for slip in (0.,.5 if asset=="BTC" else .05):
                    # Include all configurations to measure price-sampling
                    # effect, fee waiver, and a one-tick execution sensitivity.
                    name=f'{asset.lower()}_{sample}_{"offer" if offer else "nooffer"}_{"onetick" if slip else "noslip"}'
                    trades,monthly,report = evaluate(
                        asset,minute,mark,bars,sample,offer,slip)
                    trades.to_csv(OUT/f"{name}_trades.csv.gz",index=False,compression="gzip")
                    monthly.to_csv(OUT/f"{name}_monthly.csv",index=False)
                    output["results"][name]=report
                    print("DEMO_MARK_RESULT",name,json.dumps(report),flush=True)
    (OUT/"summary.json").write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8")
    print("DEMO_LIKE_MARK_REPLAY_COMPLETE",OUT,flush=True)


if __name__=="__main__":
    main()
