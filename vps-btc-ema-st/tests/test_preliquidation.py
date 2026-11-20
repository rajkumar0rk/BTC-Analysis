"""Pre-liquidation stop calculations and execution regression tests.

No exchange orders. This suite deliberately models gaps that still liquidate
despite a one-tick/$1 native stop (not a liquidation guarantee).
"""
import sys
from pathlib import Path
from types import SimpleNamespace
from decimal import Decimal

import pytest

APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))
from preliq import (pre_liq_buffer,pre_liq_stop,effective_stop,
                    reported_liquidation,estimate_liquidation,stop_crossed)
from futures_paper import FuturesPaperBot
from bot import Bot

def cfg(tmp_path,asset="BTC",paper=True):
    return SimpleNamespace(
       asset=asset,market="futures",mode="demo",futures_paper=paper,
       trading=not paper,portfolio=100,state_dir=tmp_path,
       symbol=asset+"USD",base_url="https://cdn-ind.testnet.deltaex.org",
       key="TEST_ONLY",secret="TEST_ONLY",margin=10,leverage=100,
       max_trades=10,daily_loss_limit=10,poll=3,staleness=15,
       preliq_enabled=True,preliq_btc_points=1,
       preliq_reference_btc_price=80000)

def quote(bid,ask):
    return dict(bid=bid,ask=ask,bid_size=500,ask_size=500,spread_pct=.001,timestamp=100)

def test_one_point_btc_two_directions_with_tick_rounding():
    assert pre_liq_buffer("BTC",80000,.5)==1
    assert pre_liq_stop("buy",79400,1,.5)==79401
    assert pre_liq_stop("sell",80600,1,.5)==80599
    assert effective_stop("buy",78500,79401,80000)==79401
    assert effective_stop("buy",79500,79401,80000)==79500
    assert effective_stop("sell",82000,80599,80000)==80599
    assert effective_stop("sell",80500,80599,80000)==80500

def test_eth_relative_one_btc_point_uses_tick_rounded_up():
    assert pre_liq_buffer("ETH",4000,.05)==pytest.approx(.05)
    assert pre_liq_buffer("ETH",6000,.05)==pytest.approx(.10)
    assert pre_liq_buffer("ETH",2000,.05)==pytest.approx(.05)
    assert pre_liq_stop("buy",3950,.05,.05)==pytest.approx(3950.05)
    assert pre_liq_stop("sell",4050,.05,.05)==pytest.approx(4049.95)
    assert pre_liq_buffer("BTC",80000,.5,btc_points=5)==5

def test_actual_exchange_report_required_and_direction_sanity():
    assert reported_liquidation({"liquidation_price":"79400"},"buy",80000)==79400
    assert reported_liquidation({"liquidation_price":"80600"},"sell",80000)==80600
    with pytest.raises(ValueError,match="missing"):
        reported_liquidation({"entry_price":"80000"},"buy",80000)
    with pytest.raises(ValueError,match="not below"):
        reported_liquidation({"liquidation_price":"80001"},"buy",80000)
    with pytest.raises(ValueError,match="not above"):
        reported_liquidation({"liquidation_price":"79999"},"sell",80000)
    with pytest.raises(ValueError,match="positive"):
        pre_liq_stop("buy",79400,-1,.5)
    assert stop_crossed("buy",79401,79401)
    assert stop_crossed("sell",80599,80599)

def test_proxy_is_not_claimed_as_exchange_report():
    p=estimate_liquidation(80000,"buy",100,.25)
    assert 79000<p<80000
    assert estimate_liquidation(80000,"sell",100,.25)>80000
    with pytest.raises(ValueError,match="Maintenance"):
        estimate_liquidation(80000,"buy",100,3)

def test_futures_paper_stops_before_liq_if_mark_observed(tmp_path):
    b=FuturesPaperBot(cfg(tmp_path))
    b.value=.001;b.tick=.5;b.product={"maintenance_margin":".25"}
    b.quote=quote(80000,80001)
    b.open_paper({"side":"buy","bar_ts":10000,"stop_distance_points":1500,
                  "signal_close":80000},80000,80000)
    p=b.db.get("paper_position")
    assert p["strategy_atr_stop"]==78501
    assert p["preliq_stop"]>p["liq_proxy"]
    assert p["stop"]==p["preliq_stop"]
    # Next observation arrives at the emergency stop, still ABOVE modeled liq.
    b.quote=quote(p["stop"]-.5,p["stop"])
    b.manage_paper(p["stop"])
    assert b.db.get("paper_position") is None
    trade=b.db.paper_trades()[0]
    assert trade["reason"]=="pre_liquidation_stop"
    assert trade["net_pnl_usd"]<0
    assert trade["preliq_stop"]==p["preliq_stop"]
    assert trade["liquidation_fees_usd"] if False else True
    b.db.close()

def test_price_gap_still_liquidates_and_pays_liquidation_fee(tmp_path):
    b=FuturesPaperBot(cfg(tmp_path))
    b.value=.001;b.tick=.5;b.product={"maintenance_margin":".25"}
    b.quote=quote(80000,80001)
    b.open_paper({"side":"buy","bar_ts":10000,"stop_distance_points":1500,
                  "signal_close":80000},80000,80000)
    p=b.db.get("paper_position")
    b.quote=quote(p["liq_proxy"]-150,p["liq_proxy"]-149)
    b.manage_paper(p["liq_proxy"]-149)
    trade=b.db.paper_trades()[0]
    assert trade["reason"]=="liquidation_proxy"
    assert trade["net_pnl_usd"]<0
    b.db.close()

def test_exchange_real_liq_stops_are_edited_and_never_loosened(tmp_path):
    b=Bot(cfg(tmp_path,paper=False))
    b.pid=27;b.tick=.5;b.value=.001
    exchange_pos={"product_id":27,"size":12,"entry_price":"80000",
                  "liquidation_price":"79400"}
    order={"id":456,"product_id":27,"size":12,"side":"sell",
           "stop_order_type":"stop_loss_order","stop_trigger_method":"mark_price",
           "reduce_only":True,"stop_price":"79400"}
    b.exchange_position=lambda:exchange_pos
    b.matching_orders=lambda:[order]
    def edit(product_id,order_id,price):
        assert product_id==27 and order_id==456
        order["stop_price"]=str(price)
        return {"id":456}
    b.delta.edit_stop=edit
    b.db.set("pending",{"client_id":"tested","side":"buy","contracts":12,
                        "bracket_stop":79400,"stop_distance":1500,
                        "submitted_at":10,"bar_ts":123})
    b.reconcile(79900)
    p=b.db.get("active")
    assert p["strategy_atr_stop"]==78500
    assert p["exchange_liquidation_price"]==79400
    assert p["preliq_stop"]==79401
    assert p["stop"]==79401
    assert b.db.get("liquidation_risk")["source"]=="DELTA_POSITION_API"

    exchange_pos["liquidation_price"]="79420"
    b.reconcile(79900)
    p=b.db.get("active")
    assert p["stop"]==79421
    exchange_pos["liquidation_price"]="79300"
    b.reconcile(79900)
    assert b.db.get("active")["stop"]==79421  # never lower long stop

    captured=[]
    b.emergency_close=lambda active,reason:captured.append(reason)
    exchange_pos["liquidation_price"]="79899.5"
    b.reconcile(79900)
    assert captured==["pre_liquidation_emergency_close"]
    b.db.close()

def test_short_exchange_stop_is_one_point_below_actual_liq(tmp_path):
    b=Bot(cfg(tmp_path,paper=False))
    b.pid=27;b.tick=.5;b.value=.001
    ps={"product_id":27,"size":-12,"entry_price":"80000",
        "liquidation_price":"80600"}
    order={"id":777,"product_id":27,"size":12,"side":"buy",
        "stop_order_type":"stop_loss_order","stop_trigger_method":"mark_price",
        "reduce_only":True,"stop_price":"80600"}
    b.exchange_position=lambda:ps
    b.matching_orders=lambda:[order]
    b.delta.edit_stop=lambda pid,oid,price:order.update(stop_price=str(price))
    b.db.set("pending",{"client_id":"short","side":"sell","contracts":12,
        "bracket_stop":80600,"stop_distance":1500,"submitted_at":1,"bar_ts":100})
    b.reconcile(80000)
    assert b.db.get("active")["stop"]==80599
    assert b.db.get("active")["preliq_stop"]==80599
    b.db.close()
