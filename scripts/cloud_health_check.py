"""Read-only production smoke check; no tokens in arguments, logs or output."""
import os,json,re,time
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def check():
    origin=os.environ["CF_ORIGIN"]
    if not re.fullmatch(r"https://btc-analysis\.[a-z0-9-]+\.workers\.dev",origin):raise ValueError("invalid origin")
    opener=build_opener(NoRedirect())
    def get(path,headers=None):
        try:r=opener.open(Request(origin+path,headers=headers or {}),timeout=15)
        except HTTPError as e:r=e
        with r:
            data=r.read(1024*1024+1)
            if len(data)>1024*1024:raise ValueError("response too large")
            return r.code,r.headers,data
    t=time.monotonic()
    status,h,raw=get("/health")
    if status!=200 or json.loads(raw).get("service")!="btc-analysis-cloud" or json.loads(raw).get("status")!="ok":raise ValueError("health")
    latency=round((time.monotonic()-t)*1000)
    for path in ("/v1/cloud/capabilities","/v1/cloud/operations","/v1/cloud/paper/BTCUSD/state"):
        status,h,raw=get(path)
        if status!=401 or json.loads(raw).get("error")!="invalid_credentials" or h.get("Cache-Control")!="no-store":raise ValueError("unauthenticated denial")
    status,h,raw=get("/v1/cloud/capabilities",{"Origin":"https://untrusted.invalid"})
    if status!=403 or h.get("Access-Control-Allow-Origin"):raise ValueError("origin rejection")
    status,h,raw=get("/")
    if status!=200 or b"Strategy Studio" not in raw or "frame-ancestors 'none'" not in h.get("Content-Security-Policy",""):raise ValueError("private shell/CSP")
    token=os.environ.get("CF_MONITOR_TOKEN","")
    authenticated=False
    if token:
        if not re.fullmatch(r"[A-Za-z0-9_-]{43,128}",token):raise ValueError("invalid monitor credential")
        headers={"Authorization":"Bearer "+token}
        status,h,raw=get("/v1/cloud/capabilities",headers);d=json.loads(raw)
        if status!=200 or d.get("live_orders") is not False or d.get("source_execution") is not False or d.get("storage") is not True:raise ValueError("capabilities")
        status,h,raw=get("/v1/cloud/operations",headers);d=json.loads(raw)
        if status!=200 or d.get("database")!="reachable" or d.get("live_orders") is not False:raise ValueError("D1 authenticated read")
        authenticated=True
    return {"public_health_ms":latency,"authentication_denial":"pass","origin_rejection":"pass","shell_csp":"pass","authenticated_d1_read":"pass" if authenticated else "not_configured","provider_cpu":"not_measured"}
if __name__=="__main__":
    try:print(json.dumps(check()))
    except Exception:raise SystemExit("Production health/security check failed.") from None
