"""Bounded autonomous Ubuntu maintenance executor.

No shell, no arbitrary command strings. Actions are explicitly enumerated.
Designed to run as a restricted service user with only narrow sudoers grants.
"""
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

SERVICES = frozenset({"ollama", "monolith-bridge", "monolith-codex"})
ACTIONS = frozenset({"status", "restart", "logs"})
NAME_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")


def execute(action: str, service: str, *, actor: str, audit_path: str | None = None):
    if action not in ACTIONS or service not in SERVICES or not NAME_RE.fullmatch(actor):
        raise ValueError("Action, service or actor not permitted")
    if action == "restart":
        argv = ["/usr/bin/sudo", "-n", "/usr/bin/systemctl", "restart", service + ".service"]
    elif action == "status":
        argv = ["/usr/bin/systemctl", "is-active", service + ".service"]
    else:
        argv = ["/usr/bin/journalctl", "-u", service + ".service", "-n", "80", "--no-pager", "--output=short-iso"]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=30, check=False)
        result = {"actor": actor, "action": action, "service": service,
                  "returncode": proc.returncode, "output": (proc.stdout + proc.stderr)[-12000:]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        result = {"actor": actor, "action": action, "service": service,
                  "returncode": -1, "output": type(exc).__name__}
    if audit_path:
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(), **result}
        with open(audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=sorted(ACTIONS))
    parser.add_argument("service", choices=sorted(SERVICES))
    parser.add_argument("--actor", required=True, choices=["aria", "alex", "astyria", "aurelius"])
    args = parser.parse_args()
    # CLI actor is only a label. Remote use MUST authenticate actor upstream.
    print(json.dumps(execute(args.action, args.service, actor=args.actor,
                             audit_path=os.getenv("MONOLITH_CONTROL_AUDIT")), ensure_ascii=False))


if __name__ == "__main__":
    main()
