import csv,gzip,hashlib,json,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone
from stage_repository_history import retained_risk,month_bounds,source_rows,stage_risk

class RetainedArchiveTest(unittest.TestCase):
    def test_actual_retained_mark_and_funding(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            for kind,step in (("mark_1m",60),("funding_1h",3600)):
                dest=out/kind;dest.mkdir()
                entries=retained_risk(root,dest,kind,step)
                self.assertEqual(len(entries),12)
                self.assertEqual(sum(p["expected_minutes"] for p in entries),366*86400//step)
                self.assertTrue(all(p["missing_minutes"]>=0 for p in entries))
                for p in entries:
                    _,rows=source_rows(dest/(p["sha256_gzip"]+".bin"),p["sha256_gzip"],p["observed_candles"],step=step,signed=kind=="funding_1h",blank_volume=True)
                    a,b=month_bounds(p["file"][:7])
                    self.assertTrue(all(a<=int(r[0])<b for r in rows))
                self.assertEqual(entries[0]["utc_start"],"2024-01-01T00:00:00+00:00")
                print(kind,"UTC 2024 observed",sum(p["observed_candles"] for p in entries),"missing",sum(p["missing_minutes"] for p in entries))
    def test_original_five_column_mark_is_normalized_without_volume_invention(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"mark.gz"
            data=b"time,open,high,low,close\n1704067200,100,101,99,100\n"
            raw=gzip.compress(data);p.write_bytes(raw)
            _,rows=source_rows(p,hashlib.sha256(raw).hexdigest(),1,blank_volume=True)
            self.assertEqual(rows,[["1704067200","100","101","99","100",""]])
            with self.assertRaises(ValueError):source_rows(p,"0"*64,1,blank_volume=True)
if __name__=="__main__":unittest.main()
