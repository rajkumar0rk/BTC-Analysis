"""Offline operational smoke checks, no testnet/live keys or network required."""
import sys,time
from pathlib import Path
from types import SimpleNamespace
import pytest
APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))
from bot import Bot
from audit import sync_fills,summarize_fills
from store import Store
from web import backtest

def fake_config(tmp_path):
    return SimpleNamespace(state_dir=tmp_path,mode="demo",trading=False,
                           base_url="https://cdn-ind.testnet.deltaex.org",
                           key="",secret="",halt_on_liquidation=True,
                           margin=10,leverage=100,portfolio=100,buffer_pct=0.25,
                           poll=3,staleness=15)

def test_new_native_stop_is_journaled_then_verified(monkeypatch,tmp_path):
    bot=Bot(fake_config(tmp_path));bot.pid=27;bot.tick=.5
    active={"side":"buy","size":12,"stop":79750.,"entry":80000.,
            "best":80000.,"trail_active":False,"stop_id":None}
    bot.matching_orders=lambda:[]
    bot.place=lambda action,payload:{"id":123,"reduce_only":True}
    assert bot.protect(active) is False
    assert bot.db.get("active")["stop_id"]==123
    assert bot.protect(bot.db.get("active")) is False  # exchange eventual consistency
    bot.matching_orders=lambda:[{"id":123,"product_id":27,"side":"sell",
            "size":12,"stop_order_type":"stop_loss_order",
            "reduce_only":True,"stop_trigger_method":"mark_price","stop_price":"79750.0"}]
    assert bot.protect(bot.db.get("active")) is True
    bot.db.close()

def test_duplicate_native_stops_halts(monkeypatch,tmp_path):
    bot=Bot(fake_config(tmp_path));bot.pid=27;bot.tick=.5
    active={"side":"buy","size":10,"stop":79750.,"stop_id":1}
    good={"id":1,"product_id":27,"side":"sell","size":10,
          "stop_order_type":"stop_loss_order","reduce_only":True,
          "stop_trigger_method":"mark_price","stop_price":"79750"}
    bot.matching_orders=lambda:[good,{**good,"id":2}]
    with pytest.raises(RuntimeError,match="HALTED"):bot.protect(active)
    assert "Multiple" in bot.db.get("halted")
    bot.db.close()

def test_real_fill_estimate_and_dedup(tmp_path):
    db=Store(tmp_path)
    rows=[
       {"id":"a","created_at":"2026-11-19T12:00:00Z","product_id":27,
        "side":"buy","size":"12","price":"80000","commission":"0.5",
        "fill_type":"normal","meta_data":{}},
       {"id":"b","created_at":"2026-11-19T12:10:00Z","product_id":27,
        "side":"sell","size":"12","price":"80100","commission":"0.5",
        "fill_type":"normal","meta_data":{}}
    ]
    assert db.add_fills(rows)==["a","b"]
    assert db.add_fills(rows)==[]
    x=summarize_fills(db.fills(),0.001)
    assert x["fills"]==2
    assert x["gross_realized_usd"]==1.2
    assert x["exchange_reported_commissions_usd"]==1
    assert x["estimated_gst_usd"]==0.18
    assert x["estimated_net_before_funding_usd"]==0.02
    assert x["net_inventory_contracts"]==0
    db.close()

def test_liquidation_fill_triggers_halt(tmp_path):
    db=Store(tmp_path)
    db.set("first_started_us",1000000)
    row={"id":"liq1","created_at":"2026-11-19T12:00:00Z","product_id":27,
          "side":"sell","size":"10","price":"80000","commission":"1",
          "fill_type":"liquidation","meta_data":{"liquidation_fee_in_settling_asset":"0.10"}}
    class Fake:
        def fills_page(self,product_id,start_us,cursor=None):
            return {"result":[row],"meta":{"after":None}}
    assert sync_fills(Fake(),db,27,True)==1
    assert "liquidation" in db.get("halted").lower()
    assert sync_fills(Fake(),db,27,True)==0
    db.close()

def test_dashboard_backtest_guarded_comparison_available():
    x=backtest("history","threshold","guarded")
    if "error" in x:pytest.skip("guarded artifacts not yet committed")
    assert x["statistics"]["skipped_entries_liquidation_buffer"]>0
    assert x["statistics"]["assumed_liquidations"]==0
    y=backtest("history","threshold","original")
    assert y["statistics"]["assumed_liquidations"]>0
