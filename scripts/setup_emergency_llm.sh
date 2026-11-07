#!/usr/bin/env bash
set -euo pipefail
if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama not installed. Install from the official Ollama project first." >&2
  exit 1
fi
if ! ollama list >/dev/null 2>&1; then
  echo "Ollama service unavailable. Start Ollama and retry." >&2
  exit 1
fi
ollama pull qwen3:1.7b
echo "Emergency model downloaded. Set MONOLITH_LLM_EMERGENCY=qwen3:1.7b"
