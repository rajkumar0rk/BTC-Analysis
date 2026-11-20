#!/usr/bin/env python3
"""Reproduce ETHUSD EMA20/Supertrend 1h settings adapted from user's BTC screenshot (screenshots 2026-11-20).

Reference: Delta_ETHUSD_Supertrend_ATR_Volume_Min_Max_Filters_Scalper.pine
(Pine v6, "ETHUSD EMA / ST | ATR & Volume Min Max + Net").

This is an independent OHLC broker-emulator approximation, NOT a TradingView
strategy-test export or a replay of actual order-book fills. Native
strategy.exit(loss, trail_points, trail_offset) is emulated using TV's
inferred open-high-low-close / open-low-high-close OHLC path. No future
indicators, intrabar clairvoyance, undocumented funding, or 2026-Nov partial
month. Dataset is raw ETHUSD Delta India 1m 2025-Jan to 2026-Oct, SHA-verified.
"""
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path("data/delta_india/ETHUSD/1m")
OUT=Path("analysis/eth_tv_ema_st_1h_27min_20261120")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
QTY_ETH=0.01             # Delta ETHUSD one contract = 0.01 ETH (official Delta contract detail)
EMA_LEN=20
ST_ATR_LEN=10
ST_FACTOR=3.0
SL_ATR_LEN=14
SL_ATR_MULT=2.0
TRAIL_ACTIVATION=100.0
TRAIL_DISTANCE=50.0
TICK=0.05               # ETHUSD price tick assumption; verify at execution time
TAKER_FEE=.0005
GST_RATE=.18
SCREENSHOT_SCALP_MIN=27
REALISTIC_SCALP_MIN=100_000
ENTRY_SLIP_POINTS=0.0   # screenshot assumption: no fill-price slippage
EXIT_SLIP_POINTS=0.0
RAW_REFERENCE="Delta_ETHUSD_Supertrend_ATR_Volume_Min_Max_Filters_Scalper.pine"

def source():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    months=set(MONTHS)
    files=[x for x in manifest["partitions"] if x["file"].replace(".csv.gz","") in months]
    assert len(files)==22, "Need exactly 22 completed months of ETH 1m candles"
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

def segment_exit(a,z,entry,side,initial,trail,best,activation_points,distance_points):
    """Process one monotonic segment in TradingView inferred path."""
    current_stop=(max(initial,trail) if side==1 else min(initial,trail)) if trail is not None else initial
    if (side==1 and a<=current_stop) or (side==-1 and a>=current_stop):
        return a,trail,best,"stop_gap"
    favorable=(z>a if side==1 else z<a)
    if favorable:
        best=max(best,z) if side==1 else min(best,z)
        gain=(best-entry)*side
        if gain>=activation_points:
            candidate=best-side*distance_points
            trail=(max(trail,candidate) if side==1 else min(trail,candidate)) if trail is not None else candidate
        return None,trail,best,None
    crossed=(z<=current_stop if side==1 else z>=current_stop)
    if crossed:
        return current_stop,trail,best,"native_loss_or_trail"
    return None,trail,best,None

def replay(b, direction, atr14, long, short, percentage_scaled=False):
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
                    pos["initial"],pos["trail"],pos["best"],
                    pos["activation_points"],pos["distance_points"])
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
            # The main test keeps screenshot values 100/50 ETH price points unchanged.
            # Optional sensitivity scales BTC-equivalent percentages:
            # 100/80000=0.125% activation, 50/80000=0.0625% distance.
            # ETH points are rounded to the estimated 0.05 quote tick.
            activation=(max(TICK,round_ticks(cl[i]*TRAIL_ACTIVATION/80000)*TICK)
                        if percentage_scaled else TRAIL_ACTIVATION)
            trail_distance=(max(TICK,round_ticks(cl[i]*TRAIL_DISTANCE/80000)*TICK)
                            if percentage_scaled else TRAIL_DISTANCE)
            pos=dict(side=side,entry=cl[i],entry_ns=int(ns[i]),
                     atr14=atr14[i],initial=cl[i]-side*distance,
                     trail=None,best=cl[i],activation_points=activation,
                     distance_points=trail_distance)
    if pos is not None:
        # Do not fabricate a close at 2026-11-01; retain open trade.
        open_pos=dict(entry_utc=pd.Timestamp(pos["entry_ns"],unit="ns",tz="UTC").isoformat(),
                      side=pos["side"],entry=pos["entry"])
    else:open_pos=None
    tr=pd.DataFrame(records)
    return tr,signals,open_pos

def costs(tr,scalp_window,slippage_points=0.0,optimistic_first_hour=False):
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
    if optimistic_first_hour:
        # For any intrabar stop on the first hour, exit timestamp is only
        # constrained to somewhere inside that 60-minute candle.
        # An exit within 27 minutes is POSSIBLE but not confirmed.
        # Treat every such ambiguous exit as qualifying to get an upper
        # bound on 27m-fee-waiver profitability without inventing timestamps.
        early_possible=np.isclose(held,60.0)&(z.exit_reason.to_numpy()!="supertrend_flip_close")
        eligible=eligible|early_possible
    entry_fee=ep*QTY_ETH*TAKER_FEE
    exit_fee=np.where(eligible,0.0,xp*QTY_ETH*TAKER_FEE)
    fee=entry_fee+exit_fee
    gst=fee*GST_RATE
    z["scalper_eligible"]=eligible
    z["net_points"]=pts-(fee+gst)/QTY_ETH
    z["net_usd"]=pts*QTY_ETH-fee-gst
    z["gross_usd"]=pts*QTY_ETH
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

def calculate_scenarios(b,direction,atr14,long,short,scaled):
    trades,signals,open_position=replay(b,direction,atr14,long,short,percentage_scaled=scaled)
    assert len(trades)>0,"No trades - investigate implementation"
    assert trades.exit_ns.is_monotonic_increasing
    assert (trades.holding_minutes>=60).all(),"Invalid ETH 1h holding time"
    assert not trades.duplicated(["entry_ns","direction"]).any()
    scenarios={}
    monthlies={}
    z=costs(trades,SCREENSHOT_SCALP_MIN)
    optimistic=costs(trades,SCREENSHOT_SCALP_MIN,optimistic_first_hour=True)
    stressed=costs(trades,SCREENSHOT_SCALP_MIN,slippage_points=0.5)
    unlimited=costs(trades,REALISTIC_SCALP_MIN)
    for key,model in [
        ("27min_conservative_zero_slippage",z),
        ("27min_optimistic_fee_waiver_upper_bound",optimistic),
        ("27min_conservative_plus_0p5_point_slippage_per_fill",stressed),
        ("hypothetical_unlimited_exit_fee_waiver",unlimited)
    ]:
        mon=month_results(model)
        monthlies[key]=mon
        scenarios[key]=metrics(model,mon)
        mon.to_csv(OUT/f"monthly_{'pct_scaled' if scaled else 'fixed_100_50'}_{key}.csv",index=False)
    trades.to_csv(OUT/f"trades_{'pct_scaled' if scaled else 'fixed_100_50'}.csv.gz",
                  index=False,compression="gzip")
    return dict(
        trailing_mode="eth_percentage_scaled_100_over_80000_50_over_80000"
          if scaled else "fixed_100_point_activation_50_point_trail",
        signals_on_completed_bars=signals,
        last_open_trade_at_cutoff=open_position,
        scenarios=scenarios),monthlies

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    bars,quality=source()
    direction,atr14,long,short=features(bars)
    fixed,mon_fixed=calculate_scenarios(bars,direction,atr14,long,short,scaled=False)
    scaled,mon_scaled=calculate_scenarios(bars,direction,atr14,long,short,scaled=True)

    result={
      "status":"completed_approximate_tradingview_native_trail",
      "instrument":"ETHUSD",
      "one_contract_eth":QTY_ETH,
      "source":quality,
      "screenshot_settings":dict(
          entry_timeframe="1h",stop_timeframe="1h",supertrend_atr=10,
          supertrend_factor=3,ema_length=20,entry_pullback="EMA20",
          require_st_touch_candle_shape=False,require_st_wick_only=False,
          stop_loss="ATR14 x2",master_trailing_enabled=True,
          trailing_distance_enabled=True,activation_price_points=100,
          distance_price_points=50,additional_trailing_stop_enabled=False,
          master_volume_volatility_filter="Off",
          take_fee_pct_each_side=0.05,gst_pct=18,
          scalper_offer_assumed_on_entire_history=True,
          qualifying_window_minutes=27,funding_rate_pct=0,
          initial_slippage_points=0,one_eth_contract=QTY_ETH,
          reference_price_tick_assumption=TICK),
      "fixed_100_50":fixed,
      "eth_scaled_trailing":scaled,
      "caveats":[
         "One ETHUSD contract is modeled as 0.01 ETH; unlike BTCUSD one contract, dollar notional is not equal.",
         "Core 100-point activation/50-point trailing setting is unchanged for main test; optional comparison uses ETH entry*100/80000 and ETH entry*50/80000.",
         "27-minute exit-fee waiver is assumed on historical ETH trades but actual ETH eligibility must be verified with exchange; do not treat as granted.",
         "1h OHLC bar replay only; conservative fee model assumes no 27-minute eligible intrabar exits. Optimistic upper bound assumes all first-hour intrabar stops qualify. Neither supplies exact timestamps.",
         "This is a reconstructed TradingView broker-emulator approximation, not a broker trade-history replay.",
         "No order book spread, funding charges, mark-price liquidation, variable leverage, margin restrictions, or live slippage. 0.5 price points adversely on each fill is an optional stress case.",
         "Only 22 fully completed UTC calendar months Jan 2025 through Oct 2026 are included; no November partial month.",
         "Profit factor is computed after modeled fees and GST. Net USD is for fixed 0.01 ETH contract, with no reinvestment or account sizing.",
         "OHLC path inference can differ from real 1-minute prices and TradingView's strategy engine."]}

    (OUT/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    report=["# ETHUSD EMA20/Supertrend 1h — screenshot settings (27m Scalper Offer model)",
            "",
            f"Source: {quality['raw_1m_rows']:,} SHA256-verified Delta India ETHUSD one-minute candles; {quality['complete_1h_rows']:,} 1h bars, 22 UTC months.",
            "Main test: ATR10 Supertrend3, EMA20 pullback, ATR14x2 stop, original 100/50 ETH price-point trailing, master entry filter Off.",
            "ETH normalized sensitivity: 0.125% price activation; 0.0625% price trailing distance, rounded to 0.05.",
            "Size: 1 ETHUSD lot = 0.01 ETH; 0.05% taker entry and exit, 18% GST, 27m offer modeled, funding=0, slippage=0 main.",
            "",
            "| Configuration / fee model | Trades | Net USD | Win rate | Profit factor | Positive months | Offer-eligible modeled |",
            "|---|---:|---:|---:|---:|---:|---:|"]
    for label,r in [("Original fixed ETH 100/50",fixed),("ETH percentage-scaled comparison",scaled)]:
        for key,d in r["scenarios"].items():
            report.append(f"| {label}; {key} | {d['trades']} | {d['net_profit_usd']:+.2f} | {d['win_rate_pct']:.2f}% | {d['profit_factor']} | {d['profitable_months']}/22 | {d['scalp_eligible']} |")
    report+=["","## 22-month primary fixed 100/50 (27-minute conservative)","",
             mon_fixed["27min_conservative_zero_slippage"].to_markdown(index=False),
             "", "## 22-month ETH percentage-scaled sensitivity (27-minute conservative)","",
             mon_scaled["27min_conservative_zero_slippage"].to_markdown(index=False),
             "","## Caveats",""]
    report+=["- "+c for c in result["caveats"]]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("BACKTEST_SUMMARY_JSON "+json.dumps({
        "source":quality,
        "fixed_100_50":fixed,
        "eth_scaled_trailing":scaled},separators=(",",":"),default=str),flush=True)

if __name__=="__main__":
    main()
