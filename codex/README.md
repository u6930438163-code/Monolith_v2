# Codex background worker (prototype)

This implements a durable SQLite queue and a single Codex CLI background worker. It is **not yet connected** to LibreChat, MCP, presence or agent identity/authentication; no background process has been launched.

Requirements: Python 3.11+, Codex CLI installed and authenticated on a trusted host. Configure `MONOLITH_CODEX_WORKSPACE` to a checked-out repository, and `MONOLITH_CODEX_DB` to a persistent writable directory outside the repository. Run the worker as a restricted OS account with filesystem/network isolation; do not expose the CLI directly over the network.

```bash
export MONOLITH_CODEX_WORKSPACE="$PWD"
export MONOLITH_CODEX_DB="/var/lib/monolith-codex/jobs.sqlite3"
python3 -m codex.worker enqueue --actor owner --prompt "Sprawdź testy Real Vision i opisz błędy"
python3 -m codex.worker worker
```

Query a job via `python3 -m codex.worker status JOB_ID`. CLI is invoked with `codex exec --sandbox read-only`; it can analyze but not write code. The worker is a prototype: production requires authenticated API/MCP adapter, server-side actor verification, per-agent permission checks, secrets redaction, log retention policy, bounded queues, worker lease/recovery, cancellation, host isolation, output filtering, tests and explicit approval for write/deploy operations. Do not accept arbitrary `actor` from a user-facing request.
