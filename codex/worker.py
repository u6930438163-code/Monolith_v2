"""Background Codex job runner prototype for Monolith_v2.

Queue is persisted in SQLite; execution uses the installed Codex CLI.
Run only on a trusted dedicated host with filesystem/network sandboxing.
"""
import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB = Path(os.environ.get("MONOLITH_CODEX_DB", "codex/jobs.sqlite3"))
WORKSPACE = Path(os.environ.get("MONOLITH_CODEX_WORKSPACE", ".")).resolve()
MAX_PROMPT = 8000
TIMEOUT = 900


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, actor TEXT NOT NULL, prompt TEXT NOT NULL,
        status TEXT NOT NULL, created_at TEXT NOT NULL, output TEXT,
        exit_code INTEGER)""")
    conn.commit()
    return conn


def enqueue(actor, prompt):
    if not actor or not prompt.strip() or len(prompt) > MAX_PROMPT:
        raise ValueError("Invalid actor or prompt")
    job_id = str(uuid.uuid4())
    with connect() as conn:
        conn.execute("INSERT INTO jobs (id,actor,prompt,status,created_at) VALUES (?,?,?,?,?)",
                     (job_id, actor, prompt, "queued", datetime.now(timezone.utc).isoformat()))
    return job_id


def status(job_id):
    with connect() as conn:
        row = conn.execute("SELECT id,actor,status,created_at,output,exit_code FROM jobs WHERE id=?", (job_id,)).fetchone()
    if row is None:
        raise KeyError(job_id)
    return dict(zip(("id","actor","status","created_at","output","exit_code"), row))


def run_next():
    """Single-worker runner. No API exposed; caller must enforce authorization."""
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT id,prompt FROM jobs WHERE status='queued' ORDER BY created_at LIMIT 1").fetchone()
        if row is None:
            return False
        job_id, prompt = row
        conn.execute("UPDATE jobs SET status='running' WHERE id=?", (job_id,))
    if not shutil.which("codex"):
        output, code = "Codex CLI not installed on worker host", 127
    else:
        try:
            # Read-only sandbox: code changes require a separately approved workflow.
            result = subprocess.run(
                ["codex", "exec", "--sandbox", "read-only", "--skip-git-repo-check", prompt],
                cwd=WORKSPACE, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=TIMEOUT, check=False,
                env={k:v for k,v in os.environ.items() if k not in {"GITHUB_TOKEN","GH_TOKEN"}},
            )
            output, code = result.stdout[-20000:], result.returncode
        except subprocess.TimeoutExpired:
            output, code = "Codex job timed out", 124
        except OSError as exc:
            output, code = f"Codex worker error: {type(exc).__name__}", 1
    with connect() as conn:
        conn.execute("UPDATE jobs SET status=?,output=?,exit_code=? WHERE id=?",
                     ("done" if code == 0 else "failed", output, code, job_id))
    return True


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    add = sub.add_parser("enqueue")
    add.add_argument("--actor", required=True)
    add.add_argument("--prompt", required=True)
    get = sub.add_parser("status")
    get.add_argument("id")
    sub.add_parser("once")
    sub.add_parser("worker")
    args = parser.parse_args()
    if args.cmd == "enqueue":
        print(enqueue(args.actor, args.prompt))
    elif args.cmd == "status":
        print(json.dumps(status(args.id), ensure_ascii=False, indent=2))
    elif args.cmd == "once":
        run_next()
    else:
        while True:
            if not run_next():
                time.sleep(3)


if __name__ == "__main__":
    main()
