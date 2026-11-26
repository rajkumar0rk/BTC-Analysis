"""Online consistent SQLite backup; fail-closed restore to NEW destination only."""
import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
import time
from pathlib import Path
from contextlib import closing

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def check(c):
    if c.execute("PRAGMA integrity_check").fetchall()!=[("ok",)]:
        raise ValueError("database integrity check failed")
    if c.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise ValueError("database foreign key check failed")
    tables={x[0] for x in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not {"strategies","revisions","jobs","strategy_registry","registry_events"}<=tables:
        raise ValueError("not a platform database")
    return tables

def publish(temp,destination):
    with open(temp,"rb") as f:os.fsync(f.fileno())
    os.chmod(temp,0o600)
    os.link(temp,destination)
    fd=os.open(destination.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)

def paths(source,destination):
    source=Path(source).resolve(strict=True)
    destination=Path(destination).absolute()
    if not source.is_file() or destination.exists() or destination.is_symlink():
        raise ValueError("source must exist; destination must be new")
    destination.parent.mkdir(parents=True,exist_ok=True)
    return source,destination

def backup(source,destination):
    source,destination=paths(source,destination)
    with tempfile.TemporaryDirectory(dir=destination.parent,prefix=".backup-") as d:
        temp=Path(d)/"snapshot.sqlite"
        started=time.monotonic()
        def progress(*_):
            if time.monotonic()-started>120:raise TimeoutError("backup deadline exceeded")
        with closing(sqlite3.connect(source.as_uri()+"?mode=ro",uri=True,timeout=5)) as src, closing(sqlite3.connect(temp)) as dst:
            src.backup(dst,pages=256,progress=progress,sleep=.05)
            dst.execute("PRAGMA journal_mode=DELETE")
            check(dst)
        sha=digest(temp);size=temp.stat().st_size
        publish(temp,destination)
    return {"path":str(destination),"sha256":sha,"bytes":size,"integrity":"ok"}

def restore(source,destination,expected_sha256):
    source,destination=paths(source,destination)
    import shutil
    with tempfile.TemporaryDirectory(dir=destination.parent,prefix=".restore-") as d:
        temp=Path(d)/"restored.sqlite"
        shutil.copyfile(source,temp)
        if digest(temp)!=expected_sha256:raise ValueError("backup checksum mismatch")
        with closing(sqlite3.connect(temp)) as c:
            tables=check(c);t=int(time.time())
            c.execute("""UPDATE jobs SET status=CASE WHEN status IN ('queued','cancelling') THEN 'cancelled' ELSE 'failed' END,
                         error=CASE WHEN status='running' THEN 'restored_interrupted_job' ELSE NULL END,
                         worker_token=NULL,lease_until=NULL,updated=? WHERE status IN ('queued','running','cancelling')""",(t,))
            if "paper_sessions" in tables:
                c.execute("""UPDATE paper_sessions SET status='halted',reason='restored_interrupted_session',
                          revision=revision+1,updated=? WHERE status IN ('scheduled','running')""",(t,))
            c.commit();c.execute("PRAGMA journal_mode=DELETE");check(c)
        sha=digest(temp);publish(temp,destination)
    return {"path":str(destination),"sha256":sha,"backup_sha256":expected_sha256,"integrity":"ok",
            "active_work_resumed":False}

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest="action",required=True)
    for cmd in ("backup","restore"):
        a=sub.add_parser(cmd);a.add_argument("--source",required=True);a.add_argument("--destination",required=True)
        if cmd=="restore":a.add_argument("--sha256",required=True)
    a=p.parse_args()
    r=backup(a.source,a.destination) if a.action=="backup" else restore(a.source,a.destination,a.sha256)
    print(json.dumps(r,indent=2))

if __name__=="__main__":main()
