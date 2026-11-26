import unittest,json
from email.message import Message
from cloud_health_check import check,ProbeFailure
ORIGIN="https://btc-analysis.test.workers.dev"
def response(status,body,headers):
    h=Message()
    for k,v in headers:h[k]=v
    return status,h,body if isinstance(body,bytes) else json.dumps(body).encode()
def fake(path,headers=None):
    if path=="/health":return response(200,{"status":"ok","service":"btc-analysis-cloud"},[])
    if path=="/":return response(200,b"Strategy Studio",[("Content-Security-Policy","default-src 'self'; frame-ancestors 'none'"),("X-Frame-Options","DENY")])
    if headers and headers.get("Origin"):return response(403,{"error":"origin_not_allowed"},[])
    return response(401,{"error":"invalid_credentials"},[("Cache-Control","no-store, max-age=0")])
class Tests(unittest.TestCase):
    def test_success(self):
        self.assertEqual(check(ORIGIN,"",fake,lambda x:None)["authenticated_d1_read"],"not_configured")
    def test_all_failures_reported(self):
        messages=[]
        def wrong(path,headers=None):
            if path=="/":return response(200,b"Strategy Studio",[])
            if path.endswith("/operations"):return response(200,{},[])
            return fake(path,headers)
        with self.assertRaisesRegex(ProbeFailure,"failed probes: unauthenticated /v1/cloud/operations, private shell headers"):
            check(ORIGIN,"",wrong,messages.append)
        self.assertTrue(any("CSP" in m for m in messages))
    def test_optional_token_not_logged(self):
        token="A"*43;messages=[]
        with self.assertRaises(ProbeFailure):
            check(ORIGIN,token,fake,messages.append)
        self.assertNotIn(token," ".join(messages))
if __name__=="__main__":unittest.main()
