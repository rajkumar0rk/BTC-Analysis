#!/usr/bin/env python3
"""Reproduce BTCUSD EMA20/Supertrend TradingView 1h configuration (screenshots 2026-11-20).

Reference: Delta_BTCUSD_Supertrend_ATR_Volume_Min_Max_Filters_Scalper.pine
(Pine v6, "BTCUSD EMA / ST | ATR & Volume Min Max + Net").

This is an independent OHLC broker-emulator approximation, NOT a TradingView
strategy-test export or a replay of actual order-book fills. Native
strategy.exit(loss, trail_points, trail_offset) is emulated using TV's
inferred open-high-low-close / open-low-high-close OHLC path. No future
indicators, intrabar clairvoyance, undocumented funding, or 2026-Nov partial
month. Dataset is raw Delta India 1m 2025-Jan to 2026-Oct, SHA-verified.
"""
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/btc_tv_ema_st_1h_27min_20261120")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
QTY_BTC=0.001             # 1 TV contract from screenshot
EMA_LEN=20
ST_ATR_LEN=10
ST_FACTOR=3.0
SL_ATR_LEN=14
SL_ATR_MULT=2.0
TRAIL_ACTIVATION=100.0
TRAIL_DISTANCE=50.0
TICK=0.5                # assumed BTCUSD TV/venue price tick
TAKER_FEE=.0005
GST_RATE=.18
SCREENSHOT_SCALP_MIN=27
REALISTIC_SCALP_MIN=100_000
ENTRY_SLIP_POINTS=0.0   # screenshot assumption: no fill-price slippage
EXIT_SLIP_POINTS=0.0
RAW_REFERENCE="Delta_BTCUSD_Supertrend_ATR_Volume_Min_Max_Filters_Scalper.pine"

def source():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    months=set(MONTHS)
    files=[x for x in manifest["partitions"] if x["file"].replace(".csv.gz","") in months]
    assert len(files)==22, "Need exactly 22 completed months of BTC 1m candles"
    frames=[]
    for part in files:
        path=ROOT/part["file"]
        raw=path.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==part["sha256_gzip"],path
        assert part["missing_minutes"]==0,(path,"Missing source minute")
        f=pd.read_csv(path,compression="gzip",usecols=["time","open","high","low","close","volume"])
        assert len(f)==part["observed_candles"],path
        frames.append(f)
    df=pd.concat(frames,ignore_index=True).sort_values("time").reset_index(drop=True)
    seconds=df.time.to_numpy(np.int64)
    assert np.all(np.diff(seconds)==60),"Source minute gap or duplicate"
    assert len(df)==sum(z["observed_candles"] for z in files)
    assert not ((df.low>df.high)|(df.low>df.open)|(df.low>df.close)|
                (df.high<df.open)|(df.high<df.close)|(df.low<=0)).any()
    df.index=pd.to_datetime(df.time,unit="s",utc=True)
    bars=df.resample("1h",label="right",closed="left").agg({
        "open":"first","high":"max","low":"min","close":"last","volume":"sum",
        "time":"count"})
    assert len(bars)==len(df)//60
    assert (bars.time==60).all(),"Incomplete 1h candle"
    assert bars.index[0]==pd.Timestamp("2025-01-01T01:00:00Z")
    assert bars.index[-1]==pd.Timestamp("2026-11-01T00:00:00Z")
    return bars,dict(
        source_url=manifest["source"],raw_1m_rows=len(df),complete_1h_rows=len(bars),
        source_partitions=len(files),sha256_verified=True,missing_1m_candles=0,
        first_utc="2025-01-01T00:00:00Z",last_utc="2026-10-31T23:59:00Z",
        scored_months_utc=MONTHS)

def rma_tr(h,l,c,n):
    tr=np.maximum(h-l,np.maximum(np.abs(h-np.r_[c[0],c[:-1]]),
                                 np.abs(l-np.r_[c[0],c[:-1]])))
    z=np.full(len(h),np.nan,dtype=float)
    if len(h)>=n:
        z[n-1]=np.mean(tr[:n])
        for i in range(n,len(h)):
            z[i]=(z[i-1]*(n-1)+tr[i])/n
    return z

def tv_supertrend(h,l,c,atr,fac):
    length=len(c)
    upper=np.full(length,np.nan)
    lower=np.full(length,np.nan)
    direct=np.ones(length,dtype=np.int8)  # TV ta.supertrend 1=bear, -1=bull
    line=np.full(length,np.nan)
    for i in range(length):
        if not np.isfinite(atr[i]):continue
        basic_upper=(h[i]+l[i])/2+fac*atr[i]
        basic_lower=(h[i]+l[i])/2-fac*atr[i]
        if i==0 or not np.isfinite(atr[i-1]):
            upper[i],lower[i]=basic_upper,basic_lower
            direct[i]=1
        else:
            prior_up=upper[i-1]
            prior_lo=lower[i-1]
            upper[i]=(basic_upper if basic_upper<prior_up or c[i-1]>prior_up else prior_up)
            lower[i]=(basic_lower if basic_lower>prior_lo or c[i-1]<prior_lo else prior_lo)
            if direct[i-1]==1:
                direct[i]=-1 if c[i]>upper[i] else 1
            else:
                direct[i]=1 if c[i]<lower[i] else -1
        line[i]=lower[i] if direct[i]==-1 else upper[i]
    return line,direct

def round_ticks(x):
    # Pine math.round ties away from zero; stop uses +ATR positive.
    return max(1,math.floor(x/TICK+0.5))

def features(b):
    h=b.high.to_numpy(float);l=b.low.to_numpy(float);c=b.close.to_numpy(float)
    atr10=rma_tr(h,l,c,ST_ATR_LEN)
    atr14=rma_tr(h,l,c,SL_ATR_LEN)
    _,direction=tv_supertrend(h,l,c,atr10,ST_FACTOR)
    ema=pd.Series(c).ewm(span=EMA_LEN,adjust=False).mean().to_numpy()
    ok=np.isfinite(atr14)
    long=np.zeros(len(b),dtype=bool)
    short=np.zeros(len(b),dtype=bool)
    # All screenshots: EMA20 pullback, no ST-touch shape gate; min/max
    # volatility and volume toggles NOT USED because master filter=Off.
    for i in range(1,len(b)):
        if not ok[i]:continue
        long[i]=(direction[i]==-1 and direction[i-1]==-1
                 and l[i]<=ema[i] and c[i]>ema[i])
        short[i]=(direction[i]==1 and direction[i-1]==1
                  and h[i]>=ema[i] and c[i]<ema[i])
    return direction,atr14,long,short

def segment_exit(a,z,entry,side,initial,trail,best):
    """Process one monotonic segment in TradingView inferred path."""
    current_stop=(max(initial,trail) if side==1 else min(initial,trail)) if trail is not None else initial
    if (side==1 and a<=current_stop) or (side==-1 and a>=current_stop):
        return a,trail,best,"stop_gap"
    favorable=(z>a if side==1 else z<a)
    if favorable:
        best=max(best,z) if side==1 else min(best,z)
        gain=(best-entry)*side
        if gain>=TRAIL_ACTIVATION:
            candidate=best-side*TRAIL_DISTANCE
            trail=(max(trail,candidate) if side==1 else min(trail,candidate)) if trail is not None else candidate
        return None,trail,best,None
    crossed=(z<=current_stop if side==1 else z>=current_stop)
    if crossed:
        return current_stop,trail,best,"native_loss_or_trail"
    return None,trail,best,None

def replay(b, direction, atr14, long, short):
    op=b.open.to_numpy(float)
    hi=b.high.to_numpy(float)
    lo=b.low.to_numpy(float)
    cl=b.close.to_numpy(float)
    # Pandas 3 may store tz-aware DatetimeIndex with microsecond resolution.
    # Normalize explicitly to nanoseconds before timestamp arithmetic.
    ns=np.array(b.index.as_unit('ns').asi8,np.int64)
    assert ns[0]>=1_735_000_000_000_000_000, 'Timestamp unit mismatch'
    records=[]
    pos=None
    signals={"long":int(long.sum()),"short":int(short.sum())}
    def close_pos(i,fill,reason,bar_exit_time_ns):
        nonlocal pos
        p=pos
        gross=(fill-p["entry"])*p["side"]
        hold=(bar_exit_time_ns-p["entry_ns"])/60_000_000_000
        records.append(dict(entry_ns=p["entry_ns"],exit_ns=int(bar_exit_time_ns),
            entry_utc=pd.Timestamp(p["entry_ns"],unit="ns",tz="UTC").isoformat(),
            exit_utc=pd.Timestamp(bar_exit_time_ns,unit="ns",tz="UTC").isoformat(),
            direction="LONG" if p["side"]==1 else "SHORT",
            entry_price=p["entry"],exit_price=fill,
            gross_points=gross,exit_reason=reason,
            holding_minutes=hold,initial_sl=p["initial"],
            initial_atr14=p["atr14"]))
        pos=None
    for i in range(len(b)):
        if pos is not None:
            # TradingView historical OHLC broker emulator: if open is
            # closer to HIGH, high is visited before low; else low before high.
            if abs(op[i]-hi[i])<abs(op[i]-lo[i]):
                path=(op[i],hi[i],lo[i],cl[i])
            else:
                path=(op[i],lo[i],hi[i],cl[i])
            for j in range(1,4):
                fill,pos["trail"],pos["best"],reason=segment_exit(
                    path[j-1],path[j],pos["entry"],pos["side"],
                    pos["initial"],pos["trail"],pos["best"])
                if fill is not None:
                    # Bar-level intrabar timestamps unavailable; record this
                    # bar's close as holding-time upper bound, conservatively.
                    close_pos(i,fill,reason,ns[i])
                    break
        if pos is not None and i>0:
            bearish_flip=(direction[i]==1 and direction[i-1]==-1)
            bullish_flip=(direction[i]==-1 and direction[i-1]==1)
            if (pos["side"]==1 and bearish_flip) or (pos["side"]==-1 and bullish_flip):
                close_pos(i,cl[i],"supertrend_flip_close",ns[i])
        # Existing position at START of bar cannot re-enter the same bar even
        # if a stop was triggered inside. Pine pyramiding=0, orders on close.
        # Capture this using a separate entered/started flag below.
        if pos is None and i>0 and (long[i] or short[i]):
            # A bar that closed an earlier position is excluded below by
            # the replay's trade-overlap guard.
            if records and records[-1]["exit_ns"]==int(ns[i]):
                continue
            side=1 if long[i] else -1
            distance=round_ticks(atr14[i]*SL_ATR_MULT)*TICK
            pos=dict(side=side,entry=cl[i],entry_ns=int(ns[i]),
                     atr14=atr14[i],initial=cl[i]-side*distance,
                     trail=None,best=cl[i])
    if pos is not None:
        # Do not fabricate a close at 2026-11-01; retain open trade.
        open_pos=dict(entry_utc=pd.Timestamp(pos["entry_ns"],unit="ns",tz="UTC").isoformat(),
                      side=pos["side"],entry=pos["entry"])
    else:open_pos=None
    tr=pd.DataFrame(records)
    return tr,signals,open_pos

def costs(tr,scalp_window,slippage_points=0.0):
    z=tr.copy()
    if z.empty:return z
    dirs=np.where(z.direction=="LONG",1,-1)
    ep=z.entry_price.to_numpy(float)+dirs*slippage_points
    xp=z.exit_price.to_numpy(float)-dirs*slippage_points
    pts=(xp-ep)*dirs
    held=z.holding_minutes.to_numpy(float)
    # Source Pine: 100000 minute window & assumes the offer is active for
    # the entire history, not just after joined date.
    eligible=(held>=0)&(held<=scalp_window)
    entry_fee=ep*QTY_BTC*TAKER_FEE
    exit_fee=np.where(eligible,0.0,xp*QTY_BTC*TAKER_FEE)
    fee=entry_fee+exit_fee
    gst=fee*GST_RATE
    z["scalper_eligible"]=eligible
    z["net_points"]=pts-(fee+gst)/QTY_BTC
    z["net_usd"]=pts*QTY_BTC-fee-gst
    z["gross_usd"]=pts*QTY_BTC
    z["fee_usd"]=fee
    z["gst_usd"]=gst
    z["funding_usd"]=0.0
    z["month_utc"]=pd.to_datetime(z.exit_ns,unit="ns",utc=True).dt.strftime("%Y-%m")
    return z

def month_results(z):
    out=[]
    for m in MONTHS:
        g=z[z.month_utc==m]
        win=g[g.net_usd>0].net_usd.sum()
        loss=g[g.net_usd<0].net_usd.sum()
        out.append(dict(month_utc=m,trades=len(g),
                        net_wins=int((g.net_usd>0).sum()),
                        net_losses=int((g.net_usd<0).sum()),
                        gross_points=round(float(g.gross_points.sum()),4),
                        net_points=round(float(g.net_points.sum()),4),
                        net_usd=round(float(g.net_usd.sum()),4),
                        fees_usd=round(float(g.fee_usd.sum()),4),
                        gst_usd=round(float(g.gst_usd.sum()),4),
                        profit_factor=round(float(win/(-loss)),4) if loss<0 else None))
    return pd.DataFrame(out)

def metrics(z,mon):
    profits=z[z.net_usd>0].net_usd.sum()
    losses=z[z.net_usd<0].net_usd.sum()
    pnl=z.net_usd.to_numpy(float)
    eq=np.r_[0.,np.cumsum(pnl)]
    # Add a fixed, clearly illustrative $100 capital baseline to express DD;
    # 1 TV contract is fixed and funding/margin/liquidation not simulated.
    fixed_eq=100+eq
    high=np.maximum.accumulate(fixed_eq)
    max_dd=float(np.max(high-fixed_eq))
    return dict(trades=int(len(z)),win_rate_pct=round(100*float((z.net_usd>0).mean()),3),
        net_profit_usd=round(float(pnl.sum()),4),
        net_price_points=round(float(z.net_points.sum()),4),
        gross_price_points=round(float(z.gross_points.sum()),4),
        fee_usd=round(float(z.fee_usd.sum()),4),gst_usd=round(float(z.gst_usd.sum()),4),
        profit_factor=round(float(profits/(-losses)),4) if losses<0 else None,
        profitable_months=int((mon.net_usd>0).sum()),
        negative_months=int((mon.net_usd<0).sum()),
        max_peak_to_trough_drawdown_usd=round(max_dd,4),
        scalp_eligible=int(z.scalper_eligible.sum()),
        longest_holding_minutes=round(float(z.holding_minutes.max()),2) if len(z) else None)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    b,qual=source()
    direct,atr14,lg,sh=features(b)
    all_tr,signals,open_pos=replay(b,direct,atr14,lg,sh)
    assert len(all_tr)>0,"No trades found, verify engine"
    assert all_tr.exit_ns.is_monotonic_increasing
    assert (all_tr.holding_minutes>=15).all(), "Impossible sub-bar holding time; timestamp unit corrupted"
    assert all_tr.exit_utc.str.startswith(("2025-","2026-")).all(), "Invalid timestamp unit"
    assert all_tr.entry_utc.str.startswith(("2025-","2026-")).all(), "Invalid entry date"
    assert not all_tr.duplicated(["entry_ns","direction"]).any()
    # screenshot: full historical offer with a 27-minute qualifying window, no funding/slippage
    exact=costs(all_tr,SCREENSHOT_SCALP_MIN)
    realistic=costs(all_tr,REALISTIC_SCALP_MIN)
    # 0.5 USD price points adverse on each fill, with 27-minute window
    stressed=costs(all_tr,SCREENSHOT_SCALP_MIN,slippage_points=0.5)
    m=month_results(exact)
    mr=month_results(realistic)
    ms=month_results(stressed)
    # The reference script originally used calc_bars_count=10000.
    # Report a separate indicative recent 10k-bar window; calculate the
    # indicators using full preceding history to avoid cold-start bias.
    nrecent=10000
    recent_raw,recent_signals,recent_open=replay(
        b.iloc[-nrecent:],direct[-nrecent:],atr14[-nrecent:],
        lg[-nrecent:],sh[-nrecent:])
    assert not recent_raw.empty
    recent_exact=costs(recent_raw,SCREENSHOT_SCALP_MIN)
    recent_unlimited=costs(recent_raw,REALISTIC_SCALP_MIN)
    recent_m=month_results(recent_exact)
    recent_m30=month_results(recent_unlimited)
    exact.to_csv(OUT/"trades_screenshot_offer.csv.gz",index=False,compression="gzip")
    m.to_csv(OUT/"monthly_screenshot_offer.csv",index=False)
    mr.to_csv(OUT/"monthly_unlimited_offer.csv",index=False)
    ms.to_csv(OUT/"monthly_27min_offer_plus_0p5pt_slippage.csv",index=False)
    recent_m.to_csv(OUT/"recent_10000_bars_monthly_screenshot.csv",index=False)
    recent_m30.to_csv(OUT/"recent_10000_bars_monthly_unlimited.csv",index=False)
    result=dict(
      status="completed_approximate_tradingview_native_trail",
      source=qual,
      reference_pine_filename=RAW_REFERENCE,
      screenshot_settings=dict(entry_timeframe="1h",stop_timeframe="1h",
        supertrend_atr=10,supertrend_factor=3,ema_length=20,
        entry_pullback="EMA20",require_ST_touch_candle_shape=False,
        require_ST_wick_only_touch=False,initial_stop="ATR x Multiplier",
        atr_stop_length=14,atr_stop_mult=2,enable_trailing_stop=True,
        trailing_mode="Fixed Points (Original)",enable_trailing_distance=True,
        trailing_activation_price_points=100,trailing_distance_price_points=50,
        enable_independent_trailing_stop_points=False,trailing_stop_points_unused=100,
        entry_filter_mode="Off",volatility_min_toggle=True,volatility_min_ratio=1.0,
        volume_min_toggle=True,volume_min_ratio=1.5,
        note_filter="Filter Off: min/max switches DO NOT filter entries",
        maker_fee_pct=0.02,taker_fee_pct=0.05,entry_fill="Taker",
        exit_fill="Taker",gst_pct=18,btc_per_TV_contract=QTY_BTC,
        scalper_offer_enabled=True,scalper_offer_all_history=True,
        qualifying_window_minutes=SCREENSHOT_SCALP_MIN,
        funding_rate_per_8h_pct=0,estimate_fee_voucher=False),
      signals_on_completed_bars=signals,
      last_open_trade_at_cutoff=open_pos,
      recent_10000_1h_bars=dict(
        first_completed_bar=str(b.index[-nrecent]),
        last_completed_bar=str(b.index[-1]),
        counts=recent_signals,
        screenshot_offer=metrics(recent_exact,recent_m),
        window_unlimited_offer=metrics(recent_unlimited,recent_m30),
        note="First and last calendar months are partial in this rolling 10000-bar sample."),
      scenarios={
        "screenshot_27_min_offer_zero_slip":metrics(exact,m),
        "unlimited_100000_min_offer_zero_slip":metrics(realistic,mr),
        "screenshot_27_min_offer_0p5point_adverse_each_side":metrics(stressed,ms)},
      caveats=[
        "Independent reconstruction of the saved Pine v6 logic; NOT a TradingView tester export.",
        "OHLC inferred path approximates native TradingView strategy.exit trail; same-bar execution, rounding, and fills can differ from TV.",
        "Pine calc_bars_count=10000 may restrict accessible history on some TradingView charts; a separate recent 10000-bar window is included alongside full 22-month replay.",
        "Exact screenshot's 27-min qualifying window and all-history offer are assumptions, NOT verified Delta promotion terms.",
        "Entry and exit are TAKER per screenshot; exit fee waived only if offer eligible in model.",
        "No actual bid/ask spread, order-book impact, trading latency, realized slippage, or margin liquidation.",
        "Funding explicitly set to 0 from screenshot; this does not represent historical funding payments.",
        "One TradingView fixed contract=0.001 BTC; no leverage, margin, portfolio compounding or account sizing applied.",
        "Returns scored by UTC exit calendar month to provide 22 truly complete months Jan 2025-Oct 2026.",
        "Entry timestamp is signal candle close. Intrabar exits timestamped at bar close as conservative upper bound for fee-window eligibility.",
        "Uses assumed 0.5 BTCUSD price tick for rounded initial ATR stops."] )
    (OUT/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    report=["# BTCUSD EMA20 / Supertrend (1h) screenshot-parameter replay",
            "",f"Dataset: {qual['raw_1m_rows']:,} authenticated Delta India 1-minute candle rows, 22 months.",
            "Reference: saved Pine v6 BTCUSD EMA / ST | ATR & Volume Min Max + Net.",
            "", "**Screenshot cost assumption:** Taker 0.05% opening, closing waived for <=27 minutes, GST 18%, 0 funding, 0 slippage.",
            "**Other scenario:** a 100000-minute hypothetical qualifying window; third scenario applies $0.5 adverse price slippage on both sides with the 27-minute offer.",
            "", "| Scenario | Trades | Net USD (1x0.001 BTC) | PF | Positive months /22 |",
            "|---|---:|---:|---:|---:|"]
    for name,d in result["scenarios"].items():
        report.append(f"| {name} | {d['trades']} | {d['net_profit_usd']:+.2f} | {d['profit_factor']} | {d['profitable_months']}/22 |")
    report+=["","## Monthly screenshot (UTC, 1 TradingView contract)",
             "",m.to_markdown(index=False),"","## Reproducibility / limitations",""]
    report+=["- "+x for x in result["caveats"]]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("REPLAY_SUMMARY_JSON "+json.dumps({k:result[k] for k in
        ["status","source","scenarios","signals_on_completed_bars","recent_10000_1h_bars","last_open_trade_at_cutoff"]},
        separators=(",",":"),default=str),flush=True)
    print("SCREENSHOT_MONTHLY_CSV\n"+m.to_csv(index=False),flush=True)

if __name__=="__main__":
    main()
