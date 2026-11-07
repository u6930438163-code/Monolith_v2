"""Monolith MVP: local, read-only HTTP status API.

No demo data, no arbitrary shell commands, no external bind by default.
"""
import json
import os
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from agents.connection import status as agent_connection_status
from diagnostics.collector import collect as collect_diagnostics

ROOT = Path(__file__).resolve().parents[1]
MAX_PROBE_BYTES = 1024 * 1024


def _source_origin(url):
    try:
        parsed = urlsplit(url)
        if not parsed.hostname:
            return None
        port = ":" + str(parsed.port) if parsed.port else ""
        return f"{parsed.scheme}://{parsed.hostname}{port}"
    except ValueError:
        return None


def _http_probe(url):
    timestamp = datetime.now(timezone.utc).isoformat()
    source = _source_origin(url)
    try:
        parsed = urlsplit(url)
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Invalid probe URL")
        if parsed.scheme != "https" and not (
            parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost", "::1")
        ):
            raise ValueError("Probe URL must use HTTPS or loopback HTTP")

        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = urllib.request.build_opener(NoRedirect)
        with opener.open(url, timeout=2) as response:
            raw = response.read(MAX_PROBE_BYTES + 1)
        if len(raw) > MAX_PROBE_BYTES:
            raise ValueError("Probe response too large")
        return {"status": "connected", "source": source, "timestamp_utc": timestamp, "body": raw}
    except (OSError, TimeoutError, ValueError, urllib.error.URLError):
        return {"status": "not_connected", "source": source, "timestamp_utc": timestamp, "body": None}


def _service_status(url, *, json_key=None):
    if not url:
        return {"status": "not_connected", "source": None,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(), "data": None}
    result = _http_probe(url)
    data = None
    status = result["status"]
    if status == "connected" and json_key:
        try:
            payload = json.loads(result["body"])
            data = payload.get(json_key) if isinstance(payload, dict) else None
            if not isinstance(data, list):
                status = "no_data"
                data = None
        except (json.JSONDecodeError, UnicodeDecodeError):
            status = "no_data"
    return {"status": status, "source": result["source"],
            "timestamp_utc": result["timestamp_utc"], "data": data}


def _table_rows(db_path, table, limit=50):
    path = Path(db_path)
    if not path.is_file():
        return []
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        if table != "position_reports":
            raise ValueError("Unknown table")
        return [dict(row) for row in con.execute(f"SELECT * FROM {table} LIMIT ?", (limit,))]
    except sqlite3.Error:
        return []
    finally:
        con.close()


def snapshot():
    positions = _table_rows(os.environ.get("MONOLITH_POSITIONS_DB", str(ROOT / "fleet.sqlite3")), "position_reports")
    # Fail closed: old simulation records are never surfaced.
    positions = [p for p in positions if p.get("source") == "telemetry"
                 and str(p.get("source_ref", "")).startswith("trusted-adapter:")]
    # No authenticated transmission source exists yet, so queued requests are not operational reports.
    investigations = []
    diagnostics = collect_diagnostics()
    ollama_url = os.environ.get("MONOLITH_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    ollama = _service_status(ollama_url + "/api/tags", json_key="models")
    librechat = _service_status(os.environ.get("MONOLITH_LIBRECHAT_HEALTH_URL", "").strip())
    agent_config = agent_connection_status()
    agent_timestamp = datetime.now(timezone.utc).isoformat()
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "real_data_only",
        "fleet_positions": positions,
        "transmission_investigations": investigations,
        "agent_status": {
            agent: {
                "status": "not_connected" if state == "not_connected" else "not_verified",
                "configuration": state,
                "source": "host_environment",
                "timestamp_utc": agent_timestamp,
            }
            for agent, state in agent_config.items()
        },
        "ollama": ollama,
        "librechat": librechat,
        "diagnostics": {
            "status": "available" if any(diagnostics.get(key) is not None
                                           for key in ("cpu_percent", "memory", "disk")) else "no_data",
            "source": "local_os",
            "timestamp_utc": diagnostics["timestamp"],
            "data": diagnostics,
        },
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
