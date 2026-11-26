import unittest
import tempfile
from pathlib import Path
from hashlib import sha256
from fastapi.testclient import TestClient
from btc_analysis.service.api import create_app
from btc_analysis.service.diagnostics import validate_source

TOKEN="x"*40
AUTH={"Authorization":"Bearer "+TOKEN}

class DiagnosticsTests(unittest.TestCase):
    def test_valid_inert_code(self):
        source="raise RuntimeError('must never execute')"
        r=validate_source(source)
        self.assertTrue(r["syntax_valid"])
        self.assertFalse(r["execution_allowed"])
        self.assertEqual(r["source_sha256"],sha256(source.encode()).hexdigest())
        self.assertEqual(r["diagnostics"],[])

    def test_syntax_and_scope_errors(self):
        for source in ("def bad(:","return 1","break","if True:\npass"):
            with self.subTest(source=source):
                r=validate_source(source)
                self.assertFalse(r["syntax_valid"])
                self.assertGreaterEqual(r["diagnostics"][0]["line"],1)
                self.assertGreaterEqual(r["diagnostics"][0]["column"],1)
                self.assertFalse(r["execution_allowed"])

    def test_limits(self):
        for source in (" ","x"*65537,"é"*32769):
            with self.assertRaises(ValueError):validate_source(source)

    def test_authenticated_endpoint_and_catalog(self):
        with tempfile.TemporaryDirectory() as d:
            with TestClient(create_app(Path(d)/"db.sqlite",{"operator":TOKEN})) as c:
                self.assertEqual(c.post("/v1/strategies/validate",json={"source":"pass"}).status_code,401)
                self.assertEqual(c.get("/v1/sdk/catalog").status_code,401)
                r=c.post("/v1/strategies/validate",headers=AUTH,json={"source":"def bad(:"})
                self.assertEqual(r.status_code,200)
                self.assertFalse(r.json()["syntax_valid"])
                self.assertEqual(c.post("/v1/strategies/validate",headers=AUTH,json={"source":"é"*32769}).status_code,422)
                catalog=c.get("/v1/sdk/catalog",headers=AUTH).json()
                self.assertEqual(len(catalog["indicators"]),13)
                self.assertFalse(catalog["execution_allowed"])

if __name__=="__main__":unittest.main()
