"""Explicit connection to original external AI agent endpoints.

No mock agents. A missing endpoint is reported as not_connected.
Agent endpoints must be HTTPS or loopback HTTP; tokens stay in environment.
"""
import json
import os
import urllib.parse
import urllib.request

AGENTS = ("Aria", "Alex", "Astyria", "Aurelius")
MAX_REPLY_BYTES = 1024 * 1024


def config(agent):
    if agent not in AGENTS:
        raise ValueError("Unknown agent")
    prefix = "MONOLITH_AGENT_" + agent.upper()
    endpoint = os.getenv(prefix + "_URL", "").strip()
    token = os.getenv(prefix + "_TOKEN", "")
    if not endpoint:
        return {"agent": agent, "status": "not_connected"}
    parsed = urllib.parse.urlsplit(endpoint)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Agent URL must not contain credentials or query")
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost", "::1")
    ):
        raise ValueError("Only HTTPS or loopback HTTP agent endpoints are allowed")
    if not parsed.hostname or not token:
        return {"agent": agent, "status": "not_connected"}
    return {"agent": agent, "status": "configured", "endpoint": endpoint}


def send(agent, message, *, timeout=15):
    settings = config(agent)
    if settings["status"] != "configured":
        raise ConnectionError("Agent endpoint not connected")
    if not isinstance(message, str) or not 0 < len(message.strip()) <= 8000:
        raise ValueError("Invalid message")
    token = os.environ["MONOLITH_AGENT_" + agent.upper() + "_TOKEN"]
    req = urllib.request.Request(settings["endpoint"],
        data=json.dumps({"message": message, "agent": agent}).encode("utf-8"),
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        method="POST")
    # Explicitly disable redirects to prevent credentials from following them.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = urllib.request.build_opener(NoRedirect)
    with opener.open(req, timeout=timeout) as response:
        raw = response.read(MAX_REPLY_BYTES + 1)
    if len(raw) > MAX_REPLY_BYTES:
        raise ValueError("Agent response too large")
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get("reply"), str):
        raise ValueError("Invalid agent response contract")
    return {"agent": agent, "reply": data["reply"], "source": "configured_agent_endpoint"}


def status():
    return {agent: config(agent)["status"] for agent in AGENTS}
