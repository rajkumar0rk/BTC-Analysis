import unittest
from types import SimpleNamespace
from cloud_deploy_retry import retryable,run

GET="GET /accounts/"+("a"*32)+"/workers/services/btc-analysis -> 504 Gateway Timeout"
class RetryTests(unittest.TestCase):
    def test_classifier(self):
        self.assertTrue(retryable(GET,"deploy"))
        self.assertTrue(retryable(GET,"info"))
        for operation in ("migrate","secret"):self.assertFalse(retryable(GET,operation))
        for s in ("POST /workers -> 504", "GET /other -> 504",GET.replace("504","403"),"Uploaded worker\n"+GET,GET+"\nPOST /workers -> 503"):
            self.assertFalse(retryable(s,"deploy"))
    def test_retry_and_guard(self):
        results=iter([SimpleNamespace(returncode=1,stdout="",stderr=GET),SimpleNamespace(returncode=0,stdout="",stderr="")]);guards=[];delays=[]
        run("deploy",lambda *a,**k:next(results),delays.append,lambda:guards.append(1))
        self.assertEqual(guards,[1,1]);self.assertEqual(delays,[10])
    def test_no_ambiguous_mutation_retry(self):
        delays=[]
        with self.assertRaises(RuntimeError):
            run("migrate",lambda *a,**k:SimpleNamespace(returncode=1,stdout="",stderr=GET),delays.append,lambda:None)
        self.assertEqual(delays,[])
    def test_stale_guard(self):
        calls=[]
        def guard():raise RuntimeError("stale")
        with self.assertRaisesRegex(RuntimeError,"stale"):run("deploy",lambda *a,**k:calls.append(1),lambda _:None,guard)
        self.assertEqual(calls,[])
if __name__=="__main__":unittest.main()
