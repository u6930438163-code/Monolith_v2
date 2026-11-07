"""Authenticated loopback chat-to-Ollama gateway for Monolith.

Emergency Llama 3.2 3B is disabled unless enabled by server environment.
Never accepts a client-supplied model or emergency toggle.
"""
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from core.llm_router_v2 import route, ModelUnavailable

MAX_BODY = 32768


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, obj):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def authorized(self):
        expected = os.getenv("MONOLITH_BRIDGE_TOKEN", "")
        return len(expected) >= 32 and hmac.compare_digest(
            self.headers.get("Authorization", ""), "Bearer " + expected)

    def do_GET(self):
        if not self.authorized():
            return self.respond(401, {"error": "unauthorized"})
        if self.path != "/v1/chat/models":
            return self.respond(404, {"error": "not_found"})
        enabled = os.getenv("MONOLITH_LLM_EMERGENCY_ENABLED", "false").lower() in ("true", "yes", "1")
        return self.respond(200, {
            "provider": "ollama",
            "primary": os.getenv("MONOLITH_LLM_PRIMARY") or None,
            "secondary": os.getenv("MONOLITH_LLM_SECONDARY") or None,
            "emergency": {"model": "llama3.2:3b", "enabled": enabled},
            "availability": "not_checked",
        })

    def do_POST(self):
        if not self.authorized():
            return self.respond(401, {"error": "unauthorized"})
        if self.path != "/v1/chat/generate":
            return self.respond(404, {"error": "not_found"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= MAX_BODY:
                return self.respond(413, {"error": "invalid_size"})
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict) or set(data) != {"prompt"}:
                return self.respond(400, {"error": "expected_prompt_only"})
            prompt = data["prompt"]
            if not isinstance(prompt, str) or not 0 < len(prompt.strip()) <= 16000:
                return self.respond(400, {"error": "invalid_prompt"})
            answer = route(prompt)
            return self.respond(200, answer)
        except (ValueError, json.JSONDecodeError):
            return self.respond(400, {"error": "invalid_request"})
        except ModelUnavailable:
            return self.respond(503, {"error": "models_unavailable"})
        except Exception:
            return self.respond(502, {"error": "model_backend_error"})

    def log_message(self, fmt, *args):
        # Do not log prompts or authentication credentials.
        pass


def main():
    if len(os.getenv("MONOLITH_BRIDGE_TOKEN", "")) < 32:
        raise SystemExit("MONOLITH_BRIDGE_TOKEN must contain at least 32 characters")
    host = os.getenv("MONOLITH_CHAT_HOST", "127.0.0.1")
    if host not in ("127.0.0.1", "::1"):
        raise SystemExit("Loopback binding required")
    port = int(os.getenv("MONOLITH_CHAT_PORT", "8766"))
    print(f"Monolith chat gateway listening on {host}:{port}", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
