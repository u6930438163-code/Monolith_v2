# Emergency local LLM: Qwen3 1.7B

The third-tier emergency model is `qwen3:1.7b` served by local Ollama.

## Installation (Ubuntu/Codespaces with Ollama installed)

```bash
bash scripts/setup_emergency_llm.sh
export MONOLITH_OLLAMA_URL=http://127.0.0.1:11434
export MONOLITH_LLM_PRIMARY=llama3.2-vision:11b
export MONOLITH_LLM_SECONDARY=qwen3:4b
export MONOLITH_LLM_EMERGENCY=qwen3:1.7b
python3 -m core.llm_fallback "Opisz stan usługi Ollama"
python3 -m unittest tests.test_llm_fallback -v
```

Primary and secondary values above are examples and must match models actually installed on the target host. A remote API fallback is **not** implemented in this router.

This is an independent Python entry point; it is not yet connected to LibreChat or the central chat. It reports which Ollama model answered and whether fallback was used. Failure of all models raises an error rather than inventing a response.

The small emergency model is text-only and should not be relied on for vision or complex code tasks. No shell or root execution is performed.
