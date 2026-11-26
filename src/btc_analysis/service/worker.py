"""Separate supervised trusted-fixture worker. Never imports stored strategy source.
A subprocess with hard wall limit for bounded bundled code; NOT untrusted-code isolation.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .store import Store,MAX_RESULT
from .fixture import execute_fixture


def child():
    # Only a bundled fixture handler; request input is schema checked again.
    import resource
    resource.setrlimit(resource.RLIMIT_CPU,(20,20))
    resource.setrlimit(resource.RLIMIT_FSIZE,(MAX_RESULT,MAX_RESULT))
    resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024))
    payload=json.load(sys.stdin)
    def progress(n):
        print(json.dumps({"progress":n}),file=sys.stderr,flush=True);return True
    result=execute_fixture(payload,progress)
    json.dump(result,sys.stdout,separators=(",",":"),allow_nan=False)


def work_once(store:Store,timeout=30):
    claim=store.claim()
    if claim is None:return False
    jid,token,payload=claim
    # No API credentials or inherited secrets in child environment. Fixed module,
    # no user paths, shell commands or stored source. Files created in private temp.
    try:
        with tempfile.TemporaryDirectory(prefix="btc-fixture-") as directory:
            out=Path(directory)/"result.json";err=Path(directory)/"progress.log"
            env={"PATH":os.defpath,"PYTHONUTF8":"1","TZ":"UTC"}
            with out.open("wb") as o,err.open("wb") as e:
                process=subprocess.Popen([sys.executable,"-I","-m","btc_analysis.service.worker","--child"],
                    stdin=subprocess.PIPE,stdout=o,stderr=e,env=env,cwd=directory,start_new_session=True)
                try:
                    process.stdin.write(json.dumps(payload).encode());process.stdin.close()
                    started=time.monotonic()
                    while True:
                        progress=0
                        for line in err.read_text(errors="replace").splitlines():
                            try:progress=max(progress,int(json.loads(line)["progress"]))
                            except (ValueError,KeyError,TypeError):pass
                        if not store.heartbeat(jid,token,min(99,progress)):
                            store.finish(jid,token,error="cancelled_or_lease_lost");break
                        if time.monotonic()-started>timeout:
                            store.finish(jid,token,error="worker_timeout");break
                        if process.poll() is not None:
                            if process.returncode!=0:
                                store.finish(jid,token,error="fixture_execution_failed");break
                            if out.stat().st_size>MAX_RESULT:
                                store.finish(jid,token,error="result_too_large");break
                            result=json.loads(out.read_text())
                            if result.get("kind")!="reference_fixture" or result.get("synthetic") is not True:
                                raise ValueError("invalid fixture result")
                            store.finish(jid,token,result=result);break
                        time.sleep(.05)
                finally:
                    if process.poll() is None:
                        import signal
                        try:os.killpg(process.pid,signal.SIGKILL)
                        except ProcessLookupError:pass
                    process.wait()
    except Exception:
        store.finish(jid,token,error="worker_internal_failure")
    return True


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--child",action="store_true");p.add_argument("--db")
    p.add_argument("--once",action="store_true")
    a=p.parse_args()
    if a.child:child();return
    if not a.db:p.error("--db required")
    store=Store(a.db)
    while True:
        ran=work_once(store)
        if a.once:return
        if not ran:time.sleep(1)


if __name__=="__main__":main()
