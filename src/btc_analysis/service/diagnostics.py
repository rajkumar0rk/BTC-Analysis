"""Bounded syntax diagnostics only. Never evaluates or imports supplied source."""
import json
import os
import subprocess
import sys
import threading
from hashlib import sha256

MAX_SOURCE=65536
SLOTS=threading.BoundedSemaphore(2)


class DiagnosticUnavailable(Exception):pass


def validate_source(source):
    if not isinstance(source,str) or not source.strip():
        raise ValueError("source must not be empty")
    try:raw=source.encode("utf-8")
    except UnicodeError as exc:raise ValueError("invalid Unicode source") from exc
    if len(raw)>MAX_SOURCE:raise ValueError("source exceeds 64 KiB")
    if not SLOTS.acquire(blocking=False):
        raise DiagnosticUnavailable("syntax checker busy")
    try:
        try:
            child=subprocess.run([sys.executable,"-I","-m","btc_analysis.service.diagnostics","--child"],
                input=raw,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                env={"PATH":os.defpath,"PYTHONUTF8":"1","TZ":"UTC"},
                timeout=4,check=True)
            data=json.loads(child.stdout)
        except (subprocess.SubprocessError,OSError,ValueError) as exc:
            raise DiagnosticUnavailable("syntax checker unavailable") from exc
        return {"source_sha256":sha256(raw).hexdigest(),"syntax_valid":not data["diagnostics"],
                "diagnostics":data["diagnostics"],"execution_allowed":False,
                "python_version":data["python_version"]}
    finally:SLOTS.release()


def child():
    # Compile to bytecode only; never run that bytecode. Compiler catches scope
    # errors which AST-only parsing misses. Resource limits are not a sandbox.
    import resource
    resource.setrlimit(resource.RLIMIT_CPU,(2,2))
    resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
    source=sys.stdin.buffer.read(MAX_SOURCE+1)
    if len(source)>MAX_SOURCE:raise ValueError("source limit")
    diagnostics=[]
    try:
        compile(source.decode("utf-8"),"<strategy>","exec",dont_inherit=True)
    except SyntaxError as exc:
        diagnostics.append({"severity":"error","message":str(exc.msg)[:300],
            "line":max(1,exc.lineno or 1),"column":max(1,exc.offset or 1),
            "end_line":max(1,exc.end_lineno or exc.lineno or 1),
            "end_column":max(1,exc.end_offset or (exc.offset or 1)+1)})
    except (ValueError,OverflowError,RecursionError):
        diagnostics.append({"severity":"error","message":"Source cannot be compiled",
            "line":1,"column":1,"end_line":1,"end_column":2})
    print(json.dumps({"diagnostics":diagnostics,"python_version":".".join(map(str,sys.version_info[:3]))}))


if __name__=="__main__":
    if sys.argv[1:]!=["--child"]:raise SystemExit(2)
    child()
