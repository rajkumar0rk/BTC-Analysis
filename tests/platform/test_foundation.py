import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D

from btc_analysis.contracts import (
    AssetClass, BacktestConfig, Candle, ClosedTrade, CostModel, DataKind,
    DatasetRef, Fill, Instrument, IntrabarPolicy, MarginMode, OrderIntent,
    OrderType, RunManifest, Side, StrategyRef, Timeframe,
)
from btc_analysis.serialization import canonical_bytes, fingerprint
from btc_analysis.execution_policy import SandboxPolicy, execute_custom_strategy

T = datetime(2025, 1, 1, tzinfo=timezone.utc)
END = T + timedelta(days=1)
HASH = "a" * 64
I = Instrument("delta_india", "BTCUSD", AssetClass.CRYPTO_PERPETUAL,
               "USD", "USD", D("0.1"), D("0.001"), D("1"))
MIN = Timeframe(60)
DATA = DatasetRef("btc-minute", I, DataKind.OHLCV, MIN, T, END, HASH,
                  "fixture", 0, True)
COST = CostModel(D("2"), D("5"), D(".18"), D("2"), False, False, False, "test-v1")
STRAT = StrategyRef("st", "1", HASH, HASH)
CFG = BacktestConfig(STRAT, I, (DATA,), T, END, Timeframe(900), MIN,
                     D("100"), "USD", D("10"), MarginMode.ISOLATED,
                     COST, IntrabarPolicy.BOTH_PATHS, "Asia/Kolkata", "crypto-24x7")


def fill(fid, side, price, when, qty="0.001"):
    return Fill(fid, "o-"+fid, I, when, side, D(qty), D(price),
                D(".01"), D(".002"), "USD", "recorded")


class TestFoundation(unittest.TestCase):
    def test_valid_config(self):
        self.assertEqual(CFG.reporting_timezone, "Asia/Kolkata")

    def test_invalid_decimal(self):
        for v in (float("nan"), D("NaN"), D("0"), D("-1")):
            with self.subTest(v=v), self.assertRaises(ValueError):
                replace(CFG, initial_equity=v)

    def test_timestamp(self):
        with self.assertRaises(ValueError):
            replace(CFG, start_utc=T.replace(tzinfo=None))
        with self.assertRaises(ValueError):
            replace(CFG, end_utc=END.astimezone(timezone(timedelta(hours=5, minutes=30))))

    def test_timeframe_ratio(self):
        with self.assertRaises(ValueError):
            replace(CFG, signal_timeframe=Timeframe(91))

    def test_dataset_gap(self):
        with self.assertRaises(ValueError):
            replace(CFG, datasets=(replace(DATA, gap_count=1),))

    def test_unverified_coverage(self):
        with self.assertRaises(ValueError):
            replace(CFG, datasets=(replace(DATA, coverage_verified=False),))

    def test_coverage_bounds(self):
        with self.assertRaises(ValueError):
            replace(CFG, datasets=(replace(DATA, end_utc=END-timedelta(minutes=1)),))

    def test_required_cost_inputs(self):
        for field in ("include_funding", "include_spread", "include_liquidation"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                replace(CFG, costs=replace(COST, **{field: True}))

    def test_tick_data_required(self):
        with self.assertRaises(ValueError):
            replace(CFG, intrabar_policy=IntrabarPolicy.TICK_SEQUENCE)

    def test_required_funding_available(self):
        funding = replace(DATA, dataset_id="funding", kind=DataKind.FUNDING, timeframe=None)
        self.assertTrue(replace(CFG, datasets=(DATA, funding),
                                costs=replace(COST, include_funding=True)).costs.include_funding)

    def test_instrument_expiry(self):
        with self.assertRaises(ValueError):
            replace(I, asset_class=AssetClass.FUTURE)
        future = replace(I, asset_class=AssetClass.FUTURE, expiry_utc=END)
        self.assertEqual(future.expiry_utc, END)

    def test_option_contract(self):
        with self.assertRaises(ValueError):
            replace(I, asset_class=AssetClass.OPTION, expiry_utc=END)
        option = replace(I, asset_class=AssetClass.OPTION, expiry_utc=END,
                         strike=D("90000"), option_right="call")
        self.assertEqual(option.option_right, "call")

    def test_candle_envelope_duration(self):
        c = Candle(I, MIN, T, T+timedelta(minutes=1), D(10), D(12), D(9), D(11), D(0))
        with self.assertRaises(ValueError):
            replace(c, high=D(10))
        with self.assertRaises(ValueError):
            replace(c, close_utc=T+timedelta(seconds=59))

    def test_cost_units(self):
        with self.assertRaises(ValueError):
            replace(COST, tax_rate=D(18))

    def test_cash_leverage(self):
        with self.assertRaises(ValueError):
            replace(CFG, margin_mode=MarginMode.CASH)

    def test_order_required_price_and_alignment(self):
        o = OrderIntent("o", I, T, Side.BUY, OrderType.LIMIT, D(".001"), "signal",
                        limit_price=D("90000.1"))
        for change in ({"limit_price": None}, {"quantity": D(".0001")},
                       {"limit_price": D("90000.01")}, {"reason": ""}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(o, **change)

    def test_fill_reason_required(self):
        with self.assertRaises(ValueError):
            replace(fill("a", Side.BUY, "100", T), reason="")

    def test_closed_trade_reconciliation(self):
        a = fill("a", Side.BUY, "100", T)
        b = fill("b", Side.SELL, "200", T+timedelta(minutes=1))
        trade = ClosedTrade("t", (a,), (b,), "signal", "target", D(".1"),
                            D(".02"), D(".004"), D("0"), D(".076"), "USD")
        self.assertEqual(trade.net_pnl, D(".076"))
        for change in ({"net_pnl": D(".1")}, {"fees": D(0)}, {"exit_fills": (a,)},
                       {"exit_fills": (replace(b, event_utc=T-timedelta(minutes=1)),)}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(trade, **change)

    def test_partial_fills(self):
        a = fill("a", Side.BUY, "100", T, ".002")
        b = fill("b", Side.SELL, "200", T+timedelta(minutes=1))
        c = fill("c", Side.SELL, "300", T+timedelta(minutes=2))
        trade = ClosedTrade("t", (a,), (b,c), "signal", "partial_target", D(".3"),
                            D(".03"), D(".006"), D(0), D(".264"), "USD")
        self.assertEqual(len(trade.exit_fills), 2)

    def test_deterministic_wire(self):
        self.assertEqual(canonical_bytes({"b": D("1.00"), "a": T}),
                         b'{"a":"2025-01-01T00:00:00Z","b":"1"}')
        self.assertEqual(fingerprint({"a": D("1.000")}), fingerprint({"a": D("1")}))
        self.assertNotEqual(fingerprint(CFG), fingerprint(replace(CFG, random_seed=1)))
        with self.assertRaises(TypeError):
            canonical_bytes({"bad": 0.1})

    def test_manifest(self):
        m = RunManifest("run", fingerprint(CFG), "m1", HASH, (HASH,), HASH, T,
                        ("Funding excluded",))
        self.assertEqual(len(fingerprint(m)), 64)
        with self.assertRaises(ValueError):
            replace(m, result_sha256="bad")

    def test_sandbox_fail_closed(self):
        self.assertFalse(SandboxPolicy().network_enabled)
        for kwargs in ({"network_enabled": True}, {"secrets_enabled": True},
                       {"non_root": False}, {"memory_mib": 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                SandboxPolicy(**kwargs)
        with self.assertRaises(NotImplementedError):
            execute_custom_strategy("untrusted source")


if __name__ == "__main__":
    unittest.main()
