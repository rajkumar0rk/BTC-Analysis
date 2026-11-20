# BTC/ETH EMA20 + ST Cross-Margin Hypothetical Novelty Gate

Research experiment precommitted on 2026-11-20. This is **NOT a novel strategy**; it replays the same BTC/ETH 15m indicator entries from the 20261119/20261120 fixed-$10 isolated tests. It is a margin-mode differential, following the prior $1 BTC pre-liquidation stop experiment.

## Major venue feasibility warning
Delta's Cross Margin guide describes cross-margin **USDT-settled** contracts, while current Delta India BTCUSD (product id 27) and ETHUSD (id 3136) perpetuals are **INR-settled**. Cross margin for these exact products has NOT been verified. This is a **hypothetical scenario**, not a tested supported Delta India trading configuration. It must not enable order routing.

## Frozen run parameters
- BTC/ETH Delta India verified 1m futures OHLC for Jan 2025–Nov 2026, complete UTC 15m aggregation.
- Entry: established ST(10,3), EMA20 wick-pullback + trend-side close, ATR14 >= prior20 mean and volume >=1.5x prior20 avg, closed 15m candle signals.
- 2xATR initial stop and ST opposite-flip exit. BTC trailing activation 150, distance 50 dollars; ETH percent-relative entry scalings.
- **Cross**: one position only; $100 cash account, **$10 initial margin target** at 100x; fixed <=$1000 notional per trade; all remaining account equity available to maintain position. This is ~10x effective account leverage initially. Entry fees debited from collateral, 0.25% maintenance against current notional, 0 other positions, no other unsettled payments.
- Synthetic liquidation when account wallet minus entry fees + unrealized position price PnL <= 0.25%*marked notional. Cross liquidation can consume the entire wallet, unlike isolated's $10 loss cap. A position with no positive long liquidation threshold may fall to zero without modeled liquidation; native ATR stop still exists.
- Primary exit overlay: pre-liquidation stop **BTC $1** before cross liquidation proxy, ETH dynamic entry-relative $1/80000 of entry, tick rounded UP, OR standard 2xATR stop, whichever triggers earlier, subsequent trailing tightens stop. **No entry guard/rejection**.
- Sensitivities: no preliquidation overlay, no 30min historical Scalper Offer, and bankruptcy fill after liquidation; each full-history and recent10k.
- Fee model: taker 0.05% on entry, exit 0% when hypothetically eligible within 30 minutes, otherwise taker 0.05%, assumed GST18% on commissions, modeled liquidation penalty 0.05%. Historical offer eligibility is NOT verified, funding and spread/slippage omitted. Initial fee paid from wallet.
- Replay is synthetic original 15m OHLC nearer-extreme-first, no mark-price history. Cross liquidation, $1 stops and modeled intrabar DD have large execution uncertainty.
- Report per asset: net, profit factor, wins, liquidations, max **closed equity** drawdown, max **synthetic intrabar mark-to-market equity** drawdown, worst monthly net %, complete-month profitable/loss count. Never claim real cross-mode performance.
- Isolated original runs remain untouched. Work confined to new research branch.

References: https://guides.delta.exchange/delta-exchange-india-user-guide/trading-guide/margin-explainer/cross-margin and https://docs.delta.exchange/
