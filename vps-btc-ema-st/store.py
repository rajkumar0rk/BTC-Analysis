"""One SQLite writer (bot) and multiple read-only dashboard connections."""
import json,sqlite3,time
from pathlib import Path

class Store:
    def __init__(self,directory):
        Path(directory).mkdir(parents=True,exist_ok=True)
        self.path=Path(directory)/"bot.sqlite3"
        self.db=sqlite3.connect(self.path,timeout=15)
        self.db.row_factory=sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              time_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
              level TEXT NOT NULL,kind TEXT NOT NULL,data_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS exchange_fills (
              fill_id TEXT PRIMARY KEY, created_at TEXT NOT NULL,
              side TEXT NOT NULL, size REAL NOT NULL, price REAL NOT NULL,
              commission REAL NOT NULL, liquidation_charge REAL NOT NULL,
              fill_type TEXT NOT NULL, raw_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS paper_trades (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              closed_at_utc TEXT NOT NULL,
              option_symbol TEXT NOT NULL,
              asset TEXT NOT NULL,
              side TEXT NOT NULL, contracts INTEGER NOT NULL,
              gross_pnl_usd REAL NOT NULL,
              commissions_usd REAL NOT NULL, gst_usd REAL NOT NULL,
              net_pnl_usd REAL NOT NULL,
              reason TEXT NOT NULL, trade_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS option_quote_samples (
              product_id INTEGER NOT NULL,
              minute_utc INTEGER NOT NULL,
              bid REAL NOT NULL, ask REAL NOT NULL,
              underlying_mark REAL NOT NULL,
              quote_json TEXT NOT NULL,
              PRIMARY KEY(product_id,minute_utc)
            );
            CREATE TABLE IF NOT EXISTS intents (
              client_id TEXT PRIMARY KEY,action TEXT NOT NULL,
              status TEXT NOT NULL,created_at INTEGER NOT NULL,
              payload_json TEXT NOT NULL
            );
        """)
        self.db.commit()
    def claim_lane(self,asset,market,mode,execution):
        """Persist and enforce market/environment/paper-vs-exchange DB identity.

        Reject paper -> exchange, exchange -> paper, demo -> live, BTC -> ETH
        state reuse even when a process is restarted or credentials change.
        """
        identity={"asset":asset,"market":market,"mode":mode,"execution":execution}
        old=self.get("lane_identity")
        if old is not None and old!=identity:
            raise ValueError("STATE_DIR is owned by a different strategy lane: "+
                 str(old)+"; use separate state for "+str(identity))
        if old is None:
            has_paper=(self.get("paper_wallet") is not None or
                       self.get("paper_position") is not None)
            has_exchange=(self.get("active") is not None or
                          self.get("pending") is not None or
                          bool(self.db.execute("SELECT 1 FROM intents LIMIT 1").fetchone()) or
                          bool(self.db.execute("SELECT 1 FROM exchange_fills LIMIT 1").fetchone()))
            if has_paper and execution not in ("futures_paper","options_paper"):
                raise ValueError("Existing paper wallet belongs to another execution mode")
            if has_exchange and execution in ("futures_paper","options_paper"):
                raise ValueError("Exchange order/fill journal cannot be reused for paper trading")
            with self.db:
                self.db.execute("""INSERT INTO kv(key,value) VALUES(?,?)
                       ON CONFLICT(key) DO NOTHING""",
                       ("lane_identity",json.dumps(identity,separators=(",",":"))))
    def get(self,key,default=None):
        row=self.db.execute("SELECT value FROM kv WHERE key=?",(key,)).fetchone()
        return json.loads(row["value"]) if row else default
    def set(self,key,value):
        with self.db:
            self.db.execute("INSERT INTO kv VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                            (key,json.dumps(value,separators=(",",":"),default=str)))
    def event(self,level,kind,**data):
        with self.db:
            self.db.execute("INSERT INTO events(level,kind,data_json) VALUES(?,?,?)",
                            (level,kind,json.dumps(data,separators=(",",":"),default=str)))
    def intent(self,oid,action,payload):
        with self.db:
            self.db.execute("INSERT INTO intents VALUES (?,?,?,?,?)",
                            (oid,action,"submitted_or_unknown",int(time.time()),json.dumps(payload)))
    def intent_status(self,oid,status):
        with self.db:
            self.db.execute("UPDATE intents SET status=? WHERE client_id=?",(status,oid))
    def unresolved(self):
        return [dict(row) for row in self.db.execute(
            "SELECT * FROM intents WHERE status='submitted_or_unknown' ORDER BY created_at DESC").fetchall()]
    def latest_events(self,limit=100):
        rows=self.db.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?",(min(300,int(limit)),)).fetchall()
        return [dict(time_utc=r["time_utc"],level=r["level"],kind=r["kind"],data=json.loads(r["data_json"])) for r in rows]
    def add_fills(self,records):
        inserted_ids=[]
        with self.db:
            for row in records:
                meta=row.get("meta_data") or {}
                liquidation=float(meta.get("liquidation_fee_in_settling_asset") or 0)
                cur=self.db.execute("""INSERT OR IGNORE INTO exchange_fills
                  (fill_id,created_at,side,size,price,commission,liquidation_charge,fill_type,raw_json)
                  VALUES(?,?,?,?,?,?,?,?,?)""",(
                    str(row["id"]),str(row["created_at"]),str(row["side"]),
                    float(row["size"]),float(row["price"]),float(row.get("commission") or 0),
                    liquidation,str(row.get("fill_type") or ""),
                    json.dumps(row,separators=(",",":"),default=str)))
                if cur.rowcount:inserted_ids.append(str(row["id"]))
        return inserted_ids
    def fills(self):
        return [dict(r) for r in self.db.execute(
            "SELECT * FROM exchange_fills ORDER BY created_at,fill_id").fetchall()]
    def paper_transition(self,wallet,active,event,trade=None,stats=None):
        """Atomic paper cash+inventory+closed-trade update (restart-safe)."""
        with self.db:
            for key,value in (("paper_wallet",wallet),("paper_position",active),
                              ("paper_stats",stats)):
                if key=="paper_stats" and stats is None:continue
                self.db.execute("""INSERT INTO kv(key,value) VALUES(?,?)
                  ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
                  (key,json.dumps(value,separators=(",",":"),default=str)))
            self.db.execute("INSERT INTO events(level,kind,data_json) VALUES(?,?,?)",
                 ("INFO",event["kind"],json.dumps(event,separators=(",",":"),default=str)))
            if trade is not None:
                self.db.execute("""INSERT INTO paper_trades
                  (closed_at_utc,option_symbol,asset,side,contracts,gross_pnl_usd,
                   commissions_usd,gst_usd,net_pnl_usd,reason,trade_json)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                  (trade["closed_at_utc"],trade["symbol"],trade["asset"],trade["side"],
                   trade["contracts"],trade["gross_pnl_usd"],
                   trade["commissions_usd"],trade["gst_usd"],
                   trade["net_pnl_usd"],trade["reason"],
                   json.dumps(trade,separators=(",",":"),default=str)))
    def paper_trades(self):
        return [json.loads(r["trade_json"]) for r in self.db.execute(
            "SELECT trade_json FROM paper_trades ORDER BY id").fetchall()]
    def sample_quote(self,product_id,when,bid,ask,mark,quote):
        with self.db:
            self.db.execute("""INSERT OR IGNORE INTO option_quote_samples
              (product_id,minute_utc,bid,ask,underlying_mark,quote_json)
              VALUES(?,?,?,?,?,?)""",
              (int(product_id),int(when//60)*60,float(bid),float(ask),float(mark),
               json.dumps(quote,separators=(",",":"),default=str)))
    def close(self):self.db.close()
