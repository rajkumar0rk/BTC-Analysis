#!/usr/bin/env python3
"""Compare EMA20 Touch 3% initial SL, single vs incremental profit-lock.

Same 1H Supertrend(10,3) + EMA20 first-touch signals, ratio 1.25-2.5x,
0.001 BTC, same next-hour entry, one fill per ST cycle.
Profit locks: prior baselines plus exact requested [0.16,0.30,0.50,1,2%]
and [0.16,0.50,1,2%] variants. Each path is independently replayed.
Prices are executed against both hypothetical 1m intrabar OHLC paths.
"""
import json
from pathlib import Path
import pandas as pd
from research_st_ema20_initial_sl_grid_20261122 import (
    eng, prepare_entries, run, summarize, PATHS
)

OUT=Path("analysis/st_ema20_touch_incremental_3pct_sl_20261122")
LADDERS={
    "single_0p14": (0.14,),
    "increment_0p14_0p50_1_2_5": (0.14,0.5,1.0,2.0,5.0),
    "exact_0p20_0p50_1_2": (0.20,0.50,1.0,2.0),
    "control_0p20_0p50_1_2_5": (0.20,0.50,1.0,2.0,5.0),
    "exact_0p16_0p30_0p50_1_2": (0.16,0.30,0.50,1.0,2.0),
    "exact_0p16_0p50_1_2": (0.16,0.50,1.0,2.0),
}
REFERENCE={
    "open_high_low_close": (50,0.725036,21),
    "open_low_high_close": (50,0.723046,21),
}

def main():
    engine=eng()
    engine.smoke_test()
    m,h,nfiles=engine.load()
    h=engine.features(h)
    h["volume_ratio"]=(h.volume/h.volume.shift(1).rolling(20,min_periods=20).mean().replace(0,pd.NA))
    entries=prepare_entries(engine,m,h,"touch")
    assert len(entries)==52, len(entries)
    assert tuple(LADDERS["increment_0p14_0p50_1_2_5"]) == engine.LADDERS["L13_0p14_0p5_1_2_5"]
    scores=[];months=[];trades=[]
    for path in PATHS:
        for variant,ladder in LADDERS.items():
            t=run(engine,m,h,entries,"touch",path,"3%","pct",3.0,ladder_override=ladder)
            score,monthly=summarize(t,"touch","3%",path)
            score["variant"]=variant
            score["profit_lock_ladder_pct"]=" -> ".join(f"{v:g}%" for v in ladder)
            monthly["variant"]=variant
            t["variant"]=variant
            scores.append(score);months.append(monthly);trades.append(t)
            if variant=="single_0p14":
                count,net,pos=REFERENCE[path]
                assert score["trades"]==count,(path,score)
                assert abs(score["total_net_usd"]-net)<0.00001,(path,score)
                assert score["profitable_months"]==pos,(path,score)
            print(variant,path,"profitable",score["profitable_months"],
                  "losing",score["losing_months"],"net",score["total_net_usd"],
                  "trades",score["trades"],"win%",score["win_rate_pct"],
                  "stopped",score["stopped_trades"],flush=True)

    OUT.mkdir(parents=True,exist_ok=True)
    s=pd.DataFrame(scores)
    mth=pd.concat(months,ignore_index=True)
    t=pd.concat(trades,ignore_index=True)
    s.to_csv(OUT/"summary.csv",index=False)
    mth.to_csv(OUT/"monthly.csv",index=False)
    t.to_csv(OUT/"trades.csv",index=False)
    p=[]
    for variant,g in s.groupby("variant"):
        assert len(g)==2
        p.append(dict(
          variant=variant,
          initial_stop="3%",
          lock_levels_pct=g.profit_lock_ladder_pct.iloc[0],
          profitable_months_min=int(g.profitable_months.min()),
          profitable_months_max=int(g.profitable_months.max()),
          losing_months_max=int(g.losing_months.max()),
          net_usd_min=float(g.total_net_usd.min()),
          net_usd_max=float(g.total_net_usd.max()),
          net_2025_min=float(g.net_2025.min()),
          net_2025_max=float(g.net_2025.max()),
          net_2026_min=float(g.net_2026.min()),
          net_2026_max=float(g.net_2026.max()),
          wins=int(g.wins.min()),
          losses=int(g.losses.max()),
          stops_triggered=int(g.stopped_trades.max()),
          max_realized_dd_pct=float(g.max_realized_dd_pct.max())
        ))
    paired=pd.DataFrame(p).sort_values("profitable_months_min",ascending=False)
    paired.to_csv(OUT/"comparison.csv",index=False)
    quality=dict(
      source="Delta Exchange India BTCUSD 1m native OHLCV",
      completed_months="2025-01 through 2026-10 (22)",
      total_archive_minutes=len(m),source_files=nfiles,
      timeframe="1H signal, 1m entry and stop updates",
      initial_stop_pct=3.0,
      volume_ratio_min=1.25,volume_ratio_max=2.5,
      profit_lock_ladders={k:list(v) for k,v in LADDERS.items()},
      stop_update="Raise stop to each attained positive entry-relative milestone; never loosen",
      quantity_btc=engine.QTY,roundtrip_fees_with_GST="0.059% per side",
      slippage_btc_points_per_leg=engine.SLIP,
      stop_gap_policy="Fill at actual minute open if market gaps beyond active stop",
      excludes=["Exchange funding","liquidation","margin","order-book depth",
                "actual exchange ticks / amend latency"],
      validation="Single 0.14% baseline matches separately backtested 3% initial SL",
      note="Historical intraminute order ambiguity simulated separately in both paths; not live fills"
    )
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text(
      "# EMA20 Touch: 3% initial stop plus incremental profit protection\n\n"
      "BTCUSD 1H ST(10,3) first EMA20 Touch, volume ratio 1.25-2.5x; 1m stop updates.\n"
      "Comparison includes exact 0.16% -> 0.30% -> 0.50% -> 1% -> 2% and 0.16% -> 0.50% -> 1% -> 2% ladders.\n"
      "The stop starts at -3% from entry and moves to the highest reached positive lock.\n"
      "The Supertrend flip remains a fallback exit; one fill per ST cycle.\n\n"
      "## Side-by-side across two simulated price paths\n\n"
      +paired.to_markdown(index=False)
      +"\n\n## Yearly and path-level results\n\n"
      +s[["variant","path","trades","wins","losses","profitable_2025",
          "profitable_2026","profitable_months","losing_months",
          "flat_months","net_2025","net_2026","total_net_usd",
          "stopped_trades","max_realized_dd_pct"]].to_markdown(index=False)
      +"\n\nFees, GST and 5-point execution slippage each side included. "
      "No tick sequence, order latency, funding, margin or liquidation. "
      "The results are retrospective and are not live-trading proof.\n"
    )
    print("SUCCESS",OUT,flush=True)

if __name__=="__main__":
    main()
