#!/usr/bin/env python3
"""Pre-registered feasibility test of BTC maker spread capture; NOT a fill backtest."""
import gzip,json,statistics,math,hashlib,csv
from pathlib import Path
from collections import Counter,defaultdict
ROOT=Path("data/delta_india/BTCUSD/institutional/live_snapshots")
OUT=Path("analysis/daily_maker_spread_feasibility_20261119_v2")
OUT.mkdir(parents=True,exist_ok=True)
# Exchange maker fee model 0.02% each side, 18% GST; verify current schedule before execution.
FEE_SIDE=.0002*1.18
# Gross half-spread is a one-sided execution advantage; for a complete round trip
# across both sides, maximum attainable spread is quoted full spread, NOT twice spread.
def levels(v):
    result=[]
    for x in v:
        if isinstance(x,dict):
            p=x.get("price"); q=x.get("size",x.get("quantity",x.get("qty")))
        elif isinstance(x,(list,tuple)) and len(x)>=2:p,q=x[0],x[1]
        else:continue
        try:
            p=float(p);q=float(q)
            if math.isfinite(p) and math.isfinite(q) and p>0 and q>0:result.append((p,q))
        except (TypeError,ValueError):pass
    return result
records=[];errors=Counter();hashes=[]
for f in sorted(ROOT.glob("20??-??-??.jsonl.gz")):
    hashes.append({"path":str(f),"sha256":hashlib.sha256(f.read_bytes()).hexdigest()})
    try:
        with gzip.open(f,"rt") as h:
            for line in h:
                try:
                    z=json.loads(line);book=z.get("data",{}).get("level2_book",{})
                    bids=levels(book.get("buy",[]));asks=levels(book.get("sell",[]))
                    if not bids or not asks:errors["missing_valid_bid_ask"]+=1;continue
                    bid=max(p for p,q in bids);ask=min(p for p,q in asks)
                    if bid>=ask:errors["crossed_or_locked"]+=1;continue
                    mid=(bid+ask)/2
                    spread_bps=(ask-bid)/mid*10000
                    cost_bps=2*FEE_SIDE*10000
                    # Zero adverse selection and perfect fills is NOT executable:
                    # upper bound only. No markout or queue evidence.
                    records.append({"time":z.get("requested_utc"),"day":str(z.get("requested_utc",""))[:10],"bid":bid,"ask":ask,"mid":mid,"spread_bps":spread_bps,"two_maker_fee_gst_bps":cost_bps,"perfect_two_side_capture_bps":spread_bps-cost_bps,"top_bid_qty":next((q for p,q in bids if p==bid),None),"top_ask_qty":next((q for p,q in asks if p==ask),None)})
                except Exception as e:errors["parse_row_"+type(e).__name__]+=1
    except Exception as e:errors["read_file_"+type(e).__name__]+=1
if not records:raise RuntimeError("No usable historical L2 snapshots; no synthetic fills")
with (OUT/"quote_observations.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
byday=defaultdict(list)
for x in records:byday[x["day"]].append(x)
def quantile(x,q):
    s=sorted(x);return s[min(len(s)-1,max(0,int((len(s)-1)*q)))]
daily=[]
for d,rows in sorted(byday.items()):
    s=[x["spread_bps"] for x in rows];e=[x["perfect_two_side_capture_bps"] for x in rows]
    daily.append({"day":d,"snapshots":len(rows),"median_spread_bps":statistics.median(s),"p90_spread_bps":quantile(s,.9),"positive_perfect_capture_snapshots":sum(z>0 for z in e),"median_perfect_capture_bps":statistics.median(e)})
with (OUT/"daily_quote_diagnostic.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(daily[0]));w.writeheader();w.writerows(daily)
s=[x["spread_bps"] for x in records];p=[x["perfect_two_side_capture_bps"] for x in records]
summary={"hypothesis":"passive market making may earn spread; first test whether gross full spread even covers both maker fees + GST","status":"FEASIBILITY_ONLY_NOT_EXECUTABLE_BACKTEST","symbol":"BTCUSD","source":"Delta India public REST L2 snapshots; NOT a historical continuous L2 stream","observations":len(records),"observed_days":len(daily),"first":records[0]["time"],"last":records[-1]["time"],"median_spread_bps":statistics.median(s),"p90_spread_bps":quantile(s,.9),"fee_roundtrip_bps":2*FEE_SIDE*10000,"median_ideal_net_bps":statistics.median(p),"pct_snapshots_positive_ideal_net":100*sum(x>0 for x in p)/len(p),"unusable":dict(errors),"source_sha256":hashes,"unavailable":["true queue position","actual passive fills","trade sequence between snapshots","adverse selection and future markout at seconds","order cancellation latency","portfolio margin/liquidation reconstruction","complete ETH L2 history"],"calendar_day_net_returns":"NOT COMPUTABLE from sparse snapshots; do not invent positive/negative/no-trade counts","2025_2026_annual_returns":"NOT COMPUTABLE","monthly_net_returns":"NOT COMPUTABLE","funding":"Not applicable to unfilled quote study","slippage":"No filled orders; zero slippage is only an optimistic theoretical upper bound","interpretation":"Even a positive ideal quote-capture bound is NOT an executable strategy; no user notification."}
(OUT/"quality_and_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
(OUT/"REPORT.md").write_text("# BTC maker spread-capture upper-bound audit\n\nPre-registered test: maximum theoretical two-sided spread capture at each available snapshot minus two maker fees and 18% GST, no other profit assumption. The quoted spread is NOT an earned spread. Historical point-in-time snapshots are sparse and cannot establish passive fill probability, adverse selection, queue position, funding or realistic PnL. No ETH equivalent. Never call this a backtest or annual profitability evidence.\n\n"+json.dumps({k:v for k,v in summary.items() if k!="source_sha256"},indent=2)+"\n")
print("FEASIBILITY_SUMMARY",json.dumps({k:v for k,v in summary.items() if k!="source_sha256"}))
