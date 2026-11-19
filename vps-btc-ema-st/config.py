"""Safe configuration for a single-symbol BTCUSD strategy runner."""
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

APP_DIR=Path(__file__).resolve().parent
ROOT=APP_DIR.parent

def flag(name,default=False):
    raw=os.getenv(name,str(default)).strip().lower()
    if raw not in ("true","false","1","0","yes","no"):
        raise ValueError(name+" must be true/false")
    return raw in ("true","1","yes")

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

    @property
    def base_url(self):
        return ("https://cdn-ind.testnet.deltaex.org" if self.mode=="demo"
                else "https://api.india.delta.exchange")

    @classmethod
    def read(cls,require_keys=False):
        load_dotenv(APP_DIR/".env",override=False)
        mode=os.getenv("MODE","demo").strip().lower()
        if mode not in ("demo","live"):
            raise ValueError("MODE must be demo or live; unknown URLs are forbidden")
        active=flag("TRADING_ENABLED",False)
        prefix="DELTA_DEMO" if mode=="demo" else "DELTA_LIVE"
        key=os.getenv(prefix+"_API_KEY","").strip()
        secret=os.getenv(prefix+"_API_SECRET","").strip()
        if (require_keys or active) and not (key and secret):
            raise ValueError("Missing "+prefix+" API credentials")
        if mode=="live" and active:
            if os.getenv("LIVE_TRADING_ACK")!="I_ACCEPT_REAL_BTCUSD_TRADES":
                raise ValueError("Live trading is locked: set LIVE_TRADING_ACK to exact acknowledgement")
        if active and not flag("ISOLATED_MARGIN_CONFIRMED"):
            raise ValueError("Confirm isolated mode and no auto-add margin on the exchange UI first")
        portfolio=float(os.getenv("PORTFOLIO_BUDGET_USD","100"))
        margin=float(os.getenv("MARGIN_PER_TRADE_USD","10"))
        leverage=int(os.getenv("LEVERAGE","100"))
        daily=float(os.getenv("DAILY_LOSS_LIMIT_USD","10"))
        max_trades=int(os.getenv("MAX_TRADES_PER_DAY","10"))
        buffer=float(os.getenv("MIN_LIQUIDATION_BUFFER_PCT","0.25"))
        staleness=int(os.getenv("MAX_MARK_STALENESS_SECONDS","15"))
        poll=float(os.getenv("POLL_SECONDS","3"))
        host=os.getenv("DASHBOARD_HOST","127.0.0.1")
        port=int(os.getenv("DASHBOARD_PORT","8765"))
        if not (portfolio>0 and margin>0 and margin<=portfolio and 0<leverage<=200):
            raise ValueError("Unsafe portfolio/margin/leverage configuration")
        if not (0<daily<=portfolio and 1<=max_trades<=100 and 0<=buffer<2):
            raise ValueError("Invalid trading risk limits")
        if poll<2 or staleness<3:
            raise ValueError("Poll too rapid or staleness threshold too small")
        if host not in ("127.0.0.1","localhost","::1"):
            raise ValueError("Dashboard must bind to loopback only; use SSH tunnel")
        state=Path(os.getenv("STATE_DIR","./state"))
        if not state.is_absolute():state=APP_DIR/state
        return cls(mode,active,key,secret,portfolio,margin,leverage,daily,max_trades,
                   flag("HALT_AFTER_LIQUIDATION",True),buffer,staleness,poll,host,port,state)
