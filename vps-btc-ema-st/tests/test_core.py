import os,sys,time
from pathlib import Path
import pandas as pd
import pytest
import requests
APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))
from signals import size_contracts,stop_safe,quantize_stop,closed_bars
from store import Store
from config import Config
from delta import Delta

def test_contract_sizing_fixed_10_usd_margin():
    assert size_contracts(80000,0.001,10,100)==12
    assert size_contracts(130000,0.001,10,100)==7
    assert size_contracts(80000,0.001,10,100)*0.001*80000<=1000

def test_stop_guard_at_100x():
    assert not stop_safe(80000,79200,"buy",100,0.0025,0.0025)
    assert stop_safe(80000,79750,"buy",100,0.0025,0.0025)
    assert not stop_safe(80000,80300,"buy",100,0.0025,0.0025)
    assert stop_safe(80000,80250,"sell",100,0.0025,0.0025)

def test_stop_round_toward_entry():
    assert quantize_stop(79950.21,.5,"buy")==79950.5
    assert quantize_stop(80050.21,.5,"sell")==80050.0

def test_candle_validation_completed_only():
    ts=int(time.time()//900)*900
    raw=[{"time":ts-900*(i+1),"open":1,"high":2,"low":1,"close":1.5,"volume":3}
         for i in range(110)]
    raw += [{"time":ts,"open":3,"high":3,"low":3,"close":3,"volume":3}]
    f=closed_bars(raw,ts+60)
    assert len(f)==110
    assert int(f.index[-1].timestamp())==ts-900
    raw.pop(30)
    with pytest.raises(ValueError,match="Missing"):closed_bars(raw,ts+60)

def test_store_persistence(tmp_path):
    a=Store(tmp_path);a.set("active",{"size":12})
    a.intent("test_oid","entry",{"size":12})
    a.event("INFO","test",ok=True);a.close()
    b=Store(tmp_path)
    assert b.get("active")=={"size":12}
    assert len(b.unresolved())==1
    b.intent_status("test_oid","exchange_confirmed")
    assert b.unresolved()==[]
    assert b.latest_events()[0]["data"]["ok"] is True
    b.close()

def test_live_guard_rejects_accidental_enable(monkeypatch,tmp_path):
    monkeypatch.setenv("MODE","live")
    monkeypatch.setenv("TRADING_ENABLED","true")
    monkeypatch.setenv("DELTA_LIVE_API_KEY","sample")
    monkeypatch.setenv("DELTA_LIVE_API_SECRET","sample")
    monkeypatch.setenv("ISOLATED_MARGIN_CONFIRMED","true")
    monkeypatch.delenv("LIVE_TRADING_ACK",raising=False)
    with pytest.raises(ValueError,match="Live trading is locked"):
        Config.read()

def test_api_hmac_exact_canonical_query(monkeypatch):
    from types import SimpleNamespace
    import hashlib,hmac
    cfg=SimpleNamespace(base_url="https://cdn-ind.testnet.deltaex.org",
        key="key",secret="secret")
    api=Delta(cfg)
    monkeypatch.setattr("delta.time.time",lambda:1730000000)
    captured=[]
    def fake(method,url,**kw):
        captured.append((method,url,kw))
        return SimpleNamespace(status_code=200,json=lambda:{"success":True,"result":[]})
    api.session.request=fake
    assert api.request("GET","/v2/orders",params={"product_ids":27,"states":"open,pending"},auth=True)==[]
    method,url,kw=captured[0]
    assert url.endswith("/v2/orders?product_ids=27&states=open%2Cpending")
    expected=hmac.new(b"secret",
      b"GET1730000000/v2/orders?product_ids=27&states=open%2Cpending",
      hashlib.sha256).hexdigest()
    assert kw["headers"]["signature"]==expected

def test_new_orders_have_no_implicit_post_retry(monkeypatch):
    from types import SimpleNamespace
    cfg=SimpleNamespace(base_url="https://cdn-ind.testnet.deltaex.org",
        key="key",secret="secret")
    api=Delta(cfg);calls=[]
    def fail(method,url,**kw):
        calls.append(1)
        raise requests.Timeout("timeout")
    api.session.request=fail
    from delta import DeltaError
    with pytest.raises(DeltaError):
        api.place_order({"product_id":27,"size":1,"side":"buy",
                         "order_type":"market_order"})
    assert len(calls)==1
