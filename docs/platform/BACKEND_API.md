# M6 local API and job service

Install on Linux using Python 3.11/3.12:
```bash
python -m pip install '.[data,api]'
export BTC_PLATFORM_DB="$PWD/.platform-local/jobs.sqlite"
# Generate a random secret locally; never commit it, paste into source, or put in Pages.
export BTC_PLATFORM_TOKENS_JSON="$(python -c 'import json,secrets; print(json.dumps({"operator":secrets.token_urlsafe(48)}))')"
uvicorn btc_analysis.service.api:app_from_env --factory --host 127.0.0.1 --port 8000
# Separate terminal, same absolute DB path:
python -m btc_analysis.service.worker --db "$PWD/.platform-local/jobs.sqlite"
```

Operator-managed bearer identities; owner-scoped resources, no default tokens, no browser credential storage, no public CORS. Local loopback only until TLS, external authentication, rate limiting and security review. SQLite WAL transactions, one active claimed job per DB. Limits: 100 KB request body, 64 KiB source, 100 strategies/owner, 100 versions/strategy, 8 active jobs/owner, 1000 stored jobs/owner, 2 MiB result, 600 synthetic bars per job. SQLite is the initial single-node design to keep memory use low; PostgreSQL/multi-host workers are future production work.

| Method | Route | Purpose |
| --- | --- | --- |
| GET | /health | Liveness and execution capability |
| GET | /v1/capabilities | Authenticated supported features |
| GET/POST | /v1/strategies | List or create inert source version |
| POST | /v1/strategies/{id}/versions | New immutable version; expected_version required |
| GET | /v1/strategies/{id}/versions/{version} | Retrieve original source + SHA-256 |
| POST | /v1/jobs | Submit bounded reference_fixture; Idempotency-Key required |
| GET | /v1/jobs | Recent owner-scoped jobs |
| GET | /v1/jobs/{id} | Status, progress, result |
| POST | /v1/jobs/{id}/cancel | Cancel queued / request running cancellation |

Job lifecycle queued -> running -> succeeded/failed; queued -> cancelled or running -> cancelling -> cancelled. Atomic claim, leases, stale-worker fencing, monotonic progress, cancellation wins result publication. Abandoned jobs become failed on next claim (not silently retried). Worker runs fixed installed Python module in separate subprocess with scrubbed env, resource limits and process-group kill; no stored strategy code loaded. This is a bounded **trusted fixture**, not OS isolation for arbitrary user code. Uploaded strategy source stays inert. The API explicitly rejects historical runs and arbitrary Python execution. No secrets, GitHub tokens or live trading credentials required. No VPS deployment performed.

The synthetic end-to-end fixture uses the M4 sample strategy and M5-era baseline engine, with deterministic output hash and synthetic label; never present as market performance. CI tests real HTTP auth/ownership, source immutability, duplicate submission, queue limit, concurrent claim, lease fencing, cancellation and subprocess result persistence. Production deployment, real historical job adapter, independently tested container sandbox, network isolation, access control review, rate limits and backup remain gates.
