#!/usr/bin/env bash
# Monolith_v2 Debian 13 / Ubuntu bootstrap.
# Run from repository root. Does not start services or download huge models by default.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PREFIX="${MONOLITH_PREFIX:-/opt/monolith}"
STATE="${MONOLITH_STATE:-/var/lib/monolith-codex}"
CONFIG_DIR="${MONOLITH_CONFIG_DIR:-/etc/monolith}"
INSTALL_OLLAMA=0
PULL_MODEL=0
INSTALL_CODEX=0
ENABLE_SERVICES=0
DRY_RUN=0
usage() {
  cat <<'HELP'
Usage: sudo bash scripts/install.sh [options]
  --dry-run           Print planned operations without changing system
  --with-ollama       Install Ollama using the official installer (review first)
  --pull-model        Pull llama3.2-vision:11b (large download; Ollama required)
  --with-codex        Install Codex CLI using npm (requires Node/npm)
  --enable-services   Enable/start systemd bridge and Codex worker after install
  --help              Show help
Default installs Python runtime, files and service templates only.
Secrets and Codex authentication must be configured by operator.
HELP
}
while (($#)); do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --with-ollama) INSTALL_OLLAMA=1 ;;
    --pull-model) PULL_MODEL=1 ;;
    --with-codex) INSTALL_CODEX=1 ;;
    --enable-services) ENABLE_SERVICES=1 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
  shift
done
run() {
  printf ' +'; printf ' %q' "$@"; printf '\n'
  if (( ! DRY_RUN )); then "$@"; fi
}
[[ -f "$ROOT/bridge/server.py" ]] || { echo "Run from Monolith_v2 checkout" >&2; exit 1; }
[[ -f /etc/os-release ]] || { echo "Unsupported OS" >&2; exit 1; }
# shellcheck disable=SC1091
source /etc/os-release
case "${ID:-}" in
  debian|ubuntu) ;;
  *) echo "Only Debian and Ubuntu supported; found ${ID:-unknown}" >&2; exit 1 ;;
esac
if (( ! DRY_RUN )) && [[ "$EUID" -ne 0 ]]; then
  echo "Run as root (sudo), or use --dry-run" >&2; exit 1
fi
if (( ENABLE_SERVICES )) && (( DRY_RUN == 0 )); then
  echo "Warning: enabling services requires validated credentials and Codex CLI auth."
  read -r -p "Type ENABLE to continue: " reply
  [[ "$reply" == ENABLE ]] || exit 1
fi
run apt-get update
run apt-get install -y python3 python3-venv python3-pip ca-certificates curl git
if (( ! DRY_RUN )); then
  id monolith >/dev/null 2>&1 || useradd --system --home-dir /var/lib/monolith --shell /usr/sbin/nologin monolith
fi
run install -d -m 0755 "$PREFIX"
run install -d -o monolith -g monolith -m 0700 "$STATE"
run install -d -m 0700 "$CONFIG_DIR"
# Do not copy tracked secrets or .git into deployment directory.
if (( ! DRY_RUN )); then
  for d in bridge codex core diagnostics vision; do
    cp -a "$ROOT/$d" "$PREFIX/"
  done
  python3 -m venv "$PREFIX/.venv"
  "$PREFIX/.venv/bin/pip" install --disable-pip-version-check -r "$ROOT/diagnostics/requirements.txt"
  python3 -m compileall -q "$PREFIX/bridge" "$PREFIX/codex" "$PREFIX/core" "$PREFIX/diagnostics" "$PREFIX/vision"
  if [[ ! -f "$CONFIG_DIR/bridge.env" ]]; then
    token="$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')"
    printf 'MONOLITH_BRIDGE_TOKEN=%s\nOLLAMA_API_URL=http://127.0.0.1:11434\n' "$token" > "$CONFIG_DIR/bridge.env"
    chmod 0600 "$CONFIG_DIR/bridge.env"
  fi
else
  echo " + copy bridge/codex/core/diagnostics/vision to $PREFIX"
  echo " + create venv, install psutil, compile modules and create protected token file"
fi
if (( INSTALL_OLLAMA )); then
  echo "Ollama installer requires separate verification of the official installation instructions."
  echo "Install Ollama manually from https://ollama.com/download/linux and re-run --pull-model."
fi
if (( PULL_MODEL )); then
  if (( DRY_RUN )); then
    echo " + ollama pull llama3.2-vision:11b"
  else
    command -v ollama >/dev/null || { echo "Ollama not installed" >&2; exit 1; }
    run ollama pull llama3.2-vision:11b
  fi
fi
if (( INSTALL_CODEX )); then
  if (( DRY_RUN )); then
    echo " + npm install -g @openai/codex"
  else
    command -v npm >/dev/null || { echo "Install supported Node.js and npm first" >&2; exit 1; }
    run npm install -g @openai/codex
  fi
fi
if (( ! DRY_RUN )); then
  for service in monolith-bridge monolith-codex; do
    sed "s|/usr/bin/python3 -m |$PREFIX/.venv/bin/python -m |g; s|/opt/monolith|$PREFIX|g; s|/var/lib/monolith-codex|$STATE|g; s|/etc/monolith|$CONFIG_DIR|g" "$ROOT/deploy/$service.service" > "/etc/systemd/system/$service.service"
  done
  systemctl daemon-reload
else
  echo " + generate systemd units with virtualenv Python"
fi
if (( ENABLE_SERVICES )); then
  run systemctl enable --now monolith-bridge.service
  if command -v codex >/dev/null 2>&1 || (( DRY_RUN )); then
    run systemctl enable --now monolith-codex.service
  else
    echo "Codex worker not started: CLI not installed."
  fi
fi
echo "Bootstrap complete. Run: bash scripts/verify.sh"
echo "LibreChat, MCP integration and authentication still require separate setup."
