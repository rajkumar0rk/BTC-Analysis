#!/usr/bin/env python3
"""Independent accounting audit of TSMOM component order fills; not a new strategy."""
import json
from pathlib import Path
import pandas as pd
ROOT=Path("analysis/trend_following_family_20261121/tsmom_frozen_2026_jan_sep")
FEE=.0005*1.18
for name in ("tsmom_90d_long_short",):
    orders=pd.read_csv(ROOT/f"{name}_orders.csv")
    monthly=pd.read_csv(ROOT/f"{name}_monthly.csv")
    reported=json.loads((ROOT/f"{name}_summary.json").read_text())
    assert len(orders)==reported["orders"] and len(monthly)==9
    assert abs(float(monthly.iloc[-1].end_nav)-100-reported["net_pct"])<1e-7
    assert abs(float(monthly.net_return_pct.add(100).div(100).prod())-float(monthly.iloc[-1].end_nav)/100)<1e-9
    assert abs(float(orders.fee.sum())-sum(abs(float(r.quantity_change))*float(r.price)*FEE for r in orders.itertuples()))<1e-8
    position=0.;basis=0.;entry_fees=0.;closed=[];cash=100.
    for row in orders.itertuples():
        delta=float(row.quantity_change);price=float(row.price);fee=float(row.fee)
        assert abs(fee-abs(delta)*price*FEE)<1e-8
        cash-=delta*price+fee
        if abs(position)<1e-11 or position*delta>0:
            basis+=delta*price;entry_fees+=fee;position+=delta
        else:
            closing=min(abs(delta),abs(position))
            proportion=closing/abs(position)
            allocated_basis=basis*proportion
            allocated_fee=entry_fees*proportion
            closing_delta=-closing*(1 if position>0 else -1)
            exit_fee=fee*closing/abs(delta)
            pnl=-closing_delta*price-allocated_basis-allocated_fee-exit_fee
            closed.append(dict(time_utc=row.time_utc,net_pnl=pnl,exit_fee=exit_fee,entry_fee=allocated_fee))
            basis-=allocated_basis;entry_fees-=allocated_fee;position+=closing_delta
            remaining=delta-closing_delta
            if abs(position)<1e-10:position=0.;basis=0.;entry_fees=0.
            if abs(remaining)>1e-10:
                assert position==0.
                position=remaining;basis=remaining*price;entry_fees+=fee-exit_fee
    assert abs(position)<1e-8 and abs(basis)<1e-6 and abs(entry_fees)<1e-6
    assert abs(cash-float(monthly.iloc[-1].end_nav))<1e-6,(name,cash,monthly.iloc[-1].end_nav)
    trades=pd.DataFrame(closed)
    wins=trades.loc[trades.net_pnl>0,"net_pnl"].sum()
    losses=-trades.loc[trades.net_pnl<0,"net_pnl"].sum()
    assert abs(trades.net_pnl.sum()-(cash-100))<1e-6
    trades.to_csv(ROOT/f"{name}_closed_trades_audit.csv",index=False)
    summary=dict(model=name,closed_exposure_events=len(trades),winning_events=int((trades.net_pnl>0).sum()),losing_events=int((trades.net_pnl<0).sum()),realized_pf=(wins/losses if losses else None),net_pnl=float(trades.net_pnl.sum()),total_fees=float(orders.fee.sum()),reconciled_final_nav=float(cash),note="Partial rebalance reductions are realized exposure events, not independent strategy round trips; 2025 warmup included; 2026 research-exposed.")
    (ROOT/f"{name}_accounting_audit.json").write_text(json.dumps(summary,indent=2))
    print("AUDIT_DONE",json.dumps(summary))
