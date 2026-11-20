#!/usr/bin/env python3
"""BTC-only versus synchronized ETH-confirmed BTC EMA20/Supertrend research.

Reuses the unchanged BTC $10 isolated 100x replay for exits, fees, stop
monitoring, liquidation approximations, and monthly equity bookkeeping.
Only the eligible entry bar mask changes. Results are NOT live P&L.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

import replay_btc_ema_st_screenshot as source
import replay_btc_ema_st_fixed_10_margin as prior

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis/btc_ema_st_eth_confirm_20261120"

def load_symbol(symbol):
    """Reuse sha256-verified historical 1m loader and 15m aggregator."""
    old = source.DATA
    try:
        source.DATA = ROOT / "data/delta_india" / symbol / "1m"
        return source.load()
    finally:
        source.DATA = old

def sides(frame):
    """Original 15m EMA20/ST conditions for each symbol, without future data."""
    valid = (np.isfinite(frame.ema) & np.isfinite(frame.atr14)
             & np.isfinite(frame.atr_ratio) & np.isfinite(frame.volume_ratio))
    gate = valid & (frame.atr_ratio >= 1.0) & (frame.volume_ratio >= 1.5)
    long = (gate & (frame.dir == -1) & (frame.dir.shift(1) == -1)
            & (frame.low <= frame.ema) & (frame.close > frame.ema))
    short = (gate & (frame.dir == 1) & (frame.dir.shift(1) == 1)
             & (frame.high >= frame.ema) & (frame.close < frame.ema))
    assert not (long & short).any()
    return pd.Series(np.select([long, short], [1, -1], default=0),
                     index=frame.index, dtype="int8")

def allow_btc_entries(frame, allowed):
    """Mask BTC-only entry gate; leave price, ATR/ST and BTC exits unchanged."""
    assert allowed.index.equals(frame.index)
    out = frame.copy()
    out["volume_ratio"] = out.volume_ratio.where(allowed, 0.0)
    return out

def run_mode(name, frame, allowed, last_month, external_entry_side=None):
    out = {}
    checked = allow_btc_entries(frame, allowed)
    for fill in ("threshold", "bankruptcy"):
        trades, stats = prior.replay(checked, 0, fill, external_entry_side=external_entry_side)
        monthly = prior.monthly(trades, "2025-01", last_month)
        complete = monthly[monthly.complete_month]
        stats["completed_months"] = int(len(complete))
        stats["profitable_completed_months"] = int((complete.net_profit_usd > 0).sum())
        stats["losing_completed_months"] = int((complete.net_profit_usd < 0).sum())
        stats["flat_completed_months"] = int((complete.net_profit_usd == 0).sum())
        stats["candidate_signal_bars"] = int(allowed.sum())
        monthly.to_csv(OUT / f"{name}_{fill}_monthly.csv", index=False)
        trades.to_csv(OUT / f"{name}_{fill}_trades.csv.gz",
                      index=False, compression="gzip")
        out[fill] = stats
        print(f"RESULT {name}/{fill}: net=${stats['net_profit_usd']:+.2f} "
              f"trades={stats['completed_trades']} "
              f"PF={stats['net_profit_factor']} "
              f"eligible30m={stats['scalper_eligible_trades']} "
              f"liq={stats['assumed_liquidations']} "
              f"profitable_complete_months={stats['profitable_completed_months']}/"
              f"{stats['completed_months']}", flush=True)
    return out

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    btc_bars, btc_manifest, btc_count = load_symbol("BTCUSD")
    eth_bars, eth_manifest, eth_count = load_symbol("ETHUSD")
    btc_full = source.indicators(btc_bars)
    eth_full = source.indicators(eth_bars)
    common = btc_full.index.intersection(eth_full.index)
    if len(common) < 1000:
        raise RuntimeError("Insufficient aligned BTCUSD/ETHUSD candles")
    assert common.is_unique and common.is_monotonic_increasing
    assert ((common[1:] - common[:-1]) == pd.Timedelta(minutes=15)).all()
    btc = btc_full.loc[common].copy()
    eth = eth_full.loc[common].copy()
    assert btc.index.equals(eth.index)
    b = sides(btc)
    e = sides(eth)
    eth_st = pd.Series(np.where(eth.dir.to_numpy() == -1, 1, -1),
                       index=common, dtype="int8")
    # PRIMARY: BTC and ETH must BOTH meet the entire entry rule on SAME 15m
    # closed bar, same direction. BTC alone controls the subsequent exit.
    both_full = (b != 0) & (b == e)
    # Secondary diagnostic: BTC full signal, ETH Supertrend agrees on trend.
    eth_trend_match = (b != 0) & (b == eth_st)
    assert not (both_full & ~eth_trend_match).any()
    # Requested ETH-trigger mode: ETH meets its complete 15m EMA/ST entry,
    # BTC has the same current Supertrend bias, and ONLY BTC is traded.
    btc_st = pd.Series(np.where(btc.dir.to_numpy() == -1, 1, -1),
                       index=common, dtype="int8")
    eth_driven = e.where(e == btc_st, 0)
    modes = {
      "btc_only": b != 0,
      "btc_plus_eth_matching_full_entry": both_full,
      "btc_plus_eth_matching_st_trend": eth_trend_match,
      "eth_full_signal_triggers_btc_matching_st": eth_driven != 0
    }
    final_month = str(common[-1].to_period("M"))
    report = {
      "instruments": {"traded": "BTCUSD", "confirmation": "ETHUSD"},
      "timeframe": "15m", "common_start_utc": str(common[0]),
      "common_end_utc": str(common[-1]),
      "matched_15m_bars": len(common),
      "verified_1m_bar_counts": {"BTCUSD": btc_count, "ETHUSD": eth_count},
      "source_manifests_generated_utc": {"BTCUSD": btc_manifest["generated_at_utc"],
                                          "ETHUSD": eth_manifest["generated_at_utc"]},
      "signals": {"btc": int((b!=0).sum()), "eth": int((e!=0).sum()),
                  "both_full_same_bar": int(both_full.sum()),
                  "btc_with_eth_trend": int(eth_trend_match.sum()),
                  "eth_signal_with_btc_st_trend": int((eth_driven != 0).sum())},
      "settings": prior.PARAMS,
      "limitations": "No funding, slippage or spread; assumed 30-minute Scalper Offer; "
                     "same-bar close fills and OHLC liquidation proxies (not Mark Price). "
                     "The last overlapping ETH/BTC candle limits the comparison.",
      "results": {}
    }
    for name, gate in modes.items():
        report["results"][name] = run_mode(name, btc, gate, final_month,
            external_entry_side=eth_driven.to_numpy() if name == "eth_full_signal_triggers_btc_matching_st" else None)
    (OUT / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print("SUCCESS: BTC vs ETH-confirmed BTC research complete", flush=True)

if __name__ == "__main__":
    main()
