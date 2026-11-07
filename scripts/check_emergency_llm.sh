#!/usr/bin/env bash
set -euo pipefail
echo "Monolith emergency model: llama3.2:3b"
python3 -m core.llm_control status
if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama: NOT INSTALLED"
  exit 0
fi
if ! ollama list >/dev/null 2>&1; then
  echo "Ollama: SERVICE UNAVAILABLE"
  exit 0
fi
echo "Ollama models (actual installed models):"
ollama list
echo "To download manually: ollama pull llama3.2:3b"
echo "To enable for this shell only: export MONOLITH_LLM_EMERGENCY_ENABLED=true"
