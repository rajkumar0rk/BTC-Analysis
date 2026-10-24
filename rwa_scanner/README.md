# RWA Futures US-stock-first momentum scanner

Version 2 scans Delta India tokenized US stock perpetual futures, using actual underlying US-share price movement and comparable intraday share volume where available.

## Data sources

- **Delta India public API:** live listed futures, 1-minute bars, order-book depth and 24h USD turnover.
- **Yahoo Finance via yfinance:** underlying US stock 5-minute volume/price, and optional shares float (unofficial source; missing data is reported).
- **Financial Modeling Prep (optional):** /stable/shares-float with an FMP_API_KEY repository secret, preferred over Yahoo float.
- **Google News RSS:** Reuters, AP, Bloomberg, CNBC, WSJ, FT, Barron's or MarketWatch publisher attributed items from recent 48h. Headline polarity is rule-based; these are NOT verified positive catalysts.
- **pandas-market-calendars:** NYSE trading holidays, early closes and US daylight-saving rules.

## Screening

During NYSE 09:30–11:30 ET only: underlying stock session gain >=10%; underlying session-to-date volume / average comparable session-to-date volume across 3+ prior sessions >=5; underlying stock between USD 2 and 20; float <20 million shares; at least one recent positive headline **candidate**; Delta 1m first pullback confirmed on closed candle; Delta L2 spread <=0.35% and futures 24h USD turnover >=20,000, nonempty fresh book. Every check is preserved as pass/fail/unknown.

`WATCHLIST_MANUAL_NEWS_REVIEW` is never a trade recommendation. Verify actual underlying news and broker-specific Delta liquidity before making decisions. It never sends orders.

## GitHub Actions

Workflow `Scan Delta RWA momentum` automatically checks during likely market hours twice an hour on weekdays (GitHub scheduled jobs can start late). It also runs on code changes and manual dispatch. **Outside NYSE hours it logs MARKET_CLOSED_NO_SCAN** rather than presenting stale BUY entries. For an after-hours diagnostic, manually tick "force_after_hours_research"; this will always be labeled research only. Artifacts: `rwa-momentum-scan-v2` with `results.json` and `summary.md`.

Optional: Settings → Secrets and variables → Actions → New repository secret `FMP_API_KEY`. Unset keys don't break the scan; float may be obtained from Yahoo without a reliably known as-of date.

## Local execution

```bash
pip install 'yfinance>=0.2.55,<2' 'pandas-market-calendars>=4.4,<6'
python -m unittest discover -s rwa_scanner -p 'test_*.py'
python rwa_scanner/run.py --output rwa_scanner/output
python rwa_scanner/run.py --force-after-hours-research
```

Caveats: Yahoo is an unofficial source, volume may be delayed or unavailable, lexical headline polarity can be wrong, small-float company data can be stale, and a 1m closed-candle confirmation differs from Ross Cameron's intrabar stop-entry. RWA perpetual futures price and fill risk differ from US equities.
