"""Durable SQLite registry and single-claim queue. Local deployment reference.
All ownership checks are explicit; API clients cannot claim or mutate worker state.
"""
from __future__ import annotations
import sqlite3
import json
import hashlib
import time
import uuid
from pathlib import Path
from contextlib import contextmanager

MAX_CODE=65536
MAX_RESULT=2*1024*1024
MAX_ACTIVE=8
MAX_STRATEGIES=100
MAX_VERSIONS=100
MAX_JOBS=1000
TERMINAL=("succeeded","failed","cancelled")


class Missing(Exception): pass
class Conflict(Exception): pass
class Invalid(Exception): pass


def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)


def sha(s):return hashlib.sha256(s.encode("utf-8")).hexdigest()
def now():return int(time.time())


class Store:
    def __init__(self,path):
        self.path=str(Path(path).resolve())
        Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        with self.connection() as c:
            c.executescript("""
              PRAGMA journal_mode=WAL;
              CREATE TABLE IF NOT EXISTS strategies(
                id TEXT PRIMARY KEY, owner TEXT NOT NULL, name TEXT NOT NULL, created INTEGER NOT NULL);
              CREATE TABLE IF NOT EXISTS revisions(
                strategy_id TEXT NOT NULL REFERENCES strategies(id), version INTEGER NOT NULL,
                source TEXT NOT NULL, code_sha TEXT NOT NULL, created INTEGER NOT NULL,
                PRIMARY KEY(strategy_id,version));
              CREATE TABLE IF NOT EXISTS jobs(
                id TEXT PRIMARY KEY, owner TEXT NOT NULL, request_key TEXT NOT NULL,
                request_sha TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0, created INTEGER NOT NULL, updated INTEGER NOT NULL,
                worker_token TEXT, lease_until INTEGER, result TEXT, error TEXT,
                UNIQUE(owner,request_key));
              CREATE INDEX IF NOT EXISTS jobs_queue ON jobs(status,created,id);
              CREATE INDEX IF NOT EXISTS jobs_owner ON jobs(owner,created);
            """)

    @contextmanager
    def connection(self,write=False):
        c=sqlite3.connect(self.path,timeout=10,isolation_level=None)
        c.row_factory=sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        try:
            if write:c.execute("BEGIN IMMEDIATE")
            yield c
            if write:c.commit()
        except BaseException:
            if write:c.rollback()
            raise
        finally:c.close()

    def _strategy(self,c,owner,sid):
        r=c.execute("SELECT * FROM strategies WHERE owner=? AND id=?",(owner,sid)).fetchone()
        if r is None:raise Missing("strategy not found")
        return r

    def create_strategy(self,owner,name,source):
        self._validate_source(source)
        with self.connection(True) as c:
            if c.execute("SELECT COUNT(*) FROM strategies WHERE owner=?",(owner,)).fetchone()[0]>=MAX_STRATEGIES:
                raise Conflict("strategy quota exceeded")
            sid=uuid.uuid4().hex;t=now()
            c.execute("INSERT INTO strategies VALUES(?,?,?,?)",(sid,owner,name,t))
            c.execute("INSERT INTO revisions VALUES(?,?,?,?,?)",(sid,1,source,sha(source),t))
        return self.revision(owner,sid,1)

    @staticmethod
    def _validate_source(source):
        if not isinstance(source,str) or not source.strip() or len(source.encode("utf-8"))>MAX_CODE:
            raise Invalid("invalid strategy source size")
        # Parse/execute nothing: uploaded source is untrusted inert text.

    def add_revision(self,owner,sid,source,expected_version):
        self._validate_source(source)
        with self.connection(True) as c:
            self._strategy(c,owner,sid)
            latest=c.execute("SELECT MAX(version) FROM revisions WHERE strategy_id=?",(sid,)).fetchone()[0]
            if latest!=expected_version:raise Conflict("strategy version changed")
            if latest>=MAX_VERSIONS:raise Conflict("revision quota exceeded")
            version=latest+1
            c.execute("INSERT INTO revisions VALUES(?,?,?,?,?)",(sid,version,source,sha(source),now()))
        return self.revision(owner,sid,version)

    def revision(self,owner,sid,version):
        with self.connection() as c:
            s=self._strategy(c,owner,sid)
            r=c.execute("SELECT * FROM revisions WHERE strategy_id=? AND version=?",(sid,version)).fetchone()
            if r is None:raise Missing("revision not found")
            return dict(id=sid,name=s["name"],version=r["version"],source=r["source"],code_sha256=r["code_sha"],created=r["created"])

    def strategies(self,owner):
        with self.connection() as c:
            return [dict(r) for r in c.execute("""SELECT s.id,s.name,s.created,MAX(r.version) AS latest_version
                  FROM strategies s JOIN revisions r ON r.strategy_id=s.id
                  WHERE s.owner=? GROUP BY s.id ORDER BY s.created DESC,s.id LIMIT ?""",(owner,MAX_STRATEGIES))]

    @staticmethod
    def _public(r,include_result=False):
        if r is None:raise Missing("job not found")
        d={k:r[k] for k in ("id","status","progress","created","updated","error")}
        d["request"]=json.loads(r["payload"])
        if include_result:d["result"]=json.loads(r["result"]) if r["result"] else None
        return d

    def submit(self,owner,key,payload):
        # The API only accepts schema-validated trusted fixture requests.
        if payload.get("kind")!="reference_fixture":raise Invalid("custom execution disabled")
        packed=canonical(payload);digest=sha(packed)
        with self.connection(True) as c:
            prior=c.execute("SELECT * FROM jobs WHERE owner=? AND request_key=?",(owner,key)).fetchone()
            if prior:
                if prior["request_sha"]!=digest:raise Conflict("idempotency key reused with different request")
                return self._public(prior)
            if c.execute("SELECT COUNT(*) FROM jobs WHERE owner=?",(owner,)).fetchone()[0]>=MAX_JOBS:
                raise Conflict("job history quota exceeded")
            if c.execute("SELECT COUNT(*) FROM jobs WHERE owner=? AND status IN ('queued','running','cancelling')",(owner,)).fetchone()[0]>=MAX_ACTIVE:
                raise Conflict("active job quota exceeded")
            jid=uuid.uuid4().hex;t=now()
            c.execute("""INSERT INTO jobs(id,owner,request_key,request_sha,payload,status,created,updated)
                         VALUES(?,?,?,?,?,'queued',?,?)""",(jid,owner,key,digest,packed,t,t))
            return self._public(c.execute("SELECT * FROM jobs WHERE id=?",(jid,)).fetchone())

    def job(self,owner,jid):
        with self.connection() as c:
            return self._public(c.execute("SELECT * FROM jobs WHERE owner=? AND id=?",(owner,jid)).fetchone(),True)

    def jobs(self,owner):
        with self.connection() as c:
            return [self._public(r) for r in c.execute("SELECT * FROM jobs WHERE owner=? ORDER BY created DESC,id LIMIT 100",(owner,))]

    def cancel(self,owner,jid):
        with self.connection(True) as c:
            r=c.execute("SELECT * FROM jobs WHERE owner=? AND id=?",(owner,jid)).fetchone()
            if r is None:raise Missing("job not found")
            if r["status"] in TERMINAL: return self._public(r)
            status="cancelled" if r["status"]=="queued" else "cancelling"
            c.execute("UPDATE jobs SET status=?,updated=? WHERE id=?",(status,now(),jid))
            return self._public(c.execute("SELECT * FROM jobs WHERE id=?",(jid,)).fetchone())

    def claim(self,lease_seconds=30):
        with self.connection(True) as c:
            t=now()
            # Expired worker attempts are terminal, not silently replayed.
            c.execute("""UPDATE jobs SET status=CASE WHEN status='cancelling' THEN 'cancelled' ELSE 'failed' END,
                         error=CASE WHEN status='cancelling' THEN NULL ELSE 'worker_lease_expired' END,
                         worker_token=NULL,lease_until=NULL,updated=?
                         WHERE status IN ('running','cancelling') AND lease_until<=?""",(t,t))
            # One active worker job per DB, including jobs being cancelled.
            if c.execute("SELECT 1 FROM jobs WHERE status IN ('running','cancelling') LIMIT 1").fetchone():return None
            r=c.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY created,id LIMIT 1").fetchone()
            if r is None:return None
            token=uuid.uuid4().hex
            c.execute("UPDATE jobs SET status='running',worker_token=?,lease_until=?,updated=? WHERE id=?",
                      (token,t+lease_seconds,t,r["id"]))
            return r["id"],token,json.loads(r["payload"])

    def heartbeat(self,jid,token,progress,lease_seconds=30):
        if type(progress) is not int or not 0<=progress<=99:raise Invalid("invalid progress")
        with self.connection(True) as c:
            t=now()
            r=c.execute("SELECT * FROM jobs WHERE id=? AND worker_token=?",(jid,token)).fetchone()
            if r is None or r["lease_until"]<=t or r["status"]!="running":return False
            c.execute("UPDATE jobs SET progress=MAX(progress,?),lease_until=?,updated=? WHERE id=?",
                      (progress,t+lease_seconds,t,jid))
            return True

    def finish(self,jid,token,result=None,error=None):
        packed=None if result is None else canonical(result)
        if packed is not None and len(packed.encode("utf-8"))>MAX_RESULT:raise Invalid("result too large")
        with self.connection(True) as c:
            t=now()
            r=c.execute("SELECT * FROM jobs WHERE id=? AND worker_token=?",(jid,token)).fetchone()
            if r is None or r["lease_until"]<=t or r["status"] not in ("running","cancelling"):
                return False
            cancelled=r["status"]=="cancelling"
            status="cancelled" if cancelled else "failed" if error is not None else "succeeded"
            if status=="succeeded" and packed is None:raise Invalid("successful job requires result")
            c.execute("""UPDATE jobs SET status=?,progress=?,result=?,error=?,worker_token=NULL,
                         lease_until=NULL,updated=? WHERE id=?""",
                      (status,100 if status=="succeeded" else r["progress"],
                       packed if status=="succeeded" else None,error if status=="failed" else None,t,jid))
            return True
