#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
# Exact version, npm verifies the registry tarball integrity. No install scripts.
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
npm pack lightweight-charts@5.0.9 --ignore-scripts --pack-destination "$work" >/dev/null
tar -xzf "$work/lightweight-charts-5.0.9.tgz" -C "$work"
node -e 'if(require(process.argv[1]).version!=="5.0.9")process.exit(1)' "$work/package/package.json"
mkdir -p dashboard/vendor
cp "$work/package/dist/lightweight-charts.standalone.production.js" dashboard/vendor/
cp "$work/package/LICENSE" "$work/package/NOTICE" dashboard/vendor/
node --check dashboard/vendor/lightweight-charts.standalone.production.js
