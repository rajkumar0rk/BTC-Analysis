"""BTC/ETH long CALL/PUT quote-based forward paper trader.

NO ORDERS. Never claims historical options results from underlying futures candles.
Entry ask, exit bid, bounded premium $10 incl modeled fee/GST, one option per lane.
Option exits are triggered by the SAME underlying EMA/ST ATR/trailing rules.
"""
import fcntl,math,re,time
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo

from delta import Delta
from store import Store
from signals import BAR_SECONDS,closed_bars,signal,indicators,trailing_points,quantize_stop

SYM_RE=re.compile(r"^([CP])-(BTC|ETH)-(\d+(?:\.\d+)?)-(\d{6})$")
IST=ZoneInfo("Asia/Kolkata")

def epoch(value):
    n=float(value)
    if n>1e14:n/=1e6
    elif n>1e11:n/=1e3
    return n

def parse_time(value):
    if value is None:return None
    if isinstance(value,(int,float)):return epoch(value)
    try:return datetime.fromisoformat(str(value).replace("Z","+00:00")).timestamp()
    except (TypeError,ValueError):return None

def chain_side(asset,underlying_direction):
    if asset not in ("BTC","ETH") or underlying_direction not in ("buy","sell"):
        raise ValueError("Invalid option signal direction")
    return "C" if underlying_direction=="buy" else "P"

def good_quote(ticker,now,staleness,required_size=1,exit_only=False,max_spread_pct=10):
    if not isinstance(ticker,dict):return None
    try:
        q=ticker["quotes"]
        bid=float(q["best_bid"]);ask=float(q["best_ask"])
        bid_qty=float(q["bid_size"]);ask_qty=float(q["ask_size"])
        ts=epoch(ticker["timestamp"])
        if not all(math.isfinite(v) for v in (bid,ask,bid_qty,ask_qty,ts)):
            return None
        if bid<=0 or ask<bid or ts>now+8 or now-ts>staleness:
            return None
        spread=100*(ask-bid)/((ask+bid)/2)
        if not exit_only and spread>max_spread_pct:return None
        if exit_only:
            if bid_qty<required_size:return None
        elif min(ask_qty,bid_qty)<required_size:return None
        return {"bid":bid,"ask":ask,"bid_size":bid_qty,"ask_size":ask_qty,
                "timestamp":ts,"spread_pct":spread}
    except (KeyError,TypeError,ValueError,ZeroDivisionError):
        return None

def fee_usd(underlying_mark,option_price,contracts,contract_value,rate,cap_pct):
    if min(underlying_mark,option_price,contracts,contract_value)<=0:
        raise ValueError("Invalid option fee inputs")
    premium=option_price*contracts*contract_value
    return min(underlying_mark*contracts*contract_value*rate,premium*cap_pct/100)

def quantity_for_budget(ask,mark,contract_value,budget,fee_rate,cap_pct,gst=.18):
    if min(ask,mark,contract_value,budget)<=0:return 0
    per_contract=ask*contract_value+fee_usd(mark,ask,1,contract_value,fee_rate,cap_pct)*(1+gst)
    return max(0,math.floor((budget+1e-10)/per_contract))

def paper_stats(trades,initial=100):
    balance=initial;peak=initial;dd=0
    for item in trades:
        balance+=item["net_pnl_usd"]
        peak=max(peak,balance)
        dd=max(dd,100*(1-balance/peak))
    positive=sum(t["net_pnl_usd"] for t in trades if t["net_pnl_usd"]>0)
    negative=-sum(t["net_pnl_usd"] for t in trades if t["net_pnl_usd"]<0)
    return {"starting_balance_usd":round(initial,4),
            "closed_equity_usd":round(balance,4),
            "net_profit_usd":round(balance-initial,4),
            "trades":len(trades),"winners":sum(t["net_pnl_usd"]>0 for t in trades),
            "losers":sum(t["net_pnl_usd"]<0 for t in trades),
            "profit_factor":round(positive/negative,4) if negative else None,
            "max_closed_equity_drawdown_pct":round(dd,2),
            "fee_includes_gst_assumption":True,
            "source":"forward option bid/ask PAPER only; no real orders"}

def validate_contract(info,kind,asset,symbol,now,min_hours,max_days):
    if not isinstance(info,dict) or info.get("symbol")!=symbol:
        return None
    if info.get("contract_type")!=("call_options" if kind=="C" else "put_options"):
        return None
    if info.get("state")!="live" or info.get("trading_status")!="operational":
        return None
    m=SYM_RE.match(symbol)
    if not m or m.group(1)!=kind or m.group(2)!=asset:return None
    strike=float(m.group(3))
    actual=float(info.get("strike_price",0))
    if not math.isclose(strike,actual,rel_tol=1e-8,abs_tol=0.05):
        return None
    cv=float(info.get("contract_value",0))
    settle=parse_time(info.get("settlement_time"))
    if not settle or not(min_hours*3600<=settle-now<=max_days*86400):
        return None
    if not(0<cv<=1):return None
    return {"id":int(info["id"]),"contract_value":cv,
            "expiry_ts":settle,"strike":strike,
            "symbol":symbol,"tick_size":float(info.get("tick_size") or 0)}

class OptionsPaperBot:
    def __init__(self,config):
        if config.market!="options" or config.trading:
            raise ValueError("OptionsPaperBot requires MARKET=options and TRADING_ENABLED=false")
        self.cfg=config
        self.db=Store(config.state_dir)
        self.api=Delta(config)
        if self.db.get("paper_wallet") is None:
            # Atomic baseline persisted. Never reinitialize a previous wallet.
            self.db.paper_transition(config.portfolio,None,{"kind":"paper_account_initialized"})

    def event(self,level,kind,**data):
        self.db.event(level,kind,asset=self.cfg.asset,market="options",**data)

    def market(self):
        x=self.api.ticker(self.cfg.symbol)
        ts=epoch(x.get("timestamp",0))
        mark=float(x.get("mark_price") or 0)
        last=float(x.get("close") or 0)
        now=time.time()
        if mark<=0 or last<=0 or ts>now+8 or now-ts>self.cfg.staleness:
            raise ValueError("Underlying ticker invalid or stale; no paper trade")
        self.db.set("ticker",{"mark":mark,"last":last,"ts":ts})
        return last,mark

    def bars(self):
        now=time.time()
        start=int((now-10)//BAR_SECONDS)*BAR_SECONDS-1000*BAR_SECONDS
        candles=self.api.candles(start,int(now)+1,symbol=self.cfg.symbol)
        f=closed_bars(candles,now)
        self.db.set("last_market_bar",str(f.index[-1]))
        return f

    def select(self,side,underlying_mark):
        target=chain_side(self.cfg.asset,side)
        now=time.time()
        chain=self.api.option_chain(self.cfg.asset)
        candidates=[]
        for t in chain:
            symbol=str(t.get("symbol") or "")
            m=SYM_RE.match(symbol)
            if not m or m.group(1)!=target or m.group(2)!=self.cfg.asset:
                continue
            try:
                strike=float(m.group(3))
                maturity=datetime.strptime(m.group(4),"%d%m%y").replace(tzinfo=timezone.utc)
                if abs(strike-underlying_mark)/underlying_mark>0.02:continue
                # Loose date pre-filter, actual product settlement_time is authoritative.
                if not(1<=(maturity.timestamp()-now)/86400<=self.cfg.option_max_dte_days+1):
                    continue
                q=good_quote(t,now,self.cfg.staleness,max_spread_pct=self.cfg.option_spread_max_pct)
                if not q:continue
                candidates.append((abs(strike-underlying_mark),q["spread_pct"],symbol,t,q))
            except (ValueError,TypeError):continue
        candidates.sort(key=lambda c:(c[0],c[1],c[2]))
        for _,_,symbol,t,q in candidates[:18]:
            info=self.api.option_product(symbol)
            validated=validate_contract(info,target,self.cfg.asset,symbol,now,
                                        self.cfg.option_min_dte_hours,self.cfg.option_max_dte_days)
            if not validated:continue
            lots=quantity_for_budget(q["ask"],underlying_mark,
                   validated["contract_value"],self.cfg.option_premium,
                   self.cfg.option_fee_rate,self.cfg.option_fee_cap_pct)
            lots=min(lots,int(q["ask_size"]),int(q["bid_size"]))
            if lots<1:continue
            return {"product":validated,"quote":q,"lots":lots}
        return None

    def entry(self,s,last,mark):
        day=datetime.now(IST).strftime("%Y-%m-%d")
        state=self.db.get("paper_day")
        balance=float(self.db.get("paper_wallet",self.cfg.portfolio))
        if not state or state["day"]!=day:
            state={"day":day,"start":balance,"entries":0}
            self.db.set("paper_day",state)
        if state["entries"]>=self.cfg.max_trades:
            self.event("INFO","paper_entry_skipped",reason="max_trades_day")
            return
        if balance<state["start"]-self.cfg.daily_loss_limit:
            self.event("WARN","paper_entry_skipped",reason="daily_loss_limit")
            return
        if abs(last-s["signal_close"])/s["signal_close"]>0.002:
            self.event("INFO","paper_entry_skipped",reason="underlying_price_moved")
            return
        chosen=self.select(s["side"],mark)
        if not chosen:
            self.event("WARN","paper_entry_skipped",reason="no_fresh_liquid_atm_contract_within_premium",
                       underlying=mark,side=s["side"])
            return
        product=chosen["product"];quote=chosen["quote"];lots=chosen["lots"]
        cv=product["contract_value"]
        entry_fee=fee_usd(mark,quote["ask"],lots,cv,
                          self.cfg.option_fee_rate,self.cfg.option_fee_cap_pct)
        gst=entry_fee*.18
        premium=quote["ask"]*lots*cv
        debit=premium+entry_fee+gst
        if debit>self.cfg.option_premium+1e-7 or debit>balance:
            self.event("WARN","paper_entry_skipped",reason="premium_budget_or_wallet")
            return
        sign=1 if s["side"]=="buy" else -1
        tick=0.5 if self.cfg.asset=="BTC" else 0.05
        stop=quantize_stop(mark-sign*s["stop_distance_points"],tick,s["side"])
        activation,trailing=trailing_points(self.cfg.asset,mark)
        pos={
            "asset":self.cfg.asset,"symbol":product["symbol"],
            "product_id":product["id"],"option_type":"CALL" if sign==1 else "PUT",
            "side":s["side"],"contracts":lots,"contract_value":cv,
            "expiry_ts":product["expiry_ts"],"strike":product["strike"],
            "entry_time":time.time(),"entry_underlying":mark,
            "entry_bid":quote["bid"],"entry_ask":quote["ask"],
            "entry_quote_time":quote["timestamp"],"entry_spread_pct":quote["spread_pct"],
            "entry_premium_usd":premium,"entry_fee_usd":entry_fee,
            "entry_gst_usd":gst,"initial_stop":stop,"stop":stop,"best":mark,
            "activation_points":activation,"trailing_distance_points":trailing,
            "trail_active":False,"last_bid":quote["bid"],"last_bid_ts":quote["timestamp"]}
        self.db.paper_transition(balance-debit,pos,{"kind":"paper_option_buy",
            "symbol":product["symbol"],"lots":lots,"ask":quote["ask"],"bid":quote["bid"],
            "premium_usd":premium,"fee_usd":entry_fee,"gst_usd":gst,
            "underlying_mark":mark,"underlying_signal_bar":s["bar_ts"]})
        state["entries"]+=1
        self.db.set("paper_day",state)
        self.db.sample_quote(product["id"],time.time(),quote["bid"],quote["ask"],mark,quote)

    def close(self,reason,mark):
        p=self.db.get("paper_position")
        if not p:return
        now=time.time()
        if now>=p["expiry_ts"]:
            # Settlement price unavailable in public quotes; don't fabricate it.
            self.db.set("paper_exit_pending","expired_contract_needs_exchange_settlement_price")
            self.event("ERROR","paper_exit_pending",reason="expired_contract_needs_settlement")
            return
        t=self.api.ticker(p["symbol"])
        q=good_quote(t,now,self.cfg.staleness,p["contracts"],exit_only=True)
        if not q:
            self.db.set("paper_exit_pending",reason)
            last=self.db.get("paper_exit_warning_ts",0)
            if now-last>60:
                self.db.set("paper_exit_warning_ts",now)
                self.event("ERROR","paper_exit_pending",reason=reason,
                           problem="bid stale/missing/insufficient; no invented fill",symbol=p["symbol"])
            return
        self.db.sample_quote(p["product_id"],now,q["bid"],q["ask"],mark,q)
        value=q["bid"]*p["contracts"]*p["contract_value"]
        fee=fee_usd(mark,q["bid"],p["contracts"],p["contract_value"],
                    self.cfg.option_fee_rate,self.cfg.option_fee_cap_pct)
        gst=fee*.18
        wallet=float(self.db.get("paper_wallet"))
        net=(value-fee-gst)-(p["entry_premium_usd"]+p["entry_fee_usd"]+p["entry_gst_usd"])
        stats=paper_stats(self.db.paper_trades()+[{"net_pnl_usd":net}],self.cfg.portfolio)
        trade={
           "closed_at_utc":datetime.now(timezone.utc).isoformat(),
           "entry_time_utc":datetime.fromtimestamp(p["entry_time"],timezone.utc).isoformat(),
           "symbol":p["symbol"],"asset":self.cfg.asset,"market":"options_paper",
           "side":p["side"],"option_type":p["option_type"],"contracts":p["contracts"],
           "strike":p["strike"],"expiry_ts":p["expiry_ts"],
           "underlying_entry_mark":p["entry_underlying"],"underlying_exit_mark":mark,
           "option_buy_ask":p["entry_ask"],"option_exit_bid":q["bid"],
           "buy_quote_age_s":round(p["entry_time"]-p["entry_quote_time"],2),
           "exit_quote_age_s":round(now-q["timestamp"],2),
           "entry_premium_usd":p["entry_premium_usd"],"exit_value_usd":value,
           "gross_pnl_usd":value-p["entry_premium_usd"],
           "commissions_usd":p["entry_fee_usd"]+fee,
           "gst_usd":p["entry_gst_usd"]+gst,"net_pnl_usd":net,
           "reason":reason}
        self.db.paper_transition(wallet+value-fee-gst,None,
             {"kind":"paper_option_sell","symbol":p["symbol"],"reason":reason,
              "bid":q["bid"],"net_usd":net,"balance_usd":wallet+value-fee-gst},
              trade=trade,stats=stats)
        self.db.set("paper_exit_pending",None)

    def manage(self,mark):
        p=self.db.get("paper_position")
        if not p:return
        if time.time()>=p["expiry_ts"]:
            self.close("expiry",mark)
            return
        if self.db.get("paper_exit_pending"):
            self.close(self.db.get("paper_exit_pending"),mark)
            return
        sign=1 if p["side"]=="buy" else -1
        if (mark-p["entry_underlying"])*sign>=p["activation_points"]:
            p["trail_active"]=True
        if p["trail_active"]:
            best=max(p["best"],mark) if sign==1 else min(p["best"],mark)
            p["best"]=best
            candidate=best-sign*p["trailing_distance_points"]
            p["stop"]=max(p["stop"],candidate) if sign==1 else min(p["stop"],candidate)
        # Persist trailing state BEFORE exiting.
        self.db.set("paper_position",p)
        if (mark<=p["stop"] if sign==1 else mark>=p["stop"]):
            self.close("underlying_trailing_stop" if p["trail_active"] else "underlying_atr_stop",mark)
        else:
            # Observe the OPTION bid for marked-to-bid indicative open-equity, not last trade.
            try:
                t=self.api.ticker(p["symbol"])
                q=good_quote(t,time.time(),self.cfg.staleness,p["contracts"],exit_only=True)
                if q:
                    self.db.set("paper_bid",q)
                    self.db.sample_quote(p["product_id"],time.time(),q["bid"],q["ask"],mark,q)
            except Exception:
                pass

    def on_bar(self,f,last,mark):
        bar_ts=int(f.index[-1].timestamp())
        processed=self.db.get("processed_bar")
        if processed is None:
            self.db.set("processed_bar",bar_ts)
            self.event("INFO","warmup_bar",bar_ts=bar_ts)
            return
        if bar_ts<=processed:return
        self.db.set("processed_bar",bar_ts)
        indicators_frame=indicators(f)
        dir=indicators_frame["dir"]
        p=self.db.get("paper_position")
        if p:
            flip=(p["side"]=="buy" and dir.iloc[-2]==-1 and dir.iloc[-1]==1) or (
                  p["side"]=="sell" and dir.iloc[-2]==1 and dir.iloc[-1]==-1)
            if flip:
                self.close("underlying_supertrend_flip",mark)
            return
        s=signal(f,asset=self.cfg.asset)
        self.db.set("latest_signal",s or {"bar_ts":bar_ts,"side":"none"})
        if s:
            self.event("INFO","underlying_signal",**s)
            self.entry(s,last,mark)

    def tick_once(self):
        last,mark=self.market()
        self.manage(mark)
        closed=int((time.time()-10)//BAR_SECONDS)*BAR_SECONDS-BAR_SECONDS
        prev=self.db.get("processed_bar")
        if prev is None or prev<closed:
            self.on_bar(self.bars(),last,mark)
        p=self.db.get("paper_position")
        cash=float(self.db.get("paper_wallet",self.cfg.portfolio))
        optbid=self.db.get("paper_bid")
        estimate=cash
        if p:
            if optbid and optbid["timestamp"]>=p["entry_time"]:
                estimate+=p["contracts"]*p["contract_value"]*optbid["bid"]
            else:
                estimate=None
        self.db.set("heartbeat",{"now":time.time(),"asset":self.cfg.asset,
            "market":"options","mode":self.cfg.mode,"trading_enabled":False,
            "paper":True,"mark":mark,"last":last,"active":p})
        self.db.set("paper_equity_bid_estimate",estimate)
        self.db.set("paper_wallet_cash",cash)

    def loop(self):
        self.cfg.state_dir.mkdir(parents=True,exist_ok=True)
        with open(self.cfg.state_dir/"runner.lock","w") as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise RuntimeError("This lane already has a runner")
            while True:
                try:self.tick_once()
                except KeyboardInterrupt:raise
                except Exception as exc:
                    self.event("ERROR","paper_poll_error",error=str(exc))
                time.sleep(self.cfg.poll)
