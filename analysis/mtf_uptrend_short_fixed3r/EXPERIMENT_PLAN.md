# Countertrend SHORT: completed 30m UP trend + 1m bearish range/swing events

**This experiment is NOT "30m downtrend + SHORT".** The direction of the 30-minute filter remains UP; the actual trade side is SHORT.

## Locked before results
- Source: the existing actual Delta Exchange India BTCUSD 1-minute OHLCV archive from 2025-01-01 to 2026-10-17; no fabricated candles or L1 fills.
- 30-minute regime from the LAST FULLY COMPLETED 30-minute bar (not the currently forming bar), with 2 variants identical to the original LONG research:
  - bullish_candle: completed 30m close > open, and close > previous 30m close.
  - hhhl_structure: completed 30m high > preceding high, low > preceding low, close > preceding close and close > its own open.
- **SHORT** signal on a completed one-minute candle (same bearish 1m setups as prior SHORT study):
  1. range5_break: close below low of five preceding 1m bars, previous close at or above that low.
  2. range24_break: same for 24 previous bars.
  3. swing_break: close below latest confirmed swing low, preceding close at or above pivot. Pivot center needs 3 candles each side; only confirmed pivots are eligible.
  4. swing_range24_break: break both the latest confirmed swing low and prior 24m range low.
  5. range24_high_reject: wick above previous 24m range high, close back below high and below open, near confirmed prior swing high.
- SELL SHORT next 1m OPEN, with 5 adverse BTC-price-point slippage. Short stop/target relative to SELL fill: 100/300, 200/600, 300/900, 400/1200. Cover at adverse +5 point slippage and pay futures taker 0.05% + 18% GST on entry and exit. Stop-first if intraminute TP and SL both touch, adverse gap prices. Hard timeout after 120 min.
- Exclude entry if the potential 120m window crosses assumed 00/08/16 UTC funding-event timestamps rather than inventing funding payments.
- Timezone comparisons: all hours; weekdays all hours; New York weekdays 09:30–12:00 local with DST; London weekdays 08:00–11:00 local with DST; Singapore 09:00–12:00 weekdays; India 09:00–12:00 weekdays.
- Periods: 2025 train, Jan-Jun 2026 validation, July–Oct 17 2026 recheck that is **not** globally untouched.
- Compare all 720 combinations (2 uptrend variants x 5 short setups x 6 time windows x 4 exit pairs x 3 periods); preserve empty/negative results. Output a complete compressed trade ledger and report.
- Repeated variants and session subsets are correlated. Nonpositive gross-to-net returns and isolated positive samples are not a validated edge; historical 1m OHLC prices are not executable quotes.

Keep the existing LONG and 30m-DOWN+SHORT research files unchanged. This is an additional, explicit bullish-regime countertrend SHORT experiment.
