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
cp "$work/package/LICENSE" dashboard/vendor/
# The pinned npm tarball omits NOTICE; this is the upstream v5.0.9 notice.
cp dashboard/licenses/lightweight-charts-5.0.9.NOTICE dashboard/vendor/NOTICE
printf "%s  %s\n" 22ccaf5643b4561c0accecee5d84eec78d3d058d "$work/lightweight-charts-5.0.9.tgz" | sha1sum -c -
node --check dashboard/vendor/lightweight-charts.standalone.production.js
