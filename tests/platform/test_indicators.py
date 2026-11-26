import unittest
from decimal import Decimal as D, localcontext
from datetime import datetime,timedelta,timezone
from btc_analysis.contracts import Instrument,AssetClass,Candle,Timeframe
from btc_analysis.indicators import spec,StreamingIndicator,IndicatorBook,CATALOG
from btc_analysis.strategy import crossover,crossunder,quantity_for_notional

T=datetime(2025,1,1,tzinfo=timezone.utc)
MIN=Timeframe(60)
I=Instrument("fixture","BTCUSD",AssetClass.CRYPTO_PERPETUAL,"USD","USD",D(".1"),D(".1"),D(1))

def candles(values,volumes=None):
    return [Candle(I,MIN,T+timedelta(minutes=i),T+timedelta(minutes=i+1),
                   D(x),D(x)+1,D(x)-1,D(x),D(volumes[i] if volumes else 1))
            for i,x in enumerate(values)]

def series(name,data,**params):
    ind=StreamingIndicator(spec(name,MIN,**params))
    return [ind.update(c) for c in data]

class IndicatorTests(unittest.TestCase):
    def close(self,a,b):self.assertLess(abs(a-D(b)),D("1e-24"))

    def test_sma_ema_seed_and_recurrence(self):
        c=candles([10,12,14,18,20])
        r=series("sma",c,period=3)
        self.assertEqual(r[:3],[None,None,D(12)])
        with localcontext() as ctx:
            ctx.prec=50
            self.assertEqual(r[3:],[D(44)/3,D(52)/3])
        self.assertEqual(series("ema",c,period=3),[None,None,D(12),D(15),D("17.5")])

    def test_atr_wilder_gap(self):
        c=candles([10,13,14,20])
        r=series("atr",c,period=2)
        self.assertEqual(r,[None,D(3),D("2.5"),D("4.75")])

    def test_rsi_rising_falling_flat(self):
        for prices,target in (([10,11,12,13],100),([13,12,11,10],0),([10,10,10,10],50)):
            r=series("rsi",candles(prices),period=2)
            self.assertEqual(r[:2],[None,None]);self.assertEqual(r[2:],[D(target)]*2)
        r=series("rsi",candles([10,12,11,13]),period=2)
        self.close(r[2],D(100)*2/3);self.close(r[3],D(100)*6/7)

    def test_adx_directional_seed(self):
        c=candles([10,11,12,13,14,15])
        r=series("adx",c,period=2)
        self.assertEqual(r[:3],[None,None,None]);self.assertEqual(r[3:],[D(100)]*3)
        self.assertEqual(series("adx.plus_di",c,period=2)[2],D(50))
        self.assertEqual(series("adx.minus_di",c,period=2)[2],D(0))

    def test_supertrend_flip(self):
        c=candles([10,10,15,15,8])
        r=series("supertrend.direction",c,period=1,multiplier=1)
        self.assertEqual(r,[D(-1),D(-1),D(1),D(1),D(-1)])
        self.assertEqual(series("supertrend.line",c,period=1,multiplier=1),[D(12),D(12),D(9),D(13),D(16)])

    def test_bollinger_and_stddev(self):
        c=candles([10,14])
        self.assertEqual(series("bollinger.upper",c,period=2,multiplier=2)[1],D(16))
        self.assertEqual(series("bollinger.lower",c,period=2,multiplier=2)[1],D(8))
        self.assertEqual(series("stddev",c,period=2)[1],D(2))

    def test_donchian(self):
        c=candles([10,12,8])
        self.assertEqual(series("donchian.upper",c,period=2),[None,D(13),D(13)])
        self.assertEqual(series("donchian.lower",c,period=2),[None,D(9),D(7)])

    def test_roc_volume_vwap(self):
        c=candles([10,12,15],[1,3,8])
        self.assertEqual(series("roc",c,period=2)[2],D(50))
        self.assertEqual(series("volume_ratio",c,period=2),[None,None,D(4)])
        self.assertEqual(series("vwap",c,period=2)[1],D("11.5"))
        self.assertEqual(series("vwap",candles([10,10],[0,0]),period=2),[None,None])

    def test_macd_line_and_signal(self):
        c=candles([10,12,14,16,18])
        line=series("macd.line",c,fast=2,slow=3,signal=2)
        signal=series("macd.signal",c,fast=2,slow=3,signal=2)
        hist=series("macd.histogram",c,fast=2,slow=3,signal=2)
        self.assertEqual(line,[None,None,D(1),D(1),D(1)])
        self.assertEqual(signal,[None,None,None,D(1),D(1)])
        self.assertEqual(hist,[None,None,None,D(0),D(0)])

    def test_reset_and_no_future_prefix(self):
        c=candles([10,11,15,13,20,10,12,13])
        for name,(defaults,fields) in CATALOG.items():
            p={k:(3 if k=="period" else 2 if k=="fast" else 3 if k=="slow" else 2 if k=="signal" else v) for k,v in defaults.items()}
            for field in fields:
                with self.subTest(name=name,field=field):
                    key=name+"."+field
                    full=series(key,c,**p)
                    self.assertEqual(full[:5],series(key,c[:5],**p))
                    obj=StreamingIndicator(spec(key,MIN,**p))
                    self.assertEqual(full,[obj.update(x) for x in c])
                    obj.reset();self.assertEqual(full,[obj.update(x) for x in c])

    def test_book_bounded_history_continuous_seed(self):
        c=candles([10,12,14,16,30,40])
        book=IndicatorBook((spec("ema",MIN,period=3),),history_limit=2)
        for x in c:book.update(x)
        self.assertEqual(book.get("ema",MIN,{"period":3},2),tuple(series("ema",c,period=3)[-2:]))
        with self.assertRaises(ValueError):book.get("rsi",MIN)

    def test_invalid_spec_and_order(self):
        for name,p in (("unknown",{}),("ema",{"period":True}),("ema",{"period":0}),("ema",{"period":4097}),
                       ("ema",{"x":1}),("macd",{"fast":30}),("supertrend",{"multiplier":"NaN"})):
            with self.subTest(name=name,p=p),self.assertRaises(ValueError):spec(name,MIN,**p)
        obj=StreamingIndicator(spec("ema",MIN,period=2));c=candles([10,11])
        obj.update(c[1])
        with self.assertRaises(ValueError):obj.update(c[0])

    def test_helpers(self):
        self.assertTrue(crossover(D(1),D(3),D(2),D(2)))
        self.assertTrue(crossunder(D(3),D(1),D(2),D(2)))
        self.assertFalse(crossover(None,D(3),D(2),D(2)))
        self.assertEqual(quantity_for_notional(I,D(100),D(33)),D(3))

if __name__=="__main__":unittest.main()
