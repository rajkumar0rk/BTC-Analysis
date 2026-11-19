# BTCUSD EMA20 + Supertrend — VPS mini app

Standalone folder inside **BTC-Analysis**. One BTCUSD strategy, one position, local read-only dashboard, historical backtest view, and Delta India **demo/testnet** exchange execution adapter. Live mode is explicitly locked until manual approval.

> **Warning:** This is a carefully guarded **research / forward-demo MVP**, not a production-certified execution engine. Backtest profits are not live expectations. This build has **NOT** placed or verified an order against your Delta account. Do not switch to real trading until demo fills/stops and liquidation behavior have been checked independently.

## Strategy implemented

- 15m completed candle only. Supertrend ATR10 factor3 must already be bullish for a long / bearish for a short; do not enter on flip alone.
- LONG: candle low touches EMA20, closes above EMA20. SHORT reverse.
- ATR14 must be at least its prior-20-candle mean; volume at least 1.5× prior-20-candle mean.
- ATR14×2 initial protective stop. Trailing activation +150 BTC points, fixed trailing distance 50 points. Exit on confirmed opposite Supertrend flip.
- Research bankroll $100; fixed **up-to-$10** isolated margin per entry; 100× leverage (~$1,000 notional), rounded DOWN to integer BTCUSD contracts, one position.
- Historical fee model: taker entry/exit 0.05%, GST 18%, and assumed 30-minute Scalper Offer; modeled liquidation costs. History assumes offer active throughout; this entitlement is **not verified**.
- Forward/demo/live execution uses testnet/live Delta REST, actual market/mark price, order IDs, native reduce-only stops, and polling. **Forward entry safety guard** skips setups if 2ATR stop is beyond a conservative liquidation threshold buffer. This additional guard was NOT included in historical backtest and therefore signal counts/P&L are not directly comparable.

## Prerequisites

Oracle Ubuntu VPS (even ~1 GB RAM), Python 3.10+ (prefer 3.12), Git, SSH access, a Delta **India** demo/testnet API account/key. The historical backtest reuses verified BTCUSD 1m data and scripts from the same repository branch.

**Hosts:** Delta India demo \`https://cdn-ind.testnet.deltaex.org\`; India live \`https://api.india.delta.exchange\`. Environment host is hardcoded by MODE so credentials cannot accidentally be used with the wrong exchange. Product ID, contract value and tick size are fetched from API.

## Install on VPS

Connect to VPS through SSH, then:

~~~bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip
git clone --depth 1 --branch feature/vps-ema-st-demo-live-app https://github.com/rajkumar0rk/BTC-Analysis.git
cd BTC-Analysis/vps-btc-ema-st
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
chmod 600 .env
mkdir -p state
chmod 700 state
nano .env
~~~

If the repo is private, use your own GitHub SSH key or a token with read access; **do not paste credentials into chat**. Ensure sufficient disk for repository historical data.

## .env settings: safe initial demo configuration

Copy \`.env.example\` and keep these settings initially:

~~~dotenv
MODE=demo
TRADING_ENABLED=false
DELTA_DEMO_API_KEY=
DELTA_DEMO_API_SECRET=
PORTFOLIO_BUDGET_USD=100
MARGIN_PER_TRADE_USD=10
LEVERAGE=100
ISOLATED_MARGIN_CONFIRMED=false
DAILY_LOSS_LIMIT_USD=10
MAX_TRADES_PER_DAY=10
HALT_AFTER_LIQUIDATION=true
MIN_LIQUIDATION_BUFFER_PCT=0.25
POLL_SECONDS=3
DASHBOARD_HOST=127.0.0.1
DASHBOARD_PORT=8765
STATE_DIR=./state
~~~

At this stage, **no orders are placed**. The market feed is loaded from testnet, and candidate entries are recorded in SQLite.

### Commands

~~~bash
.venv/bin/python -m pytest -q tests/
.venv/bin/python app.py doctor       # public API check; private read-only if keys set
.venv/bin/python app.py backtest     # rerun saved research scenario from repo
.venv/bin/python app.py run          # continuous bot loop (signals-only by default)
.venv/bin/python app.py status       # local SQLite state, logs, pending and active orders
.venv/bin/python app.py audit        # authenticate, sync actual fills and estimated net before funding
.venv/bin/python app.py serve        # localhost dashboard
~~~

**The first complete bar on startup is warm-up only** so it cannot enter a delayed, historical signal.

### Backtest output and accuracy

The backtest command invokes the **exact existing research script** \`../scripts/replay_btc_ema_st_fixed_10_margin.py\`. This avoids duplicating indicator/entry/exit math. The dashboard reads files in \`../analysis/btc_ema_st_fixed_10_margin_20261119/\`, including \`summary.json\`, four monthly CSVs and four compressed trade ledgers.

Historical data: Jan 2025–Nov 18 2026; most recent full month October 2026. Stored full-history optimistic ending balance **$913.13** from hypothetical $100, 42 modeled liquidations, 19/22 profitable full months. This remains **research only**: old replay assumes 15m OHLC price path, 30-minute fee offer historically, 0 slippage, 0 funding, estimated maintenance/liquidation instead of actual mark history. The guarded bot will intentionally skip some original signals.

### Dashboard access (no public port)

Run \`app.py serve\` on VPS. On your **own computer**, keep an SSH tunnel open:

~~~bash
ssh -L 8765:127.0.0.1:8765 ubuntu@YOUR_ORACLE_VPS_IP
~~~

Open \`http://127.0.0.1:8765\` in your local browser. Views: Overview / Backtest / Activity / Safety. Web API is **read-only**, never accepts trading commands or credentials. Never open inbound port 8765 on Oracle/Ubuntu firewalls.

## Enable *demo/testnet* orders (only after doctor succeeds)

1. Make a **dedicated Delta India testnet** account/API key with trading permission and **no withdrawal permission**. Testnet may differ from the exchange's UI demo feature. Confirm the account/host is the intended environment.
2. In Delta testnet UI, configure **BTCUSD isolated margin**, 100× leverage, and disable automatic margin additions/top-ups. No existing BTCUSD positions/open orders. The bot cannot remotely verify isolated mode; this is a **mandatory manual check**.
3. Add keys to \`.env\`:
   - \`DELTA_DEMO_API_KEY=...\`
   - \`DELTA_DEMO_API_SECRET=...\`
   - \`ISOLATED_MARGIN_CONFIRMED=true\`
   - \`TRADING_ENABLED=true\`
   - Keep \`MODE=demo\`.
4. Run \`app.py doctor\` again; inspect wallet, product metadata, real-time position (must be flat), existing open orders and leverage.
5. Start \`app.py run\`; watch logs and verify orders on Delta testnet. The runner places entries only after a fresh completed 15m bar, and attaches a mark-triggered stop; it also verifies/reconciles reduce-only protective stops.
6. **Manually verify the first demo fill**: entry size, side, price, bracket/stop order, reduce-only flag, mark trigger, exchange charges, cancellation/restart behavior, close/flip, final position. If any difference: stop bot and investigate. **Do not assume this adapter is production-ready** merely because unit tests pass.

Important operational details:
- The runner signs authenticated requests with HMAC-SHA256, current Unix time, canonical exact query/path/body. Synchronize Ubuntu time with NTP (\`timedatectl\`).
- It saves client IDs/order intents **before** sending orders. For an ambiguous timeout it queries the **same client order ID**, and will NOT blindly retry unknown writes.
- It refuses to silently adopt manual positions or unknown orders. After an emergency/reconciliation error, new entries are halted. A native stop may remain active when the bot is offline.
- The stop-liq risk guard is only an **approximate** filter, never a guarantee. Exchange liquidates by mark price and maintenance tiers; large gaps can bypass stop fills.
- Daily account loss guard uses exchange wallet **net equity**, so use a **dedicated bot-only account**; unrelated deposits, withdrawals or positions can affect this metric. The $100 is a budgeting assumption, **not** a wallet ring-fence. Demo account equity may start with a different amount.
- Restarts do not reset processed candles. The dashboard now shows authenticated exchange wallet equity and an **estimated realized P&L reconstructed from exchange fill IDs and actual reported commissions**, with 18% GST modeled. It does **not** reconcile funding, credits, actual GST settlement, or external account adjustments; verify real P&L against Delta's wallet, trades and funding UI.

## Background services (optional after manual smoke tests)

~~~bash
bash scripts/install_systemd.sh
sudo systemctl start btc-ema-st-dashboard
sudo systemctl start btc-ema-st-bot
sudo systemctl status btc-ema-st-bot --no-pager
journalctl -u btc-ema-st-bot -f
~~~

The bot service intentionally has **Restart=no** on failure; blindly auto-restarting uncertain trading state is dangerous. The dashboard service can restart automatically.

Pause new signals with \`sudo systemctl stop btc-ema-st-bot\`. **Stopping the service does NOT close a position or remove an exchange stop.** Always inspect positions manually after shutdown.

For a persisted halt, inspect orders/positions/fills on Delta, then:

~~~bash
.venv/bin/python app.py status
.venv/bin/python app.py reconcile
.venv/bin/python app.py reset-halt --confirm I_VERIFIED_EXCHANGE_POSITIONS_ORDERS_AND_STOPS
~~~

If unknown order intents remain, reset is refused. Never delete state to bypass it.

## Later: live mode (real-money path; NOT validated)

**Do not enable real-money execution until several weeks of demo observations, robust fill/stop parity checks, liquidation guard verification, and independent code review.**

Stop demo bot. **Use separate keys and a dedicated real account** with permission to trade BTCUSD, IP-allowlisted to your VPS. Confirm there is no demo position requiring management. Create an independent state directory to avoid mixing demo and real orders.

In \`.env\`, after manual real-account isolated-mode confirmation:

~~~dotenv
MODE=live
TRADING_ENABLED=true
DELTA_LIVE_API_KEY=YOUR_OWN_NEW_LIVE_KEY
DELTA_LIVE_API_SECRET=YOUR_OWN_NEW_LIVE_SECRET
ISOLATED_MARGIN_CONFIRMED=true
LIVE_TRADING_ACK=I_ACCEPT_REAL_BTCUSD_TRADES
STATE_DIR=./state-live
~~~

Run **doctor first**, then start bot manually and supervise the first execution. **The live integration has not been end-to-end tested against your account**; treat enabling it as a separate verification milestone, not a simple profit-producing toggle.

## Limitations worth knowing before deployment

- Exact TradingView parity has not been demonstrated. Backtest trail uses artificial 15m OHLC intrabar path; forward trail uses periodic mark-price snapshots, and native stop-market orders execute by exchange matching/mark triggers.
- Actual Scalper Offer entitlement, fee credit, GST and funding are account-dependent. Research fee assumptions may not hold live.
- The API's product metadata does not, by itself, prove isolated margin selection; user must configure/check isolated manually.
- Current app does not use authenticated fill/position websockets, exchange wallet transaction reconciliation, precision slippage simulation or 24/7 out-of-band alerts. These are important before real money.
- Real orders can fill partially, be rejected, be rate-limited or experience stale feeds. Fail-closed behavior may require manual intervention.
- This branch is separate from \`main\` and was created without accessing or deploying to your VPS. You must run the setup commands yourself.

Official references: [Delta API docs](https://docs.delta.exchange/), [India API guide](https://www.delta.exchange/algo/delta-exchange-apis), and [Delta Python REST SDK](https://github.com/delta-exchange/python-rest-client).
