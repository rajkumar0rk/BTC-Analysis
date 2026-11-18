# BTC live microstructure recorder — Oracle Linux VPS

This is a **public read-only research recorder**. Never place trading API keys on this server. It captures **new data from startup onward**, not 2025 order-book history.

## Installation (Ubuntu 22.04/24.04 Oracle AMD Always Free)

Connect with SSH and run:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv
git clone https://github.com/rajkumar0rk/BTC-Analysis.git
cd BTC-Analysis
python3 -m venv .venv
.venv/bin/pip install 'websockets>=14,<17'
.venv/bin/python scripts/collect_btc_websocket_vps.py --self-test
# A brief real-connection test. First create the output directory:
sudo mkdir -p /var/lib/btc-market-data
sudo chown "$USER":"$USER" /var/lib/btc-market-data
.venv/bin/python scripts/collect_btc_websocket_vps.py --duration 90 --require-events --free-floor-mb 2048
```

**Private repository:** If `git clone` prompts for credentials, configure a *read-only* GitHub deploy key on the VPS, or upload the scripts over SSH. Do not place GitHub tokens in shell history.

## Run as a managed service

The commands assume your checkout is at `/opt/BTC-Analysis`. If you cloned into your home directory, either move it or edit `WorkingDirectory` and `ExecStart` in the service file.

```bash
sudo mkdir -p /opt
sudo mv ~/BTC-Analysis /opt/BTC-Analysis
sudo useradd --system --home /var/lib/btc-market-data --shell /usr/sbin/nologin btcdata || true
sudo mkdir -p /var/lib/btc-market-data
sudo chown -R btcdata:btcdata /var/lib/btc-market-data
sudo cp /opt/BTC-Analysis/deploy/btc-ws-collector/btc-websocket.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now btc-websocket
sudo systemctl status btc-websocket --no-pager
sudo journalctl -u btc-websocket -f
```

To stop: `sudo systemctl stop btc-websocket`

## Data layout

`/var/lib/btc-market-data/{delta,binance_spot}/YYYY-MM-DD/HH.jsonl.gz`

Each gzip JSON Lines record includes UTC host receive timestamp (nanoseconds), venue, message kind, raw exchange payload, plus a validation annotation when available. The two feeds run concurrently with reconnect/backoff. Delta book errors cause reconnect/resubscription, with raw offending events retained.

**Binance** `depth20` is a stream of independent top-20 snapshots (not a true incremental L2 reconstruction). Delta `ob_updates` contains raw depth updates and checksum/sequence validation attempts; if its checksum format is changed, the recorder will log disconnects and not claim valid depth.

## Safety and data quality

- Default stop threshold: **2 GiB disk free**. Your initial 30 GiB VPS disk may fill relatively quickly; monitor disk daily (`df -h`).
- There is **no automatic deletion** of collected research. Archive hourly gzip files to separate storage before they fill the disk. Use encrypted object storage or another backed-up destination; never assume GitHub is appropriate for raw tick data.
- Record and inspect disconnect, parse-error, resync, timestamp skew and packet-loss flags. These records are not interchangeable with completed fills.
- VPS egress firewall must permit outbound **TCP 443** to both exchanges. No inbound WebSocket port is necessary.
- Raw Binance aggregate trades are not every individual fill. Market-making replay still needs order queue, trade-by-trade fills, and account fee details. Funding settlement cashflows are not captured by this recorder.
- The scheduled 15-minute GitHub REST snapshot collector remains independent; this VPS recorder does not modify or interfere with it.
