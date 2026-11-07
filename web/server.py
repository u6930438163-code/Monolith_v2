"""Authenticated Monolith web application and read-only workspace APIs."""
import base64
import hashlib
import hmac
import json
import os
import queue
import re
import secrets
import shlex
import socket
import struct
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from agents.connection import AGENTS, config as agent_config, send as send_agent
from core.llm_router_v2 import ModelUnavailable, route
from diagnostics.collector import collect
from mvp.status_server import ROOT, snapshot

WEB_ROOT = ROOT / "web"
MAX_BODY = 32768
MAX_FILE_BYTES = 256 * 1024
MAX_DIR_ENTRIES = 200
MAX_WEBSOCKET_FRAME = 65536
EVENTS = deque(maxlen=200)
SUBSCRIBERS = set()
SUBSCRIBERS_LOCK = threading.Lock()
LOG_LOCK = threading.Lock()
AUTH_FAILURES = {}
AUTH_LOCK = threading.Lock()
VERIFIED_AGENTS = {}
VERIFIED_LOCK = threading.Lock()
MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}$")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _ui_password():
    password = os.environ.get("MONOLITH_UI_PASSWORD") or os.environ.get("MONOLITH_BRIDGE_TOKEN", "")
    if len(password) < 24:
        raise RuntimeError("Set MONOLITH_UI_PASSWORD or MONOLITH_BRIDGE_TOKEN to a secret of at least 24 characters")
    return password


def _session_signature(timestamp):
    key = hashlib.sha256(("monolith-ui-session:" + _ui_password()).encode()).digest()
    return hmac.new(key, timestamp.encode(), hashlib.sha256).hexdigest()


def _valid_session(cookie_header):
    try:
        cookie = SimpleCookie()
        cookie.load(cookie_header or "")
        value = cookie["monolith_session"].value
        timestamp, signature = value.split(".", 1)
        issued = int(timestamp)
        if abs(int(time.time()) - issued) > 43200:
            return False
        return hmac.compare_digest(signature, _session_signature(timestamp))
    except (KeyError, ValueError, RuntimeError):
        return False


def _same_origin(handler):
    origin = handler.headers.get("Origin")
    if not origin:
        return True
    try:
        return urllib.parse.urlsplit(origin).netloc.lower() == handler.headers.get("Host", "").lower()
    except ValueError:
        return False


def _safe_path(value):
    if not isinstance(value, str) or "\x00" in value or "\\" in value:
        raise ValueError("Invalid path")
    relative = Path(value)
    if relative.is_absolute() or any(part in (".", "..") or part.startswith(".") for part in relative.parts):
        raise ValueError("Path is outside the accessible project files")
    resolved = (ROOT / relative).resolve()
    if not resolved.is_relative_to(ROOT.resolve()):
        raise ValueError("Path is outside the accessible project files")
    return resolved


def _directory_listing(path):
    target = _safe_path(path)
    if not target.is_dir():
        raise ValueError("Path is not a directory")
    entries = []
    for item in sorted(target.iterdir(), key=lambda entry: (not entry.is_dir(), entry.name.lower())):
        if item.name.startswith(".") or item.is_symlink():
            continue
        entries.append({
            "name": item.name,
            "type": "directory" if item.is_dir() else "file",
            "size": item.stat().st_size if item.is_file() else None,
        })
        if len(entries) >= MAX_DIR_ENTRIES:
            break
    return {"path": target.relative_to(ROOT).as_posix() if target != ROOT else "", "entries": entries}


def _read_project_file(path):
    target = _safe_path(path)
    if not target.is_file() or target.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("File is missing or larger than the 256 KiB read limit")
    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Only UTF-8 text files can be opened") from exc
    return {"path": target.relative_to(ROOT).as_posix(), "content": content}


def _run_read_only_command(command):
    if not isinstance(command, str) or len(command) > 512:
        raise ValueError("Invalid command")
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise ValueError("Invalid command syntax") from exc
    if not argv:
        return ""
    if argv == ["help"]:
        return "Allowed: help, pwd, ls [path], cat <path>, git status, git log, python --version, ps"
    if argv == ["pwd"]:
        return str(ROOT)
    if argv[0] == "ls" and len(argv) <= 2:
        listing = _directory_listing(argv[1] if len(argv) == 2 else "")
        return "\n".join(f"{'d' if item['type'] == 'directory' else '-'} {item['name']}" for item in listing["entries"]) or "(empty)"
    if argv[0] == "cat" and len(argv) == 2:
        return _read_project_file(argv[1])["content"]
    if argv == ["git", "status"] or argv == ["git", "status", "--short"]:
        args = ["git", "status", "--short", "--branch"]
    elif argv == ["git", "log"] or argv == ["git", "log", "--oneline"]:
        args = ["git", "--no-pager", "log", "-5", "--oneline"]
    elif argv == ["python", "--version"]:
        args = ["python3", "--version"]
    elif argv == ["ps"]:
        diagnostic = collect()
        processes = (diagnostic.get("processes") or {}).get("top_by_rss") or []
        return "\n".join(f"{item['pid']:>7} {item['name']}" for item in processes) or "No process data available"
    else:
        raise ValueError("Command not allowed. Run help for the read-only command list.")
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=5, check=False)
    output = (result.stdout + result.stderr)[:12000]
    return output or f"Exit code: {result.returncode}"


def _hyperspace_status():
    timestamp = _now()
    endpoint = os.environ.get("MONOLITH_HYPERSPACE_URL", "").strip()
    token = os.environ.get("MONOLITH_HYPERSPACE_TOKEN", "")
    if not endpoint or not token:
        return {"status": "not_connected", "source": None, "timestamp_utc": timestamp, "transmissions": []}
    try:
        parsed = urllib.parse.urlsplit(endpoint)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
                or parsed.query or parsed.fragment):
            raise ValueError("Invalid transmission endpoint configuration")
        request = urllib.request.Request(
            endpoint,
            headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
            method="GET",
        )

        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = urllib.request.build_opener(NoRedirect)
        with opener.open(request, timeout=5) as response:
            raw = response.read(512 * 1024 + 1)
        if len(raw) > 512 * 1024:
            raise ValueError("Transmission response exceeds size limit")
        payload = json.loads(raw)
        records = payload.get("transmissions") if isinstance(payload, dict) else None
        if not isinstance(records, list) or len(records) > 100:
            raise ValueError("Invalid transmission response contract")
        transmissions = []
        for item in records:
            if not isinstance(item, dict) or not all(
                isinstance(item.get(key), str) and 0 < len(item[key]) <= limit
                for key, limit in (("source", 512), ("timestamp_utc", 128), ("message", 4000))
            ):
                raise ValueError("Invalid transmission record")
            transmissions.append({key: item[key] for key in ("source", "timestamp_utc", "message")})
        origin = f"https://{parsed.hostname}" + (f":{parsed.port}" if parsed.port else "")
        return {"status": "connected", "source": origin, "timestamp_utc": _now(), "transmissions": transmissions}
    except (OSError, TimeoutError, ValueError, urllib.error.URLError, json.JSONDecodeError):
        try:
            parsed = urllib.parse.urlsplit(endpoint)
            origin = f"https://{parsed.hostname}" if parsed.scheme == "https" and parsed.hostname else None
        except ValueError:
            origin = None
        return {"status": "not_connected", "source": origin, "timestamp_utc": _now(), "transmissions": []}


def _ollama_pull(model):
    if not isinstance(model, str) or not MODEL_RE.fullmatch(model):
        raise ValueError("Invalid Ollama model name")
    base = os.environ.get("MONOLITH_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    parsed = urllib.parse.urlsplit(base)
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost", "::1")
    ):
        raise ValueError("Ollama URL must use HTTPS or loopback HTTP")
    request = urllib.request.Request(
        base + "/api/pull",
        data=json.dumps({"name": model, "stream": False}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        raw = response.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("Ollama response exceeds size limit")
    result = json.loads(raw)
    if not isinstance(result, dict) or result.get("status") != "success":
        raise ValueError("Ollama did not confirm the model download")
    return {"model": model, "status": "success"}


def _record(event, level="INFO"):
    entry = {"timestamp": _now(), "level": level, "event": event[:200]}
    with LOG_LOCK:
        EVENTS.append(entry)
        for subscriber in list(SUBSCRIBERS):
            try:
                subscriber.put_nowait({"type": "event", "message": event[:200]})
            except queue.Full:
                pass


def _status_snapshot():
    result = snapshot()
    with VERIFIED_LOCK:
        verified = dict(VERIFIED_AGENTS)
    for agent, metadata in result.get("agent_status", {}).items():
        try:
            config = agent_config(agent)
        except ValueError:
            continue
        previous = verified.get(agent)
        if (config["status"] == "configured" and previous
                and previous["endpoint"] == config["endpoint"]):
            metadata["status"] = "connected"
            metadata["timestamp_utc"] = previous["timestamp_utc"]
            metadata["source"] = "verified_agent_endpoint"
    return result


def _mark_agent_verified(agent):
    settings = agent_config(agent)
    with VERIFIED_LOCK:
        VERIFIED_AGENTS[agent] = {"endpoint": settings.get("endpoint"), "timestamp_utc": _now()}


def _frame(payload):
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if len(raw) > MAX_WEBSOCKET_FRAME:
        raise ValueError("WebSocket event exceeds frame limit")
    size = len(raw)
    header = bytes([0x81])
    if size < 126:
        header += bytes([size])
    elif size < 65536:
        header += bytes([126]) + struct.pack("!H", size)
    else:
        header += bytes([127]) + struct.pack("!Q", size)
    return header + raw


class Handler(BaseHTTPRequestHandler):
    server_version = "MonolithUI"
    sys_version = ""

    def log_message(self, fmt, *args):
        return

    def _send(self, status, payload, headers=None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if headers:
            for name, value in headers.items():
                self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; connect-src 'self' ws: wss:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")

    def _json(self, status, payload, headers=None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if headers:
            for name, value in headers.items():
                self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status, message):
        self._json(status, {"error": message})

    def _authenticated(self):
        return os.environ.get("MONOLITH_PASSWORDLESS", "").lower() == "true" or _valid_session(self.headers.get("Cookie", ""))

    def _body(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Invalid content length") from exc
        if not 0 < size <= MAX_BODY:
            raise ValueError("Invalid request size")
        data = json.loads(self.rfile.read(size))
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        return data

    def _static(self, path):
        files = {
            "/": (WEB_ROOT / "index.html", "text/html; charset=utf-8"),
            "/assets/app.css": (WEB_ROOT / "app.css", "text/css; charset=utf-8"),
            "/assets/app.js": (WEB_ROOT / "app.js", "text/javascript; charset=utf-8"),
        }
        entry = files.get(path)
        if not entry:
            self.send_error(404)
            return
        file_path, content_type = entry
        body = file_path.read_bytes()
        self.send_response(200)
        self._headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        if path in ("/", "/assets/app.css", "/assets/app.js"):
            return self._static(path)
        if path == "/health":
            return self._json(200, {"service": "monolith-web", "status": "ok"})
        if path == "/api/v1/session":
            return self._json(200, {"authenticated": True}) if self._authenticated() else self._error(401, "unauthorized")
        if path == "/ws":
            return self._websocket() if self._authenticated() else self._error(401, "unauthorized")
        if not self._authenticated():
            return self._error(401, "unauthorized")
        params = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query, keep_blank_values=True)
        if path == "/api/v1/status":
            return self._json(200, _status_snapshot())
        if path == "/api/v1/files":
            try:
                requested = params.get("path", [""])[0]
                target = _safe_path(requested)
                result = _read_project_file(requested) if target.is_file() else _directory_listing(requested)
                return self._json(200, result)
            except ValueError as exc:
                return self._error(400, str(exc))
            except OSError:
                return self._error(404, "file_unavailable")
        if path == "/api/v1/logs":
            with LOG_LOCK:
                entries = list(EVENTS)[-100:]
            return self._json(200, {"entries": entries})
        if path == "/api/v1/hyperspace":
            result = _hyperspace_status()
            return self._json(200, result)
        return self._error(404, "not_found")

    def do_POST(self):
        path = urllib.parse.urlsplit(self.path).path
        if not _same_origin(self):
            return self._error(403, "cross_origin_request_rejected")
        if path == "/api/v1/login" and os.environ.get("MONOLITH_PASSWORDLESS", "").lower() == "true":
            return self._json(200, {"authenticated": True})
        if path == "/api/v1/login":
            client = self.client_address[0]
            now = time.time()
            with AUTH_LOCK:
                attempts = [attempt for attempt in AUTH_FAILURES.get(client, []) if now - attempt < 300]
                AUTH_FAILURES[client] = attempts
                if len(attempts) >= 10:
                    return self._error(429, "too_many_attempts")
            try:
                data = self._body()
                supplied = data.get("password", "")
                if not isinstance(supplied, str) or len(supplied) > 1024:
                    raise ValueError
                valid = hmac.compare_digest(supplied.encode(), _ui_password().encode())
            except (ValueError, json.JSONDecodeError, RuntimeError):
                valid = False
            if not valid:
                with AUTH_LOCK:
                    AUTH_FAILURES[client].append(now)
                return self._error(401, "invalid_credentials")
            with AUTH_LOCK:
                AUTH_FAILURES.pop(client, None)
            timestamp = str(int(now))
            signature = _session_signature(timestamp)
            secure = "; Secure" if self.headers.get("X-Forwarded-Proto", "").lower() == "https" else ""
            cookie = f"monolith_session={timestamp}.{signature}; Path=/; HttpOnly; SameSite=Strict; Max-Age=43200{secure}"
            _record("Sesja właściciela została uwierzytelniona.")
            return self._json(200, {"authenticated": True}, {"Set-Cookie": cookie})
        if path == "/api/v1/logout":
            return self._json(200, {"authenticated": False}, {"Set-Cookie": "monolith_session=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0"})
        if not self._authenticated():
            return self._error(401, "unauthorized")
        try:
            data = self._body()
        except (ValueError, json.JSONDecodeError):
            return self._error(400, "invalid_request")
        if path == "/api/v1/chat":
            message = data.get("message")
            agent = data.get("agent", "local")
            if not isinstance(message, str) or not 0 < len(message.strip()) <= 8000:
                return self._error(400, "invalid_message")
            if agent == "local":
                try:
                    result = route(message)
                    _record("Odpowiedź lokalnego modelu została odebrana.")
                    return self._json(200, {"reply": result["response"], "source": "ollama", "model": result["model"]})
                except ModelUnavailable:
                    return self._error(503, "models_unavailable")
                except (OSError, TimeoutError):
                    return self._error(503, "model_backend_unavailable")
            if agent in AGENTS:
                return self._send_to_agent(agent, message)
            if agent == "all":
                return self._send_to_all(message)
            return self._error(400, "unknown_agent")
        if path == "/api/v1/terminal":
            try:
                result = _run_read_only_command(data.get("command"))
                _record("Wykonano dozwolone polecenie tylko do odczytu.")
                return self._json(200, {"output": result})
            except ValueError as exc:
                return self._error(400, str(exc))
            except (OSError, subprocess.SubprocessError):
                return self._error(502, "terminal_command_failed")
        if path == "/api/v1/ollama/pull":
            try:
                result = _ollama_pull(data.get("model"))
                _record(f"Pobieranie modelu Ollama {result['model']} zostało potwierdzone.")
                return self._json(200, result)
            except ValueError as exc:
                return self._error(400, str(exc))
            except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError):
                return self._error(502, "ollama_download_failed")
        return self._error(404, "not_found")

    def _send_to_agent(self, agent, message):
        try:
            result = send_agent(agent, message)
            _mark_agent_verified(agent)
            _record(f"Agent {agent} zwrócił odpowiedź przez skonfigurowany endpoint.")
            return self._json(200, {"reply": result["reply"], "source": result["source"], "agent": agent})
        except ConnectionError:
            return self._error(503, f"agent_{agent.lower()}_not_connected")
        except (OSError, TimeoutError, urllib.error.URLError):
            return self._error(502, f"agent_{agent.lower()}_unavailable")
        except (ValueError, json.JSONDecodeError):
            return self._error(502, f"agent_{agent.lower()}_invalid_response")

    def _send_to_all(self, message):
        from concurrent.futures import ThreadPoolExecutor, as_completed
        results = []
        with ThreadPoolExecutor(max_workers=len(AGENTS)) as executor:
            futures = {executor.submit(send_agent, agent, message): agent for agent in AGENTS}
            try:
                for future in as_completed(futures, timeout=20):
                    agent = futures[future]
                    try:
                        result = future.result()
                        _mark_agent_verified(agent)
                        results.append({"agent": agent, "status": "connected", "reply": result["reply"], "source": result["source"]})
                        _record(f"Agent {agent} odpowiedział na wiadomość do zespołu.")
                    except ConnectionError:
                        results.append({"agent": agent, "status": "not_connected"})
                    except (OSError, TimeoutError, urllib.error.URLError):
                        results.append({"agent": agent, "status": "unavailable"})
                    except (ValueError, json.JSONDecodeError):
                        results.append({"agent": agent, "status": "invalid_response"})
            except TimeoutError:
                for future, agent in futures.items():
                    if not future.done():
                        future.cancel()
                        results.append({"agent": agent, "status": "unavailable"})
        results.sort(key=lambda result: AGENTS.index(result["agent"]))
        connected = [item for item in results if item["status"] == "connected"]
        if not connected:
            return self._json(503, {"error": "no_agents_connected", "results": results})
        replies = [
            f"{item['agent']}: {item['reply']}" if item["status"] == "connected"
            else f"{item['agent']}: [{item['status']}]"
            for item in results
        ]
        return self._json(200, {
            "reply": "\n\n".join(replies),
            "source": "configured_agent_endpoints",
            "results": results,
        })

    def _read_websocket_frame(self):
        first = self.rfile.read(2)
        if len(first) != 2:
            return None
        opcode = first[0] & 0x0F
        masked = first[1] & 0x80
        size = first[1] & 0x7F
        if size == 126:
            raw = self.rfile.read(2)
            if len(raw) != 2:
                return None
            size = struct.unpack("!H", raw)[0]
        elif size == 127:
            return None
        if not masked or size > MAX_WEBSOCKET_FRAME:
            return None
        mask = self.rfile.read(4)
        payload = self.rfile.read(size)
        if len(mask) != 4 or len(payload) != size:
            return None
        decoded = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        return opcode, decoded

    def _websocket(self):
        if not _same_origin(self):
            return self._error(403, "cross_origin_request_rejected")
        if self.headers.get("Upgrade", "").lower() != "websocket" or "upgrade" not in self.headers.get("Connection", "").lower():
            return self._error(400, "invalid_websocket_upgrade")
        key = self.headers.get("Sec-WebSocket-Key", "")
        try:
            if len(base64.b64decode(key, validate=True)) != 16:
                raise ValueError
        except (ValueError, TypeError):
            return self._error(400, "invalid_websocket_key")
        accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        self.send_response(101, "Switching Protocols")
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()
        self.wfile.flush()
        subscriber = queue.Queue(maxsize=32)
        with SUBSCRIBERS_LOCK:
            SUBSCRIBERS.add(subscriber)
        self.connection.settimeout(1)
        last_status = 0
        try:
            while True:
                now = time.monotonic()
                if now - last_status >= 3:
                    self.wfile.write(_frame({"type": "status", "payload": _status_snapshot()}))
                    self.wfile.flush()
                    last_status = now
                try:
                    frame = self._read_websocket_frame()
                    if frame is None:
                        break
                    opcode, payload = frame
                    if opcode == 8:
                        break
                    if opcode == 9 and len(payload) <= 125:
                        raw = bytes([0x8A, len(payload)]) + payload
                        self.connection.sendall(raw)
                except socket.timeout:
                    pass
                while True:
                    try:
                        event = subscriber.get_nowait()
                    except queue.Empty:
                        break
                    self.wfile.write(_frame(event))
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionError, OSError, ValueError):
            pass
        finally:
            with SUBSCRIBERS_LOCK:
                SUBSCRIBERS.discard(subscriber)
        return None


def main():
    host = os.environ.get("MONOLITH_WEB_HOST", "127.0.0.1")
    port = int(os.environ.get("MONOLITH_WEB_PORT", "8000"))
    if os.environ.get("MONOLITH_PASSWORDLESS", "").lower() != "true":
        _ui_password()
    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    server.allow_reuse_address = True
    print(f"Monolith web listening on http://{host}:{port}", flush=True)
    _record("Interfejs Monolith uruchomił się.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
