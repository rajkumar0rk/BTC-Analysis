#!/usr/bin/env python3
"""Stage18 BTC 70/30 research candidate -- genuine independent 1m sleeve replays.

70%: 4H trend / 1H pullback / 15M breakout, max 700 BTC-point
     structural stop, 5R target, max 240-minute hold.
30%: Daily55 EMA50 Donchian, initial 2x ATR SL, 3x ATR trail,
     max 30-day holding period.

Research-only blended NAV: each sleeve independently simulates on BTC 1m data.
The monthly-rebalanced blend is SYNTHETIC. It does not resize already-open
Donchian positions at month boundaries, simulate shared exchange margin, or
make ANY live/real-money orders.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from research_every_candle_200 import FEE, SLIPPAGE, read_archive
import research_stage18_core_standalone_20261121 as core
import research_stage18_donchian_standalone_20261121 as don
import research_stage18_stage20_signal_exit_improvement_20261120 as nav

CONFIG_DEFAULT = Path("config/strategies/stage18_btc_70core_30donchian_research.json")
OUTPUT_DEFAULT = Path("analysis/stage18_btc_70core_30donchian_implementation")
BASELINE_NAME = "stage18_original_75_25_14d"
SELECTED_NAME = "stage18_70_30_30d"
MONTHS = list(nav.MONTHS)


def load_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if cfg.get("schema_version") != 1:
        raise ValueError("Unsupported strategy configuration schema")
    if cfg.get("execution_mode") != "BACKTEST_ONLY":
        raise ValueError("Only BACKTEST_ONLY mode is supported; no live orders")
    if cfg.get("market") != "BTCUSD_FUTURES":
        raise ValueError("Backtest candles must be BTCUSD Futures")
    if cfg.get("timezone") != "Asia/Kolkata":
        raise ValueError("This research is month-grouped by Asia/Kolkata")
    if cfg.get("sample") != {"first_month": "2025-01", "last_month": "2026-10"}:
        raise ValueError("Sample must match the frozen Stage18 22-month research window")
    alloc = cfg["allocation"]
    a = float(alloc["core"])
    b = float(alloc["donchian"])
    if not (math.isfinite(a) and math.isfinite(b) and 0 < a < 1 and
            0 < b < 1 and math.isclose(a+b, 1.0, abs_tol=1e-12)):
        raise ValueError("Sleeve weights must be positive and add to 1")
    if alloc.get("rebalance") != "monthly_end_synthetic":
        raise ValueError("Only synthetic monthly rebalancing is implemented")
    c=cfg["core"]
    d=cfg["donchian"]
    if c["archive_signal_family"] != "S13_pullback_near_half_atr":
        raise ValueError("Wrong source signal family; do not substitute untested signals")
    if c["execution"] != "next_available_1m_open" or d["execution"] != "next_available_1m_open":
        raise ValueError("Only next-1m-open execution supported")
    if c["monthly_accounting"] != "exit_month_realized" or d["monthly_accounting"] != "month_end_mark_to_market":
        raise ValueError("Unknown accounting scheme")
    if (float(c["theoretical_risk_per_trade_fraction"]) != .005 or
        float(d["risk_per_trade_fraction"]) != .005 or
        float(c["max_notional_multiple"]) != 3.0):
        raise ValueError("Risk or leverage differs from engine; would invalidate results")
    cost=cfg["costs"]
    expected_fee=float(cost["taker_fee_rate_per_side"])*(1+float(cost["gst_rate"]))
    if abs(expected_fee-FEE) > 1e-12 or abs(float(cost["base_adverse_slippage_points_per_side"])-SLIPPAGE)>1e-12:
        raise ValueError("Fee/GST/slippage config does not match actual replay engine")
    if list(cost["extra_adverse_slippage_bps_per_side"]) != [0,2,5]:
        raise ValueError("This frozen regression expects stress cases 0/2/5bps each side")
    if not (bool(cost["funding_included"]) is False and
            bool(cost["measured_spread_included"]) is False and
            bool(cost["actual_liquidation_included"]) is False):
        raise ValueError("Do not claim unsupported trading costs are included")
    if (float(c["min_structural_stop_points"]) <= 0 or
        float(c["max_structural_stop_points"]) <= float(c["min_structural_stop_points"]) or
        int(c["max_hold_minutes"]) <= 0 or int(d["max_hold_days"]) <= 0):
        raise ValueError("Stop and holding limits must be positive and ordered")
    if (int(d["history_complete_days"]) < max(55, int(d["channel_days"])) or
        float(d["initial_stop_atr"]) <= 0 or float(d["trailing_stop_atr"]) <= 0):
        raise ValueError("Insufficient Donchian history or invalid ATR parameters")
    return cfg


def blend_monthly(core_pct, donchian_pct, core_weight):
    """Synthetic MONTHLY rebalancing; inputs are percent returns, not fractions."""
    x=np.asarray(core_pct,dtype=float)
    y=np.asarray(donchian_pct,dtype=float)
    w=float(core_weight)
    if x.shape != y.shape or x.ndim != 1 or len(x)==0:
        raise ValueError("Both standalone sleeves must have aligned months")
    if not (np.isfinite(x).all() and np.isfinite(y).all()):
        raise ValueError("Nonfinite monthly strategy return")
    if not (0 <= w <= 1):
        raise ValueError("Invalid allocation")
    if (x<=-100).any() or (y<=-100).any():
        raise ValueError("Bankrupt standalone strategy invalidates synthetic blend")
    z=w*x+(1-w)*y
    if (z<=-100).any():
        raise ValueError("Negative synthetic portfolio equity")
    return z


def metrics(pct):
    v=np.asarray(pct,dtype=float)
    if v.ndim!=1 or not len(v) or not np.isfinite(v).all():
        raise ValueError("Invalid monthly returns")
    nav_path=np.cumprod(1+v/100)
    peak=np.maximum.accumulate(np.r_[1.,nav_path])[1:]
    return dict(
        total_return_pct=float(100*(nav_path[-1]-1)),
        positive_months=int(np.count_nonzero(v>1e-8)),
        negative_months=int(np.count_nonzero(v< -1e-8)),
        flat_months=int(np.count_nonzero(abs(v)<=1e-8)),
        max_month_end_drawdown_pct=float(100*np.max(1-nav_path/peak)),
        worst_month_pct=float(v.min()),
        month_end_equity_index=float(100*nav_path[-1]),
    )


def make_core_config(cfg):
    c=cfg["core"]
    return core.case("stage18_700pt_core",
        eff=float(c["previous_month_efficiency_max"]),
        adx=float(c["adx_4h_max"]),
        vol=float(c["h1_relative_volume_max"]),
        minrisk=float(c["min_structural_stop_points"]),
        maxrisk=float(c["max_structural_stop_points"]),
        direction="both",
        reward=float(c["take_profit_R"]),
        hold=int(c["max_hold_minutes"]))


def make_donchian_config(cfg):
    d=cfg["donchian"]
    return don.case("stage18_daily55_30day",
        days=int(d["channel_days"]),trend=d["ema_filter"],
        initial_atr=float(d["initial_stop_atr"]),
        trail_atr=float(d["trailing_stop_atr"]),
        hold_days=int(d["max_hold_days"]),
        opposite=bool(d["exit_on_opposite_signal"]),
        history=int(d["history_complete_days"]))


def donchian_pct(month_end_nav):
    n=np.asarray(month_end_nav,dtype=float)
    if len(n)<len(MONTHS):
        raise ValueError("Missing end-of-month Donchian equity values")
    sampled=n[:len(MONTHS)]
    if not np.isfinite(sampled).all() or (sampled<=0).any():
        raise ValueError("Donchian equity invalid")
    return 100*(sampled/np.r_[100.,sampled[:-1]]-1)


def verify_snapshot(summary: pd.DataFrame):
    """Freeze the published research candidate; fail if source/model diverges.

    These values are REGRESSION references, not forward profitability forecasts.
    """
    original=summary[(summary.scenario==BASELINE_NAME)&(summary.extra_bps_side==0)]
    if len(original)!=1:
        raise AssertionError("Missing original portfolio baseline")
    o=original.iloc[0]
    if abs(o.total_return_pct-13.87896)>.015 or (o.positive_months,o.negative_months,o.flat_months)!=(18,3,1):
        raise AssertionError("Original 75/25 Stage18 history failed source parity")
    expected={
        0:(14.4381,19,2,1),
        2:(11.8601,18,3,1),
        5:(8.1028,16,5,1),
    }
    for cost,(total,pos,neg,flat) in expected.items():
        row=summary[(summary.scenario==SELECTED_NAME)&(summary.extra_bps_side==cost)]
        if len(row)!=1:
            raise AssertionError("Missing 70/30 stress row "+str(cost))
        x=row.iloc[0]
        if (abs(x.total_return_pct-total)>.015 or
            (x.positive_months,x.negative_months,x.flat_months)!=(pos,neg,flat)):
            raise AssertionError("Published 70/30 model snapshot did not reproduce under cost "+str(cost))


def main():
    ap=argparse.ArgumentParser(description="Reproducible Stage18 synthetic BTC 70/30 monthly portfolio")
    ap.add_argument("--config",type=Path,default=CONFIG_DEFAULT)
    ap.add_argument("--out",type=Path,default=OUTPUT_DEFAULT)
    args=ap.parse_args()
    cfg=load_config(args.config)
    args.out.mkdir(parents=True,exist_ok=True)

    f,seg_start,_,quality=read_archive()
    month_id,source_labels=don.original.build_months(f)
    if list(source_labels[:len(MONTHS)]) != MONTHS:
        raise AssertionError("BTC 1-minute timeline does not contain the expected 22 IST months")
    events=core.load_events(f)
    improved_core=core.run_case(f,events,make_core_config(cfg))
    previous_core=core.run_case(f,events,core.case("original_core_5R_4h"))
    if improved_core is None or len(improved_core)!=63 or previous_core is None or len(previous_core)!=75:
        raise AssertionError("Original vs improved core trades failed reproducibility")
    current=np.asarray(f.time.to_numpy(np.int64),dtype=np.int64)
    if (improved_core.entry_unix.diff().dropna() < 0).any():
        raise AssertionError("Core ledger time out of order")

    bars=don.original.higher_bars(f,"1D")
    dc=make_donchian_config(cfg)
    signal,updates,atr,close,signal_count=don.filter_signals(f,bars,dc)
    old_dc=don.case("original_daily55_14days")
    original_signal,original_updates,original_atr,original_close,_=don.filter_signals(f,bars,old_dc)
    OHLC=[f[x].to_numpy(np.float64) for x in ("open","high","low","close")]
    T=current
    original_ref=don.original.run_one(*OHLC,T,month_id,seg_start,original_signal,
                                     original_updates,original_atr,original_close,3.,len(source_labels))
    # Parity with source Stage17. No accidental new data/path or same-bar stop lookahead.
    baseline_replay=don.replay(*OHLC,T,month_id,seg_start,original_signal,
                               original_updates,original_atr,original_close,3.,2.,14*1440,True,0.,len(source_labels))
    parity_delta=float(np.max(np.abs(original_ref[1]-baseline_replay[1])))
    if parity_delta>1e-8 or len(original_ref[0])!=13:
        raise AssertionError("Original Daily55 14-day ATR engine did not reconcile")
    original_returns=donchian_pct(original_ref[1])

    core_selected={};core_original={}
    monthly_rows=[];summary_rows=[];donchian_trades={}
    risk_c=cfg["core"]
    weight=float(cfg["allocation"]["core"])
    for extra in cfg["costs"]["extra_adverse_slippage_bps_per_side"]:
        fee=int(extra)
        core_selected[fee]=np.asarray([r["net_pct"] for r in nav.replay_nav(improved_core,fee)["monthly"]],float)
        core_original[fee]=np.asarray([r["net_pct"] for r in nav.replay_nav(previous_core,fee)["monthly"]],float)
        if len(core_selected[fee])!=len(MONTHS):
            raise AssertionError("Core months did not reconcile to complete calendar")
        d_replay=don.replay(*OHLC,T,month_id,seg_start,signal,updates,atr,close,
            float(dc["trail_atr"]),float(dc["initial_atr"]),
            int(dc["hold_days"])*1440,bool(dc["opposite"]),fee/10000.,len(source_labels))
        donchian_trades[fee]=len(d_replay[0])
        selected_don=donchian_pct(d_replay[1])
        if fee==0:
            donchi_ledgers=[dict(entry_unix=int(tr[0]),exit_unix=int(tr[1]),
                direction="LONG" if tr[2]==1 else "SHORT",
                initial_risk_pts=float(tr[3]),net_points=float(tr[4]),net_R=float(tr[5]),
                reason=["stop","time_cap","opposite_breakout","data_gap"][tr[6]])
                for tr in d_replay[0]]
            pd.DataFrame(donchi_ledgers).to_csv(args.out/"donchian_30day_trades.csv",index=False)
        # For the historical original benchmark, rerun the original Donchian at
        # each cost level instead of erroneously reusing baseline no-extra-cost NAV.
        d_old=baseline_replay if fee==0 else don.replay(*OHLC,T,month_id,seg_start,
              original_signal,original_updates,original_atr,original_close,
              3.,2.,14*1440,True,fee/10000.,len(source_labels))
        old_don=donchian_pct(d_old[1])
        for name,c,d,w in (
            (SELECTED_NAME,core_selected[fee],selected_don,weight),
            (BASELINE_NAME,core_original[fee],old_don,.75),
        ):
            combined=blend_monthly(c,d,w)
            st=metrics(combined)
            summary_rows.append(dict(scenario=name,extra_bps_side=fee,
                core_weight=w,donchian_weight=1-w,
                core_standalone_return_pct=metrics(c)["total_return_pct"],
                donchian_standalone_return_pct=metrics(d)["total_return_pct"],
                year2025_return_pct=metrics(combined[:12])["total_return_pct"],
                year2026_JanOct_return_pct=metrics(combined[12:])["total_return_pct"],
                core_trades=63 if name==SELECTED_NAME else 75,
                donchian_trades=len(d_replay[0]) if name==SELECTED_NAME else len(d_old[0]),
                **st))
            equity=100.
            for i,(month,cr,dr,pr) in enumerate(zip(MONTHS,c,d,combined)):
                equity*=1.+float(pr)/100
                monthly_rows.append(dict(scenario=name,extra_bps_side=fee,
                    month_ist=month,core_weight=w,donchian_weight=1-w,
                    core_month_pct=float(cr),donchian_month_pct=float(dr),
                    portfolio_month_pct=float(pr),equity_index_end=float(equity),
                    status="Profit" if pr>1e-8 else "Loss" if pr< -1e-8 else "Flat"))
    summary=pd.DataFrame(summary_rows)
    verify_snapshot(summary)
    summary.to_csv(args.out/"scenario_summary.csv",index=False)
    pd.DataFrame(monthly_rows).to_csv(args.out/"scenario_monthly_22.csv",index=False)
    improved_core.to_csv(args.out/"core_700point_1m_trades.csv",index=False)
    (args.out/"reproducibility.json").write_text(json.dumps(dict(
        strategy_id=cfg["strategy_id"],execution_mode=cfg["execution_mode"],
        source_quality=quality,months=MONTHS,core_improved_trades=len(improved_core),
        core_original_trades=len(previous_core),donchian_source_parity_delta=parity_delta,
        donchian_candidate_signal_count=signal_count,
        donchian_30day_trade_counts_by_extra_bps=donchian_trades,
        monthly_rebalance_implemented="synthetic weighted month returns, NOT live per-position rebalance",
        limitations=cfg["limitations"],regression_snapshots_verified=True,
    ),indent=2,default=str)+"\n",encoding="utf-8")
    base=summary[(summary.scenario==SELECTED_NAME)&(summary.extra_bps_side==0)].iloc[0]
    print("STAGE18_70_30_PARITY_OK",json.dumps(dict(original_Donchian_max_delta=parity_delta,
        original_core_trades=len(previous_core),selected_core_trades=len(improved_core))))
    for r in summary.to_dict("records"):
        print("PORTFOLIO_RESULT",json.dumps(r,default=str))
    print("STAGE18_70_30_IMPLEMENTED",json.dumps(dict(
        return_pct=round(float(base.total_return_pct),6),
        positive=int(base.positive_months),negative=int(base.negative_months),
        flat=int(base.flat_months),output=str(args.out),LIVE_TRADING=False)))


if __name__=="__main__":
    main()
