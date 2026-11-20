"""Configuration for independent BTC/ETH futures and options research lanes."""
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

APP_DIR=Path(__file__).resolve().parent
ROOT=APP_DIR.parent

def flag(name,default=False):
    v=os.getenv(name,str(default)).strip().lower()
    if v not in ("true","false","yes","no","1","0"):
        raise ValueError(name+" must be true/false")
    return v in ("true","yes","1")

def lane_state(asset,market,mode="demo"):
    return APP_DIR/"state"/mode/(asset+"_"+market)

@dataclass(frozen=True)
class Config:
    mode:str
    trading:bool
    key:str
    secret:str
    portfolio:float
    margin:float
    leverage:int
    daily_loss_limit:float
    max_trades:int
    halt_on_liquidation:bool
    buffer_pct:float
    staleness:int
    poll:float
    host:str
    port:int
    state_dir:Path
    asset:str="BTC"
    market:str="futures"
    option_premium:float=10.0
    option_min_dte_hours:float=36.0
    option_max_dte_days:float=14.0
    option_spread_max_pct:float=10.0
    option_fee_rate:float=0.0001
    option_fee_cap_pct:float=3.5
    futures_paper:bool=True

    @property
    def symbol(self):
        return self.asset+"USD"

    @property
    def lane(self):
        return self.asset+"_"+self.market

    @property
    def base_url(self):
        return ("https://cdn-ind.testnet.deltaex.org" if self.mode=="demo"
                else "https://api.india.delta.exchange")

    @classmethod
    def read(cls,require_keys=False):
        load_dotenv(APP_DIR/".env",override=False)
        mode=os.getenv("MODE","demo").strip().lower()
        if mode not in ("demo","live"):
            raise ValueError("MODE must be demo/live")
        asset=os.getenv("ASSET","BTC").upper().strip()
        market=os.getenv("MARKET","futures").lower().strip()
        if asset not in ("BTC","ETH"):raise ValueError("ASSET must be BTC/ETH")
        if market not in ("futures","options"):raise ValueError("MARKET must be futures/options")
        trading=flag("TRADING_ENABLED",False)
        if market=="options" and trading:
            raise ValueError("Options run in quote-based PAPER mode only; real/demo order writes intentionally disabled")
        prefix="DELTA_DEMO" if mode=="demo" else "DELTA_LIVE"
        key=os.getenv(prefix+"_API_KEY","").strip()
        secret=os.getenv(prefix+"_API_SECRET","").strip()
        if (require_keys or trading) and not(key and secret):
            raise ValueError("Missing "+prefix+" credentials")
        if mode=="live" and trading:
            if os.getenv("LIVE_TRADING_ACK")!="I_ACCEPT_REAL_"+asset+"USD_TRADES":
                raise ValueError("Live trading is locked for "+asset+"USD")
        if market=="futures" and trading and not flag("ISOLATED_MARGIN_CONFIRMED"):
            raise ValueError("Confirm isolated mode and disable auto-add margin in exchange UI first")
        portfolio=float(os.getenv("PORTFOLIO_BUDGET_USD","100"))
        margin=float(os.getenv("MARGIN_PER_TRADE_USD","10"))
        leverage=int(os.getenv("LEVERAGE","100"))
        daily=float(os.getenv("DAILY_LOSS_LIMIT_USD","10"))
        ntrades=int(os.getenv("MAX_TRADES_PER_DAY","10"))
        buffer=float(os.getenv("MIN_LIQUIDATION_BUFFER_PCT","0.25"))
        staleness=int(os.getenv("MAX_MARK_STALENESS_SECONDS","15"))
        poll=float(os.getenv("POLL_SECONDS","3"))
        host=os.getenv("DASHBOARD_HOST","127.0.0.1")
        port=int(os.getenv("DASHBOARD_PORT","8765"))
        optpremium=float(os.getenv("OPTION_PREMIUM_BUDGET_USD","10"))
        min_dte=float(os.getenv("OPTION_MIN_DTE_HOURS","36"))
        max_dte=float(os.getenv("OPTION_MAX_DTE_DAYS","14"))
        spread=float(os.getenv("OPTION_MAX_SPREAD_PCT","10"))
        fee=float(os.getenv("OPTION_TAKER_FEE_RATE","0.0001"))
        cap=float(os.getenv("OPTION_PREMIUM_FEE_CAP_PCT","3.5"))
        if not(portfolio>0 and 0<margin<=portfolio and 0<leverage<=200):
            raise ValueError("Unsafe portfolio/margin/leverage")
        if not(0<daily<=portfolio and 1<=ntrades<=100 and 0<=buffer<2):
            raise ValueError("Invalid daily risk limits")
        if not(0<optpremium<=portfolio and 24<=min_dte<=24*10
                and min_dte/24<max_dte<=45 and 0<spread<=50
                and 0<=fee<=0.01 and 0<cap<=20):
            raise ValueError("Invalid options quote/premium constraints")
        if poll<2 or staleness<3:
            raise ValueError("Invalid polling/staleness values")
        if host not in ("127.0.0.1","localhost","::1"):
            raise ValueError("Dashboard must bind only to loopback")
        state=Path(os.getenv("STATE_DIR","").strip() or lane_state(asset,market,mode))
        if not state.is_absolute():state=APP_DIR/state
        if state.resolve()==APP_DIR.resolve():
            raise ValueError("STATE_DIR may not be application root")
        return cls(mode,trading,key,secret,portfolio,margin,leverage,daily,ntrades,
                   flag("HALT_AFTER_LIQUIDATION",True),buffer,staleness,poll,host,port,
                   state,asset,market,optpremium,min_dte,max_dte,spread,fee,cap,
                   flag("FUTURES_PAPER_ENABLED",True))
