import unittest
import tempfile
import gzip
import json
from pathlib import Path
from decimal import Decimal as D
from datetime import datetime,timezone
from dataclasses import replace
from btc_analysis.contracts import Instrument, AssetClass, Timeframe
from btc_analysis.data import HistoryStore, ingest_delta, aggregate, CoverageError, SessionCalendar
from btc_analysis.data.store import sha_file, SOURCE, MAX_QUERY_ROWS
from btc_analysis.data.calendar import ContinuousCalendar

T=1735689600
I=Instrument("delta_india","BTCUSD",AssetClass.CRYPTO_PERPETUAL,"USD","USD",D(".1"),D(".001"),D(1))
def iso(t):return datetime.fromtimestamp(t,timezone.utc).isoformat()

class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.src=self.root/"source";self.src.mkdir()
        self.dst=self.root/"store"
        self.file=self.src/"2025-01.csv.gz"

    def fixture(self, offsets=(0,1,2,3,4,5), end=6, transform=None):
        with gzip.open(self.file,"wt") as f:
            f.write("time,open,high,low,close,volume\n")
            for n in offsets:
                row=f"{T+n*60},{100+n},{102+n},{99+n},{101+n},1.125"
                f.write((transform(row,n) if transform else row)+"\n")
        m=dict(source=SOURCE,symbol="BTCUSD",resolution="1m",
               timestamp_unit="unix_seconds_utc",timestamp_label="as_returned_by_API",
               partitions=[dict(file=self.file.name,utc_start=iso(T),utc_end_exclusive=iso(T+end*60),
                                expected_minutes=end,observed_candles=len(offsets),
                                missing_minutes=end-len(offsets),sha256_gzip=sha_file(self.file))])
        (self.src/"manifest.json").write_text(json.dumps(m))
        return m

    def ingest(self,verified=False):
        return ingest_delta(self.src,self.dst,"BTCUSD",timestamp_label="open" if verified else "unverified",
                            label_verified=verified,label_evidence="synthetic fixture known open" if verified else "")

    def test_roundtrip_and_no_future(self):
        self.fixture();m=self.ingest(True)
        with HistoryStore(self.dst,"BTCUSD") as s:
            self.assertEqual(s.key,m["manifest_sha256"])
            self.assertEqual(s.query(T,T+360).num_rows,6)
            rows=list(s.iter_candles(I,T,T+360,as_of=T+179))
            self.assertEqual(len(rows),2)
            self.assertEqual(rows[0].volume,D("1.125"))
            self.assertEqual(rows[1].close,D(102))
            self.assertTrue(s.dataset_ref(I,T,T+360).coverage_verified)

    def test_unverified_timestamp(self):
        self.fixture();self.ingest()
        with HistoryStore(self.dst,"BTCUSD") as s:
            with self.assertRaises(CoverageError):s.query(T,T+360)
            self.assertEqual(s.query(T,T+360,assume_open=True).num_rows,6)
            with self.assertRaises(CoverageError):s.dataset_ref(I,T,T+360)

    def test_gap_and_strict(self):
        self.fixture((0,1,3,5));self.ingest(True)
        with HistoryStore(self.dst,"BTCUSD") as s:
            c=s.coverage(T-60,T+420)
            self.assertEqual(c.missing_rows,4)
            self.assertEqual(c.gaps,((T-60,T),(T+120,T+180),(T+240,T+300),(T+360,T+420)))
            with self.assertRaises(CoverageError):s.query(T,T+360)
            self.assertEqual(s.query(T,T+360,strict=False).num_rows,4)

    def test_session_coverage(self):
        self.fixture((0,1,4,5));self.ingest(True)
        cal=SessionCalendar("fixture",T,T+360,((T,T+120),(T+240,T+360)))
        with HistoryStore(self.dst,"BTCUSD") as s:
            self.assertTrue(s.coverage(T,T+360,cal).complete)
            self.assertEqual(s.query(T,T+360,calendar=cal).num_rows,4)

    def test_duplicate_unsorted_offgrid(self):
        for offsets in ((0,0,2),(0,2,1)):
            with self.subTest(offsets=offsets):
                self.fixture(offsets)
                with self.assertRaises(ValueError):self.ingest()
        self.fixture(transform=lambda row,n:row.replace(str(T),str(T+1),1) if n==0 else row)
        with self.assertRaises(ValueError):self.ingest()

    def test_invalid_ohlcv(self):
        self.fixture(transform=lambda row,n:row.replace(",102,",",90,") if n==0 else row)
        with self.assertRaises(ValueError):self.ingest()

    def test_source_corruption(self):
        self.fixture()
        with self.file.open("ab") as f:f.write(b"bad")
        with self.assertRaisesRegex(ValueError,"checksum"):self.ingest()

    def test_manifest_count_mismatch(self):
        m=self.fixture();m["partitions"][0]["observed_candles"]=5
        (self.src/"manifest.json").write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,"counts"):self.ingest()

    def test_immutable_snapshot_and_reuse(self):
        self.fixture();first=self.ingest(True)
        p=next((self.dst/"delta_india"/"BTCUSD"/"1m"/"objects").glob("*.parquet"))
        mtime=p.stat().st_mtime_ns
        self.assertEqual(first,self.ingest(True))
        self.assertEqual(mtime,p.stat().st_mtime_ns)
        self.fixture(end=7,offsets=tuple(range(7)));second=self.ingest(True)
        self.assertNotEqual(first["manifest_sha256"],second["manifest_sha256"])
        with HistoryStore(self.dst,"BTCUSD",first["manifest_sha256"]) as s:
            self.assertEqual(s.query(T,T+360).num_rows,6)

    def test_derived_checksum(self):
        self.fixture();self.ingest(True)
        p=next((self.dst/"delta_india"/"BTCUSD"/"1m"/"objects").glob("*.parquet"))
        with p.open("ab") as f:f.write(b"bad")
        with HistoryStore(self.dst,"BTCUSD") as s:
            with self.assertRaisesRegex(ValueError,"checksum"):s.query(T,T+360)

    def test_aggregation(self):
        self.fixture();self.ingest(True)
        with HistoryStore(self.dst,"BTCUSD") as s:
            a=list(aggregate(s.iter_candles(I,T,T+360),Timeframe(180),as_of=T+299))
            self.assertEqual(len(a),1)
            self.assertEqual((a[0].open,a[0].high,a[0].low,a[0].close,a[0].volume),
                             (D(100),D(104),D(99),D(103),D("3.375")))
            self.assertEqual(int(a[0].close_utc.timestamp()),T+180)

    def test_aggregation_gap(self):
        self.fixture((0,2,3,4,5));self.ingest(True)
        with HistoryStore(self.dst,"BTCUSD") as s:
            with self.assertRaises(CoverageError):
                list(aggregate(s.iter_candles(I,T,T+360,strict=False),Timeframe(180)))
            a=list(aggregate(s.iter_candles(I,T,T+360,strict=False),Timeframe(180),strict=False))
            self.assertEqual(len(a),1)

    def test_bounded_query(self):
        self.fixture();self.ingest(True)
        with HistoryStore(self.dst,"BTCUSD") as s:
            with self.assertRaisesRegex(ValueError,"too large"):
                s.query(T,T+(MAX_QUERY_ROWS+1)*60)
            self.assertEqual(sum(b.num_rows for b in s.iter_batches(T,T+360,batch_size=2)),6)

    def test_failed_reimport_keeps_pointer(self):
        self.fixture();m=self.ingest(True)
        self.fixture((0,0,1))
        with self.assertRaises(ValueError):self.ingest(True)
        with HistoryStore(self.dst,"BTCUSD") as s:self.assertEqual(s.key,m["manifest_sha256"])

    def test_unmanifested_file(self):
        self.fixture();(self.src/"2025-02.csv.gz").write_bytes(b"unreviewed")
        with self.assertRaisesRegex(ValueError,"unmanifested"):self.ingest(True)

    def test_decimal_precision(self):
        self.fixture(transform=lambda row,n:row.replace("1.125","0.0000000000000000001"))
        with self.assertRaises(ValueError):self.ingest(True)

if __name__=="__main__":unittest.main()
