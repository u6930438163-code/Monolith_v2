#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PASSWORD_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/monolith"
PASSWORD_FILE="$PASSWORD_DIR/ui-password"

if [[ -z "${MONOLITH_UI_PASSWORD:-}" ]]; then
  umask 077
  mkdir -p "$PASSWORD_DIR"
  chmod 700 "$PASSWORD_DIR"
  if [[ -L "$PASSWORD_FILE" ]]; then
    echo "Refusing to use a symbolic link as the UI password file." >&2
    exit 2
  fi
  if [[ ! -s "$PASSWORD_FILE" ]]; then
    python3 -c 'import os,secrets,sys; p=sys.argv[1]; fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|getattr(os,"O_NOFOLLOW",0),0o600); os.write(fd,(secrets.token_urlsafe(32)+"\n").encode()); os.close(fd)' "$PASSWORD_FILE"
  fi
  chmod 600 "$PASSWORD_FILE"
  read -r MONOLITH_UI_PASSWORD < "$PASSWORD_FILE"
  export MONOLITH_UI_PASSWORD
  echo "Private UI password stored outside the repository: $PASSWORD_FILE"
  echo "Read it locally with: cat '$PASSWORD_FILE'"
fi

if [[ -z "${MONOLITH_WEB_HOST:-}" ]]; then
  if [[ "${CODESPACES:-}" == "true" ]]; then
    MONOLITH_WEB_HOST="0.0.0.0"
  else
    MONOLITH_WEB_HOST="127.0.0.1"
  fi
fi
export MONOLITH_WEB_HOST
export MONOLITH_WEB_PORT="${MONOLITH_WEB_PORT:-8000}"

cd "$ROOT"
exec python3 -m web.server
