"""Minimal MCP stdio adapter for the Codex background queue.

Start only as a local child process of a trusted MCP client. The actor identity
comes from server-side environment, NEVER from tool arguments.
"""
import json
import os
import sys

from codex.worker import enqueue, status

PROTOCOL = "2024-11-05"
TOOLS = [
    {"name": "codex_enqueue", "description": "Queue a read-only Codex analysis job.",
     "inputSchema": {"type": "object", "properties": {
         "prompt": {"type": "string", "minLength": 1, "maxLength": 8000}},
         "required": ["prompt"], "additionalProperties": False}},
    {"name": "codex_status", "description": "Read the state of your Codex job.",
     "inputSchema": {"type": "object", "properties": {
         "job_id": {"type": "string"}},
         "required": ["job_id"], "additionalProperties": False}},
]


def process(request, *, actor=None, authorized=False):
    """Return MCP JSON-RPC response. Authorization is injected by trusted host."""
    req_id = request.get("id")
    method = request.get("method")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "protocolVersion": PROTOCOL,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "monolith-codex", "version": "0.1.0"}}}
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method != "tools/call":
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}
    if not authorized or not actor:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32001, "message": "Unauthorized"}}
    params = request.get("params") or {}
    name = params.get("name")
    args = params.get("arguments") or {}
    try:
        if not isinstance(args, dict):
            raise ValueError("Invalid arguments")
        if name == "codex_enqueue":
            if set(args) != {"prompt"} or not isinstance(args["prompt"], str):
                raise ValueError("Expected prompt")
            job_id = enqueue(actor, args["prompt"])
            value = {"job_id": job_id, "status": "queued"}
        elif name == "codex_status":
            if set(args) != {"job_id"} or not isinstance(args["job_id"], str):
                raise ValueError("Expected job_id")
            value = status(args["job_id"])
            if value["actor"] != actor:
                raise PermissionError("Job belongs to a different actor")
        else:
            raise ValueError("Unknown tool")
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}]}}
    except (ValueError, PermissionError, KeyError) as exc:
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "isError": True, "content": [{"type": "text", "text": str(exc)}]}}


def main():
    # Must be supplied by the trusted service launching this stdio process.
    actor = os.environ.get("MONOLITH_AUTHENTICATED_ACTOR")
    authorized = os.environ.get("MONOLITH_CODEX_ENABLED") == "1" and bool(actor)
    for line in sys.stdin:
        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                continue
            result = process(request, actor=actor, authorized=authorized)
            if result is not None and "id" in request:
                print(json.dumps(result, ensure_ascii=False), flush=True)
        except (ValueError, TypeError):
            continue


if __name__ == "__main__":
    main()
