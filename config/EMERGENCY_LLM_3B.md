# Emergency LLM: Llama 3.2 3B

**Default: OFF.** Use `core.llm_router_v2.route` for new integrations.

Install the model when Ollama is available:

```bash
ollama pull llama3.2:3b
```

Keep emergency disabled:

```bash
export MONOLITH_LLM_EMERGENCY_ENABLED=false
```

Explicitly enable fallback:

```bash
export MONOLITH_LLM_EMERGENCY_ENABLED=true
```

Configure primary and secondary local Ollama models separately with `MONOLITH_LLM_PRIMARY` and `MONOLITH_LLM_SECONDARY`. The emergency model is only tried if enabled and previous configured models fail. No root or shell access is granted by the router.

**Migration warning:** legacy `core/llm_fallback.py` still contains the older 1.7B default and must not be used by new integrations. The safe router is `core/llm_router_v2.py`. Runtime wiring and Ollama installation are not yet confirmed.
