#!/usr/bin/env bash
set -euo pipefail
if [[ "$(id -u)" -eq 0 ]]; then echo "Run as normal Ubuntu user"; exit 1; fi
DIR="$(cd "$(dirname "$0")/.." && pwd)"
[[ -f "$DIR/.env" && -x "$DIR/.venv/bin/python" ]] || { echo "Need .env and .venv"; exit 1; }
chmod 600 "$DIR/.env"
mkdir -p "$DIR/lane-env"; chmod 700 "$DIR/lane-env"
for lane in BTC_futures ETH_futures BTC_options ETH_options; do
  file="$DIR/lane-env/$lane.env"
  if [[ ! -f "$file" ]]; then
    asset="$(echo "$lane" | cut -d_ -f1)"
    market="$(echo "$lane" | cut -d_ -f2)"
    cat > "$file" <<EOF
# Per-lane settings; inherit budget and credentials from ../.env.
MODE=demo
ASSET=$asset
MARKET=$market
TRADING_ENABLED=false
STATE_DIR=
EOF
    chmod 600 "$file"
  fi
done
USR="$(id -un)"; GRP="$(id -gn)"
unit="$(mktemp)"; dashboard="$(mktemp)"
cat > "$unit" <<EOF
[Unit]
Description=EMA ST BTC/ETH runner %i
Wants=network-online.target
After=network-online.target
[Service]
Type=simple
User=$USR
Group=$GRP
WorkingDirectory=$DIR
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=$DIR/lane-env/%i.env
ExecStart=$DIR/.venv/bin/python $DIR/app.py run
Restart=no
NoNewPrivileges=true
PrivateTmp=true
UMask=0077
TimeoutStopSec=15
LimitNOFILE=4096
[Install]
WantedBy=multi-user.target
EOF
cat > "$dashboard" <<EOF
[Unit]
Description=EMA ST BTC/ETH read-only comparison dashboard
Wants=network-online.target
After=network-online.target
[Service]
Type=simple
User=$USR
Group=$GRP
WorkingDirectory=$DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$DIR/.venv/bin/python $DIR/app.py serve
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
UMask=0077
[Install]
WantedBy=multi-user.target
EOF
sudo install -m 644 "$unit" /etc/systemd/system/ema-st@.service
sudo install -m 644 "$dashboard" /etc/systemd/system/ema-st-dashboard.service
rm -f "$unit" "$dashboard"
sudo systemctl daemon-reload
sudo systemctl enable ema-st-dashboard
echo "All four services default to ORDER WRITES OFF."
echo "Start dashboard: sudo systemctl start ema-st-dashboard"
echo "Start lanes: sudo systemctl start ema-st@BTC_futures ema-st@ETH_futures ema-st@BTC_options ema-st@ETH_options"
echo "Options are quote-based paper ONLY, regardless of environment mode."
