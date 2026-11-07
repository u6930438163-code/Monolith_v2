# Monolith_v2 — original AI agent integration

These are the owner's **original** agents, not substitute LLM personas. A name in this file does not establish an active session.

| Agent | GitHub task | Responsibility |
|---|---|---|
| Aria | #1 | LibreChat and interactive chat |
| Alex | #2 | Codespaces startup, system diagnostics |
| Astyria | #3 | Real-data-only telemetry and source provenance |
| Aurelius | #4 | Ollama and opt-in emergency Llama 3.2 3B |

## Connection contract

`agents/connection.py` supports authenticated HTTPS agent endpoints. Configure these **on the host**, not in Git:

```bash
export MONOLITH_AGENT_ARIA_URL=https://YOUR-REAL-ARIA-ENDPOINT/messages
export MONOLITH_AGENT_ARIA_TOKEN=YOUR_SECRET
```

Repeat for ALEX, ASTYRIA, AURELIUS. Never commit tokens. Endpoint expects POST JSON `{"message":"...","agent":"Aria"}`, Authorization Bearer token; returns `{"reply":"..."}`. This is an adapter contract; actual existing AI Studio/MCP endpoints may need a different adapter. Verify their real protocol before connecting.

Check connection configuration:

```bash
python3 -c 'from agents.connection import status; print(status())'
```

No endpoint configured means `not_connected`. Never replace missing original agents with fabricated identities or mark tasks completed without verified execution. GitHub issue ownership by agent name is a project label, not a GitHub account assignee. Agent workers need authenticated issue polling and reporting before tasks run automatically.

## Safety

Only HTTPS or local loopback HTTP. No root or shell authority is granted by this connector. Keep API credentials in protected secrets and enforce server-side authorization. REAL DATA ONLY: no simulated agent responses or progress.
