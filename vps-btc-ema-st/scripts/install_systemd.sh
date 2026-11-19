#!/usr/bin/env bash
set -euo pipefail
if [[ "$(id -u)" == "0" ]]; then echo "Run as normal Ubuntu user, not root"; exit 1; fi
DIR="$(cd "$(dirname "$0")/.." && pwd)"
[[ -x "$DIR/.venv/bin/python" && -f "$DIR/.env" ]] || { echo "Need .venv and .env"; exit 1; }
USER_NAME="$(id -un)"
GROUP_NAME="$(id -gn)"
mkdir -p "$DIR/state"; chmod 700 "$DIR/state"; chmod 600 "$DIR/.env"
BOT_FILE="$(mktemp)"; DASH_FILE="$(mktemp)"
cat > "$BOT_FILE" <<EOF
[Unit]
Description=BTC EMA ST Delta demo/live bot
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=$USER_NAME
Group=$GROUP_NAME
WorkingDirectory=$DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$DIR/.venv/bin/python $DIR/app.py run
Restart=no
NoNewPrivileges=true
PrivateTmp=true
UMask=0077
TimeoutStopSec=15
[Install]
WantedBy=multi-user.target
EOF
cat > "$DASH_FILE" <<EOF
[Unit]
Description=BTC EMA ST localhost dashboard
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=$USER_NAME
Group=$GROUP_NAME
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
sudo install -m 644 "$BOT_FILE" /etc/systemd/system/btc-ema-st-bot.service
sudo install -m 644 "$DASH_FILE" /etc/systemd/system/btc-ema-st-dashboard.service
rm -f "$BOT_FILE" "$DASH_FILE"
sudo systemctl daemon-reload
sudo systemctl enable btc-ema-st-dashboard
echo "Installed. Run: sudo systemctl start btc-ema-st-dashboard"
echo "Doctor first; then: sudo systemctl start btc-ema-st-bot"
echo "Bot deliberately does not restart on failure: inspect exchange and logs first."
