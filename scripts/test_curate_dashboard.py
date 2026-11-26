import unittest
from curate_dashboard import select
def run(id,net,pf,monthly,detail=True,pattern="test|p"):
    return dict(id=id,symbol="ETHUSD",source="source",strategy=pattern,net=net,profit_factor=pf,drawdown=1,detail_available=detail,months=[dict(month=f"2025-{i+1:02}",net=n) for i,n in enumerate(monthly)])
class CurateTest(unittest.TestCase):
    def test_rank_and_exclude(self):
        a=run("a",10,2,[5,5])
        b=run("b",20,3,[20,0])
        c=run("c",-1,.5,[-1])
        d=run("d",40,4,[20,20],False)
        e=run("e",3,2,[3],pattern="other|p")
        chosen,reasons=select([a,b,c,d,e])
        self.assertEqual({r["id"] for r in chosen},{"a","e"})
        self.assertEqual(set(reasons),{"b","c","d"})
if __name__=="__main__":unittest.main()
