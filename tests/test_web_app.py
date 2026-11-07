import base64
import json
import os
import socket
import struct
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import MagicMock, patch

from web import server


class WebApplicationTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"MONOLITH_UI_PASSWORD": "unit-test-password-with-at-least-24-chars"}, clear=False)
        self.env.start()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.httpd.daemon_threads = True
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.host, self.port = self.httpd.server_address
        self.base = f"http://{self.host}:{self.port}"
        self.cookie = None

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=3)
        self.env.stop()

    def request(self, path, *, method="GET", body=None, cookie=None, origin=None, extra_headers=None):
        headers = dict(extra_headers or {})
        if body is not None:
            headers["Content-Type"] = "application/json"
        if cookie:
            headers["Cookie"] = cookie
        if origin is not None:
            headers["Origin"] = origin
        request = urllib.request.Request(
            self.base + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers=headers,
            method=method,
        )
        try:
            response = urllib.request.urlopen(request, timeout=5)
        except urllib.error.HTTPError as error:
            response = error
        result = response.status, response.headers, response.read()
        response.close()
        return result

    def login(self):
        status, headers, body = self.request(
            "/api/v1/login",
            method="POST",
            body={"password": "unit-test-password-with-at-least-24-chars"},
            origin=self.base,
        )
        self.assertEqual(status, 200, body)
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertIn("SameSite=Strict", headers["Set-Cookie"])
        self.cookie = headers["Set-Cookie"].split(";", 1)[0]
        return self.cookie

    def test_static_frontend_is_served_with_security_headers(self):
        status, headers, body = self.request("/")
        self.assertEqual(status, 200)
        self.assertIn(b"Monolith", body)
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])

    def test_protected_api_requires_a_session(self):
        status, _, body = self.request("/api/v1/status")
        self.assertEqual(status, 401)
        self.assertEqual(json.loads(body)["error"], "unauthorized")

    def test_login_signs_secure_http_only_same_site_cookie(self):
        cookie = self.login()
        _, _, body = self.request("/api/v1/session", cookie=cookie)
        self.assertTrue(json.loads(body)["authenticated"])

    def test_invalid_login_and_cross_origin_posts_are_rejected(self):
        status, _, _ = self.request(
            "/api/v1/login",
            method="POST",
            body={"password": "wrong"},
            origin=self.base,
        )
        self.assertEqual(status, 401)
        status, _, _ = self.request(
            "/api/v1/chat",
            method="POST",
            body={"message": "hello", "agent": "local"},
            cookie=self.login(),
            origin="https://attacker.example",
        )
        self.assertEqual(status, 403)

    def test_file_browser_is_confined_to_non_hidden_project_files(self):
        cookie = self.login()
        status, _, body = self.request("/api/v1/files", cookie=cookie)
        self.assertEqual(status, 200)
        listing = json.loads(body)
        self.assertTrue(any(item["name"] == "README.md" for item in listing["entries"]))
        self.assertFalse(any(item["name"].startswith(".") for item in listing["entries"]))
        status, _, body = self.request("/api/v1/files?path=../README.md", cookie=cookie)
        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body)["error"], "Path is outside the accessible project files")

    def test_terminal_uses_a_bounded_allowlist_and_never_a_shell(self):
        self.assertEqual(server._run_read_only_command("help").split(",")[0], "Allowed: help")
        with self.assertRaises(ValueError):
            server._run_read_only_command("cat README.md; touch /tmp/monolith-test")
        with self.assertRaises(ValueError):
            server._run_read_only_command("bash -c 'id'")
        self.assertIn("Monolith", server._run_read_only_command("cat README.md"))

    def test_unconfigured_agents_are_reported_without_simulated_replies(self):
        with patch.dict(os.environ, {"MONOLITH_UI_PASSWORD": "unit-test-password-with-at-least-24-chars"}, clear=True):
            response, _, raw = self.request(
                "/api/v1/chat",
                method="POST",
                body={"message": "status", "agent": "Aria"},
                cookie=self.login(),
                origin=self.base,
            )
        self.assertEqual(response, 503)
        self.assertEqual(json.loads(raw)["error"], "agent_aria_not_connected")

    def test_local_chat_uses_the_existing_model_router(self):
        with patch("web.server.route", return_value={"response": "actual model reply", "model": "real-model"}):
            status, _, raw = self.request(
                "/api/v1/chat",
                method="POST",
                body={"message": "hello", "agent": "local"},
                cookie=self.login(),
                origin=self.base,
            )
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw), {
            "reply": "actual model reply",
            "source": "ollama",
            "model": "real-model",
        })

    def test_agent_chat_authenticates_to_a_real_configured_endpoint(self):
        class AgentHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.server.authorization = self.headers.get("Authorization")
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                self.server.agent = payload["agent"]
                response = json.dumps({"reply": "verified endpoint response"}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response)

            def log_message(self, fmt, *args):
                return

        agent_server = ThreadingHTTPServer(("127.0.0.1", 0), AgentHandler)
        agent_thread = threading.Thread(target=agent_server.serve_forever, daemon=True)
        agent_thread.start()
        token = "configured-test-endpoint-token"
        endpoint = f"http://127.0.0.1:{agent_server.server_address[1]}/messages"
        try:
            with patch.dict(os.environ, {
                "MONOLITH_AGENT_ARIA_URL": endpoint,
                "MONOLITH_AGENT_ARIA_TOKEN": token,
            }):
                status, _, raw = self.request(
                    "/api/v1/chat",
                    method="POST",
                    body={"message": "check connection", "agent": "Aria"},
                    cookie=self.login(),
                    origin=self.base,
                )
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(raw)["reply"], "verified endpoint response")
                self.assertEqual(agent_server.authorization, f"Bearer {token}")
                self.assertEqual(agent_server.agent, "Aria")
                with patch("web.server.snapshot", return_value={
                    "agent_status": {"Aria": {"status": "not_verified"}}
                }):
                    self.assertEqual(server._status_snapshot()["agent_status"]["Aria"]["status"], "connected")
        finally:
            with server.VERIFIED_LOCK:
                server.VERIFIED_AGENTS.pop("Aria", None)
            agent_server.shutdown()
            agent_server.server_close()
            agent_thread.join(timeout=3)

    def test_ollama_pull_reports_only_a_confirmed_model_download(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = b'{"status":"success"}'
        with patch("web.server.urllib.request.urlopen", return_value=response):
            self.assertEqual(
                server._ollama_pull("real-model:1b"),
                {"model": "real-model:1b", "status": "success"},
            )
        with patch.dict(os.environ, {"MONOLITH_OLLAMA_URL": "http://ollama.example"}, clear=False):
            with self.assertRaises(ValueError):
                server._ollama_pull("real-model:1b")

    def test_hyperspace_requires_a_configured_authenticated_source(self):
        with patch.dict(os.environ, {}, clear=True):
            result = server._hyperspace_status()
        self.assertEqual(result["status"], "not_connected")
        self.assertEqual(result["transmissions"], [])

    def test_websocket_upgrade_requires_an_authenticated_session(self):
        nonce = base64.b64encode(b"0123456789abcdef").decode()
        status, _, _ = self.request(
            "/ws",
            extra_headers={
                "Upgrade": "websocket",
                "Connection": "Upgrade",
                "Sec-WebSocket-Key": nonce,
                "Sec-WebSocket-Version": "13",
                "Origin": self.base,
            },
        )
        self.assertEqual(status, 401)

    def test_authenticated_websocket_streams_live_status_frames(self):
        cookie = self.login()
        key = base64.b64encode(b"0123456789abcdef").decode()
        payload = {"timestamp_utc": "test", "agent_status": {}}
        with patch("web.server.snapshot", return_value=payload):
            with socket.create_connection((self.host, self.port), timeout=5) as connection:
                connection.settimeout(5)
                request = (
                    "GET /ws HTTP/1.1\r\n"
                    f"Host: {self.host}:{self.port}\r\n"
                    "Upgrade: websocket\r\n"
                    "Connection: Upgrade\r\n"
                    f"Sec-WebSocket-Key: {key}\r\n"
                    "Sec-WebSocket-Version: 13\r\n"
                    f"Origin: {self.base}\r\n"
                    f"Cookie: {cookie}\r\n\r\n"
                )
                connection.sendall(request.encode())
                stream = connection.makefile("rb")
                response = stream.readline()
                self.assertIn(b"101", response)
                while stream.readline() not in (b"\r\n", b"\n", b""):
                    pass
                first, second = stream.read(2)
                self.assertEqual(first & 0x0F, 1)
                size = second & 0x7F
                if size == 126:
                    size = struct.unpack("!H", stream.read(2))[0]
                frame = json.loads(stream.read(size))
                self.assertEqual(frame["type"], "status")
                self.assertEqual(frame["payload"]["timestamp_utc"], "test")


if __name__ == "__main__":
    unittest.main()
