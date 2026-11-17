#!/usr/bin/env python3
"""One-week forward BTC quote/basis feasibility study, not executable arbitrage.

Only real public REST observations taken after 2026-11-17. 15m samples cannot
replay the order queue or order fills. Comparisons are hypothetical 1 BTC-equivalent
two-venue bid/ask marking, not account profit. Actual Delta contract quantities,
USDT/USD conversion, funding settlements and capital movements aren't validated.
"""
from __future__ import annotations
import argparse
import bisect
import collections
import datetime as dt
import json
import math
from pathlib import Path
import statistics as stats

START=dt.datetime(2026,11,17,tzinfo=dt.timezone.utc)
MIN_SAMPLES=300
DELTA_TAKER_GST=0.0005*1.18
BINANCE_SPOT_TAKER_ASSUMED=0.001
PER_EXECUTION_SLIPPAGE_POINTS=5
SKEW_LIMIT_SECONDS=5
MAX_SAMPLE_GAP_MINUTES=35

def parse_time(s):
    return dt.datetime.fromisoformat(s.replace("Z","+00:00"))

def rounded(x):
    return round(float(x),4)

def med(xs):
    return rounded(stats.median(xs)) if xs else None

def load_records(folder,asof):
    all_rows=[]; errors=collections.Counter(); duplicated=0
    files=sorted(folder.glob("20??-??-??.jsonl"))
    for path in files:
        for lineno,line in enumerate(path.read_text(encoding="utf8").splitlines(),1):
            if not line.strip():continue
            try:
                row=json.loads(line)
                stamp=parse_time(row["captured_at_utc"])
                if not START<=stamp<=asof:continue
                all_rows.append((stamp,row))
            except (ValueError,KeyError,TypeError) as ex:
                errors["invalid_json_or_timestamp"]+=1
    all_rows.sort(key=lambda x:x[0])
    filtered=[]; seen=set()
    for stamp,row in all_rows:
        if stamp in seen:
            duplicated+=1
            continue
        seen.add(stamp)
        filtered.append((stamp,row))
        for k,v in row.get("errors",{}).items():
            errors[k]+=1
    return filtered,errors,duplicated,len(files)

def normalize(rows):
    valid=[]; skipped=collections.Counter()
    for when,row in rows:
        books=row.get("books") or {}
        d=books.get("delta_india_perp")
        b=books.get("binance_btcusdt_spot")
        if not d or not b:
            skipped["missing_two_books"]+=1
            continue
        try:
            dr=parse_time(d["received_at_utc"])
            br=parse_time(b["received_at_utc"])
            skew=abs((dr-br).total_seconds())
            if skew>SKEW_LIMIT_SECONDS:
                skipped["quote_receive_skew_gt_5s"]+=1
                continue
            db=float(d["best_bid"]); da=float(d["best_ask"])
            bb=float(b["best_bid"]); ba=float(b["best_ask"])
            if min(db,da,bb,ba)<=0 or db>=da or bb>=ba:
                skipped["invalid_bid_ask"]+=1
                continue
            valid.append(dict(
                time=when,delta_bid=db,delta_ask=da,spot_bid=bb,spot_ask=ba,
                skew_seconds=skew,
                delta_spread=da-db,spot_spread=ba-bb,
                indicative_open_premium=db-ba,
                funding_delta=bool((row.get("funding") or {}).get("delta_hourly_funding_rate_candles")),
                funding_binance=bool((row.get("funding") or {}).get("binance_usdm_btcusdt_published_funding_events"))
            ))
        except (KeyError,ValueError,TypeError):
            skipped["invalid_book_payload"]+=1
    return valid,skipped

def pair_pnl(a,b):
    # 1 BTC-equivalent: long spot now / short perp now; close both later.
    # Prices are USD versus USDT and therefore this is NOT a realizable hedge PnL.
    # For each venue, subtract taker fees on both opening/closing trade notionals.
    # Opening: buy spot at ask, sell perp at bid.
    # Closing: sell spot at bid, buy perp at ask.
    gross=(b["spot_bid"]-a["spot_ask"])+(a["delta_bid"]-b["delta_ask"])
    fee=(a["spot_ask"]+b["spot_bid"])*BINANCE_SPOT_TAKER_ASSUMED
    fee+=(a["delta_bid"]+b["delta_ask"])*DELTA_TAKER_GST
    # Fixed adverse slippage for 4 leg executions; not already in book prices.
    slip=4*PER_EXECUTION_SLIPPAGE_POINTS
    return gross,fee,slip,gross-fee-slip

def evaluate_pairs(rows,horizon_minutes):
    """No-overlap successive hypothetical quotes, not real fills.

    Each candidate opens at the first valid quote after previous pair's close.
    Close using the nearest quote to +15m or +60m within +/- 7m; exclude stale.
    """
    times=[x["time"] for x in rows]
    pairs=[]
    i=0
    tolerance=dt.timedelta(minutes=7)
    target=dt.timedelta(minutes=horizon_minutes)
    while i<len(rows):
        begin=rows[i]
        position=bisect.bisect_left(times,begin["time"]+target)
        candidates=[j for j in (position-1,position,position+1) if j>i and j<len(rows)]
        if not candidates:
            break
        j=min(candidates,key=lambda k:abs(times[k]-(begin["time"]+target)))
        if abs(times[j]-(begin["time"]+target))>tolerance:
            i+=1
            continue
        # Reject any data collection gap inside the hypothetical holding window
        if any((times[k+1]-times[k]).total_seconds()/60>MAX_SAMPLE_GAP_MINUTES
               for k in range(i,j)):
            i+=1
            continue
        end=rows[j]
        gross,fee,slip,net=pair_pnl(begin,end)
        pairs.append(dict(
            entry_utc=begin["time"].isoformat(),
            exit_utc=end["time"].isoformat(),
            gross_points_proxy=rounded(gross),
            fee_points_proxy=rounded(fee),
            slippage_points_proxy=rounded(slip),
            net_points_proxy=rounded(net),
            positive_after_cost=net>0
        ))
        i=j+1
    if not pairs:
        return dict(pairs=0, positive_pairs=0,positive_pct=None,mean_net_points_proxy=None,
                    median_net_points_proxy=None,median_fee_points_proxy=None,
                    mean_gross_points_proxy=None,example_first_pair=None)
    nets=[x["net_points_proxy"] for x in pairs]
    return dict(
        pairs=len(pairs),positive_pairs=sum(x>0 for x in nets),
        positive_pct=rounded(100*sum(x>0 for x in nets)/len(nets)),
        mean_net_points_proxy=rounded(stats.mean(nets)),
        median_net_points_proxy=med(nets),
        median_fee_points_proxy=med([x["fee_points_proxy"] for x in pairs]),
        mean_gross_points_proxy=rounded(stats.mean(x["gross_points_proxy"] for x in pairs)),
        example_first_pair=pairs[0],
    )

def calculate(folder,asof):
    records,errors,dupes,files=load_records(folder,asof)
    valid,skipped=normalize(records)
    gaps=[]
    for a,b in zip(records,records[1:]):
        minutes=(b[0]-a[0]).total_seconds()/60
        if minutes>MAX_SAMPLE_GAP_MINUTES:gaps.append(rounded(minutes))
    start=records[0][0] if records else START
    span_mins=max(0,(asof-start).total_seconds()/60)
    expected=round(span_mins/15)+1
    data_days=len(set(x[0].date() for x in records))
    premium=[x["indicative_open_premium"] for x in valid]
    delta_spread=[x["delta_spread"] for x in valid]
    spot_spread=[x["spot_spread"] for x in valid]
    result={
        "report_as_of_utc":asof.isoformat(),
        "source_first_utc":records[0][0].isoformat() if records else None,
        "source_last_utc":records[-1][0].isoformat() if records else None,
        "days_with_data":data_days,
        "file_count":files,"unique_snapshots":len(records),
        "expected_15min_snapshots_approx":expected,
        "snapshot_coverage_pct":rounded(min(100,100*len(records)/expected)) if expected else None,
        "duplicate_timestamps":dupes,"gaps_over_35_minutes":len(gaps),
        "max_gap_minutes":max(gaps) if gaps else 0,
        "valid_synchronized_quotes":len(valid),
        "invalid_quote_reasons":dict(skipped),
        "public_endpoint_errors":dict(errors),
        "median_delta_spread_points":med(delta_spread),
        "median_binance_spot_spread_points":med(spot_spread),
        "median_indicative_delta_bid_minus_spot_ask_points":med(premium),
        "indicative_positive_entry_premium_pct":
            rounded(100*sum(v>0 for v in premium)/len(premium)) if premium else None,
        "delta_funding_proxy_available":sum(x["funding_delta"] for x in valid),
        "binance_published_funding_available":sum(x["funding_binance"] for x in valid),
        "basis_pair_15m":evaluate_pairs(valid,15),
        "basis_pair_60m":evaluate_pairs(valid,60),
        "minimum_sample_goal_met":len(valid)>=MIN_SAMPLES,
        "realized_pnl":None,
        "market_making_profitability":None,
        "cashflow_from_funding_verified":False,
        "warnings":[
            "Binance USDT and Delta USD prices are not fungible; quote basis results are NOT executable.",
            "Fills, depth available at quoted size, Delta contracts, exchange access and capital transfer not verified.",
            "Delta funding is an hourly rate proxy; account-level settlement data unavailable.",
            "15-minute snapshots miss transient microstructure and maker order queue dynamics.",
            "Per-side Binance spot taker fee assumed 0.10%; Delta taker 0.05% plus 18% GST; slippage assumes 5 price points per execution.",
            "This analysis is only a first data-collection feasibility study; insufficient for claims of consistent monthly profits."
        ]
    }
    return result

def report(d):
    lines=["# Forward BTC Arbitrage Feasibility — 24 November 2026","",
        "**No strategy profit is claimed.** Based only on observed forward REST snapshots.",
        "The report is a 1-week feasibility check, not an executable market-making or arbitrage backtest.","",
        "## Data quality","",
        "| Metric | Result |","|---|---:|"]
    for name,k in [
       ("First snapshot","source_first_utc"),("Last snapshot","source_last_utc"),
       ("Unique snapshots","unique_snapshots"),("Approx expected snapshots","expected_15min_snapshots_approx"),
       ("Coverage %","snapshot_coverage_pct"),("Quotes from both exchanges with <=5s receive skew","valid_synchronized_quotes"),
       ("Gaps >35m","gaps_over_35_minutes"),("Maximum gap (min)","max_gap_minutes"),
       ("Minimum 300 synchronized quotes reached","minimum_sample_goal_met"),
       ("Delta funding rate available","delta_funding_proxy_available"),
       ("Binance published funding available","binance_published_funding_available")]:
        lines.append(f"| {name} | {d[k]} |")
    lines+=["","## Quote and indicative basis","",
        "| Measurement | Result |","|---|---:|",
        f"| Median Delta bid/ask spread (points) | {d['median_delta_spread_points']} |",
        f"| Median Binance spot bid/ask spread (points) | {d['median_binance_spot_spread_points']} |",
        f"| Median Delta bid minus Binance ask (points) | {d['median_indicative_delta_bid_minus_spot_ask_points']} |",
        f"| Entry quotes with Delta bid above Binance ask (%) | {d['indicative_positive_entry_premium_pct']} |",
        "","## Hypothetical two-leg basis marks after modeled taker fees","",
        "LONG Binance spot / SHORT Delta perp; entry on one snapshot, exit at nearest later snapshot.",
        "Greedy nonoverlapping sampled pairs; **not trade fills, not realized P&L**.",
        "| Marking window | Paired snapshots | Positive after model costs | Mean net points proxy | Median fee points proxy |",
        "|---|---:|---:|---:|---:|"]
    for name,key in [("15 minutes","basis_pair_15m"),("60 minutes","basis_pair_60m")]:
        p=d[key]
        lines.append(f"| {name} | {p['pairs']} | {p['positive_pairs']} ({p['positive_pct']}%) | {p['mean_net_points_proxy']} | {p['median_fee_points_proxy']} |")
    lines+=["","## Collection / modeling issues",""]
    for k,v in sorted(d["public_endpoint_errors"].items()):
        lines.append(f"- API error ({k}): {v} snapshot(s)")
    for k,v in sorted(d["invalid_quote_reasons"].items()):
        lines.append(f"- Quote excluded ({k}): {v} snapshot(s)")
    if not d["minimum_sample_goal_met"]:
        lines.append("- **Data threshold not met (300 synchronized samples)**; do not interpret small sample rates.")
    lines+=["","## Decision","",
        "**Do not deploy arbitrage or maker trading based on these snapshots.**",
        "We can inspect whether quoted basis merits higher-frequency WebSocket collection.",
        "Market making requires depth/order-flow/trade ticks with live queue/fill modeling.",
        "Funding-based carry requires actual settlement cashflows and hedging/financing reconciliation.",
        "No 2025 L2 backfill, no 2026 directional strategy, and no guarantee of a positive month.","",
        "## Modeling assumptions",""]
    lines.extend("- "+x for x in d["warnings"])
    return "\n".join(lines)+"\n"

def self_test():
    a={"spot_ask":100,"spot_bid":99.9,"delta_bid":100.2,"delta_ask":100.3}
    b={"spot_bid":100.1,"delta_ask":100.2}
    gross,fee,slip,net=pair_pnl(a,b)
    assert abs(gross-0.1)<1e-8
    assert abs(fee-((100+100.1)*0.001+(100.2+100.2)*0.00059))<1e-8
    assert slip==20 and net<0
    print("SELF_TEST_PASSED")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--snapshots",type=Path,default=Path("analysis/forward_microstructure/snapshots"))
    p.add_argument("--out",type=Path,default=Path("analysis/forward_microstructure/first_review_2026-11-24"))
    p.add_argument("--asof-utc",default="2026-11-24T05:00:00Z")
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    if args.self_test:
        self_test();return
    asof=parse_time(args.asof_utc)
    if asof<START:raise ValueError("Analysis time before collection start")
    d=calculate(args.snapshots,asof)
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"summary.json").write_text(json.dumps(d,indent=2)+"\n",encoding="utf8")
    (args.out/"REPORT.md").write_text(report(d),encoding="utf8")
    print(report(d))
    print("WROTE",args.out)

if __name__=="__main__":
    main()
