"""Monolith MVP: local, read-only HTTP status API.

No demo data, no arbitrary shell commands, no external bind by default.
"""
import json
import os
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def _table_rows(db_path, table, limit=50):
    path = Path(db_path)
    if not path.is_file():
        return []
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        if table not in {"positions", "investigations"}:
            raise ValueError("Unknown table")
        return [dict(row) for row in con.execute(f"SELECT * FROM {table} LIMIT ?", (limit,))]
    except sqlite3.Error:
        return []
    finally:
        con.close()


def snapshot():
    positions = _table_rows(os.environ.get("MONOLITH_POSITIONS_DB", str(ROOT / "fleet.sqlite3")), "positions")
    # Fail closed: old simulation records are never surfaced.
    positions = [p for p in positions if p.get("source") == "telemetry"
                 and str(p.get("source_ref", "")).startswith("trusted-adapter:")]
    investigations = _table_rows(os.environ.get("MONOLITH_TRANSMISSIONS_DB", str(ROOT / "transmissions.sqlite3")), "investigations")
    investigations = [i for i in investigations if i.get("signal_kind") != "hyperspace_simulation"]
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "real_data_only",
        "fleet_positions": positions,
        "transmission_investigations": investigations,
        "agent_status": {agent: "not_connected" for agent in ("Aria", "Alex", "Astyria", "Aurelius")},
        "ollama": "not_verified",
        "librechat": "not_verified",
        "diagnostics": "read_only",
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urlsplit(self.path).path
        if route == "/health":
            payload = {"status": "running", "mode": "real_data_only"}
        elif route == "/api/v1/status":
            payload = snapshot()
        else:
            self.send_error(404)
            return
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    host = os.environ.get("MONOLITH_HOST", "127.0.0.1")
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("MVP binds to loopback only")
    port = int(os.environ.get("MONOLITH_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Monolith MVP status API: http://{host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
