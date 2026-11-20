#!/usr/bin/env python3
"""ETHUSD cross-asset screenshot replay: $100 portfolio, fixed <=$10 isolated margin, 100x.

Reuse identical 15m historical signal and trailing replay functions from
the preceding BTC-Analysis research branch. Fixed *margin*, NOT fixed notional:
a $10 margin budget at 100x gives <= $1000 ETHUSD notional, quantized down
to 0.01 ETH lots. Fee charges are in addition to this margin budget.

No extra capital is automatically allocated to the isolated position. On a
liquidation the isolated loss is capped at the margin posted, except for the
entry taker fee/GST paid separately by the portfolio wallet.

The underlying data are traded OHLC, NOT mark prices. OHLC-based liquidation
is an illustrative scenario, not an accurate historical liquidation replay.
"""
from pathlib import Path
import math
import json
import hashlib
import numpy as np
import pandas as pd
from replay_btc_ema_st_screenshot import indicators
from replay_btc_ema_st_100x import fee_net

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data/delta_india/ETHUSD/1m'
OUT=Path("analysis/eth_ema_st_fixed10_100x_20261120")
OUT.mkdir(parents=True, exist_ok=True)
STARTING_EQUITY_USD=100.0
PER_TRADE_MARGIN_BUDGET_USD=10.0
SELECTED_LEVERAGE=100
LOT_ETH=0.01
ETH_TICK=0.05
MAINTENANCE_FRACTION=0.0025
SCALPER_WINDOW_MINUTES=30
LIQUIDATION_BUFFER_FRACTION=0.0025
PARAMS={
  "instrument": "ETHUSD perpetual Delta India",
  "eth_per_contract": 0.01,
  "eth_tick_usd": 0.05,
  "entry_relative_trailing_activation_ratio": 150/80000,
  "entry_relative_trailing_distance_ratio": 50/80000,
  "btc_trailing_reference_price_usd": 80000,
  "point_conversion": "ETH follows percent-relative 150/50 BTC points at $80000 reference; not literal 150/50 ETH points",
  "portfolio_initial_equity_usd": STARTING_EQUITY_USD,
  "forward_stop_liquidation_buffer_fraction": LIQUIDATION_BUFFER_FRACTION,
  "entry_rejection_guard": "2ATR stop must be closer than estimated liquidation minus 0.25% extra buffer",
  "fixed_isolated_margin_budget_usd_per_trade": PER_TRADE_MARGIN_BUDGET_USD,
  "maximum_position_notional_usd": PER_TRADE_MARGIN_BUDGET_USD*SELECTED_LEVERAGE,
  "leverage":SELECTED_LEVERAGE,
  "lot_size_eth":LOT_ETH,
  "eth_usd_tick_size":0.05,
  "maintenance_margin_rate_assumed":MAINTENANCE_FRACTION,
  "scalper_fee_waiver_window_minutes_assumed":SCALPER_WINDOW_MINUTES,
  "taker_fee_pct_each_side":0.05,
  "gst_on_fees_pct":18,
  "liquidation_penalty_assumed_pct":0.05,
  "margin_mode":"isolated",
  "auto_add_margin":False,
  "auto_compound_margin":False,
  "wallet_pays_fee_outside_position_margin":True,
  "new_positions_when_wallet_cannot_cover_margin_and_entry_fee":"skip",
  "initial_stop":"ATR14 x 2",
  "trailing_activation_points":"ETH entry price * 150/80000, tick rounded",
  "trailing_distance_points":"ETH entry price * 50/80000, tick rounded",
  "signal_tf":"15m",
  "stop_monitoring_tf":"15m",
  "ohlc_path":"nearer extreme first, then farther extreme",
  "slippage_points":0,
  "funding_pct":0,
  "historical_offer_entitlement_verified":False,
  "historical_liquidation_mark_price_available":False,
}

def load_eth():
 m=json.loads((DATA/'manifest.json').read_text())
 assert m.get('symbol')=='ETHUSD' and m.get('resolution')=='1m'
 frames=[];n=0
 for p in m['partitions']:
  path=DATA/p['file']
  assert path.is_file(),path
  assert hashlib.sha256(path.read_bytes()).hexdigest()==p['sha256_gzip'],path
  assert p['missing_minutes']==0,(path,'missing minutes')
  x=pd.read_csv(path,compression='gzip')
  assert len(x)==p['observed_candles'],path
  assert {'time','open','high','low','close','volume'}.issubset(x.columns),x.columns
  frames.append(x[['time','open','high','low','close','volume']]);n+=len(x)
 df=pd.concat(frames,ignore_index=True)
 ts=df['time'].to_numpy(dtype=np.int64)
 assert np.all(np.diff(ts)==60),'1m history has gaps or duplicates'
 df['dt']=pd.to_datetime(df.time,unit='s',utc=True)
 df=df.set_index('dt')
 bars=df.resample('15min',origin='epoch',label='left',closed='left').agg(
   {'open':'first','high':'max','low':'min','close':'last','volume':'sum','time':'count'})
 assert np.all(bars.time.to_numpy()==15),'Incomplete 15m bars'
 return bars.drop(columns='time'),m,n

def eth_path_exit(o,h,l,c,side,ep,stop,best,active,liq_price):
    """Check stops vs margin barrier along assumed historical OHLC path."""
    activation_distance=max(ETH_TICK,round((ep*150/80000)/ETH_TICK)*ETH_TICK)
    distance=max(ETH_TICK,round((ep*50/80000)/ETH_TICK)*ETH_TICK)
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
            activation=ep+side*activation_distance
            if not active and ((side==1 and b>=activation) or (side==-1 and b<=activation)):
                active=True;best=activation
            if active:
                best=max(best,b) if side==1 else min(best,b)
                candidate=best-side*distance
                stop=max(stop,candidate) if side==1 else min(stop,candidate)
        else:
            protective=max(stop,liq_price) if side==1 else min(stop,liq_price)
            hit = (b<=protective) if side==1 else (b>=protective)
            if hit:
                isliq=(liq_price>=stop) if side==1 else (liq_price<=stop)
                return protective,stop,best,active,("liquidation" if isliq else "trailing" if active else "initial_stop")
    return None,stop,best,active,None

def replay(df,start,liq_fill,guarded=False,offer=True,external_entry_side=None):
    arr=df.reset_index()
    op=arr.open.to_numpy(dtype=float)
    hi=arr.high.to_numpy(dtype=float)
    lo=arr.low.to_numpy(dtype=float)
    cl=arr.close.to_numpy(dtype=float)
    ema=arr.ema.to_numpy(dtype=float)
    atr=arr.atr14.to_numpy(dtype=float)
    dr=arr.dir.to_numpy()
    ar=arr.atr_ratio.to_numpy(dtype=float)
    vr=arr.volume_ratio.to_numpy(dtype=float)
    times=arr.dt.to_numpy()
    if external_entry_side is not None and len(external_entry_side)!=len(arr):
        raise ValueError('External BTC signal count must match ETH bars')
    wallet=STARTING_EQUITY_USD
    peak=STARTING_EQUITY_USD
    max_dd_pct=0.0
    skip_margin=0
    skip_lot=0
    skip_guard=0
    max_notional=0.0
    min_notional=float("inf")
    liquidations=0
    position=None
    events=[]
    eligible_signals=0
    for i in range(max(start,36),len(arr)):
        if position is not None:
            s=position
            # Overnight opening gaps beyond estimated liquidation can bypass
            # stop-market orders; treat these as liquidations, not stop fills.
            if ((s["side"]==1 and op[i]<=s["liq_price"]) or
                (s["side"]==-1 and op[i]>=s["liq_price"])):
                xp=float(op[i])
                reason="liquidation"
            else:
                xp,s["sl"],s["best"],s["active"],reason=eth_path_exit(
                    op[i],hi[i],lo[i],cl[i],s["side"],s["entry_price"],
                    s["sl"],s["best"],s["active"],s["liq_price"])
            if xp is None and (
                (s["side"]==1 and dr[i]==1 and dr[i-1]==-1) or
                (s["side"]==-1 and dr[i]==-1 and dr[i-1]==1)
            ):
                xp=float(cl[i])
                reason="supertrend_flip"

            if xp is not None:
                if reason=="liquidation" and liq_fill=="bankruptcy":
                    xp=s["bankruptcy_price"]
                duration_minutes=(i-s["entry_idx"])*15
                fee=fee_net(s["qty_eth"],s["entry_price"],xp,s["side"],
                            duration_minutes if offer else 100000,reason,liq_fill)
                wallet_before=wallet
                if reason=="liquidation":
                    liquidations+=1
                    # Isolated position cannot absorb other wallet funds;
                    # margin at risk is initial posted IM (no auto top-up).
                    isolated_change=max(
                        -s["margin_usd"],
                        fee["gross_usd"]-fee["liquidation_fee_usd"]-fee["liquidation_gst_usd"])
                    net=isolated_change-fee["entry_fee_usd"]-fee["entry_gst_usd"]
                else:
                    isolated_change=fee["gross_usd"]-fee["exit_fee_usd"]-fee["exit_gst_usd"]
                    net=isolated_change-fee["entry_fee_usd"]-fee["entry_gst_usd"]
                wallet=max(0.,wallet+net)
                realized=wallet-wallet_before
                peak=max(peak,wallet)
                max_dd_pct=max(max_dd_pct,100*(1-wallet/peak))
                events.append(dict(
                    entry_utc=str(pd.Timestamp(times[s["entry_idx"]])+pd.Timedelta(minutes=15)),
                    exit_utc=str(pd.Timestamp(times[i])+pd.Timedelta(minutes=15)),
                    side="long" if s["side"]==1 else "short",
                    entry_price=s["entry_price"],exit_price=xp,
                    qty_eth=s["qty_eth"],contracts=s["contracts"],
                    entry_notional_usd=s["notional_usd"],
                    posted_margin_usd=s["margin_usd"],
                    liquidation_threshold_estimate=s["liq_price"],
                    stop_at_entry=s["initial_stop"],
                    exit_reason=reason,
                    hold_minutes=duration_minutes,
                    scalper_fee_waiver_applied=fee["eligible_scalper"],
                    portfolio_before_usd=wallet_before,
                    portfolio_after_usd=wallet,
                    change_usd=realized,
                    trade_pct_of_portfolio_before=100*realized/wallet_before if wallet_before else 0,
                    gross_price_pnl_usd=fee["gross_usd"],
                    isolated_position_change_usd=isolated_change,
                    entry_fee_usd=fee["entry_fee_usd"],
                    entry_gst_usd=fee["entry_gst_usd"],
                    exit_fee_usd=fee["exit_fee_usd"],
                    exit_gst_usd=fee["exit_gst_usd"],
                    liquidation_penalty_usd=fee["liquidation_fee_usd"],
                    liquidation_penalty_gst_usd=fee["liquidation_gst_usd"]))
                position=None

        if position is None and (np.isfinite(ema[i]) and np.isfinite(atr[i])
                               and np.isfinite(ar[i]) and np.isfinite(vr[i])):
            side=0
            if external_entry_side is not None:
                side=int(external_entry_side[i])
                if side not in (-1,0,1):
                    raise ValueError('Invalid external entry side')
            elif ar[i]>=1.0 and vr[i]>=1.5:
                if dr[i]==-1 and dr[i-1]==-1 and lo[i]<=ema[i] and cl[i]>ema[i]:
                    side=1
                elif dr[i]==1 and dr[i-1]==1 and hi[i]>=ema[i] and cl[i]<ema[i]:
                    side=-1
            if side:
                eligible_signals+=1
                ep=float(cl[i])
                slpts=max(ETH_TICK,round(2*atr[i]/ETH_TICK)*ETH_TICK)
                max_stop_distance=1/SELECTED_LEVERAGE-MAINTENANCE_FRACTION-LIQUIDATION_BUFFER_FRACTION
                if guarded and (max_stop_distance<=0 or slpts/ep>=max_stop_distance):
                    # Differential: guarded entries are blocked BEFORE creating a position.
                    skip_guard+=1
                    continue
                # Place <= $10 in margin, regardless of wallet balance or profit.
                # Fixed margin target, never downsized simply because wallet shrank.
                contracts=math.floor((PER_TRADE_MARGIN_BUDGET_USD*SELECTED_LEVERAGE)
                                     / (ep*LOT_ETH)+1e-10)
                if contracts<1:
                    skip_lot+=1
                    continue
                qty=contracts*LOT_ETH
                notional=ep*qty
                margin=notional/SELECTED_LEVERAGE
                entry_fee=notional*0.0005*(1+0.18)
                if wallet+1e-9<margin+entry_fee:
                    skip_margin+=1
                    continue
                liq=(ep-margin/qty)/(1-MAINTENANCE_FRACTION) if side==1 else (
                     ep+margin/qty)/(1+MAINTENANCE_FRACTION)
                bankruptcy=ep-side*margin/qty
                slpts=max(ETH_TICK,round(2*atr[i]/ETH_TICK)*ETH_TICK)
                max_notional=max(max_notional,notional)
                min_notional=min(min_notional,notional)
                position=dict(
                    side=side,entry_idx=i,entry_price=ep,qty_eth=qty,
                    contracts=contracts,notional_usd=notional,margin_usd=margin,
                    initial_stop=ep-side*slpts,sl=ep-side*slpts,
                    best=ep,active=False,liq_price=liq,
                    bankruptcy_price=bankruptcy)
    z=pd.DataFrame(events)
    if len(z):
        z["exit_month_ist"]=pd.to_datetime(z.exit_utc,utc=True).dt.tz_convert(
            "Asia/Kolkata").dt.strftime("%Y-%m")
    net=z.change_usd if len(z) else pd.Series(dtype=float)
    wins=float(net[net>0].sum())
    losses=-float(net[net<0].sum())
    first=str(pd.Timestamp(times[start]))
    stats=dict(
        start_utc=first,last_bar_utc=str(pd.Timestamp(times[-1])),
        starting_portfolio_usd=STARTING_EQUITY_USD,
        ending_portfolio_usd=round(wallet,4),
        net_profit_usd=round(wallet-STARTING_EQUITY_USD,4),
        total_return_pct=round(100*(wallet/STARTING_EQUITY_USD-1),2),
        completed_trades=len(z),wins=int((net>0).sum()),
        losses=int((net<0).sum()),
        win_rate_pct=round(float((net>0).mean()*100),2) if len(z) else None,
        net_profit_factor=round(wins/losses,4) if losses>0 else None,
        assumed_liquidations=liquidations,
        scalper_eligible_trades=int(z.scalper_fee_waiver_applied.sum()) if len(z) else 0,
        max_closed_equity_drawdown_pct=round(max_dd_pct,2),
        eligible_entry_signals=eligible_signals,
        skipped_entries_insufficient_wallet=skip_margin,
        skipped_entries_liquidation_buffer=skip_guard,
        skipped_entries_less_than_one_contract=skip_lot,
        largest_position_notional_usd=round(max_notional,2),
        smallest_position_notional_usd=round(min_notional,2) if min_notional<float("inf") else None,
        open_position_at_end=position is not None,
        fees_entry_usd=round(float(z.entry_fee_usd.sum()),3) if len(z) else 0,
        fees_exit_usd=round(float(z.exit_fee_usd.sum()),3) if len(z) else 0,
        gst_usd=round(float((z.entry_gst_usd+z.exit_gst_usd+z.liquidation_penalty_gst_usd).sum()),3) if len(z) else 0,
        liq_penalties_usd=round(float(z.liquidation_penalty_usd.sum()),3) if len(z) else 0,
        liquidation_fill=liq_fill,guarded=guarded,offer_active_assumed_full_history=offer)
    if len(z):
        assert abs(float(net.sum())-(wallet-STARTING_EQUITY_USD))<0.00001
    return z,stats

def monthly(z,first,last):
    previous=STARTING_EQUITY_USD
    month_groups={m:g for m,g in z.groupby("exit_month_ist",sort=True)} if len(z) else {}
    rows=[]
    for period in pd.period_range(first,last,freq="M"):
        key=str(period)
        g=month_groups.get(key)
        if g is None:
            end=previous
            trades=0
        else:
            end=float(g.portfolio_after_usd.iloc[-1])
            trades=len(g)
        profit=end-previous
        rows.append({
            "month_ist":key,
            "opening_balance_usd":round(previous,4),
            "net_profit_usd":round(profit,4),
            "monthly_return_pct":round(profit/previous*100,2) if previous>0 else None,
            "closing_balance_usd":round(end,4),
            "trades":trades,
            "winning_trades":int((g.change_usd>0).sum()) if trades else 0,
            "losing_trades":int((g.change_usd<0).sum()) if trades else 0,
            "liquidations":int((g.exit_reason=="liquidation").sum()) if trades else 0,
            "fees_and_gst_usd":round(float((
                 g.entry_fee_usd+g.entry_gst_usd+g.exit_fee_usd+g.exit_gst_usd+
                 g.liquidation_penalty_usd+g.liquidation_penalty_gst_usd).sum()),4) if trades else 0,
            "complete_month":(key<="2026-10" and (first!="2026-08" or key>="2026-09"))
        })
        previous=end
    return pd.DataFrame(rows)

def main():
    bars,manifest,count=load_eth()
    enriched=indicators(bars)
    output={"settings":PARAMS,"source":manifest["source"],
            "source_manifest_generated_utc":manifest["generated_at_utc"],
            "loaded_verified_one_minute_bars":count,"aggregated_15m_bars":len(bars),
            "disclaimer":"ETH 15m OHLC synthetic path and 0.25% maintenance proxy (not mark price). Historical offer entitlement unverified; no slippage, spread, funding. Same BTC entry with percentage-relative ETH trail, not literal BTC point settings."}
    for window,start in (("all_history",0),("recent_last_10000_15m",max(0,len(enriched)-10000))):
        for guarded in (False,True):
            for offer in (True,False):
                for fill in ("threshold","bankruptcy"):
                    key="_".join((window,"guarded" if guarded else "original",
                                  "offer" if offer else "nooffer",fill))
                    z,stats=replay(enriched,start,fill,guarded=guarded,offer=offer)
                    z.to_csv(OUT/f"{key}_trades.csv.gz",index=False,compression="gzip")
                    m=monthly(z,"2025-01" if start==0 else "2026-08","2026-11")
                    if start>0:
                        m.loc[m.month_ist=="2026-08","complete_month"]=False
                    m.to_csv(OUT/f"{key}_monthly.csv",index=False)
                    output[key]=stats
                    complete=m[m.complete_month]
                    output[key]["completed_months"]=len(complete)
                    output[key]["profitable_completed_months"]=int((complete.net_profit_usd>0).sum())
                    output[key]["losing_completed_months"]=int((complete.net_profit_usd<0).sum())
                    output[key]["flat_completed_months"]=int((complete.net_profit_usd==0).sum())
                    print("\n----",key,"----")
                    print(json.dumps(stats,indent=2))
                    print(m.to_string(index=False))
    (OUT/"summary.json").write_text(json.dumps(output,indent=2))
    print("ETH_100x_10margin_REPLAY_SUCCESS",OUT)

if __name__=="__main__":
    main()
