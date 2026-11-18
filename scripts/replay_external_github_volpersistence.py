#!/usr/bin/env python3
"""Paired replay of an external GitHub strategy on native Delta India BTCUSD/ETHUSD.

Source: https://github.com/anaysharma1717-svg/Volatility-Persistence-Trading-Strategy
Pinned upstream SHA: 4987ed61c4fc7f6fc738d88a6eb844b08190a838
Uses upstream ny_fix/common.py (NY entry gate and 24/7 exits),
ny_fix/indicators.py, ny_fix/signals.py, ny_fix/backtest.py.
Only predeclared conservative adjustments: fee+GST, slippage >=5 BTC
quote units each side (subject to price), 0.02% each ETH side, single
position to cap gross exposure, 1% equity risk, 2x gross leverage cap.
Neither source results nor previously backtested BTC outcomes are used.
Partial 2025-01 IST coverage is flagged; never claim verified 22/22
without prior UTC history and mark-to-market for month-spanning positions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
UPSTREAM_ROOT=ROOT/"external_strategy"/"ny_fix"
sys.path.insert(0,str(UPSTREAM_ROOT))
import common
import config

SYMBOLS=("BTCUSD","ETHUSD")
PERIODS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
OUT=ROOT/"analysis"/"github_external_volatility_persistence_20261118"
PERCENT_PER_SIDE_BTC=0.0005  # >=5 BTC quote units at all observed BTC prices <= 100k
PERCENT_PER_SIDE_ETH=0.0002
START_EQUITY=10000.0

def read_and_verify(symbol):
    base=ROOT/"data"/"delta_india"/symbol/"1m"
    manifest=json.loads((base/"manifest.json").read_text())
    if manifest.get("symbol")!=symbol: raise ValueError("Incorrect symbol "+symbol)
    months={p["file"][:7]:p for p in manifest["partitions"]}
    required=[f"{y}-{m:02d}" for y,range_ in ((2025,range(1,13)),(2026,range(1,11))) for m in range_]
    for ym in required:
        if ym not in months or months[ym]["missing_minutes"]!=0:
            raise AssertionError("Missing full UTC candle month "+symbol+" "+ym)
    frames=[]
    total=0
    for ym in sorted(months):
        if ym<"2025-01" or ym>"2026-11":continue
        item=months[ym]
        f=base/item["file"]
        digest=hashlib.sha256(f.read_bytes()).hexdigest()
        if digest!=item["sha256_gzip"]:
            raise ValueError("Checksum mismatch "+str(f))
        x=pd.read_csv(f,compression="gzip",usecols=["time","open","high","low","close","volume"])
        if len(x)!=item["observed_candles"]:
            raise ValueError("Count mismatch "+str(f))
        total+=len(x);frames.append(x)
    raw=pd.concat(frames,ignore_index=True)
    t=raw.time.to_numpy(np.int64)
    if not np.all(np.diff(t)==60):raise RuntimeError("Missing/duplicate 1m minute samples in "+symbol)
    for col in ["open","high","low","close","volume"]:
        if not np.isfinite(raw[col].to_numpy(float)).all():raise ValueError("Bad "+symbol+" "+col)
    raw.index=pd.to_datetime(raw.time,unit="s",utc=True)
    a=raw[["open","high","low","close","volume"]].resample("1h",label="left",closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    counts=raw.close.resample("1h",label="left",closed="left").count()
    if not (counts.iloc[:-1]==60).all():
        raise RuntimeError("Incomplete 1h candles inside archive "+symbol)
    a=a[counts==60]
    a=a.rename(columns={"open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"})
    a.index.name="DateTime"
    df=a.reset_index()
    return df,dict(symbol=symbol,utc_first=str(raw.index[0]),utc_last=str(raw.index[-1]),
                   raw_candles=total,verified_checksum_partitions=len(frames),
                   full_first_ist_month=False,
                   note="No Dec 31, 2024 18:30-23:59 UTC 1m candles; January 2025 Asia/Kolkata is not fully covered",
                   hourly_completed=len(df))

def run(symbol):
    df,quality=read_and_verify(symbol)
    config.INITIAL_CAPITAL=START_EQUITY
    config.FEE_RATE_PER_SIDE=0.0005*1.18
    config.SLIPPAGE_BPS_PER_SIDE=(PERCENT_PER_SIDE_BTC if symbol=="BTCUSD" else PERCENT_PER_SIDE_ETH)*10000
    config.SLIPPAGE_BPS_BY_REGIME={key:config.SLIPPAGE_BPS_PER_SIDE
                                   for key in ("low","medium","high","extreme","unknown")}
    config.VOL_SIZING=False
    config.VOL_MAX_LEV=2.0
    config.MAX_LEVERAGE=2.0
    config.MAX_CONCURRENT_TRADES=1
    config.ONLY_HIGH_VOL_TRADES=True
    config.ENABLE_4H_EMA_TREND_FILTER=True
    config.ROLLING_VOL_WINDOW=500
    common.set_strategy("simple_rr",SL_ATR_MULT=2.0,SIMPLE_RR=3.0,
                        ENABLE_PARTIAL_TP=False,MAX_CONCURRENT_TRADES=1,
                        SIZING_MODE="pct_risk",RISK_PCT_PER_TRADE=0.01)
    frame=common.prepare_fixed(df)
    stats=common.run(frame,"raw_signal",comp=True)
    ledger=stats["details"].copy()
    if ledger.empty:
        raise ValueError("Candidate produced no closed trades in "+symbol)
    ledger["entry_utc"]=pd.to_datetime(
        frame["DateTime"].iloc[ledger.entry_index.to_numpy(int)].to_numpy(),utc=True)
    ledger["exit_utc"]=pd.to_datetime(
        frame["DateTime"].iloc[ledger.exit_index.to_numpy(int)].to_numpy(),utc=True)
    ledger=ledger.sort_values(["exit_utc","entry_utc"],kind="stable")
    ledger["exit_month_ist"]=ledger.exit_utc.dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    ledger["entry_month_ist"]=ledger.entry_utc.dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    ledger["after_fee_win"]=ledger.pnl>0
    ledger["after_fee_loss"]=ledger.pnl<0
    capital=START_EQUITY
    records=[]
    for month in PERIODS:
        start=capital
        subset=ledger[ledger.exit_month_ist==month]
        capital+=float(subset.pnl.sum())
        ret=100*(capital/start-1) if start>0 else np.nan
        records.append(dict(symbol=symbol,month_ist=month,
                            trades=int(len(subset)),wins=int((subset.pnl>0).sum()),
                            losses=int((subset.pnl<0).sum()),flats=int((subset.pnl==0).sum()),
                            net_pnl=float(subset.pnl.sum()),net_account_return_pct=float(ret),
                            end_equity=capital,strictly_positive=bool(len(subset)>0 and ret>0),
                            status=("Profit" if (len(subset)>0 and ret>0) else
                                    "Loss" if (len(subset)>0 and ret<0) else
                                    "No trades" if len(subset)==0 else "Flat")))
    monthly=pd.DataFrame(records)
    missing_january=True
    winners=int(monthly.strictly_positive.sum())
    ledger.to_csv(OUT/(symbol+"_trade_ledger.csv.gz"),index=False,compression="gzip")
    monthly.to_csv(OUT/(symbol+"_22_ist_months.csv"),index=False)
    return dict(symbol=symbol,upstream="anaysharma1717-svg/Volatility-Persistence-Trading-Strategy",
                source_sha="4987ed61c4fc7f6fc738d88a6eb844b08190a838",
                candidate="NY-entry 1H raw prior-candle sign + confirmed 4H EMA200 + high historical Parkinson-vol regime, ATR5 SL2x/TP3R",
                months_profitable=winners,months_total=22,
                months_nonpositive=22-winners,
                modeled_total_return_pct=float(100*(capital/START_EQUITY-1)),
                trades=int(len(ledger)),wins=int((ledger.pnl>0).sum()),
                losses=int((ledger.pnl<0).sum()),max_trade_close_dd_pct=float(stats["max_drawdown_pct"]),
                source_quality=quality,
                months_return_ist=list(monthly[["month_ist","net_account_return_pct"]].itertuples(index=False,name=None)),
                fee_each_side_incl_gst=0.00059,
                slippage_each_side_bps=config.SLIPPAGE_BPS_PER_SIDE,
                funding_settlements_modeled=False,
                incomplete_ist_start=missing_january,
                passes_22_of_22=bool(winners==22 and not missing_january),
                limitations=[
                    "The first IST month lacks complete 2024-12-31 UTC candle coverage",
                    "Month returns book PnL only on trade exits; no month-end MTM for an open trade",
                    "Funding cashflows and actual bid-ask/price impact are unmodeled",
                    "Upstream stops/targets are 1h OHLC intrabar approximations",
                    "Source FEE rate replaced with Delta India taker+GST rate",
                    "Single position versus upstream max three to control leverage",
                ])

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    res=[run(symbol) for symbol in SYMBOLS]
    (OUT/"paired_verdict.json").write_text(json.dumps({
      "candidate_source":"https://github.com/anaysharma1717-svg/Volatility-Persistence-Trading-Strategy",
      "pinned_sha":"4987ed61c4fc7f6fc738d88a6eb844b08190a838",
      "verified_22_months_any":any(r["passes_22_of_22"] for r in res),
      "results":res},indent=2,default=str)+"\n")
    text=["# External GitHub strategy BTC+ETH 22-month replay",
          "", "Pinned source: https://github.com/anaysharma1717-svg/Volatility-Persistence-Trading-Strategy",
          "", "Caveat: January 2025 IST lacks the previous UTC day, so results are not eligible for any verified 22/22 claim.",
          "", "| Symbol | Profitable months (diagnostic) | Net total return | Trades | Wins | Losses |",
          "|---|---:|---:|---:|---:|---:|"]
    for r in res:
        text.append("| "+r["symbol"]+" | "+str(r["months_profitable"])+
         "/22 | "+f'{r["modeled_total_return_pct"]:.3f}% | '+str(r["trades"])+
         " | "+str(r["wins"])+" | "+str(r["losses"])+" |")
    text+=["","Modeled taker 0.05% per side + 18% GST on fees, BTC 5bps and ETH 2bps adverse slip each execution side.",
            "Funding settlements, L1 impact, intra-hour fill path, and end-month unrealized positions are not fully modeled.",
            "No lookahead intended. Previous completed candle signals and lagged 4h EMA state.",
            "Profitable months do not by themselves imply forward profitability."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(text)+"\n")
    print("EXTERNAL_GITHUB_CANDIDATE_TEST "+json.dumps([
      {key:r[key] for key in ("symbol","months_profitable","modeled_total_return_pct","trades","wins","losses","passes_22_of_22")}
      for r in res
    ]),flush=True)
if __name__=="__main__":main()
