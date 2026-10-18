# Data conventions

Original input is BTC 5m OHLCV, 61,206 rows (approximately 2025-12-31 to 2026-08-01 UTC). The exchange and precise instrument were not verified.

Aggregate contiguous bars as open=first open, high=max high, low=min low, close=last close, volume=sum volume; use UTC for aggregation and New York local timezone for clock analysis.

**Important:** whether original timestamps represent candle open or close was not independently verified. Prior discoveries used assumed close-labelled times. Confirm the label alignment before live use.

For directional evaluations, document whether next-period return is close-to-close or next-open-to-close; do not mix. For volatility, distinguish high-low range from absolute closing return.
