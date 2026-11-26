"""Offline restore rehearsal for a trusted D1 export. Never writes production."""
import argparse, hashlib, json, sqlite3
from pathlib import Path

def verify(source,dest):
    source,dest=Path(source),Path(dest)
    if not source.is_file() or not 0<source.stat().st_size<=256*1024*1024:raise ValueError("invalid backup size")
    # Exclusive destination; never replace a database.
    with dest.open("xb"):pass
    db=sqlite3.connect(dest)
    try:
        db.executescript(source.read_text(encoding="utf-8"))
        if db.execute("PRAGMA integrity_check").fetchall()!=[("ok",)] or db.execute("PRAGMA foreign_key_check").fetchall():raise ValueError("database integrity check failed")
        counts={t:db.execute("SELECT count(*) FROM "+t).fetchone()[0] for t in ("strategies","revisions","results")}
        if db.execute("SELECT count(*) FROM strategies s WHERE s.latest_version != (SELECT count(*) FROM revisions r WHERE r.owner=s.owner AND r.strategy_id=s.id) OR s.latest_version != COALESCE((SELECT max(version) FROM revisions r WHERE r.owner=s.owner AND r.strategy_id=s.id),0)").fetchone()[0]:raise ValueError("revision continuity failed")
        for text,sha in db.execute("SELECT source,code_sha256 FROM revisions"):
            if hashlib.sha256(text.encode()).hexdigest()!=sha:raise ValueError("revision checksum mismatch")
        for sid,version,code,symbol,dataset,result,payload,sha in db.execute("SELECT x.strategy_id,x.version,r.code_sha256,x.symbol,x.dataset_sha256,x.result_sha256,x.payload,x.payload_sha256 FROM results x JOIN revisions r ON r.owner=x.owner AND r.strategy_id=x.strategy_id AND r.version=x.version"):
            raw=json.dumps([sid,version,code,symbol,dataset,result,payload],ensure_ascii=False,separators=(",",":"))
            if hashlib.sha256(raw.encode()).hexdigest()!=sha:raise ValueError("result checksum mismatch")
        names={x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
        if not {"strategy_quota","revision_guard","revision_advance","revision_immutable_update","revision_immutable_delete","result_quota","result_immutable"}<=names:raise ValueError("required triggers absent")
        return counts
    finally:db.close()

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("source");p.add_argument("destination");a=p.parse_args()
    try:verify(a.source,a.destination)
    except Exception:raise SystemExit("Restore rehearsal failed; no production changes made.") from None
    print("Offline restore integrity, references, revision/result digests and trigger presence passed.")
