#!/usr/bin/env python3
"""Causal 1H failed order-block (breaker) proxy, fixed 3R, genuine Delta India 1m replay.

This is NOT the publisher's proprietary breaker-block implementation. Signal detector
is explicitly documented and pre-registered in NOVELTY_CHECK.md.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_daily_bollinger_30_3r import load_1m, load_funding, backtest

OUT = Path("analysis/hourly_breaker_block_3r")


def signal_detector(d):
    hour = d.resample("1h", label="right", closed="left").agg({
        "open": "first", "high": "max", "low": "min", "close": "last",
        "volume": "sum"
    })
    hour["count"] = d.close.resample("1h", label="right", closed="left").count()
    if (hour["count"] != 60).any():
        raise RuntimeError("Incomplete 1H candles, refusing simulated signals")
    close = hour.close.to_numpy(float)
    op = hour.open.to_numpy(float)
    hi = hour.high.to_numpy(float)
    lo = hour.low.to_numpy(float)
    vol = hour.volume.to_numpy(float)
    length = len(hour)

    # Wilder ATR14: first valid bar is average of first fourteen 1h true ranges.
    true_range = np.empty(length, dtype=float)
    for i in range(length):
        prev_close = close[i - 1] if i else close[i]
        true_range[i] = max(hi[i] - lo[i], abs(hi[i]-prev_close), abs(lo[i]-prev_close))
    atr = np.full(length, np.nan)
    atr[13] = float(np.mean(true_range[:14]))
    for i in range(14, length):
        atr[i] = (13*atr[i-1] + true_range[i])/14

    signals = {}
    detail = []
    blocks = []
    created = 0
    expired = 0
    invalidated = 0
    outside_session = 0
    collisions = 0
    for k in range(24, length):
        # Keep order blocks at most 48h old.
        live = [b for b in blocks if k-b["created_k"] <= 48 and not b["used"]]
        expired += len(blocks) - len(live)
        blocks = live

        # A closed bar that conclusively crosses a prior body's edge creates a breaker event.
        events = []
        for b in blocks:
            if k <= b["created_k"]+1:
                continue
            prev_close = close[k-1]
            if b["kind"] == "bullish_ob":
                if close[k] < op[k] and prev_close >= b["body_lower"] and \
                        close[k] < b["body_lower"] - 0.10*atr[k]:
                    events.append((-1, b))
            elif b["kind"] == "bearish_ob":
                if close[k] > op[k] and prev_close <= b["body_upper"] and \
                        close[k] > b["body_upper"] + 0.10*atr[k]:
                    events.append((1, b))
        if events:
            # All failed blocks are consumed even if outside session or busy.
            invalidated += len(events)
            for _, b in events:
                b["used"] = True
            if len(events) > 1:
                collisions += len(events)-1
            side, b = max(events, key=lambda x:x[1]["created_k"])
            candle_start = hour.index[k] - pd.Timedelta(hours=1)
            if candle_start.hour in (13,14,15,16):
                stop = lo[k]-0.25*atr[k] if side == 1 else hi[k]+0.25*atr[k]
                # Uses only completed candle at index k, follows next 1m OPEN.
                signals[int(hour.index[k].timestamp())] = (
                    side, float(stop), str(candle_start), float(close[k]), float(atr[k])
                )
                detail.append(dict(
                    signal_close_utc=str(hour.index[k]), signal_open_utc=str(candle_start),
                    side="LONG" if side==1 else "SHORT",
                    order_block_type=b["kind"], ob_created_utc=str(hour.index[b["created_k"]]),
                    ob_body_low=round(b["body_lower"],4),
                    ob_body_high=round(b["body_upper"],4),
                    signal_close=close[k], signal_ATR14=atr[k],
                    stop_price=stop, order_block_age_hours=k-b["created_k"]
                ))
            else:
                outside_session += 1

        # Create later-use 1H order blocks from displacement and prior opposite 1H candle.
        if np.isfinite(atr[k]) and atr[k] > 0:
            breakout_up = (
                close[k] > np.max(hi[k-12:k]) and
                close[k] > op[k] and close[k]-op[k] >= 0.5*atr[k]
            )
            breakout_dn = (
                close[k] < np.min(lo[k-12:k]) and
                close[k] < op[k] and op[k]-close[k] >= 0.5*atr[k]
            )
            if breakout_up or breakout_dn:
                # The order block is the latest prior opposite-color candle in 3 completed bars.
                for j in range(k-1,k-4,-1):
                    opposite = (close[j]<op[j]) if breakout_up else (close[j]>op[j])
                    if opposite:
                        blocks.append({
                            "created_k": k,
                            "body_lower": float(min(op[j],close[j])),
                            "body_upper": float(max(op[j],close[j])),
                            "kind": "bullish_ob" if breakout_up else "bearish_ob",
                            "used": False
                        })
                        created += 1
                        break

    info=dict(complete_1h_bars=length, raw_qualifying_breaker_signals=len(signals),
        qualifying_displacement_blocks_created=created,
        order_blocks_expired_or_consumed=expired,
        body_cross_events_all_sessions=invalidated,
        events_rejected_outside_session=outside_session,
        simultaneous_block_flip_collisions=collisions,
        market_session_utc="candle OPEN hours 13,14,15,16",
        measured_period=str(hour.index.min())+" to "+str(hour.index.max()))
    return signals, pd.DataFrame(detail), info


def score_by_time(trades):
    if trades.empty:
        return pd.DataFrame([dict(period="all",trades=0,wins=0,losses=0,win_pct=None,pf_net=None)])
    # Closed-trade date, not entry date. Nov is partial.
    dat = trades.exit_ist_month.astype(str)
    cuts=[("2025",dat.str.startswith("2025")),
          ("2026_Jan_Oct",(dat>="202601")&(dat<"202611")),
          ("2026_Nov_partial",dat=="202611"),
          ("2025_through_Oct_2026",dat<"202611"),
          ("entire_period",dat.notna())]
    results=[]
    for nm,mask in cuts:
        v=trades.loc[mask,"net_usd"].to_numpy(float)
        gp=v[v>0].sum()
        gl=-v[v<0].sum()
        results.append(dict(period=nm,trades=len(v),wins=int((v>0).sum()),
            losses=int((v<=0).sum()),win_pct=round(100*(v>0).mean(),2) if len(v) else None,
            pf_net=round(float(gp/gl),3) if gl>0 else None,
            net_closed_USD=round(float(v.sum()),2),
            targets=int((trades.loc[mask,"result"]=="target").sum()) if len(v) else 0))
    return pd.DataFrame(results)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d,source_files=load_1m()
    signals, signal_ledger, detector_info=signal_detector(d)
    funding,n_funding=load_funding()
    ledger,month,summary=backtest(d,signals,funding)
    summary["timeframe"]="1H closed candle; next genuine 1m OPEN entry and 1m stop/TP"
    summary["raw_hourly_signals"]=summary.pop("raw_daily_signals")
    summary["strategy"]="Failed 1H breakout displacement order-block body; subsequent decisive failure; fixed 3R"
    summary["published_strategy_exact_replica"]=False
    summary["source_files"]=len(source_files)
    summary["funding_proxy_files"]=n_funding
    summary["detector"]=detector_info
    period=score_by_time(ledger)
    signal_ledger.to_csv(OUT/"breaker_signal_ledger.csv",index=False)
    ledger.to_csv(OUT/"trade_ledger.csv",index=False)
    month.to_csv(OUT/"monthly_ist.csv",index=False)
    period.to_csv(OUT/"period_stats.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    report=[
        "# 1H breaker-block failure proxy, fixed 3R, true 1m replay",
        "",
        "This is a fully defined stateful breaker-block **hypothesis** inspired by a published 1H 5R strategy. It is **NOT** the publisher's exact entry detector or same 5R target. Do not compare its numerical outcome to their 30.7% / PF1.75 as if identical.",
        "Rules: a displacement candle closes outside previous 12h high/low with a body >=0.5 ATR(14), after an opposite candle in past 3h; the last opposite candle BODY is the OB. Up to 48h later, a red close below bullish OB body bottom -0.10 ATR signals SHORT (opposite for LONG), given the previous close remained inside/above the boundary. Each block can fail once.",
        "Entries only from finished hourly bars whose **opening** time lies 13:00–17:00 UTC (17 exclusive); fill next available genuine 1m open. SL signal wick +/-0.25 ATR(14), TP exactly 3 initial R. No trailing or time stop, one open position. 1m same-bar tie stop priority.",
        "Modeled taker fee 0.05% each side + 18% GST, $5 adverse slip each side, funding historic rate proxy (not settled payments). $10,000 starting equity, 1% risk/entry, max 2x notional. Contract quantity continuous. IST month-end account equity marked at hypothetical closing cost.",
        "",
        "## Detection diagnostics",
        json.dumps(detector_info,indent=2),"",
        "## Trade-period outcomes",
        period.to_markdown(index=False),"",
        "## Monthly account PnL",
        month.to_markdown(index=False),"",
        "## All-period summary",
        json.dumps(summary,indent=2),"",
        "Caveats: raw 1m OHLC has no true bid/ask depth or intraminute tick path; funding rate proxy not settlement cashflow; 2026 already researched, not untouched validation. November incomplete.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("HOURLY_BREAKER_3R_DONE")
    print(json.dumps(detector_info))
    print(json.dumps({k:v for k,v in summary.items() if k!="detector"},indent=2))
    print(period.to_string(index=False))
    print(month.to_string(index=False))


if __name__=="__main__":
    main()
