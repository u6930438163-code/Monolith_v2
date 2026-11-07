# Monolith chat gateway — Llama 3.2 3B fallback

This is an authenticated, loopback-only chat API for a trusted backend proxy.
It is **not yet connected to the LibreChat UI**.

## Start

From the repository root, with Ollama running:

```bash
export MONOLITH_BRIDGE_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
export MONOLITH_LLM_PRIMARY="your-installed-primary-model"
export MONOLITH_LLM_SECONDARY="your-installed-secondary-model"
export MONOLITH_LLM_EMERGENCY_ENABLED=false
python3 -m bridge.chat_gateway
```

In another terminal using the same token:

```bash
curl -H "Authorization: Bearer $MONOLITH_BRIDGE_TOKEN" http://127.0.0.1:8766/v1/chat/models
curl -X POST http://127.0.0.1:8766/v1/chat/generate \
  -H "Authorization: Bearer $MONOLITH_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" -d '{"prompt":"Status systemu?"}'
```

To explicitly enable emergency model, install `ollama pull llama3.2:3b`, set `MONOLITH_LLM_EMERGENCY_ENABLED=true`, and restart the gateway. Without this variable, the 3B model is never attempted.

The gateway returns the actual responding model and fallback indicator. It does not invent a reply if all models fail. It does not expose shell execution or root permissions.

**Important:** the gateway is a new endpoint on port 8766, not an integrated LibreChat provider. A trusted LibreChat adapter still needs to call this endpoint server-side, preserve authentication, and show model metadata. Do not expose the gateway publicly. Existing `bridge/server.py` remains independent on port 8765.
