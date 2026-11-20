"""Forward futures-paper lane, priced from fresh Delta bid/ask plus mark.

Never submits orders. Uses same BTC/ETH EMA-ST underlying signals as exchange bot.
Margin 100x isolated $10 per trade, no pre-entry liquidation guard.
Liquidation based on a 0.25% maintenance proxy, NOT actual venue mark history.
"""
import math,time
from datetime import datetime,timezone
from bot import Bot
from signals import BAR_SECONDS,signal,indicators,quantize_stop,size_contracts,trailing_points
from options_paper import good_quote,paper_stats

class FuturesPaperBot(Bot):
    def __init__(self,cfg):
        if cfg.market!="futures" or cfg.trading or not cfg.futures_paper:
            raise ValueError("Futures paper requires MARKET=futures TRADING_ENABLED=false FUTURES_PAPER_ENABLED=true")
        super().__init__(cfg)
        if self.db.get("paper_wallet") is None:
            self.db.paper_transition(cfg.portfolio,None,{"kind":"paper_futures_initialized"})

    def public_snapshot(self):
        t=self.delta.ticker(self.cfg.symbol)
        now=time.time()
        q=good_quote(t,now,self.cfg.staleness,required_size=1,max_spread_pct=0.30)
        mark=float(t.get("mark_price") or 0)
        last=float(t.get("close") or 0)
        if not q or mark<=0 or last<=0:
            raise ValueError("No valid fresh BTC/ETH futures bid/ask or mark")
        self.quote=q
        self.db.set("ticker",{"mark":mark,"last":last,"ts":q["timestamp"],
                     "best_bid":q["bid"],"best_ask":q["ask"]})
        return last,mark

    def open_paper(self,s,last,mark):
        if self.db.get("paper_position"):return
        balance=float(self.db.get("paper_wallet",self.cfg.portfolio))
        day=datetime.now(timezone.utc).astimezone(__import__("zoneinfo").ZoneInfo(
            "Asia/Kolkata")).strftime("%Y-%m-%d")
        d=self.db.get("paper_day")
        if not d or d["day"]!=day:
            d={"day":day,"start":balance,"entries":0}
            self.db.set("paper_day",d)
        if d["entries"]>=self.cfg.max_trades:return
        if balance<=d["start"]-self.cfg.daily_loss_limit:return
        if abs(last-s["signal_close"])/s["signal_close"]>0.002:return
        side=s["side"]
        fill=self.quote["ask"] if side=="buy" else self.quote["bid"]
        contracts=size_contracts(fill,self.value,self.cfg.margin,self.cfg.leverage)
        contracts=min(contracts,int(self.quote["bid_size"]),int(self.quote["ask_size"]))
        if contracts<1:return
        qty=contracts*self.value
        notional=qty*fill
        margin=notional/self.cfg.leverage
        fee=notional*.0005*1.18
        if balance<margin+fee:return
        sign=1 if side=="buy" else -1
        stop=quantize_stop(fill-sign*s["stop_distance_points"],self.tick,side)
        maint=float(self.product.get("maintenance_margin",.25))/100
        liq=((fill-margin/qty)/(1-maint) if sign==1 else
             (fill+margin/qty)/(1+maint))
        activation,distance=trailing_points(self.cfg.asset,fill)
        position={
            "asset":self.cfg.asset,"symbol":self.cfg.symbol,
            "side":side,"size":sign*contracts,"contracts":contracts,"qty":qty,
            "entry":fill,"notional_usd":notional,"margin_usd":margin,
            "entry_fee_gst_usd":fee,"entry_time":time.time(),
            "initial_stop":stop,"stop":stop,"best":fill,
            "activation_points":activation,"distance_points":distance,
            "liq_proxy":liq,"trail_active":False}
        self.db.paper_transition(balance-fee,position,{
            "kind":"futures_paper_entry","symbol":self.cfg.symbol,"side":side,
            "contracts":contracts,"fill_at_ask_or_bid":fill,
            "entry_fee_gst_usd":fee,"margin_usd":margin,
            "liq_proxy":liq,"stop":stop})
        d["entries"]+=1;self.db.set("paper_day",d)

    def close_paper(self,reason,mark):
        p=self.db.get("paper_position")
        if not p:return
        sign=1 if p["side"]=="buy" else -1
        fill=self.quote["bid"] if sign==1 else self.quote["ask"]
        gross=(fill-p["entry"])*p["qty"]*sign
        hold=(time.time()-p["entry_time"])/60
        eligible=reason!="liquidation_proxy" and hold<=30
        fee=0 if eligible or reason=="liquidation_proxy" else p["qty"]*fill*.0005*1.18
        liq_penalty=0
        if reason=="liquidation_proxy":
            liq_penalty=p["qty"]*fill*.0005*1.18
            realized=max(-p["margin_usd"],gross-liq_penalty)
        else:
            realized=gross-fee
        net=realized-p["entry_fee_gst_usd"]
        wallet=float(self.db.get("paper_wallet"))
        end_cash=max(0,wallet+realized)
        net=end_cash-wallet-p["entry_fee_gst_usd"]
        trade={
            "symbol":p["symbol"],"asset":self.cfg.asset,"market":"futures_paper",
            "closed_at_utc":datetime.now(timezone.utc).isoformat(),
            "entry_time_utc":datetime.fromtimestamp(p["entry_time"],timezone.utc).isoformat(),
            "side":p["side"],"contracts":p["contracts"],"qty":p["qty"],
            "entry_price":p["entry"],"exit_price":fill,
            "gross_pnl_usd":gross,"net_pnl_usd":net,
            "commissions_usd":(p["entry_fee_gst_usd"]+fee+liq_penalty)/1.18,
            "gst_usd":(p["entry_fee_gst_usd"]+fee+liq_penalty)*.18/1.18,
            "assumed_scalper_offer":eligible,"reason":reason,
            "margin_usd":p["margin_usd"],"liq_proxy":p["liq_proxy"],
            "underlying_exit_mark":mark}
        stats=paper_stats(self.db.paper_trades()+[trade],self.cfg.portfolio)
        # If the entire account was exhausted, wallet loss is capped in this paper ledger.
        self.db.paper_transition(end_cash,None,{
            "kind":"futures_paper_exit","symbol":p["symbol"],
            "reason":reason,"net_pnl_usd":net,"wallet_usd":end_cash},
            trade=trade,stats=stats)

    def manage_paper(self,mark):
        p=self.db.get("paper_position")
        if not p:return
        sign=1 if p["side"]=="buy" else -1
        crossed_liq=(mark<=p["liq_proxy"] if sign==1 else mark>=p["liq_proxy"])
        if crossed_liq:
            self.close_paper("liquidation_proxy",mark)
            return
        if (mark-p["entry"])*sign>=p["activation_points"]:
            p["trail_active"]=True
        if p["trail_active"]:
            p["best"]=max(mark,p["best"]) if sign==1 else min(mark,p["best"])
            next_stop=p["best"]-sign*p["distance_points"]
            p["stop"]=max(next_stop,p["stop"]) if sign==1 else min(next_stop,p["stop"])
        self.db.set("paper_position",p)
        if (mark<=p["stop"] if sign==1 else mark>=p["stop"]):
            self.close_paper("underlying_trail" if p["trail_active"] else "underlying_atr",mark)

    def on_bar(self,frame,last,mark):
        bar_ts=int(frame.index[-1].timestamp())
        processed=self.db.get("processed_bar")
        if processed is None:
            self.db.set("processed_bar",bar_ts)
            self.emit("INFO","paper_futures_warmup",bar_ts=bar_ts)
            return
        if bar_ts<=processed:return
        self.db.set("processed_bar",bar_ts)
        f=indicators(frame)
        direction=f["dir"]
        p=self.db.get("paper_position")
        if p:
            sign=1 if p["side"]=="buy" else -1
            flip=(sign==1 and direction.iloc[-2]==-1 and direction.iloc[-1]==1) or (
                  sign==-1 and direction.iloc[-2]==1 and direction.iloc[-1]==-1)
            if flip:self.close_paper("underlying_supertrend_flip",mark)
            return
        s=signal(frame,asset=self.cfg.asset)
        self.db.set("latest_signal",s or {"bar_ts":bar_ts,"side":"none"})
        if s:
            self.emit("INFO","futures_paper_signal",**s)
            self.open_paper(s,last,mark)

    def tick_once(self):
        last,mark=self.public_snapshot()
        self.manage_paper(mark)
        closed=int((time.time()-10)//BAR_SECONDS)*BAR_SECONDS-BAR_SECONDS
        previous=self.db.get("processed_bar")
        if previous is None or previous<closed:
            self.on_bar(self.bar_snapshot(),last,mark)
        p=self.db.get("paper_position")
        wallet=float(self.db.get("paper_wallet",self.cfg.portfolio))
        equity=wallet
        if p:
            sign=1 if p["side"]=="buy" else -1
            fill=self.quote["bid"] if sign==1 else self.quote["ask"]
            equity+=p["qty"]*(fill-p["entry"])*sign
        self.db.set("paper_equity_bid_estimate",equity)
        self.db.set("heartbeat",{
            "now":time.time(),"mode":self.cfg.mode,"asset":self.cfg.asset,
            "market":"futures","paper":True,"trading_enabled":False,
            "mark":mark,"last":last,"active":p})
