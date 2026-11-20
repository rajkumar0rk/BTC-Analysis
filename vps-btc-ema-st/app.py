#!/usr/bin/env python3
"""Per-lane commands: doctor, run, once, serve, backtest, status, audit, reconcile."""
import argparse,json,subprocess,sys,time
from config import Config,ROOT
from delta import Delta
from store import Store
from audit import sync_fills,summarize_fills
from signals import closed_bars
from bot import Bot,position_size
from options_paper import OptionsPaperBot,good_quote

def doctor(cfg):
    print("ENVIRONMENT",cfg.mode,"HOST",cfg.base_url,"ASSET",cfg.asset,"MARKET",cfg.market)
    print("ORDER WRITES",cfg.trading,"OPTIONS PAPER ONLY",cfg.market=="options")
    d=Delta(cfg)
    p=d.product(cfg.symbol)
    if p.get("symbol")!=cfg.symbol or p.get("contract_type")!="perpetual_futures":
        raise RuntimeError("Wrong underlying future: "+cfg.symbol)
    print("UNDERLYING",p.get("id"),"contract_value",p.get("contract_value"),
          "tick",p.get("tick_size"),"maintenance",p.get("maintenance_margin"))
    tick=d.ticker(cfg.symbol)
    print("UNDERLYING TICKER",tick.get("close"),"mark",tick.get("mark_price"),
          "timestamp",tick.get("timestamp"))
    start=int((time.time()-10)//900)*900-160*900
    f=closed_bars(d.candles(start,int(time.time())+1,symbol=cfg.symbol))
    print("COMPLETE BARS",len(f),"LAST",f.index[-1])
    if cfg.market=="options":
        chain=d.option_chain(cfg.asset)
        fresh=sum(good_quote(x,time.time(),cfg.staleness,
                             max_spread_pct=cfg.option_spread_max_pct) is not None for x in chain)
        print("OPTION CHAIN TICKERS",len(chain),"FRESH/TIGHT QUOTES",fresh)
        print("OPTIONS EXECUTION: QUOTE-BASED PAPER ONLY. NO ORDERS.")
    elif cfg.key and cfg.secret:
        ps=d.position(int(p["id"]))
        balances=d.wallet()
        print("POSITION CONTRACTS",position_size(ps))
        print("WALLET META",balances.get("meta") if isinstance(balances,dict) else "unknown")
        print("LEVERAGE",d.get_leverage(int(p["id"])))
        orders=d.open_orders(int(p["id"]))
        print("OPEN ORDERS",len(orders) if isinstance(orders,list) else "unrecognized")
    else:
        print("PRIVATE ACCOUNT ENDPOINTS SKIPPED (NO CREDENTIALS)")
    print("DOCTOR PASSED (READ-ONLY ENDPOINTS). NO EXECUTION VERIFIED.")

def backtest(asset):
    asset=asset.upper()
    if asset=="BTC":
        src=ROOT/"scripts"/"replay_btc_ema_st_fixed_10_margin.py"
        out=ROOT/"analysis"/"btc_ema_st_fixed_10_margin_20261119"
    elif asset=="ETH":
        src=ROOT/"scripts"/"replay_eth_ema_st_fixed10_100x.py"
        out=ROOT/"analysis"/"eth_ema_st_fixed10_100x_20261120"
    else:
        raise ValueError("Only BTC/ETH supported")
    if not src.exists():
        raise RuntimeError("Missing verified research script: "+str(src))
    print("RUNNING FUTURES BACKTEST",asset,src,flush=True)
    subprocess.run([sys.executable,str(src)],cwd=ROOT,check=True)
    print("SAVED FUTURES RESULTS",out)
    print("NO HISTORICAL OPTIONS BACKTEST: archived option-specific timestamped bid/ask/strike/expiry quotes absent.")

def status(cfg):
    db=Store(cfg.state_dir)
    try:
        result={
          "lane":cfg.lane,"mode":cfg.mode,"order_writes_enabled":cfg.trading,
          "trading_type":"quote_based_options_paper" if cfg.market=="options" else "futures",
          "heartbeat":db.get("heartbeat"),"halted":db.get("halted"),
          "signal":db.get("latest_signal"),"active":db.get(
              "paper_position" if cfg.market=="options" else "active"),
          "events":db.latest_events(20)}
        if cfg.market=="options":
            result.update(wallet_cash_usd=db.get("paper_wallet"),
                 option_equity_bid_estimate=db.get("paper_equity_bid_estimate"),
                 paper_statistics=db.get("paper_stats"),
                 closed_paper_trades=db.paper_trades())
        else:
            result.update(exchange_wallet_usd=db.get("exchange_equity_usd"),
                          exchange_fill_attribution=db.get("fill_attribution"))
        print(json.dumps(result,indent=2,default=str))
    finally:db.close()

def reconcile(cfg):
    if cfg.market!="futures":raise SystemExit("Options are paper only; no exchange orders to reconcile")
    if not(cfg.key and cfg.secret):
        raise SystemExit("Add credentials to reconcile exchange orders")
    db=Store(cfg.state_dir)
    try:
        d=Delta(cfg)
        for pending in db.unresolved():
            try:
                order=d.order_by_client_id(pending["client_id"])
                if isinstance(order,dict) and order.get("id"):
                    db.intent_status(pending["client_id"],"exchange_confirmed")
                    db.event("WARN","order_reconciled",client_id=pending["client_id"],
                             order_id=order["id"])
                    print("CONFIRMED:",pending["client_id"])
                else:print("UNRESOLVED:",pending["client_id"])
            except Exception as exc:print("UNRESOLVED:",pending["client_id"],str(exc)[:150])
        print("REMAINING UNKNOWN ORDERS",len(db.unresolved()))
    finally:db.close()

def reset(cfg,confirmation):
    if cfg.market!="futures":raise SystemExit("Options are paper only; no exchange trading halt")
    if confirmation!="I_VERIFIED_EXCHANGE_POSITIONS_ORDERS_AND_STOPS":
        raise SystemExit("Manual exchange position/order/stop verification required")
    db=Store(cfg.state_dir)
    try:
        if db.unresolved():raise SystemExit("Unknown order intents remain; reconcile first")
        db.set("halted",None)
        db.event("WARN","manual_halt_reset",asset=cfg.asset,mode=cfg.mode)
    finally:db.close()
    print("Halt cleared; check exchange positions before running.")

def main():
    p=argparse.ArgumentParser(description="BTC/ETH EMA+ST futures and options comparison")
    p.add_argument("command",choices=["doctor","run","once","serve","backtest",
                                      "status","audit","reconcile","reset-halt"])
    p.add_argument("--asset",choices=["BTC","ETH"],default=None,
                   help="Futures historical backtest asset (independent of ASSET env)")
    p.add_argument("--confirm",default="")
    args=p.parse_args()
    cfg=Config.read()
    if args.command=="doctor":doctor(cfg)
    elif args.command=="backtest":backtest(args.asset or cfg.asset)
    elif args.command=="status":status(cfg)
    elif args.command=="reconcile":reconcile(cfg)
    elif args.command=="reset-halt":reset(cfg,args.confirm)
    elif args.command=="serve":
        import uvicorn
        uvicorn.run("compare_web:app",host=cfg.host,port=cfg.port,
                    workers=1,access_log=False,proxy_headers=False)
    elif args.command=="audit":
        if cfg.market!="futures":raise SystemExit("Options paper has no exchange fills; see status")
        if not(cfg.key and cfg.secret):raise SystemExit("Account credentials required")
        api=Delta(cfg);product=api.product(cfg.symbol)
        db=Store(cfg.state_dir)
        try:
            new=sync_fills(api,db,int(product["id"]),cfg.halt_on_liquidation)
            stats=summarize_fills(db.fills(),float(product["contract_value"]))
            db.set("fill_attribution",stats)
            print(json.dumps({"new_fills":new,"estimated_pnl":stats},indent=2))
        finally:db.close()
    else:
        worker=OptionsPaperBot(cfg) if cfg.market=="options" else Bot(cfg)
        try:
            if args.command=="run":worker.loop()
            else:
                if cfg.market=="futures":worker.configure_product()
                worker.tick_once()
        finally:worker.db.close()

if __name__=="__main__":main()
