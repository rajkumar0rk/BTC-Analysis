"""Exact same-signal futures paper vs options paper comparison tests."""
import sys,time
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
import pytest

APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))
from futures_paper import FuturesPaperBot
from store import Store
import compare_web
from config import Config

def config(tmp_path,asset="BTC"):
    return SimpleNamespace(
       asset=asset,market="futures",futures_paper=True,trading=False,
       portfolio=100.,state_dir=tmp_path,mode="demo",
       symbol=asset+"USD",base_url="https://cdn-ind.testnet.deltaex.org",
       key="",secret="",margin=10.,leverage=100,max_trades=10,
       daily_loss_limit=10.,poll=3,staleness=15)

def quote(bid,ask,n=500):
    return {"bid":bid,"ask":ask,"bid_size":n,"ask_size":n,
            "timestamp":time.time(),"spread_pct":100*(ask-bid)/((ask+bid)/2)}

def test_futures_paper_uses_ask_bid_and_persists_exact_signal_bar(tmp_path):
    bot=FuturesPaperBot(config(tmp_path))
    bot.tick=.5;bot.value=.001;bot.product={"maintenance_margin":"0.25"}
    bot.quote=quote(79999,80000)
    s={"side":"buy","bar_ts":1795000000,
       "stop_distance_points":200,"signal_close":80000}
    bot.open_paper(s,80000,80000)
    p=bot.db.get("paper_position")
    assert p and p["entry"]==80000 and p["contracts"]==12
    assert p["signal_bar_ts"]==s["bar_ts"]
    assert p["margin_usd"]<=10
    assert p["stop"]==79800
    assert p["liq_proxy"]>79000
    bot.quote=quote(80200,80201)
    bot.close_paper("underlying_atr",80200)
    assert bot.db.get("paper_position") is None
    t=bot.db.paper_trades()[0]
    assert t["signal_bar_ts"]==s["bar_ts"]
    assert t["entry_price"]==80000 and t["exit_price"]==80200
    assert t["net_pnl_usd"]>0
    assert bot.db.get("paper_stats")["trades"]==1
    assert bot.db.get("paper_wallet")>100
    bot.db.close()

def test_futures_unguarded_paper_position_liquidates_before_atr_stop(tmp_path):
    bot=FuturesPaperBot(config(tmp_path))
    bot.tick=.5;bot.value=.001;bot.product={"maintenance_margin":"0.25"}
    bot.quote=quote(80000,80001)
    s={"side":"buy","bar_ts":1795000010,
       "stop_distance_points":1500,"signal_close":80000}
    bot.open_paper(s,80000,80000)
    p=bot.db.get("paper_position")
    assert p is not None
    # Entry guard stays OFF even though original ATR stop is beyond liquidation.
    # The NEW emergency exit, not entry rejection, is above the liq threshold.
    assert p["strategy_atr_stop"]<p["liq_proxy"]
    assert p["preliq_stop"]>p["liq_proxy"]
    assert p["stop"]==p["preliq_stop"]
    bot.quote=quote(79000,79002)
    bot.manage_paper(79000)
    assert bot.db.get("paper_position") is None
    t=bot.db.paper_trades()[0]
    assert t["reason"]=="liquidation_proxy"
    assert t["net_pnl_usd"]<0
    assert bot.db.get("paper_wallet")>=89 # isolated <=$10 plus entry fee
    bot.db.close()

def test_paired_comparison_counts_only_identical_underlying_signals(monkeypatch,tmp_path):
    btc_f=tmp_path/"BTC_futures";btc_o=tmp_path/"BTC_options"
    t={"symbol":"BTCUSD","asset":"BTC","side":"buy","contracts":12,
       "closed_at_utc":"2026-11-20T04:00:00Z","net_pnl_usd":2.,
       "gross_pnl_usd":2.5,"commissions_usd":.4,"gst_usd":.1,
       "reason":"underlying_atr","signal_bar_ts":123}
    o={**t,"symbol":"C-BTC-80000-241126","net_pnl_usd":3.,"gross_pnl_usd":3.5}
    fdb=Store(btc_f);odb=Store(btc_o)
    fdb.paper_transition(102,None,{"kind":"sell"},trade=t)
    odb.paper_transition(103,None,{"kind":"sell"},trade=o)
    fdb.close();odb.close()
    cfg=SimpleNamespace(asset="ETH",market="futures",mode="demo",
                        state_dir=tmp_path/"eth-futures",portfolio=100)
    monkeypatch.setattr(compare_web.Config,"read",lambda:cfg)
    monkeypatch.setattr(compare_web,"lane_state",
       lambda asset,market,mode:tmp_path/(asset+"_"+market))
    out=compare_web.paired_forward("BTC")
    assert out["matched_trades"]==1
    assert out["matched_futures_net_usd"]==2
    assert out["matched_options_net_usd"]==3
    assert out["pairs"][0]["difference_option_minus_futures_usd"]==1
    odb=Store(btc_o)
    trade2={**o,"signal_bar_ts":124,"net_pnl_usd":5}
    odb.paper_transition(108,None,{"kind":"sell"},trade=trade2)
    odb.close()
    out=compare_web.paired_forward("BTC")
    assert out["options_total_closed_paper_trades"]==2
    assert out["matched_trades"]==1

def test_futures_paper_disabled_when_exchange_orders_enabled(tmp_path):
    cfg=config(tmp_path)
    cfg.trading=True
    with pytest.raises(ValueError,match="TRADING_ENABLED=false"):
        FuturesPaperBot(cfg)
