#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
export GITHUB_SHA="$(git rev-parse HEAD)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
gh auth setup-git
git init -q -b dashboard-data "$work"
git -C "$work" remote add origin "https://github.com/$GITHUB_REPOSITORY.git"
git -C "$work" config user.name "github-actions[bot]"
git -C "$work" config user.email "41898282+github-actions[bot]@users.noreply.github.com"
set +e
git -C "$work" ls-remote --exit-code origin refs/heads/dashboard-data >/dev/null
status=$?
set -e
if [ "$status" -eq 0 ]; then
  git -C "$work" fetch --depth=1 origin refs/heads/dashboard-data
  git -C "$work" checkout -q -B dashboard-data FETCH_HEAD
elif [ "$status" -ne 2 ]; then
  echo "::error::Unable to inspect data branch"; exit 1
fi
old_run=""
old_fingerprint=""
if [ -s "$work/latest.json" ]; then
  old_run=$(python -c 'import json,sys;print(json.load(open(sys.argv[1])).get("eth_run",""))' "$work/latest.json")
  old_fingerprint=$(python -c 'import json,sys;print(json.load(open(sys.argv[1])).get("fingerprint",""))' "$work/latest.json")
fi
eth_dir=analysis/ethusd_native_atr_price_action
mkdir -p "$eth_dir" "$work/_sources"
run=$(gh api "repos/$GITHUB_REPOSITORY/actions/workflows/research-eth-native-atr-price-action.yml/runs?status=success&branch=main&per_page=1" --jq '.workflow_runs[0].id // empty')
if [ -n "$run" ] && { [ "$run" != "$old_run" ] || [ ! -s "$work/_sources/eth-trades.csv.gz" ]; }; then
  mkdir "$work/_download"
  if gh run download "$run" --name eth-native-atr-trade-ledger --dir "$work/_download" && test -s "$work/_download/full_trade_ledger.csv.gz"; then
    cp "$work/_download/full_trade_ledger.csv.gz" "$work/_sources/eth-trades.csv.gz"
    old_run="$run"
  elif [ -s "$work/_sources/eth-trades.csv.gz" ]; then
    echo "::warning::New ETH artifact unavailable; preserving last successful ledger $old_run"
  else
    echo "::error::No ETH trade evidence available"; exit 1
  fi
  rm -rf "$work/_download"
fi
test -s "$work/_sources/eth-trades.csv.gz"
cp "$work/_sources/eth-trades.csv.gz" "$eth_dir/full_trade_ledger.csv.gz"
export DASHBOARD_ETH_RUN="$old_run"
export DASHBOARD_BUNDLE_CACHE="$work/_sources/backtest-bundles"
python scripts/publish_backtest_bundles.py collect "$DASHBOARD_BUNDLE_CACHE" "$GITHUB_REPOSITORY"
# Fingerprint relevant content rather than main HEAD; unrelated commits and unchanged runs are no-ops.
fingerprint=$({
  git ls-tree -r HEAD -- data/delta_india/BTCUSD/1m data/delta_india/ETHUSD/1m analysis/delta_points_200_500/individual_trade_replay.csv analysis/institutional_discovery_stage24_failed_auction/original_trade_ledger.csv.gz scripts/backtest_bundle.py scripts/publish_backtest_bundles.py scripts/dashboard_indicator_history.py src/btc_analysis/indicators.py src/btc_analysis/contracts.py scripts/export_dashboard.py scripts/dashboard_archive.py scripts/verify_dashboard_export.py scripts/dashboard_catalog.py scripts/publish_dashboard_data.sh
  git ls-files analysis | grep -E '(ledger|_trades)[^/]*\.csv(\.gz)?$' || true
  sha256sum "$eth_dir/full_trade_ledger.csv.gz"
  printf '%s\n' "$DASHBOARD_ETH_RUN"
  find "$DASHBOARD_BUNDLE_CACHE" -maxdepth 1 -type f -name "*.json" -print0 | sort -z | xargs -0 -r sha256sum | sed "s|$DASHBOARD_BUNDLE_CACHE/||"
} | sha256sum | cut -d' ' -f1)
if [ "$fingerprint" = "$old_fingerprint" ] && [ -s "$work/data/index.json" ]; then
  echo "No changed backtest or market-data inputs; skipping export and publication"
  exit 0
fi
git ls-remote --heads origin > .dashboard-branches.txt
export DASHBOARD_PREVIOUS_DATA="$work/data"
python scripts/export_dashboard.py
python scripts/verify_dashboard_export.py
mkdir -p "$work/data"
rsync -a --delete dashboard-dist/data/ "$work/data/"
git -C "$work" add -A -- data _sources
if ! git -C "$work" diff --cached --quiet; then
  git -C "$work" commit -qm "data: publish verified backtest shards from ${GITHUB_SHA:0:12}"
fi
data_commit="$(git -C "$work" rev-parse HEAD)"
export data_commit fingerprint
python - "$work/latest.json" <<'PY'
import datetime,json,os,sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps(dict(schema=1,data_schema=2,catalog_policy=3,data_commit=os.environ["data_commit"],source_commit=os.environ["GITHUB_SHA"],fingerprint=os.environ["fingerprint"],eth_run=os.environ["DASHBOARD_ETH_RUN"],published_at=datetime.datetime.now(datetime.timezone.utc).isoformat()),separators=(",",":"))+"\n")
PY
git -C "$work" add latest.json
git -C "$work" commit -qm "data: atomically advance latest snapshot pointer"
git -C "$work" push origin HEAD:refs/heads/dashboard-data
remote="$(git -C "$work" ls-remote origin refs/heads/dashboard-data | cut -f1)"
test "$remote" = "$(git -C "$work" rev-parse HEAD)"
echo "Published data commit $data_commit (no Pages deployment)"
