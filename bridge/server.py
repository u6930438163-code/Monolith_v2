"""Monolith local authenticated bridge: health, diagnostics and Ollama Vision.

Standard-library HTTP API for trusted backend-to-backend integration.
Bind to loopback only; put behind authenticated LibreChat backend proxy.
"""
import base64
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from diagnostics.collector import collect
from vision.ollama_vision import analyze_image, MAX_IMAGE_BYTES

MAX_BODY = 17 * 1024 * 1024


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def authenticated(self):
        token = os.environ.get("MONOLITH_BRIDGE_TOKEN", "")
        supplied = self.headers.get("Authorization", "")
        return len(token) >= 32 and hmac.compare_digest(supplied, "Bearer " + token)

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {"service": "monolith-bridge", "status": "ok"})
        elif not self.authenticated():
            self.send_json(401, {"error": "unauthorized"})
        elif self.path == "/v1/diagnostics":
            self.send_json(200, collect())
        else:
            self.send_json(404, {"error": "not_found"})

    def do_POST(self):
        if not self.authenticated():
            self.send_json(401, {"error": "unauthorized"})
            return
        if self.path != "/v1/vision/analyze":
            self.send_json(404, {"error": "not_found"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= MAX_BODY:
                self.send_json(413, {"error": "invalid_size"})
                return
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict) or set(payload) != {"image_base64", "prompt"}:
                raise ValueError("Expected image_base64 and prompt")
            if not isinstance(payload["image_base64"], str) or not isinstance(payload["prompt"], str):
                raise ValueError("Invalid field types")
            image = base64.b64decode(payload["image_base64"], validate=True)
            if len(image) > MAX_IMAGE_BYTES:
                self.send_json(413, {"error": "image_too_large"})
                return
            self.send_json(200, analyze_image(image, payload["prompt"]))
        except (ValueError, json.JSONDecodeError):
            self.send_json(400, {"error": "invalid_request"})
        except Exception:
            # Do not leak internal endpoint details or user images.
            self.send_json(502, {"error": "vision_backend_unavailable"})

    def log_message(self, fmt, *args):
        # Do not log request headers or image content.
        pass


def main():
    if len(os.environ.get("MONOLITH_BRIDGE_TOKEN", "")) < 32:
        raise SystemExit("Set MONOLITH_BRIDGE_TOKEN to a random secret >= 32 characters")
    host = os.environ.get("MONOLITH_BRIDGE_HOST", "127.0.0.1")
    if host not in {"127.0.0.1", "::1"}:
        raise SystemExit("Bridge must bind to loopback; use a trusted reverse proxy")
    port = int(os.environ.get("MONOLITH_BRIDGE_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Monolith bridge listening on {host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
