# Monolith_v2 — first runnable MVP status API

Run from the repository root in Codespaces or Ubuntu:

```bash
python3 -m mvp.status_server
curl -fsS http://127.0.0.1:8765/health
curl -fsS http://127.0.0.1:8765/api/v1/status
python3 -m unittest tests.test_mvp_status -v
```

This is **not** a finished central chat or agent runtime. It is a loopback-only, read-only operational status endpoint. The default response has no invented ship positions and marks agents as disconnected until real integration exists. Existing local SQLite tables are inspected without creating files. Legacy simulated position rows are filtered from this endpoint.

Security: never publish this unauthenticated MVP endpoint publicly. It deliberately binds to localhost. It does not yet implement RBAC, TLS, telemetry attestation, chat-to-command execution, or live updates. The legacy APIs and UI must be migrated before the whole application can be called real-data-only.
