"""Read-only production smoke check with redacted per-probe diagnostics."""
import os,json,re,time,subprocess,tempfile,sys
from pathlib import Path
from email.parser import BytesParser

class ProbeFailure(Exception):
    pass

def fetch(origin,path,headers=None):
    # Use the same HTTP client as the successful deploy probe. No redirects,
    # no auth token in argv, stdout, or error text. Response files are private.
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);header_file=root/"request.headers"
        header_file.write_text("".join(f"{k}: {v}\n" for k,v in (headers or {}).items()))
        args=["curl","--silent","--show-error","--max-time","15","--connect-timeout","8",
              "--max-filesize","1048576","--proto","=https","--dump-header",str(root/"headers"),
              "--output",str(root/"body"),"--write-out","%{http_code}"]
        if headers:args+=["--header","@"+str(header_file)]
        r=subprocess.run(args+[origin+path],capture_output=True,text=True,timeout=20)
        if r.returncode or not re.fullmatch(r"[0-9]{3}",r.stdout):
            raise ProbeFailure("transport failure (curl exit "+str(r.returncode)+")")
        raw=(root/"headers").read_bytes()
        # A proxy CONNECT or informational response may precede final headers.
        blocks=re.split(rb"\r?\n\r?\n",raw)
        final=next((b for b in reversed(blocks) if b.startswith(b"HTTP/")),None)
        if final is None:raise ProbeFailure("response headers missing")
        h=BytesParser().parsebytes(final.split(b"\n",1)[1]+b"\r\n\r\n")
        body=(root/"body").read_bytes()
        if len(body)>1048576:raise ProbeFailure("response too large")
        return int(r.stdout),h,body

def wait_for_release(get,expected_sha,report=print,sleep=time.sleep,attempts=20):
    """Read-only propagation gate. Require two consecutive exact release reads."""
    if not re.fullmatch(r"[0-9a-f]{40}",expected_sha):raise ProbeFailure("invalid expected release SHA")
    stable=0
    for attempt in range(1,attempts+1):
        try:
            status,h,raw=get("/health",{"Cache-Control":"no-cache"})
            if status!=200:reason=f"HTTP {status}"
            else:
                d=json.loads(raw)
                if not isinstance(d,dict) or d.get("service")!="btc-analysis-cloud" or d.get("status")!="ok":
                    reason="unexpected health service or status"
                elif d.get("release_sha")!=expected_sha:
                    reason="release SHA not yet matched"
                else:
                    stable+=1
                    report(f"PASS release health sample {stable}/2 (attempt {attempt}/{attempts})")
                    if stable==2:return status,h,raw
                    reason=None
        except Exception:
            reason="invalid health response or transport failure"
        if reason is not None:
            stable=0
            report(f"WAIT release health (attempt {attempt}/{attempts}): {reason}")
        if attempt<attempts:sleep(3)
    raise ProbeFailure("exact release SHA did not stabilize within bounded health attempts")

def check(origin=None,token=None,get=None,report=print,expected_sha=None,sleep=time.sleep):
    origin=origin if origin is not None else os.environ.get("CF_ORIGIN","")
    token=token if token is not None else os.environ.get("CF_MONITOR_TOKEN","")
    if not re.fullmatch(r"https://btc-analysis\.[a-z0-9-]+\.workers\.dev",origin):raise ProbeFailure("invalid origin configuration")
    if token and not re.fullmatch(r"[A-Za-z0-9_-]{43,128}",token):raise ProbeFailure("invalid optional monitor credential format")
    get=get or (lambda path,headers=None:fetch(origin,path,headers))
    if expected_sha is not None:
        base_get=get
        # Poll only read-only health. Never retry migrations, secret writes or
        # an actual security-policy violation to turn a failure into success.
        def get(path,headers=None):
            if path=="/health":return wait_for_release(base_get,expected_sha,report,sleep)
            return base_get(path,headers)
    errors=[];summary={}
    def probe(label,path,expected,validate,headers=None):
        try:
            started=time.monotonic()
            status,h,raw=get(path,headers)
            if status!=expected:raise ProbeFailure(f"HTTP {status}, expected {expected}")
            validate(h,raw)
            report(f"PASS {label} (HTTP {status})")
            return round((time.monotonic()-started)*1000)
        except ProbeFailure as e:
            report(f"FAIL {label}: {e}");errors.append(label)
        except Exception:
            report(f"FAIL {label}: invalid response or transport exception");errors.append(label)
        return None
    def require(condition,message):
        if not condition:raise ProbeFailure(message)
    def payload(raw):
        try:d=json.loads(raw)
        except (ValueError,UnicodeError):raise ProbeFailure("invalid JSON") from None
        require(isinstance(d,dict),"expected JSON object")
        return d
    def health(h,raw):
        d=payload(raw);require(d.get("service")=="btc-analysis-cloud" and d.get("status")=="ok","unexpected service or status")
        if expected_sha is not None:require(d.get("release_sha")==expected_sha,"release SHA mismatch")
    def deny(h,raw):
        require(payload(raw).get("error")=="invalid_credentials","unexpected denial response")
        directives={x.strip().lower() for v in h.get_all("Cache-Control",[]) for x in v.split(",")}
        require("no-store" in directives,"Cache-Control no-store missing")
    def origin_denied(h,raw):
        require(payload(raw).get("error")=="origin_not_allowed","unexpected origin rejection")
        require(not h.get("Access-Control-Allow-Origin"),"CORS allow-origin present")
    def shell(h,raw):
        require(b"Strategy Studio" in raw,"Studio shell marker missing")
        directives=[x.strip().lower().split() for v in h.get_all("Content-Security-Policy",[]) for x in v.split(";")]
        require(["frame-ancestors","'none'"] in directives,"CSP frame-ancestors none missing")
        require(any(v.strip().upper()=="DENY" for v in h.get_all("X-Frame-Options",[])),"X-Frame-Options DENY missing")
    def capabilities(h,raw):
        d=payload(raw);require(d.get("live_orders") is False and d.get("source_execution") is False and d.get("storage") is True,"unexpected capability flags")
    def operations(h,raw):
        d=payload(raw);require(d.get("database")=="reachable" and d.get("live_orders") is False,"D1 read or capability failure")
    summary["public_health_ms"]=probe("public health","/health",200,health)
    for path in ("/v1/cloud/capabilities","/v1/cloud/operations","/v1/cloud/paper/BTCUSD/state"):
        probe("unauthenticated "+path,path,401,deny)
    probe("untrusted origin","/v1/cloud/capabilities",403,origin_denied,{"Origin":"https://untrusted.invalid"})
    probe("private shell headers","/",200,shell)
    if token:
        headers={"Authorization":"Bearer "+token}
        probe("authenticated capabilities","/v1/cloud/capabilities",200,capabilities,headers)
        probe("authenticated D1 read","/v1/cloud/operations",200,operations,headers)
    if errors:raise ProbeFailure("failed probes: "+", ".join(errors))
    return {**summary,"authentication_denial":"pass","origin_rejection":"pass","shell_csp":"pass","authenticated_d1_read":"pass" if token else "not_configured","provider_cpu":"not_measured"}

if __name__=="__main__":
    try:
        if sys.argv[1:] not in ([],["--release"]):raise ProbeFailure("invalid check arguments")
        print(json.dumps(check(expected_sha=os.environ.get("VERIFIED_SHA","") if sys.argv[1:] else None)))
    except ProbeFailure as e:raise SystemExit("Production check failed: "+str(e)) from None
    except Exception:raise SystemExit("Production check failed: unexpected internal exception") from None
