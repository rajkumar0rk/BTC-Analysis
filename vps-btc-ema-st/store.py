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
            CREATE TABLE IF NOT EXISTS intents (
              client_id TEXT PRIMARY KEY,action TEXT NOT NULL,
              status TEXT NOT NULL,created_at INTEGER NOT NULL,
              payload_json TEXT NOT NULL
            );
        """)
        self.db.commit()
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
        count=0
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
                count+=max(0,cur.rowcount)
        return count
    def fills(self):
        return [dict(r) for r in self.db.execute(
            "SELECT * FROM exchange_fills ORDER BY created_at,fill_id").fetchall()]
    def close(self):self.db.close()
