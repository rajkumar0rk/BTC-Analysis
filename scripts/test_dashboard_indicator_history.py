import unittest
from dashboard_indicator_history import declarations,metadata

class TestDeclarations(unittest.TestCase):
    def test_generic_and_native_frames(self):
        source='''m=Timeframe(900)
p={"period": 10, "multiplier": "3"}
book=IndicatorBook((spec("supertrend.line",m,**p),spec("ema.value",Timeframe(3600),period=37),spec("rsi.value",m,period=9)))
'''
        ds=declarations(source,"book");out=metadata(ds)
        self.assertEqual([x["timeframe_minutes"] for x in out],[15,60,15])
        self.assertEqual([x["panel"] for x in out],["price","price","panel"])
        self.assertEqual(out[1]["parameters"]["period"],37)
        self.assertEqual(out[2]["parameters"]["period"],9)
    def test_rejects_dynamic_code(self):
        with self.assertRaises(ValueError):declarations('book=IndicatorBook((spec("ema",Timeframe(60),period=unknown()),))',"book")
    def test_heredoc(self):
        source="run: |\n          python - <<'PY'\n          m=Timeframe(900)\n          book=IndicatorBook((spec('ema.value',m,period=21),))\n          PY\n"
        self.assertEqual(metadata(declarations(source,"book"))[0]["parameters"]["period"],21)

if __name__=="__main__":unittest.main()
