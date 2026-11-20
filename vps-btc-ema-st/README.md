# BTC & ETH Futures vs Options — EMA20 + Supertrend VPS app

Four independent research lanes in the same BTC-Analysis repository folder:

| Lane | Execution | Per-trade allocation |
| --- | --- | --- |
| BTCUSD futures | Forward futures paper by default; Delta demo exchange orders if enabled, live gated | Up to $10 isolated margin × 100 leverage |
| ETHUSD futures | Forward futures paper by default; Delta demo exchange orders if enabled, live gated | Up to $10 isolated margin × 100 leverage |
| BTC CALL/PUT options | **Forward paper only** using actual testnet/live option bid/ask | Up to $10 total premium including entry fees/GST |
| ETH CALL/PUT options | **Forward paper only** using actual testnet/live option bid/ask | Up to $10 total premium including entry fees/GST |

Options do **not** use futures leverage. Long CALL for bullish underlying, long PUT for bearish underlying. No option selling-to-open, no actual option orders.

**Important:** We have complete underlying futures candles and verified BTC/ETH historical futures backtests, but **NO historical contract-specific option bid/ask prices**, strikes, expiries or settlement data. Historical option P&L is unavailable and is never fabricated. The comparison dashboard instead shows historical futures models separately from subsequently collected **forward options paper trades**. The four forward paper lanes use separate $100 simulated wallets from the first run; the dashboard also pairs trades by **the same underlying 15m signal candle** so skipped option entries do not contaminate matched-trade comparisons. The first fair like-for-like period is one in which all relevant lanes have collected actual data.

## The same underlying strategy

Use a closed 15-minute bar and unchanged indicators from the repo's historical BTC strategy:

- Supertrend (ATR10 factor3) is already bullish/bearish (not a fresh trend-flip entry).
- EMA20 wick pullback touch and favorable candle close.
- Volume >= 1.5× prior 20 volume average, ATR14 >= prior 20 ATR14 average.
- 2×ATR14 initial stop based on underlying entry price. Supertrend opposite flip exits.
- Trailing: BTC activation 150 price points, trailing distance 50; ETH activation 0.1875% of ETH entry, trailing distance 0.0625%, frozen per position and rounded to exchange tick. ETH uses the same percentage rescaling as its earlier cross-asset backtest.
- **Futures liquidation entry guard: OFF**, as explicitly requested. This exposes the risk that liquidation at 100× occurs *before* the ATR stop. Native futures protective stops and risk journaling remain.
- Long options: filter fresh near-ATM (<=2% distance) tradable contract with expiry 36h–14d from now, spread <=10%, adequate bid/ask depth, real product contract size and official settlement metadata. Entry at fresh ASK, exit at fresh BID when the underlying stop/trailing/flip triggers. Maximum total buy debit (premium + assumed taker fee + 18% GST) $10. If an exit quote cannot be validated, the paper exit stays pending and no fake trade is created. At expiry a real settlement reference is needed, not guessed.

Options fee estimate: 0.01% of underlying notional capped at 3.5% of option premium **per side**, plus assumed 18% GST. The exchange's actual charged fees/credits and historical offer eligibility are not independently verified. Bid/ask paper results may still differ materially from real fills.

## Ubuntu / Oracle VPS installation

In an SSH session (Python 3.10+ supported; Python 3.12 recommended):

~~~bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip
git clone --depth 1 --branch feature/vps-btc-eth-futures-options-comparison https://github.com/rajkumar0rk/BTC-Analysis.git
cd BTC-Analysis/vps-btc-ema-st
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
chmod 600 .env
umask 077
nano .env
.venv/bin/python -m pytest -q tests/
~~~

Initially leave MODE=demo, TRADING_ENABLED=false, no API keys. The app reads only public historical and market data (and opens no option orders in any mode). STATE_DIR should be blank to automatically isolate states under state/demo/BTC_futures, state/demo/ETH_futures, state/demo/BTC_options and state/demo/ETH_options.

### Read-only API checks

~~~bash
ASSET=BTC MARKET=futures .venv/bin/python app.py doctor
ASSET=ETH MARKET=futures .venv/bin/python app.py doctor
ASSET=BTC MARKET=options .venv/bin/python app.py doctor
ASSET=ETH MARKET=options .venv/bin/python app.py doctor
~~~

Doctor never submits any orders. The testnet option chain may be illiquid or unavailable; that is a real limitation, not a reason to fabricate prices. If no valid quote meets bid/ask, DTE and spread limits, that option entry is skipped.

### Historical futures backtests (guard OFF)

~~~bash
.venv/bin/python app.py backtest --asset BTC
.venv/bin/python app.py backtest --asset ETH
~~~

They use verified Delta India 1m underlying history aggregated to 15m and their existing scripts. Replaying both is optional; the output files are already present on this branch. On a 1GB RAM VPS, historical jobs may require swap. **There is no historical options backtest**, because the inputs for it are not available.

Research-only simulated benchmark: BTC original $100 to $913.13, 42 modeled liquidations; ETH original $100 to $1,964.68, 113 modeled liquidations. Both assumed a historical Scalper Offer that was not verified; neither includes slippage, spread, funding or actual historical mark-price liquidation. Do not interpret those returns as what demo/live must achieve.

## Four separately isolated long-running services

~~~bash
bash scripts/install_systemd_multi.sh
sudo systemctl start ema-st-dashboard
sudo systemctl start ema-st@BTC_futures
sudo systemctl start ema-st@ETH_futures
sudo systemctl start ema-st@BTC_options
sudo systemctl start ema-st@ETH_options
sudo systemctl status ema-st@BTC_options --no-pager
journalctl -u ema-st@ETH_options -n 60 --no-pager
~~~

The installer creates four editable files in lane-env/ (BTC_futures.env, ETH_futures.env, BTC_options.env, ETH_options.env), each initially MODE=demo and TRADING_ENABLED=false. Per-lane environment variables override the common .env (which contains credentials and budgets).

Futures with order writes disabled now run **quote-based forward PAPER trading by default** (FUTURES_PAPER_ENABLED=true), with 100x isolated-margin risk, modeled mark-price liquidation, conservative fresh entry ask / exit bid and modeled fees/GST. They do not submit orders and they do not invent historical results. To run signals-only instead set FUTURES_PAPER_ENABLED=false. Options paper positions persist in each lane's SQLite database and retain their cash balance across restarts. Quote samples during active positions are stored (one per minute per product) for future auditing, not as a complete historical option-chain reconstruction. A file lock prevents duplicate processes for the same lane.

When TRADING_ENABLED=true, futures lane positions and daily-loss controls do not enforce a **combined account exposure limit** across BTC and ETH. If both use the same Delta login, their margin/fees hit the same real wallet. Prefer separate demo accounts for a true isolated $100-per-strategy comparison or explicitly plan aggregate risk before enabling both futures lanes.

### Dashboard access

The dashboard binds only to VPS localhost 127.0.0.1:8765. On your own computer, create:

~~~bash
ssh -L 8765:127.0.0.1:8765 ubuntu@YOUR_VPS_IP
~~~

Open http://127.0.0.1:8765 on your own computer. Never expose port 8765 publicly. Tabs show four-lane status, separate monthly BTC/ETH FUTURES backtests, forward BTC/ETH OPTIONS paper trades and strategy/safety differences. No dashboard endpoints can place orders.

## Enabling FUTURES testnet orders after signals-only checks

1. Create Delta **India testnet** API keys, trading-only without withdrawal permissions, ideally IP allowlisted; set DELTA_DEMO_API_KEY and DELTA_DEMO_API_SECRET in common .env.
2. Manually set BTCUSD/ETHUSD **isolated** margin, **100× leverage**, and disable auto-add margin in the exchange UI. Confirm there are no existing manual positions or orders on that product.
3. Set ISOLATED_MARGIN_CONFIRMED=true in common .env.
4. Edit ONLY the futures lane you want to activate (e.g. lane-env/BTC_futures.env): set TRADING_ENABLED=true. Keep the options lane files at false; options write attempts are rejected at startup.
5. Stop the specific service, run a manual doctor using the same ASSET/MARKET/MODE/TRADING_ENABLED environment, then restart it. Monitor order entry, actual fill price/quantity, exchange-native stop and trailing updates and venue fees.
6. Starting a futures bot does not adopt unknown exchange positions; stopping it **does not flatten an existing position**. Check the exchange UI and manage outstanding native stops on any restart/disconnect.
7. The order-writing bot intentionally does NOT auto-restart after uncertain order outcomes. Inspect, reconcile and only clear persistent halt after confirming exchange positions and order history.

~~~bash
ASSET=BTC MARKET=futures TRADING_ENABLED=true .venv/bin/python app.py doctor
sudo systemctl restart ema-st@BTC_futures
ASSET=BTC MARKET=futures .venv/bin/python app.py status
ASSET=BTC MARKET=futures .venv/bin/python app.py reconcile
~~~

If a real/demo exchange order intent remains unresolved, do not delete state or issue duplicate orders. For manual halt reset:

~~~bash
ASSET=BTC MARKET=futures .venv/bin/python app.py reset-halt --confirm I_VERIFIED_EXCHANGE_POSITIONS_ORDERS_AND_STOPS
~~~

## Later LIVE deployment

**FUTURES ONLY** has a gated live route, not validated against your account. First run demo for an extended period and independently audit fills, liquidation mark triggers, funding, fees, GST, slippage and stop placement. Use a dedicated real account, separate live keys, and separate state path per mode. For a given futures lane set MODE=live and TRADING_ENABLED=true, with DELTA_LIVE_API_KEY/SECRET in common .env, manual isolated confirmation and LIVE_TRADING_ACK=I_ACCEPT_REAL_BTCUSD_TRADES (or I_ACCEPT_REAL_ETHUSD_TRADES for ETH). This explicit acknowledgement prevents accidental order writes without permission.

**OPTIONS remain paper-only in both demo and live modes.** Setting TRADING_ENABLED=true on an option lane raises an error. To support actual options orders, a new order/fill reconciliation and underlying-triggered stop/expiry architecture must be independently tested; the code does not pretend this is implemented.

## Limitations

- Historical futures synthetic 15m OHLC trails and liquidations cannot exactly reproduce live intrabar price paths. Exchange mark-price liquidation, funding, spread, slippage and offer history are missing.
- Options close on underlying signals, not when option premium changes by the same percentage as futures. Theta/IV, strike/expiry choice and spread make option P&L very different.
- Paper bid/ask outcomes are **simulated**, even when the quotes are real. Top-of-book quotes can change and may not fill at the assumed price.
- Stale/missing option exit bids remain unresolved, not booked at invented prices. Expired positions require settlement records; zero/intrinsic settlement is never guessed.
- Only whole valid contracts are selected; if $10 including fees cannot cover one contract, the entry is skipped.
- No verified full account-level multi-lane risk cap, no authenticated fill websocket or exchange funding/credits reconciliation; the app is a research MVP, not a production-grade trading platform.
- State includes sensitive trading information; keep .env, lane-env and SQLite protected. Synchronize VPS clock with NTP.

Official API reference: https://docs.delta.exchange/ ; India fee details: https://www.delta.exchange/fees . Offline CI: .github/workflows/test-vps-multi-asset-options.yml.

## Matched forward futures-vs-options paper comparison

By default, MODE=demo and TRADING_ENABLED=false, both BTC/ETH futures now paper-trade at actual bid/ask quotes (no orders) as do their corresponding CALL/PUT options. Each paper lane has its own starting $100 portfolio. On the comparison dashboard the **Matched forward trades** table joins closed futures and option trades by their exact underlying 15-minute entry signal timestamp, and shows their NET return difference after modeled fees/GST. It also reports total paper trades and all closed net across each lane, to make option-skipped entries visible. Futures 100× liquidation is only an approximate mark-price maintenance proxy and options quote execution is hypothetical; neither is an exchange-confirmed fill.

With FUTURES_PAPER_ENABLED=false and TRADING_ENABLED=false a futures lane is signals-only (no virtual or real trades). With TRADING_ENABLED=true it routes Delta testnet/live futures orders, and any previous paper record in the same state path should be archived or isolated before changing mode. Never compare an exchange order ledger with paper quote fills as if they had identical execution certainty.
