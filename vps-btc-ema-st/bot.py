"""Single-instrument demo/live trading loop with fail-closed order reconciliation.

This is a forward-testing reference app, NOT audited production execution.
Real exchange fills, funding, latency and mark-based liquidation differ from OHLC replay.
"""
import fcntl,math,os,time,uuid
from datetime import datetime,timezone
from pathlib import Path
from delta import Delta,DeltaError
from store import Store
from audit import sync_fills,summarize_fills
from signals import BAR_SECONDS,closed_bars,signal,indicators,quantize_stop,size_contracts,stop_safe

def oid(prefix):
    # <=32 chars and unique among open orders.
    return ("ves"+prefix+str(int(time.time()*1000))+uuid.uuid4().hex[:7])[:32]

def dt_day():
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")

def result_list(payload):
    if isinstance(payload,list):return payload
    if isinstance(payload,dict) and isinstance(payload.get("result"),list):return payload["result"]
    raise ValueError("Unexpected exchange list response; refusing to guess")

def position_size(payload):
    if isinstance(payload,dict) and "size" in payload:return int(float(payload["size"]))
    if isinstance(payload,list):
        if not payload:return 0
        if len(payload)==1 and isinstance(payload[0],dict):
            return position_size(payload[0])
    raise ValueError("Unexpected position schema")

def wallet_equity(payload):
    # Check reported USD wallet balance, not hypothetical P&L.
    if isinstance(payload,dict) and "meta" in payload:
        m=payload["meta"]
        if isinstance(m,dict) and m.get("net_equity") not in (None,""):
            return float(m["net_equity"])
    raise ValueError("Wallet net_equity absent; cannot enforce daily drawdown")

def target_stop_guard(entry,side,stop,leverage,product,buffer_pct):
    maintenance=float(product.get("maintenance_margin","0.25"))/100
    return stop_safe(entry,stop,side,leverage,maintenance,buffer_pct/100)

class Bot:
    def __init__(self,config):
        self.cfg=config
        self.db=Store(config.state_dir)
        self.delta=Delta(config)
        self.product=None
        self.pid=None
        self.tick=0
        self.value=0

    def emit(self,level,kind,**items):
        self.db.event(level,kind,**items)
        if level in ("ERROR","WARN"):print(level,kind,items,flush=True)

    def halt(self,reason,**items):
        self.db.set("halted",reason)
        self.emit("ERROR","halt",reason=reason,**items)
        # Never cancel exchange-native stops as part of the kill switch.
        raise RuntimeError("BOT HALTED: "+reason)

    def is_halted(self):
        return bool(self.db.get("halted",""))

    def public_snapshot(self):
        ticker=self.delta.ticker()
        price=float(ticker.get("close") or 0)
        mark=float(ticker.get("mark_price") or 0)
        stamp=float(ticker.get("timestamp") or 0)
        if stamp>1e14:stamp/=1e6
        elif stamp>1e11:stamp/=1e3
        if price<=0 or mark<=0 or stamp<=0:
            raise ValueError("Invalid ticker price/mark/timestamp")
        delay=time.time()-stamp
        if delay< -8 or delay>self.cfg.staleness:
            raise ValueError(f"Stale or future ticker: age {delay:.1f}s")
        self.db.set("ticker",{"last":price,"mark":mark,"ts":stamp})
        return price,mark

    def bar_snapshot(self):
        now=time.time()
        start=int((now-10)//BAR_SECONDS)*BAR_SECONDS-1000*BAR_SECONDS
        # Candle history usually timestamped by bar open; no live/partial bars.
        raw=self.delta.candles(start,int(now)+1)
        frame=closed_bars(raw,now)
        if len(frame)<100:raise ValueError("Insufficient history")
        self.db.set("last_market_bar",str(frame.index[-1]))
        return frame

    def exchange_position(self):
        return self.delta.position(self.pid)

    def matching_orders(self):
        orders=result_list(self.delta.open_orders(self.pid))
        return [o for o in orders if int(o.get("product_id",-1))==self.pid]

    def wallet_check(self):
        actual=wallet_equity(self.delta.wallet())
        if not math.isfinite(actual) or actual<=0:self.halt("Invalid account equity")
        day=dt_day()
        saved=self.db.get("daily_snapshot")
        if not saved or saved["day"]!=day:
            saved={"day":day,"start_equity":actual,"entries":0}
            self.db.set("daily_snapshot",saved)
        if actual<=saved["start_equity"]-self.cfg.daily_loss_limit:
            self.halt("Daily wallet drawdown reached",initial=saved["start_equity"],current=actual)
        if saved["entries"]>=self.cfg.max_trades:
            return False,actual
        return True,actual

    def configure_product(self):
        p=self.delta.product()
        if p.get("symbol")!="BTCUSD" or p.get("contract_type")!="perpetual_futures":
            raise ValueError("Wrong exchange instrument; BTCUSD perpetual required")
        if p.get("state")!="live" or p.get("trading_status")!="operational":
            raise ValueError("Product is not currently operational")
        self.value=float(p["contract_value"])
        self.tick=float(p["tick_size"])
        self.pid=int(p["id"])
        if not (0<self.value<1 and self.tick>0):raise ValueError("Invalid product specification")
        self.product=p
        self.db.set("product",{"id":self.pid,"symbol":"BTCUSD","contract_value":self.value,
                               "tick_size":self.tick,"mode":self.cfg.mode})
        if self.cfg.trading:
            pstate=self.exchange_position()
            size=position_size(pstate)
            if size and not (self.db.get("active") or self.db.get("pending")):
                self.halt("Unexpected existing BTCUSD position: use dedicated account",size=size)
            lev=self.delta.get_leverage(self.pid)
            current=float(lev.get("leverage",0))
            if current!=self.cfg.leverage:
                if size:self.halt("Cannot change leverage with an existing position")
                self.delta.set_leverage(self.pid,self.cfg.leverage)
                confirmed=self.delta.get_leverage(self.pid)
                if float(confirmed.get("leverage",0))!=self.cfg.leverage:
                    self.halt("Leverage change not confirmed")
            # A manual isolated-vs-cross setting is required; API does not verify it.
        self.emit("INFO","startup",mode=self.cfg.mode,trading=self.cfg.trading,
                  product_id=self.pid,leverage=self.cfg.leverage,
                  margin_budget=self.cfg.margin)

    def place(self,action,payload):
        client_id=payload["client_order_id"]
        self.db.intent(client_id,action,payload)
        try:
            order=self.delta.place_order(payload)
        except Exception:
            # Not safe to retry place_order. Look up ORIGINAL ID, then stop.
            try:
                order=self.delta.order_by_client_id(client_id)
                self.db.intent_status(client_id,"exchange_confirmed")
                self.emit("WARN","reconciled_order",action=action,client_id=client_id)
                return order
            except Exception:
                self.halt("Order result ambiguous; reconcile exchange manually",action=action,client_id=client_id)
        if not isinstance(order,dict) or not order.get("id"):
            self.halt("Order accepted but missing order ID",action=action,client_id=client_id)
        self.db.intent_status(client_id,"exchange_confirmed")
        self.emit("INFO","order_ack",action=action,client_id=client_id,order_id=order["id"])
        return order

    def protect(self,active):
        expected_side="sell" if active["side"]=="buy" else "buy"
        found=None
        protected=[]
        for o in self.matching_orders():
            if o.get("side")==expected_side and o.get("stop_order_type")=="stop_loss_order":
                if (o.get("reduce_only") is True and
                    o.get("stop_trigger_method")=="mark_price" and
                    int(o.get("size",0))>=abs(active["size"])):
                    protected.append(o)
                else:
                    self.halt("Unrecognized or unsafe stop order: manual inspection required",
                              stop_order_id=o.get("id"))
            else:
                self.halt("Unexpected extra order for BTCUSD while bot owns position",
                          order_id=o.get("id"))
        if len(protected)>1:
            self.halt("Multiple protective orders found; manual reconciliation needed",
                      stop_ids=[o.get("id") for o in protected])
        if protected:found=protected[0]
        if found:
            if abs(float(found.get("stop_price") or 0)-float(active["stop"]))>self.tick/2:
                # If stop from entry bracket has different price, refuse guessing.
                self.halt("Exchange stop price disagrees with bot state")
            active["stop_id"]=int(found["id"])
            self.db.set("active",active)
            return True
        # If a stop existed earlier, its disappearance is an emergency.
        if active.get("stop_id"):
            if time.time()-float(active.get("stop_sent_at",0))<12:
                # Active-orders API can lag after an accepted stop.
                # Do NOT place a duplicate stop or trail until verified.
                return False
            self.emergency_close(active,"protective_stop_disappeared")
            return False
        # Opening order included an attached bracket stop, but if none is visible,
        # place independent reduce-only mark stop immediately after position appears.
        stop_id=oid("s")
        payload={"product_id":self.pid,"size":abs(active["size"]),"side":expected_side,
                 "order_type":"market_order","stop_order_type":"stop_loss_order",
                 "stop_price":str(active["stop"]),"stop_trigger_method":"mark_price",
                 "reduce_only":True,"client_order_id":stop_id}
        order=self.place("protective_stop",payload)
        active["stop_id"]=int(order["id"])
        active["stop_sent_at"]=time.time()
        self.db.set("active",active)
        self.emit("WARN","standalone_stop_created",order_id=order["id"])
        return False

    def emergency_close(self,active,reason):
        if not self.cfg.trading:self.halt("Emergency close needed but trading disabled")
        # Record durable intent first. Never submit a second close blindly.
        self.db.set("exit_pending",{"reason":reason,"time":time.time()})
        payload={"product_id":self.pid,"size":abs(active["size"]),
                 "side":"sell" if active["size"]>0 else "buy",
                 "order_type":"market_order","reduce_only":True,
                 "client_order_id":oid("x")}
        self.place("reduce_only_close",payload)
        self.emit("WARN","emergency_close_sent",reason=reason)
        self.db.set("halted",reason)
        # Do not remove native stop until the position is verifiably flat.

    def reconcile(self,mark):
        if not self.cfg.trading:return
        ps=self.exchange_position()
        size=position_size(ps)
        active=self.db.get("active")
        pending=self.db.get("pending")
        if pending and not active and size:
            sign=1 if pending["side"]=="buy" else -1
            if size*sign<=0 or abs(size)>pending["contracts"]:
                self.halt("Entry fill differs from expected position",size=size)
            entry=float(ps.get("entry_price") or 0)
            if entry<=0:self.halt("Cannot read confirmed position entry price")
            stop=quantize_stop(entry-sign*pending["stop_distance"],self.tick,pending["side"])
            if not target_stop_guard(entry,pending["side"],stop,self.cfg.leverage,
                                      self.product,self.cfg.buffer_pct):
                self.halt("Actual fill breached liquidation-stop buffer; manually close",
                          entry_price=entry,stop=stop)
            active={"side":pending["side"],"size":size,"entry":entry,
                    "stop":stop,"initial_stop":stop,"best":entry,"trail_active":False,
                    "stop_id":None,"entry_oid":pending["client_id"],
                    "entry_time":time.time()}
            self.db.set("active",active)
            self.db.set("pending",None)
            self.emit("INFO","entry_confirmed",size=size,entry=entry,stop=stop)
            self.protect(active)
        elif pending and not active and not size:
            if time.time()-pending["submitted_at"]>25:
                self.halt("Entry order status needs reconciliation; position still flat")
        elif active and not size:
            self.emit("INFO","position_flat_detected",was_size=active["size"],
                      entry=active["entry"],initial_stop=active["initial_stop"])
            self.db.set("active",None)
            self.db.set("exit_pending",None)
            self.db.set("closed_today",self.db.get("closed_today",0)+1)
            # Check no orphan stop order. Do not cancel unrelated orders.
            for order in self.matching_orders():
                if int(order.get("id",-1))==active.get("stop_id"):
                    self.delta.cancel_order(self.pid,int(order["id"]))
                    self.emit("INFO","orphan_stop_cancelled",order_id=order["id"])
        elif active and size!=active["size"]:
            self.halt("Unexpected partial fill or changed position size",size=size,
                      expected=active["size"])
        elif size and not active and not pending:
            self.halt("Unexpected position; bot will not take ownership",size=size)
        if self.db.get("active") and not self.db.get("exit_pending"):
            self.manage_stop(mark)

    def manage_stop(self,mark):
        active=self.db.get("active")
        if not active:return
        if not self.protect(active):
            return
        side=1 if active["side"]=="buy" else -1
        entry=float(active["entry"])
        best=float(active["best"])
        stop=float(active["stop"])
        if (mark-entry)*side>=150:
            active["trail_active"]=True
        if active["trail_active"]:
            best=max(best,mark) if side==1 else min(best,mark)
            candidate=quantize_stop(best-side*50,self.tick,active["side"])
            if (candidate>stop+self.tick if side==1 else candidate<stop-self.tick):
                if (candidate>=mark if side==1 else candidate<=mark):
                    self.emergency_close(active,"trailing_stop_market_crossed")
                    return
                try:
                    self.delta.edit_stop(self.pid,active["stop_id"],candidate)
                    # Confirm exchange protective order actually updated.
                    matching=[o for o in self.matching_orders() if int(o.get("id",-1))==active["stop_id"]]
                    if not matching or abs(float(matching[0]["stop_price"])-candidate)>self.tick/2:
                        self.halt("Trailing stop edit was not verified at exchange")
                except Exception:
                    self.halt("Trailing stop edit failed: exchange stop may be stale")
                active["stop"]=candidate
                self.emit("INFO","stop_trailed",stop=candidate,mark=mark)
        active["best"]=best
        self.db.set("active",active)

    def on_bar(self,frame,price,mark):
        bar_ts=int(frame.index[-1].timestamp())
        last=self.db.get("processed_bar")
        if last is None:
            self.db.set("processed_bar",bar_ts)
            self.emit("INFO","warmup_bar",bar_ts=bar_ts)
            return
        if bar_ts<=last:return
        # Once processed, never resend the same candle even if network/position fails.
        self.db.set("processed_bar",bar_ts)
        direction=indicators(frame)["dir"]
        active=self.db.get("active")
        if active and not self.db.get("exit_pending"):
            side=1 if active["side"]=="buy" else -1
            if (side==1 and direction.iloc[-2]==-1 and direction.iloc[-1]==1) or (
                side==-1 and direction.iloc[-2]==1 and direction.iloc[-1]==-1):
                if self.cfg.trading:
                    self.emergency_close(active,"opposite_supertrend_flip")
                return
        s=signal(frame)
        self.db.set("latest_signal",s or {"bar_ts":bar_ts,"side":"none"})
        if s:self.emit("INFO","signal",**s)
        if not s or not self.cfg.trading or self.is_halted():return
        if self.db.get("active") or self.db.get("pending") or self.db.get("exit_pending"):
            self.emit("INFO","skip",reason="already_busy")
            return
        if position_size(self.exchange_position())!=0 or self.matching_orders():
            self.halt("Exchange not flat/clean at new entry candle")
        can_enter,equity=self.wallet_check()
        if not can_enter:
            self.emit("INFO","skip",reason="daily_trade_limit")
            return
        if equity<self.cfg.margin+1:
            self.emit("WARN","skip",reason="insufficient_exchange_equity")
            return
        contracts=size_contracts(price,self.value,self.cfg.margin,self.cfg.leverage)
        if contracts<=0:self.emit("WARN","skip",reason="less_than_one_contract");return
        # Limit stale candle-close -> live fill divergence; avoid chasing.
        if abs(price-s["signal_close"])/s["signal_close"]>0.002:
            self.emit("INFO","skip",reason="price_moved_since_bar_close")
            return
        direction=1 if s["side"]=="buy" else -1
        stop=quantize_stop(price-direction*s["stop_distance_points"],self.tick,s["side"])
        # Server stop triggers on MARK, so it must be on the safe side of mark now.
        if (s["side"]=="buy" and mark<=stop) or (s["side"]=="sell" and mark>=stop):
            self.emit("WARN","skip",reason="mark_price_already_crossed_protective_stop",mark=mark,stop=stop)
            return
        if not target_stop_guard(price,s["side"],stop,self.cfg.leverage,
                                 self.product,self.cfg.buffer_pct):
            self.emit("WARN","skip",reason="initial_stop_beyond_liquidation_buffer",
                      stop=stop,price=price)
            return
        client_id=oid("e")
        # Attach exchange-native stop to the initial market order as early as possible.
        payload={"product_id":self.pid,"size":contracts,"side":s["side"],
                 "order_type":"market_order","client_order_id":client_id,
                 "reduce_only":False,"bracket_stop_loss_price":str(stop),
                 "bracket_stop_trigger_method":"mark_price"}
        self.db.set("pending",{"client_id":client_id,"side":s["side"],
                "contracts":contracts,"stop_distance":s["stop_distance_points"],
                "submitted_at":time.time(),"bar_ts":bar_ts})
        self.place("entry_with_attached_stop",payload)
        d=self.db.get("daily_snapshot")
        d["entries"]+=1
        self.db.set("daily_snapshot",d)
        self.emit("INFO","entry_sent",client_id=client_id,size=contracts,
                  stop=stop,notional=price*contracts*self.value)

    def tick_once(self):
        price,mark=self.public_snapshot()
        if self.cfg.trading:
            self.reconcile(mark)
        if self.cfg.key and self.cfg.secret:
            if time.time()-self.db.get("fills_last_poll",0)>60:
                sync_fills(self.delta,self.db,self.pid,self.cfg.halt_on_liquidation)
                self.db.set("fills_last_poll",time.time())
                self.db.set("fill_attribution",summarize_fills(self.db.fills(),self.value))
                self.db.set("exchange_equity_usd",wallet_equity(self.delta.wallet()))
                if self.db.get("halted"):
                    raise RuntimeError("Trading halted after exchange liquidation or fill audit")
        # Pull candles once per completed 15m bar, not 1m.
        last=self.db.get("processed_bar")
        closed_ts=int((time.time()-10)//BAR_SECONDS)*BAR_SECONDS-BAR_SECONDS
        if last is None or closed_ts>last:
            frame=self.bar_snapshot()
            self.on_bar(frame,price,mark)
        self.db.set("heartbeat",{"now":time.time(),"mode":self.cfg.mode,
                  "trading_enabled":self.cfg.trading,"halted":self.db.get("halted"),
                  "last":price,"mark":mark,
                  "active":self.db.get("active")})

    def loop(self):
        self.cfg.state_dir.mkdir(parents=True,exist_ok=True)
        lock=open(self.cfg.state_dir/"runner.lock","w")
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError("Another bot runner already holds lock")
        if self.is_halted():raise RuntimeError("Halted state persisted; inspect and reset manually")
        if self.db.unresolved():
            self.halt("Unresolved order intents; manual reconciliation required")
        if self.db.get("first_started_us") is None:
            self.db.set("first_started_us",int(time.time()*1_000_000))
        self.configure_product()
        while True:
            try:self.tick_once()
            except KeyboardInterrupt:raise
            except Exception as ex:
                self.emit("ERROR","tick_failed",error=str(ex))
                if self.cfg.trading:
                    if not self.db.get("halted"):
                        self.db.set("halted","poll/reconciliation failure; check exchange and restart after inspection")
                    raise
            time.sleep(self.cfg.poll)
