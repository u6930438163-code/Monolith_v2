# Monolith local backend bridge (prototype)

Connects existing Python diagnostics and Ollama Vision 11B modules to an authenticated local HTTP API. This is an actual API implementation, **not yet integrated with LibreChat**.

Run on a trusted server with Python 3.11+:
```bash
python3 -m pip install -r diagnostics/requirements.txt
export MONOLITH_BRIDGE_TOKEN="$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')"
export OLLAMA_API_URL=http://127.0.0.1:11434
python3 -m bridge.server
```

Endpoints:
- `GET /health` — public minimal liveness only
- `GET /v1/diagnostics` — Bearer token required
- `POST /v1/vision/analyze` — Bearer token required; JSON `{"image_base64":"...","prompt":"..."}`; model `llama3.2-vision:11b`

The bridge binds to loopback and must only be accessed by trusted backend code, never directly from browser JavaScript. Configure the bearer token in server-side secrets, never in git. LibreChat requires a separate authenticated tool/API adapter that checks actual user/agent identities and resource permissions before forwarding. The bridge token alone is a service credential, not per-agent authorization. Add rate limiting, concurrency caps, audit logs, request timeouts, HTTPS between hosts and sandboxing before production deployment. Do not expose Ollama or this bridge to the public internet.

No service is running automatically from committing these files.
