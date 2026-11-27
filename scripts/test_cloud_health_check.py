import unittest,json
from email.message import Message
from cloud_health_check import check,ProbeFailure,wait_for_release
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
    def test_release_propagation_requires_consecutive_exact_reads(self):
        expected="a"*40;old="b"*40;calls=[];sleeps=[];messages=[]
        releases=iter([expected,old,expected,expected])
        def get(path,headers=None):
            calls.append(path)
            if path=="/health":
                self.assertEqual(headers,{"Cache-Control":"no-cache"})
                return response(200,{"status":"ok","service":"btc-analysis-cloud","release_sha":next(releases)},[])
            return fake(path,headers)
        result=check(ORIGIN,"",get,messages.append,expected_sha=expected,sleep=sleeps.append)
        self.assertEqual(result["authentication_denial"],"pass")
        self.assertEqual(calls.count("/health"),4)
        self.assertEqual(sleeps,[3,3,3])
        self.assertTrue(any("release SHA not yet matched" in m for m in messages))
    def test_release_timeout_and_security_failure(self):
        expected="a"*40
        with self.assertRaisesRegex(ProbeFailure,"did not stabilize"):
            wait_for_release(fake,expected,lambda x:None,lambda x:None,attempts=2)
        calls=[]
        def insecure(path,headers=None):
            calls.append(path)
            if path=="/health":return response(200,{"status":"ok","service":"btc-analysis-cloud","release_sha":expected},[])
            if path=="/v1/cloud/capabilities" and not headers:return response(200,{},[])
            return fake(path,headers)
        with self.assertRaisesRegex(ProbeFailure,"unauthenticated /v1/cloud/capabilities"):
            check(ORIGIN,"",insecure,lambda x:None,expected_sha=expected,sleep=lambda x:None)
        self.assertEqual(calls.count("/v1/cloud/capabilities"),2) # denial and separate CORS probe, no retries
    def test_optional_token_not_logged(self):
        token="A"*43;messages=[]
        with self.assertRaises(ProbeFailure):
            check(ORIGIN,token,fake,messages.append)
        self.assertNotIn(token," ".join(messages))
if __name__=="__main__":unittest.main()
