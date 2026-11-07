#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="${MONOLITH_MVP_STATE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/monolith}"
HOST="${MONOLITH_HOST:-127.0.0.1}"
STATUS_PORT="${MONOLITH_PORT:-8765}"
CHAT_PORT="${MONOLITH_CHAT_PORT:-8766}"
BRIDGE_TOKEN="${MONOLITH_BRIDGE_TOKEN:-}"

if [[ "$HOST" != "127.0.0.1" && "$HOST" != "localhost" && "$HOST" != "::1" ]]; then
  echo "MVP services must bind to loopback." >&2
  exit 2
fi

mkdir -p "$STATE_DIR"

start_service() {
  local name="$1" module="$2" port="$3" host_var="$4" port_var="$5"
  local pid_file="$STATE_DIR/$name.pid" log_file="$STATE_DIR/$name.log" pid command
  if [[ -f "$pid_file" ]]; then
    pid="$(<"$pid_file")"
    command="$(ps -p "$pid" -o args= 2>/dev/null || true)"
    if [[ "$command" == *"-m $module"* ]]; then
      echo "$name already running (pid $pid, port $port)."
      return
    fi
    rm -f "$pid_file"
  fi
  cd "$ROOT"
  nohup env "$host_var=$HOST" "$port_var=$port" python3 -m "$module" \
    >>"$log_file" 2>&1 </dev/null &
  pid=$!
  printf '%s\n' "$pid" > "$pid_file"
  echo "$name starting (pid $pid, port $port); log: $log_file"
}

stop_service() {
  local name="$1" module="$2"
  local pid_file="$STATE_DIR/$name.pid" pid command
  if [[ ! -f "$pid_file" ]]; then
    echo "$name not managed by this script."
    return
  fi
  pid="$(<"$pid_file")"
  command="$(ps -p "$pid" -o args= 2>/dev/null || true)"
  if [[ "$command" == *"-m $module"* ]]; then
    kill "$pid"
    echo "$name stopped."
  else
    echo "$name process is no longer running; stale PID file removed."
  fi
  rm -f "$pid_file"
}

case "${1:-start}" in
  start)
    if command -v curl >/dev/null 2>&1 && curl --silent --fail --max-time 1 "http://$HOST:$STATUS_PORT/health" >/dev/null; then
      echo "Monolith status API already responds at http://$HOST:$STATUS_PORT."
    else
      start_service status mvp.status_server "$STATUS_PORT" MONOLITH_HOST MONOLITH_PORT
    fi
    if (( ${#BRIDGE_TOKEN} >= 32 )); then
      start_service chat bridge.chat_gateway "$CHAT_PORT" MONOLITH_CHAT_HOST MONOLITH_CHAT_PORT
    else
      echo "Chat gateway not started: set MONOLITH_BRIDGE_TOKEN (at least 32 characters)."
    fi
    echo "Status: http://$HOST:$STATUS_PORT/api/v1/status"
    ;;
  stop)
    stop_service chat bridge.chat_gateway
    stop_service status mvp.status_server
    ;;
  *)
    echo "Usage: $0 [start|stop]" >&2
    exit 2
    ;;
esac