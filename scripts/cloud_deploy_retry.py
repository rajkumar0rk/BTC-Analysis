"""Bounded retries for explicitly identified transient Cloudflare GET failures.
Never print provider output, credentials, or response bodies. Ambiguous write
failures are deliberately not retried; inspect the remote release first.
"""
import os,re,subprocess,sys,time

COMMANDS={
    "info":["d1","info","btc-analysis"],
    "migrate":["d1","migrations","apply","DB","--remote"],
    "deploy":["deploy"],
    "secret":["secret","put","AUTH_HASHES_JSON"],
}
ANSI=re.compile(r"\x1b\[[0-9;]*m")
HTTP_LINE=re.compile(r"\b(GET|POST|PUT|PATCH|DELETE|HEAD) /[^\s]+\s*->\s*(\d{3})\b")
def retryable(output,operation):
    clean=ANSI.sub("",output)
    failures=HTTP_LINE.findall(clean)
    if not failures:return False
    # Only a reported read failure, not a failed mutation. Do not retry any
    # migration or secret write, even when an internal read has failed.
    if operation not in ("info","deploy"):return False
    if operation=="deploy":
        # The observed failure is the initial service lookup, before upload.
        # Other reads may happen after mutations; fail closed for them.
        if not re.search(r"GET /accounts/[0-9a-fA-F]{32}/workers/services/btc-analysis\s*->\s*(?:429|502|503|504)\b",clean):return False
        if re.search(r"\b(?:Uploaded|Deployed|Published|Created|Uploading|uploading|version ID)\b",clean,re.I):return False
    return all(method=="GET" and code in ("429","502","503","504") for method,code in failures)

def guard():
    sha=os.environ.get("VERIFIED_SHA","")
    repo=os.environ.get("GITHUB_REPOSITORY","")
    if not re.fullmatch(r"[0-9a-f]{40}",sha) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",repo):raise RuntimeError("missing verified release identity")
    r=subprocess.run(["gh","api","repos/"+repo+"/git/ref/heads/main","--jq",".object.sha"],capture_output=True,text=True,timeout=30)
    if r.returncode or r.stdout.strip()!=sha:raise RuntimeError("main changed or could not verify; refusing cloud write")

def run(operation,execute=subprocess.run,sleep=time.sleep,check_head=guard):
    if operation not in COMMANDS:raise ValueError("invalid operation")
    command=["npx","--yes","wrangler@4.157.0",*COMMANDS[operation],"--config","wrangler.release.toml"]
    secret=os.environ.get("AUTH_HASHES_JSON","") if operation=="secret" else None
    if operation=="secret" and not secret:raise RuntimeError("missing auth digest map")
    for attempt in range(1,5):
        if operation!="info":check_head()
        r=execute(command,input=secret,capture_output=True,text=True,timeout=240)
        if r.returncode==0:
            print(f"{operation}: success (attempt {attempt})",flush=True);return
        output=(r.stdout or "")+"\n"+(r.stderr or "")
        codes=HTTP_LINE.findall(ANSI.sub("",output))
        # Fixed method/status only; do not emit URLs or response content.
        detail=", ".join(f"{m} {c}" for m,c in codes) or "provider error"
        if attempt==4 or not retryable(output,operation):raise RuntimeError(f"{operation}: failed ({detail}); no further retry")
        delay=10*2**(attempt-1)
        print(f"{operation}: transient read failure ({detail}); retry {attempt+1}/4 in {delay}s",flush=True)
        sleep(delay)

if __name__=="__main__":
    try:run(sys.argv[1] if len(sys.argv)==2 else "")
    except RuntimeError as e:raise SystemExit(str(e)) from None
    except Exception:raise SystemExit("Cloud operation failed; inspect provider state before retrying.") from None
