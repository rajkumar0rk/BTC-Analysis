"""Causal closed-bar indicator primitives for Stage37; NOT a backtest.

These are independent reference calculations, not yet verified against TA-Lib.
Only completed bars are accepted. No future bars are read.
"""
import math
import unittest


def sma(values, period):
    if period <= 0 or len(values) < period:
        raise ValueError("insufficient history")
    return sum(values[-period:]) / period


def bollinger_typical(highs, lows, closes, period=20, deviations=2):
    if not (len(highs) == len(lows) == len(closes)) or len(closes) < period:
        raise ValueError("invalid history")
    typical = [(h + l + c) / 3 for h, l, c in zip(highs[-period:], lows[-period:], closes[-period:])]
    mean = sum(typical) / period
    std = math.sqrt(sum((v - mean) ** 2 for v in typical) / period)
    return mean - deviations * std, mean, mean + deviations * std


def rsi_wilder(closes, period=14):
    if period < 1 or len(closes) < period + 1:
        raise ValueError("insufficient history")
    differences = [b - a for a, b in zip(closes, closes[1:])]
    gains = [max(d, 0) for d in differences]
    losses = [max(-d, 0) for d in differences]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
    if avg_gain == 0 and avg_loss == 0:
        return 0.0  # TA-Lib flat-series behavior must be independently verified
    if avg_loss == 0:
        return 100.0
    return 100 - 100 / (1 + avg_gain / avg_loss)


def stochastic_slowk(highs, lows, closes, fastk_period=5, slowk_period=3):
    if not (len(highs) == len(lows) == len(closes)):
        raise ValueError("invalid history")
    required = fastk_period + slowk_period - 1
    if len(closes) < required:
        raise ValueError("insufficient history")
    fastk = []
    for end in range(len(closes) - slowk_period + 1, len(closes) + 1):
        highest = max(highs[end-fastk_period:end])
        lowest = min(lows[end-fastk_period:end])
        fastk.append(0.0 if highest == lowest else 100 * (closes[end-1] - lowest) / (highest - lowest))
    return sum(fastk) / slowk_period


class CausalIndicators(unittest.TestCase):
    def test_bollinger_constant(self):
        low, mid, high = bollinger_typical([10]*20, [10]*20, [10]*20)
        self.assertEqual((low, mid, high), (10, 10, 10))

    def test_rsi_direction(self):
        self.assertEqual(rsi_wilder(list(range(20))), 100)
        self.assertEqual(rsi_wilder(list(range(20, 0, -1))), 0)

    def test_stochastic_bounds(self):
        highs, lows, closes = [10]*7, [0]*7, [5]*7
        self.assertEqual(stochastic_slowk(highs, lows, closes), 50)

    def test_missing_history_rejected(self):
        with self.assertRaises(ValueError):
            rsi_wilder([1, 2])
        with self.assertRaises(ValueError):
            stochastic_slowk([1], [0], [0.5])


if __name__ == "__main__":
    unittest.main()
