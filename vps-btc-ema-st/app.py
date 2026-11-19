#!/usr/bin/env python3
"""Commands: doctor, run, once, serve, backtest, status, reconcile, reset-halt."""
import argparse,json,subprocess,sys,time
from pathlib import Path
from config import Config,ROOT
from delta import Delta
from store import Store
from signals import closed_bars
from bot import Bot,position_size

def doctor(cfg):
    print("ENVIRONMENT:",cfg.mode,"HOST:",cfg.base_url,"ORDER_WRITES:",cfg.trading)
    d=Delta(cfg)
    p=d.product()
    assert p.get("symbol")=="BTCUSD","Wrong symbol"
    print("PRODUCT:",p.get("id"),"contract_value",p.get("contract_value"),
          "tick_size",p.get("tick_size"),"maintenance",p.get("maintenance_margin"))
    ticker=d.ticker()
    print("TICKER last:",ticker.get("close"),"mark:",ticker.get("mark_price"),
          "timestamp:",ticker.get("timestamp"))
    start=int(time.time()//900)*900-150*900
    candles=d.candles(start,int(time.time())+1)
    f=closed_bars(candles)
    print("CANDLES:",len(f),"LATEST CLOSED:",f.index[-1])
    if cfg.key and cfg.secret:
        pos=d.position(int(p["id"]))
        wallet=d.wallet()
        print("POSITION SIZE:",position_size(pos))
        print("WALLET META:",wallet.get("meta") if isinstance(wallet,dict) else "unknown")
        print("ORDER LEVERAGE:",d.get_leverage(int(p["id"])))
        open_orders=d.open_orders(int(p["id"]))
        print("ACTIVE ORDERS:",len(open_orders) if isinstance(open_orders,list) else open_orders)
    else:
        print("PRIVATE ENDPOINTS: skipped (credentials not provided)")
    if cfg.mode=="live":
        print("LIVE MODE selected; doctor never places orders.")
    print("DOCTOR COMPLETE - public/private reads only; order placement and fill behavior NOT proven.")

def backtest():
    source=ROOT/"scripts"/"replay_btc_ema_st_fixed_10_margin.py"
    if not source.exists():
        raise SystemExit("Missing source script. Clone full research branch from repository.")
    print("RUNNING REPRODUCIBLE BACKTEST:",source)
    subprocess.run([sys.executable,str(source)],cwd=ROOT,check=True)
    print("RESULT DIRECTORY:",ROOT/"analysis"/"btc_ema_st_fixed_10_margin_20261119")

def report(cfg):
    db=Store(cfg.state_dir)
    print(json.dumps({"mode":cfg.mode,"trading_enabled":cfg.trading,
        "heartbeat":db.get("heartbeat"),"halted":db.get("halted"),
        "pending":db.get("pending"),"active":db.get("active"),
        "signal":db.get("latest_signal"),"events":db.latest_events(10)},
        indent=2))
    db.close()

def reconcile(cfg):
    if not cfg.key or not cfg.secret:
        raise SystemExit("Provide keys for selected environment to inspect unknown orders")
    db=Store(cfg.state_dir)
    d=Delta(cfg)
    unresolved=db.unresolved()
    for u in unresolved:
        try:
            order=d.order_by_client_id(u["client_id"])
            if isinstance(order,dict) and order.get("id"):
                db.intent_status(u["client_id"],"exchange_confirmed")
                db.event("WARN","reconciled_manual",client_id=u["client_id"],order_id=order["id"])
                print("CONFIRMED:",u["client_id"],order.get("state"))
            else:
                print("UNRESOLVED:",u["client_id"])
        except Exception as exc:
            print("UNRESOLVED:",u["client_id"],str(exc)[:120])
    print("REMAINING UNRESOLVED:",len(db.unresolved()))
    db.close()

def reset(cfg,confirmation):
    if confirmation!="I_VERIFIED_EXCHANGE_POSITIONS_ORDERS_AND_STOPS":
        raise SystemExit("Explicit manual exchange verification acknowledgement required")
    db=Store(cfg.state_dir)
    if db.unresolved():
        raise SystemExit("Unresolved orders remain; run reconcile and inspect Delta manually")
    # Manual confirmation is meaningful; this command does NOT cancel exchange orders.
    db.set("halted",None)
    db.event("WARN","manual_halt_reset",mode=cfg.mode)
    print("HALT CLEARED. Verify no unexpected position before starting.")

def main():
    parser=argparse.ArgumentParser(description="BTCUSD EMA20/Supertrend research/demo runner")
    parser.add_argument("command",choices=["doctor","run","once","serve","backtest","status","reconcile","reset-halt"])
    parser.add_argument("--confirm",default="")
    args=parser.parse_args()
    cfg=Config.read(require_keys=False)
    if args.command=="doctor":doctor(cfg)
    elif args.command=="backtest":backtest()
    elif args.command=="status":report(cfg)
    elif args.command=="reconcile":reconcile(cfg)
    elif args.command=="reset-halt":reset(cfg,args.confirm)
    elif args.command=="serve":
        import uvicorn
        uvicorn.run("web:app",host=cfg.host,port=cfg.port,workers=1,
                    access_log=False,proxy_headers=False)
    else:
        runner=Bot(cfg)
        try:
            if args.command=="run":runner.loop()
            else:
                runner.configure_product()
                runner.tick_once()
        finally:runner.db.close()

if __name__=="__main__":main()
