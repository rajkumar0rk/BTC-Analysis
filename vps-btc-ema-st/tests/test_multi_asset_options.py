"""Quote-based options paper and four-lane comparison tests (offline only)."""
import inspect,sys,time
from datetime import datetime,timedelta,timezone
from pathlib import Path
from types import SimpleNamespace
import pytest

APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))
from options_paper import (
    OptionsPaperBot,chain_side,good_quote,fee_usd,
    quantity_for_budget,validate_contract,paper_stats)
from signals import trailing_points,signal
from store import Store
from config import Config,lane_state
from bot import Bot
from compare_web import historical,compare

def fakecfg(tmp_path,asset="BTC"):
    return SimpleNamespace(asset=asset,market="options",trading=False,
        state_dir=tmp_path,mode="demo",portfolio=100.0,
        symbol=asset+"USD",base_url="https://cdn-ind.testnet.deltaex.org",
        key="",secret="",option_premium=10.0,
        option_min_dte_hours=36.0,option_max_dte_days=14.0,
        option_spread_max_pct=10.0,option_fee_rate=.0001,
        option_fee_cap_pct=3.5,staleness=15,poll=3,
        max_trades=10,daily_loss_limit=10)

def fakequote(bid=995,ask=1000,size=50,now=None):
    return {"timestamp":time.time() if now is None else now,
        "quotes":{"best_bid":str(bid),"best_ask":str(ask),
                  "bid_size":str(size),"ask_size":str(size)}}

def test_futures_eth_trailing_rescaling_and_btc_unchanged():
    assert trailing_points("BTC",80000)==(150,50)
    assert trailing_points("ETH",4000)==(7.5,2.5)
    assert trailing_points("ETH",2000)==(3.75,1.25)
    with pytest.raises(ValueError):trailing_points("BTC2",2000)

def test_option_bid_ask_source_and_stale_rejection():
    t=fakequote()
    assert good_quote(t,time.time(),15)["bid"]==995
    assert good_quote(t,time.time()+30,15) is None
    assert good_quote(fakequote(800,1000),time.time(),15,max_spread_pct=10) is None
    assert good_quote(fakequote(size=0),time.time(),15) is None
    assert good_quote(fakequote(size=2),time.time(),15,required_size=3,exit_only=True) is None
    assert good_quote(fakequote(size=3),time.time(),15,required_size=3,exit_only=True)

def test_call_put_mapping_and_budget_after_fees():
    assert chain_side("BTC","buy")=="C"
    assert chain_side("ETH","sell")=="P"
    assert fee_usd(80000,1000,1,.001,.0001,3.5)==.008
    lots=quantity_for_budget(1000,80000,.001,10,.0001,3.5)
    assert lots==9
    total=1000*.001*lots+fee_usd(80000,1000,lots,.001,.0001,3.5)*1.18
    assert total<=10
    assert quantity_for_budget(2000,80000,.01,10,.0001,3.5)==0

def test_option_product_validation_from_exchange_metadata():
    exp=(datetime.now(timezone.utc)+timedelta(days=4))
    s="C-BTC-80000-"+exp.strftime("%d%m%y")
    p={"symbol":s,"id":898,"contract_type":"call_options",
       "state":"live","trading_status":"operational",
       "contract_value":"0.001","strike_price":"80000",
       "settlement_time":exp.isoformat(),"tick_size":"0.5"}
    x=validate_contract(p,"C","BTC",s,time.time(),36,14)
    assert x["id"]==898 and x["contract_value"]==.001
    assert validate_contract(p,"P","BTC",s,time.time(),36,14) is None
    assert validate_contract({**p,"state":"expired"},"C","BTC",s,time.time(),36,14) is None
    assert validate_contract({**p,"settlement_time":(datetime.now(timezone.utc)+timedelta(hours=3)).isoformat()},
        "C","BTC",s,time.time(),36,14) is None

def test_atomic_cash_position_paper_trade_and_quotes(tmp_path):
    db=Store(tmp_path)
    db.paper_transition(90,{"symbol":"C-BTC-test"},{"kind":"buy"})
    db.sample_quote(1,time.time(),995,1000,80000,{"best_bid":995})
    t={"closed_at_utc":"2026-11-20T00:00:00Z","symbol":"C-BTC-test",
       "asset":"BTC","side":"buy","contracts":1,
       "gross_pnl_usd":1,"commissions_usd":.1,"gst_usd":.018,
       "net_pnl_usd":.882,"reason":"underlying_atr_stop"}
    db.paper_transition(100.882,None,{"kind":"sell"},trade=t,
                        stats=paper_stats([t]))
    assert db.get("paper_wallet")==100.882
    assert db.get("paper_position") is None
    assert len(db.paper_trades())==1
    assert db.get("paper_stats")["trades"]==1
    db.close()

def test_options_paper_open_and_close_using_fresh_quote(tmp_path):
    cfg=fakecfg(tmp_path)
    bot=OptionsPaperBot(cfg)
    exp=(datetime.now(timezone.utc)+timedelta(days=4))
    sym="C-BTC-80000-"+exp.strftime("%d%m%y")
    ticker={**fakequote(), "symbol":sym,"strike_price":"80000","contract_type":"call_options"}
    product={"id":999,"symbol":sym,"contract_type":"call_options","state":"live",
        "trading_status":"operational","contract_value":"0.001",
        "strike_price":"80000","settlement_time":exp.isoformat(),"tick_size":"0.5"}
    class Fake:
        def option_chain(self,asset):return [ticker]
        def option_product(self,symbol):assert symbol==sym;return product
        def ticker(self,symbol):
            if symbol==sym:return {**fakequote(bid=1100,ask=1110),"symbol":sym}
            return {"timestamp":time.time(),"close":80000,"mark_price":80000}
    bot.api=Fake()
    bot.entry({"side":"buy","bar_ts":int(time.time())-900,
               "stop_distance_points":100,"signal_close":80000},80000,80000)
    active=bot.db.get("paper_position")
    assert active and active["option_type"]=="CALL" and active["contracts"]==9
    assert active["stop"]==79900
    assert bot.db.get("paper_wallet")<100
    bot.close("underlying_atr_stop",80100)
    assert bot.db.get("paper_position") is None
    stats=bot.db.get("paper_stats")
    assert stats["trades"]==1 and stats["net_profit_usd"]>0
    assert bot.db.paper_trades()[0]["symbol"]==sym
    bot.db.close()

def test_unquotable_exit_does_not_invent_paper_execution(tmp_path):
    bot=OptionsPaperBot(fakecfg(tmp_path))
    bot.db.paper_transition(90,{"symbol":"C-BTC-80000-260126",
        "side":"buy","contracts":2,"contract_value":.001,
        "expiry_ts":time.time()+86400},"kind" if False else {"kind":"buy"})
    bot.api=SimpleNamespace(ticker=lambda sym:fakequote(bid=0,ask=0,size=0))
    bot.close("underlying_atr_stop",80000)
    assert bot.db.get("paper_position") is not None
    assert bot.db.get("paper_exit_pending")=="underlying_atr_stop"
    assert bot.db.paper_trades()==[]
    bot.db.close()

def test_no_liquidation_entry_rejection_in_original_futures_bot():
    assert "target_stop_guard" not in inspect.getsource(Bot.on_bar)
    assert "target_stop_guard" not in inspect.getsource(Bot.reconcile)

def test_historical_btc_eth_comparison_and_no_fabricated_options():
    btc=historical("BTC","history","offer","threshold")
    eth=historical("ETH","history","offer","threshold")
    assert btc["available"] and eth["available"]
    assert btc["statistics"]["assumed_liquidations"]>0
    assert eth["statistics"]["assumed_liquidations"]>0
    assert btc["statistics"]["ending_portfolio_usd"]>100
    assert eth["statistics"]["ending_portfolio_usd"]>100
    assert historical("BTC","history","nooffer","threshold")["available"] is False

def test_options_never_order_write_even_if_live(monkeypatch,tmp_path):
    for key in ("DELTA_DEMO_API_KEY","DELTA_DEMO_API_SECRET",
                "DELTA_LIVE_API_KEY","DELTA_LIVE_API_SECRET"):
        monkeypatch.setenv(key,"")
    monkeypatch.setenv("ASSET","ETH")
    monkeypatch.setenv("MARKET","options")
    monkeypatch.setenv("MODE","live")
    monkeypatch.setenv("TRADING_ENABLED","true")
    with pytest.raises(ValueError,match="PAPER"):
        Config.read()
    monkeypatch.setenv("TRADING_ENABLED","false")
    cfg=Config.read()
    assert cfg.market=="options" and not cfg.trading and cfg.mode=="live"
