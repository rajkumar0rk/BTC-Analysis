# BTC 0.5 versus 5 price-point slippage: verified actual replay

**GitHub Actions success:** [run 44681039768](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44681039768). Archived evidence includes all 22 calendar months, 15 causal monthly profit lock strategies, baseline 5.0 BTC-price-points-per-side and revised user-specified 0.5 BTC-price-points-per-side, with additional 0/2/5-basis-point adverse-per-side stress scenarios.

## Main result

| BTC 1m historical January 2025–October 2026 | Base 5 BTC points /side | Revised 0.5 BTC points /side |
|---|---:|---:|
| Original 48h breakout: compounded 22mo account net | +16.9431% | **+18.0278%** |
| Original 48h breakout: mean calendar month net | +0.7475% | **+0.7899%** |
| Original 48h breakout: positive / negative / flat months | 12 / 10 / 0 | **12 / 10 / 0** |
| +0.5R monthly entry lock: compounded 22mo net | +15.1464% | **+15.7161%** |
| +0.5R monthly entry lock: mean calendar month net | +0.6745% | **+0.6970%** |
| +0.5R monthly entry lock: positive / negative / flat months | 15 / 7 / 0 | **15 / 7 / 0** |
| Original 48h breakout extra +2bp/side stress | +12.7836% | **+13.8299%** |
| +0.5R monthly lock extra +2bp/side stress | +13.0160% | **+13.5752%** |
| Original 48h breakout extra +5bp/side stress | +6.8184% | **+7.8097%** |
| +0.5R monthly lock extra +5bp/side stress | +9.8931% | **+10.4371%** |

**Original 5.0-point rule and its source Stage17 198 trades/marks exactly reconciled (max month-end NAV drift zero).** The updated model reduces modeled adverse entry and exit fills by 4.5 BTC price points per fill, not by changing the position risk, portfolio leverage, signal generation, fee or GST. The monthly profit-lock decisions use only earlier CLOSED trades in the current IST month and do not know future monthly outcome. For both the old and new assumptions the 2025-selected variant remained the +0.5R monthly entry lock.

### Important modeling disclosure

- This is a **user-requested assumed** adverse market slippage of **0.5 BTCUSD PRICE POINT per order side**, not a verified BTCUSD real-market fill quote, an exchange tick size assertion, 0.5% slippage, or 0.5 USD account P&L regardless of size.
- Delta market depth and 0.5 price point fill realism depend on quantity, maker versus taker execution, bid/ask spread, volatility and latency. Historical L1 order-book/tick data are **not** in this replay.
- Original existing fee approximation remains **0.05% taker each side + GST 18% on trading fees**, with partial liquidation mark-to-market. This fee model is not an exchange-authoritative historical tariff audit.
- **Historical funding has still not been deducted**. No contract lot rounding, real bid/ask, impact, margin/liquidation, open order costs or opportunity costs. The result is **not fully all-in net** and not live-ready.
- Source BTC minute archive has known gaps early Jan 2025 IST and final Oct 2026 UTC day. 2026 has already been studied; not pristine forward validation.
- **None of the 15 variants reaches 22/22 profitable months** with either base slippage. Existing losing months remain counted; no P&L month is patched or censored.
- Code and outputs are in isolated branch `research/btc-slippage-0p5-replay-20261120`; no edits to main, existing strategy backtests or live order code.

This test changes the **cost assumption**, NOT demonstrated exchange liquidity. The user can use 0.5-price-point-per-side as a research case, but meaningful live readiness requires a venue-and-size-specific slippage calibration with actual data, funding and contract constraints.
