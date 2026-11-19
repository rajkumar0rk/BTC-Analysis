"""Demo/live exchange fill reconciliation for READ-ONLY P&L attribution.

Commission is taken from authenticated Delta fills. GST is a modeled 18%.
Funding, transfers, trading credits and wallet adjustments are NOT attributed.
Net here is therefore an ESTIMATE, not settlement-grade accounting.
"""
from datetime import datetime,timezone
import time,math

def sync_fills(exchange,store,product_id,halt_after_liq=True):
    now_us=int(time.time()*1_000_000)
    last_us=store.get("fills_last_checked_us")
    if last_us is None:
        # Only include fills from app startup; dedicated account recommended.
        first=store.get("first_started_us")
        if first is None:
            first=now_us
            store.set("first_started_us",first)
        begin=max(0,int(first)-5*60*1_000_000)
    else:
        # overlap history by 10 minutes to cover indexing delay;
        # deduplicate by actual Delta fill UUID in SQLite.
        begin=max(0,int(last_us)-10*60*1_000_000)
    cursor=None;seen=set();inserted=0;liq_new=0
    for page_number in range(40):
        resp=exchange.fills_page(product_id,begin,cursor)
        rows=resp.get("result")
        if not isinstance(rows,list):
            raise ValueError("Malformed fills response; refusing to infer")
        for row in rows:
            if int(row.get("product_id",-1))!=int(product_id):
                raise ValueError("Received fill for wrong instrument")
            if not all(k in row for k in ("id","price","size","side","created_at")):
                raise ValueError("Missing critical fill fields")
        n=store.add_fills(rows)
        inserted+=n
        # Check fill type even when repeated API pages contain duplicates;
        # stop only on liquidation fills after the first app start.
        if n and halt_after_liq:
            for row in rows:
                if row.get("fill_type")=="liquidation":
                    created=row.get("created_at")
                    try:
                        occurred=datetime.fromisoformat(str(created).replace("Z","+00:00")).timestamp()*1e6
                    except (ValueError,TypeError):
                        occurred=0
                    if occurred>=store.get("first_started_us",0):
                        liq_new+=1
        if not len(rows) or len(rows)<50:
            break
        after=(resp.get("meta") or {}).get("after")
        if not after:
            break
        if after in seen:
            raise ValueError("Fill cursor repeated; reconcile manually")
        seen.add(after);cursor=after
    else:
        raise ValueError("Fill history exceeded safe pagination cap")
    store.set("fills_last_checked_us",now_us)
    store.set("fills_synced_at",datetime.now(timezone.utc).isoformat())
    if inserted:store.event("INFO","exchange_fills_synced",new_fills=inserted)
    if liq_new:
        store.event("ERROR","exchange_liquidation_fill",count=liq_new)
        store.set("halted","New exchange liquidation fill found; inspect risk and manual restart")
    return inserted

def summarize_fills(rows,contract_value=0.001,gst_fraction=0.18):
    """Average-cost matched gross P&L; independent of theoretical order fills.

    Single symbol, integer contracts, one directional position. Unmatched
    opens remain inventory; fees are debited on every fill, including opens.
    """
    qty=0.
    avg=0.
    gross=0.
    commissions=0.
    penalty=0.
    liquidations=0
    for r in rows:
        size=float(r["size"]);price=float(r["price"])
        direction=1 if r["side"]=="buy" else -1
        signed=direction*size
        if size<=0 or not math.isfinite(price) or price<=0:
            raise ValueError("Invalid stored fill")
        commissions+=float(r["commission"])
        penalty+=float(r["liquidation_charge"])
        liquidations+=r["fill_type"]=="liquidation"
        if not qty or qty*signed>0:
            newqty=qty+signed
            avg=(abs(qty)*avg+abs(signed)*price)/abs(newqty)
            qty=newqty
        else:
            close=min(abs(qty),abs(signed))
            gross+=close*contract_value*(price-avg)*(1 if qty>0 else -1)
            if abs(signed)<abs(qty):
                qty+=signed
            elif abs(signed)==abs(qty):
                qty=0.;avg=0.
            else:
                qty+=signed;avg=price
    gst=commissions*gst_fraction
    net=gross-commissions-gst-penalty
    return dict(
        fills=len(rows),gross_realized_usd=round(gross,4),
        exchange_reported_commissions_usd=round(commissions,4),
        estimated_gst_usd=round(gst,4),
        exchange_reported_liquidation_charges_usd=round(penalty,4),
        estimated_net_before_funding_usd=round(net,4),
        net_inventory_contracts=round(qty,6),
        average_open_entry_price=round(avg,2) if qty else None,
        liquidation_fills=int(liquidations),
        accounting_note="Approximation from exchange fills; GST assumed, funding/credits/transfers excluded")
