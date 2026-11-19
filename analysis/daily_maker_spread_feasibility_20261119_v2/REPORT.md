# BTC maker spread-capture upper-bound audit

Pre-registered test: maximum theoretical two-sided spread capture at each available snapshot minus two maker fees and 18% GST, no other profit assumption. The quoted spread is NOT an earned spread. Historical point-in-time snapshots are sparse and cannot establish passive fill probability, adverse selection, queue position, funding or realistic PnL. No ETH equivalent. Never call this a backtest or annual profitability evidence.

{
  "hypothesis": "passive market making may earn spread; first test whether gross full spread even covers both maker fees + GST",
  "status": "FEASIBILITY_ONLY_NOT_EXECUTABLE_BACKTEST",
  "symbol": "BTCUSD",
  "source": "Delta India public REST L2 snapshots; NOT a historical continuous L2 stream",
  "observations": 132,
  "observed_days": 32,
  "first": "2026-10-18T16:12:51.347742Z",
  "last": "2026-11-18T21:51:12.434774Z",
  "median_spread_bps": 0.06406295061391795,
  "p90_spread_bps": 0.07588318542435775,
  "fee_roundtrip_bps": 4.72,
  "median_ideal_net_bps": -4.655937049386082,
  "pct_snapshots_positive_ideal_net": 0.0,
  "unusable": {},
  "unavailable": [
    "true queue position",
    "actual passive fills",
    "trade sequence between snapshots",
    "adverse selection and future markout at seconds",
    "order cancellation latency",
    "portfolio margin/liquidation reconstruction",
    "complete ETH L2 history"
  ],
  "calendar_day_net_returns": "NOT COMPUTABLE from sparse snapshots; do not invent positive/negative/no-trade counts",
  "2025_2026_annual_returns": "NOT COMPUTABLE",
  "monthly_net_returns": "NOT COMPUTABLE",
  "funding": "Not applicable to unfilled quote study",
  "slippage": "No filled orders; zero slippage is only an optimistic theoretical upper bound",
  "interpretation": "Even a positive ideal quote-capture bound is NOT an executable strategy; no user notification."
}
