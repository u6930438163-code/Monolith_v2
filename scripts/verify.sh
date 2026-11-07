#!/usr/bin/env bash
# Read-only checks. Run from Monolith_v2 repository root.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
fail=0
check() {
  echo
  echo "== $1 =="
  shift
  "$@" || { echo "FAILED"; fail=1; }
}
check "Python unit tests" python3 -m unittest discover -s tests -v
check "Python compile" python3 -m compileall -q bridge codex core diagnostics vision tests
if command -v ollama >/dev/null 2>&1; then
  echo "== Ollama model status =="
  ollama list || fail=1
else
  echo "Ollama not installed (optional for code tests)."
fi
if command -v codex >/dev/null 2>&1; then
  echo "Codex CLI found: $(command -v codex)"
else
  echo "Codex CLI not installed."
fi
if command -v systemctl >/dev/null 2>&1; then
  for unit in monolith-bridge monolith-codex; do
    systemctl is-active "$unit" || true
  done
fi
if (( fail )); then
  echo "Some checks failed."; exit 1
fi
echo "Basic local checks passed. No end-to-end LibreChat test performed."
