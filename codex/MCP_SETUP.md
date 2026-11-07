# Local MCP integration: Codex background queue

A minimal JSON-RPC stdio MCP server is available at `python3 -m codex.mcp_server`. Tools: `codex_enqueue` and `codex_status`. The worker processes jobs separately using `python3 -m codex.worker worker`.

**Security:** the stdio MCP process must be spawned by a trusted authenticated application with `MONOLITH_AUTHENTICATED_ACTOR` and `MONOLITH_CODEX_ENABLED=1` set server-side. Never allow chat text or client tool arguments to choose these variables. Each actor may inspect only its own jobs. Do not expose this adapter over a public socket. Full integration must also check the permissions engine and record audit events; this adapter is a prototype, not production authorization.

Example local testing:
```bash
export MONOLITH_AUTHENTICATED_ACTOR=Aria
export MONOLITH_CODEX_ENABLED=1
python3 -m codex.mcp_server
```
Then send one JSON-RPC object per line, for example:
```json
{"jsonrpc":"2.0","id":1,"method":"tools/list"}
```

LibreChat's MCP server configuration varies by release; register a trusted stdio process using the deployed LibreChat version's documented schema. **No LibreChat MCP configuration has been deployed yet.** Worker host needs installed/authenticated Codex CLI, a persistent DB outside git, and appropriate sandboxing. Jobs currently use read-only Codex execution; no autonomous writes/deployments.
